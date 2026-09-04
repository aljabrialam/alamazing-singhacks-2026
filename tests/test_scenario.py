"""Spec 005 — D6, the scenario.

Carries `test_scenario_cl0019`, the last of the six assertions Article
VIII names.
"""

import pytest

from pipeline.load import latest, snapshots
from pipeline.divergence import d6_scenario as d6
from tests.conftest import HERO, HERO_EXPOSURE, HERO_NOTE

# The scenario the client actually asked about: Brent back to its
# pre-conflict level.
SERIES = "BRENT_USD_BBL"

# .alamazing/findings.md § 1, The scenario.
RECORDED_TOTAL_USD = -2_500_000
RECORDED_TOTAL_PCT = -7.8
RECORDED_POSITIONS = {
    "SYN-EQ-0025": -0.43,
    "SYN-ST-0104": -0.72,
    "SYN-EQ-0008": -0.54,
    "SYN-SP-0505": -0.82,
}


def _scenario(book):
    dates = snapshots(book)
    return d6.detect(book, HERO, SERIES, dates[-1], dates[1])[0]


def test_scenario_cl0019(book):
    """Integration — the answer to his question. Named in Article VIII.

    He asked what happens if the Strait reopens and normalises. Around
    2.5 million comes off the portfolio, on an outcome most people would
    call good news.
    """
    finding = _scenario(book)

    # SC-001.
    assert finding["total_impact_usd"] == pytest.approx(
        RECORDED_TOTAL_USD, abs=100_000
    )
    assert finding["total_impact_pct"] == pytest.approx(
        RECORDED_TOTAL_PCT, abs=0.2
    )

    # SC-002 — each position itemised, matching block 7's table.
    by_id = {p["instrument_id"]: p for p in finding["positions"]}
    assert set(by_id) == set(HERO_EXPOSURE)
    for instrument_id, expected_millions in RECORDED_POSITIONS.items():
        actual = by_id[instrument_id]["impact_usd"] / 1e6
        assert actual == pytest.approx(expected_millions, abs=0.01), (
            instrument_id
        )

    # SC-005 — the series is cited at both dates.
    scenario = finding["scenario"]
    assert scenario["series_id"] == SERIES
    assert scenario["value_now"] == pytest.approx(101.5, abs=0.01)
    assert scenario["value_then"] == pytest.approx(72.4, abs=0.01)

    assert finding["kind"] == "D6"
    assert "recommend" not in finding["detail"].lower()


def test_second_order_is_quoted_not_inferred(book):
    """SC-006 — his own words, cited by note id.

    The system must not reason that Gulf logistics implies charter rates
    implies earnings. It reports that *he said it* — N-025 records his own
    view that his operating business benefits from the same conditions.
    Principle IV; research.md R4.
    """
    finding = _scenario(book)
    second_order = finding["second_order"]
    assert second_order is not None

    assert "marine chartering" in second_order["source_of_wealth"]
    cited = [n["note_id"] for n in second_order["notes"]]
    assert "N-025" in cited

    # The quote appears in the copy, so the claim is his and not ours.
    assert "operating business benefits from the same conditions" in (
        finding["detail"]
    )

    # Both halves of the claim are evidenced.
    files = {e["file"] for e in finding["evidence"]}
    assert "clients.csv" in files
    assert "rm_notes.json" in files

    # Every cited note id resolves to a real row.
    valid = {
        n["note_id"]
        for cid in book.clients.client_id
        for n in book.notes_for(cid)
    }
    for note_id in cited:
        assert note_id in valid


def test_proxy_uses_the_worst_leg_held_and_reports_the_worse_one(book):
    """Unit — the note has no past, and the par-indexed price is a trap.

    Every structured product in this book is indexed to exactly 100.0 at
    the first snapshot, so the note carries a price for February although
    it was subscribed in April and first held in June. Repricing off that
    value looks right and captures none of the basket's ~20% fall — it
    gives -0.25m where the answer is -0.82m, and would report -6.04%
    instead of -7.80%. research.md, and the note in d6_scenario.

    So the gate is whether the client *held* it, not whether a price
    exists.
    """
    finding = _scenario(book)
    note_position = next(
        p for p in finding["positions"] if p["instrument_id"] == HERO_NOTE
    )

    # Proxied, and from the worse of the two legs he holds.
    assert note_position["proxied_from"] == "SYN-ST-0104"
    assert note_position["impact_usd"] / 1e6 == pytest.approx(-0.82, abs=0.01)

    # The par-indexed price exists — so this test would catch a
    # regression that started trusting it.
    dates = snapshots(book)
    par_price = book.instruments.set_index("instrument_id").loc[
        HERO_NOTE, f"price_{dates[1]}"
    ]
    assert par_price > 0, "the trap value is present in the data"

    # SC-003 — the substitution is recorded.
    assert "not held at" in finding["unsure_about"]
    assert "par-indexed" in finding["unsure_about"]

    # SC-004 — the strictly worse leg he does not hold is reported.
    assert finding["alternatives"]
    alternative = finding["alternative_total_impact_usd"]
    assert alternative / 1e6 == pytest.approx(-2.65, abs=0.02)
    assert "Bara" in finding["unsure_about"]
    assert "against the client" in finding["unsure_about"]


def test_reprices_from_prices_not_market_values(book):
    """Unit — market value embeds quantity; repricing is about price.

    The two ratios differ measurably on this data, so the choice is not
    academic.
    """
    dates = snapshots(book)
    now, then = dates[-1], dates[1]

    instruments = book.instruments.set_index("instrument_id")
    price_ratio = (
        instruments.loc["SYN-ST-0104", f"price_{then}"]
        / instruments.loc["SYN-ST-0104", f"price_{now}"]
    )

    from pipeline.load import client_weights

    value_ratio = (
        client_weights(book, HERO, then)
        .set_index("instrument_id")
        .loc["SYN-ST-0104", "market_value_usd"]
        / client_weights(book, HERO, now)
        .set_index("instrument_id")
        .loc["SYN-ST-0104", "market_value_usd"]
    )

    assert price_ratio != pytest.approx(value_ratio, abs=1e-6), (
        "the two ratios must differ, or this test proves nothing"
    )

    finding = _scenario(book)
    used = next(
        p for p in finding["positions"]
        if p["instrument_id"] == "SYN-ST-0104"
    )["ratio"]
    assert used == pytest.approx(price_ratio, abs=1e-9)


def test_dates_are_validated_and_order_independent(book):
    """Unit — a typo'd date raises; reversed arguments give one answer."""
    dates = snapshots(book)

    with pytest.raises(ValueError, match="not a snapshot"):
        d6.detect(book, HERO, SERIES, "1999-01-01", dates[1])

    forward = d6.detect(book, HERO, SERIES, dates[-1], dates[1])[0]
    reversed_args = d6.detect(book, HERO, SERIES, dates[1], dates[-1])[0]
    assert forward["total_impact_usd"] == pytest.approx(
        reversed_args["total_impact_usd"], abs=0.01
    )


def test_a_different_scenario_is_a_different_call(book):
    """SC-007 — Principle XI, demonstrated rather than asserted.

    "Would this work on other data?" is answered by typing a different
    series and two different dates.
    """
    dates = snapshots(book)
    brent = d6.detect(book, HERO, SERIES, dates[-1], dates[1])[0]
    rates = d6.detect(book, HERO, "UST_10Y_PCT", dates[-1], dates[2])[0]

    assert rates["scenario"]["series_id"] == "UST_10Y_PCT"
    assert rates["scenario"]["date_then"] == dates[2]
    # A different comparison date gives a different answer.
    assert rates["total_impact_usd"] != pytest.approx(
        brent["total_impact_usd"], abs=1_000
    )


def test_findings_are_deterministic(book):
    dates = snapshots(book)
    args = (HERO, SERIES, dates[-1], dates[1])
    assert d6.detect(book, *args) == d6.detect(book, *args)
