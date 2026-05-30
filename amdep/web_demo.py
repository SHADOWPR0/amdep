"""Local web delivery for the AMDEP demo command center."""

from __future__ import annotations

import argparse
import contextlib
import json
import socket
import webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from amdep.audit_pipeline import run_csv_audit
from amdep.utils import repo_root


class DemoRequestHandler(SimpleHTTPRequestHandler):
    """Serve the repository root and route / to the web command center."""

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def do_GET(self) -> None:  # noqa: N802 - stdlib hook
        if self.path in {"", "/"}:
            self.send_response(302)
            self.send_header("Location", "/web/index.html")
            self.end_headers()
            return
        super().do_GET()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run and serve the AMDEP web demo.")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface for the demo server.")
    parser.add_argument("--port", type=int, default=8088, help="Preferred port for the demo server.")
    parser.add_argument("--trials", type=int, default=18, help="Calibration gym trials before serving.")
    parser.add_argument("--seed", type=int, default=1776, help="Synthetic demo seed.")
    parser.add_argument("--skip-audit", action="store_true", help="Serve the last generated demo packet.")
    parser.add_argument("--no-open", action="store_true", help="Do not open the browser automatically.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = repo_root()
    output_dir = root / "reports" / "demo_audit"

    if not args.skip_audit:
        result = run_csv_audit(
            workers_path=root / "data" / "sample_workers.csv",
            jobsites_path=root / "data" / "sample_jobsites.csv",
            assignments_path=root / "data" / "sample_assignments.csv",
            assets_path=root / "data" / "sample_assets.csv",
            output_dir=output_dir,
            seed=args.seed,
            calibration_trials=args.trials,
        )
        print(f"Audit packet refreshed: {output_dir}")
        print(f"Solver status: {result.optimizer_result['status']}")
        print(f"Recovered capacity hours/day: {result.comparison['dispatch_delta']:.1f}")
        print(f"18-month deployment impact: ${result.deployment_economics['implementation_horizon_impact']:,.0f}")
        print(f"Annualized deployment run-rate: ${result.deployment_economics['annual_deployment_run_rate']:,.0f}")
        write_static_demo_data(output_dir, root / "web" / "demo-data.json", economics=result.deployment_economics)
    else:
        print(f"Serving existing audit packet: {output_dir}")
        write_static_demo_data(output_dir, root / "web" / "demo-data.json")

    port = _available_port(args.host, args.port)
    handler = partial(DemoRequestHandler, directory=str(root))
    server = ThreadingHTTPServer((args.host, port), handler)
    url = f"http://{args.host}:{port}/web/index.html"
    print(f"AMDEP web demo: {url}")
    print("Press Ctrl+C to stop.")
    if not args.no_open:
        webbrowser.open(url)

    with contextlib.suppress(KeyboardInterrupt):
        server.serve_forever()
    server.server_close()


def _available_port(host: str, preferred: int) -> int:
    for port in range(preferred, preferred + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if probe.connect_ex((host, port)) != 0:
                return port
    raise RuntimeError(f"No open port found from {preferred} to {preferred + 19}.")


def write_static_demo_data(packet_dir: Path, target_path: Path, economics: dict[str, float] | None = None) -> Path:
    """Write a self-contained JSON packet for static hosting."""
    import pandas as pd

    tables = {
        "workers": pd.read_csv(repo_root() / "data" / "sample_workers.csv"),
        "jobsites": pd.read_csv(repo_root() / "data" / "sample_jobsites.csv"),
        "baseline": pd.read_csv(packet_dir / "baseline_assignments.csv"),
        "optimized": pd.read_csv(packet_dir / "optimized_assignments.csv"),
        "waste": pd.read_csv(packet_dir / "top_waste_findings.csv"),
        "burden": pd.read_csv(packet_dir / "personnel_burden.csv"),
        "staffing": pd.read_csv(packet_dir / "job_staffing_status.csv"),
        "robotics": pd.read_csv(packet_dir / "robotics_plan.csv"),
        "trials": pd.read_csv(packet_dir / "calibration_trials.csv"),
        "weights": pd.read_csv(packet_dir / "recommended_weights.csv"),
        "recommendations": pd.read_csv(packet_dir / "integrations" / "recommendations_generic.csv"),
    }
    payload = {
        "disclaimer": "Synthetic randomized commercial GC staffing portfolio. Economic impact is directional until validated against historical assignments, schedules, outcomes, overrides, and job-cost records.",
        "economics": economics or {},
        "tables": {name: frame.where(pd.notna(frame), "").to_dict("records") for name, frame in tables.items()},
    }
    target_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return target_path


if __name__ == "__main__":
    main()
