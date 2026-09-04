# Data Model — Data Layer (spec 000)

**Spec**: [spec.md](./spec.md) · **Contract**: [contracts/data-layer.md](./contracts/data-layer.md)

The shape of everything this layer hands to a detector. Column names are
exact; a detector written against a name that is not in this file will
fail at spec 001, not here.

---

## `Book`

One frozen-in-practice dataclass, built once by `load_all`, passed as the
first argument to every function in the pipeline. It is the whole of what
the bank knows.

| Field | Type | Grain | Rows |
|---|---|---|---|
| `clients` | DataFrame | one row per client | 20 |
| `portfolios` | DataFrame | one row per portfolio | 24 |
| `holdings` | DataFrame | one position per portfolio per snapshot | 1,015 |
| `instruments` | DataFrame | one row per instrument | 62 |
| `mandates` | DataFrame | one row per mandate × asset class | 48 |
| `transactions` | DataFrame | one row per trade, income, fee or call | 393 |
| `credit` | DataFrame | one row per facility | 5 |
| `commitments` | DataFrame | one row per private-markets commitment | 5 |
| `cash_needs` | DataFrame | one row per known future liability | 20 |
| `market` | DataFrame | one series per snapshot date | 115 |
| `events` | DataFrame | one row per dated 2026 event | 16 |
| `notes` | `list[dict]` | one relationship-manager note | 28 |
| `imperfections` | `list[dict]` | one recorded data defect | 10 |

`notes` is a list rather than a frame because it is free text consumed by a
model at spec 002, not arithmetic. Its dicts carry `note_id`, `client_id`,
`note_date`, `rm_id`, `rm_name`, `channel`, `note`.

### Convenience accessors

Three methods, each a filter and nothing more. They exist so a detector
never writes a boolean mask by hand and never accidentally omits the
snapshot-date condition — the most likely way to sum five snapshots into
one exposure figure.

| Method | Returns |
|---|---|
| `client(client_id)` | the one client row, as a Series |
| `notes_for(client_id)` | that client's notes, ordered by `note_date` |
| `holdings_at(client_id, date)` | that client's positions at one snapshot |

---

## `holdings` after the load-time joins

The centre of gravity. 1,015 rows in, 1,015 rows out — the join must not
change the count, and a test asserts it.

**Native columns**, from `holdings.csv`, unchanged:

```
snapshot_date, portfolio_id, client_id, instrument_id, instrument_name,
asset_class, sub_asset_class, sector, region, instrument_ccy,
quantity, price_local, market_value_local, portfolio_ccy,
market_value_base, market_value_usd, weight_pct,
avg_cost_local, cost_basis_base, unrealised_pnl_base, unrealised_pnl_pct,
lending_value_base, advance_rate_pct, liquidity_tier,
valuation_date, acquired_date
```

**Added by the instruments merge** on `instrument_id`, suffixed `_inst`
where the name collides:

```
underlying_reference           the structured product's basket, free text
sustainability_excluded        Y / N
concentration_limit_applies    Y / N
currency                       the instrument's own currency
asset_class_inst               reference classification
sub_asset_class_inst
sector_inst
region_inst
liquidity_tier_inst
instrument_name_inst
price_<snapshot_date> × 5      full price history, one column per snapshot
```

**Added by the portfolios merge** on `portfolio_id`:

```
mandate_code                   e.g. BALG, CONS, BAL
```

### Why both asset classes are kept

`asset_class` is how the position is **booked**. `asset_class_inst` is the
reference classification. They differ, and the difference is spec 001's
entire argument — an accumulator referencing a property developer is booked
as a Structured Product, so no equity-concentration check sees it. A model
that discarded one of these columns would make the hero finding
unreachable. Neither is dropped.

### ⚠️ `weight_pct` is per portfolio

Carried through unchanged because it is part of the source record and
appears in evidence panels. **It is never summed to a client-level figure.**
For CL-0017 it sums to 299.9999. Client-level exposure comes from
`client_weights` only.

---

## `client_weights(book, client_id, date)` → DataFrame

Every row of `holdings_at(client_id, date)`, in its original column shape,
plus one column:

| Column | Meaning |
|---|---|
| `w` | `market_value_usd` as a percentage of the client's total `market_value_usd` at that snapshot, across **all** that client's portfolios |

**Guarantees**: `w` sums to 100.0 ± 0.001. Rows are sorted by `w`
descending, then `instrument_id` ascending, so the order is deterministic
and the largest exposure is first. Every row retains `client_id`,
`portfolio_id`, `instrument_id` and `snapshot_date`, so any figure derived
from this frame can be traced to source rows — Article VI at the primitive
level.

One denominator per client per date. Not per portfolio, not an average of
per-portfolio weights.

---

## `diff(book, client_id, date_a, date_b)` → DataFrame

One row per instrument held at **either** date. Outer join, zero-filled.

| Column | Meaning |
|---|---|
| `instrument_id` | the position |
| `instrument_name` | carried from whichever date has it |
| `asset_class` | as booked |
| `value_a`, `value_b` | `market_value_usd` at `date_a` and `date_b` |
| `weight_a`, `weight_b` | client-level `w` at each date |
| `d_value` | `value_b − value_a` |
| `d_weight` | `weight_b − weight_a` |

**Guarantees**: an instrument present at only one date appears with `0.0`
at the other, never `NaN` and never absent. Sorted by `instrument_id`.
Row count equals the size of the union of instruments at the two dates.

The structured note that settles in June is the reason this is an outer
join. An inner join drops the most important position in the demo.

---

## `attribution(book, client_id, date_a, date_b)` → DataFrame

The same frame as `diff`, re-ordered by `abs(d_value)` descending, then
`instrument_id` ascending as a tiebreak. Same columns, same rows. Answers
"who moved the portfolio".

---

## `events_between(book, date_a, date_b)` → DataFrame

Rows of `event_log.csv` whose `event_date` falls in the **inclusive** range,
sorted by `event_date` then `description`.

```
event_date, event_type, region, description,
primary_transmission, severity
```

Values are carried through **unmodified**. No enrichment, no rewording, no
inferred fields. This is Principle IV in one sentence: what a brief cites,
this function returned, and what this function returned, the file said.

---

## `events_touching(book, client_id, date_a, date_b)` → DataFrame

The subset of `events_between` whose transmission channels name something
the client holds, plus one column explaining why each row is there.

| Column | Meaning |
|---|---|
| *(all `events_between` columns)* | unmodified |
| `matched_on` | the matching terms, comma-joined and sorted — e.g. `energy` |

`matched_on` exists so the evidence panel can say *why* an event was
surfaced, and so Priscilla can reject a match she disagrees with
(Principle IX). An event with no match is excluded; absence is a real
answer.

**Matching rule**, fixed here so every detector inherits the same one:

1. Take the client's distinct `sector` and `sub_asset_class` values at any
   snapshot; lowercase, strip, sort.
2. Split `primary_transmission` on commas; lowercase, strip.
3. A term pair matches when either contains the other, provided both are
   at least four characters. Shorter terms must match exactly.

Sorted inputs, so the result does not depend on frame order. See
[research.md](./research.md) R4 and R5 for the enumerated match set and the
recorded limitation — the match is narrow rather than loose, and `shipping`
matches nothing because shipping positions are booked as `Industrials`.

---

## `imperfections` entry

One dict per affected **row**, not per instrument. The count is part of the
evidence.

| Key | Meaning |
|---|---|
| `kind` | `missing_cost_basis` \| `stale_valuation` \| `orphan_instrument` |
| `file` | the source file, e.g. `holdings.csv` |
| `client_id` | the affected client, where the row has one |
| `portfolio_id` | the affected portfolio, where the row has one |
| `instrument_id` | the affected instrument |
| `snapshot_date` | which snapshot the defect appears in |
| `field` | the column concerned |
| `detail` | one sentence, plain English, safe to render |

Ten entries against the supplied data: five `missing_cost_basis`
(CL-0003 / SYN-ST-0107, one per snapshot) and five `stale_valuation`
(CL-0002 / SYN-AL-0308, valued 2025-09-30). Zero
`orphan_instrument` — the check is implemented and currently returns
nothing.

Sorted by `kind`, `client_id`, `instrument_id`, `snapshot_date` so the
list is byte-identical between runs (Principle VII).

**No row is ever dropped, filled or repaired.** A missing cost basis stays
missing. `.alamazing/findings.md` records why this one matters: selling
Nordvind is one of Margarethe's options for the EUR 3.4m tax instalment,
and nobody can tell her its tax consequence. And the stale valuation is a
private-market mark lagging a quarter **by design** — recorded as a lag,
never presented as an error.

---

## Derived helpers

| Function | Returns |
|---|---|
| `snapshots(book)` | every snapshot date in the holdings, ascending |
| `latest(book)` | the last of them |

Both derive from the data. No date is written into `pipeline/`
(Principle XI). The demo passes `latest(book)` as "today" and
`snapshots(book)[1]` as the pre-conflict comparison — positional, so the
pipeline runs on any book with any dates.
