"""Weight calibration gym for customer-specific optimizer policy tuning."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from config import DEFAULT_ROI_ASSUMPTIONS, DEFAULT_WEIGHTS
from amdep.optimizer import optimize_deployment


OUTCOME_PENALTIES = {
    "late_arrival": 140.0,
    "overtime_event": 180.0,
    "project_delay": 525.0,
    "callback_rework_event": 420.0,
    "productivity_shortfall": 260.0,
    "safety_incident_proxy": 900.0,
    "no_show": 650.0,
    "quit_within_90_days": 1100.0,
}


@dataclass
class CalibrationResult:
    method: str
    recommended_weights: dict[str, float]
    baseline_cost: float
    calibrated_cost: float
    improvement_pct: float
    trials: pd.DataFrame
    caveat: str


def score_assignment_policy(
    assignments: pd.DataFrame,
    *,
    brain_scores: pd.DataFrame | None = None,
    roi_assumptions: dict[str, float] | None = None,
) -> float:
    """Score an assignment policy using observed outcomes when available, otherwise synthetic risk terms."""
    if assignments.empty:
        return 0.0
    assumptions = {**DEFAULT_ROI_ASSUMPTIONS, **(roi_assumptions or {})}
    frame = assignments.copy()
    if brain_scores is not None:
        risk_cols = [
            "attrition_risk_cost",
            "delay_risk_cost",
            "no_show_risk_cost",
            "crew_incompatibility_cost",
            "robotics_suitability_reward",
        ]
        frame = frame.merge(
            brain_scores[["personnel_id", "jobsite_id", *risk_cols]],
            on=["personnel_id", "jobsite_id"],
            how="left",
            suffixes=("", "_brain"),
        )
        for col in risk_cols:
            if col not in frame.columns:
                frame[col] = frame[f"{col}_brain"]
            else:
                frame[col] = frame[col].fillna(frame.get(f"{col}_brain", 0.0))

    commute_cost = (
        pd.to_numeric(frame.get("commute_minutes", 0), errors="coerce").fillna(0.0)
        * 2.0
        / 60.0
        * (assumptions["loaded_labor_cost_per_hour"] + assumptions["vehicle_cost_per_hour"])
    )
    skill_gap = 1.0 - pd.to_numeric(frame.get("skill_match_score", 1.0), errors="coerce").fillna(1.0)
    cert_gap = 1.0 - pd.to_numeric(frame.get("certification_match_score", 1.0), errors="coerce").fillna(1.0)
    risk_cost = (
        pd.to_numeric(frame.get("attrition_risk_cost", 0), errors="coerce").fillna(0.0) * 160
        + pd.to_numeric(frame.get("delay_risk_cost", 0), errors="coerce").fillna(0.0) * 210
        + pd.to_numeric(frame.get("no_show_risk_cost", 0), errors="coerce").fillna(0.0) * 180
        + pd.to_numeric(frame.get("crew_incompatibility_cost", 0), errors="coerce").fillna(0.0) * 110
        - pd.to_numeric(frame.get("robotics_suitability_reward", 0), errors="coerce").fillna(0.0) * 35
    )
    observed_cost = pd.Series(np.zeros(len(frame)), index=frame.index)
    for col, penalty in OUTCOME_PENALTIES.items():
        if col in frame.columns:
            observed_cost += pd.to_numeric(frame[col], errors="coerce").fillna(0.0).clip(0, 1) * penalty

    total = commute_cost + skill_gap * 120 + cert_gap * 500 + risk_cost + observed_cost
    return float(total.sum())


def calibrate_weight_policy(
    workers: pd.DataFrame,
    jobs: pd.DataFrame,
    baseline_assignments: pd.DataFrame,
    *,
    brain_scores: pd.DataFrame,
    roi_assumptions: dict[str, float] | None = None,
    trials: int = 18,
    seed: int = 1776,
) -> CalibrationResult:
    """Search customer-specific optimizer weights against historical or synthetic outcome cost.

    This is a lightweight random-search gym. It is intentionally simpler than Optuna so the
    open-source MVP runs without another dependency. A production version can swap in Optuna.
    """
    rng = np.random.default_rng(seed)
    baseline_cost = score_assignment_policy(
        baseline_assignments,
        brain_scores=brain_scores,
        roi_assumptions=roi_assumptions,
    )
    weight_names = list(DEFAULT_WEIGHTS)
    trial_rows: list[dict[str, float | str]] = []
    best_weights = DEFAULT_WEIGHTS.copy()
    best_cost = float("inf")

    candidates = [DEFAULT_WEIGHTS.copy()]
    for _ in range(max(0, trials - 1)):
        candidate = {}
        for name in weight_names:
            low, high = (0.75, 1.65) if name in {"certification_strictness", "skill_fit"} else (0.35, 1.85)
            candidate[name] = round(float(rng.uniform(low, high)), 3)
        candidates.append(candidate)

    for idx, weights in enumerate(candidates):
        optimized, result = optimize_deployment(
            workers,
            jobs,
            weights=weights,
            brain_scores=brain_scores,
            seed=seed + idx,
            time_limit_seconds=1.2,
            candidate_limit_per_job=22,
        )
        cost = score_assignment_policy(
            optimized,
            brain_scores=brain_scores,
            roi_assumptions=roi_assumptions,
        )
        row = {"trial": idx, "policy_cost": cost, "solver_status": result["status"], **weights}
        trial_rows.append(row)
        if cost < best_cost:
            best_cost = cost
            best_weights = weights.copy()

    improvement = max(0.0, (baseline_cost - best_cost) / baseline_cost) if baseline_cost else 0.0
    method = "historical_outcome_search" if _has_outcome_columns(baseline_assignments) else "synthetic_risk_search"
    caveat = (
        "Weights were searched against observed customer outcome columns."
        if method == "historical_outcome_search"
        else "Weights were searched against synthetic risk terms because no real outcome labels were provided."
    )
    return CalibrationResult(
        method=method,
        recommended_weights={key: round(float(value), 3) for key, value in best_weights.items()},
        baseline_cost=round(float(baseline_cost), 2),
        calibrated_cost=round(float(best_cost), 2),
        improvement_pct=round(float(improvement), 4),
        trials=pd.DataFrame(trial_rows).sort_values("policy_cost").reset_index(drop=True),
        caveat=caveat,
    )


def _has_outcome_columns(assignments: pd.DataFrame) -> bool:
    return any(col in assignments.columns for col in OUTCOME_PENALTIES)
