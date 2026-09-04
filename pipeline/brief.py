"""Spec 006 — the brief and the call list. The last four model calls.

Two model calls per concern and no more: three briefs, one ranking.
Together with spec 002's twenty extractions that is **24 calls in the
whole system**, which is what the constitution records, and every one runs
at build time with its output committed.

**Article V is stricter here than anywhere else in the build, and it is
the easy thing to get wrong.** A brief reads better if the model can see
the client's notes and objectives — and it may, those are prose, and
reading prose is the one thing only a model can do. What it must never see
is a holdings row or any figure it could restate incorrectly.

So the prompt receives: the person, their objectives, their notes, and the
**findings as already computed by pandas**. Every number in the output
arrived as text and leaves as text. The model is transcribing figures, not
producing them.

Two guards, the same shape as `claims.py`:

    a brief containing the forbidden verb is **rejected**, not edited
    a date the brief cites that appears nowhere in the data is recorded

And one that only this module needs: the ranking is **validated in code**.
A model asked to order twenty items will occasionally return nineteen, and
a call list that quietly loses a client is worse than one that is
unordered.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

_DERIVED = Path(__file__).parent.parent / "derived"
BRIEFS_PATH = _DERIVED / "briefs.json"
RANKING_PATH = _DERIVED / "ranking.json"

MODEL = "claude-opus-5"

# Briefs are prose that gets read aloud in the demo's closing beat, and
# the ranking is a judgement about urgency. Both earn the higher setting.
EFFORT = "high"

FORBIDDEN_VERB = "recommend"

# Block 8's seven rules, carried verbatim rather than paraphrased.
BRIEF_PROMPT = """Write a briefing for Priscilla Ong, a private banking relationship
manager, about one of her clients. She reads it before a meeting.

Rules:
- Use ONLY the facts supplied below. Invent nothing.
- Reference events by their date and description from the event log only.
- Never use the word "recommend". Use "worth raising" or "you may want to
  check".
- Name the person and their situation, not just the numbers.
- Three or four short paragraphs.
- End with ONE sentence she could say aloud to open the conversation.
- If the evidence does not support a claim, leave it out.

Return JSON only, no markdown fences:
{"paragraphs": ["...", "...", "..."], "opening_line": "..."}

CLIENT: {client}
OBJECTIVES: {objectives}
FINDINGS: {findings}
NOTES: {notes}
EVENTS AVAILABLE TO CITE: {events}"""

RANKING_PROMPT = """You are ordering a private banking relationship manager's client book by
how soon a conversation is worth having. She has twenty clients and can
properly watch about three.

Order by urgency of conversation, NOT by portfolio size. Age, life stage,
drawdown and imminent cash needs weigh more than the size of a mandate
breach. A large portfolio with nothing wrong ranks below a smaller one
with a dated obligation the client cannot meet.

Return JSON only, no markdown fences. Every client must appear exactly
once:
[{"client_id": "...", "why": "<one sentence>"}]

Keep `why` to one sentence, in plain English, addressed to her. Do not use
the word "recommend".

CLIENTS: {clients}"""


def _strip_fences(text: str) -> str:
    cleaned = str(text).strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def _fingerprint(payload) -> str:
    blob = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def _load(path: Path, prompt: str) -> dict:
    if path.exists():
        with path.open() as handle:
            return json.load(handle)
    return {"prompt": prompt, "model": MODEL, "effort": EFFORT, "entries": {}}


def _save(path: Path, cache: dict, prompt: str) -> None:
    cache["prompt"] = prompt
    cache["model"] = MODEL
    cache["effort"] = EFFORT
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        json.dump(cache, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _call(prompt: str) -> str:
    """The only network call in this module."""
    import anthropic

    response = anthropic.Anthropic(
        api_key=os.environ["ANTHROPIC_API_KEY"]
    ).messages.create(
        model=MODEL,
        max_tokens=16000,
        output_config={"effort": EFFORT},
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(
        block.text for block in response.content if block.type == "text"
    )


# --- briefs ---------------------------------------------------------------


def _finding_summary(finding: dict) -> dict:
    """What the model is allowed to see: the finding, already computed.

    Deliberately a whitelist rather than the whole finding dict. Passing
    the evidence rows through would put holdings identifiers and values in
    front of the model, and there is no reason for it to see them — the
    evidence panel renders from the finding itself, not from the brief.
    """
    keep = (
        "kind",
        "rule",
        "check",
        "headline",
        "detail",
        "theme",
        "theme_pct",
        "asset_class",
        "actual_pct",
        "min_pct",
        "max_pct",
        "verdict",
        "classification",
        "compliance_clean",
        "look_through_pct",
        "direct_pct",
        "total_impact_usd",
        "total_impact_pct",
        "need_pct",
        "unsure_about",
    )
    return {k: finding[k] for k in keep if k in finding}


def grounded_dates(book) -> set:
    """Every date that appears somewhere in the supplied files.

    A first version checked cited dates against `event_log.csv` alone and
    rejected three briefs for citing dates that were perfectly sourced —
    note dates, snapshot dates, and the due date of a tax instalment. The
    check was wrong, not the briefs.

    Principle IV asks that nothing be invented, not that every date be an
    event. So the valid set is every date the data contains: events,
    snapshots, note dates, obligation windows, portfolio inceptions. A
    cited date outside that set is genuinely unsourced.
    """
    dates: set[str] = set()

    dates.update(str(d) for d in book.events.event_date)
    dates.update(str(d) for d in book.holdings.snapshot_date.unique())
    dates.update(str(n.get("note_date")) for n in book.notes)
    dates.update(str(d) for d in book.portfolios.inception_date)

    for column in ("due_from", "due_to"):
        if column in book.cash_needs.columns:
            dates.update(str(d) for d in book.cash_needs[column])

    for column in ("trade_date", "settlement_date"):
        if column in book.transactions.columns:
            dates.update(str(d) for d in book.transactions[column])

    for column in ("acquired_date", "valuation_date"):
        if column in book.holdings.columns:
            dates.update(str(d) for d in book.holdings[column].unique())

    return {d for d in dates if re.fullmatch(r"\d{4}-\d{2}-\d{2}", d)}


def _unresolved_date_references(text: str, valid: set) -> list[str]:
    """Dates the brief cites that appear nowhere in the data."""
    cited = set(re.findall(r"\b(\d{4}-\d{2}-\d{2})\b", str(text)))
    return sorted(cited - valid)


def write_brief(
    book, client_id: str, findings: list[dict], refresh: bool = False
) -> dict:
    """One brief for one client. One model call, or none if cached."""
    client = book.client(client_id)
    notes = book.notes_for(client_id)

    person = {
        "name": client.client_name,
        "age": int(client.age) if client.age == client.age else None,
        "life_stage": client.life_stage,
        "source_of_wealth": client.source_of_wealth,
        "mandate": client.risk_profile,
    }
    summaries = [_finding_summary(f) for f in findings]
    events = [
        {"date": r.event_date, "description": r.description}
        for _, r in book.events.iterrows()
    ]

    payload = {
        "person": person,
        "objectives": str(client.objectives),
        "findings": summaries,
        "notes": [
            {"note_id": n.get("note_id"), "note_date": n.get("note_date"),
             "note": n.get("note")}
            for n in notes
        ],
        "prompt": BRIEF_PROMPT,
        "model": MODEL,
        "effort": EFFORT,
    }
    fingerprint = _fingerprint(payload)

    cache = _load(BRIEFS_PATH, BRIEF_PROMPT)
    entry = cache["entries"].get(client_id)
    if not refresh and entry and entry.get("fingerprint") == fingerprint:
        return entry

    if not os.environ.get("ANTHROPIC_API_KEY"):
        # A missing key degrades the product; it does not break it.
        return entry or {
            "fingerprint": None,
            "provenance": "none",
            "paragraphs": [],
            "opening_line": "",
            "rejections": ["no API key and no committed brief"],
        }

    prompt = (
        BRIEF_PROMPT.replace("{client}", json.dumps(person, default=str))
        .replace("{objectives}", str(client.objectives))
        .replace("{findings}", json.dumps(summaries, indent=2, default=str))
        .replace("{notes}", json.dumps(payload["notes"], indent=2))
        .replace("{events}", json.dumps(events, indent=2))
    )

    raw = _call(prompt)
    parsed, rejections = parse_brief(raw, book)

    if parsed is None:
        # Keep whatever was committed rather than shipping nothing.
        if entry:
            entry = {
                **entry,
                "rejections": entry.get("rejections", []) + rejections,
            }
            cache["entries"][client_id] = entry
            _save(BRIEFS_PATH, cache, BRIEF_PROMPT)
            return entry
        parsed = {"paragraphs": [], "opening_line": ""}

    result = {
        "fingerprint": fingerprint,
        "provenance": f"model:{MODEL} effort:{EFFORT}",
        "paragraphs": parsed["paragraphs"],
        "opening_line": parsed["opening_line"],
        "rejections": rejections,
    }
    cache["entries"][client_id] = result
    _save(BRIEFS_PATH, cache, BRIEF_PROMPT)
    return result


def parse_brief(raw: str, book) -> tuple[dict | None, list[str]]:
    """Model text to a brief. Never raises.

    Returns ``None`` for the brief when it must be rejected, plus the
    reasons — so a rejection is a recorded fact rather than a silent edit.
    """
    rejections: list[str] = []

    try:
        payload = json.loads(_strip_fences(raw))
    except (json.JSONDecodeError, TypeError):
        return None, ["brief output was not valid JSON; rejected"]

    if not isinstance(payload, dict):
        return None, ["brief output was not an object; rejected"]

    paragraphs = payload.get("paragraphs")
    opening = str(payload.get("opening_line") or "").strip()

    if not isinstance(paragraphs, list) or not paragraphs:
        return None, ["brief contained no paragraphs; rejected"]
    paragraphs = [str(p).strip() for p in paragraphs if str(p).strip()]
    if not opening:
        return None, ["brief contained no opening line; rejected"]

    # The model reliably repeats the opening line as a final paragraph —
    # it was asked to end with it, and it does so in both fields. Dropping
    # the duplicate is presentation, not editing: the sentence is
    # unchanged and still present as `opening_line`, which is where the
    # interface renders it.
    def _bare(text: str) -> str:
        return re.sub(r"[^a-z0-9 ]", "", str(text).lower()).strip()

    if paragraphs and _bare(paragraphs[-1]) == _bare(opening):
        paragraphs = paragraphs[:-1]

    body = " ".join(paragraphs) + " " + opening

    # Principle IX. Rejected, never rewritten — silently editing model
    # output would make the committed artifact a fiction.
    if FORBIDDEN_VERB in body.lower():
        return None, [
            f"brief used the word {FORBIDDEN_VERB!r}; rejected rather than "
            f"edited, and the previously committed brief retained"
        ]

    # Principle IV.
    unresolved = _unresolved_date_references(body, grounded_dates(book))
    if unresolved:
        rejections.append(
            "brief cites dates that appear nowhere in the supplied data: "
            + ", ".join(unresolved)
        )

    if not 3 <= len(paragraphs) <= 4:
        rejections.append(
            f"brief returned {len(paragraphs)} paragraphs rather than three "
            f"or four; kept as written rather than padded"
        )

    return {"paragraphs": paragraphs, "opening_line": opening}, rejections


# --- ranking --------------------------------------------------------------


def rank(book, summaries: dict, refresh: bool = False) -> dict:
    """Order the whole book by urgency of conversation. One model call.

    ``summaries`` maps client id to a compact, already-computed summary.
    The model never receives a raw client record (Principle V).
    """
    clients = []
    for client_id in sorted(summaries):
        client = book.client(client_id)
        clients.append(
            {
                "client_id": client_id,
                "name": client.client_name,
                "age": int(client.age) if client.age == client.age else None,
                "life_stage": client.life_stage,
                "aum_usd": round(float(client.total_aum_usd)),
                "findings": summaries[client_id],
            }
        )

    payload = {
        "clients": clients,
        "prompt": RANKING_PROMPT,
        "model": MODEL,
        "effort": EFFORT,
    }
    fingerprint = _fingerprint(payload)

    cache = _load(RANKING_PATH, RANKING_PROMPT)
    entry = cache["entries"].get("all")
    if not refresh and entry and entry.get("fingerprint") == fingerprint:
        return entry

    if not os.environ.get("ANTHROPIC_API_KEY"):
        if entry:
            return entry
        # No key, no committed ranking: fall back to a deterministic order
        # and say so. A call list in an arbitrary order beats none.
        return _validated(
            [],
            sorted(summaries),
            fingerprint,
            provenance="none",
            extra=["no API key and no committed ranking; alphabetical order"],
        )

    prompt = RANKING_PROMPT.replace(
        "{clients}", json.dumps(clients, indent=2, default=str)
    )
    raw = _call(prompt)

    try:
        proposed = json.loads(_strip_fences(raw))
        if not isinstance(proposed, list):
            proposed = []
    except (json.JSONDecodeError, TypeError):
        proposed = []

    result = _validated(
        proposed,
        sorted(summaries),
        fingerprint,
        provenance=f"model:{MODEL} effort:{EFFORT}",
    )
    cache["entries"]["all"] = result
    _save(RANKING_PATH, cache, RANKING_PROMPT)
    return result


def _validated(
    proposed: list,
    every_client: list[str],
    fingerprint: str,
    provenance: str,
    extra: list[str] | None = None,
) -> dict:
    """Every client exactly once. The model's output is not trusted.

    A model asked to order twenty items will occasionally return
    nineteen. A call list that quietly loses a client is worse than one
    that is unordered — she would never know the client was missing.

    So: duplicates dropped, unknown ids dropped, omissions appended in
    sorted order, and every correction recorded.
    """
    corrections = list(extra or [])
    known = set(every_client)
    order: list[dict] = []
    seen: set[str] = set()

    for item in proposed:
        if not isinstance(item, dict):
            corrections.append(f"dropped malformed ranking entry: {item!r}"[:120])
            continue
        client_id = str(item.get("client_id", "")).strip()
        if client_id not in known:
            corrections.append(
                f"dropped ranking entry for unknown client {client_id!r}"
            )
            continue
        if client_id in seen:
            corrections.append(f"dropped duplicate ranking entry for {client_id}")
            continue
        why = str(item.get("why") or "").strip()
        if FORBIDDEN_VERB in why.lower():
            why = ""
            corrections.append(
                f"cleared justification for {client_id}: it used the "
                f"forbidden verb"
            )
        seen.add(client_id)
        order.append({"client_id": client_id, "why": why})

    missing = [c for c in every_client if c not in seen]
    for client_id in missing:
        order.append({"client_id": client_id, "why": ""})
    if missing:
        corrections.append(
            "appended clients the ranking omitted, in sorted order: "
            + ", ".join(missing)
        )

    return {
        "fingerprint": fingerprint,
        "provenance": provenance,
        "order": order,
        "corrections": corrections,
    }
