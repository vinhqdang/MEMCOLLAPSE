"""Static quality checks for a claim bank JSON (no model needed)."""
from __future__ import annotations

import json
import re
from pathlib import Path

REQUIRED_TOP = ("domain", "project", "majority_thread", "filler", "speakers", "claims")
N_PER_IMPORTANCE = 12
N_MENTIONS = 4
CLAIM_TYPES = {"warning", "condition", "dissent", "incidental"}
STOP = {"the", "a", "an", "of", "to", "in", "on", "at", "for", "is", "it", "and", "or", "be",
        "by", "with", "that", "this", "must", "only", "not", "from", "too", "low", "high"}


def _content_words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", text.lower())
            if w not in STOP and (len(w) >= 2 or w.isdigit())}


def check_bank(path: str | Path) -> list[str]:
    """Return a list of problems; empty list means the bank passes."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    errs: list[str] = [f"missing key {k}" for k in REQUIRED_TOP if k not in raw]
    if errs:
        return errs
    if len(raw["majority_thread"]) < 6:
        errs.append("majority_thread needs >= 6 lines")
    if len(raw["filler"]) < 12:
        errs.append("filler needs >= 12 lines")
    if len(raw["speakers"]) < 6:
        errs.append("speakers needs >= 6 entries")
    claims = raw["claims"]
    ids = [c.get("id") for c in claims]
    if len(set(ids)) != len(ids):
        errs.append("duplicate claim ids")
    for imp in ("critical", "incidental"):
        n = sum(c.get("importance") == imp for c in claims)
        if n != N_PER_IMPORTANCE:
            errs.append(f"need {N_PER_IMPORTANCE} {imp} claims, got {n}")
    answers = [c.get("answer", "").lower() for c in claims]
    if len(set(answers)) != len(answers):
        errs.append("duplicate answers across claims")
    for c in claims:
        errs += _check_claim(c)
    return errs


def _check_claim(c: dict) -> list[str]:
    cid = c.get("id", "?")
    errs = []
    if c.get("type") not in CLAIM_TYPES:
        errs.append(f"{cid}: bad type {c.get('type')}")
    if (c.get("type") == "incidental") != (c.get("importance") == "incidental"):
        errs.append(f"{cid}: type/importance mismatch")
    ments = c.get("mentions", [])
    if len(ments) != N_MENTIONS or len(set(ments)) != N_MENTIONS:
        errs.append(f"{cid}: need {N_MENTIONS} distinct mentions")
    dis = c.get("distractors", [])
    opts = [c.get("answer", ""), *dis]
    if len(dis) != 2 or len({o.lower() for o in opts}) != 3:
        errs.append(f"{cid}: need 2 distractors distinct from answer")
    ans_words = _content_words(c.get("answer", ""))
    if ans_words and ans_words <= _content_words(c.get("question", "")):
        errs.append(f"{cid}: answer fully leaked by question")
    for k, m in enumerate(ments):
        if not ans_words & _content_words(m):
            errs.append(f"{cid}: mention {k} shares no content word with answer")
        for d in dis:
            dw = _content_words(d) - ans_words
            if dw and dw <= _content_words(m):
                errs.append(f"{cid}: mention {k} contains distractor '{d}'")
    return errs


if __name__ == "__main__":
    import sys
    bad = False
    for p in sys.argv[1:]:
        problems = check_bank(p)
        print(f"{p}: {'OK' if not problems else f'{len(problems)} problems'}")
        for e in problems:
            print("  -", e)
        bad |= bool(problems)
    sys.exit(1 if bad else 0)
