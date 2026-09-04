"""Spec 001 — look-through concentration.

Carries three of the six assertions Article VIII names as non-negotiable:
`test_lookthrough_cl0019`, `test_lookthrough_cl0014` and the
compliance-clean assertion.

Every integration figure cites `.alamazing/findings.md`, which records how
it was computed. Asserted with tolerance, never equality.
"""

import pandas as pd
import pytest

from pipeline.load import latest, snapshots
from pipeline.divergence import d3_hidden as d3
from tests.conftest import (
    BREACHED_CLIENT,
    GOLDEN_HARBOUR,
    GOLDEN_HARBOUR_CLIENT,
    HERO,
    HERO_DUPLICATES,
    HERO_EXPOSURE,
    HERO_NOTE,
    HERO_TRAJECTORY,
)

# .alamazing/findings.md § 1 Abdullah Al-Mansoori — The exposure.
RECORDED_HERO_PCT = 42.134
# .alamazing/findings.md § 3 Lau Chi Ming — One name, three instruments.
RECORDED_GOLDEN_HARBOUR_PCT = 29.46


def _one(findings, rule):
    matching = [f for f in findings if f["rule"] == rule]
    assert len(matching) == 1, (rule, [f["rule"] for f in findings])
    return matching[0]


# --- integration assertions ----------------------------------------------


def test_lookthrough_cl0019(book):
    """Integration 1 — the hero figure. Named in Article VIII.

    42.13% of the portfolio in shipping and energy, visible only after
    looking through the structured note to the names it references.
    """
    finding = _one(d3.detect(book, HERO), d3.SECTOR_RULE)

    assert finding["theme_pct"] == pytest.approx(RECORDED_HERO_PCT, abs=0.001)

    # The four instruments findings.md names, and only those.
    assert set(m["instrument_id"] for m in finding["members"]) == set(
        HERO_EXPOSURE
    )

    # Spread across asset classes, which is why it does not read as
    # concentration on a statement.
    assert len(finding["asset_classes"]) > 1

    # The theme name is derived from the data, not written in the module.
    assert finding["theme"] and finding["kind"] == "D3"


def test_lookthrough_cl0014(book):
    """Integration 2 — one name, three asset classes. Named in Article VIII.

    The better technical demonstration: a single company held as a bond,
    an equity and a structured product, so each line sits under a
    different limit and no concentration check sees the whole position.
    """
    finding = _one(d3.detect(book, GOLDEN_HARBOUR_CLIENT), d3.ISSUER_RULE)

    assert finding["theme_pct"] == pytest.approx(
        RECORDED_GOLDEN_HARBOUR_PCT, abs=0.01
    )

    assert set(m["instrument_id"] for m in finding["members"]) == set(
        GOLDEN_HARBOUR
    )

    # Three *different* booked asset classes. This is the whole point.
    assert len(finding["asset_classes"]) == 3

    # Individual weights, findings.md § 3.
    weights = {m["instrument_id"]: m["w"] for m in finding["members"]}
    assert weights["SYN-FI-0207"] == pytest.approx(12.87, abs=0.01)
    assert weights["SYN-ST-0106"] == pytest.approx(9.54, abs=0.01)
    assert weights["SYN-SP-0503"] == pytest.approx(7.05, abs=0.01)


def test_compliance_clean_cl0019(book):
    """Integration 3 — every control passed, and still 42% one bet.

    findings.md § 1, Why nothing flags it. This is the strongest line in
    the pitch, so the flag is asserted against all five bands and the
    single-position limit rather than taken on trust.
    """
    findings = d3.detect(book, HERO)
    assert findings, "the hero client must produce findings"

    for finding in findings:
        assert finding["compliance_clean"] is True

    bands = {b["asset_class"]: b for b in findings[0]["compliance_bands"]}

    # findings.md § 1 — the five bands, all respected.
    expected = {
        "Equity": 57.97,
        "Fixed Income": 15.67,
        "Structured Products": 12.90,
        "Cash and Equivalents": 7.45,
        "Alternatives": 6.00,
    }
    for asset_class, actual in expected.items():
        assert bands[asset_class]["actual_pct"] == pytest.approx(
            actual, abs=0.01
        ), asset_class
        assert bands[asset_class]["verdict"] == "within", asset_class

    # No single position breaches. findings.md records 13.30 against 15.
    largest = findings[0]["largest_position"]
    assert largest["actual_pct"] == pytest.approx(13.30, abs=0.01)
    assert largest["actual_pct"] < largest["limit_pct"]


def test_duplicate_underlying_cl0019(book):
    """Integration 4 — the note doubles up on names he already owns.

    Block 3 acceptance: the duplicate underlying names SYN-ST-0104 and
    SYN-EQ-0008. This is what makes the concentration explicable rather
    than merely true.
    """
    finding = _one(d3.detect(book, HERO), "duplicate_underlying")

    assert set(finding["duplicated_instrument_ids"]) == set(HERO_DUPLICATES)
    assert finding["referencing_instrument_id"] == HERO_NOTE

    # Both sides carried as evidence: the reference itself, and the rows.
    files = {e["file"] for e in finding["evidence"]}
    assert "instruments.csv" in files and "holdings.csv" in files

    # Never sold as diversification (FR-008).
    assert "diversif" not in finding["detail"].lower()


def test_trajectory_cl0019(book):
    """Integration 5 — how it got here.

    findings.md § 1, Trajectory. Membership is fixed as resolved today and
    measured backwards, so the history is visible rather than starting at
    zero before the note settled.
    """
    finding = _one(d3.detect(book, HERO), d3.SECTOR_RULE)
    got = [point["pct"] for point in finding["trajectory"]]

    assert len(got) == len(snapshots(book))
    for actual, recorded in zip(got, HERO_TRAJECTORY):
        assert actual == pytest.approx(recorded, abs=0.01)

    # Monotonically rising, which is the story: appreciation through the
    # March spike, then a step change when the note settled.
    assert got == sorted(got)


# --- unit assertions ------------------------------------------------------


def test_reference_parsing(book):
    """Unit 3 — names recovered from both places they hide.

    Block 3 describes only the underlying reference. That is incomplete:
    CL-0014's accumulator names its issuer only in the instrument name.
    See research.md R6.
    """
    instruments = book.instruments.set_index("instrument_id")

    # Shape 1 — a named basket in the reference.
    basket = d3.referenced_names(instruments.loc[HERO_NOTE])
    assert "Pacific Orient Shipping" in basket
    assert "Global Energy Majors ADR" in basket
    assert "Bara Nusantara Energy" in basket

    # Shape 2 — the issuer only in the instrument name. The reference
    # carries strike and knock-out mechanics and no name at all.
    accumulator = instruments.loc["SYN-SP-0503"]
    assert "Golden Harbour" not in str(accumulator.underlying_reference)
    assert any(
        "Golden Harbour" in n for n in d3.referenced_names(accumulator)
    ), "the issuer must be recovered from instrument_name"

    # Shape 3 — a reference naming a category, not an issuer. Degrades to
    # whatever the name yields; never raises.
    assert isinstance(
        d3.referenced_names(instruments.loc["SYN-SP-0506"]), list
    )


def test_unresolved_references_are_recorded_not_dropped(book):
    """Unit 4 — Principle X. What could not be resolved is stated.

    The hero's basket references Bara Nusantara Energy, which he does not
    hold. That fact belongs in `unsure_about`, not in silence.
    """
    findings = d3.detect(book, HERO)
    unsure = " ".join(f["unsure_about"] for f in findings)
    assert "Bara Nusantara" in unsure


def test_no_double_counting_in_any_theme(book):
    """Unit 5 — swept across every client and every snapshot.

    A structured product contributing its weight once per referenced name
    would inflate every figure plausibly — the same class of error as spec
    000's weight_pct trap. Revised SC-006: themes overlap by design, so
    the invariant is no instrument twice *within* a theme, and no theme
    over 100%.
    """
    for client_id in sorted(book.clients.client_id):
        for date in snapshots(book):
            resolved = d3.look_through(book, client_id, date)
            if resolved.empty:
                continue
            for column in ("theme_sector", "theme_issuer"):
                for label in resolved[column].dropna().unique():
                    members = resolved[resolved[column] == label]
                    assert len(members) == members.instrument_id.nunique(), (
                        client_id,
                        date,
                        label,
                    )
                    assert members.w.sum() <= 100.0001, (
                        client_id,
                        date,
                        label,
                    )


def test_compliance_clean_is_earned(book):
    """Unit 6 — a flag that defaults to true is worthless.

    Margarethe's portfolio breaches its equity ceiling, its fixed-income
    floor and its single-position limit. Anything reported for her must
    carry compliance_clean False.
    """
    findings = d3.detect(book, BREACHED_CLIENT)
    for finding in findings:
        assert finding["compliance_clean"] is False


def test_detector_runs_for_every_client(book):
    """SC-011 — general, not fitted to three clients.

    No client is named in the module. Every client in the book goes
    through the same code, and most correctly produce nothing.
    """
    produced = {}
    for client_id in sorted(book.clients.client_id):
        findings = d3.detect(book, client_id)
        produced[client_id] = len(findings)
        for finding in findings:
            # Principle VI — no finding without evidence.
            assert finding["evidence"]
            assert finding["evidence"][0]["rows"]
            # Principle IX — never the word "recommend".
            assert "recommend" not in finding["headline"].lower()
            assert "recommend" not in finding["detail"].lower()

    assert produced[HERO] > 0
    assert produced[GOLDEN_HARBOUR_CLIENT] > 0
    # Selective: most clients hold no structured product at all, so the
    # look-through is correctly silent for them.
    assert sum(1 for n in produced.values() if n == 0) >= 10


def test_findings_are_deterministic(book):
    """Principle VII — same inputs, same findings, same order."""
    assert d3.detect(book, HERO) == d3.detect(book, HERO)
    assert d3.detect(book, GOLDEN_HARBOUR_CLIENT) == d3.detect(
        book, GOLDEN_HARBOUR_CLIENT
    )


def test_threshold_is_a_parameter(book):
    """Principle XI — "what about 20%?" is answered by typing.

    The threshold is an argument with a default, not a literal, so a judge
    asking to move it gets an answer on stage.
    """
    at_25 = d3.detect(book, HERO, threshold_pct=25.0)
    at_95 = d3.detect(book, HERO, threshold_pct=95.0)

    concentration_at_95 = [
        f for f in at_95 if f["rule"] in (d3.SECTOR_RULE, d3.ISSUER_RULE)
    ]
    assert not concentration_at_95, "nothing should clear a 95% threshold"
    assert len(at_25) > len(concentration_at_95)
