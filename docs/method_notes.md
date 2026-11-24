# Method comparison: design notes and known asymmetries (to report in the paper)

- Itemised strategies (ace, ledger*) select from a full-session delta (max 320 new tokens) and are
  not told the budget; code then evicts to the budget. Summary strategies get 2*B+32 tokens and are
  told the budget. Both satisfy the same hard word budget on the *stored memory*; the asymmetry is
  in the selection step and is inherent to delta-based memory (as in ACE).
- Provenance tags count against the budget, so `ledger` holds fewer items than `ledger-noprov`;
  report kept items per strategy (stats_*.json: kept_items_final).
- `protected` degenerates to recency if the model labels nearly everything as a protected type;
  report kept_types_final and evicted_protected.
- ACE baseline differs from ledger in prompt wording as well as policy (untyped, "only NEW notes").
- `rolling-imp` names the target classes (warnings, conditions, dissent) in its prompt: a deliberately
  strong prompt-only baseline. `typed` benefits from tail clipping (OTHER section last).
- Format compliance (lines_bad, bad_per_session, empty_ledgers, truncated_outputs) is logged per
  run; itemised failures surface as empty/poor memories, which the summary family cannot suffer.
- Same-session eviction ties are broken by a content hash, not by output order.
- For itemised strategies the memories file's raw_words is the pre-eviction ledger size, not a
  budget-compliance measure.
