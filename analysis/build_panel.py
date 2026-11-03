"""Build the player-season panel behind every number in this repo.

One row per (player, club, season): usage share and chance quality on the repo's own
definitions (src/usage_model/usage.py), the same two numbers on odd and even matches
separately (for the split-half checks), and, from Transfermarkt line-ups and
substitutions, the minutes he actually played and what his team did while he was on.

Reads raw third-party data from $SOURCE_DATA (see data/DATA.md) and the crosswalk and
minutes tables from data/work/. Writes data/work/panel.parquet, which is gitignored:
it holds per-player rows and is not redistributed.

    python analysis/build_panel.py   (after crosswalk.py and minutes.py)
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from config import SOURCE, WORK

from minutes import halves
from usage_model.usage import usage_efficiency  # noqa: E402

KEY = ["league", "season", "team", "player"]


def club_ids(mx: pd.DataFrame) -> pd.DataFrame:
    """Understat team name -> Transfermarkt club id, per league-season."""
    g = pd.read_csv(SOURCE / "transfermarkt" / "games.csv.gz",
                    usecols=["game_id", "home_club_id", "away_club_id"])
    m = mx.merge(g, left_on="tm_game_id", right_on="game_id")
    cols = ["league", "season", "team", "club_id"]
    t = pd.concat([m[["league", "season", "home", "home_club_id"]].set_axis(cols, axis=1),
                   m[["league", "season", "away", "away_club_id"]].set_axis(cols, axis=1)])
    return (t.groupby(["league", "season", "team"]).club_id
             .agg(lambda s: s.value_counts().idxmax()).reset_index())


def build() -> pd.DataFrame:
    shots = pd.read_parquet(SOURCE / "understat" / "shots.parquet")
    shots = shots[shots.league != "RUS-Premier League"]  # no Transfermarkt line-ups
    print(f"shots: {len(shots):,} to {shots.date.max()}")

    full = usage_efficiency(shots)
    shots = shots.assign(half=halves(shots))
    parts = []
    for h in (0, 1):
        u = usage_efficiency(shots[shots.half == h])
        parts.append(u.set_index(KEY)[["actions", "value", "usage_share", "efficiency"]]
                     .add_suffix(f"_h{h}"))
    u = full.set_index(KEY).join(parts[0]).join(parts[1]).reset_index()

    # team totals for the whole team-season
    team = u.groupby(["league", "season", "team"]).agg(
        team_value=("value", "sum"), team_actions=("actions", "sum"))
    gm = pd.concat([shots[["league", "season", c, "game_id"]].rename(columns={c: "team"})
                    for c in ("home_team", "away_team")]).drop_duplicates()
    team["team_games"] = gm.groupby(["league", "season", "team"]).game_id.nunique()
    u = u.merge(team.reset_index(), on=["league", "season", "team"])

    # Understat name -> Understat id within each team-season (a name alone can belong to
    # several players: three different "Gabriel"s) -> Transfermarkt id
    id_map = (shots.dropna(subset=["player_id"])
              .groupby(["league", "season", "team_shot", "player"])["player_id"]
              .agg(lambda s: s.value_counts().idxmax()).rename("us_player_id").reset_index()
              .rename(columns={"team_shot": "team"}))
    u = u.merge(id_map, on=KEY, how="left")
    px = pd.read_parquet(WORK / "crosswalk_players.parquet")
    u = u.merge(px[["us_player_id", "tm_player_id"]], on="us_player_id", how="left")

    # one club per season: keep the club holding >= 80% of the player's actions
    tot = u.groupby(["us_player_id", "season"]).actions.transform("sum")
    u["club_share"] = u.actions / tot
    u = u[(u.club_share >= 0.8) & u.tm_player_id.notna()].copy()
    u["tm_player_id"] = u.tm_player_id.astype(int)

    mx = pd.read_parquet(WORK / "crosswalk_matches.parquet")
    u = u.merge(club_ids(mx), on=["league", "season", "team"], how="left")

    players = pd.read_csv(SOURCE / "transfermarkt" / "players.csv.gz",
                          usecols=["player_id", "position", "sub_position", "date_of_birth"])
    u = u.merge(players.rename(columns={"player_id": "tm_player_id"}),
                on="tm_player_id", how="left")

    # measured minutes, and what the team did while he was on the pitch
    op = pd.read_parquet(WORK / "onpitch.parquet").rename(columns={"player_id": "tm_player_id"})
    u = u.merge(op, on=["tm_player_id", "club_id", "season"], how="left")
    u["minutes"] = u.minutes_on
    u["minutes_share"] = (u.minutes / (u.team_games * 90)).clip(upper=1)
    # his share of the team's actions while he was on (measured), and the old estimate
    u["usage_on_pitch"] = u.actions / u.team_actions_on.where(u.team_actions_on > 0)
    u["usage_on_pitch_est"] = u.usage_share / u.minutes_share
    # team-mates' chance quality, counting only what they did while he was on
    u["mates_eff"] = ((u.team_value_on - u.value)
                      / (u.team_actions_on - u.actions).where(lambda x: x > 0))
    u["mates_eff_season"] = (u.team_value - u.value) / (u.team_actions - u.actions)
    u["team_ap90_on"] = u.team_actions_on / u.minutes * 90
    for h in (0, 1):  # on-pitch share on odd and even matches, for the split-half test
        u[f"usage_on_pitch_h{h}"] = (u[f"actions_h{h}"]
                                     / u[f"team_actions_on_h{h}"].where(lambda x: x > 0))

    dob = pd.to_datetime(u.date_of_birth, errors="coerce")
    u["age"] = (pd.to_datetime(u.season.str[:4] + "-09-01") - dob).dt.days / 365.25
    u["attacker"] = (u.position.eq("Attack") | u.sub_position.eq("Attacking Midfield"))
    WORK.mkdir(parents=True, exist_ok=True)
    out = WORK / "panel.parquet"
    u.to_parquet(out, index=False)
    print(f"panel: {len(u):,} player-seasons -> {out}")
    print(f"  with measured minutes: {u.minutes.notna().mean():.1%}; attackers: {u.attacker.sum():,}")
    ok = (u.minutes >= 900) & u.attacker & u.usage_on_pitch.notna()
    r = np.corrcoef(u.loc[ok, "usage_on_pitch"], u.loc[ok, "usage_on_pitch_est"])[0, 1]
    print(f"  measured vs estimated on-pitch share, attackers 900+ min: r = {r:.3f}")
    return u


if __name__ == "__main__":
    build()
