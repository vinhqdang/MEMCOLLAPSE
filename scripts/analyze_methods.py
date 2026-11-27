"""Compare memory strategies at equal budget against the benchmark's full / rolling conditions.

Reports, per model x budget (post-last-mention probes at the checkpoints where full context was
probed, so every strategy is scored on the same (claim, t) cells):
  1. accuracy by strategy x importance x frequency, and retention relative to full context;
  2. the frequency slope of each strategy (probability scale, claim FE, dialogue-clustered SE);
  3. the paired gain of each strategy over generic rolling on critical claims, with the gain
     on f=1 critical claims (the cell the paper is about) reported separately;
  4. mean memory size actually used (words), since itemised memories may under-fill the budget.

Usage: python scripts/analyze_methods.py [--base STRATEGY] results/bench/probes_heron_X.jsonl results/methods/probes_heron_X_*.jsonl
"""
from __future__ import annotations

import sys

import pandas as pd
import statsmodels.formula.api as smf

from analyze_bench import load

BASE = "rolling"


def ols(formula: str, d: pd.DataFrame):
    return smf.ols(formula, d).fit(cov_type="cluster",
                                   cov_kwds={"groups": pd.factorize(d["dlg"])[0]})


def strategy_order(d: pd.DataFrame) -> list[str]:
    first = ["full", "rolling", "rolling-imp", "typed", "ace", "ledger-supp", "ledger-noprov", "ledger-tier",
             "ledger"]
    present = list(d.strategy.unique())
    return [s for s in first if s in present] + sorted(set(present) - set(first))


def accuracy_table(d: pd.DataFrame, b: int, order: list[str]) -> None:
    s = d[(d.budget == b) | (d.strategy == "full")]
    acc = s.groupby(["importance", "strategy", "freq"])["y"].mean().unstack("freq")
    full = acc.xs("full", level="strategy")
    print(f"\n-- accuracy (retention vs full) B={b} --")
    for imp in ("critical", "incidental"):
        for st in order:
            if (imp, st) not in acc.index:
                continue
            row = acc.loc[(imp, st)]
            cells = " ".join(f"f{f}={row[f]:.3f}({row[f] / full.loc[imp, f]:.2f})"
                             for f in row.index)
            print(f"  {imp:10s} {st:14s} {cells}")


def slopes(d: pd.DataFrame, b: int, order: list[str]) -> None:
    print(f"\n-- frequency slope per doubling (prob scale) B={b} --")
    for imp in ("critical", "incidental"):
        out = []
        for st in order:
            g = d[(d.strategy == st) & ((d.budget == b) | (st == "full")) & (d.importance == imp)]
            if g.empty:
                continue
            r = ols("y ~ logf + since_last + C(claim)", g)
            out.append(f"{st}={r.params['logf']:+.3f}{'*' if r.pvalues['logf'] < .05 else ''}")
        print(f"  {imp:10s} " + "  ".join(out))


def gains(d: pd.DataFrame, b: int, order: list[str]) -> None:
    print(f"\n-- gain over {BASE} (same claim, t, dialogue; claim FE, clustered) B={b} --")
    for st in order:
        if st in ("full", BASE):
            continue
        for label, cond in (("critical all", d.importance == "critical"),
                            ("critical f=1", (d.importance == "critical") & (d.freq == 1)),
                            ("incidental", d.importance == "incidental")):
            g = d[cond & (d.budget == b) & d.strategy.isin([BASE, st])]
            if g.strategy.nunique() < 2:
                continue
            g = g.assign(treat=(g.strategy == st).astype(int))
            r = ols("y ~ treat + C(claim) + C(t)", g)
            print(f"  {st:14s} {label:13s} {r.params['treat']:+.3f} "
                  f"[{r.conf_int().loc['treat', 0]:+.3f},{r.conf_int().loc['treat', 1]:+.3f}] "
                  f"p={r.pvalues['treat']:.2g}")


def sizes(d: pd.DataFrame, b: int, order: list[str]) -> None:
    w = (d[(d.budget == b)].drop_duplicates(["strategy", "dialogue_id", "t"])
         .groupby("strategy")["memory_words"].mean())
    print(f"\n-- mean memory words B={b}: " +
          " ".join(f"{s}={w[s]:.0f}" for s in order if s in w.index))


def main() -> None:
    global BASE
    args = sys.argv[1:]
    if args[:1] == ["--base"]:  # compare against another strategy instead of generic rolling
        BASE, args = args[1], args[2:]
    d = load(args)
    full_t = set(d.loc[d.strategy == "full", "t"])
    d = d[d.t.isin(full_t)]
    order = strategy_order(d)
    for model, g in d.groupby("model"):
        print(f"\n===== {model}  domains={sorted(g.domain.unique())} =====")
        for b in sorted(x for x in g.budget.unique() if x > 0):
            accuracy_table(g, b, order)
            slopes(g, b, order)
            gains(g, b, order)
            sizes(g, b, order)


if __name__ == "__main__":
    main()
