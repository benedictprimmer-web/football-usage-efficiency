"""Paths and constants shared by the analysis scripts."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

# raw third-party data lives outside git; point SOURCE_DATA at your copy
SOURCE = Path(os.environ.get("SOURCE_DATA", ROOT / "data" / "raw")).expanduser()
WORK = ROOT / "data" / "work"          # per-player intermediates, gitignored
OUT = ROOT / "data"                    # small aggregate outputs, committed
FIG = ROOT / "figures"

# Transfermarkt league competition ids for the six Understat leagues
LEAGUE_COMPS = {"GB1", "ES1", "IT1", "L1", "FR1", "RU1"}

MIN_MINUTES = 900                      # ten full matches; see README for why
SEED = 0
N_BOOT = 2000

CASES = {  # Transfermarkt id -> display name
    167850: "Memphis Depay",
    182877: "Anthony Martial",
    8198: "Cristiano Ronaldo",
}
