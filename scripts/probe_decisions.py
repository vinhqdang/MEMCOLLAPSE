"""Decision-impact probes: does losing a critical claim from memory change what the agent decides?

For every critical claim, data/decisions.json holds a decision question whose correct action
applies the claim; distractors[0] is the lure (proceed as if the claim had never been raised) and
distractors[1] applies a wrong detail. The same model reads saved memories (any strategy), the
full transcript and an empty memory, at checkpoints after the claim's last mention.

Example:
  python scripts/probe_decisions.py --model Qwen/Qwen2.5-1.5B-Instruct --domain heron \
      --memories results/pilot/memories_Qwen2.5-1.5B-Instruct.jsonl \
                 results/methods/memories_heron_Qwen2.5-1.5B-Instruct_ledger-tier.jsonl \
      --out results/decisions/heron_Qwen2.5-1.5B-Instruct.jsonl
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import logging
import math
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from memcollapse.generator import Bank, Dialogue, build_dialogue, load_bank, render_transcript  # noqa: E402
from memcollapse.llm import HFModel  # noqa: E402
from memcollapse.prompts import probe_messages  # noqa: E402

BANKS = {"heron": "claims_heron.json", "city": "claims_city.json",
         "science": "claims_science.json", "product": "claims_product.json"}
CHECKPOINTS = (4, 8, 12, 16)
CHOICES = ("correct", "lure", "wrong", "not_mentioned")


def decision_bank(bank: Bank, items: dict) -> Bank:
    """Same claims and mentions (so dialogues are identical), decision Q/A for critical claims."""
    missing = [c.id for c in bank.claims if c.importance == "critical" and c.id not in items]
    if missing:
        raise KeyError(f"no decision item for critical claims {missing}")
    claims = tuple(
        dataclasses.replace(c, question=items[c.id]["question"], answer=items[c.id]["answer"],
                            distractors=tuple(items[c.id]["distractors"]))
        if c.importance == "critical" else c
        for c in bank.claims)
    return dataclasses.replace(bank, claims=claims)


def build_jobs(bank: Bank, dialogues: list[Dialogue], memories: list[list[str]], tag: dict):
    by_id = {c.id: c for c in bank.claims}
    jobs, meta = [], []
    for d, hist in zip(dialogues, memories):
        for t in CHECKPOINTS:
            for cm in d.claims:
                if cm.importance != "critical" or t <= cm.last:
                    continue
                claim = by_id[cm.claim_id]
                seed = zlib.crc32(f"{d.dialogue_id}|{cm.claim_id}".encode())
                msgs, correct, nd = probe_messages(hist[t - 1], claim, seed)
                opts = [m for m in msgs[1]["content"].splitlines() if m[1:3] == ") "]
                lure = next(i for i, o in enumerate(opts) if o[3:] == claim.distractors[0])
                jobs.append(msgs)
                meta.append({**tag, "dialogue_id": d.dialogue_id, "t": t, "claim_id": cm.claim_id,
                             "type": cm.type, "freq": cm.freq, "first": cm.first, "last": cm.last,
                             "since_last": t - cm.last, "_idx": (correct, lure, nd)})
    return jobs, meta


def score(model: HFModel, jobs, meta, batch_size: int) -> list[dict]:
    out = []
    for m, lp in zip(meta, model.choice_logprobs(jobs, batch_size=batch_size)):
        correct, lure, nd = m.pop("_idx")
        pred = max(range(4), key=lambda k: lp[k])
        choice = {correct: "correct", lure: "lure", nd: "not_mentioned"}.get(pred, "wrong")
        out.append({**m, "choice": choice, "correct": choice == "correct",
                    "p_correct": math.exp(lp[correct]),
                    "p_lure": math.exp(lp[lure])})
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--domain", required=True, choices=sorted(BANKS))
    ap.add_argument("--memories", nargs="+", default=[])
    ap.add_argument("--4bit", dest="four_bit", action="store_true")
    ap.add_argument("--batch-size", type=int, default=12)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

    items = json.loads((ROOT / "data" / "decisions.json").read_text(encoding="utf-8"))[args.domain]
    bank = decision_bank(load_bank(ROOT / "data" / BANKS[args.domain]), items)
    n = 48
    dialogues = [build_dialogue(bank, i, n_sessions=16, seed=0, schedule="spread") for i in range(n)]
    model = HFModel(args.model, load_in_4bit=args.four_bit)
    name = args.model.split("/")[-1] + ("-nf4" if args.four_bit else "")

    groups = [({"strategy": "full", "budget": 0},
               [[render_transcript(d, t) for t in range(1, 17)] for d in dialogues], dialogues),
              ({"strategy": "empty", "budget": 0}, [[""] * 16 for _ in dialogues], dialogues)]
    for path in args.memories:
        recs = [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x]
        for b in sorted({r["budget"] for r in recs}):
            sub = [r for r in recs if r["budget"] == b]
            dl = [dialogues[int(r["dialogue_id"].rsplit("-", 1)[1])] for r in sub]
            groups.append(({"strategy": sub[0]["strategy"], "budget": b},
                           [r["memories"] for r in sub], dl))

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.unlink(missing_ok=True)
    for tag, mems, dl in groups:
        jobs, meta = build_jobs(bank, dl, mems, {"model": name, "domain": args.domain, **tag})
        recs = score(model, jobs, meta, args.batch_size)
        with out.open("a", encoding="utf-8") as f:
            f.writelines(json.dumps(r) + "\n" for r in recs)
        acc = sum(r["correct"] for r in recs) / max(len(recs), 1)
        lure = sum(r["choice"] == "lure" for r in recs) / max(len(recs), 1)
        logging.info("%s B=%s: n=%d acc=%.3f lure=%.3f", tag["strategy"], tag["budget"],
                     len(recs), acc, lure)


if __name__ == "__main__":
    main()
