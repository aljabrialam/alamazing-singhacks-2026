"""Spec 008 — D7, explanation and attribution.

Building Block 1 of the brief. The assertion that matters is that money
paid in is never reported as performance.
"""

import pytest

from pipeline.load import latest, snapshots
from pipeline.divergence import d7_explain as d7
from tests.conftest import BREACHED_CLIENT, GOLDEN_HARBOUR_CLIENT, HERO, HERO_NOTE


def test_money_paid_in_is_never_performance(book):
    """Unit — the trap this detector exists to avoid.

    The hero's portfolio is +6.02m over the window. A single figure says
    the market gave him six million. It did not: 3.84m is a subscription
    he paid for. Getting this wrong flatters the bank, which is the class
    of error the brief warns about hardest.
    """
    finding = d7.detect(book, HERO)[0]

    acquired = {a["instrument_id"]: a for a in finding["acquired"]}
    assert HERO_NOTE in acquired, "the note was subscribed inside the window"

    note = acquired[HERO_NOTE]
    assert note["is_performance"] is False
    assert note["paid_in_usd"] == pytest.approx(3_841_229, abs=2_000)
    assert note["value_now_usd"] == pytest.approx(4_156_210, abs=1_000)
    # Its real market gain is the difference, not the whole position.
    assert note["market_movement_usd"] == pytest.approx(314_981, abs=2_000)

    # And it is not in the performance bucket.
    assert HERO_NOTE not in {h["instrument_id"] for h in finding["held"]}
    assert all(h["is_performance"] for h in finding["held"])


def test_explain_cl0019_separates_flows_from_market(book):
    """Integration — SC-004, SC-005.

    Reported as three buckets that reconcile to the total exactly, never
    as one number.
    """
    finding = d7.detect(book, HERO)[0]

    assert finding["total_change_usd"] == pytest.approx(6_018_820, abs=2_000)
    assert finding["paid_in_usd"] == pytest.approx(3_841_229, abs=2_000)
    assert finding["market_movement_usd"] == pytest.approx(
        1_862_610, abs=2_000
    )

    # The headline refuses to claim the change as performance.
    assert "money paid in, not performance" in finding["headline"]
    assert "not performance" in finding["detail"]

    # Causes come from the event log, by date.
    assert finding["events"]
    valid = set(book.events.event_date)
    for date in finding["events"]:
        assert date in valid


def test_the_three_buckets_reconcile_for_every_client(book):
    """The arithmetic must close, or the separation is decoration.

    held + paid in + market movement on acquired − taken out == total.
    """
    for client_id in sorted(book.clients.client_id):
        findings = d7.detect(book, client_id)
        if not findings:
            continue
        f = findings[0]
        reconciled = (
            f["market_movement_usd"]
            + f["paid_in_usd"]
            + f["acquired_market_movement_usd"]
            - f["taken_out_usd"]
        )
        assert reconciled == pytest.approx(
            f["total_change_usd"], abs=1.0
        ), client_id


def test_material_threshold_is_a_parameter(book):
    """Principle XI — a briefing that names every position is not a briefing."""
    wide = d7.detect(book, HERO, material_pct=0.0)[0]
    narrow = d7.detect(book, HERO, material_pct=5.0)[0]
    assert len(wide["held"]) > len(narrow["held"])


def test_dates_validated_and_order_independent(book):
    dates = snapshots(book)
    with pytest.raises(ValueError, match="not a snapshot"):
        d7.detect(book, HERO, date_then="1999-01-01")

    forward = d7.detect(book, HERO, dates[1], dates[-1])[0]
    backward = d7.detect(book, HERO, dates[-1], dates[1])[0]
    assert forward["total_change_usd"] == pytest.approx(
        backward["total_change_usd"], abs=0.01
    )


def test_every_finding_carries_evidence_and_no_forbidden_verb(book):
    for client_id in sorted(book.clients.client_id):
        for finding in d7.detect(book, client_id):
            assert finding["evidence"]
            for entry in finding["evidence"]:
                assert entry["file"] in (
                    "holdings.csv",
                    "transactions.csv",
                    "event_log.csv",
                )
                assert entry["rows"]
            assert "recommend" not in finding["headline"].lower()
            assert "recommend" not in finding["detail"].lower()


def test_findings_are_deterministic(book):
    for client_id in (HERO, BREACHED_CLIENT, GOLDEN_HARBOUR_CLIENT):
        assert d7.detect(book, client_id) == d7.detect(book, client_id)
