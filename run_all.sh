#!/usr/bin/env bash
# Rebuild every number and figure. Needs SOURCE_DATA set (see data/DATA.md).
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-.venv/bin/python}"
: "${SOURCE_DATA:?set SOURCE_DATA to your raw data folder (see data/DATA.md)}"
"$PY" analysis/build_panel.py
"$PY" analysis/analyse.py
"$PY" analysis/decompose.py
"$PY" analysis/figures.py
for m in usage wowy understat talent; do
  PYTHONPATH=src "$PY" -m "usage_model.$m" > /dev/null && echo "self-check ok: $m"
done
