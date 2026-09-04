"""Spec 008 — D9, the tax position at domicile.

The assertion that matters is the *negative* one: a client domiciled where
capital gains are not levied must be told that harvesting his losses is
pointless, not advised to harvest them.
"""

import pytest

from pipeline.divergence import d9_tax as d9
from tests.conftest import BREACHED_CLIENT, GOLDEN_HARBOUR_CLIENT, HERO

NO_COST_BASIS_NAME = "Nordvind"


def test_harvesting_is_not_suggested_where_the_domicile_does_not_levy(book):
    """Integration — SC-006. The detector's whole point.

    He holds ~62.6m of unrealised losses. Every tax-optimisation instinct
    says harvest. His domicile does not levy capital gains, so harvesting
    buys nothing — and advising it would be confidently wrong in front of
    a client who knows his own tax position better than we do.
    """
    finding = d9.detect(book, GOLDEN_HARBOUR_CLIENT)[0]
    state = finding["tax_position"]

    assert state["capital_gains_levied"] is False
    assert abs(state["losses_base"]) == pytest.approx(62_614_640, abs=1_000)
    assert abs(state["losses_base"]) > state["gains_base"]

    # It names the losses AND says realising them carries no benefit.
    assert "no capital gains benefit" in finding["headline"]
    assert "not worth doing" in finding["detail"]
    assert "buys no relief" in finding["detail"]

    # And it does not tell anyone to do anything.
    for word in ("recommend", "you should", "we suggest", "sell "):
        assert word not in finding["detail"].lower(), word


def test_domicile_governs_and_both_are_named_when_they_differ(book):
    """Integration — SC-007. Domicile, not residence."""
    finding = d9.detect(book, BREACHED_CLIENT)[0]
    state = finding["tax_position"]

    assert state["domicile"] == "Germany"
    assert state["residence"] == "Singapore"
    assert state["domicile_differs_from_residence"] is True
    assert state["capital_gains_levied"] is True

    assert "Germany" in finding["detail"]
    assert "Singapore" in finding["detail"]
    assert "domicile is what governs" in finding["detail"]

    # Her dated obligation meets her net gains.
    assert "realises taxable gains in Germany" in finding["detail"]

    # And the position that cannot be assessed is named, not dropped.
    assert state["unpriced_positions"], "she holds one with no cost basis"
    assert NO_COST_BASIS_NAME in finding["detail"]
    assert NO_COST_BASIS_NAME in finding["unsure_about"]


def test_a_small_loss_is_not_called_large(book):
    """Unit — the overstatement the first version made.

    The hero holds 519k of losses against 6.86m of gains. Calling that "a
    large unrealised loss" would be its own small exaggeration, so the
    emphatic copy is gated on the losses actually dominating.
    """
    finding = d9.detect(book, HERO)[0]
    state = finding["tax_position"]

    assert state["capital_gains_levied"] is False
    assert abs(state["losses_base"]) < state["gains_base"]
    assert "large unrealised loss" not in finding["detail"]
    assert "carries no capital gains consequence" in finding["detail"]


def test_an_unrecorded_domicile_is_stated_never_inferred(book):
    """Unit — FR-016. An invented tax rule is the worst plausible answer."""
    assert d9.CAPITAL_GAINS_LEVIED.get("Thailand") is None

    # Every domicile in the book is either known or explicitly unknown —
    # never silently absent, which `.get` would turn into None by accident
    # rather than by decision.
    for domicile in sorted(book.clients.tax_domicile.unique()):
        assert domicile in d9.CAPITAL_GAINS_LEVIED, domicile

    # And where the rule is None, the copy says so.
    for client_id in sorted(book.clients.client_id):
        for finding in d9.detect(book, client_id):
            if finding["tax_position"]["capital_gains_levied"] is None:
                assert "No capital gains rule is recorded" in finding["detail"]
                assert "nothing is inferred" in finding["unsure_about"]


def test_no_finding_proposes_a_trade(book):
    """FR-015, across the whole book. Principle IX."""
    for client_id in sorted(book.clients.client_id):
        for finding in d9.detect(book, client_id):
            body = (finding["headline"] + " " + finding["detail"]).lower()
            for phrase in ("recommend", "we suggest", "you should", "rebalance"):
                assert phrase not in body, (client_id, phrase)
            assert finding["evidence"]
            assert finding["unsure_about"]
            # It always says it is not advice.
            assert "not tax advice" in finding["unsure_about"]


def test_findings_are_deterministic(book):
    for client_id in (HERO, BREACHED_CLIENT, GOLDEN_HARBOUR_CLIENT):
        assert d9.detect(book, client_id) == d9.detect(book, client_id)
