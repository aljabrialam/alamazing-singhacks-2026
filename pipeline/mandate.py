"""Mandate bands — shared by spec 001 and spec 003.

Bands are defined **per portfolio**, against that portfolio's mandate.
Exposure concentration is a **client-level** question (spec 000's
``client_weights``). The two are never conflated: a client holding three
portfolios under three mandates has three band verdicts and one exposure.

This module lives outside ``divergence/`` because two specs need it. Spec
001 uses it for a boolean verdict — ``compliance_clean``, the strongest
line in the pitch. Spec 003 will use the same comparison to classify a
breach as drift, client-directed or inherited. Writing it twice is how two
subtly different band checks end up in one build.

Contract: ``specs/001-look-through/contracts/look-through.md``
"""

from __future__ import annotations

import pandas as pd

from pipeline.load import Book, snapshots

# Verdicts a single asset class can receive against its band.
WITHIN = "within"
BELOW = "below_min"
ABOVE = "above_max"

# Service models. **Mandate bands apply only to the first two.**
#
# A custody account is held, not managed: the bank holds the assets and
# the client directs them, so there is no strategic allocation anyone is
# steering toward. Every portfolio in this dataset carries a mandate_code
# regardless, so comparing a custody account to its band is possible and
# wrong — it produces a 97.97% "equity breach" on a single legacy holding
# and a 100% "alternatives breach" on a client's own founder shareholding.
#
# Telling a founder their portfolio breaches its equity limit when the
# position *is* the company they founded is not a finding. It is the
# system failing to understand what it is looking at, which is the
# confident fabrication the brief warns against.
#
# Custody portfolios are excluded from measurement and reported
# separately — never removed from view. See
# specs/003-mandate-classification/research.md R4.
ADVISORY = "Advisory"
DISCRETIONARY = "Discretionary"
CUSTODY = "Custody"
MANAGED = (ADVISORY, DISCRETIONARY)

# `instruments.csv` carries `concentration_limit_applies`, and it decides
# whether a single-position limit means anything for that instrument.
#
#   Y  single stocks, single-name perpetuals, direct property, unlisted
#      holdings, structured products — one name, one credit, one building
#   N  diversified funds — an index fund at 26% of a portfolio is an
#      asset-allocation question, not a concentration risk
#
# Applying the limit to everything produces false breaches on exactly the
# instruments that exist to spread risk. It also buries the real ones: on
# this data it reports a Global Developed Equity Index Fund as a breach
# while a single-stock position sits under it in the list.
#
# See specs/003-mandate-classification/research.md R6.
LIMIT_APPLIES = "Y"

_ALLOCATION_COLS = [
    "portfolio_id",
    "mandate_code",
    "asset_class",
    "actual_pct",
    "min_pct",
    "max_pct",
    "target_pct",
    "verdict",
]


def _service_models(book: Book) -> dict:
    return dict(zip(book.portfolios.portfolio_id, book.portfolios.service_model))


def managed_portfolios(book: Book, client_id: str) -> list[str]:
    """The client's portfolios that are managed to a mandate."""
    p = book.portfolios
    mine = p[p.client_id == client_id]
    return sorted(mine[mine.service_model.isin(MANAGED)].portfolio_id)


def custody_portfolios(book: Book, client_id: str, date: str) -> list[dict]:
    """Held, not managed. Reported so nothing disappears from view."""
    p = book.portfolios
    mine = p[(p.client_id == client_id) & (p.service_model == CUSTODY)]
    held = book.holdings_at(client_id, date)

    out = []
    for _, portfolio in mine.sort_values("portfolio_id").iterrows():
        rows = held[held.portfolio_id == portfolio.portfolio_id]
        out.append(
            {
                "portfolio_id": portfolio.portfolio_id,
                "portfolio_name": portfolio.portfolio_name,
                "service_model": CUSTODY,
                "value_usd": float(rows.market_value_usd.sum()),
                "positions": sorted(rows.instrument_id),
                "status": (
                    "held on a custody basis and not managed to a mandate, "
                    "so no strategic allocation band applies"
                ),
            }
        )
    return out


def portfolio_allocation(book: Book, client_id: str, date: str) -> pd.DataFrame:
    """Asset-class allocation within each of a client's **managed** portfolios.

    The denominator is the **portfolio's** value, not the client's, because
    that is the grain the mandate bands are written against.

    Custody portfolios are excluded — see MANAGED above.
    """
    if date not in snapshots(book):
        raise ValueError(
            f"{date!r} is not a snapshot in this book. "
            f"available: {snapshots(book)}"
        )

    managed = managed_portfolios(book, client_id)
    held = book.holdings_at(client_id, date)
    held = held[held.portfolio_id.isin(managed)]
    if held.empty:
        return pd.DataFrame(columns=["portfolio_id", "mandate_code",
                                     "asset_class", "actual_pct"])

    rows = []
    for portfolio_id, positions in held.groupby("portfolio_id", sort=True):
        total = positions.market_value_usd.sum()
        by_class = positions.groupby("asset_class", sort=True)
        for asset_class, group in by_class:
            rows.append(
                {
                    "portfolio_id": portfolio_id,
                    "mandate_code": positions.mandate_code.iloc[0],
                    "asset_class": asset_class,
                    "actual_pct": group.market_value_usd.sum() / total * 100.0,
                }
            )

    return pd.DataFrame(rows).sort_values(
        ["portfolio_id", "asset_class"]
    ).reset_index(drop=True)


def check_bands(book: Book, client_id: str, date: str) -> pd.DataFrame:
    """Compare each held asset class to its band. One row per class held.

    **Iterates the client's holdings, not the mandate's rows.** This is the
    difference between a correct check and a false breach: BALG defines a
    Commodities band and the hero client holds no commodities. Iterating
    the mandate would report Commodities at 0% against a minimum and call
    it a breach. Absence of a holding is not a violation
    (`.alamazing/findings.md` § Data imperfections).
    """
    allocation = portfolio_allocation(book, client_id, date)
    if allocation.empty:
        return pd.DataFrame(columns=_ALLOCATION_COLS)

    bands = book.mandates[
        ["mandate_code", "asset_class", "min_pct", "target_pct", "max_pct"]
    ]
    merged = allocation.merge(
        bands, on=["mandate_code", "asset_class"], how="left"
    )

    def verdict(row) -> str:
        # No band defined for this class. Not a breach, not an error.
        if pd.isna(row.min_pct) and pd.isna(row.max_pct):
            return WITHIN
        if pd.notna(row.min_pct) and row.actual_pct < row.min_pct:
            return BELOW
        if pd.notna(row.max_pct) and row.actual_pct > row.max_pct:
            return ABOVE
        return WITHIN

    merged["verdict"] = merged.apply(verdict, axis=1)

    return merged[_ALLOCATION_COLS].sort_values(
        ["portfolio_id", "asset_class"]
    ).reset_index(drop=True)


def check_position_limits(book: Book, client_id: str, date: str) -> pd.DataFrame:
    """Every position against its mandate's single-position limit.

    Weights are per portfolio, matching the grain the limit is written at.
    """
    managed = managed_portfolios(book, client_id)
    held = book.holdings_at(client_id, date)
    held = held[held.portfolio_id.isin(managed)]
    if held.empty:
        return pd.DataFrame(
            columns=["portfolio_id", "instrument_id", "instrument_name",
                     "actual_pct", "max_single_position_pct", "breached"]
        )

    limits = (
        book.mandates[["mandate_code", "max_single_position_pct"]]
        .drop_duplicates("mandate_code")
    )

    rows = []
    for portfolio_id, positions in held.groupby("portfolio_id", sort=True):
        total = positions.market_value_usd.sum()
        for _, position in positions.iterrows():
            rows.append(
                {
                    "portfolio_id": portfolio_id,
                    "mandate_code": position.mandate_code,
                    "instrument_id": position.instrument_id,
                    "instrument_name": position.instrument_name,
                    "actual_pct": position.market_value_usd / total * 100.0,
                    "limit_applies": (
                        position.get("concentration_limit_applies")
                        == LIMIT_APPLIES
                    ),
                }
            )

    out = pd.DataFrame(rows).merge(limits, on="mandate_code", how="left")

    # A position over the limit that the limit does not apply to is not a
    # breach. Reported as `over_limit_but_exempt` so the size is still
    # visible — Priscilla can see a 26% fund position; it is simply not a
    # concentration violation.
    over = out.max_single_position_pct.notna() & (
        out.actual_pct > out.max_single_position_pct
    )
    out["breached"] = over & out.limit_applies
    out["over_limit_but_exempt"] = over & ~out.limit_applies

    return out.sort_values(
        ["actual_pct", "instrument_id"], ascending=[False, True]
    ).reset_index(drop=True)


def compliance_verdict(book: Book, client_id: str, date: str) -> dict:
    """Is every band respected and every position within its limit?

    Returns the verdict **and its workings**, because spec 001 has to show
    them: the argument is not "he is compliant" but "here are the five
    bands, all respected, and the portfolio is still 42% one bet". A bare
    boolean would make that panel impossible to render.

    ``clean`` is earned, never defaulted. It is true only when every band
    of every one of the client's portfolios passes and no single position
    exceeds its limit.
    """
    bands = check_bands(book, client_id, date)
    positions = check_position_limits(book, client_id, date)

    breached_bands = bands[bands.verdict != WITHIN]
    breached_positions = positions[positions.breached]
    exempt_over = positions[positions.over_limit_but_exempt]

    largest = positions.iloc[0] if not positions.empty else None

    return {
        "clean": bool(breached_bands.empty and breached_positions.empty),
        "bands": bands.to_dict("records"),
        "breached_bands": breached_bands.to_dict("records"),
        "breached_positions": breached_positions.to_dict("records"),
        "custody": custody_portfolios(book, client_id, date),
        "over_limit_but_exempt": exempt_over.to_dict("records"),
        "largest_position": (
            {
                "instrument_id": largest.instrument_id,
                "instrument_name": largest.instrument_name,
                "actual_pct": float(largest.actual_pct),
                "limit_pct": (
                    float(largest.max_single_position_pct)
                    if pd.notna(largest.max_single_position_pct)
                    else None
                ),
            }
            if largest is not None
            else None
        ),
    }
