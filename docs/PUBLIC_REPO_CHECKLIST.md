# Public Repo Checklist

Before sharing publicly:

- Keep only synthetic data in `data/`.
- Keep only generated demo reports in `reports/` if you want examples.
- Do not commit `.venv/`, caches, secrets, customer files, model weights, or private connector credentials.
- Do not commit proprietary calibrated policies.
- Do not commit customer-specific benchmarks.
- Keep `LICENSE`, `NOTICE`, and `COMMERCIAL.md`.
- Run `./run_demo.sh` from a clean environment.
- Confirm `reports/demo_audit/dispatch_audit_summary.html` opens locally.
- Confirm `python -m compileall amdep config.py` passes.

The public package should prove competence without giving away private operating leverage.
