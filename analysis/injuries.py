"""Do movers flop more when they miss time injured, or when they moved on a free?

Two reasons a mover's output might fall that are not "the move changed his situation":

  (a) he was hurt. Days out in the season after the move (Aug to Jun, season yr+1),
      from the Transfermarkt injury spells in the salimt data lake. Stayers are split
      the same way, so the question is whether injury costs movers more than stayers.
  (b) he moved because his contract ran out. The data lake only holds each player's
      current contract, not the one he left, so the best available stand-in is the
      fee on his Transfermarkt transfer: nothing paid (free, or loan, which the file
      does not tell apart), and the narrower case of a nil fee dated at the turn of
      the season, when contracts end. Stayers have no transfer, so they are the
      reference for all movers rather than being split.

Writes data/injuries.json (aggregates only).

    python injuries.py          (needs data/work/season_pairs.parquet and
                                 $SOURCE_DATA/salimt/player_injuries_updated_*.csv)
    python injuries.py check    (self-test on a tiny made-up case, needs no data)
"""
from __future__ import annotations

import json
import sys
import warnings

import numpy as np
import pandas as pd

from config import OUT, SOURCE, WORK
from transfers import boot, fees, r3

DAYS_OUT = 30          # a month or more out counts as injured
FREE_WINDOW = ("06-25", "07-05")   # nil-fee moves dated here are taken as contracts ending


# ------------------------------------------------------------------ injuries

def days_out(pairs: pd.DataFrame, spells: pd.DataFrame) -> pd.Series:
    """Days injured inside season yr+1 (1 August to 30 June), counting only the part of
    each spell that falls in the window. A player with no spell at all gets 0, which
    also covers players the source does not cover (see the caveat in the README)."""
    start = pd.to_datetime((pairs.yr + 1).astype(str) + "-08-01")
    end = pd.to_datetime((pairs.yr + 2).astype(str) + "-06-30")
    w = pairs[["tm_player_id"]].assign(row=np.arange(len(pairs)), start=start.to_numpy(),
                                       end=end.to_numpy())
    j = w.merge(spells, left_on="tm_player_id", right_on="player_id")
    lo = j[["start", "from_date"]].max(axis=1)
    hi = j[["end", "end_date"]].min(axis=1)
    j["days"] = ((hi - lo).dt.days + 1).clip(lower=0)
    tot = j.groupby("row").days.sum().reindex(np.arange(len(pairs)), fill_value=0)
    return pd.Series(tot.to_numpy(), index=pairs.index)


def load_spells() -> pd.DataFrame:
    f = sorted((SOURCE / "salimt").glob("player_injuries_updated_*.csv"))[-1]
    s = pd.read_csv(f, parse_dates=["from_date", "end_date"])
    # a few spells have no end date: fall back on the days Transfermarkt says were missed
    s["end_date"] = s.end_date.fillna(s.from_date + pd.to_timedelta(s.days_missed.fillna(0), "D"))
    return s.dropna(subset=["from_date"])


# ------------------------------------------------------------------ contracts

def fee_status(pairs: pd.DataFrame, t: pd.DataFrame) -> pd.DataFrame:
    """For each mover, the fee and date of his Transfermarkt transfer into the new club
    (same matching window as transfers.slices: July of the first season to the end of the
    calendar year the second season starts in; the last one wins)."""
    mv = pairs[pairs.mover]
    t = t.merge(mv[["tm_player_id", "club_id1", "yr"]], on=["tm_player_id", "club_id1"])
    lo = pd.to_datetime(t.yr.astype(str) + "-07-01")
    hi = pd.to_datetime((t.yr + 1).astype(str) + "-12-31")
    t = (t[(t.date >= lo) & (t.date <= hi)].sort_values("date")
         .drop_duplicates(["tm_player_id", "club_id1", "yr"], keep="last"))
    out = pairs.merge(t[["tm_player_id", "club_id1", "yr", "transfer_fee", "date"]],
                      on=["tm_player_id", "club_id1", "yr"], how="left")
    out.loc[~out.mover, ["transfer_fee", "date"]] = np.nan
    md = out.date.dt.strftime("%m-%d").fillna("")
    out["nil_fee"] = out.mover & (out.transfer_fee == 0)
    out["paid"] = out.mover & (out.transfer_fee > 0)
    out["no_fee_record"] = out.mover & out.transfer_fee.isna()
    out["free_at_turn"] = out.nil_fee & ((md >= FREE_WINDOW[0]) & (md <= FREE_WINDOW[1]))
    return out


# ------------------------------------------------------------------ statistics

def cell(x: pd.DataFrame) -> list:
    """Flop rate, mean change in output per 90 (as a proportion), mean log change."""
    if len(x) == 0:
        return [np.nan] * 3
    return [x.flop.mean(), np.exp(x.d_out.mean()) - 1, x.d_out.mean()]


def pack(names: list[str], p, lo, hi) -> dict:
    return {k: {"point": r3(p[i])[0], "lo": r3(lo[i])[0], "hi": r3(hi[i])[0]}
            for i, k in enumerate(names)}


def injury_table(m: pd.DataFrame) -> dict:
    """Flop rate and mean change for movers and stayers, injured or not in season 2, plus
    the injured-minus-fit gap for each and the difference between those two gaps."""
    m = m.assign(hurt=m.days_out >= DAYS_OUT)
    cells = {f"{who}_{'injured' if h else 'fit'}": (m.mover == (who == "movers")) & (m.hurt == h)
             for who in ("movers", "stayers") for h in (True, False)}
    names = ["flop_rate", "mean_change", "mean_log_change"]

    def stat(x):
        v = {k: cell(x[(x.mover == k.startswith("movers")) & (x.hurt == k.endswith("injured"))])
             for k in cells}
        gap = {w: [v[f"{w}_injured"][i] - v[f"{w}_fit"][i] for i in (0, 2)]
               for w in ("movers", "stayers")}
        did = [gap["movers"][i] - gap["stayers"][i] for i in (0, 1)]
        return [e for k in cells for e in v[k]] + gap["movers"] + gap["stayers"] + did

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        p, lo, hi = boot(m, stat)
    keys = [f"{k}__{n}" for k in cells for n in names]
    keys += ["gap_movers__flop_rate", "gap_movers__mean_log_change",
             "gap_stayers__flop_rate", "gap_stayers__mean_log_change",
             "movers_gap_minus_stayers_gap__flop_rate",
             "movers_gap_minus_stayers_gap__mean_log_change"]
    flat = pack(keys, p, lo, hi)
    out = {"definition": f"injured = {DAYS_OUT}+ days out in Aug to Jun of season 2",
           "share_injured": {"movers": r3(m[m.mover].hurt.mean())[0],
                             "stayers": r3(m[~m.mover].hurt.mean())[0]}}
    for k, msk in cells.items():
        g = m[msk]
        out[k] = {"n": int(len(g)), "flops": int(g.flop.sum()), "mean_days_out": r3(g.days_out.mean())[0],
                  **{n: flat[f"{k}__{n}"] for n in names}}
    for k in keys:
        if k.startswith(("gap_", "movers_gap")):
            out[k] = flat[k]
    return out


def contract_table(m: pd.DataFrame) -> dict:
    """Movers by how they left (free, paid, free at the turn of the season) against all
    stayers, with the gap to stayers and the gap between free and paid movers."""
    groups = {"free_movers": m.nil_fee, "free_at_turn_movers": m.free_at_turn,
              "paid_movers": m.paid, "no_fee_record_movers": m.no_fee_record, "stayers": ~m.mover}
    names = ["flop_rate", "mean_change", "mean_log_change"]

    def stat(x):
        v = {k: cell(x[_mask(x, k)]) for k in groups}
        gaps = [v[k][i] - v["stayers"][i] for k in ("free_movers", "free_at_turn_movers", "paid_movers")
                for i in (0, 2)]
        fp = [v["free_movers"][i] - v["paid_movers"][i] for i in (0, 2)]
        return [e for k in groups for e in v[k]] + gaps + fp

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        p, lo, hi = boot(m, stat)
    keys = [f"{k}__{n}" for k in groups for n in names]
    keys += [f"gap_to_stayers_{k}__{n}" for k in ("free_movers", "free_at_turn_movers", "paid_movers")
             for n in ("flop_rate", "mean_log_change")]
    keys += ["free_minus_paid__flop_rate", "free_minus_paid__mean_log_change"]
    flat = pack(keys, p, lo, hi)
    out = {"definition": "free = Transfermarkt fee of 0 (free transfer or loan; the file cannot "
                         f"tell them apart); free_at_turn = fee 0 dated {FREE_WINDOW[0]} to {FREE_WINDOW[1]}"}
    for k, g in groups.items():
        x = m[g]
        out[k] = {"n": int(len(x)), "flops": int(x.flop.sum()), "mean_age": r3(x.age0.mean())[0],
                  **{n: flat[f"{k}__{n}"] for n in names}}
    for k in keys:
        if k.startswith(("gap_to", "free_minus")):
            out[k] = flat[k]
    return out


def _mask(x: pd.DataFrame, k: str) -> pd.Series:
    return {"free_movers": x.nil_fee, "free_at_turn_movers": x.free_at_turn, "paid_movers": x.paid,
            "no_fee_record_movers": x.no_fee_record, "stayers": ~x.mover}[k]


# ------------------------------------------------------------------ self-test

def _check():
    """Tiny made-up case: overlap clipping, the 30-day line, and fee classes."""
    pairs = pd.DataFrame({"tm_player_id": [1, 2, 3, 4], "yr": [2020] * 4,
                          "mover": [True, True, False, False], "club_id1": [9, 9, 5, 5]})
    spells = pd.DataFrame({
        "player_id": [1, 1, 2, 3],
        # 1: 10 days wholly inside, plus a spell that starts 20 days before the window opens
        # and runs 10 days into it (only 10 count); 2: a spell before the window; 3: 40 days
        "from_date": pd.to_datetime(["2021-10-01", "2021-07-12", "2021-03-01", "2021-12-01"]),
        "end_date": pd.to_datetime(["2021-10-10", "2021-08-10", "2021-03-20", "2022-01-09"]),
    })
    d = days_out(pairs, spells)
    assert d.tolist() == [10 + 10, 0, 40, 0], d.tolist()
    assert (d >= DAYS_OUT).tolist() == [False, False, True, False]
    # window edge: a spell running on past 30 June only counts to the 30th
    edge = pd.DataFrame({"player_id": [4], "from_date": pd.to_datetime(["2022-06-21"]),
                         "end_date": pd.to_datetime(["2022-08-01"])})
    assert days_out(pairs, edge).iloc[3] == 10
    t = pd.DataFrame({"tm_player_id": [1, 2, 2], "club_id1": [9, 9, 9],
                      "date": pd.to_datetime(["2021-07-01", "2021-01-15", "2021-08-20"]),
                      "transfer_fee": [0.0, 5e6, np.nan]})
    f = fee_status(pairs, t)
    assert f.loc[0, ["nil_fee", "free_at_turn"]].tolist() == [True, True]
    assert f.loc[1, "no_fee_record"]            # the later (August) row wins and has no fee
    assert not f.loc[2:, ["nil_fee", "paid", "no_fee_record"]].any().any()
    # the statistic helpers on a case worked by hand: 2 of 4 flop, mean log change -0.2
    x = pd.DataFrame({"flop": [True, True, False, False], "d_out": [-0.5, -0.5, 0.1, 0.0]})
    c = cell(x)
    assert c[0] == 0.5 and abs(c[2] + 0.225) < 1e-9 and abs(c[1] - (np.exp(-0.225) - 1)) < 1e-9
    assert np.isnan(cell(x.iloc[:0])[0])
    print("injuries.py checks pass")


# ------------------------------------------------------------------ main

def main():
    m = pd.read_parquet(WORK / "season_pairs.parquet")
    spells = load_spells()
    m["days_out"] = days_out(m, spells)
    m = fee_status(m, fees())
    res = {"pairs": int(len(m)), "movers": int(m.mover.sum()), "stayers": int((~m.mover).sum()),
           "injury_coverage": {
               "players_with_any_spell": r3(m.tm_player_id.isin(spells.player_id).mean())[0],
               "pairs_with_spell_in_season2": r3((m.days_out > 0).mean())[0],
               "spells_file_last_spell": str(spells.from_date.max().date())},
           "injuries": injury_table(m), "contracts": contract_table(m)}
    (OUT / "injuries.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    _check() if sys.argv[1:] == ["check"] else main()
