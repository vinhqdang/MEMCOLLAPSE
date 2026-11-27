# Method comparison: design notes and known asymmetries (to report in the paper)

- Itemised strategies (ace, ledger*) select from a full-session delta (max 320 new tokens) and are
  not told the budget; code then evicts to the budget. Summary strategies get 2*B+32 tokens and are
  told the budget. Both satisfy the same hard word budget on the *stored memory*; the asymmetry is
  in the selection step and is inherent to delta-based memory (as in ACE).
- Provenance tags count against the budget, so `ledger` holds fewer items than `ledger-noprov`;
  report kept items per strategy (stats_*.json: kept_items_final).
- `protected` degenerates to recency if the model labels nearly everything as a protected type;
  report kept_types_final and evicted_protected.
- ACE-style baseline differs from ledger in prompt (untyped notes vs TYPE | SPEAKER | claim) as
  well as policy (recency) and rendering (no provenance); ledger-supp / ledger-noprov isolate
  policy and provenance on the identical extractor.
- `rolling-imp` names the target classes (warnings, conditions, dissent) in its prompt: a deliberately
  strong prompt-only baseline. `typed` benefits from tail clipping (OTHER section last).
- Format compliance (lines_bad, bad_per_session, empty_ledgers, truncated_outputs) is logged per
  run; itemised failures surface as empty/poor memories, which the summary family cannot suffer.
- Same-session eviction ties are broken by a content hash, not by output order.
- For itemised strategies the memories file's raw_words is the pre-eviction ledger size, not a
  budget-compliance measure.

## Extract-then-consolidate (redesign, 2026-11-25)

- First design: the model saw the numbered ledger and wrote `SAME | n` for restatements.
  Qwen2.5-1.5B could not follow it on Heron: ACE produced 12.9k unparsable lines vs 125 notes, and
  63% of memories were empty (looping `SAME | 1 ... 57`, `SAME | <copied item>`). Those runs were
  discarded.
- Now the extractor sees only the newest session; it never sees the memory, so it cannot copy old
  items back and refresh their recency/provenance falsely. Code consolidates: a claim merges into
  an existing item when content-word overlap coefficient >= 0.4 and the two do not mention
  different numbers (status updates with new figures stay separate items; the stale one ages out).
- Threshold calibrated on bank paraphrases of the same claim (merge rate 0.80-0.91 across the 4
  domains) vs pairs of different claims (1 false merge in ~9.6k pairs); see test_ledger.
- On the real model (4 Heron dialogues, 8 sessions): ACE 240 claims, 1 bad line; ledger 125
  claims, 0 bad lines, 27 merges. The 1.5B model's type labels are noisy (e.g. "no blockers"
  typed DISSENT), which is part of what the protected policy has to survive; report type stats.
- Merge errors cost the ledger in two ways: missed merges duplicate items (budget), false merges
  hide a distinct claim. Both are measurable offline from memories_*.jsonl.

## Results: Qwen2.5-1.5B, 4 domains (2026-11-26)

Full tables: `results/methods/analysis/qwen15_{heron,city,science,product,pooled}.txt`.
Gain over generic rolling on the same (claim, t, dialogue), claim FE, dialogue-clustered SE, pooled
over 4 domains (* = p<0.05):

| strategy | B=80 crit. all | B=80 crit. f=1 | B=160 crit. all | B=160 crit. f=1 | freq. slope B=160 |
|---|---|---|---|---|---|
| typed | +0.145* | +0.022 | +0.150* | +0.024 | +0.282 |
| ledger-noprov | -0.043* | +0.008 | +0.079* | +0.255* | +0.059 |
| ledger-tier | +0.021 | +0.060* | +0.166* | +0.315* (p=1e-38) | +0.088 |

Rolling slope at B=160: +0.189; full context: +0.011.

- ledger-tier is the best strategy at B=160 in every domain (f=1 gain +0.23 to +0.36) and beats
  ledger-noprov on f=1, f=4 and critical-all: demoting decisions below warnings/conditions/dissent
  was the right call.
- Typed compaction raises critical accuracy but only for repeated claims; it is the most
  frequency-biased strategy (slope 0.28). Prompt-level importance cues do not fix the frequency
  bias; explicit item retention does.
- B=80 is too tight for any strategy to rescue singletons by much (+0.06 at best).
- Cost: incidental claims lose about 0.06-0.09 under itemised strategies.

## Results: Qwen2.5-7B NF4, 3 domains (heron, city, science; 2026-11-27)

Full tables: `results/methods/analysis/qwen7_*.txt`. Pooled, critical claims, accuracy at f=1:

| strategy | B=80 | B=160 |
|---|---|---|
| rolling | 0.12 | 0.17 |
| rolling-imp | 0.40 | 0.70 |
| typed | 0.31 | 0.46 |
| ledger-noprov | 0.44 | 0.71 |
| ledger-tier | 0.62 | 0.71 |

Direct paired test, ledger-tier minus rolling-imp (`--base rolling-imp`,
`*_pooled_vs_rollingimp.txt`):

| model | B=80 crit. f=1 | B=80 crit. all | B=160 crit. f=1 | B=160 crit. all |
|---|---|---|---|---|
| Qwen-1.5B (4 dom.) | +0.049* | -0.027 | +0.276* | +0.166* |
| Qwen-7B (3 dom.) | +0.221* | +0.148* | +0.016 | -0.028 |

- ledger-tier never loses to the strongest prompt baseline on singleton critical claims and wins
  in 3 of 4 model x budget cells. Where the model follows the importance prompt well and the
  budget is loose (7B, B=160), the prompt fix is as good; the ledger's advantage lives where the
  summariser is weak (1.5B) or the budget is tight (B=80).
- Tiered vs protected eviction only matters when protected items must be evicted (tight budget):
  identical at 7B B=160, +0.18 f=1 at 7B B=80.
- Typed compaction is the most frequency-biased strategy at both model sizes.

## Gemma-4 E4B: wholesale overwrite at B=160 on product

On product at B=160 gemma writes notes for the newest meeting only ("Meeting Notes (Meeting 16)"),
dropping the history: retention ~0.06 at every frequency. This is a distinct failure (overwrite,
frequency-independent) and should be reported separately from frequency-driven collapse.
