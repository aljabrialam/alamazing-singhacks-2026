# Phase 0 Research — Data Layer (spec 000)

**Date**: 2026-09-04 · **Spec**: [spec.md](./spec.md) · **Plan**: [plan.md](./plan.md)

Six questions had to be answered from `data/` rather than assumed. Each is
recorded below with the query that resolved it, so the answer is evidence
and not recollection (Principle IV). Every query was run against the
supplied files before `pipeline/load.py` was written.

---

## R1 — Which clients hold several portfolios, and how badly does the trap bite?

**Decision**: Recompute client-level weights from `market_value_usd` with a
single denominator per client per snapshot date. Never sum `weight_pct`.
Assert the divergence in a test using CL-0017, the worst case.

**Rationale**: The trap is not theoretical. Three of twenty clients hold
more than one portfolio, and summing the per-portfolio column gives them
weights totalling 200% or 300%:

```
CL-0001: 2 portfolios, raw weight_pct sums to 200.0001
CL-0002: 2 portfolios, raw weight_pct sums to 200.0001
CL-0017: 3 portfolios, raw weight_pct sums to 299.9999
```

The failure mode matters more than the size of it. A weight summing to
300% is obviously wrong and would be caught. The dangerous case is a
*single* exposure quoted from that book — a position at a true 6% of the
client reads as 18% of its own portfolio, or the reverse, and both are
plausible enough to reach a slide. The recorded figures also show why the
sums are 200.0001 rather than 200: the source column is itself rounded to
four decimals, which is a second reason not to build on it.

**Alternatives considered**:
- *Sum `weight_pct` and divide by the number of portfolios.* Rejected: an
  average of percentages with different denominators is not a percentage
  of anything. It happens to be close for clients whose portfolios are of
  similar size and badly wrong for CL-0017, whose three differ.
- *Use `weight_pct` for single-portfolio clients and recompute only for
  the rest.* Rejected: two code paths, one of which is only exercised by
  three clients, is how a silent wrong number survives to 18:00. The
  recomputation is one line.
- *Recompute from `market_value_base`.* Rejected: base currency differs by
  portfolio (CL-0019 is USD, CL-0003 EUR, CL-0014 HKD), so summing across
  a client's portfolios in base terms adds unlike units.

**Evidence**:
```python
p = pd.read_csv('data/portfolios.csv'); h = pd.read_csv('data/holdings.csv')
mp = p.groupby('client_id').portfolio_id.nunique()
mp[mp > 1]                       # CL-0001: 2, CL-0002: 2, CL-0017: 3
h[(h.client_id=='CL-0017') & (h.snapshot_date=='2026-08-26')].weight_pct.sum()
# → 299.9999
```

---

## R2 — Which columns collide when instruments are merged onto holdings?

**Decision**: Merge with `suffixes=('', '_inst')`, so the holdings column
keeps its bare name and the instruments column gains the suffix. Seven
columns collide.

**Rationale**: `.alamazing/implementation.md` warns that `asset_class`
exists in both. It is worse than that — the overlap is:

```
asset_class, instrument_name, sub_asset_class, sector, region,
liquidity_tier   (plus instrument_id, the join key)
```

Defaulting pandas' `_x`/`_y` suffixes would leave six columns named
`asset_class_x` and `asset_class_y` with nothing in the name to say which
is which, in a file that six detectors read. Keeping the holdings name
bare means every detector written against the *holdings* grain reads
correctly without knowing this join happened, and the instrument reference
value is available under an explicit name when a detector wants it.

The two are not redundant. `holdings.asset_class` is how the position is
*booked* — the accumulator on Golden Harbour is booked as a Structured
Product. `instruments.asset_class` is the reference classification. Spec
001's whole argument is that these differ, so neither may be discarded.

**Alternatives considered**:
- *Merge only the three columns needed* (`underlying_reference`,
  `sustainability_excluded`, `concentration_limit_applies`), avoiding
  collisions entirely. Rejected, narrowly: it is tidier, but spec 001 needs
  to compare booked against reference asset class, and spec 004 needs the
  reference `liquidity_tier` as a cross-check on the holdings one. Merging
  the whole reference frame once with explicit suffixes costs nothing at
  62 rows and leaves both available.
- *Drop the instruments copies after the merge.* Rejected for the same
  reason — it discards the comparison spec 001 rests on.

**Evidence**:
```python
sorted(set(h.columns) & set(i.columns))
# ['asset_class', 'instrument_id', 'instrument_name', 'liquidity_tier',
#  'region', 'sector', 'sub_asset_class']
```

---

## R3 — How many imperfections exist, and of what kind?

**Decision**: Record three classes, one entry per affected row, each
naming file, client, portfolio, instrument, snapshot date and the field
concerned. Never drop, never fill, never repair.

**Rationale**: Counted rather than assumed:

| Class | Rows | Where |
|---|---|---|
| `unrealised_pnl_pct` null | **5** | all CL-0003 / SYN-ST-0107 (Nordvind Industrial AB) — one row per snapshot |
| `valuation_date` ≠ `snapshot_date` | **5** | all CL-0002 / SYN-AL-0308 — valued 2025-09-30 against every later snapshot |
| `instrument_id` in holdings but not instruments | **0** | none exist |

Two findings here are worth more than the counts.

First, the missing cost basis is not one row, it is **all five snapshots**
of that holding — the cost basis never existed, because the position was
transferred in when Margarethe Voss-Brenner's husband died and no cost
basis came with it. That is what `.alamazing/findings.md` records, and it
matters materially: selling Nordvind is one of her options for the EUR 3.4m
tax instalment, and nobody can tell her the tax consequence of doing so.
The imperfection is not a data-quality nit; it is a fact about her
situation. Recording it per row rather than per instrument is what lets
spec 004 say so.

**And it is sharper than `findings.md` states.** A test written against
"five rows of SYN-ST-0107 are null" failed at ten rows, which surfaced
something the recorded findings do not mention: **CL-0009 holds the same
stock, with a full cost basis, acquired 2011-01-01, showing a +93% gain.**

```
SYN-ST-0107   PF-0005 / CL-0003   unrealised_pnl_pct = NaN   acquired 2026-02-16
SYN-ST-0107   PF-0011 / CL-0009   unrealised_pnl_pct = 93.24  acquired 2011-01-01
```

So this is **not** a reference-data omission. The instrument's cost basis
is perfectly well known to the bank; it exists two portfolios away. What is
missing is the cost basis for *her* position, because it did not come
across in the transfer — and her `acquired_date` is 2026-02-16, the date of
the transfer-in itself, not the date her husband bought it.

This changes what may honestly be said on stage. The weak version is "the
data has a gap". The true version is: *the bank knows what this stock cost
in 2011 and cannot tell Margarethe what her holding cost, because the
transfer carried a date and a value but not a history.* That is a
transfer-in defect, not a file defect, and it is precisely the kind of
thing that becomes a tax problem the moment she sells. It also means the
gap **cannot be repaired from elsewhere in the file** — CL-0009's basis is
not hers — which is the reason the number stays absent rather than being
inferred (Principle X).

A test asserting the wrong count is what found this. Recorded here because
the recorded findings will be quoted on stage and this refines one of them.

Second, the stale valuation on SYN-AL-0308 is a **private-market
valuation lagging by a quarter**, which `.alamazing/findings.md` explicitly
says is by design and must not be reported as an error. So the record must
carry both dates and let the uncertainty screen present it as a lag, not a
defect. This is the difference between noticing and crying wolf, and the
brief scores the first.

The orphan check returns zero. It is still implemented, because a real
bank's reference data does not join cleanly and the check costs one line —
and because a check that returns nothing today is how you find out the
day it stops returning nothing.

**Alternatives considered**:
- *Fill missing `unrealised_pnl_pct` with 0.* Rejected outright — it
  asserts a fact the data does not support (Principle X) and would put a
  fabricated 0% gain in front of a client deciding what to sell.
- *Drop the stale-valuation rows.* Rejected — Principle X, FR-013, and it
  would remove a real 6.32% of Margarethe's alternatives allocation.
- *Record one entry per instrument rather than per row.* Rejected: the
  count is part of the evidence, and spec 004 needs to know the gap covers
  every snapshot rather than one.

**Evidence**:
```python
h.unrealised_pnl_pct.isna().sum()                 # 5
h[h.unrealised_pnl_pct.isna()][['client_id','instrument_id']].drop_duplicates()
# CL-0003 / SYN-ST-0107
(h.valuation_date != h.snapshot_date).sum()       # 5
set(h.instrument_id) - set(i.instrument_id)       # set()
```

---

## R4 — Does keyword event matching return the two required events?

**Decision**: Yes. Keep the keyword match. Both required events are
returned for the hero client, matched on the term `energy`.

**Rationale**: The acceptance criterion is that
`events_touching(hero, pre-conflict, latest)` includes **2026-03-04**
(Strait of Hormuz closed) and **2026-08-05** (naval blockade reimposed).
Run against the data, with the client's distinct sectors and
sub-asset-classes as the term set:

```
2026-02-28 → ['energy']
2026-03-02 → ['energy']
2026-03-04 → ['energy']     ← required
2026-03-11 → ['energy']
2026-03-12 → ['energy']
2026-04-30 → []
2026-05-04 → ['energy']
2026-06-05 → []
2026-06-17 → []
2026-06-19 → []
2026-06-30 → []
2026-07-29 → []
2026-08-05 → ['energy']     ← required
```

Seven of thirteen events in the window are returned, both required ones
among them. The six excluded are the European fixed income, US technology,
duration and private credit events — correctly excluded, since he holds
none of those exposures.

Note what did **not** happen: `shipping` never matched, because no holding
of his carries `shipping` as a sector. Pacific Orient Shipping is booked
under sector `Industrials`. The match therefore works through energy alone,
which is honest but narrower than the prose suggests. See R5.

**Alternatives considered**:
- *Ask a model which events are relevant.* Rejected by Principle IV and by
  `.alamazing/implementation.md` in terms: "Do not ask a model which events
  are relevant — `event_log.csv` is authoritative and matching must be
  reproducible." A model would have matched `shipping` to Pacific Orient
  Shipping by reading its name, and produced a different answer on a
  different day.
- *Match on instrument names as well as sectors.* Deferred, not rejected —
  see R5. It would catch shipping, and it would also match far more
  loosely. Out of scope for spec 000; recorded as available.

---

## R5 — What is the false-positive risk in that match, and how is it bounded?

**Decision**: Bidirectional substring containment, with a **minimum term
length of four characters**; shorter terms must match exactly. Terms are
sorted before use so the result is order-independent.

**Rationale**: The concern with substring matching is a short token
matching something unrelated. The holding term set contains `cash`,
`gold`, `multi`, `macro` — `multi` matching `multi-asset something` would
be a plausible accident. So the whole cross-product was enumerated rather
than argued about. Across **41 holding terms** and **29 transmission
terms** — 1,189 pairs — exactly **six** match:

```
holding 'energy'          ~  transmission 'energy'
holding 'gold'            ~  transmission 'gold'
holding 'precious metals' ~  transmission 'precious metals'
holding 'precious metals' ~  transmission 'precious metals miners'
holding 'private credit'  ~  transmission 'private credit'
holding 'short duration'  ~  transmission 'duration'
```

Five are exact or near-exact. The sixth, `short duration` ~ `duration`, is
the only inferential one and it is *directionally correct* — the two
duration events in June do touch short-duration credit, less than they
touch long-duration. It is a weak true positive, not a false one.

`multi`, `macro`, `cash`, `diversified` and `sovereign` match nothing. The
minimum-length rule is therefore currently unexercised; it is kept because
the enumeration is a property of this dataset, and a four-character floor
costs nothing and removes the whole class of accident on the next one.

**The honest limitation, recorded rather than hidden** (Principle X): this
match is **narrow, not loose**. It has essentially no false positives and
several false negatives — most notably `shipping`, which matches nothing
because shipping positions are booked as `Industrials`. The two required
events are still returned, through `energy`, so the acceptance criterion
holds and the demo's causal chain is intact. But the honest statement of
what this function does is *"events whose transmission channels name an
asset class or sector this client holds"*, not *"every event that touches
this client"*. Broadening it by matching instrument names is a one-line
change available at spec 005 if the scenario needs it, and it is left
undone here because a wider net at this layer would weaken Article VI —
every event surfaced is one Priscilla has to read.

The direction of the error is deliberate. A false positive is visible in
the evidence panel and rejectable by Priscilla (Principle IX). A false
negative loses the cause of a finding silently. Within this dataset the
match makes neither mistake on the events that matter, and where it must
lean, it leans toward the reproducible.

**Alternatives considered**:
- *Exact term equality only.* Rejected: loses `precious metals` ~
  `precious metals miners`, which is a real match.
- *Token overlap on individual words.* Rejected: `equity` appears in
  `concentrated equity`, `growth equity valuations` and
  `developed market equity`, which would return the June technology
  drawdown for every equity holder in the book — 20 clients, no
  discrimination, and Article VI degraded for all of them.
- *Fuzzy string distance.* Rejected: a threshold nobody can explain in a
  compliance review, and non-obvious to reproduce.

---

## R6 — Are dates parsed to timestamps or kept as ISO strings?

**Decision**: Keep every date column as an ISO `YYYY-MM-DD` string. Do not
pass `parse_dates` to the readers.

**Rationale**: `.alamazing/implementation.md` step 1 suggests
`parse_dates` on all date columns. Taking that instruction literally makes
three things worse, so it is not followed, and the deviation is recorded
here rather than left as a silent divergence from the reference document:

1. **The snapshot dates are also column names.** `instruments.csv` carries
   `price_2025-12-31 … price_2026-08-26` and `portfolios.csv` carries
   `aum_<date>`. Spec 005 reprices a position by looking up
   `f"price_{date}"`. With a timestamp in hand that becomes
   `f"price_{date.strftime('%Y-%m-%d')}"` at every call site — the same
   conversion, written six times, each an opportunity to write it
   differently.
2. **ISO strings sort and compare correctly.** `'2026-03-04' <=
   '2026-08-26'` is true, so `events_between` needs no conversion, and
   `sorted()` on snapshot dates gives chronological order for free.
3. **JSON serialisation at spec 006 is free.** A timestamp needs a custom
   encoder; a string does not. `findings.json` is committed and diffed, so
   a stable textual form is worth having.

The cost is that no date arithmetic is available. Nothing in specs 000–006
does date arithmetic — every comparison is an ordering or an equality, and
the scenario takes two dates as parameters rather than computing an
interval.

**Alternatives considered**:
- *Parse to timestamps as the reference document suggests.* Rejected for
  the three reasons above.
- *Parse to timestamps and re-format at each boundary.* Rejected: the
  worst of both, and the boundary is exactly where a bug would be
  invisible.
- *Parse only `event_date` for the range filter.* Rejected: string
  comparison already does it correctly, and a single parsed column among
  fifteen string ones is a trap for whoever reads it next.

**Consequence for Principle XI**: strings make it *easier* to keep dates
out of the code, because a date is only ever a function argument or a
value read from the frame. No `datetime(2026, 8, 26)` can appear.

---

## Resolved

No NEEDS CLARIFICATION markers remain. All six decisions are taken, each
against a query run on the supplied data. Two deviations from
`.alamazing/implementation.md` are recorded deliberately — the date typing
in R6, and the merge suffixes in R2 — on the grounds that the reference
document is guidance for a human at speed and this file is the record of
what was actually built.
