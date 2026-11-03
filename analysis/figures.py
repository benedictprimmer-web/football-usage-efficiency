"""Draw the three figures from the aggregate tables in data/ (run analyse.py and
decompose.py first). Sized to stay readable at phone width.

    python analysis/figures.py
"""
from __future__ import annotations

import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker as mticker  # noqa: E402
import pandas as pd  # noqa: E402

from config import OUT, FIG  # noqa: E402

# one palette for every figure: blue = the situation / the highlight,
# near-black = the player, greys for context
ACCENT = "#2a78d6"
PLAYER = "#1d1d1b"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#a8a7a2"
BAND = "#dcdbd6"
GRID = "#ebeae6"
BG = "#fcfcfb"
MINUS = "−"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 12, "axes.titlesize": 15,
    "axes.labelsize": 12, "xtick.labelsize": 11.5, "ytick.labelsize": 11.5,
    "axes.edgecolor": MUTED, "axes.labelcolor": INK2,
    "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False,
    "axes.spines.right": False, "figure.facecolor": BG, "axes.facecolor": BG,
    "savefig.facecolor": BG, "svg.fonttype": "none",
})


def _save(fig, name):
    FIG.mkdir(exist_ok=True)
    fig.savefig(FIG / f"{name}.png", dpi=200, bbox_inches="tight", pad_inches=0.15)
    fig.savefig(FIG / f"{name}.svg", bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)


def _title(fig, title, sub):
    h = fig.get_figheight()
    fig.text(0.02, 1 - 0.12 / h, title, color=INK, fontsize=15, fontweight="bold", va="top")
    fig.text(0.02, 1 - 0.48 / h, sub, color=INK2, fontsize=12, va="top")


def _pct(v, dp=1):
    return f"{v:+.{dp}f}%".replace("-", MINUS)


def fig_flops():
    """Where the fall in per-90 output went, for the flops."""
    j = json.loads((OUT / "flop_decomposition.json").read_text())
    labels = list(j["share_of_fall"])
    vals = [j["share_of_fall"][k] * 100 for k in labels]
    ci = [[v * 100 for v in j["share_ci95"][k]] for k in labels]
    situation = sum(round(v) for v in vals[:3])

    fig, ax = plt.subplots(figsize=(6.4, 4.8))
    fig.subplots_adjust(left=0.03, right=0.78, top=0.80, bottom=0.14)
    ys = [3.0, 2.0, 1.0, -0.35]          # a gap before the player's bar
    for i, (lab, v, (lo, hi), y) in enumerate(zip(labels, vals, ci, ys)):
        c = ACCENT if i < 3 else PLAYER
        ax.barh(y, v, color=c, height=0.42, zorder=2)
        ax.plot([lo, hi], [y, y], color=MUTED if i == 3 else INK, lw=1.3, zorder=3)
        ax.text(0, y + 0.27, lab, fontsize=12, color=INK, va="bottom", ha="left")
        ax.text(hi + 1.2, y, f"{v:.0f}%", va="center", fontsize=12.5, color=c,
                fontweight="bold")
    # bracket the three situation bars, and label the player's bar the same way
    bx = 56
    ax.plot([bx, bx + 1.2, bx + 1.2, bx], [3.2, 3.2, 0.8, 0.8], color=ACCENT, lw=1.6,
            clip_on=False)
    ax.text(bx + 2.6, 2.0, f"The\nsituation\n{situation}%", color=ACCENT, fontsize=13,
            fontweight="bold", va="center", ha="left", linespacing=1.15)
    ax.text(bx + 2.6, -0.35, f"The\nplayer\n{round(vals[3])}%", color=PLAYER, fontsize=13,
            fontweight="bold", va="center", ha="left", linespacing=1.15)
    ax.set_xlim(0, 56)
    ax.set_ylim(-0.75, 3.75)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.set_xticks(range(0, 51, 10))
    ax.xaxis.set_major_formatter(mticker.PercentFormatter(decimals=0))
    ax.set_xlabel("Share of the fall in output per 90 (line: 95% interval)")
    ax.grid(axis="x", color=GRID, lw=0.8, zorder=0)
    _title(fig, "When a transfer flops, six tenths is the situation",
           f"{j['flops']} moves where an attacker's xG + xA per 90 fell by over 25%")
    _save(fig, "fig0_why_transfers_flop")


def fig_curve():
    """Chance quality against share of the ball per 90, with Depay on top."""
    cv = pd.read_csv(OUT / "curve_bins.csv")
    cv = cv[(cv.usage_measure == "usage_on_pitch") & (cv.n_player_seasons >= 50)]
    cs = pd.read_csv(OUT / "case_studies.csv")
    n = json.loads((OUT / "summary.json").read_text())["n_player_seasons"]

    fig, ax = plt.subplots(figsize=(6.4, 5.6))
    fig.subplots_adjust(left=0.14, right=0.97, top=0.83, bottom=0.15)
    x = cv.usage_mean * 100
    ax.axvspan(12, 16, color=GRID, lw=0, zorder=0)
    ax.text(14, 0.1435, "peak\n12–16%", ha="center", va="top", fontsize=11, color=INK2)
    ax.fill_between(x, cv.eff_lo, cv.eff_hi, color=BAND, lw=0, zorder=1)
    ax.plot(x, cv.efficiency, color=INK2, lw=2.4, zorder=2)
    ax.text(9.0, 0.1065, f"Average of\n{n:,} attacker\nseasons (band:\n95% interval)", color=INK2, fontsize=11,
            va="top", ha="left", linespacing=1.15)
    ax.annotate("drops off above 20%", (21.4, 0.1085), xytext=(20.6, 0.1005),
                fontsize=11, color=INK2, ha="right", va="center",
                arrowprops=dict(arrowstyle="-", color=INK2, lw=1, shrinkA=2, shrinkB=0))

    path = [("2015-2016", "United 15/16"), ("2017-2018", "Lyon 17/18"),
            ("2020-2021", "Lyon 20/21")]
    dp = cs[cs.player == "Memphis Depay"].set_index("season").loc[[s for s, _ in path]]
    px, py = dp.usage_on_pitch * 100, dp.efficiency
    ax.plot(px, py, color=ACCENT, lw=2.2, zorder=4)
    ax.scatter(px, py, s=80, color=ACCENT, edgecolor=BG, linewidth=1.5, zorder=5)
    offs = {"2015-2016": (-10, 0, "right"), "2017-2018": (10, 0, "left"),
            "2020-2021": (10, 6, "left")}
    for (season, lab), xi, yi, mins in zip(path, px, py, dp.minutes_share):
        dx, dy, ha = offs[season]
        ax.annotate(f"{lab}\nplayed {mins:.0%}\nof minutes", (xi, yi), xytext=(dx, dy),
                    textcoords="offset points", fontsize=11, color=INK, ha=ha,
                    va="center", linespacing=1.1)
    ax.annotate("Depay", (px.iloc[0], py.iloc[0]), xytext=(10, -4),
                textcoords="offset points", fontsize=12.5, color=ACCENT,
                fontweight="bold", ha="left", va="center")

    ax.set_xlim(7, 27)
    ax.set_ylim(0.075, 0.145)
    ax.set_xticks(range(8, 27, 4))
    ax.xaxis.set_major_formatter(mticker.PercentFormatter(decimals=0))
    ax.set_xlabel("Share of the team's shots and shot-assists\nwhile he is on the pitch")
    ax.set_ylabel("Chance quality (xG + xA per action)")
    ax.grid(axis="y", color=GRID, lw=0.8)
    _title(fig, "Chance quality peaks at 12–16% of the ball",
           "Per 90, Depay's share barely changed. His chance quality did.")
    _save(fig, "fig1_usage_efficiency")


def fig_slopes():
    """Four versions of the within-player test, per 90 as the headline."""
    ws = pd.read_csv(OUT / "within_slopes.csv").set_index("spec")
    rows = [  # spec, label, note
        ("naive", "Season totals", "playing time left in"),
        ("on_pitch", "Per 90 (headline)", "share of the ball while on the pitch"),
        ("split_half", "Shared noise removed", "share and quality from different matches"),
        ("movers_vs_mates", "Club changers vs new team-mates", "per 90, against the new team"),
    ]
    fig, ax = plt.subplots(figsize=(6.4, 5.0))
    fig.subplots_adjust(left=0.03, right=0.97, top=0.80, bottom=0.18)
    lo_x, hi_x = -6, 6
    for i, (spec, lab, note) in enumerate(rows):
        r = ws.loc[spec]
        yi = len(rows) - 1 - i
        head = spec == "on_pitch"
        c = ACCENT if head else INK2
        ax.plot([r.ci_lo_pct, r.ci_hi_pct], [yi, yi], color=c, lw=3.2 if head else 2.2,
                solid_capstyle="round", zorder=2)
        ax.scatter(r.pct_of_median, yi, s=90 if head else 60, color=c, zorder=3,
                   edgecolor=BG, linewidth=1.5)
        ax.text(lo_x + 0.1, yi + 0.42, lab, va="bottom", ha="left", fontsize=12,
                color=INK, fontweight="bold" if head else "normal")
        ax.text(lo_x + 0.1, yi + 0.17, note, va="bottom", ha="left", fontsize=11,
                color=INK2)
        ax.text(r.ci_hi_pct + 0.3, yi, _pct(r.pct_of_median), va="center", ha="left",
                fontsize=12, color=c, fontweight="bold" if head else "normal")
    ax.axvline(0, color=MUTED, lw=1, zorder=1)
    ax.set_xlim(lo_x, hi_x)
    ax.set_ylim(-0.4, len(rows) - 0.05)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.set_xticks(range(-6, 7, 2))
    ax.set_xticklabels([_pct(t, 0) if t else "0" for t in range(-6, 7, 2)])
    ax.set_xlabel("Change in chance quality per +5 points of share\n(dot: estimate; line: 95% interval)")
    ax.grid(axis="x", color=GRID, lw=0.8)
    _title(fig, "Same player, more of the ball: a small cost",
           f"Per 90, about {_pct(ws.loc['on_pitch'].pct_of_median)} per 5 extra points of share")
    _save(fig, "fig2_within_player")


if __name__ == "__main__":
    fig_flops()
    fig_curve()
    fig_slopes()
    print("figures written to", FIG)
