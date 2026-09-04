# Implementation Plan: Data Layer

**Branch**: `master` (solo build, no feature branches) | **Date**: 2026-09-04 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/000-data-layer/spec.md`

**Spec number**: 000 · **Gate**: G1 · **Time box**: 115 minutes
(`.alamazing/implementation.md` steps 1, 2 and 4: 40 + 30 + 45)

## Summary

Three modules that turn a folder of twelve CSV/JSON files into one
in-memory `Book` every detector reads from, plus the four derived views
that findings are built out of: client-level weights, a two-date
comparison, an attribution ordering, and the events that touched a client.

The technical approach is deliberately the least clever one available.
Everything is eager — the whole book is read at load and held in memory,
because it is under two megabytes and a lazy layer would cost more time
than it saves. There is no cache, no ORM, no schema. Two joins happen once
at load time so that no detector has to remember to do them. The single
piece of real care in the whole spec is that client-level weights are
recomputed from `market_value_usd` and the per-portfolio `weight_pct`
column is never summed.

No model is called. Nothing writes to `data/`.

## Technical Context

**Language/Version**: Python 3.14 (`.venv`, already provisioned)

**Primary Dependencies**: pandas 2.x. pytest for tests. Nothing else —
`anthropic` and `python-dotenv` are installed for later specs and are not
imported here.

**Storage**: Read-only files on disk. `data/` is twelve files, never
written to. No database (Principle XIII).

**Testing**: pytest. `tests/test_load.py`, `tests/test_diff.py`,
`tests/test_events.py`, and one integration file `tests/test_spine.py`
carrying the recorded figure.

**Target Platform**: macOS laptop for the build, Linux for the Vercel
build step later. Pure-Python, no platform dependency.

**Project Type**: Library — a Python package consumed by the pipeline's
own detectors and by `build.py`. No service, no CLI in this spec beyond
what `build.py` will add at spec 006.

**Performance Goals**: Load the book in under two seconds; answer any
acceptance query in under one. Not a real constraint at this data size;
recorded so that a slow implementation is visibly wrong.

**Constraints**: Deterministic output including row order (Principle VII).
No literal client id, instrument id, sector name, date or market series in
`pipeline/` (Principle XI). Only `load_all` touches the filesystem.

**Scale/Scope**: 20 clients, 24 portfolios, 1,015 holdings rows over five
snapshots, 62 instruments, 48 mandate band rows, 393 transactions, 16
events, 28 notes, 115 market observations. Fixed and known.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Article | Gate | Status |
|---|---|---|
| I. Demo Primacy | Does this reach the screen? | **PASS** — indirectly but unavoidably: every figure on S2 is computed here. This is the one spec that is allowed to be invisible, because nothing else can exist without it. |
| II. Specification First | Spec written before code, edits capped at ten minutes | **PASS** — spec.md complete, zero clarification markers |
| III. The Spine Rule | Riskiest assumption proven first | **PASS** — spine re-run before this plan: **42.1343**. Proven against raw files before a line of `load.py` exists |
| IV. Nothing Is Invented | Facts only from `data/` | **PASS** — `events_between` and `events_touching` carry event rows through unmodified; no enrichment, no external data |
| V. Model Never Counts | No model arithmetic | **PASS** — no model call anywhere in this spec. Enforced by grep for `anthropic` in `pipeline/load.py`, `diff.py`, `events.py` |
| VI. Evidence Over Assertion | Findings carry file, rows, values | **PASS (by construction)** — this spec emits no findings. It emits the *evidence primitives* findings will cite: every returned frame carries `instrument_id`, `portfolio_id`, `client_id` and `snapshot_date`, so a detector cannot build a finding without the row ids being to hand. Imperfection records themselves carry file, ids and field |
| VII. Determinism | Same in, same out | **PASS** — explicit sort keys on every return; no `set` iteration, no dict ordering dependence, no `groupby` without `sort=True` |
| VIII. Test Pyramid | ~14 unit, ~4 integration | **PASS** — this spec contributes 6 unit assertions and 1 integration assertion (the spine). Counted in the running total, not duplicated |
| IX. RM Decides | No "recommend" in RM copy | **N/A** — this layer emits no RM-facing copy. Binding from spec 001 |
| X. Honest Framing | Uncertainty stated, data problems reported | **PASS** — FR-012 and the `imperfections` list. Three classes recorded, five rows each for two of them, and the known missing cost basis named |
| XI. Portable By Construction | No hardcoded ids/dates/series | **PASS** — `load_all(path)` takes the directory; `snapshots()` derives dates from data; no exposure list, no client id. Verified by grep |
| XII. Vertical Slices | Runnable end to end | **PASS** — the book is queryable in a REPL the moment `load_all` returns |
| XIII. Declared Scope | Nothing out of scope built | **PASS** — no upload, no database, no detector logic, no caching |
| XIV. Design Is A Quarter | Time spent proportionate | **PASS** — 115 minutes, Friday night, before any screen exists. Principle XII forbids starting a screen tonight |
| XV. Living Evidence | Tagged, recorded | **PENDING** — `g1` tag and `docs/gates.md` line at the end of implementation |

**Verdict: no violations. Complexity Tracking section omitted — nothing to
justify.**

Two articles deserve a note rather than a tick, because a tick would be
glib:

- **Article VI** is satisfied structurally rather than actively. A detector
  written against this layer *can* always produce evidence, because the
  row identifiers never leave the frame. That is the strongest form the
  guarantee can take at this layer, and it is why the joins happen once at
  load rather than in each detector.
- **Article VIII**'s integration test for this spec is the spine figure.
  It is the same number as spec 001's `test_lookthrough_cl0019`, computed a
  different way — here as a raw client-weight sum over four instrument ids
  supplied by the *test*, there through `look_through()`. Two independent
  paths to one recorded figure is the point, not duplication.

## Project Structure

### Documentation (this feature)

```text
specs/000-data-layer/
├── spec.md              # requirements — written
├── plan.md              # this file
├── research.md          # Phase 0 — six decisions taken against the data
├── data-model.md        # Phase 1 — Book, and every frame's shape
├── quickstart.md        # Phase 1 — the acceptance queries, runnable
├── contracts/
│   └── data-layer.md    # Phase 1 — the six public functions
└── checklists/
    └── requirements.md  # spec quality checklist — passed
```

### Source Code (repository root)

```text
pipeline/
├── __init__.py          # exists, empty
├── load.py              # Book, load_all, client_weights, snapshots, latest
├── diff.py              # diff, attribution
├── events.py            # events_between, events_touching
└── divergence/
    └── __init__.py      # exists, empty — populated from spec 001

tests/
├── conftest.py          # one session-scoped `book` fixture
├── test_load.py         # unit: counts, joins, weights, imperfections
├── test_diff.py         # unit: appearing and disappearing positions
├── test_events.py       # unit: range and keyword matching
└── test_spine.py        # integration: 42.134 ± 0.001
```

**Structure Decision**: Single flat Python package under `pipeline/`, with
detectors in a `divergence/` subpackage from spec 001 onward. This is the
layout `.alamazing/implementation.md` specifies and the run sheet's target
tree. No `src/` directory, no models/services/lib split — three modules and
one dataclass do not need a hexagon around them, and Article XIV pays
nothing for architecture.

Tests live in a single top-level `tests/` with no unit/integration
subdirectories. The pyramid is tracked by counting assertions
(Article VIII), not by directory, and one flat folder keeps
`pytest tests/ -v` as the single command the run sheet promises.

## Phase 0 — Research

Six questions had to be answered from the data rather than assumed. All
six are resolved in [research.md](./research.md), each with the query that
resolved it. Summary:

| # | Question | Resolution |
|---|---|---|
| R1 | Which clients hold several portfolios? | CL-0001 (2), CL-0002 (2), CL-0017 (3). Their raw `weight_pct` sums to 200.0001, 200.0001 and 299.9999 |
| R2 | Which columns collide on the instruments join? | Seven: `asset_class`, `instrument_name`, `sub_asset_class`, `sector`, `region`, `liquidity_tier`, plus the key |
| R3 | How many imperfections exist, and of what kind? | 5 rows missing `unrealised_pnl_pct` (all CL-0003 / SYN-ST-0107), 5 rows with a stale `valuation_date` (CL-0002 / SYN-AL-0308), 0 orphan instruments |
| R4 | Does keyword event matching actually return the two required events? | Yes — both via the term `energy` |
| R5 | What is the false-positive risk in that match? | Real but bounded; mitigated by a minimum term length |
| R6 | How are dates typed — strings or timestamps? | Kept as ISO strings |

No NEEDS CLARIFICATION markers remain.

## Phase 1 — Design

Three artifacts, all written:

- **[data-model.md](./data-model.md)** — the `Book` dataclass field by
  field, the exact columns of each returned frame, and the imperfection
  record shape.
- **[contracts/data-layer.md](./contracts/data-layer.md)** — the six public
  functions with signatures, guarantees and failure behaviour. This is the
  contract specs 001–006 are written against; changing it later breaks
  every detector, so it is fixed now.
- **[quickstart.md](./quickstart.md)** — every acceptance query from the
  spec as a runnable block with its expected output, so the gate can be
  re-verified in thirty seconds at 15:00 without reading code.

### Design decisions worth recording

**The two joins happen once, at load.** `instruments` and the portfolio's
`mandate_code` are merged onto `holdings` inside `load_all`. The
alternative — joining inside each detector — was rejected because six
detectors each remembering to bring `underlying_reference` along is six
chances to forget, and the one that forgets produces a *plausible* number.
The cost is a wider holdings frame, which is free at 1,015 rows.

**`client_weights` returns a frame, not a scalar.** It adds a `w` column
and returns every row, so the caller can filter, group by theme, or cite
row ids. A function returning just a percentage would make Article VI
impossible to honour downstream.

**Weights are computed over the client's whole book at that date**, not
per portfolio and then averaged. Summing per-portfolio weights is the
recorded trap; averaging them is a subtler version of the same error, and
both are excluded by computing one denominator per client per date.

**`diff` uses an outer join and fills with zero, never drops.** The
structured note settles in June and has no February row. An inner join
would silently omit the single most important position in the demo — which
is exactly the class of error this spec exists to prevent.

**Event matching is a keyword match with a minimum term length.** Both
required events match on `energy`. Bidirectional substring containment on
very short tokens invites false positives, so containment requires four
characters or more; shorter terms must match exactly. A false positive
here is visible in the evidence panel and rejectable by Priscilla — a
false negative silently loses the cause of the finding, so the match errs
toward inclusion.

**Dates stay as ISO strings.** They sort correctly lexicographically,
compare cleanly against the `price_<date>` and `aum_<date>` column suffixes
in `instruments.csv` and `portfolios.csv`, and serialise to JSON without a
converter at spec 006. Parsing them to timestamps would buy nothing and
cost a `.strftime` at every boundary.

### Agent context

`CLAUDE.md` carries no `<!-- SPECKIT START -->` / `<!-- SPECKIT END -->`
markers — it is hand-authored and lists the read order for the project. No
managed section exists to update, so nothing is written to it. The
`after_plan` agent-context hook is optional and is declined for the same
reason: overwriting a hand-authored context file to insert a plan link the
constitution already implies is a net loss.

## Constitution Re-Check (post-design)

Re-evaluated after Phase 1. Still no violations. Two things the design
made *more* true than the pre-check assumed:

- **Article XI** — the design has no exposure list, no client list and no
  date list anywhere in `pipeline/`. The four exposure instrument ids that
  produce the spine figure live in the *test*, which is where the
  Definition of Done's grep explicitly permits them.
- **Article VII** — every returned frame has an explicit sort. The one
  place non-determinism could have entered is the distinct sector and
  sub-asset-class terms used for event matching; those are sorted before
  use rather than taken from a set.

## Time box

| Step | Module | Budget |
|---|---|---|
| 1 | `load.py` — Book, load_all, client_weights, snapshots | 40 min |
| 2 | `diff.py` — diff, attribution | 30 min |
| 3 | `events.py` — events_between, events_touching | 45 min |
| 4 | Tests, gate verification, commit and tag | included |

Overrun rule (Principle II): at the cap, close with a recorded assumption
rather than extending. Nothing in this spec is on the cut list — spec 000
is named in "never cut".
