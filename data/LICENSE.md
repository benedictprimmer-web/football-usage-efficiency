# Licences for the files in `data/`

Every committed file in `data/` is an aggregate or a small derived table; no raw third-party file is redistributed. Each row says which sources a file is built from and the terms that follow from them. Where sources mix, the strictest terms apply. Code in this repository is MIT-licensed (see `../LICENSE`); these terms cover the data files only.

## Sources and their terms

| Source | What it gives | Terms | Credit |
|---|---|---|---|
| Understat, via JaseZiv/worldfootballR_data | Big-5 shots with xG and assister, 2014–15 to 15 September 2025 | No open licence; the owner allows non-commercial use with attribution | Understat; Jason Zivkovic (worldfootballR_data) |
| FBref/Opta, via JaseZiv/worldfootballR_data | Shots with Opta xG, seven leagues, 2017–18 to early 2025 | Opta data belongs to Stats Perform; non-commercial research use with credit | FBref; Opta (Stats Perform) |
| Transfermarkt, via dcaribou/transfermarkt-datasets | Line-ups, substitutions, appearances, transfers, players, clubs | The mirror is tagged CC0; Transfermarkt's own terms restrict automated collection and commercial reuse, so research use only | Transfermarkt; David Cariboo |
| StatsBomb open data | 2015–16 events for four leagues | StatsBomb's open-data user agreement: free for research and non-commercial use with attribution and the StatsBomb logo | StatsBomb (logo in the README) |
| American Soccer Analysis (ASA) public API | MLS player and team seasons | CC BY-SA 4.0 | American Soccer Analysis |
| Fantasy Premier League archive, vaastav/Fantasy-Premier-League | Per-match Opta xG and xA, 2023–24 to 2025–26 | Repository MIT; the data comes from the Premier League's FPL service, whose terms bar commercial use | vaastav; Fantasy Premier League |
| salimt/football-datasets | Transfermarkt injury spells and profiles | No licence stated; Transfermarkt terms apply, research use only | salimt |
| Impect open data | Bundesliga 2023–24 events | Non-commercial use, no redistribution of the data, credit Impect with its logo | Impect (logo in the README) |
| Wyscout public dataset, Pappalardo et al. 2019 | Big-5 2017–18 events | CC BY 4.0 | Pappalardo et al. (2019), *Scientific Data* 6:236 |

## File by file

| File | Built from | Terms |
|---|---|---|
| `transfers.json`, `transfer_splits.csv`, `transfer_slices.csv`, `age_gaps.csv`, `buying_clubs.csv`, `noise_benchmark_draws_movers.csv`, `noise_benchmark_draws_stayers.csv` | Understat, Transfermarkt | Non-commercial, with credit |
| `within_slopes.csv`, `within_bins.csv`, `curve_bins.csv`, `reliability.csv`, `summary.json` | Understat, Transfermarkt | Non-commercial, with credit |
| `robustness.json`, `flop_model_frozen.json`, `predictions_2025_26.csv` | Understat, Transfermarkt | Non-commercial, with credit |
| `frozen_score_2025_26.json` | Transfermarkt | Research use, with credit |
| `case_studies.csv` | Understat, Transfermarkt (three players' season numbers) | Non-commercial, with credit |
| `chemistry.json`, `chemistry_dose.csv`, `chemistry_top_pairs.csv` | Understat, Transfermarkt | Non-commercial, with credit |
| `sb_check.json` | StatsBomb, Transfermarkt, Understat | Non-commercial, with credit to StatsBomb and its logo |
| `opta/*` (all files) | FBref/Opta, Transfermarkt | Non-commercial, with credit to FBref and Opta |
| `mid/*` (all files) | Understat, Transfermarkt | Non-commercial, with credit |
| `opta/mid/*` (all files) | FBref/Opta, Transfermarkt | Non-commercial, with credit to FBref and Opta |
| `asa.json` | American Soccer Analysis | **Released under CC BY-SA 4.0**, as the source requires: you may share and adapt it, with credit to American Soccer Analysis and this repository, under the same licence |
| `fpl.json` | Fantasy Premier League archive | Non-commercial, with credit |
| `injuries.json` | salimt/football-datasets, Transfermarkt, Understat | Research use, with credit |
| `pass_checks.json` | Impect, Wyscout | Non-commercial, with credit to Impect (and its logo) and to Pappalardo et al. 2019. It holds summary statistics only (growth rates, counts, intervals); no Impect event data is redistributed |
| `DATA.md`, `LICENSE.md` | This repository | MIT, with the code |

## Checked for redistribution limits

Impect bars redistribution of its data, and Transfermarkt and the FPL service bar commercial reuse. No committed file holds their raw records: `pass_checks.json` has only aggregate rates, and the Transfermarkt-derived files hold aggregates plus, for named players, season-level numbers, clubs and transfer dates. Nothing was removed on these grounds in round 1 of the review; if a source objects, the file goes.
