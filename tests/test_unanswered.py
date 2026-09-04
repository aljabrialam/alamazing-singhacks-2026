"""Spec 004 — D5, the question nobody answered.

Block 6: "D5 is roughly twenty lines. It is what converts the demo from
analytics to advisory. Do not cut it."
"""

from pipeline.divergence import d5_unanswered as d5
from tests.conftest import HERO


def _all_findings(book):
    return {
        f["unanswered_question"]["note_id"]: f
        for client_id in sorted(book.clients.client_id)
        for f in d5.detect(book, client_id)
    }


def test_unanswered_n026_and_n028(book):
    """Integration — both notes block 6 names, with their quotes.

    N-026 is the one the whole demo turns on: he asked what happens if the
    Strait reopens, and Priscilla's own note says "We have not modelled
    this." Spec 005 answers it.
    """
    found = _all_findings(book)

    assert "N-026" in found
    hero = found["N-026"]
    assert hero["client_id"] == HERO
    assert hero["unanswered_question"]["asked_on"] == "2026-08-12"
    assert "Strait reopens" in hero["unanswered_question"]["question"]
    assert "have not modelled" in " ".join(hero["markers"]["admitted"])
    assert "asked for a view" in hero["markers"]["asked"]

    assert "N-028" in found
    other = found["N-028"]
    assert "have not yet replied" in " ".join(other["markers"]["admitted"])

    # Both cite a real note id in rm_notes.json.
    valid = {
        n["note_id"]
        for cid in book.clients.client_id
        for n in book.notes_for(cid)
    }
    for finding in (hero, other):
        assert finding["evidence"][0]["file"] == "rm_notes.json"
        for row in finding["evidence"][0]["rows"]:
            assert row in valid
        # The manager's own words are quoted.
        assert finding["unanswered_question"]["question"] in (
            finding["evidence"][0]["note"]
        )


def test_answered_and_commentary_are_excluded(book):
    """Unit — two guards, both learned from the data. research.md R5.

    N-002 and N-006 both contain question markers and both were answered
    in the same note. Surfacing them would put "unanswered question" in
    front of Priscilla for two questions she demonstrably answered, which
    destroys her trust in the one that is real.

    N-025 contains the word "unresolved" — describing the Strait, not an
    open item. It belongs to the hero client, so a false positive there
    would land on the demo screen.
    """
    found = _all_findings(book)

    assert "N-002" not in found, "answered in the same note"
    assert "N-006" not in found, "answered in the same note"
    assert "N-025" not in found, "market commentary, not an open item"

    # An admission overrides the answer check: "Have not yet replied"
    # contains "replied" and would otherwise cancel itself.
    assert "N-028" in found


def test_the_matcher_is_selective(book):
    """Three open questions in twenty-eight notes, not twenty-eight."""
    found = _all_findings(book)
    total_notes = sum(
        len(book.notes_for(cid)) for cid in book.clients.client_id
    )
    assert total_notes == 28
    assert len(found) == 3, sorted(found)


def test_findings_are_deterministic(book):
    assert d5.detect(book, HERO) == d5.detect(book, HERO)
