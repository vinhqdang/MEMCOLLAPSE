"""Itemised memory with provenance and budget-constrained eviction (pure functions).

Extract-then-consolidate: the LLM only lists the claims of the newest session (it never sees
the memory, so it cannot copy old items back); code consolidates them. A new claim that
paraphrases an existing item (content-word overlap >= MERGE_THRESHOLD and no conflicting
numbers) adds the session to that item's provenance; otherwise it is appended verbatim. Item text
is never rewritten afterwards, so details cannot erode through repeated paraphrase. (An earlier
design asked the model to write "SAME | n" for restatements; small models could not follow it.)
Eviction under the word budget is a deterministic policy:

- "protected": items typed WARNING/CONDITION/DISSENT/DECISION are evicted only after every
  other item is gone; within a tier the least recently mentioned goes first. Support count is
  deliberately NOT used, so a claim mentioned once is not disadvantaged (our method).
- "support":   lowest support (number of sessions mentioning it) first, then oldest
  (frequency-driven ablation: reproduces the bias of summarisers).
- "recency":   least recently mentioned first (ACE-style itemised context with FIFO pruning).
"""
from __future__ import annotations

import re
import zlib
from dataclasses import dataclass, replace

TYPES = ("warning", "condition", "dissent", "decision", "status", "other")
PROTECTED_TYPES = frozenset({"warning", "condition", "dissent", "decision"})
POLICIES = ("protected", "support", "recency")

MERGE_THRESHOLD = 0.4  # calibrated on bank paraphrases: 80-91% same-claim merges, ~0 false

_BULLET = re.compile(r"^\s*(?:[-*•]\s*|\d+[.)]\s+)")  # "2.5 million" is not a bullet
_SAME_LIKE = re.compile(r"^SAME\s*\|", re.IGNORECASE)  # legacy restatement syntax: never a claim
_PREAMBLE = re.compile(r"(:\s*$)|^(here (is|are)|new notes|notes\b|none\b|no new)", re.IGNORECASE)
_NUM = re.compile(r"\d+(?:[.,]\d+)?")
_STOP = frozenset(
    "the a an and or of to in on for is are was were be been it its this that we our i you they "
    "at by with from as not no but so if all still has have had just about will would can do does "
    "did than then there their what which who me my us also into".split())


@dataclass(frozen=True)
class Item:
    text: str
    type: str
    speaker: str
    sessions: tuple[int, ...]

    @property
    def last(self) -> int:
        return self.sessions[-1] if self.sessions else 0


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", text.lower()).strip()


def _parse_line(raw: str, typed: bool) -> Item | None:
    line = _BULLET.sub("", raw.replace("**", "")).strip()
    if not line or _SAME_LIKE.match(line) or _PREAMBLE.search(line):
        return None
    if not typed:
        return Item(text=line, type="other", speaker="", sessions=())
    parts = [p.strip() for p in line.split("|")]
    if len(parts) >= 3 and parts[0].lower() in TYPES:
        text = " | ".join(parts[2:]).strip()
        return Item(text, parts[0].lower(), parts[1], ()) if text else None
    if len(parts) == 2 and parts[0].lower() in TYPES and parts[1]:  # speaker omitted
        return Item(parts[1], parts[0].lower(), "", ())
    return None


def parse_delta(output: str, typed: bool = True) -> tuple[tuple[Item, ...], int]:
    """Parse model output into (claims, #non-empty lines that are not claims)."""
    new: list[Item] = []
    bad = 0
    for raw in output.splitlines():
        if not raw.strip():
            continue
        item = _parse_line(raw, typed)
        if item is None:
            bad += 1
        else:
            new.append(item)
    return tuple(new), bad


def _content(text: str) -> frozenset[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return frozenset(w for w in words if w.isdigit() or (len(w) > 2 and w not in _STOP))


def similarity(a: str, b: str) -> float:
    """Overlap coefficient of content words; 0 if both mention numbers and the numbers differ
    (so 'sprint 1: 24 tickets' never absorbs 'sprint 2: 18 tickets')."""
    na, nb = set(_NUM.findall(a)), set(_NUM.findall(b))
    if na and nb and na != nb:
        return 0.0
    ca, cb = _content(a), _content(b)
    return len(ca & cb) / max(1, min(len(ca), len(cb)))


def _match(ledger: list[Item], text: str) -> int | None:
    best, best_k = MERGE_THRESHOLD, None
    for k, it in enumerate(ledger):
        s = similarity(it.text, text)
        if s >= best:
            best, best_k = s, k
    return best_k


def apply_delta(ledger: tuple[Item, ...], new: tuple[Item, ...], session: int
                ) -> tuple[tuple[Item, ...], int]:
    """Return (new ledger, #claims merged into an existing item).

    A claim matching an existing item adds `session` to its provenance (text and type of the
    first statement are kept); otherwise it is appended with provenance (session,). Matching runs
    against the growing ledger, so duplicates within one output collapse into one item.
    """
    out = list(ledger)
    merged = 0
    for it in new:
        k = _match(out, it.text)
        if k is None:
            out.append(replace(it, sessions=(session,)))
            continue
        merged += 1
        if session not in out[k].sessions:
            out[k] = replace(out[k], sessions=(*out[k].sessions, session))
    return tuple(out), merged


def render_item(item: Item, provenance: bool) -> str:
    if not provenance:
        return f"- {item.text}"
    who = f"{item.speaker}; " if item.speaker else ""
    when = "s" + ",".join(str(s) for s in item.sessions)
    return f"- [{item.type.upper()}; {who}{when}] {item.text}"


def render(ledger: tuple[Item, ...], provenance: bool) -> str:
    return "\n".join(render_item(it, provenance) for it in ledger)


def _tiebreak(item: Item) -> int:
    """Content hash: items added in the same session are not ranked by output position."""
    return zlib.crc32(_norm(item.text).encode())


def _eviction_key(policy: str, k: int, item: Item) -> tuple:
    if policy == "protected":
        return (item.type in PROTECTED_TYPES, item.last, _tiebreak(item), k)
    if policy == "support":
        return (len(item.sessions), item.last, _tiebreak(item), k)
    if policy == "recency":
        return (item.last, _tiebreak(item), k)
    raise ValueError(f"unknown policy {policy!r}; expected one of {POLICIES}")


def enforce_budget(ledger: tuple[Item, ...], budget: int, policy: str,
                   provenance: bool) -> tuple[Item, ...]:
    """Evict items (in policy order) until the rendered ledger fits in `budget` words."""
    sizes = [len(render_item(it, provenance).split()) for it in ledger]
    total = sum(sizes)
    order = sorted(range(len(ledger)), key=lambda k: _eviction_key(policy, k, ledger[k]))
    dropped: set[int] = set()
    for k in order:
        if total <= budget:
            break
        dropped.add(k)
        total -= sizes[k]
    return tuple(it for k, it in enumerate(ledger) if k not in dropped)
