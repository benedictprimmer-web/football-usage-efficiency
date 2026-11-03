"""Why does a transfer flop? Split each club move's change in per-90 output into four parts.

A player's output per 90 minutes (npxG + xA) is exactly

    team actions per 90 × his share of them while on the pitch × team-mates' quality per action
        × his quality relative to team-mates

so the log change from one season to the next is the sum of the four log changes. Everything
is per 90, so playing time drops out. For attackers who changed club (at least 900 league
minutes and 20 actions in both seasons), this measures how much of a fall came from each part.

    python analysis/decompose.py   (needs data/work/panel.parquet from build_panel.py)
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from config import OUT

PARTS = {
    "d_share": "Less of the ball while on the pitch",
    "d_team": "New team created fewer chances",
    "d_mates": "New team-mates' chances were worse",
    "d_rel": "Player did worse than new team-mates",
}
FLOP = np.log(0.75)  # per-90 output fell by more than 25%


def moves() -> pd.DataFrame:
    d = pd.read_parquet(OUT / "work" / "panel.parquet")
    d = d[d.attacker & (d.club_share >= 0.8) & (d.minutes_share < 1) & (d.mates_eff > 0)].copy()
    d["yr"] = d.season.str[:4].astype(int)
    d["team_ap90"] = d.team_actions / d.team_games
    d["out90"] = d.value / d.minutes * 90
    d["rel"] = d.efficiency / d.mates_eff
    cols = ["tm_player_id", "yr", "team", "player", "minutes", "usage_on_pitch",
            "team_ap90", "mates_eff", "rel", "out90", "actions"]
    nxt = d[cols].assign(yr=lambda x: x.yr - 1)
    m = d[cols].merge(nxt, on=["tm_player_id", "yr"], suffixes=("0", "1"))
    m = m[(m.team0 != m.team1) & (m.minutes0 >= 900) & (m.minutes1 >= 900)
          & (m.actions0 >= 20) & (m.actions1 >= 20)].copy()

    def dlog(c):
        return np.log(m[c + "1"]) - np.log(m[c + "0"])

    m["d_out"] = dlog("out90")
    m["d_share"], m["d_team"] = dlog("usage_on_pitch"), dlog("team_ap90")
    m["d_mates"], m["d_rel"] = dlog("mates_eff"), dlog("rel")
    assert (m.d_out - m[list(PARTS)].sum(axis=1)).abs().max() < 1e-9
    return m


def main():
    m = moves()
    fl = m[m.d_out < FLOP]
    share = {p: float(fl[p].mean() / fl.d_out.mean()) for p in PARTS}
    rng = np.random.default_rng(1)
    ids = fl.tm_player_id.unique()
    f2 = fl.set_index("tm_player_id")
    boot = np.array([[x[p].mean() / x.d_out.mean() for p in PARTS]
                     for x in (f2.loc[rng.choice(ids, len(ids))] for _ in range(2000))])
    out = {
        "moves": int(len(m)), "players": int(m.tm_player_id.nunique()), "flops": int(len(fl)),
        "flop_mean_per90_change": round(float(np.exp(fl.d_out.mean()) - 1), 3),
        "share_of_fall": {PARTS[p]: round(share[p], 3) for p in PARTS},
        "share_ci95": {PARTS[p]: [round(float(np.percentile(boot[:, i], 2.5)), 3),
                                  round(float(np.percentile(boot[:, i], 97.5)), 3)]
                       for i, p in enumerate(PARTS)},
    }
    (OUT / "flop_decomposition.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
