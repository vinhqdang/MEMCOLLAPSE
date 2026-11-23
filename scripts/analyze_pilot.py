"""Summaries + logistic regression for pilot probe records.

Usage: python scripts/analyze_pilot.py results/pilot/probes_*.jsonl
"""
from __future__ import annotations

import sys

import pandas as pd
import statsmodels.formula.api as smf


def load(paths: list[str]) -> pd.DataFrame:
    return pd.concat([pd.read_json(p, lines=True) for p in paths], ignore_index=True)


def summarize(d: pd.DataFrame) -> None:
    print("== accuracy by strategy x importance (all probes after first mention) ==")
    print(d.groupby(["model", "strategy", "budget", "importance"])[["correct", "chose_not_mentioned"]]
          .mean().round(3).to_string())
    post = d[(d.since_last >= 0)]
    print("\n== after last mention: accuracy by freq ==")
    print(post.groupby(["model", "strategy", "budget", "importance", "freq"])["correct"]
          .agg(["mean", "size"]).round(3).unstack("freq").to_string())
    end = post[post.t == post.t.max()]
    print("\n== final session (end-of-dialogue recoverability) by freq ==")
    print(end.groupby(["model", "strategy", "budget", "importance", "freq"])["correct"]
          .mean().round(3).unstack("freq").to_string())


def regress(d: pd.DataFrame) -> None:
    post = d[d.strategy.str.startswith("rolling") & (d.since_last >= 0)].copy()
    post["y"] = post.correct.astype(int)
    post["logf"] = post.freq.map({1: 0, 2: 1, 4: 2})
    for (model, strat, budget, imp), g in post.groupby(["model", "strategy", "budget", "importance"]):
        model = f"{model} {strat}"
        try:
            fit = smf.glm("y ~ logf + since_last + last + C(claim_id)", data=g,
                          family=__import__("statsmodels.api").api.families.Binomial()
                          ).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(g.dialogue_id)[0]})
            print(f"{model} B={budget} {imp}: beta_logf={fit.params['logf']:.3f} "
                  f"(p={fit.pvalues['logf']:.3g}), beta_since_last={fit.params['since_last']:.3f} "
                  f"n={len(g)}")
        except Exception as exc:  # report and continue; small pilots can be separable
            print(f"{model} B={budget} {imp}: fit failed: {exc}")


if __name__ == "__main__":
    data = load(sys.argv[1:])
    summarize(data)
    print("\n== GLM (rolling, post-last-mention), claim fixed effects, dialogue-clustered SE ==")
    regress(data)
