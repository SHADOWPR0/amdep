"""CLI for running an AmDep dispatch audit packet."""

from __future__ import annotations

import argparse
from pathlib import Path

from amdep.audit_pipeline import run_csv_audit
from amdep.integrations.known_stacks import KNOWN_STACKS
from amdep.utils import repo_root


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run American Deployment dispatch audit.")
    parser.add_argument("--workers", type=Path, help="Workers/personnel CSV. Defaults to demo data.")
    parser.add_argument("--jobsites", type=Path, help="Jobsites/work orders CSV. Defaults to demo data.")
    parser.add_argument("--assignments", type=Path, help="Historical assignments CSV.")
    parser.add_argument("--assets", type=Path, help="Assets/equipment/robotics CSV.")
    parser.add_argument("--output", type=Path, default=Path("reports/demo_audit"), help="Output packet directory.")
    parser.add_argument("--seed", type=int, default=1776)
    parser.add_argument("--trials", type=int, default=18, help="Calibration gym trials.")
    parser.add_argument("--list-stacks", action="store_true", help="List known integration target stacks and exit.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.list_stacks:
        for stack_id, manifest in KNOWN_STACKS.items():
            print(f"{stack_id}: {manifest.display_name} ({manifest.category})")
        return

    root = repo_root()
    workers = args.workers or root / "data" / "sample_workers.csv"
    jobsites = args.jobsites or root / "data" / "sample_jobsites.csv"
    assignments = args.assignments
    assets = args.assets
    if args.workers is None and args.jobsites is None:
        assignments = assignments or root / "data" / "sample_assignments.csv"
        assets = assets or root / "data" / "sample_assets.csv"

    result = run_csv_audit(
        workers_path=workers,
        jobsites_path=jobsites,
        assignments_path=assignments,
        assets_path=assets,
        output_dir=args.output,
        seed=args.seed,
        calibration_trials=args.trials,
    )
    print(f"Audit packet saved to {args.output.resolve()}")
    print(f"Open: {(args.output / 'dispatch_audit_summary.html').resolve()}")
    print(f"Solver status: {result.optimizer_result['status']}")
    print(f"Recovered capacity hours/day: {result.comparison['dispatch_delta']:.1f}")
    print(f"18-month deployment impact: ${result.deployment_economics['implementation_horizon_impact']:,.0f}")
    print(f"Annualized deployment run-rate: ${result.deployment_economics['annual_deployment_run_rate']:,.0f}")
    print(f"Calibration method: {result.calibration.method}")


if __name__ == "__main__":
    main()
