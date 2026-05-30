"""Typed field ontology for American Deployment."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class Region(BaseModel):
    region_id: str
    name: str
    city_label: str
    center_lat: float
    center_lon: float


class Skill(BaseModel):
    name: str
    category: str = "field"


class Certification(BaseModel):
    name: str
    is_hard_constraint: bool = True


class Personnel(BaseModel):
    personnel_id: str
    name: str
    role: str
    home_region: str
    home_lat: float
    home_lon: float
    skills: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    crew_id: str | None = None
    supervisor_id: str | None = None
    hourly_rate: float = 55.0
    fatigue_base: float = 0.25
    reliability_score: float = 0.9
    is_supervisor: bool = False


class Supervisor(Personnel):
    is_supervisor: bool = True
    max_reports: int = 10


class Crew(BaseModel):
    crew_id: str
    supervisor_id: str
    home_region: str
    members: list[str] = Field(default_factory=list)
    cohesion_score: float = 0.75


class Jobsite(BaseModel):
    jobsite_id: str
    name: str
    region: str
    city: str
    lat: float
    lon: float
    project_type: str
    phase: str
    urgency: int = Field(ge=1, le=5)
    required_headcount: int = Field(ge=1)
    required_skills: list[str] = Field(default_factory=list)
    required_certifications: list[str] = Field(default_factory=list)
    required_equipment: list[str] = Field(default_factory=list)
    shift_start: str = "07:00"
    shift_end: str = "15:30"
    weather_risk: float = Field(ge=0, le=1)
    schedule_volatility: float = Field(ge=0, le=1)
    can_accept_robotics: bool = False
    inspection_need: float = Field(default=0.0, ge=0, le=1)


class Equipment(BaseModel):
    asset_id: str
    asset_kind: Literal["vehicle", "equipment"]
    asset_type: str
    home_region: str
    capability: str
    hourly_cost: float = 22.0
    available: bool = True


class RoboticAsset(BaseModel):
    asset_id: str
    asset_kind: Literal["robotic"] = "robotic"
    robot_type: str
    home_region: str
    capability: str
    cost_per_day: float = 300.0
    available: bool = True


class Assignment(BaseModel):
    assignment_id: str
    deployment_date: date
    personnel_id: str
    jobsite_id: str
    supervisor_id: str | None = None
    crew_id: str | None = None
    assignment_source: Literal["naive", "optimized"]
    commute_minutes: float
    skill_match_score: float
    certification_match: bool
    total_cost_score: float = 0.0


class DeploymentDay(BaseModel):
    deployment_date: date
    assignments: list[Assignment] = Field(default_factory=list)


class Constraint(BaseModel):
    name: str
    constraint_type: Literal["hard", "soft"]
    description: str
    active: bool = True


class OptimizationResult(BaseModel):
    status: str
    objective_value: float
    assignments_created: int
    unfilled_slots: int
    solver_seconds: float
    notes: list[str] = Field(default_factory=list)


ONTOLOGY_RELATIONSHIPS = [
    "Personnel lives_in Region",
    "Personnel has_skill Skill",
    "Personnel has_cert Certification",
    "Personnel assigned_to Jobsite",
    "Personnel reports_to Supervisor",
    "Personnel compatible_with Crew",
    "Supervisor manages Personnel",
    "Jobsite requires Skill",
    "Jobsite requires Certification",
    "Jobsite requires Equipment",
    "Jobsite can_accept RoboticAsset",
    "Equipment assigned_to Jobsite",
    "Vehicle assigned_to Personnel/Crew",
    "Assignment creates commute burden",
    "Assignment creates fatigue risk",
    "Assignment affects retention risk",
    "Assignment affects project throughput",
]

