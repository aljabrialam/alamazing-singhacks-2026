# Phase 0 Research — Liquidity and the Unanswered Question (spec 004)

**Date**: 2026-09-04 · Run before the spec was written.

Six questions. One found that **block 6's acceptance narrative
contradicts block 6's own liquidity definition**, and one found a
constraint on CL-0014 that `findings.md` does not mention and which
changes his finding materially.

---

## R1 — The needs are not in USD. FX conventions differ by series.

`planned_cash_needs` carries a `currency` column, and both demo needs are
foreign:

```
CN-004  CL-0003  EUR 3,400,000   2026-10-01 .. 2026-12-31  Confirmed
CN-013  CL-0014  HKD 60,000,000  2026-11-01 .. 2027-06-30  Confirmed
```

Holdings are compared in `market_value_usd`, so both need converting.
`market_context.csv` carries the rates — and **the two use opposite
conventions**, stated in the `unit` column, not inferable from the series
id:

```
EURUSD   1.092   unit = "USD per EUR"   ->  multiply
USDHKD   7.810   unit = "HKD per USD"   ->  divide
```

**Decision**: read the `unit` string and choose the operation from it.
Guessing from the series name is the trap: treating `USDHKD` as "USD per
HKD" turns HKD 60m into **USD 468.6m** instead of USD 7.68m — a 61×
error, and one that would make the finding look catastrophic rather than
merely serious.

Converted:

```
EUR 3,400,000  x 1.092  =  USD 3,712,800
HKD 60,000,000 / 7.810  =  USD 7,682,458
```

---

## R2 — Block 6's "tight" figure uses a different definition than block 6's rule

**Block 6 instructs**: *"Liquid = liquidity_tier in (Daily, Weekly)."*

**Block 6 then asserts**: *"CL-0003: EUR 3.4m ... against cash 7.69% +
fixed income 9.15% = 16.8% liquid ... Tight."*

Those are two different definitions and they give very different answers:

| Definition | CL-0003 |
|---|---|
| `liquidity_tier in (Daily, Weekly)` — as instructed | **88.29%** |
| cash + fixed income — as asserted | **16.83%** |

The gap is her equity. **All 71.46% of her equity is `Daily`** — they are
daily-dealing funds, genuinely sellable tomorrow. So by the rule block 6
gives, her liquidity is not tight at all: the need is 16.74% of the
portfolio and liquid assets cover it **5.27 times over**.

**Decision**: compute the tier-based figure, because it is the correct
answer to "can this be funded by the date required", and report the
asset-class figure **alongside** it, because it answers a different and
more important question.

**The important question is not whether she can pay. It is what paying
costs her.** Cash plus fixed income is 16.83% of the portfolio; the bill
is 16.74%. Those are the same number. So meeting the tax instalment
consumes **essentially all of her non-equity holdings**, or it comes out
of equity.

`findings.md` § 2 says exactly this in prose — *"Meeting the tax bill
means selling equity she never chose, in a portfolio she does not
understand"* — and block 6 compressed it into the word "Tight", which is
the one reading the data does not support. The prose was right; the
one-line acceptance criterion was not.

So the finding is not a liquidity warning. It is: *she can pay this
comfortably, and paying it means selling the equity she never chose,
in the portfolio she has twice said she does not understand.* That is
worse than tight, and it is true.

---

## R3 — CL-0014 cannot fund his need by selling. The facility blocks it.

**`findings.md` does not mention this, and it is the strongest finding in
the spec.**

Block 6 says *"subtract anything pledged in credit_facilities"*. For
CL-0014 that instruction turns out to govern the whole answer.

```
CF-0002   collateral portfolio PF-0016 — his ONLY portfolio
          drawn                HKD  58,000,000  of a 70,000,000 limit
          utilisation          82.86%
          collateral value     HKD 206,878,860
          lending value        HKD  83,565,930
          LTV                  69.41%
          margin call at       70.00%
          -> 0.59 percentage points of headroom
```

He is **0.59pp from a margin call today**, and the collateral is the same
portfolio that is 29.45% one issuer, down 41–47%.

Now apply the need. He requires HKD 60m by mid-2027. If he sells HKD 60m
of that collateral to fund it, at the implied 40.4% advance rate:

```
lending value   HKD 83,565,930  ->  HKD 59,329,738
LTV on 58m drawn        69.41%  ->  97.76%     against a 70% trigger
```

**Selling to meet the need triggers the margin call the sale was meant to
avoid.** A naive liquidity check says he has 73.38% liquid against a
29.00% need and is comfortable — 2.53× coverage. He is not comfortable.
Almost none of that liquidity is *free*, because it is collateral against
a facility with 0.59pp of headroom.

`findings.md` § 3 records only that *"Priscilla reviewed what is sellable
and recorded that he was surprised how little of it is liquid."* The
facility explains **why** — and makes his position considerably more
urgent than recorded.

**Decision**: the runway detector must net off pledged collateral and
report LTV headroom, both today and after the need is met. A coverage
ratio computed without the facility is the kind of confidently wrong
number this project exists not to produce.

---

## R4 — Liquidity tiers, measured

```
CL-0003   Daily 88.29%   Monthly 6.32%   Illiquid 5.39%
CL-0014   Daily 42.95%   Weekly 30.43%   Illiquid 26.62%
```

CL-0014's illiquid 26.62% is the Mid-Levels apartment (19.58%) plus the
accumulator (7.05%) — matching `findings.md` § 3 exactly. His 30.43%
`Weekly` is the two perpetuals, which counts as liquid under block 6's
rule but is worth naming separately in a brief: a week is fine for a
2027 need and would not be for a margin call.

**Block 6's "Monthly does not count"** is honoured. It excludes CL-0003's
6.32% alternatives, which is correct for a near-dated need.

---

## R5 — The unanswered-question matcher needs two guards, not one

Block 6 gives question markers and RM admissions. Run naively, both
misfire.

**Guard 1 — a question asked and answered in the same note is not
unanswered.**

```
N-002  CL-0001  "Asked what products give him more of that.
                 Discussed the shipping and energy FCN"          answered
N-006  CL-0003  "asked whether she should be worried ...
                 Sent a short note."                             answered
```

Both match "asked what" / "asked whether". Both were answered in the same
sentence. Emitting them would put "unanswered question" in front of
Priscilla for two questions she demonstrably answered — which destroys
trust in the one that is real.

**Guard 2 — "Unresolved" as a bare word catches market commentary.**

```
N-025  "charter rates stay elevated while the Strait situation
        is unresolved"                                    NOT a question
```

That is a description of the world, not an open item. Matching it would
attach a spurious unanswered-question flag to the hero client's *other*
note.

**Decision**: RM admissions must be **first-person about the bank's own
action** — `we have not modelled/analysed/looked/run`, `have not yet
replied/responded/come back` — or a standalone `Unresolved.` sentence.
Question markers additionally require that no answer marker (`sent a`,
`discussed`, `explained`, `replied`, `walked through`, `showed`) appears.

An admission **overrides** the answer check, because `"Have not yet
replied"` contains the word "replied" and would otherwise cancel itself.

Result across all 20 clients — 3 open questions:

```
N-026  CL-0019  asked for a view + we have not modelled    *** required
N-028  CL-0004  asked whether   + have not yet replied     *** required
N-023  CL-0017  standalone "Unresolved."
```

Both required notes are found, and both answered-in-note cases are
correctly excluded.

**Recorded false negative** (Principle X): `N-011` CL-0007 reads *"Long-held
UK tax questions remain unresolved"*. That **is** an open item, and this
matcher misses it, because `remain unresolved` is neither a first-person
admission nor a standalone sentence. Broadening the rule to catch it
re-admits N-025. The rule errs toward precision, and the miss is stated
rather than hidden — three real open questions surfaced, one real one
missed, zero false positives.

---

## R6 — The Finding schema blocks this spec

Flagged in spec 001 and now blocking, as predicted.

`specs/001-divergence-engine/contracts/finding.schema.json` declares:

```json
"kind": { "enum": ["D1", "D2", "D3", "D4"] }
```

But `.alamazing/implementation.md` and `RUN-SHEET.md` both specify **D5**
(unanswered question) and **D6** (scenario). This spec emits D4 and D5;
spec 005 emits D6.

**Decision**: extend the enum to `D1..D6` and document each. This is the
obvious fix and the decision belonged to whichever spec first needed it,
which is this one. The `unanswered_question` object the schema already
defines is D5's payload, so the schema clearly anticipated D5 and only the
enum was left behind.

---

## Resolved

Six questions. Recorded corrections: block 6's own acceptance narrative
uses a definition its rule contradicts (R2), the FX convention differs by
series and is only knowable from the `unit` column (R1), the matcher needs
two guards rather than none (R5), and the committed schema needs
extending (R6).

One new finding of substance: **CL-0014 cannot fund his need by selling**
(R3). Verified from the facility rows, not inferred.
