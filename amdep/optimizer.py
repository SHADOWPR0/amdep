"""OR-Tools optimization layer for constrained deployment decisions."""

from __future__ import annotations

from datetime import date
from time import perf_counter

import numpy as np
import pandas as pd

from config import DEFAULT_WEIGHTS
from amdep.features import build_pair_features

try:
    from ortools.sat.python import cp_model
except Exception:  # pragma: no cover - fallback used only when OR-Tools is unavailable
    cp_model = None


def optimize_deployment(
    workers: pd.DataFrame,
    jobs: pd.DataFrame,
    *,
    weights: dict[str, float] | None = None,
    brain_scores: pd.DataFrame | None = None,
    seed: int = 1776,
    deployment_date: date | None = None,
    time_limit_seconds: float = 8.0,
    candidate_limit_per_job: int = 28,
) -> tuple[pd.DataFrame, dict[str, object]]:
    """Optimize personnel-job assignments with hard cert and one-assignment-per-day constraints."""
    active_weights = {**DEFAULT_WEIGHTS, **(weights or {})}
    day = deployment_date or date.today()
    start = perf_counter()
    pairs = brain_scores.copy() if brain_scores is not None else build_pair_features(workers, jobs)
    pairs = pairs[pairs["has_required_certifications"].astype(bool)].copy()
    pairs["pair_cost"] = pairs.apply(lambda row: _pair_cost(row, active_weights), axis=1)
    pairs = (
        pairs.sort_values(["jobsite_id", "pair_cost", "commute_minutes"])
        .groupby("jobsite_id", group_keys=False)
        .head(candidate_limit_per_job)
        .reset_index(drop=True)
    )

    if cp_model is None:
        assignments = _fallback_greedy(workers, jobs, pairs, day)
        return assignments, {
            "status": "fallback_greedy_no_ortools",
            "objective_value": float(assignments.get("total_cost_score", pd.Series(dtype=float)).sum()),
            "assignments_created": int(len(assignments)),
            "unfilled_slots": int(max(0, jobs["required_headcount"].sum() - len(assignments))),
            "solver_seconds": round(perf_counter() - start, 3),
            "notes": ["OR-Tools unavailable; used deterministic greedy fallback."],
        }

    model = cp_model.CpModel()
    pair_records = pairs.to_dict("records")
    x: dict[tuple[str, str], cp_model.IntVar] = {}
    pair_by_key: dict[tuple[str, str], dict[str, object]] = {}

    for row in pair_records:
        key = (str(row["personnel_id"]), str(row["jobsite_id"]))
        x[key] = model.NewBoolVar(f"x_{key[0]}_{key[1]}")
        pair_by_key[key] = row

    for personnel_id in workers["personnel_id"].astype(str):
        vars_for_person = [var for (pid, _jid), var in x.items() if pid == personnel_id]
        if vars_for_person:
            model.Add(sum(vars_for_person) <= 1)

    under_vars: dict[str, cp_model.IntVar] = {}
    for _, job in jobs.iterrows():
        jobsite_id = str(job["jobsite_id"])
        target = int(job["required_headcount"])
        vars_for_job = [var for (_pid, jid), var in x.items() if jid == jobsite_id]
        under = model.NewIntVar(0, target, f"under_{jobsite_id}")
        under_vars[jobsite_id] = under
        if vars_for_job:
            model.Add(sum(vars_for_job) + under == target)
        else:
            model.Add(under == target)

    supervisor_overload_vars = []
    supervisor_rows = workers.loc[workers["is_supervisor"].astype(bool)]
    for _, supervisor in supervisor_rows.iterrows():
        supervisor_id = str(supervisor["personnel_id"])
        report_ids = set(workers.loc[workers["supervisor_id"].astype(str) == supervisor_id, "personnel_id"].astype(str))
        report_vars = [var for (pid, _jid), var in x.items() if pid in report_ids]
        if not report_vars:
            continue
        capacity = int(supervisor.get("max_reports", 10))
        overload = model.NewIntVar(0, max(0, len(report_vars)), f"overload_{supervisor_id}")
        model.Add(sum(report_vars) <= capacity + overload)
        supervisor_overload_vars.append(overload)

    objective_terms = []
    for key, var in x.items():
        objective_terms.append(var * int(round(float(pair_by_key[key]["pair_cost"]) * 10)))
    urgency_scale = 1.0 + float(active_weights.get("job_urgency", 1.0))
    for _, job in jobs.iterrows():
        penalty = int(round((1650 + 250 * int(job["urgency"])) * urgency_scale))
        objective_terms.append(under_vars[str(job["jobsite_id"])] * penalty)
    for overload in supervisor_overload_vars:
        objective_terms.append(overload * int(round(650 * float(active_weights.get("supervisor_balance", 1.0)))))

    model.Minimize(sum(objective_terms))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(time_limit_seconds)
    solver.parameters.max_deterministic_time = max(0.5, float(time_limit_seconds))
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = int(seed)
    status = solver.Solve(model)
    status_name = solver.StatusName(status)

    selected_rows = []
    worker_lookup = workers.set_index("personnel_id").to_dict("index")
    job_lookup = jobs.set_index("jobsite_id").to_dict("index")
    for key, var in x.items():
        if solver.Value(var) != 1:
            continue
        row = pair_by_key[key]
        worker = worker_lookup[key[0]]
        job = job_lookup[key[1]]
        selected_rows.append(_assignment_row(row, worker, job, day, len(selected_rows) + 1))

    assignments = pd.DataFrame(selected_rows)
    unfilled = int(sum(solver.Value(var) for var in under_vars.values()))
    result = {
        "status": status_name,
        "objective_value": float(solver.ObjectiveValue()) / 10.0 if status in (cp_model.OPTIMAL, cp_model.FEASIBLE) else float("nan"),
        "assignments_created": int(len(assignments)),
        "unfilled_slots": unfilled,
        "solver_seconds": round(perf_counter() - start, 3),
        "notes": [
            "Required certifications are treated as hard constraints.",
            "Synthetic risk scores are demo cost terms until validated against customer outcomes.",
        ],
    }
    return assignments, result


def _pair_cost(row: pd.Series, weights: dict[str, float]) -> float:
    commute = float(row["commute_minutes"])
    skill_gap = 1.0 - float(row["skill_match_score"])
    cert_gap = 1.0 - float(row["certification_match_score"])
    attrition = float(row.get("attrition_risk_cost", 0.0))
    delay = float(row.get("delay_risk_cost", 0.0))
    no_show = float(row.get("no_show_risk_cost", 0.0))
    crew_bad = float(row.get("crew_incompatibility_cost", 0.0))
    robotics_reward = float(row.get("robotics_suitability_reward", 0.0))
    urgency = float(row.get("job_urgency", 3.0))
    overtime = min(float(row.get("overtime_hours_30d", 0.0)) / 36.0, 1.4)
    fatigue = float(row.get("fatigue_base", 0.25))

    cost = 0.0
    cost += commute * 1.55 * float(weights.get("commute_reduction", 1.0))
    cost += skill_gap * 210.0 * float(weights.get("skill_fit", 1.0))
    cost += cert_gap * 400.0 * float(weights.get("certification_strictness", 1.0))
    cost += attrition * 120.0 * float(weights.get("retention_protection", 1.0))
    cost += no_show * 105.0 * float(weights.get("overtime_reduction", 1.0))
    cost += (overtime + fatigue) * 55.0 * float(weights.get("overtime_reduction", 1.0))
    cost += crew_bad * 90.0 * float(weights.get("crew_cohesion", 1.0))
    cost += delay * urgency * 42.0 * float(weights.get("job_urgency", 1.0))
    cost -= robotics_reward * 18.0 * float(weights.get("robotics_utilization", 1.0))
    if int(row.get("region_match", 0)) == 0:
        cost += 18.0 * float(weights.get("commute_reduction", 1.0))
    return max(float(cost), 1.0)


def _assignment_row(row: dict[str, object], worker: dict[str, object], job: dict[str, object], day: date, ordinal: int) -> dict[str, object]:
    return {
        "assignment_id": f"O-{day.strftime('%Y%m%d')}-{ordinal:04d}",
        "deployment_date": day.isoformat(),
        "assignment_source": "optimized",
        "personnel_id": row["personnel_id"],
        "jobsite_id": row["jobsite_id"],
        "supervisor_id": worker.get("supervisor_id", ""),
        "crew_id": worker.get("crew_id", ""),
        "worker_name": worker.get("name", ""),
        "worker_role": worker.get("role", ""),
        "job_name": job.get("name", ""),
        "project_type": job.get("project_type", ""),
        "phase": job.get("phase", ""),
        "schedule_volatility": round(float(job.get("schedule_volatility", 0.0)), 4),
        "change_order_exposure": round(float(job.get("change_order_exposure", 0.0)), 2),
        "home_region": worker.get("home_region", ""),
        "job_region": job.get("region", ""),
        "commute_minutes": round(float(row["commute_minutes"]), 2),
        "skill_match_score": round(float(row["skill_match_score"]), 4),
        "certification_match": True,
        "certification_match_score": round(float(row["certification_match_score"]), 4),
        "job_urgency": int(job.get("urgency", 3)),
        "attrition_risk_cost": round(float(row.get("attrition_risk_cost", 0.0)), 4),
        "delay_risk_cost": round(float(row.get("delay_risk_cost", 0.0)), 4),
        "no_show_risk_cost": round(float(row.get("no_show_risk_cost", 0.0)), 4),
        "crew_incompatibility_cost": round(float(row.get("crew_incompatibility_cost", 0.0)), 4),
        "robotics_suitability_reward": round(float(row.get("robotics_suitability_reward", 0.0)), 4),
        "total_cost_score": round(float(row["pair_cost"]), 2),
        "dispatch_reason": "global constrained optimizer",
    }


def _fallback_greedy(workers: pd.DataFrame, jobs: pd.DataFrame, pairs: pd.DataFrame, day: date) -> pd.DataFrame:
    assigned_people: set[str] = set()
    selected: list[dict[str, object]] = []
    worker_lookup = workers.set_index("personnel_id").to_dict("index")
    job_lookup = jobs.set_index("jobsite_id").to_dict("index")
    for _, job in jobs.sort_values("urgency", ascending=False).iterrows():
        job_pairs = pairs.loc[pairs["jobsite_id"] == job["jobsite_id"]].sort_values("pair_cost")
        for _, row in job_pairs.iterrows():
            if len([item for item in selected if item["jobsite_id"] == job["jobsite_id"]]) >= int(job["required_headcount"]):
                break
            personnel_id = str(row["personnel_id"])
            if personnel_id in assigned_people:
                continue
            assigned_people.add(personnel_id)
            selected.append(_assignment_row(row.to_dict(), worker_lookup[personnel_id], job_lookup[str(job["jobsite_id"])], day, len(selected) + 1))
    return pd.DataFrame(selected)
