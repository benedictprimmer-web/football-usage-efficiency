"""Why do transfers fail? Movers against stayers, a noise-only benchmark, and who flops.

A player's output per 90 minutes (npxG + xA) is exactly

    team actions per 90 while he is on  x  his share of them  x  team-mates' quality per action
        x  his quality relative to team-mates

so the log change from one season to the next is the sum of four log changes. Every
term is measured over the minutes he was actually on the pitch (minutes.py).

The first version of this repo split the fall for movers whose output dropped by more
than 25% and called the parts "situation" and "player". Two reviewers pointed out the
gap: players who stay at the same club also have seasons like that. So this script
puts every number for movers next to the same number for stayers, and next to what
pure noise in a player's chance quality would produce.

Writes data/transfers.json and small tables in data/ (all aggregates).

    python analysis/transfers.py   (needs data/work/panel.parquet)
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from config import OUT, SOURCE, WORK, SEED, N_BOOT, MIN_MINUTES

PARTS = {
    "d_team": "Team chances per 90",
    "d_share": "His share of the ball",
    "d_mates": "Team-mates' chance quality",
    "d_rel": "His quality relative to team-mates",
}
SITUATION = ["d_team", "d_share", "d_mates"]
FLOP = np.log(0.75)  # output per 90 fell by more than 25%
MIN_ACTIONS = 20


# ------------------------------------------------------------------ the pairs

def season_pairs() -> pd.DataFrame:
    """Every attacker with 900+ measured minutes in two consecutive seasons."""
    d = pd.read_parquet(WORK / "panel.parquet")
    d = d[d.attacker & (d.minutes >= MIN_MINUTES) & (d.actions >= MIN_ACTIONS)
          & (d.mates_eff > 0) & (d.usage_on_pitch > 0)].copy()
    d["yr"] = d.season.str[:4].astype(int)
    d["out90"] = d.value / d.minutes * 90
    d["rel"] = d.efficiency / d.mates_eff
    cols = ["tm_player_id", "player", "yr", "league", "team", "club_id", "minutes", "actions",
            "value", "usage_on_pitch", "team_ap90_on", "mates_eff", "rel", "out90",
            "efficiency", "age", "minutes_share"]
    nxt = d[cols].assign(yr=lambda x: x.yr - 1)
    m = d[cols].merge(nxt, on=["tm_player_id", "yr"], suffixes=("0", "1"))
    m = m.rename(columns={"player0": "player"}).drop(columns="player1")
    m["mover"] = m.club_id0 != m.club_id1

    def dlog(c):
        return np.log(m[c + "1"]) - np.log(m[c + "0"])

    m["d_out"] = dlog("out90")
    m["d_team"], m["d_share"] = dlog("team_ap90_on"), dlog("usage_on_pitch")
    m["d_mates"], m["d_rel"] = dlog("mates_eff"), dlog("rel")
    assert (m.d_out - m[list(PARTS)].sum(axis=1)).abs().max() < 1e-9
    m["d_situation"] = m[SITUATION].sum(axis=1)
    m["flop"] = m.d_out < FLOP
    return m.reset_index(drop=True)


# ------------------------------------------------------------------ helpers

def boot(df: pd.DataFrame, stat, n=N_BOOT, seed=SEED):
    """Point and 95% interval, resampling whole players."""
    point = np.asarray(stat(df), dtype=float)
    rng = np.random.default_rng(seed)
    idx = df.groupby("tm_player_id").indices
    ids = np.array(list(idx))
    draws = np.array([stat(df.iloc[np.concatenate([idx[i] for i in rng.choice(ids, len(ids))])])
                      for _ in range(n)], dtype=float)
    lo, hi = np.nanpercentile(draws, [2.5, 97.5], axis=0)
    return point, lo, hi


def r3(x):
    return [round(float(v), 4) for v in np.atleast_1d(x)]


def variance_shares(g: pd.DataFrame) -> np.ndarray:
    """cov(part, total) / var(total): how much of the spread in output changes each part
    accounts for. The four add up to 1 and do not depend on picking a tail."""
    v = g.d_out.var()
    return np.array([g[p].cov(g.d_out) / v for p in PARTS])


def tail_shares(g: pd.DataFrame) -> np.ndarray:
    """Share of the mean log fall among flops that each part accounts for."""
    f = g[g.flop]
    return np.array([f[p].mean() / f.d_out.mean() for p in PARTS])


# ------------------------------------------------------------------ 1. movers v stayers

def movers_vs_stayers(m: pd.DataFrame) -> dict:
    def stat(x):
        mv, st = x[x.mover], x[~x.mover]
        return [mv.flop.mean(), st.flop.mean(), mv.flop.mean() - st.flop.mean(),
                np.exp(mv.d_out.mean()) - 1, np.exp(st.d_out.mean()) - 1,
                mv.d_out.mean() - st.d_out.mean()]
    p, lo, hi = boot(m, stat)
    keys = ["flop_rate_movers", "flop_rate_stayers", "flop_rate_gap",
            "mean_change_movers", "mean_change_stayers", "mean_log_gap"]
    out = {k: {"point": r3(p[i])[0], "lo": r3(lo[i])[0], "hi": r3(hi[i])[0]}
           for i, k in enumerate(keys)}
    out["n_movers"], out["n_stayers"] = int(m.mover.sum()), int((~m.mover).sum())
    out["n_flops_movers"] = int((m.mover & m.flop).sum())
    out["n_flops_stayers"] = int((~m.mover & m.flop).sum())
    # the gap in mean log change, part by part: where the extra damage of a move sits
    def gap(x):
        mv, st = x[x.mover], x[~x.mover]
        return [mv[p].mean() - st[p].mean() for p in PARTS]
    p, lo, hi = boot(m, gap)
    out["mean_log_gap_by_part"] = {PARTS[k]: {"point": r3(p[i])[0], "lo": r3(lo[i])[0],
                                              "hi": r3(hi[i])[0]} for i, k in enumerate(PARTS)}
    return out


def splits(m: pd.DataFrame) -> pd.DataFrame:
    """Tail split (as in version 1) and variance split, for movers and stayers."""
    rows = []
    for who, g in (("movers", m[m.mover]), ("stayers", m[~m.mover])):
        for kind, fn in (("flop tail", tail_shares), ("variance", variance_shares)):
            p, lo, hi = boot(g, fn, n=N_BOOT // 2)
            for i, k in enumerate(PARTS):
                rows.append(dict(group=who, split=kind, part=PARTS[k], share=p[i],
                                 lo=lo[i], hi=hi[i], n=len(g), flops=int(g.flop.sum())))
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ 2. noise only

def player_actions() -> pd.DataFrame:
    """Every action (shot or shot-assist, no penalties) with its xG, per player-team-season."""
    s = pd.read_parquet(SOURCE / "understat" / "shots.parquet",
                        columns=["season", "team_shot", "player", "player_assisted",
                                 "xg", "result", "situation"])
    s = s[(s.result != "OwnGoal") & (s.situation != "Penalty")]
    a = pd.concat([s[["season", "team_shot", "player", "xg"]],
                   s.dropna(subset=["player_assisted"])[["season", "team_shot", "player_assisted", "xg"]]
                   .rename(columns={"player_assisted": "player"})])
    return a.rename(columns={"team_shot": "team"})


def noise_benchmark(m: pd.DataFrame, movers: bool = True, n_sims: int = 200) -> dict:
    """What flops look like if each player's quality relative to team-mates never changed.

    Keep every season pair's three situation parts as observed. Replace the change in the
    player's relative quality with pure sampling noise: redraw his actions in each season
    with replacement from his own pooled actions over both seasons, so his true quality is
    the same in both, and take the log change in the mean. Then select flops exactly as
    in the data and split them. Run on stayers too: if the benchmark reproduces the
    stayers' real flop rate, it is calibrated.
    """
    acts = player_actions()
    key = acts.groupby(["season", "team", "player"]).xg.apply(np.array)
    rng = np.random.default_rng(SEED)
    g = m[m.mover == movers].reset_index(drop=True)
    pools, sizes, ok = [], [], []
    for r in g.itertuples():
        a0 = key.get((f"{r.yr}-{r.yr + 1}", r.team0, r.player))
        a1 = key.get((f"{r.yr + 1}-{r.yr + 2}", r.team1, r.player))
        ok.append(a0 is not None and a1 is not None)
        if ok[-1]:
            pools.append(np.concatenate([a0, a1]))
            sizes.append((len(a0), len(a1)))
    ok = np.array(ok)
    sit = g.loc[ok, "d_situation"].to_numpy()
    parts_sit = g.loc[ok, SITUATION].to_numpy()
    rows, sds = [], []
    for _ in range(n_sims):
        d_rel = np.array([np.log(rng.choice(pool, n1).mean()) - np.log(rng.choice(pool, n0).mean())
                          for pool, (n0, n1) in zip(pools, sizes)])
        sds.append(d_rel.std())
        d_out = sit + d_rel
        f = d_out < FLOP
        rows.append([f.mean()] + [parts_sit[f, j].mean() / d_out[f].mean() for j in range(3)]
                    + [d_rel[f].mean() / d_out[f].mean()])
    r = np.array(rows)
    name = "movers" if movers else "stayers"
    pd.DataFrame(r, columns=["flop_rate"] + [PARTS[k] for k in SITUATION] + [PARTS["d_rel"]]
                 ).to_csv(OUT / f"noise_benchmark_draws_{name}.csv", index=False, float_format="%.4f")
    obs = g.loc[ok]
    return {
        "group": name, "pairs": int(ok.sum()), "sims": n_sims,
        "flop_rate_noise_only": r3(np.percentile(r[:, 0], [50, 2.5, 97.5])),
        "flop_rate_observed": r3(obs.flop.mean())[0],
        "player_share_noise_only": r3(np.percentile(r[:, 4], [50, 2.5, 97.5])),
        "player_share_observed": r3(obs.loc[obs.flop, "d_rel"].mean() / obs.loc[obs.flop, "d_out"].mean())[0],
        "sd_d_rel_noise_only": r3(np.mean(sds))[0],
        "sd_d_rel_observed": r3(obs.d_rel.std())[0],
    }


def usage_in_flops(m: pd.DataFrame) -> dict:
    """How much of a flop is losing the ball: the share-of-the-ball part of the average
    flop's fall, and the share of flops that would not have been flops had his share held."""
    def parts(g):
        f = g[g.flop]
        return [f.d_share.mean() / f.d_out.mean(), ((f.d_out - f.d_share) >= FLOP).mean(),
                (f.d_share < 0).mean()]

    def stat(x):
        return parts(x[x.mover]) + parts(x[~x.mover]) + [parts(x[x.mover])[0] - parts(x[~x.mover])[0]]
    p, lo, hi = boot(m, stat)
    keys = ["movers_share_of_fall", "movers_flops_undone", "movers_share_fell",
            "stayers_share_of_fall", "stayers_flops_undone", "stayers_share_fell", "gap_share_of_fall"]
    return {k: {"point": r3(p[i])[0], "lo": r3(lo[i])[0], "hi": r3(hi[i])[0]}
            for i, k in enumerate(keys)}


def age_adjusted(m: pd.DataFrame) -> dict:
    """Movers reweighted to the stayers' age mix, so the gap is not a gap in age."""
    m = m.assign(band=pd.cut(m.age0, [0, 23, 26, 29, 50], right=False, labels=False))
    m = m.dropna(subset=["band"])

    def stat(x):
        st, mv = x[~x.mover], x[x.mover]
        w = st.band.value_counts(normalize=True)
        rate = mv.groupby("band").flop.mean()
        chg = mv.groupby("band").d_out.mean()
        return [(rate * w).sum() - st.flop.mean(), (chg * w).sum() - st.d_out.mean()]
    p, lo, hi = boot(m, stat)
    return {"flop_rate_gap": {"point": r3(p[0])[0], "lo": r3(lo[0])[0], "hi": r3(hi[0])[0]},
            "mean_log_gap": {"point": r3(p[1])[0], "lo": r3(lo[1])[0], "hi": r3(hi[1])[0]}}


# ------------------------------------------------------------------ 3. who flops

def fees() -> pd.DataFrame:
    t = pd.read_csv(SOURCE / "transfermarkt" / "transfers.csv.gz",
                    usecols=["player_id", "transfer_date", "to_club_id", "transfer_fee"])
    t["date"] = pd.to_datetime(t.transfer_date, errors="coerce")
    return t.rename(columns={"player_id": "tm_player_id", "to_club_id": "club_id1"})


def slices(m: pd.DataFrame) -> pd.DataFrame:
    """Flop rate and mean change for movers and stayers, by age, fee, league path."""
    mv = m[m.mover].copy()
    # the last Transfermarkt transfer of this player into the new club between July of the
    # first season and the end of the calendar year the second season starts in
    t = fees().merge(mv[["tm_player_id", "club_id1", "yr"]], on=["tm_player_id", "club_id1"])
    lo = pd.to_datetime(t.yr.astype(str) + "-07-01")
    hi = pd.to_datetime((t.yr + 1).astype(str) + "-12-31")
    t = (t[(t.date >= lo) & (t.date <= hi)].sort_values("date")
         .drop_duplicates(["tm_player_id", "club_id1", "yr"], keep="last"))
    mv = mv.merge(t[["tm_player_id", "club_id1", "yr", "transfer_fee"]],
                  on=["tm_player_id", "club_id1", "yr"], how="left")
    mv["fee_band"] = pd.cut(mv.transfer_fee.fillna(-1), [-2, -0.5, 0, 10e6, 30e6, 1e12],
                            labels=["No fee on record", "Free or loan", "Under €10m",
                                    "€10m–30m", "Over €30m"])
    mv["path"] = np.where(mv.league0 == mv.league1, "Same league", "Changed league")
    m = m.copy()
    m["age_band"] = pd.cut(m.age0, [0, 23, 26, 29, 50], right=False,
                           labels=["Under 23", "23–25", "26–28", "29 and over"])
    mv["age_band"] = pd.cut(mv.age0, [0, 23, 26, 29, 50], right=False,
                            labels=["Under 23", "23–25", "26–28", "29 and over"])
    rows = []

    def add(dim, g, who):
        for lev, x in g.groupby(dim, observed=True):
            if len(x) < 25:
                continue
            p, lo, hi = boot(x, lambda y: [y.flop.mean(), np.exp(y.d_out.mean()) - 1,
                                           y.d_rel.mean(), y.d_situation.mean()], n=N_BOOT // 4)
            rows.append(dict(slice=dim, level=str(lev), group=who, n=len(x),
                             flop_rate=p[0], flop_lo=lo[0], flop_hi=hi[0],
                             mean_change=p[1], change_lo=lo[1], change_hi=hi[1],
                             d_player=p[2], d_situation=p[3]))
    add("age_band", mv, "movers")
    add("age_band", m[~m.mover], "stayers")
    add("fee_band", mv, "movers")
    add("path", mv, "movers")
    return pd.DataFrame(rows), mv


def buying_clubs(mv: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Average change in the player's own quality (relative to team-mates) after joining
    each club, shrunk towards the overall mean (empirical Bayes), and whether a club's
    record in one half of the years predicts the other half."""
    g = mv.groupby("club_id1")
    mean_all = mv.d_rel.mean()
    var_within = mv.d_rel.var()
    c = g.agg(n=("d_rel", "size"), mean=("d_rel", "mean"), team=("team1", "last"),
              league=("league1", "last")).reset_index()
    tau2 = max(c["mean"].var() - (var_within / c.n).mean(), 1e-6)
    c["shrunk"] = mean_all + (c["mean"] - mean_all) * tau2 / (tau2 + var_within / c.n)
    # persistence: early years against late years, clubs with 4+ signings in each
    early = mv[mv.yr <= 2018].groupby("club_id1").d_rel.agg(["mean", "size"])
    late = mv[mv.yr >= 2019].groupby("club_id1").d_rel.agg(["mean", "size"])
    j = early.merge(late, left_index=True, right_index=True, suffixes=("_e", "_l"))
    j = j[(j.size_e >= 4) & (j.size_l >= 4)]
    rho = float(j.mean_e.corr(j.mean_l, method="spearman")) if len(j) > 5 else float("nan")
    rng = np.random.default_rng(SEED)
    null = [j.mean_e.corr(pd.Series(rng.permutation(j.mean_l.to_numpy()), index=j.index),
                          method="spearman") for _ in range(2000)]
    persist = {"clubs": int(len(j)), "spearman_early_late": round(rho, 3),
               "perm_p": round(float(np.mean(np.abs(null) >= abs(rho))), 3),
               "tau": round(float(np.sqrt(tau2)), 4)}
    return c.sort_values("shrunk"), persist


# ------------------------------------------------------------------ 4. predict a flop

def _logit(X, y, lam=1.0, iters=50):
    X = np.column_stack([np.ones(len(X)), X])
    b = np.zeros(X.shape[1])
    for _ in range(iters):
        p = 1 / (1 + np.exp(-X @ b))
        W = p * (1 - p)
        H = X.T @ (X * W[:, None]) + lam * np.diag([0] + [1] * (X.shape[1] - 1))
        b -= np.linalg.solve(H, X.T @ (p - y) + lam * np.r_[0, b[1:]])
    return b


def _auc(score, y):
    order = np.argsort(score)
    ranks = np.empty(len(score))
    ranks[order] = np.arange(1, len(score) + 1)
    pos = y == 1
    return (ranks[pos].sum() - pos.sum() * (pos.sum() + 1) / 2) / (pos.sum() * (~pos).sum())


def predict_flops(m: pd.DataFrame) -> dict:
    """Can you see a flop coming, using only what is known on the day of the move?
    Train on moves into 2015-16 to 2019-20, test on 2020-21 onwards, untouched."""
    mv = m[m.mover].copy()
    feats = {
        "age": mv.age0,
        "log out per 90 last season": np.log(mv.out900),
        "log quality vs team-mates": np.log(mv.rel0),
        "log share of the ball": np.log(mv.usage_on_pitch0),
        "share of minutes played": mv.minutes_share0,
        "changed league": (mv.league0 != mv.league1).astype(float),
    }
    X = pd.DataFrame(feats).astype(float)
    ok = X.notna().all(axis=1)
    X, y, yr = X[ok], mv.flop[ok].astype(float).to_numpy(), mv.yr[ok].to_numpy()
    mu, sd = X[yr <= 2018].mean(), X[yr <= 2018].std()
    Z = ((X - mu) / sd).to_numpy()
    tr, te = yr <= 2018, yr >= 2019
    b = _logit(Z[tr], y[tr])
    score = np.column_stack([np.ones(te.sum()), Z[te]]) @ b
    auc = _auc(score, y[te])
    rng = np.random.default_rng(SEED)
    idx = np.where(te)[0]
    bs = []
    for _ in range(N_BOOT):
        k = rng.choice(len(idx), len(idx))
        if y[te][k].min() == y[te][k].max():
            continue
        bs.append(_auc(score[k], y[te][k]))
    top = score >= np.quantile(score, 0.8)
    return {
        "train_moves": int(tr.sum()), "test_moves": int(te.sum()),
        "test_flop_rate": round(float(y[te].mean()), 3),
        "auc": round(float(auc), 3), "auc_lo": round(float(np.percentile(bs, 2.5)), 3),
        "auc_hi": round(float(np.percentile(bs, 97.5)), 3),
        "flop_rate_top_fifth_of_risk": round(float(y[te][top].mean()), 3),
        "flop_rate_rest": round(float(y[te][~top].mean()), 3),
        "coefficients": {k: round(float(v), 3) for k, v in zip(X.columns, b[1:])},
    }


def age_gaps(m: pd.DataFrame) -> pd.DataFrame:
    """Flop rate of movers minus stayers within each age band, resampling players."""
    m = m.assign(age_band=pd.cut(m.age0, [0, 23, 26, 29, 50], right=False,
                                 labels=["Under 23", "23–25", "26–28", "29 and over"]))
    rows = []
    for b, g in m.groupby("age_band", observed=True):
        p, lo, hi = boot(g, lambda x: [x[x.mover].flop.mean() - x[~x.mover].flop.mean()])
        rows.append(dict(age_band=str(b), movers=int(g.mover.sum()), stayers=int((~g.mover).sum()),
                         gap=p[0], lo=lo[0], hi=hi[0]))
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ main

def main():
    m = season_pairs()
    m.to_parquet(WORK / "season_pairs.parquet", index=False)
    res = {"pairs": int(len(m)), "players": int(m.tm_player_id.nunique()),
           "seasons": f"{m.yr.min()}-{m.yr.min() + 1} to {m.yr.max() + 1}-{m.yr.max() + 2}"}
    res["movers_vs_stayers"] = movers_vs_stayers(m)
    sp = splits(m)
    sp.to_csv(OUT / "transfer_splits.csv", index=False, float_format="%.4f")
    res["noise_benchmark"] = noise_benchmark(m, movers=True)
    res["noise_benchmark_stayers"] = noise_benchmark(m, movers=False)
    res["age_adjusted"] = age_adjusted(m)
    res["usage_in_flops"] = usage_in_flops(m)
    sl, mv = slices(m)
    sl.to_csv(OUT / "transfer_slices.csv", index=False, float_format="%.4f")
    ag = age_gaps(m)
    ag.to_csv(OUT / "age_gaps.csv", index=False, float_format="%.4f")
    print(ag.round(3).to_string(index=False))
    clubs, persist = buying_clubs(mv)
    clubs[clubs.n >= 8].to_csv(OUT / "buying_clubs.csv", index=False, float_format="%.4f")
    res["buying_club_persistence"] = persist
    res["predict_flops"] = predict_flops(m)
    (OUT / "transfers.json").write_text(json.dumps(res, indent=1))
    pd.set_option("display.width", 180)
    print(json.dumps(res, indent=1))
    print(sp.round(3).to_string(index=False))
    print(sl.round(3).to_string(index=False))
    print(clubs[clubs.n >= 8].head(8).round(3).to_string(index=False))
    print(clubs[clubs.n >= 8].tail(8).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
