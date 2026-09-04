# Contract — Data Layer (spec 000)

**Spec**: [../spec.md](../spec.md) · **Data model**: [../data-model.md](../data-model.md)

Six public functions plus two helpers. **Specs 001 through 006 are written
against this contract.** Changing a signature here after spec 001 breaks
every detector, so it is fixed now rather than discovered later.

The contract is a Python module boundary, not an HTTP API — this is a
library consumed in-process by `pipeline/build.py`. There is no network
interface anywhere in the system by design (Technology Standards: the
pipeline and the web app meet at one committed JSON artifact).

---

## Invariants — hold for every function below

1. **Only `load_all` performs I/O.** Every other function takes an
   already-loaded `Book`. A detector cannot accidentally re-read the disk
   mid-computation, so a build cannot half-see a changed file.
2. **No function calls a language model.** No `anthropic` import exists in
   `pipeline/load.py`, `diff.py` or `events.py` (Principle V).
3. **Deterministic, including row order.** Every returned frame has an
   explicit sort. No reliance on set or dict iteration order
   (Principle VII).
4. **Nothing is mutated.** Inputs are never modified in place; every
   function returns a new frame. `data/` is never written to.
5. **No row is dropped.** Filtering to a client or a date is selection;
   discarding a row because it is inconvenient is not permitted
   (FR-013).
6. **Row identifiers survive.** Every returned frame carries enough of
   `client_id`, `portfolio_id`, `instrument_id` and `snapshot_date` to
   trace any derived figure to its source rows (Principle VI).
7. **No literals.** No client id, instrument id, sector name, date or
   market series appears in any signature default or function body
   (Principle XI).

---

## `load_all(path: str = "data/") -> Book`

Reads the twelve files, performs the two joins, records imperfections,
returns the `Book`.

**Parameters** — `path`: the data directory. An argument, never a constant.
There is no file-upload path and none will be added (Principle XI).

**Returns** — a `Book` with the row counts in
[data-model.md](../data-model.md).

**Guarantees**
- `len(book.holdings) == 1015` for the supplied folder, and the joins do
  not change that count.
- Every holdings row carries `underlying_reference`,
  `sustainability_excluded`, `concentration_limit_applies` and
  `mandate_code`.
- Both `asset_class` and `asset_class_inst` are present; neither is
  dropped.
- All date columns are ISO `YYYY-MM-DD` strings, not timestamps
  ([research.md](../research.md) R6).
- `book.imperfections` is non-empty and sorted deterministically.

**Raises** — `FileNotFoundError` if any of the twelve files is absent,
naming the file. A partially loaded book is worse than no book, so the
failure is loud.

---

## `client_weights(book: Book, client_id: str, date: str) -> DataFrame`

Client-level exposure. **The one function that must not be wrong.**

**Parameters** — `client_id`, `date`: both arguments. `date` must be a
snapshot present in the data.

**Returns** — every row of that client's holdings at that snapshot, plus a
`w` column: `market_value_usd` as a percentage of the client's total
`market_value_usd` at that date, across **all** their portfolios.

**Guarantees**
- `w` sums to `100.0 ± 0.001`.
- One denominator per client per date. `weight_pct` is **never** summed to
  reach a client-level figure (Technology Standards;
  [research.md](../research.md) R1).
- Sorted by `w` descending, then `instrument_id` ascending.
- An empty frame with the expected columns when the client holds nothing
  at that date — not an error, and no division by zero.

**Raises** — `ValueError` if `date` is not a snapshot in the data, naming
the available snapshots. Returning an empty frame for a typo'd date is how
a zero exposure gets quoted as a fact (FR-018).

---

## `diff(book, client_id, date_a, date_b) -> DataFrame`

What changed, per instrument, between two snapshots.

**Returns** — one row per instrument held at either date, with `value_a`,
`value_b`, `weight_a`, `weight_b`, `d_value`, `d_weight`.

**Guarantees**
- Outer join. An instrument present at only one date appears with `0.0`
  at the other — never `NaN`, never absent.
- Row count equals the union of instruments at the two dates.
- Sorted by `instrument_id`.

**Raises** — `ValueError` if either date is not a snapshot in the data.

---

## `attribution(book, client_id, date_a, date_b) -> DataFrame`

Who moved the portfolio. Same rows and columns as `diff`, ordered by
`abs(d_value)` descending, then `instrument_id` ascending as a
deterministic tiebreak.

---

## `events_between(book, date_a, date_b) -> DataFrame`

**Returns** — rows of `event_log.csv` whose `event_date` falls in the
**inclusive** range `[date_a, date_b]`, sorted by `event_date` then
`description`.

**Guarantees** — every field is carried through **unmodified**. No
enrichment, no rewording, no inferred columns. What a brief cites, this
returned; what this returned, the file said (Principle IV).

Unlike the holdings functions, the dates here need not be snapshot dates —
any ISO date range is valid, because events are not snapshotted.

---

## `events_touching(book, client_id, date_a, date_b) -> DataFrame`

The subset of `events_between` whose transmission channels name something
the client holds, plus a `matched_on` column giving the matching terms,
comma-joined and sorted.

**Matching rule** — fixed here so every detector inherits one definition:

1. The client's distinct `sector` and `sub_asset_class` values at any
   snapshot; lowercased, stripped, **sorted**.
2. `primary_transmission` split on commas; lowercased, stripped.
3. A pair matches when either string contains the other, provided both are
   at least four characters. Shorter terms must match exactly.

**Guarantees**
- Keyword match in code. **A model is never asked which events are
  relevant** — `event_log.csv` is authoritative and the match must be
  reproducible (Principle IV, and `.alamazing/implementation.md` step 4 in
  terms).
- An event matching nothing is excluded. Absence is a real answer.
- `matched_on` is populated for every returned row, so the evidence panel
  can state why the event is there and Priscilla can reject a match she
  disagrees with (Principle IX).
- Sorted inputs, so the result is independent of frame order.

**Recorded limitation** (Principle X) — the match is **narrow, not loose**.
It has effectively no false positives on this dataset and several false
negatives: `shipping` matches nothing, because shipping positions are
booked under sector `Industrials`. The honest description of this function
is *"events whose transmission channels name an asset class or sector this
client holds"*, not *"every event that touches this client"*. Both required
events are still returned, via `energy`. See
[research.md](../research.md) R5 for the enumerated match set.

---

## Helpers

### `snapshots(book) -> list[str]`

Every snapshot date in the holdings, ascending, derived from the data.

### `latest(book) -> str`

The last of them.

**Why these exist** — so no date is ever written into `pipeline/`. The
demo passes `latest(book)` as "today" and `snapshots(book)[1]` as the
pre-conflict comparison. Positional, so the pipeline runs on any book with
any dates (Principle XI). This is what makes "would this work on other
data?" answerable by typing rather than asserting.

---

## Downstream consumers

Recorded so the cost of a change to this contract is visible:

| Spec | Module | Uses |
|---|---|---|
| 001 | `d3_hidden.py` | `client_weights`, `latest`, `underlying_reference`, both asset-class columns |
| 002 | `d1_said.py` | `look_through` from 001, therefore `client_weights` |
| 003 | `d2_mandate.py` | `holdings_at`, `mandate_code`, `mandates`, `transactions` |
| 004 | `d4_runway.py`, `d5_unanswered.py` | `client_weights`, `liquidity_tier`, `cash_needs`, `commitments`, `credit`, `notes_for` |
| 005 | `d6_scenario.py` | `client_weights`, `market`, `snapshots`, the `price_<date>` columns |
| 006 | `brief.py`, `build.py` | `Book`, `notes_for`, `client`, `events_touching`, `imperfections` |

Six of six specs consume `client_weights` directly or transitively. That is
why R1 is the longest entry in the research file.
