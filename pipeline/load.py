"""Spec 000 — the data layer.

One folder of files in, one queryable ``Book`` out.

This module is the only place in the pipeline that touches the filesystem,
and the only place client-level exposure is computed. Both facts are
deliberate: a detector cannot half-see a changed file mid-build, and there
is exactly one denominator for a client's weights.

Contract: ``specs/000-data-layer/contracts/data-layer.md``
Shapes:   ``specs/000-data-layer/data-model.md``
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

# Grain of the holdings frame. Used to name row identifiers in evidence
# records so an imperfection can always be traced to its source row.
_ROW_KEYS = ("client_id", "portfolio_id", "instrument_id", "snapshot_date")

# The twelve sources, mapped to the Book field each becomes. The names are
# the bank's, not ours — see jb-docs/DATA_DICTIONARY.md.
_CSV_SOURCES = {
    "clients": "clients.csv",
    "portfolios": "portfolios.csv",
    "holdings": "holdings.csv",
    "instruments": "instruments.csv",
    "mandates": "mandates.csv",
    "transactions": "transactions.csv",
    "credit": "credit_facilities.csv",
    "commitments": "commitments.csv",
    "cash_needs": "planned_cash_needs.csv",
    "market": "market_context.csv",
    "events": "event_log.csv",
}
_NOTES_SOURCE = "rm_notes.json"

# Suffix applied to instrument reference columns that collide with holdings
# columns. Seven collide; pandas' default _x/_y says nothing about which is
# which, in a frame six detectors read. See research.md R2.
_INST_SUFFIX = "_inst"


@dataclass
class Book:
    """Everything the bank knows, as loaded from one folder.

    The first argument of every function in the pipeline. Detectors read
    from it and never from disk.
    """

    clients: pd.DataFrame
    portfolios: pd.DataFrame
    holdings: pd.DataFrame
    instruments: pd.DataFrame
    mandates: pd.DataFrame
    transactions: pd.DataFrame
    credit: pd.DataFrame
    commitments: pd.DataFrame
    cash_needs: pd.DataFrame
    market: pd.DataFrame
    events: pd.DataFrame
    notes: list = field(default_factory=list)
    imperfections: list = field(default_factory=list)

    def client(self, client_id: str) -> pd.Series:
        """The one client row. Raises if the id is not in the book."""
        rows = self.clients[self.clients.client_id == client_id]
        if rows.empty:
            raise ValueError(
                f"no such client: {client_id!r}. "
                f"known: {sorted(self.clients.client_id)}"
            )
        return rows.iloc[0]

    def notes_for(self, client_id: str) -> list:
        """That client's notes, oldest first."""
        return sorted(
            (n for n in self.notes if n.get("client_id") == client_id),
            key=lambda n: (n.get("note_date", ""), n.get("note_id", "")),
        )

    def holdings_at(self, client_id: str, date: str) -> pd.DataFrame:
        """That client's positions at one snapshot, across all portfolios.

        The snapshot condition is the point. Omitting it sums five
        snapshots into one exposure figure, which looks plausible.
        """
        return self.holdings[
            (self.holdings.client_id == client_id)
            & (self.holdings.snapshot_date == date)
        ]


def snapshots(book: Book) -> list[str]:
    """Every snapshot date in the holdings, ascending, derived from data.

    ISO strings sort lexicographically, so this is chronological. No date
    is written into this module (Principle XI).
    """
    return sorted(book.holdings.snapshot_date.unique().tolist())


def latest(book: Book) -> str:
    """The most recent snapshot. What the demo calls "today"."""
    return snapshots(book)[-1]


def _row_evidence(row: pd.Series) -> dict:
    """The identifiers that let a record be traced back to its source row."""
    return {k: row.get(k) for k in _ROW_KEYS}


def _collect_imperfections(
    holdings: pd.DataFrame, instruments: pd.DataFrame
) -> list[dict]:
    """Record what the files cannot tell us. Never drop, fill or repair.

    Their brief asks for this explicitly: if something in the data looks
    wrong or contradictory, say so. Noticing is worth more than quietly
    working around it (Principle X).

    One entry per affected *row*, not per instrument — the count is part of
    the evidence, and spec 004 needs to know a gap spans every snapshot
    rather than one.
    """
    found: list[dict] = []

    # No cost basis carried through. Against this data that is a single
    # holding, transferred in on a death, missing at every snapshot. It
    # matters because selling it is one option for a tax instalment, and
    # nobody can state the tax consequence of doing so.
    for _, row in holdings[holdings.unrealised_pnl_pct.isna()].iterrows():
        found.append(
            {
                "kind": "missing_cost_basis",
                "file": _CSV_SOURCES["holdings"],
                **_row_evidence(row),
                "field": "unrealised_pnl_pct",
                "detail": (
                    f"{row.instrument_name} carries no cost basis, so its "
                    f"gain or loss is unknown. Nothing was assumed in its "
                    f"place."
                ),
            }
        )

    # A valuation older than the snapshot it is reported against. Private
    # market marks lag a quarter by design, so this is a lag to be stated,
    # not an error to be flagged.
    stale = holdings[holdings.valuation_date != holdings.snapshot_date]
    for _, row in stale.iterrows():
        found.append(
            {
                "kind": "stale_valuation",
                "file": _CSV_SOURCES["holdings"],
                **_row_evidence(row),
                "field": "valuation_date",
                "detail": (
                    f"{row.instrument_name} is valued at "
                    f"{row.valuation_date} against a {row.snapshot_date} "
                    f"snapshot. Private market valuations lag by design; "
                    f"this is a lag, not an error."
                ),
            }
        )

    # Reference data that does not join. Returns nothing against this data.
    # Implemented anyway — a real bank's reference data does not join
    # cleanly, and this is how you find out the day it stops being true.
    known = set(instruments.instrument_id)
    orphans = holdings[~holdings.instrument_id.isin(known)]
    for _, row in orphans.iterrows():
        found.append(
            {
                "kind": "orphan_instrument",
                "file": _CSV_SOURCES["holdings"],
                **_row_evidence(row),
                "field": "instrument_id",
                "detail": (
                    f"{row.instrument_id} is held but absent from "
                    f"{_CSV_SOURCES['instruments']}. The row is retained; "
                    f"its reference attributes are unknown."
                ),
            }
        )

    # Byte-identical between runs (Principle VII).
    return sorted(
        found,
        key=lambda i: (
            i["kind"],
            str(i["client_id"]),
            str(i["instrument_id"]),
            str(i["snapshot_date"]),
        ),
    )


def load_all(path: str = "data/") -> Book:
    """Read the twelve files, join twice, record imperfections.

    ``path`` is an argument, never a constant. There is no file-upload
    feature and none will be added (Principle XI).

    Dates are left as ISO strings rather than parsed. They sort correctly,
    they match the ``price_<date>`` and ``aum_<date>`` column suffixes the
    scenario detector looks up, and they serialise to JSON without a
    converter. See research.md R6.
    """
    root = Path(path)
    frames: dict[str, pd.DataFrame] = {}

    for name, filename in _CSV_SOURCES.items():
        f = root / filename
        if not f.exists():
            raise FileNotFoundError(f"missing data file: {f}")
        frames[name] = pd.read_csv(f)

    notes_file = root / _NOTES_SOURCE
    if not notes_file.exists():
        raise FileNotFoundError(f"missing data file: {notes_file}")
    with notes_file.open() as fh:
        notes = json.load(fh)

    holdings = frames["holdings"]
    instruments = frames["instruments"]
    before = len(holdings)

    # Imperfections are collected from the raw frames, before the joins, so
    # a record's row identifiers are the source row's.
    imperfections = _collect_imperfections(holdings, instruments)

    # Bring the instrument reference onto every position. Both asset_class
    # columns survive: `asset_class` is how the position is booked,
    # `asset_class_inst` is the reference classification. Spec 001's whole
    # argument is that these differ — an accumulator on a property
    # developer is booked as a structured product, so no equity
    # concentration check sees it. Neither may be dropped.
    holdings = holdings.merge(
        instruments,
        on="instrument_id",
        how="left",
        suffixes=("", _INST_SUFFIX),
    )

    holdings = holdings.merge(
        frames["portfolios"][["portfolio_id", "mandate_code"]],
        on="portfolio_id",
        how="left",
    )

    # A merge that duplicates rows inflates every weight in the book, and
    # it inflates them plausibly. Fail loudly instead.
    if len(holdings) != before:
        raise ValueError(
            f"joins changed the holdings row count: {before} -> "
            f"{len(holdings)}. A duplicate key in "
            f"{_CSV_SOURCES['instruments']} or "
            f"{_CSV_SOURCES['portfolios']} would do this."
        )

    frames["holdings"] = holdings

    return Book(notes=notes, imperfections=imperfections, **frames)


def client_weights(book: Book, client_id: str, date: str) -> pd.DataFrame:
    """Client-level exposure. The one function that must not be wrong.

    ``weight_pct`` in holdings.csv is scoped to a *portfolio*. Summing it
    for a client who holds several gives 200% or 300% — and, worse, gives a
    single position a believable but wrong share. So the weight is
    recomputed here from ``market_value_usd`` with one denominator per
    client per date, across every portfolio they hold.

    Recorded in the constitution's Technology Standards as the single most
    likely source of a silent wrong number in this dataset.

    Returns every row of the client's holdings at that snapshot plus a
    ``w`` column. A frame, not a scalar — so the caller can filter, group
    by theme, or cite row ids. A function returning a bare percentage would
    make Principle VI impossible to honour downstream.
    """
    available = snapshots(book)
    if date not in available:
        raise ValueError(
            f"{date!r} is not a snapshot in this book. available: {available}"
        )

    held = book.holdings_at(client_id, date)
    if held.empty:
        # Not an error: a client may hold nothing at a given snapshot. An
        # empty frame with the right columns, and no division by zero.
        return held.assign(w=pd.Series(dtype="float64"))

    total = held.market_value_usd.sum()
    weighted = held.assign(w=held.market_value_usd / total * 100.0)

    return weighted.sort_values(
        ["w", "instrument_id"], ascending=[False, True]
    ).reset_index(drop=True)
