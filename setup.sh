#!/usr/bin/env bash
# Create the project virtualenv and install dependencies.
#   ./setup.sh            then   source .venv/bin/activate
set -euo pipefail
cd "$(dirname "$0")"
PY=${PYTHON:-python3}
"$PY" -c 'import sys; assert sys.version_info >= (3, 11), "Need Python 3.11+"'
[ -d .venv ] || "$PY" -m venv .venv
.venv/bin/pip install --upgrade pip -q
.venv/bin/pip install -r requirements.txt -q
echo "Done. Activate with: source .venv/bin/activate"
