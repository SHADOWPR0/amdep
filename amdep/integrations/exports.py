"""Export optimized recommendations for contractor software stacks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

from amdep.integrations.known_stacks import KNOWN_STACKS

if TYPE_CHECKING:  # pragma: no cover
    from amdep.dispatch_gym import DispatchAuditResult


def export_integration_bundle(result: "DispatchAuditResult", output_dir: Path) -> list[Path]:
    """Write adapter-ready files for common contractor systems.

    These exports are not blind write-backs. They are review queues and payload
    drafts. A production connector should preserve operations approval and
    audit logs before changing any system of record.
    """
    integration_dir = output_dir / "integrations"
    integration_dir.mkdir(parents=True, exist_ok=True)
    paths = [
        _write_manifest(integration_dir),
        _write_generic_recommendations(result, integration_dir),
        _write_procore_resource_planning(result, integration_dir),
        _write_servicetitan_recommendations(result, integration_dir),
        _write_hcss_heavyjob_recommendations(result, integration_dir),
        _write_sage_recommendations(result, integration_dir),
        _write_autodesk_acc_recommendations(result, integration_dir),
        _write_acculynx_recommendations(result, integration_dir),
        _write_foundry_objects(result, integration_dir),
    ]
    return paths


def _base_recommendations(result: "DispatchAuditResult") -> pd.DataFrame:
    optimized = result.optimized_assignments.copy()
    if optimized.empty:
        return pd.DataFrame()
    waste_lookup = {}
    if not result.waste_findings.empty:
        waste_lookup = (
            result.waste_findings.drop_duplicates("jobsite_id")
            .set_index("jobsite_id")["reason"]
            .to_dict()
        )
    optimized["recommendation_id"] = [f"REC-{idx + 1:05d}" for idx in range(len(optimized))]
    optimized["recommended_action"] = "review_assignment"
    optimized["approval_status"] = "pending_operations_review"
    optimized["reason"] = optimized["jobsite_id"].map(waste_lookup).fillna(
        "Optimizer selected this assignment under skills, certification, geography, burden, urgency, and capacity constraints."
    )
    optimized["daily_route_minutes"] = optimized["commute_minutes"] * 2.0
    optimized["estimated_daily_route_cost"] = optimized["daily_route_minutes"] / 60.0 * 77.0
    return optimized


def _write_manifest(output_dir: Path) -> Path:
    path = output_dir / "adapter_manifest.json"
    payload = {
        "product": "American Deployment Community Edition",
        "purpose": "Dispatch optimization recommendation exports for customer-approved integration work.",
        "writeback_policy": "review_first_no_blind_system_mutation",
        "known_stacks": [manifest.to_dict() for manifest in KNOWN_STACKS.values()],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def _write_generic_recommendations(result: "DispatchAuditResult", output_dir: Path) -> Path:
    path = output_dir / "recommendations_generic.csv"
    frame = _base_recommendations(result)
    columns = [
        "recommendation_id",
        "approval_status",
        "recommended_action",
        "personnel_id",
        "worker_name",
        "jobsite_id",
        "job_name",
        "home_region",
        "job_region",
        "commute_minutes",
        "daily_route_minutes",
        "estimated_daily_route_cost",
        "skill_match_score",
        "certification_match_score",
        "attrition_risk_cost",
        "delay_risk_cost",
        "no_show_risk_cost",
        "crew_incompatibility_cost",
        "robotics_suitability_reward",
        "reason",
    ]
    _write_columns(frame, path, columns)
    return path


def _write_procore_resource_planning(result: "DispatchAuditResult", output_dir: Path) -> Path:
    path = output_dir / "procore_resource_planning_recommendations.csv"
    frame = _base_recommendations(result)
    export = pd.DataFrame()
    if not frame.empty:
        export = pd.DataFrame(
            {
                "Project": frame["jobsite_id"],
                "Project Name": frame["job_name"],
                "Person": frame["worker_name"],
                "Employee ID": frame["personnel_id"],
                "Start Date": frame.get("deployment_date", ""),
                "End Date": frame.get("deployment_date", ""),
                "Start Time": "07:00",
                "End Time": "15:30",
                "Percent Allocated": 100,
                "Status": "recommended",
                "Overtime": False,
                "Tags": "AmDep optimized;operations review",
                "AmDep Recommendation ID": frame["recommendation_id"],
                "AmDep Reason": frame["reason"],
            }
        )
    export.to_csv(path, index=False)
    return path


def _write_servicetitan_recommendations(result: "DispatchAuditResult", output_dir: Path) -> Path:
    path = output_dir / "servicetitan_appointment_recommendations.csv"
    frame = _base_recommendations(result)
    export = pd.DataFrame()
    if not frame.empty:
        export = pd.DataFrame(
            {
                "recommendation_id": frame["recommendation_id"],
                "job_id": frame["jobsite_id"],
                "appointment_id": "",
                "technician_id": frame["personnel_id"],
                "technician_name": frame["worker_name"],
                "recommended_action": "assign_or_reassign_technician",
                "dispatch_date": frame.get("deployment_date", ""),
                "reason": frame["reason"],
                "review_status": "pending_operations_review",
            }
        )
    export.to_csv(path, index=False)
    return path


def _write_hcss_heavyjob_recommendations(result: "DispatchAuditResult", output_dir: Path) -> Path:
    path = output_dir / "hcss_heavyjob_crew_equipment_recommendations.csv"
    frame = _base_recommendations(result)
    export = pd.DataFrame()
    if not frame.empty:
        export = pd.DataFrame(
            {
                "business_unit": "",
                "job_code": frame["jobsite_id"],
                "job_name": frame["job_name"],
                "foreman_id": frame.get("supervisor_id", ""),
                "employee_id": frame["personnel_id"],
                "crew_id": frame.get("crew_id", ""),
                "recommended_date": frame.get("deployment_date", ""),
                "recommendation_id": frame["recommendation_id"],
                "reason": frame["reason"],
            }
        )
    export.to_csv(path, index=False)
    return path


def _write_sage_recommendations(result: "DispatchAuditResult", output_dir: Path) -> Path:
    path = output_dir / "sage_construction_recommendations.csv"
    frame = _base_recommendations(result)
    export = pd.DataFrame()
    if not frame.empty:
        export = pd.DataFrame(
            {
                "PROJECTID": frame["jobsite_id"],
                "EMPLOYEEID": frame["personnel_id"],
                "ENTRYDATE": frame.get("deployment_date", ""),
                "TASKID": "",
                "COSTTYPEID": "",
                "RECOMMENDED_ACTION": "review_assignment",
                "AMDEP_RECOMMENDATION_ID": frame["recommendation_id"],
                "AMDEP_REASON": frame["reason"],
            }
        )
    export.to_csv(path, index=False)
    return path


def _write_autodesk_acc_recommendations(result: "DispatchAuditResult", output_dir: Path) -> Path:
    path = output_dir / "autodesk_construction_cloud_recommendations.csv"
    frame = _base_recommendations(result)
    export = pd.DataFrame()
    if not frame.empty:
        export = pd.DataFrame(
            {
                "projectId": frame["jobsite_id"],
                "projectName": frame["job_name"],
                "assigneeExternalId": frame["personnel_id"],
                "assigneeName": frame["worker_name"],
                "suggestedActionType": "deployment_review",
                "recommendationId": frame["recommendation_id"],
                "reason": frame["reason"],
                "reviewStatus": "pending_operations_review",
            }
        )
    export.to_csv(path, index=False)
    return path


def _write_acculynx_recommendations(result: "DispatchAuditResult", output_dir: Path) -> Path:
    path = output_dir / "acculynx_roofing_recommendations.csv"
    frame = _base_recommendations(result)
    export = pd.DataFrame()
    if not frame.empty:
        export = pd.DataFrame(
            {
                "jobId": frame["jobsite_id"],
                "jobName": frame["job_name"],
                "productionOwnerOrCrewId": frame.get("crew_id", ""),
                "recommendedPersonnelId": frame["personnel_id"],
                "recommendedPersonnelName": frame["worker_name"],
                "recommendationId": frame["recommendation_id"],
                "zapierAction": "create_review_task",
                "reason": frame["reason"],
            }
        )
    export.to_csv(path, index=False)
    return path


def _write_foundry_objects(result: "DispatchAuditResult", output_dir: Path) -> Path:
    path = output_dir / "foundry_object_imports.json"
    recommendations = _base_recommendations(result)
    payload = {
        "object_sets": {
            "Personnel": _records(result.workers, limit=500),
            "Jobsite": _records(result.jobs, limit=500),
            "OptimizedAssignment": _records(result.optimized_assignments, limit=1000),
            "DeploymentRecommendation": _records(recommendations, limit=1000),
            "WasteFinding": _records(result.waste_findings, limit=500),
        },
        "action_types": [
            "approve_recommendation",
            "reject_recommendation",
            "override_assignment",
            "mark_operationally_infeasible",
        ],
    }
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return path


def _write_columns(frame: pd.DataFrame, path: Path, columns: list[str]) -> None:
    if frame.empty:
        pd.DataFrame(columns=columns).to_csv(path, index=False)
        return
    for column in columns:
        if column not in frame.columns:
            frame[column] = ""
    frame[columns].to_csv(path, index=False)


def _records(frame: pd.DataFrame, *, limit: int) -> list[dict[str, object]]:
    if frame.empty:
        return []
    clean = frame.head(limit).where(pd.notna(frame.head(limit)), None)
    return clean.to_dict("records")
