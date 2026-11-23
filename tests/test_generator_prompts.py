from collections import Counter
from pathlib import Path

import pytest

from memcollapse.generator import (FREQ_LEVELS, build_dialogue, load_bank, mention_schedule,
                                   render_transcript, select_claims)
from memcollapse.prompts import NOT_DISCUSSED, clip_words, probe_messages, probe_options

BANK = load_bank(Path(__file__).resolve().parents[1] / "data" / "claims_heron.json")


@pytest.mark.parametrize("freq,last", [(1, 4), (2, 4), (4, 4), (4, 8), (2, 7)])
def test_schedule_ends_at_last_and_has_freq_mentions(freq, last):
    s = mention_schedule(freq, last)
    assert len(s) == freq and s[-1] == last and list(s) == sorted(set(s))


def test_schedule_rejects_impossible():
    with pytest.raises(ValueError):
        mention_schedule(4, 3)


def test_frequency_is_counterbalanced_per_claim():
    counts = Counter()
    for d in range(36):
        for c, f in select_claims(BANK, d, 6):
            counts[(c.id, f)] += 1
    for c in BANK.claims:
        per = [counts[(c.id, f)] for f in FREQ_LEVELS]
        assert max(per) - min(per) <= 2, (c.id, per)


def test_dialogue_mentions_match_metadata():
    d = build_dialogue(BANK, 3, n_sessions=16, seed=1)
    for cm in d.claims:
        hits = [s for s in range(1, 17)
                if any(u.tag == f"claim:{cm.claim_id}" for u in d.sessions[s - 1])]
        assert tuple(hits) == cm.mention_sessions
    assert "Meeting 16" in render_transcript(d, 16)


def test_last_mention_independent_of_frequency_range():
    lasts = {f: set() for f in FREQ_LEVELS}
    for i in range(60):
        for cm in build_dialogue(BANK, i).claims:
            lasts[cm.freq].add(cm.last)
    assert lasts[1] == lasts[2] == lasts[4] == {4, 5, 6, 7, 8}


def test_probe_options_contain_answer_and_not_discussed():
    c = BANK.claims[0]
    opts, idx = probe_options(c, seed=5)
    assert opts[idx] == c.answer and NOT_DISCUSSED in opts and len(set(opts)) == 4
    assert probe_options(c, seed=5) == (opts, idx)


def test_probe_messages_include_memory():
    msgs, correct, nd = probe_messages("some notes", BANK.claims[0], 1)
    assert "some notes" in msgs[-1]["content"] and correct != nd


def test_clip_words():
    assert clip_words("a b c", 5) == ("a b c", 3)
    text, raw = clip_words("a b\nc d e\nf", 4)
    assert raw == 6 and len(text.split()) == 4 and text.startswith("a b\nc d")
