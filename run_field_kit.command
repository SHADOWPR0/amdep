#!/bin/zsh
set -e
cd "$(dirname "$0")"

python_missing_message() {
  echo ""
  echo "AMDEP Field Kit needs Python 3.11 or newer."
  echo ""
  echo "Install Python from:"
  echo "  https://www.python.org/downloads/"
  echo ""
  echo "After installing Python, double-click run_field_kit.command again."
  echo ""
}

if ! command -v python3 >/dev/null 2>&1; then
  python_missing_message
  exit 1
fi

if ! python3 - <<'PY' >/dev/null 2>&1
import sys
raise SystemExit(0 if sys.version_info >= (3, 11) else 1)
PY
then
  python_missing_message
  python3 --version || true
  exit 1
fi

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
  .venv/bin/python -m pip install --upgrade pip
  .venv/bin/python -m pip install -r requirements.txt
fi
.venv/bin/python -m amdep.field_kit
