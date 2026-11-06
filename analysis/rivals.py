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
    p, lo, hi, _ = R.boot_p(x, lambda z: [z[z.mover].badf.mean() - z[~z.mover].badf.mean(),
                                          ols(z, ["badf"])[0]])
    n_q = len(a) + len(gone)
    return {"qualifying_seasons": int(n_q), "no_big5_row_next_season": int(len(gone)),
            "share_dropped": round(len(gone) / n_q, 4),
            "dropped_with_transfer_away": int(gone.mover.sum()),
            "dropped_without_transfer": int((~gone.mover).sum()),
            "bound_all_dropped_counted_lost": {"raw_gap": ci(p[0], lo[0], hi[0]),
                                               "matched_gap": ci(p[1], lo[1], hi[1])}}


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

def primary_family() -> dict:
    ps, est = {}, {}
    for src, path in (("Understat", OUT / "robustness.json"), ("Opta", OUT / "opta" / "robustness.json")):
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
    if not MID:
        res["luck_minus_benchmark"] = luck_difference(m)
        res["player_part_among_flops"] = part_among_flops(m)
    if not OPTA and not MID:
        res["name_match"] = name_match()
        res["primary_family"] = primary_family()
    (OUT / "rivals.json").write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    check() if sys.argv[1:] == ["check"] else main()
