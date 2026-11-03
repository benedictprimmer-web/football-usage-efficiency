# Review loop

This repo is being pushed toward done by a review loop, started on 3 November 2026. Each round, two fresh critics read the repo on their own and score ten components from 0 to 10: a senior quant portfolio manager and prop trader, and the head of data science at a London sports-trading firm. The lower of the two scores counts. A three-seat council (prosecution, defence, practice) argues the headline on the README's first screen, and its testable points go to the builder. A builder then fixes only the components scored below 9, one commit per round titled `Loop round N: …`. Components at 9 or above freeze. The loop runs for up to 10 rounds, or until every done marker passes. The critics see the scores from earlier rounds, never the builder's reasoning.

## Components

| # | Component | 10 looks like |
|---|---|---|
| C1 | First screen | The README's first screen (about 25 lines) states the finding with its size and interval, the method in one sentence and the main limit. A reader who stops there is not misled. |
| C2 | Reproducibility | `run_all.sh` rebuilds every result, figure and the one-pager from the committed inputs; the README check script passes; seeds fixed; pinned versions; runtime stated. |
| C3 | Inference | Every number in the README carries an interval, and every test says whether it was pre-registered and whether it passes after multiple-testing correction. Exploratory results are labelled. |
| C4 | Alternative explanations | For the headline, the obvious rival stories (confounds, mechanical artefacts, selection, data errors) are named and each is tested or bounded. A sceptic cannot name an untested one that would overturn it. |
| C5 | Leakage and look-ahead | Nothing in a prediction or a normal uses data from its own period or later; held-out data were not looked at before the freeze; the commit history shows the order. |
| C6 | Charts | Each chart's message reads in five seconds: a sentence headline that states the finding, one highlight colour, labelled axes with units, the null or benchmark drawn in, source line. Readable on a phone. |
| C7 | Tradeability | Wherever a result could be read as a trade, costs, turnover and capacity are stated, or the README says plainly that it is not a trade. Nothing implies money that the numbers do not support. |
| C8 | Writing | Ben's voice: plain words and whole sentences, en dashes only, no "not X but Y", every code or acronym glossed on first use, absolute dates. The one-pager matches the README. |
| C9 | Data and licences | No raw data committed where the licence bars it, sources credited, licence files present, no local paths or secrets. |
| C10 | Professional report | It reads like a short research note a desk would circulate. Every bullet starts with the point itself (the number or the conclusion), never the set-up. No waffle: no sentence a reader would skip loses anything. Headings say what the section shows. Standard parts in the standard order (finding, why it matters, method, results, robustness, limits, reproduce). Clear enough that a non-specialist founder follows it on one read. |

## Scorecard

Lower of the two critics' scores. A dash means not yet scored.

| Component | R1 | R2 | R3 | R4 | R5 | R6 | R7 | R8 | R9 | R10 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| C1 First screen | 5 | – | – | – | – | – | – | – | – | – |
| C2 Reproducibility | 7 | – | – | – | – | – | – | – | – | – |
| C3 Inference | 4 | – | – | – | – | – | – | – | – | – |
| C4 Alternative explanations | 5 | – | – | – | – | – | – | – | – | – |
| C5 Leakage and look-ahead | 6 | – | – | – | – | – | – | – | – | – |
| C6 Charts | 7 | – | – | – | – | – | – | – | – | – |
| C7 Tradeability | 2 | – | – | – | – | – | – | – | – | – |
| C8 Writing | 6 | – | – | – | – | – | – | – | – | – |
| C9 Data and licences | 7 | – | – | – | – | – | – | – | – | – |
| C10 Professional report | 5 | – | – | – | – | – | – | – | – | – |

## Mechanical markers

| Marker | Before round 1 (commit 51d7f74) | After round 1 |
|---|---|---|
| `./run_all.sh --quick` exits 0 | Pass | Pass |
| `analysis/verify.py` prints no FAIL | Pass | Pass (122 checks, README and side studies) |
| No em dashes in README, one-pager source or figure text | Pass | Pass |
| No local home-directory paths in tracked files | Pass | Pass |
| A second `./run_all.sh --quick` leaves `git status` clean | Fail: figures and the one-pager carried timestamps and random SVG ids | Pass |

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
