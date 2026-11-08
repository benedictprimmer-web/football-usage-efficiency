"""Draw every figure and the one-page summary from the aggregate tables in data/.

House style: one blue highlight, near-black for the player, greys for context; a title
that states the finding; values labelled on the chart; 4:5 PNGs (1440 x 1800 px) that
read at phone width; SVG copies for print.

    python analysis/figures.py
"""
from __future__ import annotations

import json
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402

from config import OUT, FIG, ROOT  # noqa: E402

BLUE, BLUE2, BLUE3, BLUE4 = "#1B64C2", "#6FA2E3", "#B7D2F3", "#EAF2FC"
PLAYER = "#1D1D1B"
TEXT, TEXT2, LIGHT, RULE = "#3D3D3A", "#767671", "#B9B8B3", "#DDDCD7"
BG = "#FFFFFF"
MINUS = "−"
REPO = "github.com/benedictprimmer-web/football-usage-efficiency"
SOURCE_LINE = f"Data: Understat, Transfermarkt\nBen Rimmer · {REPO}"
SOURCE_BOTH = f"Data: Understat, Opta via FBref, Transfermarkt\nBen Rimmer · {REPO}"

plt.rcParams.update({
    "font.family": ["Helvetica Neue", "Arial", "DejaVu Sans"], "font.size": 11.5,
    "axes.edgecolor": LIGHT, "axes.labelcolor": TEXT2, "xtick.color": TEXT2,
    "ytick.color": TEXT2, "xtick.labelsize": 10.5, "ytick.labelsize": 10.5,
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
    "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
    "svg.fonttype": "none", "pdf.fonttype": 42,
    "svg.hashsalt": "football-usage-efficiency",   # stable ids, so a rebuild changes nothing
})
PNG_META, SVG_META, PDF_META = {"Software": None}, {"Date": None}, {"CreationDate": None, "ModDate": None}

W, H = 4.8, 6.0          # inches: 4:5, 1440 x 1800 px at 300 dpi
L, R = 0.25 / W, 1 - 0.25 / W


def pct(v, dp=1, sign=True):
    s = f"{v * 100:+.{dp}f}%" if sign else f"{v * 100:.{dp}f}%"
    return s.replace("-", MINUS)


def ci(lo, hi, dp=1):
    """'(1.1, 4.8)' in percentage points, with proper minus signs."""
    z = f"{0:.{dp}f}"
    return (f"({lo * 100:.{dp}f}, {hi * 100:.{dp}f})".replace(f"-{z},", f"{z},")
            .replace(f"-{z})", f"{z})").replace("-", MINUS))


def fill(s: str, width_in: float, fontsize: float, bold=False) -> str:
    """Wrap to a width in inches (Helvetica averages about half an em per character)."""
    per = fontsize * (0.56 if bold else 0.5) / 72
    return textwrap.fill(s, max(int(width_in / per), 10), break_on_hyphens=False)


def wrapped(fig, x, y, s, width_in, fontsize=10.5, **kw):
    """Figure text wrapped to a fixed width; returns its height as a figure fraction."""
    t = fill(s, width_in, fontsize, kw.get("fontweight") == "bold")
    fig.text(x, y, t, fontsize=fontsize, linespacing=1.25, **kw)
    # matplotlib's line pitch is about 1.4 x the font size at linespacing 1.25, so measure
    # with that, or a wrapped title runs into the text under it
    return (t.count("\n") + 1) * fontsize * 1.42 / 72 / fig.get_figheight()


def frame(title: str, sub: str, source: str = SOURCE_LINE, w=W, h=H):
    """A figure with the house header (blue tab, title, subtitle) and source line.
    Returns the figure and the y (figure fraction) where the header ends."""
    fig = plt.figure(figsize=(w, h))
    fig.patches.append(plt.Rectangle((L, 1 - 0.22 / h), 0.5 / w, 0.04 / h, color=BLUE,
                                     transform=fig.transFigure, figure=fig))
    y = 1 - 0.32 / h
    y -= wrapped(fig, L, y, title, (R - L) * w, fontsize=16.5, fontweight="bold",
                 color=PLAYER, va="top") + 0.1 / h
    y -= wrapped(fig, L, y, sub, (R - L) * w, fontsize=10, color=TEXT2, va="top")
    fig.text(L, 0.14 / h, source, fontsize=7, color=TEXT2, va="bottom", linespacing=1.3)
    return fig, y - 0.3 / h


def save(fig, name):
    FIG.mkdir(exist_ok=True)
    fig.savefig(FIG / f"{name}.png", dpi=300, metadata=PNG_META)
    fig.savefig(FIG / f"{name}.svg", metadata=SVG_META)
    plt.close(fig)


def flat(ax, ticks, labels):
    ax.set_yticks([])
    ax.set_xticks(ticks)
    ax.set_xticklabels(labels)
    ax.tick_params(axis="x", length=0)
    ax.spines["bottom"].set_color(RULE)


# ------------------------------------------------------------------ the charts

MOVE_ROWS = [("d_share", "His share of the ball"),
             ("d_team", "Chances his team creates"),
             ("d_mates", "Quality of team-mates' chances"),
             ("d_rel", "His own quality v team-mates")]


def draw_move(ax, r, fs=1.0):
    """Movers minus stayers with the same last season (deciles of share and of output per
    90, age band, season), part by part. His share of the ball is the one highlight."""
    g = r["rtm"]["regression"]
    vals = [g[k] for k, _ in MOVE_ROWS] + [g["d_out"]]
    labels = [lab for _, lab in MOVE_ROWS] + ["Output per 90, net"]
    y = np.arange(len(vals))[::-1].astype(float) * 1.45
    y[-1] -= 0.5
    for i, v in enumerate(vals):
        last = i == len(vals) - 1
        col = BLUE if i == 0 else (TEXT2 if last else LIGHT)
        txt = BLUE if i == 0 else TEXT2
        p = v["point"] * 100
        ax.barh(y[i], p, height=0.55, color=col)
        ax.plot([v["lo"] * 100, v["hi"] * 100], [y[i] - 0.42] * 2, color=col, lw=1.6, solid_capstyle="butt")
        side = 1 if p >= 0 else -1
        ax.text(p + 0.3 * side, y[i] + 0.02, pct(v["point"]), va="center",
                ha="left" if side > 0 else "right", fontsize=11 * fs, fontweight="bold",
                color=txt)
        # the interval sits on the same line: beyond the value, or across the zero line
        # for a fall, where the left edge has no room
        if side > 0:
            ax.annotate(ci(v["lo"], v["hi"]), (p + 0.3, y[i] + 0.02), xytext=(44 * fs, 0),
                        textcoords="offset points", va="center", fontsize=8 * fs, color=TEXT2)
        else:
            ax.text(0.3, y[i] + 0.02, ci(v["lo"], v["hi"]), va="center", fontsize=8 * fs,
                    color=TEXT2)
        ax.text(-7.8, y[i] + 0.36, labels[i], fontsize=10 * fs, va="bottom",
                color=BLUE if i == 0 else (PLAYER if last else TEXT),
                fontweight="bold" if i == 0 or last else "normal")
    ax.axvline(0, color=TEXT, lw=0.9)
    ax.axhline((y[-2] + y[-1]) / 2 + 0.05, color=RULE, lw=0.8)
    ax.set_xlim(-7.8, 7.8)
    ax.set_ylim(y[-1] - 0.75, y[0] + 1.0)
    flat(ax, [-6, -3, 0, 3, 6], [f"{MINUS}6%", f"{MINUS}3%", "0", "+3%", "+6%"])
    ax.spines["bottom"].set_visible(False)
    ax.annotate("← lower after the move", (0, 0), xytext=(0, -24), xycoords="axes fraction",
                textcoords="offset points", fontsize=8.5 * fs, color=TEXT2)
    ax.annotate("higher →", (1, 0), xytext=(0, -24), xycoords="axes fraction",
                textcoords="offset points", fontsize=8.5 * fs, color=TEXT2, ha="right")


def fig_move(r):
    sh = r["rtm"]["movers_last_season"]["share_movers"]
    d = r["rtm"]["regression"]["d_share"]["point"]
    fig, top = frame(f"A mover who keeps his place has about {abs(d) * 100:.0f}% less of the ball, "
                     f"and no measurable change in output per 90",
                     f"Movers minus matched stayers, % change in each part of xG+xA per 90. Only "
                     f"players who kept 900 minutes ({r['n_movers']} moves, {r['n_stayers']:,} stays). "
                     f"Lines: 95% intervals")
    ax = fig.add_axes([L, 0.14, R - L, top - 0.15])
    draw_move(ax, r)
    save(fig, "fig0_what_a_move_does")


def draw_luck(ax, t, fs=1.0):
    """Observed flop rates against the rate with the player's quality held fixed."""
    nb, ns, mv = t["noise_benchmark"], t["noise_benchmark_stayers"], t["movers_vs_stayers"]
    rows = [
        ("Moved club", mv["flop_rate_movers"]["point"], mv["flop_rate_movers"]["lo"],
         mv["flop_rate_movers"]["hi"], BLUE),
        ("Moved, luck only", *nb["flop_rate_noise_only"], TEXT2),
        ("Stayed", mv["flop_rate_stayers"]["point"], mv["flop_rate_stayers"]["lo"],
         mv["flop_rate_stayers"]["hi"], PLAYER),
        ("Stayed, luck only", *ns["flop_rate_noise_only"], LIGHT),
    ]
    for i, (lab, p, lo, hi, c) in enumerate(rows):
        y = 3 - i - (0.3 if i >= 2 else 0)
        ax.plot([lo * 100, hi * 100], [y, y], color=c, lw=7, alpha=0.18, solid_capstyle="round")
        ax.plot(p * 100, y, "o", ms=9, color=c)
        ax.text(p * 100, y + 0.24, pct(p, 0, False), ha="center", va="bottom",
                fontsize=11 * fs, fontweight="bold", color=c)
        ax.text(0, y, lab + "  ", ha="right", va="center", fontsize=10 * fs, color=TEXT,
                transform=ax.get_yaxis_transform())
    ax.set_xlim(12, 26)
    ax.set_ylim(-0.9, 3.8)
    flat(ax, [15, 20, 25], ["15%", "20%", "25%"])


def fig_luck(t):
    nb = t["noise_benchmark"]
    p = nb["player_share_noise_only"]
    pp_ = json.loads((OUT / "rivals.json").read_text())["player_part_among_flops"]["movers"]
    fig, top = frame("Movers' flop rate sits inside a luck benchmark too noisy to see a small rise",
                     "Regulars on Understat: share of seasons where output per 90 fell by more "
                     "than 25%. For \"luck only\", each season keeps its real change of team and "
                     "role, and his chance quality is redrawn from his own shots (200 runs). "
                     "Bands: 95% intervals")
    ax = fig.add_axes([L + 0.3, top - 0.31, R - L - 0.3, 0.29])
    draw_luck(ax, t)
    wrapped(fig, L, top - 0.38,
            f"His own part of a flop: {pct(pp_['point'], 0, False)} ({pct(pp_['lo'], 0, False)}, "
            f"{pct(pp_['hi'], 0, False)}) in the data, {pct(p[0], 0, False)} ({pct(p[1], 0, False)}, "
            f"{pct(p[2], 0, False)}) from luck. The benchmark cannot see a rise of 1 to 3 points.",
            (R - L) * W, fontsize=10, color=PLAYER, va="top")
    save(fig, "fig1_flops_look_like_luck")


AGES = ["Under 23", "23–25", "26–28", "29 and over"]


def draw_age(ax, sl, ag, fs=1.0, highlight=False):
    """Movers minus stayers in flop rate, by age band, with 95% intervals."""
    for i, b in enumerate(AGES):
        y = len(AGES) - 1 - i
        g = ag[ag.age_band == b].iloc[0]
        hl = highlight and b == "26–28"
        c = BLUE if hl else LIGHT
        ax.plot([g.lo * 100, g.hi * 100], [y, y], color=c, lw=2.5, solid_capstyle="butt")
        ax.plot(g.gap * 100, y, "o", ms=8, color=BLUE if hl else TEXT2)
        ax.text(26, y, (f"{g.gap * 100:+.0f}" if round(g.gap * 100) != 0 else "0").replace("-", MINUS), va="center", ha="right",
                fontsize=10.5 * fs, fontweight="bold", color=BLUE if hl else TEXT2)
        ax.text(0, y, b + "  ", va="center", ha="right", fontsize=10 * fs, color=TEXT,
                transform=ax.get_yaxis_transform())
    ax.axvline(0, color=TEXT, lw=0.8)
    ax.set_xlim(-12, 26)
    ax.set_ylim(-0.6, len(AGES) - 0.4)
    flat(ax, [-10, 0, 10, 20], [f"{MINUS}10", "0", "+10", "+20 points"])


def fig_age(sl, ag, holm):
    g = ag[ag.age_band == "26–28"].iloc[0]
    fig, top = frame("Only the 26 to 28 band clears zero, and it fails a correction for 11 tests",
                     "Flop rate (output per 90 down by more than 25%) after a club move, minus "
                     "the rate for players of the same age who stayed, in percentage points. "
                     "Age on 1 September of the first season. Lines: 95% intervals")
    ax = fig.add_axes([L + 0.24, top - 0.38, R - L - 0.25, 0.36])
    draw_age(ax, sl, ag)
    wrapped(fig, L, top - 0.45,
            f"At 26–28: {g.gap * 100:+.0f} points ({g.lo * 100:.0f}, {g.hi * 100:.0f}), "
            f"p = {holm['p']:.3f}, or {holm['p_holm']:.2f} after the Holm correction. A lead "
            f"to test on new seasons."
            .replace("-", MINUS),
            (R - L) * W, fontsize=10, color=TEXT, va="top")
    save(fig, "fig2_age")


SPEC_NAMES = {
    "on_pitch_split_half": ("Per 90, split-half", "share and quality from different matches"),
    "on_pitch": ("Per 90, same matches", "shared noise left in"),
    "all_vs_mates": ("Against team-mates", "team quality cancels out"),
    "baseline": ("Plus last season's quality", "allows for regression to the mean"),
    "stayers": ("Same club both seasons", ""),
    "movers": ("Changed club", ""),
    "movers_vs_mates": ("Changed club, v new team-mates", ""),
    "naive": ("Season totals, not per 90", "playing time hides the effect"),
}


def draw_within(ax, ws, fs=1.0):
    w = ws.set_index("spec")
    order = list(SPEC_NAMES)
    for i, k in enumerate(order):
        r = w.loc[k]
        y = len(order) - 1 - i
        head = i == 0
        if head:
            ax.axhspan(y - 0.48, y + 0.48, color=BLUE4, zorder=0)
        c = BLUE if head else TEXT
        ax.plot([r.ci_lo_pct, r.ci_hi_pct], [y, y], color=c, lw=2, solid_capstyle="butt")
        ax.plot(r.pct_of_median, y, "o", ms=6.5, color=c)
        lab, note = SPEC_NAMES[k]
        ax.text(-14, y + (0.14 if note else 0), lab, fontsize=9.5 * fs, va="center",
                color=PLAYER if head else TEXT, fontweight="bold" if head else "normal")
        if note:
            ax.text(-14, y - 0.27, note, fontsize=8 * fs, va="center", color=TEXT2)
        ax.text(5, y, (f"{r.pct_of_median:+.1f}%" if round(r.pct_of_median, 1) != 0 else "0.0%").replace("-", MINUS), fontsize=9.5 * fs,
                va="center", ha="right", color=c, fontweight="bold" if head else "normal")
    ax.axvline(0, color=TEXT, lw=0.8)
    ax.set_xlim(-14, 5)
    ax.set_ylim(-0.7, len(order) - 0.45)
    flat(ax, [-6, -4, -2, 0, 2], [f"{MINUS}6", f"{MINUS}4", f"{MINUS}2", "0", "+2%"])
    ax.spines["bottom"].set_bounds(-6.5, 2.8)


def fig_within(ws, s):
    h = s["headline_pct_of_median"]
    fig, top = frame(f"Five more points of the ball comes with chances about "
                     f"{abs(h['point']):.1f}% worse",
                     f"Same player, consecutive seasons: change in xG+xA per shot or "
                     f"shot-assist for 5 more points of his share of the team's, while on the "
                     f"pitch. {s['n_pairs']:,} pairs of seasons, 95% intervals. Not shown: season "
                     f"share with minutes held fixed, {ws.set_index('spec').loc['minutes', 'pct_of_median']:+.1f}%"
                     .replace("-", MINUS))
    ax = fig.add_axes([L, 0.12, R - L, top - 0.13])
    draw_within(ax, ws)
    save(fig, "fig3_within_player")


def draw_chem(ax, ds, fs=1.0):
    y = np.arange(len(ds))[::-1]
    for i, (yi, r) in enumerate(zip(y, ds.itertuples())):
        c, line = (BLUE, BLUE2) if i == 0 else (TEXT2, LIGHT)   # new pairs are the highlight
        ax.plot([(r.lo - 1) * 100, (r.hi - 1) * 100], [yi, yi], color=line, lw=2)
        ax.plot((r.chemistry - 1) * 100, yi, "o", ms=8, color=c)
        ax.text(0, yi, r.prior_minutes + "  ", va="center", ha="right", fontsize=10 * fs,
                color=TEXT, transform=ax.get_yaxis_transform())
        ax.text(5.8, yi, f"{(r.chemistry - 1) * 100:+.1f}%".replace("-", MINUS), va="center",
                ha="right", fontsize=10 * fs, color=c, fontweight="bold")
    ax.axvline(0, color=TEXT, lw=0.8)
    ax.set_xlim(-6, 6)
    ax.set_ylim(-0.7, len(ds) - 0.3)
    flat(ax, [-4, -2, 0, 2, 4], [f"{MINUS}4", f"{MINUS}2", "0", "+2", "+4%"])


def fig_chem(ds, c):
    g, n = c["growth_within_first_season"], c["growth_next_season"]
    fig, top = frame("No sign that time together makes team-mates link up more",
                     "Shots one player set up for the other, against the rate their own "
                     "habits and minutes together predict, by minutes already played together "
                     "at the club. Pair-seasons with 450+ minutes together, 95% intervals")
    ax = fig.add_axes([L + 0.3, top - 0.38, R - L - 0.3, 0.36])
    draw_chem(ax, ds)
    wrapped(fig, L, top - 0.47,
            f"The bars compare whole pair-seasons. Two separate tests within the same pairs: "
            f"new pairs in the second half of their first season against the first, "
            f"{pct(g['growth'])} {ci(g['lo'], g['hi'])}; the same pair a season later, "
            f"{pct(n['growth'])} {ci(n['lo'], n['hi'])}.",
            (R - L) * W, fontsize=10, color=TEXT, va="top")
    save(fig, "fig4_chemistry")


def draw_depay(axes, cs, fs=1.0):
    d = cs[(cs.player == "Memphis Depay")
           & cs.season.isin(["2015-2016", "2017-2018", "2020-2021"])].sort_values("season")
    x = np.arange(len(d))
    labs = ["United\n2015–16", "Lyon\n2017–18", "Lyon\n2020–21"]
    spec = ((axes[0], "usage_on_pitch", PLAYER, "His share of the team's shots and shot-assists",
             lambda v: f"{v * 100:.0f}%", (0, 0.36)),
            (axes[1], "efficiency", BLUE, "His chance quality (xG+xA per action)",
             lambda v: f"{v:.3f}", (0, 0.17)))
    for ax, col, colour, ttl, fmt, lim in spec:
        v = d[col].to_numpy()
        ax.plot(x, v, color=colour, lw=2.2, zorder=1)
        for i, vi in enumerate(v):
            ax.plot(i, vi, "o", ms=10, mfc=BG if i == 0 else colour, mec=colour, mew=2, zorder=2)
            ax.text(i, vi + lim[1] * 0.12, fmt(vi), ha="center", fontsize=11 * fs,
                    fontweight="bold", color=colour)
        ax.set_ylim(*lim)
        ax.set_xlim(-0.5, len(d) - 0.5)
        ax.set_title(ttl, loc="left", fontsize=10 * fs, color=TEXT2)
        flat(ax, x, labs if ax is axes[1] else [""] * len(x))
    axes[1].text(0, d.efficiency.iloc[0] - 0.035, f"only {int(d.actions.iloc[0])} actions",
                 ha="center", fontsize=8.5 * fs, color=TEXT2)


def fig_depay(cs):
    fig, top = frame("Depay's share of the ball rose a little at Lyon, and his chance quality "
                     "rose from a small first sample",
                     "Memphis Depay, measured over the minutes he was on the pitch. Hollow: a "
                     "small sample, whose chance quality is uncertain by about 0.015 either way")
    gap = (top - 0.16) / 2
    a1 = fig.add_axes([L + 0.02, 0.16 + gap * 1.08, R - L - 0.04, gap * 0.72])
    a2 = fig.add_axes([L + 0.02, 0.16, R - L - 0.04, gap * 0.72])
    draw_depay((a1, a2), cs)
    save(fig, "fig5_depay")


def draw_positions(ax, r, rm, fs=1.0):
    """Attackers against midfielders after a move, matched: share of the ball and net output."""
    rows = []
    for lab, key in (("Share of the ball", "d_share"), ("Output per 90, net", "d_out")):
        for who, x, c in (("Attackers", r, PLAYER), ("Midfielders", rm, BLUE)):
            rows.append((lab, who, x["rtm"]["regression"][key], c))
    ys = [3.6, 2.9, 1.2, 0.5]
    for y, (lab, who, v, c) in zip(ys, rows):
        ax.plot([v["lo"] * 100, v["hi"] * 100], [y, y], color=c, lw=2, alpha=0.5)
        ax.plot(v["point"] * 100, y, "o", ms=7, color=c)
        ax.text(0, y, who + "  ", transform=ax.get_yaxis_transform(), ha="right", va="center",
                fontsize=9.5 * fs, color=c)
        ax.text(14, y, pct(v["point"]), ha="right", va="center", fontsize=9.5 * fs,
                fontweight="bold", color=c)
    for y, lab in ((4.25, "Share of the ball"), (1.85, "Output per 90, net")):
        ax.text(-14, y, lab, fontsize=9 * fs, color=TEXT2, va="center")
    ax.axvline(0, color=TEXT, lw=0.8)
    ax.set_xlim(-14, 14)
    ax.set_ylim(-0.1, 4.6)
    flat(ax, [-10, -5, 0, 5], [f"{MINUS}10", f"{MINUS}5", "0", "+5%"])


def draw_lost(ax, rv, rvo, fs=1.0):
    """Share of each group below 900 league minutes the next season, both sources."""
    rows = []
    for src, x in (("Understat", rv), ("Opta", rvo)):
        lp = x["lost_place"]["minutes_only_rates_ci"]
        rows += [(f"{src}, moved", lp["movers"], BLUE), (f"{src}, stayed", lp["stayers"], TEXT2)]
    for i, (lab, v, c) in enumerate(rows):
        y = 3 - i - (0.4 if i >= 2 else 0)
        ax.plot([v["lo"] * 100, v["hi"] * 100], [y, y], color=c, lw=7, alpha=0.2, solid_capstyle="round")
        ax.plot(v["point"] * 100, y, "o", ms=9, color=c)
        ax.text(v["point"] * 100, y + 0.24, pct(v["point"], 0, False), ha="center", va="bottom",
                fontsize=11 * fs, fontweight="bold", color=c)
        ax.text(0, y, lab + "  ", ha="right", va="center", fontsize=10 * fs, color=TEXT,
                transform=ax.get_yaxis_transform())
    ax.set_xlim(10, 40)
    ax.set_ylim(-1.0, 3.8)
    flat(ax, [10, 20, 30, 40], ["10%", "20%", "30%", "40%"])
    ax.set_xlabel("share of players under 900 league minutes", fontsize=8.5 * fs, color=TEXT2)


def fig_lost(r, ro):
    rv, rvo = (json.loads((d / "rivals.json").read_text()) for d in (OUT, OUT / "opta"))
    g = rv["lost_place"]["minutes_only_floors"]["lost900"]
    go = rvo["lost_place"]["minutes_only_floors"]["lost900"]
    fig, top = frame("Three movers in ten fall below 900 league minutes, "
                     "against one stayer in five",
                     "Attackers with 900 league minutes and 20 shots or shot-assists in a season, "
                     "and a Big-5 row the next (at least one shot or shot-assist). Share with under "
                     "900 league minutes the next season. Bands: 95% intervals", source=SOURCE_BOTH)
    ax = fig.add_axes([L + 0.33, top - 0.28, R - L - 0.34, 0.26])
    draw_lost(ax, rv, rvo)
    wrapped(fig, L, top - 0.36,
            f"Against stayers with the same last season, age and season, the gap is "
            f"{g['point'] * 100:+.1f} points {ci(g['lo'], g['hi'])} on Understat and "
            f"{go['point'] * 100:+.1f} {ci(go['lo'], go['hi'])} on Opta, which shares Transfermarkt's "
            f"minutes.",
            (R - L) * W, fontsize=10, color=PLAYER, va="top")
    save(fig, "fig6_lost_place")


FEE_ROWS = [("Any fee paid", "Any fee paid"), ("Over €30m", "Over €30m"), ("€10m–30m", "€10–30m"),
            ("Under €10m", "Under €10m"), ("Free or loan", "Free or loan"),
            ("No fee on record", "No fee, and mostly no\ntransfer history at all")]


def draw_fees(ax, rv, fs=1.0):
    """Flop-or-lost-place gap, movers in each fee band against all stayers, matched."""
    for i, (k, lab) in enumerate(FEE_ROWS):
        v = rv["lost_place"]["by_fee_band"][k]
        y = len(FEE_ROWS) - 1 - i - (0.4 if i > 0 else 0)
        c = BLUE if i == 0 else (LIGHT if k == "No fee on record" else TEXT2)
        ax.plot([v["badf"]["lo"] * 100, v["badf"]["hi"] * 100], [y, y], color=c, lw=2.5, solid_capstyle="butt")
        ax.plot(v["badf"]["point"] * 100, y, "o", ms=8, color=c)
        ax.text(0, y, f"{lab} ({v['n_movers']})  ", transform=ax.get_yaxis_transform(), ha="right", va="center",
                fontsize=9.5 * fs, color=PLAYER if i == 0 else TEXT, fontweight="bold" if i == 0 else "normal",
                linespacing=1.1)
        ax.text(50, y, f"{v['badf']['point'] * 100:+.1f}".replace("-", MINUS), ha="right", va="center",
                fontsize=10 * fs, color=c, fontweight="bold")
    ax.axvline(0, color=TEXT, lw=0.9)
    ax.set_xlim(-14, 50)
    ax.set_ylim(-0.9, len(FEE_ROWS) - 0.4)
    flat(ax, [-10, 0, 10, 20, 30], [f"{MINUS}10", "0", "+10", "+20", "+30"])
    ax.set_xlabel("points, movers minus stayers", fontsize=8.5 * fs, color=TEXT2)


def fig_fees():
    rv = json.loads((OUT / "rivals.json").read_text())
    v = rv["lost_place"]["by_fee_band"]["Any fee paid"]["badf"]
    fig, top = frame("Where a fee was paid, too few movers lose their place to tell from stayers",
                     "Flop or lost place the next season, movers in each fee band minus all stayers, "
                     "matched on last season. Movers in brackets. Lines: 95% intervals", source=SOURCE_LINE)
    ax = fig.add_axes([L + 0.42, top - 0.36, R - L - 0.43, 0.34])
    draw_fees(ax, rv)
    wrapped(fig, L, top - 0.43,
            f"Fee paid: {pct(v['point'])[:-1]} points {ci(v['lo'], v['hi'])}, too few to rule out about 7. Most no-fee moves "
            f"belong to players with no Transfermarkt history, so that bar may use hindsight.",
            (R - L) * W, fontsize=10, color=PLAYER, va="top")
    save(fig, "fig7_fee_bands")


CHECKS = [("Matched (headline)", lambda v: v["lost_place"]["matched"]["badf"]),
          ("Plus minutes share", lambda v: v["lost_place"]["matched_with_minutes_share_decile"]["badf"]),
          ("Plus late-season minutes, finishing", lambda v: v["lost_place"]["matched_with_late_season_minutes_and_finishing"]["badf"]),
          ("No loans, promoted or relegated", lambda v: v["lost_place"]["without_either"]["badf"]),
          ("Club-season intervals", lambda v: v["lost_place"]["matched_buying_club_season_clusters"]["badf"]),
          ("Dropouts all counted kept", lambda v: v["survival"]["bound_all_dropped_counted_kept"]["matched_gap"]),
          ("Dropouts all counted lost", lambda v: v["survival"]["bound_all_dropped_counted_lost"]["matched_gap"]),
          ("Fee paid only", lambda v: v["lost_place"]["by_fee_band"]["Any fee paid"]["badf"]),
          ("Without no-fee moves", lambda v: v["lost_place"]["no_fee_audit"]["without_no_fee_moves"]["badf"])]


def draw_checks(ax, rv, fs=1.0):
    """The flop-or-lost-place gap under each check, with 95% intervals."""
    for i, (lab, f) in enumerate(CHECKS):
        v = f(rv)
        y = len(CHECKS) - 1 - i
        c = BLUE if i == 0 else TEXT2
        ax.plot([v["lo"] * 100, v["hi"] * 100], [y, y], color=c, lw=2)
        ax.plot(v["point"] * 100, y, "o", ms=6, color=c)
        ax.text(0, y, lab + "  ", transform=ax.get_yaxis_transform(), ha="right", va="center",
                fontsize=8.5 * fs, color=TEXT)
        ax.text(24, y, f"{v['point'] * 100:+.1f}".replace("-", MINUS), ha="right", va="center",
                fontsize=8.5 * fs, color=c, fontweight="bold")
    ax.axvline(0, color=TEXT, lw=0.8)
    ax.set_xlim(-6, 24)
    ax.set_ylim(-0.6, len(CHECKS) - 0.4)
    flat(ax, [0, 10, 20], ["0", "+10", "+20"])


# ------------------------------------------------------------------ one-pager

def onepager(t, s, c, ws, sl, ag, ds, rm, r, ro):
    """A4 portrait summary, built from the same draw_* functions."""
    import qrcode
    mm = 1 / 25.4
    fig = plt.figure(figsize=(210 * mm, 297 * mm))

    def box(x, y, w, h):  # mm from the top-left corner
        return fig.add_axes([x / 210, 1 - (y + h) / 297, w / 210, h / 297])

    def txt(x, y, s_, width=None, **kw):
        kw.setdefault("va", "top")
        if width:
            return wrapped(fig, x / 210, 1 - y / 297, s_, width * mm, **kw)
        return fig.text(x / 210, 1 - y / 297, s_, **kw)

    def head(x, y, s_):
        txt(x, y, s_, fontsize=10.5, fontweight="bold", color=PLAYER)

    fig.patches.append(plt.Rectangle((15 / 210, 1 - 13 / 297), 14 / 210, 1.2 / 297, color=BLUE,
                                     transform=fig.transFigure, figure=fig))
    txt(15, 16, "Attacking transfers: why do they often fail?", fontsize=17, fontweight="bold", color=PLAYER)
    txt(15, 27, "Usage, playing time and luck after a move, Big-5, 2014–15 to 2024–25",
        fontsize=11, color=TEXT2)
    txt(195, 16, "Ben Rimmer", fontsize=11, fontweight="bold", color=PLAYER, ha="right")
    txt(195, 21.5, "First-class BSc Economics, Exeter", fontsize=8.5, color=TEXT2, ha="right")
    txt(195, 26, "benedict.p.rimmer@gmail.com", fontsize=8.5, color=TEXT2, ha="right")

    mv, nb = t["movers_vs_stayers"], t["noise_benchmark"]
    g, go = r["rtm"]["regression"], ro["rtm"]["regression"]
    lp, lpo = r["lost_place"], ro["lost_place"]
    gch = c["growth_next_season"]

    def iv(x, dp=1):
        return f"{pct(x['point'], dp)} ({pct(x['lo'], dp).lstrip('+')}, {pct(x['hi'], dp).lstrip('+')})"

    def pts(x):
        return (f"{x['point'] * 100:+.1f} points ({x['lo'] * 100:.1f}, "
                f"{x['hi'] * 100:.1f})").replace("-", MINUS)
    rv = json.loads((OUT / "rivals.json").read_text())
    fp = rv["lost_place"]["by_fee_band"]["Any fee paid"]["badf"]
    nf = rv["lost_place"]["no_fee_audit"]["without_no_fee_moves"]["badf"]
    sj = rv["lost_place"]["starts_in_first_10_after_joining"]["starts10j"]
    answer = (f"After a move between Big-5 clubs, an attacker is {pct(lp['regression']['bad_gap']['point'])[:-1]} points "
              f"{ci(lp['regression']['bad_gap']['lo'], lp['regression']['bad_gap']['hi'])} more likely to flop or lose his "
              f"place than a stayer with the same last season; without moves Transfermarkt records no fee for, which "
              f"may carry hindsight, {pct(nf['point'])[:-1]} {ci(nf['lo'], nf['hi'])}. Paid and free moves cannot yet "
              f"be told apart. He starts {abs(sj['point']) * 100:.1f} points fewer of his first 10 matches after joining. "
              f"If he keeps his place, output per 90 changes by {pct(g['d_out']['point'])} "
              f"{ci(g['d_out']['lo'], g['d_out']['hi'])}. Observational and exploratory.")
    txt(15, 37, answer, width=120, fontsize=8.5, color=TEXT)
    stats = [(f"{lp['regression']['bad_gap']['point'] * 100:+.1f} pts".replace("-", MINUS),
              "flop or lost his place, movers v stayers, matched"),
             (f"{pct(rv['lost_place']['minutes_only_rates_ci']['movers']['point'], 0, False)} v "
              f"{pct(rv['lost_place']['minutes_only_rates_ci']['stayers']['point'], 0, False)}",
              "under 900 league minutes next season, movers v stayers"),
             (f"{sj['point'] * 100:+.1f} pts".replace("-", MINUS), "starts in 10 matches from first squad, matched")]
    for i, (big, small) in enumerate(stats):
        y0 = 36 + i * 10.5
        txt(146, y0, big, fontsize=14.5, fontweight="bold", color=BLUE)
        txt(146, y0 + 6, small, fontsize=7, color=TEXT2)

    head(15, 70, "What a move does, against stayers with the same last season (per 90)")
    draw_move(box(15, 77, 180, 62), r, fs=0.95)

    head(15, 151, "Below 900 league minutes the next season")
    rv_, rvo_ = (json.loads((d / "rivals.json").read_text()) for d in (OUT, OUT / "opta"))
    draw_lost(box(40, 158, 55, 40), rv_, rvo_, fs=0.85)
    head(110, 151, "Same player, 5 points more of the ball")
    draw_within(box(110, 158, 85, 54), ws, fs=0.8)

    head(15, 222, "Flop or lost place under each check (points)")
    draw_checks(box(62, 229, 40, 38), rv_, fs=0.8)
    head(110, 222, "After a move: attackers v midfielders (matched)")
    draw_positions(box(140, 229, 55, 36), r, rm, fs=0.85)

    fig.lines.append(plt.Line2D([15 / 210, 195 / 210], [1 - 274 / 297] * 2, color=RULE, lw=0.8,
                                transform=fig.transFigure))
    lim = ("Limits: observational and exploratory, nothing pre-registered; shots and "
           "shot-assists only; the four-part split is accounting; no betting, fantasy or prop "
           "market tested, so no trading signal. Big-5: top divisions of England, Spain, Italy, "
           "Germany, France. Data: Understat, Opta via FBref, Transfermarkt. 95% intervals.")
    txt(15, 276.5, lim, width=160, fontsize=7, color=TEXT2)
    txt(15, 289, REPO, fontsize=8, color=BLUE)
    q = qrcode.QRCode(border=0, box_size=1)
    q.add_data("https://" + REPO)
    q.make()
    ax = box(181, 277, 14, 14)
    ax.imshow(np.array(q.get_matrix()), cmap="Greys", interpolation="nearest")
    ax.axis("off")

    with PdfPages(ROOT / "onepager.pdf", metadata=PDF_META) as pdf:
        pdf.savefig(fig)
    fig.savefig(FIG / "onepager.png", dpi=150, metadata=PNG_META)
    plt.close(fig)


def main():
    t = json.loads((OUT / "transfers.json").read_text())
    s = json.loads((OUT / "summary.json").read_text())
    c = json.loads((OUT / "chemistry.json").read_text())
    ws = pd.read_csv(OUT / "within_slopes.csv")
    sl = pd.read_csv(OUT / "transfer_slices.csv")
    ag = pd.read_csv(OUT / "age_gaps.csv")
    ds = pd.read_csv(OUT / "chemistry_dose.csv")
    cs = pd.read_csv(OUT / "case_studies.csv")
    r = json.loads((OUT / "robustness.json").read_text())
    ro = json.loads((OUT / "opta" / "robustness.json").read_text())
    fig_move(r)
    fig_lost(r, ro)
    fig_fees()
    fig_luck(t)
    fig_age(sl, ag, r["slice_family"]["age 26–28: movers v stayers"])
    fig_within(ws, s)
    fig_chem(ds, c)
    fig_depay(cs)
    rm = json.loads((OUT / "mid" / "robustness.json").read_text())
    onepager(t, s, c, ws, sl, ag, ds, rm, r, ro)
    print("figures written to", FIG)


if __name__ == "__main__":
    main()
