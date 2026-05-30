"""Robotics readiness and future fleet deployment scoring."""

from __future__ import annotations

import pandas as pd

from amdep.utils import travel_minutes


def robotics_readiness(jobs: pd.DataFrame, assets: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]]:
    robots = assets.loc[assets["asset_kind"] == "robotic"].copy()
    if robots.empty:
        return pd.DataFrame(), {"available_robots": 0, "robotics_utilization_pct": 0.0, "avoidable_inspection_trips": 0}

    candidates = jobs.copy()
    candidates["robotics_readiness_score"] = candidates.apply(_job_robotics_score, axis=1)
    candidates = candidates.sort_values(["robotics_readiness_score", "urgency"], ascending=False)
    rows = []
    used_assets: set[str] = set()
    for _, job in candidates.iterrows():
        if job["robotics_readiness_score"] < 45:
            continue
        available = robots.loc[~robots["asset_id"].isin(used_assets) & robots["available"].astype(bool)].copy()
        if available.empty:
            break
        available["travel_minutes"] = available.apply(
            lambda asset: _asset_travel_proxy(asset, job),
            axis=1,
        )
        robot = available.sort_values(["travel_minutes", "cost_per_day"]).iloc[0]
        used_assets.add(str(robot["asset_id"]))
        avoided_trips = 2 if float(job["inspection_need"]) > 0.72 else 1
        rows.append(
            {
                "jobsite_id": job["jobsite_id"],
                "job_name": job["name"],
                "region": job["region"],
                "robotic_asset": robot["asset_id"],
                "robot_type": robot["asset_type"],
                "readiness_score": round(float(job["robotics_readiness_score"]), 1),
                "inspection_need": job["inspection_need"],
                "estimated_avoidable_trips": avoided_trips,
                "estimated_travel_minutes_removed": round(float(available["travel_minutes"].min() * avoided_trips), 1),
                "operator_note": _robotics_note(job),
            }
        )

    plan = pd.DataFrame(rows)
    summary = {
        "available_robots": int(robots["available"].sum()),
        "robotics_candidates": int((candidates["robotics_readiness_score"] >= 45).sum()),
        "deployed_robots": int(len(plan)),
        "robotics_utilization_pct": float(len(plan) / max(1, int(robots["available"].sum()))),
        "avoidable_inspection_trips": int(plan["estimated_avoidable_trips"].sum()) if not plan.empty else 0,
        "travel_minutes_removed": float(plan["estimated_travel_minutes_removed"].sum()) if not plan.empty else 0.0,
    }
    return plan, summary


def _job_robotics_score(job: pd.Series) -> float:
    score = 0.0
    score += 34.0 if bool(job.get("can_accept_robotics", False)) else 0.0
    score += float(job.get("inspection_need", 0.0)) * 30.0
    score += float(job.get("urgency", 3)) * 4.5
    score += float(job.get("schedule_volatility", 0.0)) * 8.0
    if str(job.get("phase", "")).lower() in {"inspection readiness", "closeout", "turnover", "warranty"}:
        score += 10.0
    if str(job.get("project_type", "")).lower() in {"healthcare", "hospitality", "commercial interiors", "office renovation", "adaptive reuse"}:
        score += 7.0
    if float(job.get("weather_risk", 0.0)) > 0.70:
        score -= 14.0
    return max(0.0, min(score, 100.0))


def _asset_travel_proxy(asset: pd.Series, job: pd.Series) -> float:
    region_distance_proxy = 12.0 if asset["home_region"] == job["region"] else 48.0
    return region_distance_proxy + travel_minutes(float(job["lat"]), float(job["lon"]), float(job["lat"]) + 0.02, float(job["lon"]) + 0.02)


def _robotics_note(job: pd.Series) -> str:
    if str(job.get("phase")) == "inspection readiness":
        return "Inspection readiness: capture support can reduce avoidable superintendent site trips."
    if str(job.get("phase")) in {"closeout", "turnover"}:
        return "Closeout proof burden: capture unit can support punch, owner walk, and turnover documentation."
    return "Capture-ready project: use future fleet layer for site verification."
