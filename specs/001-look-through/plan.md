# Implementation Plan: Look-Through Concentration

**Branch**: `main` (solo build) | **Date**: 2026-09-04 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-look-through/spec.md`

**Spec number**: 001 · **Gate**: G2 · **Time box**: 60 minutes
(`.alamazing/implementation.md` step 5)

**Status**: **Planned, not started. Phase 0 is blocking** — see
§ Verification status in the spec. Seven figures are quoted rather than
reproduced, and Python execution was unavailable when this was written.

## Summary

One module, `pipeline/divergence/d3_hidden.py`, with two public functions:
`look_through`, which adds a resolved `theme` to every holding, and
`detect`, which emits findings from it.

The mechanism is small enough to state in a sentence: **a structured
product is resolved to the names it references, not the asset class it is
booked as.** Everything else in this spec is bookkeeping around that one
move — parse the reference, match the names, total by theme, compare
against the mandate, and attach evidence.

The care goes into three places. Parsing free text that will not always
parse. Matching names loosely enough to catch an ADR against an ordinary
share, but tightly enough not to invent a match. And computing
`compliance_clean` as an earned positive rather than the absence of a
negative — because that flag is the pitch, and a flag that defaults to
true is worthless.

No model is called. `.alamazing/implementation.md` step 5 budgets 60
minutes and instructs that this detector is built **first** among the six,
because the other five reuse its look-through.

## Technical Context

**Language/Version**: Python 3.14 (`.venv`)

**Primary Dependencies**: pandas 2.x, pytest. Nothing new. `anthropic`
stays uninstalled from this module's perspective — spec 002 is the first
to import it.

**Storage**: None. Consumes the in-memory `Book` from spec 000.

**Testing**: pytest. `tests/test_lookthrough.py` (unit + the three
integration assertions), extending the existing flat `tests/`.

**Target Platform**: Same as spec 000 — laptop for the build, Linux for
the later Vercel build step.

**Project Type**: Library module inside the existing `pipeline/` package.

**Performance Goals**: The detector over all 20 clients at all 5 snapshots
in under two seconds. Not a constraint; recorded so a quadratic name-match
is visibly wrong.

**Constraints**: No filesystem or model access (spec 000's contract
invariant 1 and 2). Deterministic finding order. No literal client id,
instrument id, sector, theme name, threshold or date (Principle XI).

**Scale/Scope**: 20 clients, up to ~11 holdings each per snapshot, 62
instruments of which a handful carry an underlying reference. Tiny.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Article | Gate | Status |
|---|---|---|
| I. Demo Primacy | Does this reach the screen? | **PASS** — it *is* the screen. The headline figure and the mandate panel both come from this module |
| II. Specification First | Spec before code, edits capped | **PASS** — spec.md complete. The verification-status table is the recorded assumption Principle II requires, not an open question left dangling |
| III. The Spine Rule | Riskiest assumption proven first | **PASS with a caveat** — the spine figure itself is proven (spec 000, twice). The riskiest assumption *in this spec* is that the reference text parses to names that match the client's holdings. That is unproven, and Phase 0 task R1 exists to prove it before any code is written |
| IV. Nothing Is Invented | Facts only from `data/` | **PASS** — the underlying reference is read from `instruments.csv`; no external knowledge of what the basket contains |
| V. Model Never Counts | No model arithmetic | **PASS** — no model call. The parse is a string split, the match a substring test, the totals pandas |
| VI. Evidence Over Assertion | Findings carry file, rows, values | **PASS** — FR-014, FR-015. Every finding built from `client_weights` rows, which spec 000 guarantees retain their identifiers. A finding with no evidence is not emitted |
| VII. Determinism | Same in, same out | **PASS** — explicit sort on themes and on the finding list; parsed names sorted before matching |
| VIII. Test Pyramid | ~14 unit, ~4 integration | **PASS** — contributes ~5 unit and **3** integration assertions (SC-001, SC-004, SC-005). Two of the six required assertions in Article VIII's table (`test_lookthrough_cl0019`, `test_lookthrough_cl0014`) land here |
| IX. RM Decides | No "recommend", no deciding | **PASS** — FR-008, FR-017. The detector reports the duplicate and does not suggest a replacement. Grep-verified |
| X. Honest Framing | Uncertainty stated | **PASS** — FR-016 puts loose matches and parse failures in `unsure_about`. The spec's verification table and the schema inconsistency are both reported rather than smoothed |
| XI. Portable By Construction | No hardcoded ids/dates/series | **PASS** — the 25% threshold is a parameter, the theme names are derived from data, snapshots come from `snapshots(book)`. Grep-verified |
| XII. Vertical Slices | Runnable end to end | **PASS** — `detect(book, cid)` returns findings in a REPL with no UI |
| XIII. Declared Scope | Nothing out of scope built | **PASS** — no classification, no optimiser, no chart, no model |
| XIV. Design Is A Quarter | Proportionate effort | **PASS** — 60 minutes. `compliance_clean` must be *visible*, which is a spec 007 obligation this spec enables by emitting the flag |
| XV. Living Evidence | Tagged, recorded | **PENDING** — G2 covers specs 001–005 together, so no tag closes at the end of this spec alone |

**Verdict: no violations. Complexity Tracking omitted.**

One article needs a note rather than a tick:

- **Article III.** The constitution's spine is a *number*, and that number
  is already proven. But this spec introduces a second, smaller
  assumption — that `"Worst-of basket: Pacific Orient Shipping / Global
  Energy Majors ADR / Bara Nusantara Energy"` parses into names that
  actually match `instrument_name` values in the client's book. If the
  ADR suffix or a word-order difference defeats the match, the duplicate
  finding is empty and SC-003 fails. It is six minutes to check and
  potentially an hour to discover late, so it is Phase 0 task R1 and it
  blocks everything.

## Project Structure

### Documentation (this feature)

```text
specs/001-look-through/
├── spec.md              # requirements — written, figures unverified
├── plan.md              # this file
├── research.md          # Phase 0 — NOT YET WRITTEN, blocking
├── data-model.md        # Phase 1 — after Phase 0
├── quickstart.md        # Phase 1 — after Phase 0
├── contracts/
│   └── look-through.md  # Phase 1 — the two public functions
└── checklists/
    └── requirements.md  # spec quality checklist
```

### Source Code (repository root)

```text
pipeline/
├── load.py              # spec 000 — consumed, not modified
├── diff.py              # spec 000
├── events.py            # spec 000
├── mandate.py           # NEW — shared band comparison (see below)
└── divergence/
    ├── __init__.py
    └── d3_hidden.py     # NEW — look_through, detect

tests/
├── conftest.py          # extended with CL-0014 constants
└── test_lookthrough.py  # NEW — 5 unit + 3 integration assertions
```

**Structure Decision**: One new detector module under
`pipeline/divergence/`, matching the run sheet's target tree and
`.alamazing/implementation.md`'s naming (`d3_hidden.py`).

**One deliberate addition: `pipeline/mandate.py`.** The band comparison is
needed by *this* spec for `compliance_clean` and by *spec 003* for breach
classification. Block 5 says so explicitly — "spec 001 needs it for
`compliance_clean`". Writing it inside `d3_hidden.py` would mean spec 003
either imports from a detector module, which is backwards, or duplicates
the comparison, which is how two subtly different band checks end up in
one build.

So the comparison lives in a shared module that both consume: this spec
uses it for a boolean verdict, spec 003 for classification. This is the
only structural decision in the spec and it is made now because
retrofitting it at 11:00 Saturday costs more than writing it once tonight.

## Phase 0 — Research **(BLOCKING — not yet done)**

**Nothing in Phase 1 or later may begin until all seven items resolve.**
Each requires running Python against `data/`, which was unavailable when
this plan was written.

| # | Question | Why it blocks | Resolves |
|---|---|---|---|
| **R1** | Does the underlying reference parse to names that match `instrument_name` in the client's holdings? | The riskiest assumption in the spec. If the ADR suffix or word order defeats the match, the duplicate finding is empty and SC-003 fails | FR-002, FR-003, SC-003 |
| **R2** | Do the five trajectory figures reproduce? | Four of the five are unverified. A trajectory that does not reproduce is a figure quoted on stage that the data does not support | SC-004 |
| **R3** | Do CL-0019's five bands reproduce, and is the largest position really 13.30% against a 15% limit? | `compliance_clean = True` is the strongest line in the pitch. If any band is actually breached, the entire argument changes shape | SC-002 |
| **R4** | Does CL-0014's Golden Harbour total 29.46% across those three instruments, and are they genuinely three different booked asset classes? | The generality proof. If the three collapse to one asset class the story is weaker but still true | SC-005 |
| **R5** | How should a theme be *named*, given names must be derived rather than written? | A theme name appears in RM-facing copy. Deriving "shipping and energy" from the data without hardcoding it is the one genuinely awkward part of this spec | FR-001, FR-020 |
| **R6** | Which instruments in the whole book carry an underlying reference, and do all of them parse? | Determines whether the parse needs to be defensive or merely correct, and whether the fallback path is exercised at all | FR-002, FR-016 |
| **R7** | Do theme totals account for 100% of client value for every client at every snapshot? | Catches double-counting. A structured product resolved to three names must not contribute three times its weight | SC-006 |

**R5 is the one with no obvious answer.** The others are measurements; this
one is a design decision constrained by Principle XI. A theme called
`"shipping and energy"` is exactly what should appear in Priscilla's brief,
and writing that string in `pipeline/` violates FR-020. The candidate
approaches, to be decided in Phase 0 with the data in front of me:

1. **Theme = the resolved instrument's own sector**, so the hero's theme is
   whatever `sector` those four rows carry. Derived, portable, and the name
   is whatever the bank already calls it. Risk: the four may not share one
   sector — the shipping names are booked `Industrials` and the energy
   names `Energy` (established in spec 000, research R5), which would split
   the 42% into two themes and break SC-001.
2. **Theme = a cluster of co-referenced names**, identified by the graph of
   which holdings a structured product references. The hero's note ties
   shipping and energy together *because his own note references both*.
   Fully derived, no naming needed — the theme is labelled by joining its
   members' sectors. More faithful to what the finding actually is, and
   more code.
3. **Theme = sector, with a caller-supplied grouping parameter.** Portable
   by the letter of FR-020 since the grouping is an argument, but it pushes
   the interesting decision into `build.py`, where it becomes a literal in
   a different file. Rejected in advance as gaming the grep.

**Approach 2 is the likely answer** — it is what the finding *is*, and it
produces the 42% figure as a single theme without anyone naming shipping
or energy. But it must be confirmed against R1 and R7 before committing,
because it depends entirely on the reference matching real holdings.

## Phase 1 — Design *(after Phase 0)*

To be written once Phase 0 resolves:

- **data-model.md** — the `theme` column, the theme-total frame, the
  compliance verdict, and the two Finding shapes this spec emits.
- **contracts/look-through.md** — `look_through` and `detect` with
  guarantees and failure behaviour, plus `mandate.py`'s shared comparison.
  Fixed before spec 002 consumes `look_through`.
- **quickstart.md** — the acceptance figures as runnable blocks.

### Design decisions already settled

**`look_through` returns a frame, not theme totals.** It adds a `theme`
column to `client_weights`'s output and returns every row. Totals are a
`groupby` the caller performs. Spec 002 needs the rows — it filters
exposure by theme against a claim's target — so a function returning only
totals would force it to recompute.

**`detect` emits at most two findings per client, and possibly zero.** No
finding is fabricated to fill a screen. A client with no concentration and
no duplicate produces an empty list, which is a correct answer.

**`compliance_clean` is computed per client across all their portfolios.**
Bands are per portfolio; the flag is a property of the client's whole
position, so it is true only when every one of their portfolios passes.

**The threshold is a parameter defaulting to 25.** Block 3 sets 25%.
Making it an argument satisfies FR-020 and means "what about 20%?" is
answered by typing rather than explaining.

**Parse failures degrade, never throw.** A reference that does not parse
falls back to the sector theme and records the failure in `unsure_about`.
Spec 002's block states the principle for model output — "malformed output
returns no findings, never throws" — and the same discipline applies to
malformed data.

## Constitution Re-Check (post-design)

**Not yet performed.** Phase 1 is not written. To be completed before
implementation, with particular attention to Article XI once R5 is decided
— approach 3 above would pass the grep while violating the intent, and the
re-check is where that gets caught.

## Time box

| Step | Work | Budget |
|---|---|---|
| Phase 0 | Reproduce all seven figures | 15 min |
| 1 | `mandate.py` — shared band comparison | 15 min |
| 2 | `d3_hidden.py` — parse, match, theme resolution | 25 min |
| 3 | `d3_hidden.py` — the two findings, evidence, `compliance_clean` | 20 min |
| 4 | Tests: 5 unit + 3 integration | included |
| | **Total** | **75 min** vs a 60-min budget |

**The overrun is declared rather than hidden.** `.alamazing/implementation.md`
budgets 60 minutes for step 5 and does not account for `mandate.py`, which
block 5 nonetheless requires this spec to produce. Fifteen minutes spent
here is saved in spec 003.

Overrun rule (Principle II): at the cap, close with a recorded assumption
rather than extending. Nothing in this spec is cuttable — the constitution
names spec 001 and the mandate panel in "never cut".

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| The reference names do not match holdings (R1) | SC-003 fails; the duplicate finding is empty and the most explicable part of the pitch is lost | Phase 0 task R1, before any code |
| The four exposure rows span two sectors, so theme-by-sector splits the 42% (R5) | SC-001 fails through a naming choice rather than an arithmetic error | Approach 2 (co-reference clustering) sidesteps it; confirm in Phase 0 |
| A resolved structured product double-counts across its referenced names | Theme totals exceed 100%; every figure inflated plausibly | SC-006 asserted for all 20 clients at all 5 snapshots, as spec 000 did for weights |
| A trajectory figure does not reproduce (R2) | A number quoted on stage that the data does not support | Phase 0; if it fails, report it (Principle X) rather than reconcile it |
| `mandate.py` diverges from spec 003's needs | Two band checks in one build | Written once, consumed by both; spec 003 extends rather than reimplements |
