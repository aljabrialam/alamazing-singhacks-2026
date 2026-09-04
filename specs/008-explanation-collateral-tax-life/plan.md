# Implementation Plan: Explanation, Collateral, Tax and Life Events

**Date**: 2026-09-05 | **Spec**: [spec.md](./spec.md) | **Gate**: none (post-G3)

**Time box**: 90 minutes total, **hard**, with a cut after each detector.

## Summary

Four detectors, specified together because they came from one audit, and
built in an order derived from what each actually finds
([research.md](./research.md)).

**This spec is explicitly allowed to ship partially.** The brief says two
or three done well beats all of them thinly, and the constitution's
16:00 freeze converts unbuilt work into roadmap rather than debt. So the
plan is an ordered queue with a stop-anywhere property, not a batch.

| Order | Detector | Where | Budget |
|---|---|---|---|
| 1 | **D8** collateral trajectory | extend `d4_runway.py` | 20 min |
| 2 | **D7** explanation / attribution | new `d7_explain.py` | 30 min |
| 3 | **D9** tax, domicile-aware | new `d9_tax.py` | 25 min |
| 4 | **D10** life events | new `d10_lifeevents.py` | 15 min |

After each: run the suite, rebuild `findings.json`, commit. If the clock
goes, the queue stops where it is and the README says which shipped.

## Technical Context

**Language**: Python 3.14, pandas, pytest. **No model call in any of the
four.**

**Schema**: the Finding `kind` enum currently admits D1–D6. D7, D9 and
D10 need it extended to D10. D8 is not a new kind — it extends the
existing D4 finding, which is the right call: a client does not have a
"liquidity finding" and a separate "collateral finding", they have one
funding problem.

**Constraints**: no literal client id, instrument id, sector, domicile,
date or series in `pipeline/`. Deterministic. No "recommend".

## Constitution Check

| Article | Status |
|---|---|
| I. Demo Primacy | **PASS for D8, conditional for the rest.** D8 changes what a judge sees on the CL-0014 screen. D7/D9/D10 add panels; if they do not reach the screen before the freeze they are roadmap, not features |
| II. Specification First | **PASS** — spec written before code, cut order fixed in advance so nothing is relitigated at 15:00 |
| IV. Nothing Is Invented | **PASS, and load-bearing here.** Two of these detectors have a documented way of being confidently wrong. D7 must not credit the market with money paid in; D9 must not assume a tax treatment for a domicile it has no rule for |
| V. Model Never Counts | **PASS** — no model call in any of the four |
| VI. Evidence | **PASS** — facility rows, transaction rows, holdings rows, and the profile fields all cited |
| VII. Determinism | **PASS** — pure arithmetic over stored columns |
| VIII. Test Pyramid | **PASS** — ~2 unit + 1 integration per detector, added with each |
| IX. RM Decides | **PASS, and it is the whole design of D9.** No trade, no harvest, no optimisation. FR-015 |
| X. Honest Framing | **PASS** — the partial-ship outcome is planned for and labelled, not discovered |
| XI. Portable | **PASS** — the domicile table is data-shaped with an explicit "no rule recorded" default |
| XII. Vertical Slices | **PASS** — each detector ships end to end, findings through to the screen, before the next starts |

**No violations.**

Two notes:

**Article IV is why D9 is specified as a reporter rather than an
optimiser.** CL-0014 holds ~62.6m of unrealised losses and is domiciled
in Hong Kong. Every tax-optimisation instinct says harvest. The correct
output is that harvesting is of little value to *him* — and a system that
gets this wrong is not slightly off, it is giving a client advice he can
immediately identify as ignorant of his own affairs. The negative finding
is the valuable one.

**Article I is why the order is what it is.** D8 is first not because it
is easiest but because it is the only one of the four that changes a
screen a judge will definitely see. CL-0014 is currently the thinnest of
the three briefed clients; the trajectory makes him the one where waiting
has a measurable cost.

## Phase 0 — complete

Six findings — [research.md](./research.md). The two that shape the code:

**D7 would credit the market with USD 3.84m the client paid in.** The
FCN's +4,156,210 is a subscription: 300,000 units at HKD 100 on
2026-04-15, now HKD 108.20. Reported as one number the portfolio looks
like it gained 6.02m; the truth is ~3.84m in and ~2.18m earned.

**D9 would tell a Hong Kong domiciliary to harvest capital losses.** See
above.

## Design decisions

**D8 extends the D4 finding rather than adding a kind.** One funding
problem, one finding. The trajectory goes inside the existing `facility`
object as a list of snapshots, so the web layer needs one new panel, not
a new route.

**Attribution reports three buckets and never one total.** FR-006 and
FR-008. A single "portfolio change" figure is the wrong shape for the
question, regardless of how it is computed.

**The domicile table is explicit and small**, covering only the
domiciles present in the data, with `None` meaning *no rule recorded* —
which is reported rather than defaulted. It is not a tax engine and the
copy must not let anyone think it is.

**D10 addresses the profile, not the portfolio.** The finding is that the
recorded `liquidity_needs` contradicts the client's own stated plans —
and the profile is what drives suitability, so it is the thing to fix.

## Time box and the stop rule

90 minutes, four checkpoints. **After each detector: suite green,
`findings.json` rebuilt, committed.** The queue stops wherever the clock
stops, and the README's roadmap section names what did not ship and why.

The one thing this plan will not do is start a detector it cannot finish.
Principle XII: from 13:00 there must always be a runnable path from
`data/` to a rendered brief, and a half-written detector in the build
breaks it.
