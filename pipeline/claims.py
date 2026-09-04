"""Spec 002 — prose into testable claims. The only model call in the system.

**This is the only file in the repository that imports a model client.**
That is the architecture, not an accident: `grep -rn "anthropic" pipeline/`
must match this file and nothing else. A second match means the wall
between reading and counting has been breached.

What the model does here: reads what a client said and returns it as a
structured claim, in the client's own words. What it does not do:
arithmetic, receive any figure, or decide whether a claim is violated.
Those happen in `divergence/d1_said.py`, in pandas.

Extraction runs at **build time** and the output is committed to
``derived/claims.json`` alongside the prompt that produced it. Nothing calls
a model at demo time (Principle VII), and a regulator asking "why did your
system say this" gets the same answer twice.

Two guards make fabrication structurally hard (Principle IV):

    the quote must appear verbatim in the source text, or the claim is
    dropped and the rejection recorded

    a check type outside the permitted set becomes `other`, which no code
    path tests

A model that drifts therefore produces *fewer* claims, never invented
ones.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

# Derived data, not code — so it lives outside ``pipeline/``. That keeps
# the Principle XI grep over the pipeline clean, and it is the honest
# classification: a cache of per-client claims is an artifact keyed by
# client id, in the same category as the findings file spec 006 writes,
# not a module that names a client.
CACHE_PATH = Path(__file__).parent.parent / "derived" / "claims.json"

MODEL = "claude-opus-5"

# Extraction against a fixed schema over ~600 words of prose. Low effort is
# the right setting and it is the lever that replaced temperature.
EFFORT = "low"

# The constitution's Technology Standards require temperature 0. **That is
# not achievable on any current model**: sampling parameters were removed
# from the Messages API, and passing `temperature` now returns a 400. So
# the requirement is met a different way, and the difference is recorded
# rather than glossed:
#
#   determinism at demo time comes from the committed cache, not from the
#   sampling parameter
#
# That is in fact the stronger guarantee. Temperature 0 reduces variance
# but never eliminated it; a committed artifact is byte-identical every
# run, which is what Principle VII actually asks for. See
# specs/002-said-vs-held/research.md.
TEMPERATURE_NOTE = (
    "temperature is not settable on current models (removed from the "
    "Messages API); determinism comes from this committed cache"
)

# The check types plain code knows how to test. Anything else is coerced
# to `other`, which is testable by nothing.
CHECKS = (
    "avoid_sector",
    "avoid_region",
    "reduce_risk",
    "refuse_realise_loss",
    "needs_liquidity_by",
    "other",
)

# Checks that are meaningless without something to test against.
NEEDS_TARGET = ("avoid_sector", "avoid_region", "needs_liquidity_by")

# Committed alongside its output, per the constitution's Technology
# Standards. Block 4 supplies the schema and the rules; they are carried
# here verbatim rather than paraphrased.
PROMPT = """You are reading a private banking client's stated objectives and their
relationship manager's meeting notes. Extract every claim the client has
made about what they want, refuse to do, or are worried about.

Return JSON only. No prose, no markdown fences.

[{"claim": "<what they said, in their terms>",
  "check":  "avoid_sector" | "avoid_region" | "reduce_risk" |
            "refuse_realise_loss" | "needs_liquidity_by" | "other",
  "target": "<sector, region, or date - or null>",
  "source": "<objectives | note_id>",
  "stated_on": "<YYYY-MM-DD or null>"}]

Rules:
- Only claims the client made. Not the RM's opinion.
- If the note records the RM's concern rather than the client's words,
  skip it.
- Quote their phrasing in `claim`. Use their words, not a paraphrase --
  a claim whose words do not appear in the source will be discarded.
- `target` for avoid_sector must be a single lowercase word or short
  phrase as the client said it, e.g. "shipping".

OBJECTIVES: {objectives}
NOTES: {notes}"""


def _fingerprint(objectives: str, notes: list[dict]) -> str:
    """Content hash, so editing one note invalidates only that client."""
    payload = json.dumps(
        {
            "objectives": objectives,
            "notes": [
                {"note_id": n.get("note_id"), "note": n.get("note")}
                for n in notes
            ],
            "prompt": PROMPT,
            "model": MODEL,
            "effort": EFFORT,
        },
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def _source_text(objectives: str, notes: list[dict]) -> str:
    return " ".join([objectives or "", *(n.get("note", "") for n in notes)])


def _strip_fences(text: str) -> str:
    """Models wrap JSON in markdown fences regardless of instruction."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def _quote_is_grounded(quote: str, source: str) -> bool:
    """Does the client actually say this?

    A model asked to quote will occasionally paraphrase, and a paraphrase
    presented to a client as their own words is the worst failure this
    system could have. So the check is deliberately blunt: a run of the
    quoted words must appear in the source text.

    Compared on lowercased, whitespace-collapsed text, and satisfied by
    any six-word window of the quote — enough to tolerate a trailing
    period or a dropped article, not enough to admit an invention.
    """
    def norm(s: str) -> str:
        return re.sub(r"[^a-z0-9 ]", " ", str(s).lower())

    def collapse(s: str) -> str:
        return " ".join(s.split())

    haystack = collapse(norm(source))
    words = collapse(norm(quote)).split()
    if not words:
        return False
    if len(words) <= 6:
        return " ".join(words) in haystack
    return any(
        " ".join(words[i : i + 6]) in haystack
        for i in range(len(words) - 5)
    )


def parse_claims(
    raw: str, objectives: str, notes: list[dict]
) -> tuple[list[dict], list[str]]:
    """Model text to claims. Never raises (FR-012).

    Returns the surviving claims and a list of rejection reasons, so what
    was discarded is recorded rather than silently lost (Principle X).
    """
    rejected: list[str] = []

    try:
        payload = json.loads(_strip_fences(raw))
    except (json.JSONDecodeError, TypeError):
        return [], ["model output was not valid JSON; no claims extracted"]

    if not isinstance(payload, list):
        return [], ["model output was not a list; no claims extracted"]

    source = _source_text(objectives, notes)
    note_ids = {n.get("note_id") for n in notes}
    kept: list[dict] = []

    for item in payload:
        if not isinstance(item, dict) or "check" not in item:
            rejected.append(f"malformed claim dropped: {item!r}"[:160])
            continue

        quote = str(item.get("claim") or "").strip()
        if not quote:
            rejected.append("claim with no quoted words dropped")
            continue

        # Principle IV — the model may not invent what a client said.
        if not _quote_is_grounded(quote, source):
            rejected.append(
                f"claim dropped, quoted words not found in the source: "
                f"{quote[:80]!r}"
            )
            continue

        check = item.get("check")
        if check not in CHECKS:
            rejected.append(
                f"unrecognised check {check!r} coerced to 'other' "
                f"(nothing tests it)"
            )
            check = "other"

        target = item.get("target")
        target = str(target).strip().lower() if target else None
        if check in NEEDS_TARGET and not target:
            rejected.append(f"{check} claim with no target dropped")
            continue

        claim_source = str(item.get("source") or "").strip()
        if claim_source not in note_ids and claim_source != "objectives":
            # Keep the claim but do not let it cite a source that does not
            # exist. An ungrounded citation is worse than none.
            rejected.append(
                f"claim cited unknown source {claim_source!r}; "
                f"attributed to objectives"
            )
            claim_source = "objectives"

        kept.append(
            {
                "claim": quote,
                "check": check,
                "target": target,
                "source": claim_source,
                "stated_on": item.get("stated_on") or None,
            }
        )

    kept.sort(key=lambda c: (c["check"], c["source"], c["claim"]))
    return kept, rejected


def _load_cache() -> dict:
    if CACHE_PATH.exists():
        with CACHE_PATH.open() as fh:
            return json.load(fh)
    return {
        "prompt": PROMPT,
        "model": MODEL,
        "effort": EFFORT,
        "determinism": TEMPERATURE_NOTE,
        "clients": {},
    }


def _save_cache(cache: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    cache["prompt"] = PROMPT
    cache["model"] = MODEL
    cache["effort"] = EFFORT
    cache["determinism"] = TEMPERATURE_NOTE
    with CACHE_PATH.open("w") as fh:
        json.dump(cache, fh, indent=2, sort_keys=True)
        fh.write("\n")


def extract_claims(
    client_row, notes: list[dict], refresh: bool = False
) -> list[dict]:
    """Claims for one client. One model call, or none if already cached.

    ``refresh=False`` is the default and the demo path: the committed
    cache is read and no network call is made. Regenerating is an explicit
    action, never a side effect of running the pipeline.

    With no API key and no cache entry this returns an empty list. A
    missing key degrades the product; it does not break it (FR-015).
    """
    objectives = str(getattr(client_row, "objectives", "") or "")
    client_id = str(client_row.client_id)
    fingerprint = _fingerprint(objectives, notes)

    cache = _load_cache()
    entry = cache["clients"].get(client_id)

    if not refresh and entry and entry.get("fingerprint") == fingerprint:
        return entry["claims"]

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        # Stale entry is better than nothing, and nothing is better than a
        # guess. Either way, no exception.
        return entry["claims"] if entry else []

    import anthropic

    # Explicit replacement rather than str.format: the prompt contains a
    # JSON schema, and every brace in it would have to be doubled.
    notes_json = json.dumps(
        [
            {
                "note_id": n.get("note_id"),
                "note_date": n.get("note_date"),
                "note": n.get("note"),
            }
            for n in notes
        ],
        indent=2,
    )
    prompt = PROMPT.replace(
        "{objectives}", objectives or "(none recorded)"
    ).replace("{notes}", notes_json)

    response = anthropic.Anthropic(api_key=api_key).messages.create(
        model=MODEL,
        max_tokens=16000,
        output_config={"effort": EFFORT},
        messages=[{"role": "user", "content": prompt}],
    )
    raw = "".join(
        block.text for block in response.content if block.type == "text"
    )

    claims, rejected = parse_claims(raw, objectives, notes)

    cache["clients"][client_id] = {
        "fingerprint": fingerprint,
        "provenance": f"model:{MODEL} effort:{EFFORT}",
        "claims": claims,
        "rejected": rejected,
    }
    _save_cache(cache)
    return claims


def rejections_for(client_id: str) -> list[str]:
    """What was discarded during extraction, for `unsure_about`."""
    entry = _load_cache()["clients"].get(str(client_id))
    return entry.get("rejected", []) if entry else []


def provenance_for(client_id: str) -> str:
    """How this client's claims were produced — model, or hand-written."""
    entry = _load_cache()["clients"].get(str(client_id))
    return entry.get("provenance", "unknown") if entry else "none"
