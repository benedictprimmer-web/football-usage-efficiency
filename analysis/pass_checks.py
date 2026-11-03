"""Two more pass-level checks on the chemistry result, from other providers' event data.

sb_check.py reruns the growth test on StatsBomb passes (2015-16). Here it is rerun on two
further sources, so that no single provider's way of recording passes carries the finding:

  impect    Impect open data, Bundesliga 2023-24 (306 matches): passes with receivers,
            line-ups and substitution times. github.com/ImpectAPI/open-data. Terms
            (LICENSE.pdf there): non-commercial, no redistribution, credit Impect as the
            data source. The raw files stay outside this repo.
  wyscout   Wyscout public dataset (Pappalardo et al. 2019, Scientific Data 6:236, figshare,
            CC BY 4.0), Big-5 leagues 2017-18 (1,826 matches). Passes carry no receiver:
            the receiver is inferred as the player of the NEXT event when that event is by
            the same team, in the same half, by a different player, and the pass was
            accurate. Accurate passes followed by an opponent's event (a duel, say) get no
            receiver and drop out. Substitution and red-card minutes come from the match
            files.

The test is the one in sb_check.pass_growth. Count completed open-play passes A -> B per
minute together; fit the expected rate per team and half of the season with a passer term
and a receiver term (chemistry.expected); then compare growth from the first half to the
second for pairs who are NEW that season against ESTABLISHED pairs. A team's overall
tempo cancels, because the expected rate is refitted in each half.

New and established come from Transfermarkt's pair_minutes (data/work/pair_minutes.parquet):
new = the pair played no minutes together in the previous season in any Big-5 league,
established = 900 or more. Source players are mapped to Transfermarkt ids by date of birth
and name, then by name within the club. Pairs with an unmapped player are dropped, and so
are teams with no previous-season record in the Big-5 data (promoted clubs), where "new" cannot
be told from "unknown".

Writes data/pass_checks.json (aggregates only).

    SOURCE_DATA=... python analysis/pass_checks.py          (after minutes.py)
    python analysis/pass_checks.py rebuild                  (reread the raw event files)
    python analysis/pass_checks.py check                    (self-test)
"""
from __future__ import annotations

import difflib
import json
import sys

import numpy as np
import pandas as pd

from config import OUT, SOURCE, WORK, N_BOOT
from crosswalk import norm_player, team_map, tm_games
from chemistry import expected, boot_pairs, ratio, r4, n_pairs

MIN_HALF = 450          # minutes together in each half, as in sb_check
ESTABLISHED = 900       # previous-season minutes together
IMPECT = SOURCE / "impect" / "repo" / "data"
WYSCOUT = SOURCE / "wyscout"
IMPECT_LEAGUE, IMPECT_SEASON = "GER-Bundesliga", "2023-2024"
WYSCOUT_FILES = {"England": "ENG-Premier League", "Spain": "ESP-La Liga", "Italy": "ITA-Serie A",
                 "Germany": "GER-Bundesliga", "France": "FRA-Ligue 1"}
WYSCOUT_SEASON = "2017-2018"
# Wyscout club names that crosswalk.team_map cannot bridge to Transfermarkt's
WYSCOUT_ALIASES = {"Internazionale": "Inter Milan", "Bayern München": "Bayern Munich"}
IMPECT_P2 = 10000       # Impect's clock: the second half starts at 10,000 seconds


# ------------------------------------------------------------------ shared pieces

def minutes_rows(match_id, team, start, subs_on, subs_off, end) -> list[dict]:
    """On and off minute for every player of one team in one match. start: players on at
    kick-off; subs_on / subs_off: {player: minute}; end: full length in minutes."""
    rows = []
    for p in set(start) | set(subs_on):
        on = 0.0 if p in start else float(subs_on[p])
        off = float(subs_off.get(p, end))
        if off > on:
            rows.append({"match_id": match_id, "team": team, "player": p, "on": on, "off": off})
    return rows


def pair_table(passes: pd.DataFrame, mins: pd.DataFrame, matches: pd.DataFrame) -> pd.DataFrame:
    """Passes A -> B and minutes together per team and half of the season, with the expected
    count (as sb_check.pass_links). passes: match_id, team, passer, receiver. mins: match_id,
    team, player, on, off. matches: match_id, league, date."""
    matches = matches.copy()
    # half of the season by date within each league, as in sb_check
    matches["part"] = (matches.groupby("league").date.rank(method="dense", pct=True) > 0.5).astype(int)
    mins = mins.merge(matches[["match_id", "part"]], on="match_id")
    x = mins[["match_id", "team", "part", "player", "on", "off"]]
    p = x.merge(x[["match_id", "team", "player", "on", "off"]], on=["match_id", "team"],
                suffixes=("_a", "_b"))
    p = p[p.player_a != p.player_b]
    p["m"] = (np.minimum(p.off_a, p.off_b) - np.maximum(p.on_a, p.on_b)).clip(lower=0)
    m = p.groupby(["team", "part", "player_a", "player_b"]).m.sum().rename("m")
    passes = passes.merge(matches[["match_id", "part"]], on="match_id")
    n = passes.groupby(["team", "part", "passer", "receiver"]).size().rename("n")
    n.index = n.index.set_names(["team", "part", "player_a", "player_b"])
    d = m.to_frame().join(n).fillna({"n": 0}).reset_index()
    d = d[d.m > 0].rename(columns={"player_a": "a", "player_b": "b"})
    d["e"] = expected(d, ["team", "part"])
    return d


def tm_pair_prior(prior_season: str) -> tuple[pd.Series, set]:
    """Minutes together in the previous season by unordered pair (any club), and the set of
    clubs with a record in that season."""
    pm = pd.read_parquet(WORK / "pair_minutes.parquet")
    pm = pm[pm.season == prior_season]
    both = pd.concat([pm.rename(columns={"player_id_a": "a", "player_id_b": "b"}),
                      pm.rename(columns={"player_id_a": "b", "player_id_b": "a"})])
    return both.groupby(["a", "b"]).minutes_together.sum(), set(pm.club_id)


def growth_test(d: pd.DataFrame, prior: pd.Series, n_boot: int = N_BOOT // 2) -> dict:
    """First half against second half, new pairs against established pairs (sb_check's test).
    d: team, part, a, b (Transfermarkt ids), m, n, e."""
    d = d.join(prior.rename("prior"), on=["a", "b"]).fillna({"prior": 0})
    g = d.groupby(["team", "a", "b"])
    d = d[(g.part.transform("nunique") == 2) & (g.m.transform("min") >= MIN_HALF)].copy()
    d["group"] = np.where(d.prior == 0, "new", np.where(d.prior >= ESTABLISHED, "established", "other"))
    other = d[d.group == "other"]
    d = d[d.group != "other"]

    def growth(x):
        return ratio(x[x.part == 1]) / ratio(x[x.part == 0]) - 1

    def stat(x):
        return growth(x[x.group == "new"]) - growth(x[x.group == "established"])
    out = {}
    for grp in ("new", "established"):
        x = d[d.group == grp]
        p, lo, hi = boot_pairs(x, growth, n=n_boot)
        out[grp] = {"pairs": n_pairs(x), "passes": int(x.n.sum()),
                    "growth": r4(p), "lo": r4(lo), "hi": r4(hi),
                    "ratio_first_half": r4(ratio(x[x.part == 0])),
                    "ratio_second_half": r4(ratio(x[x.part == 1]))}
    p, lo, hi = boot_pairs(d, stat, n=n_boot)
    out["new_minus_established"] = {"gap": r4(p), "lo": r4(lo), "hi": r4(hi)}
    out["pairs_between_0_and_900_dropped"] = n_pairs(other) if len(other) else 0
    return out


def map_players(src: pd.DataFrame, cand: pd.DataFrame) -> pd.Series:
    """Source player -> Transfermarkt id. src: pid, club_id (Transfermarkt club of his team, may
    be NaN), names (list), dob. cand: Transfermarkt players of that league-season: player_id,
    club_id, name, dob. Rule 1 date of birth and name (exact, or close spelling); rule 2 name
    within the club (exact, or a last name that is unique there)."""
    by_dob = {k: v for k, v in cand.groupby("dob")}
    by_club = {k: v for k, v in cand.groupby("club_id")}
    out = {}
    for r in src.itertuples():
        names = [norm_player(n) for n in r.names if n]
        hit = None
        c = by_dob.get(r.dob)
        if c is not None:
            cn = {norm_player(n): pid for n, pid in zip(c.name, c.player_id)}
            hit = next((cn[n] for n in names if n in cn), None)
            if hit is None and len(set(c.player_id)) == 1:
                best = max(difflib.SequenceMatcher(None, n, k).ratio() for n in names for k in cn)
                hit = c.player_id.iloc[0] if best >= 0.6 else None
        if hit is None and r.club_id in by_club:
            c = by_club[r.club_id]
            cn = {norm_player(n): pid for n, pid in zip(c.name, c.player_id)}
            hit = next((cn[n] for n in names if n in cn), None)
            if hit is None:
                for n in names:
                    last = [pid for k, pid in cn.items() if k and n and k.split()[-1] == n.split()[-1]]
                    if len(set(last)) == 1:
                        hit = last[0]
                        break
        if hit is not None:
            out[r.pid] = int(hit)
    return pd.Series(out, dtype="Int64")


def tm_candidates(league: str, season: str) -> pd.DataFrame:
    iv = pd.read_parquet(WORK / "intervals.parquet", columns=["player_id", "club_id", "league", "season"])
    iv = iv[(iv.league == league) & (iv.season == season)].drop_duplicates(["player_id", "club_id"])
    pl = pd.read_csv(SOURCE / "transfermarkt" / "players.csv.gz",
                     usecols=["player_id", "name", "date_of_birth"])
    pl["dob"] = pl.date_of_birth.astype(str).str[:10]
    return iv.merge(pl[["player_id", "name", "dob"]], on="player_id")


def club_ids(names: dict, league: str, season: str) -> dict:
    """{source team id: Transfermarkt club id} by club name within one league-season."""
    g = tm_games()
    g = g[(g.league == league) & (g.season == season)]
    tm = pd.concat([g[["home_club_name", "home_club_id"]].set_axis(["n", "id"], axis=1),
                    g[["away_club_name", "away_club_id"]].set_axis(["n", "id"], axis=1)]).drop_duplicates()
    ids = tm.set_index("n").id
    tmap = team_map(list(names.values()), list(ids.index))
    return {t: int(ids[tmap[n][0]]) for t, n in names.items() if n in tmap}


def to_transfermarkt(d: pd.DataFrame, sp: pd.DataFrame, team_names: dict, team_league: dict,
                     season: str) -> tuple[pd.DataFrame, dict]:
    """Give every pair Transfermarkt ids and the team its Transfermarkt club. sp: pid, team,
    names, dob (one row per player-team); team_names: {team: club name}; team_league: {team:
    league}. Pairs with an unmapped player are dropped."""
    mapped, club_of = [], {}
    for lg in sorted(set(team_league.values())):
        teams = [t for t, v in team_league.items() if v == lg]
        clubs = club_ids({t: team_names[t] for t in teams}, lg, season)
        club_of |= clubs
        s = sp[sp.team.isin(teams)].assign(club_id=lambda z: z.team.map(clubs))
        ids = map_players(s.drop_duplicates("pid"), tm_candidates(lg, season))
        mapped.append(ids)
    ids = pd.concat(mapped)
    ids = ids[~ids.index.duplicated()]
    both = d.a.map(ids).notna() & d.b.map(ids).notna()
    pl = pd.concat([d[["team", "a"]].rename(columns={"a": "pid"}),
                    d[["team", "b"]].rename(columns={"b": "pid"})]).drop_duplicates("pid")
    stats = {"players_on_pitch": int(len(pl)), "players_mapped": int(pl.pid.map(ids).notna().sum()),
             "share_pair_minutes_mapped": r4(d.m[both].sum() / d.m.sum()),
             "teams_matched_to_a_club": f"{len(club_of)} of {len(team_league)}"}
    d = d[both].assign(a=lambda z: z.a.map(ids), b=lambda z: z.b.map(ids)).astype({"a": int, "b": int})
    d = d[d.a != d.b].assign(club_id=lambda z: z.team.map(club_of))
    return d, stats


def run_source(label, passes, mins, matches, sp, team_names, team_league, season, prior_season,
               extra) -> dict:
    """Pair table, id mapping, previous-season split and growth test for one source."""
    d = pair_table(passes, mins, matches)
    d, res = to_transfermarkt(d, sp, team_names, team_league, season)
    res = {"matches": int(matches.match_id.nunique()), "passes_counted": int(len(passes))} | res
    prior, prior_clubs = tm_pair_prior(prior_season)
    keep = d.club_id.isin(prior_clubs)
    res["teams_used"] = int(d[keep].team.nunique())
    res["teams_dropped_no_previous_season_record"] = int(d.team.nunique() - d[keep].team.nunique())
    res |= extra
    res["pass_growth"] = growth_test(d[keep], prior)
    print(label, json.dumps(res, indent=1))
    return res


# ------------------------------------------------------------------ Impect

def impect_clock(sec: float, l1: float) -> float:
    """Impect game time (seconds, second half starts at 10,000) -> minutes played."""
    return (sec if sec < IMPECT_P2 else l1 + sec - IMPECT_P2) / 60


def impect_match(events: list, lineup: dict) -> tuple[list, list]:
    """Completed open-play passes with a receiver, and on/off minutes, for one match."""
    t1 = [e["gameTime"]["gameTimeInSec"] for e in events if e["periodId"] == 1]
    t2 = [e["gameTime"]["gameTimeInSec"] for e in events if e["periodId"] == 2]
    l1 = max(t1)
    end = impect_clock(max(t2), l1)
    mid = lineup["id"]
    passes = []
    for e in events:
        p = e.get("pass")
        if (e["actionType"] == "PASS" and e["result"] == "SUCCESS" and p and p.get("receiver")
                and p["receiver"]["type"] == "TEAMMATE" and e.get("setPiece") is None
                and e["phase"] != "SET_PIECE" and e["player"]["id"] != p["receiver"]["playerId"]):
            passes.append((mid, e["squadId"], e["player"]["id"], p["receiver"]["playerId"]))
    rows = []
    for side in ("squadHome", "squadAway"):
        s = lineup[side]
        on, off = {}, {}
        for x in s["substitutions"]:
            t = impect_clock(x["gameTime"]["gameTimeInSec"], l1)
            if x["fromPosition"] == "BANK":
                on[x["playerId"]] = t
            elif x["toPosition"] == "BANK":      # substituted off, or sent off
                off[x["playerId"]] = t
        rows += minutes_rows(mid, s["id"], {x["playerId"] for x in s["startingPositions"]},
                             on, off, end)
    return passes, rows


def impect_build() -> dict:
    """Stream the 306 match files one at a time and keep only passes and minutes."""
    mt = pd.DataFrame(json.loads((IMPECT / "matches").glob("matches_*.json").__next__().read_text()))
    passes, rows = [], []
    for mid in mt.id:
        ev = json.loads((IMPECT / "events" / f"events_{mid}.json").read_text())
        lu = json.loads((IMPECT / "lineups" / f"lineups_{mid}.json").read_text())
        a, b = impect_match(ev, lu)
        passes += a
        rows += b
    sq = {s["id"]: s["name"] for s in json.loads(next((IMPECT / "squads").glob("squads_*.json")).read_text())}
    pl = pd.DataFrame(json.loads(next((IMPECT / "players").glob("players_*.json")).read_text()))
    return dict(
        passes=pd.DataFrame(passes, columns=["match_id", "team", "passer", "receiver"]),
        mins=pd.DataFrame(rows),
        matches=mt.assign(match_id=mt.id, league=IMPECT_LEAGUE,
                          date=pd.to_datetime(mt.scheduledDate)).drop(columns=["id"]),
        players=pl.assign(pid=pl.id, dob=pl.birthdate.astype(str).str[:10],
                          names=[[a, f"{b} {c}"] for a, b, c in
                                 zip(pl.commonname, pl.firstname, pl.lastname)])[["pid", "names", "dob"]],
        squads=sq)


def impect() -> dict:
    cache = WORK / "pass_checks_impect.pkl"
    if cache.exists() and "rebuild" not in sys.argv[1:]:
        z = pd.read_pickle(cache)
    else:
        z = impect_build()
        pd.to_pickle(z, cache)
    team_of = z["mins"][["team", "player"]].drop_duplicates().rename(columns={"player": "pid"})
    sp = team_of.merge(z["players"], on="pid")
    teams = {t: IMPECT_LEAGUE for t in team_of.team.unique()}
    return run_source("impect", z["passes"], z["mins"].rename(columns={"player": "player"}),
                      z["matches"], sp, z["squads"], teams, IMPECT_SEASON, "2022-2023",
                      {"source": "Impect open data (github.com/ImpectAPI/open-data), Bundesliga 2023-24",
                       "established": "900+ minutes together in 2022-23 (Transfermarkt pair_minutes)",
                       "receiver": "recorded"})


# ------------------------------------------------------------------ Wyscout

def fix_text(s: str) -> str:
    """Wyscout's JSON escapes accents twice ('M\\u00e1laga'); undo that, and the odd UTF-8 read
    as Latin-1, when either applies."""
    if "\\u" in s:
        s = s.encode("ascii", "backslashreplace").decode("unicode_escape")
    try:
        return s.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s


def infer_receivers(ev: pd.DataFrame) -> pd.DataFrame:
    """Open-play passes with an inferred receiver. ev: one match's events in order, with
    period, team, player, event, sub, accurate. Receiver = the next event's player when
    that event is by the same team, in the same period, by another named player and the
    pass was accurate. Free kicks, corners and throw-ins are event 3 and not passes; goalkeeper
    hand passes (sub-event 81) are left out."""
    nxt = ev[["period", "team", "player"]].shift(-1)
    ok = ((ev.event == 8) & (ev.sub != 81) & ev.accurate & (nxt.team == ev.team)
          & (nxt.period == ev.period) & (nxt.player != ev.player) & (nxt.player > 0)
          & (ev.player > 0))
    return pd.DataFrame({"passer": ev.player[ok], "receiver": nxt.player[ok].astype(int),
                         "team": ev.team[ok]})


def wyscout_minute(m: float, l1: float) -> float:
    """Wyscout substitution minute (nominal, second half from 46) -> minutes played."""
    return float(m) if m <= 45 else l1 + (m - 45)


def wyscout_league(league_file: str) -> dict:
    ev = pd.DataFrame(json.loads((WYSCOUT / "events" / f"events_{league_file}.json").read_text()))
    ev = ev[["matchId", "matchPeriod", "eventSec", "teamId", "playerId", "eventId", "subEventId", "tags"]]
    ev["accurate"] = [any(t["id"] == 1801 for t in tags) for tags in ev.tags]
    ev = ev.drop(columns="tags").rename(columns={"matchId": "match_id", "matchPeriod": "period",
                                                 "teamId": "team", "playerId": "player",
                                                 "eventId": "event", "subEventId": "sub"})
    ev["pnum"] = ev.period.map({"1H": 1, "2H": 2})
    ev = ev[ev.pnum.notna()]
    ev = ev.sort_values(["match_id", "pnum", "eventSec"], kind="stable")
    passes, rows, n_acc = [], [], 0
    mt = json.loads((WYSCOUT / "matches" / f"matches_{league_file}.json").read_text())
    by_id = {x["wyId"]: x for x in mt}
    for match_id, e in ev.groupby("match_id", sort=False):
        r = infer_receivers(e.assign(period=e.pnum).reset_index(drop=True))
        n_acc += int(((e.event == 8) & (e.sub != 81) & e.accurate).sum())
        passes.append(r.assign(match_id=match_id))
        l1 = e.eventSec[e.pnum == 1].max() / 60
        end = l1 + e.eventSec[e.pnum == 2].max() / 60
        m = by_id[match_id]
        for tid, td in m["teamsData"].items():
            f = td.get("formation")
            if not f or not f.get("lineup"):
                continue
            subs = f["substitutions"] if isinstance(f["substitutions"], list) else []   # "null" if none
            sub_on = {s["playerIn"]: wyscout_minute(s["minute"], l1) for s in subs if s["playerIn"]}
            sub_off = {s["playerOut"]: wyscout_minute(s["minute"], l1) for s in subs if s["playerOut"]}
            for p in f["lineup"] + f["bench"]:        # a red card ends a player's match
                red = str(p.get("redCards", "0"))
                if red.isdigit() and int(red) > 0:
                    sub_off[p["playerId"]] = min(sub_off.get(p["playerId"], end),
                                                 wyscout_minute(int(red), l1))
            rows += minutes_rows(match_id, int(tid), {p["playerId"] for p in f["lineup"]},
                                 sub_on, sub_off, end)
    mdf = pd.DataFrame([{"match_id": x["wyId"], "league": WYSCOUT_FILES[league_file],
                         "date": pd.to_datetime(x["dateutc"])} for x in mt])
    return dict(passes=pd.concat(passes), mins=pd.DataFrame(rows), matches=mdf, accurate=n_acc)


def wyscout_build() -> dict:
    parts = [wyscout_league(f) for f in WYSCOUT_FILES]          # one league file at a time
    names = {t["wyId"]: fix_text(t["name"]) for t in json.loads((WYSCOUT / "teams.json").read_text())}
    teams = {k: WYSCOUT_ALIASES.get(v, v) for k, v in names.items()}
    pl = pd.DataFrame(json.loads((WYSCOUT / "players.json").read_text()))
    first, last, short = (pl[c].map(fix_text) for c in ("firstName", "lastName", "shortName"))
    pl = pl.assign(pid=pl.wyId, dob=pl.birthDate.astype(str).str[:10],
                   names=[[f"{a} {b}", s] for a, b, s in zip(first, last, short)])
    return dict(parts=parts, teams=teams, players=pl[["pid", "names", "dob"]])


def wyscout() -> dict:
    cache = WORK / "pass_checks_wyscout.pkl"
    if cache.exists() and "rebuild" not in sys.argv[1:]:
        z = pd.read_pickle(cache)
    else:
        z = wyscout_build()
        pd.to_pickle(z, cache)
    parts = z["parts"]
    passes = pd.concat([p["passes"] for p in parts])
    mins = pd.concat([p["mins"] for p in parts])
    matches = pd.concat([p["matches"] for p in parts])
    accurate = sum(p["accurate"] for p in parts)
    team_league = {}
    for p, lg in zip(parts, WYSCOUT_FILES.values()):
        team_league |= {t: lg for t in p["mins"].team.unique()}
    team_of = mins[["team", "player"]].drop_duplicates().rename(columns={"player": "pid"})
    sp = team_of.merge(z["players"], on="pid")
    return run_source("wyscout", passes, mins, matches, sp, z["teams"], team_league,
                      WYSCOUT_SEASON, "2016-2017",
                      {"source": "Wyscout public dataset, Pappalardo et al. 2019 (figshare, CC BY 4.0), "
                                 "Big-5 leagues 2017-18",
                       "established": "900+ minutes together in 2016-17 (Transfermarkt pair_minutes)",
                       "receiver": "inferred: next event's player, same team and half, accurate pass",
                       "accurate_open_play_passes": int(accurate),
                       "share_with_inferred_receiver": r4(len(passes) / accurate)})


# ------------------------------------------------------------------ run

def _check():
    # minutes: a starter subbed off at 60, his replacement on from 60
    r = minutes_rows(1, 7, {1, 2}, {3: 60.0}, {1: 60.0}, 90.0)
    got = {x["player"]: (x["on"], x["off"]) for x in r}
    assert got == {1: (0.0, 60.0), 2: (0.0, 90.0), 3: (60.0, 90.0)}, got
    assert abs(impect_clock(10814.245, 2881.399) - (2881.399 + 814.245) / 60) < 1e-9
    assert wyscout_minute(30, 47.0) == 30 and wyscout_minute(46, 47.0) == 48.0
    # receivers: accurate pass -> next event by a team-mate; not when the next event is the
    # opponent's, in the other half, by the same player, or the pass was inaccurate
    ev = pd.DataFrame({
        "period": [1, 1, 1, 1, 1, 2, 2], "team": [1, 1, 1, 2, 1, 1, 1],
        "player": [10, 11, 12, 20, 13, 14, 15], "event": [8, 8, 8, 1, 8, 8, 1],
        "sub": [85, 85, 85, 11, 85, 85, 11], "accurate": [True, True, False, True, True, True, False]})
    r = infer_receivers(ev)
    assert list(zip(r.passer, r.receiver)) == [(10, 11), (11, 12), (14, 15)], r
    # 12 was inaccurate, 13 is followed by the second half
    opp = ev.iloc[[0, 3]].assign(team=[1, 2]).reset_index(drop=True)      # next event is the opponent's
    assert len(infer_receivers(opp)) == 0
    # pair table: two players the whole match and equal passes both ways -> expected = observed
    pas = pd.DataFrame({"match_id": [1] * 6, "team": [1] * 6, "passer": [1, 1, 1, 2, 2, 2],
                        "receiver": [2, 2, 2, 1, 1, 1]})
    mi = pd.DataFrame({"match_id": [1, 1], "team": [1, 1], "player": [1, 2], "on": [0., 0.], "off": [90., 90.]})
    ma = pd.DataFrame({"match_id": [1], "league": ["x"], "date": pd.to_datetime(["2020-01-01"])})
    t = pair_table(pas, mi, ma)
    assert np.allclose(t.n, 3) and np.allclose(t.e, 3) and np.allclose(t.m, 90), t
    # growth test on teams of six: no true growth -> gap near zero; new pairs' passing +30% in
    # the second half -> a clear positive gap (shrunk a little, since the expected rate is refitted)
    rng = np.random.default_rng(1)
    rows = [(t, part, t * 100 + i, t * 100 + j, 1000.0, (i + j) % 2)
            for t in range(40) for part in (0, 1) for i in range(6) for j in range(6) if i != j]
    d = pd.DataFrame(rows, columns=["team", "part", "a", "b", "m", "est"])
    first = d[d.part == 0]
    prior = pd.Series(np.where(first.est == 1, 2000.0, 0.0),
                      index=pd.MultiIndex.from_arrays([first.a, first.b], names=["a", "b"]))
    for bump, lo_hi in ((0.0, (-0.1, 0.1)), (0.3, (0.05, 0.4))):
        mu = 100 * np.where((d.part == 1) & (d.est == 0), 1 + bump, 1.0)
        d["n"] = rng.poisson(mu)
        d["e"] = expected(d, ["team", "part"])
        g = growth_test(d, prior, n_boot=100)["new_minus_established"]
        assert lo_hi[0] < g["gap"] < lo_hi[1] and g["lo"] <= g["gap"] <= g["hi"], (bump, g)
    print("ok")


def main():
    res = {"impect": impect()}
    res["wyscout"] = wyscout()
    (OUT / "pass_checks.json").write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    _check() if "check" in sys.argv[1:] else main()
