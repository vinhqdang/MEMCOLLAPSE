"""Memory strategies compared at equal word budget.

Summary family (the model rewrites one free-text memory each session):
  rolling      generic rolling summary (runner.rolling_memories; baseline from the benchmark)
  rolling-imp  same, but told to preserve warnings/conditions/dissent (prompt-only fix)
  typed        typed-section compaction in the spirit of Knowledge Triage / TypeCompact
               (Zerhoudi et al., CIKM 2026); our re-implementation

Itemised family (the model only proposes deltas; code keeps items verbatim, see ledger.py):
  ace          untyped bullets, delta updates, recency pruning (ACE-style, Zhang et al. 2026)
  ledger-supp  typed + provenance, support-count eviction (ablation: frequency-driven policy)
  ledger-noprov typed, protected eviction, no provenance tags in the rendered memory (ablation)
  ledger       typed + provenance, protected eviction
  ledger-tier  typed, tiered eviction (decisions below warnings/conditions/dissent), no tags
"""
from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass

from .generator import Bank, Dialogue, render_session
from .ledger import PROTECTED_TYPES, Item, apply_delta, enforce_budget, parse_delta, render
from .llm import HFModel
from .prompts import EMPTY_MEMORY, UPDATE_SYSTEM, clip_words

log = logging.getLogger(__name__)
TOKENS_PER_WORD = 2.0
DELTA_MAX_TOKENS = 320

ROLLING_IMP_TEMPLATE = (
    "Project: {project}\n\n"
    "Current memory notes:\n{memory}\n\n"
    "Transcript of the new meeting:\n{session}\n\n"
    "Rewrite the memory notes so they incorporate the new meeting. "
    "Preserve every warning, condition, requirement and dissenting opinion, even if it was "
    "mentioned only once; drop routine progress and small talk first. "
    "The notes must be at most {budget} words. Output only the notes."
)

TYPED_TEMPLATE = (
    "Project: {project}\n\n"
    "Current memory notes:\n{memory}\n\n"
    "Transcript of the new meeting:\n{session}\n\n"
    "Rewrite the memory notes so they incorporate the new meeting, organised under these "
    "headings:\n"
    "CONSTRAINTS & WARNINGS: risks, requirements and preconditions (keep them verbatim, never drop)\n"
    "DISAGREEMENTS: who objected to what\n"
    "DECISIONS\n"
    "STATUS: latest progress only\n"
    "OTHER: minor details (compress or drop these first when space is short)\n"
    "The notes must be at most {budget} words. Output only the notes."
)

# Itemised extractors see only the new session (extract-then-consolidate, see ledger.py).
LEDGER_TEMPLATE = (
    "Project: {project}\n\n"
    "Transcript of meeting {t}:\n{session}\n\n"
    "List the claims from this meeting worth remembering, one per line, in the form\n"
    "TYPE | SPEAKER | claim in at most 15 words\n"
    "where TYPE is WARNING (a risk or problem), CONDITION (a requirement or precondition), "
    "DISSENT (an objection to the plan), DECISION, STATUS (progress figures) or OTHER.\n"
    "Keep names, numbers and places exact. Skip small talk. Output only these lines."
)

ACE_TEMPLATE = (
    "Project: {project}\n\n"
    "Transcript of meeting {t}:\n{session}\n\n"
    "List the information from this meeting worth remembering as notes, one per line, "
    "starting with '- ' and at most 15 words each.\n"
    "Keep names, numbers and places exact. Skip small talk. Output only the notes."
)


@dataclass(frozen=True)
class ItemisedConfig:
    typed: bool
    policy: str
    provenance: bool
    template: str


SUMMARY_TEMPLATES = {"rolling-imp": ROLLING_IMP_TEMPLATE, "typed": TYPED_TEMPLATE}
ITEMISED = {
    "ace": ItemisedConfig(typed=False, policy="recency", provenance=False, template=ACE_TEMPLATE),
    "ledger-supp": ItemisedConfig(True, "support", True, LEDGER_TEMPLATE),
    "ledger-noprov": ItemisedConfig(True, "protected", False, LEDGER_TEMPLATE),
    "ledger": ItemisedConfig(True, "protected", True, LEDGER_TEMPLATE),
    "ledger-tier": ItemisedConfig(True, "tiered", False, LEDGER_TEMPLATE),
}
STRATEGIES = tuple(SUMMARY_TEMPLATES) + tuple(ITEMISED)


def _messages(user: str) -> list[dict]:
    return [{"role": "system", "content": UPDATE_SYSTEM}, {"role": "user", "content": user}]


def summary_memories(model: HFModel, bank: Bank, dialogues: list[Dialogue], budget: int,
                     batch_size: int, template: str) -> list[list[tuple[str, int]]]:
    T = len(dialogues[0].sessions)
    if any(len(d.sessions) != T for d in dialogues):
        raise ValueError("all dialogues must have the same number of sessions")
    current = ["" for _ in dialogues]
    history: list[list[tuple[str, int]]] = [[] for _ in dialogues]
    for t in range(1, T + 1):
        msgs = [_messages(template.format(project=bank.project, memory=current[i] or EMPTY_MEMORY,
                                          session=render_session(d, t), budget=budget))
                for i, d in enumerate(dialogues)]
        outs = model.generate(msgs, max_new_tokens=int(budget * TOKENS_PER_WORD) + 32,
                              batch_size=batch_size)
        for i, o in enumerate(outs):
            clipped, raw = clip_words(o, budget)
            current[i] = clipped
            history[i].append((clipped, raw))
        log.info("summary budget=%d session %d/%d done", budget, t, T)
    return history


def itemised_memories(model: HFModel, bank: Bank, dialogues: list[Dialogue], budget: int,
                      batch_size: int, cfg: ItemisedConfig
                      ) -> tuple[list[list[tuple[str, int]]], dict[str, int]]:
    """Returns per-dialogue (rendered memory, pre-eviction words) and parse statistics."""
    T = len(dialogues[0].sessions)
    if any(len(d.sessions) != T for d in dialogues):
        raise ValueError("all dialogues must have the same number of sessions")
    ledgers: list[tuple[Item, ...]] = [() for _ in dialogues]
    history: list[list[tuple[str, int]]] = [[] for _ in dialogues]
    stats: dict = {"claims": 0, "lines_new": 0, "lines_merged": 0, "lines_bad": 0,
                   "truncated_outputs": 0, "evicted": 0, "evicted_protected": 0,
                   "empty_ledgers": 0, "kept_items_final": 0, "kept_types_final": {},
                   "bad_per_session": []}
    for t in range(1, T + 1):
        prompts = [cfg.template.format(project=bank.project, t=t, session=render_session(d, t))
                   for d in dialogues]
        outs = _extract(model, prompts, batch_size)
        bad_t = 0
        for i, o in enumerate(outs):
            if _hit_token_cap(model, o):  # last line may be cut mid-claim: drop it
                o = "\n".join(o.splitlines()[:-1])
                stats["truncated_outputs"] += 1
            new, bad = parse_delta(o, typed=cfg.typed)
            grown, merged = apply_delta(ledgers[i], new, session=t)
            kept = enforce_budget(grown, budget, cfg.policy, cfg.provenance)
            kept_ids = {id(it) for it in kept}
            gone = [it for it in grown if id(it) not in kept_ids]
            stats["claims"] += len(new)
            stats["lines_new"] += len(grown) - len(ledgers[i])
            stats["lines_merged"] += merged
            stats["lines_bad"] += bad
            stats["evicted"] += len(gone)
            stats["evicted_protected"] += sum(it.type in PROTECTED_TYPES for it in gone)
            stats["empty_ledgers"] += not kept
            bad_t += bad
            ledgers[i] = kept
            # second field: pre-eviction ledger size (NOT a budget-compliance measure here)
            history[i].append((render(kept, cfg.provenance),
                               len(render(grown, cfg.provenance).split())))
        stats["bad_per_session"].append(bad_t)
        log.info("itemised budget=%d session %d/%d done bad=%d empty=%d", budget, t, T, bad_t,
                 stats["empty_ledgers"])
    stats["kept_items_final"] = sum(len(led) for led in ledgers)
    stats["kept_types_final"] = dict(Counter(it.type for led in ledgers for it in led))
    return history, stats


def _extract(model: HFModel, prompts: list[str], batch_size: int) -> list[str]:
    """Greedy extraction, cached per model instance by prompt.

    The extractor never sees the memory, so its output for a session does not depend on budget
    or eviction policy: all itemised variants sharing a template reuse one generation, and the
    ablations are guaranteed to consolidate exactly the same extracted claims.
    """
    cache: dict[str, str] = model.__dict__.setdefault("_extract_cache", {})
    todo = list(dict.fromkeys(p for p in prompts if p not in cache))
    if todo:
        outs = model.generate([_messages(p) for p in todo], max_new_tokens=DELTA_MAX_TOKENS,
                              batch_size=batch_size)
        cache.update(zip(todo, outs))
    return [cache[p] for p in prompts]


def _hit_token_cap(model: HFModel, output: str) -> bool:
    tok = getattr(model, "tok", None)
    if tok is None:
        return False
    return len(tok.encode(output, add_special_tokens=False)) >= DELTA_MAX_TOKENS - 2


def run_strategy(name: str, model: HFModel, bank: Bank, dialogues: list[Dialogue], budget: int,
                 batch_size: int) -> tuple[list[list[tuple[str, int]]], dict[str, int]]:
    if name in SUMMARY_TEMPLATES:
        return summary_memories(model, bank, dialogues, budget, batch_size,
                                SUMMARY_TEMPLATES[name]), {}
    if name in ITEMISED:
        return itemised_memories(model, bank, dialogues, budget, batch_size, ITEMISED[name])
    raise ValueError(f"unknown strategy {name!r}; expected one of {STRATEGIES}")
