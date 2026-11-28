import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from probe_decisions import BANKS, build_jobs, decision_bank  # noqa: E402

from memcollapse.generator import build_dialogue, load_bank  # noqa: E402

ITEMS = json.loads((ROOT / "data" / "decisions.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("domain", sorted(BANKS))
def test_decision_bank_keeps_dialogues_identical(domain):
    base = load_bank(ROOT / "data" / BANKS[domain])
    dec = decision_bank(base, ITEMS[domain])
    for i in (0, 7, 47):
        assert build_dialogue(base, i).sessions == build_dialogue(dec, i).sessions


@pytest.mark.parametrize("domain", sorted(BANKS))
def test_decision_items_well_formed(domain):
    items = ITEMS[domain]
    for cid, it in items.items():
        opts = [it["answer"], *it["distractors"]]
        assert len(opts) == 3 and len(set(opts)) == 3, cid
        assert it["question"].endswith("?"), cid


def test_jobs_only_critical_post_last_with_lure_index():
    base = load_bank(ROOT / "data" / BANKS["heron"])
    bank = decision_bank(base, ITEMS["heron"])
    d = build_dialogue(bank, 0)
    jobs, meta = build_jobs(bank, [d], [["mem"] * 16], {"strategy": "x"})
    assert jobs and all(m["t"] > m["last"] for m in meta)
    assert all(m["claim_id"].startswith("c") for m in meta)
    assert all(len(set(m["_idx"])) == 3 for m in meta)
