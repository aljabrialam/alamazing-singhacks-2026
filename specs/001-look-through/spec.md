# Feature Specification: Look-Through Concentration

**Feature Branch**: `main` (solo build, no feature branches)

**Created**: 2026-09-04

**Status**: **Draft — figures NOT yet reproduced.** See § Verification status.

**Input**: User description: block 3 of `alamazing-all-specs.md`, pasted
unmodified. Reproduced in Appendix A.

**Spec number**: 001 · **Gate**: G2 · **Depends on**: spec 000 (consumes
`client_weights`, `latest`, `snapshots`)

> **Directory naming.** `specs/001-divergence-engine/` is the spec
> bundle's umbrella feature folder — the source of `findings.md` and
> `implementation.md`. It is not a member of the fixed 000→007 sequence.
> This folder, `specs/001-look-through/`, is sequence spec 001.

---

## ⚠️ Verification status

**This specification was written while Python execution was unavailable.**
Every figure below is quoted from `.alamazing/findings.md` and block 3.
Only one has been reproduced from the data.

| Figure | Source | Status |
|---|---|---|
| CL-0019 look-through **42.134%** at latest snapshot | findings.md § 1 | ✅ **Reproduced** — spec 000 `test_spine_cl0019_from_pipeline`, twice, two independent paths |
| CL-0019 trajectory **29.41 / 29.50 / 34.08 / 41.07 / 42.13** | findings.md § 1, Trajectory | ⚠️ **Quoted, not reproduced** |
| CL-0019 `compliance_clean = True`, five bands | findings.md § 1, Why nothing flags it | ⚠️ **Quoted, not reproduced** |
| CL-0019 largest position **13.30%** vs limit 15 | block 5 acceptance | ⚠️ **Quoted, not reproduced** |
| CL-0014 Golden Harbour **29.46%** = 12.87 + 9.54 + 7.05 | findings.md § 3 | ⚠️ **Quoted, not reproduced** |
| SYN-SP-0505 `underlying_reference` exact text | block 3, findings.md § 1 | ⚠️ **Quoted, not reproduced** |
| Duplicate underlying resolves to SYN-ST-0104 and SYN-EQ-0008 | block 3 acceptance | ⚠️ **Quoted, not reproduced** |

**No task in [tasks.md](./tasks.md) may be marked complete on a quoted
figure.** Phase 0 of the plan reproduces all seven before implementation
starts, and any that does not reproduce is reported rather than
reconciled — Principle X, and the constitution's own instruction that if
something in the data looks wrong or contradictory, say so.

Recorded under Principle II: this is a stated assumption closing an open
question inside the ten-minute cap, not a guess presented as fact.

---

## Why this exists

Abdullah Al-Mansoori's portfolio respects **every** mandate band and
breaches **no** single-name limit. It is also 42% one bet.

An exception engine cannot raise this, because there is no exception. A
limit monitor cannot raise it, because no limit is exceeded. A
concentration report cannot raise it, because the exposure is split across
four instruments in three different asset classes — one of which is a
structured note whose booked classification says nothing about what it
actually references.

That is the argument the entire product rests on, and this specification
is where it becomes a number.

The mechanism is one step: **resolve a structured product to the names it
references, rather than accepting the asset class it is booked as.** Do
that, and 42.13% of Abdullah's portfolio turns out to be a single bet on
Gulf shipping and energy — against a stated objective, typed at
onboarding in 2014, of building wealth *outside the Gulf region and
outside the shipping sector*.

Nothing in this spec calls a model. It is parsing and arithmetic.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — See through the structured product (Priority: P1)

Priscilla needs to know what her client is *actually* exposed to, not what
his positions are labelled. The system resolves each holding to a theme:
an ordinary position resolves to its own sector, and a structured product
resolves to the names in its underlying reference. Exposure is then totalled
by theme at client level.

**Why this priority**: This is the hero finding and the product's central
claim. Without it there is no demo (constitution, Kill switch: "never
cut — spec 001").

**Independent Test**: Ask for the hero client's look-through at the latest
snapshot and assert the shipping-and-energy theme totals 42.134% ± 0.001,
matching the figure recorded in `.alamazing/findings.md`. Delivers value
alone: the number is the pitch.

**Acceptance Scenarios**:

1. **Given** the hero client at the latest snapshot, **When** the
   look-through is computed, **Then** the shipping-and-energy theme totals
   **42.134% ± 0.001** of client-level value.
2. **Given** a holding with no underlying reference, **When** its theme is
   resolved, **Then** the theme derives from its own sector and the
   holding is unchanged.
3. **Given** a structured product with an underlying reference, **When**
   its theme is resolved, **Then** the theme derives from the referenced
   names and **not** from its booked asset class.
4. **Given** the look-through result, **When** any theme total is read,
   **Then** the sum of all theme totals accounts for 100% of the client's
   value — no position is dropped and none is double-counted.
5. **Given** the hero client, **When** theme totals are ranked, **Then**
   the shipping-and-energy theme exceeds the 25% threshold and is flagged.

---

### User Story 2 — Say plainly that nothing is breached (Priority: P1)

The system checks every mandate band and every single-position limit, finds
nothing breached, and **states that as a positive result** alongside the
concentration finding. The two appear together: the portfolio is compliant,
*and* it is 42% one bet.

**Why this priority**: P1 and inseparable from Story 1. The concentration
figure alone is a risk report. The concentration figure next to "every
control passed" is the argument. Block 5 states the requirement in terms —
the detector must express "checked, nothing breached" as a positive
statement, because spec 001 needs it for `compliance_clean`.

**Independent Test**: Assert `compliance_clean` is `True` for the hero
client, that all five of his asset-class bands are within range, and that
his largest single position is under the mandate's limit.

**Acceptance Scenarios**:

1. **Given** the hero client, **When** every band in his mandate is
   compared to his portfolio's actual allocation, **Then** all are within
   range and `compliance_clean` is `True`.
2. **Given** the hero client, **When** his largest single position is
   compared to the mandate's single-position limit, **Then** it is below
   the limit.
3. **Given** a client with a band breach, **When** `compliance_clean` is
   computed, **Then** it is `False` — the flag is earned, never assumed.
4. **Given** `compliance_clean` is `True`, **When** the finding is
   rendered, **Then** the flag is visible in the interface and not merely
   asserted in the pitch (block 3, COMPLIANCE-CLEAN FLAG).
5. **Given** bands are defined per portfolio and exposure per client,
   **When** both are computed, **Then** neither is conflated with the
   other.

---

### User Story 3 — Name the position that doubles up (Priority: P1)

Where a structured product references names the client already holds
outright, the system says so and names both sides. This is not
diversification; it is added exposure to a position already held.

**Why this priority**: P1 because it is what makes the finding
*explicable* rather than merely true. "42% concentrated" invites argument.
"Your note's basket contains two names you already own outright" ends it.

**Independent Test**: Assert that for the hero client the duplicate-
underlying finding names the shipping single stock and the energy fund as
the positions the note references.

**Acceptance Scenarios**:

1. **Given** a structured product's underlying reference, **When** the
   referenced names are matched against the client's other holdings,
   **Then** every holding that is also referenced is named in the finding.
2. **Given** the hero client, **When** the duplicate underlying is
   detected, **Then** it names **SYN-ST-0104** and **SYN-EQ-0008**.
3. **Given** a referenced name the client does **not** hold, **When**
   matching runs, **Then** it is not reported as a duplicate, and its
   absence is not treated as an error.
4. **Given** a duplicate underlying, **When** the finding is written,
   **Then** it carries both the structured product's row and the
   duplicated holdings' rows as evidence.

---

### User Story 4 — Show how it got here (Priority: P2)

The system computes the same look-through at every snapshot in the data, so
the exposure can be read as a trajectory rather than a single number.

**Why this priority**: P2 — the finding stands without it. But a single
figure invites "was it always like that?", and the trajectory answers it:
appreciation through the March energy spike, then a step change in June
when the note settled. Two causes, both visible.

**Independent Test**: Assert the five-snapshot trajectory matches the
figures recorded in `.alamazing/findings.md` to ± 0.01.

**Acceptance Scenarios**:

1. **Given** the hero client, **When** the look-through is computed at
   every snapshot, **Then** the totals are **29.41 / 29.50 / 34.08 /
   41.07 / 42.13**, each ± 0.01.
2. **Given** a snapshot at which a position did not yet exist, **When**
   the look-through is computed, **Then** it contributes nothing and the
   computation does not fail.
3. **Given** the trajectory, **When** it is returned, **Then** snapshots
   are ordered chronologically and derived from the data, never from a
   written list.

---

### User Story 5 — One name held three ways (Priority: P2)

The same detector, run against a different client, finds a single company
held simultaneously as a bond, an equity and a structured product — three
asset classes, one credit risk.

**Why this priority**: P2 for the demo, but it is the better *technical*
demonstration of the mechanism, and it proves the detector is general
rather than fitted to one client. If a judge asks "does this only work for
Abdullah?", this is the answer.

**Independent Test**: Assert the Golden Harbour theme totals 29.46% ± 0.01
across three named instruments in three different asset classes.

**Acceptance Scenarios**:

1. **Given** the second client, **When** the look-through is computed,
   **Then** the Golden Harbour theme totals **29.46% ± 0.01**.
2. **Given** that theme, **When** its constituents are listed, **Then**
   they are **SYN-FI-0207** (12.87%), **SYN-ST-0106** (9.54%) and
   **SYN-SP-0503** (7.05%), each ± 0.01.
3. **Given** those three instruments, **When** their booked asset classes
   are read, **Then** they are three *different* classes — which is why no
   asset-class concentration check sees the exposure.
4. **Given** the detector, **When** it runs on any client in the book,
   **Then** it produces findings without that client being named in the
   code (Principle XI).

---

### Edge Cases

- **A client with no structured products.** Every theme resolves from
  sector alone. No finding unless a sector itself exceeds the threshold.
- **A structured product whose reference names nothing the client holds.**
  Theme concentration may still be reported; duplicate underlying is not.
  Absence of a duplicate is a real answer.
- **An underlying reference that does not parse** — no colon, unexpected
  separator, empty after stripping. The holding falls back to its sector
  theme, and the parse failure is recorded in `unsure_about` rather than
  silently swallowed.
- **A referenced name matching more than one holding.** All matches are
  named. Ambiguity is surfaced, not resolved by picking one.
- **A referenced name matching a holding only loosely** — e.g. an ADR of a
  name held as an ordinary share. Matched, and the looseness recorded in
  `unsure_about`.
- **A theme just below the 25% threshold.** No finding. The threshold is a
  parameter, not a literal, so it is visible and adjustable.
- **A mandate with no band for an asset class the client holds** — or a
  band for a class nobody holds. Neither is a breach
  (`.alamazing/findings.md` § Data imperfections). Absence of a row is not
  a violation.
- **A client holding several portfolios under different mandates.** Bands
  are checked per portfolio against that portfolio's own mandate;
  `compliance_clean` is true only when all of them pass.
- **A snapshot where the client holds nothing.** Empty look-through, no
  finding, no division by zero.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST resolve every holding to a theme, where a
  holding with no underlying reference resolves from its own sector and a
  holding with one resolves from the names that reference contains.
- **FR-002**: The system MUST parse an underlying reference by discarding
  any descriptive prefix before a colon, splitting the remainder on the
  separator between names, and trimming whitespace from each result.
- **FR-003**: The system MUST match each parsed name against the
  instrument names of the client's other holdings, tolerating trailing
  qualifiers such as depositary-receipt suffixes.
- **FR-004**: The system MUST total resolved exposure by theme at
  **client** level, computed from the client-level weights established in
  spec 000 and never from the per-portfolio weight column.
- **FR-005**: The system MUST flag any theme exceeding a threshold
  supplied as a parameter, defaulting to 25% of client-level value.
- **FR-006**: The system MUST emit a theme-concentration finding naming the
  theme, its total, and every holding contributing to it.
- **FR-007**: The system MUST emit a duplicate-underlying finding when a
  structured product references names the client already holds outright,
  naming the product and each duplicated holding.
- **FR-008**: The system MUST NOT describe a duplicate underlying as
  diversification. It is added exposure to a position already held.
- **FR-009**: The system MUST compare every asset-class band of each of the
  client's portfolios against that portfolio's actual allocation, and every
  single position against the mandate's single-position limit.
- **FR-010**: The system MUST set `compliance_clean` to true only when
  every band is respected and no single position exceeds its limit, and
  MUST compute this explicitly rather than inferring it from the absence of
  a breach elsewhere.
- **FR-011**: The system MUST treat a missing mandate band as neither a
  breach nor an error.
- **FR-012**: The system MUST compute bands at portfolio level and
  concentration at client level, and MUST NOT conflate the two.
- **FR-013**: The system MUST compute the look-through at every snapshot in
  the data, in chronological order derived from the data.
- **FR-014**: Every finding MUST carry its evidence: source file, row
  identifiers and values, conforming to the recorded Finding schema
  (`specs/001-divergence-engine/contracts/finding.schema.json`).
- **FR-015**: A finding that cannot produce evidence MUST NOT be emitted
  (Principle VI).
- **FR-016**: Every finding MUST record what would change the answer in
  `unsure_about`, including any name matched loosely and any reference that
  failed to parse.
- **FR-017**: Relationship-manager-facing copy MUST NOT contain the word
  "recommend" (Principle IX).
- **FR-018**: The system MUST NOT call a language model. All resolution,
  matching and arithmetic MUST be deterministic code (Principle V).
- **FR-019**: Identical inputs MUST produce identical findings, including
  their order (Principle VII).
- **FR-020**: No client identifier, instrument identifier, sector name,
  theme name, threshold or date may appear as a literal in the pipeline.
  All MUST be arguments or derived from data (Principle XI).
- **FR-021**: The system MUST emit findings for any client in the book, not
  only the three demo clients.

### Key Entities

- **Theme** — what a position is *actually* exposed to, as opposed to how
  it is booked. Derived from a holding's sector, or from the names inside a
  structured product's underlying reference. The unit of concentration.
- **Underlying reference** — the free text on a structured product naming
  the instruments it is written against. For the hero client's note this is
  a worst-of basket of three names, two of which he holds outright.
- **Theme concentration** — a theme's total share of client-level value,
  and the holdings comprising it.
- **Duplicate underlying** — the relationship between a structured product
  and a holding it references. Not diversification.
- **Mandate band** — the minimum, target and maximum share for one asset
  class under one mandate, plus that mandate's single-position limit.
  Applies per portfolio.
- **Compliance verdict** — the explicit result of checking every band and
  every position limit. A positive statement when nothing breaches, not the
  absence of a finding.
- **Finding** — as defined by the recorded Finding schema. This spec emits
  `kind: "D3"` (hidden-when-split).

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The hero client's shipping-and-energy theme totals **42.134%
  ± 0.001** at the latest snapshot, matching `.alamazing/findings.md`.
  Asserted with tolerance, never equality.
- **SC-002**: `compliance_clean` is **True** for the hero client, with all
  five asset-class bands within range and the largest single position
  below the mandate limit.
- **SC-003**: The duplicate-underlying finding for the hero client names
  exactly **SYN-ST-0104** and **SYN-EQ-0008**.
- **SC-004**: The hero client's trajectory across the five snapshots is
  **29.41 / 29.50 / 34.08 / 41.07 / 42.13**, each ± 0.01.
- **SC-005**: The second client's Golden Harbour theme totals **29.46% ±
  0.01**, comprising **SYN-FI-0207** 12.87%, **SYN-ST-0106** 9.54% and
  **SYN-SP-0503** 7.05%, each ± 0.01, across three different booked asset
  classes.
- **SC-006**: Theme totals account for 100% ± 0.001 of client-level value
  for every client at every snapshot — nothing dropped, nothing
  double-counted.
- **SC-007**: Every emitted finding carries at least one evidence entry
  naming a file and one or more row identifiers, and validates against the
  recorded Finding schema.
- **SC-008**: No emitted finding contains the word "recommend".
- **SC-009**: Two consecutive runs produce byte-identical findings.
- **SC-010**: A search of the pipeline for hardcoded client identifiers,
  instrument identifiers, sectors, dates or market series returns nothing
  outside the test suite.
- **SC-011**: The detector runs over all 20 clients without error and
  without any client being named in the code.

---

## Assumptions

- Spec 000's contract holds. This spec consumes `client_weights`,
  `snapshots` and `latest`, and adds no filesystem or model access.
- The 25% concentration threshold comes from block 3. It is a parameter
  with that default, not a constant, so it is visible and adjustable — and
  so the same detector answers "what about 20%?" on stage.
- The `theme` for a resolved structured product is derived from the
  referenced names. Where two references share a name, they share a theme;
  the precise naming rule is an implementation concern recorded in
  [plan.md](./plan.md), not a requirement.
- Name matching tolerates trailing qualifiers (an ADR of a name held as an
  ordinary share is the same underlying exposure). Every loose match is
  recorded in `unsure_about` rather than presented as certain.
- Mandate bands are per portfolio; `.alamazing/implementation.md` step 7
  states this and spec 003 relies on it. This spec computes the same
  comparison for `compliance_clean` and spec 003 will reuse rather than
  duplicate it.
- `.alamazing/findings.md` records CL-0019's largest position as 13.30%
  and CL-0003's as 26.06%. Only the mandate's limit is compared against;
  those figures are checks on the arithmetic, not inputs to it.
- Float sums are compared with tolerance throughout.

---

## Out of Scope

Per Principle XIII, and not to be revisited:

- **Any model call.** Spec 002 is the only detector that needs one.
- Claim extraction from prose. That is spec 002, and it consumes this
  spec's `look_through`.
- Breach classification into drift / client-directed / inherited. That is
  spec 003. This spec computes only the boolean compliance verdict it needs
  for `compliance_clean`.
- Liquidity, runway and unanswered questions — spec 004.
- Scenario repricing — spec 005.
- Ranking findings, writing briefs, or any output artifact — spec 006.
- Charts. A chart without a finding attached is decoration (Principle I).
- A portfolio optimiser, or any suggestion of what to hold instead. The
  system proposes and explains; Priscilla decides (Principle IX).

---

## Known inconsistency in the recorded artifacts

Reported rather than worked around (Principle X):

**The Finding schema's `kind` enum admits only D1–D4**
(`specs/001-divergence-engine/contracts/finding.schema.json`), but
`.alamazing/implementation.md` and `RUN-SHEET.md` both specify detectors
**D5** (unanswered question) and **D6** (scenario), in specs 004 and 005.

This does not block spec 001, which emits `D3`. It will block spec 004 the
moment a finding is validated against the schema. Flagged now, to be
resolved when spec 004 is specified — by extending the enum, which is the
obvious fix, but the decision belongs to that spec and not to this one.

---

## Appendix A — Source block

Block 3 of `alamazing-all-specs.md`, pasted unmodified into
`/speckit.specify`. Its ACCEPTANCE list appears in Success Criteria above,
with the tolerances preserved and the float-equality prohibition carried
into SC-001, SC-004 and SC-005.

## Appendix B — Constitution articles this spec answers to

| Article | How this spec satisfies it |
|---|---|
| I. Demo Primacy | This is the hero finding. It reaches the screen as the mandate panel and the headline figure |
| III. The Spine Rule | SC-001 is the spine, now reached through `look_through` rather than a raw weight sum |
| IV. Nothing Is Invented | No external data; the underlying reference is read from `instruments.csv` |
| V. Model Never Counts | FR-018. No model call in this spec |
| VI. Evidence Over Assertion | FR-014, FR-015, SC-007. A detector that cannot produce evidence produces nothing |
| VII. Determinism | FR-019, SC-009 |
| VIII. Test Pyramid | Unit assertions on reference parsing, name matching, theme resolution and band comparison; integration assertions SC-001, SC-004, SC-005 against recorded figures |
| IX. RM Decides | FR-008, FR-017. No "recommend"; no suggestion of what to hold instead |
| X. Honest Framing | FR-016, the parse-failure edge case, the verification-status table, and the schema inconsistency above |
| XI. Portable By Construction | FR-020, FR-021, SC-010, SC-011. The threshold is a parameter; no theme or client is named in code |
| XII. Vertical Slices | The detector returns findings the moment it runs; no UI needed to demonstrate it |
| XIV. Design Is A Quarter | `compliance_clean` must be *visible*, per block 3 — not merely computed |
