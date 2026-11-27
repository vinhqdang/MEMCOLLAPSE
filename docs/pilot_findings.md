# Pilot findings (2026-11-23)

Setup: 1 domain (clinic booking migration), 24 claims (12 critical, 12 incidental), 48 dialogues x 16 sessions,
claim frequency in {1,2,4} counterbalanced across dialogues, last-mention session drawn independently of frequency.
Memory: rolling LLM summary (budget 80/160 words, generic prompt), truncation (last-B words), full transcript.
Probe: 4-way MCQ incl. "not mentioned", answered by the same model from memory only.
Analysis: binomial GLM on post-last-mention probes, claim fixed effects, last-mention + time-since-last covariates,
dialogue-clustered SEs (`scripts/analyze_pilot.py`).

## 1. Frequency-driven erasure (spread schedule)

End-of-dialogue recoverability, critical claims, rolling B=160:

| model | f=1 | f=2 | f=4 | full context |
|---|---|---|---|---|
| Qwen2.5-1.5B | 0.18 | 0.58 | 0.72 | 0.99-1.00 |
| Phi-3.5-mini | 0.23 | 0.46 | 0.46 | 0.78-0.89 |
| gemma-4-E4B | 0.41 | 0.44 | 0.48 | 0.97-1.00 |
| Qwen2.5-7B | 0.17 | 0.50 | 0.47 | 0.96-1.00 |

beta(log2 freq) for critical claims > 0 and significant (p<0.05) in 8/8 model x budget cells;
for incidental claims in 6/8 (gemma: n.s.).

## 2. Controls
- Full context: nearly flat in frequency -> probe is not frequency-biased.
- Truncation: flat in frequency -> the effect is specific to iterative summarisation, not recency.
- Empty memory: 0-19% (prior guessability floor).

## 3. Frequency vs. first-mention confound (clustered schedule, mentions in [L-f+1, L])
Qwen2.5-1.5B: beta_logf = 0.78 / 0.66 (B=80, crit/incid), 1.30 / 1.79 (B=160); all p <= 0.013.
Phi-3.5-mini (critical): beta_logf = 0.37 (p=0.010, B=80), 0.39 (p=0.017, B=160); incidental 0.23 (n.s.) / 0.40 (p=0.012).
The effect survives in both models when repeated mentions are not introduced earlier.

## 4. Importance sensitivity differs by model
gemma-4-E4B keeps critical claims far more than incidental (0.64 vs 0.10 post-last-mention, B=160),
yet still loses ~60% of single-mention critical claims by session 16. Phi-3.5 is importance-blind
(critical ~= incidental). Larger/better models change *what* is kept, not whether rare claims erode.

## Open issues before scaling
1. Single domain, template dialogues -> add 2-3 domains + a naturalistic (LLM-paraphrased) variant.
2. Probe uses the summariser model as reader -> add a fixed external reader.
3. Decision-impact metric (does erasure flip downstream decisions?) not yet measured.
4. Method: importance/provenance-aware compression vs Compaction-Cliff typing and ACE at equal budget.

## 5. Full-context DiD control (2026-11-24, `scripts/analyze_bench.py`)
The full-transcript condition is not perfectly flat in frequency (more paraphrases in context
make the MCQ easier), so the summarisation-specific effect is the logf x rolling interaction
against full context at shared checkpoints, on the probability scale (logit DiD is unstable
near the full-context ceiling; gemma separates).

Heron, B=160, prob-scale slope per doubling of frequency (full -> rolling, DiD p):
- Qwen2.5-1.5B critical +0.006 -> +0.272 (p=4e-19); incidental +0.036 -> +0.219 (p=7e-10)
- Qwen2.5-7B   critical +0.019 -> +0.185 (p=2e-5);  incidental +0.021 -> +0.116 (p=1e-4)
- Phi-3.5      critical n.s.; incidental +0.016 -> +0.133 (p=0.003)
- gemma-4-E4B  n.s. (importance-driven retention; incidental nearly all erased)

Phi-3.5 on city/science/product (pooled, 3 domains): full-context slope ~+0.077 (critical) and
rolling slope smaller (+0.02/+0.04) -> no summarisation-specific frequency effect; Phi erases
most claims regardless (retention rolling/full 0.14-0.38). The frequency effect is therefore
model-dependent: strong in the Qwen family, weak/absent in Phi, superseded by importance in gemma.

Qwen2.5-1.5B on city/science/product (pooled, B=160): full-context flat (slope +0.006..+0.013);
rolling slope +0.160; DiD critical +0.147 (p=2e-15), incidental +0.154 (p=1e-21).
Per domain DiD (critical / incidental, B=160): city +0.10 / +0.12, science +0.15 / +0.19,
product +0.19 / +0.15, all p<=0.002. Single-mention claims retain 4-22% of full-context
accuracy vs 36-53% at f=4. B=80: summaries erase nearly everything (DiD small/n.s. for critical).

Qwen2.5-7B (NF4) B=160, DiD critical / incidental: Heron +0.105 (p=0.002) / +0.127 (p=2e-5);
city+science+product pooled +0.034 (p=0.03) / +0.003 (n.s.). Weaker cross-domain than Qwen-1.5B.
Quantisation check (Heron, bf16 vs NF4): Qwen-7B DiD crit +0.166 vs +0.105, incid +0.095 vs +0.127;
gemma n.s. in both, critical retention 0.6 vs 0.5-0.6, incidental ~0.1 in both -> conclusions unchanged.

## Naturalised dialogues (Qwen2.5-1.5B, LLM-rewritten sessions)

Prob-scale DiD logf x rolling vs full, post-last-mention (results/natural/analysis/):

| Domain | crit B=80 | crit B=160 | incid B=80 | incid B=160 |
|---|---|---|---|---|
| Heron | +0.038 (p=.12) | +0.218 (p=3e-12) | +0.042 (p=.049) | +0.176 (p=5e-10) |
| city | +0.049 (p=.11) | +0.062 (p=.047) | -0.005 | +0.021 |
| pooled | +0.044 (p=.025) | +0.140 (p=2e-9) | +0.019 | +0.099 (p=1e-7) |

Templated reference (B=160 crit): Heron +0.27, city +0.10. Effect persists, ~20-40% smaller.
City incidental: rolling erases nearly everything (5-12% retention), so there is no gradient left to measure.

## Fixed reader (Qwen2.5-7B NF4 re-probes every writer's Heron memories)

Results are in results/reader/analysis_q7b_reader.txt.
- Qwen-1.5B writer: crit DiD at B=160 is +0.255 (p=3e-14), versus +0.272 when it reads its own memories.
- Phi writer: only incidental is significant (+0.101).
- gemma writer: no effect.

So the gradient lives in the memory, not the reader.
