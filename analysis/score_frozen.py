"""Score the frozen predictions for moves into 2025-26, once.

data/flop_model_frozen.json and data/predictions_2025_26.csv were committed at 20:50 on
3 November 2026 and scored at 21:09 the same day. This is not a prospective test: the
Transfermarkt copy holding the 2025-26 minutes was already on disk, and 2025-26 Premier
League outcomes from FPL had been read and committed 30 minutes before the freeze (commit
51d7f74). The freeze is procedural, not blind. The prospective test is
analysis/freeze_2026_27.py.

No source in this repo has 2025-26 Understat shots, so a flop (output per 90 down by more
than 25%, on the same source as training) cannot be scored. What is scored is the other
half of the outcome: whether the player lost his place, meaning under 900 Big-5 league
minutes in 2025-26, from Transfermarkt appearances (the copy built on 5 September 2026
runs to 28 June 2026).

Round 2 of the review found three faults in the frozen test set, all fixed here only in a
second, labelled score (the frozen file itself is never changed):
- two buying clubs were not in the Big-5 in 2025-26 (the destination league came from
  clubs.csv, which keeps a relegated club's old league);
- January moves were included, and their minutes at the old club counted;
- calibration was not reported.

    python analysis/score_frozen.py
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from config import OUT, SOURCE, SEED, N_BOOT, MIN_MINUTES
from transfers import _auc

BIG5 = {"GB1", "ES1", "IT1", "L1", "FR1"}


def score(pred: pd.DataFrame, minutes: pd.Series) -> dict:
    p = pred.assign(minutes=pred.tm_player_id.map(minutes).fillna(0).to_numpy())
    p["lost"] = (p.minutes < MIN_MINUTES).astype(float)
    y, s = p.lost.to_numpy(), p.p_flop_or_lost_place.to_numpy()
    rng = np.random.default_rng(SEED)
    bs = []
    for _ in range(N_BOOT):
        k = rng.choice(len(s), len(s))
        if y[k].min() != y[k].max():
            bs.append(_auc(s[k], y[k]))
    top = s >= np.median(s)
    return {"moves": int(len(p)), "lost_place": int(y.sum()),
            "lost_rate": round(float(y.mean()), 3),
            "auc_lost_place": round(float(_auc(s, y)), 3),
            "auc_lo": round(float(np.percentile(bs, 2.5)), 3),
            "auc_hi": round(float(np.percentile(bs, 97.5)), 3),
            "lost_rate_riskier_half": round(float(y[top].mean()), 3),
            "lost_rate_safer_half": round(float(y[~top].mean()), 3),
            "mean_predicted_flop_or_lost": round(float(s.mean()), 3)}


def check():
    pred = pd.DataFrame({"tm_player_id": [1, 2, 3, 4], "p_flop_or_lost_place": [0.9, 0.8, 0.2, 0.1]})
    r = score(pred, pd.Series({1: 100, 2: 500, 3: 2000, 4: 3000}))
    assert r["lost_place"] == 2 and r["auc_lost_place"] == 1.0, r
    print("score_frozen self-check ok")


def main():
    pred = pd.read_csv(OUT / "predictions_2025_26.csv")
    a = pd.read_csv(SOURCE / "transfermarkt" / "appearances.csv.gz",
                    usecols=["player_id", "date", "competition_id", "minutes_played"])
    a = a[a.competition_id.isin(BIG5) & (a.date >= "2025-08-01") & (a.date <= "2026-06-30")]
    minutes = a.groupby("player_id").minutes_played.sum()
    res = {"scored_on": "2026-11-03", "source": "Transfermarkt appearances to 28 June 2026",
           "prospective": False,
           "what_is_scored": "lost his place (under 900 Big-5 league minutes in 2025-26); "
                             "flops need 2025-26 Understat shots, which no source here has"} | score(pred, minutes)
    # second score, labelled post hoc: summer moves to clubs that played 2025-26 in the
    # Big-5, minutes at the new club only
    a2 = pd.read_csv(SOURCE / "transfermarkt" / "appearances.csv.gz",
                     usecols=["player_id", "player_club_id", "date", "competition_id", "minutes_played"])
    a2 = a2[a2.competition_id.isin(BIG5) & (a2.date >= "2025-08-01") & (a2.date <= "2026-06-30")]
    big5_2025 = set(a2.player_club_id)
    tr = pd.read_csv(SOURCE / "transfermarkt" / "transfers.csv.gz",
                     usecols=["player_id", "to_club_id", "transfer_date"])
    tr = tr[(tr.transfer_date >= "2025-07-01") & (tr.transfer_date <= "2026-02-01")]
    p = pred.merge(tr, left_on=["tm_player_id", "transfer_date"], right_on=["player_id", "transfer_date"],
                   how="left").drop_duplicates("tm_player_id")
    keep = p.to_club_id.isin(big5_2025) & (p.transfer_date <= "2025-09-01")
    at_new = a2.groupby(["player_id", "player_club_id"]).minutes_played.sum()
    mins_new = pd.Series({i: at_new.get((i, c), 0) for i, c in zip(p.tm_player_id, p.to_club_id)})
    res["post_hoc_clean_subset"] = {
        "what": "summer moves (to 1 September 2025) to clubs with a 2025-26 Big-5 league "
                "appearance, minutes at the new club only; a correction made after the first "
                "score was seen",
        "dropped_not_big5": int((~p.to_club_id.isin(big5_2025)).sum()),
        "dropped_january": int((p.transfer_date > "2025-09-01").sum())} | score(
        pred[keep.to_numpy()].reset_index(drop=True), mins_new)
    # why there is no prospective freeze for 2026-27 yet: this copy barely holds the
    # summer 2026 window, only the 30 June and 1 July dates when loans end and contracts turn
    tr_all = pd.read_csv(SOURCE / "transfermarkt" / "transfers.csv.gz", usecols=["transfer_date"])
    s26 = tr_all[(tr_all.transfer_date >= "2026-06-01") & (tr_all.transfer_date <= "2026-09-01")]
    res["summer_2026_records"] = {"records_1_june_to_1_september": int(len(s26)),
                                  "dated_30_june_or_1_july": int(s26.transfer_date.isin(["2026-06-30", "2026-07-01"]).sum())}
    (OUT / "frozen_score_2025_26.json").write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    check() if sys.argv[1:] == ["check"] else main()
