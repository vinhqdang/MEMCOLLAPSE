"""Run memory strategies over dialogues and probe every claim at every session."""
from __future__ import annotations

import json
import logging
import math
import zlib
from dataclasses import asdict, dataclass
from pathlib import Path

from .generator import Bank, Dialogue, render_session, render_transcript
from .llm import HFModel
from .prompts import clip_words, probe_messages, update_messages

log = logging.getLogger(__name__)
TOKENS_PER_WORD = 2.0


@dataclass(frozen=True)
class ProbeRecord:
    model: str
    strategy: str
    budget: int
    dialogue_id: str
    t: int
    claim_id: str
    importance: str
    type: str
    freq: int
    first: int
    last: int
    since_last: int
    correct: bool
    chose_not_mentioned: bool
    p_correct: float
    memory_words: int


def rolling_memories(model: HFModel, bank: Bank, dialogues: list[Dialogue],
                     budget: int, batch_size: int) -> list[list[tuple[str, int]]]:
    """For each dialogue, memory after each session t=1..T as (text, raw_word_count)."""
    T = len(dialogues[0].sessions)
    current = ["" for _ in dialogues]
    history: list[list[tuple[str, int]]] = [[] for _ in dialogues]
    for t in range(1, T + 1):
        msgs = [update_messages(bank.project, current[i], render_session(d, t), budget)
                for i, d in enumerate(dialogues)]
        outs = model.generate(msgs, max_new_tokens=int(budget * TOKENS_PER_WORD) + 32,
                              batch_size=batch_size)
        for i, o in enumerate(outs):
            clipped, raw = clip_words(o, budget)
            current[i] = clipped
            history[i].append((clipped, raw))
        log.info("rolling budget=%d session %d/%d done", budget, t, T)
    return history


def truncation_memories(dialogues: list[Dialogue], budget: int) -> list[list[tuple[str, int]]]:
    out = []
    for d in dialogues:
        hist = []
        for t in range(1, len(d.sessions) + 1):
            words = render_transcript(d, t).split()
            hist.append((" ".join(words[-budget:]), len(words)))
        out.append(hist)
    return out


def full_memories(dialogues: list[Dialogue]) -> list[list[tuple[str, int]]]:
    out = []
    for d in dialogues:
        hist = []
        for t in range(1, len(d.sessions) + 1):
            txt = render_transcript(d, t)
            hist.append((txt, len(txt.split())))
        out.append(hist)
    return out


def probe_all(model: HFModel, bank: Bank, dialogues: list[Dialogue],
              memories: list[list[tuple[str, int]]], strategy: str, budget: int,
              batch_size: int, checkpoints: set[int] | None = None) -> list[ProbeRecord]:
    by_id = {c.id: c for c in bank.claims}
    jobs, meta = [], []
    for di, d in enumerate(dialogues):
        for t, (mem, _raw) in enumerate(memories[di], start=1):
            if checkpoints is not None and t not in checkpoints:
                continue
            for cm in d.claims:
                if t < cm.first:
                    continue
                seed = zlib.crc32(f"{d.dialogue_id}|{cm.claim_id}".encode())
                msgs, correct, nd = probe_messages(mem, by_id[cm.claim_id], seed)
                jobs.append(msgs)
                meta.append((d, t, cm, correct, nd, len(mem.split())))
    logps = model.choice_logprobs(jobs, batch_size=batch_size)
    recs = []
    for (d, t, cm, correct, nd, mw), lp in zip(meta, logps):
        pred = max(range(4), key=lambda k: lp[k])
        recs.append(ProbeRecord(
            model=model.name, strategy=strategy, budget=budget, dialogue_id=d.dialogue_id,
            t=t, claim_id=cm.claim_id, importance=cm.importance, type=cm.type, freq=cm.freq,
            first=cm.first, last=cm.last, since_last=t - cm.last, correct=pred == correct,
            chose_not_mentioned=pred == nd, p_correct=math.exp(lp[correct]),
            memory_words=mw,
        ))
    return recs


def save_records(recs: list[ProbeRecord], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(asdict(r)) + "\n")


def save_memories(dialogues: list[Dialogue], memories: list[list[tuple[str, int]]],
                  strategy: str, budget: int, model: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        for d, hist in zip(dialogues, memories):
            f.write(json.dumps({"model": model, "strategy": strategy, "budget": budget,
                                "dialogue_id": d.dialogue_id,
                                "memories": [m for m, _ in hist],
                                "raw_words": [r for _, r in hist]}) + "\n")
