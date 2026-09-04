"""Spec 002 — D1, what he said against what he holds.

Every bank checks a portfolio against its mandate. Nobody checks it against
what the client **said**, because what they said lives in prose no risk
system reads.

One client's mandate says equity 40–65 and is monitored daily. His stated
objective says he wants wealth *outside* a particular region and *outside*
a particular sector. It was typed at onboarding and, on the evidence of his
portfolio, never looked at again.

**This module contains no model client and must never acquire one.**
`claims.py` did the reading; this file does the testing, in pandas. The
model never sees a figure and never decides whether a claim is violated —
that separation is the architecture, and it is what makes the answer the
same tomorrow.

Contract: ``specs/002-said-vs-held/contracts/said-vs-held.md``
"""

from __future__ import annotations

import pandas as pd

from pipeline.claims import provenance_for, rejections_for
from pipeline.load import Book, latest
from pipeline.mandate import WITHIN, compliance_verdict
from pipeline.divergence.d3_hidden import look_through

KIND = "D1"

# Above this share of client value, a contradicted claim is worth raising.
# A parameter, not a literal (Principle XI).
DEFAULT_THRESHOLD_PCT = 20.0

# Where a target may legitimately be found. **Source fields only.**
#
# `theme_sector` and `theme_issuer` are deliberately excluded. Matching
# against them also reaches the recorded figure, but only because a label
# this pipeline *wrote* happens to contain the target word — the exposure
# would be pulled in by our own string rather than by the bank's data.
# That is circular, it breaks the moment a label is reworded, and the
# wrong version passes the acceptance test. See research.md R4.
_SEED_FIELDS = (
    "instrument_name",
    "sector",
    "sub_asset_class",
    "underlying_reference",
)

# Checks this module knows how to test. Others are carried through to the
# findings' context but tested elsewhere or not at all.
_AVOIDANCE = ("avoid_sector", "avoid_region")


def _seeds(resolved: pd.DataFrame, target: str) -> pd.DataFrame:
    """Holdings that mention the target in the bank's own fields."""
    needle = str(target).strip().lower()
    if not needle:
        return resolved.iloc[0:0]

    def mentions(row) -> bool:
        return any(
            needle in str(row[field]).lower()
            for field in _SEED_FIELDS
            if field in row.index
        )

    return resolved[resolved.apply(mentions, axis=1)]


def exposure_to(book: Book, client_id: str, target: str, date: str) -> dict:
    """How exposed is this client to something they said they'd avoid?

    Two figures, both reported, because reporting only the second invites
    "how is an energy fund shipping?" and reporting only the first
    understates the position:

        direct        the positions that name the target
        look_through  the whole theme those positions sit inside, once
                      structured products are resolved to what they
                      reference (spec 001)
    """
    resolved = look_through(book, client_id, date)
    if resolved.empty:
        return {
            "direct_pct": 0.0,
            "look_through_pct": 0.0,
            "themes": [],
            "direct_ids": [],
            "look_through_ids": [],
        }

    seeds = _seeds(resolved, target)
    if seeds.empty:
        return {
            "direct_pct": 0.0,
            "look_through_pct": 0.0,
            "themes": [],
            "direct_ids": [],
            "look_through_ids": [],
        }

    themes = sorted(set(seeds.theme_sector.dropna()))
    expanded = resolved[
        resolved.theme_sector.isin(themes)
        | resolved.instrument_id.isin(seeds.instrument_id)
    ]

    return {
        "direct_pct": float(seeds.w.sum()),
        "look_through_pct": float(expanded.w.sum()),
        "themes": themes,
        "direct_ids": sorted(seeds.instrument_id),
        "look_through_ids": sorted(expanded.instrument_id),
        "rows": expanded,
    }


def _quote_evidence(book: Book, client_id: str, claim: dict) -> list[dict]:
    """Where the client said it. Objectives, or a note by its id."""
    source = claim.get("source")
    if source == "objectives":
        return [
            {
                "file": "clients.csv",
                "rows": [client_id],
                "note": f'stated objective: "{claim["claim"]}"',
            }
        ]

    # A note id. Verified against rm_notes.json — Principle IV requires
    # every citation to resolve to a real row.
    note = next(
        (n for n in book.notes_for(client_id) if n.get("note_id") == source),
        None,
    )
    if note is None:
        return []
    return [
        {
            "file": "rm_notes.json",
            "rows": [source],
            "note": (
                f'{note.get("note_date")} ({note.get("channel")}): '
                f'"{claim["claim"]}"'
            ),
        }
    ]


def _holdings_evidence(rows: pd.DataFrame) -> dict:
    return {
        "file": "holdings.csv",
        "rows": sorted(rows.instrument_id.tolist()),
        "note": "; ".join(
            f"{r.instrument_id} {r.instrument_name} {r.w:.2f}%"
            for _, r in rows.sort_values("w", ascending=False).iterrows()
        ),
    }


def detect(
    book: Book,
    client_id: str,
    date: str | None = None,
    threshold_pct: float = DEFAULT_THRESHOLD_PCT,
) -> list[dict]:
    """Findings where the portfolio contradicts something the client said.

    Reads the committed claims. **Makes no model call** — the claims were
    extracted at build time and committed (Principle VII), so this runs
    with no API key and no network.
    """
    date = date or latest(book)
    claims = _claims_for(book, client_id)
    if not claims:
        return []

    verdict = compliance_verdict(book, client_id, date)
    unsure = _unsure(client_id)
    findings: list[dict] = []
    checked_clear: list[dict] = []
    carried_untested: list[dict] = []

    # Several claims can contradict the same thing. Margarethe says three
    # separate times that she wants less risk; reporting one breach three
    # times is noise, and it buries the fact that she said it three ways.
    # So claims are grouped by what they contradict, and every supporting
    # quote travels with the one finding.
    risk_claims: list[dict] = []

    for claim in claims:
        if claim["check"] in _AVOIDANCE:
            finding = _test_avoidance(
                book, client_id, date, claim, threshold_pct, verdict, unsure
            )
            if finding:
                findings.append(finding)
            else:
                checked_clear.append(
                    {"claim": claim["claim"], "check": claim["check"]}
                )
        elif claim["check"] == "reduce_risk":
            risk_claims.append(claim)
        else:
            # needs_liquidity_by and refuse_realise_loss are extracted and
            # carried, but liquidity belongs to spec 004. Recorded rather
            # than dropped so nothing the client said disappears silently
            # (Principle X).
            carried_untested.append(
                {"claim": claim["claim"], "check": claim["check"]}
            )

    if risk_claims:
        finding = _test_reduce_risk(
            risk_claims, verdict, client_id, book, unsure
        )
        if finding:
            findings.append(finding)
        else:
            checked_clear.extend(
                {"claim": c["claim"], "check": c["check"]} for c in risk_claims
            )

    for finding in findings:
        finding["checked_and_clear"] = checked_clear
        finding["carried_untested"] = carried_untested

    return sorted(
        findings,
        key=lambda f: (-f.get("look_through_pct", 0.0), f["headline"]),
    )


def _claims_for(book: Book, client_id: str) -> list[dict]:
    from pipeline.claims import extract_claims

    # refresh defaults to False, so this reads the committed cache and
    # makes no call. The import is local to keep the module-level
    # namespace free of anything model-shaped.
    return extract_claims(book.client(client_id), book.notes_for(client_id))


def _unsure(client_id: str) -> str:
    rejected = rejections_for(client_id)
    parts = [f"Claims produced by {provenance_for(client_id)}."]
    if rejected:
        parts.append(
            "Discarded during extraction: " + "; ".join(rejected) + "."
        )
    return " ".join(parts)


def _test_avoidance(
    book: Book,
    client_id: str,
    date: str,
    claim: dict,
    threshold_pct: float,
    verdict: dict,
    unsure: str,
) -> dict | None:
    """Did they say avoid it, and do they hold it? Tested in code."""
    target = claim.get("target")
    if not target:
        return None

    exposure = exposure_to(book, client_id, target, date)
    if exposure["look_through_pct"] <= threshold_pct:
        return None

    evidence = _quote_evidence(book, client_id, claim)
    if not evidence:
        # Principle VI — no evidence, no finding.
        return None
    evidence.append(_holdings_evidence(exposure["rows"]))

    kind_word = "sector" if claim["check"] == "avoid_sector" else "region"
    direct = exposure["direct_pct"]
    through = exposure["look_through_pct"]

    detail = (
        f'The client said: "{claim["claim"]}". '
        f"{direct:.2f}% of the portfolio names {target} directly. "
        f"Once the structured product is resolved to the names it "
        f"references, the exposure those positions sit inside is "
        f"{through:.2f}% — {', '.join(exposure['themes']) or target}. "
    )
    if verdict["clean"]:
        detail += (
            "Every mandate band is respected, so no existing control "
            "raises this. The mandate is monitored; what the client said "
            "is not. It may be worth raising."
        )
    else:
        detail += "This sits alongside a mandate breach, reported separately."

    return {
        "client_id": client_id,
        "kind": KIND,
        "check": claim["check"],
        "severity": 5 if through >= 40 else 4,
        "confidence": "high",
        "headline": (
            f'Client asked for exposure outside {target}; '
            f'the portfolio holds {through:.2f}% in that {kind_word}.'
        ),
        "detail": detail,
        "claim": claim,
        "target": target,
        "direct_pct": direct,
        "look_through_pct": through,
        "themes": exposure["themes"],
        "stated_on": claim.get("stated_on"),
        "compliance_clean": verdict["clean"],
        "evidence": evidence,
        "events": [],
        "unsure_about": unsure,
        "classification": None,
    }


def _test_reduce_risk(
    claims: list[dict], verdict: dict, client_id: str, book: Book, unsure: str
) -> dict | None:
    """They asked for less risk. Does the mandate check agree they have it?

    The test is the band verdict from `mandate.py` — a comparison in code,
    never a model's judgement about whether a portfolio feels risky.

    Takes **all** of the client's risk-reduction claims and emits one
    finding carrying every quote. Someone who says three separate times
    that they have never taken a risk with money has not made three
    findings; they have made one point, three times, and that repetition
    is itself the evidence.
    """
    breached = [b for b in verdict["bands"] if b["verdict"] != WITHIN]
    if not breached:
        return None

    evidence: list[dict] = []
    for claim in claims:
        evidence.extend(_quote_evidence(book, client_id, claim))
    if not evidence:
        return None

    claim = claims[0]
    evidence.append(
        {
            "file": "mandates.csv",
            "rows": sorted({b["mandate_code"] for b in breached}),
            "note": "; ".join(
                f'{b["asset_class"]} {b["actual_pct"]:.2f}% against '
                f'{b["min_pct"]:.0f}-{b["max_pct"]:.0f} ({b["verdict"]})'
                for b in breached
            ),
        }
    )

    worst = max(breached, key=lambda b: abs(b["actual_pct"] - b["target_pct"]))

    return {
        "client_id": client_id,
        "kind": KIND,
        "check": claim["check"],
        "severity": 5,
        "confidence": "high",
        "headline": (
            f'Client asked for less risk; {worst["asset_class"]} is at '
            f'{worst["actual_pct"]:.2f}% against a '
            f'{worst["min_pct"]:.0f}-{worst["max_pct"]:.0f} band.'
        ),
        "detail": (
            (
                f"The client said: "
                + "; ".join(f'"{c["claim"]}"' for c in claims)
                + ". "
            )
            + f"The portfolio breaches "
            f"{len(breached)} mandate "
            f"{'band' if len(breached) == 1 else 'bands'}: "
            + "; ".join(
                f'{b["asset_class"]} at {b["actual_pct"]:.2f}% against '
                f'{b["min_pct"]:.0f}-{b["max_pct"]:.0f}'
                for b in breached
            )
            + ". What they asked for and what they hold point in opposite "
            "directions. It may be worth raising before anything is sold."
        ),
        "claim": claim,
        "supporting_claims": claims,
        "direct_pct": None,
        "target": None,
        "look_through_pct": float(worst["actual_pct"]),
        "stated_on": claim.get("stated_on"),
        "compliance_clean": verdict["clean"],
        "breached_bands": breached,
        "evidence": evidence,
        "events": [],
        "unsure_about": unsure,
        "classification": None,
    }
