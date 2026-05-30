"""Deployment metrics, waste finder, and before/after comparisons."""

from __future__ import annotations

import numpy as np
import pandas as pd

from config import DEFAULT_ROI_ASSUMPTIONS
from amdep.features import certification_match_score, skill_match_score
from amdep.retention import calculate_personnel_burden
from amdep.utils import pipe_list, safe_pct, travel_minutes, weighted_percentile


def compute_kpis(
    assignments: pd.DataFrame,
    workers: pd.DataFrame,
    jobs: pd.DataFrame,
    *,
    roi_assumptions: dict[str, float] | None = None,
) -> dict[str, float]:
    assumptions = {**DEFAULT_ROI_ASSUMPTIONS, **(roi_assumptions or {})}
    if assignments.empty:
        return _empty_kpis()

    route_burn_hours = float(assignments["commute_minutes"].sum() * 2.0 / 60.0)
    avg_commute = float(assignments["commute_minutes"].mean())
    p90_commute = weighted_percentile(assignments["commute_minutes"], 90)
    labor_waste = route_burn_hours * assumptions["loaded_labor_cost_per_hour"]
    vehicle_cost = route_burn_hours * assumptions["vehicle_cost_per_hour"]
    burden = calculate_personnel_burden(assignments, workers, jobs)
    staffing = job_staffing_status(assignments, jobs)
    supervisor_overload = supervisor_overload_index(assignments, workers)
    crew_fragment = crew_fragmentation_index(assignments)
    equipment_utilization = estimate_equipment_utilization(assignments, jobs)

    return {
        "assignments": float(len(assignments)),
        "total_route_burn_hours": route_burn_hours,
        "average_commute_minutes": avg_commute,
        "p90_commute_minutes": p90_commute,
        "total_estimated_labor_waste": labor_waste,
        "fuel_truck_cost": vehicle_cost,
        "daily_deployment_cost": labor_waste + vehicle_cost,
        "overtime_risk": float(np.clip((assignments["commute_minutes"] > 55).mean() + avg_commute / 220.0, 0, 1)),
        "personnel_burden_index": float(burden["burden_score"].mean()),
        "attrition_risk_proxy": float(burden["attrition_risk_proxy"].mean()),
        "supervisor_overload_index": supervisor_overload,
        "crew_fragmentation_index": crew_fragment,
        "skill_coverage_pct": float(assignments["skill_match_score"].mean()),
        "jobs_fully_staffed_pct": float(staffing["fully_staffed"].mean()),
        "equipment_utilization_pct": equipment_utilization,
        "robotics_utilization_pct": 0.0,
    }


def compare_kpis(naive: dict[str, float], optimized: dict[str, float], *, workdays_per_year: int = 250) -> dict[str, float]:
    daily_savings = naive["daily_deployment_cost"] - optimized["daily_deployment_cost"]
    realization_factor = DEFAULT_ROI_ASSUMPTIONS["impact_realization_factor"]
    realized_daily_savings = daily_savings * realization_factor
    implementation_horizon_months = 18
    route_recovery = safe_pct(
        naive["total_route_burn_hours"] - optimized["total_route_burn_hours"],
        naive["total_route_burn_hours"],
    )
    realized_annual = realized_daily_savings * workdays_per_year
    return {
        "daily_savings": daily_savings,
        "annualized_savings": daily_savings * workdays_per_year,
        "realization_factor": realization_factor,
        "realized_daily_savings": realized_daily_savings,
        "realized_annualized_savings": realized_annual,
        "implementation_horizon_months": implementation_horizon_months,
        "implementation_horizon_impact": realized_annual * implementation_horizon_months / 12.0,
        "route_burn_recovery_pct": route_recovery,
        "average_commute_delta": naive["average_commute_minutes"] - optimized["average_commute_minutes"],
        "p90_commute_delta": naive["p90_commute_minutes"] - optimized["p90_commute_minutes"],
        "burden_delta": naive["personnel_burden_index"] - optimized["personnel_burden_index"],
        "dispatch_delta": naive["total_route_burn_hours"] - optimized["total_route_burn_hours"],
    }


def calculate_deployment_economics(
    *,
    baseline_assignments: pd.DataFrame,
    optimized_assignments: pd.DataFrame,
    jobs: pd.DataFrame,
    baseline_kpis: dict[str, float],
    optimized_kpis: dict[str, float],
    baseline_burden: pd.DataFrame,
    optimized_burden: pd.DataFrame,
    robotics_summary: dict[str, object],
    workdays_per_year: int = 250,
    implementation_horizon_months: int = 18,
) -> dict[str, float]:
    """Estimate organizational deployment impact from the simulated before/after.

    This is still synthetic, but it is derived from the generated GC portfolio and
    the actual optimizer output rather than a hand-entered claim.
    """
    route_capacity = max(0.0, baseline_kpis["daily_deployment_cost"] - optimized_kpis["daily_deployment_cost"]) * workdays_per_year

    baseline_staffing = job_staffing_status(baseline_assignments, jobs)
    optimized_staffing = job_staffing_status(optimized_assignments, jobs)
    coverage_gap_reduction = max(
        0,
        int(baseline_staffing["unfilled_slots"].sum()) - int(optimized_staffing["unfilled_slots"].sum()),
    )
    urgent_gap_reduction = max(
        0,
        int(baseline_staffing.loc[baseline_staffing["urgency"] >= 4, "unfilled_slots"].sum())
        - int(optimized_staffing.loc[optimized_staffing["urgency"] >= 4, "unfilled_slots"].sum()),
    )

    baseline_quality = _assignment_quality_index(baseline_assignments)
    optimized_quality = _assignment_quality_index(optimized_assignments)
    role_fit_lift = max(0.0, optimized_quality["role_fit"] - baseline_quality["role_fit"])
    cert_fit_lift = max(0.0, optimized_quality["cert_fit"] - baseline_quality["cert_fit"])
    baseline_leaks = _deployment_leak_index(baseline_assignments)
    optimized_leaks = _deployment_leak_index(optimized_assignments)
    leak_delta = {key: max(0.0, baseline_leaks[key] - optimized_leaks[key]) for key in baseline_leaks}
    high_burden_reduction = max(
        0,
        int((baseline_burden["burden_band"] == "High").sum()) - int((optimized_burden["burden_band"] == "High").sum()),
    )
    medium_high_burden_reduction = max(
        0,
        int(baseline_burden["burden_band"].isin(["Medium", "High"]).sum())
        - int(optimized_burden["burden_band"].isin(["Medium", "High"]).sum()),
    )
    route_hours_recovered = max(0.0, baseline_kpis["total_route_burn_hours"] - optimized_kpis["total_route_burn_hours"])
    fully_staffed_lift = max(0.0, optimized_kpis["jobs_fully_staffed_pct"] - baseline_kpis["jobs_fully_staffed_pct"])
    qa_closeout_trips = float(robotics_summary.get("avoidable_inspection_trips", 0.0) or 0.0)
    baseline_retention = _retention_exposure(baseline_assignments)
    optimized_retention = _retention_exposure(optimized_assignments)
    retained_key_staff = max(0.0, baseline_retention["expected_quits"] - optimized_retention["expected_quits"])

    # Modeled using conservative internal-cost proxies for a regional GC staff plan.
    coverage_value = coverage_gap_reduction * 18_000.0 + urgent_gap_reduction * 14_000.0
    role_fit_value = role_fit_lift * max(1.0, optimized_kpis["assignments"]) * 8_500.0
    cert_fit_value = cert_fit_lift * max(1.0, optimized_kpis["assignments"]) * 11_000.0
    retention_value = retained_key_staff * 142_000.0
    burden_value = high_burden_reduction * 26_000.0 + medium_high_burden_reduction * 6_000.0
    qa_closeout_value = qa_closeout_trips * 7_500.0
    schedule_variance_value = leak_delta["schedule_risk"] * 1_350.0
    rework_value = leak_delta["qa_rework"] * 1_100.0
    co_admin_value = leak_delta["co_admin"] * 0.34
    margin_fade_value = leak_delta["margin_fade"] * 1_800.0
    admin_operating_model_value = retained_key_staff * 18_000.0 + route_hours_recovered * 135.0 * 52.0
    compounding_factor = min(0.22, max(0.0, (retained_key_staff * 0.035) + (fully_staffed_lift * 0.12) + (role_fit_lift * 0.18)))

    direct_run_rate = (
        route_capacity
        + retention_value
        + coverage_value
        + role_fit_value
        + cert_fit_value
        + burden_value
        + qa_closeout_value
        + schedule_variance_value
        + rework_value
        + co_admin_value
        + margin_fade_value
        + admin_operating_model_value
    )
    compounding_value = direct_run_rate * compounding_factor
    annual_run_rate = direct_run_rate + compounding_value
    horizon_impact = annual_run_rate * implementation_horizon_months / 12.0
    peer_revenue_proxy = 704_000_000.0
    peer_net_income_proxy = peer_revenue_proxy * 0.041

    return {
        "route_capacity_value": round(route_capacity, 2),
        "coverage_value": round(coverage_value, 2),
        "retention_value": round(retention_value, 2),
        "role_fit_value": round(role_fit_value, 2),
        "certification_value": round(cert_fit_value, 2),
        "burden_value": round(burden_value, 2),
        "qa_closeout_value": round(qa_closeout_value, 2),
        "schedule_variance_value": round(schedule_variance_value, 2),
        "rework_value": round(rework_value, 2),
        "co_admin_value": round(co_admin_value, 2),
        "margin_fade_value": round(margin_fade_value, 2),
        "admin_operating_model_value": round(admin_operating_model_value, 2),
        "direct_run_rate": round(direct_run_rate, 2),
        "compounding_factor": round(compounding_factor, 4),
        "compounding_value": round(compounding_value, 2),
        "annual_deployment_run_rate": round(annual_run_rate, 2),
        "implementation_horizon_months": float(implementation_horizon_months),
        "implementation_horizon_impact": round(horizon_impact, 2),
        "coverage_gap_reduction": float(coverage_gap_reduction),
        "urgent_gap_reduction": float(urgent_gap_reduction),
        "role_fit_lift": round(role_fit_lift, 4),
        "cert_fit_lift": round(cert_fit_lift, 4),
        "high_burden_reduction": float(high_burden_reduction),
        "medium_high_burden_reduction": float(medium_high_burden_reduction),
        "baseline_expected_quits": round(baseline_retention["expected_quits"], 4),
        "optimized_expected_quits": round(optimized_retention["expected_quits"], 4),
        "retained_key_staff": round(retained_key_staff, 4),
        "baseline_long_haul_key_staff": float(baseline_retention["long_haul_key_staff"]),
        "optimized_long_haul_key_staff": float(optimized_retention["long_haul_key_staff"]),
        "route_hours_recovered": round(route_hours_recovered, 2),
        "fully_staffed_lift": round(fully_staffed_lift, 4),
        "qa_closeout_trips": qa_closeout_trips,
        "peer_revenue_proxy": peer_revenue_proxy,
        "peer_net_income_proxy": round(peer_net_income_proxy, 2),
        "profit_leverage_pct": round(annual_run_rate / max(peer_net_income_proxy, 1.0), 4),
    }


def _assignment_quality_index(assignments: pd.DataFrame) -> dict[str, float]:
    if assignments.empty:
        return {"role_fit": 0.0, "cert_fit": 0.0}
    return {
        "role_fit": float(pd.to_numeric(assignments["skill_match_score"], errors="coerce").fillna(0.0).mean()),
        "cert_fit": float(pd.to_numeric(assignments["certification_match_score"], errors="coerce").fillna(0.0).mean()),
    }


def _retention_exposure(assignments: pd.DataFrame) -> dict[str, float]:
    if assignments.empty:
        return {"expected_quits": 0.0, "long_haul_key_staff": 0.0}
    frame = assignments.copy()
    role_text = frame.get("worker_role", frame.get("role", "")).astype(str).str.lower() if "worker_role" in frame or "role" in frame else pd.Series("", index=frame.index)
    if role_text.eq("").all():
        worker_name = frame.get("worker_name", pd.Series("", index=frame.index)).astype(str).str.lower()
        key_staff = worker_name.str.contains("super|manager|executive|engineer|closeout|safety|quality|mep")
    else:
        key_staff = role_text.str.contains("superintendent|project manager|project executive|project engineer|safety|quality|closeout|mep")
    commute = pd.to_numeric(frame.get("commute_minutes", 0), errors="coerce").fillna(0.0)
    overtime = _numeric_column(frame, "overtime_hours_30d", 0.0)
    skill_gap = 1.0 - pd.to_numeric(frame.get("skill_match_score", 1), errors="coerce").fillna(1.0)
    long_haul = (commute >= 75) & key_staff
    two_hour_round_trip = (commute >= 60) & key_staff
    exposure = (
        long_haul.astype(float) * 0.18
        + two_hour_round_trip.astype(float) * 0.07
        + (commute.clip(0, 120) / 120.0) * 0.04
        + (overtime.clip(0, 30) / 30.0) * 0.05
        + skill_gap.clip(0, 1) * 0.04
    )
    exposure = exposure.where(key_staff, exposure * 0.35)
    return {
        "expected_quits": float(exposure.sum()),
        "long_haul_key_staff": float(long_haul.sum()),
    }


def _deployment_leak_index(assignments: pd.DataFrame) -> dict[str, float]:
    if assignments.empty:
        return {"schedule_risk": 0.0, "qa_rework": 0.0, "co_admin": 0.0, "margin_fade": 0.0}
    frame = assignments.copy()
    commute = pd.to_numeric(frame.get("commute_minutes", 0), errors="coerce").fillna(0.0)
    skill_gap = 1.0 - pd.to_numeric(frame.get("skill_match_score", 1), errors="coerce").fillna(1.0)
    cert_gap = 1.0 - pd.to_numeric(frame.get("certification_match_score", 1), errors="coerce").fillna(1.0)
    volatility = _numeric_column(frame, "schedule_volatility", 0.35)
    co_exposure = _numeric_column(frame, "change_order_exposure", 3500.0)
    role_text = frame.get("worker_role", pd.Series("", index=frame.index)).astype(str).str.lower()
    phase = frame.get("phase", pd.Series("", index=frame.index)).astype(str).str.lower()
    pm_or_super = role_text.str.contains("superintendent|project manager|project executive|project engineer")
    qa_phase = phase.str.contains("inspection|closeout|turnover|warranty|interiors|mep")

    schedule_risk = ((commute / 60.0) * 0.38 + skill_gap * 1.4 + volatility * 1.15 + cert_gap * 0.8).sum()
    qa_rework = ((skill_gap * 1.2 + cert_gap * 1.4 + volatility * 0.35 + qa_phase.astype(float) * 0.28) * (1 + commute / 150.0)).sum()
    co_admin = (co_exposure * (0.025 + skill_gap * 0.055 + volatility * 0.045 + pm_or_super.astype(float) * 0.018)).sum()
    margin_fade = (skill_gap * 0.9 + cert_gap * 0.5 + volatility * 0.7 + (commute > 60).astype(float) * 0.55).sum()
    return {
        "schedule_risk": float(schedule_risk),
        "qa_rework": float(qa_rework),
        "co_admin": float(co_admin),
        "margin_fade": float(margin_fade),
    }


def _numeric_column(frame: pd.DataFrame, column: str, default: float) -> pd.Series:
    if column not in frame:
        return pd.Series(default, index=frame.index, dtype=float)
    return pd.to_numeric(frame[column], errors="coerce").fillna(default)


def build_waste_findings(naive: pd.DataFrame, optimized: pd.DataFrame, workers: pd.DataFrame, jobs: pd.DataFrame, assumptions: dict[str, float] | None = None) -> pd.DataFrame:
    """Rank bad baseline assignments with closer-qualified alternatives and optimized swaps."""
    if naive.empty:
        return pd.DataFrame()
    roi = {**DEFAULT_ROI_ASSUMPTIONS, **(assumptions or {})}
    worker_lookup = workers.set_index("personnel_id").to_dict("index")
    job_lookup = jobs.set_index("jobsite_id").to_dict("index")
    optimized_job_map = optimized.sort_values("commute_minutes").groupby("jobsite_id").first().to_dict("index") if not optimized.empty else {}
    rows = []

    for _, assignment in naive.iterrows():
        job = job_lookup.get(assignment["jobsite_id"])
        if not job:
            continue
        required_skills = pipe_list(job["required_skills"])
        required_certs = pipe_list(job["required_certifications"])
        alternatives = []
        for _, worker in workers.iterrows():
            skills = pipe_list(worker["skills"])
            certs = pipe_list(worker["certifications"])
            if skill_match_score(skills, required_skills) <= 0:
                continue
            if certification_match_score(certs, required_certs) < 1.0:
                continue
            commute = travel_minutes(worker["home_lat"], worker["home_lon"], job["lat"], job["lon"])
            alternatives.append((commute, worker["personnel_id"], worker["name"]))
        if not alternatives:
            continue
        alternatives.sort(key=lambda item: item[0])
        best_commute, best_id, best_name = alternatives[0]
        avoidable_minutes = max(0.0, float(assignment["commute_minutes"]) - float(best_commute))
        if avoidable_minutes < 12 and float(assignment["commute_minutes"]) < 65:
            continue
        optimized_pick = optimized_job_map.get(assignment["jobsite_id"], {})
        daily_cost = (avoidable_minutes * 2.0 / 60.0) * (roi["loaded_labor_cost_per_hour"] + roi["vehicle_cost_per_hour"])
        rows.append(
            {
                "assignment_id": assignment["assignment_id"],
                "jobsite_id": assignment["jobsite_id"],
                "job_name": assignment.get("job_name", job["name"]),
                "assigned_personnel": assignment["personnel_id"],
                "assigned_worker": assignment.get("worker_name", worker_lookup.get(assignment["personnel_id"], {}).get("name", "")),
                "assigned_commute_minutes": round(float(assignment["commute_minutes"]), 1),
                "closer_qualified_worker": best_id,
                "closer_qualified_name": best_name,
                "closer_commute_minutes": round(float(best_commute), 1),
                "avoidable_minutes_one_way": round(float(avoidable_minutes), 1),
                "estimated_dollars_per_day": round(float(daily_cost), 2),
                "annualized_cost": round(float(daily_cost * roi["workdays_per_year"]), 2),
                "optimized_reassignment": optimized_pick.get("personnel_id", ""),
                "reason": f"Drove {float(assignment['commute_minutes']):.0f} minutes despite qualified project staff within {best_commute:.0f} minutes.",
            }
        )
    return pd.DataFrame(rows).sort_values("estimated_dollars_per_day", ascending=False).reset_index(drop=True)


def job_staffing_status(assignments: pd.DataFrame, jobs: pd.DataFrame) -> pd.DataFrame:
    counts = assignments.groupby("jobsite_id").size().rename("assigned_headcount") if not assignments.empty else pd.Series(dtype=int, name="assigned_headcount")
    status = jobs[["jobsite_id", "name", "region", "required_headcount", "urgency"]].merge(counts, on="jobsite_id", how="left")
    status["assigned_headcount"] = status["assigned_headcount"].fillna(0).astype(int)
    status["fully_staffed"] = status["assigned_headcount"] >= status["required_headcount"]
    status["unfilled_slots"] = (status["required_headcount"] - status["assigned_headcount"]).clip(lower=0)
    return status.sort_values(["fully_staffed", "urgency"], ascending=[True, False])


def supervisor_overload_index(assignments: pd.DataFrame, workers: pd.DataFrame) -> float:
    if assignments.empty:
        return 0.0
    reports = workers.loc[workers["supervisor_id"].astype(str) != ""].groupby("supervisor_id").size()
    active = assignments.groupby("supervisor_id").size()
    aligned = pd.DataFrame({"reports": reports, "active": active}).fillna(0)
    if aligned.empty:
        return 0.0
    overload = (aligned["active"] / aligned["reports"].replace(0, np.nan)).fillna(0).clip(lower=0)
    return float(np.clip(overload.quantile(0.90), 0, 2) / 2)


def crew_fragmentation_index(assignments: pd.DataFrame) -> float:
    if assignments.empty:
        return 0.0
    crew_regions = assignments.groupby("crew_id")["job_region"].nunique()
    crew_jobs = assignments.groupby("crew_id")["jobsite_id"].nunique()
    raw = (crew_regions * crew_jobs).replace([np.inf, -np.inf], 0)
    return float(np.clip(raw.mean() / 8.0, 0, 1))


def estimate_equipment_utilization(assignments: pd.DataFrame, jobs: pd.DataFrame) -> float:
    if assignments.empty:
        return 0.0
    staffed_jobs = assignments["jobsite_id"].nunique()
    jobs_requiring_equipment = jobs.loc[jobs["required_equipment"].astype(str) != "", "jobsite_id"].nunique()
    return safe_pct(min(staffed_jobs, jobs_requiring_equipment), jobs_requiring_equipment)


def operator_wake_up_calls(waste: pd.DataFrame, naive: pd.DataFrame, optimized: pd.DataFrame, burden: pd.DataFrame, graph_summary: dict[str, object], robotics_summary: dict[str, object]) -> list[str]:
    calls = []
    passed_count = int((waste["avoidable_minutes_one_way"] > 15).sum()) if not waste.empty else 0
    top_route_recovery = float(waste.head(12)["avoidable_minutes_one_way"].sum() * 2 / 60) if not waste.empty else 0.0
    calls.append(f"{passed_count} staff assignments drove past closer qualified project coverage options.")
    calls.append(f"Top 12 project-staff swaps recover {top_route_recovery:.1f} daily route-burn hours.")
    calls.append(f"{len(graph_summary.get('overloaded_supervisors', []))} supervisors show geographically incoherent or overloaded clusters.")
    calls.append(f"{int((burden['burden_band'] == 'High').sum())} high-value personnel carry high burden risk.")
    calls.append(f"{len(graph_summary.get('certification_bottlenecks', []))} certifications create hidden bottlenecks.")
    calls.append(f"Progress-capture deployment could remove {int(robotics_summary.get('avoidable_inspection_trips', 0))} inspection trips in the current scenario.")
    return calls


def _empty_kpis() -> dict[str, float]:
    keys = [
        "assignments",
        "total_route_burn_hours",
        "average_commute_minutes",
        "p90_commute_minutes",
        "total_estimated_labor_waste",
        "fuel_truck_cost",
        "daily_deployment_cost",
        "overtime_risk",
        "personnel_burden_index",
        "attrition_risk_proxy",
        "supervisor_overload_index",
        "crew_fragmentation_index",
        "skill_coverage_pct",
        "jobs_fully_staffed_pct",
        "equipment_utilization_pct",
        "robotics_utilization_pct",
    ]
    return {key: 0.0 for key in keys}
