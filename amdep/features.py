"""Feature builders for the AmDep Brain Layer."""

from __future__ import annotations

import numpy as np
import pandas as pd

from amdep.utils import pipe_list, safe_pct, travel_minutes


PAIR_FEATURE_COLUMNS = [
    "commute_minutes",
    "skill_match_score",
    "certification_match_score",
    "region_match",
    "fatigue_base",
    "reliability_inverse",
    "overtime_hours_30d",
    "history_long_haul_count",
    "weekend_late_assignments_30d",
    "crew_affinity",
    "job_urgency",
    "weather_risk",
    "schedule_volatility",
    "inspection_need",
    "required_headcount",
    "is_supervisor",
]


def skill_match_score(worker_skills: list[str], required_skills: list[str]) -> float:
    if not required_skills:
        return 1.0
    if not worker_skills:
        return 0.0
    overlap = len(set(worker_skills).intersection(required_skills))
    return safe_pct(overlap, len(set(required_skills)))


def certification_match_score(worker_certs: list[str], required_certs: list[str]) -> float:
    if not required_certs:
        return 1.0
    if not worker_certs:
        return 0.0
    overlap = len(set(worker_certs).intersection(required_certs))
    return safe_pct(overlap, len(set(required_certs)))


def has_required_certifications(worker_certs: list[str], required_certs: list[str]) -> bool:
    return set(required_certs).issubset(set(worker_certs))


def build_pair_features(workers: pd.DataFrame, jobs: pd.DataFrame) -> pd.DataFrame:
    """Create personnel-job feature rows for optimization and synthetic ML."""
    rows: list[dict[str, object]] = []
    worker_records = workers.to_dict("records")
    job_records = jobs.to_dict("records")
    for worker in worker_records:
        worker_skills = pipe_list(worker.get("skills"))
        worker_certs = pipe_list(worker.get("certifications"))
        for job in job_records:
            required_skills = pipe_list(job.get("required_skills"))
            required_certs = pipe_list(job.get("required_certifications"))
            commute = travel_minutes(
                float(worker["home_lat"]),
                float(worker["home_lon"]),
                float(job["lat"]),
                float(job["lon"]),
            )
            skill_score = skill_match_score(worker_skills, required_skills)
            cert_score = certification_match_score(worker_certs, required_certs)
            rows.append(
                {
                    "personnel_id": worker["personnel_id"],
                    "jobsite_id": job["jobsite_id"],
                    "supervisor_id": worker.get("supervisor_id", ""),
                    "crew_id": worker.get("crew_id", ""),
                    "home_region": worker.get("home_region", ""),
                    "job_region": job.get("region", ""),
                    "commute_minutes": round(commute, 2),
                    "skill_match_score": round(skill_score, 4),
                    "certification_match_score": round(cert_score, 4),
                    "has_required_certifications": has_required_certifications(worker_certs, required_certs),
                    "region_match": int(worker.get("home_region") == job.get("region")),
                    "fatigue_base": float(worker.get("fatigue_base", 0.25)),
                    "reliability_inverse": 1.0 - float(worker.get("reliability_score", 0.90)),
                    "overtime_hours_30d": float(worker.get("overtime_hours_30d", 0.0)),
                    "history_long_haul_count": float(worker.get("history_long_haul_count", 0.0)),
                    "weekend_late_assignments_30d": float(worker.get("weekend_late_assignments_30d", 0.0)),
                    "crew_affinity": float(worker.get("crew_affinity", 0.72)),
                    "job_urgency": float(job.get("urgency", 3)),
                    "weather_risk": float(job.get("weather_risk", 0.2)),
                    "schedule_volatility": float(job.get("schedule_volatility", 0.2)),
                    "inspection_need": float(job.get("inspection_need", 0.0)),
                    "required_headcount": float(job.get("required_headcount", 1)),
                    "is_supervisor": int(bool(worker.get("is_supervisor", False))),
                    "robot_ready_job": int(bool(job.get("can_accept_robotics", False))),
                }
            )
    return pd.DataFrame(rows)


def build_synthetic_labels(features: pd.DataFrame, seed: int = 1776) -> pd.DataFrame:
    """Create transparent synthetic targets for demo-only ML models."""
    rng = np.random.default_rng(seed)
    frame = features.copy()
    commute_norm = np.clip(frame["commute_minutes"] / 120.0, 0, 1.5)
    overtime_norm = np.clip(frame["overtime_hours_30d"] / 36.0, 0, 1.2)
    long_haul_norm = np.clip(frame["history_long_haul_count"] / 8.0, 0, 1.2)
    skill_gap = 1.0 - frame["skill_match_score"]
    cert_gap = 1.0 - frame["certification_match_score"]
    reliability_gap = frame["reliability_inverse"]

    attrition_logit = -3.2 + 2.0 * commute_norm + 1.6 * frame["fatigue_base"] + 1.1 * overtime_norm + 0.7 * long_haul_norm + 0.8 * skill_gap
    delay_logit = -2.5 + 1.3 * skill_gap + 1.8 * cert_gap + 0.75 * frame["weather_risk"] + 1.2 * frame["schedule_volatility"] + 0.18 * frame["job_urgency"]
    no_show_logit = -3.4 + 1.4 * commute_norm + 1.2 * reliability_gap + 0.9 * overtime_norm + 0.8 * frame["fatigue_base"]
    compatible_logit = 1.9 + 1.2 * frame["region_match"] + 1.4 * frame["skill_match_score"] + 1.0 * frame["crew_affinity"] - 1.1 * commute_norm - 0.7 * frame["schedule_volatility"]
    robotics_logit = -2.0 + 2.2 * frame["robot_ready_job"] + 1.7 * frame["inspection_need"] + 0.55 * frame["job_urgency"] - 0.4 * frame["weather_risk"]

    def sample(logit: pd.Series) -> np.ndarray:
        probability = 1.0 / (1.0 + np.exp(-logit))
        return (rng.random(len(probability)) < probability).astype(int)

    frame["attrition_risk_label"] = sample(attrition_logit)
    frame["delay_risk_label"] = sample(delay_logit)
    frame["no_show_risk_label"] = sample(no_show_logit)
    frame["crew_compatible_label"] = sample(compatible_logit)
    frame["robotics_suitable_label"] = sample(robotics_logit)
    return frame

