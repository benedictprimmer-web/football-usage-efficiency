# Data

No raw third-party data is in this repository. This file says where each source comes from, what licence it carries, and where the scripts expect to find it.

## What is here

| File | What it holds |
|---|---|
| `curve_bins.csv` | Efficiency by usage-share bin (and by on-pitch usage), with 95% intervals. Aggregates only. |
| `within_slopes.csv` | Within-player slopes under each specification, with 95% intervals. |
| `within_bins.csv` | Season-to-season changes, binned into tenths, for figure 3. |
| `reliability.csv` | Split-half reliability of efficiency and usage by minutes band. |
| `summary.json` | Sample sizes and the headline numbers quoted in the README. |
| `case_studies.csv` | Season-level usage, minutes share and efficiency for Depay, Martial and Ronaldo. Derived statistics, no market values. |

## What you need to supply

Point `SOURCE_DATA` at a folder laid out like this:

```
$SOURCE_DATA/
  understat/shots.parquet          tidy Understat shots, 2014-15 to 4 Jan 2025
  transfermarkt/players.csv.gz     positions
  transfermarkt/appearances.csv.gz league minutes
  transfermarkt/games.csv.gz       season and date of each match
  crosswalk/players.csv            Understat player id -> Transfermarkt player id
```

### Understat shots

- **Source:** [understat.com](https://understat.com), via the static `.rds` archive in [JaseZiv/worldfootballR_data](https://github.com/JaseZiv/worldfootballR_data) (`data/understat_shots/`), Big-5 leagues plus the Russian Premier League.
- **How:** `src/usage_model/understat.py` downloads the six files and writes `shots.parquet` (`pip install rdata`, then `PYTHONPATH=src python -c "from usage_model.understat import read_shots; read_shots()"`). Copy the result to `$SOURCE_DATA/understat/`.
- **Licence:** Understat publishes no open licence. The owner has said the data is free for non-commercial use with attribution. Commercial use needs Understat's permission. The archive's own licence covers its code and packaging only.

### Transfermarkt tables

- **Source:** [transfermarkt.com](https://www.transfermarkt.com), via [dcaribou/transfermarkt-datasets](https://github.com/dcaribou/transfermarkt-datasets) (also on Kaggle as `davidcariboo/player-scores`). The project README links the current download location for `players`, `appearances` and `games`.
- **Licence:** the mirror is tagged CC0. The underlying data is Transfermarkt's, and Transfermarkt's terms restrict automated collection and commercial reuse. Treat it as research use only.

### Player crosswalk

- **What:** one row per Understat player matched to a Transfermarkt id (`us_player_id`, `tm_player_id`). The analysis reads only those two columns.
- **How:** built in the private repo by matching normalised names within each league-season, using club to break ties, then taking the Transfermarkt id that wins the most seasons. About 6,400 players match. It is not shipped because it is derived from both sources above; the method is simple to rebuild.

## Data not used here

The wider model also uses StatsBomb open data (non-commercial licence, attribution required) and a frozen FBref/Opta snapshot (proprietary, removed from FBref in January 2025). Neither feeds any number in this repository.
