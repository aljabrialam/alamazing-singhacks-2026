# Feature Specification: Said vs Held

**Feature Branch**: `main` (solo build)

**Created**: 2026-09-04

**Status**: Draft — key figure pre-verified, see § Pre-flight

**Input**: Block 4 of `alamazing-all-specs.md`, pasted unmodified.

**Spec number**: 002 · **Gate**: G2 · **Depends on**: spec 001
(`look_through`), spec 000 (`Book`, `notes_for`, `client`)

**The only spec in the build that calls a model.**

---

## Pre-flight — the figure that could have derailed the design

Verified before writing this spec, because the acceptance criterion
("a finding at 42.134%") is not reachable by the obvious route.

`shipping` is **not a sector** in this dataset. Pacific Orient Shipping is
booked `Industrials`. So a naive `sector == target` test finds nothing,
and summing only the positions whose names say "shipping" gives **33.20%**,
not 42.13%.

The chain that reaches the recorded figure, verified:

```
claim target "shipping"
  ->  seed on source fields only (instrument_name, sector,
      sub_asset_class, underlying_reference)
        SYN-SP-0505  12.90%   reference names Pacific Orient Shipping
        SYN-ST-0104  11.41%   Pacific Orient Shipping Ltd
        SYN-EQ-0025   8.88%   Asia Pacific Shipping and Logistics Fund
                     -------
                      33.20%
  ->  expand to the look_through theme those seeds sit in
        "Energy + Industrials"  ->  42.1343%   ✅ recorded 42.134
```

**Seeds must come from source fields, never from a derived theme label.**
Matching against `theme_issuer` also reaches 42.13%, but only because that
label happens to contain the word "Shipping" — the energy fund would be
pulled in by a string the pipeline itself wrote. That is circular, and it
would break the moment a label was reworded. The two-step chain is also
the more explicable one, which matters more: *three positions are shipping
by name, and once you look through the note, the exposure they sit inside
is 42% of the book.*

Both figures are reported. 33.20% is what he holds in shipping by name;
42.13% is what he is exposed to once the note is resolved.

---

## Why this exists

Every bank checks a portfolio against its mandate. Nobody checks it
against what the client **said**, because what they said lives in prose no
risk system reads.

Abdullah's mandate says equity 40–65. It is monitored daily. His stated
objective says *"Build wealth outside the Gulf region and outside the
shipping sector"* — typed at onboarding and, on the evidence of his
portfolio, never looked at again.

This is the product's differentiator and the one place a language model
earns its place: **reading prose is the thing only a model can do, and it
is the only thing it is allowed to do here.** It converts what a client
said into a testable claim. Plain code then tests the claim. The model
never sees a number, never computes one, and never decides whether a claim
is violated.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Turn what he said into something checkable (Priority: P1)

The system reads a client's stated objectives and their relationship
manager's notes, and extracts each claim the **client** made about what
they want, refuse, or worry about — in their own words, with its source
and date.

**Why this priority**: Nothing else in this spec exists without it, and it
is the only model call in the system.

**Independent Test**: Extract claims for the hero client and assert one
has `check = avoid_sector` and `target = shipping`, sourced to his
objectives.

**Acceptance Scenarios**:

1. **Given** the hero client's objectives, **When** claims are extracted,
   **Then** one has `check = avoid_sector`, `target = shipping`, and
   `source = objectives`.
2. **Given** his two notes, **When** claims are extracted, **Then** claims
   are also drawn from **N-025** and **N-026**, each citing its note id.
3. **Given** a note recording the relationship manager's *own* concern
   rather than the client's words, **When** claims are extracted, **Then**
   it is skipped.
4. **Given** any extracted claim, **When** it is read, **Then** `claim`
   quotes the client's phrasing rather than paraphrasing it.
5. **Given** the model returns text that is not valid JSON, **When**
   extraction runs, **Then** it returns no claims and does not raise.
6. **Given** extraction has run once, **When** the pipeline runs again,
   **Then** the committed claims are reused and **no model call is made**.

---

### User Story 2 — Test the claim in code, never in the model (Priority: P1)

For each claim, deterministic code decides whether the portfolio
contradicts it. An `avoid_sector` claim is tested by seeding on the target
and expanding through spec 001's look-through.

**Why this priority**: P1 and inseparable from Story 1. This separation is
the architectural spine and the answer to half the questions a banking
judge will ask.

**Independent Test**: Assert the hero client's `avoid_sector` claim
produces a finding at 42.134% ± 0.001, and that no model call occurs
during detection.

**Acceptance Scenarios**:

1. **Given** an `avoid_sector` claim, **When** it is tested, **Then** the
   exposure is computed by code from the look-through, and the finding
   reports **42.134% ± 0.001** for the hero client.
2. **Given** any claim, **When** it is tested, **Then** the decision to
   emit a finding is made by a threshold comparison in code and not by a
   model.
3. **Given** a claim whose target the portfolio does not contradict,
   **When** it is tested, **Then** no finding is emitted, and that is
   recorded as a checked-and-clear result rather than silence.
4. **Given** detection runs, **When** the process is inspected, **Then**
   no network call is made.

---

### Story 3 — Quote him back to himself (Priority: P1)

Every finding carries the client's own words, the source they came from,
and the date they were said.

**Why this priority**: P1. A finding that says "42% shipping exposure" is
a risk report. A finding that says *"you asked for wealth outside the
shipping sector — here is 42%"* is the product. The quote is the finding.

**Independent Test**: Assert every emitted finding contains a non-empty
quote, a resolvable source, and a date where the source carries one.

**Acceptance Scenarios**:

1. **Given** a finding from an objectives-sourced claim, **When** it is
   read, **Then** it quotes the objective text and cites `clients.csv`.
2. **Given** a finding from a note-sourced claim, **When** it is read,
   **Then** it quotes the note and cites the **note id** and
   `rm_notes.json`.
3. **Given** any cited note id, **When** it is checked, **Then** it
   resolves to a row in `rm_notes.json`.
4. **Given** a finding, **When** its copy is read, **Then** it does not
   contain the word "recommend".

---

### Story 4 — A second client, a different kind of claim (Priority: P2)

The same extraction run against a different client yields a different
class of claim — a wish to reduce risk rather than avoid a sector — and
the code tests it differently.

**Why this priority**: P2 for the demo, but it proves the mechanism is not
a single hardcoded test wearing a model's clothes.

**Independent Test**: Assert CL-0003's note N-005 yields a `reduce_risk`
claim quoting her words.

**Acceptance Scenarios**:

1. **Given** CL-0003's note **N-005**, **When** claims are extracted,
   **Then** one has `check = reduce_risk`, quoting *"never taken a risk
   with money"* or *"something safe and boring"*.
2. **Given** a `reduce_risk` claim, **When** it is tested, **Then** the
   test is a comparison against her mandate's risk position in code, not
   a model's judgement.
3. **Given** her portfolio breaches its equity ceiling, **When** the claim
   is tested, **Then** a finding is emitted citing both her words and the
   breach.

---

### Edge Cases

- **The model returns markdown fences around the JSON.** Stripped before
  parsing.
- **The model returns valid JSON of the wrong shape** — a dict instead of
  a list, or a claim missing `check`. Malformed claims are dropped
  individually; well-formed ones in the same response are kept.
- **The model returns a `check` value outside the permitted set.**
  Coerced to `other`, which is testable by nothing and therefore emits no
  finding.
- **The model invents a claim the client never made.** Guarded by
  requiring the quote to appear in the source text; a claim whose quote
  cannot be found is dropped and recorded.
- **A claim with a null target on a check that needs one.** Dropped.
- **The client made no claims.** Empty list, no findings, no error.
- **No API key present.** The committed claims are used. If none exist,
  extraction returns nothing and the pipeline continues — a missing key
  degrades the product, it does not break it.
- **A note that both records the client's words and the RM's opinion.**
  Only the client's part is extracted; the RM's concern is surfaced
  separately by spec 004, and where the two disagree both are shown
  (Principle IX).

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST extract claims from a client's stated
  objectives and their relationship manager's notes using **exactly one**
  model call per client.
- **FR-002**: Each claim MUST carry the client's phrasing, a check type
  from the permitted set, a target where the check needs one, its source,
  and the date it was stated where the source carries one.
- **FR-003**: The system MUST extract only claims the **client** made. A
  note recording the relationship manager's own concern MUST be skipped.
- **FR-004**: The model MUST NOT perform arithmetic, receive any figure,
  or decide whether a claim is violated (Principle V).
- **FR-005**: The system MUST test each claim in deterministic code.
- **FR-006**: An `avoid_sector` claim MUST be tested by seeding on the
  target across source fields only — never a derived theme label — and
  expanding to the look-through themes those seeds belong to.
- **FR-007**: The system MUST report both the direct exposure to the
  target and the look-through exposure of the theme it sits inside.
- **FR-008**: The system MUST emit a finding only when a threshold
  comparison in code is exceeded, with the threshold as a parameter.
- **FR-009**: Every finding MUST quote the client's own words and cite its
  source — `clients.csv` for objectives, or `rm_notes.json` with a note id.
- **FR-010**: Every cited note id MUST resolve to a row in
  `rm_notes.json`.
- **FR-011**: A claim whose quoted words cannot be found in the source
  text MUST be dropped and the rejection recorded, so a model cannot
  fabricate a claim into a finding.
- **FR-012**: Malformed model output MUST produce no findings and MUST NOT
  raise (block 4, in terms).
- **FR-013**: Claims MUST be extracted at **build time**, committed to
  disk alongside the prompt that produced them, and reused thereafter. **No
  model call may occur at demo time** (Principle VII).
- **FR-014**: Model temperature MUST be 0.
- **FR-015**: The system MUST function with no API key by using the
  committed claims.
- **FR-016**: Relationship-manager-facing copy MUST NOT contain the word
  "recommend" (Principle IX).
- **FR-017**: A claim that is checked and found not to be contradicted
  MUST be recorded as a clear result, not omitted silently.
- **FR-018**: Anything the extraction could not determine MUST be recorded
  in `unsure_about` (Principle X).
- **FR-019**: No client identifier, instrument identifier, sector, target
  or date may appear as a literal in the pipeline (Principle XI).
- **FR-020**: Given the same committed claims, findings MUST be identical
  across runs including order (Principle VII).

### Key Entities

- **Claim** — something the client said they want, refuse, or worry about,
  in their words, with a machine-testable check type, an optional target,
  its source and its date. The output of the only model call in the system.
- **Check type** — one of `avoid_sector`, `avoid_region`, `reduce_risk`,
  `refuse_realise_loss`, `needs_liquidity_by`, `other`. Determines which
  code path tests the claim. `other` is testable by nothing and emits
  nothing.
- **Contradiction** — a claim tested against the portfolio and found to be
  contradicted, with the exposure that contradicts it and the evidence
  rows behind that exposure.
- **Claims cache** — the committed artifact holding every extracted claim
  and the prompt that produced it. What makes the demo deterministic and
  what a regulator would ask to see.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The hero client's objectives yield a claim with
  `check = avoid_sector` and `target = shipping`.
- **SC-002**: That claim produces a finding reporting **42.134% ± 0.001**
  look-through exposure, and **33.20% ± 0.01** direct exposure.
- **SC-003**: Claims are also extracted from **N-025** and **N-026**.
- **SC-004**: CL-0003's note **N-005** yields a `reduce_risk` claim
  quoting her own words.
- **SC-005**: Every emitted finding contains a non-empty quote from the
  client and a source that resolves to a row in `clients.csv` or
  `rm_notes.json`.
- **SC-006**: Malformed model output produces zero findings and raises
  nothing — asserted against at least four malformed shapes.
- **SC-007**: A claim whose quote does not appear in its source text is
  dropped.
- **SC-008**: Detection performs **zero** network calls, asserted by
  running it with the model client unavailable.
- **SC-009**: Two runs over the same committed claims produce identical
  findings.
- **SC-010**: No emitted finding contains the word "recommend".
- **SC-011**: A search of the pipeline for hardcoded identifiers, sectors,
  targets or dates returns nothing outside the test suite.

---

## Assumptions

- Spec 001's `look_through` contract holds and is reused rather than
  reimplemented (block 4, CRITICAL SEPARATION).
- The claims cache is committed to the repository. Regenerating it is an
  explicit action, not a side effect of running the pipeline.
- Extraction quality is assessed by whether the required claims appear,
  not by scoring the model. Article VIII excludes model output quality
  from testing.
- The `avoid_region` check is implemented on the same seed-and-expand
  mechanism as `avoid_sector`, since region is a holdings column. It is
  not in the acceptance criteria and is therefore not asserted.
- `needs_liquidity_by` and `refuse_realise_loss` are extracted and stored
  but tested in spec 004, which owns liquidity. Storing them now costs
  nothing and avoids a second model call later.
- Model: `claude-opus-5` at `effort: low`. **Not** temperature 0 — see
  [research.md](./research.md) R5: temperature was removed from the
  Messages API and cannot be set on any current model. Determinism comes
  from the committed cache instead, which is the stronger guarantee. This
  is a live conflict with the constitution's Technology Standards and is
  flagged there for amendment.

---

## Out of Scope

- Any model call at demo time. Build time only, output committed.
- Any model involvement in arithmetic or in deciding a violation.
- Liquidity and runway testing of `needs_liquidity_by` claims — spec 004.
- Scenario repricing — spec 005.
- Scoring or evaluating model output quality (Article VIII).
- A chat interface (Principle XIII).

---

## Fallback, per block 4

If extraction proves unreliable, the three demo clients' claims are
committed as a fixture and the substitution is stated in the README.

**The architecture makes this cheap**, which is the point worth noting:
because claims are committed artifacts read from disk, the fallback and
the real path are the *same code path* — only the provenance of the file
differs. There is no separate degraded mode to build or test. The cache
records how each claim was produced, so an audit can tell them apart.

---

## Appendix — Constitution articles this spec answers to

| Article | How this spec satisfies it |
|---|---|
| IV. Nothing Is Invented | FR-011 — a claim whose quote is not in the source is dropped, so the model cannot fabricate one into a finding |
| V. Model Reads and Writes, Never Counts | FR-004, FR-005, SC-008. The model converts prose to a claim and touches nothing else |
| VI. Evidence Over Assertion | FR-009, FR-010, SC-005 |
| VII. Determinism | FR-013, FR-014, FR-020, SC-009. Build-time extraction, committed output, temperature 0 |
| IX. RM Decides | FR-016, and where a note disagrees with the data both are shown |
| X. Honest Framing | FR-017, FR-018, and the fallback stated in the README rather than hidden |
| XI. Portable By Construction | FR-019, SC-011. Targets come from claims, which come from the data |
