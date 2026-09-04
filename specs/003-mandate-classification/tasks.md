# Tasks: Mandate Classification (spec 003)

**Prerequisites**: [spec.md](./spec.md), [plan.md](./plan.md), [research.md](./research.md) · specs 000–002 verified

**Gate**: G2 · **Time box**: 45 min · **Cut status**: the mandate panel is
named in "never cut"

Phase 0 complete — **six** questions resolved, two reference-document
errors and **two** live defects in spec 001 found. R6 was discovered only
because R4's prediction turned out wrong; both are recorded in
[research.md](./research.md). Tests required: **4 unit + 3 integration**,
including `test_mandate_cl0003_inherited`, named in Article VIII.

---

## Phase 1 — Fix `mandate.py` (regression, do first)

Spec 001 shipped a `compliance_clean` that reads three custody-account
false breaches as real. Fix before building on top of it.

- [x] T001 Add the service-model constants to `pipeline/mandate.py` — advisory, discretionary and custody — as named values rather than literals at the point of use
- [x] T002 Exclude custody portfolios from band comparison in `pipeline/mandate.py`, joining `service_model` from `portfolios.csv`
- [x] T003 Exclude custody portfolios from the single-position limit check in `pipeline/mandate.py`
- [x] T004 Report custody portfolios separately from `compliance_verdict` in `pipeline/mandate.py`, with portfolio id, name, value and held-not-managed status — excluded from measurement, never removed from view (FR-002)
- [x] T005 **Unit 1** — `tests/test_mandate.py::test_custody_is_not_measured_against_a_band` asserts the three custody portfolios yield no breach, that they are still reported, and that a 100% single-asset custody holding is not a violation
- [x] T005a **Unit 1b** — `tests/test_mandate.py::test_diversified_funds_are_exempt_from_the_position_limit` gates the single-position check on `concentration_limit_applies`. **Added after Phase 0's R6** — spec 001 applied the limit to diversified funds, producing false breaches that buried a real single-stock one
- [x] T006 Re-run the whole suite and confirm spec 001 is still green, and that CL-0019, CL-0003 and CL-0014 figures are unchanged (SC-005)
- [x] T007 Confirm CL-0001 and CL-0002 flip to compliance-clean and CL-0017 stays breached for one real reason rather than two (SC-004, [research.md](./research.md) R4)

---

## Phase 2 — Classification

- [x] T008 Define acquisition and disposal transaction types in `pipeline/divergence/d2_mandate.py` as named constants with the values actually present in the data — `Buy`, `Structured Product Subscription`, `Redemption Request`, `Withdrawal` (FR-008, [research.md](./research.md) R1)
- [x] T009 **Unit 2** — `tests/test_classification.py::test_transaction_types_exist_in_the_data` asserts every named constant matches at least one row, so the silent-match-nothing bug cannot recur
- [x] T010 Derive the reporting year from the latest snapshot in `pipeline/divergence/d2_mandate.py`, never as a literal (FR-011)
- [x] T011 Implement the `inherited` test in `pipeline/divergence/d2_mandate.py`: inception in the reporting year **and** no client-initiated acquisition into the breached class (FR-004)
- [x] T012 Implement the `client_directed` test in `pipeline/divergence/d2_mandate.py` with **breach direction selecting evidence direction** — acquisitions into the class for `above_max`, disposals out of it for `below_min` (FR-005, [research.md](./research.md) R3)
- [x] T013 Make `client_directed` take precedence over `inherited` in `pipeline/divergence/d2_mandate.py` (FR-007)
- [x] T014 Default to `drift` in `pipeline/divergence/d2_mandate.py`, with copy saying the weights moved through market action rather than through a decision (FR-006)
- [x] T015 **Unit 3** — `tests/test_classification.py::test_direction_selects_evidence_direction` asserts an acquisition into a class does **not** make a below-minimum breach client-directed
- [x] T016 **Unit 4** — `tests/test_classification.py::test_every_classification_is_permitted` asserts all classifications across the book are one of the three values (SC-007)

---

## Phase 3 — Findings

- [x] T017 Emit one finding per breach in `pipeline/divergence/d2_mandate.py`, carrying the classification, the band, the actual value and the direction
- [x] T018 Attach evidence in `pipeline/divergence/d2_mandate.py`: the mandate rows, the portfolio inception date, and the transaction rows examined (FR-010)
- [x] T019 Emit the positive checked-and-clear result for a client with no breach in `pipeline/divergence/d2_mandate.py`, naming every band checked and its actual value — block 5: this is not a null (FR-009)
- [x] T020 Write classification-specific RM-facing copy in `pipeline/divergence/d2_mandate.py` — three classifications describe three different conversations — without the forbidden verb (FR-013)
- [x] T021 Record in `unsure_about` anything the classification could not determine, including the missing cost basis spec 000 recorded for the inherited holding (FR-015)

---

## Phase 4 — Integration assertions

- [x] T022 **Integration 1** — `tests/test_classification.py::test_mandate_cl0003_inherited` asserts Equity `approx(71.46, abs=0.01)` vs 10–30, Fixed Income `approx(9.15, abs=0.01)` vs 45–75, largest position `approx(26.06, abs=0.01)`, classification `inherited`. **Named in Article VIII** (SC-001)
- [x] T023 **Integration 2** — `tests/test_classification.py::test_mandate_cl0014_drift` asserts Equity `approx(23.39, abs=0.01)` vs 30–55, breached low, classification `drift` (SC-002)
- [x] T024 **Integration 3** — `tests/test_classification.py::test_mandate_cl0019_clean` asserts no breach, all five bands within range, largest position 13.30 vs 15, and that the result is a positive statement naming every band. **Named in Article VIII** (SC-003)

---

## Phase 5 — Definition of Done

- [x] T025 Run `pytest tests/ -v` and paste the output — item 1
- [x] T026 Confirm every figure matches `.alamazing/findings.md` with `pytest.approx` — item 2
- [x] T027 Confirm every finding carries file, row ids and values and validates against `finding.schema.json` — item 3
- [x] T028 [P] Confirm `grep -rln anthropic pipeline/` still matches only `claims.py` — item 4
- [x] T029 Confirm this spec cites no events and leaves `events` empty rather than unsourced — item 5
- [x] T030 [P] Run `grep -rni recommend pipeline/` — item 6
- [x] T031 Confirm unknowns are in `unsure_about` — item 7
- [x] T032 [P] Run the portability grep over `pipeline/` — item 9
- [x] T033 Commit with the spec number, noting the `mandate.py` regression fix in the message — item 8

---

## Dependencies

```
Phase 1  T001 … T007   mandate.py regression fix  (BLOCKING)
  └─> Phase 2  T008 … T016   classification
        └─> Phase 3  T017 … T021   findings
              └─> Phase 4  T022 … T024   integration
                    └─> Phase 5  T025 … T033   Definition of Done
```

**Phase 1 must come first.** Building classification on top of a
comparison that reports false breaches would mean classifying breaches
that do not exist — and one of them would be a founder's own company.

## Article VIII budget

| Layer | Count | Where |
|---|---|---|
| Unit | 4 | T005, T009, T015, T016 |
| Integration | 3 | T022, T023, T024 |

Project total after this spec: **24 unit, 11 integration**. This spec
closes the last two named assertions in Article VIII's table apart from
the scenario (spec 005) and the end-to-end determinism test (spec 006).

## Strategy

**MVP is Phase 1 + T011 + T022.** The `inherited` classification on
CL-0003 is the third demo finding; the custody fix is a correctness
prerequisite.

Nothing here is cuttable — the mandate panel is named in "never cut", and
Phase 1 fixes shipped code.
