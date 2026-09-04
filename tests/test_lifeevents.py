"""Spec 008 — D10, what the allocation was not built for.

The finding is about the **profile**, not the portfolio. That distinction
is the reason this exists separately from D4, which already reports the
obligation itself.
"""

import pytest

from pipeline.divergence import d10_lifeevents as d10
from tests.conftest import BREACHED_CLIENT, GOLDEN_HARBOUR_CLIENT, HERO


def test_profile_contradiction_cl0019(book):
    """Integration — SC-008.

    His recorded liquidity needs are Low against a 25-year horizon, and his
    own note describes USD 5m needed for a family office inside eighteen
    months. The profile is what suitability runs against, so a portfolio
    can pass every check and still be built for the wrong horizon.
    """
    finding = d10.detect(book, HERO)[0]
    profile = finding["recorded_profile"]

    assert profile["liquidity_needs"] in d10.LOW_LIQUIDITY
    assert profile["investment_horizon_years"] == pytest.approx(25.0, abs=0.1)

    obligation = max(finding["obligations"], key=lambda o: o["amount_usd"])
    assert obligation["amount_usd"] == pytest.approx(5_000_000, abs=1_000)
    assert obligation["years_away"] < d10.DEFAULT_NEAR_YEARS

    # It addresses the profile, not the holdings.
    assert "profile that looks out of date" in finding["detail"]
    assert "suitability" in finding["detail"]
    assert "rebalance" not in finding["detail"].lower()

    # Both halves evidenced: the profile field and the obligation.
    files = {e["file"] for e in finding["evidence"]}
    assert "clients.csv" in files
    assert "planned_cash_needs.csv" in files


def test_a_consistent_profile_produces_nothing(book):
    """FR — no finding where the profile matches the obligations.

    Two of twenty clients contradict themselves. A detector that fired for
    everyone would be worth nothing.
    """
    firing = [
        client_id
        for client_id in sorted(book.clients.client_id)
        if d10.detect(book, client_id)
    ]
    assert 1 <= len(firing) <= 5, firing

    # Both demo clients with High/Medium recorded needs are silent.
    for client_id in (BREACHED_CLIENT, GOLDEN_HARBOUR_CLIENT):
        recorded = str(book.client(client_id).liquidity_needs)
        if recorded not in d10.LOW_LIQUIDITY:
            assert d10.detect(book, client_id) == []


def test_thresholds_are_parameters(book):
    """Principle XI — the horizon and materiality bounds are arguments."""
    # An impossibly tight near-window silences it.
    assert d10.detect(book, HERO, near_years=0.1) == []
    # An impossibly high materiality bar silences it.
    assert d10.detect(book, HERO, material_pct=99.0) == []


def test_no_markdown_leaks_into_prose(book):
    """The detail is rendered as plain text, so asterisks would show."""
    for client_id in sorted(book.clients.client_id):
        for finding in d10.detect(book, client_id):
            assert "**" not in finding["detail"]
            assert "**" not in finding["headline"]
            assert "recommend" not in finding["detail"].lower()
            assert finding["unsure_about"]


def test_findings_are_deterministic(book):
    for client_id in sorted(book.clients.client_id):
        assert d10.detect(book, client_id) == d10.detect(book, client_id)
