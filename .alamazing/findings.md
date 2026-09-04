# Verified Findings

**Feature:** `001-divergence-engine`
Computed from `data/` on 2026-09-04. Every figure below is reproducible
from the supplied files. Snapshot: 2026-08-26 unless stated.

---

## Client selection

Twenty clients read. Three chosen — each demonstrates a *different* kind of
divergence, and each is invisible to a different existing control.

| # | Client | Divergence | Why it escapes today's tools |
|---|---|---|---|
| 1 | Abdullah Al-Mansoori (CL-0019) | Stated objective vs look-through exposure | Passes every mandate check |
| 2 | Margarethe Voss-Brenner (CL-0003) | Mandate breach that is neither drift nor client-directed | Breach monitoring can't classify it |
| 3 | Lau Chi Ming (CL-0014) | One name held three ways + liquidity | Each instrument looks like a different asset class |

---

## 1. Abdullah Al-Mansoori — CL-0019 · **hero client**

**Stated objective** (`clients.csv`): "Build wealth outside the Gulf region
and outside the shipping sector; fund a family office in Asia."

**Source of wealth:** Gulf logistics, port services and marine chartering.

**Mandate:** BALG (Balanced Growth), Advisory. USD 32.2m.

### The exposure

| Instrument | Weight |
|---|---|
| SYN-EQ-0025 Asia Pacific Shipping and Logistics Fund | 8.88% |
| SYN-ST-0104 Pacific Orient Shipping Ltd | 11.41% |
| SYN-EQ-0008 Global Energy Majors Equity Fund | 8.94% |
| SYN-SP-0505 Fixed Coupon Note ref. Basket C | 12.90% |
| **Look-through total** | **42.13%** |

**The structured product is the point.** SYN-SP-0505's
`underlying_reference` is a worst-of basket: *Pacific Orient Shipping /
Global Energy Majors ADR / Bara Nusantara Energy.* Two of the three are
names he already holds outright. It is not diversification — it is a
leveraged short-volatility position on holdings he already owns.

### Trajectory

| Snapshot | Look-through weight |
|---|---|
| 2025-12-31 | 29.41% |
| 2026-02-27 | 29.50% |
| 2026-03-31 | 34.08% |
| 2026-06-30 | 41.07% |
| 2026-08-26 | **42.13%** |

Two causes: appreciation through the March energy spike, then a step change
in June when the FCN settled.

### Why nothing flags it

Every BALG band is respected:

| Asset class | Actual | Band |
|---|---|---|
| Equity | 57.97% | 40–65 |
| Fixed Income | 15.67% | 15–40 |
| Structured Products | 12.90% | 0–15 |
| Cash | 7.45% | 2–15 |
| Alternatives | 6.00% | 0–25 |

No single position exceeds the 15% limit — the largest is 13.30%.

**His portfolio passes every compliance check the bank runs, and it is 42%
one bet.** This is the argument: not a limit breach, so no monitoring
system catches it. It appears only when you look through the structured
product and read what he said he wanted.

### Supporting notes

- **N-025, 2026-04-15** — subscribed the FCN. Priscilla recorded: his
  operating business benefits from the same conditions, and he said the
  point of the Asia portfolio was to be uncorrelated with the Gulf
  business. *It currently is not.*
- **N-026, 2026-08-12** — he asked what happens if the Strait reopens and
  normalises. Priscilla recorded: *"We have not modelled this."*

### Events

- 2026-03-04 — Strait of Hormuz effectively closed, Brent past USD 120
- 2026-08-05 — naval blockade reimposed, energy risk premium re-widens

### The scenario — answering his actual question (D6)

He asked what happens if the Strait reopens and normalises. Brent is
**USD 101.5** today and was **USD 72.4** on 27 February, the day before the
conflict began. Repricing his four positions to their pre-conflict levels:

| Position | Today | Pre-conflict | Impact |
|---|---|---|---|
| Asia Pacific Shipping | 2.86m | 2.43m | −0.43m |
| Pacific Orient Shipping | 3.68m | 2.95m | −0.72m |
| Global Energy Majors | 2.88m | 2.34m | −0.54m |
| FCN Basket C | 4.16m | 3.34m | −0.82m |
| **Total** | | | **−2.5m** |

**Roughly 7.8% of the portfolio**, on a de-escalation — an outcome most
people would call good news.

**The second-order effect is the real answer.** His business is Gulf
logistics, port services and marine chartering. His own note (N-025)
records his view that charter rates stay elevated while the Strait
situation is unresolved. So the same event takes 2.5m from the portfolio
*and* reduces his business earnings, at the same time.

The diversification he asked for in 2014 is precisely what would have
protected him here. He does not have it.

**And the note behaves worst of all.** SYN-SP-0505 is a *worst-of* basket.
On the downside he is exposed to whichever of the three underlyings falls
furthest, not the average — and two of the three are names he already
holds outright.

### The opening line

> "You asked me two weeks ago what happens if the Strait reopens. Around
> 2.5 million comes off the portfolio — and your charter rates fall in the
> same week."

**Why this client wins:** he asked a question, nobody answered it, and the
demo answers it — with a number, grounded in the event log. That is the
whole distance from monitoring to advisory in one exchange.

---

## 2. Margarethe Voss-Brenner — CL-0003

**Mandate:** CONS (Conservative), Advisory. EUR base. USD 22.2m.
Transferred in 2026-02-16 following her husband's death.

### The breach

| Asset class | Actual | Band |
|---|---|---|
| Equity | **71.46%** | 10–30 |
| Fixed Income | **9.15%** | 45–75 |
| Cash | 7.69% | 5–25 |
| Alternatives | 6.32% | 0–15 |
| Structured Products | 5.39% | 0–10 |

Largest single position: Global Luxury and Consumer Brands Fund at
**26.06%**. Second: Nordvind Industrial AB at **18.37%** — her late
husband's industrial holding.

### The classification problem — and a design consequence

The brief asks us to separate **drift** from **client-directed**. This
portfolio is neither. It was transferred in as it stood. Nobody chose this
allocation for her, and she has not traded.

**We add a third classification: `inherited`.** Same breach, a third
conversation — and one that cannot be had the way the other two are had.

### Why it is urgent

- **N-005, 2026-02-16** — she asked that nothing be changed for now, said
  several times she does not understand what is in the portfolio, and
  described herself as someone who has never taken a risk with money.
  Priscilla's own note: *"The portfolio as transferred is not
  conservative."*
- **N-006, 2026-05-29** — she asked whether she should be worried about
  the Middle East and said she would prefer "something safe and boring".
  A German inheritance tax instalment of **EUR 3.4m falls due before year
  end**.

EUR 3.4m against USD 22.2m is roughly 15% of the portfolio, and cash plus
fixed income together are only 16.8%. Meeting the tax bill means selling
equity she never chose, in a portfolio she does not understand.

### The opening line

> "You asked for something safe and boring. Before we get there, we need
> to talk about the tax instalment — because paying it will mean selling,
> and I'd rather we chose what."

---

## 3. Lau Chi Ming — CL-0014

**Mandate:** BAL (Balanced), Advisory. HKD base. USD 26.5m.

### One name, three instruments

| Instrument | Asset class | Weight | Unrealised |
|---|---|---|---|
| SYN-FI-0207 Golden Harbour Properties 5.25% Perpetual | Fixed Income | 12.87% | −41.65% |
| SYN-ST-0106 Golden Harbour Properties Ltd | Equity | 9.54% | −47.39% |
| SYN-SP-0503 Accumulator ref. Golden Harbour Properties | Structured Products | 7.05% | −41.70% |
| **Golden Harbour, combined** | three classes | **29.46%** | — |

Add Direct Property – Mid-Levels Apartment at 19.58% (illiquid) and
Greater China Equity at 13.84%, and his own business is Hong Kong property
development.

**The accumulator compounds it.** Its terms: daily accumulation at strike
HKD 17.20, knock-out at 19.80, **double-up below strike**. It is down
41.7%, which means it is accumulating at twice the rate into a falling
name he already owns two other ways.

### Mandate

Equity is **23.39% against a 30–55 band** — breached on the low side, not
because he sold but because his equity fell. Drift, and in the direction
that makes the exposure look smaller than it is.

### Liquidity

- **N-019, 2026-08-11** — the redevelopment needs an **HKD 60m equity
  contribution by mid-2027**. Priscilla reviewed what is sellable and
  recorded that he was surprised how little of it is liquid.
- Cash is 5.80%. The Mid-Levels apartment (19.58%) and the accumulator
  (7.05%) are Illiquid; both perpetuals are Weekly.

### Supporting note

**N-018, 2026-03-05** — Priscilla told him the perpetual, the shares, the
accumulator and his own development business are all the same bet. He said
that is why he is confident.

### The opening line

> "You told me in March you were confident because it's all the same bet.
> I want to show you what that bet looks like now, and what it means for
> the HKD 60m you need next year."

---

## Reserve

Not in the demo, worth mentioning if asked.

| Client | Divergence |
|---|---|
| Aishah binti Rahman (CL-0005) | Sustainability policy adopted 2024; holds an energy fund she was unaware of, and a legacy palm position she considers separate but which sits inside the same mandate |
| Hartono Wijaya Kusuma (CL-0001) | Told Priscilla in January that the JB relationship is the wealth *not* tied to the family coal mine; in April subscribed a shipping and energy FCN. Needs SGD 9m for a property deposit in early 2027 |
| Cheung Kwok Wing (CL-0012) | The brief's own worked example. Deliberately not used — every team that read the README will demo this client |

**Note on CL-0012.** Avoiding it is a deliberate choice, not an oversight.
Say so if a judge asks.

---

## Data imperfections found

For the uncertainty screen. Handling these thoughtfully counts; assuming
they are absent does not.

- `SYN-ST-0107` Nordvind Industrial AB (CL-0003) has no
  `unrealised_pnl_pct` — no cost basis carried through the transfer-in.
  Its gain or loss is unknown, which matters because selling it is one of
  the options for the tax instalment.
- `mandates.csv` lists a Commodities band for mandates where no client
  holds commodities. Absence of the row is not a breach.
- Private-market valuations lag a quarter by design. Not flagged as error.
