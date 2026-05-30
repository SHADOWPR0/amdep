"""Build a local AMDEP Field Kit zip without customer data."""

from __future__ import annotations

import shutil
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
PACKAGE_ROOT = DIST / "amdep-field-kit"
ZIP_PATH = DIST / "amdep-field-kit.zip"

INCLUDE_PATHS = [
    "amdep",
    "api",
    "config.py",
    "data",
    "docs",
    "field_kit",
    "foundry_ready",
    "index.html",
    "LICENSE",
    "NOTICE",
    "pyproject.toml",
    "README.md",
    "requirements.txt",
    "run_demo.sh",
    "run_field_kit.bat",
    "run_field_kit.command",
    "tests",
    "web",
]

EXCLUDED_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "dist",
    "field_kit_workspace",
    "models",
}


def main() -> None:
    if PACKAGE_ROOT.exists():
        shutil.rmtree(PACKAGE_ROOT)
    PACKAGE_ROOT.mkdir(parents=True)
    for relative in INCLUDE_PATHS:
        source = ROOT / relative
        if not source.exists():
            continue
        target = PACKAGE_ROOT / relative
        if source.is_dir():
            shutil.copytree(source, target, ignore=ignore_package_noise)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    write_package_readme()
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(PACKAGE_ROOT.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(DIST))
    shutil.rmtree(PACKAGE_ROOT)
    print(ZIP_PATH)


def ignore_package_noise(_directory: str, names: list[str]) -> set[str]:
    ignored = set()
    for name in names:
        if name in EXCLUDED_PARTS or name.endswith((".pyc", ".pyo", ".log")):
            ignored.add(name)
    return ignored


def write_package_readme() -> None:
    text = """# AMDEP Field Kit

Local read-only staffing intake and audit package.

## Who Should Install It

This is a technical handoff kit, not an app store install. An FDE, internal IT lead, ops analyst, or reasonably technical project-controls person should run the first install.

The kit needs:

- Python 3.11 or newer.
- Internet access for the first dependency install, unless IT preloads the Python packages.
- Permission to create a local `.venv` folder inside the unzipped package.

## macOS

Double-click `run_field_kit.command`, or run:

```bash
./run_field_kit.command
```

## Windows

Double-click `run_field_kit.bat`.

If Python is missing, install Python from:

```text
https://www.python.org/downloads/windows/
```

During install, check "Add python.exe to PATH" if shown.

## If It Does Not Start

If the launcher stops on a company machine, IT may need to approve Python, the local `.venv` folder, or package installation from `requirements.txt`.

## Browser

The launcher opens:

```text
http://127.0.0.1:8095/
```

Drop copied exports into the intake UI. The kit writes all private working files under `field_kit_workspace/`, which is intentionally excluded from Git and package builds.

## Model Notes

Read `docs/FIELD_KIT_MODEL_CARD.md` before presenting output as anything more than a local read-only pilot. First-run results use synthetic risk scoring unless customer outcome labels are provided.

Default policy weights live in `config.py`. Every audit run writes calibrated/recommended weights to:

```text
field_kit_workspace/reports/audit_*/recommended_weights.csv
field_kit_workspace/reports/audit_*/calibration_trials.csv
```
"""
    (PACKAGE_ROOT / "FIELD_KIT_README.md").write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
