from memcollapse.ledger import (Item, apply_delta, enforce_budget, parse_delta, render,
                                PROTECTED_TYPES)


def _items():
    return (
        Item(text="vendor demo went well", type="decision", speaker="Ana", sessions=(1, 2, 3)),
        Item(text="lunch is Thai food", type="other", speaker="Bo", sessions=(1,)),
        Item(text="backup skips audit-log db", type="warning", speaker="Cy", sessions=(2,)),
        Item(text="sprint 3 closed 12 tickets", type="status", speaker="Di", sessions=(4,)),
    )


def test_parse_delta_reads_new_items_and_restatements():
    out = "WARNING | Cy | backup skips audit-log db\nSAME | 2\ngarbage line\nOTHER|Bo|lunch is Thai"
    new, same, bad = parse_delta(out, n_existing=3)
    assert [(i.type, i.speaker, i.text) for i in new] == [
        ("warning", "Cy", "backup skips audit-log db"), ("other", "Bo", "lunch is Thai")]
    assert same == (2,)
    assert bad == 1


def test_parse_delta_ignores_out_of_range_restatement_and_unknown_type():
    new, same, bad = parse_delta("SAME | 9\nSAME | 0\nRUMOUR | X | y", n_existing=3)
    assert new == () and same == () and bad == 3


def test_parse_delta_untyped_mode_accepts_plain_bullets():
    new, same, bad = parse_delta("- keep the EU endpoint\n- SAME | 1", n_existing=1, typed=False)
    assert [i.text for i in new] == ["keep the EU endpoint"] and same == (1,) and bad == 0


def test_apply_delta_adds_provenance_without_mutating():
    led = _items()
    new_led = apply_delta(led, (Item("new risk", "warning", "Ed", ()),), same=(3,), session=4)
    assert led[2].sessions == (2,)  # original untouched
    assert new_led[2].sessions == (2, 4)
    assert new_led[-1].sessions == (4,) and len(new_led) == 5


def test_apply_delta_drops_copied_items_without_adding_provenance():
    led = _items()
    new_led = apply_delta(led, (Item("Lunch is Thai food.", "other", "Bo", ()),), same=(), session=5)
    assert len(new_led) == len(led) and new_led[1].sessions == (1,)


def test_untyped_malformed_same_is_not_a_note():
    new, same, bad = parse_delta("Same | Priya\nSAME | Mei", n_existing=2, typed=False)
    assert new == () and same == () and bad == 2


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
    assert [i.text for i in kept] == ["vendor demo went well"]  # most-supported survives


def test_recency_policy_keeps_newest():
    kept = enforce_budget(_items(), budget=6, policy="recency", provenance=False)
    assert [i.text for i in kept] == ["sprint 3 closed 12 tickets"]


def test_enforce_budget_never_exceeds_budget():
    for policy in ("protected", "support", "recency"):
        kept = enforce_budget(_items(), budget=9, policy=policy, provenance=True)
        assert len(render(kept, provenance=True).split()) <= 9


def test_numbers_are_not_mistaken_for_bullets():
    new, _, _ = parse_delta("- 2.5 million budget overrun", 0, typed=False)
    assert new[0].text == "2.5 million budget overrun"
    new, _, _ = parse_delta("1. WARNING | Ana | 3.5% error rate", 0)
    assert new[0].text == "3.5% error rate"


def test_tolerant_same_variants():
    _, same, bad = parse_delta("SAME | 3.\nSAME | #2\nSAME | 1 | restated text", n_existing=3)
    assert same == (3, 2, 1) and bad == 0


def test_bold_type_is_accepted():
    new, _, bad = parse_delta("**WARNING** | Ana | audit log not backed up", 0)
    assert bad == 0 and new[0].type == "warning"


def test_ace_preamble_is_not_a_note_but_same_prefix_word_is():
    new, _, bad = parse_delta("Here are the new notes:\n- Same vendor as before", 0, typed=False)
    assert [i.text for i in new] == ["Same vendor as before"] and bad == 1


def test_eviction_tiebreak_ignores_output_order():
    items = tuple(Item(f"claim number {k} about topic", "warning", "A", (5,)) for k in range(6))
    for policy in ("protected", "support", "recency"):
        a = enforce_budget(items, 20, policy, provenance=False)
        b = enforce_budget(items[::-1], 20, policy, provenance=False)
        assert {i.text for i in a} == {i.text for i in b}
