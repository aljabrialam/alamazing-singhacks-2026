# Tasks: Explanation, Collateral, Tax and Life Events (spec 008)

**Prerequisites**: [spec.md](./spec.md), [plan.md](./plan.md), [research.md](./research.md) · specs 000–007 shipped, `g3` tagged

**Time box**: 90 min hard · **Post-G3 extension inside the feature freeze**

**This spec is allowed to ship partially.** The brief: *"two or three done
well beats all of them done thinly."* The queue below stops wherever the
clock stops, and whatever is unbuilt is labelled roadmap in the README —
not left half-written in the build.

---

## Phase 0 — Schema

- [ ] T001 Extend the Finding `kind` enum in `specs/001-divergence-engine/contracts/finding.schema.json` to admit `D7`, `D9` and `D10`, documenting each. **D8 is deliberately not a new kind** — it extends the existing D4 finding, because a client has one funding problem, not a liquidity finding and a separate collateral finding

## Phase 1 — D8 collateral trajectory  ·  20 min  ·  SHIP FIRST

- [ ] T002 Read the facility's history at every snapshot in `pipeline/divergence/d4_runway.py` — loan-to-value, drawn, collateral value, headroom (FR-001)
- [ ] T003 State the direction and magnitude of the loan-to-value change across the window (FR-002)
- [ ] T004 Identify an increase in the drawn balance as a **decision**, citing the transaction where one exists (FR-003)
- [ ] T005 Attribute a rise on an unchanged drawn balance to falling collateral value (FR-004)
- [ ] T006 Name the concentration finding as the cause where one exists for the same client, rather than restating it (FR-005)
- [ ] T007 [P] **Unit** — assert the trajectory omits a snapshot the facility does not carry rather than interpolating
- [ ] T008 **Integration** — assert CL-0014's five loan-to-value readings `53.93 / 53.53 / 65.62 / 67.96 / 69.41` each ±0.01, headroom falling 44,420,170 → 25,565,930, and the March draw identified as a decision (SC-001, SC-002, SC-003)
- [ ] T009 Surface the trajectory in the web layer beside the existing facility copy
- [ ] T010 **CHECKPOINT** — suite green, `findings.json` rebuilt, commit. Stop here if the clock has gone

## Phase 2 — D7 explanation  ·  30 min

- [ ] T011 Create `pipeline/divergence/d7_explain.py` reusing `diff()` and `attribution()` from spec 000 unchanged
- [ ] T012 Classify each position into **held throughout / acquired / disposed** using the flow transaction types spec 003 named — no new literals (FR-006, FR-010)
- [ ] T013 Separate the portfolio's total change into **flows and market movement**, and never report it as a single figure (FR-008)
- [ ] T014 Mark an acquired position's value change as **not performance**, citing the acquiring transaction (FR-007)
- [ ] T015 Name causes from `event_log.csv` by date and description only, via `events_touching` (FR-009)
- [ ] T016 Omit a position with no flow and no price change rather than reporting zero
- [ ] T017 [P] **Unit** — assert an acquired position is never counted as performance
- [ ] T018 **Integration** — assert the hero client's window separates ≈ USD 3.84m paid in from ≈ USD 2.18m market movement, and that the FCN's +4,156,210 sits in the acquired bucket (SC-004, SC-005)
- [ ] T019 Surface the three buckets in the web layer
- [ ] T020 **CHECKPOINT** — suite green, rebuild, commit. Stop here if the clock has gone

## Phase 3 — D9 tax, domicile-aware  ·  25 min

- [ ] T021 Create `pipeline/divergence/d9_tax.py` aggregating unrealised gains and losses across **all** a client's portfolios (FR-011)
- [ ] T022 Define the domicile table as a small explicit mapping of the domiciles present in the data, with `None` meaning **no rule recorded** (FR-016, plan.md)
- [ ] T023 Name both domicile and residence where they differ, and identify the domicile as governing (FR-012)
- [ ] T024 Where the domicile does not levy capital gains, report that harvesting losses is **of little value to this client** — and do not suggest harvesting (FR-013). **This is the detector's whole point**
- [ ] T025 Name a position with no cost basis as unquantifiable rather than excluding it or assuming it flat (FR-014)
- [ ] T026 State that meeting a dated obligation realises taxable gains, where the client holds net gains and has one (SC-007)
- [ ] T027 Propose no trade, sale or optimisation anywhere in the copy (FR-015)
- [ ] T028 [P] **Unit** — assert a domicile with no recorded rule yields a stated absence, never an inferred treatment
- [ ] T029 **Integration** — assert CL-0014's finding reports large losses *and* that harvesting is of little value at his domicile; assert CL-0003's names Germany, Singapore and the unquantifiable position (SC-006, SC-007)
- [ ] T030 Surface the tax position in the web layer
- [ ] T031 **CHECKPOINT** — suite green, rebuild, commit. Stop here if the clock has gone

## Phase 4 — D10 life events  ·  15 min

- [ ] T032 Create `pipeline/divergence/d10_lifeevents.py` comparing recorded liquidity needs and investment horizon against dated obligations (FR-017)
- [ ] T033 Cite the profile field and the source of the obligation (FR-018)
- [ ] T034 Address the **profile** rather than the portfolio, because the profile drives suitability (FR-019)
- [ ] T035 **Integration** — assert the hero client's contradiction is reported: liquidity needs recorded low against a dated obligation inside the horizon (SC-008)
- [ ] T036 **CHECKPOINT** — suite green, rebuild, commit

## Phase 5 — Definition of Done, whatever shipped

- [ ] T037 Run `pytest tests/ -v` and paste the output — item 1
- [ ] T038 Confirm every new figure matches [research.md](./research.md) with `pytest.approx` — item 2
- [ ] T039 Confirm every new finding carries file, row ids and values and validates against the schema — item 3
- [ ] T040 [P] Confirm `grep -rln anthropic pipeline/` still matches only `claims.py` and `brief.py` — item 4
- [ ] T041 Confirm every cited event resolves to a row in `event_log.csv` — item 5
- [ ] T042 [P] Run `grep -rni recommend pipeline/` and confirm no finding proposes a trade — item 6
- [ ] T043 Confirm unknowns are in `unsure_about`, including any domicile with no recorded rule — item 7
- [ ] T044 [P] Run the portability grep, including for domicile names — item 9
- [ ] T045 **Update the README**: move what shipped into the specs table and the "Directions" audit; put what did not ship in a roadmap section with the honest reason — Principle X
- [ ] T046 Commit with the spec number — item 8

---

## Dependencies

```
T001 schema  (blocks D7, D9, D10 — not D8)
  ├─> Phase 1  D8   T002 … T010   SHIP FIRST
  ├─> Phase 2  D7   T011 … T020
  ├─> Phase 3  D9   T021 … T031
  └─> Phase 4  D10  T032 … T036
        └─> Phase 5  T037 … T046
```

**The four detectors are independent of each other.** That is the point of
the ordering — any prefix of the queue is a complete, shippable state.

## Article VIII budget

| Detector | Unit | Integration |
|---|---|---|
| D8 | 1 | 1 |
| D7 | 1 | 1 |
| D9 | 1 | 1 |
| D10 | 0 | 1 |

Project total if all four ship: **38 unit, 19 integration, 2 e2e**.

## Strategy

**MVP is Phase 1.** D8 alone justifies this spec: it is twenty minutes,
it uses columns already in the file, and it turns the weakest of the three
demo clients into the one where waiting is measurably expensive.

**Stop rule.** After each checkpoint the build is green, `findings.json`
is rebuilt and everything is committed. The queue stops wherever the clock
stops. Nothing half-written enters the build — Principle XII requires a
runnable path from `data/` to a rendered brief at all times.
