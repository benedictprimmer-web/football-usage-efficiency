"""Do team-mates click? Pair chemistry from shot assists and minutes on the pitch together.

For every ordered pair of team-mates (A sets up, B shoots) in a club-season:

    observed  N_ab = open-play shots B took from A's passes
    exposure  M_ab = minutes A and B were on the pitch together (minutes.py, from
                     Transfermarkt line-ups and substitutions)
    expected  E_ab = M_ab x a_a x b_b, where a_a is how much A sets up and b_b how much B
                     finishes from set-ups, fitted so that each player's expected totals
                     match his actual totals (a Poisson model with a passer effect and a
                     receiver effect, fitted by iterative proportional fitting)

Chemistry is N/E summed over pairs: above 1 means the pair link up more than their
separate habits and their time together predict.

Tests:
  1. growth      the same pair in the first and second half of their first season
                 together, and in consecutive seasons at the same club
  2. persistence does a pair's chemistry in one season predict the next, beyond noise?
  3. dose        chemistry by minutes already played together
  4. reunions    old team-mates who meet again at a new club, against new pairs

Writes data/chemistry.json and data/chemistry_*.csv (aggregates only).

    python analysis/chemistry.py   (after minutes.py and build_panel.py)
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from config import OUT, SOURCE, WORK, SEED, N_BOOT, SHOTS_FILE

MIN_TOGETHER = 450  # minutes together in the unit being compared (five full matches)


# ------------------------------------------------------------------ data

def assisted_shots() -> pd.DataFrame:
    """Open-play assisted shots with Transfermarkt ids for both players."""
    s = pd.read_parquet(SOURCE / SHOTS_FILE)
    s = s[(s.league != "RUS-Premier League") & (s.situation == "OpenPlay")
          & s.player_assisted.notna() & (s.result != "OwnGoal")]
    s = s[s.player != s.player_assisted]
    px = pd.read_parquet(WORK / "crosswalk_players.parquet")
    shots_all = pd.read_parquet(SOURCE / SHOTS_FILE,
                                columns=["league", "season", "team_shot", "player", "player_id"])
    # Understat gives the assister by name only; name -> id within the team-season
    nm = (shots_all.dropna(subset=["player_id"])
          .groupby(["season", "team_shot", "player"]).player_id
          .agg(lambda x: x.value_counts().idxmax()).rename("us_pid").reset_index())
    s = s.merge(nm.rename(columns={"player": "player_assisted", "us_pid": "pid_a"}),
                on=["season", "team_shot", "player_assisted"], how="left")
    s = s.merge(px[["us_player_id", "tm_player_id"]].rename(
        columns={"us_player_id": "pid_a", "tm_player_id": "a"}), on="pid_a", how="left")
    s = s.merge(px[["us_player_id", "tm_player_id"]].rename(
        columns={"us_player_id": "player_id", "tm_player_id": "b"}), on="player_id", how="left")
    mx = pd.read_parquet(WORK / "crosswalk_matches.parquet")
    s = s.merge(mx[["us_game_id", "tm_game_id"]], left_on="game_id", right_on="us_game_id")
    g = pd.read_csv(SOURCE / "transfermarkt" / "games.csv.gz",
                    usecols=["game_id", "home_club_id", "away_club_id"])
    s = s.merge(g, left_on="tm_game_id", right_on="game_id", suffixes=("", "_tm"))
    s["club_id"] = np.where(s.team_shot == s.home_team, s.home_club_id, s.away_club_id)
    print(f"assisted open-play shots: {len(s):,}; both players matched: "
          f"{s[['a', 'b']].notna().all(axis=1).mean():.1%}")
    s = s.dropna(subset=["a", "b"])
    return s[["tm_game_id", "club_id", "season", "date", "a", "b", "xg"]].astype(
        {"a": int, "b": int}).rename(columns={"tm_game_id": "game_id"})


def pair_games() -> pd.DataFrame:
    """Minutes together for every ordered pair of team-mates in every league match."""
    iv = pd.read_parquet(WORK / "intervals.parquet")
    dates = pd.read_csv(SOURCE / "transfermarkt" / "games.csv.gz", usecols=["game_id", "date"])
    iv = iv.merge(dates, on="game_id")
    x = iv[["game_id", "club_id", "season", "date", "player_id", "on", "off"]]
    p = x.merge(x[["game_id", "club_id", "player_id", "on", "off"]], on=["game_id", "club_id"],
                suffixes=("_a", "_b"))
    p = p[p.player_id_a != p.player_id_b]
    p["m"] = (np.minimum(p.off_a, p.off_b) - np.maximum(p.on_a, p.on_b)).clip(lower=0)
    p = p[p.m > 0]
    # first or second half of the club's season, by date
    rank = p.groupby(["club_id", "season"]).date.rank(method="dense", pct=True)
    p["part"] = (rank > 0.5).astype(int)
    return p.rename(columns={"player_id_a": "a", "player_id_b": "b"})[
        ["game_id", "club_id", "season", "date", "part", "a", "b", "m"]]


# ------------------------------------------------------------------ the model

def expected(d: pd.DataFrame, unit: list[str], iters: int = 30) -> pd.Series:
    """Fit E_ab = M_ab * alpha_a * beta_b within each unit (e.g. club-season) so that every
    passer's and every receiver's expected total equals his observed total."""
    d = d.copy()
    d["alpha"], d["beta"] = 1.0, 1.0
    ka, kb = unit + ["a"], unit + ["b"]
    na = d.groupby(ka).n.transform("sum")
    nb = d.groupby(kb).n.transform("sum")
    for _ in range(iters):
        e = d.m * d.alpha * d.beta
        d["alpha"] *= (na / e.groupby([d[k] for k in ka]).transform("sum")).fillna(0)
        e = d.m * d.alpha * d.beta
        d["beta"] *= (nb / e.groupby([d[k] for k in kb]).transform("sum")).fillna(0)
    return (d.m * d.alpha * d.beta).fillna(0)


def link_table(sh: pd.DataFrame, pg: pd.DataFrame, unit: list[str]) -> pd.DataFrame:
    """Observed and expected set-ups per ordered pair within each unit."""
    m = pg.groupby(unit + ["a", "b"]).m.sum().rename("m")
    n = sh.groupby(unit + ["a", "b"]).agg(n=("xg", "size"), xg=("xg", "sum"))
    d = m.to_frame().join(n).fillna({"n": 0, "xg": 0}).reset_index()
    d["e"] = expected(d, unit)
    return d


def shrink(n: pd.Series, e: pd.Series) -> tuple[pd.Series, float]:
    """Gamma-Poisson empirical Bayes: each pair's true ratio theta varies around 1 with
    variance tau2, and N ~ Poisson(E * theta). Moment estimate of tau2 from
    E[(N - E)^2 - N] = tau2 * E^2; the posterior mean pulls small samples towards 1."""
    tau2 = max(float(((n - e) ** 2 - n).sum() / (e ** 2).sum()), 1e-6)
    return (n + 1 / tau2) / (e + 1 / tau2), tau2


def ratio(d: pd.DataFrame) -> float:
    return d.n.sum() / d.e.sum()


def boot_pairs(d: pd.DataFrame, stat, n=N_BOOT, seed=SEED):
    """Point and 95% interval, resampling whole pairs (unordered)."""
    key = np.minimum(d.a, d.b).astype(str) + "-" + np.maximum(d.a, d.b).astype(str)
    idx = d.groupby(key.to_numpy()).indices
    ids = np.array(list(idx))
    rng = np.random.default_rng(seed)
    draws = [stat(d.iloc[np.concatenate([idx[i] for i in rng.choice(ids, len(ids))])])
             for _ in range(n)]
    lo, hi = np.nanpercentile(np.array(draws, dtype=float), [2.5, 97.5], axis=0)
    return stat(d), lo, hi


def n_pairs(d: pd.DataFrame) -> int:
    """Unordered pairs: A setting up B and B setting up A count once."""
    return int(pd.MultiIndex.from_arrays([np.minimum(d.a, d.b), np.maximum(d.a, d.b)]).nunique())


def r4(x):
    return round(float(x), 4)


# ------------------------------------------------------------------ tests

def growth_within_season(sh, pg) -> dict:
    """New pairs only (never on the pitch together before this club-season): chemistry
    in the first half of the season against the second half. Same two players, same
    club, same season, so the only thing that has changed is time together."""
    first = pg.groupby(["a", "b"]).season.min().rename("first_season")
    pg = pg.join(first, on=["a", "b"])
    sh = sh.join(first, on=["a", "b"])
    pg, sh = pg[pg.season == pg.first_season], sh[sh.season == sh.first_season]
    # the expected rate is fitted per club-season-half, so a team that improves in
    # spring raises E for every pair and cancels
    sh = sh.merge(pg[["game_id", "a", "b", "part"]].drop_duplicates(), on=["game_id", "a", "b"])
    d = link_table(sh, pg, ["club_id", "season", "part"])
    # 2014-15 is the first season in the data, so a pair there may not be new
    d = d[d.season != "2014-2015"]
    g = d.groupby(["club_id", "season", "a", "b"])
    d = d[(g.part.transform("nunique") == 2) & (g.m.transform("min") >= MIN_TOGETHER)]

    def stat(x):
        return ratio(x[x.part == 1]) / ratio(x[x.part == 0]) - 1
    p, lo, hi = boot_pairs(d, stat)
    return {"pairs": n_pairs(d), "growth": r4(p), "lo": r4(lo), "hi": r4(hi),
            "ratio_first_half": r4(ratio(d[d.part == 0])), "ratio_second_half": r4(ratio(d[d.part == 1]))}


def season_links(sh, pg) -> pd.DataFrame:
    d = link_table(sh, pg, ["club_id", "season"])
    d["yr"] = d.season.str[:4].astype(int)
    # minutes together before this season, at this club and anywhere
    d = d.sort_values("yr")
    d["prior_here"] = d.groupby(["a", "b", "club_id"]).m.cumsum() - d.m
    d["prior_any"] = d.groupby(["a", "b"]).m.cumsum() - d.m
    d["season_no"] = d.groupby(["a", "b", "club_id"]).cumcount() + 1
    return d


def growth_across_seasons(d) -> dict:
    """The same pair at the same club, season t+1 against season t."""
    k = ["a", "b", "club_id"]
    x = d.merge(d[k + ["yr", "n", "e", "m"]].assign(yr=lambda z: z.yr - 1), on=k + ["yr"],
                suffixes=("0", "1"))
    x = x[(x.m0 >= MIN_TOGETHER) & (x.m1 >= MIN_TOGETHER)]

    def stat(z):
        return (z.n1.sum() / z.e1.sum()) / (z.n0.sum() / z.e0.sum()) - 1
    p, lo, hi = boot_pairs(x, stat)
    return {"pair_seasons": int(len(x)), "growth": r4(p), "lo": r4(lo), "hi": r4(hi)}


def persistence(d) -> dict:
    """Excess set-ups (observed minus expected) in season t against season t+1 for the
    same pair at the same club, and the same correlation with pairs shuffled within the
    club-season (the noise floor)."""
    k = ["a", "b", "club_id"]
    d = d[d.m >= MIN_TOGETHER].copy()
    d["shr"] = d.n - d.e
    x = d.merge(d[k + ["yr", "shr"]].assign(yr=lambda z: z.yr - 1).rename(
        columns={"shr": "shr1"}), on=k + ["yr"])
    r = x.shr.corr(x.shr1)
    rng = np.random.default_rng(SEED)
    null = []
    for _ in range(500):
        y = x.copy()
        y["shr1"] = y.groupby(["club_id", "season"]).shr1.transform(
            lambda s: rng.permutation(s.to_numpy()))
        null.append(y.shr.corr(y.shr1))
    return {"pair_seasons": int(len(x)), "corr_next_season": r4(r),
            "null_mean": r4(np.mean(null)), "null_95": r4(np.percentile(null, 97.5)),
            }


def dose(d) -> pd.DataFrame:
    """Chemistry by minutes the pair had already played together at this club."""
    d = d[(d.m >= MIN_TOGETHER) & (d.yr >= 2015)].copy()
    d["band"] = pd.cut(d.prior_here, [-1, 0, 1500, 3000, 6000, 1e9],
                       labels=["New pair", "Under 1,500", "1,500–3,000", "3,000–6,000", "Over 6,000"])
    rows = []
    for b, g in d.groupby("band", observed=True):
        p, lo, hi = boot_pairs(g, ratio, n=N_BOOT // 4)
        rows.append(dict(prior_minutes=str(b), pair_seasons=len(g), chemistry=p, lo=lo, hi=hi))
    return pd.DataFrame(rows)


def reunions(d) -> dict:
    """First season at a club for pairs who had played together elsewhere, against
    first seasons for pairs who had never played together."""
    first = d[(d.season_no == 1) & (d.m >= MIN_TOGETHER) & (d.yr >= 2015)].copy()
    first["reunited"] = first.prior_any > 0
    re, new = first[first.reunited], first[~first.reunited]
    p, lo, hi = boot_pairs(first, lambda x: ratio(x[x.reunited]) / ratio(x[~x.reunited]) - 1)
    return {"reunited_pairs": int(len(re)), "new_pairs": int(len(new)),
            "reunited": r4(ratio(re)), "new": r4(ratio(new)),
            "gap": r4(p), "lo": r4(lo), "hi": r4(hi)}


def top_pairs(d, names: pd.Series) -> pd.DataFrame:
    """Pairs with the most set-ups beyond expectation over their whole time together
    (shrunk), for the README's short list. Undirected: A to B plus B to A."""
    u = d.assign(x=np.minimum(d.a, d.b), y=np.maximum(d.a, d.b))
    g = u.groupby(["x", "y"]).agg(n=("n", "sum"), e=("e", "sum"), m=("m", "sum"),
                                 xg=("xg", "sum"), club=("club_id", "last"))
    g["m"] = g.m / 2  # each direction carries the same minutes together
    g = g[g.m >= 3000]
    g["chem_shrunk"], tau2 = shrink(g.n, g.e)
    g.attrs["sd_true"] = float(np.sqrt(tau2))
    g = g.reset_index()
    g["pair"] = g.x.map(names) + " & " + g.y.map(names)
    return g.sort_values("chem_shrunk", ascending=False)


def main():
    sh = assisted_shots()
    pg = pair_games()
    res = {"assisted_shots": int(len(sh)), "pair_matches": int(len(pg))}
    res["growth_within_first_season"] = growth_within_season(sh, pg)
    d = season_links(sh, pg)
    res["growth_next_season"] = growth_across_seasons(d)
    res["persistence"] = persistence(d)
    res["reunions"] = reunions(d)
    ds = dose(d)
    ds.to_csv(OUT / "chemistry_dose.csv", index=False, float_format="%.4f")
    names = pd.read_csv(SOURCE / "transfermarkt" / "players.csv.gz",
                        usecols=["player_id", "name"]).set_index("player_id").name
    tp = top_pairs(d, names)
    res["long_pairs"] = {"pairs_3000_minutes": int(len(tp)),
                         "sd_true_chemistry": r4(tp.attrs["sd_true"])}
    tp.head(15)[["pair", "m", "n", "e", "chem_shrunk"]].to_csv(
        OUT / "chemistry_top_pairs.csv", index=False, float_format="%.3f")
    (OUT / "chemistry.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))
    print(ds.round(3).to_string(index=False))
    print(tp.head(15)[["pair", "m", "n", "e", "chem_shrunk"]].round(2).to_string(index=False))


def _check():
    # two passers, two shooters, equal minutes: a perfectly "habit-only" table fits exactly
    d = pd.DataFrame({"u": 1, "a": [1, 1, 2, 2], "b": [3, 4, 3, 4], "m": [90.0] * 4,
                      "n": [4.0, 2.0, 2.0, 1.0]})
    e = expected(d, ["u"])
    assert np.allclose(e, d.n), e.tolist()
    # an extra link between 1 and 3 shows up as N > E for that pair only
    d.loc[0, "n"] = 8
    e = expected(d, ["u"])
    assert d.n[0] > e[0] and abs(d.n.sum() - e.sum()) < 1e-6
    print("ok")


if __name__ == "__main__":
    import sys
    _check() if "check" in sys.argv[1:] else main()
