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
The effect survives when repeated mentions are not introduced earlier. (Phi B=160 rerun pending.)

## 4. Importance sensitivity differs by model
gemma-4-E4B keeps critical claims far more than incidental (0.64 vs 0.10 post-last-mention, B=160),
yet still loses ~60% of single-mention critical claims by session 16. Phi-3.5 is importance-blind
(critical ~= incidental). Larger/better models change *what* is kept, not whether rare claims erode.

## Open issues before scaling
1. Single domain, template dialogues -> add 2-3 domains + a naturalistic (LLM-paraphrased) variant.
2. Probe uses the summariser model as reader -> add a fixed external reader.
3. Decision-impact metric (does erasure flip downstream decisions?) not yet measured.
4. Method: importance/provenance-aware compression vs Compaction-Cliff typing and ACE at equal budget.
