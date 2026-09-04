# Quickstart — Data Layer (spec 000)

**Spec**: [spec.md](./spec.md) · **Contract**: [contracts/data-layer.md](./contracts/data-layer.md)

Every acceptance criterion as a runnable block with its expected output.
Thirty seconds to re-verify the gate without reading code — which is the
point at 15:00 on Saturday when something downstream looks wrong and the
question is whether the data layer still holds.

## Prerequisites

```bash
cd ~/Documents/Projects/alamazing-singhacks-2026
source .venv/bin/activate
```

pandas and pytest only. No API key is needed — nothing in spec 000 calls a
model.

---

## 0 — The spine, from raw files

Run this **before** trusting anything else. It bypasses the pipeline
entirely and asks pandas the question directly, so it fails independently
of any bug in `load.py`.

```bash
python3 - <<'PY'
import pandas as pd
h = pd.read_csv('data/holdings.csv')
t = h[(h.client_id=='CL-0019') & (h.snapshot_date=='2026-08-26')]
w = t.market_value_usd / t.market_value_usd.sum() * 100
print(round(w[t.instrument_id.isin(
    ['SYN-EQ-0025','SYN-ST-0104','SYN-EQ-0008','SYN-SP-0505'])].sum(), 4))
PY
```

**Expected: `42.1343`** (or `42.1344` — the fourth decimal varies with
float summation order; both are correct). Anything else means the data or
the environment is wrong, and nothing downstream is worth debugging until
it prints.

---

## 1 — The book loads

```bash
python3 -c "
from pipeline.load import load_all
b = load_all()
assert len(b.holdings)==1015 and len(b.clients)==20
assert len(b.portfolios)==24 and len(b.notes)==28
print('imperfections:', len(b.imperfections))
print('OK')
"
```

**Expected:**
```
imperfections: 10
OK
```

Ten: five rows with no cost basis, five with a valuation lagging a quarter.
Non-empty is the acceptance criterion; the exact count is recorded so a
change is noticed.

---

## 2 — The joins landed

```bash
python3 -c "
from pipeline.load import load_all
b = load_all()
for c in ['underlying_reference','sustainability_excluded',
          'concentration_limit_applies','mandate_code',
          'asset_class','asset_class_inst']:
    assert c in b.holdings.columns, c
print('joined columns present, rows:', len(b.holdings))
"
```

**Expected:** `joined columns present, rows: 1015`

The row count is the assertion that matters. A merge that duplicates rows
inflates every weight in the book, and it inflates them *plausibly*.

---

## 3 — Client weights, and the trap

```bash
python3 -c "
from pipeline.load import load_all, client_weights, latest
b = load_all(); d = latest(b)
for cid in sorted(b.clients.client_id):
    w = client_weights(b, cid, d)
    assert abs(w.w.sum() - 100) < 1e-3, (cid, w.w.sum())
print('all 20 clients sum to 100% at', d)

cid = 'CL-0017'
raw = b.holdings_at(cid, d).weight_pct.sum()
rec = client_weights(b, cid, d).w.sum()
print(f'{cid}: raw weight_pct sum={raw:.4f}  recomputed={rec:.4f}')
"
```

**Expected:**
```
all 20 clients sum to 100% at 2026-08-26
CL-0017: raw weight_pct sum=299.9999  recomputed=100.0000
```

The second line is the trap, demonstrated rather than described. CL-0017
holds three portfolios. Summing the source column gives 300%.

---

## 4 — The spine, through the pipeline

The same figure as block 0, reached through `client_weights`. Two
independent paths to one recorded number.

```bash
python3 -c "
from pipeline.load import load_all, client_weights, latest
b = load_all()
w = client_weights(b, 'CL-0019', latest(b))
sel = ['SYN-EQ-0025','SYN-ST-0104','SYN-EQ-0008','SYN-SP-0505']
print(round(w[w.instrument_id.isin(sel)].w.sum(), 4))
"
```

**Expected: `42.1343`** (± 0.0001). Recorded in
`.alamazing/findings.md`, § Abdullah Al-Mansoori.

---

## 5 — What changed, including the position that did not exist

```bash
python3 -c "
from pipeline.load import load_all, snapshots
from pipeline.diff import diff, attribution
b = load_all(); s = snapshots(b)
d = diff(b, 'CL-0019', s[1], s[-1])
n = d[d.instrument_id=='SYN-SP-0505'].iloc[0]
print(f'SYN-SP-0505  value_a={n.value_a}  value_b={n.value_b:,.0f}')
a = attribution(b, 'CL-0019', s[1], s[-1])
print('largest mover:', a.iloc[0].instrument_id, f'{a.iloc[0].d_value:,.0f}')
"
```

**Expected:**
```
SYN-SP-0505  value_a=0.0  value_b=4,156,210
largest mover: SYN-SP-0505 4,156,210
```

`value_a` is `0.0`, not `NaN` and not a missing row. The note settled in
June; an inner join would have dropped the most important position in the
demo.

---

## 6 — Which events touched him

```bash
python3 -c "
from pipeline.load import load_all, snapshots
from pipeline.events import events_touching
b = load_all(); s = snapshots(b)
e = events_touching(b, 'CL-0019', s[1], s[-1])
print(e[['event_date','matched_on']].to_string(index=False))
assert '2026-03-04' in set(e.event_date)
assert '2026-08-05' in set(e.event_date)
print('both required events present')
"
```

**Expected** — seven events, including:
```
2026-03-04  energy      ← Strait of Hormuz effectively closed
2026-08-05  energy      ← naval blockade reimposed
both required events present
```

Both match on `energy`. `shipping` matches nothing — his shipping positions
are booked under sector `Industrials`. That limitation is recorded in
[research.md](./research.md) R5 rather than hidden; the required events are
returned regardless.

---

## 7 — Determinism

```bash
python3 -c "
from pipeline.load import load_all
import pandas as pd
a, b = load_all(), load_all()
pd.testing.assert_frame_equal(a.holdings, b.holdings)
assert a.imperfections == b.imperfections
print('two loads identical, including row order')
"
```

**Expected:** `two loads identical, including row order`

---

## 8 — The imperfections, named

```bash
python3 -c "
from pipeline.load import load_all
b = load_all()
for i in b.imperfections[:2]:
    print(i['kind'], i['client_id'], i['instrument_id'], i['snapshot_date'], '|', i['detail'])
print('...', len(b.imperfections), 'total')
"
```

**Expected** — the first entries are the missing cost basis on
CL-0003 / SYN-ST-0107, one per snapshot. That is Nordvind Industrial AB,
transferred in when Margarethe Voss-Brenner's husband died with no cost
basis attached. It matters because selling it is one of her options for the
EUR 3.4m tax instalment, and nobody can tell her the tax consequence.

The other five are CL-0002 / SYN-AL-0308, valued 2025-09-30 against every
later snapshot — a private-market mark lagging a quarter **by design**.
Recorded as a lag, not reported as an error.

---

## 9 — The full test suite

```bash
pytest tests/ -v
```

**Expected** — all green, with the integration assertion named:

```
tests/test_spine.py::test_spine_cl0019_from_pipeline PASSED
```

---

## 10 — Portability, before tagging G1

```bash
grep -rn "CL-00\|SYN-\|2026-0\|BRENT" pipeline/
```

**Expected: no output.** Client ids, instrument ids, dates and market
series are arguments, never literals (Principle XI). The four exposure
instrument ids that produce 42.13% live in `tests/`, which the Definition
of Done explicitly permits.

---

## If a block fails

| Block | Meaning |
|---|---|
| 0 | The data or the environment is wrong. Stop. Nothing downstream matters |
| 1 | A file is missing, or a reader is mis-parsing. Check the exception's filename |
| 2 | Row count ≠ 1015 means the merge duplicated. Check the join keys, not the weights |
| 3 | A client not summing to 100% means a second denominator crept in. This is the trap |
| 4 | Block 0 passing and block 4 failing isolates the bug to `client_weights` |
| 5 | `NaN` instead of `0.0` means the join is inner, or the fill is missing |
| 6 | Missing a required event means the term set or the split is wrong. Print `matched_on` |
| 7 | Non-determinism means a missing sort, or set iteration order |
| 10 | A literal reached `pipeline/`. Move it to a parameter before tagging |
