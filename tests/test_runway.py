"""Spec 004 — D4, liquidity runway."""

import pytest

from pipeline.load import latest
from pipeline.divergence import d4_runway as d4
from tests.conftest import BREACHED_CLIENT, GOLDEN_HARBOUR_CLIENT


def _one(findings, need_id):
    matching = [f for f in findings if f["obligation"]["id"] == need_id]
    assert len(matching) == 1, need_id
    return matching[0]


def test_runway_cl0003(book):
    """Integration 1 — she can pay easily, and paying costs her the equity.

    Block 6 calls this "tight" on a cash-plus-fixed-income figure. By
    block 6's own liquidity rule she is 88.29% liquid and covers the bill
    five times over. The real finding is the second figure: cash plus
    fixed income is 16.83% and the bill is 16.74%, so meeting it consumes
    essentially all her non-equity holdings. research.md R2.
    """
    finding = _one(d4.detect(book, BREACHED_CLIENT), "CN-004")
    funds = finding["liquidity"]

    # SC-001 — the conversion.
    assert finding["obligation"]["currency"] == "EUR"
    assert finding["obligation"]["amount_usd"] == pytest.approx(
        3_712_800, abs=1_000
    )

    # SC-002 — both figures, and the need as a share of the portfolio.
    assert funds["liquid_pct"] == pytest.approx(88.29, abs=0.01)
    assert funds["near_cash_pct"] == pytest.approx(16.83, abs=0.01)
    assert finding["need_pct"] == pytest.approx(16.74, abs=0.01)

    # The bill is almost exactly the size of her non-equity holdings.
    assert finding["near_cash_cover_ratio"] == pytest.approx(1.01, abs=0.02)
    assert finding["cover_ratio"] == pytest.approx(5.27, abs=0.02)

    # She is not blocked — no facility.
    assert finding["funding_blocked_by_facility"] is False

    # The copy makes the distinction rather than calling it tight.
    assert "88.29%" in finding["detail"]
    assert "cash and fixed income" in finding["detail"]


def test_runway_cl0014(book):
    """Integration 2 — he cannot fund it by selling.

    73% liquid against a 29% need reads as 2.5x comfort. His only
    portfolio is the collateral for a facility 0.59pp from a margin call,
    and funding the need from it pushes loan-to-value to 97.76%.
    research.md R3 — this is not in findings.md.
    """
    finding = _one(d4.detect(book, GOLDEN_HARBOUR_CLIENT), "CN-013")
    funds = finding["liquidity"]
    facility = finding["facility"]
    after = finding["facility_after_sale"]

    # SC-003 — the conversion.
    assert finding["obligation"]["currency"] == "HKD"
    assert finding["obligation"]["amount_usd"] == pytest.approx(
        7_682_458, abs=1_000
    )

    # SC-005 — illiquid holdings match findings.md § 3 exactly.
    assert funds["by_tier"]["Illiquid"] == pytest.approx(26.62, abs=0.01)

    # SC-004 — the facility, and what funding the need does to it.
    assert facility["ltv_pct"] == pytest.approx(69.41, abs=0.01)
    assert facility["margin_call_ltv_pct"] == pytest.approx(70.0, abs=0.01)
    assert facility["margin_call_ltv_pct"] - facility["ltv_pct"] < 1.0

    assert after["ltv_pct_after"] > facility["margin_call_ltv_pct"]
    assert after["breaches_margin_call"] is True

    # No unpledged liquidity: his only portfolio *is* the collateral.
    assert funds["free_liquid_usd"] == pytest.approx(0.0, abs=1.0)
    assert finding["funding_blocked_by_facility"] is True

    # The headline says so plainly.
    assert "cannot be funded" in finding["headline"]
    assert finding["severity"] == 5

    # Evidence cites the facility row.
    files = {e["file"] for e in finding["evidence"]}
    assert "credit_facilities.csv" in files


def test_only_daily_and_weekly_count(book):
    """Unit 3 — block 6: Monthly and Illiquid do not count."""
    date = latest(book)
    for client_id in sorted(book.clients.client_id):
        funds = d4.liquidity(book, client_id, date)
        if not funds["total_usd"]:
            continue
        excluded = sum(
            pct
            for tier, pct in funds["by_tier"].items()
            if tier not in d4.LIQUID_TIERS
        )
        assert funds["liquid_pct"] + excluded == pytest.approx(100.0, abs=0.01)

    # Her Monthly alternatives are excluded, and her Illiquid structured
    # product too.
    funds = d4.liquidity(book, BREACHED_CLIENT, date)
    assert "Monthly" in funds["by_tier"]
    assert "Illiquid" in funds["by_tier"]
    assert funds["liquid_pct"] == pytest.approx(88.29, abs=0.01)


def test_pledged_collateral_is_reported(book):
    """Unit 4 — a facility only blocks when there is no free liquidity.

    Two clients here have zero unpledged liquidity and are blocked. One
    has a pledged custody account *and* an unpledged discretionary
    portfolio — he funds the need from the latter and is not blocked. The
    naive version reported all three as blocked.
    """
    blocked, unblocked_with_facility = [], []
    for client_id in sorted(book.clients.client_id):
        for finding in d4.detect(book, client_id):
            if not finding.get("facility"):
                continue
            if finding["funding_blocked_by_facility"]:
                blocked.append(finding)
            else:
                unblocked_with_facility.append(finding)

    assert blocked, "the book must contain a genuinely blocked obligation"
    assert unblocked_with_facility, (
        "and one where a facility exists but does not constrain"
    )

    # Blocked implies no unpledged liquidity covers the need.
    for finding in blocked:
        assert (
            finding["liquidity"]["free_liquid_usd"]
            < finding["obligation"]["amount_usd"]
        )
        assert finding["facility_after_sale"]["breaches_margin_call"]

    # Unblocked implies free liquidity does cover it.
    for finding in unblocked_with_facility:
        assert (
            finding["liquidity"]["free_liquid_usd"]
            >= finding["obligation"]["amount_usd"]
        )


def test_private_market_lag_is_noted_never_flagged(book):
    """Block 6 — industry practice, not an error (FR-007)."""
    finding = _one(d4.detect(book, BREACHED_CLIENT), "CN-004")
    unsure = finding["unsure_about"]
    assert "lag" in unsure
    assert "industry practice" in unsure
    # Not reported as a defect.
    assert "error" not in unsure.lower().replace("rather than current", "")


def test_findings_are_deterministic(book):
    for client_id in (BREACHED_CLIENT, GOLDEN_HARBOUR_CLIENT):
        assert d4.detect(book, client_id) == d4.detect(book, client_id)
