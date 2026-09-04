"""Spec 000 — what changed between two snapshots.

A brief has to say not just what the portfolio *is* but what moved and who
moved it. This module compares one client's positions at two dates and can
rank that comparison by the size of the value change.

Contract: ``specs/000-data-layer/contracts/data-layer.md``
"""

from __future__ import annotations

import pandas as pd

from pipeline.load import Book, client_weights

# Columns describing the instrument rather than the position. Taken from
# whichever date carries them, so a position present at only one date still
# has a readable name in an evidence panel.
_DESCRIPTIVE = ("instrument_name", "asset_class")

_OUT = [
    "instrument_id",
    *_DESCRIPTIVE,
    "value_a",
    "value_b",
    "weight_a",
    "weight_b",
    "d_value",
    "d_weight",
]


def _side(book: Book, client_id: str, date: str, suffix: str) -> pd.DataFrame:
    """One date's positions, reduced to the columns the comparison needs."""
    w = client_weights(book, client_id, date)
    keep = ["instrument_id", *_DESCRIPTIVE, "market_value_usd", "w"]
    return w[keep].rename(
        columns={"market_value_usd": f"value_{suffix}", "w": f"weight_{suffix}"}
    )


def diff(
    book: Book, client_id: str, date_a: str, date_b: str
) -> pd.DataFrame:
    """Per instrument: value and weight at both dates, plus the deltas.

    An **outer** join. Positions appear and disappear — a structured note
    that settles between the two dates has no earlier row at all. An inner
    join would silently omit it, and in this book that note is the single
    most important position in the demo. So an instrument held at only one
    date appears with ``0.0`` at the other: never ``NaN``, never absent.
    """
    a = _side(book, client_id, date_a, "a")
    b = _side(book, client_id, date_b, "b")

    merged = a.merge(b, on="instrument_id", how="outer", suffixes=("_x", "_y"))

    # Coalesce the descriptive columns across the two sides.
    for col in _DESCRIPTIVE:
        left, right = f"{col}_x", f"{col}_y"
        if left in merged.columns:
            merged[col] = merged[left].fillna(merged[right])
            merged = merged.drop(columns=[left, right])

    for col in ("value_a", "value_b", "weight_a", "weight_b"):
        merged[col] = merged[col].fillna(0.0)

    merged["d_value"] = merged.value_b - merged.value_a
    merged["d_weight"] = merged.weight_b - merged.weight_a

    return (
        merged[_OUT]
        .sort_values("instrument_id")
        .reset_index(drop=True)
    )


def attribution(
    book: Book, client_id: str, date_a: str, date_b: str
) -> pd.DataFrame:
    """Who moved the portfolio. ``diff``, ordered by absolute value change.

    Same rows, same columns, different order. ``instrument_id`` breaks ties
    so the ordering is deterministic (Principle VII).
    """
    d = diff(book, client_id, date_a, date_b)
    return (
        d.assign(_abs=d.d_value.abs())
        .sort_values(["_abs", "instrument_id"], ascending=[False, True])
        .drop(columns="_abs")
        .reset_index(drop=True)
    )
