#!/usr/bin/env bash
# Rebuild every number and figure.
#   ./run_all.sh           full rebuild from raw data (needs SOURCE_DATA, see data/DATA.md)
#   ./run_all.sh --quick   figures and one-pager only, from the aggregates shipped in data/
set -euo pipefail
cd "$(dirname "$0")"
PY="$(pwd)/${PYTHON:-.venv/bin/python}"

if [[ "${1:-}" != "--quick" ]]; then
  : "${SOURCE_DATA:?set SOURCE_DATA to your raw data folder (see data/DATA.md), or run with --quick}"
  "$PY" analysis/crosswalk.py      # Understat <-> Transfermarkt matches and players
  "$PY" analysis/minutes.py        # who was on the pitch, minute by minute
  "$PY" analysis/build_panel.py    # player-season panel
  "$PY" analysis/analyse.py        # within-player tests, curve, reliability
  "$PY" analysis/transfers.py      # movers v stayers, luck benchmark, slices, flop predictor
  "$PY" analysis/chemistry.py      # pair chemistry from shot assists
  "$PY" analysis/statsbomb.py      # StatsBomb 2015-16 passes and minutes (downloads once)
  "$PY" analysis/sb_check.py       # minutes check, pass-level chemistry, links agreement
fi
"$PY" analysis/figures.py

# self-checks: small synthetic cases with known answers
for m in crosswalk minutes chemistry; do
  (cd analysis && "$PY" "$m.py" check > /dev/null) && echo "self-check ok: $m"
done
for m in usage wowy understat talent; do
  PYTHONPATH=src "$PY" -m "usage_model.$m" > /dev/null && echo "self-check ok: $m"
done
# every number quoted in the README against the tables in data/
"$PY" analysis/verify.py
