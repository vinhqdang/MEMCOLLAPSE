from pathlib import Path

import pytest

from memcollapse.generator import build_dialogue, load_bank
from memcollapse.methods import ITEMISED, run_strategy

BANK = Path(__file__).resolve().parents[1] / "data" / "claims_heron.json"


class FakeModel:
    """Each session: one new WARNING (distinct number) and a restatement of the first one."""

    name = "fake"

    def __init__(self) -> None:
        self.prompts: list[str] = []
        self.calls = 0

    def generate(self, batch, max_new_tokens, batch_size=16):
        self.calls += 1
        self.prompts += [m[-1]["content"] for m in batch]
        return [f"- WARNING | Ana | risk number {self.calls} must be tracked\n"
                f"- WARNING | Ana | tracking of risk number 1 is a must\nbad" for _ in batch]


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
    # per dialogue and session: 1 bad line; session 1 the restatement collapses into the new
    # item, later it merges into item 1 -> 10 new items, 10 merges per dialogue
    assert stats["lines_bad"] == 20
    assert stats["lines_new"] == 20 and stats["lines_merged"] == 20
    assert stats["evicted"] > 0


def test_restated_item_accumulates_provenance(setup):
    bank, dialogues = setup
    mems, _ = run_strategy("ledger", FakeModel(), bank, dialogues[:1], budget=500, batch_size=1)
    assert "[WARNING; Ana; s1,2,3,4,5,6,7,8,9,10] risk number 1 must" in mems[0][-1][0]


def test_extractor_never_sees_memory(setup):
    bank, dialogues = setup
    fake = FakeModel()
    run_strategy("ledger", fake, bank, dialogues[:1], budget=200, batch_size=1)
    assert all("risk number" not in p for p in fake.prompts)


def test_untyped_ace_keeps_most_recent(setup):
    bank, dialogues = setup
    mems, _ = run_strategy("ace", FakeModel(), bank, dialogues[:1], budget=12, batch_size=1)
    # one note fits; it must be one mentioned in the last session (the newest, or the restated
    # note 1), never an older one
    final = mems[0][-1][0]
    assert final.count(chr(10)) == 0 and len(final.split()) <= 12
    assert "risk number 10" in final or "risk number 1 " in final


def test_unknown_strategy_raises(setup):
    bank, dialogues = setup
    with pytest.raises(ValueError):
        run_strategy("nope", FakeModel(), bank, dialogues, 80, 2)


def test_all_itemised_configs_have_valid_policy():
    from memcollapse.ledger import POLICIES
    assert all(cfg.policy in POLICIES for cfg in ITEMISED.values())
