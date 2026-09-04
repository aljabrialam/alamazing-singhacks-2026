# Tasks: Said vs Held (spec 002)

**Prerequisites**: [spec.md](./spec.md), [plan.md](./plan.md) · specs 000 and 001 verified

**Gate**: G2 · **Time box**: 55 min · **Cut status**: cuttable to the
committed fixture (block 4 FALLBACK), never cut entirely

Phase 0 resolved before the spec was written — [spec.md](./spec.md)
§ Pre-flight. Tests required (Article VIII): **4 unit + 2 integration**.

---

## Phase 1 — Extraction (the only model call in the system)

- [x] T001 Write the extraction prompt in `pipeline/claims.py` as a module constant, carrying block 4's schema and rules verbatim — only claims the client made, skip the RM's own concern, quote their phrasing
- [x] T002 Implement the model call in `pipeline/claims.py` against `claude-opus-5` at `effort: low`, one call per client, reading the key from the environment. *(Amended: originally specified temperature 0 against Sonnet. Temperature cannot be set on current models, and the Sonnet choice was an unrequested cost downgrade — research.md R5.)*
- [x] T003 Strip markdown fences before parsing in `pipeline/claims.py` — models wrap JSON in them regardless of instruction
- [x] T004 Parse defensively in `pipeline/claims.py`: a non-list response, a non-dict claim, or a claim missing `check` is dropped individually while well-formed claims in the same response are kept (FR-012)
- [x] T005 Coerce a `check` value outside the permitted set to `other` in `pipeline/claims.py`, so model drift reduces findings rather than producing wrong ones
- [x] T006 Implement the quote guard in `pipeline/claims.py`: drop any claim whose quoted words do not appear in the source text, and record the rejection (FR-011, Principle IV)
- [x] T007 Implement the content-hash cache in `pipeline/claims.py` keyed on the client's objectives and notes text, storing prompt, model id, provenance and claims (FR-013)
- [x] T008 Return the committed claims and make no call when no API key is present in `pipeline/claims.py` — a missing key degrades the product, it does not break it (FR-015)
- [x] T009 Generate `derived/claims.json` for all 20 clients and **read it by hand** before committing, checking that no claim attributes the RM's words to the client
- [x] T010 [P] **Unit 1** — `tests/test_claims.py::test_malformed_output_returns_nothing` asserts at least four malformed shapes yield zero claims and raise nothing (SC-006)
- [x] T011 [P] **Unit 2** — `tests/test_claims.py::test_quote_must_appear_in_source` asserts a fabricated quote is dropped (SC-007)
- [x] T012 [P] **Unit 3** — `tests/test_claims.py::test_unknown_check_becomes_other` asserts an out-of-set check is coerced, not kept
- [x] T013 [P] **Unit 4** — `tests/test_claims.py::test_fences_are_stripped` asserts fenced JSON parses

---

## Phase 2 — Testing the claims in code

- [x] T014 Implement the seed match in `pipeline/divergence/d1_said.py` against `instrument_name`, `sector`, `sub_asset_class` and `underlying_reference` **only** — never a derived theme label (FR-006, plan.md R4)
- [x] T015 Implement expansion to the look-through themes the seeds belong to in `pipeline/divergence/d1_said.py`, reusing spec 001's `look_through` rather than reimplementing it
- [x] T016 Report both direct and look-through exposure in `pipeline/divergence/d1_said.py` (FR-007)
- [x] T017 Implement `avoid_sector` and `avoid_region` on the shared seed-and-expand mechanism in `pipeline/divergence/d1_said.py`
- [x] T018 Implement `reduce_risk` in `pipeline/divergence/d1_said.py` by comparing the mandate band verdict from `pipeline/mandate.py`, emitting when a breach raises risk above what the client asked for
- [x] T019 Store `needs_liquidity_by` and `refuse_realise_loss` claims without testing them in `pipeline/divergence/d1_said.py` — spec 004 owns liquidity; storing them now avoids a second model call
- [x] T020 Gate emission on a threshold parameter in `pipeline/divergence/d1_said.py`, defaulting to 20% per `.alamazing/implementation.md` step 6 (FR-008)
- [x] T021 Record a checked-and-clear result for a claim that is not contradicted in `pipeline/divergence/d1_said.py` (FR-017)
- [x] T022 Attach evidence to every finding in `pipeline/divergence/d1_said.py`: the client's quote, `clients.csv` or the note id in `rm_notes.json`, and the holdings rows behind the exposure (FR-009)
- [x] T023 Write RM-facing copy in `pipeline/divergence/d1_said.py` that quotes the client and avoids the forbidden verb (FR-016)

---

## Phase 3 — Integration assertions

- [x] T024 **Integration 1** — `tests/test_said_vs_held.py::test_avoid_sector_cl0019` asserts the claim has `check=avoid_sector`, `target=shipping`, and the finding reports `approx(42.134, abs=0.001)` look-through and `approx(33.20, abs=0.01)` direct (SC-001, SC-002)
- [x] T025 **Integration 2** — `tests/test_said_vs_held.py::test_reduce_risk_cl0003` asserts N-005 yields a `reduce_risk` claim quoting her own words (SC-004)
- [x] T026 Assert claims are drawn from N-025 and N-026 in `tests/test_said_vs_held.py` (SC-003)
- [x] T027 Assert every finding quotes the client and cites a source resolving to `clients.csv` or a real note id (SC-005, FR-010)
- [x] T028 Assert detection makes **no** network call, by running it with the model client patched to raise (SC-008)
- [x] T029 Assert two runs over the committed claims give identical findings (SC-009)

---

## Phase 4 — Definition of Done

- [x] T030 Run `pytest tests/ -v` and paste the output — item 1
- [x] T031 Confirm both acceptance figures match `.alamazing/findings.md` with `pytest.approx` — item 2
- [x] T032 Confirm every finding carries file, row ids and values, and validates against `finding.schema.json` — item 3
- [x] T033 Confirm `grep -rn "anthropic" pipeline/` matches **only** `claims.py` — item 4. The wall is the architecture; a second match means it has been breached
- [x] T034 Confirm every cited note id resolves to a row in `rm_notes.json` — item 5
- [x] T035 [P] Run `grep -rni "recommend" pipeline/` — item 6
- [x] T036 Confirm dropped claims and unresolvable targets are recorded in `unsure_about` — item 7
- [x] T037 [P] Run `grep -rn "CL-00\|SYN-\|2026-0\|BRENT" pipeline/` and confirm nothing. The cache moved to `derived/` for exactly this reason: a per-client artifact is data, not code — item 9
- [x] T038 Commit with the spec number and the cache in the same commit — item 8

---

## Dependencies

```
Phase 1  T001 … T013   claims.py + the committed cache
  └─> Phase 2  T014 … T023   d1_said.py, reading the cache
        └─> Phase 3  T024 … T029   integration
              └─> Phase 4  T030 … T038   Definition of Done
```

T014 blocks everything in Phase 2 — it is the trap identified in plan.md
R4, where the wrong implementation *passes the acceptance test*.

## Article VIII budget

| Layer | Count | Where |
|---|---|---|
| Unit | 4 | T010–T013, all offline |
| Integration | 2 | T024, T025 |

Project total after this spec: **20 unit, 8 integration**. Both
integration assertions cite `.alamazing/findings.md`; both use
`pytest.approx`.

## Strategy

**MVP is T001–T017 plus T024.** The hero client's claim producing 42.134%
is the whole demo value of this spec.

**Cut path** (block 4 FALLBACK): if extraction is unreliable, hand-write
the cache and state it in the README. Because the cache is a committed
file read from disk, the fallback is the *same code path* — only
`provenance` differs. Nothing separate to build or test.
