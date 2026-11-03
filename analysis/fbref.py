"""FBref/Opta shots for seven leagues, in the same shape as the Understat shots.

Understat covers only the Big-5 (and Russia). FBref carried Opta's shot-level xG for many
more leagues until January 2026, and the worldfootballR_data archive kept it (release
`fb_match_shooting`). This script turns the files for the Big-5, Portugal and the
Eredivisie into the schema the rest of the pipeline reads, so every test can be rerun on
a second xG provider and on moves from two big selling leagues.

The shot-assist is the player behind the shot's first shot-creating action when that
action is a pass, which is how Opta defines a key pass. FBref gives the passer by name
only, so he is matched to a player id within the team-season, as with Understat.

Reads $SOURCE_DATA/fbref/<LEAGUE>_M_1st_match_shooting.csv, writes
$SOURCE_DATA/opta/shots.parquet. Then run the pipeline with SHOTS=opta.

    python analysis/fbref.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from config import SOURCE

LEAGUES = {"ENG": "ENG-Premier League", "ESP": "ESP-La Liga", "ITA": "ITA-Serie A",
           "GER": "GER-Bundesliga", "FRA": "FRA-Ligue 1", "POR": "POR-Primeira Liga",
           "NED": "NED-Eredivisie"}


# FBref short names that the crosswalk's automatic passes cannot place ("Paris S-G"
# normalises to "paris", which is Paris FC)
CLUBS = {"Paris S-G": "Paris Saint-Germain", "West Brom": "West Bromwich Albion",
         "Gladbach": "Borussia Mönchengladbach", "M'Gladbach": "Borussia Mönchengladbach",
         "Fortuna Sittard": "Fortuna Sittardia Combinatie"}


def _code(href: pd.Series) -> pd.Series:
    """'/en/players/173db1f4/Leo-Jaba' -> 0x173db1f4 as an integer id."""
    return href.str.extract(r"/players/([0-9a-f]{8})/")[0].map(
        lambda c: int(c, 16) if isinstance(c, str) else np.nan)


def tidy(raw: pd.DataFrame, league: str) -> pd.DataFrame:
    d = raw.copy()
    d["Squad"] = d.Squad.replace(CLUBS)
    d["game_id"] = d.MatchURL.str.extract(r"/matches/([0-9a-f]{8})/")[0]
    teams = (d.groupby(["game_id", "Home_Away"]).Squad.first().unstack())
    d = d.join(teams.rename(columns={"Home": "home_team", "Away": "away_team"}), on="game_id")
    y = d.Season_End_Year.astype(int)
    passed = d.Event_SCA_1.fillna("").str.startswith("Pass")
    notes = d.Notes.fillna("")
    # FBref does not label penalties: they are the shots from the spot (12-13 yards)
    # carrying Opta's fixed penalty xG of about 0.76-0.79
    dist, xg = pd.to_numeric(d.Distance, errors="coerce"), pd.to_numeric(d.xG, errors="coerce")
    pen = dist.between(11, 13) & xg.between(0.7, 0.8)
    out = pd.DataFrame({
        "league": league,
        "season": (y - 1).astype(str) + "-" + y.astype(str),
        "game_id": d.game_id,
        "team_shot": d.Squad,
        "home_team": d.home_team,
        "away_team": d.away_team,
        "minute": pd.to_numeric(d.Minute.astype(str).str.split("+").str[0], errors="coerce"),
        "xg": pd.to_numeric(d.xG, errors="coerce"),
        "player": d.Player,
        "player_assisted": d.Player_SCA_1.where(passed & (d.Player_SCA_1 != d.Player)),
        "result": np.where(d.Outcome.eq("Goal"), "Goal", d.Outcome.fillna("")),
        "situation": np.where(pen, "Penalty",
                              np.where(notes.str.contains("Free kick", case=False), "DirectFreekick",
                                       "OpenPlay")),
        "date": d.Date.astype(str),
        "player_id": _code(d.Player_Href).astype("Int64"),
    })
    return out.dropna(subset=["xg", "minute", "home_team", "away_team"]).reset_index(drop=True)


def build():
    frames = []
    for code, league in LEAGUES.items():
        raw = pd.read_csv(SOURCE / "fbref" / f"{code}_M_1st_match_shooting.csv", low_memory=False)
        t = tidy(raw, league)
        frames.append(t)
        print(f"{league}: {len(t):,} shots, {t.season.min()} to {t.season.max()}, "
              f"{t.player_assisted.notna().mean():.0%} with a shot-assist", flush=True)
    out = pd.concat(frames, ignore_index=True)
    (SOURCE / "opta").mkdir(exist_ok=True)
    out.to_parquet(SOURCE / "opta" / "shots.parquet", index=False)
    print(f"{len(out):,} shots to {out.date.max()}")


if __name__ == "__main__":
    build()
