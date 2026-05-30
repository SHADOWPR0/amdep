from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from amdep.audit_pipeline import run_csv_audit
from amdep.ingestion import load_customer_bundle, normalize_bundle


ROOT = Path(__file__).resolve().parents[1]


class PartialInputAuditTests(unittest.TestCase):
    def test_workers_jobs_only_builds_clean_empty_assets_frame(self) -> None:
        frames = load_customer_bundle(
            workers_path=ROOT / "data" / "sample_workers.csv",
            jobsites_path=ROOT / "data" / "sample_jobsites.csv",
        )

        normalized = normalize_bundle(frames)

        assets = normalized["assets"]
        self.assertTrue(assets.empty)
        self.assertIn("available", assets.columns)
        self.assertEqual(len(assets.columns), len(set(assets.columns)))

    def test_workers_jobs_only_audit_runs_without_assets_or_assignments(self) -> None:
        with TemporaryDirectory() as output_dir:
            result = run_csv_audit(
                workers_path=ROOT / "data" / "sample_workers.csv",
                jobsites_path=ROOT / "data" / "sample_jobsites.csv",
                output_dir=Path(output_dir),
                calibration_trials=1,
            )

            self.assertIn(result.optimizer_result["status"], {"OPTIMAL", "FEASIBLE"})
            self.assertEqual(result.robotics_summary["available_robots"], 0)
            self.assertTrue((Path(output_dir) / "dispatch_audit_summary.html").exists())

    def test_audit_reports_deployment_economics_from_simulated_before_after(self) -> None:
        with TemporaryDirectory() as output_dir:
            result = run_csv_audit(
                workers_path=ROOT / "data" / "sample_workers.csv",
                jobsites_path=ROOT / "data" / "sample_jobsites.csv",
                assignments_path=ROOT / "data" / "sample_assignments.csv",
                assets_path=ROOT / "data" / "sample_assets.csv",
                output_dir=Path(output_dir),
                calibration_trials=1,
            )

            economics = result.deployment_economics
            self.assertGreater(economics["annual_deployment_run_rate"], 0)
            self.assertGreater(economics["implementation_horizon_impact"], economics["annual_deployment_run_rate"])
            self.assertGreaterEqual(economics["retained_key_staff"], 0)
            self.assertIn("retention_value", economics)
            self.assertIn("compounding_value", economics)


if __name__ == "__main__":
    unittest.main()
