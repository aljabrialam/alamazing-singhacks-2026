# Tasks: Scenario (spec 005)

**Prerequisites**: [spec.md](./spec.md), [plan.md](./plan.md), [research.md](./research.md)

**Gate**: G2 — **this spec closes it** · **Time box**: 40 min ·
**Cut status**: the scenario panel is on the demo script; not cuttable

Tests required: **3 unit + 1 integration**, the integration being
`test_scenario_cl0019`, the last of Article VIII's six named assertions.

---

## Phase 1 — Repricing

- [x] T001 Implement `detect(book, client_id, series_id, date_now, date_then)` in `pipeline/divergence/d6_scenario.py` with the series and both dates as arguments (FR-001, [research.md](./research.md) R5)
- [x] T002 Validate both dates as snapshots and make the comparison order-independent in `pipeline/divergence/d6_scenario.py`, so reversed arguments do not silently invert the answer
- [x] T003 Reprice each holding by the ratio of its `price_<date>` values, **not** its market values, in `pipeline/divergence/d6_scenario.py` (FR-002, R2)
- [x] T004 Select the affected theme from spec 001's `look_through`, so the scenario reprices the same positions the concentration finding names
- [x] T005 Itemise each position's value before, value after and impact in `pipeline/divergence/d6_scenario.py` (FR-003)
- [x] T006 Report the total in USD and as a share of the client's portfolio (FR-004)
- [x] T007 Cite the named series and its value at both dates as evidence (FR-008)
- [x] T008 [P] **Unit 1** — `tests/test_scenario.py::test_reprices_from_prices_not_market_values` asserts the ratio comes from the price columns, and that the two differ measurably on this data
- [x] T009 [P] **Unit 2** — `tests/test_scenario.py::test_dates_are_validated_and_order_independent` asserts an unknown date raises and reversed arguments give the same answer

## Phase 2 — The position with no past

- [x] T010 Proxy a holding with no earlier price from the **worst-performing basket leg the client holds**, in `pipeline/divergence/d6_scenario.py` — a worst-of note pays on its worst leg (FR-005, R2)
- [x] T011 Record the proxy and the leg it came from in `unsure_about` (FR-005, SC-003)
- [x] T012 Compute and report the impact under a basket leg the client does **not** hold where its move is larger, with the note that the strictly correct leg is a name he does not hold (FR-006, SC-004, R3)
- [x] T013 Exclude a holding **not held** at the earlier date with no basket reference, and record the exclusion — never invent a ratio (FR-007). **Amended during implementation**: the gate is holdings presence, not price presence. Every structured product is par-indexed to 100.0 at the first snapshot, so the note carries a price for a date before it existed; trusting it understated the scenario by a third
- [x] T014 [P] **Unit 3** — `tests/test_scenario.py::test_proxy_uses_the_worst_leg_held_and_reports_the_worse_one` asserts the proxy leg is the worst among those held, and that the unheld leg's larger impact is reported

## Phase 3 — Second order

- [x] T015 Detect the overlap between the client's recorded source of wealth and the scenario's theme in `pipeline/divergence/d6_scenario.py` (FR-009)
- [x] T016 Quote the note in which the client recorded that view, citing its id — the system reports his statement, it does not infer the link (FR-009, FR-010, R4)
- [x] T017 Make no second-order claim where the source of wealth does not share the theme, or where no note records it (FR-010)
- [x] T018 Write the RM-facing copy in `pipeline/divergence/d6_scenario.py` without the forbidden verb, stating the impact and proposing nothing (FR-013)

## Phase 4 — Integration and Definition of Done

- [x] T019 **Integration** — `tests/test_scenario.py::test_scenario_cl0019` asserts total impact `approx(-2.5e6, abs=0.1e6)` and `approx(-7.8, abs=0.2)` percent, with the four positions itemised at −0.43m / −0.72m / −0.54m / −0.82m each ± 0.01m. **The last of Article VIII's six named assertions** (SC-001, SC-002)
- [x] T020 Assert the finding cites BRENT_USD_BBL at 101.5 and 72.4 (SC-005)
- [x] T021 Assert the second-order effect cites `clients.csv` and note N-025 (SC-006)
- [x] T022 Assert a different series and dates produce a different, non-erroring result — the portability demonstration (SC-007)
- [x] T023 Run `pytest tests/ -v` and paste the output — item 1
- [x] T024 Confirm findings validate against the Finding schema with `kind` D6 — item 3
- [x] T025 [P] Confirm `grep -rln anthropic pipeline/` matches only `claims.py` — item 4
- [x] T026 Confirm every cited note id resolves to a row in `rm_notes.json` — item 5
- [x] T027 [P] Run `grep -rni recommend pipeline/` — item 6
- [x] T028 Confirm the proxy and the worst-of alternative are recorded in `unsure_about` — item 7
- [x] T029 [P] Run the portability grep over `pipeline/` — item 9
- [x] T030 Commit with the spec number — item 8
- [x] T031 Confirm all six of Article VIII's named assertions are green, then tag `g2` and record it in `docs/gates.md` — Principle XV

---

## Dependencies

```
Phase 1  T001 … T009   repricing
  └─> Phase 2  T010 … T014   the proxy
        └─> Phase 3  T015 … T018   second order
              └─> Phase 4  T019 … T031   integration, DoD, G2
```

## Article VIII budget

| Layer | Count | Where |
|---|---|---|
| Unit | 3 | T008, T009, T014 |
| Integration | 1 | T019 |

Project total after this spec: **32 unit, 15 integration**. Against
Article VIII's ~14 / ~4 shape — the overage is driven by the six named
assertions plus the per-client sweeps, each of which guards a
silent-wrong-number path rather than a crash.

**This spec closes G2.** All six named assertions green:
`test_lookthrough_cl0019`, `test_lookthrough_cl0014`,
`test_mandate_cl0003_inherited`, `test_mandate_cl0019_clean`,
`test_scenario_cl0019`, and `test_findings_are_deterministic` (per
detector; the end-to-end build variant arrives with spec 006).

## Strategy

**MVP is Phase 1 + T010 + T019.** The number is the answer to his
question. The second-order effect is what makes it matter, and it is ten
minutes.
