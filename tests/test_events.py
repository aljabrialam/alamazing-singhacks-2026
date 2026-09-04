"""Spec 000 — unit assertions for event selection.

`event_log.csv` is authoritative. These assertions check that what comes
back is what the file said, and that the match which decides relevance is
reproducible rather than judged (Principle IV).
"""

from pipeline.load import snapshots
from pipeline.events import events_between, events_touching
from tests.conftest import BLOCKADE_REIMPOSED, HERO, STRAIT_CLOSED


def test_events_between_inclusive_and_ordered(book):
    """Unit 7 — inclusive at both ends, date-ordered, fields untouched."""
    dates = sorted(book.events.event_date)
    lo, hi = dates[0], dates[-1]

    every = events_between(book, lo, hi)
    assert len(every) == len(book.events), "inclusive at both ends"
    assert every.event_date.tolist() == sorted(every.event_date.tolist())

    # A single-day range returns that day's events, not none.
    one = events_between(book, STRAIT_CLOSED, STRAIT_CLOSED)
    assert len(one) >= 1
    assert set(one.event_date) == {STRAIT_CLOSED}

    # Values are carried through from the file unmodified.
    source = book.events[book.events.event_date == STRAIT_CLOSED].iloc[0]
    assert one.iloc[0].description == source.description
    assert one.iloc[0].severity == source.severity


def test_events_touching_hero_client(book):
    """Unit 8 — the two events the hero's causal chain depends on.

    2026-03-04, the Strait of Hormuz effectively closed. 2026-08-05, the
    naval blockade reimposed. Both must be returned, and both must resolve
    to a row of event_log.csv (Principle IV).
    """
    s = snapshots(book)
    touching = events_touching(book, HERO, s[1], s[-1])

    returned = set(touching.event_date)
    assert STRAIT_CLOSED in returned
    assert BLOCKADE_REIMPOSED in returned

    # Every returned event resolves to a real row, by date and description.
    source = {
        (r.event_date, r.description) for _, r in book.events.iterrows()
    }
    for _, event in touching.iterrows():
        assert (event.event_date, event.description) in source

    # matched_on is populated on every row, so the evidence panel can say
    # why the event is there and Priscilla can reject a match she
    # disagrees with (Principle IX).
    assert touching.matched_on.notna().all()
    assert (touching.matched_on.str.len() > 0).all()

    # The selection discriminates. Events touching exposures he does not
    # hold — European fixed income, US technology, duration — are excluded.
    window = events_between(book, s[1], s[-1])
    assert len(touching) < len(window)


def test_unmatched_events_are_excluded(book):
    """Absence of a match is a real answer, not a gap to be filled."""
    s = snapshots(book)
    touching = events_touching(book, HERO, s[1], s[-1])
    window = events_between(book, s[1], s[-1])

    excluded = set(window.event_date) - set(touching.event_date)
    assert excluded, "some events must not match, or the filter does nothing"
