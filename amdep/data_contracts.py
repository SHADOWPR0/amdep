"""CSV contracts for the algorithm-first AmDep dispatch audit."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


REQUIRED_COLUMNS = {
    "workers": {
        "personnel_id",
        "home_region",
        "home_lat",
        "home_lon",
        "skills",
        "certifications",
    },
    "jobsites": {
        "jobsite_id",
        "name",
        "region",
        "lat",
        "lon",
        "required_headcount",
        "required_skills",
        "required_certifications",
    },
    "assignments": {
        "personnel_id",
        "jobsite_id",
    },
    "assets": {
        "asset_id",
        "asset_kind",
        "asset_type",
        "home_region",
        "available",
    },
}


OPTIONAL_OUTCOME_COLUMNS = {
    "late_arrival",
    "overtime_event",
    "project_delay",
    "callback_rework_event",
    "productivity_shortfall",
    "safety_incident_proxy",
    "no_show",
    "quit_within_90_days",
    "actual_start",
    "actual_end",
    "actual_duration_hours",
    "scheduled_start",
    "scheduled_end",
    "dispatcher_override",
    "override_reason",
}


@dataclass
class ValidationIssue:
    dataset: str
    severity: str
    field: str
    message: str


@dataclass
class ValidationReport:
    issues: list[ValidationIssue]

    @property
    def ok(self) -> bool:
        return not any(issue.severity == "error" for issue in self.issues)

    def to_frame(self) -> pd.DataFrame:
        if not self.issues:
            return pd.DataFrame([{"dataset": "all", "severity": "ok", "field": "", "message": "Schema validation passed."}])
        return pd.DataFrame([issue.__dict__ for issue in self.issues])


def validate_frames(frames: dict[str, pd.DataFrame]) -> ValidationReport:
    """Validate a partial customer bundle without requiring perfect data."""
    issues: list[ValidationIssue] = []
    for dataset, required in REQUIRED_COLUMNS.items():
        if dataset not in frames:
            if dataset in {"workers", "jobsites"}:
                issues.append(ValidationIssue(dataset, "error", "", f"Missing required {dataset} CSV."))
            continue
        frame = frames[dataset]
        missing = sorted(required - set(frame.columns))
        for column in missing:
            issues.append(ValidationIssue(dataset, "error", column, "Required column is missing."))
        if frame.empty:
            issues.append(ValidationIssue(dataset, "error", "", "CSV has no rows."))

    if "workers" in frames and "personnel_id" in frames["workers"]:
        duplicates = frames["workers"]["personnel_id"].duplicated().sum()
        if duplicates:
            issues.append(ValidationIssue("workers", "error", "personnel_id", f"{duplicates} duplicate personnel ids."))
    if "jobsites" in frames and "jobsite_id" in frames["jobsites"]:
        duplicates = frames["jobsites"]["jobsite_id"].duplicated().sum()
        if duplicates:
            issues.append(ValidationIssue("jobsites", "error", "jobsite_id", f"{duplicates} duplicate jobsite ids."))

    for dataset, lat_col, lon_col in [("workers", "home_lat", "home_lon"), ("jobsites", "lat", "lon")]:
        if dataset not in frames:
            continue
        frame = frames[dataset]
        for column in [lat_col, lon_col]:
            if column in frame:
                missing = pd.to_numeric(frame[column], errors="coerce").isna().sum()
                if missing:
                    issues.append(ValidationIssue(dataset, "warning", column, f"{missing} rows have missing/non-numeric coordinates."))

    if "assignments" in frames:
        assignments = frames["assignments"]
        if "workers" in frames and "personnel_id" in assignments:
            unknown = ~assignments["personnel_id"].isin(frames["workers"]["personnel_id"])
            if unknown.any():
                issues.append(ValidationIssue("assignments", "warning", "personnel_id", f"{int(unknown.sum())} assignments reference unknown personnel."))
        if "jobsites" in frames and "jobsite_id" in assignments:
            unknown = ~assignments["jobsite_id"].isin(frames["jobsites"]["jobsite_id"])
            if unknown.any():
                issues.append(ValidationIssue("assignments", "warning", "jobsite_id", f"{int(unknown.sum())} assignments reference unknown jobsites."))
        found_outcomes = OPTIONAL_OUTCOME_COLUMNS.intersection(assignments.columns)
        if not found_outcomes:
            issues.append(ValidationIssue("assignments", "warning", "outcomes", "No outcome columns found; calibration will use synthetic risk scoring."))

    return ValidationReport(issues)

