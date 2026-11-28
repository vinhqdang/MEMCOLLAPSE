"""Single-mention critical accuracy per strategy x budget with 95% dialogue-clustered bootstrap CIs.

Same cells as analyze_methods.py: post-last-mention probes at the checkpoints where full context
was probed. Usage: python scripts/table_f1_ci.py results/bench/probes_X.jsonl results/methods/probes_X_*.jsonl
"""
from __future__ import annotations

import sys

import numpy as np

from analyze_bench import load

N_BOOT = 1000


def main() -> None:
    d = load(sys.argv[1:])
    full_t = set(d.loc[d.strategy == "full", "t"])
    d = d[d.t.isin(full_t) & (d.importance == "critical") & (d.freq == 1)]
    rng = np.random.default_rng(0)
    for (st, b), g in d.groupby(["strategy", "budget"]):
        per = g.groupby("dlg")["y"].agg(["sum", "count"]).to_numpy()
        s = per[rng.integers(0, len(per), size=(N_BOOT, len(per)))].sum(axis=1)
        lo, hi = np.percentile(s[:, 0] / s[:, 1], [2.5, 97.5])
        print(f"{st:14s} B={b:<3d} acc={g.y.mean():.3f} [{lo:.3f}, {hi:.3f}] n={len(g)}")


if __name__ == "__main__":
    main()
