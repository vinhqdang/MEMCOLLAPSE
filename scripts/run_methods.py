"""Compare memory strategies (baselines + provenance ledger) at equal word budget.

Uses the same dialogues and probe seeds as run_pilot.py, so the full-context / rolling probes
from results/bench can be joined for DiD and retention-vs-full analysis.

Example:
  python scripts/run_methods.py --model Qwen/Qwen2.5-1.5B-Instruct --bank data/claims_heron.json \
      --name heron --strategies rolling-imp typed ace ledger-supp ledger-noprov ledger
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from memcollapse.generator import build_dialogue, load_bank  # noqa: E402
from memcollapse.llm import HFModel  # noqa: E402
from memcollapse.methods import STRATEGIES, run_strategy  # noqa: E402
from memcollapse.naturalize import load_rendered  # noqa: E402
from memcollapse.runner import probe_all, save_memories, save_records  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--bank", required=True)
    ap.add_argument("--name", required=True, help="tag prefix for output files (e.g. domain)")
    ap.add_argument("--strategies", nargs="+", default=list(STRATEGIES), choices=STRATEGIES)
    ap.add_argument("--n", type=int, default=48)
    ap.add_argument("--sessions", type=int, default=16)
    ap.add_argument("--budgets", type=int, nargs="+", default=[80, 160])
    ap.add_argument("--batch-size", type=int, default=12)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--schedule", choices=["spread", "clustered"], default="spread")
    ap.add_argument("--rendered", default=None)
    ap.add_argument("--out", default=str(ROOT / "results" / "methods"))
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--dtype", choices=["bfloat16", "float16", "float32"], default="bfloat16")
    ap.add_argument("--4bit", dest="four_bit", action="store_true")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

    bank = load_bank(args.bank)
    dialogues = [build_dialogue(bank, i, n_sessions=args.sessions, seed=args.seed,
                                schedule=args.schedule) for i in range(args.n)]
    if args.rendered:
        dialogues = load_rendered(dialogues, Path(args.rendered))
    model = HFModel(args.model, dtype=getattr(torch, args.dtype), device=args.device,
                    load_in_4bit=args.four_bit)
    tag = f"{args.name}_{args.model.split('/')[-1]}" + ("-nf4" if args.four_bit else "")
    out = Path(args.out)
    for strat in args.strategies:
        probes_path = out / f"probes_{tag}_{strat}.jsonl"
        mem_path = out / f"memories_{tag}_{strat}.jsonl"
        for p in (probes_path, mem_path):
            p.unlink(missing_ok=True)
        all_stats = {}
        for b in args.budgets:
            mems, stats = run_strategy(strat, model, bank, dialogues, b, args.batch_size)
            save_memories(dialogues, mems, strat, b, args.model, mem_path)
            save_records(probe_all(model, bank, dialogues, mems, strat, b, args.batch_size),
                         probes_path)
            all_stats[b] = stats
            logging.info("%s budget %d done %s", strat, b, stats)
        (out / f"stats_{tag}_{strat}.json").write_text(json.dumps(all_stats, indent=2),
                                                       encoding="utf-8")


if __name__ == "__main__":
    main()
