"""Spec 000 — unit assertion for the two-date comparison."""

from pipeline.load import client_weights, snapshots
from pipeline.diff import attribution, diff
from tests.conftest import HERO, HERO_NOTE


def test_appearing_and_disappearing_positions(book):
    """Unit 6 — an outer join, zero-filled, nothing dropped.

    The structured note settles between these two dates, so it has no
    earlier row at all. An inner join would silently omit the single most
    important position in the demo — exactly the class of error spec 000
    exists to prevent.
    """
    s = snapshots(book)
    then, now = s[1], s[-1]

    d = diff(book, HERO, then, now)

    note = d[d.instrument_id == HERO_NOTE]
    assert len(note) == 1, "exactly once, not duplicated by the outer join"
    row = note.iloc[0]

    # 0.0, not NaN and not a missing row.
    assert row.value_a == 0.0
    assert row.weight_a == 0.0
    assert row.value_b > 0
    assert row.d_value == row.value_b

    # The name survives from whichever date carries it, so an evidence
    # panel can render a position that did not exist at the earlier date.
    assert isinstance(row.instrument_name, str) and row.instrument_name

    # Every instrument held at either date, exactly once.
    union = set(client_weights(book, HERO, then).instrument_id) | set(
        client_weights(book, HERO, now).instrument_id
    )
    assert set(d.instrument_id) == union
    assert len(d) == len(union)

    # No NaN survives anywhere in the numeric columns.
    numeric = ["value_a", "value_b", "weight_a", "weight_b", "d_value", "d_weight"]
    assert not d[numeric].isna().any().any()

    # attribution: same rows, ordered by absolute value change.
    a = attribution(book, HERO, then, now)
    assert set(a.instrument_id) == union
    assert len(a) == len(d)
    magnitudes = a.d_value.abs().tolist()
    assert magnitudes == sorted(magnitudes, reverse=True)
