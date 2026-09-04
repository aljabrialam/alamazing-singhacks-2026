# Implementation Plan: Said vs Held

**Date**: 2026-09-04 | **Spec**: [spec.md](./spec.md) | **Gate**: G2

**Time box**: 60 minutes (`.alamazing/implementation.md` step 6)

## Summary

Two modules with a hard wall between them.

`pipeline/claims.py` makes **one model call per client**, turning prose
into machine-testable claims, and writes them to a committed cache
alongside the prompt that produced them. It is the only file in the
repository that imports `anthropic`.

`pipeline/divergence/d1_said.py` reads that cache and tests each claim
against the portfolio in deterministic pandas. It has no model import and
cannot acquire one without the Definition of Done grep failing.

That wall is the architecture. Everything else is a string comparison and
a `groupby`.

## Technical Context

**Language**: Python 3.14. **Dependencies**: pandas, pytest, and
`anthropic` — used in `claims.py` only. **Model**: `claude-opus-5` at
`effort: low`.

*Two corrections to this plan as first written, both in
[research.md](./research.md) R5:* the model is Opus, not Sonnet — I had
optimised for per-token cost on 20 build-time calls, which is not a real
constraint and not my call to make. And **temperature 0 is not
achievable**: sampling parameters were removed from the Messages API.

**Storage**: `derived/claims.json`, committed. Holds the prompt, model id,
effort, and every claim with its fingerprint and provenance. Outside
`pipeline/` because it is derived data keyed by client id, not code.

**Constraints**: No model call at detect time (Principle VII). No literal
client id, sector or target in `pipeline/` (Principle XI).

## Constitution Check

| Article | Status |
|---|---|
| I. Demo Primacy | **PASS** — this is the differentiator; the quote-back is the line the pitch turns on |
| III. Spine | **PASS** — 42.1343 pre-verified through the seed-and-expand chain before the spec was written |
| IV. Nothing Is Invented | **PASS** — FR-011 drops any claim whose quote is not literally present in the source text. This is the guard that matters: a model asked to quote will occasionally paraphrase, and a paraphrase presented as a client's words in front of that client is the worst failure this system could have |
| V. Model Never Counts | **PASS** — the model receives prose and returns claims. It is never sent a figure, a weight or a holding. `d1_said.py` imports no model client |
| VI. Evidence | **PASS** — every finding cites `clients.csv` or a note id in `rm_notes.json`, plus the holdings rows behind the exposure |
| VII. Determinism | **PASS by a different mechanism than the constitution names** — extraction at build time, output committed, prompt committed beside it. **Temperature 0 is not achievable** (removed from the Messages API); the committed cache supplies determinism instead, and is the stronger guarantee. Flagged for amendment — [research.md](./research.md) R5 |
| VIII. Test Pyramid | **PASS** — 4 unit (parse, malformed, quote-guard, check-coercion) + 2 integration (SC-002, SC-004) |
| IX. RM Decides | **PASS** — no "recommend"; the RM's own concern is not extracted as a client claim, and spec 004 surfaces it separately |
| X. Honest Framing | **PASS** — FR-017 records checked-and-clear; FR-018 records what could not be determined; the fallback is a README statement, not a hidden branch |
| XI. Portable | **PASS** — targets come from claims, which come from the data. Nothing is named in code |
| XIII. Declared Scope | **PASS** — no chat, no demo-time inference |

**No violations.**

One note rather than a tick. **Article IV is doing more work here than
anywhere else in the build.** Every other detector reads numbers from
files; this one reads meaning from prose, and the failure mode is a
plausible sentence rather than a wrong figure. Two guards, both cheap:
the quote must appear verbatim in the source text (FR-011), and the check
type must be in the permitted set or it is coerced to `other`, which
tests nothing. A model that drifts produces *fewer* findings, never
invented ones.

## Structure

```text
pipeline/
├── claims.py                 NEW — the only anthropic import in the repo
└── divergence/
    └── d1_said.py            NEW — reads the cache, tests in pandas

derived/
└── claims.json               NEW — committed: prompt + claims + provenance
                              outside pipeline/ because it is derived data
                              keyed by client id, not code

tests/
├── test_claims.py            NEW — 4 unit, all offline
└── test_said_vs_held.py      NEW — 2 integration
```

**Why the cache is a committed file and not a build artifact.** The
constitution requires no model call at demo time and the prompt committed
alongside its output. A file in the repo satisfies both, is diffable in
review, and makes block 4's fallback free: the hand-written fixture and
the model output are the *same code path*, differing only in the
`provenance` field. There is no degraded mode to build or test separately.

## Phase 0 — Research

Resolved before the spec was written; recorded in [spec.md](./spec.md)
§ Pre-flight.

| # | Question | Resolution |
|---|---|---|
| R1 | Can `target = "shipping"` reach 42.134%? | **Yes**, via seed-on-source-fields then expand-to-theme. Verified: seed 33.1979%, expanded 42.1343% |
| R2 | Is `shipping` a sector? | **No.** Booked `Industrials`. A `sector == target` test finds nothing — this is why the naive design fails |
| R3 | Do the required notes carry the required claims? | **Yes.** N-025 has his uncorrelation statement, N-026 his Strait question, N-005 "never taken a risk with money" and N-006 "something safe and boring" |
| R4 | Can seeds be matched against theme labels? | **No — rejected.** It reaches 42.13% only because a pipeline-written label contains "Shipping". Circular, and breaks on a reword |

## Design decisions

**Seeds from source fields only.** `instrument_name`, `sector`,
`sub_asset_class`, `underlying_reference`. Never `theme_sector` or
`theme_issuer`. R4 is the reason and it is the subtlest trap in this spec:
the wrong version *passes the acceptance test* while being circular.

**Both figures are reported.** Direct exposure to the named target
(33.20%) and the look-through theme it sits inside (42.13%). Reporting
only the second invites "how is an energy fund shipping?"; reporting both
answers it before it is asked.

**One call per client, cached by content hash.** The key is a hash of the
objectives and notes text, so editing a note invalidates that client's
entry and nothing else.

**`other` is a sink, not an error.** A check type outside the permitted
set becomes `other`, which no code path tests. Model drift reduces
findings rather than producing wrong ones.

**Detection never touches the network.** `d1_said.py` imports only pandas
and spec 001. Asserted by grep and by running detection with the model
client patched to raise.

## Time box

| Step | Work | Budget |
|---|---|---|
| 1 | `claims.py` — prompt, call, parse, guards, cache | 25 min |
| 2 | Generate and hand-review the cache for 20 clients | 10 min |
| 3 | `d1_said.py` — the check implementations | 20 min |
| 4 | Tests | included |
| | **Total** | **55 min** within the 60-minute budget |
