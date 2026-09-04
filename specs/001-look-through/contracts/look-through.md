# Contract — Look-Through Concentration (spec 001)

**Spec**: [../spec.md](../spec.md) · **Research**: [../research.md](../research.md)

Two modules. **Spec 002 consumes `look_through` directly**, and spec 003
consumes all of `mandate.py`, so these signatures are fixed here rather
than discovered later.

Inherits every invariant from spec 000's contract: no I/O, no model call,
nothing mutated, no row dropped, row identifiers survive, deterministic
including order, no literals.

---

## `pipeline/mandate.py`

Bands are **per portfolio**. Exposure concentration is **per client**. The
two are never conflated — that is the same class of error as spec 000's
`weight_pct` trap, one level up, and `test_bands_are_per_portfolio_not_per_client`
asserts the distinction across all 20 clients.

### `portfolio_allocation(book, client_id, date) -> DataFrame`

Asset-class allocation within each of the client's portfolios. The
denominator is the **portfolio's** value, because that is the grain the
bands are written against.

Columns: `portfolio_id`, `mandate_code`, `asset_class`, `actual_pct`.
Sorted by `portfolio_id`, `asset_class`. Raises `ValueError` on a date
that is not a snapshot.

### `check_bands(book, client_id, date) -> DataFrame`

One row per asset class **held**, with its band and a verdict of `within`,
`below_min` or `above_max`.

**Iterates the client's holdings, not the mandate's rows.** This is the
difference between a correct check and a false breach: the hero's BALG
mandate defines a Commodities band and he holds no commodities. Iterating
the mandate would report Commodities at 0% against a minimum and call it a
breach — destroying the strongest line in the pitch with a bug.
`.alamazing/findings.md` § Data imperfections states it directly: absence
of the row is not a breach.

A class with no band row is `within` — neither breach nor error.

### `check_position_limits(book, client_id, date) -> DataFrame`

Every position against its mandate's `max_single_position_pct`, weighted
per portfolio. Sorted by `actual_pct` descending, so row 0 is the largest
position. Adds a boolean `breached`.

### `compliance_verdict(book, client_id, date) -> dict`

```
{
  "clean":               bool,
  "bands":               [ ...every band row... ],
  "breached_bands":      [ ...breaches only... ],
  "breached_positions":  [ ...breaches only... ],
  "largest_position":    {instrument_id, instrument_name, actual_pct, limit_pct}
}
```

**Returns the verdict *and its workings*.** A bare boolean would make spec
007's mandate panel impossible to render, and the panel is the point: the
argument is not "he is compliant" but "here are the five bands, every one
respected, and the portfolio is still 42% one bet".

`clean` is **earned, never defaulted** — true only when every band of every
one of the client's portfolios passes and no single position exceeds its
limit. `test_compliance_clean_is_earned` asserts it is `False` for a
client with a known breach, so a flag that defaulted true could not pass.

---

## `pipeline/divergence/d3_hidden.py`

### `referenced_names(row) -> list[str]`

The names a holding references, recovered from **two** places.

1. `underlying_reference` after the colon, split on `/`
2. `instrument_name` after a `ref.` marker, up to the first comma

**Block 3 describes only the first.** That is incomplete against this
data: one client's accumulator carries no name in its reference at all —
only strike, knock-out and double-up mechanics — and names its issuer in
the instrument name. A parser reading only the reference cannot find that
issuer, and `test_lookthrough_cl0014`, a required assertion, fails. See
[../research.md](../research.md) R6.

Returns names **sorted**, so nothing downstream depends on which source
produced them. Never raises: a reference naming a category rather than an
issuer yields whatever the name gives, possibly nothing.

### `look_through(book, client_id, date) -> DataFrame`

Every row of `client_weights`, plus two columns:

| Column | Meaning |
|---|---|
| `theme_sector` | the sector theme this row belongs to, or `None` |
| `theme_issuer` | the issuer theme this row belongs to, or `None` |

**A frame, not theme totals.** Spec 002 filters these rows against a
claim's target and would otherwise recompute them. Totals are a `groupby`
the caller performs.

**Two rules, both applied**, because neither alone reproduces both
recorded figures ([../research.md](../research.md) R5):

| Rule | Membership | Answers |
|---|---|---|
| **sector** | every holding whose sector matches the sector of any referenced name, plus the product | "what is he actually exposed to, once you look through the note?" |
| **issuer** | the specific holdings the referenced names match, plus the product; requires ≥ 2 matches | "how many ways does he own the same company?" |

**Theme labels are derived from the data.** A sector theme is the joined
sector values as the files spell them. An issuer theme is the joined
reference names as written — not the longer names of the lines that
matched, because calling a two-company basket after one of them would
mislead in RM-facing copy. **No theme name is written in the module**
(Principle XI).

Themes **overlap by design** — a holding may belong to both. So theme
totals do **not** sum to 100%, and the invariant is instead: no instrument
twice within a theme, and no theme over 100%. A structured product
contributing its weight once per referenced name would inflate every
figure plausibly, and `test_no_double_counting_in_any_theme` sweeps all 20
clients at all 5 snapshots for exactly that.

### `trajectory(book, client_id, instrument_ids) -> list[dict]`

That set of instruments' combined client-level weight at every snapshot,
chronologically.

**Membership is fixed as resolved today, then measured backwards.** That
is the question being asked — "this grew from 29.41% to 42.13%" — and it
is not the same as re-resolving the theme at each date. Re-resolving
returns zero before the structured product settled, because with no
product there is nothing to look through, which hides precisely the
history the trajectory exists to show. This was a real defect caught by
comparing output to the recorded figures.

### `detect(book, client_id, date=None, threshold_pct=25.0) -> list[dict]`

Findings for one client. **Possibly none, which is a real answer** — no
finding is fabricated to fill a screen.

`date` defaults to the latest snapshot, derived from the data.
`threshold_pct` is a parameter so "what about 20%?" is answered by typing
rather than explaining (Principle XI, `test_threshold_is_a_parameter`).

Emits up to three rules, sorted by `theme_pct` descending then `rule` then
`theme`:

| `rule` | Threshold-gated | Purpose |
|---|---|---|
| `sector` | yes | the magnitude |
| `issuer` | yes | one name, several ways |
| `duplicate_underlying` | **no** | the explanation |

`duplicate_underlying` is emitted regardless of magnitude because it is a
qualitative fact about the position, not a size. It is what makes the
concentration *explicable*: "42% concentrated" invites argument, "your
note's basket contains two names you already own outright" ends it. It
carries `duplicated_instrument_ids` and `referencing_instrument_id`, and
its copy never calls the duplication diversification — on the downside a
worst-of basket pays on whichever underlying falls furthest, so it adds to
an existing position rather than spreading it.

**Every finding validates against the recorded Finding schema**
(`specs/001-divergence-engine/contracts/finding.schema.json`) with
`kind: "D3"`, and is JSON-serialisable for spec 006. Verified across all
13 findings the book produces.

**Every finding carries evidence or is not emitted** (Principle VI). The
`sector` and `issuer` rules cite `holdings.csv` rows;
`duplicate_underlying` additionally cites the `instruments.csv` row and
quotes the reference text itself.

`unsure_about` records what would change the answer (Principle X): names
the reference lists that the client does not hold, and names matched on a
prefix rather than in full.

`events` is empty — this spec cites none. Populated from spec 005.

---

## Downstream consumers

| Spec | Uses |
|---|---|
| 002 `d1_said.py` | `look_through` — filters its rows against a claim's `target` |
| 003 `d2_mandate.py` | all of `mandate.py`; extends the verdict into drift / client-directed / inherited |
| 005 `d6_scenario.py` | `look_through` to select the affected theme before repricing |
| 006 `build.py` | `detect` for every client |

Four of the five remaining specs depend on this contract. That is why the
two rules and the trajectory semantics are settled here rather than left
to whichever spec discovers them.
