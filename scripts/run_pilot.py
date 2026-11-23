"""Pilot: does iterative summarisation erase low-frequency claims faster?

Example:
  python scripts/run_pilot.py --model Qwen/Qwen2.5-1.5B-Instruct --n 24 --budgets 80 160
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from memcollapse.generator import build_dialogue, load_bank  # noqa: E402
from memcollapse.llm import HFModel  # noqa: E402
from memcollapse.naturalize import load_rendered  # noqa: E402
from memcollapse.runner import (full_memories, probe_all, rolling_memories,  # noqa: E402
                                save_memories, save_records, truncation_memories)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--bank", default=str(ROOT / "data" / "claims_heron.json"))
    ap.add_argument("--n", type=int, default=24)
    ap.add_argument("--sessions", type=int, default=16)
    ap.add_argument("--budgets", type=int, nargs="+", default=[80, 160])
    ap.add_argument("--batch-size", type=int, default=12)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=str(ROOT / "results" / "pilot"))
    ap.add_argument("--skip-full", action="store_true")
    ap.add_argument("--schedule", choices=["spread", "clustered"], default="spread")
    ap.add_argument("--rendered", default=None,
                    help="JSONL of naturalised sessions (from scripts/naturalize_dialogues.py)")
    ap.add_argument("--name", default=None, help="tag added to output filenames")
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    out = Path(args.out)
    tag = args.model.split("/")[-1] if not args.name else f"{args.name}_{args.model.split('/')[-1]}"
    bank = load_bank(args.bank)
    dialogues = [build_dialogue(bank, i, n_sessions=args.sessions, seed=args.seed,
                                schedule=args.schedule) for i in range(args.n)]
    if args.rendered:
        dialogues = load_rendered(dialogues, Path(args.rendered))
    model = HFModel(args.model)
    probes_path, mem_path = out / f"probes_{tag}.jsonl", out / f"memories_{tag}.jsonl"
    for p in (probes_path, mem_path):
        p.unlink(missing_ok=True)

    if not args.skip_full:
        mems = full_memories(dialogues)
        recs = probe_all(model, bank, dialogues, mems, "full", 0, max(1, args.batch_size // 4),
                         checkpoints={4, 8, 12, args.sessions})
        save_records(recs, probes_path)
        logging.info("full-context probes: %d", len(recs))

    for b in args.budgets:
        mems = truncation_memories(dialogues, b)
        save_records(probe_all(model, bank, dialogues, mems, "truncate", b, args.batch_size),
                     probes_path)
        mems = rolling_memories(model, bank, dialogues, b, args.batch_size)
        save_memories(dialogues, mems, "rolling", b, args.model, mem_path)
        save_records(probe_all(model, bank, dialogues, mems, "rolling", b, args.batch_size),
                     probes_path)
        logging.info("budget %d done", b)

    empty = [[("", 0)] * args.sessions for _ in dialogues]
    save_records(probe_all(model, bank, dialogues, empty, "empty", 0, args.batch_size,
                           checkpoints={args.sessions}), probes_path)


if __name__ == "__main__":
    main()
