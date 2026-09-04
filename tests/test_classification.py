"""Spec 003 — mandate breaches and their classification.

Carries two assertions Article VIII names by name:
`test_mandate_cl0003_inherited` and `test_mandate_cl0019_clean`.
"""

import pytest

from pipeline.load import latest
from pipeline.divergence import d2_mandate as d2
from pipeline.mandate import ABOVE, BELOW, WITHIN
from tests.conftest import (
    BREACHED_CLIENT,
    GOLDEN_HARBOUR_CLIENT,
    HERO,
    NO_COST_BASIS_INSTRUMENT,
)

# .alamazing/findings.md § 2 Margarethe Voss-Brenner — The breach.
RECORDED_EQUITY = 71.46
RECORDED_FIXED_INCOME = 9.15
RECORDED_LARGEST = 26.06
# .alamazing/findings.md § 3 Lau Chi Ming — Mandate.
RECORDED_CL0014_EQUITY = 23.39


def _by_class(findings):
    return {f["asset_class"]: f for f in findings if "asset_class" in f}


# --- integration assertions ----------------------------------------------


def test_mandate_cl0003_inherited(book):
    """Integration 1 — the third classification. Named in Article VIII.

    71.46% equity on a Conservative mandate, and she has never traded.
    Neither drift nor client-directed: transferred in as it stood when her
    husband died. Nobody chose this allocation for her.
    """
    findings = d2.detect(book, BREACHED_CLIENT)
    by_class = _by_class(findings)

    equity = by_class["Equity"]
    assert equity["actual_pct"] == pytest.approx(RECORDED_EQUITY, abs=0.01)
    assert equity["min_pct"] == pytest.approx(10, abs=0.01)
    assert equity["max_pct"] == pytest.approx(30, abs=0.01)
    assert equity["verdict"] == ABOVE
    assert equity["classification"] == d2.INHERITED

    fixed = by_class["Fixed Income"]
    assert fixed["actual_pct"] == pytest.approx(
        RECORDED_FIXED_INCOME, abs=0.01
    )
    assert fixed["min_pct"] == pytest.approx(45, abs=0.01)
    assert fixed["max_pct"] == pytest.approx(75, abs=0.01)
    assert fixed["verdict"] == BELOW
    assert fixed["classification"] == d2.INHERITED

    # The classification is earned from inception plus transactions, and
    # never from the portfolio's name — which happens to say "Inherited".
    evidence = equity["classification_evidence"]
    assert evidence["inception_in_reporting_year"] is True
    assert evidence["directing_transactions"] == []
    assert evidence["transactions_examined"], "transactions must be examined"

    verdict_positions = equity["breached_positions"]
    assert equity["compliance_clean"] is False

    # findings.md § 2 records her largest position at 26.06% — Global
    # Luxury and Consumer Brands Fund. It is a *diversified fund*, so it
    # is over the mandate's 10% limit but exempt from it, and reported as
    # such rather than as a breach. research.md R6.
    exempt = {p["instrument_id"] for p in equity["over_limit_but_exempt"]}
    assert exempt, "her largest positions are funds the limit exempts"
    exempt_pcts = [
        p["actual_pct"] for p in equity["over_limit_but_exempt"]
    ]
    assert max(exempt_pcts) == pytest.approx(RECORDED_LARGEST, abs=0.01)

    # Her real concentration breach is the holding with no cost basis —
    # so the position that breaches the limit is the one nobody can price
    # for tax. research.md R6.
    breached_ids = {p["instrument_id"] for p in verdict_positions}
    assert NO_COST_BASIS_INSTRUMENT in breached_ids
    assert NO_COST_BASIS_INSTRUMENT in equity["unsure_about"]


def test_mandate_cl0019_clean(book):
    """Integration 2 — not a null. Named in Article VIII.

    Block 5: "The CL-0019 result is not a null. The detector must be able
    to express 'checked, nothing breached' as a positive statement."
    """
    findings = d2.detect(book, HERO)
    assert len(findings) == 1
    clear = findings[0]

    assert clear["verdict"] == WITHIN
    assert clear["classification"] is None
    assert clear["compliance_clean"] is True

    # Every band named, so "nothing breached" is auditable.
    checked = {c["asset_class"]: c for c in clear["bands_checked"]}
    expected = {
        "Equity": (57.97, 40, 65),
        "Fixed Income": (15.67, 15, 40),
        "Structured Products": (12.90, 0, 15),
        "Cash and Equivalents": (7.45, 2, 15),
        "Alternatives": (6.00, 0, 25),
    }
    assert set(checked) == set(expected)
    for asset_class, (actual, low, high) in expected.items():
        band = checked[asset_class]
        assert band["actual_pct"] == pytest.approx(actual, abs=0.01)
        assert band["min_pct"] == pytest.approx(low, abs=0.01)
        assert band["max_pct"] == pytest.approx(high, abs=0.01)

    # Largest position 13.30 against a 15 limit.
    largest = clear["largest_position"]
    assert largest["actual_pct"] == pytest.approx(13.30, abs=0.01)
    assert largest["actual_pct"] < largest["limit_pct"]

    # Stated affirmatively, not as an absence.
    assert "respected" in clear["headline"]


def test_mandate_cl0014_drift(book):
    """Integration 3 — breached low, and not because he sold.

    findings.md § 3: "breached on the low side, not because he sold but
    because his equity fell. Drift, and in the direction that makes the
    exposure look smaller than it is."
    """
    findings = d2.detect(book, GOLDEN_HARBOUR_CLIENT)
    equity = _by_class(findings)["Equity"]

    assert equity["actual_pct"] == pytest.approx(
        RECORDED_CL0014_EQUITY, abs=0.01
    )
    assert equity["min_pct"] == pytest.approx(30, abs=0.01)
    assert equity["max_pct"] == pytest.approx(55, abs=0.01)
    assert equity["verdict"] == BELOW
    assert equity["classification"] == d2.DRIFT

    # He *did* trade in 2026 — a structured product subscription. It was
    # into a different class, so it is not evidence of client direction.
    evidence = equity["classification_evidence"]
    assert evidence["directing_transactions"] == []
    assert evidence["inception_in_reporting_year"] is False


# --- unit assertions ------------------------------------------------------


def test_transaction_types_exist_in_the_data(book):
    """Unit 1 — the guard against the silent-match-nothing bug.

    Both reference documents specify `transactions.type` with values
    'BUY' and 'SUBSCRIPTION'. Neither exists. Written that way the filter
    matches nothing, every client reads as never having traded, and every
    breach classifies as inherited — the right answer for one client, for
    entirely the wrong reason. research.md R1.
    """
    present = set(book.transactions.transaction_type)

    for value in d2.ACQUISITIONS:
        assert value in present, f"{value!r} not in transactions.csv"
    for value in d2.DISPOSALS:
        assert value in present, f"{value!r} not in transactions.csv"
    assert d2.TRANSFER_IN in present

    # And the names the reference documents use are genuinely absent, so
    # this test would have caught the bug.
    assert "BUY" not in present
    assert "SUBSCRIPTION" not in present
    assert not hasattr(book.transactions, "type")


def test_direction_selects_evidence_direction(book):
    """Unit 2 — block 5's rule is one-directional and that is wrong.

    A purchase cannot explain a *below-minimum* breach: buying into a
    class that is under its floor moves it back toward the band. So for a
    below-min breach the evidence must be a disposal, not an acquisition.
    research.md R3.

    CL-0014 is the live case: he subscribed to a structured product in
    January, and his equity is below its floor. If direction were ignored
    he would classify client_directed; block 5 requires drift.
    """
    equity = _by_class(d2.detect(book, GOLDEN_HARBOUR_CLIENT))["Equity"]
    assert equity["verdict"] == BELOW
    assert equity["classification"] == d2.DRIFT
    assert (
        equity["classification_evidence"]["evidence_direction"]
        == "disposals out of the class"
    )

    # An above-max breach looks the other way.
    above = [
        f
        for cid in book.clients.client_id
        for f in d2.detect(book, cid)
        if f.get("verdict") == ABOVE
    ]
    assert above, "the book must contain an above-max breach"
    assert all(
        f["classification_evidence"]["evidence_direction"]
        == "acquisitions into the class"
        for f in above
    )


def test_every_classification_is_permitted(book):
    """Unit 3 — three values, and all three occur on real data."""
    seen = set()
    for client_id in sorted(book.clients.client_id):
        for finding in d2.detect(book, client_id):
            classification = finding["classification"]
            assert classification in (
                d2.INHERITED,
                d2.CLIENT_DIRECTED,
                d2.DRIFT,
                None,
            ), classification
            seen.add(classification)

    # None of the three branches is dead code — unlike a guard proven only
    # by a synthetic case, each of these fires on the bank's own data.
    assert d2.INHERITED in seen
    assert d2.CLIENT_DIRECTED in seen
    assert d2.DRIFT in seen
    assert None in seen, "at least one client must breach nothing"


def test_reporting_year_is_derived_not_written(book):
    """Unit 4 — Principle XI. `inherited` needs a year; it comes from data."""
    assert d2.reporting_year(book) == latest(book)[:4]
    assert len(d2.reporting_year(book)) == 4


def test_every_finding_carries_evidence(book):
    """Principle VI, across the whole book."""
    for client_id in sorted(book.clients.client_id):
        for finding in d2.detect(book, client_id):
            assert finding["evidence"]
            for entry in finding["evidence"]:
                assert entry["file"] in (
                    "mandates.csv",
                    "portfolios.csv",
                    "transactions.csv",
                )
                assert entry["rows"]
            assert "recommend" not in finding["headline"].lower()
            assert "recommend" not in finding["detail"].lower()


def test_findings_are_deterministic(book):
    """Principle VII."""
    for client_id in (HERO, BREACHED_CLIENT, GOLDEN_HARBOUR_CLIENT):
        assert d2.detect(book, client_id) == d2.detect(book, client_id)
