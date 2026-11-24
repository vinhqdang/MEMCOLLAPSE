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
  ledger       typed + provenance, protected eviction (ours)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from .generator import Bank, Dialogue, render_session
from .ledger import Item, apply_delta, enforce_budget, parse_delta, render, render_numbered
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

LEDGER_TEMPLATE = (
    "Project: {project}\n\n"
    "Current memory ledger (numbered):\n{memory}\n\n"
    "Transcript of the new meeting (meeting {t}):\n{session}\n\n"
    "List the claims from the new meeting worth remembering, one per line, in the form\n"
    "TYPE | SPEAKER | claim in at most 15 words\n"
    "where TYPE is WARNING (a risk or problem), CONDITION (a requirement or precondition), "
    "DISSENT (an objection to the plan), DECISION, STATUS (progress figures) or OTHER.\n"
    "If a claim restates a ledger item, write only: SAME | <item number>\n"
    "Keep names, numbers and places exact. Skip small talk. Output only these lines."
)

ACE_TEMPLATE = (
    "Project: {project}\n\n"
    "Current notes (numbered):\n{memory}\n\n"
    "Transcript of the new meeting (meeting {t}):\n{session}\n\n"
    "Output only NEW notes to add for information not already in the notes, one per line, "
    "starting with '- ' and at most 15 words each. If the meeting restates note n, write only: "
    "SAME | n\nKeep names, numbers and places exact. Skip small talk."
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
}
STRATEGIES = tuple(SUMMARY_TEMPLATES) + tuple(ITEMISED)


def _messages(user: str) -> list[dict]:
    return [{"role": "system", "content": UPDATE_SYSTEM}, {"role": "user", "content": user}]


def summary_memories(model: HFModel, bank: Bank, dialogues: list[Dialogue], budget: int,
                     batch_size: int, template: str) -> list[list[tuple[str, int]]]:
    T = len(dialogues[0].sessions)
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
    ledgers: list[tuple[Item, ...]] = [() for _ in dialogues]
    history: list[list[tuple[str, int]]] = [[] for _ in dialogues]
    stats = {"lines_new": 0, "lines_same": 0, "lines_bad": 0, "evicted": 0}
    for t in range(1, T + 1):
        msgs = [_messages(cfg.template.format(
            project=bank.project, t=t, session=render_session(d, t),
            memory=render_numbered(ledgers[i], cfg.provenance) or EMPTY_MEMORY))
            for i, d in enumerate(dialogues)]
        outs = model.generate(msgs, max_new_tokens=DELTA_MAX_TOKENS, batch_size=batch_size)
        for i, o in enumerate(outs):
            new, same, bad = parse_delta(o, n_existing=len(ledgers[i]), typed=cfg.typed)
            grown = apply_delta(ledgers[i], new, same, session=t)
            kept = enforce_budget(grown, budget, cfg.policy, cfg.provenance)
            stats["lines_new"] += len(new)
            stats["lines_same"] += len(same)
            stats["lines_bad"] += bad
            stats["evicted"] += len(grown) - len(kept)
            ledgers[i] = kept
            history[i].append((render(kept, cfg.provenance),
                               len(render(grown, cfg.provenance).split())))
        log.info("itemised budget=%d session %d/%d done %s", budget, t, T, stats)
    return history, stats


def run_strategy(name: str, model: HFModel, bank: Bank, dialogues: list[Dialogue], budget: int,
                 batch_size: int) -> tuple[list[list[tuple[str, int]]], dict[str, int]]:
    if name in SUMMARY_TEMPLATES:
        return summary_memories(model, bank, dialogues, budget, batch_size,
                                SUMMARY_TEMPLATES[name]), {}
    if name in ITEMISED:
        return itemised_memories(model, bank, dialogues, budget, batch_size, ITEMISED[name])
    raise ValueError(f"unknown strategy {name!r}; expected one of {STRATEGIES}")
