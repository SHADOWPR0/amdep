"""Deterministic synthetic commercial GC staff-deployment data for AmDep."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from config import (
    CERTIFICATION_TYPES,
    DEFAULT_SEED,
    EQUIPMENT_TYPES,
    PROJECT_PHASES,
    PROJECT_TYPES,
    REGION_CLUSTERS,
    ROBOTIC_ASSET_TYPES,
    SKILL_TYPES,
)
from amdep.utils import encode_list, repo_root

FIRST_NAMES = [
    "Jack",
    "Mason",
    "Cole",
    "Dylan",
    "Troy",
    "Grant",
    "Wyatt",
    "Luke",
    "Nate",
    "Reed",
    "Ava",
    "Grace",
    "Nora",
    "Mia",
    "Lena",
    "Quinn",
    "Brooke",
    "June",
    "Carmen",
    "Riley",
]

LAST_NAMES = [
    "Walker",
    "Reyes",
    "Hughes",
    "Morgan",
    "Bennett",
    "Sullivan",
    "Diaz",
    "Carter",
    "Price",
    "Hayes",
    "Romero",
    "Foster",
    "Nelson",
    "Brooks",
    "Torres",
    "Miller",
]

EASTER_EGG_NAMES = {
    12: "Gabe Owners",
    42: "Hugh Januz",
    77: "Anita Changeorder",
    118: "Bill Backcharge",
    151: "Penny Closeout",
    188: "Al B. There",
}


def _rng(seed: int) -> np.random.Generator:
    return np.random.default_rng(seed)


def _sample_coord(rng: np.random.Generator, region: str, spread: float = 0.045) -> tuple[float, float]:
    center = REGION_CLUSTERS[region]
    return (
        float(center["lat"] + rng.normal(0, spread)),
        float(center["lon"] + rng.normal(0, spread)),
    )


def _choose_skills(rng: np.random.Generator, is_supervisor: bool = False) -> list[str]:
    if is_supervisor:
        base = rng.choice(
            ["project superintendent", "senior project manager", "project manager", "safety manager"],
            p=[0.44, 0.22, 0.24, 0.10],
        )
        extras = rng.choice(SKILL_TYPES, size=int(rng.integers(1, 3)), replace=False)
        return sorted(set([base, *extras]))
    primary = rng.choice(SKILL_TYPES)
    extras = rng.choice(SKILL_TYPES, size=int(rng.integers(0, 3)), replace=False)
    return sorted(set([primary, *extras]))


def _choose_certs(rng: np.random.Generator, skills: list[str]) -> list[str]:
    certs: set[str] = {"OSHA 30"}
    if "safety manager" in skills or "project superintendent" in skills:
        certs.add("First Aid/CPR")
        certs.add("safety trained supervisor")
    if "MEP coordinator" in skills:
        certs.add("MEP coordination")
    if "quality manager" in skills:
        certs.add("quality management")
    if "closeout manager" in skills:
        certs.add("closeout documentation")
    if "project executive" in skills or "project manager" in skills:
        certs.add("permit coordination")
    if rng.random() < 0.45:
        certs.add(str(rng.choice(CERTIFICATION_TYPES)))
    if rng.random() < 0.20:
        certs.add(str(rng.choice(CERTIFICATION_TYPES)))
    return sorted(certs)


def generate_personnel(n_personnel: int = 200, n_supervisors: int = 25, seed: int = DEFAULT_SEED) -> pd.DataFrame:
    """Generate personnel and embedded supervisor rows."""
    rng = _rng(seed)
    regions = list(REGION_CLUSTERS)
    region_probs = np.array([0.17, 0.14, 0.24, 0.16, 0.14, 0.15])
    supervisor_ids = [f"P{i:03d}" for i in range(1, n_supervisors + 1)]
    supervisor_regions: dict[str, str] = {}
    rows: list[dict[str, object]] = []

    for idx in range(1, n_personnel + 1):
        personnel_id = f"P{idx:03d}"
        is_supervisor = idx <= n_supervisors
        home_region = str(rng.choice(regions, p=region_probs))
        lat, lon = _sample_coord(rng, home_region, spread=0.038 if is_supervisor else 0.052)
        skills = _choose_skills(rng, is_supervisor)
        certs = _choose_certs(rng, skills)
        if is_supervisor:
            supervisor_regions[personnel_id] = home_region

        if is_supervisor:
            role = str(rng.choice(["project superintendent", "senior superintendent", "project manager", "general superintendent"]))
            supervisor_id = ""
            crew_id = f"C{idx:03d}"
        else:
            same_region_sups = [sid for sid, region in supervisor_regions.items() if region == home_region]
            supervisor_id = str(rng.choice(same_region_sups or supervisor_ids))
            crew_id = f"C{int(rng.integers(1, 31)):03d}"
            role = skills[0]

        rows.append(
            {
                "personnel_id": personnel_id,
                "name": EASTER_EGG_NAMES.get(idx, f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"),
                "role": role,
                "is_supervisor": is_supervisor,
                "home_region": home_region,
                "home_city": REGION_CLUSTERS[home_region]["city"],
                "home_lat": round(lat, 6),
                "home_lon": round(lon, 6),
                "skills": encode_list(skills),
                "certifications": encode_list(certs),
                "crew_id": crew_id,
                "supervisor_id": supervisor_id,
                "hourly_rate": round(float(rng.normal(82 if is_supervisor else 55, 9)), 2),
                "fatigue_base": round(float(np.clip(rng.beta(2.1, 5.2), 0.03, 0.92)), 3),
                "reliability_score": round(float(np.clip(rng.normal(0.90, 0.065), 0.62, 0.99)), 3),
                "overtime_hours_30d": round(float(np.clip(rng.gamma(2.0, 3.2), 0, 36)), 1),
                "history_long_haul_count": int(rng.poisson(2.1)),
                "weekend_late_assignments_30d": int(rng.poisson(1.3)),
                "crew_affinity": round(float(np.clip(rng.normal(0.72, 0.16), 0.20, 0.98)), 3),
                "preferred_regions": encode_list([home_region, str(rng.choice(regions))]),
                "max_reports": int(rng.integers(8, 13)) if is_supervisor else 0,
                "active": True,
            }
        )

    return pd.DataFrame(rows)


def generate_jobsites(n_jobsites: int = 55, seed: int = DEFAULT_SEED + 11) -> pd.DataFrame:
    """Generate GC project-staff demand around Southwest Florida / Gulf Coast clusters."""
    rng = _rng(seed)
    regions = list(REGION_CLUSTERS)
    rows: list[dict[str, object]] = []
    for idx in range(1, n_jobsites + 1):
        region = str(rng.choice(regions, p=[0.15, 0.13, 0.21, 0.16, 0.16, 0.19]))
        lat, lon = _sample_coord(rng, region, spread=0.060)
        project_type = str(rng.choice(PROJECT_TYPES))
        phase = str(rng.choice(PROJECT_PHASES, p=[0.07, 0.11, 0.09, 0.09, 0.17, 0.19, 0.13, 0.08, 0.05, 0.02]))

        if project_type == "healthcare":
            skills = ["project superintendent", "MEP coordinator", str(rng.choice(["safety manager", "quality manager"]))]
            equipment = ["QA/QC inspection kit"]
        elif project_type == "commercial interiors":
            skills = ["project manager", "project engineer", str(rng.choice(["assistant superintendent", "closeout manager"]))]
            equipment = ["site tablet kit"]
        elif project_type == "hospitality":
            skills = ["project manager", str(rng.choice(["quality manager", "closeout manager", "MEP coordinator"]))]
            equipment = ["progress camera kit"]
        elif project_type == "multifamily":
            skills = ["project superintendent", "assistant superintendent", str(rng.choice(["scheduler", "project engineer"]))]
            equipment = ["layout station"]
        elif project_type in {"education", "municipal"}:
            skills = ["project manager", "safety manager", str(rng.choice(["quality manager", "project engineer"]))]
            equipment = ["document control kit"]
        elif project_type == "industrial":
            skills = ["project superintendent", "MEP coordinator", "safety manager"]
            equipment = ["safety trailer"]
        elif project_type == "office renovation":
            skills = ["project manager", "project engineer", str(rng.choice(["MEP coordinator", "assistant project manager"]))]
            equipment = ["punchlist tablet set"]
        else:
            skills = list(rng.choice(SKILL_TYPES, size=int(rng.integers(2, 4)), replace=False))
            equipment = [str(rng.choice(EQUIPMENT_TYPES))]

        certs: set[str] = set()
        if "safety manager" in skills or rng.random() < 0.45:
            certs.add("OSHA 30")
            certs.add("First Aid/CPR")
        if project_type == "healthcare":
            certs.add("ICRA awareness")
        if "MEP coordinator" in skills:
            certs.add("MEP coordination")
        if "quality manager" in skills:
            certs.add("quality management")
        if rng.random() < 0.28:
            certs.add(str(rng.choice(["LEED AP", "stormwater inspector", "fall protection", "permit coordination"])))

        inspection_need = float(np.clip(rng.beta(2.2, 2.0), 0.05, 0.98))
        can_accept_robotics = bool(inspection_need > 0.50 or phase in {"inspection readiness", "closeout", "turnover"})
        rows.append(
            {
                "jobsite_id": f"J{idx:03d}",
                "name": f"{REGION_CLUSTERS[region]['city']} {project_type.title()} {idx:02d}",
                "region": region,
                "city": REGION_CLUSTERS[region]["city"],
                "lat": round(lat, 6),
                "lon": round(lon, 6),
                "project_type": project_type,
                "phase": phase,
                "urgency": int(rng.choice([1, 2, 3, 4, 5], p=[0.10, 0.18, 0.33, 0.25, 0.14])),
                "required_headcount": int(rng.choice([1, 2, 3, 4], p=[0.20, 0.43, 0.27, 0.10])),
                "required_skills": encode_list(skills),
                "required_certifications": encode_list(certs),
                "required_equipment": encode_list(equipment),
                "shift_start": str(rng.choice(["06:30", "07:00", "07:30"])),
                "shift_end": str(rng.choice(["15:00", "15:30", "16:00", "17:00"])),
                "weather_risk": round(float(np.clip(rng.beta(2.0, 5.0), 0.02, 0.92)), 3),
                "schedule_volatility": round(float(np.clip(rng.beta(2.1, 3.4), 0.02, 0.95)), 3),
                "can_accept_robotics": can_accept_robotics,
                "inspection_need": round(inspection_need, 3),
                "change_order_exposure": round(float(np.clip(rng.gamma(2.2, 1800), 500, 22_000)), 2),
                "status": str(rng.choice(["ready", "blocked", "hot", "inspection pending"], p=[0.52, 0.16, 0.20, 0.12])),
            }
        )
    return pd.DataFrame(rows)


def generate_assets(n_assets: int = 40, n_robots: int = 8, seed: int = DEFAULT_SEED + 23) -> pd.DataFrame:
    """Generate equipment, vehicles, and future robotics assets."""
    rng = _rng(seed)
    regions = list(REGION_CLUSTERS)
    rows: list[dict[str, object]] = []
    for idx in range(1, n_assets + 1):
        asset_type = str(rng.choice(EQUIPMENT_TYPES))
        asset_kind = "vehicle" if any(token in asset_type for token in ["truck", "van", "trailer"]) else "equipment"
        rows.append(
            {
                "asset_id": f"A{idx:03d}",
                "asset_kind": asset_kind,
                "asset_type": asset_type,
                "home_region": str(rng.choice(regions)),
                "capability": asset_type,
                "hourly_cost": round(float(rng.normal(28 if asset_kind == "vehicle" else 42, 8)), 2),
                "cost_per_day": 0.0,
                "available": bool(rng.random() > 0.08),
                "robot_ready": False,
            }
        )

    for ridx, robot_type in enumerate(ROBOTIC_ASSET_TYPES, start=1):
        capability = (
            "inspection"
            if "inspection" in robot_type or "drone" in robot_type
            else "layout"
            if "layout" in robot_type
            else "materials"
            if "materials" in robot_type
            else "progress"
        )
        rows.append(
            {
                "asset_id": f"R{ridx:03d}",
                "asset_kind": "robotic",
                "asset_type": robot_type,
                "home_region": str(rng.choice(regions)),
                "capability": capability,
                "hourly_cost": 0.0,
                "cost_per_day": round(float(rng.normal(300, 55)), 2),
                "available": bool(rng.random() > 0.12),
                "robot_ready": True,
            }
        )
    return pd.DataFrame(rows)


def generate_synthetic_company(seed: int = DEFAULT_SEED) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return personnel, jobsites, and assets for the default demo."""
    return (
        generate_personnel(seed=seed),
        generate_jobsites(seed=seed + 11),
        generate_assets(seed=seed + 23),
    )


def ensure_sample_data(output_dir: Path | None = None, seed: int = DEFAULT_SEED) -> None:
    """Write deterministic sample CSVs, including baseline assignments."""
    from amdep.naive_scheduler import build_naive_schedule

    output = output_dir or repo_root() / "data"
    output.mkdir(parents=True, exist_ok=True)
    workers, jobs, assets = generate_synthetic_company(seed=seed)
    naive = build_naive_schedule(workers, jobs, seed=seed, deployment_date=date(2026, 5, 18))
    workers.to_csv(output / "sample_workers.csv", index=False)
    jobs.to_csv(output / "sample_jobsites.csv", index=False)
    assets.to_csv(output / "sample_assets.csv", index=False)
    naive.to_csv(output / "sample_assignments.csv", index=False)


if __name__ == "__main__":
    ensure_sample_data()
