# Implementation Plan: Scenario

**Date**: 2026-09-04 | **Spec**: [spec.md](./spec.md) | **Gate**: G2 (closes it)

**Time box**: 40 minutes (`.alamazing/implementation.md` step 10)

## Summary

One module, `pipeline/divergence/d6_scenario.py`. It is the smallest
detector after D5 and the one the demo ends on.

The arithmetic is a ratio of two prices applied to a market value. The
care goes into three places: the position that has no past, the leg the
proxy comes from, and the second-order effect — which must be *quoted*
rather than inferred, because the moment the system starts reasoning about
a client's business it stops being auditable.

`detect(book, client_id, series_id, date_now, date_then)`. The series and
both dates are arguments; nothing is baked in.

## Technical Context

**Language**: Python 3.14, pandas, pytest. **No model call, no forecast,
no volatility assumption** — block 7 says so three ways.

**Constraints**: No literal series id, date, client id or instrument id in
`pipeline/`. Deterministic.

## Constitution Check

| Article | Status |
|---|---|
| I. Demo Primacy | **PASS** — this is the closing beat. D5 finds the question, this answers it |
| IV. Nothing Is Invented | **PASS** — FR-007: no price, no ratio, no figure. The second-order effect is **quoted from N-025**, not inferred (FR-010) |
| V. Model Never Counts | **PASS** — arithmetic over stored prices |
| VI. Evidence | **PASS** — cites the price columns, the series at both dates, `clients.csv` and the note id |
| VII. Determinism | **PASS** — pure arithmetic, explicit sorts |
| VIII. Test Pyramid | **PASS** — 3 unit + 1 integration, the last named assertion (`test_scenario_cl0019`) |
| IX. RM Decides | **PASS** — states the impact, proposes nothing |
| X. Honest Framing | **PASS** — R3's worst-of alternative reported alongside the headline, with the direction of the uncertainty stated |
| XI. Portable | **PASS** — FR-001, SC-007. A different series and dates is a different scenario, demonstrated on stage |

**No violations.**

Two notes:

**Article IV is why the second-order effect is a quote.** The tempting
version reasons about his business: *Gulf logistics, therefore charter
rates, therefore earnings fall.* That chain is plausible and the system
must not make it. What it can do is report that **he said it** — N-025
records his own view that charter rates stay elevated while the Strait is
unresolved. The system cites him. That is the difference between an
auditable finding and a language model free-associating about
geopolitics, which is the failure the brief names explicitly.

**Article X is why the worst-of alternative is reported.** The recorded
−2.5m uses Pacific Orient as the proxy leg. The basket's third name fell
further and is not held, so on a strict worst-of reading the impact is
nearer −2.65m. The headline stays at the recorded figure; the alternative
is stated because the uncertainty runs *against* the client, and that is
the direction worth naming.

## Structure

```text
pipeline/divergence/
└── d6_scenario.py     NEW — reprice, proxy, second-order

tests/
└── test_scenario.py   NEW — 3 unit + 1 integration
```

## Phase 0 — complete

Five questions — [research.md](./research.md). Every recorded figure
reproduces.

| # | Finding |
|---|---|
| R1 | All of block 7's table reproduces: −431,200 / −722,210 / −535,200, total **−2,509,429 = −7.790%** against a recorded −2.5m / −7.8% |
| R2 | The FCN has no pre-war row. Block 7's proxy leg is **structurally correct** for a worst-of basket — Pacific Orient is the worse of the two he holds. Use **price** ratios, not market-value ratios |
| R3 | **The third basket leg is in the book and fell furthest** (−23.10% against −19.75%). He does not hold it. Strict worst-of gives −2.649m / −8.223%, outside the recorded tolerance. Headline stays recorded; alternative reported |
| R4 | The second-order effect is **in the data** — source of wealth in `clients.csv`, and his own view in N-025. Quoted, not inferred |
| R5 | The series is **evidence, not input**: the arithmetic runs off price columns. Still a parameter, because the finding cites it |

## Design decisions

**Price ratios, not market-value ratios.** Market value embeds quantity,
which changes when a position is traded. Repricing is a question about
price. The price-based figure also lands closer to the record — R2.

**The proxy leg is the worst mover among the legs held.** Not "the first
one" and not "the average". A worst-of note pays on its worst leg, so the
proxy should come from there — R2.

**The worst-of alternative is computed, not just mentioned.** A sentence
saying "it might be worse" is weaker than a number. R3.

**The second-order effect is assembled from two cited rows**, never from
reasoning about the client's industry — R4.

**Both dates are validated as snapshots, and order-independent.** Passing
them the wrong way round should not silently invert the sign of the
answer.

## Time box

| Step | Work | Budget |
|---|---|---|
| 1 | Repricing and the proxy | 20 min |
| 2 | Second-order effect | 10 min |
| 3 | Tests | 10 min |
| | **Total** | **40 min**, on budget |
