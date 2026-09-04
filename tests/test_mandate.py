"""Spec 001 — unit assertions for the shared band comparison.

`pipeline/mandate.py` is consumed by this spec for a boolean verdict and
by spec 003 for breach classification, so its behaviour is pinned here
before either depends on it.
"""

import pandas as pd
import pytest

from pipeline.load import latest
from pipeline.mandate import (
    ABOVE,
    BELOW,
    WITHIN,
    check_bands,
    check_position_limits,
    compliance_verdict,
)
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


def test_custody_is_not_measured_against_a_band(book):
    """Unit — a custody account is held, not managed.

    Three portfolios in this book are custody accounts, and every
    portfolio carries a mandate_code regardless. Comparing them to a band
    produces a 97.97% "equity breach" on a single legacy holding and a
    100% "alternatives breach" on a client's own founder shareholding.

    Telling a founder their portfolio breaches its equity limit when the
    position *is* the company they founded is not a finding — it is the
    system failing to understand what it is looking at.
    research.md R4 (spec 003).
    """
    from pipeline.mandate import CUSTODY, MANAGED, custody_portfolios

    date = latest(book)
    custody = book.portfolios[book.portfolios.service_model == CUSTODY]
    assert not custody.empty, "precondition: the book has custody accounts"

    for _, portfolio in custody.iterrows():
        client_id = portfolio.client_id

        # Excluded from measurement.
        bands = check_bands(book, client_id, date)
        assert portfolio.portfolio_id not in set(bands.portfolio_id)

        positions = check_position_limits(book, client_id, date)
        assert portfolio.portfolio_id not in set(positions.portfolio_id)

        # But still reported, so nothing disappears from view.
        reported = custody_portfolios(book, client_id, date)
        assert portfolio.portfolio_id in {c["portfolio_id"] for c in reported}
        entry = next(
            c for c in reported if c["portfolio_id"] == portfolio.portfolio_id
        )
        assert entry["value_usd"] > 0
        assert entry["positions"]
        assert "not managed to a mandate" in entry["status"]

    # Only managed portfolios are ever compared.
    models = dict(zip(book.portfolios.portfolio_id, book.portfolios.service_model))
    for client_id in sorted(book.clients.client_id):
        for portfolio_id in check_bands(book, client_id, date).portfolio_id:
            assert models[portfolio_id] in MANAGED


def test_diversified_funds_are_exempt_from_the_position_limit(book):
    """Unit — `concentration_limit_applies` gates the single-position check.

    A diversified index fund at 26% of a portfolio is an asset-allocation
    question, not a concentration risk. Applying a single-name limit to it
    produces false breaches on exactly the instruments that exist to
    spread risk — and buries the real ones: one client's genuine
    single-stock breach was listed *below* a false one.
    research.md R6 (spec 003).
    """
    from pipeline.mandate import LIMIT_APPLIES

    date = latest(book)
    flags = dict(
        zip(
            book.instruments.instrument_id,
            book.instruments.concentration_limit_applies,
        )
    )

    saw_exempt_over_limit = False
    for client_id in sorted(book.clients.client_id):
        positions = check_position_limits(book, client_id, date)
        if positions.empty:
            continue
        for _, row in positions.iterrows():
            over = (
                pd.notna(row.max_single_position_pct)
                and row.actual_pct > row.max_single_position_pct
            )
            applies = flags[row.instrument_id] == LIMIT_APPLIES

            # A breach requires both: over the limit, and subject to it.
            assert bool(row.breached) == bool(over and applies)
            assert bool(row.over_limit_but_exempt) == bool(over and not applies)
            if over and not applies:
                saw_exempt_over_limit = True

    assert saw_exempt_over_limit, (
        "the book must contain a diversified fund over its limit, or this "
        "test proves nothing"
    )
