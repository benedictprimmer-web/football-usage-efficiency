"""Check every number quoted in the README against the tables in data/.

Each check builds the exact text the README should contain from the data, and looks for
it. Prints PASS or FAIL per line and exits non-zero on any failure, so a stale README
cannot survive a rebuild.

    python analysis/verify.py
"""
from __future__ import annotations

import json
import sys

import pandas as pd

from config import OUT, ROOT

M = "−"


def p(v, dp=1, sign=False):
    s = f"{v * 100:+.{dp}f}%" if sign else f"{v * 100:.{dp}f}%"
    return s.replace("-", M)


def n(v, dp=1):
    return f"{v * 100:.{dp}f}".replace("-", M)


def checks() -> list[tuple[str, str]]:
    t = json.loads((OUT / "transfers.json").read_text())
    s = json.loads((OUT / "summary.json").read_text())
    c = json.loads((OUT / "chemistry.json").read_text())
    mv, nb = t["movers_vs_stayers"], t["noise_benchmark"]
    g = mv["mean_log_gap_by_part"]
    sl = pd.read_csv(OUT / "transfer_slices.csv")
    ag = pd.read_csv(OUT / "age_gaps.csv").set_index("age_band")
    ws = pd.read_csv(OUT / "within_slopes.csv").set_index("spec")
    cs = pd.read_csv(OUT / "case_studies.csv")
    pr = t["predict_flops"]
    bc = t["buying_club_persistence"]

    def sl_rate(dim, lev, grp="movers"):
        return sl[(sl.slice == dim) & (sl.level == lev) & (sl.group == grp)].flop_rate.iloc[0]

    def spec(k):
        r = ws.loc[k]
        return (f"{r.pct_of_median:.1f}%".replace("-", M),
                f"{r.ci_lo_pct:.1f}% to {r.ci_hi_pct:+.1f}%".replace("-", M)
                .replace("+0.0%", "0.0%").replace("−0.0%", "0.0%"))

    nbs, aa, u = t["noise_benchmark_stayers"], t["age_adjusted"], t["usage_in_flops"]

    def band(v):  # "22% (20% to 24%)"
        return f"{p(v[0], 0)} ({p(v[1], 0)} to {p(v[2], 0)})"

    def gi(x, dp=1):  # "+2.9%" style for a part of the gap, and its interval
        return p(x["point"], dp, True), f"{p(x['lo'], dp, True)} to {p(x['hi'], dp, True)}"

    out = [
        ("movers", f"{mv['n_movers']} club moves"),
        ("stayers", f"{mv['n_stayers']:,} seasons where the player stayed"),
        ("flop movers", f"Attackers who moved flopped {p(mv['flop_rate_movers']['point'], 0)} of the time"),
        ("flop stayers", f"and stayers {p(mv['flop_rate_stayers']['point'], 0)}, a gap"),
        ("flop gap", f"gap of {mv['flop_rate_gap']['point'] * 100:.1f} points (95% interval "
                     f"{n(mv['flop_rate_gap']['lo'])} to {mv['flop_rate_gap']['hi'] * 100:+.1f})"),
        ("age-adjusted gap", f"or {aa['flop_rate_gap']['point'] * 100:.1f} points after adjusting for age "
                             f"({n(aa['flop_rate_gap']['lo'])} to {aa['flop_rate_gap']['hi'] * 100:+.1f})"),
        ("share part", f"falls by {abs(g['His share of the ball']['point']) * 100:.1f}% (95% interval "
                       f"{gi(g['His share of the ball'])[1]})"),
        ("usage movers", f"accounts for {p(u['movers_share_of_fall']['point'], 0)} of the average fall for movers "
                         f"({p(u['movers_share_of_fall']['lo'], 0)} to {p(u['movers_share_of_fall']['hi'], 0)})"),
        ("usage stayers", f"and {p(u['stayers_share_of_fall']['point'], 0)} for stayers"),
        ("usage undone", f"{p(u['movers_flops_undone']['point'], 0)} of movers' flops would not have been flops"),
        ("team part", f"creates more chances ({gi(g['Team chances per 90'])[0]})"),
        ("mates part", f"better ones ({gi(g['Team-mates' + chr(39) + ' chance quality'])[0]})"),
        ("net", f"he ends up {p(mv['mean_log_gap']['point'])} ahead of stayers "
                f"({p(mv['mean_log_gap']['lo'])} to {p(mv['mean_log_gap']['hi'])})"),
        ("net age-adjusted", f"or {p(aa['mean_log_gap']['point'])} after adjusting for age "
                             f"({p(aa['mean_log_gap']['lo'], 1, True)} to {p(aa['mean_log_gap']['hi'], 1, True)})"),
        ("luck headline", f"would flop {p(nb['flop_rate_noise_only'][0], 0)} of the time"),
        ("luck stayers", f"it gives stayers {p(nbs['flop_rate_noise_only'][0], 0)} against a real {p(nbs['flop_rate_observed'], 0)}"),
        ("luck movers row", f"| Moved club | {p(nb['flop_rate_observed'], 0)} | {band(nb['flop_rate_noise_only'])} | "
                            f"{p(nb['player_share_observed'], 0)} | {band(nb['player_share_noise_only'])} |"),
        ("luck stayers row", f"| Stayed | {p(nbs['flop_rate_observed'], 0)} | {band(nbs['flop_rate_noise_only'])} | "
                             f"{p(nbs['player_share_observed'], 0)} | {band(nbs['player_share_noise_only'])} |"),
        ("noise share", f"About {round((nb['sd_d_rel_noise_only'] / nb['sd_d_rel_observed']) ** 2 * 10) * 10:.0f}% "
                        f"of the spread"),
        ("age movers", f"26 to 28 flop {p(sl_rate('age_band', '26–28'), 0)}"),
        ("age stayers", f"against {p(sl_rate('age_band', '26–28', 'stayers'), 0)} for stayers"),
        ("age gap", f"(gap +{ag.loc['26–28', 'gap'] * 100:.0f} points, +{ag.loc['26–28', 'lo'] * 100:.0f} "
                    f"to +{ag.loc['26–28', 'hi'] * 100:.0f})"),
        ("age 29+", f"movers aged 29 and over {p(sl_rate('age_band', '29 and over'), 0)}"),
        ("league", f"new league flop {p(sl_rate('path', 'Changed league'), 0)} of the time, "
                   f"against {p(sl_rate('path', 'Same league'), 0)}"),
        ("fee 30m", f"{p(sl_rate('fee_band', 'Over €30m'), 0)} of moves over €30m"),
        ("fee 10-30", f"{p(sl_rate('fee_band', '€10m–30m'), 0)} at €10–30m"),
        ("fee <10", f"{p(sl_rate('fee_band', 'Under €10m'), 0)} under €10m"),
        ("fee free", f"{p(sl_rate('fee_band', 'Free or loan'), 0)} of free or loan moves"),
        ("fee none", f"{int(sl[(sl.slice == 'fee_band') & (sl.level == 'No fee on record')].n.iloc[0])} moves "
                     f"have no fee on record"),
        ("clubs", f"only {bc['clubs']} clubs made enough signings"),
        ("clubs rho", f"(rank correlation {bc['spearman_early_late']:.2f}, p = {bc['perm_p']:.2f})".replace("-", M)),
        ("auc", f"AUC (the chance it ranks a random flop above a random non-flop) of {pr['auc']:.2f} "
                f"({pr['auc_lo']:.2f} to {pr['auc_hi']:.2f})"),
        ("risk fifth", f"flop {p(pr['flop_rate_top_fifth_of_risk'], 0)} of the time, against "
                       f"{p(pr['flop_rate_rest'], 0)} for the rest"),
        ("pairs", f"{s['n_pairs']:,} pairs of seasons from {int(ws.loc['on_pitch', 'n_players'])} players"),
        ("headline", f"chance quality {abs(s['headline_pct_of_median']['point']):.1f}% lower (95% interval "
                     f"{s['headline_pct_of_median']['lo']:.1f}% to {s['headline_pct_of_median']['hi']:.1f}%)".replace("-", M)),
        ("scale", f"cuts a player's share by about {abs(g['His share of the ball']['point']) * s['median_usage_on_pitch'] * 100:.1f} "
                  f"points ({abs(g['His share of the ball']['point']) * 100:.1f}% of a {s['median_usage_on_pitch'] * 100:.0f}% share), "
                  f"which on this slope is worth about "
                  f"{abs(g['His share of the ball']['point']) * s['median_usage_on_pitch'] * 100 / 5 * abs(s['headline_pct_of_median']['point']):.1f}%"),
        ("chem first season", f"{p(c['growth_within_first_season']['growth'])} more in the second half"),
        ("chem first season ci", f"({p(c['growth_within_first_season']['lo'], 1, True)} to "
                                 f"{p(c['growth_within_first_season']['hi'], 1, True)}, "
                                 f"{c['growth_within_first_season']['pairs']:,} pairs)"),
        ("chem next season", f"a season later: {p(c['growth_next_season']['growth'], 1, True)} "
                             f"({p(c['growth_next_season']['lo'], 1, True)} to "
                             f"{p(c['growth_next_season']['hi'], 1, True)})"),
        ("persistence", f"(correlation {c['persistence']['corr_next_season']:.2f}, against "
                        f"{c['persistence']['null_95']:.2f} at the 95th percentile"),
        ("reunions", f"start {p(c['reunions']['gap'])} ahead of new pairs "
                     f"({p(c['reunions']['lo'], 1, True)} to {p(c['reunions']['hi'], 1, True)})"),
        ("median quality", f"({s['median_efficiency']:.3f} xG+xA per action)"),
        ("part table share", "| His share of the ball | {} | {} |".format(*gi(g['His share of the ball']))),
        ("part table team", "| Chances his team creates | {} | {} |".format(*gi(g['Team chances per 90']))),
        ("part table mates", "| Quality of team-mates' chances | {} | {} |".format(*gi(g["Team-mates' chance quality"]))),
        ("part table own", "| His own quality against team-mates | {} | {} |".format(*gi(g["His quality relative to team-mates"]))),
        ("part table net", "| Output per 90 | {} | {} |".format(*gi(mv['mean_log_gap']))),
    ]
    for k in ["on_pitch_split_half", "on_pitch", "all_vs_mates", "baseline", "minutes",
              "naive", "stayers", "movers", "movers_vs_mates"]:
        a, b = spec(k)
        out.append((f"spec {k}", f"| {a} | {b} |"))
    d = cs[cs.player == "Memphis Depay"].set_index("season")
    out += [
        ("depay share utd", f"United in 2015-16 ({d.loc['2015-2016', 'usage_on_pitch'] * 100:.0f}%)"),
        ("depay share lyon", f"Lyon in 2017-18 ({d.loc['2017-2018', 'usage_on_pitch'] * 100:.0f}%)"),
        ("depay quality", f"from {d.loc['2015-2016', 'efficiency']:.3f} per action to "
                          f"{d.loc['2017-2018', 'efficiency']:.3f}, and to {d.loc['2020-2021', 'efficiency']:.3f}"),
        ("depay actions", f"only {int(d.loc['2015-2016', 'actions'])} actions"),
        ("depay minutes", f"{d.loc['2015-2016', 'minutes_share'] * 100:.0f}% of United's league minutes, "
                          f"against {d.loc['2017-2018', 'minutes_share'] * 100:.0f}% and "
                          f"{d.loc['2020-2021', 'minutes_share'] * 100:.0f}% at Lyon"),
    ]
    r = cs[cs.player == "Cristiano Ronaldo"].set_index("season")
    out += [
        ("ronaldo quality", f"({r.loc['2021-2022', 'efficiency']:.3f} per action, against "
                            f"{r.loc['2020-2021', 'efficiency']:.3f} at Juventus"),
        ("ronaldo share", f"smaller share ({r.loc['2021-2022', 'usage_on_pitch'] * 100:.0f}%, against "
                          f"{r.loc['2020-2021', 'usage_on_pitch'] * 100:.0f}%)"),
    ]
    sb = OUT / "sb_check.json"
    if sb.exists():
        b = json.loads(sb.read_text())
        out += [
            ("sb matches", f"{b['matches']:,} matches"),
            ("sb minutes", f"within a minute in {p(b['minutes']['sub_on_minute_within_1'], 0)} of cases"),
            ("sb new", f"new pairs changed by {p(b['pass_growth']['new']['growth'], 1, True)}"),
            ("sb established", f"established pairs by {p(b['pass_growth']['established']['growth'], 1, True)}"),
            ("sb gap", f"a gap of {p(b['pass_growth']['new_minus_established']['gap'], 1, True)} "
                       f"({p(b['pass_growth']['new_minus_established']['lo'], 1, True)} to "
                       f"{p(b['pass_growth']['new_minus_established']['hi'], 1, True)})"),
            ("sb links", f"correlation {b['links_agree']['corr']:.2f}, against {b['links_agree']['null_95']:.2f} by chance"),
            ("sb top fifth", f"set up {p(b['links_agree']['shot_ratio_top_fifth_pass_links'] - 1, 0)} more shots"),
        ]
    op = OUT / "opta" / "transfers.json"
    if op.exists():  # the Opta rerun on seven leagues (SHOTS=opta)
        o = json.loads(op.read_text())
        mo, s_ = o["movers_vs_stayers"], o["selling_leagues_into_big5"]
        sh = mo["mean_log_gap_by_part"]["His share of the ball"]
        out += [
            ("opta moves", f"| Moves / stays | {mv['n_movers']} / {mv['n_stayers']:,} | "
                           f"{mo['n_movers']} / {mo['n_stayers']:,} |"),
            ("opta share", f"{p(sh['point'], 1, True)} ({p(sh['lo'], 1, True)} to {p(sh['hi'], 1, True)}) |"),
            ("opta auc", f"{o['predict_flops']['auc']:.2f} ({o['predict_flops']['auc_lo']:.2f} to "
                         f"{o['predict_flops']['auc_hi']:.2f})"),
            ("selling moves", f"{s_['moves']} attackers moved from those leagues into the Big-5"),
            ("selling fall", f"fell by {p(-s_['mean_change']['point'], 0)} ({p(-s_['mean_change']['hi'], 0)} "
                             f"to {p(-s_['mean_change']['lo'], 0)}) and {p(s_['flop_rate']['point'], 0)} of them flopped"),
            ("selling player", f"unchanged ({p(s_['player_change']['point'], 1, True)}, "
                               f"{p(s_['player_change']['lo'], 1, True)} to {p(s_['player_change']['hi'], 1, True)})"),
        ]
    md = OUT / "mid" / "transfers.json"
    if md.exists():  # midfielders (SAMPLE=mid)
        mi = json.loads(md.read_text())["movers_vs_stayers"]
        sh, net = mi["mean_log_gap_by_part"]["His share of the ball"], mi["mean_log_gap"]
        out += [
            ("mid share", f"| {p(sh['point'], 1, True)} ({p(sh['lo'], 1, True)} to {p(sh['hi'], 1, True)}) |"),
            ("mid net", f"ends up {p(-net['point'])} behind players who stayed ({p(net['lo'], 1, True)} "
                        f"to {p(net['hi'], 1, True)})"),
            ("mid moves", f"| {mi['n_movers']} / {mi['n_stayers']:,} |"),
        ]
    extra = {k: OUT / f"{k}.json" for k in ("asa", "fpl", "injuries", "pass_checks")}
    if all(f.exists() for f in extra.values()):
        a_, f_, i_, pc = (json.loads(f.read_text()) for f in extra.values())
        am, aw = a_["movers_vs_stayers"], a_["within_player"]["per_5_points"]
        f5 = f_["pairs"]["2024-25 -> 2025-26"]["FWD+MID"]
        gi_ = i_["injuries"]["gap_movers__flop_rate"]
        wy = pc["wyscout"]["pass_growth"]["new_minus_established"]
        out += [
            ("mls share", f"share falls by {p(-am['share_of_ball']['point'])} ({p(am['share_of_ball']['lo'], 1, True)} "
                          f"to {p(am['share_of_ball']['hi'], 1, True)})"),
            ("mls flop", f"({p(am['flop_rate_movers']['point'], 0)} against {p(am['flop_rate_stayers']['point'], 0)}, "
                         f"a gap of {am['flop_rate_gap']['point'] * 100:+.1f} points"),
            ("mls within", f"chance quality {p(-aw['point'])} lower ({p(aw['lo'], 1, True)} to {p(aw['hi'], 1, True)})"),
            ("fpl", f"{f5['n_movers']} forwards and midfielders changed Premier League club with 900 minutes either "
                    f"side: {p(f5['flop_rate_movers']['point'], 0)} flopped against {p(f5['flop_rate_stayers']['point'], 0)}"),
            ("injury gap", f"a gap of {gi_['point'] * 100:+.1f} points ({gi_['lo'] * 100:+.1f} to "
                           f"{gi_['hi'] * 100:+.1f})".replace("-", M)),
            ("wyscout gap", f"{p(wy['gap'], 1, True)} ({p(wy['lo'], 1, True)} to {p(wy['hi'], 1, True)}) |"),
        ]
    return out


def main():
    readme = (ROOT / "README.md").read_text().replace("**", "")  # bold does not change a number
    fails = 0
    for name, text in checks():
        ok = text in readme
        fails += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {name}: {text}")
    print(f"\n{'all README numbers match data/' if not fails else f'{fails} README number(s) out of date'}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
