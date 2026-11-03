"""Who was on the pitch, minute by minute: true on-pitch share and true shared minutes.

The first version of this repo estimated a player's share of the ball while on the
pitch from season totals. This script measures it. Transfermarkt line-ups give the
starters, its match events give every substitution and red card, so each player has
an on and off minute in every league match. Understat gives the minute of every shot.
Together they say which shots and shot-assists his team made while he was on.

Writes to data/work/ (gitignored):
    intervals.parquet    one row per player per league match: club, on, off
    onpitch.parquet      per player-club-season: minutes, and the team's actions and
                         xG+xA while he was on the pitch
    pair_minutes.parquet per pair of team-mates per club-season: minutes on together

    python analysis/minutes.py   (after crosswalk.py)
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from config import SOURCE, WORK
from crosswalk import tm_games

TM = SOURCE / "transfermarkt"


def intervals(games: pd.DataFrame) -> pd.DataFrame:
    """On and off minute for every player who played a league match."""
    ids = set(games.game_id)
    lu = pd.read_csv(TM / "game_lineups.csv.gz",
                     usecols=["game_id", "player_id", "club_id", "type"])
    lu = lu[lu.game_id.isin(ids)].drop_duplicates(["game_id", "player_id"])
    ev = pd.read_csv(TM / "game_events.csv.gz",
                     usecols=["game_id", "minute", "type", "club_id", "player_id",
                              "player_in_id", "description"])
    ev = ev[ev.game_id.isin(ids)]
    end = ev.groupby("game_id").minute.max().clip(lower=90).rename("end")

    subs = ev[ev.type == "Substitutions"]
    reds = ev[(ev.type == "Cards")
              & ev.description.fillna("").str.contains("Red card|Second yellow", case=False)]
    on = pd.concat([
        lu[lu.type == "starting_lineup"].assign(on=0.0)[["game_id", "player_id", "club_id", "on"]],
        subs.dropna(subset=["player_in_id"]).assign(player_id=lambda x: x.player_in_id.astype(int))
            .assign(on=lambda x: x.minute.astype(float))[["game_id", "player_id", "club_id", "on"]],
    ]).drop_duplicates(["game_id", "player_id"])
    off = (pd.concat([subs[["game_id", "player_id", "minute"]],
                      reds[["game_id", "player_id", "minute"]]])
             .groupby(["game_id", "player_id"]).minute.min().rename("off"))
    iv = on.join(off, on=["game_id", "player_id"]).join(end, on="game_id")
    iv["off"] = iv.off.fillna(iv.end).clip(upper=iv.end)
    iv = iv[iv.off > iv.on].drop(columns="end")
    return iv.merge(games[["game_id", "league", "season"]], on="game_id")


def team_actions(shots: pd.DataFrame, mx: pd.DataFrame, games: pd.DataFrame) -> pd.DataFrame:
    """Understat actions (shots and shot-assists, no penalties or own goals) keyed to
    Transfermarkt game and club ids, with the minute they happened."""
    s = shots[(shots.result != "OwnGoal") & (shots.situation != "Penalty")]
    s = s.merge(mx[["us_game_id", "tm_game_id"]], left_on="game_id", right_on="us_game_id")
    s = s.merge(games[["game_id", "home_club_id", "away_club_id"]],
                left_on="tm_game_id", right_on="game_id", suffixes=("", "_tm"))
    s["club_id"] = np.where(s.team_shot == s.home_team, s.home_club_id, s.away_club_id)
    # an assisted shot is two actions, the shot and the shot-assist, each worth its xG
    s["n"] = 1 + s.player_assisted.notna()
    s["v"] = s.xg * s.n
    return s[["tm_game_id", "club_id", "minute", "half", "n", "v"]].rename(
        columns={"tm_game_id": "game_id"})


def halves(shots: pd.DataFrame) -> np.ndarray:
    """0/1 per shot: alternate each team's league matches by date (odd/even)."""
    g = (shots[["league", "season", "team_shot", "game_id", "date"]]
         .drop_duplicates(["league", "season", "team_shot", "game_id"])
         .sort_values("date"))
    g["half"] = g.groupby(["league", "season", "team_shot"]).cumcount() % 2
    m = shots.merge(g[["league", "season", "team_shot", "game_id", "half"]],
                    on=["league", "season", "team_shot", "game_id"], how="left")
    return m.half.to_numpy()


def onpitch(iv: pd.DataFrame, acts: pd.DataFrame) -> pd.DataFrame:
    """Per player-club-season: minutes, and the team's actions and value while he was on,
    in total and on odd and even matches separately."""
    m = iv.merge(acts, on=["game_id", "club_id"])
    m = m[(m.minute >= m.on) & (m.minute < m.off)]
    on = m.groupby(["player_id", "club_id", "season"]).agg(
        team_actions_on=("n", "sum"), team_value_on=("v", "sum"))
    for h in (0, 1):
        on[f"team_actions_on_h{h}"] = (m[m.half == h].groupby(["player_id", "club_id", "season"])
                                       .n.sum())
    mins = (iv.assign(mins=iv.off - iv.on)
              .groupby(["player_id", "club_id", "season"])
              .agg(minutes_on=("mins", "sum"), games_on=("game_id", "nunique")))
    out = mins.join(on).reset_index()
    return out.fillna({c: 0 for c in out.columns if c.startswith("team_")})


def pair_minutes(iv: pd.DataFrame) -> pd.DataFrame:
    """Minutes each pair of team-mates spent on the pitch together, per club-season."""
    a = iv[["game_id", "club_id", "season", "player_id", "on", "off"]]
    p = a.merge(a, on=["game_id", "club_id", "season"], suffixes=("_a", "_b"))
    p = p[p.player_id_a < p.player_id_b]
    p["together"] = (np.minimum(p.off_a, p.off_b) - np.maximum(p.on_a, p.on_b)).clip(lower=0)
    return (p.groupby(["club_id", "season", "player_id_a", "player_id_b"])
              .agg(minutes_together=("together", "sum"), games=("game_id", "nunique"))
              .reset_index())


def build():
    shots = pd.read_parquet(SOURCE / "understat" / "shots.parquet")
    shots = shots.assign(half=halves(shots))
    mx = pd.read_parquet(WORK / "crosswalk_matches.parquet")
    # only matches both sources hold, so minutes and shots cover the same games
    games = tm_games()
    games = games[games.game_id.isin(mx.tm_game_id)]
    iv = intervals(games)
    iv.to_parquet(WORK / "intervals.parquet", index=False)
    op = onpitch(iv, team_actions(shots, mx, games))
    op.to_parquet(WORK / "onpitch.parquet", index=False)
    pm = pair_minutes(iv)
    pm.to_parquet(WORK / "pair_minutes.parquet", index=False)
    print(f"intervals: {len(iv):,} player-matches in {iv.game_id.nunique():,} league games")
    print(f"on-pitch: {len(op):,} player-club-seasons; pairs: {len(pm):,}")
    # sanity: a full match is 90+ minutes; starters who finish should sum to ~11 x 90
    per_game = iv.assign(m=iv.off - iv.on).groupby(["game_id", "club_id"]).m.sum()
    print(f"median team minutes per match: {per_game.median():.0f} (11 x 90 = 990, plus stoppage)")


def _check():
    iv = pd.DataFrame({"game_id": [1, 1, 1], "club_id": [9, 9, 9], "season": ["s"] * 3,
                       "player_id": [1, 2, 3], "on": [0.0, 0.0, 60.0], "off": [94.0, 60.0, 94.0]})
    acts = pd.DataFrame({"game_id": [1, 1, 1], "club_id": [9, 9, 9], "half": [0, 0, 0],
                         "minute": [10, 60, 80], "n": [1, 2, 1], "v": [.1, .4, .3]})
    op = onpitch(iv, acts).set_index("player_id")
    assert op.loc[1, "team_actions_on"] == 4 and op.loc[2, "team_actions_on"] == 1
    assert op.loc[3, "team_actions_on"] == 3 and op.loc[3, "minutes_on"] == 34
    pm = pair_minutes(iv).set_index(["player_id_a", "player_id_b"]).minutes_together
    assert pm[(1, 2)] == 60 and pm[(1, 3)] == 34 and pm[(2, 3)] == 0
    print("ok")


if __name__ == "__main__":
    import sys
    _check() if "check" in sys.argv[1:] else build()
