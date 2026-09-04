# Phase 0 Research — Mandate Classification (spec 003)

**Date**: 2026-09-04 · Run before the spec was written.

Five questions. Two of them found errors in the reference documents, and
one found **a live defect in spec 001** that this spec must fix.

---

## R1 — What are the transaction column and values actually called?

**Both reference documents are wrong.** Block 5 and
`.alamazing/implementation.md` step 7 both specify:

```python
trades = transactions[(transactions.client_id == cid)
                    & (transactions.type.isin(['BUY','SUBSCRIPTION']))]
```

Neither the column nor the values exist.

| Reference says | Data actually has |
|---|---|
| `transactions.type` | `transaction_type` |
| `'BUY'` | `'Buy'` |
| `'SUBSCRIPTION'` | `'Structured Product Subscription'` |

Full value set: `Buy`, `Capital Call`, `Coupon`, `Distribution`,
`Dividend`, `Facility Drawdown`, `Interest`, `Interest Charge`,
`Management Fee`, `Redemption Request`, `Structured Product Subscription`,
`Transfer In`, `Valuation Update`, `Withdrawal`.

**Why this matters more than a typo.** Written as specified, the filter
raises `AttributeError` — which is the *good* outcome. Written as
`transaction_type.isin(['BUY','SUBSCRIPTION'])`, it silently matches
**nothing**, every client has "no trades", and **every breach in the book
classifies as `inherited`**. The demo would show Margarethe's finding
looking exactly right, for entirely the wrong reason, and the bug would be
invisible.

**Decision**: acquisition types are `('Buy', 'Structured Product
Subscription')`, defined as a module constant so the set is stated in one
place and asserted by a test that fails if the data ever stops containing
them.

---

## R2 — Do the classification inputs give the recorded answers?

**Yes, all three.**

```
CL-0003  PF-0005  inception 2026-02-16  acquisitions: 0
         transactions: Dividend 6, Interest 4, Coupon 2,
                       Management Fee 2, Transfer In 1
         -> inception in 2026 AND no acquisitions      -> inherited  ✅

CL-0014  PF-0016  inception 2011-04-01  acquisitions: 1
         the one acquisition is a Structured Product Subscription
         (the accumulator). The breached class is EQUITY.
         -> no acquisition into the breached class      -> drift      ✅

CL-0019  PF-0023  inception 2014-02-01
         -> no breach at all                           -> clean      ✅
```

`PF-0005` is the **only** 2026 inception in the book, and its
`portfolio_name` is literally *"Inherited Portfolio - Under Review"*. The
dataset's authors put the answer in the name; the classification derives
it from inception date and transaction history instead, because a name is
not evidence.

**CL-0014 proves the rule has to be "into the breached class", not "any
acquisition".** He *did* subscribe to something in January 2026. If the
test were "any BUY or SUBSCRIPTION exists", he would classify
`client_directed` — and block 5 says he must be `drift`. The acquisition
was into Structured Products; the breach is in Equity. Different class,
so it is not evidence of client direction.

---

## R3 — Can a purchase ever explain a *below-minimum* breach?

**No. Block 5's classification rule is incomplete, and this is a logic
error rather than a typo.**

Block 5 says:

> `client_directed` — transactions show BUY or SUBSCRIPTION into the
> breached asset class

That is only coherent for an **above-maximum** breach. For a
**below-minimum** breach, buying *into* the class moves it back toward
the band — it is evidence *against* client direction, not for it. What
would explain a below-min breach is a **disposal out of** the class.

**Decision**: the direction of the breach selects the direction of the
evidence.

| Breach | `client_directed` requires |
|---|---|
| `above_max` | an acquisition **into** that class — `Buy`, `Structured Product Subscription` |
| `below_min` | a disposal **out of** that class — `Redemption Request`, `Withdrawal` |

**Consequence on this data**: there are 4 `Withdrawal` and 2
`Redemption Request` rows in the whole book and no `Sell` type at all, so
below-min breaches will nearly always classify as `drift` — which is
exactly the answer block 5 requires for CL-0014, reached by correct
reasoning rather than by coincidence.

CL-0014's is also the more interesting reading: his equity fell below the
floor **because his equity fell**, not because he sold. `findings.md` § 3
says so — *"breached on the low side, not because he sold but because his
equity fell. Drift, and in the direction that makes the exposure look
smaller than it is."*

---

## R4 — Three portfolios are **custody accounts**, and bands do not apply

**This is the significant find, and it is a live defect in spec 001.**

`portfolios.csv` carries a `service_model` column with three values:
`Advisory`, `Discretionary`, `Custody`. Every portfolio also carries a
`mandate_code` — **including the custody accounts**. Applying strategic
asset allocation bands to a custody account is a category error: the bank
holds the assets, the client directs them, and nobody is managing them to
a band.

Doing it anyway produces three false breaches:

```
CL-0001  PF-0002  "Legacy Holdings Custody Account"  Equity       97.97%  above_max
CL-0002  PF-0004  "Founder Shareholding Custody"     Alternatives 100.00% above_max
CL-0017  PF-0021  "Next Generation Account"          Cash          15.89% above_max
```

Look at what those actually are. PF-0002 holds **one legacy stock** at
97.97%. PF-0004 holds **one unlisted founder shareholding** at 100% — the
client's own company. Telling a founder that their portfolio "breaches its
equity limit" when the position *is* the company they founded is not a
finding; it is the system failing to understand what it is looking at.
That is precisely the confident-fabrication failure the brief warns
against.

**Decision**: band checks and single-position limits apply to `Advisory`
and `Discretionary` portfolios only. Custody portfolios are **excluded
from the comparison and reported separately** as held-not-managed, with
their value, so nothing disappears — the relationship manager can still
see them, they are simply not measured against a band they were never
managed to.

**This is a regression fix, not a new feature.** Spec 001's
`compliance_clean` currently reads the custody breaches as real.

**My first prediction here was wrong and is corrected below.** I wrote
that CL-0001 and CL-0002 would both flip to clean once custody was
excluded. Implementing it, both stayed `False` — because each also had
*single-position* breaches in its managed portfolio. Chasing that turned
up R6, a second and larger defect. The final position, after both fixes:

| Client | before | after | why |
|---|---|---|---|
| CL-0001 | `False` | **`True`** | custody breach excluded, and its two remaining position breaches were diversified funds the limit does not apply to (R6) |
| CL-0002 | `False` | `False` | Meridian Semiconductor, a single stock, is genuinely at 15.18% against a 15% limit |
| CL-0017 | `False` | `False` | real breaches remain: PF-0019 Equity 56.21, and two private-market funds over a 25% limit |

Recorded rather than tidied, because the prediction was in the file before
the implementation contradicted it.

**The three demo clients are unaffected** — CL-0019 PF-0023, CL-0003
PF-0005 and CL-0014 PF-0016 are all `Advisory`. So 42.1343%,
`compliance_clean = True`, 71.46% and 23.39% all stand exactly as
recorded. The hero finding does not move.

Verified before touching code, which is why it is a two-line change in
`mandate.py` rather than an hour at 15:00.

---

## R5 — Which breaches exist in the whole book?

Fourteen real breaches across ten clients, after excluding custody:

```
CL-0003  PF-0005  Advisory        Equity                71.46  above_max
CL-0003  PF-0005  Advisory        Fixed Income           9.15  below_min
CL-0005  PF-0007  Discretionary   Equity                67.74  above_max
CL-0007  PF-0009  Discretionary   Commodities           18.93  above_max
CL-0009  PF-0011  Advisory        Cash and Equivalents  44.98  above_max
CL-0009  PF-0011  Advisory        Fixed Income          14.45  below_min
CL-0011  PF-0013  Advisory        Alternatives          47.28  above_max
CL-0011  PF-0013  Advisory        Fixed Income          24.47  below_min
CL-0014  PF-0016  Advisory        Equity                23.39  below_min
CL-0016  PF-0018  Advisory        Equity                67.72  above_max
CL-0016  PF-0018  Advisory        Fixed Income          21.83  below_min
CL-0017  PF-0019  Discretionary   Equity                56.21  above_max
CL-0018  PF-0022  Advisory        Commodities           14.04  above_max
CL-0018  PF-0022  Advisory        Fixed Income          22.98  below_min
```

Ten of twenty clients breach something; ten do not. **CL-0019 is in the
second group**, which is the whole argument: his portfolio is the one that
passes every check and is still 42% one bet.

Note CL-0009 at 44.98% cash against a 25% ceiling — "Post-Sale Deployment
Portfolio", so he has just sold a business and the cash is undeployed.
Real breach, benign cause, and a good illustration that the
classification matters more than the flag.

---

## Resolved

Five questions closed. Two errors found in the reference documents (R1's
column and value names, R3's one-directional rule), and one live defect in
already-shipped code (R4). All three recorded rather than quietly
corrected, per Principle X.

The three recorded acceptance figures reproduce unchanged.


---

## R6 — The single-position limit is applied to instruments it exempts

**Found while checking why R4's prediction failed. Larger than R4.**

`instruments.csv` carries a `concentration_limit_applies` column — 26 `Y`,
36 `N` — which decides whether a single-position limit means anything for
that instrument:

| Flag | Instruments |
|---|---|
| **Y** | single stocks, single-name perpetuals, direct property, unlisted holdings, structured products — one name, one credit, one building |
| **N** | diversified funds — index funds, sector funds, regional funds |

**Spec 001 ignored the flag and applied the limit to everything.** Spec
000 deliberately merged the column onto every holdings row; spec 001 then
never read it.

A diversified index fund at 26% of a portfolio is an asset-allocation
question, not a concentration risk. Applying a single-name limit to it
produces false breaches on precisely the instruments that exist to spread
risk — and worse, it **buries the real ones**:

```
CL-0001  PF-0001  SYN-EQ-0001  26.56%  N  Global Developed Equity Index Fund  <- reported, false
         PF-0001  SYN-FI-0204  15.72%  N  Asia Investment Grade Credit Fund   <- reported, false

CL-0002  PF-0003  SYN-EQ-0003  24.04%  N  US Technology Leaders Fund          <- reported, false
         PF-0003  SYN-ST-0102  15.18%  Y  Meridian Semiconductor Corp         <- REAL, listed second
```

CL-0002's genuine single-stock breach was sitting *below* a false one in
the same list. That is the failure mode worth caring about: not a wrong
number, but a real finding made invisible by noise around it.

**Decision**: `breached` requires `concentration_limit_applies == 'Y'`. A
position over the limit that the limit does not apply to is reported as
`over_limit_but_exempt` — the size stays visible, it is simply not a
violation. Nothing is hidden; it is reclassified.

### What this changes for the demo clients

**CL-0019 — nothing.** Largest position 13.30%, still under the limit
either way, `compliance_clean` still `True`. The hero finding does not
move, and all 45 tests stayed green through both fixes.

**CL-0003 — the recorded "26.06% single position" is exempt.** Block 5
and `findings.md` § 2 both cite it as her largest single position, which
it is: Global Luxury and Consumer Brands Fund. But it is a **diversified
fund**, so it is not a concentration breach. Her real one is:

```
SYN-ST-0107  Nordvind Industrial AB  18.37%  vs a 10% limit   Y
```

**That is the holding with no cost basis** — the one spec 000 recorded as
an imperfection because nothing came across in the transfer. So the
position that breaches her concentration limit is the same position nobody
can price for tax purposes, and selling it is one of her options for the
EUR 3.4m instalment. `findings.md` states both facts in separate
paragraphs; the system now joins them.

The spec reports the 26.06% figure as her largest position (matching the
record) **and** Nordvind as the actual breach. Both are true and they say
different things.

**CL-0014 — three real position breaches appear**, none of which
`findings.md` mentions: the Mid-Levels apartment at 19.58%, the Pacific Rim
Bank perpetual at 17.57%, and the Golden Harbour perpetual at 12.87%, all
against a 12% limit. All three are `Y` instruments. His concentration
problem is worse than recorded, and it is worse in a way that supports the
existing finding rather than complicating it.
