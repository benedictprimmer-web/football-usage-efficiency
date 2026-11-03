"""Check every number quoted in the README and docs/side_studies.md against data/.

Each check builds the exact text the README (or the side studies) should contain from the
data, and looks for it. Prints PASS or FAIL per line and exits non-zero on any failure, so
a stale README cannot survive a rebuild.

    python analysis/verify.py
"""
from __future__ import annotations

import json
import sys

import pandas as pd

from config import OUT, ROOT

M = "−"


def _z(s: str) -> str:
    """Minus signs, and no sign on a zero."""
    s = s.replace("-", M)
    for z in ("0.0", "0"):
        for sg in ("+", M):
            s = s.replace(f"({sg}{z}%", f"({z}%").replace(f" {sg}{z}%", f" {z}%")
    return s


def p(v, dp=1, sign=False):
    return _z(f"{v * 100:+.{dp}f}%" if sign else f"{v * 100:.{dp}f}%")


def n(v, dp=1):
    return f"{v * 100:.{dp}f}".replace("-", M)


def iv(x, dp=1):
    """'−4.2% (−6.0% to −2.5%)' from a {point, lo, hi} dict of fractions."""
    return f"{p(x['point'], dp, True)} ({p(x['lo'], dp, True)} to {p(x['hi'], dp, True)})"


def pts(x, word=True):
    """'+11.8 points (+8.0 to +15.4)' from fractions."""
    s = f"{x['point'] * 100:+.1f}{' points' if word else ''} ({x['lo'] * 100:+.1f} to {x['hi'] * 100:+.1f})"
    return s.replace("-", M)


def pp(x):
    """('+11.8', '+8.0', '+15.4'): point and interval in points, signed."""
    return tuple(f"{x[k] * 100:+.1f}".replace("-", M) for k in ("point", "lo", "hi"))


def r0(x):
    """'31% (27% to 34%)'."""
    return f"{p(x['point'], 0)} ({p(x['lo'], 0)} to {p(x['hi'], 0)})"


def band(v):  # [point, lo, hi] list -> '22% (20% to 24%)'
    return f"{p(v[0], 0)} ({p(v[1], 0)} to {p(v[2], 0)})"


def pv(v):
    return f"{v:.3f}" if v < 0.1 else f"{v:.2f}"


def auc(d, k="auc"):
    return f"{d[k]:.2f} ({d[k + '_lo']:.2f} to {d[k + '_hi']:.2f})"


def checks() -> list[tuple[str, str]]:
    t = json.loads((OUT / "transfers.json").read_text())
    o = json.loads((OUT / "opta" / "transfers.json").read_text())
    r = json.loads((OUT / "robustness.json").read_text())
    ro = json.loads((OUT / "opta" / "robustness.json").read_text())
    rm = json.loads((OUT / "mid" / "robustness.json").read_text())
    rmo = json.loads((OUT / "opta" / "mid" / "robustness.json").read_text())
    tm = json.loads((OUT / "mid" / "transfers.json").read_text())
    tmo = json.loads((OUT / "opta" / "mid" / "transfers.json").read_text())
    fz = json.loads((OUT / "frozen_score_2025_26.json").read_text())
    s = json.loads((OUT / "summary.json").read_text())
    mv, nb, nbs = t["movers_vs_stayers"], t["noise_benchmark"], t["noise_benchmark_stayers"]
    g = mv["mean_log_gap_by_part"]
    sl = pd.read_csv(OUT / "transfer_slices.csv")
    slo = pd.read_csv(OUT / "opta" / "transfer_slices.csv")
    ws = pd.read_csv(OUT / "within_slopes.csv").set_index("spec")
    pr, bc, u = t["predict_flops"], t["buying_club_persistence"], t["usage_in_flops"]
    reg, raw, rw = r["rtm"]["regression"], r["rtm"]["raw"], r["rtm"]["reweighted"]
    rego, rawo, rwo = ro["rtm"]["regression"], ro["rtm"]["raw"], ro["rtm"]["reweighted"]
    lp, lpo = r["lost_place"], ro["lost_place"]
    sf, sfo = r["slice_family"], ro["slice_family"]
    rp = r["predictor"]
    bsr = r["benchmark_share_redrawn"]
    st, sto = r["moves"]["buying_club_strength_pre_move"], ro["moves"]["buying_club_strength_pre_move"]

    def sl_row(dim, lev, grp="movers", d=sl):
        return d[(d.slice == dim) & (d.level == lev) & (d.group == grp)].iloc[0]

    def sl_rate(dim, lev, grp="movers"):
        return sl_row(dim, lev, grp).flop_rate

    def sl_iv(dim, lev, grp="movers"):
        x = sl_row(dim, lev, grp)
        return r0({"point": x.flop_rate, "lo": x.flop_lo, "hi": x.flop_hi})

    def spec(k):
        x = ws.loc[k]
        return (f"{x.pct_of_median:.1f}%".replace("-", M),
                f"{x.ci_lo_pct:.1f}% to {x.ci_hi_pct:+.1f}%".replace("-", M)
                .replace("+0.0%", "0.0%").replace("−0.0%", "0.0%"))

    def gi(x, dp=1):
        return p(x["point"], dp, True), f"{p(x['lo'], dp, True)} to {p(x['hi'], dp, True)}"

    def neg(x):  # 'fall by 2.5% (−4.7% to −0.5%)'
        return f"{p(-x['point'])} ({p(x['lo'], 1, True)} to {p(x['hi'], 1, True)})"

    def fam(d, k):
        return d[k]

    def row(label, key):
        return (f"| {label} | {iv(raw[key])} | {iv(reg[key])} | {iv(rawo[key])} | {iv(rego[key])} |")

    holm_age = sf["age 26–28: movers v stayers"]
    out = [
        # first screen
        ("share matched", f"{p(reg['d_share']['point'], 1, True)} (95% interval {p(reg['d_share']['lo'], 1, True)} to "
                          f"{p(reg['d_share']['hi'], 1, True)}) on Understat, {iv(rego['d_share'])} on Opta"),
        ("output matched", f"{iv(reg['d_out'])} on Understat, {iv(rego['d_out'])} on Opta"),
        ("raw output gap", f"The raw gap of {p(raw['d_out']['point'], 1, True)}"),
        ("lost headline", f"{p(lp['bad_movers']['point'], 0)} of movers flop or fall below 900 league minutes "
                          f"the next season, against {p(lp['bad_stayers']['point'], 0)} of stayers, "
                          "{} points after matching ({} to {}); ".format(*pp(lp['regression']['bad_gap']))
                          + f"on Opta {pts(lpo['regression']['bad_gap'])}"),
        ("luck first screen", f"({p(nb['flop_rate_observed'], 0)} against {p(nb['flop_rate_noise_only'][0], 0)})"),
        ("opta age gap", "{} points after age, {} to {}".format(*pp(o['age_adjusted']['flop_rate_gap']))),
        ("sample", f"{lp['n_movers']} moves with {lp['n_stayers']:,} stays"),
        ("kept", f"{lp['n_movers_kept']} of the {lp['n_movers']} movers and {lp['n_stayers_kept']:,} of the "
                 f"{lp['n_stayers']:,} stayers"),
        # why it matters
        ("lost movers", f"({p(lp['lost_movers']['point'], 0)}, {p(lp['lost_movers']['lo'], 0)} to "
                        f"{p(lp['lost_movers']['hi'], 0)}), against one stayer in five "
                        f"({p(lp['lost_stayers']['point'], 0)}, {p(lp['lost_stayers']['lo'], 0)} to "
                        f"{p(lp['lost_stayers']['hi'], 0)})"),
        ("own matched", f"per 90 fall by {neg(reg['d_own'])} against matched stayers"),
        # status of tests
        ("holm predictor", f"(p = {pv(fam(sf, 'predictor: AUC above 0.5')['p'])}, adjusted "
                           f"{pv(fam(sf, 'predictor: AUC above 0.5')['p_holm'])})"),
        ("holm age", f"p = {pv(holm_age['p'])}, adjusted {pv(holm_age['p_holm'])}"),
        ("holm opta", f"predictor (adjusted {pv(sfo['predictor: AUC above 0.5']['p_holm'])}) and the league "
                      f"path (adjusted {pv(sfo['league: changed v same']['p_holm'])})"),
        # usage table
        ("rtm share", row("His share of the ball", "d_share")),
        ("rtm own", row("His own shots and shot-assists per 90", "d_own")),
        ("rtm team", row("His team's actions per 90, without him", "d_team_ex")),
        ("rtm out", row("Output per 90", "d_out")),
        ("rtm flop", f"| Flop rate, points | {pts(raw['flopf'], False)} | {pts(reg['flopf'], False)} | "
                     f"{pts(rawo['flopf'], False)} | {pts(rego['flopf'], False)} |"),
        ("last season", f"median share was {p(r['rtm']['movers_last_season']['share_movers'])} against "
                        f"{p(r['rtm']['movers_last_season']['share_stayers'])}"),
        ("reweighted", f"{iv(rw['d_share'])} on Understat and {iv(rwo['d_share'])} on Opta"),
        ("denominator", f"his own actions per 90 fall by {p(-raw['d_own']['point'])} and the team's rise by "
                        f"{p(raw['d_team']['point'])}"),
        ("denominator share", f"of the {p(-raw['d_share']['point'])[:-1]} points"),
        ("own after", f"After matching, his own actions fall by {p(-reg['d_own']['point'])}"),
        ("strength", f"made {p(st['team_actions_per_match_change']['point'])} "
                     f"({p(st['team_actions_per_match_change']['lo'])} to {p(st['team_actions_per_match_change']['hi'])}) more"),
        ("strength opta", f"(Opta {p(sto['team_actions_per_match_change']['point'])}, "
                          f"{p(sto['team_actions_per_match_change']['lo'])} to {p(sto['team_actions_per_match_change']['hi'])})"),
        ("stronger", f"and {r0(st['share_joining_stronger'])} of movers joined"),
        # lost place table
        ("lost row", f"| Below 900 minutes the next season | {r0(lp['lost_movers'])} | {r0(lp['lost_stayers'])} | "
                     f"{r0(lpo['lost_movers'])} | {r0(lpo['lost_stayers'])} |"),
        ("bad row", f"| Flop or below 900 minutes | {r0(lp['bad_movers'])} | {r0(lp['bad_stayers'])} | "
                    f"{r0(lpo['bad_movers'])} | {r0(lpo['bad_stayers'])} |"),
        ("gap row", f"| Gap, matched | {pts(lp['regression']['bad_gap'])} | | {pts(lpo['regression']['bad_gap'])} | |"),
        ("lost age", "age adjustment ({} points, {} to {})".format(*pp(lp['age_adjusted']['bad_gap']))),
        # luck
        ("luck movers row", f"| Moved club | {r0(mv['flop_rate_movers'])} | {band(nb['flop_rate_noise_only'])} | "
                            f"{band(bsr['movers']['flop_rate_role_and_quality_fixed'])} | "
                            f"{p(nb['player_share_observed'], 0)} | {band(nb['player_share_noise_only'])} |"),
        ("luck stayers row", f"| Stayed | {r0(mv['flop_rate_stayers'])} | {band(nbs['flop_rate_noise_only'])} | "
                             f"{band(bsr['stayers']['flop_rate_role_and_quality_fixed'])} | "
                             f"{p(nbs['player_share_observed'], 0)} | {band(nbs['player_share_noise_only'])} |"),
        ("player part", f"({p(nb['player_share_observed'], 0)} against {p(nb['player_share_noise_only'][1], 0)} "
                        f"to {p(nb['player_share_noise_only'][2], 0)})"),
        ("noise share", f"About {r0(r['luck_spread_share_ci'])} of the spread"),
        ("opta luck", f"movers flop {r0(o['movers_vs_stayers']['flop_rate_movers'])} of the time against "
                      f"{p(o['noise_benchmark']['flop_rate_noise_only'][0], 0)} from luck"),
        ("usage movers", f"accounts for {r0(u['movers_share_of_fall'])} of the average mover's flop"),
        ("usage undone", f"{p(u['movers_flops_undone']['point'], 0)} of movers' flops "
                         f"({p(u['movers_flops_undone']['lo'], 0)} to {p(u['movers_flops_undone']['hi'], 0)})"),
        # who flops
        ("fam predictor", f"| Predictor, AUC above 0.5 | {pr['auc']:.2f} ({pr['auc_lo']:.2f} to {pr['auc_hi']:.2f}) | "
                          f"{pv(sf['predictor: AUC above 0.5']['p'])} | {pv(sf['predictor: AUC above 0.5']['p_holm'])} |"),
        ("fam age", f"| Age 26–28, movers v stayers | {pts(holm_age['estimate'])} | {pv(holm_age['p'])} | "
                    f"{pv(holm_age['p_holm'])} |"),
        ("fam fee", "| Fee under €10m v other movers | {} | {} | {} |".format(
            pts(sf['fee Under €10m: v other movers']['estimate']), pv(sf['fee Under €10m: v other movers']['p']),
            pv(sf['fee Under €10m: v other movers']['p_holm']))),
        ("fam league", "| Changed league v same league | {} | {} | {} |".format(
            pts(sf['league: changed v same']['estimate']), pv(sf['league: changed v same']['p']),
            pv(sf['league: changed v same']['p_holm']))),
        ("fam clubs", f"| Buying clubs, early v late record | rank correlation {bc['spearman_early_late']:.2f} | "
                      f"{pv(bc['perm_p'])} | {pv(sf['buying clubs: early v late record']['p_holm'])} |".replace("-", M)),
        ("age movers", f"26 to 28 flop {sl_iv('age_band', '26–28')} of the time, against "
                       f"{sl_iv('age_band', '26–28', 'stayers')} for stayers"),
        ("league", f"new league flop {sl_iv('path', 'Changed league')} of the time, against "
                   f"{sl_iv('path', 'Same league')} for movers"),
        ("league opta", f"the gap is {pts(sfo['league: changed v same']['estimate'])}"),
        ("fee 30m", f"{p(sl_rate('fee_band', 'Over €30m'), 0)} of moves over €30m"),
        ("fee 10-30", f"{p(sl_rate('fee_band', '€10m–30m'), 0)} at €10–30m"),
        ("fee <10", f"{p(sl_rate('fee_band', 'Under €10m'), 0)} under €10m"),
        ("fee free", f"{p(sl_rate('fee_band', 'Free or loan'), 0)} of free or loan moves"),
        ("fee none", f"{int(sl[(sl.slice == 'fee_band') & (sl.level == 'No fee on record')].n.iloc[0])} moves "
                     f"have no fee on record"),
        ("clubs", f"only {bc['clubs']} clubs made enough signings"),
        ("clubs rho", f"(rank correlation {bc['spearman_early_late']:.2f}, p = {bc['perm_p']:.2f})".replace("-", M)),
        # predictor
        ("auc", f"out-of-time AUC of {pr['auc']:.2f} ({pr['auc_lo']:.2f} to {pr['auc_hi']:.2f})"),
        ("test moves", f"tested on 2020–21 onwards ({pr['test_moves']} moves)"),
        ("risk fifth", f"flop {p(pr['flop_rate_top_fifth_of_risk'], 0)} of the time, against "
                       f"{p(pr['flop_rate_rest'], 0)} for the rest"),
        ("auc all", f"{auc(rp['all_moves_flop_or_lost_place'])} for \"flop or lost his place\" across "
                    f"{rp['all_moves_flop_or_lost_place']['test_moves']} test moves"),
        ("auc as not flop", f"non-flops gives {auc(rp['all_moves_lost_place_counted_as_not_flop'])}"),
        ("auc lost", f"lost places alone {auc(rp['all_moves_lost_place_only'])}"),
        ("frozen n", f"predictions for {fz['moves']} moves into 2025–26"),
        ("frozen lost", f"{fz['lost_place']} of the {fz['moves']} fell below 900 league minutes"),
        ("frozen auc", f"AUC of {auc(fz, 'auc_lost_place').replace(' (', ' (', 1)}".replace(
            f"{fz['auc_lost_place']:.2f} ({fz['auc_lost_place_lo'] if 'auc_lost_place_lo' in fz else 0}", "")
         if False else f"AUC of {fz['auc_lost_place']:.2f} ({fz['auc_lo']:.2f} to {fz['auc_hi']:.2f})"),
        # robustness
        ("opta share", f"({p(rawo['d_share']['point'], 1, True)} raw, {p(rego['d_share']['point'], 1, True)} matched)"),
        ("opta out", f"({p(rawo['d_out']['point'], 1, True)}, {p(rawo['d_out']['lo'], 1, True)} to "
                     f"{p(rawo['d_out']['hi'], 1, True)})"),
        ("opta auc", f"{o['predict_flops']['auc']:.2f} ({o['predict_flops']['auc_lo']:.2f} to "
                     f"{o['predict_flops']['auc_hi']:.2f}) out of time"),
        ("mid share", f"share falls by {neg(tm['movers_vs_stayers']['mean_log_gap_by_part']['His share of the ball'])} "
                      f"raw and {neg(rm['rtm']['regression']['d_share'])} matched"),
        ("mid out", f"output per 90 falls by {neg(tm['movers_vs_stayers']['mean_log_gap'])}"),
        ("mid flop", f"They flop {r0(tm['movers_vs_stayers']['flop_rate_movers'])} of the time against "
                     f"{r0(tm['movers_vs_stayers']['flop_rate_stayers'])} for midfielders who stay"),
        ("mid age", "{} points after age ({} to {})".format(*pp(tm['age_adjusted']['flop_rate_gap']))),
        ("mid lost", f"{p(rm['lost_place']['bad_movers']['point'], 0)} of them flop or lose their place against "
                     f"{p(rm['lost_place']['bad_stayers']['point'], 0)} of stayers "
                     + "({} points matched, {} to {})".format(*pp(rm['lost_place']['regression']['bad_gap']))),
        ("mid opta", f"On Opta the share falls by "
                     f"{neg(tmo['movers_vs_stayers']['mean_log_gap_by_part']['His share of the ball'])}"),
        ("loans", f"({r['moves']['n_loans']} moves). Without them the share gap is "
                  f"{iv(r['moves']['without_loans']['share_gap'])}"),
        ("promoted", f"Without the {r['moves']['n_promoted_buyer']} moves to promoted clubs and "
                     f"{r['moves']['n_relegated_seller']} from relegated clubs it is "
                     f"{iv(r['moves']['without_promoted_or_relegated']['share_gap'])}"),
        ("pairs", f"{s['n_pairs']:,} pairs of seasons from {int(ws.loc['on_pitch', 'n_players'])} players"),
        ("headline", f"chance quality {abs(s['headline_pct_of_median']['point']):.1f}% lower (95% interval "
                     f"{s['headline_pct_of_median']['lo']:.1f}% to {s['headline_pct_of_median']['hi']:.1f}%)".replace("-", M)),
        ("scale", f"cuts a player's share by about {abs(g['His share of the ball']['point']) * s['median_usage_on_pitch'] * 100:.1f} "
                  f"points ({abs(g['His share of the ball']['point']) * 100:.1f}% of a {s['median_usage_on_pitch'] * 100:.0f}% share), "
                  f"which on this slope is worth about "
                  f"{abs(g['His share of the ball']['point']) * s['median_usage_on_pitch'] * 100 / 5 * abs(s['headline_pct_of_median']['point']):.1f}%"),
        # limits
        ("corr", f"correlate {r['rtm']['corr_team_share']:.2f}".replace("-", M)
                 + "; in his quality and team-mates' quality "
                 + f"{r['rtm']['corr_rel_mates']:.2f})".replace("-", M)),
        # details
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

    # MLS (README robustness)
    a_ = json.loads((OUT / "asa.json").read_text())
    am = a_["movers_vs_stayers"]
    out += [
        ("mls share", f"share falls by {p(-am['share_of_ball']['point'])} ({p(am['share_of_ball']['lo'], 1, True)} "
                      f"to {p(am['share_of_ball']['hi'], 1, True)})"),
        ("mls team", f"({p(am['team_chances_per90']['point'], 1, True)}, {p(am['team_chances_per90']['lo'], 1, True)} "
                     f"to {p(am['team_chances_per90']['hi'], 1, True)})"),
        ("mls flop", f"({p(am['flop_rate_movers']['point'], 0)} against {p(am['flop_rate_stayers']['point'], 0)}, "
                     + "a gap of {} points, {} to {})".format(*pp(am['flop_rate_gap']))),
        ("mls n", f"{am['n_movers']} attacker moves"),
    ]
    return out


def side_checks() -> list[tuple[str, str]]:
    """Numbers in docs/side_studies.md."""
    c = json.loads((OUT / "chemistry.json").read_text())
    cs = pd.read_csv(OUT / "case_studies.csv")
    o = json.loads((OUT / "opta" / "transfers.json").read_text())
    s_ = o["selling_leagues_into_big5"]
    out = [
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
        ("selling moves", f"{s_['moves']} attackers moved from those leagues into the Big-5"),
        ("selling fall", f"fell by {p(-s_['mean_change']['point'], 0)} ({p(-s_['mean_change']['hi'], 0)} "
                         f"to {p(-s_['mean_change']['lo'], 0)}) and {p(s_['flop_rate']['point'], 0)} of them flopped"),
        ("selling player", f"unchanged ({p(s_['player_change']['point'], 1, True)}, "
                           f"{p(s_['player_change']['lo'], 1, True)} to {p(s_['player_change']['hi'], 1, True)})"),
    ]
    d = cs[cs.player == "Memphis Depay"].set_index("season")
    out += [
        ("depay share utd", f"United in 2015–16 ({d.loc['2015-2016', 'usage_on_pitch'] * 100:.0f}%)"),
        ("depay share lyon", f"Lyon in 2017–18 ({d.loc['2017-2018', 'usage_on_pitch'] * 100:.0f}%)"),
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
    b = json.loads((OUT / "sb_check.json").read_text())
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
    f_, i_, pc = (json.loads((OUT / f"{k}.json").read_text()) for k in ("fpl", "injuries", "pass_checks"))
    f5 = f_["pairs"]["2024-25 -> 2025-26"]["FWD+MID"]
    inj = i_["injuries"]
    gi_ = inj["gap_movers__flop_rate"]
    con = i_["contracts"]
    wy = pc["wyscout"]["pass_growth"]["new_minus_established"]
    out += [
        ("fpl", f"{f5['n_movers']} forwards and midfielders changed Premier League club with 900 minutes either "
                f"side: {p(f5['flop_rate_movers']['point'], 0)} flopped ({p(f5['flop_rate_movers']['lo'], 0)} to "
                f"{p(f5['flop_rate_movers']['hi'], 0)}) against {r0(f5['flop_rate_stayers'])} of "
                f"{f5['n_stayers']} who stayed"),
        ("injured", f"flopped {r0(inj['movers_injured']['flop_rate'])} of the time "
                    f"({inj['movers_injured']['n']} moves), against {r0(inj['movers_fit']['flop_rate'])}"),
        ("injury gap", f"a gap of {gi_['point'] * 100:+.1f} points ({gi_['lo'] * 100:+.1f} to "
                       f"{gi_['hi'] * 100:+.1f})".replace("-", M)),
        ("free", f"flopped {r0(con['free_movers']['flop_rate'])} of the time, against "
                 f"{r0(con['paid_movers']['flop_rate'])} where a fee was paid"),
        ("wyscout gap", f"{p(wy['gap'], 1, True)} ({p(wy['lo'], 1, True)} to {p(wy['hi'], 1, True)}) |"),
    ]
    return out


def main():
    fails = 0
    for fname, fn in (("README.md", checks), ("docs/side_studies.md", side_checks)):
        text = (ROOT / fname).read_text().replace("**", "")  # bold does not change a number
        for name, want in fn():
            ok = want in text
            fails += not ok
            print(f"{'PASS' if ok else 'FAIL'}  {fname}: {name}: {want}")
    print(f"\n{'all README numbers match data/' if not fails else f'{fails} README number(s) out of date'}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
