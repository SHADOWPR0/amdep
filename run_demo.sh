#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
pip install -r requirements.txt
python -m amdep.run_audit \
  --workers data/sample_workers.csv \
  --jobsites data/sample_jobsites.csv \
  --assignments data/sample_assignments.csv \
  --assets data/sample_assets.csv \
  --output reports/demo_audit \
  --trials 18

echo
echo "Audit packet written to: $(pwd)/reports/demo_audit"
echo "Open reports/demo_audit/dispatch_audit_summary.html in a browser or dispatch_audit_summary.md in any markdown viewer."
