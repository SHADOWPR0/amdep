from __future__ import annotations

import shutil
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from amdep.field_kit import analyze_workspace, materialize_normalized_bundle


ROOT = Path(__file__).resolve().parents[1]


class FieldKitTests(unittest.TestCase):
    def test_field_kit_classifies_sample_bundle_and_materializes_normalized_csvs(self) -> None:
        with TemporaryDirectory() as workspace_dir:
            workspace = Path(workspace_dir)
            inbox = workspace / "inbox"
            inbox.mkdir(parents=True)
            for filename in ["sample_workers.csv", "sample_jobsites.csv", "sample_assignments.csv", "sample_assets.csv"]:
                shutil.copy2(ROOT / "data" / filename, inbox / filename)

            summary = analyze_workspace(workspace)
            paths = materialize_normalized_bundle(workspace, summary)

            self.assertEqual(summary["readiness"]["status"], "ready_for_audit")
            self.assertGreaterEqual(summary["readiness"]["score"], 90)
            self.assertEqual(set(paths), {"workers", "jobsites", "assignments", "assets"})
            for path in paths.values():
                self.assertTrue(path.exists())


if __name__ == "__main__":
    unittest.main()
