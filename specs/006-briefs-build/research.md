# Phase 0 Research — Briefs and Build (spec 006)

**Date**: 2026-09-04 · Run before the spec was written.

Five questions. No corrections to the reference documents this time —
block 8 is accurate. One cross-check worth having, and two design
decisions that follow from what the demo script actually needs.

---

## R1 — What must `findings.json` contain? Read from the demo script.

The file is the only thing the web app gets, so its shape is dictated by
the three screens in `docs/demo-script.md` rather than by what the
detectors happen to produce.

| Beat | Screen | Needs |
|---|---|---|
| 0:00–0:35 | S1 call list | 20 clients, ranked, each with name, AUM, and one line of justification |
| 0:35–1:00 | S2 header | name, age, mandate, AUM, and the **objective quoted verbatim** |
| 1:00–1:30 | S2 exposure | the look-through theme, its total, and the positions comprising it |
| 1:30–1:50 | S2 mandate panel | **every band**, actual against range, and the compliance verdict |
| 1:50–2:15 | Evidence drawer | holdings rows, the event log entry, the RM note |
| 2:15–2:40 | S2 opening line | the unanswered question, and one sentence to say aloud |
| 2:40–2:52 | Actions + S3 | keep / reject / annotate, and the uncertainty screen |

Two consequences:

**The mandate panel needs all five bands, not just breaches.** The 1:30
beat is *"every mandate band is respected"* — that sentence requires the
bands to be on screen. Spec 003's checked-and-clear finding already
carries them.

**S3 needs two different kinds of uncertainty.** The imperfections spec
000 recorded (missing cost basis, stale valuation) *and* the
`unsure_about` strings every detector emits. They are different: one is
"the data cannot tell us", the other is "our method has a limit".
`findings.json` carries both, separately.

---

## R2 — Cross-check: does the file's AUM agree with the holdings?

**Yes, exactly.** `clients.csv` carries `total_aum_usd`, and it matches
the sum of `market_value_usd` computed at client level:

```
CL-0019   total_aum_usd  32,214,266.33
          computed       32,214,266
```

Worth checking rather than assuming, because the whole build rests on
client-level sums and an independent column that agrees with them is free
corroboration. It also means S1 can quote AUM from either source without
the two disagreeing on stage.

The range across the book is **USD 8,182,936 to 87,902,980** — and the
demo script's opening line says *"twenty families, from eight million to
eighty-eight"*. The script was written against the data.

All twenty clients belong to **RM-SG-014, Priscilla Ong, Asia desk**. So
the call list is her whole book, not a filtered subset.

---

## R3 — How many model calls, and where do they live?

Constitution, Technology Standards (as amended to 1.2.0): **24 calls in
the whole system** — 20 claim extractions, 3 briefs, 1 ranking.

This spec adds the last **4**.

| Call | Count | Scope |
|---|---|---|
| `write_brief` | 3 | the demo clients only |
| `rank` | 1 | all 20, in one call |

Block 8 says briefs are one call per client and the build runs all six
detectors over the three demo clients. So three briefs, not twenty —
which is also the honest scope: a brief is only worth writing where the
detectors produced something substantial to write about.

**Same architecture as spec 002.** Output committed to disk, keyed by a
content hash of its inputs, with the prompt and model recorded alongside.
Regenerating is explicit; the demo path reads the file and makes no call.
That is what Principle VII asks for and it is already proven to work.

`derived/briefs.json` and `derived/ranking.json`, beside
`derived/claims.json`.

---

## R4 — Ranking must not be by portfolio size, and the inputs exist

Block 8: *"ranks all twenty clients by how soon a conversation is worth
having — not by portfolio size. Age, life stage, drawdown and imminent
cash needs weigh more than breach size."*

Every input named is present in `clients.csv`:

```
age, life_stage, risk_profile, risk_tolerance_score,
investment_horizon_years, liquidity_needs, objectives
```

`life_stage` has twelve values, several of which carry urgency on their
face — *"Recently inherited - transition"*, *"Pre-retirement"*,
*"Post-liquidity event"*, *"Retired - legacy and philanthropy"*.

**Decision**: the model ranks, and it receives **derived findings only** —
never raw client records (Principle V's table: *"Receive a raw client
record"* is in the MUST NOT column). So the ranking input per client is:
name, age, life stage, AUM, and a compact summary of what the detectors
found. The model weighs urgency; it computes nothing.

**One thing the model must not do**: invent a client id or reorder into a
list that omits someone. So the ranking is validated in code — every
client id must appear exactly once, and any the model drops are appended
in a deterministic order rather than lost.

---

## R5 — What does `test_findings_are_deterministic` actually have to prove?

Block 8 calls it *"the only one that matters"*. Two builds, identical
output.

**The subtlety is that a naive version passes trivially.** If the build
reads committed briefs and committed claims, then of course two runs
match — nothing varies. That test would be worth almost nothing.

**Decision**: the determinism test asserts on the **serialised JSON
bytes**, and separately asserts that the build makes **no model call** —
by running it with the API key removed. Together those prove the useful
property: the demo output is fixed *and* it is fixed because the model
calls are committed rather than because the test was lucky.

A second assertion is worth more than either: the file must contain the
recorded figures. A deterministic build of the wrong numbers is still
deterministic. So the end-to-end test checks 42.134, `compliance_clean`,
the inherited classification and the scenario total in the written file —
the same figures the unit and integration layers assert, verified once
more after serialisation, where a float could have been rounded or a key
dropped.

---

## Resolved

Five questions. Block 8 needed no corrections. The two decisions that
matter: **the model receives derived findings only** (R4), and **the
determinism test proves the absence of model calls, not just equal
output** (R5).
