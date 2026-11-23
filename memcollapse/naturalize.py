"""LLM rewriting of templated sessions into naturalistic dialogue, with fact-preservation checks.

A rewritten session is accepted only if, for every claim mentioned in that session, all
content words of the claim's answer still appear in the rewrite. Otherwise the templated
session is kept (and the fallback is recorded), so claim content is never silently lost.
"""
from __future__ import annotations

import json
import re
from dataclasses import replace
from pathlib import Path

from .generator import Bank, Dialogue, render_session
from .llm import HFModel

NATURALIZE_SYSTEM = "You rewrite meeting transcripts so they read like real, unscripted conversations."
NATURALIZE_TEMPLATE = (
    "Rewrite the meeting transcript below as a natural conversation between the same speakers. "
    "You may add short reactions, interruptions and back-and-forth, and reorder turns, but you must "
    "keep EVERY fact, number, name, date, condition and objection exactly as stated, keep who said "
    "it, and must not add any new facts. Use the format 'Name (role): text', one turn per line. "
    "Output only the transcript.\n\n{session}"
)
NUM_WORD = re.compile(r"[a-z0-9]+")


def key_words(answer: str) -> set[str]:
    stop = {"the", "a", "an", "of", "to", "in", "on", "at", "it", "is", "be", "and", "or", "by",
            "with", "must", "only", "not", "so", "that", "from", "too"}
    return {w for w in NUM_WORD.findall(answer.lower()) if w not in stop}


def preserves_claims(rewrite: str, answers: list[str]) -> bool:
    words = set(NUM_WORD.findall(rewrite.lower()))
    return all(key_words(a) <= words for a in answers)


def _session_answers(bank: Bank, d: Dialogue, s: int) -> list[str]:
    by_id = {c.id: c for c in bank.claims}
    return [by_id[m.claim_id].answer for m in d.claims if s in m.mention_sessions]


def naturalize(model: HFModel, bank: Bank, dialogues: list[Dialogue], batch_size: int,
               max_new_tokens: int = 700) -> tuple[list[Dialogue], dict]:
    jobs = [(di, s) for di, d in enumerate(dialogues) for s in range(1, len(d.sessions) + 1)]
    msgs = []
    for di, s in jobs:
        body = render_session(dialogues[di], s).split("\n", 1)[1]
        msgs.append([{"role": "system", "content": NATURALIZE_SYSTEM},
                     {"role": "user", "content": NATURALIZE_TEMPLATE.format(session=body)}])
    outs = model.generate(msgs, max_new_tokens=max_new_tokens, batch_size=batch_size)
    rendered = [[None] * len(d.sessions) for d in dialogues]
    stats = {"sessions": len(jobs), "fallback": 0}
    for (di, s), out in zip(jobs, outs):
        d = dialogues[di]
        if preserves_claims(out, _session_answers(bank, d, s)) and out.strip():
            rendered[di][s - 1] = out.strip()
        else:
            stats["fallback"] += 1
            rendered[di][s - 1] = render_session(d, s).split("\n", 1)[1]
    return [replace(d, rendered=tuple(r)) for d, r in zip(dialogues, rendered)], stats


def save_rendered(dialogues: list[Dialogue], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for d in dialogues:
            f.write(json.dumps({"dialogue_id": d.dialogue_id, "rendered": list(d.rendered)}) + "\n")


def load_rendered(dialogues: list[Dialogue], path: Path) -> list[Dialogue]:
    table = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        rec = json.loads(line)
        table[rec["dialogue_id"]] = tuple(rec["rendered"])
    missing = [d.dialogue_id for d in dialogues if d.dialogue_id not in table]
    if missing:
        raise KeyError(f"{len(missing)} dialogues missing from {path}, e.g. {missing[0]}")
    return [replace(d, rendered=table[d.dialogue_id]) for d in dialogues]
