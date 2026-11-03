"""Check the repo's data and its chemistry result against StatsBomb's 2015-16 event data.

StatsBomb's free release covers 2015-16 in full for the Premier League, La Liga, Serie A
and Ligue 1 (1,517 matches; its Bundesliga file holds only Leverkusen's 34). It records
every pass with its receiver and every substitution to the second. Three checks:

  1. minutes    Transfermarkt substitution minutes against StatsBomb's, match by match
  2. links      do pairs that set up more shots than expected (Understat) also pass to
                each other more than expected (StatsBomb)? If both sources see the same
                pairs, the shot-assist measure is picking up something real
  3. passes     the chemistry growth test again, on passes rather than shot assists:
                hundreds of times more events, so a far sharper test. New pairs in their
                first season against pairs who already had a season together

Writes data/sb_check.json (aggregates only).

    python analysis/sb_check.py   (after statsbomb.py, minutes.py and chemistry.py)
"""
from __future__ import annotations

import difflib
import json

import numpy as np
import pandas as pd

from config import OUT, SOURCE, WORK, SEED, N_BOOT
from crosswalk import norm_player, team_map, tm_games
from chemistry import (expected, boot_pairs, ratio, r4, n_pairs, assisted_shots, pair_games,
                       link_table)
from statsbomb import COMPS, _get

SEASON_STR = "2015-2016"
MIN_HALF = 450


def sb_lineup_names(match_ids) -> pd.DataFrame:
    rows = []
    for mid in match_ids:
        for team in _get(f"lineups/{mid}.json"):
            for p in team["lineup"]:
                rows.append({"match_id": mid, "sb_team": team["team_name"],
                             "sb_pid": p["player_id"],
                             "name": p["player_nickname"] or p["player_name"],
                             "full": p["player_name"]})
    return pd.DataFrame(rows)


def map_games(sbg: pd.DataFrame) -> pd.DataFrame:
    """StatsBomb match -> Transfermarkt game, by league, date and club names."""
    g = tm_games()
    g = g[g.season == SEASON_STR]
    out = []
    for lg, s in sbg.groupby("league"):
        t = g[g.league == lg]
        names = team_map(pd.concat([s.home, s.away]).unique(),
                         pd.concat([t.home_club_name, t.away_club_name]).unique())
        s = s.assign(h=s.home.map(lambda n: names.get(n, (None,))[0]),
                     a=s.away.map(lambda n: names.get(n, (None,))[0]))
        m = s.merge(t, left_on=["h", "a"], right_on=["home_club_name", "away_club_name"])
        out.append(m[["match_id", "game_id", "home", "away", "home_club_id", "away_club_id"]])
    return pd.concat(out)


def map_players(gm: pd.DataFrame, names: pd.DataFrame) -> pd.DataFrame:
    """StatsBomb player -> Transfermarkt id, matching names within each match and club."""
    iv = pd.read_parquet(WORK / "intervals.parquet")
    tmn = pd.read_csv(SOURCE / "transfermarkt" / "players.csv.gz",
                      usecols=["player_id", "name"]).set_index("player_id").name
    iv = iv[iv.game_id.isin(gm.game_id)].assign(tm_name=lambda x: x.player_id.map(tmn))
    side = pd.concat([gm.assign(sb_team=gm.home, club_id=gm.home_club_id),
                      gm.assign(sb_team=gm.away, club_id=gm.away_club_id)])
    names = names.merge(side[["match_id", "sb_team", "game_id", "club_id"]],
                        on=["match_id", "sb_team"])
    by = {k: v for k, v in iv.groupby(["game_id", "club_id"])}
    votes = []
    for r in names.itertuples():
        c = by.get((r.game_id, r.club_id))
        if c is None:
            continue
        cand = {norm_player(n): pid for n, pid in zip(c.tm_name.fillna(""), c.player_id)}
        a, b = norm_player(r.name), norm_player(r.full)
        hit = cand.get(a) or cand.get(b)
        if hit is None:
            last = {k.split()[-1]: v for k, v in cand.items() if k}
            if len([k for k in cand if k and k.split()[-1] == a.split()[-1]]) == 1:
                hit = last.get(a.split()[-1])
        if hit is None:
            m = difflib.get_close_matches(a, list(cand), n=1, cutoff=0.7)
            hit = cand[m[0]] if m else None
        if hit is not None:
            votes.append((r.sb_pid, hit))
    v = pd.DataFrame(votes, columns=["sb_pid", "tm_pid"]).value_counts().rename("n").reset_index()
    return v.sort_values("n", ascending=False).drop_duplicates("sb_pid")


def check_minutes(gm, pmap) -> dict:
    sbm = pd.read_parquet(WORK / "sb_minutes.parquet").merge(
        pmap, left_on="player_id", right_on="sb_pid").merge(gm[["match_id", "game_id"]], on="match_id")
    iv = pd.read_parquet(WORK / "intervals.parquet")
    m = sbm.merge(iv, left_on=["game_id", "tm_pid"], right_on=["game_id", "player_id"],
                  suffixes=("_sb", "_tm"))
    subs_on = m[m.on_sb > 0]
    sb_mins = m.off_sb.clip(upper=90) - m.on_sb.clip(upper=90)
    tm_mins = m.off_tm.clip(upper=90) - m.on_tm.clip(upper=90)
    return {"player_matches": int(len(m)),
            "minutes_corr": r4(np.corrcoef(sb_mins, tm_mins)[0, 1]),
            "median_abs_diff_minutes": r4((sb_mins - tm_mins).abs().median()),
            "within_2_minutes": r4(((sb_mins - tm_mins).abs() <= 2).mean()),
            "sub_on_minute_within_1": r4(((subs_on.on_sb - subs_on.on_tm).abs() <= 1.5).mean())}


def pass_links(gm, pmap) -> pd.DataFrame:
    """Completed open-play passes A -> B per club and half of the season, with minutes
    together from StatsBomb's own substitutions."""
    pas = pd.read_parquet(WORK / "sb_passes.parquet")
    mins = pd.read_parquet(WORK / "sb_minutes.parquet")
    ids = pmap.set_index("sb_pid").tm_pid
    games = pd.read_parquet(WORK / "sb_games.parquet")
    games = games[games.match_id.isin(gm.match_id)]
    rank = games.date.rank(method="dense", pct=True)
    # half of the season by date within each league
    games["part"] = games.groupby("league").date.rank(method="dense", pct=True).gt(0.5).astype(int)
    del rank
    mins = mins.merge(games[["match_id", "part"]], on="match_id")
    x = mins[["match_id", "team", "part", "player_id", "on", "off"]]
    p = x.merge(x[["match_id", "team", "player_id", "on", "off"]], on=["match_id", "team"],
                suffixes=("_a", "_b"))
    p = p[p.player_id_a != p.player_id_b]
    p["m"] = (np.minimum(p.off_a, p.off_b) - np.maximum(p.on_a, p.on_b)).clip(lower=0)
    m = p.groupby(["team", "part", "player_id_a", "player_id_b"]).m.sum().rename("m")
    pas = pas.merge(games[["match_id", "part"]], on="match_id")
    n = pas.groupby(["team", "part", "passer", "receiver"]).size().rename("n")
    n.index = n.index.set_names(["team", "part", "player_id_a", "player_id_b"])
    d = m.to_frame().join(n).fillna({"n": 0}).reset_index()
    d = d[d.m > 0].rename(columns={"player_id_a": "a_sb", "player_id_b": "b_sb"})
    d["e"] = expected(d.rename(columns={"a_sb": "a", "b_sb": "b"}), ["team", "part"])
    d["a"], d["b"] = d.a_sb.map(ids), d.b_sb.map(ids)
    return d.dropna(subset=["a", "b"]).astype({"a": int, "b": int})


def pass_growth(d: pd.DataFrame) -> dict:
    """First half against second half of 2015-16, new pairs against established pairs."""
    pm = pd.read_parquet(WORK / "pair_minutes.parquet")
    prior = pm[pm.season == "2014-2015"]
    prior = pd.concat([prior.rename(columns={"player_id_a": "a", "player_id_b": "b"}),
                       prior.rename(columns={"player_id_a": "b", "player_id_b": "a"})])
    prior = prior.groupby(["a", "b"]).minutes_together.sum()
    d = d.join(prior.rename("prior"), on=["a", "b"]).fillna({"prior": 0})
    g = d.groupby(["team", "a", "b"])
    d = d[(g.part.transform("nunique") == 2) & (g.m.transform("min") >= MIN_HALF)]
    d["group"] = np.where(d.prior == 0, "new", np.where(d.prior >= 900, "established", "other"))
    d = d[d.group != "other"]

    def growth(x):
        return ratio(x[x.part == 1]) / ratio(x[x.part == 0]) - 1

    def stat(x):
        return growth(x[x.group == "new"]) - growth(x[x.group == "established"])
    out = {}
    for grp in ("new", "established"):
        x = d[d.group == grp]
        p, lo, hi = boot_pairs(x, growth, n=N_BOOT // 2)
        out[grp] = {"pairs": n_pairs(x), "passes": int(x.n.sum()),
                    "growth": r4(p), "lo": r4(lo), "hi": r4(hi)}
    p, lo, hi = boot_pairs(d, stat, n=N_BOOT // 2)
    out["new_minus_established"] = {"gap": r4(p), "lo": r4(lo), "hi": r4(hi)}
    return out


def convergent(d: pd.DataFrame) -> dict:
    """Pair residuals from passes (StatsBomb) against pair residuals from shot assists
    (Understat), same pairs, same season."""
    sh = assisted_shots()
    pg = pair_games()
    sh, pg = sh[sh.season == SEASON_STR], pg[pg.season == SEASON_STR]
    u = link_table(sh, pg, ["club_id", "season"])
    sb = d.groupby(["a", "b"])[["n", "e", "m"]].sum()
    us = u.groupby(["a", "b"])[["n", "e"]].sum()
    j = sb.merge(us, left_index=True, right_index=True, suffixes=("_pass", "_shot"))
    j = j[(j.m >= 900) & (j.e_shot >= 1)]
    zp = np.log((j.n_pass + 1) / (j.e_pass + 1))
    zs = (j.n_shot - j.e_shot) / np.sqrt(j.e_shot)
    rng = np.random.default_rng(SEED)
    null = [np.corrcoef(zp, rng.permutation(zs.to_numpy()))[0, 1] for _ in range(1000)]
    # top fifth by pass residual: do they also set up more shots than expected?
    top = zp >= zp.quantile(0.8)
    return {"pairs": int(len(j)), "unordered_pairs": n_pairs(j.reset_index()), "corr": r4(np.corrcoef(zp, zs)[0, 1]),
            "null_95": r4(np.percentile(np.abs(null), 95)),
            "shot_ratio_top_fifth_pass_links": r4(j.n_shot[top].sum() / j.e_shot[top].sum()),
            "shot_ratio_rest": r4(j.n_shot[~top].sum() / j.e_shot[~top].sum())}


def main():
    sbg = pd.read_parquet(WORK / "sb_games.parquet")
    sbg = sbg[sbg.league != COMPS[9]]  # Bundesliga file is Leverkusen only
    gm = map_games(sbg)
    names = sb_lineup_names(gm.match_id)
    pmap = map_players(gm, names)
    res = {"matches": int(len(gm)), "of_statsbomb_matches": int(len(sbg)),
           "players_mapped": int(len(pmap)),
           "players_in_lineups": int(names.sb_pid.nunique())}
    res["minutes"] = check_minutes(gm, pmap)
    d = pass_links(gm, pmap)
    res["pass_growth"] = pass_growth(d)
    res["links_agree"] = convergent(d)
    (OUT / "sb_check.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
