"""Spec 000 — which events touched a client.

``event_log.csv`` is authoritative for anything that happened. Where a
model's recollection and the file disagree, the file wins (Principle IV).
So these functions carry event rows through unmodified, and the decision
about which events are relevant is a keyword match in code — never a
question put to a model, because the answer has to be the same tomorrow.

Contract: ``specs/000-data-layer/contracts/data-layer.md``
"""

from __future__ import annotations

import pandas as pd

from pipeline.load import Book

# Columns of event_log.csv whose values are carried through untouched.
_EVENT_COLS = [
    "event_date",
    "event_type",
    "region",
    "description",
    "primary_transmission",
    "severity",
]

# Holdings columns that describe what a client is exposed to, in the
# vocabulary the event log's transmission channels use.
_EXPOSURE_COLS = ("sector", "sub_asset_class")

# Below this length a term must match exactly. Bidirectional substring
# containment on very short tokens invites accidents — "multi" inside
# "multi-asset something" would be a plausible one. Against this data the
# floor is unexercised (research.md R5 enumerates all 1,189 pairs; six
# match, five of them exactly), and it is kept because that enumeration is
# a property of this dataset and not of the next one.
_MIN_SUBSTRING_LEN = 4


def events_between(book: Book, date_a: str, date_b: str) -> pd.DataFrame:
    """Events in the inclusive range, date-ordered, fields unmodified.

    ISO date strings compare correctly, so no parsing is needed. The dates
    need not be snapshot dates — events are not snapshotted.
    """
    lo, hi = sorted([date_a, date_b])
    e = book.events
    window = e[(e.event_date >= lo) & (e.event_date <= hi)]
    return (
        window.sort_values(["event_date", "description"])
        .reset_index(drop=True)
    )


def _terms(values) -> list[str]:
    """Normalise free text to a sorted list of comparable terms.

    Sorted, so nothing downstream depends on frame or set iteration order
    (Principle VII).
    """
    out = set()
    for v in values:
        if pd.isna(v):
            continue
        for part in str(v).split(","):
            t = part.strip().lower()
            if t:
                out.add(t)
    return sorted(out)


def exposure_terms(book: Book, client_id: str) -> list[str]:
    """What this client is exposed to, in the event log's vocabulary.

    Taken across every snapshot rather than the latest one: an event in
    March is relevant to a position held in March, whether or not it is
    still held today.
    """
    held = book.holdings[book.holdings.client_id == client_id]
    values = []
    for col in _EXPOSURE_COLS:
        values.extend(held[col].tolist())
    return _terms(values)


def _matches(term: str, channel: str) -> bool:
    """Does one exposure term match one transmission channel?"""
    if len(term) < _MIN_SUBSTRING_LEN or len(channel) < _MIN_SUBSTRING_LEN:
        return term == channel
    return term in channel or channel in term


def events_touching(
    book: Book, client_id: str, date_a: str, date_b: str
) -> pd.DataFrame:
    """Events whose transmission channels name something the client holds.

    Adds ``matched_on``: the matching terms, sorted and comma-joined. It
    exists so an evidence panel can state *why* an event was surfaced, and
    so the relationship manager can reject a match she disagrees with
    (Principle IX).

    An event matching nothing is excluded. Absence of a match is a real
    answer, not a gap to be filled.

    **This match is narrow, not loose.** On this data it has effectively no
    false positives and several false negatives: a transmission channel
    naming an activity matches nothing when the holdings that do that
    activity are booked under a broader sector heading. The honest
    description is "events whose transmission
    channels name an asset class or sector this client holds", not "every
    event that touches this client". Recorded in research.md R5 rather than
    hidden, because a false positive is visible and rejectable while a
    false negative silently loses the cause of a finding.
    """
    window = events_between(book, date_a, date_b)
    if window.empty:
        return window.assign(matched_on=pd.Series(dtype="object"))

    terms = exposure_terms(book, client_id)

    rows, matched = [], []
    for _, event in window.iterrows():
        channels = _terms([event.primary_transmission])
        hits = sorted(
            {t for t in terms for c in channels if _matches(t, c)}
        )
        if hits:
            rows.append(event)
            matched.append(", ".join(hits))

    if not rows:
        return window.iloc[0:0].assign(matched_on=pd.Series(dtype="object"))

    out = pd.DataFrame(rows).reset_index(drop=True)
    out["matched_on"] = matched
    return out[[*_EVENT_COLS, "matched_on"]]
