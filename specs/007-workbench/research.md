# Phase 0 Research — The Workbench (spec 007)

**Date**: 2026-09-05 · Run before the spec was written.

Six questions. One conflict between the two design documents that has to
be resolved rather than averaged, and one thing the mockup shows that the
data does not currently support.

---

## R1 — The two design documents disagree on tokens

`design-notes.md` and `.alamazing/mockup.html` specify different palettes.

| Token | design-notes.md | mockup.html |
|---|---|---|
| ground | `#E7E9E5` | `#F0F1ED` |
| ink | `#16202E` | `#131B26` |
| hair | `#E2E3DF` | `#E4E5E1` |
| exposure tints | — | `#C79355 → #8A5E23`, four tints of one hue |
| safe | — | `#2E6B52` |

The mockup also carries two things the notes do not mention at all: a
**four-into-one figure** and a **band chart with pins**.

**Decision: the mockup wins on anything it specifies; the notes govern
everything else.** Two reasons. The run sheet identifies
`mockup-visual.html` as *"the one with the four-into-one figure and the
band chart"* and `design/mockup.html` as *"the quieter fallback if you
fall behind on the UI"* — so the visual mockup is the intended direction,
not an alternative. And `.alamazing/mockup.html` is a copy of it, which is
what spec 007 names.

Where they do not conflict, the notes are richer and binding: the
three-voice type rule, monospace confined to evidence, no all-caps, no
arrows on buttons, the two-shadow paper treatment, and the instruction
that boldness is spent in exactly two places.

`.alamazing/globals.css` is the shadcn token file and uses the *notes'*
palette. Rather than reconcile two hex sets by hand, the CSS variables
take the mockup's values and the shadcn HSL triples are left as supplied —
they differ by two or three per cent of lightness, which is below the
threshold anyone will see, and rewriting them risks breaking the
component theme for no visible gain. Recorded so the difference is a
decision rather than an oversight.

---

## R2 — The mockup's masthead date is not today's date

```html
<div class="s">Priscilla Ong · Asia desk · Wednesday 26 August 2026</div>
```

That is the **snapshot date**, not the day the demo runs. It is correct
and it should stay correct — the brief is *as at* the latest snapshot, and
saying so is what makes the figures defensible.

**Decision**: the masthead renders `meta.snapshot_date` from
`findings.json`, formatted long. Never `new Date()`. A page that says
"today" and shows August figures is the kind of small dishonesty that
invites a hard question.

---

## R3 — The four-into-one figure needs data the build already carries

The figure needs, per position: a short label, a weight, and an asset
class. Then one combined total.

`findings.json` carries all of it in the D3 sector finding's `members`
array — `instrument_id`, `instrument_name`, `asset_class`, `w` — plus
`theme_pct` for the total. Verified against the written file.

The mockup abbreviates the labels ("Asia Pacific Shipping Fund" for
"Asia Pacific Shipping and Logistics Fund"). **Decision**: render the full
`instrument_name` and let it wrap. Abbreviating in the UI would mean the
screen and the evidence panel disagree about what a position is called,
and the evidence panel is the trust story.

---

## R4 — The band chart's "pin" position needs a scale the data does not give

The mockup draws each band as a track with a green region for the
permitted range and a pin at the actual value. That needs a **scale
maximum** per row, and neither `findings.json` nor `mandates.csv` supplies
one.

**Decision**: the track runs 0–100%, and the permitted region and pin are
placed as percentages of that. It is honest, it needs no invented scale,
and it makes the bands comparable to each other down the column — Equity
40–65 looks wide and Structured Products 0–15 looks narrow, which is true
and is the point.

The alternative — scaling each row to its own band — would make a 0–15
band and a 40–65 band render the same width, which flatters the tight one
and misleads.

---

## R5 — Sixteen clients with nothing is a feature, and the number is checkable

Block 9: *"Sixteen with nothing today — say so. That absence is a feature;
a system that finds something wrong with everyone gets ignored by
Thursday."*

Counted from the built file rather than trusted: of twenty clients, the
detectors produce a **checked-and-clear** mandate result and no other
finding for a substantial minority. The exact count is computed at render
time from `findings.json` rather than written into the copy, so the
sentence cannot drift out of date if the data changes.

**Decision**: S1 states the count, derived. The word "sixteen" does not
appear in the source.

---

## R6 — What the actions actually do

Block 9 requires *Keep for the meeting / Not useful / Add a note* on every
finding, and Principle IX requires that rejection record its reason.

There is no server (Principle XIII: no database, no authentication). So
the decisions live in the browser's local storage, keyed by finding.

**Decision**: implement them as real, persistent-across-reload state, and
**say plainly in the README that they persist locally rather than to a
CRM**. That is the honest version. A disabled button that looks
interactive is worse than a working one that is scoped — and Strategic
Impact is assessed on whether the relationship manager retains control,
which a working keep/reject demonstrates and a mock does not.

Rejection prompts for a reason and stores it. Nothing is sent anywhere.

---

## Resolved

Six questions. The material ones: **the mockup governs where it
specifies** (R1), **the masthead shows the snapshot date, never today**
(R2), **the band track is a 0–100 scale so tight bands look tight** (R4),
and **the actions are real local state, described honestly** (R6).
