"""More rival explanations for the headline, the cut-off checks, and the primary test family.

Round 2 of the review loop (LOOP.md) asked for these, on top of robustness.py:

1. The lost-place gap under the same checks as the share gap: matched on a decile of last
   season's share of minutes as well, without promoted or relegated clubs, without likely
   loans, and with the next-season floor at 450 and 1,350 minutes instead of 900.
2. Survival. A qualifying season with no Big-5 row the next season drops out of every
   test (sold abroad or down a division, relegated with his club, injured all season, or
   not matched). Those seasons are counted, split by whether Transfermarkt shows a
   transfer away from his club, and the lost-place gap is bounded by counting them all
   as lost.
3. Set pieces and the shots market. His own actions per 90 split into shots and
   shot-assists, and into open play and set pieces (Understat labels corners, free
   kicks and direct free kicks; Opta labels only direct free kicks), and his share of
   the team's open-play actions while he is on, measured match by match as in
   minutes.py.
4. The flop line at 15% and 35% as well as 25%.
5. Intervals that resample the buying club-season as well as the player, since
   team-mates at the same new club share its changes.
6. The position label. Transfermarkt gives one position per player (today's); the
   share gap is rerun on players whose line-up position was attacking in both seasons.
7. The name match: how many Understat shots belong to a player matched to Transfermarkt.
8. The luck benchmark as one difference, data minus luck, with the data's own
   resampling uncertainty included.
9. The primary family: the matched share, own-actions, output and flop-or-lost-place
   gaps on both sources, eight tests, with Holm-adjusted p-values.

    python analysis/rivals.py            (needs data/work/panel.parquet and SOURCE_DATA)
    SHOTS=opta python analysis/rivals.py
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from config import OUT, ROOT, SOURCE, WORK, SEED, N_BOOT, MIN_MINUTES, GROUP, OPTA, MID, SHOTS_FILE
import transfers as T
import robustness as R

ATTACK_POS = {"Centre-Forward", "Left Winger", "Right Winger", "Second Striker",
              "Attacking Midfield", "Attack"}


def ci(p, lo, hi):
    return R.ci(p, lo, hi)


def ols(x: pd.DataFrame, ys: list[str], cells=("share_dec", "out_dec", "age_band", "yr")) -> np.ndarray:
    X = R.design(x, cells)
    b, *_ = np.linalg.lstsq(X, x[ys].to_numpy(float), rcond=None)
    return b[1]


def boot_cluster(df, stat, cluster, n=N_BOOT, seed=SEED):
    """Point and 95% interval, resampling whole clusters (here buying club-seasons)."""
    point = np.asarray(stat(df), dtype=float)
    rng = np.random.default_rng(seed)
    idx = df.groupby(cluster).indices
    ids = list(idx)
    draws = np.array([stat(df.iloc[np.concatenate([idx[ids[i]] for i in rng.integers(0, len(ids), len(ids))])])
                      for _ in range(n)], dtype=float)
    lo, hi = np.nanpercentile(draws, [2.5, 97.5], axis=0)
    return point, lo, hi


def flags(x: pd.DataFrame) -> pd.DataFrame:
    """Promoted buyer, relegated seller and likely loan, as in robustness.move_checks."""
    p = pd.read_parquet(WORK / "panel.parquet", columns=["season", "club_id"])
    p["yr"] = p.season.str[:4].astype(int)
    clubs = p.groupby("yr").club_id.apply(set)
    x = x.copy()
    x["promoted_buyer"] = [c not in clubs.get(y, set()) for c, y in zip(x.club_id1, x.yr)]
    x["relegated_seller"] = [c not in clubs.get(y + 1, set()) for c, y in zip(x.club_id0, x.yr)]
    t = T.fees()
    t = t[["tm_player_id", "date"]].assign(frm=pd.read_csv(
        SOURCE / "transfermarkt" / "transfers.csv.gz", usecols=["from_club_id"]).from_club_id,
        to=t.club_id1)
    back = x[x.mover].merge(t, on="tm_player_id")
    back = back[(back.frm == back.club_id1) & (back.to == back.club_id0)
                & (back.date > pd.to_datetime(back.yr.astype(str) + "-07-01"))
                & (back.date <= pd.to_datetime((back.yr + 2).astype(str) + "-09-01"))]
    keys = set(zip(back.tm_player_id, back.yr))
    x["loan"] = np.array([(i, y) in keys for i, y in zip(x.tm_player_id, x.yr)]) & x.mover.to_numpy()
    return x


# ------------------------------------------------------------------ 1. lost place, checked

def late_minutes_share() -> pd.Series:
    """Share of his club's league minutes he played in the second half of its season, by
    (player, club, season): a club that has stopped picking him before selling him shows here."""
    iv = pd.read_parquet(WORK / "intervals.parquet", columns=["game_id", "player_id", "club_id", "season", "on", "off"])
    d = pd.read_csv(SOURCE / "transfermarkt" / "games.csv.gz", usecols=["game_id", "date"])
    iv = iv.merge(d, on="game_id")
    g = iv.drop_duplicates(["game_id", "club_id"])[["game_id", "club_id", "season", "date"]].copy()
    g["late"] = g.groupby(["club_id", "season"]).date.rank(method="first", pct=True) > 0.5
    n_late = g[g.late].groupby(["club_id", "season"]).size()
    iv = iv.merge(g[["game_id", "club_id", "late"]], on=["game_id", "club_id"])
    mins = iv[iv.late].assign(m=lambda x: x.off - x.on).groupby(["player_id", "club_id", "season"]).m.sum()
    den = n_late.reindex(mins.index.droplevel(0)).to_numpy() * 90
    return (mins / den).clip(upper=1)


def finishing() -> pd.Series:
    """Goals minus xG per shot in a season, by (season, team, player): clubs buy on goals."""
    s = pd.read_parquet(SOURCE / SHOTS_FILE, columns=["season", "team_shot", "player", "xg", "result", "situation"])
    s = s[(s.result != "OwnGoal") & (s.situation != "Penalty")]
    g = s.assign(goal=(s.result == "Goal").astype(float)).groupby(["season", "team_shot", "player"])
    return (g.goal.sum() - g.xg.sum()) / g.size()


def decile(x: pd.Series, ref: pd.Series) -> np.ndarray:
    cuts = np.nanquantile(ref, np.linspace(0, 1, 11)[1:-1])
    return np.searchsorted(cuts, x.fillna(np.nanmedian(ref)))


def starts_first_ten(a: pd.DataFrame) -> np.ndarray:
    """Share of his next club's first 10 league matches of the next season that he started."""
    lu = pd.read_csv(SOURCE / "transfermarkt" / "game_lineups.csv.gz",
                     usecols=["game_id", "player_id", "club_id", "type"])
    lu = lu[lu.type == "starting_lineup"]
    iv = pd.read_parquet(WORK / "intervals.parquet", columns=["game_id", "club_id", "season"]).drop_duplicates()
    d = pd.read_csv(SOURCE / "transfermarkt" / "games.csv.gz", usecols=["game_id", "date"])
    g = iv.merge(d, on="game_id").sort_values("date")
    g["k"] = g.groupby(["club_id", "season"]).cumcount()
    first = g[g.k < 10]
    st = lu.merge(first, on=["game_id", "club_id"]).groupby(["player_id", "club_id", "season"]).size()
    key = list(zip(a.tm_player_id, a.club_id1, (a.yr + 1).astype(str) + "-" + (a.yr + 2).astype(str)))
    return st.reindex(key).fillna(0).to_numpy() / 10

def starts_after_joining(a: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """The same, counting the 10 league matches from his first matchday squad at the new
    club (starting or on the bench), so matches before a late signing arrived do not count.
    Also returns how many of the club's league matches came before that first squad."""
    lu = pd.read_csv(SOURCE / "transfermarkt" / "game_lineups.csv.gz",
                     usecols=["game_id", "player_id", "club_id", "type"])
    iv = pd.read_parquet(WORK / "intervals.parquet", columns=["game_id", "club_id", "season"]).drop_duplicates()
    d = pd.read_csv(SOURCE / "transfermarkt" / "games.csv.gz", usecols=["game_id", "date"])
    g = iv.merge(d, on="game_id").sort_values(["date", "game_id"])
    g["k"] = g.groupby(["club_id", "season"]).cumcount()
    sq = lu.merge(g, on=["game_id", "club_id"])
    first = sq.groupby(["player_id", "club_id", "season"]).k.min()
    sq = sq.join(first.rename("k0"), on=["player_id", "club_id", "season"])
    st = sq[(sq.type == "starting_lineup") & (sq.k >= sq.k0) & (sq.k < sq.k0 + 10)]
    n = st.groupby(["player_id", "club_id", "season"]).size()
    key = list(zip(a.tm_player_id, a.club_id1, (a.yr + 1).astype(str) + "-" + (a.yr + 2).astype(str)))
    return n.reindex(key).fillna(0).to_numpy() / 10, first.reindex(key).to_numpy()


def lost_checks(a: pd.DataFrame, m: pd.DataFrame) -> dict:
    a = flags(R.add_cells(a, m))
    cuts = np.quantile(m.minutes_share0, np.linspace(0, 1, 11)[1:-1])
    a["min_dec"] = np.searchsorted(cuts, a.minutes_share0)
    a["badf"] = a.bad.astype(float)
    for f in (450, 900, 1350):
        a[f"lost{f}"] = (a.minutes1 < f).astype(float)
    base = ("share_dec", "out_dec", "age_band", "yr")
    out = {}

    def run(name, x, ys, cells=base):
        p, lo, hi, pv = R.boot_p(x, lambda z: ols(z, ys, cells))
        out[name] = {"n_movers": int(x.mover.sum()), "n_stayers": int((~x.mover).sum())} | {
            y: ci(p[i], lo[i], hi[i]) | {"p": round(float(pv[i]), 4)} for i, y in enumerate(ys)}

    pr = a.mover & (a.promoted_buyer | a.relegated_seller)
    run("matched", a, ["badf"])
    run("matched_with_minutes_share_decile", a, ["badf"], base + ("min_dec",))
    run("without_promoted_or_relegated", a[~pr], ["badf"])
    run("without_likely_loans", a[~a.loan], ["badf"])
    run("without_either", a[~pr & ~a.loan], ["badf"])
    run("minutes_only_floors", a, ["lost450", "lost900", "lost1350"])
    p, lo, hi, _ = R.boot_p(a, lambda z: [z[z.mover].lost900.mean(), z[~z.mover].lost900.mean()])
    out["minutes_only_rates_ci"] = {"movers": ci(p[0], lo[0], hi[0]), "stayers": ci(p[1], lo[1], hi[1])}
    p, lo, hi, _ = R.boot_p(a, lambda z: R.reweighted(z, ["badf"]))
    out["reweighted_cells"] = {"badf": ci(p[0], lo[0], hi[0])}
    # the selling side: was he already out of the side before the sale, and did he score
    # above his xG (clubs buy on goals, and finishing regresses)
    late = late_minutes_share()
    a["late_share"] = late.reindex(list(zip(a.tm_player_id, a.club_id0,
                                            a.yr.astype(str) + "-" + (a.yr + 1).astype(str)))).to_numpy()
    a["late_dec"] = decile(a.late_share, a.late_share)
    fin = finishing()
    a["fin0"] = fin.reindex(list(zip(a.yr.astype(str) + "-" + (a.yr + 1).astype(str), a.team0, a.player))).to_numpy()
    a["fin_dec"] = decile(a.fin0, a.fin0)
    run("matched_with_late_season_minutes_and_finishing", a, ["badf"], base + ("min_dec", "late_dec", "fin_dec"))
    out["late_season_minutes_share"] = {"movers": round(float(a.loc[a.mover, "late_share"].mean()), 4),
                                        "stayers": round(float(a.loc[~a.mover, "late_share"].mean()), 4)}
    # starts in the first 10 league matches at the next club: the input a match price uses
    a["starts10"] = starts_first_ten(a)
    run("starts_in_first_10_matches", a, ["starts10"])
    out["starts_in_first_10_rates"] = {"movers": round(float(a.loc[a.mover, "starts10"].mean()), 4),
                                       "stayers": round(float(a.loc[~a.mover, "starts10"].mean()), 4)}
    a["starts10j"], a["missed_before"] = starts_after_joining(a)
    run("starts_in_first_10_after_joining", a, ["starts10j"])
    out["starts_after_joining_rates"] = {"movers": round(float(a.loc[a.mover, "starts10j"].mean()), 4),
                                         "stayers": round(float(a.loc[~a.mover, "starts10j"].mean()), 4)}
    out["matches_before_first_squad"] = {"movers": round(float(a.loc[a.mover, "missed_before"].mean()), 2),
                                         "stayers": round(float(a.loc[~a.mover, "missed_before"].mean()), 2),
                                         "never_in_squad_movers": int(a.loc[a.mover, "missed_before"].isna().sum())}
    # by fee band and by whether the buying club made more shots the season before: is the
    # gap about squad fillers and step-ups to deeper squads?
    t = T.fees().merge(a.loc[a.mover, ["tm_player_id", "club_id1", "yr"]], on=["tm_player_id", "club_id1"])
    t = (t[(t.date >= pd.to_datetime(t.yr.astype(str) + "-07-01"))
           & (t.date <= pd.to_datetime((t.yr + 1).astype(str) + "-12-31"))]
         .sort_values("date").drop_duplicates(["tm_player_id", "club_id1", "yr"], keep="last"))
    a = a.merge(t[["tm_player_id", "club_id1", "yr", "transfer_fee"]].assign(has_row=True),
                on=["tm_player_id", "club_id1", "yr"], how="left")
    a["has_row"] = a.has_row.fillna(False).astype(bool)
    # loan returns: he had earlier gone from the buying club to the selling club, so the
    # "move" is a loan ending (the loan flag above only catches loans that end later)
    tr = pd.read_csv(SOURCE / "transfermarkt" / "transfers.csv.gz",
                     usecols=["player_id", "transfer_date", "from_club_id", "to_club_id"])
    tr["date"] = pd.to_datetime(tr.transfer_date, errors="coerce")
    e = a.loc[a.mover, ["tm_player_id", "club_id0", "club_id1", "yr"]].merge(
        tr, left_on=["tm_player_id", "club_id1", "club_id0"], right_on=["player_id", "from_club_id", "to_club_id"])
    e = e[(e.date >= pd.to_datetime((e.yr - 2).astype(str) + "-07-01"))
          & (e.date <= pd.to_datetime((e.yr + 1).astype(str) + "-06-30"))]
    lr = set(zip(e.tm_player_id, e.yr))
    a["loan_return"] = np.array([(i, y) in lr for i, y in zip(a.tm_player_id, a.yr)]) & a.mover.to_numpy()
    a["fee_band"] = np.where(~a.mover, "stayer", pd.cut(a.transfer_fee.fillna(-1), [-2, -0.5, 0, 10e6, 30e6, 1e12],
                             labels=["No fee on record", "Free or loan", "Under €10m", "€10m–30m", "Over €30m"]).astype(str))
    out["by_fee_band"] = {}
    paid = ["Under €10m", "€10m–30m", "Over €30m"]
    for b in ["Free or loan", "Under €10m", "€10m–30m", "Over €30m", "No fee on record", "Any fee paid"]:
        x = a[(a.fee_band.isin(paid) if b == "Any fee paid" else (a.fee_band == b)) | ~a.mover]
        p, lo, hi, pv = R.boot_p(x, lambda z: ols(z, ["badf"], base), n=N_BOOT // 2)
        out["by_fee_band"][b] = {"n_movers": int(x.mover.sum()), "badf": ci(p[0], lo[0], hi[0]) | {"p": round(float(pv[0]), 4)},
                                 "loan_returns": int((x.mover & x.loan_return).sum())}
    nf = a.mover & (a.fee_band == "No fee on record")
    out["no_fee_audit"] = {"movers": int(nf.sum()), "loan_returns": int((nf & a.loan_return).sum()),
                           "transfer_row_without_fee": int((nf & a.has_row & ~a.loan_return).sum()),
                           "no_transfer_row": int((nf & ~a.has_row & ~a.loan_return).sum()),
                           # a player with no Transfermarkt transfer history at all: the mirror
                           # holds transfers for players it still follows, so a missing history
                           # mostly means a later career outside its coverage, known only after
                           "no_transfer_history_at_all": int((nf & ~a.tm_player_id.isin(set(tr.player_id))).sum()),
                           "by_first_season": {str(k): int(v) for k, v in a[nf].groupby("yr").size().items()},
                           "movers_by_first_season": {str(k): int(v) for k, v in a[a.mover].groupby("yr").size().items()}}
    for nm, keep in (("without_loan_returns", ~a.loan_return),
                     ("no_fee_without_loan_returns", (nf & ~a.loan_return) | ~a.mover),
                     ("without_no_fee_moves", ~nf),
                     ("loan_returns_only", a.loan_return | ~a.mover)):
        x = a[keep]
        p, lo, hi, pv = R.boot_p(x, lambda z: ols(z, ["badf"], base), n=N_BOOT // 2)
        out["no_fee_audit"][nm] = {"n_movers": int(x.mover.sum()), "badf": ci(p[0], lo[0], hi[0]) | {"p": round(float(pv[0]), 4)}}
    # a second family, named after the results were seen: the five disjoint fee bands, the
    # two starts measures and the loan-return split, Holm-corrected together
    fam = {f"fee {b}": out["by_fee_band"][b]["badf"]["p"] for b in
           ["Free or loan", "Under €10m", "€10m–30m", "Over €30m", "No fee on record"]}
    fam["starts, first 10 club matches"] = out["starts_in_first_10_matches"]["starts10"]["p"]
    fam["starts, 10 matches from first squad"] = out["starts_in_first_10_after_joining"]["starts10j"]["p"]
    fam["no-fee moves without loan returns"] = out["no_fee_audit"]["no_fee_without_loan_returns"]["badf"]["p"]
    adj = R.holm({k: max(v, 1 / N_BOOT) for k, v in fam.items()})
    out["post_hoc_family"] = {k: {"p": fam[k], "p_holm": adj[k], "survives": bool(adj[k] < 0.05)} for k in fam}
    pp_ = pd.read_parquet(WORK / "panel.parquet", columns=["season", "club_id", "team_actions", "team_games"])
    pp_["yr"] = pp_.season.str[:4].astype(int)
    stg = (pp_.drop_duplicates(["club_id", "yr"]).set_index(["club_id", "yr"])
           .eval("team_actions / team_games"))
    s0 = stg.reindex(list(zip(a.club_id0, a.yr))).to_numpy()
    s1 = stg.reindex(list(zip(a.club_id1, a.yr))).to_numpy()
    a["step_up"] = s1 > s0
    out["by_buying_club_strength"] = {}
    for nm, keep in (("stronger_buyer", a.step_up), ("not_stronger_buyer", ~a.step_up & np.isfinite(s1))):
        x = a[(a.mover & keep) | ~a.mover]
        p, lo, hi, pv = R.boot_p(x, lambda z: ols(z, ["badf"], base), n=N_BOOT // 2)
        out["by_buying_club_strength"][nm] = {"n_movers": int(x.mover.sum()), "badf": ci(p[0], lo[0], hi[0])}
    # injuries: injured (30+ days out in the next season) and fit, separately
    import injuries as INJ
    a["injured"] = INJ.days_out(a, INJ.load_spells()) >= INJ.DAYS_OUT
    out["by_injury"] = {}
    for nm, keep in (("fit", ~a.injured), ("injured", a.injured)):
        x = a[keep]
        p, lo, hi, pv = R.boot_p(x, lambda z: ols(z, ["badf"], base), n=N_BOOT // 2)
        out["by_injury"][nm] = {"n_movers": int(x.mover.sum()), "n_stayers": int((~x.mover).sum()),
                                "badf": ci(p[0], lo[0], hi[0])}
    out["injured_share"] = {"movers": round(float(a.loc[a.mover, "injured"].mean()), 4),
                            "stayers": round(float(a.loc[~a.mover, "injured"].mean()), 4)}
    out["rates_minutes_only"] = {
        f"lost{f}_{w}": round(float(a.loc[a.mover == (w == "movers"), f"lost{f}"].mean()), 4)
        for f in (450, 900, 1350) for w in ("movers", "stayers")}
    p, lo, hi = boot_cluster(a, lambda z: ols(z, ["badf"]), ["club_id1", "yr"])
    out["matched_buying_club_season_clusters"] = {"badf": ci(p[0], lo[0], hi[0])}
    return out


# ------------------------------------------------------------------ 2. survival

def survival(a: pd.DataFrame, m: pd.DataFrame) -> dict:
    """Qualifying seasons with no Big-5 row next season, and the lost-place gap if every one
    of them counted as lost."""
    d = pd.read_parquet(WORK / "panel.parquet")
    d["yr"] = d.season.str[:4].astype(int)
    q = d[d[GROUP] & (d.minutes >= MIN_MINUTES) & (d.actions >= T.MIN_ACTIONS)
          & (d.mates_eff > 0) & (d.usage_on_pitch > 0)].copy()
    q = q[q.yr.isin(set(a.yr))]
    seen = set(zip(a.tm_player_id, a.yr))
    gone = q[[(i, y) not in seen for i, y in zip(q.tm_player_id, q.yr)]].copy()
    t = pd.read_csv(SOURCE / "transfermarkt" / "transfers.csv.gz",
                    usecols=["player_id", "transfer_date", "from_club_id", "to_club_id"])
    t["date"] = pd.to_datetime(t.transfer_date, errors="coerce")
    g = gone.merge(t, left_on=["tm_player_id", "club_id"], right_on=["player_id", "from_club_id"], how="left")
    g = g[g.date.isna() | ((g.date >= pd.to_datetime((g.yr + 1).astype(str) + "-05-15"))
                           & (g.date <= pd.to_datetime((g.yr + 2).astype(str) + "-02-01"))
                           & (g.to_club_id != g.club_id))]
    left = set(zip(g.dropna(subset=["date"]).tm_player_id, g.dropna(subset=["date"]).yr))
    gone["mover"] = [(i, y) in left for i, y in zip(gone.tm_player_id, gone.yr)]
    gone["out90"] = gone.value / gone.minutes * 90
    x = pd.concat([a[["tm_player_id", "yr", "mover", "bad", "usage_on_pitch0", "out900", "age0"]],
                   pd.DataFrame({"tm_player_id": gone.tm_player_id, "yr": gone.yr, "mover": gone.mover,
                                 "bad": True, "usage_on_pitch0": gone.usage_on_pitch,
                                 "out900": gone.out90, "age0": gone.age})], ignore_index=True)
    x = R.add_cells(x, m)
    x["badf"] = x.bad.astype(float)
    x["keptf"] = np.where(np.arange(len(x)) >= len(a), 0.0, x.badf)   # every dropout kept instead
    # players who did play Big-5 league minutes next season but at two or more clubs (the
    # 80% rule drops them): their Transfermarkt minutes say whether they kept a place
    op = pd.read_parquet(WORK / "onpitch.parquet")
    op["yr"] = op.season.str[:4].astype(int) - 1
    nx = op.groupby(["player_id", "yr"]).agg(mins=("minutes_on", "sum"), clubs=("club_id", lambda c: set(c)))
    k = list(zip(gone.tm_player_id, gone.yr))
    rec = nx.reindex(k)
    played = rec.mins.notna().to_numpy()
    rec_bad = np.where(played, rec.mins.fillna(0).to_numpy() < MIN_MINUTES, True)
    rec_mover = np.array([(len(cs) > 1 or c0 not in cs) if isinstance(cs, set) else mv
                          for c0, cs, mv in zip(gone.club_id, rec.clubs, gone.mover)], dtype=bool)
    x["recf"] = x.badf.copy()
    x["mover_rec"] = x.mover.copy()
    x.loc[len(a):, "recf"] = rec_bad.astype(float)
    x.loc[len(a):, "mover_rec"] = rec_mover
    xr = x.assign(mover=x.mover_rec)
    p, lo, hi, _ = R.boot_p(x, lambda z: [z[z.mover].badf.mean() - z[~z.mover].badf.mean(),
                                          ols(z, ["badf"])[0], ols(z, ["keptf"])[0]])
    pr_, lor, hir, _ = R.boot_p(xr, lambda z: [ols(z, ["recf"])[0]])
    n_q = len(a) + len(gone)
    return {"qualifying_seasons": int(n_q), "no_big5_row_next_season": int(len(gone)),
            "share_dropped": round(len(gone) / n_q, 4),
            "dropped_with_transfer_away": int(gone.mover.sum()),
            "dropped_without_transfer": int((~gone.mover).sum()),
            "bound_all_dropped_counted_lost": {"raw_gap": ci(p[0], lo[0], hi[0]),
                                               "matched_gap": ci(p[1], lo[1], hi[1])},
            "bound_all_dropped_counted_kept": {"matched_gap": ci(p[2], lo[2], hi[2])},
            "dropped_who_played_big5_next_season": int(played.sum()),
            "dropped_who_played_900_next_season": int((played & ~rec_bad).sum()),
            "split_season_players_recovered": {"matched_gap": ci(pr_[0], lor[0], hir[0]),
                                               "rest_counted": "lost"}}


# ------------------------------------------------------------------ 3. own actions, split

def own_split(m: pd.DataFrame) -> dict:
    s = pd.read_parquet(SOURCE / SHOTS_FILE,
                        columns=["season", "team_shot", "player", "player_assisted", "result", "situation"])
    s = s[(s.result != "OwnGoal") & (s.situation != "Penalty")]
    setp = s.situation.isin(["FromCorner", "SetPiece", "DirectFreekick"])
    rows = []
    for kind, sub, who in (("shots", s, "player"), ("assists", s.dropna(subset=["player_assisted"]), "player_assisted")):
        for play, mask in (("open", ~setp.loc[sub.index]), ("set", setp.loc[sub.index])):
            c = sub[mask].groupby(["season", "team_shot", who]).size().rename(f"{kind}_{play}")
            rows.append(c.rename_axis(["season", "team", "player"]))
    c = pd.concat(rows, axis=1).fillna(0)
    m = m.copy()
    for k in (0, 1):
        key = pd.MultiIndex.from_arrays([(m.yr + k).astype(str) + "-" + (m.yr + k + 1).astype(str),
                                         m[f"team{k}"], m.player])
        cc = c.reindex(key).fillna(0).to_numpy()
        for j, col in enumerate(c.columns):
            m[f"{col}{k}"] = cc[:, j]
        m[f"found{k}"] = key.isin(c.index)
    m = m[m.found0 & m.found1].copy()
    # the team's open-play actions while he was on, so his open-play share can be measured
    import minutes as MN
    shots = pd.read_parquet(SOURCE / SHOTS_FILE)
    shots = shots.assign(half=MN.halves(shots))
    shots = shots[~shots.situation.isin(["FromCorner", "SetPiece", "DirectFreekick"])]
    mx = pd.read_parquet(WORK / "crosswalk_matches.parquet")
    games = MN.tm_games()
    games = games[games.game_id.isin(mx.tm_game_id)]
    iv = pd.read_parquet(WORK / "intervals.parquet")
    op = MN.onpitch(iv, MN.team_actions(shots, mx, games)).set_index(["player_id", "club_id", "season"])
    for k in (0, 1):
        key = list(zip(m.tm_player_id, m[f"club_id{k}"],
                       (m.yr + k).astype(str) + "-" + (m.yr + k + 1).astype(str)))
        m[f"team_open_on{k}"] = op.team_actions_on.reindex(key).to_numpy()
    m = m[(m.team_open_on0 > 0) & (m.team_open_on1 > 0)].copy()

    def d(cols):
        n0 = sum(m[f"{c}0"] for c in cols) + 0.5
        n1 = sum(m[f"{c}1"] for c in cols) + 0.5
        return np.log(n1 / m.minutes1) - np.log(n0 / m.minutes0)
    m["d_own_shots"] = d(["shots_open", "shots_set"])
    m["d_own_assists"] = d(["assists_open", "assists_set"])
    m["d_own_open"] = d(["shots_open", "assists_open"])
    m["d_own_set"] = d(["shots_set", "assists_set"])
    m["d_team_open"] = np.log(m.team_open_on1 / m.minutes1) - np.log(m.team_open_on0 / m.minutes0)
    m["d_share_open"] = m.d_own_open - m.d_team_open
    cols = list(c.columns)
    tot = lambda k: sum(m[f"{col}{k}"] for col in cols)
    m["set_frac0"] = (m.shots_set0 + m.assists_set0) / tot(0)
    m["set_frac1"] = (m.shots_set1 + m.assists_set1) / tot(1)
    m["d_set_frac"] = m.set_frac1 - m.set_frac0
    m = R.add_cells(m, m)
    ys = ["d_own_shots", "d_own_assists", "d_own_open", "d_own_set", "d_set_frac",
          "d_share_open", "d_team_open"]
    p, lo, hi, pv = R.boot_p(m, lambda z: ols(z, ys))
    out = {"pairs": int(len(m)), "set_piece_labels": "Opta: direct free kicks only" if OPTA
           else "Understat: corners, set pieces and direct free kicks"}
    out |= {y: ci(p[i], lo[i], hi[i]) | {"p": round(float(pv[i]), 4)} for i, y in enumerate(ys)}
    out["set_frac_movers_last_season"] = round(float(m.loc[m.mover, "set_frac0"].mean()), 4)
    return out


# ------------------------------------------------------------------ Lee bounds

def lee_bounds(a: pd.DataFrame, m: pd.DataFrame) -> dict:
    """The share, own-actions and output gaps use only players who kept a 900-minute season,
    and movers keep it less often. Lee (2009) trimming bounds: trim the stayers' outcome by
    the excess share of stayers kept, from the top and then from the bottom, so both groups
    have the same share kept. Raw gaps, intervals resample whole players."""
    keep_m = 1 - a.loc[a.mover, "lost"].mean()
    keep_s = 1 - a.loc[~a.mover, "lost"].mean()
    q = (keep_s - keep_m) / keep_s
    m = m.assign(d_own=m.d_team + m.d_share)
    ys = ["d_share", "d_own", "d_out"]

    def stat(z):
        mv, st = z[z.mover], z[~z.mover]
        out = []
        for y in ys:
            v = np.sort(st[y].to_numpy())
            k = int(round(q * len(v)))
            out += [mv[y].mean() - v[k:].mean(), mv[y].mean() - v[:len(v) - k].mean()]
        return out
    p, lo, hi, _ = R.boot_p(m, stat)
    res = {"kept_movers": round(float(keep_m), 4), "kept_stayers": round(float(keep_s), 4),
           "trim_share": round(float(q), 4)}
    for i, y in enumerate(ys):
        res[y] = {"lower": ci(p[2 * i], lo[2 * i], hi[2 * i]), "upper": ci(p[2 * i + 1], lo[2 * i + 1], hi[2 * i + 1])}
    return res


def predictor_baseline(a: pd.DataFrame) -> dict:
    """The flop predictor against a one-input baseline: last season's output per 90 alone.
    A flop is a fall from last season, so a big last season predicts one mechanically."""
    mv = a[a.mover & ~a.lost].reset_index(drop=True)
    X = R.features(mv)
    y, yr = mv.flop.to_numpy(float), mv.yr.to_numpy()
    full, _ = R.fit_score(X, y, yr)
    base_, _ = R.fit_score(X[["log out per 90 last season"]], y, yr)
    return {"full": {k: full[k] for k in ("auc", "auc_lo", "auc_hi", "test_moves")},
            "output_only": {k: base_[k] for k in ("auc", "auc_lo", "auc_hi", "test_moves")}}


def full_time_check() -> dict:
    """For a player on the pitch for every league minute, his team's actions while he was on
    must equal all its actions: the test that would have caught the stoppage-time bug."""
    d = pd.read_parquet(WORK / "panel.parquet", columns=["minutes", "team_games", "team_actions_on", "team_actions"])
    full = d[(d.minutes >= d.team_games * 90 - 0.5) & (d.team_actions > 0)]
    r = full.team_actions_on / full.team_actions
    return {"players": int(len(full)), "median_ratio": round(float(r.median()), 4),
            "mean_ratio": round(float(r.mean()), 4)}


# ------------------------------------------------------------------ 4-6. cut-offs, clusters, position

def cutoffs_clusters_position(m: pd.DataFrame) -> dict:
    m = R.add_cells(m, m)
    for f in (15, 25, 35):
        m[f"flop{f}"] = (m.d_out < np.log(1 - f / 100)).astype(float)
    m["d_own"] = m.d_team + m.d_share
    out = {}
    p, lo, hi, pv = R.boot_p(m, lambda z: ols(z, ["flop15", "flop25", "flop35"]))
    out["flop_line"] = {k: ci(p[i], lo[i], hi[i]) | {"p": round(float(pv[i]), 4)}
                        for i, k in enumerate(["flop15", "flop25", "flop35"])}
    out["flop_rates"] = {f"flop{f}_{w}": round(float(m.loc[m.mover == (w == "movers"), f"flop{f}"].mean()), 4)
                         for f in (15, 25, 35) for w in ("movers", "stayers")}
    ys = ["d_share", "d_own", "d_out"]
    p, lo, hi = boot_cluster(m, lambda z: ols(z, ys), ["club_id1", "yr"])
    out["matched_buying_club_season_clusters"] = {y: ci(p[i], lo[i], hi[i]) for i, y in enumerate(ys)}
    # the position on the team sheet, season by season
    lu = pd.read_csv(SOURCE / "transfermarkt" / "game_lineups.csv.gz",
                     usecols=["date", "player_id", "club_id", "type", "position"])
    lu = lu[lu.type == "starting_lineup"].copy()
    dt = pd.to_datetime(lu.date)
    lu["yr"] = np.where(dt.dt.month >= 7, dt.dt.year, dt.dt.year - 1)
    lu["att"] = lu.position.isin(ATTACK_POS)
    pos = lu.groupby(["player_id", "club_id", "yr"]).att.mean()
    a0 = pos.reindex(list(zip(m.tm_player_id, m.club_id0, m.yr))).to_numpy()
    a1 = pos.reindex(list(zip(m.tm_player_id, m.club_id1, m.yr + 1))).to_numpy()
    keep = (a0 >= 0.5) & (a1 >= 0.5)
    x = m[keep]
    p, lo, hi, pv = R.boot_p(x, lambda z: ols(z, ys))
    out["attacking_line_up_position_both_seasons"] = {
        "pairs": int(len(x)), "n_movers": int(x.mover.sum()),
        "share_of_pairs_kept": round(float(keep.mean()), 4)} | {
        y: ci(p[i], lo[i], hi[i]) | {"p": round(float(pv[i]), 4)} for i, y in enumerate(ys)}
    return out


# ------------------------------------------------------------------ 7. name match

def name_match() -> dict:
    s = pd.read_parquet(SOURCE / SHOTS_FILE, columns=["league", "season", "player_id", "situation"])
    s = s[~s.league.str.startswith("RUS") & (s.situation != "Penalty")].dropna(subset=["player_id"])
    px = pd.read_parquet(WORK / "crosswalk_players.parquet")
    s["matched"] = pd.to_numeric(s.player_id).isin(set(pd.to_numeric(px.us_player_id.dropna())))
    by = s.groupby(["league", "season"]).matched.mean()
    pl = s.groupby("player_id").matched.first()
    return {"shots_by_matched_players": round(float(s.matched.mean()), 4),
            "worst_league_season": {"which": " ".join(by.idxmin()), "share": round(float(by.min()), 4)},
            "players_matched": round(float(pl.mean()), 4), "players": int(len(pl))}


# ------------------------------------------------------------------ 8. luck as one difference

def luck_difference(m: pd.DataFrame) -> dict:
    out = {}
    for who, g in (("movers", m[m.mover]), ("stayers", m[~m.mover])):
        draws = pd.read_csv(OUT / f"noise_benchmark_draws_{who}.csv").flop_rate.to_numpy()
        rng = np.random.default_rng(SEED)
        idx = g.groupby("tm_player_id").indices
        ids = np.array(list(idx))
        obs = np.array([g.iloc[np.concatenate([idx[i] for i in rng.choice(ids, len(ids))])].flop.mean()
                        for _ in range(N_BOOT)])
        diff = obs - rng.choice(draws, N_BOOT)
        out[who] = ci(g.flop.mean() - np.median(draws), *np.percentile(diff, [2.5, 97.5]))
    return out


def part_among_flops(m: pd.DataFrame) -> dict:
    """The player's own part of the average flop's fall, with an interval."""
    j = list(T.PARTS).index("d_rel")
    out = {}
    for who, g in (("movers", m[m.mover]), ("stayers", m[~m.mover])):
        p, lo, hi = T.boot(g, lambda x: [T.tail_shares(x)[j]])
        out[who] = ci(p[0], lo[0], hi[0])
    return out


# ------------------------------------------------------------------ 9. primary family

def primary_family(sources=(("Understat", OUT / "robustness.json"),)) -> dict:
    """Four tests on one source. Opta is run as its own family, a sensitivity check: it shares
    Transfermarkt's minutes, the sample rules and most seasons with Understat, so counting
    both sources in one family would double-count the lost-place test."""
    ps, est = {}, {}
    for src, path in sources:
        r = json.loads(path.read_text())
        for k, lab in (("d_share", "share of shots and shot-assists"), ("d_own", "own actions per 90"),
                       ("d_out", "output per 90")):
            x = r["rtm"]["regression"][k]
            ps[f"{src}: {lab}"], est[f"{src}: {lab}"] = x["p"], x
        x = r["lost_place"]["regression"]["bad_gap"]
        ps[f"{src}: flop or lost place"], est[f"{src}: flop or lost place"] = x["p"], x
    adj = R.holm(ps)
    return {k: {"estimate": {q: est[k][q] for q in ("point", "lo", "hi")}, "p": ps[k],
                "p_at_floor": bool(ps[k] <= 1 / N_BOOT), "p_holm": adj[k], "survives": bool(adj[k] < 0.05)}
            for k in sorted(ps, key=ps.get)}


# ------------------------------------------------------------------ self-check

def check():
    rng = np.random.default_rng(2)
    n = 3000
    x = pd.DataFrame({"g": rng.integers(0, 300, n)})
    x["y"] = rng.normal(0, 1, n) + rng.normal(0, 1, 300)[x.g]   # a shared shock per cluster
    _, lo, hi = boot_cluster(x, lambda z: [z.y.mean()], "g", n=400)
    se_naive = x.y.std() / np.sqrt(n)
    assert (hi[0] - lo[0]) / 3.92 > 2 * se_naive, (lo, hi, se_naive)   # clusters widen it
    assert R.holm({"a": 0.0005, "b": 0.2}) == {"a": 0.001, "b": 0.2}
    print("rivals self-check ok")


def main():
    m = T.season_pairs()
    a = R.lost_place(R.all_moves(), m)
    res = {}
    for name, fn in (("lost_place", lambda: lost_checks(a, m)), ("survival", lambda: survival(a, m)),
                     ("own_split", lambda: own_split(m)),
                     ("cutoffs_clusters_position", lambda: cutoffs_clusters_position(m))):
        print(name, "...", flush=True)
        res[name] = fn()
    res["lee_bounds"] = lee_bounds(a, m)
    if not MID:
        res["luck_minus_benchmark"] = luck_difference(m)
        res["player_part_among_flops"] = part_among_flops(m)
    if not OPTA and not MID:
        res["name_match"] = name_match()
        res["primary_family"] = primary_family()
        res["opta_family"] = primary_family((("Opta", OUT / "opta" / "robustness.json"),))
        rr = json.loads((OUT / "robustness.json").read_text())
        # the smallest gap with 80% power at the 5% level: 2.8 standard errors
        res["min_detectable_points"] = {k: round(2.8 * (x["hi"] - x["lo"]) / 3.92 * 100, 1) for k, x in (
            ("flop", rr["rtm"]["regression"]["flopf"]), ("flop_or_lost", rr["lost_place"]["regression"]["bad_gap"]))}
        res["full_time_check"] = full_time_check()
        res["predictor_baseline"] = predictor_baseline(a)
    (OUT / "rivals.json").write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    check() if sys.argv[1:] == ["check"] else main()
