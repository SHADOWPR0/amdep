"""Customer CSV ingestion and normalization for dispatch audits."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from amdep.data_contracts import validate_frames
from amdep.features import build_pair_features


WORKER_DEFAULTS = {
    "name": "",
    "role": "project staff",
    "is_supervisor": False,
    "home_city": "",
    "skills": "",
    "certifications": "",
    "crew_id": "",
    "supervisor_id": "",
    "hourly_rate": 55.0,
    "fatigue_base": 0.25,
    "reliability_score": 0.90,
    "overtime_hours_30d": 0.0,
    "history_long_haul_count": 0,
    "weekend_late_assignments_30d": 0,
    "crew_affinity": 0.72,
    "preferred_regions": "",
    "max_reports": 10,
    "active": True,
}

JOB_DEFAULTS = {
    "city": "",
    "project_type": "commercial project",
    "phase": "production",
    "urgency": 3,
    "required_equipment": "",
    "shift_start": "07:00",
    "shift_end": "15:30",
    "weather_risk": 0.20,
    "schedule_volatility": 0.25,
    "can_accept_robotics": False,
    "inspection_need": 0.25,
    "change_order_exposure": 0.0,
    "status": "ready",
}

ASSET_DEFAULTS = {
    "capability": "",
    "hourly_cost": 0.0,
    "cost_per_day": 0.0,
    "available": True,
    "robot_ready": False,
}

ASSET_COLUMNS = [
    "asset_id",
    "asset_kind",
    "asset_type",
    "home_region",
    "capability",
    "hourly_cost",
    "cost_per_day",
    "available",
    "robot_ready",
]


def load_customer_bundle(
    *,
    workers_path: Path,
    jobsites_path: Path,
    assignments_path: Path | None = None,
    assets_path: Path | None = None,
) -> dict[str, pd.DataFrame]:
    """Load the customer CSV bundle expected by the audit runner."""
    frames = {
        "workers": pd.read_csv(workers_path),
        "jobsites": pd.read_csv(jobsites_path),
    }
    if assignments_path:
        frames["assignments"] = pd.read_csv(assignments_path)
    if assets_path:
        frames["assets"] = pd.read_csv(assets_path)
    return frames


def normalize_bundle(frames: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Normalize imperfect CSVs into the internal audit schema."""
    validation = validate_frames(frames)
    if not validation.ok:
        errors = validation.to_frame()
        errors = errors.loc[errors["severity"] == "error"]
        raise ValueError("CSV validation failed:\n" + errors.to_string(index=False))

    workers = _apply_defaults(frames["workers"], WORKER_DEFAULTS)
    jobs = _apply_defaults(frames["jobsites"], JOB_DEFAULTS)
    assets = _apply_defaults(frames.get("assets", pd.DataFrame()), ASSET_DEFAULTS)
    if assets.empty:
        assets = pd.DataFrame(columns=ASSET_COLUMNS)
    assignments = frames.get("assignments")

    workers["personnel_id"] = workers["personnel_id"].astype(str)
    jobs["jobsite_id"] = jobs["jobsite_id"].astype(str)
    workers["name"] = workers["name"].where(workers["name"].astype(str).str.len() > 0, workers["personnel_id"])
    workers["home_city"] = workers["home_city"].where(workers["home_city"].astype(str).str.len() > 0, workers["home_region"])
    jobs["city"] = jobs["city"].where(jobs["city"].astype(str).str.len() > 0, jobs["region"])
    workers["active"] = workers["active"].fillna(True).astype(bool)
    workers["is_supervisor"] = workers["is_supervisor"].fillna(False).astype(bool)

    normalized = {"workers": workers, "jobsites": jobs, "assets": assets}
    if assignments is not None:
        normalized["assignments"] = enrich_assignments(assignments, workers, jobs)
    return normalized


def enrich_assignments(assignments: pd.DataFrame, workers: pd.DataFrame, jobs: pd.DataFrame) -> pd.DataFrame:
    """Add commute, fit, names, and route fields to uploaded historical assignments."""
    frame = assignments.copy()
    frame["personnel_id"] = frame["personnel_id"].astype(str)
    frame["jobsite_id"] = frame["jobsite_id"].astype(str)
    pairs = build_pair_features(workers, jobs)
    pair_enrich = pairs[
        [
            "personnel_id",
            "jobsite_id",
            "commute_minutes",
            "skill_match_score",
            "certification_match_score",
            "home_region",
            "job_region",
            "job_urgency",
        ]
    ].rename(columns={"job_urgency": "pair_job_urgency"})
    frame = frame.merge(pair_enrich, on=["personnel_id", "jobsite_id"], how="left", suffixes=("", "_pair"))
    for column in ["commute_minutes", "skill_match_score", "certification_match_score", "home_region", "job_region"]:
        pair_column = f"{column}_pair"
        if pair_column in frame.columns:
            frame[column] = frame[column].fillna(frame[pair_column]) if column in frame else frame[pair_column]
    frame["job_urgency"] = frame.get("job_urgency", frame["pair_job_urgency"]).fillna(frame["pair_job_urgency"]).fillna(3).astype(int)
    if "assignment_id" not in frame.columns:
        frame["assignment_id"] = [f"CUST-{idx + 1:04d}" for idx in range(len(frame))]
    frame["assignment_source"] = frame.get("assignment_source", "customer_baseline")
    frame["certification_match"] = pd.to_numeric(frame["certification_match_score"], errors="coerce").fillna(0) >= 1
    frame["total_cost_score"] = pd.to_numeric(frame["commute_minutes"], errors="coerce").fillna(0)
    worker_names = workers.set_index("personnel_id")["name"].to_dict()
    job_names = jobs.set_index("jobsite_id")["name"].to_dict()
    frame["worker_name"] = frame["personnel_id"].map(worker_names)
    frame["job_name"] = frame["jobsite_id"].map(job_names)
    return frame


def _apply_defaults(frame: pd.DataFrame, defaults: dict[str, object]) -> pd.DataFrame:
    result = frame.copy()
    for column, default in defaults.items():
        if column not in result.columns:
            result[column] = default
    return result
