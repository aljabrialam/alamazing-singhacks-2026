# Tasks: Look-Through Concentration (spec 001)

**Input**: Design documents from `/specs/001-look-through/`
**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md) · spec 000 complete and verified (`g1`)

**Gate**: G2 · **Time box**: 75 minutes (declared overrun against the
60-minute budget — see plan.md § Time box) · **Cut status**: never cut

**Tests are required**, not optional (Article VIII). This spec's budget:
**~5 unit + 3 integration**, of which two are named in the constitution's
required-assertions table — `test_lookthrough_cl0019` and
`test_lookthrough_cl0014`.

---

## ⚠️ Phase 0 is blocking

**Seven figures in [spec.md](./spec.md) are quoted from
`.alamazing/findings.md` and have not been reproduced.** Python execution
was unavailable when these documents were written.

**No task below Phase 0 may start, and no task may be ticked on a quoted
figure.** If a figure does not reproduce, it is reported — not reconciled,
not quietly adjusted. Principle X, and the constitution's own instruction:
if something in the data looks wrong or contradictory, say so.

---

## Phase 0 — Reproduce every figure (BLOCKING)

- [ ] T001 Print the `underlying_reference` of every holding in the book that has one, with the holder's client id, and confirm the hero client's note reads as block 3 records it — resolves plan.md R6
- [ ] T002 Parse the hero client's reference and match the resulting names against `instrument_name` of his other holdings, confirming the match reaches SYN-ST-0104 and SYN-EQ-0008 — resolves R1, the riskiest assumption in this spec
- [ ] T003 Compute the hero client's four-instrument look-through at all five snapshots and compare to 29.41 / 29.50 / 34.08 / 41.07 / 42.13 — resolves R2, SC-004
- [ ] T004 Compute the hero client's asset-class allocation per portfolio against his mandate's bands, and his largest single position against the single-position limit, comparing to the five bands and 13.30% recorded in findings.md — resolves R3, SC-002
- [ ] T005 Compute CL-0014's Golden Harbour total across SYN-FI-0207, SYN-ST-0106 and SYN-SP-0503, confirm 29.46 / 12.87 / 9.54 / 7.05, and print each instrument's booked asset class to confirm they are three different classes — resolves R4, SC-005
- [ ] T006 Print the distinct `sector` of the hero client's four exposure instruments to determine whether theme-by-sector splits the 42% figure, then decide the theme-naming approach from plan.md R5's three candidates — resolves R5, the one open design decision
- [ ] T007 Write `specs/001-look-through/research.md` recording all seven resolutions with the query that resolved each, in the shape of spec 000's research file, and state plainly any figure that did not reproduce

---

## Phase 1 — Design artifacts

- [ ] T008 Write `specs/001-look-through/data-model.md`: the `theme` column, the theme-total frame, the compliance verdict, and the two Finding shapes this spec emits
- [ ] T009 Write `specs/001-look-through/contracts/look-through.md` fixing `look_through`, `detect` and the shared band comparison before spec 002 consumes them
- [ ] T010 Write `specs/001-look-through/quickstart.md` with each acceptance figure as a runnable block and its expected output
- [ ] T011 Write `specs/001-look-through/checklists/requirements.md` and run the spec-quality validation, recording what failed on the first pass
- [ ] T012 Re-run the post-design constitution check in plan.md, with particular attention to Article XI once R5 is decided — candidate approach 3 would pass the grep while violating the intent

---

## Phase 2 — Foundational: shared band comparison

**Blocks User Story 2.** Consumed by this spec for a boolean verdict and by
spec 003 for breach classification. Written once, per plan.md § Structure
Decision.

- [ ] T013 Implement the per-portfolio asset-class allocation in `pipeline/mandate.py`, computed within each portfolio and never across a client's portfolios (FR-012)
- [ ] T014 Implement the band comparison in `pipeline/mandate.py`, joining `mandates` on the portfolio's `mandate_code` and reporting each asset class as below minimum, within range, or above maximum
- [ ] T015 Implement the single-position limit check in `pipeline/mandate.py` against `max_single_position_pct`
- [ ] T016 Treat a missing mandate band as neither breach nor error in `pipeline/mandate.py` — absence of a row is not a violation (FR-011, `.alamazing/findings.md` § Data imperfections)
- [ ] T017 [P] **Unit assertion 1** — `tests/test_mandate.py::test_band_comparison_classifies_all_three_cases` asserts a within-range class, a below-minimum class and an above-maximum class are each identified correctly
- [ ] T018 [P] **Unit assertion 2** — `tests/test_mandate.py::test_missing_band_is_not_a_breach` asserts an asset class with no band row produces no breach and no error

---

## Phase 3 — User Story 1: See through the structured product (P1)

**Goal**: Every holding resolved to what it is actually exposed to, and
exposure totalled by theme at client level.

**Independent test**: `pytest tests/test_lookthrough.py -k cl0019` passes
and the hero client's theme totals 42.134% ± 0.001.

**Budget**: 25 minutes.

- [ ] T019 [US1] Implement the reference parser in `pipeline/divergence/d3_hidden.py`: discard any prefix before a colon, split the remainder on the name separator, strip whitespace, and return the names sorted for determinism (FR-002)
- [ ] T020 [US1] Return the sector-theme fallback and record the failure for `unsure_about` when a reference does not parse, in `pipeline/divergence/d3_hidden.py` — degrade, never throw (FR-016)
- [ ] T021 [US1] Implement name matching in `pipeline/divergence/d3_hidden.py`, tolerating trailing qualifiers such as a depositary-receipt suffix, and recording every loose match for `unsure_about` (FR-003, FR-016)
- [ ] T022 [US1] Implement `look_through(book, client_id, date)` in `pipeline/divergence/d3_hidden.py`, adding a `theme` column to `client_weights`'s output by the approach decided in T006, returning every row rather than totals (FR-001, FR-004)
- [ ] T023 [US1] Ensure a structured product contributes its weight to exactly one theme, never once per referenced name, in `pipeline/divergence/d3_hidden.py` — double-counting inflates every figure plausibly
- [ ] T024 [US1] **Integration assertion 1** — `tests/test_lookthrough.py::test_lookthrough_cl0019` asserts the hero client's shipping-and-energy theme totals `pytest.approx(42.134, abs=0.001)`, citing `.alamazing/findings.md` § 1. Named in Article VIII's required table
- [ ] T025 [P] [US1] **Unit assertion 3** — `tests/test_lookthrough.py::test_reference_parsing` asserts the prefix is discarded, the names split, whitespace stripped, and that an unparseable reference falls back to sector rather than raising
- [ ] T026 [P] [US1] **Unit assertion 4** — `tests/test_lookthrough.py::test_theme_totals_account_for_everything` asserts theme totals sum to 100% ± 0.001 for all 20 clients at all 5 snapshots, catching double-counting (SC-006)

---

## Phase 4 — User Story 2: Say plainly that nothing is breached (P1)

**Goal**: `compliance_clean` as an earned positive, not the absence of a
negative. This flag is the pitch.

**Independent test**: `compliance_clean` is `True` for the hero client with
all five bands in range, and `False` for a client with a known breach.

**Budget**: 10 minutes (the comparison itself is Phase 2).

- [ ] T027 [US2] Compute `compliance_clean` in `pipeline/divergence/d3_hidden.py` from `pipeline/mandate.py`'s verdict, true only when every band of every one of the client's portfolios is respected and no single position exceeds its limit (FR-010)
- [ ] T028 [US2] Attach `compliance_clean` to every finding this spec emits, so the flag travels with the concentration figure rather than being computed separately by the interface (block 3, COMPLIANCE-CLEAN FLAG)
- [ ] T029 [US2] **Integration assertion 2** — `tests/test_lookthrough.py::test_compliance_clean_cl0019` asserts `compliance_clean is True` for the hero client, that all five asset-class bands are within range, and that his largest single position is below the mandate limit (SC-002)
- [ ] T030 [P] [US2] **Unit assertion 5** — `tests/test_lookthrough.py::test_compliance_clean_is_earned` asserts the flag is `False` for a client with a known band breach, so a defaulting-true flag cannot pass

---

## Phase 5 — User Story 3: Name the position that doubles up (P1)

**Goal**: Name both sides of the duplication, and never call it
diversification.

**Independent test**: The duplicate finding for the hero client names
exactly SYN-ST-0104 and SYN-EQ-0008.

**Budget**: 10 minutes.

- [ ] T031 [US3] Emit the duplicate-underlying finding in `pipeline/divergence/d3_hidden.py`, naming the structured product and every holding it references, with `kind: "D3"` per the recorded Finding schema (FR-007)
- [ ] T032 [US3] Attach evidence to the duplicate finding in `pipeline/divergence/d3_hidden.py` — the product's row and each duplicated holding's rows, by file and row identifier (FR-014)
- [ ] T033 [US3] Emit no finding rather than an empty one when a reference matches nothing the client holds, in `pipeline/divergence/d3_hidden.py` (FR-015, Principle VI)
- [ ] T034 [US3] Write the finding's `headline` and `detail` in `pipeline/divergence/d3_hidden.py` without the word "recommend" and without describing the duplication as diversification (FR-008, FR-017)
- [ ] T035 [US3] **Integration assertion 3** — `tests/test_lookthrough.py::test_duplicate_underlying_cl0019` asserts the finding names exactly SYN-ST-0104 and SYN-EQ-0008 and carries evidence for each (SC-003)

---

## Phase 6 — User Story 4: Show how it got here (P2)

**Goal**: The exposure as a trajectory, so "was it always like that?" has
an answer.

**Independent test**: The five-snapshot trajectory matches the recorded
figures to ± 0.01.

**Budget**: 5 minutes.

- [ ] T036 [US4] Implement the trajectory in `pipeline/divergence/d3_hidden.py` by computing `look_through` at every snapshot from `snapshots(book)`, in chronological order derived from the data (FR-013)
- [ ] T037 [US4] Attach the trajectory to the theme-concentration finding in `pipeline/divergence/d3_hidden.py`, so the interface renders a cause rather than a single number
- [ ] T038 [US4] **Integration assertion 4** — `tests/test_lookthrough.py::test_trajectory_cl0019` asserts the five totals against `pytest.approx(..., abs=0.01)`, citing findings.md § 1 Trajectory (SC-004)

---

## Phase 7 — User Story 5: One name held three ways (P2)

**Goal**: Prove the detector is general, not fitted to one client.

**Independent test**: CL-0014's Golden Harbour theme totals 29.46% ± 0.01
across three different booked asset classes.

**Budget**: 5 minutes — the detector already exists; this is a second
client through it.

- [ ] T039 [US5] Extend `tests/conftest.py` with CL-0014's constants — the client id and the three Golden Harbour instrument ids — keeping every identifier in `tests/` where the portability grep permits it
- [ ] T040 [US5] **Integration assertion 5** — `tests/test_lookthrough.py::test_lookthrough_cl0014` asserts the Golden Harbour theme totals `pytest.approx(29.46, abs=0.01)` across the three instruments at 12.87 / 9.54 / 7.05, and that their booked asset classes are three *different* values. Named in Article VIII's required table
- [ ] T041 [US5] Run `detect` over all 20 clients and confirm it completes without error and without any client being named in the code (SC-011, FR-021)

---

## Phase 8 — Definition of Done

**No refactoring.** Verification only.

- [ ] T042 Run `pytest tests/ -v` and paste the output into the completion report — item 1
- [ ] T043 Confirm every acceptance figure matches `.alamazing/findings.md` and is asserted with `pytest.approx`, never equality — item 2
- [ ] T044 Confirm every emitted finding carries file, row identifiers and values, and validates against `specs/001-divergence-engine/contracts/finding.schema.json` — item 3
- [ ] T045 [P] Run `grep -rn "anthropic\|openai\|groq" pipeline/` and confirm no output — item 4, Principle V
- [ ] T046 Confirm any event cited by a finding resolves to a row in `event_log.csv` — item 5. This spec cites no events; confirm the `events` array is empty rather than populated with anything unsourced
- [ ] T047 [P] Run `grep -rni "recommend" pipeline/` and confirm no output — item 6, Principle IX
- [ ] T048 Confirm loose name matches and parse failures are recorded in `unsure_about` rather than omitted — item 7, Principle X
- [ ] T049 [P] Run `grep -rn "CL-00\|SYN-\|2026-0\|BRENT" pipeline/` and confirm no output; also grep for the threshold and any theme name literal — item 9, Principle XI
- [ ] T050 Confirm two consecutive runs produce identical findings including order — Principle VII, SC-009
- [ ] T051 Commit with the spec number in the message: `git commit -m "spec 001: look-through concentration"` — item 8

---

## Dependencies

```
Phase 0  T001 … T007   BLOCKING — every figure reproduced first
  └─> Phase 1  T008 … T012   design artifacts
        └─> Phase 2  T013 … T018   mandate.py (shared with spec 003)
              ├─> US1  T019 … T026   parse, match, theme, 42.134%
              │     ├─> US2  T027 … T030   compliance_clean
              │     ├─> US3  T031 … T035   duplicate underlying
              │     └─> US4  T036 … T038   trajectory
              │           └─> US5  T039 … T041   second client
              └─> Phase 8  T042 … T051   Definition of Done
```

US2, US3 and US4 all depend on US1 and on nothing else, so they are
independent of each other. US5 depends only on US1 too — it is the same
detector against a different client — but is placed last because it is the
cheapest and the most cuttable.

**US1 is the only story that cannot be cut.** The cut order names the third
client, CL-0014, at 16:30, which is US5.

---

## Parallel execution

Within Phase 2, the two test assertions are independent:

```
T017  band comparison classifies three cases
T018  missing band is not a breach
```

Within US1, T025 and T026 test different behaviours of the same module and
are separate functions in one file. Across stories, US2 / US3 / US4 touch
different parts of `detect` and could be built in any order once US1 is
green — on a solo build that means "any order", not "simultaneously".

Phase 8's greps — T045, T047, T049 — run together.

---

## Article VIII budget — this spec's contribution

| Layer | Count | Where |
|---|---|---|
| Unit | **5** | T017, T018 (mandate), T025, T026 (parse, totals), T030 (earned flag) |
| Integration | **5** | T024, T029, T035, T038, T040 |
| E2E | 0 | Spec 006 |

Running project total after this spec: **16 unit, 6 integration** against
Article VIII's ~14 / ~4 shape. The integration count runs over because
this spec alone carries three of the six *required* assertions
(`test_lookthrough_cl0019`, `test_lookthrough_cl0014`, and
`test_mandate_cl0019_clean` in the form of `test_compliance_clean_cl0019`).
Those are non-negotiable by name, so the overage is the constitution's own
requirement rather than test theatre.

**Every integration assertion cites a recorded figure.** T024, T038 cite
findings.md § 1; T040 cites § 3; T029 cites § 1's band table. An assertion
with no recorded derivation does not count toward this article.

**Tolerance, never equality.** T024 `abs=0.001`; T038 and T040 `abs=0.01`,
matching the tolerances block 3 states.

---

## Implementation strategy

**MVP is Phase 2 + US1 + US2.** The 42.134% figure next to
`compliance_clean = True` is the entire pitch. US3 makes it explicable,
US4 makes it a story, US5 makes it general — all three are additive.

**Nothing here is on the cut list except US5.** The constitution names
spec 001 and the mandate panel in "never cut", and the cut order releases
CL-0014 at 16:30.

**Overrun rule** (Principle II): at 75 minutes, close with a recorded
assumption rather than extending. If Phase 0 reveals that a figure does not
reproduce, that *is* the recorded assumption — report it and proceed with
what the data supports.
