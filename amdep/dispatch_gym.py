"""Replay, score, optimize, and calibrate field dispatch policies."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from config import DEFAULT_SEED, DEFAULT_WEIGHTS
from amdep.brain import train_synthetic_brain
from amdep.calibration import CalibrationResult, calibrate_weight_policy, score_assignment_policy
from amdep.graph_analysis import graph_insights
from amdep.metrics import build_waste_findings, calculate_deployment_economics, compare_kpis, compute_kpis, job_staffing_status
from amdep.naive_scheduler import build_naive_schedule
from amdep.optimizer import optimize_deployment
from amdep.retention import calculate_personnel_burden
from amdep.robotics import robotics_readiness
from amdep.roi import ROIAssumptions, calculate_roi_cases
from amdep.synthetic_data import generate_synthetic_company


@dataclass
class DispatchAuditResult:
    workers: pd.DataFrame
    jobs: pd.DataFrame
    assets: pd.DataFrame
    baseline_assignments: pd.DataFrame
    optimized_assignments: pd.DataFrame
    brain_scores: pd.DataFrame
    calibration: CalibrationResult
    optimizer_result: dict[str, object]
    baseline_kpis: dict[str, float]
    optimized_kpis: dict[str, float]
    comparison: dict[str, float]
    waste_findings: pd.DataFrame
    personnel_burden: pd.DataFrame
    job_staffing_status: pd.DataFrame
    robotics_plan: pd.DataFrame
    robotics_summary: dict[str, object]
    graph_summary: dict[str, object]
    roi_cases: dict[str, dict[str, float]]
    deployment_economics: dict[str, float]
    policy_score_baseline: float
    policy_score_optimized: float
    caveat: str


def run_dispatch_audit(
    *,
    workers: pd.DataFrame,
    jobs: pd.DataFrame,
    assets: pd.DataFrame,
    baseline_assignments: pd.DataFrame | None = None,
    seed: int = DEFAULT_SEED,
    calibration_trials: int = 18,
    use_calibrated_policy: bool = True,
) -> DispatchAuditResult:
    """Run the algorithm-first audit: replay baseline, calibrate policy, optimize, score."""
    if baseline_assignments is None or baseline_assignments.empty:
        baseline_assignments = build_naive_schedule(workers, jobs, seed=seed)

    # Synthetic demo Brain Layer is trained on the customer's entity shape. Real production
    # training swaps this for outcome-labeled customer history.
    brain = train_synthetic_brain(workers, jobs, seed=seed)
    brain_scores = brain.score_pairs(workers, jobs)
    calibration = calibrate_weight_policy(
        workers,
        jobs,
        baseline_assignments,
        brain_scores=brain_scores,
        trials=calibration_trials,
        seed=seed,
    )
    weights = calibration.recommended_weights if use_calibrated_policy else DEFAULT_WEIGHTS
    optimized, optimizer_result = optimize_deployment(
        workers,
        jobs,
        weights=weights,
        brain_scores=brain_scores,
        seed=seed,
        time_limit_seconds=4.0,
    )

    baseline_kpis = compute_kpis(baseline_assignments, workers, jobs)
    optimized_kpis = compute_kpis(optimized, workers, jobs)
    comparison = compare_kpis(
        baseline_kpis,
        optimized_kpis,
        workdays_per_year=ROIAssumptions.defaults().workdays_per_year,
    )
    waste = build_waste_findings(baseline_assignments, optimized, workers, jobs)
    baseline_burden = calculate_personnel_burden(baseline_assignments, workers, jobs)
    burden = calculate_personnel_burden(optimized, workers, jobs)
    staffing = job_staffing_status(optimized, jobs)
    robotics_plan, robotics_summary = robotics_readiness(jobs, assets)
    graph_summary = graph_insights(workers, jobs, assets, optimized)
    high_burden_reduction = max(
        0,
        int((calculate_personnel_burden(baseline_assignments, workers, jobs)["burden_band"] == "High").sum())
        - int((burden["burden_band"] == "High").sum()),
    )
    roi_cases = calculate_roi_cases(
        baseline_kpis,
        optimized_kpis,
        high_burden_reduction=high_burden_reduction,
        robotics_trip_savings=float(robotics_summary.get("avoidable_inspection_trips", 0)),
    )
    deployment_economics = calculate_deployment_economics(
        baseline_assignments=baseline_assignments,
        optimized_assignments=optimized,
        jobs=jobs,
        baseline_kpis=baseline_kpis,
        optimized_kpis=optimized_kpis,
        baseline_burden=baseline_burden,
        optimized_burden=burden,
        robotics_summary=robotics_summary,
        workdays_per_year=ROIAssumptions.defaults().workdays_per_year,
    )
    baseline_policy_score = score_assignment_policy(baseline_assignments, brain_scores=brain_scores)
    optimized_policy_score = score_assignment_policy(optimized, brain_scores=brain_scores)
    return DispatchAuditResult(
        workers=workers,
        jobs=jobs,
        assets=assets,
        baseline_assignments=baseline_assignments,
        optimized_assignments=optimized,
        brain_scores=brain_scores,
        calibration=calibration,
        optimizer_result=optimizer_result,
        baseline_kpis=baseline_kpis,
        optimized_kpis=optimized_kpis,
        comparison=comparison,
        waste_findings=waste,
        personnel_burden=burden,
        job_staffing_status=staffing,
        robotics_plan=robotics_plan,
        robotics_summary=robotics_summary,
        graph_summary=graph_summary,
        roi_cases=roi_cases,
        deployment_economics=deployment_economics,
        policy_score_baseline=round(float(baseline_policy_score), 2),
        policy_score_optimized=round(float(optimized_policy_score), 2),
        caveat=calibration.caveat,
    )


def run_default_demo_audit(seed: int = DEFAULT_SEED) -> DispatchAuditResult:
    workers, jobs, assets = generate_synthetic_company(seed=seed)
    baseline = build_naive_schedule(workers, jobs, seed=seed)
    return run_dispatch_audit(
        workers=workers,
        jobs=jobs,
        assets=assets,
        baseline_assignments=baseline,
        seed=seed,
    )
