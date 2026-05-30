"""NetworkX operational graph and deployment analytics."""

from __future__ import annotations

import networkx as nx
import pandas as pd

from amdep.metrics import build_waste_findings
from amdep.retention import calculate_personnel_burden
from amdep.utils import pipe_list


def build_operational_graph(workers: pd.DataFrame, jobs: pd.DataFrame, assets: pd.DataFrame, assignments: pd.DataFrame) -> nx.MultiDiGraph:
    graph = nx.MultiDiGraph(name="AmDep Field Ontology")
    for _, worker in workers.iterrows():
        graph.add_node(worker["personnel_id"], label=worker["name"], node_type="Personnel", region=worker["home_region"])
        graph.add_edge(worker["personnel_id"], worker["home_region"], relationship="lives_in")
        for skill in pipe_list(worker["skills"]):
            graph.add_node(skill, label=skill, node_type="Skill")
            graph.add_edge(worker["personnel_id"], skill, relationship="has_skill")
        for cert in pipe_list(worker["certifications"]):
            graph.add_node(cert, label=cert, node_type="Certification")
            graph.add_edge(worker["personnel_id"], cert, relationship="has_cert")
        if worker.get("supervisor_id"):
            graph.add_edge(worker["personnel_id"], worker["supervisor_id"], relationship="reports_to")

    for _, job in jobs.iterrows():
        graph.add_node(job["jobsite_id"], label=job["name"], node_type="Jobsite", region=job["region"], urgency=job["urgency"])
        graph.add_edge(job["jobsite_id"], job["region"], relationship="located_in")
        for skill in pipe_list(job["required_skills"]):
            graph.add_edge(job["jobsite_id"], skill, relationship="requires_skill")
        for cert in pipe_list(job["required_certifications"]):
            graph.add_edge(job["jobsite_id"], cert, relationship="requires_cert")
        for equipment in pipe_list(job["required_equipment"]):
            graph.add_node(equipment, label=equipment, node_type="EquipmentType")
            graph.add_edge(job["jobsite_id"], equipment, relationship="requires_equipment")

    for _, asset in assets.iterrows():
        node_type = "RoboticAsset" if asset["asset_kind"] == "robotic" else "Equipment"
        graph.add_node(asset["asset_id"], label=asset["asset_type"], node_type=node_type, region=asset["home_region"])
        graph.add_edge(asset["asset_id"], asset["home_region"], relationship="based_in")

    for _, assignment in assignments.iterrows():
        graph.add_edge(
            assignment["personnel_id"],
            assignment["jobsite_id"],
            relationship="assigned_to",
            commute_minutes=float(assignment["commute_minutes"]),
        )
    return graph


def graph_insights(workers: pd.DataFrame, jobs: pd.DataFrame, assets: pd.DataFrame, assignments: pd.DataFrame) -> dict[str, object]:
    burden = calculate_personnel_burden(assignments, workers, jobs)
    overloaded = _overloaded_supervisors(workers, assignments)
    bottlenecks = _certification_bottlenecks(workers, jobs)
    fragmentation = _crew_cohesion_breakdowns(assignments)
    asset_underuse = assets.loc[assets["available"].astype(bool) & (assets["asset_kind"] != "robotic")].head(8)
    geographic_mismatch = assignments.loc[(assignments["home_region"] != assignments["job_region"]) & (assignments["commute_minutes"] > 55)].copy() if not assignments.empty else pd.DataFrame()
    underutilized = workers.loc[~workers["personnel_id"].isin(assignments["personnel_id"].unique())].head(12)
    return {
        "overloaded_supervisors": overloaded.to_dict("records"),
        "geographic_mismatch_clusters": geographic_mismatch.head(12).to_dict("records"),
        "certification_bottlenecks": bottlenecks.to_dict("records"),
        "workers_with_repeated_bad_burden": burden.head(12).to_dict("records"),
        "underutilized_personnel": underutilized[["personnel_id", "name", "role", "home_region", "skills"]].to_dict("records"),
        "crew_cohesion_breakdowns": fragmentation.to_dict("records"),
        "asset_underutilization": asset_underuse[["asset_id", "asset_type", "home_region", "available"]].to_dict("records"),
    }


def high_value_reassignment_opportunities(naive: pd.DataFrame, optimized: pd.DataFrame, workers: pd.DataFrame, jobs: pd.DataFrame) -> pd.DataFrame:
    return build_waste_findings(naive, optimized, workers, jobs).head(15)


def _overloaded_supervisors(workers: pd.DataFrame, assignments: pd.DataFrame) -> pd.DataFrame:
    if assignments.empty:
        return pd.DataFrame(columns=["supervisor_id", "active_assignments", "regions", "jobs"])
    grouped = assignments.groupby("supervisor_id").agg(
        active_assignments=("personnel_id", "count"),
        regions=("job_region", "nunique"),
        jobs=("jobsite_id", "nunique"),
    )
    supervisor_meta = workers.loc[workers["is_supervisor"].astype(bool), ["personnel_id", "name", "home_region", "max_reports"]]
    result = grouped.reset_index().merge(supervisor_meta, left_on="supervisor_id", right_on="personnel_id", how="left")
    result["overload_score"] = (result["active_assignments"] / result["max_reports"].replace(0, 10)).fillna(0) + result["regions"] * 0.18
    return result.loc[result["overload_score"] > 0.82].sort_values("overload_score", ascending=False).head(10)


def _certification_bottlenecks(workers: pd.DataFrame, jobs: pd.DataFrame) -> pd.DataFrame:
    supply_rows = []
    for cert in sorted({cert for value in workers["certifications"] for cert in pipe_list(value)} | {cert for value in jobs["required_certifications"] for cert in pipe_list(value)}):
        supply = workers["certifications"].apply(lambda value: cert in pipe_list(value)).sum()
        demand = jobs["required_certifications"].apply(lambda value: cert in pipe_list(value)).sum()
        if demand == 0:
            continue
        supply_rows.append(
            {
                "certification": cert,
                "qualified_personnel": int(supply),
                "demanding_jobs": int(demand),
                "demand_supply_ratio": round(float(demand / max(1, supply)), 3),
            }
        )
    return pd.DataFrame(supply_rows).sort_values("demand_supply_ratio", ascending=False).head(8)


def _crew_cohesion_breakdowns(assignments: pd.DataFrame) -> pd.DataFrame:
    if assignments.empty:
        return pd.DataFrame(columns=["crew_id", "job_regions", "jobs", "members", "fragmentation_score"])
    grouped = assignments.groupby("crew_id").agg(
        job_regions=("job_region", "nunique"),
        jobs=("jobsite_id", "nunique"),
        members=("personnel_id", "nunique"),
    )
    grouped["fragmentation_score"] = grouped["job_regions"] * grouped["jobs"] / grouped["members"].clip(lower=1)
    return grouped.reset_index().sort_values("fragmentation_score", ascending=False).head(10)

