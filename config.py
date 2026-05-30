"""Configuration defaults for American Deployment."""

from __future__ import annotations

APP_NAME = "AMERICAN DEPLOYMENT"
SHORT_NAME = "AmDep"
TAGLINE = "Elite project-staff deployment intelligence for commercial builders."
DEFAULT_SEED = 1776

BASE_COLORS = {
    "ink": "#071018",
    "navy": "#0B1826",
    "panel": "#122131",
    "panel_alt": "#172A3A",
    "slate": "#253849",
    "bone": "#F3EDE0",
    "muted": "#9BA8A7",
    "teal": "#2BA6A0",
    "green": "#55B86E",
    "gold": "#C7A353",
    "orange": "#E56A32",
    "red": "#D35B54",
}

REGION_CLUSTERS = {
    "Naples": {"lat": 26.1420, "lon": -81.7948, "city": "Naples"},
    "Bonita-Estero": {"lat": 26.3398, "lon": -81.7787, "city": "Bonita Springs / Estero"},
    "Fort Myers": {"lat": 26.6406, "lon": -81.8723, "city": "Fort Myers"},
    "Cape Coral": {"lat": 26.5629, "lon": -81.9495, "city": "Cape Coral"},
    "Lehigh-Immokalee": {"lat": 26.6253, "lon": -81.5767, "city": "Lehigh Acres / Immokalee"},
    "Sarasota-Punta Gorda": {"lat": 27.1270, "lon": -82.0200, "city": "Punta Gorda / Sarasota"},
}

SKILL_TYPES = [
    "project executive",
    "senior project manager",
    "project manager",
    "assistant project manager",
    "project superintendent",
    "assistant superintendent",
    "project engineer",
    "safety manager",
    "quality manager",
    "MEP coordinator",
    "scheduler",
    "closeout manager",
    "self-perform lead",
]

CERTIFICATION_TYPES = [
    "OSHA 30",
    "First Aid/CPR",
    "ICRA awareness",
    "LEED AP",
    "stormwater inspector",
    "fall protection",
    "quality management",
    "safety trained supervisor",
    "MEP coordination",
    "permit coordination",
    "closeout documentation",
]

PROJECT_TYPES = [
    "commercial interiors",
    "healthcare",
    "hospitality",
    "multifamily",
    "education",
    "municipal",
    "office renovation",
    "industrial",
    "clubhouse/amenity",
    "adaptive reuse",
]

PROJECT_PHASES = [
    "preconstruction handoff",
    "mobilization",
    "foundations",
    "structure",
    "MEP rough-in",
    "interiors",
    "inspection readiness",
    "closeout",
    "turnover",
    "warranty",
]

EQUIPMENT_TYPES = [
    "pickup truck",
    "site tablet kit",
    "laser scanner",
    "progress camera kit",
    "safety trailer",
    "temporary office kit",
    "QA/QC inspection kit",
    "punchlist tablet set",
    "layout station",
    "document control kit",
]

ROBOTIC_ASSET_TYPES = [
    "progress capture drone",
    "autonomous layout rover",
    "inspection drone",
    "laser scan rover",
    "site camera tower",
    "concrete scan robot",
    "thermal envelope scanner",
    "turnover capture unit",
]

DEFAULT_WEIGHTS = {
    "commute_reduction": 1.0,
    "skill_fit": 1.0,
    "certification_strictness": 1.0,
    "supervisor_balance": 0.8,
    "retention_protection": 0.9,
    "crew_cohesion": 0.7,
    "overtime_reduction": 0.8,
    "robotics_utilization": 0.5,
    "job_urgency": 0.8,
}

DEFAULT_ROI_ASSUMPTIONS = {
    "loaded_labor_cost_per_hour": 55.0,
    "vehicle_cost_per_hour": 22.0,
    "workdays_per_year": 250,
    "impact_realization_factor": 1.0,
    "replacement_cost_per_lost_employee": 18_000.0,
    "supervisor_cost_per_hour": 85.0,
    "robotic_asset_cost_per_day": 300.0,
    "inspection_rework_cost": 2_500.0,
    "attrition_reduction_sensitivity": 0.25,
}
