# Implementation Plan: Briefs and Build

**Date**: 2026-09-04 | **Spec**: [spec.md](./spec.md) | **Gate**: G3

**Time box**: 80 minutes (`.alamazing/implementation.md` steps 11 and 12:
60 + 20)

## Summary

Two modules and one test.

`pipeline/brief.py` holds the last four model calls in the system — three
briefs and one ranking — cached and committed exactly as `claims.py` does
it. That pattern is already proven, so this is the third instance of it
rather than a new idea.

`pipeline/build.py` is the command-line entry point. It runs the
detectors, assembles the file the web layer reads, and writes it. It is
mostly plumbing; the care is in the shape of the output, which is dictated
by the demo script rather than by what the detectors happen to emit.

`tests/test_determinism.py` is the test block 8 calls the only one that
matters — and it has to prove more than equal bytes.

## Technical Context

**Language**: Python 3.14, pandas, pytest, `anthropic` (in `brief.py`
only). **Model**: `claude-opus-5` at `effort: high` for briefs — this is
prose that gets read aloud — and `high` for the ranking.

**Storage**: `derived/briefs.json`, `derived/ranking.json`, committed.
Output to `web/public/findings.json`.

**Constraints**: No model call at build time when artifacts are committed.
No literal client id, sector, date or series in `pipeline/`. Byte-identical
output across runs.

## Constitution Check

| Article | Status |
|---|---|
| I. Demo Primacy | **PASS** — this produces the file every screen reads, and the sentence the demo ends on |
| IV. Nothing Is Invented | **PASS** — FR-004: brief event references are checked against the event log; unresolvable ones are recorded, not shipped as fact |
| V. Model Never Counts | **PASS** — the model receives **derived findings only**, never a raw client record. It writes prose and orders a list; it computes nothing |
| VI. Evidence | **PASS** — findings carry their evidence through to the file unchanged; FR-013 |
| VII. Determinism | **PASS** — FR-015 and the test that proves it, including the no-API-key run |
| VIII. Test Pyramid | **PASS** — 3 unit + 2 e2e. This spec supplies the **e2e layer** Article VIII budgets at 2 |
| IX. RM Decides | **PASS** — FR-003 rejects a brief containing the forbidden verb rather than editing it. Keep/reject/annotate is spec 007's surface, but the file carries the finding ids it hangs off |
| X. Honest Framing | **PASS** — FR-014 keeps data imperfections and method limits apart, because they are different kinds of not-knowing |
| XI. Portable | **PASS** — FR-010, SC-005. `--clients CL-0019` on stage |
| XIII. Declared Scope | **PASS** — no chat, no demo-time inference, no twenty briefs |

**No violations.**

Two notes:

**Article V is stricter here than anywhere else, and it is the easy thing
to get wrong.** A brief reads better if the model can see the client's
notes and objectives — and it may, those are prose. What it must never see
is a holdings row or a figure it could restate incorrectly. So the brief
prompt receives: the person (name, age, life stage, source of wealth),
their objectives, their notes, and the **findings as already computed**.
Every number in the output came from pandas and travelled through the
prompt as text. The model is transcribing figures, not producing them.

**Article X is why the uncertainty record has two halves.** Spec 000's
imperfections say *the data cannot tell us this*. The detectors'
`unsure_about` strings say *our method has this limit*. Collapsing them
into one list would make the honest thing look like a single caveat blob;
kept apart, S3 can say which is which.

## Structure

```text
pipeline/
├── brief.py            NEW — write_brief, rank. The last 4 model calls
└── build.py            NEW — CLI, assembles web/public/findings.json

derived/
├── claims.json         spec 002
├── briefs.json         NEW — committed
└── ranking.json        NEW — committed

web/public/findings.json  NEW — the artifact the web layer reads

tests/
└── test_determinism.py  NEW — 3 unit + 2 e2e
```

## Phase 0 — complete

Five questions — [research.md](./research.md). Block 8 needed no
corrections, which is the first time in this build.

| # | Finding |
|---|---|
| R1 | The file's shape comes from the demo script's seven beats. Two consequences: the mandate panel needs **all five bands**, not just breaches; S3 needs **two kinds** of uncertainty |
| R2 | Cross-check: `total_aum_usd` agrees exactly with the computed client-level sum (32,214,266). Range 8.18m–87.90m matches the script's "eight million to eighty-eight". All 20 clients are Priscilla's |
| R3 | **4 calls** here — 3 briefs, 1 ranking — bringing the total to the 24 the constitution now records. Same committed-artifact pattern as spec 002 |
| R4 | Every ranking input block 8 names exists in `clients.csv`. The model gets **derived findings only**; the ranking is **validated in code** so a dropped client is corrected rather than lost |
| R5 | **The determinism test needs three assertions, not one.** Equal bytes passes trivially when everything is committed |

## Design decisions

**The determinism test proves three things.** Block 8 asks for equal
output, which a build reading committed files satisfies for free. So the
test also asserts the build makes **no model call** (run with the key
removed) and that the file **contains the recorded figures**. A
deterministic build of the wrong numbers is still deterministic; the third
assertion is the one that would catch a serialisation bug that rounded
42.1343 to 42.

**The ranking is validated, not trusted.** A model asked to order twenty
items will occasionally return nineteen. Missing clients are appended in a
deterministic order and the correction is recorded, so the call list is
never short and the fix is visible.

**A brief containing the forbidden verb is rejected, not edited.**
Silently rewriting model output would make the committed artifact a
fiction. Rejecting keeps the previous brief and records why.

**JSON is written with sorted keys and a fixed indent**, so byte equality
is a real property rather than an accident of dict ordering.

## Time box

| Step | Work | Budget |
|---|---|---|
| 1 | `brief.py` — prompt, call, guards, cache | 30 min |
| 2 | Generate and read the three briefs by hand | 15 min |
| 3 | `build.py` — CLI, assembly, write | 20 min |
| 4 | `test_determinism.py` | 15 min |
| | **Total** | **80 min**, on budget |

**Cut path**: block 8's own fallback — if credits run short, print the
findings and write the briefs by hand into the committed file. Because
briefs are read from disk, the fallback is the same code path; only
`provenance` differs. Already proven in spec 002.
