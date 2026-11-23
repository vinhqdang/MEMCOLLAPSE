from dataclasses import replace
from pathlib import Path

from memcollapse.generator import build_dialogue, load_bank, render_session
from memcollapse.naturalize import (key_words, load_rendered, preserves_claims,
                                    save_rendered)

BANK = load_bank(Path(__file__).resolve().parents[1] / "data" / "claims_heron.json")


def test_key_words_drop_stopwords_keep_numbers():
    assert key_words("Before 30 June") == {"before", "30", "june"}


def test_preserves_claims_detects_lost_detail():
    assert preserves_claims("Priya: the limit is 300 requests per minute", ["300 requests per minute"])
    assert not preserves_claims("Priya: the limit is quite low", ["300 requests per minute"])
    assert preserves_claims("nothing relevant", [])


def test_rendered_overrides_template_rendering():
    d = build_dialogue(BANK, 0, n_sessions=4)
    d2 = replace(d, rendered=("one", "two", "three", "four"))
    assert render_session(d2, 2) == "--- Meeting 2 ---\ntwo"
    assert "Meeting 2" in render_session(d, 2) and "two" not in render_session(d, 2).split("\n")[1]


def test_save_and_load_rendered_roundtrip(tmp_path):
    ds = [build_dialogue(BANK, i) for i in range(2)]
    ds = [replace(d, rendered=tuple(f"s{s}-d{i}" for s in range(16))) for i, d in enumerate(ds)]
    p = tmp_path / "r.jsonl"
    save_rendered(ds, p)
    plain = [build_dialogue(BANK, i) for i in range(2)]
    loaded = load_rendered(plain, p)
    assert [d.rendered for d in loaded] == [d.rendered for d in ds]
