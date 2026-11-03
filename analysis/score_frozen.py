"""Score the frozen predictions for moves into 2025-26, once.

data/flop_model_frozen.json and data/predictions_2025_26.csv were committed before any
2025-26 outcome was read (see the git log). No source in this repo has 2025-26 shots for
the Big-5, so a flop (output per 90 down by more than 25%) cannot be scored yet. What can
be scored is the other half of the outcome: whether the player lost his place, meaning
under 900 league minutes in the Big-5 in 2025-26, from Transfermarkt appearances (the
copy built on 5 September 2026 runs to 28 June 2026).

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
    p = pred.assign(minutes=pred.tm_player_id.map(minutes).fillna(0))
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
           "what_is_scored": "lost his place (under 900 Big-5 league minutes in 2025-26); "
                             "flops wait for 2025-26 shot data"} | score(pred, minutes)
    (OUT / "frozen_score_2025_26.json").write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    check() if sys.argv[1:] == ["check"] else main()
