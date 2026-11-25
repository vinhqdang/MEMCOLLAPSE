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
