"""Spec 004 — D5, the question nobody answered.

The smallest detector in the system and the one block 6 refuses to let go:
*"D5 is roughly twenty lines. It is what converts the demo from analytics
to advisory. Do not cut it."*

It is right. Every other detector describes a portfolio. This one notices
that a person asked something and is still waiting.

On 12 August the hero client asked what happens to his portfolio if the
Strait reopens and normalises. Priscilla's own note records: *"We have not
modelled this."* Spec 005 answers it. This module is what finds that it
was asked.

Two guards, both learned from the data rather than assumed — see
``specs/004-liquidity-unanswered/research.md`` R5:

    a question asked and answered in the same note is not unanswered
    "unresolved" describing the world is not an open item

Without the first, two questions Priscilla demonstrably answered would be
flagged as ignored — which destroys her trust in the one that is real.

Contract: ``specs/004-liquidity-unanswered/contracts/unanswered.md``
"""

from __future__ import annotations

import re

from pipeline.load import Book

KIND = "D5"

# The client asked something.
_ASKED = re.compile(
    r"asked for a view|asked whether|asked what|asked if|asked me|"
    r"asked how|asked about",
    re.IGNORECASE,
)

# The relationship manager admitting the bank has not done something.
#
# Deliberately first-person and specific. A bare "unresolved" matches
# market commentary — one note reads "charter rates stay elevated while
# the Strait situation is unresolved", which is a description of the world,
# not an open item. Matching it would attach a spurious flag to the hero
# client's other note. So an admission is either "we have not <verb>",
# "have not yet <replied>", or a standalone "Unresolved." sentence.
_ADMITTED = re.compile(
    r"we have not (?:modelled|modeled|analysed|analyzed|looked|run|done)"
    r"|have not yet (?:replied|responded|come back|reverted)"
    r"|(?:^|\.\s+)unresolved\.",
    re.IGNORECASE,
)

# Evidence that the question was in fact dealt with.
_ANSWERED = re.compile(
    r"sent a|sent him|sent her|sent the|discussed|explained|"
    r"walked (?:him|her|through)|replied|responded|reviewed with|"
    r"talked through|showed (?:him|her)|answered",
    re.IGNORECASE,
)


def _open_items(note: str) -> dict:
    """Classify one note. Returns the markers found and the verdict."""
    asked = _ASKED.findall(note)
    admitted = _ADMITTED.findall(note)
    answered = _ANSWERED.findall(note)

    # An admission overrides the answer check. "Have not yet replied"
    # contains the word "replied" and would otherwise cancel itself.
    is_open = bool(admitted) or (bool(asked) and not answered)

    return {
        "asked": sorted({m.strip().lower() for m in asked}),
        "admitted": sorted({m.strip().lower() for m in admitted}),
        "answered": sorted({m.strip().lower() for m in answered}),
        "is_open": is_open,
    }


def detect(book: Book, client_id: str) -> list[dict]:
    """Open questions for one client, oldest first.

    A question answered by a **later** note is also closed — so the notes
    are walked in order and an earlier open item is cleared if a
    subsequent note answers it.
    """
    notes = book.notes_for(client_id)
    findings: list[dict] = []

    for index, note in enumerate(notes):
        text = str(note.get("note", ""))
        state = _open_items(text)
        if not state["is_open"]:
            continue

        # Did a later note deal with it? An admission is not cleared this
        # way — "we have not modelled this" stays true until somebody
        # models it, and no later note in this dataset says they did.
        later_answered = None
        if not state["admitted"]:
            for follower in notes[index + 1 :]:
                if _ANSWERED.search(str(follower.get("note", ""))):
                    later_answered = follower.get("note_id")
                    break
        if later_answered:
            continue

        findings.append(
            {
                "client_id": client_id,
                "kind": KIND,
                "severity": 4 if state["admitted"] else 3,
                "confidence": "high",
                "headline": _headline(state, note),
                "detail": _detail(state, note),
                "unanswered_question": {
                    "note_id": note.get("note_id"),
                    "asked_on": note.get("note_date"),
                    "question": text.strip(),
                },
                "markers": {
                    "asked": state["asked"],
                    "admitted": state["admitted"],
                },
                "evidence": [
                    {
                        "file": "rm_notes.json",
                        "rows": [note.get("note_id")],
                        "note": (
                            f'{note.get("note_date")} '
                            f'({note.get("channel")}): "{text.strip()}"'
                        ),
                    }
                ],
                "events": [],
                "unsure_about": (
                    "Detected from phrasing in the note. A question "
                    "answered by telephone and not written down would not "
                    "be found here, and one recorded in different words "
                    "may be missed."
                ),
                "classification": None,
            }
        )

    return sorted(
        findings, key=lambda f: f["unanswered_question"]["note_id"]
    )


def _headline(state: dict, note) -> str:
    when = note.get("note_date")
    if state["asked"] and state["admitted"]:
        return (
            f"Asked on {when} and not yet answered — the note records it "
            f"as outstanding."
        )
    if state["admitted"]:
        # No question in this note; the manager recorded an open item.
        return f"Left open on {when} — the note records it as unresolved."
    return f"Asked on {when}; no answer is recorded."


def _detail(state: dict, note) -> str:
    when = note.get("note_date")
    text = str(note.get("note", "")).strip()

    if state["admitted"] and state["asked"]:
        opening = (
            f"The client asked a question on {when} and the note records "
            f"that it was not answered."
        )
    elif state["admitted"]:
        opening = (
            f"The note of {when} records an item as outstanding."
        )
    else:
        opening = (
            f"The client asked a question on {when} and no answer appears "
            f"in this note or any later one."
        )

    return (
        f'{opening} In the relationship manager\'s own words: "{text}" '
        f"It may be worth closing this before the next conversation."
    )
