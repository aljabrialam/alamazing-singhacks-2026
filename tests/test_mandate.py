"""Spec 001 — unit assertions for the shared band comparison.

`pipeline/mandate.py` is consumed by this spec for a boolean verdict and
by spec 003 for breach classification, so its behaviour is pinned here
before either depends on it.
"""

import pytest

from pipeline.load import latest
from pipeline.mandate import ABOVE, BELOW, WITHIN, check_bands, compliance_verdict
from tests.conftest import BREACHED_CLIENT, GOLDEN_HARBOUR_CLIENT, HERO


def test_band_comparison_classifies_all_three_cases(book):
    """Unit 1 — within, below minimum and above maximum all identified.

    One client supplies all three: Margarethe's inherited portfolio is
    above its equity ceiling and below its fixed-income floor at the same
    time, with other classes in range.
    """
    bands = check_bands(book, BREACHED_CLIENT, latest(book))
    verdicts = dict(zip(bands.asset_class, bands.verdict))

    assert verdicts["Equity"] == ABOVE
    assert verdicts["Fixed Income"] == BELOW
    assert verdicts["Cash and Equivalents"] == WITHIN

    # A breach on the low side is a breach. CL-0014's equity fell below
    # its floor without him selling anything.
    low = check_bands(book, GOLDEN_HARBOUR_CLIENT, latest(book))
    assert dict(zip(low.asset_class, low.verdict))["Equity"] == BELOW


def test_missing_band_is_not_a_breach(book):
    """Unit 2 — absence of a mandate row is not a violation.

    The hero's BALG mandate defines a Commodities band and he holds no
    commodities. An implementation iterating the *mandate's* asset classes
    rather than the *client's* would report Commodities at 0% against a
    minimum and call it a breach. It would be wrong, and it would break
    the strongest line in the pitch.

    `.alamazing/findings.md` § Data imperfections states it directly:
    absence of the row is not a breach.
    """
    date = latest(book)
    bands = check_bands(book, HERO, date)

    held = set(book.holdings_at(HERO, date).asset_class)
    defined = set(
        book.mandates[
            book.mandates.mandate_code
            == book.holdings_at(HERO, date).mandate_code.iloc[0]
        ].asset_class
    )

    # There is genuinely a band he has no holding for — otherwise this
    # test proves nothing.
    assert defined - held, "expected a band with no matching holding"

    # Only held classes are reported, and none of them breaches.
    assert set(bands.asset_class) == held
    assert (bands.verdict == WITHIN).all()
    assert compliance_verdict(book, HERO, date)["clean"] is True


def test_bands_are_per_portfolio_not_per_client(book):
    """Bands apply per portfolio; exposure is a client-level question.

    Conflating the two is the same class of error as spec 000's
    `weight_pct` trap, one level up.
    """
    date = latest(book)
    for client_id in sorted(book.clients.client_id):
        bands = check_bands(book, client_id, date)
        if bands.empty:
            continue
        for portfolio_id, group in bands.groupby("portfolio_id"):
            assert group.actual_pct.sum() == pytest.approx(100.0, abs=1e-3), (
                client_id,
                portfolio_id,
            )
