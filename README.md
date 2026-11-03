# Can usage rates explain failed transfers?

**A player's output is how much of the ball he gets times what he does with it. This tests whether the second part changes when the first does.**

## What I found

Barely. When the same attacker gets 5% more of his team's shots and shot-assists, the quality of his chances drops by about 1.7%. That could be nothing at all, as the range runs from a 3.4% drop to a 0.1% rise.

That means a player's quality mostly travels with him, while how much of the ball he gets depends on his minutes and the club he joins. So a transfer that looks like a flop can partly be a player who simply got less of the ball.

![Chance quality against share of the ball for 4,592 attacker seasons, with Memphis Depay's career on top](figures/fig1_usage_efficiency.png)

*The grey line is the average across 4,592 attacker seasons, and the shaded band is the range it probably sits in. The blue line is Memphis Depay.*

## Depay

At United in 2015-16 Depay played 43% of the league minutes, and the quality of his chances was well below average. At Lyon he played 75%, then 86%. He took almost a fifth of the team's shots and shot-assists, and his chances got better, from 0.086 to 0.124 per action.

Per minute on the pitch, his share of the ball was about the same at both clubs (22% at United, 24% at Lyon). The difference was that Lyon played him. His chances per action were also worse at United, but that rests on only 69 actions, so part of it is likely noise.

Two more cases are in `data/case_studies.csv`. Martial's chances got worse when he moved from Monaco to United, though his Monaco figure rests on only 61 actions. Ronaldo's held up at United in 2021-22, yet the team's expected goal difference was 0.25 per 90 worse with him on the pitch, a cost that per-action numbers cannot see.

## What the terms mean

- **Usage share** is a player's shots and shot-assists, as a percentage of his team's over the league season.
- **Chance quality** (efficiency) is the expected goals plus expected assists he produces per shot or shot-assist, without penalties.
- **xG** (expected goals) is the chance a shot is scored, based on thousands of similar shots.
- **xA** (expected assists) is the xG of the shot a pass sets up.

## Why it matters

A team only creates so many chances in a season, so usage works like a conserved quantity. The shares add up to 100%, and one player's rise comes out of his team-mates'. If chance quality fell steeply as a player got more of the ball, a signing could make the team worse while his own numbers looked good.

## How I tested it

I followed the same player from one season to the next: 2,646 pairs of seasons from 883 players, 592 of them club changes. Each step below names a trap and the fix.

- **Minutes.** Usage share counts minutes, and a player in form plays more. I held the change in minutes fixed. Without that, the effect reads as zero (−0.1%).
- **Shared noise.** One speculative shot raises a player's usage and lowers his chance quality at the same time, which builds a false trade-off. I measured usage on odd-numbered matches and chance quality on even ones, then the reverse. This gives the headline of −1.7%, and I chose it as the headline before running it.
- **Regression to the mean.** A player coming off a lucky season tends to drift back whatever happens to his role. Controlling for last season's chance quality leaves the result at −1.7%.
- **Team context.** A move changes the chances everyone on the team gets. Club changers show a 4.4% fall, and it disappears (−0.3%) when I measure them against their new team-mates. A player who moves into a bigger role often joins a team that makes worse chances for everyone.
- **Minimum minutes.** Below 900 league minutes, most of a player's chance quality is noise, so every season in the sample has at least 900.

![Four versions of the within-player test, with the headline highlighted](figures/fig2_within_player.png)

For a scout, that means a player's chance quality mostly travels with him, and his share of the ball is set largely by the club he joins.

## Limitations

**The data**

- **Leagues.** Understat covers only the Big-5 leagues and the Russian Premier League, from 2014-15. Selling-league seasons are invisible, including Depay's at PSV before he joined United.
- **Dates.** The shot data stops on 4 January 2025, halfway through 2024-25.
- **What counts as an action.** Only shots and the pass before a shot. Dribbles, carries, pressing and defending are not in it, so it only suits attackers.
- **Minutes.** Minutes and positions come from Transfermarkt and are joined to the shot data by name and club, so a few players may be mismatched or missing.
- **Licences.** The underlying data is for non-commercial research only, so this repo ships code and summary tables, not the raw data (see `data/DATA.md`).

**The method**

- **Noise and survivorship.** Chance quality on fewer than 100 actions is noisy. A pair needs 900 minutes in both seasons, so players whose role collapsed drop out, which probably hides some of the steepest falls.
- **Coaching.** If a coach gives the ball to whoever is in form, part of the pattern reflects his choices. The control for last season's form absorbs the obvious version of this.
- **Observational.** No experiment sits behind any of this, so it shows a pattern, not a cause.

## How this fits the wider model

This is one question from a larger transfer valuation model, kept private because its data cannot be redistributed. That model asks how good a player is (price-blind), what he is worth to a given club, and what he will cost. The usage idea sits underneath all three: a signing helps only if his chance quality beats that of the play he takes over. This result supports the assumption that chance quality travels with the player.

## Reproduce

You need Python 3.11 or later and your own copy of the source data (`data/DATA.md` gives the layout).

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
export SOURCE_DATA=/path/to/your/raw/data
./run_all.sh
```

`run_all.sh` builds the player-season panel, computes every number in this README into `data/`, and draws the figures, in about three minutes. The model code in `src/usage_model/` has offline self-checks: `PYTHONPATH=src python -m usage_model.usage` (and the same for `wowy` and `understat`).

## Data and licences

Shot-level xG comes from [Understat](https://understat.com), via the [worldfootballR_data](https://github.com/JaseZiv/worldfootballR_data) archive by Jason Zivkovic. Minutes and positions come from [Transfermarkt](https://www.transfermarkt.com), via [transfermarkt-datasets](https://github.com/dcaribou/transfermarkt-datasets) by David Cariboo. Both are used for non-commercial research and neither is redistributed here: `data/` holds only aggregate tables and season-level numbers for the three players above. Code is MIT-licensed (`LICENSE`), and the data keeps its owners' terms.

## About

Ben Rimmer, First-class BSc Economics, University of Exeter. benedict.p.rimmer@gmail.com

<details>
<summary>Full method and tables</summary>

### Where the question comes from

Basketball has studied this for 20 years. Dean Oliver's usage rate measures the share of a team's possessions a player ends while he is on the floor, and his skill curves show that most players get less efficient as they are asked to do more.

### Definitions and sample

The definitions are the ones the wider model uses (`src/usage_model/usage.py`), applied unchanged. Penalties and own goals are excluded. Usage and chance quality come from Understat shot data. Minutes and positions come from Transfermarkt, joined through an id crosswalk.

I kept forwards and attacking midfielders (Transfermarkt position "Attack" or "Attacking Midfield") with at least 900 league minutes in a season: 4,592 player-seasons from 1,436 players. Positions are each player's Transfermarkt position, which is fixed across his career. Russian seasons appear only for players the crosswalk could match through a Big-5 season (99 player-seasons). When a player changes club mid-season, I keep the club that holds at least 80% of his actions and drop the season otherwise. That keeps Ronaldo's 2021-22 (one Juventus match, then United).

### Why 900 minutes

I split each team's league matches into odd and even, measured each player's chance quality on each half, and correlated the two.

| League minutes | Seasons | Efficiency reliability | Usage reliability |
|---|--:|--:|--:|
| under 450 | 2,116 | 0.11 | 0.66 |
| 450 to 899 | 1,391 | 0.34 | 0.71 |
| 900 to 1,799 | 2,363 | 0.58 | 0.83 |
| 1,800 and over | 2,229 | 0.73 | 0.87 |

*Reliability is the split-half correlation stepped up to a full season (Spearman-Brown).*

Below 900 minutes, most of the variation in a player's chance quality is noise. Above it, more than half is signal. Usage is measured more reliably than chance quality at every level.

### Across players: the curve

I binned player-seasons by usage share and computed total value over total actions in each bin. The 95% intervals come from a bootstrap that resamples whole players, because a player's seasons are not independent. The curve is flat at about 0.12 per action from 4% to 14% usage and sits about 8% lower above 18%. This comparison mixes two things (better players get more of the ball, and better teams make better chances), so the test that matters is the one within players.

### Within players: the full specification

I took every pair of consecutive seasons where the player passed the 900-minute floor in both and regressed the change in efficiency on the change in usage share. Each pair is weighted by the precision of its efficiency change, `1 / (1/actions₁ + 1/actions₂)`, so a pair built on 300 actions counts for more than one built on 60.

The repo's usage share uses the whole season as its denominator, so it is roughly (share of the season played) × (share of play while on the pitch). Usage share and share of the season played correlate at 0.85 here. Using usage per minute on the pitch, in place of holding minutes fixed, gives −2.0%, and the two approaches agree.

The headline in absolute terms is −0.0019 xG+xA per action per 5 points of usage, or −1.7% of the median efficiency of 0.115 (interval −3.4% to +0.1%). Removing the shared noise shrinks the slope by about a third. The regression-to-the-mean control uses last season's efficiency measured on the other half of the matches.

| Specification | Pairs | Change per +5 points of usage | 95% interval |
|---|--:|--:|--:|
| Usage share as defined, nothing fixed | 2,646 | −0.1% | −1.3% to +1.1% |
| Holding minutes fixed | 2,646 | −2.9% | −5.2% to −0.6% |
| Usage per minute on the pitch | 2,646 | −2.0% | −3.5% to −0.5% |
| **Split-half, minutes fixed (headline)** | 2,646 | **−1.7%** | **−3.4% to +0.1%** |
| Split-half plus last season's efficiency | 2,646 | −1.7% | −3.4% to +0.1% |
| Same club both seasons | 2,054 | −0.9% | −3.6% to +1.8% |
| Changed club | 592 | −4.4% | −8.6% to −0.1% |
| Changed club, against new team-mates | 592 | −0.3% | −4.0% to +3.5% |
| Everyone, against team-mates | 2,646 | −2.1% | −4.1% to +0.0% |

*Percentages are of the median efficiency (0.115 npxG+xA per action). Intervals come from 2,000 bootstrap draws resampling whole players. Full table in `data/within_slopes.csv`.*

Players who stay at the same club show no clear drop (−0.9%). Measured against team-mates, the pooled slope stays at about −2%, so team context accounts for the club changers' fall and leaves the pooled slope in place.

### Where the slope comes from

![Season-to-season changes in usage and chance quality, binned into tenths](figures/fig3_within_bins.png)

Most of the slope rests on the fifth of pairs where usage fell hardest: those players' efficiency rose by 0.003 to 0.005 per action. In the tenth where usage rose most, efficiency barely moved.

### The three players in more detail

Season numbers are in `data/case_studies.csv`. Depay's share of play while on the pitch barely moved across United and Lyon (22%, 24%, 22%), and he played 86% of Lyon's minutes in 2020-21 at 18.6% usage. At United he was short of minutes, and he was never short of the ball. His PSV seasons are missing because Understat does not cover the Eredivisie.

Martial's United team-mates averaged 0.098 per action in 2015-16, against 0.109 for Monaco's attackers. Over the next five seasons at United he sat between 0.106 and 0.170 at 6% to 12% usage, with no clear pattern.

Ronaldo's on/off figure is the wider model's WOWY measure: the team's xG difference per 90 with him on the pitch against off it, shrunk towards zero when the off-pitch sample is thin. That cost would show up in what the team does around a player, such as pressing, or in possessions that never reach a shot.

### More limitations

- The full usage definition in the wider model adds turnovers, but that data comes from a frozen FBref/Opta snapshot that cannot be shared.
- Russian seasons are thin (99 player-seasons), and there is no Eredivisie, Primeira Liga or Championship, so Antony's Ajax seasons are also invisible.
- Minutes for 2024-25 are counted to the same date as the shot data. Transfermarkt minutes and positions are crowd-maintained.
- The baseline control does not rule out subtler versions of coaching choices.

### The wider model

The model keeps three questions apart:

1. **How good is he?** A talent score built price-blind: market value, wage and fee are never inputs, and the code refuses to fit if a price-like column appears (`src/usage_model/talent.py`, reference copy).
2. **What is he worth to this club?** A club-specific value that turns expected xG difference into league position and then into revenue, including the step in revenue that comes with Champions League qualification.
3. **What will he cost?** A fee model trained on disclosed transfer fees, validated season by season on later seasons only.

An earlier test found that a usage-weighted efficiency gap predicts the change in a team's xG difference after 2,364 transfers, with a small effect (r = +0.083, interval +0.042 to +0.123).

Out of time, the talent model's undervalued-player screen picked players whose market value doubled within two years at 23.5%, against a base rate of 13.2% (1,806 players screened). It passes two of its four pre-registered tests and fails two. It reads Haaland's injury-shortened 2021-22 at Dortmund as an ordinary season, because it cannot tell a star's injury from a fringe player's time on the bench, and Antony could not be scored at all, because his Ajax season is in the Eredivisie. Its decile test points the right way (the top tenth outgrows the bottom tenth, with an interval clear of zero) but only 5 of 9 steps rise, against a bar of 6. The tests were set before the results were seen and have not been loosened.

### Scripts

| Script | What it does |
|---|---|
| `analysis/build_panel.py` | Builds the player-season panel from raw data into `data/work/` (gitignored) |
| `analysis/analyse.py` | Computes every number above and writes the small tables in `data/` |
| `analysis/figures.py` | Draws the three figures from those tables, as PNG and SVG |

</details>
