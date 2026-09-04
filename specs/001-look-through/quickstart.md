# Quickstart — Look-Through Concentration (spec 001)

**Spec**: [spec.md](./spec.md) · **Contract**: [contracts/look-through.md](./contracts/look-through.md)

Every acceptance figure as a runnable block with its verified output.
Thirty seconds to re-check the spec at 15:00 without reading code.

## Prerequisites

```bash
cd ~/Documents/Projects/alamazing-singhacks-2026
source .venv/bin/activate
```

No API key. Nothing in spec 001 calls a model.

---

## 1 — The hero figure

```bash
python3 -c "
from pipeline.load import load_all
from pipeline.divergence import d3_hidden as d3
b = load_all()
f = [x for x in d3.detect(b, 'CL-0019') if x['rule'] == 'sector'][0]
print(f\"{f['theme']}  {f['theme_pct']:.4f}%  clean={f['compliance_clean']}\")
print(sorted(m['instrument_id'] for m in f['members']))
"
```

**Expected:**
```
Energy + Industrials  42.1343%  clean=True
['SYN-EQ-0008', 'SYN-EQ-0025', 'SYN-SP-0505', 'SYN-ST-0104']
```

42.1343 against a recorded 42.13 (`.alamazing/findings.md` § 1). The theme
label is derived from the data — those are the sector values as the files
spell them.

---

## 2 — Every control passed, and still 42% one bet

```bash
python3 -c "
from pipeline.load import load_all
from pipeline.mandate import compliance_verdict
from pipeline.load import latest
b = load_all()
v = compliance_verdict(b, 'CL-0019', latest(b))
print('clean =', v['clean'])
for r in v['bands']:
    print(f\"  {r['asset_class']:<22}{r['actual_pct']:6.2f}  band {r['min_pct']:.0f}-{r['max_pct']:.0f}  {r['verdict']}\")
lp = v['largest_position']
print(f\"  largest {lp['instrument_id']} {lp['actual_pct']:.2f} vs limit {lp['limit_pct']:.0f}\")
"
```

**Expected:**
```
clean = True
  Alternatives            6.00  band 0-25  within
  Cash and Equivalents    7.45  band 2-15  within
  Equity                 57.97  band 40-65  within
  Fixed Income           15.67  band 15-40  within
  Structured Products    12.90  band 0-15  within
  largest SYN-EQ-0001 13.30 vs limit 15
```

All five match `.alamazing/findings.md` § 1 to two decimals. **This is the
argument**: nothing breaches, no existing control raises anything, and the
portfolio is still 42% one bet.

Note what is *absent*: BALG also defines a Commodities band and he holds
no commodities. Only held classes are reported — absence of a holding is
not a breach.

---

## 3 — The note doubles up on names he already owns

```bash
python3 -c "
from pipeline.load import load_all
from pipeline.divergence import d3_hidden as d3
b = load_all()
f = [x for x in d3.detect(b, 'CL-0019') if x['rule'] == 'duplicate_underlying'][0]
print('references:', f['referencing_instrument_id'])
print('duplicates:', f['duplicated_instrument_ids'])
print(f['detail'])
"
```

**Expected:**
```
references: SYN-SP-0505
duplicates: ['SYN-EQ-0008', 'SYN-ST-0104']
The product references Global Energy Majors ADR, Pacific Orient Shipping.
Those names are already held directly as Pacific Orient Shipping Ltd
(11.41%), Global Energy Majors Equity Fund (8.94%). Together with the
product itself that is 33.25% of the portfolio on the same underlying. On
the downside a worst-of basket pays on whichever underlying falls
furthest, so this adds to an existing position rather than spreading it —
worth raising as part of the same conversation.
```

Exactly the two instruments block 3 requires. Note the copy never calls it
diversification, and never uses the forbidden verb.

---

## 4 — How it got here

```bash
python3 -c "
from pipeline.load import load_all
from pipeline.divergence import d3_hidden as d3
b = load_all()
f = [x for x in d3.detect(b, 'CL-0019') if x['rule'] == 'sector'][0]
for p in f['trajectory']:
    print(f\"  {p['snapshot_date']}  {p['pct']:.2f}%\")
"
```

**Expected:**
```
  2025-12-31  29.41%
  2026-02-27  29.50%
  2026-03-31  34.08%
  2026-06-30  41.07%
  2026-08-26  42.13%
```

All five match `.alamazing/findings.md` § 1 Trajectory. Two causes,
visible rather than asserted: drift through the March energy spike
(29.50 → 34.08), then the step change when the note settled
(34.08 → 41.07).

---

## 5 — One name, three asset classes

```bash
python3 -c "
from pipeline.load import load_all
from pipeline.divergence import d3_hidden as d3
b = load_all()
f = [x for x in d3.detect(b, 'CL-0014') if x['rule'] == 'issuer'][0]
print(f\"{f['theme']}  {f['theme_pct']:.4f}%\")
for m in f['members']:
    print(f\"  {m['instrument_id']}  {m['w']:5.2f}%  {m['asset_class']}\")
"
```

**Expected:**
```
Golden Harbour Properties Ltd  29.4527%
  SYN-FI-0207  12.87%  Fixed Income
  SYN-ST-0106   9.54%  Equity
  SYN-SP-0503   7.05%  Structured Products
```

29.4527 against a recorded 29.46. **Three different booked asset
classes** — a third of a bond limit, a third of an equity limit, a third
of a structured-product limit, and no concentration check sees the whole
position.

The issuer name is recovered from the instrument name
(`"Accumulator ref. Golden Harbour Properties Ltd, 12M"`), because the
accumulator's `underlying_reference` carries only strike and knock-out
mechanics and names nobody. A parser following block 3 literally finds
nothing here.

---

## 6 — Selective, not fitted to three clients

```bash
python3 -c "
from pipeline.load import load_all
from pipeline.divergence import d3_hidden as d3
b = load_all()
for cid in sorted(b.clients.client_id):
    n = len(d3.detect(b, cid))
    if n: print(f'  {cid}  {n} findings')
"
```

**Expected** — six of twenty, including one from the reserve list:

```
  CL-0001  2 findings      <- 'the wealth NOT tied to the family coal mine'
  CL-0002  2 findings
  CL-0007  1 findings
  CL-0013  2 findings
  CL-0014  3 findings
  CL-0019  3 findings
```

**CL-0001 is the useful one.** `.alamazing/findings.md` § Reserve records
him as having told Priscilla the JB relationship is the wealth *not* tied
to the family coal mine, then subscribing a shipping and energy note in
April. The detector finds him unprompted. That is the strongest available
evidence it generalises rather than being fitted to CL-0019.

**CL-0007 gets one finding rather than two**, which is the threshold doing
real work: his gold sector theme is 24.04%, just under the 25% boundary,
so only the qualitative duplicate-underlying finding fires. A boundary
that nothing sits near is a boundary chosen to make three clients light
up; this one has a client just below it.

Fourteen of twenty produce nothing, correctly — they hold no structured
product, so there is nothing to look through.

---

## 7 — The threshold is a parameter

```bash
python3 -c "
from pipeline.load import load_all
from pipeline.divergence import d3_hidden as d3
b = load_all()
for t in (20.0, 25.0, 45.0):
    n = len([f for f in d3.detect(b,'CL-0019',threshold_pct=t)
             if f['rule'] in ('sector','issuer')])
    print(f'  threshold {t:5.1f}%  ->  {n} concentration findings')
"
```

**Expected:**
```
  threshold  20.0%  ->  2 concentration findings
  threshold  25.0%  ->  2 concentration findings
  threshold  45.0%  ->  0 concentration findings
```

"What about 20%?" is answered on stage by typing (Principle XI).

---

## 8 — The test suite

```bash
pytest tests/ -v
```

**Expected** — 29 green, including the three Article VIII assertions this
spec carries:

```
tests/test_lookthrough.py::test_lookthrough_cl0019       PASSED
tests/test_lookthrough.py::test_lookthrough_cl0014       PASSED
tests/test_lookthrough.py::test_compliance_clean_cl0019  PASSED
```

---

## 9 — Portability, before G2

```bash
grep -rn "CL-00\|SYN-\|2026-0\|BRENT" pipeline/
grep -rni "recommend" pipeline/
grep -rn "anthropic\|openai\|groq" pipeline/
```

**Expected: no output from any of the three.**

---

## If a block fails

| Block | Meaning |
|---|---|
| 1 | If the theme splits into `Energy` and `Industrials` separately, the sector union is not being applied — see research.md R5 |
| 2 | A Commodities breach means the check is iterating the mandate's rows rather than the client's holdings |
| 3 | Empty duplicates means the name match failed. Print `_match_key` on both sides; the ADR suffix is the usual cause |
| 4 | Leading zeros mean membership is being re-resolved at each date instead of fixed today — see the contract on `trajectory` |
| 5 | Missing Golden Harbour means the parser is reading only `underlying_reference` and not `instrument_name` |
| 6 | All 20 clients firing means the threshold or the match is too loose |
