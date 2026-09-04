# Implementation Plan: Liquidity Runway and the Unanswered Question

**Date**: 2026-09-04 | **Spec**: [spec.md](./spec.md) | **Gate**: G2

**Time box**: 65 minutes (`.alamazing/implementation.md` steps 8 and 9:
40 + 25)

## Summary

Three files. A small FX helper, and the two detectors.

`pipeline/fx.py` converts an amount to USD using the market context,
choosing multiplication or division from the rate's **stated unit**. It is
its own module because getting it wrong is a 61× error and because spec
005 will need it too.

`pipeline/divergence/d4_runway.py` is the larger detector and the one
where the interesting work is. The naive version — compare need to liquid
assets — says both demo clients are comfortable. Netting pledged
collateral says one of them cannot fund his obligation at all without
triggering a margin call.

`pipeline/divergence/d5_unanswered.py` is twenty lines and two guards. It
is the one block 6 says not to cut.

One committed contract changes: the Finding schema's `kind` enum extends
to D6.

## Technical Context

**Language**: Python 3.14, pandas, pytest. **No model call.**

**Constraints**: No literal currency, series id, client id or date in
`pipeline/`. FX rates read from `market_context.csv` at the reporting
snapshot. Deterministic.

## Constitution Check

| Article | Status |
|---|---|
| I. Demo Primacy | **PASS** — D5 sets up spec 005's answer; block 6 calls it the conversion from analytics to advisory |
| IV. Nothing Is Invented | **PASS** — FR-002: no rate, no figure. The rate is read, never assumed, and the *convention* is read too |
| V. Model Never Counts | **PASS** — no model call |
| VI. Evidence | **PASS** — needs cite `planned_cash_needs.csv`, facilities cite `credit_facilities.csv`, open questions cite the note id |
| VII. Determinism | **PASS** — explicit sorts; fixed regexes |
| VIII. Test Pyramid | **PASS** — 5 unit + 3 integration |
| IX. RM Decides | **PASS** — reports what funding costs, never what to sell |
| X. Honest Framing | **PASS** — R2's contradiction, R5's recorded false negative, and the private-market lag all stated rather than smoothed |
| XI. Portable | **PASS** — currencies come from the data; the FX helper takes a currency code as an argument |

**No violations.**

Two notes:

**Article IV is why `fx.py` exists at all.** The temptation is a
three-line inline conversion. But the two rates this demo needs use
*opposite conventions*, and only the `unit` column says which. An inline
guess turns HKD 60m into USD 468m — a number that would look like a
catastrophe rather than an obligation, and wrong in the direction that
makes the finding more dramatic. That is exactly the failure mode
Principle IV exists to prevent, so the conversion gets its own module and
its own test.

**Article X is why block 6's "Tight" is not reproduced.** Block 6's
acceptance line asserts CL-0003's liquidity is tight; block 6's own rule
computes 88.29%. Reproducing the assertion would mean shipping a figure
the data contradicts. The spec reports what is true and says why it
differs — R2.

## Structure

```text
pipeline/
├── fx.py                        NEW — unit-aware conversion
└── divergence/
    ├── d4_runway.py             NEW — needs, commitments, facilities
    └── d5_unanswered.py         NEW — twenty lines, two guards

specs/001-divergence-engine/contracts/finding.schema.json   MODIFIED — enum D1..D6

tests/
├── test_fx.py                   NEW — 2 unit
├── test_runway.py               NEW — 2 unit + 2 integration
└── test_unanswered.py           NEW — 1 unit + 1 integration
```

## Phase 0 — complete

Six questions, resolved before any code — [research.md](./research.md).

| # | Finding |
|---|---|
| R1 | Needs are EUR and HKD. **The two rates use opposite conventions**, knowable only from the `unit` column. Guessing is a 61× error |
| R2 | **Block 6's acceptance narrative contradicts block 6's rule.** Tier-based liquidity is 88.29%, not the 16.8% the "Tight" claim rests on. Both reported; the stronger true statement replaces "tight" |
| R3 | **CL-0014 cannot fund his need by selling.** Facility at 69.41% LTV against a 70% trigger; funding the need pushes it to 97.76%. Not in `findings.md` |
| R4 | Tiers measured. CL-0014's 26.62% illiquid matches the recorded property + accumulator exactly |
| R5 | The matcher needs **two guards**: answered-in-note, and bare "unresolved" as market commentary. One recorded false negative |
| R6 | **The Finding schema blocks this spec.** `kind` enum is D1–D4; this spec emits D5. Extended to D6 |

## Design decisions

**FX conversion reads the unit, not the series name.** R1.

**Both liquidity figures are reported.** Tier-based answers "can this be
funded by the date"; cash-plus-fixed-income answers "what does funding it
consume". The second is the finding for CL-0003 — R2.

**Pledged collateral is netted, and the post-sale loan-to-value is
computed.** Without it, CL-0014 reads as comfortable at 2.53× coverage. He
is 0.59pp from a margin call — R3.

**The private-market lag is noted, never flagged.** Block 6 is explicit:
industry practice, not an error.

**D5's admission check overrides the answer check**, because *"Have not
yet replied"* contains "replied" and would otherwise cancel itself — R5.

**The schema enum is extended rather than worked around.** The schema
already defines an `unanswered_question` object, so it anticipated D5 and
only the enum lagged.

## Time box

| Step | Work | Budget |
|---|---|---|
| 0 | Extend the Finding schema enum | 2 min |
| 1 | `fx.py` + tests | 8 min |
| 2 | `d4_runway.py` | 30 min |
| 3 | `d5_unanswered.py` | 15 min |
| 4 | Tests | 10 min |
| | **Total** | **65 min**, on budget |

**Cut order within this spec**: if the clock runs out, D4 goes and D5
stays. Block 6 says so in terms.
