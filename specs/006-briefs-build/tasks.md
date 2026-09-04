# Tasks: Briefs and Build (spec 006)

**Prerequisites**: [spec.md](./spec.md), [plan.md](./plan.md), [research.md](./research.md) · specs 000–005 verified, `g2` tagged

**Gate**: G3 · **Time box**: 80 min

Tests required: **3 unit + 2 end-to-end**. This spec supplies the e2e
layer Article VIII budgets at 2.

---

## Phase 1 — Briefs

- [x] T001 Write the brief prompt in `pipeline/brief.py` as a module constant, carrying block 8's seven load-bearing rules verbatim
- [x] T002 Assemble the brief input in `pipeline/brief.py` from the person, their objectives, their notes and the **already-computed findings** — never a raw holdings row or client record (FR-001, Principle V)
- [x] T003 Implement the model call in `pipeline/brief.py` against `claude-opus-5`, one per client, reading the key from the environment
- [x] T004 Parse the response into paragraphs and one opening line in `pipeline/brief.py` (FR-002)
- [x] T005 Reject a brief containing the forbidden verb, retain the committed one, and record the rejection — never silently edit model output (FR-003)
- [x] T006 Check every event the brief references against `event_log.csv` by date, and record an unresolvable reference in `unsure_about` (FR-004, Principle IV)
- [x] T007 Implement the content-hash cache in `pipeline/brief.py`, storing prompt, model, effort and provenance (FR-008)
- [x] T008 Return the committed brief and make no call when no API key is present (FR-009)
- [x] T009 Generate `derived/briefs.json` for the three demo clients and **read all three by hand** before committing — block 8: if it reads like a risk report, tighten the prompt rather than editing the output
- [x] T010 [P] **Unit 1** — `tests/test_determinism.py::test_brief_with_forbidden_verb_is_rejected` asserts a brief containing it is refused and the rejection recorded
- [x] T011 [P] **Unit 2** — `tests/test_determinism.py::test_brief_event_references_are_checked` asserts an unresolvable event reference is recorded rather than shipped as fact

## Phase 2 — Ranking

- [x] T012 Write the ranking prompt in `pipeline/brief.py`, carrying block 8's instruction that age, life stage, drawdown and imminent cash needs weigh more than breach size
- [x] T013 Assemble the ranking input as **derived findings only** — name, age, life stage, AUM and a compact finding summary per client (FR-005, Principle V)
- [x] T014 Implement the single ranking call covering all clients in `pipeline/brief.py` (FR-005)
- [x] T015 Validate the ranking in code: every client exactly once, omissions appended deterministically, duplicates dropped, and every correction recorded (FR-006, [research.md](./research.md) R4)
- [x] T016 Require one sentence of justification per entry in `pipeline/brief.py` (FR-007)
- [x] T017 Generate `derived/ranking.json` and confirm the order is not by AUM (SC-004)
- [x] T018 [P] **Unit 3** — `tests/test_determinism.py::test_ranking_is_validated_not_trusted` asserts a ranking missing a client is corrected and the correction recorded

## Phase 3 — Build

- [x] T019 Implement the command line in `pipeline/build.py` with `--data`, `--clients` and `--series` arguments, none hardcoded (FR-010). **`--series` is required**: a named default put a market series identifier in `pipeline/`, and deriving one from the data was worse — the largest move in this window is European gas at 97%, which would have silently changed the demo's answer. CLAUDE.md's documented command updated to match
- [x] T020 Fail with the offending id named when a client does not exist, in `pipeline/build.py` (FR-012)
- [x] T021 Run all six detectors over the named clients, and the mandate and look-through detectors over every client, in `pipeline/build.py` (FR-011)
- [x] T022 Assemble the call list from the ranking, with name, AUM and justification per entry (FR-013, R1)
- [x] T023 Assemble the per-client payload: header fields, the quoted objective, the brief, the findings with their evidence, the mandate panel with **all** bands, and the scenario (FR-013, R1)
- [x] T024 Assemble the uncertainty record with **data imperfections and method limits kept apart** (FR-014, R1)
- [x] T025 Write `web/public/findings.json` with sorted keys and a fixed indent so byte equality is a real property, creating the directory if absent (FR-015)
- [x] T026 Confirm the build never writes to `data/` (FR-017)

## Phase 4 — Determinism and Definition of Done

- [x] T027 **E2E 1** — `tests/test_determinism.py::test_findings_are_deterministic` builds twice and asserts **byte-identical** output (SC-007). Named in Article VIII
- [x] T028 **E2E 2** — `tests/test_determinism.py::test_build_makes_no_model_call_and_carries_the_figures` asserts the build completes with the API key removed, produces the same bytes, and that the written file contains 42.134, the compliance verdict, the inherited classification and the scenario total (SC-006, SC-008). **A deterministic build of wrong numbers is still deterministic** — this is the assertion that catches that
- [x] T029 Assert every finding in the written file validates against the Finding schema (SC-009)
- [x] T030 Assert the ranking contains all 20 clients exactly once and is not ordered by AUM (SC-003, SC-004)
- [x] T031 Assert `--clients CL-0019` alone succeeds and produces a call list containing that client (SC-005)
- [x] T032 Run `pytest tests/ -v` and paste the output — item 1
- [x] T033 [P] Confirm `grep -rln anthropic pipeline/` matches only `claims.py` and `brief.py` — item 4. Two files now, and only two
- [x] T034 Confirm every event cited in every brief resolves to a row in `event_log.csv` — item 5
- [x] T035 [P] Run `grep -rni recommend pipeline/` and confirm no RM-facing copy contains it — item 6
- [x] T036 Confirm the uncertainty record carries both halves — item 7
- [x] T037 [P] Run the portability grep over `pipeline/` — item 9
- [x] T038 Confirm the model call count is exactly 24 across the system — 20 claims, 3 briefs, 1 ranking (SC-001)
- [x] T039 Commit with the spec number, including the committed briefs, ranking and findings file — item 8

---

## Dependencies

```
Phase 1  T001 … T011   brief.py write_brief
  └─> Phase 2  T012 … T018   brief.py rank
        └─> Phase 3  T019 … T026   build.py
              └─> Phase 4  T027 … T039   determinism, DoD
```

Phase 3 depends on both model artifacts existing, because the build reads
them rather than generating them.

## Article VIII budget

| Layer | Count | Where |
|---|---|---|
| Unit | 3 | T010, T011, T018 |
| E2E | **2** | T027, T028 |

Project total after this spec: **35 unit, 15 integration, 2 e2e**. The
e2e layer is now complete at Article VIII's budgeted 2, and
`test_findings_are_deterministic` — the last named assertion — is one of
them.

## Strategy

**MVP is T019–T027.** A committed findings file that builds
deterministically is what spec 007 needs; the briefs make it worth
reading.

**Cut path**: block 8's own fallback — write the three briefs by hand into
`derived/briefs.json`. Same code path, different `provenance`. Proven in
spec 002.
