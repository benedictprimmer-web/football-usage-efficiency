"""Draw the figures from the aggregate tables in data/ (run analyse.py first).

    python analysis/figures.py
"""
from __future__ import annotations

import json

import matplotlib
import matplotlib.ticker
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from config import OUT, FIG  # noqa: E402

ACCENT = "#2a78d6"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#a8a7a2"
BAND = "#e4e3df"
BG = "#fcfcfb"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 12, "axes.titlesize": 15,
    "axes.labelsize": 12, "axes.edgecolor": MUTED, "axes.labelcolor": INK2,
    "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False,
    "axes.spines.right": False, "figure.facecolor": BG, "axes.facecolor": BG,
    "savefig.facecolor": BG, "svg.fonttype": "none",
})


def _save(fig, name):
    FIG.mkdir(exist_ok=True)
    fig.savefig(FIG / f"{name}.png", dpi=200, bbox_inches="tight")
    fig.savefig(FIG / f"{name}.svg", bbox_inches="tight")
    plt.close(fig)


def _title(fig, ax, title, sub):
    ax.set_title(title, loc="left", color=INK, fontweight="bold", pad=34)
    ax.text(0, 1.03, sub, transform=ax.transAxes, color=INK2, fontsize=11, va="bottom")


# season rows drawn on the main figure, in the order they are joined
CASE_PATH = {
    "Memphis Depay": [("2015-2016", "United 15/16"), ("2017-2018", "Lyon 17/18"),
                      ("2020-2021", "Lyon 20/21")],
    "Anthony Martial": [("2014-2015", "Monaco 14/15"), ("2015-2016", "United 15/16")],
    "Cristiano Ronaldo": [("2020-2021", "Juventus 20/21"), ("2021-2022", "United 21/22")],
}
MARKER = {"Memphis Depay": "o", "Anthony Martial": "s", "Cristiano Ronaldo": "D"}
# label offsets in points, hand-placed so nothing collides
OFFS = {
    ("Memphis Depay", "2015-2016"): (8, -14), ("Memphis Depay", "2017-2018"): (-10, 9),
    ("Memphis Depay", "2020-2021"): (8, 6),
    ("Anthony Martial", "2014-2015"): (8, 2), ("Anthony Martial", "2015-2016"): (-10, 4),
    ("Cristiano Ronaldo", "2020-2021"): (8, 4), ("Cristiano Ronaldo", "2021-2022"): (6, -22),
}


MEDIAN_EFF_KEY = "median_efficiency"


def fig_curve():
    cv = pd.read_csv(OUT / "curve_bins.csv")
    cv = cv[cv.usage_measure == "usage_share"]
    cs = pd.read_csv(OUT / "case_studies.csv")
    n = json.loads((OUT / "summary.json").read_text())["n_player_seasons"]

    fig, ax = plt.subplots(figsize=(7.2, 6.4))
    x = cv.usage_mean * 100
    ax.fill_between(x, cv.eff_lo, cv.eff_hi, color=BAND, lw=0, zorder=1)
    ax.plot(x, cv.efficiency, color=INK2, lw=2, zorder=2)
    ax.text(2.6, cv.eff_lo.iloc[0] - 0.004,
            f"All attackers, {n:,} seasons\n(average and 95% interval)",
            color=INK2, fontsize=10.5, va="top")

    # light bracket over the flat stretch of the curve
    yb = 0.1335
    ax.plot([4, 14], [yb, yb], color=MUTED, lw=1)
    for xe in (4, 14):
        ax.plot([xe, xe], [yb - 0.0018, yb], color=MUTED, lw=1)
    ax.text(9, yb + 0.0012, "flat from 4% to 14%", color=INK2, fontsize=10,
            ha="center", va="bottom")

    for name, path in CASE_PATH.items():
        p = cs[cs.player == name].set_index("season").loc[[s for s, _ in path]]
        px, py = p.usage_share * 100, p.efficiency
        ax.plot(px, py, color=ACCENT, lw=1.6, alpha=0.55, zorder=3)
        ax.scatter(px, py, s=64, marker=MARKER[name], color=ACCENT,
                   edgecolor=BG, linewidth=1.5, zorder=4)
        for (season, lab), xi, yi in zip(path, px, py):
            dx, dy = OFFS[(name, season)]
            ax.annotate(lab, (xi, yi), xytext=(dx, dy), textcoords="offset points",
                        fontsize=10, color=INK, ha="left" if dx > 0 else "right", va="center")
        ax.annotate(name.split()[-1], (px.iloc[0], py.iloc[0]),
                    xytext={"Depay": (-10, 0), "Martial": (8, 14),
                            "Ronaldo": (8, 16)}[name.split()[-1]],
                    textcoords="offset points", fontsize=11, color=ACCENT,
                    fontweight="bold", va="center",
                    ha="right" if name.endswith("Depay") else "left")

    ax.annotate("Team 0.25 xGD/90 worse\nwith him on the pitch",
                (14.6, 0.146), xytext=(19.5, 0.172), textcoords="data",
                fontsize=10, color=INK2, ha="center",
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=1))

    ax.set_xlim(2, 25)
    ax.set_ylim(0.075, 0.205)
    ax.set_xlabel("Usage share: player's % of his team's shots and shot-assists")
    ax.set_ylabel("Chance quality per action (npxG + xA)")
    ax.grid(axis="y", color=BAND, lw=0.8)
    _title(fig, ax, "More of the ball, about the same chance quality",
           "Flat up to 14% usage, about 8% lower above 18%. Three careers on top.")
    _save(fig, "fig1_usage_efficiency")


def fig_slopes():
    """Four plain-language versions of the within-player test."""
    ws = pd.read_csv(OUT / "within_slopes.csv").set_index("spec")
    rows = [  # spec, label, note
        ("naive", "Raw comparison", "same player, next season, nothing held fixed"),
        ("minutes", "Same minutes", "change in minutes held fixed"),
        ("split_half", "Clean test (headline)", "same minutes, usage and quality from different matches"),
        ("movers_vs_mates", "Club changers vs new team-mates", "quality measured against the new team"),
    ]
    fig, ax = plt.subplots(figsize=(7.2, 4.9))
    lo_x, hi_x = -6.5, 4.5
    for i, (spec, lab, note) in enumerate(rows):
        r = ws.loc[spec]
        yi = len(rows) - 1 - i
        head = spec == "split_half"
        c = ACCENT if head else INK2
        ax.plot([r.ci_lo_pct, r.ci_hi_pct], [yi, yi], color=c, lw=3 if head else 2.2,
                solid_capstyle="round", zorder=2)
        ax.scatter(r.pct_of_median, yi, s=80 if head else 60, color=c, zorder=3,
                   edgecolor=BG, linewidth=1.5)
        ax.text(lo_x + 0.1, yi + 0.36, lab, va="bottom", ha="left", fontsize=11.5,
                color=INK if head else INK2, fontweight="bold" if head else "normal")
        ax.text(lo_x + 0.1, yi + 0.17, note, va="bottom", ha="left", fontsize=9.5,
                color=INK2)
        val = f"{r.pct_of_median:+.1f}%".replace("-", "\u2212")
        rng = f"({r.ci_lo_pct:+.1f} to {r.ci_hi_pct:+.1f})".replace("-", "\u2212")
        ax.text(r.ci_hi_pct + 0.25, yi, f"{val}  {rng}", va="center", ha="left",
                fontsize=10, color=c, fontweight="bold" if head else "normal")
    ax.axvline(0, color=MUTED, lw=1, zorder=1)
    ax.text(0, len(rows) - 0.25, "no effect", ha="center", va="bottom",
            fontsize=10, color=INK2)
    ax.set_xlim(lo_x, hi_x)
    ax.set_ylim(-0.5, len(rows) - 0.05)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.set_xticks(range(-6, 5, 2))
    ax.set_xticklabels([f"{t:+d}%".replace("-", "\u2212") if t else "0" for t in range(-6, 5, 2)])
    ax.set_xlabel("% change in chance quality per +5 points of usage\n(dot: best estimate; line: 95% interval)")
    ax.grid(axis="x", color=BAND, lw=0.8)
    _title(fig, ax, "Same player, more of the ball: a small cost at most",
           "The clean test finds \u22121.7%, and its range just reaches zero.")
    _save(fig, "fig2_within_player")


def fig_bins():
    wb = pd.read_csv(OUT / "within_bins.csv")
    s = json.loads((OUT / "summary.json").read_text())
    med = s[MEDIAN_EFF_KEY]
    fig, ax = plt.subplots(figsize=(7.2, 5.2))
    x = wb.d_usage * 100
    y, ylo, yhi = (wb[c] / med * 100 for c in ("d_eff", "d_eff_lo", "d_eff_hi"))
    ax.vlines(x, ylo, yhi, color=MUTED, lw=2)
    ax.scatter(x, y, s=56, color=ACCENT, zorder=3, edgecolor=BG, linewidth=1.5)
    b = s["specs"]["minutes"]["pct"] / 5          # % per percentage point
    xx = pd.Series([x.min(), x.max()])
    ax.plot(xx, b * xx, color=INK2, lw=1.4, ls="--")
    ax.text(xx.iloc[1], b * xx.iloc[1] - 0.6, "fitted slope", color=INK2,
            fontsize=10, ha="right", va="top")
    ax.axhline(0, color=MUTED, lw=1)
    ax.set_xlabel("Change in usage share from one season to the next\n(percentage points, minutes held fixed; each dot is a tenth of the pairs)")
    ax.set_ylabel("% change in chance quality")
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(
        lambda v, _: f"{v:+.0f}%".replace("-", "\u2212") if v else "0"))
    ax.grid(axis="y", color=BAND, lw=0.8)
    _title(fig, ax, "Losing the ball helps a little more than gaining it hurts",
           "Bars: 95% intervals. % of the median chance quality, 0.115 per action.")
    _save(fig, "fig3_within_bins")


if __name__ == "__main__":
    fig_curve()
    fig_slopes()
    fig_bins()
    print("figures written to", FIG)
