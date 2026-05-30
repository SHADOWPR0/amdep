"""Human-style baseline scheduler for the AmDep before state."""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from amdep.features import certification_match_score, skill_match_score
from amdep.utils import pipe_list, travel_minutes


def build_naive_schedule(
    workers: pd.DataFrame,
    jobs: pd.DataFrame,
    *,
    seed: int = 1776,
    deployment_date: date | None = None,
) -> pd.DataFrame:
    """Build a plausible baseline deployment plan.

    The baseline mostly respects skills, loosely respects certifications, favors familiar project teams,
    and misses global route-burn minimization.
    """
    rng = np.random.default_rng(seed)
    day = deployment_date or date.today()
    available = set(workers.loc[workers["active"].astype(bool), "personnel_id"].tolist())
    worker_lookup = workers.set_index("personnel_id").to_dict("index")
    job_order = jobs.sample(frac=1, random_state=seed).sort_values(["urgency", "schedule_volatility"], ascending=[False, False])
    rows: list[dict[str, object]] = []

    for _, job in job_order.iterrows():
        required_skills = pipe_list(job["required_skills"])
        required_certs = pipe_list(job["required_certifications"])
        assigned_for_job = 0
        target = int(job["required_headcount"])
        if not available:
            break

        for _slot in range(target):
            candidates = []
            for personnel_id in list(available):
                worker = worker_lookup[personnel_id]
                skills = pipe_list(worker["skills"])
                certs = pipe_list(worker["certifications"])
                s_score = skill_match_score(skills, required_skills)
                c_score = certification_match_score(certs, required_certs)
                if s_score <= 0 and rng.random() > 0.22:
                    continue
                if c_score < 1.0 and rng.random() > 0.16:
                    continue
                commute = travel_minutes(worker["home_lat"], worker["home_lon"], job["lat"], job["lon"])
                familiarity_bonus = 0.0
                if worker.get("home_region") == job.get("region"):
                    familiarity_bonus -= 18.0
                if str(worker.get("supervisor_id", "")).endswith(("001", "002", "003", "004", "005")):
                    familiarity_bonus -= 9.0
                if worker.get("crew_id") in {"C001", "C002", "C003", "C004", "C005"}:
                    familiarity_bonus -= 7.0
                noise = float(rng.normal(0, 24))
                score = commute * 0.54 - 42.0 * s_score - 16.0 * c_score + familiarity_bonus + noise
                candidates.append((score, personnel_id, commute, s_score, c_score))

            if not candidates:
                continue

            candidates.sort(key=lambda item: item[0])
            if rng.random() < 0.18 and len(candidates) > 8:
                far_pool = sorted(candidates, key=lambda item: item[2], reverse=True)[: max(3, len(candidates) // 4)]
                choice = far_pool[int(rng.integers(0, len(far_pool)))]
                reason = "familiar-project-team bias overrode route logic"
            else:
                top_n = min(len(candidates), int(rng.integers(3, 10)))
                choice = candidates[int(rng.integers(0, top_n))]
                reason = "manual staffing heuristic"

            _score, personnel_id, commute, s_score, c_score = choice
            worker = worker_lookup[personnel_id]
            available.remove(personnel_id)
            assigned_for_job += 1
            rows.append(
                {
                    "assignment_id": f"N-{day.strftime('%Y%m%d')}-{len(rows) + 1:04d}",
                    "deployment_date": day.isoformat(),
                    "assignment_source": "naive",
                    "personnel_id": personnel_id,
                    "jobsite_id": job["jobsite_id"],
                    "supervisor_id": worker.get("supervisor_id", ""),
                    "crew_id": worker.get("crew_id", ""),
                    "worker_name": worker.get("name", ""),
                    "worker_role": worker.get("role", ""),
                    "job_name": job.get("name", ""),
                    "project_type": job.get("project_type", ""),
                    "phase": job.get("phase", ""),
                    "schedule_volatility": round(float(job.get("schedule_volatility", 0.0)), 4),
                    "change_order_exposure": round(float(job.get("change_order_exposure", 0.0)), 2),
                    "home_region": worker.get("home_region", ""),
                    "job_region": job.get("region", ""),
                    "commute_minutes": round(float(commute), 2),
                    "skill_match_score": round(float(s_score), 4),
                    "certification_match": bool(c_score >= 1.0),
                    "certification_match_score": round(float(c_score), 4),
                    "job_urgency": int(job.get("urgency", 3)),
                    "total_cost_score": round(float(max(commute, 0) + (1 - s_score) * 80 + (1 - c_score) * 250), 2),
                    "dispatch_reason": reason,
                }
            )
        if assigned_for_job == 0 and rng.random() < 0.08:
            continue

    return pd.DataFrame(rows)
