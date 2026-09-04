# Data Model: Divergence Engine

**Feature:** `001-divergence-engine`
**Constitution:** `.specify/memory/constitution.md` v3.0.0

---

## Data model

### 3.1 The joins that matter

```
clients.csv          client_id
  └─ portfolios.csv  portfolio_id, client_id     ← some clients have >1
       └─ holdings.csv   portfolio_id, instrument_id, snapshot_date
            └─ instruments.csv  instrument_id, underlying_reference
       └─ mandates.csv       portfolio_id → allocation bands, limits
       └─ credit_facilities.csv  portfolio_id → LTV history
  └─ commitments.csv        client_id → uncalled capital
  └─ planned_cash_needs.csv client_id → what's needed, when
  └─ rm_notes.json          client_id → Priscilla's prose

event_log.csv     standalone, authoritative for 2026
market_context.csv  same five dates as holdings
```

**Two traps the brief warns about:**

- Some clients hold more than one portfolio. Aggregate at **client** level
  for concentration, not portfolio level. This is D3.
- `instruments.underlying_reference` tells you what a structured product
  is actually exposed to. Asset class only tells you what it's *called*.

### 3.2 The five snapshots

| Date | What it marks |
|---|---|
| 2025-12-31 | Baseline |
| 2026-02-27 | Day before Middle East conflict |
| 2026-03-31 | After Strait of Hormuz closure |
| 2026-06-30 | After June technology drawdown |
| 2026-08-26 | Today |

Comparing snapshots is where the work is. A single snapshot tells you what
a portfolio *is*; the sequence tells you what *happened*.

---
