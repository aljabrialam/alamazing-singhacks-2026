# Implementation Plan: Mandate Classification

**Date**: 2026-09-04 | **Spec**: [spec.md](./spec.md) | **Gate**: G2

**Time box**: 45 minutes (`.alamazing/implementation.md` step 7)

## Summary

One new module, `pipeline/divergence/d2_mandate.py`, plus **two changes to
`pipeline/mandate.py`** — the shared band comparison spec 001 built.

The comparison already works. What this spec adds is the judgement on top
of it: given a breach, was it inherited, chosen, or drifted into? That is
three lines of logic and a careful reading of two columns.

The `mandate.py` changes are not additive niceties. Phase 0 found that
comparing custody portfolios to mandate bands produces three false
breaches, one of which tells a founder their own company is a limit
violation. Fixing it changes spec 001's output for two clients and is a
**regression fix**, not scope creep.

## Technical Context

**Language**: Python 3.14, pandas, pytest. **No model call.**

**Storage**: None — reads the `Book`.

**Constraints**: Deterministic. No literal client id, asset class, date or
year in `pipeline/`. The reporting year is derived from the latest
snapshot (FR-011).

## Constitution Check

| Article | Status |
|---|---|
| I. Demo Primacy | **PASS** — the mandate panel is named in "never cut", and the `inherited` classification is the third of the three demo findings |
| IV. Nothing Is Invented | **PASS** — classification derives from inception date and transaction rows. The portfolio literally named *"Inherited Portfolio - Under Review"* is **not** read; a name is not evidence |
| V. Model Never Counts | **PASS** — no model call |
| VI. Evidence | **PASS** — every finding carries mandate rows, inception date, and the transactions examined |
| VII. Determinism | **PASS** — explicit sorts; classification is a pure function of two columns |
| VIII. Test Pyramid | **PASS** — 4 unit + 3 integration, including `test_mandate_cl0003_inherited` which Article VIII names by name |
| IX. RM Decides | **PASS** — no rebalancing proposal, no "recommend". Three classifications describe three *conversations*, and which to have is hers |
| X. Honest Framing | **PASS** — two reference-document errors and one live defect recorded in [research.md](./research.md) rather than silently corrected |
| XI. Portable | **PASS** — reporting year derived from data; transaction types are named constants; no asset class named in code |
| XII. Vertical Slices | **PASS** — `detect()` returns findings in a REPL |

**No violations.**

Two notes rather than ticks:

**Article IV is why the portfolio name is ignored.** `PF-0005` is called
*"Inherited Portfolio - Under Review"*. Reading that string would produce
the right answer for the wrong reason and would generalise to nothing.
Classification uses inception date plus transaction history, and the name
is not consulted — which is also what makes the demo answer "would this
work on other data?" honestly.

**Article X is doing unusual work here.** This spec ships a fix to code
that already passed its own gate. The temptation is to quietly correct
`mandate.py` and say nothing; the brief explicitly rewards the opposite.
The before/after table for CL-0001, CL-0002 and CL-0017 is in
[research.md](./research.md) R4.

## Structure

```text
pipeline/
├── mandate.py                 MODIFIED — exclude custody; report separately
└── divergence/
    └── d2_mandate.py          NEW — classification and findings

tests/
├── test_mandate.py            EXTENDED — custody exclusion
└── test_classification.py     NEW — 4 unit + 3 integration
```

## Phase 0 — complete

Five questions, all resolved against the data before any code. Full
detail in [research.md](./research.md). Summary:

| # | Finding |
|---|---|
| R1 | **Both reference docs are wrong** about the transaction column and values. `transaction_type`, not `type`; `'Buy'` / `'Structured Product Subscription'`, not `'BUY'` / `'SUBSCRIPTION'`. Written as specified it matches nothing and **every breach classifies `inherited`** — right answer, invisible bug |
| R2 | All three acceptance classifications reproduce. CL-0014 proves the rule must be "into the **breached** class" — he did subscribe to something, just not equity |
| R3 | **Block 5's rule is one-directional.** A purchase cannot explain a below-minimum breach; only a disposal can. Breach direction must select evidence direction |
| R4 | **Three custody portfolios.** Bands do not apply. Three false breaches today, including a founder's own shareholding at 100%. Live defect in spec 001's `compliance_clean` |
| R5 | 14 real breaches across 10 clients after exclusion. CL-0019 is in the clean half — which is the argument |

## Design decisions

**Breach direction selects evidence direction.** `above_max` looks for
acquisitions into the class; `below_min` looks for disposals out of it.
Block 5 specifies only the first, which is incorrect for the second — see
R3. This is the one place the spec deviates from the block on reasoning
rather than on data.

**`client_directed` beats `inherited`.** A portfolio transferred in this
year *and* subsequently bought into is not something nobody chose.

**Custody is excluded, not deleted.** The portfolio is still reported,
with its value and a held-not-managed status. Removing it from view would
be a different error — Priscilla needs to know the founder shareholding
exists, she just does not need it flagged against a band it was never
managed to.

**The reporting year comes from the latest snapshot.** `inherited`
requires inception "in 2026", and 2026 must not appear in `pipeline/`.

**Transaction types are named constants.** R1 is the reason: a literal at
the point of use is how the silent-match-nothing bug happens, and a
constant is greppable and testable.

## Time box

| Step | Work | Budget |
|---|---|---|
| 1 | `mandate.py` — custody exclusion + separate reporting | 10 min |
| 2 | Re-verify spec 001 still green after the change | 5 min |
| 3 | `d2_mandate.py` — classification and findings | 20 min |
| 4 | Tests: 4 unit + 3 integration | 10 min |
| | **Total** | **45 min**, on budget |
