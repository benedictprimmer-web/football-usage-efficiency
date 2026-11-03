"""Why does a transfer flop? Split each club move's change in output into four parts.

A player's output in a season (npxG + xA) is exactly

    minutes played × team actions per minute × his share of them while on the pitch × quality per action

so the log change in output from one season to the next is the sum of the four log changes.
For attackers who changed club (at least 900 minutes before the move, 450 after), this
measures how much of a fall in output came from each part.

    python analysis/decompose.py   (needs data/work/panel.parquet from build_panel.py)
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from config import OUT

PARTS = {
    "d_min": "Played fewer minutes",
    "d_share": "Less of the ball while on the pitch",
    "d_qual": "Worse chances per action",
    "d_team": "New team created fewer chances",
}
FLOP = np.log(0.75)  # output fell by more than 25%


def moves() -> pd.DataFrame:
    d = pd.read_parquet(OUT / "work" / "panel.parquet")
    d = d[d.attacker & (d.club_share >= 0.8) & (d.minutes_share < 1)].copy()
    d["yr"] = d.season.str[:4].astype(int)
    d["team_apm"] = d.team_actions / (d.team_games * 90)
    cols = ["tm_player_id", "yr", "team", "player", "minutes", "usage_on_pitch",
            "team_apm", "efficiency", "value", "actions"]
    nxt = d[cols].assign(yr=lambda x: x.yr - 1)
    m = d[cols].merge(nxt, on=["tm_player_id", "yr"], suffixes=("0", "1"))
    m = m[(m.team0 != m.team1) & (m.minutes0 >= 900) & (m.minutes1 >= 450)
          & (m.actions0 >= 20) & (m.actions1 >= 10)].copy()

    def dlog(c):
        return np.log(m[c + "1"]) - np.log(m[c + "0"])

    m["d_out"] = dlog("value")
    m["d_min"], m["d_team"] = dlog("minutes"), dlog("team_apm")
    m["d_share"], m["d_qual"] = dlog("usage_on_pitch"), dlog("efficiency")
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
        "flop_mean_output_change": round(float(np.exp(fl.d_out.mean()) - 1), 3),
        "share_of_fall": {PARTS[p]: round(share[p], 3) for p in PARTS},
        "share_ci95": {PARTS[p]: [round(float(np.percentile(boot[:, i], 2.5)), 3),
                                  round(float(np.percentile(boot[:, i], 97.5)), 3)]
                       for i, p in enumerate(PARTS)},
    }
    (OUT / "flop_decomposition.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
