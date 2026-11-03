# Why do transfers fail? A look at usage rates in football

**When an attacker's output falls after a move, did he get worse, or did the move change his situation?**

**A move cuts an attacker's share of the ball by about 4–6%, leaves his output per 90 about where it was, and makes him about 12 points more likely to flop or lose his place.**

- **Share of the ball: −4.2% (95% interval −6.0% to −2.5%) on Understat, −6.4% (−8.4% to −4.4%) on Opta.** This is a mover's share of his team's shots and shot-assists while he is on the pitch, against players who stayed and had the same season before (same decile of share and of output per 90, same age band, same season).
- **Output per 90 barely moves: +1.2% (−1.9% to +4.4%) on Understat, −0.7% (−4.0% to +2.5%) on Opta.** The raw gap of +3.6% that suggested a better team makes up for the lost ball shrinks to about zero once movers are compared with stayers who had the same last season.
- **Playing time is the larger cost: 44% of movers flop or fall below 900 league minutes the next season, against 33% of stayers, +11.8 points after matching (+8.0 to +15.4); on Opta +14.0 points (+9.4 to +18.4).** A flop is output per 90 down by more than 25%.
- **Among regulars who keep their place, movers flop about as often as luck alone predicts on Understat (19% against 22%), and more often than stayers on Opta (+4.8 points after age, +0.5 to +9.6).**

**Method.** I compare 865 moves with 2,562 stays by attackers in the Big-5 (the top divisions of England, Spain, Italy, Germany and France), 2014–15 to 2024–25, each after a season of 900 league minutes; output is xG+xA per 90 minutes on the pitch (expected goals plus the expected goals of the shots he set up), and its log change is split into four parts that multiply to it.
**Limits.** It is observational and exploratory: nothing was pre-registered, it counts shots and shot-assists only, the four-part split is accounting, and clubs pick movers on things last season's numbers do not show. No betting, fantasy or player-prop market was tested, so nothing here is a trading signal.

![A move costs an attacker about 4% of his share of the ball, and his output per 90 barely changes](figures/fig0_what_a_move_does.png)

## Why it matters

- **A recruitment team should budget for a new attacker to see about 4–6% less of the ball, and treat his minutes as the main risk.** One mover in three falls below 900 league minutes the next season (31%, 27% to 33%), against one stayer in five (19%, 17% to 21%). A regular's first-season dip in xG+xA is mostly what luck produces, so one season is a weak reason to sell.
- **A player-props or anytime-scorer trader pricing a new signing off his shots per 90 at the old club would overstate his volume.** His own shots and shot-assists per 90 fall by 2.5% (−4.7% to −0.5%) against matched stayers, and the bigger risk to any over is that he plays fewer minutes. This has not been tested against a price: see [Limits](#limits).

## Status of tests

Nothing here was pre-registered: every test is exploratory, and the 2020–21 onwards window used to test the flop predictor existed when its inputs were chosen. The slice tests (age bands, fee bands, league path, buying clubs, and the predictor's AUC, the chance it ranks a random flop above a random non-flop) form a family of 11, and I give Holm-adjusted p-values for it (Holm controls the chance of any false positive in the family). On Understat only the predictor survives (p = 0.002, adjusted 0.022); the 26–28 age gap has p = 0.029, adjusted 0.29. On Opta the predictor (adjusted 0.005) and the league path (adjusted 0.009) survive. Full table in [Who flops](#who-flops-only-the-predictor-survives-the-multiple-testing-correction).

## Method

- **Sample.** Attackers (centre-forwards, wingers and attacking midfielders on Transfermarkt) with 900 league minutes and 20 shots or shot-assists in a season, followed by any league appearance the next season. A move is a change of club between the two seasons. 601 of the 865 movers and 2,075 of the 2,562 stayers also reach 900 minutes the next season; the four-part tests use those.
- **Usage.** His share of the ball is his shots and shot-assists as a share of his team's while he is on the pitch, with minutes measured match by match from Transfermarkt (a public transfer and line-up database) line-ups and substitutions. Understat (a public xG site) gives every shot and its assister.
- **Four parts.** Output per 90 = team actions per 90 while he is on × his share × team-mates' xG+xA per action × his xG+xA per action relative to team-mates. The log change is the sum of the four log changes. It is an identity, so credit can move between parts: his own actions sit inside the team's, and his quality is measured against team-mates'.
- **Matching for regression to the mean.** A regression of each change on a mover flag plus dummies for the decile of last season's share, the decile of last season's output per 90, age band and season; a second version reweights stayers to the movers' mix of cells. Intervals come from 2,000 bootstrap draws that resample whole players.
- **Second source.** Every test is rerun on Opta's xG (Stats Perform's event data, as published by FBref until January 2026) for the Big-5 plus Portugal and the Eredivisie, 2017–18 to 2024–25.

## Results

### A move costs about 4–6% of the ball, and about two fifths of that is fewer shots of his own

| Movers minus stayers | Understat, raw | Understat, matched | Opta, raw | Opta, matched |
|---|--:|--:|--:|--:|
| His share of the ball | −4.9% (−7.0% to −2.8%) | −4.2% (−6.0% to −2.5%) | −7.2% (−9.6% to −4.8%) | −6.4% (−8.4% to −4.4%) |
| His own shots and shot-assists per 90 | −1.9% (−4.3% to +0.2%) | −2.5% (−4.7% to −0.5%) | −3.3% (−6.0% to −0.5%) | −3.3% (−5.8% to −0.9%) |
| His team's actions per 90, without him | +4.0% (+2.1% to +6.0%) | +2.7% (+0.9% to +4.6%) | +5.6% (+3.2% to +7.8%) | +4.6% (+2.5% to +6.6%) |
| Output per 90 | +3.6% (+0.2% to +6.9%) | +1.2% (−1.9% to +4.4%) | +0.4% (−3.4% to +4.1%) | −0.7% (−4.0% to +2.5%) |
| Flop rate, points | +1.4 (−2.1 to +4.9) | +3.2 (−0.3 to +6.7) | +4.2 (−0.1 to +8.7) | +5.1 (+0.9 to +9.5) |

- **Regression to the mean moves the share gap only a little.** Movers' last seasons were not unusually big: their median share was 17.8% against 17.4% for stayers, and their median output per 90 was a little lower. The reweighted version gives −4.3% (−6.1% to −2.4%) on Understat and −6.6% (−8.9% to −4.3%) on Opta.
- **The share of the ball falls partly because the new team does more.** Share is his actions divided by the team's. On raw numbers his own actions per 90 fall by 1.9% and the team's rise by 2.9%, so about three of the 4.9 points come from the denominator. After matching, his own actions fall by 2.5%, which is the part a shots market would feel.
- **The better team is visible before the move.** The clubs movers join made 2.9% (1.2% to 4.4%) more shots and shot-assists per match the season before than the clubs they left (Opta 2.6%, 0.7% to 4.5%), and 54% (50% to 58%) of movers joined a club that made more. So "joins a better team" holds on information known on the day; how much of the extra output that buys is small once movers are matched.

### Playing time: a third of movers lose their place

| | Understat movers | Understat stayers | Opta movers | Opta stayers |
|---|--:|--:|--:|--:|
| Below 900 minutes the next season | 31% (27% to 33%) | 19% (17% to 21%) | 33% (29% to 37%) | 20% (18% to 22%) |
| Flop or below 900 minutes | 44% (41% to 47%) | 33% (32% to 35%) | 49% (45% to 52%) | 35% (33% to 38%) |
| Gap, matched | +11.8 points (+8.0 to +15.4) | | +14.0 points (+9.4 to +18.4) | |

- **This is the largest and clearest gap in the study, and the 900-minute floor in earlier versions hid it.** It survives matching on last season, age adjustment (+11.8 points, +7.9 to +15.7) and both sources. Players with no league minutes at all the next season are not in the data, for movers or stayers.

### Among regulars, flops look like luck on Understat and less so on Opta

Picking moves by a big fall also picks bad luck, so I measured how much luck alone produces. For each pair of seasons I kept the real change of team and role, fixed the player's quality against his team-mates, and redrew his chance quality from his own shots, 200 times. A second benchmark also redraws his share of the ball from his own pooled share, so both his role and his quality are fixed.

| | Flop rate, data | Luck only | Luck only, share redrawn too | Player's part of a flop, data | Player's part, luck only |
|---|--:|--:|--:|--:|--:|
| Moved club | 19% (16% to 22%) | 22% (20% to 24%) | 20% (18% to 23%) | 39% | 33% (28% to 38%) |
| Stayed | 18% (16% to 19%) | 19% (17% to 20%) | 19% (18% to 21%) | 42% | 39% (36% to 41%) |

- **On Understat the movers' flop rate sits below both luck bands.** The benchmarks run about a point high on stayers, so they cannot detect a real rise of 1 to 3 points in movers' flop rate.
- **The player's own part of a flop is above the luck band (39% against 28% to 38%), so some real change in quality shows through.** About 69% (60% to 79%) of the spread in a mover's change of quality against team-mates is what sampling noise alone would give.
- **On Opta, movers flop 24% (20% to 28%) of the time against 25% from luck, and 4.8 points more than stayers after age (+0.5 to +9.6).** Losing the ball accounts for 28% (20% to 36%) of the average mover's flop on Understat, and 32% of movers' flops (24% to 41%) would not have been flops had his share held.

![Movers flop no more often than luck alone predicts](figures/fig1_flops_look_like_luck.png)

### Who flops: only the predictor survives the multiple-testing correction

<img src="figures/fig2_age.png" width="420" align="right" alt="Flop rate gap by age band, with 95% intervals">

| Test (Understat) | Estimate | p | Holm p |
|---|--:|--:|--:|
| Predictor, AUC above 0.5 | 0.62 (0.54 to 0.70) | 0.002 | 0.022 |
| Age 26–28, movers v stayers | +9.1 points (+0.8 to +17.3) | 0.029 | 0.29 |
| Fee under €10m v other movers | −7.4 points (−15.0 to +0.4) | 0.070 | 0.63 |
| Changed league v same league | +5.1 points (−1.4 to +11.6) | 0.12 | 0.92 |
| Buying clubs, early v late record | rank correlation −0.19 | 0.57 | 1.00 |

- **Age.** Movers aged 26 to 28 flop 28% (20% to 36%) of the time, against 19% (16% to 22%) for stayers of the same age. The other three bands' gaps all include zero.
- **League.** Players who move to a new league flop 22% (17% to 28%) of the time, against 17% (14% to 21%) for movers within the same league. On Opta, where the new league is often a step up from Portugal or the Eredivisie, the gap is +12.6 points (+4.8 to +19.6) and survives the correction.
- **Fee.** 20% of moves over €30m flop, 17% at €10–30m, 13% under €10m and 19% of free or loan moves, and every interval overlaps. 149 moves have no fee on record in Transfermarkt.
- **Buying club.** After shrinking each club's record towards the average, the spread between clubs is close to zero, and only 11 clubs made enough signings to compare 2015–19 with 2020–25 (rank correlation −0.19, p = 0.57).

<br clear="right">

### Can you see it coming? A little, and the frozen test is still out

- **On regulars who keep their place, a simple model gives an out-of-time AUC of 0.62 (0.54 to 0.70).** AUC is the chance it ranks a random flop above a random non-flop. It is a ridge-penalised logistic regression on six inputs known on the day (age, output per 90, quality against team-mates, share of the ball, share of minutes, change of league), trained on moves into 2015–16 to 2019–20 and tested on 2020–21 onwards (280 moves). The fifth of moves it rates riskiest flop 23% of the time, against 16% for the rest.
- **On every move known on the day, it does about as well: 0.64 (0.59 to 0.70) for "flop or lost his place" across 400 test moves.** Counting players who lost their place as non-flops gives 0.63 (0.55 to 0.71), and predicting lost places alone 0.67 (0.62 to 0.73).
- **Frozen on 3 November 2026 and scored once.** The model for "flop or lost his place", refitted on every move into 2015–16 to 2024–25, is in `data/flop_model_frozen.json`, and its predictions for 80 moves into 2025–26 are in `data/predictions_2025_26.csv`, committed before any 2025–26 outcome was read. No source here has 2025–26 Big-5 shots, so flops cannot be scored yet. Lost places can: 21 of the 80 fell below 900 league minutes, and the model ranks them with an AUC of 0.54 (0.40 to 0.68), no better than chance on this small sample.

## Robustness

- **Opta, seven leagues.** The usage cost holds and is larger (−7.2% raw, −6.4% matched). Output per 90 roughly breaks even (+0.4%, −3.4% to +4.1%). The predictor scores 0.70 (0.64 to 0.76) out of time. FBref's 2024–25 file stops about halfway through the season.
- **Midfielders who are not attacking midfielders pay about twice as much of the ball.** On Understat their share falls by 9.6% (−12.9% to −6.3%) raw and 7.0% (−10.2% to −3.9%) matched, and output per 90 falls by 5.2% (−10.6% to +0.2%). They flop 33% (28% to 37%) of the time against 24% (23% to 26%) for midfielders who stay, +9.5 points after age (+4.0 to +14.5), and 53% of them flop or lose their place against 39% of stayers (+16.1 points matched, +11.4 to +20.3). On Opta the share falls by 12.0% (−16.3% to −7.8%).
- **MLS (Major League Soccer), a league with no richer clubs to move up to.** From [American Soccer Analysis](https://www.americansocceranalysis.com) player-seasons, with share estimated from season totals, 153 attacker moves show the same usage cost: share falls by 3.8% (−7.3% to −0.4%), the new team does not create more chances (−0.6%, −3.0% to +2.0%), and movers flop more often than stayers (25% against 18%, a gap of +8.0 points, +0.8 to +15.7).
- **Loans, promoted and relegated clubs.** Transfermarkt does not flag loans, so a move counts as a likely loan when the player went back to the selling club within two seasons (109 moves). Without them the share gap is −5.3% (−7.5% to −3.1%). Without the 52 moves to promoted clubs and 114 from relegated clubs it is −4.6% (−6.8% to −2.4%).
- **The same player with more of the ball.** Following one player from one season to the next (2,693 pairs of seasons from 897 players), seasons where his share was 5 points higher came with chance quality 1.7% lower (95% interval −3.0% to −0.5%), with share and quality measured on different matches. The typical move cuts a player's share by about 0.8 points (4.9% of a 17% share), which on this slope is worth about 0.3% in chance quality.

![Five more points of the ball comes with chances about 1.7% worse](figures/fig3_within_player.png)

## Limits

- **Observational.** Clubs choose whom to buy and coaches choose a player's share; matching removes only what last season's numbers show.
- **Shots and shot-assists only.** Carries, pressing and build-up passes are invisible, so this suits attackers.
- **The four-part split is accounting.** His own actions count in the team's total, and his quality is measured against team-mates', so credit shifts between parts (the changes in his share and in team chances correlate −0.21; in his quality and team-mates' quality −0.30).
- **Selection after the move.** The four-part tests need 900 minutes after the move, which a third of movers do not reach; the flop-or-lost-place rate covers them, and players with no league minutes at all are missing from both groups.
- **Leagues and years.** Understat covers the Big-5 to 15 September 2025; the Opta rerun adds Portugal and the Eredivisie to early 2025. Moves from the Championship, Belgium or Brazil are invisible.
- **Name matching.** Understat and Transfermarkt are joined by names within each league-season, using club to settle clashes. All 20,002 fixtures match; a few players may be mismatched.
- **Not a trading signal.** No betting, fantasy or player-prop market was tested, and no costs or capacity are estimated; the out-of-time predictor test has 280 moves. The next test is whether prices already reflect the drop: Fantasy Premier League (FPL) prices and ownership for 2023–24 to 2025–26 are in the sources, and anytime-scorer or shots odds for a signing's first 5–10 matches would be the market test.

## What would change my mind

- If the frozen predictions do no better than chance on 2025–26 flops once shots are available, the predictor is noise.
- If a club's own tracking data showed movers keep their touches and lose only shots, the usage cost would be about who finishes moves, and his involvement would be unchanged.
- If the age gap at 26–28 disappears on new seasons, it was noise.

## Reproduce

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
./run_all.sh --quick                                # figures from the shipped tables, about 20 seconds
export SOURCE_DATA=/path/to/your/raw/data          # layout and checksums in data/DATA.md
./run_all.sh                                        # everything from raw data
```

The full run rebuilds every number and figure, runs the self-checks, and checks every number quoted in this README and in `docs/side_studies.md` against the tables in `data/` (`analysis/verify.py` prints PASS or FAIL for each). It takes about 20 minutes on a laptop, most of it reading the StatsBomb files. A second `./run_all.sh --quick` leaves `git status` clean: figures and the one-pager carry no timestamps. Python 3.14, versions pinned in `requirements.txt`.

## Data and licences

- **Shots and xG:** [Understat](https://understat.com) via [worldfootballR_data](https://github.com/JaseZiv/worldfootballR_data) (Jason Zivkovic), 2014–15 to 15 September 2025.
- **Opta xG, seven leagues:** [FBref](https://fbref.com) via worldfootballR_data, 2017–18 to early 2025.
- **Minutes, line-ups, substitutions, transfers:** [Transfermarkt](https://www.transfermarkt.com) via [transfermarkt-datasets](https://github.com/dcaribou/transfermarkt-datasets) (David Cariboo).
- **Side studies:** [StatsBomb open data](https://github.com/statsbomb/open-data), [American Soccer Analysis](https://www.americansocceranalysis.com) (CC BY-SA 4.0), the [FPL archive](https://github.com/vaastav/Fantasy-Premier-League) (MIT), [salimt/football-datasets](https://github.com/salimt/football-datasets), [Impect open data](https://github.com/ImpectAPI/open-data) and the [Wyscout public dataset](https://figshare.com/collections/Soccer_match_event_dataset/4415000) (CC BY 4.0).

None of the raw data is in this repository. `data/LICENSE.md` maps every committed file in `data/` to its source and terms; `data/asa.json` is released under CC BY-SA 4.0. Code is MIT-licensed. The other aggregates, the figures and the one-pager are for non-commercial use with credit to the sources.

<img src="figures/statsbomb_logo.png" width="160" alt="StatsBomb"> &nbsp; <img src="figures/impect_logo.svg" width="120" alt="Impect">

## About

Ben Rimmer, First-class BSc Economics, University of Exeter. benedict.p.rimmer@gmail.com

A one-page summary is in [`onepager.pdf`](onepager.pdf). Side studies (chemistry between team-mates, StatsBomb, Impect and Wyscout pass checks, Depay and Ronaldo, FPL 2025–26, injuries and free transfers) are in [`docs/side_studies.md`](docs/side_studies.md). The review method and scores are in [`LOOP.md`](LOOP.md).

<details>
<summary>Full method and tables</summary>

### Minutes on the pitch

Transfermarkt line-ups give the starters, and its match events give every substitution and red card, so each player has an on and off minute in every league match (573,444 player-matches in 20,002 games). Understat gives the minute of every shot. Together they say which shots and shot-assists his team made while he was on. The first version of this repo estimated this from season totals; the measured share correlates 0.95 with that estimate.

### The four parts, raw

An action is a shot or a shot-assist. Penalties and own goals are excluded. An assisted shot counts for both players, each credited with its xG. The transfer tests need 20 actions in each season as well as 900 minutes, which is why they have 601 moves and the within-player tests have 605.

| Part | Movers minus stayers | 95% interval |
|---|--:|--:|
| His share of the ball | −4.9% | −7.0% to −2.8% |
| Chances his team creates | +2.9% | +1.2% to +4.8% |
| Quality of team-mates' chances | +3.5% | +1.8% to +5.4% |
| His own quality against team-mates | +2.0% | −0.4% to +4.3% |
| Output per 90 | +3.6% | +0.2% to +6.9% |

*Differences in mean log change. Intervals from 2,000 bootstrap draws resampling whole players. Tables in `data/transfers.json`, `data/transfer_splits.csv` and, for the matched versions, `data/robustness.json`.*

Among flops, the player's part is 39% for movers and 42% for stayers. Across all seasons, measured as each part's share of the variance in output changes, it is 37% for movers and 41% for stayers.

### Why 900 minutes

I split each team's league matches into odd and even, measured each player on each half, and correlated the two (stepped up to a full season).

| League minutes | Seasons | Chance quality reliability | Usage reliability |
|---|--:|--:|--:|
| under 450 | 2,539 | 0.19 | 0.88 |
| 450 to 899 | 1,322 | 0.34 | 0.50 |
| 900 to 1,799 | 2,305 | 0.59 | 0.73 |
| 1,800 and over | 2,411 | 0.73 | 0.86 |

Below 900 minutes most of the variation in chance quality is noise.

### Within-player tests

Each pair of seasons is weighted by the precision of its change in quality, `1 / (1/actions₁ + 1/actions₂)`. Percentages are of the median chance quality (0.116 xG+xA per action), per 5 points of share. Full table in `data/within_slopes.csv`.

| Specification | Pairs | Per +5 points of share | 95% interval |
|---|--:|--:|--:|
| **Per 90, split-half (headline)** | 2,693 | **−1.7%** | **−3.0% to −0.5%** |
| Per 90, same matches | 2,693 | −2.5% | −4.1% to −0.9% |
| Per 90, against team-mates | 2,693 | −1.9% | −3.6% to −0.2% |
| Season share split-half, plus last season's quality | 2,693 | −2.0% | −4.0% to −0.2% |
| Season share, minutes held fixed | 2,693 | −3.5% | −5.9% to −1.1% |
| Season share, nothing held fixed | 2,693 | −0.3% | −1.5% to +0.9% |
| Per 90, same club both seasons | 2,088 | −1.9% | −3.8% to 0.0% |
| Per 90, changed club | 605 | −2.0% | −4.8% to +0.9% |
| Per 90, changed club, against new team-mates | 605 | −0.1% | −2.7% to +2.6% |

### The luck benchmarks

For each pair of seasons, the three situation parts stay as observed. The change in his quality against team-mates is replaced by pure sampling noise: his actions in each season are redrawn with replacement from his own pooled actions over both seasons, so his true quality is the same in both, and the noise is the log change in the mean. Flops are then selected and split exactly as in the data. 200 runs each for movers and stayers; draws in `data/noise_benchmark_draws_*.csv`. The first benchmark keeps the observed change in his share of the ball, so it ignores the negative link between share and quality within a season. The second redraws his action count in each season as binomial on his team's actions while he was on, at his pooled share, and redraws his quality with those counts (`analysis/robustness.py`).

### The flop predictor

A ridge-penalised logistic regression on six standardised inputs known on the day of the move: age, output per 90, quality against team-mates, share of the ball, share of minutes played, and whether the move changes league. Trained on moves where the first season starts in 2018 or earlier, tested once on the rest. The frozen version and how to score it are in `data/flop_model_frozen.json`; `analysis/score_frozen.py` scores it.

### Scripts

| Script | What it does |
|---|---|
| `analysis/crosswalk.py` | Joins Understat and Transfermarkt matches and players |
| `analysis/minutes.py` | On and off minutes for every player in every league match, and minutes together for every pair |
| `analysis/build_panel.py` | The player-season panel, in `data/work/` (gitignored) |
| `analysis/analyse.py` | Within-player tests, reliability, the usage curve |
| `analysis/transfers.py` | Movers against stayers, the luck benchmark, slices, the flop predictor |
| `analysis/robustness.py` | Matching for regression to the mean, the denominator, lost places, loans and promotion, the second luck benchmark, Holm, the frozen predictor |
| `analysis/score_frozen.py` | Scores the frozen 2025–26 predictions once |
| `analysis/chemistry.py` | Pair chemistry from shot assists |
| `analysis/statsbomb.py`, `analysis/sb_check.py` | StatsBomb 2015–16 checks |
| `analysis/fbref.py` | FBref/Opta shots for seven leagues, for the `SHOTS=opta` rerun |
| `analysis/figures.py` | Every figure and the one-pager |
| `analysis/verify.py` | Checks the README's and side studies' numbers against `data/` |

### The wider model

This repo is one question from a private transfer valuation model built on data that cannot be shared. That model asks how good a player is (price-blind), what he is worth to a given club, and what he will cost.

</details>
