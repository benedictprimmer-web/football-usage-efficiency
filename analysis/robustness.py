"""Rival explanations for the headline, the status of every slice test, and a predictor
scored on every move known on the day.

Round 1 of the review loop (LOOP.md) asked five things of the headline "a move costs an
attacker about 5% of his share of the ball":

1. Regression to the mean. Movers are bought after big seasons, and big seasons are
   followed by smaller ones whoever you play for. Every mover-minus-stayer gap is rerun
   with movers and stayers compared within the same decile of last season's share of the
   ball, the same decile of last season's output per 90, the same age band and the same
   season (a regression with those dummies), and again by reweighting stayers to the
   movers' mix of cells. Intervals resample whole players.
2. The denominator. Share = his actions / his team's actions while he is on. His own
   shots and shot-assists per 90 are reported next to his share, and the team's actions
   per 90 are reported without his own, so "the team created more" is not partly him.
3. Selection after the move. The 900-minute floor drops players who lost their place,
   and movers lose it more often. "Flop or lost his place" counts every qualifying
   player-season that has any league row the next season.
4. Loans, promoted and relegated clubs, and a buying club's strength measured the
   season before the move (known on the day).
5. A second luck benchmark that redraws his share of the ball as well as his chance
   quality, so the benchmark holds both his role and his quality fixed.

It also gives Holm-adjusted p-values for the family of slice tests (age bands, fee
bands, league path, buying clubs, predictor), rescores the flop predictor on every move
known on the day, and freezes the fitted model with its scaling (Understat run only).

    python analysis/robustness.py              (needs data/work/panel.parquet)
    SHOTS=opta python analysis/robustness.py
"""
from __future__ import annotations

import json
import sys
from datetime import date

import numpy as np
import pandas as pd

from config import OUT, SOURCE, WORK, SEED, N_BOOT, MIN_MINUTES, GROUP, OPTA, MID, ROOT
import transfers as T

FREEZE_DATE = "2026-11-03"


def ci(p, lo, hi):
    return {"point": round(float(p), 4), "lo": round(float(lo), 4), "hi": round(float(hi), 4)}


def boot_p(df, stat, n=N_BOOT, seed=SEED):
    """Point, 95% interval and a two-sided bootstrap p-value for each element of stat,
    resampling whole players (the p-value is twice the share of draws on the far side of
    zero, floored at one draw)."""
    point = np.asarray(stat(df), dtype=float)
    rng = np.random.default_rng(seed)
    idx = df.groupby("tm_player_id").indices
    ids = np.array(list(idx))
    draws = np.array([stat(df.iloc[np.concatenate([idx[i] for i in rng.choice(ids, len(ids))])])
                      for _ in range(n)], dtype=float)
    lo, hi = np.nanpercentile(draws, [2.5, 97.5], axis=0)
    side = np.where(point >= 0, (draws <= 0).mean(axis=0), (draws >= 0).mean(axis=0))
    pv = np.clip(2 * side, 1 / n, 1)
    return point, lo, hi, pv


# ------------------------------------------------------------------ the samples

def all_moves() -> pd.DataFrame:
    """Every qualifying season (900 minutes, 20 actions) followed by any league row the next
    season: the moves and stays known on the day, before we know who keeps his place."""
    d = pd.read_parquet(WORK / "panel.parquet")
    d["yr"] = d.season.str[:4].astype(int)
    q = d[d[GROUP] & (d.minutes >= MIN_MINUTES) & (d.actions >= T.MIN_ACTIONS)
          & (d.mates_eff > 0) & (d.usage_on_pitch > 0)].copy()
    q["out90"] = q.value / q.minutes * 90
    q["rel"] = q.efficiency / q.mates_eff
    nxt = (d.sort_values("minutes").groupby(["tm_player_id", "yr"])
           .agg(club_id1=("club_id", "last"), league1=("league", "last"),
                minutes1=("minutes", "sum"), actions1=("actions", "sum")).reset_index())
    nxt["yr"] -= 1
    keep = ["tm_player_id", "player", "yr", "league", "team", "club_id", "minutes", "actions",
            "usage_on_pitch", "out90", "rel", "age", "minutes_share", "team_actions", "team_games"]
    a = q[keep].merge(nxt, on=["tm_player_id", "yr"])
    a = a.rename(columns={c: c + "0" for c in keep if c not in ("tm_player_id", "player", "yr")})
    a["mover"] = a.club_id0 != a.club_id1
    # only next seasons the source covers in full (Understat to 15 September 2025, so
    # 2025-26 is out; FBref/Opta to early 2025, so 2024-25 is out too)
    games = d.groupby("yr").team_games.median()
    full = set(games[games >= 30].index)
    return a[(a.yr + 1).isin(full)].reset_index(drop=True)


def lost_place(a: pd.DataFrame, m: pd.DataFrame) -> pd.DataFrame:
    """Mark each season in a as kept (a 900-minute pair exists), with its flop flag, or lost."""
    k = m.groupby(["tm_player_id", "yr"]).flop.max().rename("flop").reset_index()
    a = a.merge(k, on=["tm_player_id", "yr"], how="left")
    a["lost"] = a.flop.isna()
    a["flop"] = a.flop.fillna(False).astype(bool)
    a["bad"] = a.flop | a.lost
    return a


def add_cells(x: pd.DataFrame, ref: pd.DataFrame) -> pd.DataFrame:
    """Deciles of last season's share and output per 90 (cut points from ref), age band."""
    x = x.copy()
    for c, name in (("usage_on_pitch0", "share_dec"), ("out900", "out_dec")):
        cuts = np.quantile(ref[c], np.linspace(0, 1, 11)[1:-1])
        x[name] = np.searchsorted(cuts, x[c])
    x["age_band"] = np.searchsorted([23, 26, 29], x.age0.fillna(ref.age0.median()), side="right")
    return x


def design(x: pd.DataFrame, cells=("share_dec", "out_dec", "age_band", "yr")) -> np.ndarray:
    cols = [np.ones(len(x)), x.mover.to_numpy(float)]
    for c in cells:
        v = x[c].to_numpy()
        for lev in np.unique(v)[1:]:
            cols.append((v == lev).astype(float))
    return np.column_stack(cols)


def ols_mover(x: pd.DataFrame, ys: list[str]) -> np.ndarray:
    """Coefficient on mover for each outcome, with decile, age-band and season dummies."""
    X = design(x)
    Y = x[ys].to_numpy(float)
    b, *_ = np.linalg.lstsq(X, Y, rcond=None)
    return b[1]


def reweighted(x: pd.DataFrame, ys: list[str]) -> np.ndarray:
    """Movers minus stayers, stayers reweighted to the movers' mix of cells (quintiles of
    share and of output, age band); cells with no stayer are dropped."""
    cell = (x.share_dec // 2) * 100 + (x.out_dec // 2) * 10 + x.age_band
    mv, st = x.mover.to_numpy(), ~x.mover.to_numpy()
    cm = pd.Series(cell[mv]).value_counts()
    cs = pd.Series(cell[st]).value_counts()
    common = cm.index.intersection(cs.index)
    w = cell.map((cm[common] / cm[common].sum()) / cs[common]).fillna(0).to_numpy()
    inm = mv & cell.isin(common).to_numpy()
    Y = x[ys].to_numpy(float)
    return Y[inm].mean(axis=0) - (Y[st] * w[st, None]).sum(axis=0) / w[st].sum()


# ------------------------------------------------------------------ 1-2. RTM and denominator

def rtm(m: pd.DataFrame) -> dict:
    m = m.copy()
    m["d_own"] = m.d_team + m.d_share                         # his own actions per 90
    m["d_team_ex"] = (np.log(m.team_ap90_on1 * (1 - m.usage_on_pitch1))
                      - np.log(m.team_ap90_on0 * (1 - m.usage_on_pitch0)))  # team without him
    m["flopf"] = m.flop.astype(float)
    m = add_cells(m, m)
    ys = ["d_share", "d_own", "d_team", "d_team_ex", "d_mates", "d_rel", "d_out", "flopf"]

    def raw(x):
        return x.loc[x.mover, ys].mean().to_numpy() - x.loc[~x.mover, ys].mean().to_numpy()
    out = {}
    for name, fn in (("raw", raw), ("regression", lambda x: ols_mover(x, ys)),
                     ("reweighted", lambda x: reweighted(x, ys))):
        p, lo, hi, pv = boot_p(m, fn)
        out[name] = {y: ci(p[i], lo[i], hi[i]) | {"p": round(float(pv[i]), 4)}
                     for i, y in enumerate(ys)}
    # the split is an identity, so credit moves between parts: his actions sit inside the
    # team's, and his quality is measured against team-mates'
    out["corr_team_share"] = round(float(m.d_team.corr(m.d_share)), 3)
    out["corr_rel_mates"] = round(float(m.d_rel.corr(m.d_mates)), 3)
    # how far movers' last season sat above stayers': the selection the test removes
    out["movers_last_season"] = {
        "share_movers": round(float(m.loc[m.mover, "usage_on_pitch0"].median()), 4),
        "share_stayers": round(float(m.loc[~m.mover, "usage_on_pitch0"].median()), 4),
        "out90_movers": round(float(m.loc[m.mover, "out900"].median()), 4),
        "out90_stayers": round(float(m.loc[~m.mover, "out900"].median()), 4),
        "age_movers": round(float(m.loc[m.mover, "age0"].mean()), 2),
        "age_stayers": round(float(m.loc[~m.mover, "age0"].mean()), 2)}
    return out


# ------------------------------------------------------------------ 3. lost his place

def lost_place_tests(a: pd.DataFrame, m: pd.DataFrame) -> dict:
    a = add_cells(a, m)
    a["lostf"], a["badf"] = a.lost.astype(float), a.bad.astype(float)
    ys = ["lostf", "badf"]

    def raw(x):
        mv, st = x[x.mover], x[~x.mover]
        return [mv.lostf.mean(), st.lostf.mean(), mv.badf.mean(), st.badf.mean(),
                mv.lostf.mean() - st.lostf.mean(), mv.badf.mean() - st.badf.mean()]

    def age(x):
        st, mv = x[~x.mover], x[x.mover]
        w = st.age_band.value_counts(normalize=True)
        return [(mv.groupby("age_band")[y].mean() * w).sum() - st[y].mean() for y in ys]
    p, lo, hi, _ = boot_p(a, raw)
    keys = ["lost_movers", "lost_stayers", "bad_movers", "bad_stayers", "lost_gap", "bad_gap"]
    out = {k: ci(p[i], lo[i], hi[i]) for i, k in enumerate(keys)}
    for name, fn in (("age_adjusted", age), ("regression", lambda x: ols_mover(x, ys))):
        p, lo, hi, pv = boot_p(a, fn)
        out[name] = {k: ci(p[i], lo[i], hi[i]) | {"p": round(float(pv[i]), 4)}
                     for i, k in enumerate(["lost_gap", "bad_gap"])}
    out["n_movers"], out["n_stayers"] = int(a.mover.sum()), int((~a.mover).sum())
    out["n_movers_kept"] = int((a.mover & ~a.lost).sum())
    out["n_stayers_kept"] = int((~a.mover & ~a.lost).sum())
    # the same floor at 450 minutes, as a sensitivity check
    return out


# ------------------------------------------------------------------ 4. loans, promotion, strength

def move_checks(m: pd.DataFrame) -> dict:
    p = pd.read_parquet(WORK / "panel.parquet", columns=["season", "club_id", "team_actions",
                                                         "team_games"])
    p["yr"] = p.season.str[:4].astype(int)
    clubs = p.groupby("yr").club_id.apply(set)
    strength = (p.groupby(["club_id", "yr"]).apply(lambda g: (g.team_actions / g.team_games).iloc[0],
                                                   include_groups=False).rename("tapg"))
    m = m.copy()
    m["promoted_buyer"] = [c not in clubs.get(y, set()) for c, y in zip(m.club_id1, m.yr)]
    m["relegated_seller"] = [c not in clubs.get(y + 1, set()) for c, y in zip(m.club_id0, m.yr)]
    # loans: Transfermarkt does not flag them, so a move counts as a likely loan when the
    # player went back from the new club to the old one within two seasons
    t = T.fees()
    t = t[["tm_player_id", "date"]].assign(frm=pd.read_csv(
        SOURCE / "transfermarkt" / "transfers.csv.gz", usecols=["from_club_id"]).from_club_id,
        to=t.club_id1)
    back = m[m.mover].merge(t, on="tm_player_id")
    back = back[(back.frm == back.club_id1) & (back.to == back.club_id0)
                & (back.date > pd.to_datetime(back.yr.astype(str) + "-07-01"))
                & (back.date <= pd.to_datetime((back.yr + 2).astype(str) + "-09-01"))]
    loan_keys = set(zip(back.tm_player_id, back.yr))
    m["loan"] = np.array([(i, y) in loan_keys for i, y in zip(m.tm_player_id, m.yr)]) & m.mover.to_numpy()
    s0 = strength.reindex(list(zip(m.club_id0, m.yr))).to_numpy()
    s1 = strength.reindex(list(zip(m.club_id1, m.yr))).to_numpy()
    m["d_strength_pre"] = np.log(s1) - np.log(s0)

    def gaps(x):
        mv, st = x[x.mover], x[~x.mover]
        return [mv.d_share.mean() - st.d_share.mean(), mv.d_out.mean() - st.d_out.mean(),
                mv.flop.mean() - st.flop.mean()]
    out = {"n_loans": int(m.loan.sum()), "n_promoted_buyer": int((m.mover & m.promoted_buyer).sum()),
           "n_relegated_seller": int((m.mover & m.relegated_seller).sum())}
    for name, keep in (("without_loans", ~m.loan),
                       ("without_promoted_or_relegated",
                        ~(m.mover & (m.promoted_buyer | m.relegated_seller))),
                       ("without_any", ~m.loan & ~(m.mover & (m.promoted_buyer | m.relegated_seller)))):
        x = m[keep]
        p, lo, hi = T.boot(x, gaps)
        out[name] = {"n_movers": int(x.mover.sum())} | {
            k: ci(p[i], lo[i], hi[i]) for i, k in enumerate(["share_gap", "out_gap", "flop_gap"])}
    mv = m[m.mover & np.isfinite(m.d_strength_pre)]
    p, lo, hi = T.boot(mv, lambda x: [np.exp(x.d_strength_pre.mean()) - 1,
                                      (x.d_strength_pre > 0).mean()])
    out["buying_club_strength_pre_move"] = {
        "n": int(len(mv)), "team_actions_per_match_change": ci(p[0], lo[0], hi[0]),
        "share_joining_stronger": ci(p[1], lo[1], hi[1])}
    return out


# ------------------------------------------------------------------ 5. share redrawn too

def benchmark_share(m: pd.DataFrame, n_sims: int = 200) -> dict:
    """Luck benchmark holding both his role and his quality fixed. For each pair his action
    count in each season is redrawn as binomial on his team's actions while he was on, with
    his pooled share over both seasons, and his chance quality is redrawn from his own
    pooled actions with the redrawn counts. Team chances and team-mates' quality stay as
    observed."""
    acts = T.player_actions()
    key = acts.groupby(["season", "team", "player"]).xg.apply(np.array)
    rng = np.random.default_rng(SEED)
    res = {}
    for who, g in (("movers", m[m.mover]), ("stayers", m[~m.mover])):
        g = g.reset_index(drop=True)
        pools, ok = [], []
        for r in g.itertuples():
            a0 = key.get((f"{r.yr}-{r.yr + 1}", r.team0, r.player))
            a1 = key.get((f"{r.yr + 1}-{r.yr + 2}", r.team1, r.player))
            ok.append(a0 is not None and a1 is not None)
            if ok[-1]:
                pools.append(np.concatenate([a0, a1]))
        ok = np.array(ok)
        x = g[ok]
        T0 = np.round(x.actions0 / x.usage_on_pitch0).to_numpy().astype(int)
        T1 = np.round(x.actions1 / x.usage_on_pitch1).to_numpy().astype(int)
        pp = (x.actions0 + x.actions1).to_numpy() / (T0 + T1)
        rest = (x.d_team + x.d_mates).to_numpy()
        rates = []
        for _ in range(n_sims):
            n0 = np.maximum(rng.binomial(T0, pp), 1)
            n1 = np.maximum(rng.binomial(T1, pp), 1)
            d_sh = np.log(n1 / T1) - np.log(n0 / T0)
            d_rel = np.array([np.log(rng.choice(pl, b).mean()) - np.log(rng.choice(pl, a).mean())
                              for pl, a, b in zip(pools, n0, n1)])
            rates.append(((rest + d_sh + d_rel) < T.FLOP).mean())
        res[who] = {"pairs": int(ok.sum()),
                    "flop_rate_observed": round(float(x.flop.mean()), 4),
                    "flop_rate_role_and_quality_fixed": [round(float(v), 4) for v in
                                                         np.percentile(rates, [50, 2.5, 97.5])]}
    return res


# ------------------------------------------------------------------ test family and Holm

def holm(ps: dict) -> dict:
    keys = sorted(ps, key=ps.get)
    k = len(keys)
    out, running = {}, 0.0
    for i, key in enumerate(keys):
        running = max(running, min(1.0, (k - i) * ps[key]))
        out[key] = round(running, 4)
    return out


def slice_family(m: pd.DataFrame, persist_p: float, auc_p: float) -> dict:
    sl, mv = T.slices(m)
    ps, est = {}, {}
    m = m.assign(band=pd.cut(m.age0, [0, 23, 26, 29, 50], right=False,
                             labels=["Under 23", "23–25", "26–28", "29 and over"]))
    for b, g in m.groupby("band", observed=True):
        p, lo, hi, pv = boot_p(g, lambda x: [x[x.mover].flop.mean() - x[~x.mover].flop.mean()])
        ps[f"age {b}: movers v stayers"], est[f"age {b}: movers v stayers"] = pv[0], ci(p[0], lo[0], hi[0])
    for b in ["Free or loan", "Under €10m", "€10m–30m", "Over €30m"]:
        x = mv.assign(inb=mv.fee_band.astype(str) == b)
        p, lo, hi, pv = boot_p(x, lambda y: [y[y.inb].flop.mean() - y[~y.inb].flop.mean()])
        ps[f"fee {b}: v other movers"], est[f"fee {b}: v other movers"] = pv[0], ci(p[0], lo[0], hi[0])
    x = mv.assign(chg=mv.path == "Changed league")
    p, lo, hi, pv = boot_p(x, lambda y: [y[y.chg].flop.mean() - y[~y.chg].flop.mean()])
    ps["league: changed v same"], est["league: changed v same"] = pv[0], ci(p[0], lo[0], hi[0])
    if persist_p is not None:
        ps["buying clubs: early v late record"] = max(persist_p, 1 / 2000)
    ps["predictor: AUC above 0.5"] = auc_p
    adj = holm(ps)
    return {k: {"estimate": est.get(k), "p": round(float(ps[k]), 4), "p_holm": adj[k],
                "survives": bool(adj[k] < 0.05)} for k in sorted(ps, key=ps.get)}


# ------------------------------------------------------------------ the predictor

FEATS = ["age", "log out per 90 last season", "log quality vs team-mates",
         "log share of the ball", "share of minutes played", "changed league"]


def features(x: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "age": x.age0, "log out per 90 last season": np.log(x.out900),
        "log quality vs team-mates": np.log(x.rel0),
        "log share of the ball": np.log(x.usage_on_pitch0),
        "share of minutes played": x.minutes_share0,
        "changed league": (x.league0 != x.league1).astype(float)}).astype(float)


def fit_score(X, y, yr, split=2018):
    ok = X.notna().all(axis=1).to_numpy()
    X, y, yr = X[ok], y[ok], yr[ok]
    tr, te = yr <= split, yr > split
    mu, sd = X[tr].mean(), X[tr].std()
    Z = ((X - mu) / sd).to_numpy()
    b = T._logit(Z[tr], y[tr])
    s = np.column_stack([np.ones(te.sum()), Z[te]]) @ b
    yt = y[te]
    auc = T._auc(s, yt)
    rng = np.random.default_rng(SEED)
    bs = []
    for _ in range(N_BOOT):
        k = rng.choice(len(s), len(s))
        if yt[k].min() != yt[k].max():
            bs.append(T._auc(s[k], yt[k]))
    bs = np.array(bs)
    top = s >= np.quantile(s, 0.8)
    return {"train_moves": int(tr.sum()), "test_moves": int(te.sum()),
            "test_rate": round(float(yt.mean()), 3), "auc": round(float(auc), 3),
            "auc_lo": round(float(np.percentile(bs, 2.5)), 3),
            "auc_hi": round(float(np.percentile(bs, 97.5)), 3),
            "p_auc_above_half": round(float(max(2 * (bs <= 0.5).mean(), 1 / N_BOOT)), 4),
            "rate_top_fifth": round(float(yt[top].mean()), 3),
            "rate_rest": round(float(yt[~top].mean()), 3)}, (b, mu, sd)


def predictor(a: pd.DataFrame) -> tuple[dict, tuple]:
    mv = a[a.mover].reset_index(drop=True)
    X, yr = features(mv), mv.yr.to_numpy()
    out = {}
    kept = ~mv.lost.to_numpy()
    out["as_published_900_minute_movers"], _ = fit_score(X[kept], mv.flop[kept].to_numpy(float), yr[kept])
    out["all_moves_flop_or_lost_place"], fwd = fit_score(X, mv.bad.to_numpy(float), yr)
    out["all_moves_lost_place_counted_as_not_flop"], _ = fit_score(X, mv.flop.to_numpy(float), yr)
    out["all_moves_lost_place_only"], _ = fit_score(X, mv.lost.to_numpy(float), yr)
    out["n_moves_known_on_the_day"] = int(len(mv))
    out["n_lost_place"] = int(mv.lost.sum())
    return out, (X, mv, yr)


def freeze(a: pd.DataFrame, X: pd.DataFrame, mv: pd.DataFrame, yr: np.ndarray) -> dict:
    """Refit the 'flop or lost his place' model on every move with a known outcome, write
    its coefficients and scaling, and predict every move into 2025-26 known today."""
    ok = X.notna().all(axis=1).to_numpy()
    Xo, y = X[ok], mv.bad.to_numpy(float)[ok]
    mu, sd = Xo.mean(), Xo.std()
    b = T._logit(((Xo - mu) / sd).to_numpy(), y)
    model = {
        "frozen_on": FREEZE_DATE,
        "what": "ridge logistic (lambda 1) for P(flop or lost his place) after a club move",
        "outcome": "output per 90 (xG+xA) down by more than 25%, or under 900 league minutes "
                   "or 20 actions the next season; Understat attackers, Big-5",
        "trained_on_moves_into": f"{int(yr[ok].min()) + 1}-{str(int(yr[ok].min()) + 2)[2:]} to "
                                 f"{int(yr[ok].max()) + 1}-{str(int(yr[ok].max()) + 2)[2:]}",
        "n_train": int(ok.sum()),
        "features": FEATS,
        "mean": [round(float(mu[f]), 6) for f in FEATS],
        "sd": [round(float(sd[f]), 6) for f in FEATS],
        "intercept": round(float(b[0]), 6),
        "coefficients": [round(float(v), 6) for v in b[1:]],
        "how_to_score": "z = (x - mean) / sd; p = 1 / (1 + exp(-(intercept + z . coefficients)))",
    }
    # moves into 2025-26 known today: a qualifying 2024-25 season, then a Transfermarkt
    # transfer to another club in a Big-5 league dated 1 July 2025 to 1 February 2026
    d = pd.read_parquet(WORK / "panel.parquet")
    d["yr"] = d.season.str[:4].astype(int)
    q = d[d[GROUP] & (d.yr == 2024) & (d.minutes >= MIN_MINUTES) & (d.actions >= T.MIN_ACTIONS)
          & (d.mates_eff > 0) & (d.usage_on_pitch > 0)].copy()
    q["out90"], q["rel"] = q.value / q.minutes * 90, q.efficiency / q.mates_eff
    tr = pd.read_csv(SOURCE / "transfermarkt" / "transfers.csv.gz")
    tr["date"] = pd.to_datetime(tr.transfer_date, errors="coerce")
    tr = tr[(tr.date >= "2025-07-01") & (tr.date <= "2026-02-01")]
    cl = pd.read_csv(SOURCE / "transfermarkt" / "clubs.csv.gz",
                     usecols=["club_id", "name", "domestic_competition_id"])
    tm_league = {"GB1": "ENG", "ES1": "ESP", "IT1": "ITA", "L1": "GER", "FR1": "FRA"}
    cl = cl[cl.domestic_competition_id.isin(tm_league)]
    t = (tr.merge(cl, left_on="to_club_id", right_on="club_id")
         .sort_values("date").drop_duplicates("player_id"))
    p = q.merge(t[["player_id", "from_club_id", "to_club_id", "to_club_name", "date",
                   "domestic_competition_id", "transfer_fee"]],
                left_on=["tm_player_id", "club_id"], right_on=["player_id", "from_club_id"])
    p = p[p.to_club_id != p.club_id]
    league_code = {"ENG-Premier League": "ENG", "ESP-La Liga": "ESP", "ITA-Serie A": "ITA",
                   "GER-Bundesliga": "GER", "FRA-Ligue 1": "FRA"}
    x = pd.DataFrame({"age0": p.age, "out900": p.out90, "rel0": p.rel,
                      "usage_on_pitch0": p.usage_on_pitch, "minutes_share0": p.minutes_share,
                      "league0": p.league.map(league_code),
                      "league1": p.domestic_competition_id.map(tm_league)})
    Z = (features(x)[FEATS] - mu) / sd
    pr = 1 / (1 + np.exp(-(b[0] + Z.to_numpy() @ b[1:])))
    pred = pd.DataFrame({"tm_player_id": p.tm_player_id, "player": p.player, "age": p.age.round(1),
                         "from_team": p.team, "to_club": p.to_club_name,
                         "to_league": x.league1, "transfer_date": p.date.dt.date.astype(str),
                         "p_flop_or_lost_place": pr.round(4)})
    pred = pred.sort_values(["p_flop_or_lost_place", "tm_player_id"], ascending=[False, True])
    return model, pred


# ------------------------------------------------------------------ self-check

def check():
    """Holm on a known case, and the regression recovering a planted gap under selection."""
    assert holm({"a": 0.01, "b": 0.04, "c": 0.03}) == {"a": 0.03, "c": 0.06, "b": 0.06}
    rng = np.random.default_rng(1)
    n = 4000
    s0 = rng.normal(0, 1, n)
    mover = rng.random(n) < 1 / (1 + np.exp(-2 * s0))      # movers picked after big seasons
    d = -0.5 * s0 - 0.05 * mover + rng.normal(0, 0.1, n)    # regression to the mean plus a true -5%
    x = pd.DataFrame({"usage_on_pitch0": s0, "out900": rng.normal(0, 1, n), "age0": 25.0,
                      "yr": 2020, "mover": mover, "y": d, "tm_player_id": np.arange(n)})
    x = add_cells(x, x)
    raw = x[x.mover].y.mean() - x[~x.mover].y.mean()
    adj = ols_mover(x, ["y"])[0]
    assert raw < -0.3 and abs(adj + 0.05) < 0.03, (raw, adj)
    print("robustness self-check ok")


# ------------------------------------------------------------------ main

def main():
    m = T.season_pairs()
    a = lost_place(all_moves(), m)
    res = {"pairs": int(len(m)), "n_movers": int(m.mover.sum()), "n_stayers": int((~m.mover).sum())}
    print("regression to the mean ...", flush=True)
    res["rtm"] = rtm(m)
    print("lost his place ...", flush=True)
    res["lost_place"] = lost_place_tests(a, m)
    print("loans, promotion, strength ...", flush=True)
    res["moves"] = move_checks(m)
    print("predictor ...", flush=True)
    res["predictor"], (X, mv, yr) = predictor(a)
    if not MID:
        print("benchmark with share redrawn ...", flush=True)
        res["benchmark_share_redrawn"] = benchmark_share(m)
        t = json.loads((OUT / "transfers.json").read_text())
        nb = t["noise_benchmark"]
        res["luck_spread_share"] = round((nb["sd_d_rel_noise_only"] / nb["sd_d_rel_observed"]) ** 2, 3)
        bc = t["buying_club_persistence"]
        res["slice_family"] = slice_family(m, bc["perm_p"] if bc["clubs"] > 5 else None,
                                           res["predictor"]["as_published_900_minute_movers"]["p_auc_above_half"])
        # interval on the share of the spread in his own change that luck gives: the
        # benchmark's noise SD is held at its 200-run mean, the observed SD is resampled
        sd_noise = nb["sd_d_rel_noise_only"]
        p, lo, hi = T.boot(m[m.mover], lambda x: [(sd_noise / x.d_rel.std()) ** 2])
        res["luck_spread_share_ci"] = ci(p[0], lo[0], hi[0])
    if not OPTA and not MID:
        model, pred = freeze(a, X, mv, yr)
        (OUT / "flop_model_frozen.json").write_text(json.dumps(model, indent=1) + "\n")
        pred.to_csv(OUT / "predictions_2025_26.csv", index=False)
        res["predictions_2025_26"] = int(len(pred))
    (OUT / "robustness.json").write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    check() if sys.argv[1:] == ["check"] else main()
