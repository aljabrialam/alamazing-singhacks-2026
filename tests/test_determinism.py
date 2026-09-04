"""Spec 006 — the build, and the test block 8 calls the only one that matters.

Two builds, identical output. But equal bytes passes trivially when every
model artifact is committed, so this file proves three things rather than
one:

    the output is byte-identical across runs
    the build makes NO model call — asserted with the key removed
    the written file carries the recorded figures

The third is the one that earns its place. **A deterministic build of the
wrong numbers is still deterministic.** See
``specs/006-briefs-build/research.md`` R5.
"""

import json

import pytest

from pipeline.brief import FORBIDDEN_VERB, _validated, grounded_dates, parse_brief
from pipeline.build import build, serialise
from tests.conftest import BREACHED_CLIENT, GOLDEN_HARBOUR_CLIENT, HERO

DEMO_CLIENTS = [HERO, BREACHED_CLIENT, GOLDEN_HARBOUR_CLIENT]

# The scenario the demo asks about. Named here, in tests/, because
# `pipeline/` may not name a market series (Principle XI).
SERIES = "BRENT_USD_BBL"


@pytest.fixture(scope="module")
def payload():
    """One build, reused. Writing is disabled — the test does not touch
    the committed artifact."""
    return build(SERIES, data_dir="data/", client_ids=DEMO_CLIENTS, write=False)


# --- end to end -----------------------------------------------------------


def test_findings_are_deterministic():
    """E2E 1 — two builds, byte-identical. Named in Article VIII.

    "A regulated advisory system cannot answer differently on different
    days." Asserted on the serialised bytes rather than the dicts, because
    the bytes are what ships.
    """
    first = build(SERIES, data_dir="data/", client_ids=DEMO_CLIENTS, write=False)
    second = build(SERIES, data_dir="data/", client_ids=DEMO_CLIENTS, write=False)

    assert serialise(first) == serialise(second)
    assert first == second


def test_build_makes_no_model_call_and_carries_the_figures(monkeypatch):
    """E2E 2 — determinism by construction, and the numbers are right.

    Removing the key would make any model call fail loudly. The build
    still completes and produces the same bytes, which proves the
    determinism comes from committed artifacts rather than from luck.

    Then the recorded figures are checked in the written structure — the
    assertion that catches a deterministic build of wrong numbers.
    """
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    with_key_removed = build(
        SERIES, data_dir="data/", client_ids=DEMO_CLIENTS, write=False
    )
    assert serialise(with_key_removed) == serialise(
        build(SERIES, data_dir="data/", client_ids=DEMO_CLIENTS, write=False)
    )

    clients = with_key_removed["clients"]

    # 42.134 — the spine, after serialisation.
    hero = clients[HERO]
    sector = next(
        f
        for f in hero["findings"]
        if f.get("kind") == "D3" and f.get("rule") == "sector"
    )
    assert sector["theme_pct"] == pytest.approx(42.134, abs=0.001)

    # compliance_clean — the strongest line in the pitch.
    assert hero["mandate_panel"]["clean"] is True
    assert len(hero["mandate_panel"]["bands"]) == 5

    # The inherited classification — the third class.
    equity = next(
        f
        for f in clients[BREACHED_CLIENT]["findings"]
        if f.get("kind") == "D2" and f.get("asset_class") == "Equity"
    )
    assert equity["classification"] == "inherited"
    assert equity["actual_pct"] == pytest.approx(71.46, abs=0.01)

    # The scenario — the answer to his question.
    scenario = next(f for f in hero["findings"] if f.get("kind") == "D6")
    assert scenario["total_impact_usd"] == pytest.approx(
        -2_500_000, abs=100_000
    )
    assert scenario["total_impact_pct"] == pytest.approx(-7.8, abs=0.2)

    # The unanswered question, which the scenario answers.
    assert any(f.get("kind") == "D5" for f in hero["findings"])


# --- the built file -------------------------------------------------------


def test_every_finding_validates_against_the_schema(payload):
    """SC-009 — the file the web layer reads is schema-valid."""
    schema = json.loads(
        open(
            "specs/001-divergence-engine/contracts/finding.schema.json"
        ).read()
    )
    kinds = set(schema["properties"]["kind"]["enum"])
    required = schema["required"]

    total = 0
    for client_id, client in payload["clients"].items():
        for finding in client["findings"]:
            total += 1
            assert finding["kind"] in kinds, (client_id, finding["kind"])
            for key in required:
                assert key in finding, (client_id, key)
            assert finding["evidence"], client_id
    assert total > 40, "the book should produce a substantial set"


def test_ranking_covers_every_client_and_is_not_by_size(payload):
    """SC-003, SC-004 — block 8: not by portfolio size."""
    call_list = payload["call_list"]

    ids = [entry["client_id"] for entry in call_list]
    assert len(ids) == payload["meta"]["client_count"] == 20
    assert len(set(ids)) == 20, "every client exactly once"

    ranks = [entry["rank"] for entry in call_list]
    assert ranks == list(range(1, 21))

    by_aum = sorted(call_list, key=lambda e: -e["aum_usd"])
    assert [e["client_id"] for e in by_aum] != ids, (
        "the order must differ from the order by AUM"
    )

    # Each entry carries one sentence of justification.
    assert all(entry["why"].strip() for entry in call_list)


def test_uncertainty_keeps_the_two_kinds_apart(payload):
    """FR-014 — data imperfections and method limits are different."""
    uncertainty = payload["uncertainty"]

    assert uncertainty["data_imperfections"], "spec 000 recorded ten"
    assert uncertainty["method_limits"], "the detectors record limits"

    kinds = {i["kind"] for i in uncertainty["data_imperfections"]}
    assert "missing_cost_basis" in kinds
    assert "stale_valuation" in kinds

    for limit in uncertainty["method_limits"]:
        assert limit["client_id"]
        assert limit["unsure_about"].strip()


def test_briefs_are_clean_and_cite_only_grounded_dates(book, payload):
    """SC-002, FR-003, FR-004."""
    valid = grounded_dates(book)

    for client_id in DEMO_CLIENTS:
        brief = payload["clients"][client_id]["brief"]
        assert brief, client_id
        assert 3 <= len(brief["paragraphs"]) <= 4, client_id
        assert brief["opening_line"].strip(), client_id

        body = " ".join(brief["paragraphs"]) + " " + brief["opening_line"]
        assert FORBIDDEN_VERB not in body.lower(), client_id

        import re

        for cited in re.findall(r"\b(\d{4}-\d{2}-\d{2})\b", body):
            assert cited in valid, (client_id, cited)

        # The opening line is not repeated as a final paragraph.
        assert brief["paragraphs"][-1].strip().strip('"') != (
            brief["opening_line"].strip().strip('"')
        )


def test_a_single_client_build_works():
    """SC-005 — "run it on someone else", answered by typing an id."""
    single = build(SERIES, data_dir="data/", client_ids=[HERO], write=False)
    assert single["meta"]["deep_clients"] == [HERO]
    assert HERO in {e["client_id"] for e in single["call_list"]}
    # The call list is still the whole book, ranked.
    assert len(single["call_list"]) == 20
    # And the other clients got the shallow pass.
    assert single["clients"][BREACHED_CLIENT]["depth"] == (
        "mandate_and_lookthrough"
    )


def test_unknown_client_fails_with_the_id_named():
    """FR-012, SC-010 — an empty entry for a typo would look like a
    client with nothing wrong."""
    with pytest.raises(ValueError, match="CL-9999"):
        build(SERIES, data_dir="data/", client_ids=["CL-9999"], write=False)


# --- unit -----------------------------------------------------------------


def test_brief_with_forbidden_verb_is_rejected(book):
    """Unit 1 — Principle IX. Rejected, never rewritten.

    Silently editing model output would make the committed artifact a
    fiction.
    """
    raw = json.dumps(
        {
            "paragraphs": ["a", "b", "c"],
            "opening_line": f"I would {FORBIDDEN_VERB} we talk.",
        }
    )
    parsed, rejections = parse_brief(raw, book)
    assert parsed is None
    assert any(FORBIDDEN_VERB in r for r in rejections)
    assert any("rejected rather than" in r for r in rejections)


def test_brief_date_references_are_checked(book):
    """Unit 2 — Principle IV, and the check that was wrong first time.

    A first version compared cited dates against `event_log.csv` alone and
    rejected three perfectly sourced briefs — for citing note dates,
    snapshot dates, and a tax instalment due date. The valid set is every
    date the data contains.
    """
    valid = grounded_dates(book)

    # A real event date, a real note date and a real snapshot date all
    # pass; a fabricated one does not.
    assert "2026-03-04" in valid, "the Strait closure"
    assert "2026-08-12" in valid, "the note that asks the question"
    assert "2026-02-27" in valid, "the pre-conflict snapshot"
    assert "1987-10-19" not in valid

    raw = json.dumps(
        {
            "paragraphs": ["On 2026-03-04 the Strait closed.", "b", "c"],
            "opening_line": "But on 1987-10-19 nothing happened here.",
        }
    )
    parsed, rejections = parse_brief(raw, book)
    assert parsed is not None, "an unsourced date is recorded, not fatal"
    assert any("1987-10-19" in r for r in rejections)
    assert not any("2026-03-04" in r for r in rejections)


def test_ranking_is_validated_not_trusted():
    """Unit 3 — a call list that quietly loses a client is the worst case.

    She would never know the client was missing. So omissions are
    appended deterministically, duplicates and unknown ids dropped, and
    every correction recorded.
    """
    every = ["CL-0001", "CL-0002", "CL-0003"]
    proposed = [
        {"client_id": "CL-0002", "why": "urgent"},
        {"client_id": "CL-0002", "why": "duplicate"},
        {"client_id": "CL-9999", "why": "does not exist"},
        {"client_id": "CL-0003", "why": f"I {FORBIDDEN_VERB} calling"},
    ]

    result = _validated(proposed, every, "fp", provenance="test")
    order = [e["client_id"] for e in result["order"]]

    assert order == ["CL-0002", "CL-0003", "CL-0001"]
    assert len(order) == len(set(order)) == 3

    # The forbidden verb is cleared from the justification, not shipped.
    justification = {e["client_id"]: e["why"] for e in result["order"]}
    assert justification["CL-0003"] == ""

    corrections = " ".join(result["corrections"])
    assert "duplicate" in corrections
    assert "CL-9999" in corrections
    assert "CL-0001" in corrections
    assert "forbidden verb" in corrections


def test_the_model_never_sees_a_raw_client_record(book):
    """Principle V — the model receives derived findings only.

    The summary passed to the brief is a whitelist, so a holdings
    identifier or a raw row cannot reach the prompt even if a detector
    starts carrying one.
    """
    from pipeline.brief import _finding_summary
    from pipeline.divergence import d3_hidden

    finding = d3_hidden.detect(book, HERO)[0]
    summary = _finding_summary(finding)

    assert "evidence" not in summary
    assert "members" not in summary
    assert "compliance_bands" not in summary
    assert summary["headline"] == finding["headline"]
