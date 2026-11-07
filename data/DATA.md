# Data

No raw third-party data is in this repository. This file says what is here, where each source comes from, what licence it carries, and where the scripts expect to find it. [`LICENSE.md`](LICENSE.md) maps every committed file in `data/` to its sources and terms.

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
| `asa.json`, `fpl.json`, `injuries.json`, `pass_checks.json` | MLS replication, FPL 2025–26 check, injuries and free transfers, Impect and Wyscout pass checks |
| `mid/`, `opta/mid/` | The same tables for midfielders who are not attacking midfielders (`SAMPLE=mid`) |
| `robustness.json` (and in `opta/`, `mid/`, `opta/mid/`) | Matching for regression to the mean, the denominator, flop or lost place, loans and promoted or relegated clubs, the second luck benchmark, Holm-adjusted slice tests, the predictor on every move |
| `rivals.json` (and in `opta/`) | The lost-place gap under each check, by fee band and with the no-fee audit, starts, survival bounds, Lee bounds, set pieces and open-play share, the flop line, club-season intervals, line-up position, name match, data minus luck, the predictor baseline, the test families |
| `flop_model_frozen.json` | The flop-or-lost-place model frozen on 3 November 2026: features, scaling, coefficients |
| `predictions_2025_26.csv` | Its predictions for 80 moves into 2025–26, committed 19 minutes before they were scored, with the outcomes already on disk (not a prospective test; the commit message of 5845cab says otherwise and is wrong). Player names were removed on 6 November 2026; rows keep the Transfermarkt id |
| `frozen_score_2025_26.json` | The scoring of those predictions on lost places (Transfermarkt minutes), a labelled post-hoc rescoring on a cleaned test set, and a count of the summer 2026 transfer records |

## What you need to supply

Point `SOURCE_DATA` at a folder laid out like this:

```
$SOURCE_DATA/
  understat/shots.parquet              tidy Understat shots, 2014–15 to 15 Sep 2025
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
- **Licence:** Understat publishes no licence or terms of reuse. This repo ships only aggregates, for non-commercial research, and commercial use would need Understat's permission.

### Transfermarkt tables

- **Source:** [transfermarkt.com](https://www.transfermarkt.com), via [dcaribou/transfermarkt-datasets](https://github.com/dcaribou/transfermarkt-datasets). The project README links the current download location; the copy used here was built on 5 September 2026 and cannot be downloaded again, so the checksums below are the only way to tell whether another copy is the same.
- **Licence:** the mirror is tagged CC0. The underlying data is Transfermarkt's, whose terms restrict automated collection and commercial reuse. Treat it as research use only.

### StatsBomb open data

- **Source:** [statsbomb/open-data](https://github.com/statsbomb/open-data), 2015–16 Premier League, La Liga, Serie A and Ligue 1 (the Bundesliga file holds only Leverkusen and is left out).
- **Version:** `analysis/statsbomb.py` fetches commit `4b73468`, pinned on 6 November 2026. The cached copy behind the published side-study numbers was fetched earlier from `master` and was not re-checked against that commit.
- **Licence:** free for non-commercial research with attribution to StatsBomb. Raw data is not redistributed here.

### FBref/Opta shots

- **Source:** Opta xG as published by [FBref](https://fbref.com), which carried Opta data until January 2026 (the archive used here stops on 3 February 2025), archived in [JaseZiv/worldfootballR_data](https://github.com/JaseZiv/worldfootballR_data) (release `fb_match_shooting`, the `*_M_1st_match_shooting.csv` files). Big-5 from 2017–18, Portugal and the Eredivisie from 2018–19, to 3 February 2025 (19 January for Portugal and the Eredivisie).
- **Licence:** FBref's data is Opta's (Stats Perform), and FBref is governed by the [Sports Reference terms of use](https://www.sports-reference.com/termsofuse.html). This repo ships only aggregates, for non-commercial research, with credit to FBref and Opta; the raw files are not redistributed.

### Sources for the extra checks

- **American Soccer Analysis** API (MLS, 2013 on): CC BY-SA 4.0, credit ASA. Fetched by `analysis/asa.py` into `$SOURCE_DATA/asa/`.
- **Fantasy Premier League archive**, [vaastav/Fantasy-Premier-League](https://github.com/vaastav/Fantasy-Premier-League) (MIT): `merged_gw.csv`, `players_raw.csv`, `teams.csv` for 2023–24 to 2025–26 in `$SOURCE_DATA/fpl/<season>/`.
- **salimt/football-datasets** (Transfermarkt injuries; no licence stated, so research use only and never redistributed): `$SOURCE_DATA/salimt/`.
- **Impect open data**, Bundesliga 2023–24 ([ImpectAPI/open-data](https://github.com/ImpectAPI/open-data), commit `d412b35`): non-commercial, no redistribution, credit Impect with its logo. `$SOURCE_DATA/impect/`.
- **Wyscout public dataset**, Pappalardo et al. 2019 ([figshare](https://figshare.com/collections/Soccer_match_event_dataset/4415000), CC BY 4.0): 2017–18 Big-5 events and matches in `$SOURCE_DATA/wyscout/`.

## Raw input checksums

SHA-256 of the copies the full rebuilds used on 3 and 6 November 2026 (the same files both times). A different copy of a source will give slightly different numbers; these let you tell whether yours is the same.

| File | SHA-256 |
|---|---|
| `understat/bundesliga_shot_data.rds` | `7481d4eea7a32c261ae45711e735a074c23aa4530a181c7f3c490150e8639bee` |
| `understat/epl_shot_data.rds` | `c51e6661029a2b0f2b770bd9fc0a54da1913b303d6c6c908d11008f5c526ab60` |
| `understat/la_liga_shot_data.rds` | `1a3a80f5e42c797ad056cb38fa10ca7c27b11f90987ee1921347eeba0728a803` |
| `understat/ligue_1_shot_data.rds` | `bbc5bc4e6f0ffc94f01ec016e4df45dc6d53264f92c917e113c0c5b9ecdbc49a` |
| `understat/rfpl_shot_data.rds` | `5ce54bf53ec86195b034fee6caae5cb283e98f019c364634fdf983fd67719901` |
| `understat/serie_a_shot_data.rds` | `fb024cc8fc8aa72edf6b826629ffe1f36dc3f2e20645f3aade85a4f2ec36b559` |
| `understat/shots.parquet` | `94a22f7a4f5df891c97a9df0692dbb4d9a9d7f12cb91a816a0c683212c2fc4bf` |
| `transfermarkt/games.csv.gz` | `142561989017d379bcf9e72bad0b87e0996bae0e7b710ebb3def9255f464c741` |
| `transfermarkt/game_lineups.csv.gz` | `5e83d6fad28364aadfea608013700cf09990062eede1ad9ef189189b0af47ba2` |
| `transfermarkt/game_events.csv.gz` | `80eb3b2a85c780b2caaf1e8850c3d16de7f8b1240b53aaf415bdc56b641d7d68` |
| `transfermarkt/appearances.csv.gz` | `e096c2b158fc3d52c4550526c4d4850dd62f31007652f4bcae112eadb1646802` |
| `transfermarkt/players.csv.gz` | `d22e407981d5b51a79bf8ff59835729f3526f7dc3495a6d8ed2f852ed2e86403` |
| `transfermarkt/clubs.csv.gz` | `aa57ab56e87faffaea1e8697439a32caf10116d8f2f2dfb3a57193c0bb1d641b` |
| `transfermarkt/transfers.csv.gz` | `90326983daf7e6ac7aabdfe62b90936d9bf1dd2171e53dec75c3751eb1620a83` |
| `fbref/ENG_M_1st_match_shooting.csv` | `0c5f45b66629931e611e7a14f19c9954dd8fe77da4fbf88f66696f4e061e6f1e` |
| `fbref/ESP_M_1st_match_shooting.csv` | `9b5125111baf16181da8735276ba7911809bdd29d8d7068cbef4371e730dd3c2` |
| `fbref/FRA_M_1st_match_shooting.csv` | `c0dd30594ebe82531d4199ece128f68798f886e4bc5934c4a1b5f7ccca31e1e3` |
| `fbref/GER_M_1st_match_shooting.csv` | `8ba5d0a83cd0a89201cd4b723024e50a581ed69d6000399ee3fc11cda3b1cecd` |
| `fbref/ITA_M_1st_match_shooting.csv` | `2a3c0c95cfd3dc64744af51925477fb40f453dc05f1936c31f07e8ce35b838cb` |
| `fbref/NED_M_1st_match_shooting.csv` | `0436c6c67afa1025e88afb9088dbb1d836c7c92e84c4ec66109a80ad21934af9` |
| `fbref/POR_M_1st_match_shooting.csv` | `f62a34bfbc818ed953f2c829462a7366648b6593e95e6ef42019497057fce5be` |
| `asa/players.json` | `f1a56facf818ab305d81fecb71e273ab633bc05dbc178487eabc2cedddf0c729` |
| `asa/players_xgoals.json` | `a5c03c60a4c277d6c8d5c825cb7f8fc3565ef4f2d145bfaa157d5959ead6556d` |
| `asa/teams.json` | `0e353bf7eaeed41f6c08c07b4aeeb4c5b786d1e8dd7a6da5437c38a1de6fe14f` |
| `asa/teams_xgoals.json` | `acbc8c695430c2d81a521b9df4fe6839abae019e5fd8bfe5287205f2b76053bd` |
| `salimt/player_injuries_updated_20260929.csv` | `c622ed5684ec42e456ee23a9f5a78d61f74293d55e38882a7829ad71fb40d815` |
| `salimt/player_profiles.csv` | `7ef9afbacf97577d099f21a0ef0ea0d46381bd4806a119f095b9562762a20096` |
| `wyscout/events.zip` | `877e015b716ffdeea18f04418e3f24fed307ed03c37ff305cabe1f47c4822a45` |
| `wyscout/matches.zip` | `c8f92bb7533e5c127e043cee764c991b5c25b4f5e70a65be931baae0b1765ce9` |
| `fpl/2023-24/merged_gw.csv` | `e9c09c8856f1c86b4f920f46ddd5033af83409439dfda53be925df2a3e7c8a9e` |
| `fpl/2023-24/players_raw.csv` | `43d8cf5efb3d901f2499558c40b392b7f0ee22afe28030f36266ad29024c63d9` |
| `fpl/2023-24/teams.csv` | `7795f091ccea17fda0752cb07b935e1515b09a9d3f924147997cbf28139edd49` |
| `fpl/2024-25/merged_gw.csv` | `5bbbcba6353b4c72ad273adcc8e3aa451946a826564679788f45b1cb3325b84e` |
| `fpl/2024-25/players_raw.csv` | `75686051b265cbe7755ac71213ecaad21b26ee1cc46a8bafbba19c39ce894b05` |
| `fpl/2024-25/teams.csv` | `d10a6db8feca6db9e44a3ba50b15168396667ea387fee9235d6b211c7f598c3b` |
| `fpl/2025-26/merged_gw.csv` | `0d09f1f1cb1b5520ec8e2f25238aa652efe2a263d8ca7cb2b6538b27bf86727d` |
| `fpl/2025-26/players_raw.csv` | `412ce0172016f8f98f25177dc6de9f3cd2a8ec7a6135f9aa638d7fdee784d67b` |
| `fpl/2025-26/teams.csv` | `b29df099cb0ad25413e284e53116099b0e0496874f99743dbc0870d8241b46c5` |

Not checksummed: the StatsBomb files, which `analysis/statsbomb.py` downloads from statsbomb/open-data (commit `4b73468`) on first run, and the Impect files, a sparse clone of ImpectAPI/open-data at commit `d412b35943340d50867a48deddf64fb7b65c6191`.
