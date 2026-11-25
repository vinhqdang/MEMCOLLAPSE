import json
from pathlib import Path

from memcollapse.ledger import (MERGE_THRESHOLD, PROTECTED_TYPES, Item, apply_delta,
                                enforce_budget, parse_delta, render, similarity)

DATA = Path(__file__).resolve().parents[1] / "data"


def _items():
    return (
        Item(text="vendor demo went well", type="decision", speaker="Ana", sessions=(1, 2, 3)),
        Item(text="lunch is Thai food", type="other", speaker="Bo", sessions=(1,)),
        Item(text="backup skips audit-log db", type="warning", speaker="Cy", sessions=(2,)),
        Item(text="sprint 3 closed 12 tickets", type="status", speaker="Di", sessions=(4,)),
    )


def test_parse_typed_lines_and_count_bad():
    out = "WARNING | Cy | backup skips audit-log db\ngarbage line\nOTHER|Bo|lunch is Thai"
    new, bad = parse_delta(out)
    assert [(i.type, i.speaker, i.text) for i in new] == [
        ("warning", "Cy", "backup skips audit-log db"), ("other", "Bo", "lunch is Thai")]
    assert bad == 1


def test_parse_tolerates_missing_speaker_extra_pipes_and_bold():
    new, bad = parse_delta("**WARNING** | Ana | rate | 3.5% error\nDISSENT | SLA too low")
    assert bad == 0
    assert (new[0].type, new[0].text) == ("warning", "rate | 3.5% error")
    assert (new[1].type, new[1].speaker, new[1].text) == ("dissent", "", "SLA too low")


def test_parse_rejects_unknown_type_same_lines_and_preambles():
    new, bad = parse_delta("RUMOUR | X | y\nSAME | 2\nHere are the claims:\nSAME | Jo | z")
    assert new == () and bad == 4


def test_untyped_accepts_plain_and_bulleted_notes_but_not_preambles():
    out = "Here are the notes:\n- keep the EU endpoint\nSprint 2: 18 tickets closed\nNotes:"
    new, bad = parse_delta(out, typed=False)
    assert [i.text for i in new] == ["keep the EU endpoint", "Sprint 2: 18 tickets closed"]
    assert bad == 2


def test_numbers_are_not_mistaken_for_bullets():
    new, _ = parse_delta("- 2.5 million budget overrun", typed=False)
    assert new[0].text == "2.5 million budget overrun"
    new, _ = parse_delta("1. WARNING | Ana | 3.5% error rate")
    assert new[0].text == "3.5% error rate"


def test_paraphrase_merges_into_existing_item_and_adds_provenance():
    led = _items()
    para = Item("The audit-log db is still skipped by the backup", "warning", "Ed", ())
    new_led, merged = apply_delta(led, (para,), session=5)
    assert merged == 1 and len(new_led) == len(led)
    assert new_led[2].sessions == (2, 5) and new_led[2].text == led[2].text
    assert led[2].sessions == (2,)  # original untouched


def test_different_numbers_never_merge():
    led = _items()
    upd = Item("sprint 4 closed 15 tickets", "status", "Di", ())
    new_led, merged = apply_delta(led, (upd,), session=5)
    assert merged == 0 and len(new_led) == 5 and new_led[-1].sessions == (5,)


def test_duplicates_within_one_output_collapse():
    a = Item("cutover needs the EU endpoint for SMS", "condition", "Jo", ())
    b = Item("SMS provider must use EU endpoint before cutover", "condition", "Jo", ())
    new_led, merged = apply_delta((), (a, b), session=1)
    assert len(new_led) == 1 and merged == 1 and new_led[0].sessions == (1,)


def test_threshold_separates_bank_paraphrases_from_other_claims():
    b = json.loads((DATA / "claims_heron.json").read_text(encoding="utf-8"))
    claims = b["claims"]
    same = [similarity(c["mentions"][0], m) >= MERGE_THRESHOLD
            for c in claims for m in c["mentions"][1:]]
    diff = [similarity(c["mentions"][0], d["mentions"][0]) >= MERGE_THRESHOLD
            for c in claims for d in claims if c["id"] < d["id"]]
    assert sum(same) / len(same) > 0.7
    assert sum(diff) <= 1


def test_render_includes_type_and_provenance():
    line = render((_items()[2],), provenance=True)
    assert line == "- [WARNING; Cy; s2] backup skips audit-log db"
    assert render((_items()[2],), provenance=False) == "- backup skips audit-log db"


def test_protected_policy_evicts_unprotected_first_even_if_frequent():
    kept = enforce_budget(_items(), budget=12, policy="protected", provenance=False)
    types = {i.type for i in kept}
    assert "warning" in types and "decision" in types
    assert all(i.type in PROTECTED_TYPES for i in kept)


def test_support_policy_evicts_rare_items_first():
    kept = enforce_budget(_items(), budget=6, policy="support", provenance=False)
    assert [i.text for i in kept] == ["vendor demo went well"]


def test_recency_policy_keeps_newest():
    kept = enforce_budget(_items(), budget=6, policy="recency", provenance=False)
    assert [i.text for i in kept] == ["sprint 3 closed 12 tickets"]


def test_enforce_budget_never_exceeds_budget():
    for policy in ("protected", "tiered", "support", "recency"):
        kept = enforce_budget(_items(), budget=9, policy=policy, provenance=True)
        assert len(render(kept, provenance=True).split()) <= 9


def test_eviction_tiebreak_ignores_output_order():
    items = tuple(Item(f"claim number {k} about topic", "warning", "A", (5,)) for k in range(6))
    for policy in ("protected", "tiered", "support", "recency"):
        a = enforce_budget(items, 20, policy, provenance=False)
        b = enforce_budget(items[::-1], 20, policy, provenance=False)
        assert {i.text for i in a} == {i.text for i in b}


def test_tiered_policy_evicts_decisions_before_warnings():
    items = (Item("backup skips audit-log db", "warning", "Cy", (1,)),
             Item("go live on 1 May", "decision", "Al", (5,)),
             Item("lunch is Thai food", "other", "Bo", (6,)))
    kept = enforce_budget(items, budget=6, policy="tiered", provenance=False)
    assert [i.type for i in kept] == ["warning"]
    kept = enforce_budget(items, budget=12, policy="tiered", provenance=False)
    assert [i.type for i in kept] == ["warning", "decision"]
