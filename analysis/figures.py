"""Draw the figures from the aggregate tables in data/ (run analyse.py first).

    python analysis/figures.py
"""
from __future__ import annotations

import json

import matplotlib
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


def fig_curve():
    cv = pd.read_csv(OUT / "curve_bins.csv")
    cv = cv[cv.usage_measure == "usage_share"]
    cs = pd.read_csv(OUT / "case_studies.csv")
    n = json.loads((OUT / "summary.json").read_text())["n_player_seasons"]

    fig, ax = plt.subplots(figsize=(7.2, 6.2))
    x = cv.usage_mean * 100
    ax.fill_between(x, cv.eff_lo, cv.eff_hi, color=BAND, lw=0, zorder=1)
    ax.plot(x, cv.efficiency, color=INK2, lw=2, zorder=2)
    ax.text(2.6, cv.eff_lo.iloc[0] - 0.004,
            f"All attackers, {n:,} seasons\n(mean and 95% interval)",
            color=INK2, fontsize=10.5, va="top")

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
                    xytext={"Depay": (8, -28), "Martial": (8, 14),
                            "Ronaldo": (8, 16)}[name.split()[-1]],
                    textcoords="offset points", fontsize=11, color=ACCENT,
                    fontweight="bold")

    ax.annotate("Team 0.25 xGD/90 worse\nwith him on the pitch",
                (14.6, 0.146), xytext=(19.5, 0.172), textcoords="data",
                fontsize=10, color=INK2, ha="center",
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=1))

    ax.set_xlim(2, 25)
    ax.set_ylim(0.075, 0.205)
    ax.set_xlabel("Usage share: player's % of his team's shots and shot-assists")
    ax.set_ylabel("Efficiency: npxG + xA per action")
    ax.grid(axis="y", color=BAND, lw=0.8)
    _title(fig, ax, "More of the ball, about the same quality",
           "Efficiency barely moves with usage share. Three careers traced on top.")
    _save(fig, "fig1_usage_efficiency")


def fig_slopes():
    ws = pd.read_csv(OUT / "within_slopes.csv")
    order = ["naive", "minutes", "on_pitch", "split_half", "baseline",
             "stayers", "movers", "movers_vs_mates", "all_vs_mates"]
    labels = {
        "naive": "Usage share as defined, nothing fixed",
        "minutes": "Holding minutes fixed",
        "on_pitch": "Usage per minute on the pitch",
        "split_half": "Split-half, minutes fixed (headline)",
        "baseline": "+ last season's efficiency",
        "stayers": "Same club both seasons",
        "movers": "Changed club",
        "movers_vs_mates": "Changed club, vs new team-mates",
        "all_vs_mates": "Everyone, vs team-mates",
    }
    w = ws.set_index("spec").loc[order].reset_index()
    fig, ax = plt.subplots(figsize=(7.2, 5.6))
    y = range(len(w))[::-1]
    for yi, r in zip(y, w.itertuples()):
        c = ACCENT if r.spec == "split_half" else INK2
        ax.plot([r.ci_lo_pct, r.ci_hi_pct], [yi, yi], color=c, lw=2.2,
                solid_capstyle="round")
        ax.scatter(r.pct_of_median, yi, s=60, color=c, zorder=3,
                   edgecolor=BG, linewidth=1.5)
        ax.text(-14.6, yi, labels[r.spec], va="center", ha="left", fontsize=10.5,
                color=INK if r.spec == "split_half" else INK2,
                fontweight="bold" if r.spec == "split_half" else "normal")
    ax.axvline(0, color=MUTED, lw=1)
    ax.set_xlim(-15, 5)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.set_xlabel("Change in efficiency per +5 points of usage share\n(% of median efficiency, 95% interval)")
    ax.grid(axis="x", color=BAND, lw=0.8)
    _title(fig, ax, "Same player, next season",
           "A small cost at most, and it sits with players who change club.")
    _save(fig, "fig2_within_player")


def fig_bins():
    wb = pd.read_csv(OUT / "within_bins.csv")
    s = json.loads((OUT / "summary.json").read_text())
    fig, ax = plt.subplots(figsize=(7.2, 5.2))
    x = wb.d_usage * 100
    ax.vlines(x, wb.d_eff_lo, wb.d_eff_hi, color=MUTED, lw=2)
    ax.scatter(x, wb.d_eff, s=56, color=ACCENT, zorder=3, edgecolor=BG, linewidth=1.5)
    b = s["specs"]["minutes"]["point"] / 5
    xx = pd.Series([x.min(), x.max()])
    ax.plot(xx, b * xx, color=INK2, lw=1.4, ls="--")
    ax.axhline(0, color=MUTED, lw=1)
    ax.set_xlabel("Change in usage share, percentage points\n(minutes held fixed; each dot is one tenth of the pairs)")
    ax.set_ylabel("Change in efficiency (npxG + xA per action)")
    ax.grid(axis="y", color=BAND, lw=0.8)
    _title(fig, ax, "Season-to-season changes, binned",
           "Dashed line: fitted slope, all pairs. Bars: 95% intervals.")
    _save(fig, "fig3_within_bins")


if __name__ == "__main__":
    fig_curve()
    fig_slopes()
    fig_bins()
    print("figures written to", FIG)
