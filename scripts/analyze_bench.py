"""Pooled multi-domain analysis with a full-context difference-in-differences control.

The frequency effect attributable to summarisation is the logf x rolling interaction:
how much more the rolling-summary condition depends on frequency than the full-transcript
condition at the same checkpoints (t in {4, 8, 12, T}). This removes any frequency bias of the
probe itself (repeated mentions -> more paraphrases in context -> easier MCQ).

Usage: python scripts/analyze_bench.py results/bench/probes_*.jsonl [results/pilot/probes_*.jsonl.gz]
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf


def load(paths: list[str]) -> pd.DataFrame:
    d = pd.concat([pd.read_json(p, lines=True) for p in paths], ignore_index=True)
    d["domain"] = d["dialogue_id"].str.extract(r"^([a-z_]+)")[0]
    d["claim"] = d["domain"] + ":" + d["claim_id"]
    d["dlg"] = d["domain"] + ":" + d["dialogue_id"]
    d["logf"] = np.log2(d["freq"])
    d["y"] = d["correct"].astype(int)  # bool endog would be split into 2 columns by patsy
    d["model"] = d["model"].str.split("/").str[-1]
    return d[d["t"] > d["last"]].copy()  # post-last-mention probes only


def fit(formula: str, d: pd.DataFrame):
    return smf.glm(formula, d, family=sm.families.Binomial()).fit(
        cov_type="cluster", cov_kwds={"groups": pd.factorize(d["dlg"])[0]})


def table(d: pd.DataFrame) -> None:
    full_t = set(d.loc[d.strategy == "full", "t"])
    sub = d[d.strategy.isin(["full", "rolling"]) & d.t.isin(full_t)]
    print(sub.groupby(["model", "importance", "strategy", "budget", "freq"])["correct"].mean()
          .unstack("freq").round(3).to_string())


def did(d: pd.DataFrame) -> None:
    print("\n== DiD: logf x rolling (rolling vs full at shared checkpoints), claim FE ==")
    full_t = set(d.loc[d.strategy == "full", "t"])
    for (model, imp), g in d.groupby(["model", "importance"]):
        for b in sorted(g.loc[g.strategy == "rolling", "budget"].unique()):
            s = g[((g.strategy == "rolling") & (g.budget == b)) | (g.strategy == "full")]
            s = s[s.t.isin(full_t)].assign(roll=lambda x: (x.strategy == "rolling").astype(int))
            r = fit("y ~ logf * roll + since_last + C(claim)", s)
            lp = smf.ols("y ~ logf * roll + since_last + C(claim)", s).fit(
                cov_type="cluster", cov_kwds={"groups": pd.factorize(s["dlg"])[0]})
            k = "logf:roll"
            acc = s.groupby(["roll", "freq"])["y"].mean()
            ret = " ".join(f"f{f}={acc[1, f] / acc[0, f]:.2f}" for f in (1, 2, 4))
            print(f"{model:24s} {imp:10s} B={b:<3d} logit DiD={r.params[k]:+.3f} (p={r.pvalues[k]:.3g}) | "
                  f"prob slopes full={lp.params['logf']:+.3f} roll={lp.params['logf'] + lp.params[k]:+.3f} "
                  f"DiD={lp.params[k]:+.3f} (p={lp.pvalues[k]:.3g}) | retention {ret} | n={len(s)}")


def rolling_only(d: pd.DataFrame) -> None:
    print("\n== rolling only, all post-last-mention checkpoints, pooled over domains ==")
    roll = d[d.strategy == "rolling"]
    for (model, imp, b), g in roll.groupby(["model", "importance", "budget"]):
        r = fit("y ~ logf + since_last + last + C(claim)", g)
        print(f"{model:32s} {imp:10s} B={b:<3d} beta_logf={r.params['logf']:+.3f} "
              f"(p={r.pvalues['logf']:.3g}) n={len(g)} domains={g.domain.nunique()}")


def main() -> None:
    d = load(sys.argv[1:])
    table(d)
    rolling_only(d)
    did(d)


if __name__ == "__main__":
    main()
