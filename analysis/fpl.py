"""2025-26 out-of-sample proxy: movers against stayers in the Premier League, from FPL data.

Understat stops in September 2025, so the main results cannot be tested on the season
just played. Fantasy Premier League publishes Opta's expected goals (xG), expected assists
(xA) and minutes for every player-match, and the community archive
vaastav/Fantasy-Premier-League (MIT licence) keeps them. That is enough to ask the headline
question again on new data: do attackers who change Premier League club see their xG+xA per 90
fall more often than those who stay?

This is a proxy, not a rerun. FPL has no shot-level data, so the share of the ball (and the
four-part split in transfers.py) cannot be computed, and it only sees players who were in the
Premier League in both seasons, so a move to or from another league is invisible.

A player is matched across seasons by FPL `code`, which persists; `element` and `id`
are re-numbered every year. His club for a season is the one he played most minutes for.
Writes data/fpl.json (aggregates only).

    python fpl.py   (needs $SOURCE_DATA/fpl, see DATA.md)     python fpl.py check
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from config import OUT, SOURCE, SEED, N_BOOT, MIN_MINUTES

FLOP = np.log(0.75)  # output per 90 fell by more than 25%
SEASONS = ["2023-24", "2024-25", "2025-26"]
POSITIONS = {3: "MID", 4: "FWD"}   # FPL element_type
GROUPS = {"FWD": ["FWD"], "MID": ["MID"], "FWD+MID": ["FWD", "MID"]}


def season_table(folder) -> pd.DataFrame:
    """One row per player: code, position, main club, minutes and xG+xA for the season.

    The position comes from players_raw (merged_gw labels some 2024-25 players 'AM').
    Club is where he played most minutes, so a January move inside the league counts
    for the club he spent longer at.
    """
    g = pd.read_csv(folder / "merged_gw.csv", low_memory=False,
                    usecols=["element", "team", "minutes", "expected_goals", "expected_assists"])
    p = pd.read_csv(folder / "players_raw.csv", usecols=["id", "code", "element_type"])
    g["xga"] = g.expected_goals + g.expected_assists
    by_club = g.groupby(["element", "team"], as_index=False).agg(minutes=("minutes", "sum"))
    club = by_club.sort_values(["element", "minutes"], ascending=[True, False]) \
                  .drop_duplicates("element").set_index("element").team
    tot = g.groupby("element").agg(minutes=("minutes", "sum"), xga=("xga", "sum"))
    t = tot.join(club.rename("club")).reset_index().merge(p, left_on="element", right_on="id")
    t["pos"] = t.element_type.map(POSITIONS)
    return t[["code", "pos", "club", "minutes", "xga"]]


def pairs(a: pd.DataFrame, b: pd.DataFrame) -> pd.DataFrame:
    """Players with MIN_MINUTES in both seasons, matched on code."""
    m = a[a.minutes >= MIN_MINUTES].merge(b[b.minutes >= MIN_MINUTES], on="code",
                                          suffixes=("0", "1"))
    m = m[(m.xga0 > 0) & (m.xga1 > 0)].copy()
    m["out0"], m["out1"] = m.xga0 / m.minutes0 * 90, m.xga1 / m.minutes1 * 90
    m["d_out"] = np.log(m.out1 / m.out0)
    m["mover"] = m.club0 != m.club1
    m["flop"] = m.d_out < FLOP
    return m.reset_index(drop=True)


def boot(df: pd.DataFrame, stat, n=N_BOOT, seed=SEED):
    """Point and 95% interval, resampling whole players."""
    point = np.asarray(stat(df), dtype=float)
    rng = np.random.default_rng(seed)
    idx = df.groupby("code").indices
    ids = np.array(list(idx))
    draws = np.array([stat(df.iloc[np.concatenate([idx[i] for i in rng.choice(ids, len(ids))])])
                      for _ in range(n)], dtype=float)
    lo, hi = np.nanpercentile(draws, [2.5, 97.5], axis=0)
    return point, lo, hi


def r4(x):
    return round(float(x), 4)


def compare(m: pd.DataFrame) -> dict:
    """Movers against stayers: flop rates, mean change in output per 90, and the gaps."""
    def stat(x):
        mv, st = x[x.mover], x[~x.mover]
        return [mv.flop.mean(), st.flop.mean(), mv.flop.mean() - st.flop.mean(),
                np.exp(mv.d_out.mean()) - 1, np.exp(st.d_out.mean()) - 1,
                mv.d_out.mean() - st.d_out.mean()]
    keys = ["flop_rate_movers", "flop_rate_stayers", "flop_rate_gap",
            "mean_change_movers", "mean_change_stayers", "mean_log_gap"]
    out = {"n_movers": int(m.mover.sum()), "n_stayers": int((~m.mover).sum()),
           "n_flops_movers": int((m.mover & m.flop).sum()),
           "n_flops_stayers": int((~m.mover & m.flop).sum())}
    if min(out["n_movers"], out["n_stayers"]) < 5:
        return out | {"note": "too few movers or stayers for an interval"}
    p, lo, hi = boot(m, stat)
    for i, k in enumerate(keys):
        out[k] = {"point": r4(p[i]), "lo": r4(lo[i]), "hi": r4(hi[i])}
    return out


def main():
    folder = SOURCE / "fpl"
    t = {s: season_table(folder / s) for s in SEASONS}
    res = {"source": "vaastav/Fantasy-Premier-League (MIT licence), FPL xG and xA from Opta",
           "min_minutes": MIN_MINUTES, "flop": "xG+xA per 90 down by more than 25%",
           "mover": "main club (most minutes) differs between the two seasons",
           "pairs": {}}
    for s0, s1 in zip(SEASONS, SEASONS[1:]):
        m = pairs(t[s0], t[s1])
        res["pairs"][f"{s0} -> {s1}"] = {
            name: compare(m[m.pos0.isin(pos)]) for name, pos in GROUPS.items()}
    (OUT / "fpl.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


def _check():
    """A tiny synthetic case with known answers, including a matching-by-code trap."""
    def tab(rows):
        return pd.DataFrame(rows, columns=["code", "pos", "club", "minutes", "xga"])
    a = tab([(1, "FWD", "A", 1800, 18.0),    # stays, 0.9 per 90
             (2, "FWD", "A", 1800, 18.0),    # moves, 0.9 per 90
             (3, "FWD", "B", 1800, 18.0),    # stays, 0.9 per 90
             (4, "FWD", "B", 800, 20.0),     # under 900 minutes: dropped
             (5, "FWD", "C", 900, 9.0)])     # moves, 0.9 per 90
    b = tab([(1, "FWD", "A", 1800, 9.0),     # stays, 0.45 per 90: flop
             (2, "FWD", "D", 1800, 9.0),     # moves, 0.45: flop
             (3, "FWD", "B", 1800, 16.2),    # stays, 0.81: fell 10%, not a flop
             (4, "FWD", "B", 1800, 18.0),
             (5, "FWD", "E", 900, 8.1)])     # moves, 0.81: not a flop
    m = pairs(a, b)
    assert sorted(m.code) == [1, 2, 3, 5]
    assert m.set_index("code").mover.to_dict() == {1: False, 2: True, 3: False, 5: True}
    assert m.set_index("code").flop.to_dict() == {1: True, 2: True, 3: False, 5: False}
    o = compare(m)
    assert (o["n_movers"], o["n_stayers"]) == (2, 2) and "flop_rate_movers" not in o
    big = pd.concat([m.assign(code=m.code + 10 * k) for k in range(5)], ignore_index=True)
    o = compare(big)
    assert o["flop_rate_movers"]["point"] == 0.5 and o["flop_rate_gap"]["point"] == 0.0
    assert abs(o["mean_change_stayers"]["point"] - (np.sqrt(0.5 * 0.9) - 1)) < 1e-3
    print("fpl.py checks pass")


if __name__ == "__main__":
    _check() if "check" in sys.argv[1:] else main()
