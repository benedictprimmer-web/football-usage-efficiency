# An attacker after a move: fewer starts, a little less of the ball

**When an attacker's output falls after a move, did he get worse, or did the move change his situation?**

**After a move between two Big-5 clubs, an attacker is about 12 points more likely to flop or lose his place, almost all of it in moves where no fee was recorded; his share of his team's shots and shot-assists is about 4% lower; and if he keeps playing, his output per 90 is about where it was.**

- **Flop or lost place: +11.7 points (95% interval +7.9 to +15.4).** 44% of movers flop or fall below 900 league minutes the next season, against 33% of stayers with the same last season. A flop is output per 90 down by more than 25%. Where a fee was paid the gap is +1.8 points (−3.8 to +7.4); after free or loan moves it is +9.5, and where Transfermarkt has no fee, +25.2.
- **Starts: 41% of his new club's first 10 league matches, against 56% for stayers,** a matched gap of −14.2 points (−16.8 to −11.6).
- **Share of shots and shot-assists: −4.1% (−5.8% to −2.4%),** a relative change of about 0.7 of a point off a 16.9% share. In open play alone it is −2.4% (−4.2% to −0.6%); the rest is set pieces.
- **Output per 90: +1.3% (−1.9% to +4.4%)** for the 601 of 865 movers who reach 900 minutes again. Movers keep their place less often, and bounds for that selection run from −4.9% to +12.1%, so this is not evidence that output holds for every mover.

**Method.** 865 moves and 2,562 stays by attackers in the Big-5 (the top divisions of England, Spain, Italy, Germany and France), 2014–15 to 2024–25, each after a season of 900 league minutes. Output is xG+xA per 90 (expected goals plus the expected goals of the shots he set up) from Understat, a public xG site. Movers are compared with stayers who had the same last season (decile of share and of output per 90, age band, season) in a regression. Opta's xG, as FBref published it, is a sensitivity check: it shares Transfermarkt's minutes and most seasons, so it is not an independent replication.
**Limits.** It is observational, and nothing was pre-registered: clubs may sell players they no longer plan to pick. Only moves between Big-5 clubs are in it, and how the 845 seasons with no Big-5 row next season are counted moves the gap from +5.7 to +15.3 points. No price was tested, so nothing here is a trading signal.

<img src="figures/fig6_lost_place.png" width="49%" alt="A third of movers fall below 900 league minutes the next season, against a fifth of stayers"> <img src="figures/fig0_what_a_move_does.png" width="49%" alt="A mover who keeps his place has about 4% less of the ball, and the same output per 90">

## At a glance

| Claim (Understat, matched) | Estimate | Only players who kept 900 minutes? | Survives Holm? | Outcome chosen before looking? |
|---|--:|---|---|---|
| Flop or lost place | +11.7 points (+7.9 to +15.4) | No | Yes | No |
| Starts in first 10 matches | −14.2 points (−16.8 to −11.6) | No | Not in a family | No |
| Share of shots and shot-assists | −4.1% (−5.8% to −2.4%) | Yes | Yes | Yes |
| Own shots and shot-assists per 90 | −2.6% (−4.8% to −0.6%) | Yes | Yes | Yes |
| Output per 90 | +1.3% (−1.9% to +4.4%) | Yes | No | Yes |

## Why it matters

- **A recruitment team should plan for fewer starts, and should read a free or loan signing's minutes as the main risk.** One mover in three falls below 900 league minutes the next season (30%, 27% to 33%), against one stayer in five (19%, 17% to 20%). For moves where a fee was paid, the gap is within noise.
- **The volume loss is small, and on Understat it is set pieces.** His own open-play shots and shot-assists per 90 do not fall on Understat (−0.5%, −2.7% to +1.7%), while his set-piece actions per 90 fall by 11.9% (−17.3% to −6.3%). Opta, which marks only direct free kicks, shows his actions outside direct free kicks down 3.3% (−5.9% to −0.7%), so the two sources disagree on how much is set pieces.
- **This is not a trade.** The quantity a pre-match player price uses is start probability, and that is where the gap is: 14 points fewer starts in the first 10 matches. Season-long player markets and fantasy prices would feel the minutes risk too. No price, margin or cost was tested; the FPL side study has only 18 Premier League movers.

## Inference

- **Primary family: four tests on Understat, Holm-corrected.** The matched gaps in share of shots and shot-assists, in his own actions per 90, in output per 90 and in "flop or lost place". Holm controls the chance of any false positive in the family. Share and flop-or-lost-place reach the bootstrap's floor (p at or below 0.0005; Holm-adjusted 0.002), and own actions survives (adjusted 0.026); output does not (adjusted 0.418), as the headline expects. The same four tests on Opta, as their own family, give the same pattern.
- **Nothing was pre-registered, and one outcome was chosen after looking.** "Flop or lost place" was added after a first look showed the 900-minute floor hid lost places. Since then the floor (450, 900, 1,350 minutes), the flop line (15%, 25%, 35%), five exclusions and two luck benchmarks have been tried; the tables show all of them. Every result here is exploratory.
- **The smallest gap the matched comparison could see with 80% power is about 5 points** (5.1 for flops, 5.3 for flop or lost place).
- **The secondary family: 11 slice tests (age bands, fee bands, league path, buying clubs, the predictor), also Holm-corrected.** On Understat only the predictor survives (p = 0.002, adjusted 0.022); the 26–28 age gap has p = 0.029, adjusted 0.29. On Opta the predictor (adjusted 0.005) and the league path (adjusted 0.009) survive.
- **Intervals resample whole players, 2,000 times.** Resampling whole buying club-seasons instead, since team-mates at a new club share its changes, gives −4.1% (−5.9% to −2.3%) for the share gap and +11.7 points (+7.9 to +15.6) for flop or lost place.

## Method

- **Sample.** Attackers (centre-forwards, wingers and attacking midfielders on Transfermarkt, a public transfer and line-up database) with 900 league minutes and 20 shots or shot-assists in a season, followed by any Big-5 league appearance the next season. A move is a change of club between the two seasons. 601 of the 865 movers and 2,075 of the 2,562 stayers also reach 900 minutes the next season; the four-part tests use those.
- **Usage.** His share is his shots and shot-assists as a share of his team's while he is on the pitch, with minutes measured match by match from Transfermarkt line-ups and substitutions. Understat gives every shot, its assister and whether it came from open play or a set piece. Penalties are left out.
- **Four parts.** Output per 90 = team actions per 90 while he is on × his share × team-mates' xG+xA per action × his xG+xA per action relative to team-mates. Each change is a log change, close to a percentage change for small moves, so the four parts add up to the change in output. The split is accounting: his own actions sit inside the team's, and his quality is measured against team-mates', so credit can move between parts.
- **Matching for regression to the mean.** A regression of each change on a mover flag plus dummies for the decile of last season's share, the decile of last season's output per 90, age band and season. A second version reweights stayers to the movers' mix of cells.
- **Second source.** Every test is rerun on Opta's xG for the Big-5 plus Portugal and the Eredivisie, 2017–18 to 3 February 2025.

## Results

### After a move his share is 4–6% lower; on Understat, set pieces and a busier new team account for most of it

| Movers minus stayers | Understat, raw | Understat, matched | Opta, raw | Opta, matched |
|---|--:|--:|--:|--:|
| His share of the ball | −4.4% (−6.4% to −2.3%) | −4.1% (−5.8% to −2.4%) | −6.5% (−8.9% to −4.1%) | −6.1% (−8.2% to −4.1%) |
| His own shots and shot-assists per 90 | −1.9% (−4.3% to +0.2%) | −2.6% (−4.8% to −0.6%) | −3.3% (−6.0% to −0.5%) | −3.5% (−6.0% to −1.1%) |
| His team's actions per 90, without him | +3.4% (+1.4% to +5.4%) | +2.4% (+0.5% to +4.3%) | +4.7% (+2.4% to +7.0%) | +4.0% (+1.8% to +6.1%) |
| Output per 90 | +3.6% (+0.2% to +6.9%) | +1.3% (−1.9% to +4.4%) | +0.4% (−3.4% to +4.1%) | −0.7% (−4.1% to +2.4%) |
| Flop rate, points | +1.4 (−2.1 to +4.9) | +3.2 (−0.4 to +6.8) | +4.2 (−0.1 to +8.7) | +5.1 (+1.0 to +9.4) |

"His share of the ball" means his share of the team's shots and shot-assists while he is on, not possession or touches. Three team numbers appear in this section: the chances his team creates while he is on (+1.5% matched, a part in fig0), the same without his own actions (+2.4% matched, the table), and the buying club's shots and shot-assists per match the season before the move (+2.9%).

- **About three fifths of the matched share fall is fewer actions of his own, and two fifths is a team that does more.** His own actions per 90 fall by 2.6% against a share fall of 4.1%. Reweighting instead of regression gives −4.0% (−5.8% to −2.2%) on Understat and −6.6% (−8.8% to −4.2%) on Opta.
- **On Understat, his own fall is set pieces.** Matched, his open-play actions per 90 change by −0.5% (−2.7% to +1.7%) and his set-piece actions by −11.9% (−17.3% to −6.3%). His shots fall by 4.2% (−7.0% to −1.7%) and his shot-assists do not change (−0.1%, −3.5% to +3.1%). Opta marks only direct free kicks, and outside them his actions still fall, so on Opta set pieces explain less of it.
- **His share of open play still falls, because the new team makes more.** Measured match by match on open-play actions only, his share falls by 2.4% (−4.2% to −0.6%) on Understat, while the team's open-play actions per 90 with him on rise by 1.9% (0.0% to +3.9%), an interval that reaches zero.
- **The better team is visible before the move.** The clubs movers join made 2.9% (1.2% to 4.4%) more shots and shot-assists per match the season before than the clubs they left (Opta 2.6%, 0.7% to 4.5%). That is a small step up: 54% (50% to 58%) of movers joined a club that made more, close to an even split.

### Playing time: a third of movers lose their place, mostly after free, loan or unrecorded moves

| | Understat movers | Understat stayers | Opta movers | Opta stayers |
|---|--:|--:|--:|--:|
| No 900-minute season next (under 900 minutes or 20 actions, or split between clubs) | 31% (27% to 33%) | 19% (17% to 21%) | 33% (29% to 37%) | 20% (18% to 22%) |
| Flop or below 900 minutes | 44% (41% to 47%) | 33% (32% to 35%) | 49% (45% to 52%) | 35% (33% to 38%) |
| Gap, matched | +11.7 points (+7.9 to +15.4) | | +14.1 points (+9.6 to +18.6) | |

- **This is the largest and clearest gap in the study.** It survives matching on last season, age adjustment (+11.8 points, +7.9 to +15.7) and the Opta rerun. On minutes alone (under 900 league minutes), the matched gap is +11.5 points (+7.8 to +14.9) on Understat.
- **It holds under the checks the share gap gets** (Understat, matched, flop or lost place):

| Check | Gap, points |
|---|--:|
| Also matched on last season's share of his club's minutes | +10.7 (+7.0 to +14.3) |
| Without moves to promoted or from relegated clubs | +9.9 (+5.5 to +14.2) |
| Without likely loans | +10.6 (+6.5 to +14.5) |
| Without either | +8.6 (+3.9 to +13.2) |
| Floor at 450 minutes, minutes only | +3.8 (+1.3 to +6.1) |
| Floor at 1,350 minutes, minutes only | +14.0 (+10.1 to +18.0) |
| Every season with no Big-5 row next season counted as lost | +15.3 (+11.9 to +18.7) |
| Every season with no Big-5 row next season counted as kept | +5.7 (+2.5 to +8.7) |
| Split-season players brought back on their Transfermarkt minutes, the rest counted as lost | +7.7 (+4.2 to +11.0) |
| Also matched on his share of minutes in the second half of last season, and on goals minus xG | +10.2 (+6.3 to +13.7) |
| Stayers reweighted to the movers' mix of cells | +11.1 (+7.0 to +15.0) |
| Buying club made more shots the season before | +8.1 (+3.2 to +13.5) |
| Buying club did not | +13.0 (+6.8 to +18.6) |
| Fit all next season (under 30 days out) | +12.4 (+7.8 to +17.4) |
| Injured 30 days or more | +11.0 (+4.8 to +17.1) |

- **Who drops out decides the range.** 845 of 4,272 qualifying seasons have no Big-5 row the next season: sold abroad or down a division, relegated with the club, injured all season, not matched, or split between two clubs (the sample keeps a season only when one club holds 80% of his actions). 315 of them show a Transfermarkt transfer away from his club, and 191 played Big-5 league minutes the next season, 125 of them 900 or more. The gap is +5.7 points if every dropout kept his place and +15.3 if every one lost it.
- **The gap sits in moves with no fee on record.** Each fee band against all stayers, matched:

| Moves | Movers | Gap, points |
|---|--:|--:|
| Any fee paid | 327 | +1.8 (−3.8 to +7.4) |
| Over €30m | 86 | −0.9 (−11.0 to +9.6) |
| €10–30m | 126 | +2.5 (−5.8 to +10.8) |
| Under €10m | 115 | +3.3 (−6.0 to +13.4) |
| Free or loan | 262 | +9.5 (+3.0 to +16.4) |
| No fee on record | 276 | +25.2 (+18.8 to +31.0) |

- **Starts in the first 10 matches.** Movers start 41% of their new club's first 10 league matches, against 56% for stayers, matched −14.2 points (−16.8 to −11.6); on Opta −16.3 (−19.3 to −13.4). Movers had played slightly less in the second half of their last season too (58% of their club's minutes against 60%), which the matching on late-season minutes allows for.

### Among regulars, the luck benchmark cannot tell movers from luck

Picking moves by a big fall also picks bad luck, so I measured how much luck alone produces. For each pair of seasons I kept the real change of team and role, fixed the player's quality against his team-mates, and redrew his chance quality from his own shots, 200 times. A second benchmark also redraws his share of the ball from his own pooled share, so both his role and his quality are fixed.

| | Flop rate, data | Luck only | Luck only, share redrawn too | Player's part of a flop, data | Player's part, luck only |
|---|--:|--:|--:|--:|--:|
| Moved club | 19% (16% to 22%) | 22% (19% to 24%) | 20% (18% to 23%) | 36% (28% to 45%) | 33% (27% to 39%) |
| Stayed | 18% (16% to 19%) | 19% (17% to 20%) | 19% (17% to 20%) | 42% (38% to 46%) | 39% (36% to 42%) |

- **Data minus luck: −2.7 points (−6.5 to +1.1) for movers on Understat, −1.3 (−6.1 to +2.9) on Opta.** This includes the data's own resampling uncertainty. The benchmark runs about a point high on stayers too, so it cannot detect a real rise of 1 to 3 points in movers' flop rate.
- **The player's own part of a flop is within the luck band.** 36% (28% to 45%) in the data, against 33% (27% to 39%) from luck. About 73% (65% to 84%) of the spread in a mover's change of quality against team-mates is what sampling noise alone would give.
- **Against stayers, movers flop a little more often.** Matched, the gap is +3.2 points (−0.4 to +6.8) on Understat and +5.1 (+1.0 to +9.4) on Opta. With the flop line at a 15% or a 35% fall instead of 25%, the Understat gap is +2.2 (−2.0 to +6.4) and +3.7 (+0.9 to +6.4).
- **Losing the ball accounts for 27% (19% to 35%) of the average mover's flop on Understat,** and 32% of movers' flops (24% to 41%) would not have been flops had his share held.

![Movers' flop rate sits inside a luck benchmark too noisy to see a small rise](figures/fig1_flops_look_like_luck.png)

### Who flops: only the predictor survives the multiple-testing correction

<img src="figures/fig2_age.png" width="420" align="right" alt="Flop rate gap by age band, with 95% intervals">

| Test (Understat) | Estimate | p | Holm p |
|---|--:|--:|--:|
| Predictor, AUC above 0.5 | 0.63 (0.55 to 0.71) | 0.002 | 0.022 |
| Age 26–28, movers v stayers | +9.1 points (+0.8 to +17.3) | 0.029 | 0.29 |
| Fee under €10m v other movers | −7.4 points (−15.0 to +0.4) | 0.070 | 0.63 |
| Changed league v same league | +5.1 points (−1.4 to +11.6) | 0.12 | 0.92 |
| Buying clubs, early v late record | rank correlation −0.10 | 0.77 | 1.00 |

- **Age.** Movers aged 26 to 28 flop 28% (20% to 36%) of the time, against 19% (16% to 22%) for stayers of the same age. The other three bands' gaps all include zero.
- **League.** Players who move to a new league flop 22% (17% to 28%) of the time, against 17% (14% to 21%) for movers within the same league. On Opta, where the new league is often a step up from Portugal or the Eredivisie, the gap is +12.6 points (+4.8 to +19.6) and survives the correction.
- **Fee.** Moves over €30m flop 20% (11% to 28%) of the time, €10–30m moves 17% (10% to 25%), moves under €10m 13% (6% to 20%), and free or loan moves 19% (14% to 25%); every interval overlaps. 149 moves have no fee on record in Transfermarkt.
- **Buying club.** After shrinking each club's record towards the average, the spread between clubs is close to zero, and only 11 clubs made enough signings to compare 2015–19 with 2020–25 (rank correlation −0.10, p = 0.77).

<br clear="right">

### Can you see it coming? A little, and no prospective test has been run

- **On regulars who keep their place, a simple model gives a pseudo-out-of-time AUC of 0.63 (0.55 to 0.71).** AUC is the chance it ranks a random flop above a random non-flop, where 0.5 is a coin toss. The model is a logistic regression, shrunk towards zero to avoid overfitting, on six inputs known on the day (age, output per 90, quality against team-mates, share of the ball, share of minutes, change of league). It is trained on moves into 2015–16 to 2019–20 and tested on 2020–21 onwards (280 moves). "Pseudo" because the test seasons existed when the inputs were chosen.
- **On every move known on the day, it does about as well: 0.65 (0.59 to 0.70) for "flop or lost his place" across 400 test moves.** Counting players who lost their place as non-flops gives 0.64 (0.56 to 0.71), and predicting lost places alone 0.68 (0.62 to 0.73). An AUC in the low 0.60s on a few hundred moves has no stated use.
- **The 2025–26 "frozen" test is not prospective.** The model in `data/flop_model_frozen.json` and its predictions for 80 moves into 2025–26 in `data/predictions_2025_26.csv` were committed at 20:50 on 3 November 2026 and scored 19 minutes later. The Transfermarkt minutes for 2025–26 were already on disk, and 2025–26 Premier League outcomes from FPL had been committed 30 minutes before the freeze. On lost places, 21 of the 80 fell below 900 league minutes and the model ranks them with an AUC of 0.54 (0.40 to 0.68), no better than chance. The test set also held 4 moves to clubs outside the Big-5 and 8 January moves (2 moves were both); without them, and counting minutes at the new club only, it is 0.52 (0.37 to 0.68) on 70 moves. The commit that froze it (5845cab) says it came before any 2025–26 outcome was read; that is wrong, for the reasons above. After the stoppage-time fix below, a rebuild would give slightly different predictions; the frozen file is kept as committed. Flops cannot be scored, because no source here has 2025–26 Understat shots.
- **A prospective test needs a newer Transfermarkt copy.** Of the 2,850 transfers this copy dates 1 June to 1 September 2026, 2,799 are dated 30 June or 1 July, when loans end and contracts turn over, so the summer 2026 window is missing. The next step is to freeze predictions for summer 2026 moves as soon as a copy with that window exists, before any 2026–27 minutes are in it.

## Robustness

- **Opta, seven leagues.** The usage cost holds and is larger (−6.5% raw, −6.1% matched), and in open play it is −6.0% (−8.2% to −4.0%). Output per 90 roughly breaks even (+0.4%, −3.4% to +4.1%). The predictor scores 0.70 (0.64 to 0.77) pseudo out of time, helped by easy cases: moves up from Portugal and the Eredivisie, which the change-of-league input picks up. FBref's 2024–25 files stop on 3 February 2025.
- **Position on the team sheet.** Transfermarkt gives one position per player, as of 2026. Keeping only pairs where his starting line-up position was an attacking one in both seasons (91% of pairs), the share gap is −4.1% (−5.7% to −2.5%).
- **Name matching.** Understat and Transfermarkt are joined by names within each league-season, using club to settle clashes. 93% of Understat's non-penalty shots belong to a player matched to Transfermarkt; the worst league-season is La Liga 2017–18, at 85%.
- **Midfielders who are not attacking midfielders lose about 1.6 times as much of the ball.** On Understat their share falls by 9.3% (−12.7% to −6.1%) raw and 6.7% (−10.0% to −3.8%) matched, and output per 90 falls by 5.2% (−10.6% to +0.2%). They flop 33% (28% to 37%) of the time against 24% (23% to 26%) for midfielders who stay, +9.5 points after age (+4.0 to +14.5), and 53% of them flop or lose their place against 39% of stayers (+16.3 points matched, +11.6 to +20.4). On Opta the share falls by 11.8% (−15.9% to −7.6%). The sample uses today's Transfermarkt position, so a winger later moved back into midfield counts as a midfielder in every season.
- **MLS (Major League Soccer), a league outside Europe with a salary cap.** From [American Soccer Analysis](https://www.americansocceranalysis.com) player-seasons, with share estimated from season totals rather than minutes on the pitch, 153 attacker moves show the same usage cost: share falls by 3.8% (−7.3% to −0.4%), the new team does not create more chances (−0.6%, −3.0% to +2.0%), and movers flop more often than stayers (25% against 18%, a gap of +8.0 points, +0.8 to +15.7).
- **Loans, promoted and relegated clubs.** Transfermarkt does not flag loans, so a move counts as a likely loan when the player went back to the selling club within two seasons (109 moves). The flag uses what happened later, so it is a check, never an input to a prediction. Without them the share gap is −4.8% (−7.0% to −2.6%). Without the 52 moves to promoted clubs and 114 from relegated clubs it is −4.1% (−6.2% to −1.9%).
- **The same player with more of the ball.** Following one player from one season to the next (2,693 pairs of seasons from 897 players), seasons where his share was 5 points higher came with chance quality 1.5% lower (95% interval −2.9% to −0.1%), with share and quality measured on different matches. The typical move cuts a player's share by about 0.7 points (4.4% of a 16% share), which on this slope is worth about 0.2% in chance quality. Among movers measured against their new team-mates the slope is 0.0% (−2.6% to +2.8%).

![Five more points of the ball comes with chances about 1.5% worse](figures/fig3_within_player.png)

## Limits

- **Observational.** Clubs choose whom to buy and coaches choose a player's share; matching removes only what last season's numbers show.
- **Only moves between Big-5 clubs.** Players sold to the Championship, Turkey, Saudi Arabia or MLS have no Big-5 row the next season and drop out, as do stayers relegated with their club. Counting them moves the lost-place gap from +5.7 to +15.3 points.
- **Who is sold.** A selling club may let go a player it no longer plans to pick. Matching on his minutes in the second half of last season catches part of that; what the club knew and the data do not is untested.
- **League minutes only.** A player at a club in Europe can lose league minutes to rotation without losing his place.
- **January moves are not in it.** A season counts only when one club holds 80% or more of a player's actions, so a player who changed club mid-season drops out of that season.
- **Position is today's.** The sample uses Transfermarkt's position as of 2026; the line-up check above covers it for attackers.
- **Shots and shot-assists only.** Carries, pressing and build-up passes are invisible, so this suits attackers.
- **The four-part split is accounting.** His own actions count in the team's total, and his quality is measured against team-mates', so credit shifts between parts, and the parts' changes correlate.
- **Leagues and years.** Understat covers the Big-5 to 15 September 2025; the Opta rerun adds Portugal and the Eredivisie to 3 February 2025. Moves from the Championship, Belgium or Brazil are invisible.
- **Not a trading signal.** No betting, fantasy or player-prop market was tested, and no costs or capacity are estimated. The market test would be whether pre-team-news anytime-scorer or shots prices for a signing's first 10 matches already allow for the 14-point fall in starts; that needs odds history this repo does not have.

## What would change my mind

- If a club's own tracking data showed movers keep their touches and lose only shots, the usage cost would be about who finishes moves, and his involvement would be unchanged.
- If the share and starts gaps vanish once each player's intended role at the buying club is known (scouting reports, contract length), they are about which players are bought, not the move.
- If predictions frozen before 2026–27 do no better than chance on lost places, the predictor is noise.
- This list used to say the lost-place gap would be about loans and squad fillers if it vanished for fee-paid moves. It does: +1.8 points (−3.8 to +7.4) where a fee was paid.

## Reproduce

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
./run_all.sh --quick                                # figures from the shipped tables, about 30 seconds
export SOURCE_DATA=/path/to/your/raw/data          # layout and checksums in data/DATA.md
./run_all.sh                                        # everything from raw data
```

The full run rebuilds every number and figure, runs the self-checks, and checks every number quoted in this README and in `docs/side_studies.md` against the tables in `data/` (`analysis/verify.py` prints PASS or FAIL for each). It takes about 30 minutes on a laptop, most of it the StatsBomb files and the bootstraps. Two bugs were fixed on 6 November 2026: the midfielder run overwrote the attackers' season pairs, and stoppage-time shots were left out of a player's team total while he was on (Transfermarkt ends every match at minute 90, Understat dates stoppage-time shots 91 and later). A self-check now asserts that a player on for every league minute sees all his team's actions (median ratio 1.000 across 269 such seasons). A full run on that date reproduces every committed table byte for byte. The Transfermarkt copy (built 5 September 2026) cannot be downloaded again, so a third party can rebuild from raw data only with a copy whose checksums match `data/DATA.md`. A second `./run_all.sh --quick` leaves `git status` clean: figures and the one-pager carry no timestamps. Python 3.14, versions pinned in `requirements.txt`.

## Data and licences

- **Shots and xG:** [Understat](https://understat.com) via [worldfootballR_data](https://github.com/JaseZiv/worldfootballR_data) (Jason Zivkovic), 2014–15 to 15 September 2025.
- **Opta xG, seven leagues:** [FBref](https://fbref.com) via worldfootballR_data, 2017–18 to 3 February 2025.
- **Minutes, line-ups, substitutions, transfers:** [Transfermarkt](https://www.transfermarkt.com) via [transfermarkt-datasets](https://github.com/dcaribou/transfermarkt-datasets) (David Cariboo).
- **Side studies:** [StatsBomb open data](https://github.com/statsbomb/open-data), [American Soccer Analysis](https://www.americansocceranalysis.com) (CC BY-SA 4.0), the [FPL archive](https://github.com/vaastav/Fantasy-Premier-League) (MIT), [salimt/football-datasets](https://github.com/salimt/football-datasets), [Impect open data](https://github.com/ImpectAPI/open-data) and the [Wyscout public dataset](https://figshare.com/collections/Soccer_match_event_dataset/4415000) (CC BY 4.0).

None of the raw data is in this repository. `data/LICENSE.md` maps every committed file in `data/` to its source and terms; `data/asa.json` is released under CC BY-SA 4.0. Code is MIT-licensed. For the other aggregates, the figures and the one-pager, the sources' own terms apply and restrict commercial use; Understat, the main source, publishes no licence at all.

<img src="figures/statsbomb_logo.png" width="160" alt="StatsBomb"> &nbsp; <img src="figures/impect_logo.svg" width="120" alt="Impect">

## About

Ben Rimmer, First-class BSc Economics, University of Exeter. benedict.p.rimmer@gmail.com

A one-page summary is in [`onepager.pdf`](onepager.pdf), drawn from the same tables. Side studies (chemistry between team-mates, StatsBomb, Impect and Wyscout pass checks, Depay and Ronaldo, FPL 2025–26, injuries and free transfers) are in [`docs/side_studies.md`](docs/side_studies.md). How this repo was reviewed is in [`LOOP.md`](LOOP.md).

<details>
<summary>Full method and tables</summary>

### Minutes on the pitch

Transfermarkt line-ups give the starters, and its match events give every substitution and red card, so each player has an on and off minute in every league match (573,444 player-matches in 20,002 games). Understat gives the minute of every shot. Together they say which shots and shot-assists his team made while he was on.

### The four parts, raw

An action is a shot or a shot-assist. Penalties and own goals are excluded. An assisted shot counts for both players, each credited with its xG. The transfer tests need 20 actions in each season as well as 900 minutes, which is why they have 601 moves and the within-player tests have 605.

| Part | Movers minus stayers | 95% interval |
|---|--:|--:|
| His share of the ball | −4.4% | −6.4% to −2.3% |
| Chances his team creates | +2.4% | +0.7% to +4.3% |
| Quality of team-mates' chances | +3.2% | +1.4% to +5.0% |
| His own quality against team-mates | +2.4% | +0.0% to +4.7% |
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
| **Per 90, split-half (headline)** | 2,693 | **−1.5%** | **−2.9% to −0.1%** |
| Per 90, same matches | 2,693 | −2.1% | −3.9% to −0.4% |
| Per 90, against team-mates | 2,693 | −1.9% | −3.5% to −0.3% |
| Season share split-half, plus last season's quality | 2,693 | −2.0% | −4.0% to −0.2% |
| Season share, minutes held fixed | 2,693 | −3.5% | −5.9% to −1.1% |
| Season share, nothing held fixed | 2,693 | −0.3% | −1.5% to +0.9% |
| Per 90, same club both seasons | 2,088 | −1.3% | −3.2% to +0.6% |
| Per 90, changed club | 605 | −2.0% | −5.1% to +1.1% |
| Per 90, changed club, against new team-mates | 605 | 0.0% | −2.6% to +2.8% |

### The luck benchmarks

For each pair of seasons, the three situation parts stay as observed. The change in his quality against team-mates is replaced by pure sampling noise: his actions in each season are redrawn with replacement from his own pooled actions over both seasons, so his true quality is the same in both, and the noise is the log change in the mean. Flops are then selected and split exactly as in the data. 200 runs each for movers and stayers; draws in `data/noise_benchmark_draws_*.csv`. The first benchmark keeps the observed change in his share of the ball, so it ignores the negative link between share and quality within a season. The second redraws his action count in each season as binomial on his team's actions while he was on, at his pooled share, and redraws his quality with those counts (`analysis/robustness.py`). "Data minus luck" pairs a bootstrap draw of the data with a random benchmark run, 2,000 times (`analysis/rivals.py`).

### The flop predictor

A ridge-penalised logistic regression on six standardised inputs known on the day of the move: age, output per 90, quality against team-mates, share of the ball, share of minutes played, and whether the move changes league. Trained on moves where the first season starts in 2018 or earlier, tested on the rest. The frozen version and how to score it are in `data/flop_model_frozen.json`; `analysis/score_frozen.py` scores it. A rebuild never rewrites the frozen files; it only checks that it would produce the same predictions.

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
