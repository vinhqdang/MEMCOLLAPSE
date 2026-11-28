"""Analyse decision-impact probes (scripts/probe_decisions.py output).

Per model x budget: decision accuracy and lure rate by strategy x frequency; the frequency DiD
(logf x memory vs full context, claim FE, dialogue-clustered SE); and the paired gain of each
strategy over rolling on single-mention claims.

Usage: python scripts/analyze_decisions.py results/decisions/*.jsonl
"""
from __future__ import annotations

import sys
import warnings

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf


def load(paths: list[str]) -> pd.DataFrame:
    d = pd.concat([pd.read_json(p, lines=True) for p in paths], ignore_index=True)
    d["claim"] = d["domain"] + ":" + d["claim_id"]
    d["dlg"] = d["domain"] + ":" + d["dialogue_id"]
    d["logf"] = np.log2(d["freq"])
    d["y"] = d["correct"].astype(int)
    d["lure"] = (d["choice"] == "lure").astype(int)
    return d


def ols(formula: str, d: pd.DataFrame):
    return smf.ols(formula, d).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d["dlg"])[0]})


def report(g: pd.DataFrame, model: str) -> None:
    print(f"\n===== {model}  domains={sorted(g.domain.unique())} =====")
    tab = g.groupby(["strategy", "budget", "freq"]).agg(acc=("y", "mean"), lure=("lure", "mean"))
    print(tab.unstack("freq").round(3).to_string())
    full = g[g.strategy == "full"]
    for (st, b), m in g[~g.strategy.isin(["full", "empty"])].groupby(["strategy", "budget"]):
        s = pd.concat([full.assign(mem=0), m.assign(mem=1)])
        for out in ("y", "lure"):
            r = ols(f"{out} ~ logf * mem + since_last + C(claim)", s)
            k = "logf:mem"
            print(f"  DiD {out:4s} {st:12s} B={b:<3d} {r.params[k]:+.3f} (p={r.pvalues[k]:.3g})")
    for b in sorted(g.loc[g.strategy == "rolling", "budget"].unique()):
        base = g[(g.strategy == "rolling") & (g.budget == b) & (g.freq == 1)]
        for st in sorted(set(g.strategy) - {"full", "empty", "rolling"}):
            m = g[(g.strategy == st) & (g.budget == b) & (g.freq == 1)]
            if m.empty:
                continue
            s = pd.concat([base.assign(treat=0), m.assign(treat=1)])
            r = ols("y ~ treat + C(claim) + C(t)", s)
            rl = ols("lure ~ treat + C(claim) + C(t)", s)
            print(f"  f=1 gain over rolling B={b:<3d} {st:12s} acc {r.params['treat']:+.3f} "
                  f"(p={r.pvalues['treat']:.3g}) | lure {rl.params['treat']:+.3f} (p={rl.pvalues['treat']:.3g})")


def main() -> None:
    d = load(sys.argv[1:])
    for model, g in d.groupby("model"):
        report(g, model)


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    main()
