"""Paths and constants shared by the analysis scripts."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

# raw third-party data lives outside git; point SOURCE_DATA at your copy
SOURCE = Path(os.environ.get("SOURCE_DATA", ROOT / "data" / "raw")).expanduser()
# SHOTS=opta runs the same pipeline on FBref/Opta shots for seven leagues (fbref.py),
# writing to its own folders so the Understat results are untouched
OPTA = os.environ.get("SHOTS", "understat") == "opta"
WORK = ROOT / "data" / ("work_opta" if OPTA else "work")   # per-player intermediates, gitignored
OUT = ROOT / "data" / "opta" if OPTA else ROOT / "data"    # small aggregate outputs, committed
FIG = ROOT / "figures"
SHOTS_FILE = ("opta" if OPTA else "understat") + "/shots.parquet"

# Transfermarkt league competition ids for the six Understat leagues
LEAGUE_COMPS = {"GB1", "ES1", "IT1", "L1", "FR1", "RU1"}
# leagues whose line-ups and substitutions Transfermarkt covers in full
TM_LEAGUES = {"GB1": "ENG-Premier League", "ES1": "ESP-La Liga", "IT1": "ITA-Serie A",
              "L1": "GER-Bundesliga", "FR1": "FRA-Ligue 1"}
if OPTA:
    TM_LEAGUES |= {"PO1": "POR-Primeira Liga", "NL1": "NED-Eredivisie"}

MIN_MINUTES = 900                      # ten full matches; see README for why
SEED = 0
N_BOOT = 2000

CASES = {  # Transfermarkt id -> display name
    167850: "Memphis Depay",
    182877: "Anthony Martial",
    8198: "Cristiano Ronaldo",
}
