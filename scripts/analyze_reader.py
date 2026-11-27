"""Frequency DiD when a fixed external reader probes every writer's rolling memories.

Each writer's rolling memories (re-probed by the reader) are paired with the same reader's
full-context probes, so the reader is held fixed across conditions and writers; any remaining
frequency effect is due to what the writer kept, not to how the reader uses notes.

Usage: python scripts/analyze_reader.py READER_FULL_PROBES.jsonl results/reader/*_reads_*.jsonl
"""
from __future__ import annotations

import re
import sys
import warnings

import pandas as pd

from analyze_bench import did, load


def main() -> None:
    full_path, read_paths = sys.argv[1], sys.argv[2:]
    full = load([full_path])
    full = full[full.strategy == "full"]
    parts = []
    for p in read_paths:
        r = load([p])
        writer = re.search(r"rolling\[(?:.*/)?([^\]]+)\]", r.strategy.iloc[0]).group(1)
        label = f"{r.model.iloc[0]}<-{writer}"
        parts += [r.assign(strategy="rolling", model=label), full.assign(model=label)]
    did(pd.concat(parts, ignore_index=True))


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    main()
