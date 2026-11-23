"""Prompt builders for memory updates and claim probes (pure functions)."""
from __future__ import annotations

import random

from .generator import Claim

NOT_DISCUSSED = "This was not mentioned in the notes"
LETTERS = ("A", "B", "C", "D")

UPDATE_SYSTEM = (
    "You maintain the running memory notes of an assistant that attends a project's "
    "meetings. The assistant will later rely ONLY on these notes to answer questions "
    "about the project."
)

UPDATE_TEMPLATE = (
    "Project: {project}\n\n"
    "Current memory notes:\n{memory}\n\n"
    "Transcript of the new meeting:\n{session}\n\n"
    "Rewrite the memory notes so they incorporate the new meeting. "
    "The notes must be at most {budget} words. Output only the notes."
)

PROBE_SYSTEM = "You answer questions about a project using only the provided notes."

PROBE_TEMPLATE = (
    "Notes:\n{memory}\n\n"
    "Question: {question}\n{options}\n\n"
    "If the notes do not contain the answer, choose the option saying it was not mentioned. "
    "Answer with a single letter."
)

EMPTY_MEMORY = "(no notes yet)"


def update_messages(project: str, memory: str, session: str, budget: int) -> list[dict]:
    user = UPDATE_TEMPLATE.format(project=project, memory=memory or EMPTY_MEMORY,
                                  session=session, budget=budget)
    return [{"role": "system", "content": UPDATE_SYSTEM}, {"role": "user", "content": user}]


def probe_options(claim: Claim, seed: int) -> tuple[tuple[str, ...], int]:
    """Shuffled 4-way options and index of the correct one (deterministic in seed)."""
    opts = [claim.answer, *claim.distractors[:2], NOT_DISCUSSED]
    order = list(range(4))
    random.Random(seed).shuffle(order)
    shuffled = tuple(opts[i] for i in order)
    return shuffled, shuffled.index(claim.answer)


def probe_messages(memory: str, claim: Claim, seed: int) -> tuple[list[dict], int, int]:
    """Returns (messages, correct_idx, not_discussed_idx)."""
    opts, correct = probe_options(claim, seed)
    opt_text = "\n".join(f"{LETTERS[i]}) {o}" for i, o in enumerate(opts))
    user = PROBE_TEMPLATE.format(memory=memory or EMPTY_MEMORY,
                                 question=claim.question, options=opt_text)
    msgs = [{"role": "system", "content": PROBE_SYSTEM}, {"role": "user", "content": user}]
    return msgs, correct, opts.index(NOT_DISCUSSED)


def clip_words(text: str, budget: int) -> tuple[str, int]:
    """Hard-enforce the word budget. Returns (clipped_text, original_word_count)."""
    words = text.split()
    if len(words) <= budget:
        return text.strip(), len(words)
    # keep line structure up to the budget
    out, count = [], 0
    for line in text.strip().splitlines():
        lw = line.split()
        if count + len(lw) > budget:
            remaining = budget - count
            if remaining > 0:
                out.append(" ".join(lw[:remaining]))
            break
        out.append(line)
        count += len(lw)
    return "\n".join(out).strip(), len(words)
