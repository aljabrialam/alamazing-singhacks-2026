# Implementation — step by step

**Feature:** `001-divergence-engine`
Every module, in build order, with signatures, logic and the exact output
to check against. Figures come from `findings.md`.

**Rule for the whole file:** if your output doesn't match the "verify"
block, stop and fix it before moving on. Every number here was computed
from the real data.

---

## Schema reference

Keep this open. Column names are exact.

**`holdings.csv`** — 1,015 rows, the centre of gravity
```
snapshot_date, portfolio_id, client_id, instrument_id, instrument_name,
asset_class, sub_asset_class, sector, region, instrument_ccy,
quantity, price_local, market_value_local, portfolio_ccy,
market_value_base, market_value_usd, weight_pct,
avg_cost_local, cost_basis_base, unrealised_pnl_base, unrealised_pnl_pct,
lending_value_base, advance_rate_pct, liquidity_tier,
valuation_date, acquired_date
```

**`instruments.csv`**
```
instrument_id, instrument_name, asset_class, sub_asset_class, sector,
region, currency, liquidity_tier, underlying_reference,
sustainability_excluded, concentration_limit_applies,
price_2025-12-31, price_2026-02-27, price_2026-03-31,
price_2026-06-30, price_2026-08-26
```

**`portfolios.csv`** — `portfolio_id, client_id, mandate_code, base_currency, aum_<date>, …`
**`mandates.csv`** — `mandate_code, asset_class, min_pct, target_pct, max_pct, max_single_position_pct`
**`clients.csv`** — `client_id, client_name, age, life_stage, objectives, risk_profile, tax_domicile, …`
**`event_log.csv`** — `event_date, event_type, region, description, primary_transmission, severity`
**`market_context.csv`** — `snapshot_date, series_id, series_name, category, unit, value`
**`rm_notes.json`** — list of `{note_id, client_id, note_date, rm_id, rm_name, channel, note}`

### ⚠️ The trap that will cost you an hour

**`weight_pct` is per-portfolio, not per-client.** Clients with several
portfolios (CL-0017 Fong) will give you wrong numbers if you sum it.

Always recompute at client level:

```python
def client_weights(h, client_id, date):
    t = h[(h.client_id == client_id) & (h.snapshot_date == date)]
    total = t.market_value_usd.sum()
    return t.assign(w = t.market_value_usd / total * 100)
```

For CL-0019 (one portfolio) both give 42.13%. For CL-0017 they diverge —
and that difference is the whole point of D3.

### Snapshot handling — Principle XI

**Do not hardcode these.** Read them from the data:

```python
def snapshots(book):
    return sorted(book.holdings.snapshot_date.unique())

def latest(book):
    return snapshots(book)[-1]
```

The demo passes `date_now = latest(book)` and `date_then = snapshots(book)[1]`.
Positional, not literal — so the pipeline runs on any book with any dates.

For readability in this document only, the demo values are:

| Position | Date | What it marks |
|---|---|---|
| [0] | 2025-12-31 | Baseline |
| [1] | 2026-02-27 | Day before the conflict |
| [2] | 2026-03-31 | Strait closed |
| [3] | 2026-06-30 | Tech drawdown |
| [4] | 2026-08-26 | Today |

Verify before tagging g1:

```bash
grep -rn "CL-00\|SYN-\|2026-0\|BRENT" pipeline/
# expect nothing outside tests/
```

---

## Step 1 — `pipeline/load.py` · 40 min

### Write

```python
from dataclasses import dataclass, field
import pandas as pd, json

@dataclass
class Book:
    clients: pd.DataFrame
    portfolios: pd.DataFrame
    holdings: pd.DataFrame
    instruments: pd.DataFrame
    mandates: pd.DataFrame
    transactions: pd.DataFrame
    credit: pd.DataFrame
    commitments: pd.DataFrame
    cash_needs: pd.DataFrame
    market: pd.DataFrame
    events: pd.DataFrame
    notes: list
    imperfections: list = field(default_factory=list)

    def client(self, cid):     return self.clients[self.clients.client_id == cid].iloc[0]
    def notes_for(self, cid):  return [n for n in self.notes if n['client_id'] == cid]
    def holdings_at(self, cid, date):
        return self.holdings[(self.holdings.client_id == cid)
                           & (self.holdings.snapshot_date == date)]

def load_all(path="data/") -> Book:
    ...
```

### Logic

1. Read every CSV with `parse_dates` on all date columns.
2. `json.load` the notes.
3. Merge `instruments` into `holdings` on `instrument_id` to bring
   `underlying_reference`, `sustainability_excluded`,
   `concentration_limit_applies` onto every row. Suffix the collisions —
   `asset_class` exists in both.
4. Merge `portfolios[['portfolio_id','mandate_code']]` into `holdings`.
5. **Log imperfections, never drop rows.** Append a dict to
   `book.imperfections` for each of:
   - rows where `unrealised_pnl_pct` is null (there is at least one —
     Nordvind, CL-0003)
   - rows where `valuation_date != snapshot_date`
   - any `instrument_id` in holdings but not in instruments

### Verify

```python
b = load_all()
assert len(b.holdings) == 1015
assert len(b.clients)  == 20
assert len(b.portfolios) == 24
assert len(b.notes)  == 28
print(b.imperfections)          # non-empty — these feed S3
```

---

## Step 2 — `pipeline/diff.py` · 30 min

### Write

```python
def diff(book, client_id, date_a, date_b) -> pd.DataFrame:
    """Per instrument: value and weight at both dates, plus deltas."""

def attribution(book, client_id, date_a, date_b) -> pd.DataFrame:
    """Same, sorted by absolute value change. Who moved the portfolio."""
```

### Logic

Take client-level weights at both dates, outer-join on `instrument_id`
(positions appear and disappear — SYN-SP-0505 does not exist before June),
fill missing with 0, compute `d_value` and `d_weight`.

### Verify

```python
d = diff(b, 'CL-0019', '2026-02-27', '2026-08-26')
# SYN-SP-0505 appears with value_a = 0
# SYN-ST-0104 value_b ≈ 3,676,056
```

---

## Step 3 — the gate: reproduce 42.13% · 20 min

**Do not proceed until this prints.**

```python
EXPOSURE = ['SYN-EQ-0025','SYN-ST-0104','SYN-EQ-0008','SYN-SP-0505']
w = client_weights(b.holdings, 'CL-0019', TODAY)
print(w[w.instrument_id.isin(EXPOSURE)].w.sum())   # → 42.1343 or 42.1344
```

If your pipeline produces that from the raw files, everything after is
assembly.

---

## Step 4 — `pipeline/events.py` · 45 min

### Write

```python
def events_between(book, date_a, date_b) -> pd.DataFrame

def events_touching(book, client_id, date_a, date_b) -> pd.DataFrame:
    """Events whose primary_transmission matches the client's exposures."""
```

### Logic

`primary_transmission` is free text — *"Energy, LNG, shipping, Gulf credit,
airlines"*. Split on commas, lowercase, strip. Match against the client's
distinct `sector` and `sub_asset_class` values, also lowercased.

Keep it a keyword match. Do **not** ask a model which events are relevant —
`event_log.csv` is authoritative and matching must be reproducible.

### Verify

```python
e = events_touching(b, 'CL-0019', PRE_WAR, TODAY)
# must include 2026-03-04 (Strait closed) and 2026-08-05 (blockade)
```

---

## Step 5 — `pipeline/divergence/d3_hidden.py` · 60 min

**Build D3 first.** It carries the hero finding and the other detectors
reuse its look-through.

### Write

```python
def look_through(book, client_id, date) -> pd.DataFrame:
    """Adds a `theme` column. Structured products resolve to their
    underlying_reference rather than their stated asset_class."""

def detect(book, client_id) -> list[Finding]
```

### Logic

1. Client-level weights at `TODAY`.
2. For each row with a non-null `underlying_reference`, parse the names out
   of the text. SYN-SP-0505 reads:
   `"Worst-of basket: Pacific Orient Shipping / Global Energy Majors ADR / Bara Nusantara Energy"`
   Strip the prefix before `:`, split on `/`, strip whitespace.
3. Match those names against `instrument_name` of the client's other
   holdings — fuzzy is fine, substring on the first two words works here.
4. Two findings to emit:
   - **theme concentration** — group by theme (sector or resolved
     underlying), flag any theme over 25% of the client
   - **duplicate underlying** — the note references names the client
     already holds outright
5. **Set `compliance_clean = True`** when every mandate band is respected
   and no single position breaches `max_single_position_pct`. Check this
   explicitly; it is the strongest line in the pitch.

### Verify

| Client | Expected |
|---|---|
| CL-0019 | shipping+energy theme = **42.13%**, `compliance_clean = True`, duplicate underlying flags SYN-ST-0104 and SYN-EQ-0008 |
| CL-0014 | Golden Harbour = **29.46%** across SYN-FI-0207 (12.87), SYN-ST-0106 (9.54), SYN-SP-0503 (7.05) |

CL-0014's is the better technical demonstration — one name across three
different asset classes. CL-0019's is the better story.

---

## Step 6 — `pipeline/divergence/d1_said_vs_held.py` · 60 min

**This is the differentiator.** The only detector that needs a model.

### Write

```python
def extract_claims(client_row, notes) -> list[dict]:
    """One LLM call. Prose → testable claims."""

def detect(book, client_id) -> list[Finding]
```

### The prompt

```
You are reading a private banking client's stated objectives and their
relationship manager's meeting notes. Extract every claim the client has
made about what they want, refuse to do, or are worried about.

Return JSON only. No prose, no markdown fences.

[{"claim": "<what they said, in their terms>",
  "check":  "avoid_sector" | "avoid_region" | "reduce_risk" |
            "refuse_realise_loss" | "needs_liquidity_by" | "other",
  "target": "<sector, region, or date — or null>",
  "source": "<objectives | note_id>",
  "stated_on": "<YYYY-MM-DD or null>"}]

Rules:
- Only claims the client made. Not the RM's opinion.
- If the note records the RM's concern rather than the client's words,
  skip it.
- Quote their phrasing in `claim`.

OBJECTIVES: {objectives}
NOTES: {notes}
```

### Logic

The model produces claims. **Plain code tests them.** Never let the model
decide whether a claim is violated.

```python
if claim['check'] == 'avoid_sector':
    exposure = look_through(book, cid, TODAY)          # reuse D3
    hit = exposure[exposure.theme.str.contains(claim['target'], case=False)]
    if hit.w.sum() > 20:
        emit Finding(kind='D1', ...)
```

### Verify

CL-0019 objectives contain *"outside the Gulf region and outside the
shipping sector"*. Expect a claim with `check = avoid_sector`,
`target = shipping`, and a finding at 42.13%.

Also expect claims from N-025 and N-026.

### Fallback if the LLM is flaky

Hardcode the three clients' claims as a JSON fixture and note it honestly
in the README. The demo survives; the story is slightly weaker. Better
than a broken pipeline at 15:00.

---

## Step 7 — `pipeline/divergence/d2_mandate.py` · 45 min

### Write

```python
def detect(book, client_id) -> list[Finding]   # classification in the Finding
```

### Logic

1. Portfolio-level weights by `asset_class` (bands are per portfolio).
2. Join `mandates` on the portfolio's `mandate_code`.
3. Flag where `actual < min_pct` or `actual > max_pct`.
4. Flag single positions above `max_single_position_pct`.
5. **Classify** — this is the judgement the brief is testing:

```python
trades = transactions[(transactions.client_id == cid)
                    & (transactions.type.isin(['BUY','SUBSCRIPTION']))]

if portfolio_inception >= '2026-01-01' and trades.empty:
    cls = 'inherited'          # transferred in as it stood — nobody chose it
elif trades_into_breached_class.any():
    cls = 'client_directed'
else:
    cls = 'drift'
```

### Verify

| Client | Expected |
|---|---|
| CL-0003 | Equity **71.46%** vs 10–30; Fixed Income **9.15%** vs 45–75; single position 26.06%; class **`inherited`** (PF-0005 inception 2026-02-16) |
| CL-0014 | Equity **23.39%** vs 30–55, breached low; class `drift` |
| CL-0019 | **No breach.** Every band respected. |

The third row is not a null result — it is the finding. Make sure your
code can express "checked, nothing breached, and the risk is still there."

---

## Step 8 — `pipeline/divergence/d4_runway.py` · 40 min

### Logic

Liquid = `liquidity_tier` in `('Daily','Weekly')`. Illiquid and Monthly do
not count toward a near-dated need.

For each row of `planned_cash_needs` plus uncalled `commitments`: compare
the amount to liquid value at that horizon, and subtract anything pledged
in `credit_facilities`.

### Verify

- **CL-0003** — EUR 3.4m tax instalment before year end; cash 7.69% + fixed
  income 9.15% = **16.8% liquid** against a need of roughly 15% of the
  portfolio. Tight.
- **CL-0014** — HKD 60m by mid-2027; cash 5.80%, and 19.58% locked in the
  Mid-Levels apartment plus 7.05% in the accumulator, both Illiquid.

---

## Step 9 — `pipeline/divergence/d5_unanswered.py` · 25 min

Small. It is the emotional core of the demo.

### Logic

Scan notes for a question the client asked with no later note answering it.
Match on question markers — *"asked for a view"*, *"asked whether"*,
*"asked what"* — then check whether any subsequent note for that client
references the same subject.

For the demo, the honest short version is to detect the RM's own admission:
`"We have not modelled this"`, `"Have not yet replied"`, `"Unresolved"`.

### Verify

- **N-026, CL-0019, 2026-08-12** — *"He asked for a view on what happens if
  the Strait reopens and normalises. We have not modelled this."*
- Also catches **N-028, CL-0004** — *"Have not yet replied."*

---

## Step 10 — `pipeline/divergence/d6_scenario.py` · 40 min

Answers their middle requirement — *what could happen next*.

### Signature — Principle XI

```python
def detect(book, client_id, series_id, date_now, date_then) -> list[Finding]
```

The series and both dates are parameters. "What if the Strait reopens" is
one call; "what if rates fall" is the same function with `UST_10Y_PCT` and
two different dates. That is the answer to "would this work on other
data?" — demonstrated rather than asserted.

### Logic

1. Pull `series_id` from `market_context`. For the demo call that is
   `BRENT_USD_BBL`: **101.5** today, **72.4** at the pre-conflict snapshot.
2. For each holding in the affected theme, reprice to its `PRE_WAR`
   market value from the snapshot history.
3. For SYN-SP-0505 (issued June, no pre-war value) proxy off SYN-ST-0104's
   ratio and **say so in the finding's `unsure_about`**.
4. Sum the impact and express it as a share of the portfolio.
5. Add the second-order effect where `source_of_wealth` shares the theme.

### Verify

```
Shipping fund    2.86m → 2.43m   −0.43m
Pacific Orient   3.68m → 2.95m   −0.72m
Energy majors    2.88m → 2.34m   −0.54m
FCN Basket C     4.16m → 3.34m   −0.82m
                          total  −2.5m   = −7.8% of 32.2m
```

Second-order: source of wealth is *Gulf logistics, port services and marine
chartering*, and N-025 records his own view that charter rates stay
elevated while the Strait is unresolved. The same event hits both.

---

## Step 11 — `pipeline/brief.py` · 60 min

One LLM call per client. Build time only.

```python
def write_brief(client_row, findings, notes) -> dict:
    """Returns {paragraphs: [str], opening_line: str}"""
```

### The prompt

```
Write a briefing for Priscilla Ong, a private banking relationship manager,
about one of her clients. She reads it before a meeting.

Rules:
- Use ONLY the facts supplied below. Invent nothing.
- Reference events by their date and description from the event log only.
- Never use the word "recommend". Use "worth raising" or "you may want to
  check".
- Name the person and their situation, not just the numbers.
- Three or four short paragraphs.
- End with ONE sentence she could say aloud to open the conversation.
- If the evidence does not support a claim, leave it out.

CLIENT: {name}, {age}, {life_stage}. {source_of_wealth}.
OBJECTIVES: {objectives}
FINDINGS: {findings_json}
NOTES: {notes}
```

### Iterate until

The output reads like the brief's own worked example — a person, a number,
a cause, and something that makes waiting impossible. If it reads like a
risk report, tighten the prompt rather than editing the output by hand.

---

## Step 12 — `pipeline/build.py` · 20 min

```python
def build(path="data/") -> None:
    book = load_all(path)
    findings = []
    for cid in ['CL-0019','CL-0003','CL-0014']:
        for mod in (d1, d2, d3, d4, d5, d6):
            findings += mod.detect(book, cid)
    ranked = rank(findings)                     # LLM call, one
    briefs = {cid: write_brief(...) for cid in ...}
    json.dump({...}, open('web/public/findings.json','w'), indent=2)
```

Run the other 17 clients through D2 and D3 only — cheap, and it makes the
call list real rather than a mock of three.

### `tests/test_determinism.py`

```python
def test_findings_are_deterministic():
    a = build_findings(load_all("data/"))
    b = build_findings(load_all("data/"))
    assert a == b
```

Screenshot it passing. It goes in the README under "why you can trust it."

---

## Step 13 — the web app

Build **S2 first**. It is the demo.

```
web/app/page.tsx              S1 call list
web/app/client/[id]/page.tsx  S2 the brief   ← start here
web/app/uncertain/page.tsx    S3
```

Read `findings.json` with a plain `import` — it is static, no fetch, no
loading state.

Build against `design/mockup.html` literally. Tokens are in
`design/globals.css`; drop it in after `npx shadcn@latest init`.

### S2 must contain, in this order

1. Name, age, mandate, AUM
2. The objective, quoted
3. Three or four paragraphs of brief
4. **The mandate panel** — every band, and the verdict that nothing breaches
5. **The scenario panel** — what happens if the Strait reopens
6. The opening line, large
7. Keep / Not useful / Add a note
8. Evidence, always visible on desktop

Items 4 and 6 are the two things a judge remembers. Everything else is
quiet.

---

## Order of operations, condensed

```
load → diff → [GATE: 42.13%] → events → D3 → D1 → D2 → D4 → D5 → D6
     → brief → build → findings.json → S2 → S1 → S3 → deploy → rehearse
```

Never start step N+1 until step N's verify block passes.

---

## Float tolerance — read before writing any test

Sums over floats vary in the last decimal with summation order and pandas
version. The gate figure computed on a clean run is **42.1343** or
**42.1344** depending on how the division is ordered.

**Assert with tolerance, never equality.**

```python
import pytest

def test_lookthrough_cl0019(book):
    assert look_through_total(book, 'CL-0019') == pytest.approx(42.134, abs=0.001)
```

Applies to every integration assertion in Article VIII. An equality assert
on a float sum is a test that fails for a reason that has nothing to do
with the code.
