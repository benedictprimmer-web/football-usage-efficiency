"""Every number in the README. Reads data/work/panel.parquet (build_panel.py).

Writes small aggregate tables to data/:
    curve_bins.csv        efficiency by usage-share bin, with 95% CIs
    within_slopes.csv     within-player slopes under each specification, with 95% CIs
    reliability.csv       split-half reliability of efficiency and usage by minutes band
    case_studies.csv      season rows for the three case-study players (derived stats only)
    summary.json          the headline numbers quoted in the README

    python analysis/analyse.py
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from config import WORK, OUT, MIN_MINUTES, SEED, N_BOOT, CASES

STEP = 0.05          # report slopes per +5 percentage points of usage share


# ------------------------------------------------------------------ helpers

def wls(X: list[np.ndarray], y: np.ndarray, w: np.ndarray) -> np.ndarray:
    """Weighted least squares with an intercept. Returns [b0, b1, ...]."""
    A = np.column_stack([np.ones(len(y))] + list(X))
    sw = np.sqrt(w)
    return np.linalg.lstsq(A * sw[:, None], y * sw, rcond=None)[0]


def cluster_boot(df: pd.DataFrame, stat, n_boot: int = N_BOOT, seed: int = SEED):
    """Point estimate and 95% CI, resampling whole players (a player's
    seasons are not independent of each other)."""
    point = stat(df)
    rng = np.random.default_rng(seed)
    idx = df.groupby("tm_player_id").indices
    ids = np.array(list(idx))
    draws = []
    for _ in range(n_boot):
        pick = rng.choice(ids, len(ids))
        draws.append(stat(df.iloc[np.concatenate([idx[i] for i in pick])]))
    lo, hi = np.percentile(np.array(draws), [2.5, 97.5], axis=0)
    return point, lo, hi


def sample(panel: pd.DataFrame) -> pd.DataFrame:
    """Attacking players (Transfermarkt 'Attack' or attacking midfield) with at
    least MIN_MINUTES league minutes in the season."""
    return panel[panel.attacker & (panel.minutes >= MIN_MINUTES)].copy()


# ------------------------------------------------------------------ 1. reliability

def reliability(panel: pd.DataFrame) -> pd.DataFrame:
    """Split-half (odd v even matches) correlation, Spearman-Brown stepped up to
    a full season. This is what sets the minutes floor."""
    a = panel[panel.attacker].copy()
    a["band"] = pd.cut(a.minutes, [0, 450, 900, 1800, 5000],
                       labels=["<450", "450-899", "900-1799", "1800+"], right=False)
    rows = []
    for band, g in a.groupby("band", observed=True):
        row = {"minutes_band": band, "n": len(g)}
        for c in ("efficiency", "usage_share"):
            d = g[[f"{c}_h0", f"{c}_h1"]].dropna()
            r = d.corr().iloc[0, 1]
            row[f"{c}_split_half_r"] = r
            row[f"{c}_reliability"] = 2 * r / (1 + r)
        rows.append(row)
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ 2. the curve

EDGES = [0, .04, .06, .08, .10, .12, .14, .16, .18, .20, .22, 1.0]


def curve(a: pd.DataFrame, x: str = "usage_share") -> pd.DataFrame:
    """Action-weighted efficiency (total value / total actions) in each usage bin."""
    a = a.assign(bin=pd.cut(a[x], EDGES, right=False))
    bins = a.bin.cat.categories

    def stat(d):
        g = d.groupby("bin", observed=False)
        eff = g.value.sum() / g.actions.sum()
        rel = g.apply(lambda s: np.average(s.efficiency / s.mates_eff, weights=s.actions)
                      if len(s) else np.nan, include_groups=False)
        return np.concatenate([eff.reindex(bins).to_numpy(), rel.reindex(bins).to_numpy()])

    point, lo, hi = cluster_boot(a, stat, n_boot=N_BOOT // 2)
    k = len(bins)
    g = a.groupby("bin", observed=False)
    return pd.DataFrame({
        "usage_measure": x,
        "bin_lo": [b.left for b in bins], "bin_hi": [b.right for b in bins],
        "usage_mean": g[x].mean().to_numpy(),
        "n_player_seasons": g.size().to_numpy(),
        "actions": g.actions.sum().to_numpy(),
        "efficiency": point[:k], "eff_lo": lo[:k], "eff_hi": hi[:k],
        "eff_vs_teammates": point[k:], "rel_lo": lo[k:], "rel_hi": hi[k:],
    })


def cross_section_slope(a: pd.DataFrame) -> tuple:
    def stat(d):
        return wls([d.usage_share.to_numpy()], d.efficiency.to_numpy(),
                   d.actions.to_numpy())[1] * STEP
    return cluster_boot(a, stat)


# ------------------------------------------------------------------ 3. within player

def pairs(a: pd.DataFrame) -> pd.DataFrame:
    """Same player, consecutive seasons, both above the minutes floor."""
    a = a.assign(sy=a.season.str[:4].astype(int))
    p = a.merge(a.assign(sy=a.sy - 1), on=["tm_player_id", "sy"], suffixes=("_1", "_2"))
    p["mover"] = p.team_1 != p.team_2
    # inverse-variance weight for a difference of two per-action means
    p["w"] = 1 / (1 / p.actions_1 + 1 / p.actions_2)
    for h in (0, 1):
        p[f"w_h{h}"] = 1 / (1 / p[f"actions_h{h}_1"] + 1 / p[f"actions_h{h}_2"])
    return p


def _d(p, col, h=""):
    return (p[f"{col}{h}_2"] - p[f"{col}{h}_1"]).to_numpy()


def spec_naive(p):
    """Δefficiency on Δusage share: the repo definition, nothing held fixed."""
    return wls([_d(p, "usage_share")], _d(p, "efficiency"), p.w.to_numpy())[1] * STEP


def spec_minutes(p):
    """Δefficiency on Δusage share, holding Δ(share of the season played) fixed."""
    return wls([_d(p, "usage_share"), _d(p, "minutes_share")],
               _d(p, "efficiency"), p.w.to_numpy())[1] * STEP


def spec_on_pitch(p):
    """Δefficiency on Δ(usage share per unit of time on the pitch)."""
    return wls([_d(p, "usage_on_pitch")], _d(p, "efficiency"), p.w.to_numpy())[1] * STEP


def spec_split_half(p):
    """As spec_minutes, but usage measured on odd matches and efficiency on even
    matches (and the reverse; the two are averaged). A low-xG shot raises usage
    and lowers efficiency in the same match; splitting removes that shared noise."""
    out = []
    for hu, he in ((0, 1), (1, 0)):
        q = p.dropna(subset=[f"efficiency_h{he}_1", f"efficiency_h{he}_2",
                             f"usage_share_h{hu}_1", f"usage_share_h{hu}_2"])
        out.append(wls([_d(q, "usage_share", f"_h{hu}"), _d(q, "minutes_share")],
                       _d(q, "efficiency", f"_h{he}"), q[f"w_h{he}"].to_numpy())[1])
    return float(np.mean(out)) * STEP


def spec_baseline(p):
    """As spec_split_half, plus last season's efficiency from the other half as a
    control. Players coming off a lucky season drift back down whatever happens
    to their usage; this soaks up that regression to the mean."""
    out = []
    for hu, he in ((0, 1), (1, 0)):
        q = p.dropna(subset=[f"efficiency_h{he}_1", f"efficiency_h{he}_2",
                             f"usage_share_h{hu}_1", f"usage_share_h{hu}_2",
                             f"efficiency_h{hu}_1"])
        out.append(wls([_d(q, "usage_share", f"_h{hu}"), _d(q, "minutes_share"),
                        q[f"efficiency_h{hu}_1"].to_numpy()],
                       _d(q, "efficiency", f"_h{he}"), q[f"w_h{he}"].to_numpy())[1])
    return float(np.mean(out)) * STEP


def spec_vs_teammates(p):
    """As spec_minutes, with the outcome measured against team-mates' efficiency
    that season, so a move to a team that makes better or worse chances cancels."""
    y = ((p.efficiency_2 - p.mates_eff_2) - (p.efficiency_1 - p.mates_eff_1)).to_numpy()
    return wls([_d(p, "usage_share"), _d(p, "minutes_share")], y, p.w.to_numpy())[1] * STEP


SPECS = [
    ("naive", "Repo usage share, nothing held fixed", spec_naive, "all"),
    ("minutes", "Holding minutes fixed", spec_minutes, "all"),
    ("on_pitch", "Usage per minute on the pitch", spec_on_pitch, "all"),
    ("split_half", "Split-half, minutes fixed (headline)", spec_split_half, "all"),
    ("baseline", "Split-half plus last season's efficiency", spec_baseline, "all"),
    ("movers", "Club changers only", spec_minutes, "movers"),
    ("stayers", "Same club both seasons", spec_minutes, "stayers"),
    ("movers_vs_mates", "Club changers, efficiency relative to team-mates", spec_vs_teammates, "movers"),
    ("all_vs_mates", "Everyone, efficiency relative to team-mates", spec_vs_teammates, "all"),
]


def within(p: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for key, label, fn, sub in SPECS:
        d = p if sub == "all" else p[p.mover] if sub == "movers" else p[~p.mover]
        point, lo, hi = cluster_boot(d, fn)
        rows.append(dict(spec=key, label=label, subset=sub, n_pairs=len(d),
                         n_players=d.tm_player_id.nunique(),
                         slope_per_5pp=point, ci_lo=lo, ci_hi=hi))
    return pd.DataFrame(rows)


def within_bins(p: pd.DataFrame) -> pd.DataFrame:
    """Binned picture of the headline spec: Δefficiency (minutes partialled out)
    against Δusage share, for the supporting figure."""
    dm = _d(p, "minutes_share")
    w = p.w.to_numpy()
    resid = {}
    for col in ("usage_share", "efficiency"):
        y = _d(p, col)
        b = wls([dm], y, w)
        resid[col] = y - b[0] - b[1] * dm
    d = p[["tm_player_id", "w", "mover"]].assign(du=resid["usage_share"], de=resid["efficiency"])
    d["bin"] = pd.qcut(d.du, 10, labels=False)

    def stat(x):
        g = x.groupby("bin")
        return np.concatenate([
            g.apply(lambda s: np.average(s.du, weights=s.w), include_groups=False).to_numpy(),
            g.apply(lambda s: np.average(s.de, weights=s.w), include_groups=False).to_numpy()])
    point, lo, hi = cluster_boot(d, stat, n_boot=N_BOOT // 2)
    k = 10
    return pd.DataFrame({"decile": range(k), "d_usage": point[:k], "d_eff": point[k:],
                         "d_eff_lo": lo[k:], "d_eff_hi": hi[k:],
                         "n": d.groupby("bin").size().to_numpy()})


# ------------------------------------------------------------------ main

def main():
    panel = pd.read_parquet(WORK / "panel.parquet")
    a = sample(panel)
    p = pairs(a)

    rel = reliability(panel)
    rel.to_csv(OUT / "reliability.csv", index=False, float_format="%.4f")

    cv = pd.concat([curve(a, "usage_share"), curve(a, "usage_on_pitch")])
    cv.to_csv(OUT / "curve_bins.csv", index=False, float_format="%.5f")

    ws = within(p)
    med = float(a.efficiency.median())
    ws["pct_of_median"] = ws.slope_per_5pp / med * 100
    ws["ci_lo_pct"] = ws.ci_lo / med * 100
    ws["ci_hi_pct"] = ws.ci_hi / med * 100
    ws.to_csv(OUT / "within_slopes.csv", index=False, float_format="%.5f")
    wb = within_bins(p)
    wb.to_csv(OUT / "within_bins.csv", index=False, float_format="%.5f")

    cs = panel[panel.tm_player_id.isin(CASES)].copy()
    cs["player"] = cs.tm_player_id.map(CASES)
    cs = cs.sort_values(["player", "season"])[
        ["player", "season", "league", "team", "minutes", "actions", "usage_share",
         "minutes_share", "usage_on_pitch", "efficiency", "mates_eff"]]
    cs.to_csv(OUT / "case_studies.csv", index=False, float_format="%.4f")

    xs = cross_section_slope(a)
    head = ws.set_index("spec").loc["split_half"]
    summary = dict(
        min_minutes=MIN_MINUTES,
        n_player_seasons=int(len(a)), n_players=int(a.tm_player_id.nunique()),
        n_pairs=int(len(p)), n_mover_pairs=int(p.mover.sum()),
        seasons=f"{a.season.min()} to {a.season.max()}",
        median_efficiency=med, median_usage_share=float(a.usage_share.median()),
        cross_section_slope_per_5pp=dict(zip(["point", "lo", "hi"], map(float, xs))),
        headline_slope_per_5pp=dict(point=float(head.slope_per_5pp),
                                    lo=float(head.ci_lo), hi=float(head.ci_hi)),
        headline_pct_of_median=dict(point=float(head.slope_per_5pp / med * 100),
                                    lo=float(head.ci_lo / med * 100),
                                    hi=float(head.ci_hi / med * 100)),
        specs={r.spec: dict(point=r.slope_per_5pp, lo=r.ci_lo, hi=r.ci_hi,
                            pct=r.pct_of_median, pct_lo=r.ci_lo_pct, pct_hi=r.ci_hi_pct,
                            n_pairs=int(r.n_pairs)) for r in ws.itertuples()},
        corr_usage_minutes=float(a[["usage_share", "minutes_share"]].corr().iloc[0, 1]),
    )
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2))

    pd.set_option("display.width", 160)
    print(rel.round(3).to_string(index=False))
    print(cv[cv.usage_measure == "usage_share"].round(4).to_string(index=False))
    print(ws.round(5).to_string(index=False))
    print(wb.round(4).to_string(index=False))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
