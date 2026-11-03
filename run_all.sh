#!/usr/bin/env bash
# Rebuild every number and figure. Needs SOURCE_DATA set (see data/DATA.md).
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-.venv/bin/python}"
"$PY" analysis/build_panel.py
"$PY" analysis/analyse.py
"$PY" analysis/figures.py
