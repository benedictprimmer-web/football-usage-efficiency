# What a move costs an attacker: his place, and some of the ball

**When an attacker's output falls after a move, did he get worse, or did the move change his situation?**

**After a move between two Big-5 clubs, an attacker is 12 to 14 points more likely to flop or lose his place, his share of his team's shots and shot-assists falls by 4–6%, and if he keeps playing his output per 90 stays about level.**

- **Flop or lost place: +11.8 points (95% interval +8.0 to +15.4) on Understat, +14.0 (+9.4 to +18.4) on Opta.** 44% of movers flop or fall below 900 league minutes the next season, against 33% of stayers. Most of it is lost places: 31% of movers fall below 900 minutes, against 19% of stayers. A flop is output per 90 down by more than 25%.
- **Share of shots and shot-assists: −4.2% (−6.0% to −2.5%) on Understat, −6.4% (−8.4% to −4.4%) on Opta.** This is a relative change, about 0.8 of a point off a 17.8% share. In open play alone it is −2.6% (−4.4% to −0.7%) on Understat: the rest is set pieces he no longer takes or attacks.
- **Output per 90: +1.2% (−1.9% to +4.4%) on Understat, −0.7% (−4.0% to +2.5%) on Opta,** for the 601 of 865 movers who reach 900 minutes again.

**Method.** I compare 865 moves with 2,562 stays by attackers in the Big-5 (the top divisions of England, Spain, Italy, Germany and France), 2014–15 to 2024–25, each after a season of 900 league minutes. Output is xG+xA per 90 (expected goals plus the expected goals of the shots he set up) from Understat, a public xG site, and again from Opta, the data company whose xG FBref published. Movers are compared with stayers who had the same last season: same decile of share and of output per 90, same age band and season, in a regression.
**Limits.** It is observational, and nothing was pre-registered. Only moves between Big-5 clubs are in it: 845 of 4,272 qualifying seasons (20%) have no Big-5 row the next season, and counting all of them as lost places would widen the gap to +15.3 points. No betting, fantasy or player-prop market was tested, so nothing here is a trading signal.

<img src="figures/fig6_lost_place.png" width="49%" alt="A third of movers fall below 900 league minutes the next season, against a fifth of stayers"> <img src="figures/fig0_what_a_move_does.png" width="49%" alt="A move costs an attacker about 4% of his share of the ball, and his output per 90 barely changes">

## Why it matters

- **A recruitment team should treat minutes as the main risk in a new attacker.** One mover in three falls below 900 league minutes the next season (31%, 27% to 33%), against one stayer in five (19%, 17% to 21%), and the gap holds against stayers with the same share of their club's minutes last season.
- **The volume loss is small, and part of it is set pieces.** His own open-play shots and shot-assists per 90 do not fall on Understat (−0.3%, −2.5% to +1.8%); his set-piece actions per 90 fall by 11.9% (−17.1% to −6.3%), and his new team makes more of the open-play chances.
- **This is not a trade.** His shots per 90 fall 4.1% (−6.8% to −1.5%) against matched stayers on Understat. That is small next to the margin a bookmaker builds into a player-shots price, and a match-level prop settles after the line-ups are out, so the season-level minutes risk does not carry over to it. No price was tested.

## Inference

- **Primary family: eight tests, Holm-corrected.** The matched gaps in share of shots and shot-assists, in his own actions per 90, in output per 90 and in "flop or lost place", on each source. Holm controls the chance of any false positive in the family. The share and flop-or-lost-place gaps survive on both sources (each p below 0.0005, the bootstrap's floor; Holm-adjusted 0.004), and so does Opta's own-actions gap (adjusted 0.044). Understat's own-actions gap does not (adjusted 0.060), and neither output gap does (adjusted 0.888), as the headline expects.
- **Nothing was pre-registered, and one outcome was chosen after looking.** "Flop or lost place" was added in round 1 of the review, after a reviewer pointed out that the 900-minute floor hid lost places. Every result here is exploratory.
- **The secondary family: 11 slice tests (age bands, fee bands, league path, buying clubs, the predictor), also Holm-corrected.** On Understat only the predictor survives (p = 0.002, adjusted 0.022); the 26–28 age gap has p = 0.029, adjusted 0.29. On Opta the predictor (adjusted 0.005) and the league path (adjusted 0.009) survive.
- **Intervals resample whole players, 2,000 times.** Resampling whole buying club-seasons instead, since team-mates at a new club share its changes, gives −4.2% (−6.0% to −2.4%) for the share gap and +11.8 points (+8.0 to +15.6) for flop or lost place.

## Method

- **Sample.** Attackers (centre-forwards, wingers and attacking midfielders on Transfermarkt, a public transfer and line-up database) with 900 league minutes and 20 shots or shot-assists in a season, followed by any Big-5 league appearance the next season. A move is a change of club between the two seasons. 601 of the 865 movers and 2,075 of the 2,562 stayers also reach 900 minutes the next season; the four-part tests use those.
- **Usage.** His share is his shots and shot-assists as a share of his team's while he is on the pitch, with minutes measured match by match from Transfermarkt line-ups and substitutions. Understat gives every shot, its assister and whether it came from open play or a set piece. Penalties are left out.
- **Four parts.** Output per 90 = team actions per 90 while he is on × his share × team-mates' xG+xA per action × his xG+xA per action relative to team-mates. Each change is a log change, close to a percentage change for small moves, so the four parts add up to the change in output. The split is accounting: his own actions sit inside the team's, and his quality is measured against team-mates', so credit can move between parts.
- **Matching for regression to the mean.** A regression of each change on a mover flag plus dummies for the decile of last season's share, the decile of last season's output per 90, age band and season. A second version reweights stayers to the movers' mix of cells.
- **Second source.** Every test is rerun on Opta's xG for the Big-5 plus Portugal and the Eredivisie, 2017–18 to 3 February 2025.

## Results

### A move costs 4–6% of his share, and set pieces and a busier new team explain most of it

| Movers minus stayers | Understat, raw | Understat, matched | Opta, raw | Opta, matched |
|---|--:|--:|--:|--:|
| His share of the ball | −4.9% (−7.0% to −2.8%) | −4.2% (−6.0% to −2.5%) | −7.2% (−9.6% to −4.8%) | −6.4% (−8.4% to −4.4%) |
| His own shots and shot-assists per 90 | −1.9% (−4.3% to +0.2%) | −2.5% (−4.7% to −0.5%) | −3.3% (−6.0% to −0.5%) | −3.3% (−5.8% to −0.9%) |
| His team's actions per 90, without him | +4.0% (+2.1% to +6.0%) | +2.7% (+0.9% to +4.6%) | +5.6% (+3.2% to +7.8%) | +4.6% (+2.5% to +6.6%) |
| Output per 90 | +3.6% (+0.2% to +6.9%) | +1.2% (−1.9% to +4.4%) | +0.4% (−3.4% to +4.1%) | −0.7% (−4.0% to +2.5%) |
| Flop rate, points | +1.4 (−2.1 to +4.9) | +3.2 (−0.3 to +6.7) | +4.2 (−0.1 to +8.7) | +5.1 (+0.9 to +9.5) |

"His share of the ball" means his share of the team's shots and shot-assists while he is on, not possession or touches.

- **About three fifths of the matched share fall is fewer actions of his own, and two fifths is a team that does more.** His own actions per 90 fall by 2.5% against a share fall of 4.2%. Reweighting instead of regression gives −4.3% (−6.1% to −2.4%) on Understat and −6.6% (−8.9% to −4.3%) on Opta.
- **His own fall is set pieces.** Matched, on Understat, his open-play actions per 90 change by −0.3% (−2.5% to +1.8%) and his set-piece actions by −11.9% (−17.1% to −6.3%). His shots fall by 4.1% (−6.8% to −1.5%) and his shot-assists do not change (+0.1%, −3.3% to +3.4%). Opta labels only direct free kicks as set pieces, so it cannot make this split.
- **His share of open play still falls, because the new team makes more.** Measured match by match on open-play actions only, his share falls by 2.6% (−4.4% to −0.7%) on Understat, while the team's open-play actions per 90 with him on rise by 2.3% (+0.3% to +4.3%).
- **The better team is visible before the move.** The clubs movers join made 2.9% (1.2% to 4.4%) more shots and shot-assists per match the season before than the clubs they left (Opta 2.6%, 0.7% to 4.5%). That is a small step up: 54% (50% to 58%) of movers joined a club that made more, close to an even split.

### Playing time: a third of movers lose their place

| | Understat movers | Understat stayers | Opta movers | Opta stayers |
|---|--:|--:|--:|--:|
| Below 900 minutes the next season | 31% (27% to 33%) | 19% (17% to 21%) | 33% (29% to 37%) | 20% (18% to 22%) |
| Flop or below 900 minutes | 44% (41% to 47%) | 33% (32% to 35%) | 49% (45% to 52%) | 35% (33% to 38%) |
| Gap, matched | +11.8 points (+8.0 to +15.4) | | +14.0 points (+9.4 to +18.4) | |

- **This is the largest and clearest gap in the study.** It survives matching on last season, age adjustment (+11.8 points, +7.9 to +15.7) and both sources. Below 900 minutes alone, the matched gap is +11.4 points (+7.7 to +14.7) on Understat.
- **It holds under the checks the share gap gets** (Understat, matched, flop or lost place):

| Check | Gap, points |
|---|--:|
| Also matched on last season's share of his club's minutes | +10.8 (+7.0 to +14.4) |
| Without moves to promoted or from relegated clubs | +10.0 (+5.6 to +14.3) |
| Without likely loans | +10.7 (+6.6 to +14.6) |
| Without either | +8.7 (+4.1 to +13.3) |
| Floor at 450 minutes, minutes only | +3.8 (+1.3 to +6.2) |
| Floor at 1,350 minutes, minutes only | +14.1 (+10.1 to +18.1) |
| Every season with no Big-5 row next season counted as lost | +15.3 (+11.8 to +18.6) |

- **The players who drop out make the gap bigger, not smaller.** 845 of 4,272 qualifying seasons have no Big-5 row the next season: sold abroad or down a division, relegated with the club, injured all season, or not matched. 315 of them show a Transfermarkt transfer away from his club.

### Among regulars, the luck benchmark cannot tell movers from luck

Picking moves by a big fall also picks bad luck, so I measured how much luck alone produces. For each pair of seasons I kept the real change of team and role, fixed the player's quality against his team-mates, and redrew his chance quality from his own shots, 200 times. A second benchmark also redraws his share of the ball from his own pooled share, so both his role and his quality are fixed.

| | Flop rate, data | Luck only | Luck only, share redrawn too | Player's part of a flop, data | Player's part, luck only |
|---|--:|--:|--:|--:|--:|
| Moved club | 19% (16% to 22%) | 22% (20% to 24%) | 20% (18% to 23%) | 39% (30% to 48%) | 33% (28% to 38%) |
| Stayed | 18% (16% to 19%) | 19% (17% to 20%) | 19% (18% to 21%) | 42% (38% to 47%) | 39% (36% to 41%) |

- **Data minus luck: −2.7 points (−6.7 to +1.0) for movers on Understat, −1.3 (−5.8 to +3.0) on Opta.** This includes the data's own resampling uncertainty. The benchmark runs about a point high on stayers too, so it cannot detect a real rise of 1 to 3 points in movers' flop rate.
- **The player's own part of a flop is within the luck band.** 39% (30% to 48%) in the data, against 33% (28% to 38%) from luck. About 69% (60% to 79%) of the spread in a mover's change of quality against team-mates is what sampling noise alone would give.
- **Against stayers, movers flop a little more often.** Matched, the gap is +3.2 points (−0.3 to +6.7) on Understat and +5.1 (+0.9 to +9.5) on Opta. With the flop line at a 15% or a 35% fall instead of 25%, the Understat gap is +2.2 (−2.0 to +6.3) and +3.7 (+0.9 to +6.3).
- **Losing the ball accounts for 28% (20% to 36%) of the average mover's flop on Understat,** and 32% of movers' flops (24% to 41%) would not have been flops had his share held.

![Movers' flop rate sits inside a luck benchmark too noisy to see a small rise](figures/fig1_flops_look_like_luck.png)

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
- **Fee.** Moves over €30m flop 20% (11% to 28%) of the time, €10–30m moves 17% (10% to 25%), moves under €10m 13% (6% to 20%), and free or loan moves 19% (14% to 25%); every interval overlaps. 149 moves have no fee on record in Transfermarkt.
- **Buying club.** After shrinking each club's record towards the average, the spread between clubs is close to zero, and only 11 clubs made enough signings to compare 2015–19 with 2020–25 (rank correlation −0.19, p = 0.57).

<br clear="right">

### Can you see it coming? A little, and no prospective test has been run

- **On regulars who keep their place, a simple model gives a pseudo-out-of-time AUC of 0.62 (0.54 to 0.70).** AUC is the chance it ranks a random flop above a random non-flop, where 0.5 is a coin toss. The model is a logistic regression, shrunk towards zero to avoid overfitting, on six inputs known on the day (age, output per 90, quality against team-mates, share of the ball, share of minutes, change of league). It is trained on moves into 2015–16 to 2019–20 and tested on 2020–21 onwards (280 moves). "Pseudo" because the test seasons existed when the inputs were chosen.
- **On every move known on the day, it does about as well: 0.64 (0.59 to 0.70) for "flop or lost his place" across 400 test moves.** Counting players who lost their place as non-flops gives 0.63 (0.55 to 0.71), and predicting lost places alone 0.67 (0.62 to 0.73). An AUC in the low 0.60s on a few hundred moves has no stated use.
- **The 2025–26 "frozen" test is not prospective.** The model in `data/flop_model_frozen.json` and its predictions for 80 moves into 2025–26 in `data/predictions_2025_26.csv` were committed at 20:50 on 3 November 2026 and scored 19 minutes later. The Transfermarkt minutes for 2025–26 were already on disk, and 2025–26 Premier League outcomes from FPL had been committed 30 minutes before the freeze. On lost places, 21 of the 80 fell below 900 league minutes and the model ranks them with an AUC of 0.54 (0.40 to 0.68), no better than chance. Round 2 of the review found two buying clubs outside the Big-5 and 8 January moves in the test set; without them, and counting minutes at the new club only, it is 0.52 (0.37 to 0.68) on 70 moves. Flops cannot be scored, because no source here has 2025–26 Understat shots.
- **A prospective test needs a newer Transfermarkt copy.** Of the 2,850 transfers this copy dates 1 June to 1 September 2026, 2,799 are dated 30 June or 1 July, when loans end and contracts turn over, so the summer 2026 window is missing. The next step is to freeze predictions for summer 2026 moves as soon as a copy with that window exists, before any 2026–27 minutes are in it.

## Robustness

- **Opta, seven leagues.** The usage cost holds and is larger (−7.2% raw, −6.4% matched), and in open play it is −6.3% (−8.4% to −4.2%). Output per 90 roughly breaks even (+0.4%, −3.4% to +4.1%). The predictor scores 0.70 (0.64 to 0.76) out of time. FBref's 2024–25 files stop on 3 February 2025.
- **Position on the team sheet.** Transfermarkt gives one position per player, as of 2026. Keeping only pairs where his starting line-up position was an attacking one in both seasons (91% of pairs), the share gap is −4.2% (−5.9% to −2.6%).
- **Name matching.** Understat and Transfermarkt are joined by names within each league-season, using club to settle clashes. 93% of Understat's non-penalty shots belong to a player matched to Transfermarkt; the worst league-season is La Liga 2017–18, at 85%.
- **Midfielders who are not attacking midfielders lose about 1.6 times as much of the ball.** On Understat their share falls by 9.6% (−12.9% to −6.3%) raw and 7.0% (−10.2% to −3.9%) matched, and output per 90 falls by 5.2% (−10.6% to +0.2%). They flop 33% (28% to 37%) of the time against 24% (23% to 26%) for midfielders who stay, +9.5 points after age (+4.0 to +14.5), and 53% of them flop or lose their place against 39% of stayers (+16.1 points matched, +11.4 to +20.3). On Opta the share falls by 12.0% (−16.3% to −7.8%). The sample uses today's Transfermarkt position, so a winger later moved back into midfield counts as a midfielder in every season.
- **MLS (Major League Soccer), a league outside Europe with a salary cap.** From [American Soccer Analysis](https://www.americansocceranalysis.com) player-seasons, with share estimated from season totals rather than minutes on the pitch, 153 attacker moves show the same usage cost: share falls by 3.8% (−7.3% to −0.4%), the new team does not create more chances (−0.6%, −3.0% to +2.0%), and movers flop more often than stayers (25% against 18%, a gap of +8.0 points, +0.8 to +15.7).
- **Loans, promoted and relegated clubs.** Transfermarkt does not flag loans, so a move counts as a likely loan when the player went back to the selling club within two seasons (109 moves). Without them the share gap is −5.3% (−7.5% to −3.1%). Without the 52 moves to promoted clubs and 114 from relegated clubs it is −4.6% (−6.8% to −2.4%).
- **The same player with more of the ball.** Following one player from one season to the next (2,693 pairs of seasons from 897 players), seasons where his share was 5 points higher came with chance quality 1.7% lower (95% interval −3.0% to −0.5%), with share and quality measured on different matches. The typical move cuts a player's share by about 0.8 points (4.9% of a 17% share), which on this slope is worth about 0.3% in chance quality. Among movers measured against their new team-mates the slope is −0.1% (−2.7% to +2.6%).

![Five more points of the ball comes with chances about 1.7% worse](figures/fig3_within_player.png)

## Limits

- **Observational.** Clubs choose whom to buy and coaches choose a player's share; matching removes only what last season's numbers show.
- **Only moves between Big-5 clubs.** Players sold to the Championship, Turkey, Saudi Arabia or MLS have no Big-5 row the next season and drop out, as do stayers relegated with their club. The bound above says this makes the lost-place gap conservative.
- **January moves are not in it.** A season counts only when one club holds 80% or more of a player's actions, so a player who changed club mid-season drops out of that season.
- **Shots and shot-assists only.** Carries, pressing and build-up passes are invisible, so this suits attackers.
- **The four-part split is accounting.** His own actions count in the team's total, and his quality is measured against team-mates', so credit shifts between parts, and the parts' changes correlate.
- **Leagues and years.** Understat covers the Big-5 to 15 September 2025; the Opta rerun adds Portugal and the Eredivisie to 3 February 2025. Moves from the Championship, Belgium or Brazil are invisible.
- **Not a trading signal.** No betting, fantasy or player-prop market was tested, and no costs or capacity are estimated. The next test is whether prices already reflect the drop: Fantasy Premier League (FPL) prices and ownership for 2023–24 to 2025–26 are in the sources, and anytime-scorer or shots odds for a signing's first 5–10 matches would be the market test.

## What would change my mind

- If a club's own tracking data showed movers keep their touches and lose only shots, the usage cost would be about who finishes moves, and his involvement would be unchanged.
- If the lost-place gap disappears for moves to clubs that paid a fee and gave him a long contract, it is about loans and squad fillers, not the move.
- If predictions frozen before 2026–27 do no better than chance on lost places, the predictor is noise.

## Reproduce

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
./run_all.sh --quick                                # figures from the shipped tables, about 30 seconds
export SOURCE_DATA=/path/to/your/raw/data          # layout and checksums in data/DATA.md
./run_all.sh                                        # everything from raw data
```

The full run rebuilds every number and figure, runs the self-checks, and checks every number quoted in this README and in `docs/side_studies.md` against the tables in `data/` (`analysis/verify.py` prints PASS or FAIL for each). It takes about 30 minutes on a laptop, most of it the StatsBomb files and the bootstraps. On 6 November 2026 a full run from the raw files reproduced every committed table byte for byte, once a bug was fixed that let the midfielder run overwrite the attackers' season pairs. A second `./run_all.sh --quick` leaves `git status` clean: figures and the one-pager carry no timestamps. Python 3.14, versions pinned in `requirements.txt`.

## Data and licences

- **Shots and xG:** [Understat](https://understat.com) via [worldfootballR_data](https://github.com/JaseZiv/worldfootballR_data) (Jason Zivkovic), 2014–15 to 15 September 2025.
- **Opta xG, seven leagues:** [FBref](https://fbref.com) via worldfootballR_data, 2017–18 to 3 February 2025.
- **Minutes, line-ups, substitutions, transfers:** [Transfermarkt](https://www.transfermarkt.com) via [transfermarkt-datasets](https://github.com/dcaribou/transfermarkt-datasets) (David Cariboo).
- **Side studies:** [StatsBomb open data](https://github.com/statsbomb/open-data), [American Soccer Analysis](https://www.americansocceranalysis.com) (CC BY-SA 4.0), the [FPL archive](https://github.com/vaastav/Fantasy-Premier-League) (MIT), [salimt/football-datasets](https://github.com/salimt/football-datasets), [Impect open data](https://github.com/ImpectAPI/open-data) and the [Wyscout public dataset](https://figshare.com/collections/Soccer_match_event_dataset/4415000) (CC BY 4.0).

None of the raw data is in this repository. `data/LICENSE.md` maps every committed file in `data/` to its source and terms; `data/asa.json` is released under CC BY-SA 4.0. Code is MIT-licensed. The other aggregates, the figures and the one-pager are for non-commercial use with credit to the sources, whose own terms apply.

<img src="figures/statsbomb_logo.png" width="160" alt="StatsBomb"> &nbsp; <img src="figures/impect_logo.svg" width="120" alt="Impect">

## About

Ben Rimmer, First-class BSc Economics, University of Exeter. benedict.p.rimmer@gmail.com

A one-page summary is in [`onepager.pdf`](onepager.pdf), drawn from the same tables. Side studies (chemistry between team-mates, StatsBomb, Impect and Wyscout pass checks, Depay and Ronaldo, FPL 2025–26, injuries and free transfers) are in [`docs/side_studies.md`](docs/side_studies.md). The review method and scores are in [`LOOP.md`](LOOP.md).

<details>
<summary>Full method and tables</summary>

### Minutes on the pitch

Transfermarkt line-ups give the starters, and its match events give every substitution and red card, so each player has an on and off minute in every league match (573,444 player-matches in 20,002 games). Understat gives the minute of every shot. Together they say which shots and shot-assists his team made while he was on.

### The four parts, raw

An action is a shot or a shot-assist. Penalties and own goals are excluded. An assisted shot counts for both players, each credited with its xG. The transfer tests need 20 actions in each season as well as 900 minutes, which is why they have 601 moves and the within-player tests have 605.

| Part | Movers minus stayers | 95% interval |
|---|--:|--:|
| His share of the ball | −4.9% | −7.0% to −2.8% |
| Chances his team creates | +2.9% | +1.2% to +4.8% |
| Quality of team-mates' chances | +3.5% | +1.8% to +5.4% |
| His own quality against team-mates | +2.0% | −0.4% to +4.3% |
| Output per 90 | +3.6% | +0.2% to +6.9% |

*Differences in mean log change. Intervals from 2,000 bootstrap draws resampling whole players. Tables in `data/transfers.json`, `data/transfer_splits.csv` and, for the matched versions and the round 2 checks, `data/robustness.json` and `data/rivals.json`.*

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

Each pair of seasons is weighted by the precision of its change in quality, `1 / (1/actions₁ + 1/actions₂)`. Percentages are of the median chance quality (0.116 xG+xA per action), per 5 points of share. The split-half version is the headline because share and quality come from different matches, so a lucky match cannot raise both. Full table in `data/within_slopes.csv`.

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

For each pair of seasons, the three situation parts stay as observed. The change in his quality against team-mates is replaced by pure sampling noise: his actions in each season are redrawn with replacement from his own pooled actions over both seasons, so his true quality is the same in both, and the noise is the log change in the mean. Flops are then selected and split exactly as in the data. 200 runs each for movers and stayers; draws in `data/noise_benchmark_draws_*.csv`. The first benchmark keeps the observed change in his share of the ball, so it ignores the negative link between share and quality within a season. The second redraws his action count in each season as binomial on his team's actions while he was on, at his pooled share, and redraws his quality with those counts (`analysis/robustness.py`). "Data minus luck" pairs a bootstrap draw of the data with a random benchmark run, 2,000 times (`analysis/rivals.py`).

### The flop predictor

A ridge-penalised logistic regression on six standardised inputs known on the day of the move: age, output per 90, quality against team-mates, share of the ball, share of minutes played, and whether the move changes league. Trained on moves where the first season starts in 2018 or earlier, tested once on the rest. The frozen version and how to score it are in `data/flop_model_frozen.json`; `analysis/score_frozen.py` scores it. A rebuild never rewrites the frozen files; it only checks that it would produce the same predictions.

### Scripts

| Script | What it does |
|---|---|
| `analysis/crosswalk.py` | Joins Understat and Transfermarkt matches and players |
| `analysis/minutes.py` | On and off minutes for every player in every league match, and minutes together for every pair |
| `analysis/build_panel.py` | The player-season panel, in `data/work/` (gitignored) |
| `analysis/analyse.py` | Within-player tests, reliability, the usage curve |
| `analysis/transfers.py` | Movers against stayers, the luck benchmark, slices, the flop predictor |
| `analysis/robustness.py` | Matching for regression to the mean, the denominator, lost places, loans and promotion, the second luck benchmark, Holm, the frozen predictor |
| `analysis/rivals.py` | The lost-place checks, survival, set pieces and open play, the flop line, club-season intervals, line-up position, name match, data minus luck, the primary family |
| `analysis/score_frozen.py` | Scores the frozen 2025–26 predictions |
| `analysis/chemistry.py` | Pair chemistry from shot assists |
| `analysis/statsbomb.py`, `analysis/sb_check.py` | StatsBomb 2015–16 checks |
| `analysis/fbref.py` | FBref/Opta shots for seven leagues, for the `SHOTS=opta` rerun |
| `analysis/figures.py` | Every figure and the one-pager |
| `analysis/verify.py` | Checks the README's and side studies' numbers against `data/` |

</details>
