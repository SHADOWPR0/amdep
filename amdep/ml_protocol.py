"""Customer-data ML protocol reference for AmDep."""

from __future__ import annotations


TARGETS = [
    "quit_within_90_days",
    "late_arrival",
    "overtime_event",
    "project_delay",
    "callback_rework_event",
    "productivity_shortfall",
    "safety_incident_proxy",
    "asset_idle_time",
    "robotics_deployment_success",
]

FEATURE_FAMILIES = {
    "commute": ["one_way_minutes", "round_trip_minutes", "distance_percentile", "repeated_long_haul_count"],
    "region": ["home_region", "job_region", "region_match", "service_area_density"],
    "skill_cert": ["skill_overlap", "certification_coverage", "scarce_cert_flag"],
    "supervisor": ["span_of_control", "geographic_dispersion", "prior_pairing_count"],
    "crew": ["crew_history", "cohesion_score", "crew_fragmentation"],
    "job": ["project_phase", "urgency", "weather_risk", "schedule_volatility"],
    "workload": ["overtime_30d", "weekend_assignments", "fatigue_sequence"],
    "assets": ["equipment_availability", "robotics_readiness", "asset_idle_time"],
}

MODEL_CANDIDATES = [
    "logistic_regression_baseline",
    "random_forest",
    "hist_gradient_boosting",
    "xgboost_optional",
    "calibrated_classifiers",
    "survival_analysis_later",
    "contextual_bandits_later",
    "reinforcement_learning_later",
]


def protocol_steps() -> list[str]:
    return [
        "Use time-based train/test splits so the model predicts future operations from past operations.",
        "Prevent leakage by excluding post-assignment outcomes from pre-assignment features.",
        "Calibrate probabilities before showing them to operations reviewers.",
        "Track feature importance and prepare SHAP-compatible explanations.",
        "Monitor drift by region, supervisor, season, and project type.",
        "Log human overrides, stated override reasons, and eventual outcomes.",
    ]
