"""Spec 002 — unit assertions for claim extraction.

**Every test here is offline.** They exercise the parser, not the model.
Article VIII excludes model output quality from testing; what is tested is
that malformed or ungrounded output cannot become a finding.
"""

import json

from pipeline.claims import CHECKS, parse_claims

OBJECTIVES = "Build wealth outside the shipping sector; fund an office."
NOTES = [
    {
        "note_id": "N-999",
        "note_date": "2026-01-01",
        "note": "He said he would prefer something safe and boring.",
    }
]


def _parse(raw):
    return parse_claims(raw, OBJECTIVES, NOTES)


def test_malformed_output_returns_nothing():
    """Unit 1 — block 4: malformed output returns no findings, never throws.

    Four shapes, none of which may raise.
    """
    for raw in (
        "not json at all",
        "",
        '{"claim": "a dict not a list"}',
        '[1, 2, 3]',
    ):
        claims, rejected = _parse(raw)
        assert claims == [], raw
        assert rejected, "a rejection must be recorded, not silence"

    # Valid JSON, valid list, but the claims inside are junk. Well-formed
    # siblings must survive; junk must not.
    mixed = json.dumps(
        [
            {"no_check_key": True},
            {
                "claim": "outside the shipping sector",
                "check": "avoid_sector",
                "target": "shipping",
                "source": "objectives",
            },
        ]
    )
    claims, rejected = _parse(mixed)
    assert len(claims) == 1
    assert claims[0]["check"] == "avoid_sector"
    assert rejected


def test_quote_must_appear_in_source():
    """Unit 2 — Principle IV. The model may not invent what a client said.

    This is the guard that matters most in the whole build. A model asked
    to quote will occasionally paraphrase, and a paraphrase shown to a
    client as their own words is the worst failure this system could have.
    """
    fabricated = json.dumps(
        [
            {
                "claim": "I want to invest heavily in cryptocurrency",
                "check": "other",
                "target": None,
                "source": "objectives",
            }
        ]
    )
    claims, rejected = _parse(fabricated)
    assert claims == []
    assert any("not found in the source" in r for r in rejected)

    # A real quote from the note survives.
    genuine = json.dumps(
        [
            {
                "claim": "something safe and boring",
                "check": "reduce_risk",
                "target": None,
                "source": "N-999",
            }
        ]
    )
    claims, _ = _parse(genuine)
    assert len(claims) == 1


def test_unknown_check_becomes_other():
    """Unit 3 — drift reduces findings; it never produces wrong ones."""
    raw = json.dumps(
        [
            {
                "claim": "outside the shipping sector",
                "check": "sell_everything_immediately",
                "target": "shipping",
                "source": "objectives",
            }
        ]
    )
    claims, rejected = _parse(raw)
    assert len(claims) == 1
    assert claims[0]["check"] == "other"
    assert claims[0]["check"] in CHECKS
    assert any("coerced to 'other'" in r for r in rejected)


def test_fences_are_stripped():
    """Unit 4 — models fence JSON regardless of instruction."""
    inner = json.dumps(
        [
            {
                "claim": "outside the shipping sector",
                "check": "avoid_sector",
                "target": "Shipping",
                "source": "objectives",
            }
        ]
    )
    for raw in (f"```json\n{inner}\n```", f"```\n{inner}\n```"):
        claims, _ = _parse(raw)
        assert len(claims) == 1, raw
        # Targets are normalised to lowercase so the seed match is
        # case-independent.
        assert claims[0]["target"] == "shipping"


def test_target_required_checks_are_dropped_without_one():
    """A check that needs a target and has none is meaningless."""
    raw = json.dumps(
        [
            {
                "claim": "outside the shipping sector",
                "check": "avoid_sector",
                "target": None,
                "source": "objectives",
            }
        ]
    )
    claims, rejected = _parse(raw)
    assert claims == []
    assert any("no target" in r for r in rejected)


def test_unknown_source_is_not_cited():
    """An ungrounded citation is worse than none (Principle IV)."""
    raw = json.dumps(
        [
            {
                "claim": "something safe and boring",
                "check": "reduce_risk",
                "target": None,
                "source": "N-000-does-not-exist",
            }
        ]
    )
    claims, rejected = _parse(raw)
    assert len(claims) == 1
    assert claims[0]["source"] == "objectives"
    assert any("unknown source" in r for r in rejected)


def test_parsing_is_deterministic():
    """Same model text, same claims, same order (Principle VII)."""
    raw = json.dumps(
        [
            {
                "claim": "something safe and boring",
                "check": "reduce_risk",
                "target": None,
                "source": "N-999",
            },
            {
                "claim": "outside the shipping sector",
                "check": "avoid_sector",
                "target": "shipping",
                "source": "objectives",
            },
        ]
    )
    assert _parse(raw)[0] == _parse(raw)[0]
