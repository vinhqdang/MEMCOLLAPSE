"""Rewrite templated dialogues into naturalistic transcripts (fact-checked) and save them.

Example:
  python scripts/naturalize_dialogues.py --model Qwen/Qwen2.5-7B-Instruct \
      --bank data/claims_city.json --n 48 --out data/rendered/city_spread.jsonl
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
from memcollapse.naturalize import naturalize, save_rendered  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--bank", required=True)
    ap.add_argument("--n", type=int, default=48)
    ap.add_argument("--sessions", type=int, default=16)
    ap.add_argument("--schedule", choices=["spread", "clustered"], default="spread")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

    bank = load_bank(args.bank)
    dialogues = [build_dialogue(bank, i, n_sessions=args.sessions, seed=args.seed,
                                schedule=args.schedule) for i in range(args.n)]
    model = HFModel(args.model)
    rendered, stats = naturalize(model, bank, dialogues, args.batch_size)
    out = Path(args.out)
    save_rendered(rendered, out)
    stats.update(model=args.model, bank=args.bank, schedule=args.schedule)
    out.with_suffix(".stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
    logging.info("naturalised %s: %s", out, stats)


if __name__ == "__main__":
    main()
