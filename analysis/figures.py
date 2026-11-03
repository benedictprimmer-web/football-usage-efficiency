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
    """'(1.1 to 4.8)' in percentage points, with proper minus signs."""
    z = f"{0:.{dp}f}"
    return (f"({lo * 100:.{dp}f} to {hi * 100:.{dp}f})".replace(f"-{z} ", f"{z} ")
            .replace(f"-{z})", f"{z})").replace("-", MINUS))


def fill(s: str, width_in: float, fontsize: float, bold=False) -> str:
    """Wrap to a width in inches (Helvetica averages about half an em per character)."""
    per = fontsize * (0.56 if bold else 0.5) / 72
    return textwrap.fill(s, max(int(width_in / per), 10), break_on_hyphens=False)


def wrapped(fig, x, y, s, width_in, fontsize=10.5, **kw):
    """Figure text wrapped to a fixed width; returns its height as a figure fraction."""
    t = fill(s, width_in, fontsize, kw.get("fontweight") == "bold")
    fig.text(x, y, t, fontsize=fontsize, linespacing=1.25, **kw)
    return (t.count("\n") + 1) * fontsize * 1.25 / 72 / fig.get_figheight()


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
    fig, top = frame("A move costs an attacker about 4% of his share of the ball, and his "
                     "output per 90 barely changes",
                     f"Change in xG+xA per 90 after a club move, minus the change for players "
                     f"who stayed and had the same last season (decile of share, decile of "
                     f"output per 90, age band, season), split into four parts that multiply "
                     f"to output. {r['n_movers']} moves, {r['n_stayers']:,} stays. "
                     f"Brackets: 95% intervals")
    ax = fig.add_axes([L, 0.14, R - L, top - 0.15])
    draw_move(ax, r)
    save(fig, "fig0_what_a_move_does")


def draw_luck(ax, t, fs=1.0):
    """Observed flop rates against the rate with the player's quality held fixed."""
    nb, ns, mv = t["noise_benchmark"], t["noise_benchmark_stayers"], t["movers_vs_stayers"]
    rows = [
        ("Moved club", mv["flop_rate_movers"]["point"], mv["flop_rate_movers"]["lo"],
         mv["flop_rate_movers"]["hi"], PLAYER),
        ("Moved, luck only", *nb["flop_rate_noise_only"], BLUE),
        ("Stayed", mv["flop_rate_stayers"]["point"], mv["flop_rate_stayers"]["lo"],
         mv["flop_rate_stayers"]["hi"], TEXT2),
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
    fig, top = frame("Movers flop no more often than luck alone predicts",
                     "Share of seasons where output per 90 fell by more than 25%. For \"luck "
                     "only\", each season keeps its real change of team and role, and the "
                     "player's chance quality is redrawn from his own shots with his quality "
                     "against team-mates fixed (200 runs). Bands: 95% intervals")
    ax = fig.add_axes([L + 0.3, top - 0.33, R - L - 0.3, 0.31])
    draw_luck(ax, t)
    wrapped(fig, L, top - 0.40,
            f"The player's own part of a flop: {pct(nb['player_share_observed'], 0, False)} in "
            f"the data, {pct(p[0], 0, False)} ({pct(p[1], 0, False)} to {pct(p[2], 0, False)}) "
            f"from luck. The benchmark runs a point high on stayers, cannot see a rise of 1 to "
            f"3 points, and counts only players with 900 minutes after the move.",
            (R - L) * W, fontsize=10, color=PLAYER, va="top")
    save(fig, "fig1_flops_look_like_luck")


AGES = ["Under 23", "23–25", "26–28", "29 and over"]


def draw_age(ax, sl, ag, fs=1.0):
    """Movers minus stayers in flop rate, by age band, with 95% intervals."""
    for i, b in enumerate(AGES):
        y = len(AGES) - 1 - i
        g = ag[ag.age_band == b].iloc[0]
        hl = b == "26–28"
        c = BLUE if hl else LIGHT
        ax.plot([g.lo * 100, g.hi * 100], [y, y], color=c, lw=2.5, solid_capstyle="butt")
        ax.plot(g.gap * 100, y, "o", ms=8, color=BLUE if hl else TEXT2)
        ax.text(26, y, f"{g.gap * 100:+.0f}".replace("-", MINUS), va="center", ha="right",
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
            f"At 26–28: {g.gap * 100:+.0f} points ({g.lo * 100:+.0f} to {g.hi * 100:+.0f}), "
            f"p = {holm['p']:.3f}, or {holm['p_holm']:.2f} after the Holm correction. A lead "
            f"to test on new seasons."
            .replace("-", MINUS),
            (R - L) * W, fontsize=10, color=TEXT, va="top")
    save(fig, "fig2_age")


SPEC_NAMES = {
    "on_pitch_split_half": ("Headline: per 90, noise split", "share and quality from different matches"),
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
        ax.text(5, y, f"{r.pct_of_median:+.1f}%".replace("-", MINUS), fontsize=9.5 * fs,
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
                     f"pitch. {s['n_pairs']:,} pairs of seasons, 95% intervals")
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
            f"New pairs, second half of their first season against the first: "
            f"{pct(g['growth'])} {ci(g['lo'], g['hi'])}. The same pair a season later: "
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
            ax.text(i, vi + lim[1] * 0.08, fmt(vi), ha="center", fontsize=11 * fs,
                    fontweight="bold", color=colour)
        ax.set_ylim(*lim)
        ax.set_xlim(-0.5, len(d) - 0.5)
        ax.set_title(ttl, loc="left", fontsize=10 * fs, color=TEXT2)
        flat(ax, x, labs if ax is axes[1] else [""] * len(x))
    axes[1].text(0, d.efficiency.iloc[0] - 0.035, f"only {int(d.actions.iloc[0])} actions",
                 ha="center", fontsize=8.5 * fs, color=TEXT2)


def fig_depay(cs):
    fig, top = frame("Depay's share of the ball rose a little at Lyon, and his chances got "
                     "much better",
                     "Memphis Depay, measured over the minutes he was on the pitch. Hollow: "
                     "a small sample")
    gap = (top - 0.16) / 2
    a1 = fig.add_axes([L + 0.02, 0.16 + gap * 1.08, R - L - 0.04, gap * 0.72])
    a2 = fig.add_axes([L + 0.02, 0.16, R - L - 0.04, gap * 0.72])
    draw_depay((a1, a2), cs)
    save(fig, "fig5_depay")


def draw_positions(ax, t, tm, fs=1.0):
    """Attackers against midfielders after a move: share of the ball and net output."""
    rows = []
    for lab, key in (("Share of the ball", "share"), ("Output per 90, net", "net")):
        for who, x, c in (("Attackers", t, PLAYER), ("Midfielders", tm, BLUE)):
            mv = x["movers_vs_stayers"]
            v = mv["mean_log_gap_by_part"]["His share of the ball"] if key == "share" else mv["mean_log_gap"]
            rows.append((lab, who, v, c))
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


# ------------------------------------------------------------------ one-pager

def onepager(t, s, c, ws, sl, ag, ds, tm, r, ro):
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
    txt(15, 16, "Why do transfers fail?", fontsize=24, fontweight="bold", color=PLAYER)
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
        return f"{pct(x['point'], dp)} ({pct(x['lo'], dp)} to {pct(x['hi'], dp)})"

    def pts(x):
        return (f"{x['point'] * 100:+.1f} points ({x['lo'] * 100:+.1f} to "
                f"{x['hi'] * 100:+.1f})").replace("-", MINUS)
    answer = (f"Against stayers with the same last season, a move cuts an attacker's share "
              f"of his team's shots and shot-assists by {iv(g['d_share'])} (Opta "
              f"{pct(go['d_share']['point'])}), and output per 90 barely moves "
              f"({pct(g['d_out']['point'])}; Opta {pct(go['d_out']['point'])}). The larger "
              f"cost is his place: {pct(lp['bad_movers']['point'], 0, False)} of movers flop or "
              f"drop below 900 league minutes, against {pct(lp['bad_stayers']['point'], 0, False)} "
              f"of stayers ({pts(lp['regression']['bad_gap'])} matched; Opta "
              f"{lpo['regression']['bad_gap']['point'] * 100:+.1f}). Regulars who keep their "
              f"place flop about as often as luck predicts on Understat, less clearly on Opta.")
    txt(15, 37, answer, width=118, fontsize=9, color=TEXT)
    stats = [(pct(g["d_share"]["point"]), "share of the ball after a move, matched"),
             (f"{lp['regression']['bad_gap']['point'] * 100:+.1f} pts".replace("-", MINUS),
              "flop or lost his place, movers v stayers"),
             (pct(gch["growth"]), f"pair chemistry, second season v first {ci(gch['lo'], gch['hi'])}")]
    for i, (big, small) in enumerate(stats):
        y0 = 36 + i * 10.5
        txt(146, y0, big, fontsize=14.5, fontweight="bold", color=BLUE)
        txt(146, y0 + 6, small, fontsize=7, color=TEXT2)

    head(15, 70, "What a move does, against stayers with the same last season (per 90)")
    draw_move(box(15, 77, 180, 62), r, fs=0.95)

    head(15, 151, "Flop rates against luck alone")
    draw_luck(box(45, 158, 50, 40), t, fs=0.85)
    head(110, 151, "Same player, 5 points more of the ball")
    draw_within(box(110, 158, 85, 54), ws, fs=0.8)

    head(15, 222, "Flop rate by age, moved minus stayed (points)")
    draw_age(box(40, 229, 55, 36), sl, ag, fs=0.85)
    head(110, 222, "After a move: attackers v midfielders (raw)")
    draw_positions(box(140, 229, 55, 36), t, tm, fs=0.85)

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
    fig_luck(t)
    fig_age(sl, ag, r["slice_family"]["age 26–28: movers v stayers"])
    fig_within(ws, s)
    fig_chem(ds, c)
    fig_depay(cs)
    tm = json.loads((OUT / "mid" / "transfers.json").read_text())
    onepager(t, s, c, ws, sl, ag, ds, tm, r, ro)
    print("figures written to", FIG)


if __name__ == "__main__":
    main()
