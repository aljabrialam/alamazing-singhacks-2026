"""Currency conversion, read from the market context.

This is its own module for one reason: **the rates in this dataset use
opposite conventions, and only the `unit` column says which.**

    EURUSD   1.092   unit = "USD per EUR"   ->  multiply
    USDHKD   7.810   unit = "HKD per USD"   ->  divide

Inferring the direction from the series identifier is the trap. Treating
``USDHKD`` as "USD per HKD" turns a HKD 60,000,000 obligation into
USD 468,600,000 instead of USD 7,682,458 — a 61x error, wrong in the
direction that makes a finding look like a catastrophe rather than a bill.

A wrong number that is dramatic is worse than one that is dull, because
nobody questions it. So the convention is read, never guessed, and a
currency with no rate produces **no figure at all** rather than a
plausible one (Principle IV).

Consumed by spec 004 (planned cash needs, commitments) and spec 005
(scenario repricing).
"""

from __future__ import annotations

from pipeline.load import Book, latest

USD = "USD"

# The `unit` column spells the direction out. "USD per EUR" means one EUR
# buys 1.092 USD, so an EUR amount is multiplied. "HKD per USD" means one
# USD buys 7.810 HKD, so an HKD amount is divided.
_USD_PER = "USD per"


def _rate_row(book: Book, currency: str, date: str):
    """Find a rate for this currency, whichever way round it is quoted."""
    market = book.market
    rows = market[market.snapshot_date == date]
    for series_id in (f"{currency}{USD}", f"{USD}{currency}"):
        match = rows[rows.series_id == series_id]
        if not match.empty:
            return match.iloc[0]
    return None


def to_usd(
    book: Book, amount: float, currency: str, date: str | None = None
) -> dict:
    """Convert an amount to USD using the rate at ``date``.

    Returns a dict rather than a float so the caller always has the
    provenance to put in an evidence panel, and so a failure is a value
    rather than an exception:

        {"usd": float | None,
         "rate": float | None,
         "series_id": str | None,
         "unit": str | None,
         "note": str}

    ``usd`` is ``None`` when no rate exists. Nothing is invented.
    """
    date = date or latest(book)
    currency = str(currency).strip().upper()

    if currency == USD:
        return {
            "usd": float(amount),
            "rate": 1.0,
            "series_id": None,
            "unit": None,
            "note": "already USD, no conversion applied",
        }

    row = _rate_row(book, currency, date)
    if row is None:
        return {
            "usd": None,
            "rate": None,
            "series_id": None,
            "unit": None,
            "note": (
                f"no {currency}/USD rate in the market context at {date}, "
                f"so this amount is not converted and no USD figure is "
                f"stated"
            ),
        }

    rate = float(row.value)
    unit = str(row.unit)

    # The whole point of this module.
    if unit.startswith(_USD_PER):
        usd = float(amount) * rate
        direction = "multiplied"
    else:
        usd = float(amount) / rate
        direction = "divided"

    return {
        "usd": usd,
        "rate": rate,
        "series_id": str(row.series_id),
        "unit": unit,
        "note": (
            f"{currency} {amount:,.0f} {direction} by {row.series_id} "
            f"{rate} ({unit}) at {date}"
        ),
    }
