# Implementation Plan: Divergence Engine

**Feature:** `001-divergence-engine`
**Constitution:** `.specify/memory/constitution.md` v3.0.0
**Spec:** `spec.md`

---

## Architecture

**Python computes. TypeScript presents. They meet at a JSON file.**

```
data/*.csv  →  pipeline (Python)  →  findings.json  →  Next.js (static)
```

Three reasons this is right for solo-in-12-hours:

**Pandas does snapshot diffing in one line.** The core of this challenge is
comparing five dated snapshots. `groupby` + `pivot` + subtract. Rewriting
that in TypeScript is an hour you don't have, and the repo is already
Python.

**Nothing runs live at demo time.** The frontend reads a static JSON file.
No server, no API, no model call on stage. Antabay's locked SEL→TYO route
was right for the same reason — the demo cannot fail because there is
nothing running to fail.

**UX is 25%.** Next.js + Tailwind gives you a designed surface. Streamlit
does not, and half the room will use it.

**Determinism.** Model calls happen at build time, output is committed to
`findings.json`. Same output every run. The brief demands grounded,
defensible reasoning — a live LLM improvising in front of a judge is the
opposite of that.

---

## 2. Repo layout

```
alamazing/
├─ pipeline/
│  ├─ load.py            # all files → dataframes, joined
│  ├─ diff.py            # snapshot comparison
│  ├─ events.py          # event_log lookup + attribution
│  ├─ divergence/
│  │  ├─ d1_said_vs_held.py
│  │  ├─ d2_mandate.py
│  │  ├─ d3_hidden.py
│  │  └─ d4_runway.py
│  ├─ brief.py           # findings → prose memo (LLM, build-time)
│  └─ build.py           # orchestrates → web/public/findings.json
├─ data/                 # unzipped from the challenge
├─ web/
│  ├─ app/
│  │  ├─ page.tsx              # S1 call list
│  │  ├─ client/[id]/page.tsx  # S2 the brief
│  │  └─ uncertain/page.tsx    # S3 what we're unsure about
│  ├─ components/
│  │  ├─ call-list.tsx
│  │  ├─ brief-memo.tsx
│  │  ├─ evidence-drawer.tsx
│  │  └─ finding-actions.tsx   # accept / dismiss / note
│  └─ public/findings.json
└─ SPEC.md
```

---

## Pipeline stages

### Stage 1 — `load.py`

```python
def load_all(path="data/") -> Book:
    """Every file, typed, joined, indexed by client_id."""
```

Returns one object holding all dataframes plus a `clients()` iterator.
Parse dates properly. Do not silently drop rows — the brief says the data
contains deliberate real-world imperfections, and handling them
thoughtfully counts in your favour.

**Log every imperfection you find.** It feeds S3 and it is evidence of
judgement.

### Stage 2 — `diff.py`

```python
def diff(book, client_id, date_a, date_b) -> DataFrame:
    """Per-instrument: units, value, weight at both dates, and deltas."""

def attribution(book, client_id, date_a, date_b) -> DataFrame:
    """Which holdings drove the client-level change, ranked by contribution."""
```

Aggregate across **all** the client's portfolios.

### Stage 3 — `events.py`

```python
def events_between(book, date_a, date_b) -> DataFrame

def events_touching(book, client_id, date_a, date_b) -> DataFrame:
    """Events whose transmission channel matches the client's exposures."""
```

**`event_log.csv` is authoritative.** If the model's memory disagrees with
the file, the file wins. Never let an explanation cite an event that isn't
in it — that's the difference between defensible and merely plausible.

### Stage 4 — divergence detectors

Each returns a list of `Finding`:

```python
@dataclass
class Finding:
    client_id: str
    kind: str            # D1 | D2 | D3 | D4
    severity: int        # 1-5
    confidence: str      # high | medium | low
    headline: str        # one sentence, plain English
    detail: str          # the reasoning
    evidence: list       # source rows — file, row ids, values
    events: list         # event_log ids
    unsure_about: str    # what would change this answer, or ""
```

`evidence` and `unsure_about` are not optional. They are Technical &
Operational Feasibility (25%) and the honesty test respectively.

**D1 — said vs held** (`d1_said_vs_held.py`)

Read `rm_notes.json` per client. Extract stated positions: what they say
they want, refuse to do, are worried about, plan to do. Test each against
holdings and transactions.

```
"won't sell at a loss"     → unrealised losses + no realising trades
"wants to reduce risk"     → equity weight rose since the note
"worried about China"      → exposure via underlying_reference increased
"needs liquidity in 2027"  → nothing liquid maturing before then
```

This detector is the differentiator. Most teams won't open this file.

**D2 — mandate vs reality** (`d2_mandate.py`)

Current weights against `mandates.csv` bands. For every breach, classify:

- **Drift** — weights moved through market action, no trades
- **Client-directed** — `transactions.csv` shows the client bought into it

Same breach, opposite conversations. This distinction is judgement, and
the brief names it explicitly.

**D3 — hidden when split** (`d3_hidden.py`)

Two passes:

1. Aggregate all a client's portfolios. Concentration invisible in each
   individually, obvious combined.
2. Look through structured products via `underlying_reference`. A client
   who thinks they've diversified may hold the same underlying twice.

**D4 — plan vs runway** (`d4_runway.py`)

`planned_cash_needs.csv` + `commitments.csv` (uncalled capital) against
what's actually sellable by then. Factor `credit_facilities.csv` LTV
across snapshots — a falling portfolio raises LTV toward a margin call.

Private-market valuations lag a quarter. That's industry practice, not an
error. Don't flag it as one.

### Stage 5 — `brief.py`

Turn findings into the memo. **One LLM call per client, at build time.**

Input: the client's row, their notes, their findings with evidence and
events. Output: a written brief, in Priscilla's language.

Prompt constraints — these are load-bearing:

```
- Use only facts in the supplied evidence. Cite nothing else.
- Reference events only by their event_log id.
- Never say "recommend." Say "worth raising" or "you may want to check."
- Name the person, their age, their situation. Not just the numbers.
- End with one sentence she could actually open the conversation with.
- If the evidence doesn't support a claim, say so instead.
```

Their worked example is the target shape. Read it again before writing
this prompt.

### Stage 6 — `build.py`

Everything → `web/public/findings.json`. Committed. Deterministic.

---

## 5. Screens

### S1 — The Call List (`/`)

Twenty clients ranked. Each row: name, AUM, top finding headline, severity,
one sentence of *why now*.

Ranking must be defensible — show the factors, don't hide them behind a
score. Their menu ends with "who does she call first, and can you defend
the ranking?"

### S2 — The Brief (`/client/[id]`)

**The main screen. It is a document, not a dashboard.**

```
┌──────────────────────────────────────────────────┐
│  Chen Wei Ming · 71 · Retired · SGD 12.4m        │
│  Meeting Thursday                                 │
├──────────────────────────────────────────────────┤
│                                                   │
│  He told you in June he won't sell at a loss.    │
│  His bond portfolio is down USD 5.6m since        │
│  February, after yields rose following the        │
│  energy shock [EVT-2026-03-11].                   │
│                                                   │
│  He draws USD 1.1m a year. His longest bond       │
│  matures in 2045. Waiting for recovery is not     │
│  a plan he can outlive.                           │
│                                                   │
│  ─────────────────────────────────────────       │
│  Worth opening with:                              │
│  "You told me you didn't want to sell at a       │
│   loss. I want to show you what waiting costs."  │
│  ─────────────────────────────────────────       │
│                                                   │
│  [ Accept ]  [ Dismiss ]  [ Add note ]           │
│                                                   │
│  ▸ Evidence (14 rows, 2 events)                  │
└──────────────────────────────────────────────────┘
```

Prose in serif. Evidence drawer opens to the actual rows. Every claim
traces.

The three action buttons are Strategic Impact made visible — Priscilla
decides, the system proposes.

### S3 — What I'm Not Sure About (`/uncertain`)

Low-confidence findings, data imperfections found during load, and what
you'd check next. Explicitly rewarded, and nobody else will build it.

---
