"""Itemised memory with provenance and budget-constrained eviction (pure functions).

The LLM only proposes deltas (new items / restatements of existing items); item text is never
rewritten afterwards, so details cannot erode through repeated paraphrase. Eviction under the
word budget is a deterministic policy:

- "protected": items typed WARNING/CONDITION/DISSENT/DECISION are evicted only after every
  other item is gone; within a tier the least recently mentioned goes first. Support count is
  deliberately NOT used, so a claim mentioned once is not disadvantaged (our method).
- "support":   lowest support (number of sessions mentioning it) first, then oldest
  (frequency-driven ablation: reproduces the bias of summarisers).
- "recency":   least recently mentioned first (ACE-style itemised context with FIFO pruning).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, replace

TYPES = ("warning", "condition", "dissent", "decision", "status", "other")
PROTECTED_TYPES = frozenset({"warning", "condition", "dissent", "decision"})
POLICIES = ("protected", "support", "recency")

_BULLET = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s*")
_SAME = re.compile(r"^SAME\s*\|\s*(\d+)\s*$", re.IGNORECASE)


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


def parse_delta(output: str, n_existing: int, typed: bool = True
                ) -> tuple[tuple[Item, ...], tuple[int, ...], int]:
    """Parse model output into (new items, 1-based restated indices, #unparsable lines)."""
    new: list[Item] = []
    same: list[int] = []
    bad = 0
    for raw in output.splitlines():
        line = _BULLET.sub("", raw).strip()
        if not line:
            continue
        m = _SAME.match(line)
        if m:
            k = int(m.group(1))
            if 1 <= k <= n_existing:
                same.append(k)
            else:
                bad += 1
            continue
        if line.upper().startswith("SAME"):  # malformed restatement, never a note
            bad += 1
            continue
        if not typed:
            new.append(Item(text=line, type="other", speaker="", sessions=()))
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) != 3 or parts[0].lower() not in TYPES or not parts[2]:
            bad += 1
            continue
        new.append(Item(text=parts[2], type=parts[0].lower(), speaker=parts[1], sessions=()))
    return tuple(new), tuple(dict.fromkeys(same)), bad


def _touch(item: Item, session: int) -> Item:
    if session in item.sessions:
        return item
    return replace(item, sessions=(*item.sessions, session))


def apply_delta(ledger: tuple[Item, ...], new: tuple[Item, ...], same: tuple[int, ...],
                session: int) -> tuple[Item, ...]:
    """Return a new ledger: restated items gain provenance, new items are appended.

    Only explicit SAME restatements add provenance. A new line whose text duplicates an existing
    item is dropped without touching provenance: models often copy the ledger back verbatim,
    which would otherwise inflate support counts with sessions that never mentioned the claim.
    """
    out = [(_touch(it, session) if (k + 1) in same else it) for k, it in enumerate(ledger)]
    seen = {_norm(it.text) for it in out}
    for it in new:
        key = _norm(it.text)
        if key in seen:
            continue
        seen.add(key)
        out.append(replace(it, sessions=(session,)))
    return tuple(out)


def render_item(item: Item, provenance: bool) -> str:
    if not provenance:
        return f"- {item.text}"
    who = f"{item.speaker}; " if item.speaker else ""
    when = "s" + ",".join(str(s) for s in item.sessions)
    return f"- [{item.type.upper()}; {who}{when}] {item.text}"


def render(ledger: tuple[Item, ...], provenance: bool) -> str:
    return "\n".join(render_item(it, provenance) for it in ledger)


def render_numbered(ledger: tuple[Item, ...], provenance: bool) -> str:
    return "\n".join(f"{k}. {render_item(it, provenance)[2:]}" for k, it in enumerate(ledger, 1))


def _eviction_key(policy: str, k: int, item: Item) -> tuple:
    if policy == "protected":
        return (item.type in PROTECTED_TYPES, item.last, k)
    if policy == "support":
        return (len(item.sessions), item.last, k)
    if policy == "recency":
        return (item.last, k)
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
