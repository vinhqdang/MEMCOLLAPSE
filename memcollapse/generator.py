"""Controlled multi-session dialogue generator.

Key design: every claim's *content* is fixed; only its mention frequency is
manipulated (counterbalanced across dialogues), while the session of its LAST
mention is drawn independently of frequency. This isolates frequency-driven
erasure from recency.
"""
from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

FREQ_LEVELS = (1, 2, 4)
LAST_MENTION_CHOICES = (4, 5, 6, 7, 8)
MAJORITY_PER_SESSION = 2
FILLER_PER_SESSION = 3


@dataclass(frozen=True)
class Claim:
    id: str
    type: str
    importance: str
    mentions: tuple[str, ...]
    question: str
    answer: str
    distractors: tuple[str, ...]


@dataclass(frozen=True)
class Bank:
    domain: str
    project: str
    majority_thread: tuple[str, ...]
    filler: tuple[str, ...]
    speakers: tuple[str, ...]
    claims: tuple[Claim, ...]


@dataclass(frozen=True)
class Utterance:
    speaker: str
    text: str
    tag: str  # "claim:<id>", "majority", "filler", "progress"


@dataclass(frozen=True)
class ClaimMeta:
    claim_id: str
    importance: str
    type: str
    freq: int
    mention_sessions: tuple[int, ...]
    speaker: str

    @property
    def first(self) -> int:
        return self.mention_sessions[0]

    @property
    def last(self) -> int:
        return self.mention_sessions[-1]


@dataclass(frozen=True)
class Dialogue:
    dialogue_id: str
    sessions: tuple[tuple[Utterance, ...], ...]  # index 0 == session 1
    claims: tuple[ClaimMeta, ...] = field(default_factory=tuple)


def load_bank(path: str | Path) -> Bank:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    claims = tuple(
        Claim(
            id=c["id"], type=c["type"], importance=c["importance"],
            mentions=tuple(c["mentions"]), question=c["question"],
            answer=c["answer"], distractors=tuple(c["distractors"]),
        )
        for c in raw["claims"]
    )
    if any(len(c.mentions) < max(FREQ_LEVELS) for c in claims):
        raise ValueError("every claim needs >= max(FREQ_LEVELS) paraphrases")
    return Bank(
        domain=raw["domain"], project=raw["project"],
        majority_thread=tuple(raw["majority_thread"]), filler=tuple(raw["filler"]),
        speakers=tuple(raw["speakers"]), claims=claims,
    )


SCHEDULES = ("spread", "clustered")


def mention_schedule(freq: int, last: int, mode: str = "spread") -> tuple[int, ...]:
    """Sessions (1-based) in which a claim is mentioned; always ends at `last`.

    spread:    mentions evenly spaced over [1, last]
    clustered: mentions in consecutive sessions [last-freq+1, last]
    """
    if freq < 1 or last < freq:
        raise ValueError(f"invalid freq={freq} last={last}")
    if mode not in SCHEDULES:
        raise ValueError(f"unknown schedule mode {mode!r}")
    if freq == 1:
        return (last,)
    if mode == "clustered":
        return tuple(range(last - freq + 1, last + 1))
    pts = np.linspace(1, last, freq)
    sessions = tuple(sorted({int(round(p)) for p in pts}))
    if len(sessions) != freq or sessions[-1] != last:
        raise AssertionError("schedule construction failed")
    return sessions


def select_claims(bank: Bank, d_idx: int, per_importance: int) -> list[tuple[Claim, int]]:
    """Pick claims and counterbalanced frequencies for dialogue d_idx."""
    chosen: list[tuple[Claim, int]] = []
    for imp in ("critical", "incidental"):
        pool = [c for c in bank.claims if c.importance == imp]
        start = (d_idx * per_importance) % len(pool)
        picked = [pool[(start + k) % len(pool)] for k in range(per_importance)]
        for c in picked:
            c_idx = pool.index(c)
            freq = FREQ_LEVELS[(c_idx + d_idx) % len(FREQ_LEVELS)]
            chosen.append((c, freq))
    return chosen


def _progress_line(rng: random.Random, session: int) -> str:
    return (f"Sprint {session} update: we closed {rng.randint(8, 30)} tickets and the "
            f"integration test pass rate is {rng.randint(80, 99)}%.")


def build_dialogue(bank: Bank, d_idx: int, n_sessions: int = 16,
                   per_importance: int = 6, seed: int = 0,
                   schedule: str = "spread") -> Dialogue:
    rng = random.Random(seed * 100_003 + d_idx)
    metas: list[ClaimMeta] = []
    for claim, freq in select_claims(bank, d_idx, per_importance):
        last = rng.choice([L for L in LAST_MENTION_CHOICES if L >= freq and L <= n_sessions])
        metas.append(ClaimMeta(
            claim_id=claim.id, importance=claim.importance, type=claim.type,
            freq=freq, mention_sessions=mention_schedule(freq, last, schedule),
            speaker=rng.choice(bank.speakers),
        ))
    by_id = {c.id: c for c in bank.claims}
    sessions = []
    for s in range(1, n_sessions + 1):
        utts: list[Utterance] = []
        for m in metas:
            if s in m.mention_sessions:
                k = m.mention_sessions.index(s)
                utts.append(Utterance(m.speaker, by_id[m.claim_id].mentions[k], f"claim:{m.claim_id}"))
        for line in rng.sample(bank.majority_thread, MAJORITY_PER_SESSION):
            utts.append(Utterance(rng.choice(bank.speakers), line, "majority"))
        for line in rng.sample(bank.filler, FILLER_PER_SESSION):
            utts.append(Utterance(rng.choice(bank.speakers), line, "filler"))
        utts.append(Utterance(bank.speakers[0], _progress_line(rng, s), "progress"))
        rng.shuffle(utts)
        sessions.append(tuple(utts))
    return Dialogue(dialogue_id=f"{bank.domain}-{schedule}-{seed}-{d_idx:04d}",
                    sessions=tuple(sessions), claims=tuple(metas))


def render_session(dialogue: Dialogue, s: int) -> str:
    """Render 1-based session s as a transcript."""
    lines = [f"--- Meeting {s} ---"]
    lines += [f"{u.speaker}: {u.text}" for u in dialogue.sessions[s - 1]]
    return "\n".join(lines)


def render_transcript(dialogue: Dialogue, upto: int) -> str:
    return "\n\n".join(render_session(dialogue, s) for s in range(1, upto + 1))
