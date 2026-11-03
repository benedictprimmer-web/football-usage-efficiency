"""MLS replication from American Soccer Analysis season totals: movers v stayers, and the
same player with more of the ball.

Why: Understat and Opta cover Europe only. MLS is a different league, so it is a test of
whether the pattern travels. ASA publishes season totals but no line-ups, so the share
of the ball while on the pitch is ESTIMATED, not measured. The estimate is the one the
first version of this repo used:

    share on pitch = (his shots + key passes) / (team shots + key passes)
                     / (his minutes / team minutes)

with team minutes = (all players' minutes) / 11. It assumes his actions are spread evenly
over the time he is on, and it is noisier than the match-by-match version used for Europe.
A player who changed club mid-season is kept: shares and minutes are summed over his stints.

Data: American Soccer Analysis public API, CC BY-SA 4.0 (data licence stated in its
openapi.json). Raw JSON is cached outside the repo in $SOURCE_DATA/asa; four requests in all.

    cd analysis && SOURCE_DATA=... python asa.py          (writes data/asa.json)
    python asa.py check                                   (tiny synthetic self-test)
    python asa.py fetch                                   (only if the cache is missing)
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request

import numpy as np
import pandas as pd

from config import OUT, SOURCE, MIN_MINUTES, SEED, N_BOOT

API = "https://app.americansocceranalysis.com/api/v1/mls"
RAW = SOURCE / "asa"
ATTACKERS = {"ST", "W", "AM"}   # ASA's general_position; it has no "F"
FLOP = np.log(0.75)             # output per 90 fell by more than 25%
STEP = 0.05                     # slopes per +5 points of share
MIN_ACTIONS = 20


# ------------------------------------------------------------------ data

def fetch() -> None:
    """Four polite requests, two seconds apart. Skips files already cached."""
    RAW.mkdir(parents=True, exist_ok=True)
    jobs = {"players_xgoals.json": "/players/xgoals?split_by_teams=true&split_by_seasons=true&stage_name=Regular%20Season",
            "teams_xgoals.json": "/teams/xgoals?split_by_seasons=true&stage_name=Regular%20Season",
            "players.json": "/players", "teams.json": "/teams"}
    for name, path in jobs.items():
        if (RAW / name).exists():
            continue
        req = urllib.request.Request(API + path, headers={"User-Agent": "transfer-usage-public (research)"})
        (RAW / name).write_bytes(urllib.request.urlopen(req, timeout=60).read())
        time.sleep(2)


def stints() -> pd.DataFrame:
    """One row per player, season and club (a mid-season move gives two)."""
    d = pd.DataFrame(json.loads((RAW / "players_xgoals.json").read_text()))
    d["season"] = d.season_name.astype(int)
    d["actions"] = d.shots + d.key_passes.fillna(0)
    d["value"] = d.xgoals_plus_xassists
    d = d.rename(columns={"minutes_played": "minutes"})
    g = d.groupby(["team_id", "season"])
    d["team_actions"], d["team_minutes"] = g.actions.transform("sum"), g.minutes.transform("sum")
    return d


def panel(d: pd.DataFrame) -> pd.DataFrame:
    """One row per player-season: totals over stints, main club, and the on-pitch share."""
    d = d.assign(
        share_num=d.actions / d.team_actions,                       # his share of team actions
        time_den=d.minutes * 11 / d.team_minutes,                   # his share of team minutes
        team_ap90_w=d.team_actions * 990 / d.team_minutes * d.minutes)
    d = d.sort_values("minutes", ascending=False)
    g = d.groupby(["player_id", "season"])
    p = g.agg(minutes=("minutes", "sum"), actions=("actions", "sum"), value=("value", "sum"),
              share_num=("share_num", "sum"), time_den=("time_den", "sum"),
              team_ap90_w=("team_ap90_w", "sum"), team=("team_id", "first"),
              pos=("general_position", "first"), stints=("team_id", "size")).reset_index()
    p["share"] = p.share_num / p.time_den
    p["team_ap90"] = p.team_ap90_w / p.minutes
    p["out90"] = p.value / p.minutes * 90
    p["quality"] = p.value / p.actions
    return p[p.pos.isin(ATTACKERS) & (p.minutes >= MIN_MINUTES) & (p.actions >= MIN_ACTIONS)
             & (p.share > 0) & (p.out90 > 0)].reset_index(drop=True)


def pairs(p: pd.DataFrame) -> pd.DataFrame:
    nxt = p.assign(season=p.season - 1)
    m = p.merge(nxt, on=["player_id", "season"], suffixes=("0", "1"))
    m["mover"] = m.team0 != m.team1
    for c in ("share", "team_ap90", "out90"):
        m["d_" + c] = np.log(m[c + "1"]) - np.log(m[c + "0"])
    m["flop"] = m.d_out90 < FLOP
    m["w"] = 1 / (1 / m.actions0 + 1 / m.actions1)
    return m


# ------------------------------------------------------------------ statistics

def boot(df: pd.DataFrame, stat, n: int = N_BOOT, seed: int = SEED):
    """Point and 95% interval, resampling whole players."""
    point = np.asarray(stat(df), dtype=float)
    rng = np.random.default_rng(seed)
    idx = df.groupby("player_id").indices
    ids = np.array(list(idx))
    draws = np.array([stat(df.iloc[np.concatenate([idx[i] for i in rng.choice(ids, len(ids))])])
                      for _ in range(n)], dtype=float)
    lo, hi = np.nanpercentile(draws, [2.5, 97.5], axis=0)
    return point, lo, hi


def cell(p, lo, hi):
    return {"point": round(float(p), 4), "lo": round(float(lo), 4), "hi": round(float(hi), 4)}


def movers_vs_stayers(m: pd.DataFrame) -> dict:
    """Mover minus stayer in mean log change, shown as a % (flop: difference in rate)."""
    def stat(x):
        mv, st = x[x.mover], x[~x.mover]
        pct = [np.exp(mv[c].mean() - st[c].mean()) - 1 for c in ("d_share", "d_team_ap90", "d_out90")]
        return pct + [mv.flop.mean(), st.flop.mean(), mv.flop.mean() - st.flop.mean()]
    p, lo, hi = boot(m, stat)
    keys = ["share_of_ball", "team_chances_per90", "output_per90", "flop_rate_movers",
            "flop_rate_stayers", "flop_rate_gap"]
    out = {k: cell(p[i], lo[i], hi[i]) for i, k in enumerate(keys)}
    out["n_movers"], out["n_stayers"] = int(m.mover.sum()), int((~m.mover).sum())
    out["n_players"] = int(m.player_id.nunique())
    return out


def _wls(x, y, w):
    A = np.column_stack([np.ones(len(y)), x])
    sw = np.sqrt(w)
    return np.linalg.lstsq(A * sw[:, None], y * sw, rcond=None)[0]


def within_player(m: pd.DataFrame) -> dict:
    """Change in chance quality on change in on-pitch share, per +5 points, as a % of the
    median quality. Weighted by actions. Season totals only, so no split-half: a speculative
    shot raises share and lowers quality together, which biases this slope downwards."""
    med = float(np.median(np.r_[m.quality0, m.quality1]))

    def stat(x):
        return _wls((x.share1 - x.share0).to_numpy(), (x.quality1 - x.quality0).to_numpy(),
                    x.w.to_numpy())[1] * STEP / med
    p, lo, hi = boot(m, stat)
    return {"per_5_points": cell(p, lo, hi), "median_quality": round(med, 4), "n_pairs": len(m),
            "n_players": int(m.player_id.nunique()), "mean_share": round(float(np.r_[m.share0, m.share1].mean()), 4)}


# ------------------------------------------------------------------ run and check

def main() -> None:
    fetch()
    d = stints()
    teams = pd.DataFrame(json.loads((RAW / "teams_xgoals.json").read_text()))
    p = panel(d)
    m = pairs(p)
    seasons = sorted(d.season.unique())
    ts = d.groupby(["team_id", "season"]).shots.sum().rename("p_shots").reset_index()
    ts["season"] = ts.season.astype(int)
    teams["season"] = teams.season_name.astype(int)
    ck = teams.merge(ts, on=["team_id", "season"])
    res = {"source": "American Soccer Analysis public API, CC BY-SA 4.0; MLS regular seasons",
           "seasons": [int(seasons[0]), int(seasons[-1])],
           "share_is_estimated_from_season_totals": True,
           "positions": sorted(ATTACKERS), "min_minutes": MIN_MINUTES,
           "player_seasons": len(p), "team_seasons": len(teams),
           "team_shots_check_ratio": round(float(ck.p_shots.sum() / ck.shots_for.sum()), 4),
           "movers_vs_stayers": movers_vs_stayers(m), "within_player": within_player(m)}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "asa.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


def _check() -> None:
    """Tiny synthetic case with a known answer."""
    # a team of 11 players, one 3,000-minute regular with 25% of the actions, one who plays
    # half as many minutes with 10%: shares on the pitch must come out at 0.25 and 0.20
    rows = [dict(player_id="a", team_id="T", season=2020, general_position="ST", minutes=3000,
                 actions=100, value=10.0), dict(player_id="b", team_id="T", season=2020,
                 general_position="ST", minutes=1500, actions=40, value=4.0)]
    rows += [dict(player_id=f"x{i}", team_id="T", season=2020, general_position="CB",
                  minutes=(33000 - 4500) / 9, actions=260 / 9, value=0.0) for i in range(9)]
    d = pd.DataFrame(rows)
    g = d.groupby("team_id")
    d["team_actions"], d["team_minutes"] = g.actions.transform("sum"), g.minutes.transform("sum")
    assert abs(d.team_minutes.iloc[0] - 33000) < 1e-9 and abs(d.team_actions.iloc[0] - 400) < 1e-9
    s = (d.actions / d.team_actions) / (d.minutes * 11 / d.team_minutes)
    assert abs(s.iloc[0] - 0.25) < 1e-9 and abs(s.iloc[1] - 0.20) < 1e-9, s.head(2)
    # bootstrap: movers lose exactly 10% of share, stayers nothing
    n = 40
    t = pd.DataFrame({"player_id": range(n), "mover": [i < 20 for i in range(n)]})
    t["d_share"] = np.where(t.mover, np.log(0.9), 0.0)
    t["d_team_ap90"], t["d_out90"] = 0.0, 0.0
    t["flop"] = False
    r = movers_vs_stayers(t)["share_of_ball"]
    assert abs(r["point"] + 0.1) < 1e-9 and r["lo"] <= r["point"] <= r["hi"], r
    # within-player: quality falls 0.01 for every +0.05 of share
    rng = np.random.default_rng(1)
    s0 = rng.uniform(0.1, 0.3, n)
    ds = rng.uniform(-0.05, 0.05, n)
    w = pd.DataFrame({"player_id": range(n), "share0": s0, "share1": s0 + ds, "quality0": 0.1,
                      "quality1": 0.1 - 0.2 * ds, "w": 50.0})
    q = within_player(w)
    assert abs(q["per_5_points"]["point"] * 0.1 + 0.01) < 1e-9, q
    print("asa.py check: ok")


if __name__ == "__main__":
    _check() if sys.argv[1:] == ["check"] else main()
