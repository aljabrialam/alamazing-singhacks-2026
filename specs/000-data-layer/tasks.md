# Tasks: Data Layer (spec 000)

**Input**: Design documents from `/specs/000-data-layer/`
**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/data-layer.md](./contracts/data-layer.md), [quickstart.md](./quickstart.md)

**Gate**: G1 · **Time box**: 115 minutes · **Cut status**: never cut
(constitution, Kill switch)

**Tests are required**, not optional. Article VIII of the constitution
mandates them in absolute counts, and the Definition of Done fails without
them. This spec's budget: **6 unit assertions + 1 integration assertion**,
counted toward the project total of ~14 unit / ~4 integration / 2 e2e.

---

## Phase 1 — Setup

- [ ] T001 Verify the spine from raw files before writing any module, per quickstart.md block 0, and stop the spec if it does not print 42.1343 ± 0.0001
- [ ] T002 [P] Create `tests/conftest.py` with one session-scoped `book` fixture calling `load_all("data/")`, so the twelve files are read once per test run rather than once per test

---

## Phase 2 — Foundational (blocking)

**Blocks every user story.** `Book` is the first argument of every function
in the pipeline, so its shape is settled before anything reads it.

- [ ] T003 Define the `Book` dataclass in `pipeline/load.py` with the thirteen fields listed in data-model.md, `imperfections` defaulting to an empty list via `field(default_factory=list)`
- [ ] T004 Add the three accessors `client(client_id)`, `notes_for(client_id)` and `holdings_at(client_id, date)` to `Book` in `pipeline/load.py`, ordering `notes_for` by `note_date` so it is deterministic
- [ ] T005 Add `snapshots(book)` and `latest(book)` to `pipeline/load.py`, deriving dates from `holdings.snapshot_date` and returning them ascending — no date literal anywhere (Principle XI, FR-005)

---

## Phase 3 — User Story 1: Load the book once, correctly (P1)

**Goal**: One folder in, one queryable `Book` out, with both joins applied,
every row retained, and every defect recorded rather than repaired.

**Independent test**: `pytest tests/test_load.py -v` passes and
quickstart.md blocks 1, 2, 7 and 8 print their expected output. The book is
queryable in a REPL — this story delivers value alone.

**Budget**: 25 of load.py's 40 minutes.

- [ ] T006 [US1] Implement `load_all(path="data/")` in `pipeline/load.py` reading the twelve sources — eleven CSVs with `pd.read_csv` and `rm_notes.json` with `json.load` — with `path` as an argument and no `parse_dates`, keeping all dates as ISO strings per research.md R6
- [ ] T007 [US1] Raise `FileNotFoundError` naming the missing file when any of the twelve is absent, in `pipeline/load.py` — a partially loaded book is worse than no book
- [ ] T008 [US1] Merge `instruments` onto `holdings` on `instrument_id` with `how="left"` and `suffixes=("", "_inst")` in `pipeline/load.py`, keeping both `asset_class` and `asset_class_inst`, per research.md R2
- [ ] T009 [US1] Merge `portfolios[["portfolio_id", "mandate_code"]]` onto `holdings` on `portfolio_id` in `pipeline/load.py`
- [ ] T010 [US1] Assert internally that the holdings row count is unchanged by both merges in `pipeline/load.py`, raising if a merge duplicated rows — a duplicating merge inflates every weight in the book, plausibly
- [ ] T011 [P] [US1] Record `missing_cost_basis` imperfections in `pipeline/load.py`, one entry per holdings row where `unrealised_pnl_pct` is null, each naming file, client, portfolio, instrument, snapshot date, field and a one-sentence `detail` (FR-012)
- [ ] T012 [P] [US1] Record `stale_valuation` imperfections in `pipeline/load.py`, one entry per row where `valuation_date != snapshot_date`, carrying both dates and describing it as a lag rather than an error — private-market marks lag a quarter by design (`.alamazing/findings.md`)
- [ ] T013 [P] [US1] Record `orphan_instrument` imperfections in `pipeline/load.py` for any `instrument_id` in holdings but absent from instruments; the check returns nothing against this data and is implemented anyway
- [ ] T014 [US1] Sort `book.imperfections` by `kind`, `client_id`, `instrument_id`, `snapshot_date` in `pipeline/load.py` so the list is byte-identical between runs (Principle VII)
- [ ] T015 [US1] **Unit assertion 1** — `tests/test_load.py::test_book_row_counts` asserts 1015 holdings, 20 clients, 24 portfolios, 28 notes
- [ ] T016 [P] [US1] **Unit assertion 2** — `tests/test_load.py::test_joins_present_and_no_row_inflation` asserts the six joined columns exist and the holdings row count is still 1015
- [ ] T017 [P] [US1] **Unit assertion 3** — `tests/test_load.py::test_imperfections_recorded` asserts the list is non-empty, that the missing cost basis on CL-0003 / SYN-ST-0107 appears once per snapshot, and that no row was dropped

---

## Phase 4 — User Story 2: Client-level exposure, not portfolio-level (P1)

**Goal**: One denominator per client per date. The recorded trap, closed
once, in the only place client exposure is computed.

**Independent test**: `pytest tests/test_load.py -k weights -v` and
`tests/test_spine.py` pass; quickstart.md blocks 3 and 4 print their
expected output, including CL-0017's raw 299.9999 against a recomputed 100.

**Budget**: remaining 15 of load.py's 40 minutes.

**This is the highest-risk task in the spec.** Six of six downstream specs
consume it directly or transitively (contracts/data-layer.md, Downstream
consumers).

- [ ] T018 [US2] Implement `client_weights(book, client_id, date)` in `pipeline/load.py`, computing `w` as `market_value_usd / total * 100` with a single total per client per date across all their portfolios, and never summing `weight_pct` (FR-006, research.md R1)
- [ ] T019 [US2] Raise `ValueError` naming the available snapshots when `date` is not present in the data, in `pipeline/load.py` — an empty frame for a typo'd date is how a zero exposure gets quoted as a fact (FR-018)
- [ ] T020 [US2] Return an empty frame with the expected columns, with no division by zero, when the client holds nothing at that date, in `pipeline/load.py`
- [ ] T021 [US2] Sort the returned frame by `w` descending then `instrument_id` ascending in `pipeline/load.py` (Principle VII)
- [ ] T022 [US2] **Unit assertion 4** — `tests/test_load.py::test_client_weights_sum_to_100` asserts `w.sum() == pytest.approx(100, abs=1e-3)` for all 20 clients at every snapshot date, not a sample (SC-003)
- [ ] T023 [US2] **Unit assertion 5** — `tests/test_load.py::test_weight_pct_trap_is_real` asserts that for the three-portfolio client the raw `weight_pct` sum is approximately 300 while the recomputed weights sum to 100, demonstrating the trap rather than describing it (SC-004)
- [ ] T024 [US2] **Integration assertion** — `tests/test_spine.py::test_spine_cl0019_from_pipeline` asserts the four exposure instruments sum to `pytest.approx(42.134, abs=0.001)` through `client_weights`, citing `.alamazing/findings.md` § Abdullah Al-Mansoori in a comment. Tolerance, never equality (SC-002)

---

## Phase 5 — User Story 3: What changed between two dates (P2)

**Goal**: Every instrument held at either date, exactly once, zero-filled
where absent. The structured note that settled in June must appear.

**Independent test**: `pytest tests/test_diff.py -v` passes and
quickstart.md block 5 shows `value_a=0.0` for the note.

**Budget**: 30 minutes.

- [ ] T025 [US3] Implement `diff(book, client_id, date_a, date_b)` in `pipeline/diff.py` as an **outer** join of `client_weights` at both dates on `instrument_id`, filling missing values with `0.0`, returning `value_a`, `value_b`, `weight_a`, `weight_b`, `d_value`, `d_weight`, sorted by `instrument_id`
- [ ] T026 [US3] Coalesce `instrument_name` and `asset_class` from whichever date carries them in `pipeline/diff.py`, so a position present at only one date still has a readable name in an evidence panel
- [ ] T027 [US3] Validate both dates against the snapshots in `pipeline/diff.py`, raising `ValueError` as `client_weights` does
- [ ] T028 [US3] Implement `attribution(book, client_id, date_a, date_b)` in `pipeline/diff.py` returning the same frame ordered by `abs(d_value)` descending then `instrument_id` ascending as a deterministic tiebreak
- [ ] T029 [US3] **Unit assertion 6** — `tests/test_diff.py::test_appearing_and_disappearing_positions` asserts a position absent at the earlier date has `value_a == 0.0` rather than `NaN` or a missing row, that the row count equals the union of instruments at the two dates, and that `attribution` returns the same rows in descending order of absolute value change

---

## Phase 6 — User Story 4: Which events touched this client (P2)

**Goal**: The event log, carried through unmodified, filtered by a keyword
match that is reproducible and never delegated to a model.

**Independent test**: `pytest tests/test_events.py -v` passes and
quickstart.md block 6 returns both 2026-03-04 and 2026-08-05.

**Budget**: 45 minutes.

- [ ] T030 [US4] Implement `events_between(book, date_a, date_b)` in `pipeline/events.py` filtering `event_date` on an **inclusive** ISO string range, sorted by `event_date` then `description`, carrying every field through unmodified (FR-010, Principle IV)
- [ ] T031 [US4] Implement the term-set builder in `pipeline/events.py`: the client's distinct `sector` and `sub_asset_class` values, lowercased, stripped and **sorted** so the result does not depend on frame order
- [ ] T032 [US4] Implement the match predicate in `pipeline/events.py`: split `primary_transmission` on commas, lowercase and strip, then match a pair when either contains the other provided both are at least four characters, requiring exact equality below that length (research.md R5)
- [ ] T033 [US4] Implement `events_touching(book, client_id, date_a, date_b)` in `pipeline/events.py`, adding a `matched_on` column of the sorted matching terms comma-joined, excluding events that match nothing
- [ ] T034 [US4] **Unit assertion 7** — `tests/test_events.py::test_events_between_inclusive_and_ordered` asserts the range is inclusive at both ends and the result is date-ordered
- [ ] T035 [US4] **Unit assertion 8** — `tests/test_events.py::test_events_touching_hero_client` asserts both 2026-03-04 and 2026-08-05 are returned for the hero client between the pre-conflict and latest snapshots, that every returned event resolves to a row of `event_log.csv`, and that `matched_on` is populated on every row (SC-005)

---

## Phase 7 — Polish & Definition of Done

**No refactoring.** These are verification tasks, not improvement tasks.

- [ ] T036 Run `pytest tests/ -v` and paste the output into the completion report — Definition of Done item 1
- [ ] T037 Run every block of [quickstart.md](./quickstart.md) in order and confirm each prints its recorded expected output — Definition of Done item 2
- [ ] T038 Run `grep -rn "CL-00\|SYN-\|2026-0\|BRENT" pipeline/` and confirm no output; the four exposure instrument ids live in `tests/`, which the Definition of Done explicitly permits — item 9, Principle XI
- [ ] T039 [P] Run `grep -rn "anthropic\|openai\|recommend" pipeline/` and confirm no output — Definition of Done items 4 and 6, Principles V and IX
- [ ] T040 [P] Confirm two consecutive loads produce identical frames including row order, per quickstart.md block 7 — Principle VII
- [ ] T041 Confirm every recorded imperfection names its file, row identifiers and field, and that `unsure_about`-class unknowns are recorded rather than guessed — Definition of Done items 3 and 7, Principle X
- [ ] T042 Commit with the spec number in the message: `git commit -m "spec 000: data layer"` — Definition of Done item 8
- [ ] T043 Tag `g1`, append `| G1 — Data | HH:MM | g1 |` to `docs/gates.md`, commit that line, and push tags — Principle XV; a gate claimed but not tagged did not pass

---

## Dependencies

```
T001 spine (blocking — stop the spec if it fails)
  └─> T002 conftest
        └─> T003, T004, T005  Book + helpers  (Phase 2, blocking)
              ├─> US1  T006 … T017   load, joins, imperfections
              │     └─> US2  T018 … T024   client_weights + spine assertion
              │           ├─> US3  T025 … T029   diff, attribution
              │           └─> US4  T030 … T035   events
              └─> Phase 7  T036 … T043   verification, commit, tag
```

**Story order is not arbitrary.** US2 depends on US1 (weights need a loaded
book). US3 depends on US2 (`diff` is built from `client_weights` at two
dates). US4 depends only on US1 — it needs holdings for the term set, not
weights — so US3 and US4 are independent of each other and could be built
in either order. US4 is placed second because its 45 minutes is the largest
single block and the run sheet's checkpoint is the event assertion.

---

## Parallel execution

Within US1, the three imperfection recorders touch different rows of the
same function and are logically independent:

```
T011  missing_cost_basis
T012  stale_valuation      } same file, independent logic
T013  orphan_instrument
```

Within Phase 7, T039 and T040 are independent greps and can run together
with T038.

Across stories, US3 (`diff.py`) and US4 (`events.py`) are different files
with no shared code and can be built in parallel once US2 is green. On a
solo build that means "either order", not "simultaneously".

The test assertions T015/T016/T017 are marked `[P]` where they touch
different behaviours of the same module; they are separate test functions in
one file.

---

## Article VIII budget — this spec's contribution

| Layer | Count | Where |
|---|---|---|
| Unit | **8** | T015, T016, T017 (load), T022, T023 (weights), T029 (diff), T034, T035 (events) |
| Integration | **1** | T024 — the spine, 42.134 ± 0.001, against a figure recorded in `.alamazing/findings.md` |
| E2E | 0 | Deferred to spec 006, where `build.py` exists to run end to end |

Eight unit assertions against a plan estimate of six. The two extra are
T023 (the `weight_pct` trap) and T034 (inclusive event range) — both cheap,
both guarding a silent-wrong-number path rather than a crash, which is the
test Article VIII says is worth writing. The project total remains within
the ~14 unit / ~4 integration shape.

**Every integration assertion cites a recorded figure.** T024 cites
`.alamazing/findings.md` § Abdullah Al-Mansoori. An assertion with no
recorded derivation would not count toward this article.

**Tolerance, never equality.** T022, T023 and T024 all use
`pytest.approx`. 42.1343 and 42.1344 are both correct; an equality assert
on a float sum fails for a reason that has nothing to do with the code.

---

## Implementation strategy

**MVP is US1 + US2.** A loaded book and a correct client-level weight is
the whole of the Spine Rule and everything spec 001 needs. If the clock
ran out after T024, spec 001 could still be built.

US3 and US4 are P2 and additive: the trajectory table and the causal chain
in the brief need them, the hero concentration figure does not.

**Nothing here is on the cut list.** Spec 000 is named in the
constitution's "never cut". If this spec overruns, the response is to cut
something later — not to cut a task from this file.

**Overrun rule** (Principle II): at 115 minutes, close the remaining work
with a recorded assumption rather than extending. In practice the only
credibly cuttable task is T028 `attribution`, which is a re-sort of `diff`
and could be done by the caller.
