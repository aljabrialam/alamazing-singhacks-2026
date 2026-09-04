# Phase 0 Research — Explanation, Collateral, Tax, Life Events (spec 008)

**Date**: 2026-09-05 · Run before the spec was written.

Four gaps identified by auditing the build against the official brief's
*"Directions the Data Supports"*. This file establishes whether the data
supports each, and what each would actually find — which is what sets the
priority.

**The brief's own warning governs the scope decision:**

> A menu, not a checklist. Two or three done well beats all of them done
> thinly.

So all four are specified. They are **not** all built. The cut order in
[tasks.md](./tasks.md) is derived from the findings below, and whatever
does not ship by the freeze is labelled roadmap in the README rather than
half-implemented.

---

## R1 — D7 Explanation: the machinery exists and is unused

`pipeline/diff.py` supplies `diff()` and `attribution()`. Both were built
and tested in spec 000 and are called **nowhere** outside their own test
file. Building Block 1 — the one the brief lists *first* — is exactly what
they are for.

Attribution for the hero client, pre-conflict snapshot to latest:

```
SYN-SP-0505  Fixed Coupon Note ref. Basket C     +4,156,210   +12.90pp
SYN-ST-0104  Pacific Orient Shipping Ltd            +722,210    +0.14pp
SYN-EQ-0008  Global Energy Majors Equity Fund       +535,200    -0.01pp
SYN-EQ-0025  Asia Pacific Shipping and Logistics    +431,200    -0.40pp
SYN-AL-0303  Tanjong Global Macro Fund              +221,400    -0.53pp
SYN-FI-0210  Emerging Market Sovereign Bond Fund    -215,000    -2.34pp
                                          TOTAL   +6,018,820
```

**And here is why this needs care rather than a chart.** The largest line
is not performance. It is a purchase:

```
transactions.csv  2026-04-15  Structured Product Subscription
                  SYN-SP-0505  300,000 units @ HKD 100.00 = HKD 30,000,000
holdings.csv      2026-08-26   300,000 units @ HKD 108.20 = HKD 32,460,000
                                                          = USD  4,156,210
```

He **paid in HKD 30m** — about USD 3.84m at the snapshot rate. So of the
+6.02m the portfolio gained, roughly **3.84m is money he put in, and only
~2.18m is market movement.**

A naive attribution credits the market with 6.02m. That is the difference
the brief is describing between *"did arithmetic"* and *"understood what
you were looking at"* — and it is a mistake that flatters the bank, which
makes it worse.

**Decision**: attribution reports **three buckets, never one number** —
positions held throughout (genuine market movement), positions acquired in
the window (new money, explicitly not performance), and positions disposed
of. `transaction_type` in `('Buy', 'Structured Product Subscription',
'Redemption Request', 'Withdrawal')` identifies a flow, using the same
named constants spec 003 established.

Events are already available per client: `events_touching` returns seven
for the hero client in this window, including the two that matter
(2026-03-04, 2026-08-05). So the *position → change → cause* loop the
brief calls *"the core of the whole challenge"* can be closed from parts
that already exist and are already tested.

**Cost**: assembly plus a flow/market split. **Value**: Building Block 1,
listed first in the brief, currently unaddressed.

---

## R2 — D8 Collateral: we read one snapshot of five

`credit_facilities.csv` carries `drawn`, `collateral_market_value`,
`lending_value`, `ltv_pct` and `headroom` at **all five snapshots**. Spec
004 reads the latest only.

CL-0014's facility `CF-0002`:

```
              LTV      drawn         headroom      collateral value
2025-12-31   53.93%   52,000,000   44,420,170      219,536,340
2026-02-27   53.53%   52,000,000   45,141,750      245,469,500
2026-03-31   65.62%   58,000,000   30,390,462      222,792,925   <- drew +6m
2026-06-30   67.96%   58,000,000   27,350,325      212,160,650
2026-08-26   69.41%   58,000,000   25,565,930      206,878,860   <- trigger 70%
```

Two facts only the trajectory shows:

**He drew an extra HKD 6m in March**, while his collateral was falling.
That is a decision, not drift — and it is the single move that took him
from comfortable to exposed.

**Since March he has borrowed nothing more and his loan-to-value has
still risen** — 65.62 → 67.96 → 69.41. The collateral is shrinking
underneath him, and we already know why: it *is* the portfolio that is
29.45% one property developer, down 41–47%.

Headroom fell from HKD 44.4m to 25.6m while he did nothing.

**Why this matters more than the static reading.** Spec 004 currently
says *"0.59 percentage points from a margin call"*, which reads as a fact
that might always have been true. The trajectory says he is **moving**
toward the trigger, the movement is accelerating, and it is driven by the
concentration D3 already flagged. Combined with D4's finding that he
cannot fund his HKD 60m obligation by selling — because selling triggers
the call — this is the strongest single client story available in the
book, and it is currently half-told.

The brief lists it explicitly: *"**Collateral** — trace loan-to-value
across the five snapshots."*

**Cost**: lowest of the four — the columns exist, the module exists.
**Value**: highest, because it upgrades the weakest of the three demo
clients.

---

## R3 — D9 Tax: the interesting answer is "don't"

The brief asks for *"unrealised gains and losses together within a
household, and at **tax domicile rather than residence**"*.

Both are in the data. **Seven of twenty clients have a tax domicile that
differs from their country of residence:**

```
CL-0001  domicile Indonesia       resident Singapore
CL-0003  domicile Germany         resident Singapore
CL-0007  domicile United Kingdom  resident Singapore
CL-0009  domicile Sweden          resident Singapore
```

Unrealised positions for the three demo clients:

```
         domicile        gains          losses        no cost basis
CL-0003  Germany     +2,621,596       -226,000            1
CL-0014  Hong Kong  +12,500,000   -62,614,640            0
CL-0019  UAE         +6,862,240      -519,000            0
```

**CL-0014 is why this detector must be built with judgement or not at
all.** He is sitting on **HKD-equivalent 62.6m of unrealised losses**. A
naive tax-optimisation engine would shout *harvest them*. But his
domicile is **Hong Kong**, which does not levy capital gains tax — so
harvesting is close to worthless to him, and the advice would be
confidently wrong in front of a client who knows his own tax position
better than the system does.

The correct output for him is a **negative finding**: large harvestable
losses, and a domicile that makes harvesting them pointless. Saying so is
a stronger signal of understanding than any optimisation.

**CL-0003 is the positive case, and it compounds two existing findings.**
Domicile Germany, resident Singapore, with a **German inheritance tax
instalment of EUR 3.4m due before year end**. She holds +2.62m of gains
against only -0.23m of losses, so meeting the bill means realising
German-taxable gains — and the one position that could offset is
`SYN-ST-0107`, which **carries no cost basis at all**, so its tax
consequence cannot be stated from this data.

That is three findings meeting: the inherited breach (D2), the liquidity
constraint (D4), and now the tax position — all pointing at the same
sale, and one of them unanswerable because of a transfer-in defect spec
000 recorded on day one.

**Decision**: build it as a **domicile-aware** detector that reports the
position and names what it cannot compute, never as an optimiser. No
suggested trades — Principle IX, and the brief's own *"support human
decision-making rather than replace it"*.

**Cost**: medium — new logic, but no new data plumbing.
**Value**: high on understanding, and it strengthens CL-0003.

---

## R4 — D10 Life events: real, and mostly already covered

The brief: *"objectives and cash needs describe futures the current
allocations were not built for."*

```
         life_stage                        horizon  liquidity_needs
CL-0003  Recently inherited - transition      15y   Medium
CL-0014  Peak earning years                   12y   High
CL-0019  Peak earning years                   25y   Low
```

The sharpest available finding is a **contradiction inside the client
profile itself**: CL-0019's recorded `liquidity_needs` is **Low** and his
horizon is 25 years — but note **N-026** records a Singapore family
office planned for **2027, needing about USD 5m of seed capital**. The
profile says he needs no liquidity; his own words say he needs USD 5m
within eighteen months.

That is the same *said-versus-recorded* shape as D1, applied to the risk
profile rather than the portfolio — and it is the kind of thing that
matters because the profile is what drives suitability checks.

**But D4 already surfaces the USD 5m need**, and it already reports that
cash plus fixed income covers it 1.49 times. So D10's marginal
contribution is the *profile contradiction*, not the cash need — a
smaller finding than the other three, and the one with the most overlap.

**Decision**: specified, lowest priority. If the freeze arrives first it
is roadmap, and the honest reason is that D4 already carries most of its
value.

---

## Priority, derived from the above

| | Detector | Cost | Value | Order |
|---|---|---|---|---|
| **D8** | Collateral trajectory | lowest | highest — upgrades the weakest demo client | **1** |
| **D7** | Explanation / attribution | low — machinery exists | high — Building Block 1, listed first | **2** |
| **D9** | Tax, domicile-aware | medium | high on understanding; compounds CL-0003 | **3** |
| **D10** | Life events | medium | lowest — D4 covers most of it | **4** |

## Resolved

All four are supported by the data and each has a real finding. Two
carry a genuine risk of being confidently wrong if built carelessly:

- **D7** would credit the market with USD 3.84m the client paid in.
- **D9** would tell a Hong Kong domiciliary to harvest capital losses.

Both are recorded here so the implementation cannot make the mistake
quietly, and both are the kind of error that *flatters* the output — which
is the class the brief warns about most.
