# Tasks: Liquidity Runway and the Unanswered Question (spec 004)

**Prerequisites**: [spec.md](./spec.md), [plan.md](./plan.md), [research.md](./research.md)

**Gate**: G2 · **Time box**: 65 min · **Cut status**: D4 cuttable, **D5 is
not** (block 6)

Tests required: **5 unit + 3 integration**.

---

## Phase 0 — Unblock the schema

- [x] T001 Extend the `kind` enum in `specs/001-divergence-engine/contracts/finding.schema.json` to `D1..D6` and document each detector, resolving the blocker flagged in spec 001 ([research.md](./research.md) R6)

## Phase 1 — FX

- [x] T002 Implement `to_usd(book, amount, currency, date)` in `pipeline/fx.py`, selecting multiplication or division from the rate's **stated unit** rather than the series identifier (FR-001, [research.md](./research.md) R1)
- [x] T003 Return no figure and record the reason when no rate exists for a currency, in `pipeline/fx.py` — never invent a rate (FR-002)
- [x] T004 [P] **Unit 1** — `tests/test_fx.py::test_conventions_are_read_not_guessed` asserts the EUR rate multiplies and the HKD rate divides, and that swapping them would be a 61× error
- [x] T005 [P] **Unit 2** — `tests/test_fx.py::test_unknown_currency_invents_nothing` asserts an unknown currency yields no figure and records why

## Phase 2 — D4 runway

- [x] T006 Implement available funds in `pipeline/divergence/d4_runway.py`, counting only Daily and Weekly liquidity tiers (FR-003)
- [x] T007 Report the cash-plus-fixed-income figure alongside the tier figure in `pipeline/divergence/d4_runway.py`, because they answer different questions (FR-006, R2)
- [x] T008 Net off pledged collateral and report facility loan-to-value against the margin-call threshold in `pipeline/divergence/d4_runway.py` (FR-004)
- [x] T009 Compute the post-sale loan-to-value where funding the need requires selling pledged collateral, in `pipeline/divergence/d4_runway.py` (FR-005, R3)
- [x] T010 Include uncalled commitments alongside planned needs in `pipeline/divergence/d4_runway.py`, carrying the call window as recorded
- [x] T011 Note the private-market valuation lag in `unsure_about` where it affects a conclusion, and never flag it as an error (FR-007)
- [x] T012 Attach evidence in `pipeline/divergence/d4_runway.py`: the need row, the holdings rows counted, and the facility row (FR-012)
- [x] T013 [P] **Unit 3** — `tests/test_runway.py::test_only_daily_and_weekly_count` asserts Monthly and Illiquid are excluded
- [x] T014 [P] **Unit 4** — `tests/test_runway.py::test_pledged_collateral_is_reported` asserts a pledged portfolio reports headroom and post-sale loan-to-value, **and that a facility only blocks funding when no unpledged liquidity covers the need**. The first implementation reported three clients as blocked; one of them has an unpledged discretionary portfolio and simply pays from it
- [x] T015 **Integration 1** — `tests/test_runway.py::test_runway_cl0003` asserts the need converts to USD 3,712,800, tier funds 88.29%, cash+FI 16.83%, need 16.74% of portfolio (SC-001, SC-002)
- [x] T016 **Integration 2** — `tests/test_runway.py::test_runway_cl0014` asserts USD 7,682,458, illiquid 26.62%, facility LTV 69.41% vs 70%, and post-sale LTV above the threshold (SC-003, SC-004, SC-005)

## Phase 3 — D5 unanswered

- [x] T017 Implement question and admission markers in `pipeline/divergence/d5_unanswered.py` as named constants
- [x] T018 Implement the answered guard in `pipeline/divergence/d5_unanswered.py` — same note or a later note (FR-009, R5)
- [x] T019 Restrict admissions to first-person statements about the bank's own action, or a standalone "Unresolved." sentence, so market commentary is not matched (R5)
- [x] T020 Make an admission override the answer guard in `pipeline/divergence/d5_unanswered.py` (FR-010)
- [x] T021 Cite the note id, the date and the quote in every open question (FR-011)
- [x] T022 **Unit 5** — `tests/test_unanswered.py::test_answered_and_commentary_are_excluded` asserts N-002, N-006 and N-025 are not surfaced
- [x] T023 **Integration 3** — `tests/test_unanswered.py::test_unanswered_n026_and_n028` asserts both required notes are surfaced with their quotes (SC-006)

## Phase 4 — Definition of Done

- [x] T024 Run `pytest tests/ -v` and paste the output — item 1
- [x] T025 Confirm every figure matches `.alamazing/findings.md` or [research.md](./research.md) with `pytest.approx` — item 2
- [x] T026 Confirm findings validate against the extended Finding schema — item 3
- [x] T027 [P] Confirm `grep -rln anthropic pipeline/` matches only `claims.py` — item 4
- [x] T028 Confirm every cited note id resolves to a row in `rm_notes.json` — item 5
- [x] T029 [P] Run `grep -rni recommend pipeline/` — item 6
- [x] T030 Confirm the private-market lag and the R5 false negative are recorded — item 7
- [x] T031 [P] Run the portability grep over `pipeline/` — item 9
- [x] T032 Commit with the spec number — item 8

---

## Dependencies

```
T001 schema            (BLOCKING — no schema-valid D5 finding without it)
  └─> Phase 1  T002 … T005   fx.py
        ├─> Phase 2  T006 … T016   D4
        └─> Phase 3  T017 … T023   D5   (independent of D4)
              └─> Phase 4  T024 … T032
```

D5 does not depend on D4. If D4 is cut, D5 still ships.

## Article VIII budget

| Layer | Count | Where |
|---|---|---|
| Unit | 5 | T004, T005, T013, T014, T022 |
| Integration | 3 | T015, T016, T023 |

Project total after this spec: **29 unit, 14 integration**.

## Strategy

**MVP is T001 + Phase 3.** D5 is twenty lines and is what block 6 refuses
to let go. D4's value is real but it is the cuttable half.
