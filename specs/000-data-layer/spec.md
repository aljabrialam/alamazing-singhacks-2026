# Feature Specification: Data Layer

**Feature Branch**: `000-data-layer`

**Created**: 2026-09-04

**Status**: Draft

**Input**: User description: "Build the data layer for the Divergence Engine." (block 2 of `alamazing-all-specs.md`, reproduced verbatim in Appendix A)

**Spec number**: 000 — first in the fixed order 000 → 001 → ... → 007. Gate: **G1**.

---

## Why this exists

Every finding the Divergence Engine emits is a number, and every number is
computed from the twelve Julius Baer files in `data/`. This specification
builds the one layer all six detectors read from. If it is wrong, every
figure downstream is wrong in a way that looks plausible — which is worse
than a crash.

It also fixes, once, the single most expensive mistake available in this
dataset: `weight_pct` in `holdings.csv` is scoped to a **portfolio**, not
to a **client**. A client holding several portfolios (CL-0017 holds three)
returns a believable but incorrect exposure if that column is summed.
Client-level exposure is recomputed from `market_value_usd`, and this
specification is the only place that recomputation is written.

No model is called anywhere in this spec. It is arithmetic and joins.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Load the book once, correctly (Priority: P1)

Priscilla's relationship-manager workbench is built at build time from a
folder of files. The pipeline must open that folder, read all twelve
sources, join them so that each holding row knows its instrument's
underlying reference and its portfolio's mandate, and hand back one object
that every detector can query. Nothing is dropped, nothing is silently
coerced, and anything the files cannot answer is recorded rather than
guessed.

**Why this priority**: Nothing else in the project can start. This is the
Spine Rule (Principle III) made into a module — the 42.134% figure the
whole product rests on is reachable only from a correctly loaded book.

**Independent Test**: Load the supplied folder and assert the row counts
(1,015 holdings, 20 clients, 24 portfolios, 28 notes) and that the joined
columns are present on every holdings row. Delivers value on its own: the
book is queryable in a REPL.

**Acceptance Scenarios**:

1. **Given** the twelve files in `data/`, **When** the book is loaded,
   **Then** it exposes 1,015 holdings rows, 20 clients, 24 portfolios and
   28 relationship-manager notes.
2. **Given** the book is loaded, **When** any holdings row is inspected,
   **Then** it carries its instrument's `underlying_reference`,
   `sustainability_excluded` and `concentration_limit_applies`, and its
   portfolio's `mandate_code`.
3. **Given** an `asset_class` column exists in both `holdings.csv` and
   `instruments.csv`, **When** the two are joined, **Then** both values
   remain available under distinct, suffixed names and neither is lost.
4. **Given** the book is loaded, **When** the set of snapshot dates is
   requested, **Then** it is derived from the data and returned in
   ascending order — never read from a list written into the source.

---

### User Story 2 — Client-level exposure, not portfolio-level (Priority: P1)

An exposure figure quoted to a client must be a share of everything that
client holds with the bank, across every portfolio. The layer provides one
function that returns each of a client's holdings at a given snapshot with
its weight recomputed as its share of that client's total market value in
USD.

**Why this priority**: This is the recorded trap (Technology Standards,
and the "trap that will cost you an hour" in `.alamazing/implementation.md`).
It is P1 alongside Story 1 because a book that loads correctly and a weight
that is computed incorrectly produce a demo that is confidently wrong.

**Independent Test**: For a client with one portfolio, the recomputed
weights and `weight_pct` agree. For a client with several, they diverge,
and the recomputed set sums to 100% while the raw column does not. Both
are asserted.

**Acceptance Scenarios**:

1. **Given** a client and a snapshot date, **When** client weights are
   requested, **Then** every returned weight is that holding's
   `market_value_usd` as a percentage of the client's total
   `market_value_usd` at that date, and the weights sum to 100%.
2. **Given** a client holding exactly one portfolio, **When** client
   weights are compared to `weight_pct`, **Then** they agree within
   rounding tolerance.
3. **Given** a client holding more than one portfolio, **When** the raw
   `weight_pct` column is summed, **Then** it exceeds 100%, and the
   recomputed weights still sum to 100% — demonstrating the trap rather
   than describing it.
4. **Given** the hero client at the latest snapshot, **When** the weights
   of the four exposure instruments are summed, **Then** the total is
   **42.134 ± 0.001** (`.alamazing/findings.md`, § Abdullah Al-Mansoori).

---

### User Story 3 — What changed between two dates (Priority: P2)

A brief must be able to say not just what the portfolio is, but what moved
and who moved it. The layer compares a client's holdings at two snapshot
dates, per instrument, in both value and weight, and can rank that
comparison by the size of the value change.

**Why this priority**: P2 because the concentration finding (spec 001)
stands without it, but the *trajectory* — 29.41% in December to 42.13% in
August — is what turns a number into a story, and spec 005 consumes the
same comparison.

**Independent Test**: Compare the hero client between the pre-conflict and
latest snapshots and assert that a position issued in between appears with
a zero opening value rather than being dropped by the join.

**Acceptance Scenarios**:

1. **Given** two snapshot dates, **When** a client's holdings are compared,
   **Then** every instrument held at either date appears exactly once, with
   its value and weight at both dates and the change in each.
2. **Given** an instrument that did not exist at the earlier date,
   **When** it appears in the comparison, **Then** its earlier value and
   weight are zero — not absent, not null.
3. **Given** an instrument that was sold before the later date, **When** it
   appears in the comparison, **Then** its later value and weight are zero
   and the row is retained.
4. **Given** a comparison, **When** attribution is requested, **Then** the
   same rows are returned ordered by the absolute size of the value change,
   largest first.

---

### User Story 4 — Which events touched this client (Priority: P2)

The event log is the only permitted account of what happened in the world.
The layer returns the events falling between two dates, and the subset of
those whose stated transmission channels intersect the sectors and
sub-asset-classes the client actually holds.

**Why this priority**: P2 for build order, but it carries Principle IV.
Every cause cited in a brief must resolve to a row in `event_log.csv`, and
the match must be reproducible — so it is a keyword match in code, never a
model deciding what looks relevant.

**Independent Test**: Ask which events touched the hero client between the
pre-conflict and latest snapshots; assert both the Strait closure and the
blockade are returned, by date.

**Acceptance Scenarios**:

1. **Given** two dates, **When** events between them are requested,
   **Then** every event whose date falls in the inclusive range is
   returned, ordered by date, with its description and severity intact
   from the file.
2. **Given** a client and a date range, **When** touching events are
   requested, **Then** an event is included only when a comma-separated
   term in its stated transmission channels matches, case-insensitively,
   one of the sectors or sub-asset-classes that client holds.
3. **Given** the hero client and the range from the pre-conflict snapshot
   to the latest, **When** touching events are requested, **Then** the
   result includes **2026-03-04** (Strait of Hormuz closure) and
   **2026-08-05** (naval blockade reimposed) — both rows of
   `event_log.csv`.
4. **Given** any returned event, **When** it is cited downstream, **Then**
   its date and description are those of a real row in the file, carried
   through unmodified.

---

### User Story 5 — Say what the data cannot tell you (Priority: P2)

The files contain known imperfections. The layer records each one it meets,
with enough detail to name it on stage, and never drops or repairs a row to
make a number tidier.

**Why this priority**: Julius Baer wrote this into the brief — noticing is
worth more than quietly working around it (Principle X). It is P2 only
because the recording, not the display, belongs here.

**Independent Test**: Load the book and assert the imperfection record is
non-empty and that the known missing cost basis is among the entries, cited
by client and instrument.

**Acceptance Scenarios**:

1. **Given** a holdings row with no unrealised profit-and-loss percentage,
   **When** the book is loaded, **Then** the row is retained and an
   imperfection is recorded naming its file, client, instrument and the
   field that is missing.
2. **Given** a holdings row whose valuation date differs from its snapshot
   date, **When** the book is loaded, **Then** the row is retained and the
   discrepancy is recorded with both dates.
3. **Given** an instrument identifier appearing in holdings but not in the
   instrument reference file, **When** the book is loaded, **Then** the row
   is retained and the orphan is recorded.
4. **Given** the supplied folder, **When** the book is loaded, **Then** the
   imperfection record is non-empty and includes the industrial holding
   transferred in without a cost basis (CL-0003 / SYN-ST-0107).

---

### Edge Cases

- **A client with several portfolios.** Weights are recomputed across all
  of them at client level. Asserted directly, because this is the trap.
- **Portfolios in different base currencies.** Client-level arithmetic uses
  the USD column only; base and local currency columns are never summed
  across portfolios.
- **A position that appears between two snapshots.** The structured note
  settles in June and has no earlier row. It appears in the comparison with
  a zero opening value.
- **A position that disappears.** Retained with a zero closing value.
- **A client with no holdings at a requested date.** An empty result with
  the expected columns, not an error and not a division by zero.
- **A snapshot date not present in the data.** Rejected explicitly rather
  than silently returning nothing.
- **An event whose transmission channels match nothing the client holds.**
  Excluded. Absence of a match is a real answer.
- **A mandate band for an asset class no client holds.** Not an error, not
  a breach — recorded as an imperfection at most (`.alamazing/findings.md`,
  § Data imperfections).
- **A note with no matching client.** Retained and recorded, never
  attached to the wrong client.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST load all twelve supplied data files from a
  directory given as an argument, and expose each as a queryable table plus
  the relationship-manager notes as an ordered list.
- **FR-002**: The system MUST expose 1,015 holdings rows, 20 clients, 24
  portfolios and 28 notes when given the supplied folder.
- **FR-003**: The system MUST attach to every holdings row its instrument's
  underlying reference, sustainability exclusion flag and
  concentration-limit flag, preserving both the holding's and the
  instrument's asset class under distinct names.
- **FR-004**: The system MUST attach to every holdings row the mandate code
  of the portfolio that holds it.
- **FR-005**: The system MUST derive the set of snapshot dates from the
  loaded data and return them in ascending order. No snapshot date may be
  written as a literal anywhere in the pipeline.
- **FR-006**: The system MUST compute a client's exposure weights from
  `market_value_usd` as a share of that client's total across all of that
  client's portfolios at a given snapshot. It MUST NOT sum the per-portfolio
  `weight_pct` column to reach a client-level figure.
- **FR-007**: Client-level weights returned for a client and date MUST sum
  to 100%.
- **FR-008**: The system MUST compare a client's holdings at two snapshot
  dates per instrument, retaining instruments present at only one date with
  a zero value and weight at the other, and reporting the change in both
  value and weight.
- **FR-009**: The system MUST be able to return that comparison ordered by
  the absolute size of the change in value, largest first.
- **FR-010**: The system MUST return all events whose date falls within an
  inclusive range of two dates, ordered by date, with their fields carried
  through from the file unmodified.
- **FR-011**: The system MUST select the events touching a client by
  splitting each event's stated transmission channels on commas and matching
  the resulting terms, case-insensitively and after trimming, against the
  distinct sectors and sub-asset-classes that client holds. The match MUST
  be performed in code and MUST NOT involve a model.
- **FR-012**: The system MUST record, rather than remove or repair, every
  imperfection it meets: a missing unrealised profit-and-loss percentage, a
  valuation date differing from its snapshot date, and an instrument
  identifier absent from the instrument reference file. Each record MUST
  name the file, the identifiers of the affected row, and the field
  concerned.
- **FR-013**: The system MUST NOT drop any input row for any reason.
- **FR-014**: Only the load function may read from disk. Every other
  function MUST operate on an already-loaded book.
- **FR-015**: No function in this layer may call a language model. All
  arithmetic MUST be deterministic and performed in code (Principle V).
- **FR-016**: No client identifier, instrument identifier, sector name,
  date or market series identifier may appear as a literal in the pipeline.
  All four MUST be arguments (Principle XI).
- **FR-017**: Identical inputs MUST produce identical outputs on every run,
  including row order (Principle VII).
- **FR-018**: The system MUST reject a request for a snapshot date that is
  not present in the data, rather than returning an empty result that could
  be mistaken for a real answer.
- **FR-019**: There MUST NOT be a file-upload capability (Principle XI).

### Key Entities

- **Book** — everything the bank knows, as loaded from one folder: clients,
  portfolios, holdings across five snapshots, instruments, mandate bands,
  transactions, credit facilities, commitments, planned cash needs, market
  context, the event log, and the relationship manager's notes. Carries its
  own list of recorded imperfections. It is the single argument every
  detector takes.
- **Client** — a person, with age, life stage, stated objectives, source of
  wealth, risk profile and tax domicile. Holds one or more portfolios.
- **Portfolio** — a mandate code and a base currency, belonging to exactly
  one client. Bands are checked at this level; exposure is not.
- **Holding** — one instrument in one portfolio at one snapshot date, with
  its market value in local, base and USD terms, its cost basis where one
  exists, its liquidity tier and its per-portfolio weight.
- **Instrument** — the reference record for a security, including its
  underlying reference where it is a structured product, its sustainability
  exclusion, whether a concentration limit applies, and its price at each
  snapshot.
- **Event** — a dated occurrence with a region, a description, its stated
  transmission channels and a severity. Authoritative for anything that
  happened (Principle IV).
- **Note** — one dated record of a conversation between the relationship
  manager and a client, in her words. The only source of what the client
  actually said.
- **Imperfection** — a recorded defect in the input: which file, which row,
  which field, and what is wrong with it. Feeds the uncertainty screen.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Loading the supplied folder yields exactly 1,015 holdings
  rows, 20 clients, 24 portfolios and 28 notes.
- **SC-002**: The hero client's four exposure instruments sum to **42.134
  ± 0.001** of that client's holdings at the latest snapshot, matching the
  figure recorded in `.alamazing/findings.md`. Asserted with tolerance,
  never equality.
- **SC-003**: Client-level weights sum to 100% ± 0.001 for every client at
  every snapshot date in the data — all 20 clients, not a sample.
- **SC-004**: For at least one client holding several portfolios, the summed
  per-portfolio weight column and the recomputed client-level weights
  differ measurably, and the difference is asserted in a test.
- **SC-005**: The events touching the hero client between the pre-conflict
  and latest snapshots include the two dated rows 2026-03-04 and
  2026-08-05, and every returned event resolves to a row of
  `event_log.csv`.
- **SC-006**: The imperfection record is non-empty and names the industrial
  holding carrying no cost basis, by client and instrument.
- **SC-007**: No input row is lost: holdings row count after joining equals
  the row count before.
- **SC-008**: Two consecutive loads of the same folder produce identical
  output, including row order.
- **SC-009**: A search of the pipeline for hardcoded client identifiers,
  instrument identifiers, dates or market series returns nothing outside
  the test suite.
- **SC-010**: The whole layer loads and answers every acceptance query in
  under five seconds on a laptop, so the build stays inside its time box.

---

## Assumptions

- The twelve files in `data/` are the complete and authoritative universe.
  No external market data, no model recollection (Principle IV).
- `data/` is read-only. It is never written to, never repaired in place.
- Snapshot dates are treated positionally — earliest, pre-conflict, latest
  — and read from the data. The demo's dates are recorded in
  `.alamazing/implementation.md` for readability only; the code never names
  them.
- Cross-portfolio arithmetic uses `market_value_usd`, which the data
  dictionary states is already converted. No currency conversion is
  performed here.
- Mandate bands apply per portfolio; exposure concentration applies per
  client. The layer supports both and never conflates them.
- Notes are attributed by the client identifier in the notes file itself.
- Event-to-client matching is a substring keyword match on comma-separated
  transmission terms. It is deliberately simple so it is reproducible; a
  false positive is visible in the evidence panel and correctable by the
  relationship manager, and a model is never asked to judge relevance.
- Float sums are compared with tolerance throughout. The spine figure is
  42.1343 or 42.1344 depending on summation order; both are correct.
- This layer emits no relationship-manager-facing copy, so the prohibition
  on the word "recommend" has nothing to constrain here; it binds specs 001
  onward.

---

## Out of Scope

Per Principle XIII, and not to be revisited:

- File upload, or any user-supplied data path at run time.
- A database, a schema or a migration. Files on disk.
- Any detector logic. This layer computes weights, comparisons and event
  matches; it decides nothing. Findings begin at spec 001.
- Any language-model call.
- Currency conversion, price sourcing, or any market data beyond
  `market_context.csv`.
- Caching, lazy loading or performance work. The whole book is under two
  megabytes.

---

## Appendix A — Source block

This specification was written from block 2 of `alamazing-all-specs.md`,
pasted unmodified into `/speckit.specify`. That block's ACCEPTANCE list is
reproduced in Success Criteria above, with the float-tolerance requirement
preserved verbatim in SC-002.

## Appendix B — Constitution articles this spec answers to

| Article | How this spec satisfies it |
|---|---|
| III. The Spine Rule | SC-002 is the spine figure, reproduced from raw files |
| IV. Nothing Is Invented | FR-010, FR-011; the event log is carried through unmodified |
| V. The Model Reads and Writes | FR-015; no model call exists in this layer |
| VI. Evidence Over Assertion | FR-012; imperfections name file, row and field |
| VII. Determinism | FR-017, SC-008 |
| VIII. Test Pyramid | Unit assertions on weight recomputation and event matching; one integration assertion, SC-002, against a recorded figure |
| X. Honest Framing | FR-012, FR-013, SC-006; imperfections are recorded, not smoothed |
| XI. Portable By Construction | FR-005, FR-016, FR-019, SC-009 |
| XII. Vertical Slices | The layer is queryable in a REPL the moment it loads |
