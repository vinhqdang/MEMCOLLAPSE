"""Figure 1: post-last-mention accuracy vs. mention frequency, by memory strategy.

Usage: python scripts/plot_retention.py OUT.pdf BUDGET probes_*.jsonl[.gz]
Rows: models; columns: critical / incidental. Error bars: 95% CI, dialogue-clustered bootstrap.
"""
from __future__ import annotations

import sys

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from analyze_bench import load  # noqa: E402

STYLE = {"full": ("#1f4e79", "o", "full context"),
         "truncate": ("#8c8c8c", "s", "truncation"),
         "rolling": ("#c0392b", "^", "rolling summary")}
N_BOOT = 500


def boot_ci(g: pd.DataFrame, rng: np.random.Generator) -> tuple[float, float]:
    per = g.groupby("dlg")["y"].agg(["sum", "count"]).to_numpy()
    idx = rng.integers(0, len(per), size=(N_BOOT, len(per)))
    s = per[idx].sum(axis=1)
    est = s[:, 0] / s[:, 1]
    return float(np.percentile(est, 2.5)), float(np.percentile(est, 97.5))


def main() -> None:
    out, budget, paths = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
    d = load(paths)
    full_t = set(d.loc[d.strategy == "full", "t"])
    d = d[d.t.isin(full_t) & ((d.budget == budget) | (d.strategy == "full"))]
    rng = np.random.default_rng(0)
    models = sorted(d.model.unique())
    fig, axes = plt.subplots(len(models), 2, figsize=(3.3, 1.55 * len(models) + 0.4),
                             sharex=True, sharey=True, squeeze=False)
    for r, model in enumerate(models):
        for c, imp in enumerate(("critical", "incidental")):
            ax = axes[r, c]
            for strat, (col, mk, lab) in STYLE.items():
                g = d[(d.model == model) & (d.importance == imp) & (d.strategy == strat)]
                if g.empty:
                    continue
                xs, ys, lo, hi = [], [], [], []
                for f, gf in g.groupby("freq"):
                    a, b = boot_ci(gf, rng)
                    xs.append(f); ys.append(gf.y.mean()); lo.append(a); hi.append(b)
                ys_a = np.array(ys)
                ax.errorbar(xs, ys, yerr=[ys_a - lo, np.array(hi) - ys_a], color=col, marker=mk,
                            ms=3.5, lw=1.2, capsize=2, label=lab)
            ax.set_xscale("log", base=2)
            ax.set_xticks([1, 2, 4], ["1", "2", "4"])
            ax.set_ylim(0, 1.02)
            ax.grid(alpha=0.25, lw=0.5)
            ax.tick_params(labelsize=7)
            if r == 0:
                ax.set_title(imp, fontsize=8)
            if c == 0:
                ax.set_ylabel(model.replace("-Instruct", "").replace("-instruct", "").replace("@nf4", " (NF4)"), fontsize=7)
            if r == len(models) - 1:
                ax.set_xlabel("mentions $f$", fontsize=7)
    h, lab = axes[0, 0].get_legend_handles_labels()
    fig.legend(h, lab, loc="upper center", ncol=3, fontsize=6.5, frameon=False,
               bbox_to_anchor=(0.5, 1.0))
    fig.tight_layout(rect=(0, 0, 1, 0.95), h_pad=0.4, w_pad=0.4)
    fig.savefig(out)


if __name__ == "__main__":
    main()
