"""Build the player-season panel behind every number in this repo.

One row per (player, season) for players with a single club in that season:
usage share and efficiency on the repo's own definitions (src/usage_model/usage.py),
the same two numbers on odd and even matches separately (for the split-half checks),
league minutes and position from Transfermarkt.

Reads raw third-party data from $SOURCE_DATA (default: ./data/raw). See data/DATA.md
for how to get each file. Writes the panel to $SOURCE_DATA/../work/panel.parquet,
which is gitignored: it holds per-player rows and is not redistributed.

    python analysis/build_panel.py
"""
from __future__ import annotations

import pandas as pd

from config import SOURCE, WORK, LEAGUE_COMPS

from usage_model.usage import usage_efficiency  # noqa: E402

KEY = ["league", "season", "team", "player"]


def _halves(shots: pd.DataFrame) -> pd.Series:
    """0/1 per shot: alternate each team's league matches by date (odd/even)."""
    g = (shots[["league", "season", "team_shot", "game_id", "date"]]
         .drop_duplicates(["league", "season", "team_shot", "game_id"])
         .sort_values("date"))
    g["half"] = g.groupby(["league", "season", "team_shot"]).cumcount() % 2
    m = shots.merge(g[["league", "season", "team_shot", "game_id", "half"]],
                    on=["league", "season", "team_shot", "game_id"], how="left")
    return m.half.to_numpy()


def build() -> pd.DataFrame:
    shots = pd.read_parquet(SOURCE / "understat" / "shots.parquet")
    print(f"shots: {len(shots):,}")

    full = usage_efficiency(shots)
    shots = shots.assign(half=_halves(shots))
    parts = []
    for h in (0, 1):
        u = usage_efficiency(shots[shots.half == h])
        parts.append(u.set_index(KEY)[["actions", "value", "usage_share", "efficiency"]]
                     .add_suffix(f"_h{h}"))
    u = full.set_index(KEY).join(parts[0]).join(parts[1]).reset_index()

    # team efficiency: value per terminal action for the whole team-season
    team = u.groupby(["league", "season", "team"]).agg(
        team_value=("value", "sum"), team_actions=("actions", "sum"))
    team["team_eff"] = team.team_value / team.team_actions
    # matches per team-season, to turn league minutes into a share of the season
    gm = pd.concat([shots[["league", "season", c, "game_id"]].rename(columns={c: "team"})
                    for c in ("home_team", "away_team")]).drop_duplicates()
    team["team_games"] = gm.groupby(["league", "season", "team"]).game_id.nunique()
    u = u.merge(team.reset_index(), on=["league", "season", "team"])
    # team-mates' efficiency: the same team, with the player's own actions removed
    u["mates_eff"] = (u.team_value - u.value) / (u.team_actions - u.actions)

    # Understat name -> Understat id (modal, as in the source repo) -> Transfermarkt id
    id_map = (shots.dropna(subset=["player_id"]).groupby("player")["player_id"]
              .agg(lambda s: s.value_counts().idxmax()).rename("us_player_id"))
    u = u.merge(id_map, left_on="player", right_index=True, how="left")
    cw = pd.read_csv(SOURCE / "crosswalk" / "players.csv",
                     usecols=["us_player_id", "tm_player_id"])
    u = u.merge(cw, on="us_player_id", how="left")

    # one club per season: a mid-season move splits a season across two
    # denominators. Keep the main club when it holds >= 80% of the player's
    # actions that season (e.g. Ronaldo 2021-22: one Juventus match, then
    # United); drop the season when the split is closer than that.
    tot = u.groupby(["us_player_id", "season"]).actions.transform("sum")
    u["club_share"] = u.actions / tot
    u = u[(u.club_share >= 0.8) & u.tm_player_id.notna()].copy()
    u["tm_player_id"] = u.tm_player_id.astype(int)

    players = pd.read_csv(SOURCE / "transfermarkt" / "players.csv.gz",
                          usecols=["player_id", "position", "sub_position", "date_of_birth"])
    u = u.merge(players.rename(columns={"player_id": "tm_player_id"}),
                on="tm_player_id", how="left")

    ap = pd.read_csv(SOURCE / "transfermarkt" / "appearances.csv.gz",
                     usecols=["player_id", "game_id", "competition_id", "minutes_played"])
    ap = ap[ap.competition_id.isin(LEAGUE_COMPS)]
    # season from the games table, not the date: 2019-20 ran into August 2020
    games = pd.read_csv(SOURCE / "transfermarkt" / "games.csv.gz",
                        usecols=["game_id", "season", "date"])
    # the shot data stops on 4 January 2025, mid-way through 2024-25; count
    # minutes only up to the same date so the two halves of usage line up
    games = games[games.date <= shots.date.max()].drop(columns="date")
    ap = ap.merge(games, on="game_id")
    ap["season"] = ap.season.astype(int).map(lambda y: f"{y}-{y + 1}")
    mins = (ap.groupby(["player_id", "season"]).minutes_played.sum()
              .rename("minutes").reset_index().rename(columns={"player_id": "tm_player_id"}))
    u = u.merge(mins, on=["tm_player_id", "season"], how="left")

    # usage_share = (share of the season on the pitch) x (share of play while on it)
    u["minutes_share"] = (u.minutes / (u.team_games * 90)).clip(upper=1)
    u["usage_on_pitch"] = u.usage_share / u.minutes_share
    u["attacker"] = (u.position.eq("Attack")
                     | u.sub_position.eq("Attacking Midfield"))
    WORK.mkdir(parents=True, exist_ok=True)
    out = WORK / "panel.parquet"
    u.to_parquet(out, index=False)
    print(f"panel: {len(u):,} player-seasons -> {out}")
    print(f"  with minutes: {u.minutes.notna().mean():.1%}; attackers: {u.attacker.sum():,}")
    return u


if __name__ == "__main__":
    build()
