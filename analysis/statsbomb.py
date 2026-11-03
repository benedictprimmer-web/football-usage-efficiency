"""StatsBomb open data, 2015-16: every pass between team-mates, and who was on the pitch.

StatsBomb released full event data for 2015-16 in four of the big five leagues (1,517
matches; its Bundesliga file holds only Leverkusen's 34). This script reduces each match's
events to small tables and keeps the raw JSON only as a local cache:

    sb_passes.parquet   one row per completed open-play pass: passer, receiver,
                        minute, whether it reached the box, whether it set up a shot,
                        and that shot's xG
    sb_minutes.parquet  one row per player per match: the minutes he came on and went off
                        (from the starting XI, substitutions and red cards)

Data: https://github.com/statsbomb/open-data (free, with attribution to StatsBomb).
Raw files are cached under $SOURCE_DATA/statsbomb/; the reduced tables go to data/work/.

    python analysis/statsbomb.py
"""
from __future__ import annotations

import gzip
import json
import time
import urllib.request

import pandas as pd

from config import SOURCE, WORK

BASE = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"
SEASON = 27  # 2015/2016
COMPS = {2: "ENG-Premier League", 11: "ESP-La Liga", 12: "ITA-Serie A",
         9: "GER-Bundesliga", 7: "FRA-Ligue 1"}
CACHE = SOURCE / "statsbomb" / "open_2015_16"
BOX_X, BOX_Y = 102, (18, 62)  # StatsBomb pitch is 120 x 80


def _get(path: str):
    """Fetch one JSON file, caching it gzipped. Retries politely."""
    dest = CACHE / (path.replace("/", "_") + ".gz")
    if dest.exists():
        with gzip.open(dest, "rt") as f:
            return json.load(f)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(f"{BASE}/{path}", timeout=60) as r:
                raw = r.read()
            break
        except OSError:
            time.sleep(2 ** attempt)
    else:
        raise RuntimeError(f"could not fetch {path}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(dest, "wb") as f:
        f.write(raw)
    return json.loads(raw)


def minutes(events: list[dict], match_id: int) -> list[dict]:
    """On and off minute for every player who played, from the event stream."""
    end = max(e["minute"] + e["second"] / 60 for e in events)
    on, off, team = {}, {}, {}
    for e in events:
        t = e["type"]["name"]
        if t == "Starting XI":
            for p in e["tactics"]["lineup"]:
                pid = p["player"]["id"]
                on[pid], team[pid] = 0.0, e["team"]["name"]
        elif t == "Substitution":
            m = e["minute"] + e["second"] / 60
            off[e["player"]["id"]] = m
            new = e["substitution"]["replacement"]["id"]
            on[new], team[new] = m, e["team"]["name"]
        else:
            card = (e.get("foul_committed", {}).get("card") or e.get("bad_behaviour", {}).get("card") or {})
            if card.get("name") in ("Red Card", "Second Yellow") and "player" in e:
                off[e["player"]["id"]] = e["minute"] + e["second"] / 60
    return [{"match_id": match_id, "team": team[p], "player_id": p,
             "on": on[p], "off": off.get(p, end)} for p in on]


def passes(events: list[dict], match_id: int) -> list[dict]:
    """Completed open-play passes between team-mates, with the xG of any shot they set up."""
    xg = {e["id"]: e["shot"]["statsbomb_xg"] for e in events
          if e["type"]["name"] == "Shot" and e["shot"]["type"]["name"] == "Open Play"}
    rows = []
    for e in events:
        if e["type"]["name"] != "Pass":
            continue
        p = e["pass"]
        if "outcome" in p or "recipient" not in p or p.get("type", {}).get("name") in (
                "Corner", "Free Kick", "Throw-in", "Goal Kick", "Kick Off"):
            continue
        x, y = p["end_location"]
        rows.append({
            "match_id": match_id, "team": e["team"]["name"], "minute": e["minute"],
            "passer": e["player"]["id"], "receiver": p["recipient"]["id"],
            "into_box": x >= BOX_X and BOX_Y[0] <= y <= BOX_Y[1],
            "xa": xg.get(p.get("assisted_shot_id"), 0.0),
            "shot_assist": p.get("assisted_shot_id") in xg,
        })
    return rows


def build():
    pas, mins, names, games = [], [], {}, []
    for cid, league in COMPS.items():
        for g in _get(f"matches/{cid}/{SEASON}.json"):
            mid = g["match_id"]
            games.append({"match_id": mid, "league": league, "date": g["match_date"],
                          "home": g["home_team"]["home_team_name"],
                          "away": g["away_team"]["away_team_name"]})
            ev = _get(f"events/{mid}.json")
            pas += passes(ev, mid)
            mins += minutes(ev, mid)
            for e in ev:
                if "player" in e:
                    names[e["player"]["id"]] = e["player"]["name"]
        print(f"{league}: {sum(x['league'] == league for x in games)} matches", flush=True)
    WORK.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(pas).to_parquet(WORK / "sb_passes.parquet", index=False)
    m = pd.DataFrame(mins)
    m["player"] = m.player_id.map(names)
    m.to_parquet(WORK / "sb_minutes.parquet", index=False)
    pd.DataFrame(games).to_parquet(WORK / "sb_games.parquet", index=False)
    print(f"{len(games):,} matches, {len(pas):,} completed open-play passes, {len(m):,} appearances")


if __name__ == "__main__":
    build()
