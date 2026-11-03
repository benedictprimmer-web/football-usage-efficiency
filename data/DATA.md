# Data

No raw third-party data is in this repository. This file says what is here, where each source comes from, what licence it carries, and where the scripts expect to find it.

## What is here

All aggregates, plus season numbers for three case-study players.

| File | What it holds |
|---|---|
| `transfers.json` | Movers against stayers: flop rates, the four-part gap, the luck benchmark, buying-club persistence and the flop predictor, with 95% intervals |
| `transfer_splits.csv` | The four-part split for movers and stayers, among flops and across all seasons |
| `transfer_slices.csv` | Flop rate and mean change by age, fee and league path |
| `age_gaps.csv` | Movers minus stayers by age band |
| `buying_clubs.csv` | Each buying club's record (8+ signings), raw and shrunk |
| `noise_benchmark_draws_movers.csv`, `_stayers.csv` | The 200 runs of the luck benchmark |
| `within_slopes.csv`, `within_bins.csv` | Within-player tests under each specification |
| `curve_bins.csv` | Chance quality by share of the ball |
| `reliability.csv` | Split-half reliability by minutes band |
| `chemistry.json`, `chemistry_dose.csv`, `chemistry_top_pairs.csv` | Pair chemistry tests and the top pairs |
| `sb_check.json` | StatsBomb checks: minutes, pass-level chemistry, agreement of pass and shot links |
| `summary.json` | Sample sizes and the within-player headline |
| `case_studies.csv` | Season numbers for Depay, Martial and Ronaldo |
| `opta/` | The same tables rebuilt on FBref/Opta shots for seven leagues (`SHOTS=opta`) |

## What you need to supply

Point `SOURCE_DATA` at a folder laid out like this:

```
$SOURCE_DATA/
  understat/shots.parquet              tidy Understat shots, 2014-15 to 15 Sep 2025
  transfermarkt/games.csv.gz           every match: date, clubs, competition
  transfermarkt/game_lineups.csv.gz    starters and substitutes
  transfermarkt/game_events.csv.gz     substitutions and cards, with the minute
  transfermarkt/appearances.csv.gz     who played, for the player crosswalk
  transfermarkt/players.csv.gz         position, date of birth, name
  transfermarkt/clubs.csv.gz           club names
  transfermarkt/transfers.csv.gz       transfer dates and fees
  statsbomb/                           filled by analysis/statsbomb.py on first run
  fbref/<LEAGUE>_M_1st_match_shooting.csv  FBref/Opta shots (ENG, ESP, ITA, GER, FRA, POR, NED)
  opta/                                written by analysis/fbref.py
```

The crosswalk between the two sources is built from these files by `analysis/crosswalk.py`.

### Understat shots

- **Source:** [understat.com](https://understat.com), via the `.rds` archive in [JaseZiv/worldfootballR_data](https://github.com/JaseZiv/worldfootballR_data) (release `understat_shots`, last updated 18 September 2025, when the project was archived). Big-5 leagues plus the Russian Premier League; Russia is not used here, because Transfermarkt line-ups cover the Big-5.
- **How:** download the six `.rds` files from the release, then `src/usage_model/understat.py` turns them into `shots.parquet` (`tidy_shots` on each file, then concatenate).
- **Licence:** Understat publishes no open licence. The owner has said the data is free for non-commercial use with attribution.

### Transfermarkt tables

- **Source:** [transfermarkt.com](https://www.transfermarkt.com), via [dcaribou/transfermarkt-datasets](https://github.com/dcaribou/transfermarkt-datasets). The project README links the current download location; the copy used here was built on 5 September 2026.
- **Licence:** the mirror is tagged CC0. The underlying data is Transfermarkt's, whose terms restrict automated collection and commercial reuse. Treat it as research use only.

### StatsBomb open data

- **Source:** [statsbomb/open-data](https://github.com/statsbomb/open-data), 2015-16 Premier League, La Liga, Serie A and Ligue 1 (the Bundesliga file holds only Leverkusen and is left out).
- **Licence:** free for non-commercial research with attribution to StatsBomb. Raw data is not redistributed here.

### FBref/Opta shots

- **Source:** Opta xG as published by [FBref](https://fbref.com) until January 2026, archived in [JaseZiv/worldfootballR_data](https://github.com/JaseZiv/worldfootballR_data) (release `fb_match_shooting`, the `*_M_1st_match_shooting.csv` files). Big-5 from 2017-18, Portugal and the Eredivisie from 2018-19, to early 2025.
- **Licence:** FBref's data is Opta's (Stats Perform). Use for non-commercial research with credit to FBref and Opta; the raw files are not redistributed here.
