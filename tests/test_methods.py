from pathlib import Path

import pytest

from memcollapse.generator import build_dialogue, load_bank
from memcollapse.methods import ITEMISED, run_strategy

BANK = Path(__file__).resolve().parents[1] / "data" / "claims_heron.json"


class FakeModel:
    """Emits one WARNING per session plus a restatement of item 1; records prompts."""

    name = "fake"

    def __init__(self) -> None:
        self.prompts: list[str] = []
        self.calls = 0

    def generate(self, batch, max_new_tokens, batch_size=16):
        self.calls += 1
        self.prompts += [m[-1]["content"] for m in batch]
        return [f"- WARNING | Ana | risk number {self.calls} must be tracked\nSAME | 1\nbad"
                for _ in batch]


@pytest.fixture(scope="module")
def setup():
    bank = load_bank(str(BANK))
    return bank, [build_dialogue(bank, i, n_sessions=10) for i in range(2)]


def test_ledger_memories_respect_budget_and_keep_provenance(setup):
    bank, dialogues = setup
    mems, stats = run_strategy("ledger", FakeModel(), bank, dialogues, budget=40, batch_size=2)
    assert len(mems) == 2 and all(len(h) == 10 for h in mems)
    assert all(len(m.split()) <= 40 for h in mems for m, _ in h)
    assert "[WARNING; Ana; s" in mems[0][-1][0]
    # 10 "bad" lines + one "SAME | 1" against the empty ledger, per dialogue
    assert stats["lines_bad"] == 22
    assert stats["lines_new"] == 20 and stats["evicted"] > 0


def test_prompt_shows_previous_ledger(setup):
    bank, dialogues = setup
    fake = FakeModel()
    run_strategy("ledger", fake, bank, dialogues[:1], budget=200, batch_size=1)
    assert "1. [WARNING; Ana; s1] risk number 1 must be tracked" in fake.prompts[1]


def test_untyped_ace_keeps_newest(setup):
    bank, dialogues = setup
    mems, _ = run_strategy("ace", FakeModel(), bank, dialogues[:1], budget=12, batch_size=1)
    # one item fits; it must be one refreshed in the last session (the newest note or the
    # note restated by "SAME | 1"), never an older one
    final = mems[0][-1][0]
    assert final.count(chr(10)) == 0 and len(final.split()) <= 12
    assert "risk number 10" in final or "risk number 2 " in final


def test_unknown_strategy_raises(setup):
    bank, dialogues = setup
    with pytest.raises(ValueError):
        run_strategy("nope", FakeModel(), bank, dialogues, 80, 2)


def test_all_itemised_configs_have_valid_policy():
    from memcollapse.ledger import POLICIES
    assert all(cfg.policy in POLICIES for cfg in ITEMISED.values())
