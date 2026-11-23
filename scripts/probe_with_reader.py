"""Re-probe saved memories with a fixed external reader model.

Separates 'the summariser dropped the claim' from 'the reader failed to use the memory'.

Example:
  python scripts/probe_with_reader.py --reader Qwen/Qwen2.5-7B-Instruct \
      --memories results/pilot/memories_Phi-3.5-mini-instruct.jsonl \
      --bank data/claims_heron.json --out results/reader/probes_reader-q7b_on_phi.jsonl
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from memcollapse.generator import build_dialogue, load_bank  # noqa: E402
from memcollapse.llm import HFModel  # noqa: E402
from memcollapse.runner import probe_all, save_records  # noqa: E402


def load_memories(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reader", required=True)
    ap.add_argument("--memories", required=True)
    ap.add_argument("--bank", required=True)
    ap.add_argument("--sessions", type=int, default=16)
    ap.add_argument("--schedule", choices=["spread", "clustered"], default="spread")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--batch-size", type=int, default=12)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

    bank = load_bank(args.bank)
    recs = load_memories(Path(args.memories))
    n = 1 + max(int(r["dialogue_id"].rsplit("-", 1)[1]) for r in recs)
    by_id = {d.dialogue_id: d for d in (build_dialogue(bank, i, n_sessions=args.sessions,
                                                        seed=args.seed, schedule=args.schedule)
                                         for i in range(n))}
    reader = HFModel(args.reader)
    out = Path(args.out)
    out.unlink(missing_ok=True)
    for budget in sorted({r["budget"] for r in recs}):
        group = [r for r in recs if r["budget"] == budget]
        missing = [r["dialogue_id"] for r in group if r["dialogue_id"] not in by_id]
        if missing:
            raise KeyError(f"dialogue ids not reproducible (check --schedule/--seed): {missing[0]}")
        dialogues = [by_id[r["dialogue_id"]] for r in group]
        mems = [[(m, 0) for m in r["memories"]] for r in group]
        probes = probe_all(reader, bank, dialogues, mems, f"rolling[{group[0]['model']}]",
                           budget, args.batch_size)
        save_records(probes, out)
        logging.info("budget %d: %d probes", budget, len(probes))


if __name__ == "__main__":
    main()
