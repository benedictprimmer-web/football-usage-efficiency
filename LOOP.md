# Review loop

This repo is being pushed toward done by a review loop, started on 3 November 2026. Each round, two fresh critics read the repo on their own and score ten components from 0 to 10: a senior quant portfolio manager and prop trader, and the head of data science at a London sports-trading firm. The lower of the two scores counts. A three-seat council (prosecution, defence, practice) argues the headline on the README's first screen, and its testable points go to the builder. A builder then fixes only the components scored below 9, one commit per round titled `Loop round N: …`. Components at 9 or above freeze. The loop runs for up to 10 rounds, or until every done marker passes. The critics see the scores from earlier rounds, never the builder's reasoning.

## Components

| # | Component | 10 looks like |
|---|---|---|
| C1 | First screen | 6 |
| C2 | Reproducibility | 7 |
| C3 | Inference | 5 |
| C4 | Alternative explanations | 5 |
| C5 | Leakage and look-ahead | 4 |
| C6 | Charts | 6 |
| C7 | Tradeability | 5 |
| C8 | Writing | 7 |
| C9 | Data and licences | 7 |
| C10 | Professional report | 6 |

## Scorecard

Lower of the two critics' scores. A dash means not yet scored.

| Component | R1 | R2 | R3 | R4 | R5 | R6 | R7 | R8 | R9 | R10 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| C1 First screen | 5 | 6 | – | – | – | – | – | – | – | – |
| C2 Reproducibility | 7 | 7 | – | – | – | – | – | – | – | – |
| C3 Inference | 4 | 5 | – | – | – | – | – | – | – | – |
| C4 Alternative explanations | 5 | 5 | – | – | – | – | – | – | – | – |
| C5 Leakage and look-ahead | 6 | 4 | – | – | – | – | – | – | – | – |
| C6 Charts | 7 | 6 | – | – | – | – | – | – | – | – |
| C7 Tradeability | 2 | 5 | – | – | – | – | – | – | – | – |
| C8 Writing | 6 | 7 | – | – | – | – | – | – | – | – |
| C9 Data and licences | 7 | 7 | – | – | – | – | – | – | – | – |
| C10 Professional report | 5 | 6 | – | – | – | – | – | – | – | – |

## Mechanical markers

| Marker | Before round 1 (commit 51d7f74) | After round 1 | Before round 2 (8be91d6) | After round 2 |
|---|---|---|---|---|
| `./run_all.sh --quick` exits 0 | Pass | Pass | Pass | Pass |
| `analysis/verify.py` prints no FAIL | Pass | Pass (122 checks, README and side studies) | Pass on `--quick`; the full rebuild FAILed 3 side-study checks (injuries) | Pass (149 checks) |
| No em dashes in README, one-pager source or figure text | Pass | Pass | Pass | Pass |
| No local home-directory paths in tracked files | Pass | Pass | Pass | Pass |
| A second `./run_all.sh --quick` leaves `git status` clean | Fail: figures and the one-pager carried timestamps and random SVG ids | Pass | Pass | Pass |
| A full `./run_all.sh` from raw data reproduces every committed table (added in round 2) | – | – | Fail: `injuries.json` changed | Pass: every file in `data/`, `figures/` and the one-pager byte for byte |

## Round 1 council

On the headline as it stood on 3 November 2026: "Moving club costs an attacker about 5% of his share of the ball, and the better team he joins makes up for it."

- **Converged.** Every headline number matched `data/transfers.json`, and the usage cost replicates on Opta (−7.2%, −9.6% to −4.8%), on midfielders (−12.0% on Opta) and in MLS (−3.8%).
- **Split.** "The better team makes up for it" fails age adjustment (+3.0%, −0.5% to +6.9%) and Opta (+0.4%, −3.4% to +4.1%). "Flops look like luck" is absence of evidence, and the player's part of a flop sits above the luck band (39% against 28% to 38%).
- **Practice.** Recruitment teams already model role and regression to the mean, so the usage cost alone tells them little they do not price; a trading desk would need a market test before acting.
- **Cannot be settled by research here.** Whether the usage drop shows up as mispriced anytime-scorer or shots odds in a signing's first 5–10 matches (a question for a head of trading with prop-odds history), and what a club's own tracking-data usage forecast said at signing (a question for a head of recruitment).
- **Defence's extra checks, folded into round 1.** Movers lose their place far more often than stayers (30.5% against 19.0% below 900 minutes), which the 900-minute floor hid; the luck benchmark runs high and cannot see a decline of 1–3 points; Opta contradicts "flops look like luck" (+4.8 points after age); the four-part split is accounting, with correlated parts; and the first screen led with an unadjusted flop gap.

## Round 1 changes

- **Regression to the mean, both sources (`analysis/robustness.py`).** Every gap rerun against stayers in the same decile of last season's share and output per 90, age band and season, and by reweighting, with player-clustered intervals. The share cost holds: −4.2% (−6.0% to −2.5%) on Understat, −6.4% (−8.4% to −4.4%) on Opta. The net output gain shrinks to +1.2% (−1.9% to +4.4%) and −0.7% (−4.0% to +2.5%).
- **Denominator.** His own shots and shot-assists per 90 now sit next to his share: −1.9% raw and −2.5% (−4.7% to −0.5%) matched on Understat, so about three of the 4.9 raw points of share were the team doing more. Team actions are also shown without his own, and the buying club's strength is measured the season before the move (+2.9%, 1.2% to 4.4%).
- **Lost places.** "Flop or below 900 minutes" is now a headline outcome: 44% of movers against 33% of stayers, +11.8 points matched (+8.0 to +15.4); Opta +14.0 (+9.4 to +18.4).
- **Loans, promoted and relegated clubs** named, flagged where the data allow, and excluded as a check; the share gap holds (−5.3% without likely loans, −4.6% without promoted or relegated clubs).
- **Second luck benchmark** redrawing share as well as quality; its limits (runs high, cannot see 1–3 points) stated next to the result.
- **Inference.** A status-of-tests note (nothing pre-registered, all exploratory), Holm-adjusted p-values for the 11 slice tests (only the predictor survives on Understat; the predictor and league path on Opta), and intervals on every rate in the README.
- **Look-ahead.** The predictor rescored on all 865 moves known on the day (0.64, 0.59 to 0.70, for flop or lost place); the 2020–21 test window is stated as known when features were chosen. The model was frozen (`data/flop_model_frozen.json`) and its predictions for 80 moves into 2025–26 committed in a separate earlier commit, then scored once on lost places: AUC 0.54 (0.40 to 0.68). Flops wait for 2025–26 shot data.
- **Tradeability.** A plain statement that no market was tested and nothing here is a trading signal, with the next test named.
- **Report and writing.** README restructured to finding, why it matters, status of tests, method, results, robustness, limits, reproduce; side studies moved to `docs/side_studies.md` and still checked by `verify.py`; seasons written 2014–15 throughout; the one-pager rewritten to match.
- **Charts.** fig0 shows the matched gaps with one highlight; fig1 retitled "Movers flop no more often than luck alone predicts"; fig2 now shows age-band gaps with 95% intervals and the Holm result; fig4 has one highlight.
- **Data and reproducibility.** `data/LICENSE.md` maps every data file to its sources and terms, with `asa.json` released under CC BY-SA 4.0; SHA-256 checksums of the raw inputs in `data/DATA.md`; deterministic SVG, PNG and PDF output.

## Round 2 council

On the headline as it stood on 6 November 2026: "A move cuts an attacker's share of the ball by about 4–6%, leaves his output per 90 about where it was, and makes him about 12 points more likely to flop or lose his place."

- **Converged.** Every headline number matched `data/robustness.json`. The share cut holds on both sources, with matching, reweighting, without loans and in MLS; the lost-place gap is the strongest result; output per 90 sits near zero.
- **Split.** "4–6%" is relative (about 0.8 of a point) and readers may take it as points; "the ball" means shots and shot-assists, not touches; "about 12" was Understat only (Opta 14.0); the output claim covers only movers who reach 900 minutes again; "cuts" and "makes" are causal verbs for observational data.
- **Practice.** Recruitment should plan on minutes; the share cut is a small volume adjustment. For trading, a 2.5% fall in own actions is likely inside a bookmaker's margin, and match props settle after line-ups, so the minutes risk does not carry over.
- **Cannot be settled here.** What clubs see that the data does not; whether movers keep their touches; whether prices already reflect the drop; a prospective predictor test.

## Round 2 changes

The two critics agreed on two factual errors, and both are fixed: the README said the 2025–26 predictions were committed before any 2025–26 outcome was read (FPL 2025–26 outcomes were committed 30 minutes earlier, and Transfermarkt's 2025–26 minutes were on disk), and it said movers' flop rate sat below both luck bands (it sits inside the second).

- **Reproducibility bug (C2).** A full rebuild from raw data at 8be91d6 did not reproduce `data/injuries.json`: the midfielder run of `transfers.py` overwrote the attackers' season pairs, which `injuries.py` reads. Each sample now writes its own file, and the full rebuild reproduces every committed table.
- **The lost-place gap gets the share gap's checks (C4, `analysis/rivals.py`).** Matched on last season's minutes share (+10.8 points), without promoted or relegated clubs (+10.0), without likely loans (+10.7), without either (+8.7), floors at 450 and 1,350 minutes (+3.8, +14.1), and a survival bound counting the 845 of 4,272 seasons with no Big-5 row next season as lost (+15.3).
- **Set pieces (C4, C7).** On Understat the fall in his own actions is all set pieces (open play −0.3%, set pieces −11.9%); his open-play share still falls 2.6% because the new team makes more. Shots per 90 fall 4.1%; shot-assists do not move. The headline now says "partly set pieces".
- **Inference (C3).** A primary family of eight tests with Holm (share and flop-or-lost-place survive on both sources; output on neither), the post-hoc status of the lost-place outcome stated, intervals resampling buying club-seasons, data minus luck as one difference with its interval, the flop line at 15% and 35%, intervals on the player's part of a flop and on the fee bands, and numbers without intervals cut.
- **Look-ahead (C5).** The 2025–26 test is now called what it is, not prospective; a labelled post-hoc rescoring drops two non-Big-5 buyers and 8 January moves (AUC 0.52, 0.37 to 0.68); the frozen files are never rewritten by a rebuild; "out of time" is now "pseudo out of time". A prospective freeze for 2026–27 was built and then dropped: this Transfermarkt copy has no summer 2026 window (2,799 of 2,850 records are 30 June or 1 July loan ends and contract changes), so the "moves" were mostly loan returns.
- **Other rivals (C4).** Line-up position season by season (share gap −4.2% on the 91% of pairs that were attacking both seasons), name-match rate (93% of shots), January movers and the Big-5-only sample named as limits.
- **Charts (C6).** New fig6 for lost places, now on the first screen next to fig0; fig1 retitled and the data made the highlight; fig0 says the share change is relative; fig4's caption names the measure its bars show; fig5 no longer says "much better" on 69 actions; the one-pager leads with lost places, uses matched midfielder numbers and drops the age highlight that failed Holm.
- **Tradeability (C7).** The props bullet now says plainly that this is not a trade, why the effect is small for match props, and that no price was tested.
- **Writing and report (C1, C8, C10).** New title; the first screen leads with the largest result, names "moves between Big-5 clubs", glosses Understat and Opta, and gives the share in points; the "two fifths" heading now uses the matched ratio (three fifths); absolute dates for FBref (3 February 2025); "about twice" is now "about 1.6 times"; the MLS line no longer says "no richer clubs"; the private-model paragraph is cut.
- **Data and licences (C9).** The unsourced claim that Understat's owner allows non-commercial use is gone; Sports Reference's terms are linked for FBref; the repo says it cannot grant rights over derived data; the prediction file is flagged as player-level; Impect is pinned to commit `d412b35` and the unpinned StatsBomb fetch is stated.
