"""Spec 004 — currency conversion.

The whole module exists because the two rates this demo needs are quoted
in opposite directions, and only the `unit` column says which.
"""

import pytest

from pipeline.fx import to_usd


def test_conventions_are_read_not_guessed(book):
    """Unit 1 — the 61x error this module exists to prevent.

    EURUSD is "USD per EUR" and multiplies. USDHKD is "HKD per USD" and
    divides. Inferring from the series identifier gets one of them
    backwards, and the wrong one is wrong in the direction that makes a
    bill look like a catastrophe. research.md R1.
    """
    eur = to_usd(book, 3_400_000, "EUR")
    assert eur["series_id"] == "EURUSD"
    assert "USD per" in eur["unit"]
    assert eur["usd"] == pytest.approx(3_712_800, abs=1_000)
    assert "multiplied" in eur["note"]

    hkd = to_usd(book, 60_000_000, "HKD")
    assert hkd["series_id"] == "USDHKD"
    assert "USD per" not in hkd["unit"]
    assert hkd["usd"] == pytest.approx(7_682_458, abs=1_000)
    assert "divided" in hkd["note"]

    # What the guess would have produced: 60,000,000 x 7.81 = 468.6m,
    # against the correct 7.68m. Sixty-one times too large.
    wrong = 60_000_000 * hkd["rate"]
    assert wrong / hkd["usd"] == pytest.approx(61.0, abs=1.0)


def test_unknown_currency_invents_nothing(book):
    """Unit 2 — Principle IV. No rate, no figure."""
    result = to_usd(book, 500, "ZWL")
    assert result["usd"] is None
    assert result["rate"] is None
    assert "no ZWL/USD rate" in result["note"]


def test_usd_is_not_converted(book):
    result = to_usd(book, 1_000, "USD")
    assert result["usd"] == pytest.approx(1_000, abs=0.01)
    assert result["rate"] == 1.0
