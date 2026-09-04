# Phase 0 Research — Look-Through Concentration (spec 001)

**Date**: 2026-09-04 · **Spec**: [spec.md](./spec.md) · **Plan**: [plan.md](./plan.md)

Seven questions, all resolved against `data/`. Each is recorded with the
query that resolved it.

**Headline: every quoted figure reproduced.** All seven items in the
spec's verification-status table are now verified. But two of them
reproduce only under a **different design than block 3 describes**, and
one Success Criterion in the spec was wrong. Both are corrected below.

---

## Summary of verification

| Figure | Recorded | Reproduced | Status |
|---|---|---|---|
| CL-0019 look-through | 42.13% | **42.1343** | ✅ exact |
| CL-0019 trajectory | 29.41 / 29.50 / 34.08 / 41.07 / 42.13 | 29.4060 / 29.5030 / 34.0834 / 41.0691 / 42.1343 | ✅ all within ±0.01 |
| CL-0019 bands | Eq 57.97, FI 15.67, SP 12.90, Cash 7.45, Alt 6.00 | identical to 2dp | ✅ exact |
| CL-0019 largest position | 13.30% vs limit 15 | 13.30 vs 15.0 | ✅ exact |
| CL-0019 `compliance_clean` | True | **True** — all five bands in range | ✅ |
| CL-0014 Golden Harbour | 29.46% = 12.87 + 9.54 + 7.05 | **29.4527** = 12.87 + 9.54 + 7.05 | ✅ within ±0.01 |
| CL-0014 three asset classes | three | Fixed Income, Equity, Structured Products | ✅ |
| Duplicate underlying | SYN-ST-0104, SYN-EQ-0008 | exactly those two | ✅ |

Nothing had to be reported as unsupported. The data backs every number in
`.alamazing/findings.md` that this spec asserts.

---

## R1 — Does the reference parse to names that match his holdings?

**This was the riskiest assumption in the spec. It holds.**

**Decision**: Parse by discarding the prefix before the colon, splitting on
`/`, stripping whitespace. Match by taking the **first two words** of each
parsed name, lowercased, as a substring test against `instrument_name`.

**Rationale**: The concern was the `ADR` suffix. `instruments.csv` reads:

```
'Worst-of basket: Pacific Orient Shipping / Global Energy Majors ADR / Bara Nusantara Energy'
```

He holds *Global Energy Majors Equity **Fund***, not an ADR. A full-string
match fails. The first-two-words rule resolves it:

```
'Pacific Orient Shipping'   -> first2='pacific orient'  -> ['SYN-ST-0104']
'Global Energy Majors ADR'  -> first2='global energy'   -> ['SYN-EQ-0008']
'Bara Nusantara Energy'     -> first2='bara nusantara'  -> []
```

Exactly the two instruments block 3 requires, and the third correctly
matches nothing — he does not hold Bara Nusantara. **SC-003 holds.**

`.alamazing/implementation.md` step 5 predicted this: "fuzzy is fine,
substring on the first two words works here." It does. Verified rather
than trusted.

**Alternatives considered**:
- *Full-string match.* Rejected — fails on the ADR suffix, which is the
  whole risk.
- *Token-overlap scoring with a threshold.* Rejected: a threshold nobody
  can explain in a compliance review, for a problem two words solve.
- *Match on the instrument's sector instead of its name.* Rejected — it
  would match every energy holding rather than the specific referenced
  name, which is a different finding (and is in fact R5's sector rule).

---

## R2 — Does the trajectory reproduce?

**Decision**: Yes. All five snapshots, all within ±0.01.

```
2025-12-31   got 29.4060   recorded 29.41   delta -0.0040   OK
2026-02-27   got 29.5030   recorded 29.50   delta +0.0030   OK
2026-03-31   got 34.0834   recorded 34.08   delta +0.0034   OK
2026-06-30   got 41.0691   recorded 41.07   delta -0.0009   OK
2026-08-26   got 42.1343   recorded 42.13   delta +0.0043   OK
```

**Rationale**: Worth noting *why* the first two figures are the same sum
over a different number of instruments. SYN-SP-0505 settles in June, so at
the first three snapshots the total is three instruments, not four. The
step from 34.08 to 41.07 is the note appearing; the drift from 29.50 to
34.08 is the March energy spike. Two causes, exactly as
`.alamazing/findings.md` states, and both visible in the numbers rather
than asserted.

The spec 000 `diff` outer join is what makes this computable — an inner
join would have dropped the note at the early snapshots and the trajectory
would have been four figures with a hole.

---

## R3 — Do CL-0019's bands reproduce, and is he really clean?

**Decision**: Yes, exactly. `compliance_clean = True` is earned.

```
PF-0023, mandate BALG, single-position limit 15.0

Equity                 57.97   band 40-65   OK
Fixed Income           15.67   band 15-40   OK
Structured Products    12.90   band  0-15   OK
Cash and Equivalents    7.45   band  2-15   OK
Alternatives            6.00   band  0-25   OK

bands defined but not held: ['Commodities']
largest position 13.30 vs limit 15.0
```

Every figure matches `.alamazing/findings.md` § 1 to two decimal places.
**The pitch's strongest line is true**: his portfolio passes every check
the bank runs, and it is 42% one bet.

Two details worth carrying forward:

**He holds one portfolio, not several.** So `compliance_clean` for him is a
single-portfolio verdict. The cross-portfolio case (a client whose
portfolios sit under different mandates) is untested by this client and
must still be handled — CL-0001, CL-0002 and CL-0017 hold several.

**The Commodities band confirms a recorded imperfection.** BALG defines a
Commodities band and he holds no commodities. `.alamazing/findings.md`
§ Data imperfections says explicitly: absence of the row is not a breach.
Confirmed present, and FR-011 is the requirement that handles it. A naive
implementation that iterates the *mandate's* classes rather than the
*client's* would report a Commodities breach at 0% against a minimum — and
would be wrong.

---

## R4 — Does CL-0014's Golden Harbour reproduce?

**Decision**: Yes. 29.4527 against a recorded 29.46, within ±0.01.

```
SYN-FI-0207  12.87%  Fixed Income          Golden Harbour Properties 5.25% Perpetual
SYN-ST-0106   9.54%  Equity                Golden Harbour Properties Ltd
SYN-SP-0503   7.05%  Structured Products   Accumulator ref. Golden Harbour Properties Ltd, 12M
                     ---------------------
             29.4527  three different asset classes
```

Each individual weight matches to two decimals. The three booked asset
classes are genuinely different, which is the point: **no asset-class
concentration check sees this exposure**, because it is a third of a bond
limit, a third of an equity limit and a third of a structured-product
limit.

---

## R5 — How is a theme derived, without naming one in code?

**This is the design question, and the answer is not what block 3
describes.**

**Decision**: **Two theme rules, both emitted.** They answer different
questions and each reproduces a different recorded figure.

| Rule | Question it answers | Membership | CL-0019 | CL-0014 |
|---|---|---|---|---|
| **sector** | "What is he actually exposed to, once you look through the note?" | the referenced names' **sectors**, then every holding in those sectors, plus the product | **42.13%** ✅ | 49.03% |
| **issuer** | "How many ways does he own the same company?" | the **specific holdings** the names match, plus the product | 33.25% | **29.45%** ✅ |

**Rationale**: Block 3 says "group by resolved theme, flag any theme above
25%", implying one mechanism. Neither single mechanism produces both
recorded figures:

- **Sector-only** gives CL-0019 its 42.13% but gives CL-0014 **49.03%** —
  because Real Estate also contains the Mid-Levels apartment. Not 29.46.
- **Issuer-only** gives CL-0014 its 29.45% but gives CL-0019 **33.25%** —
  it misses the Asia Pacific Shipping fund at 8.88%, which the note does
  not reference and which is linked only by sharing Pacific Orient's
  `Industrials` sector. Not 42.13.

So the two recorded findings in `.alamazing/findings.md` are, on
inspection, **findings of two different kinds** — and the document
describes them that way without saying so:

> CL-0019 — "Stated objective vs look-through exposure"
> CL-0014 — "One name held three ways + liquidity"

The first is thematic. The second is single-issuer. Both are concentration
invisible to existing controls, for different reasons. Emitting both rules
is not hedging; it is what the data supports, and it makes the detector
answer both questions for every client rather than fitting each client to
its own rule.

The R5 candidate approaches in [plan.md](./plan.md) are resolved as
follows: **approach 1 (sector) and approach 2 (co-reference) are both
correct, for different findings.** Approach 3 (caller-supplied grouping)
stays rejected as grep-gaming.

**No theme name is written in code.** A sector theme is labelled by joining
its sector names as they appear in the data — the hero's is
`Energy + Industrials`. An issuer theme is labelled by the matched name as
parsed from the reference — `Golden Harbour Properties Ltd`. Both derive
entirely from the files (FR-020).

**Alternatives considered**:
- *Pick one rule and accept one figure.* Rejected: both figures are
  recorded, and `test_lookthrough_cl0014` is a named required assertion in
  Article VIII. Dropping it is not available.
- *Special-case by client.* Rejected outright — Principle XI, and it would
  make the detector a lookup table.
- *Sector rule with the apartment excluded by liquidity tier.* Rejected as
  reverse-engineering the answer: there is no principled reason a direct
  property holding is outside a Real Estate theme. It *is* Real Estate
  exposure, which is why 49.03% is a true statement about CL-0014 and
  worth emitting alongside the 29.45%.

---

## R6 — Which instruments carry a reference, and do they all parse?

**Decision**: Nine instruments carry one, in **three different shapes**.
The parser must read `instrument_name` as well as `underlying_reference`.

```
SYN-SP-0501  'Worst-of basket: Global Energy Majors ADR / Gulf Marine Services / Helios Cloud Systems'
SYN-SP-0502  'Single underlying: Helios Cloud Systems Inc'
SYN-SP-0505  'Worst-of basket: Pacific Orient Shipping / Global Energy Majors ADR / Bara Nusantara Energy'
SYN-SP-0506  'Worst-of basket: three Asian banking majors, autocall observation quarterly'
SYN-SP-0503  'Daily accumulation at strike HKD 17.20, knock-out HKD 19.80, double-up below strike'
SYN-SP-0504  'Underlying: XAU spot, 100% capital protection at maturity, 70% participation'
SYN-CM-0401  'XAU spot, allocated, Singapore vault'
SYN-CM-0402  'XAU spot'
SYN-AL-0308  'Series D preference shares, last priced round Sep-2025'
```

**This is the second finding that changes the design.** Block 3 says "rows
with a non-null `underlying_reference` resolve to the names in that
reference". For **SYN-SP-0503 — CL-0014's accumulator — there is no name in
the reference at all.** It carries strike, knock-out and double-up
mechanics. The issuer appears only in the `instrument_name`:

```
name: 'Accumulator ref. Golden Harbour Properties Ltd, 12M'
ref : 'Daily accumulation at strike HKD 17.20, knock-out HKD 19.80, double-up below strike'
```

A parser reading only `underlying_reference` **cannot find Golden
Harbour**, and `test_lookthrough_cl0014` — a named required assertion —
fails. So the parser must take names from two places:

1. `underlying_reference`, after the colon, split on `/`.
2. `instrument_name`, after the marker `ref.`, up to the first comma.

Three shapes, handled:

| Shape | Example | Names recoverable |
|---|---|---|
| Named basket | SYN-SP-0501/0505 | ✅ from the reference |
| Named single underlying | SYN-SP-0502, SYN-SP-0503 | ✅ from `ref.` in the name |
| Unnamed / descriptive | SYN-SP-0506 "three Asian banking majors", SYN-CM-0401 "XAU spot", SYN-AL-0308 "Series D preference shares" | ❌ none — falls back to sector, recorded in `unsure_about` |

**SYN-SP-0506 is the honest case.** "Three Asian banking majors" names no
issuer, so the look-through genuinely cannot resolve it. CL-0003 holds it
at 5.39%, well under any threshold, so nothing is lost — but the parser
must degrade rather than throw, and must say what it could not resolve
(FR-016). This is the parse-failure edge case in the spec, and it is
exercised by real data rather than hypothetical.

**One known parse artifact**, recorded rather than fixed: the `ref.`
extraction on SYN-SP-0505 yields `'Basket C'` from *"Fixed Coupon Note ref.
Basket C, 9.20% p.a., 12M"* — a basket label, not an issuer. It matches no
holding and is therefore harmless. Suppressing it would require knowing
that "Basket C" is a label and "Golden Harbour Properties Ltd" is a
company, which is exactly the kind of judgement this layer must not make.
It stays, it matches nothing, and it is recorded in `unsure_about`.

---

## R7 — Do themes double-count, and how discriminating is the detector?

**Decision**: No double-counting. The detector is selective. **But one
Success Criterion in the spec is wrong and is corrected here.**

Swept all 20 clients × all 5 snapshots — 50 themes computed:

```
themes computed: 50
no double-count (every theme's row count == its distinct instrument count)
no theme over 100%
max theme weight: 88.585
```

**SC-006 as written in the spec is incorrect.** It requires theme totals to
"account for 100% ± 0.001 of client-level value". That would only hold if
themes **partitioned** the book. They do not — the two rules overlap by
design, and a holding can belong to a sector theme and an issuer theme at
once. Summing them would exceed 100% and *should*.

**The correct invariant, and what is now asserted:**

1. No instrument appears twice **within** a single theme.
2. No single theme exceeds 100% of client value.

That catches the actual failure mode — a structured product contributing
its weight once per referenced name, which would inflate the hero's figure
past 42% plausibly. It is the same class of error as spec 000's
`weight_pct` trap, and it is caught the same way: swept across every
client and every date, not sampled.

### Discrimination

Only **8 of 20 clients hold a structured product at all**, so the
look-through is silent for the other twelve — correctly. At a 25%
threshold:

```
client    product        sector%  issuer%  sectors
CL-0001   SYN-SP-0505      44.99    44.99  ['Energy']
CL-0002   SYN-SP-0502      88.56     7.80  ['Information Technology']
CL-0003   SYN-SP-0506       5.39     5.39  []
CL-0007   SYN-SP-0504      24.04    24.04  ['Gold']
CL-0013   SYN-SP-0502      57.06    22.49  ['Information Technology']
CL-0014   SYN-SP-0503      49.03    29.45  ['Real Estate']
CL-0015   SYN-SP-0501      12.84    12.84  []
CL-0019   SYN-SP-0505      42.13    33.25  ['Energy', 'Industrials']

sector-theme  > 25%: 5 of 8
issuer-theme  > 25% with >= 2 matched holdings: 2 of 8
```

Five and two out of eight. Selective enough to mean something, broad
enough not to be fitted to one client. CL-0007 at 24.04% sits just under
the threshold, which is a useful demonstration that 25% is a real boundary
and not a number chosen to make three clients light up.

**Two incidental confirmations worth having:**

**CL-0001 holds the same note.** SYN-SP-0505 appears in his book at 6.18%
alongside a 44.99% Energy sector theme. `.alamazing/findings.md` § Reserve
describes exactly this client — *"told Priscilla in January that the JB
relationship is the wealth **not** tied to the family coal mine; in April
subscribed a shipping and energy FCN"*. The detector finds the reserve
client unprompted, which is the strongest available evidence that it
generalises rather than being fitted to CL-0019.

**CL-0002's 88.56% is real but blunt.** SYN-SP-0502 references Helios
Cloud Systems, an Information Technology name, and he is 88% Information
Technology. True, and closer to "you are 88% tech" than to a look-through
insight. It is emitted because it is true; whether it is *interesting* is
Priscilla's call, not the detector's (Principle IX).

---

## Resolved

All seven questions closed. Two corrections carried into the spec:

1. **The parser must read `instrument_name` as well as
   `underlying_reference`** (R6). Without it, CL-0014's accumulator is
   invisible and a required assertion fails. Block 3's description is
   incomplete on this point.
2. **SC-006 is replaced** (R7). Themes overlap by design and do not sum to
   100%. The invariant is no double-count within a theme, and no theme over
   100%.

One design decision taken: **two theme rules, both emitted** (R5), because
each reproduces one of the two recorded figures and neither alone
reproduces both.

No figure had to be reported as unsupported by the data.
