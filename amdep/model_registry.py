"""Tiny model registry for synthetic AmDep Brain Layer models."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib

from amdep.utils import repo_root


def default_model_dir() -> Path:
    path = repo_root() / "models"
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_registry(registry: dict[str, Any], path: Path | None = None) -> Path:
    target = path or default_model_dir() / "synthetic_brain.joblib"
    target.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(registry, target)
    return target


def load_registry(path: Path | None = None) -> dict[str, Any]:
    target = path or default_model_dir() / "synthetic_brain.joblib"
    return joblib.load(target)


def registry_exists(path: Path | None = None) -> bool:
    target = path or default_model_dir() / "synthetic_brain.joblib"
    return target.exists()

