"""Join Understat to Transfermarkt: one match crosswalk and one player crosswalk.

Understat has the shots and xG; Transfermarkt has minutes, line-ups and
substitutions. They use different ids and different club spellings, so every
number in this repo rests on this join.

Matches. A league fixture is unique within a season (league, season, home,
away), so once club names agree the two sources line up. Club names are
mapped one league at a time, in four passes: exact after normalising, a short
hand list of aliases, one name's words contained in the other's, then a close
spelling match. Each pass only claims names still unclaimed, so "Inter" cannot
collide with "AC Milan" over Transfermarkt's "Inter Milan".

Players. Within each league-season, a normalised name that is unique on both
sides is a vote for that pair of ids; a clash is settled by club. A player
appears in many seasons, so the Transfermarkt id with the most votes wins.

Writes data/work/crosswalk_matches.parquet and data/work/crosswalk_players.parquet
(gitignored: they list individual players).

    python analysis/crosswalk.py
"""
from __future__ import annotations

import difflib
import html
import re
import unicodedata

import pandas as pd

from config import SOURCE, WORK, TM_LEAGUES

# tokens that carry no club identity once case and punctuation are gone;
# 1-2 character tokens and pure digits are dropped too (FC, AC, 04)
_NOISE = {
    "afc", "cfc", "ssc", "rcd", "sco", "bsc", "hsc", "fco", "losc", "ogc",
    "vfl", "vfb", "fsv", "tsg", "spvgg", "estac",
    "club", "calcio", "football", "fussballclub", "fusballclub",
    "associazione", "sportiva", "societa",
}

# normalised Understat spelling -> normalised Transfermarkt spelling, for the
# few clubs the automatic passes cannot bridge
ALIASES = {
    "cologne": "koln",
    "rasenballsport leipzig": "leipzig",
    "evian thonon gaillard": "thonon evian grand geneve",
    "psg": "paris saint germain",
    "spal 2013": "spal",
    "athletic club": "athletic bilbao",
    "wolves": "wolverhampton wanderers",
    "rennes": "stade rennais",
    "brest": "stade brestois",
}

_CONF = {"exact": 0, "alias": 1, "fuzzy": 2}


def _plain(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s)
                   if not unicodedata.combining(c))


def norm_team(name: str) -> str:
    """Casefold, strip accents, punctuation and club-suffix noise."""
    toks = re.sub(r"[^a-z0-9]+", " ", _plain(str(name)).casefold()).split()
    keep = [t for t in toks if len(t) > 2 and not t.isdigit() and t not in _NOISE]
    return " ".join(keep) or " ".join(toks)


def norm_player(name: str) -> str:
    """'N&#039;Golo Kanté' -> 'n golo kante'. Understat names carry HTML entities."""
    s = _plain(html.unescape(html.unescape(str(name)))).casefold()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", s).split())


def team_map(us_names, tm_names) -> dict:
    """{Understat club name: (Transfermarkt club name, confidence)} for one league."""
    us = {}
    for n in dict.fromkeys(us_names):
        us.setdefault(norm_team(n), []).append(n)
    pool = {}
    for n in dict.fromkeys(tm_names):
        pool.setdefault(norm_team(n), n)
    out = {}

    def claim(u, t, conf):
        name = pool.pop(t)
        for spelling in us.pop(u):
            out[spelling] = (name, conf)

    for n in list(us):
        if n in pool:
            claim(n, n, "exact")
    for n in list(us):
        a = ALIASES.get(n)
        if a and a in pool:
            claim(n, a, "alias")
    for n in list(us):
        st = set(n.split())
        hits = [t for t in pool if st <= set(t.split()) or set(t.split()) <= st]
        if len(hits) == 1:
            claim(n, hits[0], "alias")
    for n in list(us):
        hits = difflib.get_close_matches(n, pool, n=2, cutoff=0.75)
        ratio = lambda h: difflib.SequenceMatcher(None, n, h).ratio()  # noqa: E731
        if len(hits) == 1 or (len(hits) > 1 and ratio(hits[0]) - ratio(hits[1]) > 0.1):
            claim(n, hits[0], "fuzzy")
    return out


def tm_games() -> pd.DataFrame:
    g = pd.read_csv(SOURCE / "transfermarkt" / "games.csv.gz",
                    usecols=["game_id", "competition_id", "competition_type", "season",
                             "date", "home_club_id", "away_club_id",
                             "home_club_name", "away_club_name"])
    g = g[(g.competition_type == "domestic_league") & g.competition_id.isin(TM_LEAGUES)]
    g = g.dropna(subset=["home_club_name", "away_club_name"]).copy()
    g["league"] = g.competition_id.map(TM_LEAGUES)
    g["season"] = g.season.astype(int).map(lambda y: f"{y}-{y + 1}")
    return g


def match_crosswalk(shots: pd.DataFrame, games: pd.DataFrame) -> pd.DataFrame:
    us = shots[["league", "season", "game_id", "home_team", "away_team"]].drop_duplicates("game_id")
    rows = []
    for lg, u in us.groupby("league"):
        t = games[games.league == lg]
        names = team_map(pd.concat([u.home_team, u.away_team]).unique(),
                         pd.concat([t.home_club_name, t.away_club_name]).unique())
        key = t.set_index(["season", "home_club_name", "away_club_name"]).game_id
        key = key[~key.index.duplicated()]
        for r in u.itertuples():
            h, a = names.get(r.home_team), names.get(r.away_team)
            if h is None or a is None:
                continue
            tm_id = key.get((r.season, h[0], a[0]))
            if tm_id is not None:
                rows.append((r.game_id, int(tm_id), lg, r.season, r.home_team, r.away_team,
                             max(h[1], a[1], key=_CONF.get)))
    return pd.DataFrame(rows, columns=["us_game_id", "tm_game_id", "league", "season",
                                       "home", "away", "confidence"])


def player_crosswalk(shots: pd.DataFrame, games: pd.DataFrame) -> pd.DataFrame:
    us = shots.dropna(subset=["player_id"]).copy()
    us["us_pid"] = us.player_id.astype("int64")
    us["name"] = us.player.map(norm_player)
    us["club"] = us.team_shot.map(norm_team)
    us = us.drop_duplicates(["league", "season", "us_pid"])

    ap = pd.read_csv(SOURCE / "transfermarkt" / "appearances.csv.gz",
                     usecols=["game_id", "player_id", "player_club_id", "player_name"])
    ap = ap.merge(games[["game_id", "league", "season"]], on="game_id")
    clubs = pd.read_csv(SOURCE / "transfermarkt" / "clubs.csv.gz", usecols=["club_id", "name"])
    ap = ap.merge(clubs.rename(columns={"club_id": "player_club_id", "name": "club_name"}),
                  on="player_club_id", how="left")
    ap = ap.drop_duplicates(["league", "season", "player_id"]).copy()
    ap["name"] = ap.player_name.map(norm_player)
    ap["club"] = ap.club_name.fillna("").map(norm_team)

    votes = []
    tm_by = dict(tuple(ap.groupby(["league", "season"])))
    for k, u in us.groupby(["league", "season"]):
        t = tm_by.get(k)
        if t is None:
            continue
        uc, tc = u.name.value_counts(), t.name.value_counts()
        tg = dict(tuple(t.groupby("name")))
        for r in u.itertuples():
            c = tg.get(r.name)
            if c is None:
                continue
            if uc[r.name] == 1 and tc[r.name] == 1:
                votes.append((r.us_pid, int(c.player_id.iloc[0])))
            else:
                hit = c[c.club == r.club]
                if len(hit) == 1:
                    votes.append((r.us_pid, int(hit.player_id.iloc[0])))
    v = pd.DataFrame(votes, columns=["us_player_id", "tm_player_id"])
    tally = v.value_counts().rename("votes").reset_index()
    tally["vote_share"] = tally.votes / tally.groupby("us_player_id").votes.transform("sum")
    return (tally.sort_values(["us_player_id", "votes", "tm_player_id"],
                              ascending=[True, False, True])
                 .drop_duplicates("us_player_id").reset_index(drop=True))


def build():
    shots = pd.read_parquet(SOURCE / "understat" / "shots.parquet")
    shots = shots[shots.league != "RUS-Premier League"]  # Transfermarkt line-ups: Big-5 only
    games = tm_games()
    mx = match_crosswalk(shots, games)
    px = player_crosswalk(shots, games)
    WORK.mkdir(parents=True, exist_ok=True)
    mx.to_parquet(WORK / "crosswalk_matches.parquet", index=False)
    px.to_parquet(WORK / "crosswalk_players.parquet", index=False)
    n_us = shots.game_id.nunique()
    print(f"matches: {len(mx):,} of {n_us:,} Understat fixtures ({len(mx) / n_us:.1%})")
    print(f"players: {len(px):,} Understat ids matched; "
          f"{(px.vote_share == 1).mean():.1%} unanimous across seasons")
    return mx, px


def _check():
    m = team_map(["Inter", "AC Milan", "FC Cologne", "Athletic Club"],
                 ["Inter Milan", "AC Milan", "1.FC Köln", "Athletic Bilbao"])
    assert m["Inter"][0] == "Inter Milan" and m["AC Milan"] == ("AC Milan", "exact")
    assert m["FC Cologne"][0] == "1.FC Köln" and m["Athletic Club"][0] == "Athletic Bilbao"
    assert norm_player("N&#039;Golo Kanté") == "n golo kante"
    print("ok")


if __name__ == "__main__":
    import sys
    _check() if "check" in sys.argv[1:] else build()
