"""Spec 000 — unit assertions for the load layer.

Five assertions: the book's shape, the joins, the imperfection record, the
weight recomputation, and the trap it exists to close.
"""

import pandas as pd
import pytest

from pipeline.load import client_weights, latest, snapshots
from tests.conftest import (
    HERO,
    MULTI_PORTFOLIO_CLIENT,
    NO_COST_BASIS_CLIENT,
    NO_COST_BASIS_INSTRUMENT,
)

# Row counts from jb-docs/DATA_DICTIONARY.md, § Files.
EXPECTED = {"holdings": 1015, "clients": 20, "portfolios": 24, "notes": 28}


def test_book_row_counts(book):
    """Unit 1 — the twelve files loaded, nothing dropped."""
    assert len(book.holdings) == EXPECTED["holdings"]
    assert len(book.clients) == EXPECTED["clients"]
    assert len(book.portfolios) == EXPECTED["portfolios"]
    assert len(book.notes) == EXPECTED["notes"]


def test_joins_present_and_no_row_inflation(book):
    """Unit 2 — both joins landed and neither duplicated a row.

    The row count is the assertion that matters. A merge that duplicates
    rows inflates every weight in the book, and it inflates them
    plausibly enough to reach a slide.
    """
    for col in (
        "underlying_reference",
        "sustainability_excluded",
        "concentration_limit_applies",
        "mandate_code",
    ):
        assert col in book.holdings.columns, col

    # Both asset classes survive. `asset_class` is how the position is
    # booked; `asset_class_inst` is the reference classification. Spec 001
    # rests on the two differing.
    assert "asset_class" in book.holdings.columns
    assert "asset_class_inst" in book.holdings.columns

    assert len(book.holdings) == EXPECTED["holdings"]


def test_imperfections_recorded(book):
    """Unit 3 — data problems reported, not worked around.

    Their brief: if something in the data looks wrong or contradictory,
    say so. Noticing is worth more than quietly working around it
    (Principle X).
    """
    assert book.imperfections, "the record must not be empty"

    # Every record must be traceable to its source row (Principle VI).
    for record in book.imperfections:
        for key in ("kind", "file", "instrument_id", "field", "detail"):
            assert record.get(key), (key, record)

    missing = [
        i for i in book.imperfections if i["kind"] == "missing_cost_basis"
    ]
    assert missing, "the transferred-in holding with no cost basis"
    assert {i["client_id"] for i in missing} == {NO_COST_BASIS_CLIENT}
    assert {i["instrument_id"] for i in missing} == {NO_COST_BASIS_INSTRUMENT}

    # The gap spans every snapshot — the cost basis never existed, rather
    # than being absent from one report. Spec 004 needs that distinction.
    assert len(missing) == len(snapshots(book))

    # Nothing was dropped to tidy the numbers.
    held = book.holdings[
        (book.holdings.instrument_id == NO_COST_BASIS_INSTRUMENT)
        & (book.holdings.client_id == NO_COST_BASIS_CLIENT)
    ]
    assert len(held) == len(snapshots(book))
    assert held.unrealised_pnl_pct.isna().all()

    # The gap belongs to the transfer, not to the instrument. Another
    # client holds the same stock with a full cost basis and a +93% gain,
    # acquired in 2011. So this is not a reference-data omission that
    # could be repaired from elsewhere in the file — the cost basis for
    # *her* position never came across when it was transferred in on her
    # husband's death. Nothing can supply it, which is why the number
    # stays absent rather than being inferred.
    elsewhere = book.holdings[
        (book.holdings.instrument_id == NO_COST_BASIS_INSTRUMENT)
        & (book.holdings.client_id != NO_COST_BASIS_CLIENT)
    ]
    assert not elsewhere.empty
    assert elsewhere.unrealised_pnl_pct.notna().all()
    assert not any(
        i["client_id"] != NO_COST_BASIS_CLIENT for i in missing
    ), "only the transferred-in position is affected"

    # Deterministic ordering (Principle VII).
    kinds = [i["kind"] for i in book.imperfections]
    assert kinds == sorted(kinds)


def test_client_weights_sum_to_100(book):
    """Unit 4 — one denominator per client per date. All 20, every date.

    Not a sample. A single client with a second denominator is a silent
    wrong number, and the whole product is built on these weights.
    """
    for client_id in sorted(book.clients.client_id):
        for date in snapshots(book):
            w = client_weights(book, client_id, date)
            if w.empty:
                continue
            assert w.w.sum() == pytest.approx(100.0, abs=1e-3), (
                client_id,
                date,
            )


def test_weight_pct_trap_is_real(book):
    """Unit 5 — the trap, demonstrated rather than described.

    `weight_pct` in holdings.csv is scoped to a *portfolio*. This client
    holds three, so summing the column gives roughly 300%. The recomputed
    weights give 100%. Recorded in the constitution's Technology Standards
    as the single most likely source of a silent wrong number here.
    """
    date = latest(book)
    raw = book.holdings_at(MULTI_PORTFOLIO_CLIENT, date).weight_pct.sum()
    recomputed = client_weights(book, MULTI_PORTFOLIO_CLIENT, date).w.sum()

    portfolios = book.holdings_at(
        MULTI_PORTFOLIO_CLIENT, date
    ).portfolio_id.nunique()
    assert portfolios > 1

    assert raw == pytest.approx(100.0 * portfolios, abs=0.01)
    assert recomputed == pytest.approx(100.0, abs=1e-3)
    assert abs(raw - recomputed) > 1.0, "the two must visibly diverge"


def test_unknown_snapshot_is_rejected(book):
    """A typo'd date must not return an empty frame.

    An empty result is how a zero exposure gets quoted as a fact (FR-018).
    """
    with pytest.raises(ValueError, match="not a snapshot"):
        client_weights(book, HERO, "1999-01-01")


def test_two_loads_are_identical():
    """Principle VII — same inputs, same output, including row order."""
    from pipeline.load import load_all

    a, b = load_all("data/"), load_all("data/")
    pd.testing.assert_frame_equal(a.holdings, b.holdings)
    assert a.imperfections == b.imperfections
