"""CLI entrypoint for training the synthetic AmDep Brain Layer."""

from __future__ import annotations

from config import DEFAULT_SEED
from amdep.brain import train_synthetic_brain
from amdep.model_registry import save_registry
from amdep.synthetic_data import generate_synthetic_company


def main() -> None:
    workers, jobs, _assets = generate_synthetic_company(seed=DEFAULT_SEED)
    brain = train_synthetic_brain(workers, jobs, seed=DEFAULT_SEED)
    path = save_registry({"brain": brain, "seed": DEFAULT_SEED, "synthetic_only": True})
    print(f"Saved synthetic Brain Layer registry to {path}")


if __name__ == "__main__":
    main()

