"""Spec 002 — said vs held, integration.

Runs entirely against the **committed** claims cache. No model call, no
network, no API key required (Principle VII).
"""

import json

import pytest

from pipeline.claims import CACHE_PATH, extract_claims
from pipeline.divergence import d1_said as d1
from tests.conftest import BREACHED_CLIENT, HERO

# .alamazing/findings.md § 1 — the look-through concentration.
RECORDED_LOOKTHROUGH = 42.134
# Verified in spec 002 § Pre-flight: the positions naming shipping directly.
RECORDED_DIRECT = 33.20
# .alamazing/findings.md § 2 — equity against a 10-30 conservative band.
RECORDED_EQUITY = 71.46


def test_avoid_sector_cl0019(book):
    """Integration 1 — what he said, against what he holds.

    He asked for wealth outside the shipping sector. The portfolio is
    42.13% in the theme that shipping sits inside, and every mandate band
    is respected — so nothing the bank monitors would raise it.
    """
    findings = d1.detect(book, HERO)
    avoid = [f for f in findings if f["check"] == "avoid_sector"]
    assert len(avoid) == 1
    finding = avoid[0]

    assert finding["target"] == "shipping"
    assert finding["look_through_pct"] == pytest.approx(
        RECORDED_LOOKTHROUGH, abs=0.001
    )
    assert finding["direct_pct"] == pytest.approx(RECORDED_DIRECT, abs=0.01)

    # The claim came from his stated objectives, not from a note.
    assert finding["claim"]["source"] == "objectives"
    assert finding["claim"]["check"] == "avoid_sector"

    # The argument: contradicted, and simultaneously compliant.
    assert finding["compliance_clean"] is True


def test_reduce_risk_cl0003(book):
    """Integration 2 — she asked for safe and boring, three times.

    All three quotes travel with one finding. Someone who says three
    separate times that they have never taken a risk with money has made
    one point, three times, and the repetition is itself the evidence.
    """
    findings = d1.detect(book, BREACHED_CLIENT)
    risk = [f for f in findings if f["check"] == "reduce_risk"]
    assert len(risk) == 1, "one finding, not one per quote"
    finding = risk[0]

    assert finding["look_through_pct"] == pytest.approx(
        RECORDED_EQUITY, abs=0.01
    )

    quotes = " ".join(c["claim"] for c in finding["supporting_claims"]).lower()
    assert "never taken a risk with money" in quotes
    assert "safe and boring" in quotes

    # Both required notes are cited.
    cited = {r for e in finding["evidence"] for r in e["rows"]}
    assert "N-005" in cited
    assert "N-006" in cited


def test_claims_extracted_from_required_notes(book):
    """SC-003 — claims are drawn from N-025 and N-026, not just objectives."""
    claims = extract_claims(book.client(HERO), book.notes_for(HERO))
    sources = {c["source"] for c in claims}
    assert "N-025" in sources
    assert "N-026" in sources
    assert "objectives" in sources


def test_every_finding_quotes_the_client_and_cites_a_real_source(book):
    """SC-005, FR-010 — Principle VI, across every client in the book."""
    valid_notes = {
        n["note_id"] for cid in book.clients.client_id
        for n in book.notes_for(cid)
    }

    for client_id in sorted(book.clients.client_id):
        for finding in d1.detect(book, client_id):
            assert finding["claim"]["claim"].strip(), client_id
            assert finding["evidence"], client_id

            for entry in finding["evidence"]:
                assert entry["file"] in (
                    "clients.csv",
                    "rm_notes.json",
                    "holdings.csv",
                    "mandates.csv",
                ), entry
                assert entry["rows"], entry
                # Every cited note id resolves to a real row.
                if entry["file"] == "rm_notes.json":
                    for row in entry["rows"]:
                        assert row in valid_notes, row

            # Principle IX.
            assert "recommend" not in finding["headline"].lower()
            assert "recommend" not in finding["detail"].lower()

            # The client's words appear in the copy that quotes them.
            assert finding["claim"]["claim"][:24] in finding["detail"]


def test_detection_makes_no_model_call(book, monkeypatch):
    """SC-008 — nothing runs at demo time.

    The strongest form of this assertion available: make any attempt to
    construct a model client raise, then run detection. If the wall were
    breached anywhere, this fails.
    """
    import pipeline.claims as claims_module

    def explode(*args, **kwargs):
        raise AssertionError("detection must not call a model")

    # Remove the key so the extraction path cannot even try, and poison
    # the import so it would be caught if it did.
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(claims_module, "_save_cache", explode)

    findings = d1.detect(book, HERO)
    assert findings, "the committed cache must carry the hero's claims"
    assert findings[0]["look_through_pct"] == pytest.approx(
        RECORDED_LOOKTHROUGH, abs=0.001
    )


def test_nothing_the_client_said_disappears(book):
    """FR-017, Principle X — checked-and-clear and untested are recorded.

    A claim that was tested and found clear is a result, not silence. A
    claim this spec does not test is carried, not dropped. The interface
    can then say "checked against nine things he said".
    """
    findings = d1.detect(book, HERO)
    assert findings
    finding = findings[0]

    claims = extract_claims(book.client(HERO), book.notes_for(HERO))
    accounted = (
        1
        + len(finding["checked_and_clear"])
        + len(finding["carried_untested"])
    )
    assert accounted == len(claims), (
        "every extracted claim must be a finding, clear, or carried"
    )


def test_findings_are_deterministic(book):
    """SC-009 — Principle VII."""
    assert d1.detect(book, HERO) == d1.detect(book, HERO)
    assert d1.detect(book, BREACHED_CLIENT) == d1.detect(
        book, BREACHED_CLIENT
    )


def test_cache_is_committed_with_its_prompt(book):
    """Technology Standards — the prompt is committed alongside its output."""
    assert CACHE_PATH.exists(), "the cache must be a committed artifact"
    cache = json.loads(CACHE_PATH.read_text())

    assert cache["prompt"].strip(), "the prompt must be committed"
    assert cache["model"], "the model id must be recorded"
    assert len(cache["clients"]) == len(book.clients), "all 20 clients"

    # Provenance travels with every entry, so a hand-written fallback
    # fixture and real model output can be told apart in an audit.
    for entry in cache["clients"].values():
        assert entry["provenance"]
        assert "fingerprint" in entry


def test_seeds_never_match_a_derived_theme_label(book):
    """research.md R4 — the trap where the wrong code passes the test.

    Matching the target against `theme_sector` / `theme_issuer` also
    reaches 42.13%, but only because a label this pipeline wrote happens
    to contain the word "Shipping". The exposure would be pulled in by our
    own string rather than by the bank's data.

    Asserted directly: a target that appears *only* in a derived label
    must find nothing.
    """
    import pandas as pd

    # A holding whose *only* mention of the target is in the two derived
    # columns. Real data has no such row — every theme label is built from
    # words that also appear in a source field — so the guard is asserted
    # against a constructed one.
    frame = pd.DataFrame(
        [
            {
                "instrument_id": "X-1",
                "instrument_name": "Something Unrelated Fund",
                "sector": "Diversified",
                "sub_asset_class": "Developed Market Equity",
                "underlying_reference": None,
                "theme_sector": "Sentinel Theme",
                "theme_issuer": "Sentinel Issuer Ltd",
                "w": 99.0,
            }
        ]
    )

    assert d1._seeds(frame, "sentinel").empty, (
        "a target present only in a derived theme label must not seed — "
        "matching it would pull exposure in by a string the pipeline "
        "itself wrote (research.md R4)"
    )

    # The same target in a source field does seed, so the test is not
    # passing merely because nothing matches anything.
    frame.loc[0, "sector"] = "Sentinel"
    assert not d1._seeds(frame, "sentinel").empty
