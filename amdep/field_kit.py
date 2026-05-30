"""Local-only AMDEP Field Kit for read-only customer intake pilots."""

from __future__ import annotations

import argparse
import contextlib
import json
import mimetypes
import re
import shutil
import socket
import webbrowser
from datetime import datetime
from email import policy
from email.parser import BytesParser
from functools import partial
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

import pandas as pd

from amdep.audit_pipeline import run_csv_audit
from amdep.utils import repo_root
from config import DEFAULT_WEIGHTS


DEFAULT_GEO = (39.8283, -98.5795, "Unresolved market")
COORDINATE_RE = re.compile(r"(-?\d{1,2}(?:\.\d+)?)\s*[,/ ]\s*(-?\d{1,3}(?:\.\d+)?)")

LOCATION_DEFAULTS = {
    "naples fl": (26.1420, -81.7948, "Naples, FL", "city"),
    "naples": (26.1420, -81.7948, "Naples, FL", "city"),
    "bonita springs": (26.3398, -81.7787, "Bonita Springs, FL", "city"),
    "bonita": (26.3398, -81.7787, "Bonita Springs, FL", "city"),
    "estero": (26.4381, -81.8068, "Estero, FL", "city"),
    "fort myers": (26.6406, -81.8723, "Fort Myers, FL", "city"),
    "cape coral": (26.5629, -81.9495, "Cape Coral, FL", "city"),
    "lehigh acres": (26.6253, -81.6248, "Lehigh Acres, FL", "city"),
    "immokalee": (26.4187, -81.4173, "Immokalee, FL", "city"),
    "sarasota": (27.3364, -82.5307, "Sarasota, FL", "city"),
    "punta gorda": (26.9298, -82.0454, "Punta Gorda, FL", "city"),
    "tampa": (27.9506, -82.4572, "Tampa, FL", "city"),
    "st petersburg": (27.7676, -82.6403, "St. Petersburg, FL", "city"),
    "orlando": (28.5383, -81.3792, "Orlando, FL", "city"),
    "jacksonville": (30.3322, -81.6557, "Jacksonville, FL", "city"),
    "miami": (25.7617, -80.1918, "Miami, FL", "city"),
    "fort lauderdale": (26.1224, -80.1373, "Fort Lauderdale, FL", "city"),
    "west palm": (26.7153, -80.0534, "West Palm Beach, FL", "city"),
    "atlanta": (33.7490, -84.3880, "Atlanta, GA", "city"),
    "savannah": (32.0809, -81.0912, "Savannah, GA", "city"),
    "charlotte": (35.2271, -80.8431, "Charlotte, NC", "city"),
    "raleigh": (35.7796, -78.6382, "Raleigh, NC", "city"),
    "greensboro": (36.0726, -79.7920, "Greensboro, NC", "city"),
    "charleston": (32.7765, -79.9311, "Charleston, SC", "city"),
    "greenville sc": (34.8526, -82.3940, "Greenville, SC", "city"),
    "columbia sc": (34.0007, -81.0348, "Columbia, SC", "city"),
    "nashville": (36.1627, -86.7816, "Nashville, TN", "city"),
    "memphis": (35.1495, -90.0490, "Memphis, TN", "city"),
    "knoxville": (35.9606, -83.9207, "Knoxville, TN", "city"),
    "birmingham": (33.5186, -86.8104, "Birmingham, AL", "city"),
    "huntsville": (34.7304, -86.5861, "Huntsville, AL", "city"),
    "mobile al": (30.6954, -88.0399, "Mobile, AL", "city"),
    "new orleans": (29.9511, -90.0715, "New Orleans, LA", "city"),
    "houston": (29.7604, -95.3698, "Houston, TX", "city"),
    "dallas": (32.7767, -96.7970, "Dallas, TX", "city"),
    "fort worth": (32.7555, -97.3308, "Fort Worth, TX", "city"),
    "austin": (30.2672, -97.7431, "Austin, TX", "city"),
    "san antonio": (29.4241, -98.4936, "San Antonio, TX", "city"),
    "phoenix": (33.4484, -112.0740, "Phoenix, AZ", "city"),
    "las vegas": (36.1699, -115.1398, "Las Vegas, NV", "city"),
    "denver": (39.7392, -104.9903, "Denver, CO", "city"),
    "salt lake": (40.7608, -111.8910, "Salt Lake City, UT", "city"),
    "los angeles": (34.0522, -118.2437, "Los Angeles, CA", "city"),
    "san diego": (32.7157, -117.1611, "San Diego, CA", "city"),
    "san francisco": (37.7749, -122.4194, "San Francisco, CA", "city"),
    "sacramento": (38.5816, -121.4944, "Sacramento, CA", "city"),
    "seattle": (47.6062, -122.3321, "Seattle, WA", "city"),
    "portland": (45.5152, -122.6784, "Portland, OR", "city"),
    "chicago": (41.8781, -87.6298, "Chicago, IL", "city"),
    "milwaukee": (43.0389, -87.9065, "Milwaukee, WI", "city"),
    "minneapolis": (44.9778, -93.2650, "Minneapolis, MN", "city"),
    "detroit": (42.3314, -83.0458, "Detroit, MI", "city"),
    "cleveland": (41.4993, -81.6944, "Cleveland, OH", "city"),
    "columbus oh": (39.9612, -82.9988, "Columbus, OH", "city"),
    "pittsburgh": (40.4406, -79.9959, "Pittsburgh, PA", "city"),
    "philadelphia": (39.9526, -75.1652, "Philadelphia, PA", "city"),
    "new york": (40.7128, -74.0060, "New York, NY", "city"),
    "manhattan": (40.7831, -73.9712, "Manhattan, NY", "city"),
    "brooklyn": (40.6782, -73.9442, "Brooklyn, NY", "city"),
    "boston": (42.3601, -71.0589, "Boston, MA", "city"),
    "washington dc": (38.9072, -77.0369, "Washington, DC", "city"),
    "baltimore": (39.2904, -76.6122, "Baltimore, MD", "city"),
    "richmond": (37.5407, -77.4360, "Richmond, VA", "city"),
    "norfolk": (36.8508, -76.2859, "Norfolk, VA", "city"),
    "indianapolis": (39.7684, -86.1581, "Indianapolis, IN", "city"),
    "st louis": (38.6270, -90.1994, "St. Louis, MO", "city"),
    "kansas city": (39.0997, -94.5786, "Kansas City, MO", "city"),
    "oklahoma city": (35.4676, -97.5164, "Oklahoma City, OK", "city"),
    "tulsa": (36.1540, -95.9928, "Tulsa, OK", "city"),
}

STATE_ALIASES = {
    "al": "alabama", "ak": "alaska", "az": "arizona", "ar": "arkansas", "ca": "california",
    "co": "colorado", "ct": "connecticut", "de": "delaware", "dc": "district of columbia",
    "fl": "florida", "ga": "georgia", "hi": "hawaii", "id": "idaho", "il": "illinois",
    "in": "indiana", "ia": "iowa", "ks": "kansas", "ky": "kentucky", "la": "louisiana",
    "me": "maine", "md": "maryland", "ma": "massachusetts", "mi": "michigan", "mn": "minnesota",
    "ms": "mississippi", "mo": "missouri", "mt": "montana", "ne": "nebraska", "nv": "nevada",
    "nh": "new hampshire", "nj": "new jersey", "nm": "new mexico", "ny": "new york",
    "nc": "north carolina", "nd": "north dakota", "oh": "ohio", "ok": "oklahoma",
    "or": "oregon", "pa": "pennsylvania", "ri": "rhode island", "sc": "south carolina",
    "sd": "south dakota", "tn": "tennessee", "tx": "texas", "ut": "utah", "vt": "vermont",
    "va": "virginia", "wa": "washington", "wv": "west virginia", "wi": "wisconsin", "wy": "wyoming",
}

STATE_CENTROIDS = {
    "alabama": (32.8067, -86.7911, "Alabama"),
    "alaska": (61.3707, -152.4044, "Alaska"),
    "arizona": (33.7298, -111.4312, "Arizona"),
    "arkansas": (34.9697, -92.3731, "Arkansas"),
    "california": (36.1162, -119.6816, "California"),
    "colorado": (39.0598, -105.3111, "Colorado"),
    "connecticut": (41.5978, -72.7554, "Connecticut"),
    "delaware": (39.3185, -75.5071, "Delaware"),
    "district of columbia": (38.9072, -77.0369, "Washington, DC"),
    "florida": (27.7663, -81.6868, "Florida"),
    "georgia": (33.0406, -83.6431, "Georgia"),
    "hawaii": (21.0943, -157.4983, "Hawaii"),
    "idaho": (44.2405, -114.4788, "Idaho"),
    "illinois": (40.3495, -88.9861, "Illinois"),
    "indiana": (39.8494, -86.2583, "Indiana"),
    "iowa": (42.0115, -93.2105, "Iowa"),
    "kansas": (38.5266, -96.7265, "Kansas"),
    "kentucky": (37.6681, -84.6701, "Kentucky"),
    "louisiana": (31.1695, -91.8678, "Louisiana"),
    "maine": (44.6939, -69.3819, "Maine"),
    "maryland": (39.0639, -76.8021, "Maryland"),
    "massachusetts": (42.2302, -71.5301, "Massachusetts"),
    "michigan": (43.3266, -84.5361, "Michigan"),
    "minnesota": (45.6945, -93.9002, "Minnesota"),
    "mississippi": (32.7416, -89.6787, "Mississippi"),
    "missouri": (38.4561, -92.2884, "Missouri"),
    "montana": (46.9219, -110.4544, "Montana"),
    "nebraska": (41.1254, -98.2681, "Nebraska"),
    "nevada": (38.3135, -117.0554, "Nevada"),
    "new hampshire": (43.4525, -71.5639, "New Hampshire"),
    "new jersey": (40.2989, -74.5210, "New Jersey"),
    "new mexico": (34.8405, -106.2485, "New Mexico"),
    "new york": (42.1657, -74.9481, "New York"),
    "north carolina": (35.6301, -79.8064, "North Carolina"),
    "north dakota": (47.5289, -99.7840, "North Dakota"),
    "ohio": (40.3888, -82.7649, "Ohio"),
    "oklahoma": (35.5653, -96.9289, "Oklahoma"),
    "oregon": (44.5720, -122.0709, "Oregon"),
    "pennsylvania": (40.5908, -77.2098, "Pennsylvania"),
    "rhode island": (41.6809, -71.5118, "Rhode Island"),
    "south carolina": (33.8569, -80.9450, "South Carolina"),
    "south dakota": (44.2998, -99.4388, "South Dakota"),
    "tennessee": (35.7478, -86.6923, "Tennessee"),
    "texas": (31.0545, -97.5635, "Texas"),
    "utah": (40.1500, -111.8624, "Utah"),
    "vermont": (44.0459, -72.7107, "Vermont"),
    "virginia": (37.7693, -78.1700, "Virginia"),
    "washington": (47.4009, -121.4905, "Washington"),
    "west virginia": (38.4912, -80.9545, "West Virginia"),
    "wisconsin": (44.2685, -89.6165, "Wisconsin"),
    "wyoming": (42.7560, -107.3025, "Wyoming"),
}

DATASET_PROFILES = {
    "workers": {
        "label": "People / roster",
        "filename_terms": ["employee", "personnel", "worker", "staff", "roster", "people", "team", "workday", "hris"],
        "columns": {
            "personnel_id": ["personnel_id", "employee_id", "employee id", "worker_id", "worker id", "staff id", "person id", "id"],
            "name": ["name", "employee name", "worker name", "full name", "person", "staff name"],
            "role": ["role", "title", "job title", "position", "classification", "labor category"],
            "home_region": ["home_region", "home region", "region", "market", "branch", "office", "home base", "base"],
            "home_address": ["home_address", "home address", "address", "employee address", "worker address"],
            "home_city": ["home_city", "home city", "city"],
            "home_state": ["home_state", "home state", "state"],
            "home_lat": ["home_lat", "home latitude", "latitude", "lat"],
            "home_lon": ["home_lon", "home longitude", "longitude", "lon", "lng"],
            "home_zip": ["home_zip", "home zip", "zip", "zipcode", "postal code"],
            "skills": ["skills", "skill", "trade", "trades", "discipline", "capabilities"],
            "certifications": ["certifications", "certification", "certs", "cert", "osha", "training"],
            "supervisor_id": ["supervisor_id", "supervisor id", "manager id", "reports to"],
            "crew_id": ["crew_id", "crew id", "crew", "team id"],
        },
        "audit_required": ["personnel_id", "skills", "certifications"],
    },
    "jobsites": {
        "label": "Jobs / projects",
        "filename_terms": ["job", "jobs", "project", "projects", "site", "jobsite", "work order", "procore", "autodesk"],
        "columns": {
            "jobsite_id": ["jobsite_id", "job id", "job_id", "project id", "project_id", "project number", "job number", "id"],
            "name": ["name", "project name", "job name", "site name", "work order", "description"],
            "region": ["region", "market", "city", "location", "area", "branch"],
            "city": ["city", "municipality"],
            "state": ["state", "province"],
            "address": ["address", "job address", "project address", "site address"],
            "zip": ["zip", "zipcode", "postal code", "job zip", "project zip"],
            "lat": ["lat", "latitude", "job lat", "site lat"],
            "lon": ["lon", "lng", "longitude", "job lon", "site lon"],
            "required_headcount": ["required_headcount", "headcount", "required headcount", "needed", "slots", "staff needed"],
            "required_skills": ["required_skills", "required skills", "skill", "trade", "scope", "discipline"],
            "required_certifications": ["required_certifications", "required certs", "certifications", "certs", "osha"],
            "phase": ["phase", "project phase", "stage", "status"],
            "urgency": ["urgency", "priority", "risk", "criticality"],
        },
        "audit_required": ["jobsite_id", "name", "required_headcount", "required_skills", "required_certifications"],
    },
    "assignments": {
        "label": "Current assignments",
        "filename_terms": ["assignment", "assignments", "schedule", "staffing", "dispatch", "lookahead", "look ahead"],
        "columns": {
            "personnel_id": ["personnel_id", "employee_id", "employee id", "worker id", "person id", "staff id"],
            "worker_name": ["worker name", "employee name", "person", "name", "staff"],
            "jobsite_id": ["jobsite_id", "job id", "project id", "project number", "job number"],
            "job_name": ["job name", "project name", "site", "project", "job"],
            "deployment_date": ["date", "deployment date", "assignment date", "scheduled date"],
            "supervisor_id": ["supervisor_id", "supervisor id", "manager id", "reports to"],
            "crew_id": ["crew_id", "crew id", "crew", "team id"],
        },
        "audit_required": ["personnel_id", "jobsite_id"],
    },
    "assets": {
        "label": "Equipment / assets",
        "filename_terms": ["asset", "assets", "equipment", "fleet", "vehicle", "robot", "drone"],
        "columns": {
            "asset_id": ["asset_id", "asset id", "equipment id", "vehicle id", "id"],
            "asset_kind": ["asset_kind", "kind", "category", "asset category"],
            "asset_type": ["asset_type", "type", "equipment type", "vehicle type"],
            "home_region": ["home_region", "region", "market", "branch", "yard", "depot"],
            "available": ["available", "status", "active"],
        },
        "audit_required": ["asset_id", "asset_kind", "asset_type", "home_region", "available"],
    },
    "certifications": {
        "label": "Certifications / training",
        "filename_terms": ["cert", "certification", "osha", "training", "license", "safety"],
        "columns": {
            "personnel_id": ["personnel_id", "employee_id", "employee id", "worker id", "staff id"],
            "worker_name": ["employee name", "worker name", "name"],
            "certifications": ["certification", "certifications", "cert", "training", "osha", "license"],
            "expiration": ["expiration", "expires", "expiry", "expiration date"],
        },
        "audit_required": ["personnel_id", "certifications"],
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the local-only AMDEP Field Kit.")
    parser.add_argument("--host", default="127.0.0.1", help="Local host interface.")
    parser.add_argument("--port", type=int, default=8095, help="Preferred local port.")
    parser.add_argument("--workspace", type=Path, default=repo_root() / "field_kit_workspace")
    parser.add_argument("--no-open", action="store_true", help="Do not open a browser automatically.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    workspace = args.workspace.resolve()
    init_workspace(workspace)
    port = _available_port(args.host, args.port)
    handler = partial(FieldKitHandler, workspace=workspace, static_dir=repo_root() / "field_kit")
    server = ThreadingHTTPServer((args.host, port), handler)
    url = f"http://{args.host}:{port}/"
    print(f"AMDEP Field Kit: {url}")
    print(f"Private workspace: {workspace}")
    print("Press Ctrl+C to stop.")
    if not args.no_open:
        webbrowser.open(url)
    with contextlib.suppress(KeyboardInterrupt):
        server.serve_forever()
    server.server_close()


def init_workspace(workspace: Path) -> None:
    for child in ["inbox", "normalized", "reports", "profiles"]:
        (workspace / child).mkdir(parents=True, exist_ok=True)


def _available_port(host: str, preferred: int) -> int:
    for port in range(preferred, preferred + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if probe.connect_ex((host, port)) != 0:
                return port
    raise RuntimeError(f"No open port found from {preferred} to {preferred + 19}.")


class FieldKitHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, workspace: Path, static_dir: Path, **kwargs):
        self.workspace = workspace
        self.static_dir = static_dir
        super().__init__(*args, directory=str(static_dir), **kwargs)

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path in {"", "/"}:
            return self._send_file(self.static_dir / "index.html", "text/html")
        if parsed.path == "/api/status":
            return self._send_json(status_payload(self.workspace))
        if parsed.path == "/api/analyze":
            return self._send_json(analyze_workspace(self.workspace))
        if parsed.path == "/api/model":
            return self._send_json(model_payload(self.workspace))
        if parsed.path.startswith("/docs/"):
            return self._send_doc_file(parsed.path.removeprefix("/docs/"))
        if parsed.path.startswith("/workspace/"):
            return self._send_workspace_file(parsed.path.removeprefix("/workspace/"))
        return super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/upload":
            return self._handle_upload()
        if parsed.path == "/api/profile":
            return self._handle_profile()
        if parsed.path == "/api/run-audit":
            return self._handle_run_audit()
        self.send_error(HTTPStatus.NOT_FOUND, "Unknown endpoint")

    def _handle_upload(self) -> None:
        inbox = self.workspace / "inbox"
        inbox.mkdir(parents=True, exist_ok=True)
        length = int(self.headers.get("Content-Length", "0"))
        content_type = self.headers.get("Content-Type", "")
        body = self.rfile.read(length)
        message = BytesParser(policy=policy.default).parsebytes(
            f"Content-Type: {content_type}\r\n\r\n".encode("utf-8") + body
        )
        saved = []
        if message.is_multipart():
            for part in message.iter_parts():
                filename = part.get_filename()
                if not filename:
                    continue
                target = inbox / safe_filename(filename)
                target.write_bytes(part.get_payload(decode=True) or b"")
                saved.append({"file": target.name, "bytes": target.stat().st_size})
        self._send_json({"saved": saved, "summary": analyze_workspace(self.workspace)})

    def _handle_profile(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length) or b"{}")
        profile_path = self.workspace / "profiles" / "company_intake.json"
        profile_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        self._send_json({"ok": True, "profile_path": str(profile_path)})

    def _handle_run_audit(self) -> None:
        try:
            summary = analyze_workspace(self.workspace)
            normalized = materialize_normalized_bundle(self.workspace, summary)
            output_dir = self.workspace / "reports" / datetime.now().strftime("audit_%Y%m%d_%H%M%S")
            result = run_csv_audit(
                workers_path=normalized["workers"],
                jobsites_path=normalized["jobsites"],
                assignments_path=normalized.get("assignments"),
                assets_path=normalized.get("assets"),
                output_dir=output_dir,
                calibration_trials=6,
            )
            report = output_dir / "dispatch_audit_summary.html"
            command_dir = write_local_command_center(self.workspace, output_dir, normalized, result.deployment_economics)
            self._send_json(
                {
                    "ok": True,
                    "report_url": f"/workspace/{report.relative_to(self.workspace).as_posix()}",
                    "command_url": f"/workspace/{command_dir.relative_to(self.workspace).as_posix()}/index.html",
                    "report_path": str(report),
                    "output_dir": str(output_dir),
                    "solver_status": result.optimizer_result["status"],
                    "impact_18_month": round(float(result.deployment_economics["implementation_horizon_impact"]), 2),
                    "annual_run_rate": round(float(result.deployment_economics["annual_deployment_run_rate"]), 2),
                    "readiness": summary["readiness"],
                }
            )
        except Exception as exc:  # noqa: BLE001 - local FDE tool should return operator-readable failure.
            self._send_json({"ok": False, "error": str(exc), "summary": analyze_workspace(self.workspace)}, status=400)

    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, indent=2, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path, content_type: str) -> None:
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_workspace_file(self, relative: str) -> None:
        target = (self.workspace / unquote(relative)).resolve()
        if not target.is_file() or self.workspace not in target.parents:
            self.send_error(HTTPStatus.NOT_FOUND, "Workspace file not found")
            return
        explicit_types = {
            ".css": "text/css",
            ".html": "text/html",
            ".js": "application/javascript",
            ".json": "application/json",
            ".svg": "image/svg+xml",
            ".webmanifest": "application/manifest+json",
        }
        content_type = explicit_types.get(target.suffix.lower()) or mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        self._send_file(target, content_type)

    def _send_doc_file(self, relative: str) -> None:
        target = (repo_root() / "docs" / unquote(relative)).resolve()
        docs_root = (repo_root() / "docs").resolve()
        if not target.is_file() or docs_root not in target.parents:
            self.send_error(HTTPStatus.NOT_FOUND, "Documentation file not found")
            return
        content_type = "text/markdown; charset=utf-8" if target.suffix.lower() == ".md" else "text/plain; charset=utf-8"
        self._send_file(target, content_type)


def status_payload(workspace: Path) -> dict:
    init_workspace(workspace)
    files = sorted((workspace / "inbox").glob("*"))
    return {
        "workspace": str(workspace),
        "inbox": str(workspace / "inbox"),
        "file_count": len([item for item in files if item.is_file()]),
        "profile_exists": (workspace / "profiles" / "company_intake.json").exists(),
    }


def model_payload(workspace: Path) -> dict:
    latest_weights_path = latest_report_file(workspace, "recommended_weights.csv")
    latest_trials_path = latest_report_file(workspace, "calibration_trials.csv")
    latest_weights = []
    if latest_weights_path is not None:
        try:
            latest_weights = pd.read_csv(latest_weights_path).where(pd.notna, "").to_dict("records")
        except (FileNotFoundError, pd.errors.EmptyDataError):
            latest_weights = []
    return {
        "status": "Local transparent model stack. First-run risk scores are synthetic until customer outcomes are supplied.",
        "model_card_url": "/docs/FIELD_KIT_MODEL_CARD.md",
        "default_weights_file": "config.py",
        "default_weights": DEFAULT_WEIGHTS,
        "code_paths": {
            "feature_layer": "amdep/features.py",
            "risk_models": "amdep/brain.py",
            "optimizer": "amdep/optimizer.py",
            "calibration": "amdep/calibration.py",
            "economics": "amdep/metrics.py",
        },
        "model_families": [
            "Logistic regression: attrition and no-show risk",
            "Histogram gradient boosting: delay risk",
            "Random forest: crew compatibility and robotics suitability",
            "OR-Tools CP-SAT: constrained staffing optimizer, with greedy fallback",
        ],
        "latest_run": {
            "recommended_weights_url": workspace_url(workspace, latest_weights_path),
            "calibration_trials_url": workspace_url(workspace, latest_trials_path),
            "recommended_weights": latest_weights,
        },
    }


def latest_report_file(workspace: Path, filename: str) -> Path | None:
    reports = workspace / "reports"
    if not reports.exists():
        return None
    candidates = sorted(reports.glob(f"audit_*/{filename}"), reverse=True)
    return candidates[0] if candidates else None


def workspace_url(workspace: Path, path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return f"/workspace/{path.relative_to(workspace).as_posix()}"
    except ValueError:
        return None


def analyze_workspace(workspace: Path) -> dict:
    init_workspace(workspace)
    files = [path for path in sorted((workspace / "inbox").glob("*")) if path.is_file()]
    classified = [classify_file(path) for path in files]
    readiness = readiness_score(classified)
    summary = {
        "workspace": str(workspace),
        "inbox": str(workspace / "inbox"),
        "files": classified,
        "datasets": best_by_dataset(classified),
        "readiness": readiness,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }
    write_intake_summary(workspace, summary)
    return summary


def classify_file(path: Path) -> dict:
    frame, read_error = read_tabular_preview(path)
    columns = list(frame.columns) if frame is not None else []
    rows = int(len(frame)) if frame is not None else None
    lower_name = path.name.lower()
    candidates = []
    for dataset, profile in DATASET_PROFILES.items():
        mapped = map_columns(columns, profile["columns"])
        filename_score = sum(2 for term in profile["filename_terms"] if term in lower_name)
        column_score = sum(4 for key in profile["audit_required"] if key in mapped)
        support_score = max(0, len(mapped) - len(set(profile["audit_required"]).intersection(mapped)))
        score = filename_score + column_score + support_score
        required_missing = [key for key in profile["audit_required"] if key not in mapped]
        candidates.append(
            {
                "dataset": dataset,
                "label": profile["label"],
                "score": score,
                "mapped_columns": mapped,
                "missing_required": required_missing,
            }
        )
    best = max(candidates, key=lambda item: item["score"]) if candidates else None
    confidence = min(1.0, (best["score"] if best else 0) / 24)
    classification = best["dataset"] if best and best["score"] > 0 else "unknown"
    return {
        "file": path.name,
        "path": str(path),
        "extension": path.suffix.lower(),
        "bytes": path.stat().st_size,
        "rows_previewed": rows,
        "columns": columns,
        "classification": classification,
        "label": DATASET_PROFILES.get(classification, {}).get("label", "Unknown"),
        "confidence": round(confidence, 2),
        "mapped_columns": best["mapped_columns"] if best else {},
        "missing_required": best["missing_required"] if best else [],
        "read_error": read_error,
    }


def read_tabular_preview(path: Path) -> tuple[pd.DataFrame | None, str | None]:
    suffix = path.suffix.lower()
    try:
        if suffix in {".csv", ".txt"}:
            return pd.read_csv(path, nrows=200), None
        if suffix in {".xlsx", ".xls"}:
            return pd.read_excel(path, nrows=200), None
    except Exception as exc:  # noqa: BLE001
        return None, str(exc)
    return None, None


def map_columns(columns: list[str], synonyms: dict[str, list[str]]) -> dict[str, str]:
    normalized = {normalize_header(column): column for column in columns}
    mapped = {}
    for canonical, options in synonyms.items():
        for option in options:
            key = normalize_header(option)
            if key in normalized:
                mapped[canonical] = normalized[key]
                break
    return mapped


def normalize_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value).strip().lower()).strip()


def best_by_dataset(classified: list[dict]) -> dict[str, dict]:
    result = {}
    for item in classified:
        dataset = item["classification"]
        if dataset == "unknown":
            continue
        if dataset not in result or item["confidence"] > result[dataset]["confidence"]:
            result[dataset] = item
    return result


def readiness_score(classified: list[dict]) -> dict:
    datasets = best_by_dataset(classified)
    score = 0
    notes = []
    if "workers" in datasets:
        score += 30
    else:
        notes.append("Need a people roster.")
    if "jobsites" in datasets:
        score += 30
    else:
        notes.append("Need an active jobs/projects list.")
    if "assignments" in datasets:
        score += 18
    else:
        notes.append("Assignments missing; AMDEP can still propose an optimized plan, but cannot compare against current staffing.")
    if "certifications" in datasets or ("workers" in datasets and "certifications" in datasets["workers"]["mapped_columns"]):
        score += 10
    else:
        notes.append("Certification data missing; OSHA/cert checks will be weaker.")
    if "assets" in datasets:
        score += 5
    if all(dataset in datasets for dataset in ["workers", "jobsites"]):
        score += 7
    status = "ready_for_audit" if score >= 67 and all(dataset in datasets for dataset in ["workers", "jobsites"]) else "intake_needed"
    return {"score": min(score, 100), "status": status, "notes": notes}


def write_intake_summary(workspace: Path, summary: dict) -> None:
    (workspace / "intake_summary.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    lines = [
        "# AMDEP Field Kit Intake Summary",
        "",
        f"- Workspace: `{summary['workspace']}`",
        f"- Readiness: {summary['readiness']['score']} ({summary['readiness']['status']})",
        f"- Files: {len(summary['files'])}",
        "",
        "## Files",
        "",
    ]
    for item in summary["files"]:
        lines.append(f"- `{item['file']}` -> {item['label']} ({item['confidence']:.0%})")
    lines.extend(["", "## Notes", ""])
    lines.extend(f"- {note}" for note in summary["readiness"]["notes"] or ["No immediate blockers found."])
    (workspace / "intake_summary.md").write_text("\n".join(lines), encoding="utf-8")


def materialize_normalized_bundle(workspace: Path, summary: dict) -> dict[str, Path]:
    datasets = summary["datasets"]
    if "workers" not in datasets or "jobsites" not in datasets:
        raise ValueError("Need at least a people roster and active jobs/projects file before running an audit.")
    normalized_dir = workspace / "normalized"
    normalized_dir.mkdir(parents=True, exist_ok=True)
    normalize_workers(datasets["workers"]).to_csv(normalized_dir / "workers.csv", index=False)
    normalize_jobsites(datasets["jobsites"]).to_csv(normalized_dir / "jobsites.csv", index=False)
    paths = {"workers": normalized_dir / "workers.csv", "jobsites": normalized_dir / "jobsites.csv"}
    if "assignments" in datasets:
        normalize_assignments(datasets["assignments"]).to_csv(normalized_dir / "assignments.csv", index=False)
        paths["assignments"] = normalized_dir / "assignments.csv"
    if "assets" in datasets:
        normalize_assets(datasets["assets"]).to_csv(normalized_dir / "assets.csv", index=False)
        paths["assets"] = normalized_dir / "assets.csv"
    return paths


def write_local_command_center(workspace: Path, packet_dir: Path, normalized_paths: dict[str, Path], economics: dict) -> Path:
    """Create a local command center using the same web UI as the demo, backed by this audit packet."""
    command_dir = workspace / "command_center"
    docs_dir = workspace / "docs"
    source_web = repo_root() / "web"
    if command_dir.exists():
        shutil.rmtree(command_dir)
    shutil.copytree(source_web, command_dir, ignore=shutil.ignore_patterns("demo-data.json"))
    docs_dir.mkdir(parents=True, exist_ok=True)
    for doc_name in ["DEMO_METHODOLOGY_AND_DEPLOYMENT.md", "FIELD_KIT_MODEL_CARD.md", "FIELD_KIT_MVP.md"]:
        source_doc = repo_root() / "docs" / doc_name
        if source_doc.exists():
            shutil.copy2(source_doc, docs_dir / doc_name)
    write_command_center_data(packet_dir, normalized_paths, command_dir / "demo-data.json", economics)
    return command_dir


def write_command_center_data(packet_dir: Path, normalized_paths: dict[str, Path], target_path: Path, economics: dict) -> Path:
    table_paths = {
        "workers": normalized_paths["workers"],
        "jobsites": normalized_paths["jobsites"],
        "baseline": packet_dir / "baseline_assignments.csv",
        "optimized": packet_dir / "optimized_assignments.csv",
        "waste": packet_dir / "top_waste_findings.csv",
        "burden": packet_dir / "personnel_burden.csv",
        "staffing": packet_dir / "job_staffing_status.csv",
        "robotics": packet_dir / "robotics_plan.csv",
        "trials": packet_dir / "calibration_trials.csv",
        "weights": packet_dir / "recommended_weights.csv",
        "recommendations": packet_dir / "integrations" / "recommendations_generic.csv",
    }
    payload = {
        "disclaimer": "Customer-provided copied exports normalized locally by AMDEP Field Kit. Review recommendations before any operational change.",
        "economics": economics,
        "tables": {},
    }
    for name, path in table_paths.items():
        try:
            frame = pd.read_csv(path)
        except (FileNotFoundError, pd.errors.EmptyDataError):
            frame = pd.DataFrame()
        payload["tables"][name] = frame.where(pd.notna(frame), "").to_dict("records")
    target_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return target_path


def normalize_workers(item: dict) -> pd.DataFrame:
    frame = read_full_table(Path(item["path"]))
    mapped = item["mapped_columns"]
    result = pd.DataFrame()
    result["personnel_id"] = source_or_sequence(frame, mapped.get("personnel_id"), "P")
    result["name"] = source_or_default(frame, mapped.get("name"), result["personnel_id"])
    result["role"] = source_or_default(frame, mapped.get("role"), "project staff")
    location_hints = build_location_hints(
        frame,
        mapped,
        ["home_address", "home_city", "home_state", "home_zip", "home_region"],
    )
    resolved_locations = location_hints.map(resolve_location)
    result["home_region"] = source_or_default(frame, mapped.get("home_region"), [item[2] for item in resolved_locations])
    result["home_lat"] = numeric_or_default(frame, mapped.get("home_lat"), [item[0] for item in resolved_locations])
    result["home_lon"] = numeric_or_default(frame, mapped.get("home_lon"), [item[1] for item in resolved_locations])
    result["home_city"] = source_or_default(frame, mapped.get("home_city"), [item[2].split(",")[0] for item in resolved_locations])
    result["skills"] = source_or_default(frame, mapped.get("skills"), result["role"])
    result["certifications"] = source_or_default(frame, mapped.get("certifications"), "OSHA 30")
    result["crew_id"] = source_or_default(frame, mapped.get("crew_id"), "")
    result["supervisor_id"] = source_or_default(frame, mapped.get("supervisor_id"), "")
    return result


def normalize_jobsites(item: dict) -> pd.DataFrame:
    frame = read_full_table(Path(item["path"]))
    mapped = item["mapped_columns"]
    result = pd.DataFrame()
    result["jobsite_id"] = source_or_sequence(frame, mapped.get("jobsite_id"), "J")
    result["name"] = source_or_default(frame, mapped.get("name"), result["jobsite_id"])
    location_hints = build_location_hints(frame, mapped, ["address", "city", "state", "zip", "region"])
    resolved_locations = location_hints.map(resolve_location)
    result["region"] = source_or_default(frame, mapped.get("region"), [item[2] for item in resolved_locations])
    result["lat"] = numeric_or_default(frame, mapped.get("lat"), [item[0] for item in resolved_locations])
    result["lon"] = numeric_or_default(frame, mapped.get("lon"), [item[1] for item in resolved_locations])
    result["city"] = source_or_default(frame, mapped.get("city"), [item[2].split(",")[0] for item in resolved_locations])
    result["required_headcount"] = numeric_or_default(frame, mapped.get("required_headcount"), 1).astype(int).clip(lower=1)
    result["required_skills"] = source_or_default(frame, mapped.get("required_skills"), "project manager")
    result["required_certifications"] = source_or_default(frame, mapped.get("required_certifications"), "OSHA 30")
    result["phase"] = source_or_default(frame, mapped.get("phase"), "production")
    result["urgency"] = numeric_or_default(frame, mapped.get("urgency"), 3).astype(int).clip(lower=1, upper=5)
    return result


def normalize_assignments(item: dict) -> pd.DataFrame:
    frame = read_full_table(Path(item["path"]))
    mapped = item["mapped_columns"]
    result = pd.DataFrame()
    result["personnel_id"] = source_or_default(frame, mapped.get("personnel_id"), "")
    result["jobsite_id"] = source_or_default(frame, mapped.get("jobsite_id"), "")
    result["supervisor_id"] = source_or_default(frame, mapped.get("supervisor_id"), "")
    result["crew_id"] = source_or_default(frame, mapped.get("crew_id"), "")
    result = result.loc[(result["personnel_id"].astype(str) != "") & (result["jobsite_id"].astype(str) != "")]
    return result


def normalize_assets(item: dict) -> pd.DataFrame:
    frame = read_full_table(Path(item["path"]))
    mapped = item["mapped_columns"]
    result = pd.DataFrame()
    result["asset_id"] = source_or_sequence(frame, mapped.get("asset_id"), "A")
    result["asset_kind"] = source_or_default(frame, mapped.get("asset_kind"), "equipment")
    result["asset_type"] = source_or_default(frame, mapped.get("asset_type"), "field asset")
    result["home_region"] = source_or_default(frame, mapped.get("home_region"), "Unresolved market")
    result["available"] = source_or_default(frame, mapped.get("available"), True)
    return result


def read_full_table(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    return pd.read_csv(path)


def source_or_sequence(frame: pd.DataFrame, source: str | None, prefix: str) -> pd.Series:
    if source and source in frame:
        values = frame[source].fillna("").astype(str)
        return values.where(values.str.len() > 0, [f"{prefix}{idx + 1:04d}" for idx in range(len(frame))])
    return pd.Series([f"{prefix}{idx + 1:04d}" for idx in range(len(frame))])


def source_or_default(frame: pd.DataFrame, source: str | None, default) -> pd.Series:
    if source and source in frame:
        return frame[source].fillna("").astype(str)
    if isinstance(default, pd.Series):
        return default.astype(str)
    if isinstance(default, list):
        return pd.Series(default).astype(str)
    return pd.Series([default for _ in range(len(frame))])


def numeric_or_default(frame: pd.DataFrame, source: str | None, default) -> pd.Series:
    if source and source in frame:
        series = pd.to_numeric(frame[source], errors="coerce")
    else:
        series = pd.Series([None for _ in range(len(frame))], dtype="float64")
    default_series = pd.Series(default if isinstance(default, list) else [default for _ in range(len(frame))])
    return series.fillna(pd.to_numeric(default_series, errors="coerce")).fillna(0)


def build_location_hints(frame: pd.DataFrame, mapped: dict[str, str], keys: list[str]) -> pd.Series:
    hints = []
    for _, row in frame.iterrows():
        parts = []
        for key in keys:
            source = mapped.get(key)
            if not source or source not in frame.columns:
                continue
            value = row.get(source, "")
            if pd.notna(value) and str(value).strip():
                parts.append(str(value).strip())
        hints.append(" ".join(parts))
    return pd.Series(hints, dtype="string")


def resolve_location(value: object) -> tuple[float, float, str]:
    text = str(value or "").strip()
    lower = text.lower()
    coordinate_match = COORDINATE_RE.search(lower)
    if coordinate_match:
        lat = float(coordinate_match.group(1))
        lon = float(coordinate_match.group(2))
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            return lat, lon, text
    normalized = normalize_location_text(lower)
    for token, resolved in sorted(LOCATION_DEFAULTS.items(), key=lambda item: len(item[0]), reverse=True):
        if normalize_location_text(token) in normalized:
            return resolved[:3]
    tokens = set(normalized.split())
    for abbrev, state_name in STATE_ALIASES.items():
        if abbrev in tokens:
            return STATE_CENTROIDS[state_name]
    for state_name, resolved in STATE_CENTROIDS.items():
        if state_name in normalized:
            return resolved
    return DEFAULT_GEO


def normalize_location_text(value: str) -> str:
    value = value.replace(".", " ")
    value = value.replace(",", " ")
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def safe_filename(filename: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._ -]+", "_", Path(filename).name).strip()
    return cleaned or "uploaded_file"


if __name__ == "__main__":
    main()
