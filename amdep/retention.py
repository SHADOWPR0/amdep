"""Interpretable personnel burden and attrition proxy scoring."""

from __future__ import annotations

import numpy as np
import pandas as pd

from amdep.utils import normalize01


def calculate_personnel_burden(assignments: pd.DataFrame, workers: pd.DataFrame, jobs: pd.DataFrame) -> pd.DataFrame:
    """Calculate a demo burden score and attrition-risk proxy for every worker."""
    if assignments.empty:
        base = workers[["personnel_id", "name", "home_region", "role"]].copy()
        base["burden_score"] = 0.0
        base["burden_band"] = "Low"
        base["attrition_risk_proxy"] = 0.05
        base["burden_drivers"] = "No assignment in selected deployment."
        return base

    merged = assignments.merge(
        workers[
            [
                "personnel_id",
                "name",
                "role",
                "home_region",
                "fatigue_base",
                "overtime_hours_30d",
                "history_long_haul_count",
                "weekend_late_assignments_30d",
                "crew_affinity",
            ]
        ],
        on="personnel_id",
        how="right",
        suffixes=("_assignment", "_worker"),
    )
    merged["commute_minutes"] = pd.to_numeric(merged["commute_minutes"], errors="coerce").fillna(0.0)
    merged["skill_match_score"] = pd.to_numeric(merged["skill_match_score"], errors="coerce").fillna(1.0)
    merged["assigned"] = merged["jobsite_id"].notna()

    grouped = (
        merged.groupby("personnel_id")
        .agg(
            name=("name", "first"),
            role=("role", "first"),
            home_region=("home_region_worker", "first"),
            assignments=("assigned", "sum"),
            avg_commute=("commute_minutes", "mean"),
            max_commute=("commute_minutes", "max"),
            skill_gap=("skill_match_score", lambda s: float(1.0 - s.mean())),
            fatigue_base=("fatigue_base", "first"),
            overtime_hours_30d=("overtime_hours_30d", "first"),
            history_long_haul_count=("history_long_haul_count", "first"),
            weekend_late_assignments_30d=("weekend_late_assignments_30d", "first"),
            crew_affinity=("crew_affinity", "first"),
        )
        .reset_index()
    )
    grouped["long_commute_today"] = (grouped["max_commute"] > 60).astype(float)
    grouped["crew_mismatch"] = 1.0 - grouped["crew_affinity"].fillna(0.72)
    grouped["score_raw"] = (
        normalize01(grouped["avg_commute"]) * 24
        + normalize01(grouped["max_commute"]) * 16
        + normalize01(grouped["overtime_hours_30d"]) * 14
        + normalize01(grouped["history_long_haul_count"]) * 11
        + normalize01(grouped["weekend_late_assignments_30d"]) * 8
        + grouped["fatigue_base"].fillna(0.25) * 14
        + grouped["crew_mismatch"].fillna(0.25) * 7
        + grouped["skill_gap"].fillna(0.0) * 6
    )
    grouped["burden_score"] = np.clip(grouped["score_raw"], 0, 100).round(1)
    grouped["burden_band"] = pd.cut(
        grouped["burden_score"],
        bins=[-1, 34, 67, 101],
        labels=["Low", "Medium", "High"],
    ).astype(str)
    grouped["attrition_risk_proxy"] = np.clip(0.04 + grouped["burden_score"] / 140.0, 0.02, 0.78).round(3)
    grouped["burden_drivers"] = grouped.apply(_driver_text, axis=1)
    return grouped.sort_values("burden_score", ascending=False)


def _driver_text(row: pd.Series) -> str:
    drivers = []
    if row["max_commute"] > 60:
        drivers.append(f"{row['max_commute']:.0f} min route")
    if row["overtime_hours_30d"] > 14:
        drivers.append(f"{row['overtime_hours_30d']:.0f} overtime hrs/30d")
    if row["history_long_haul_count"] >= 4:
        drivers.append("repeated long-haul history")
    if row["skill_gap"] > 0.34:
        drivers.append("skill mismatch frustration")
    if row["crew_mismatch"] > 0.38:
        drivers.append("low project-team continuity")
    if not drivers:
        drivers.append("manageable current burden")
    return "; ".join(drivers)
