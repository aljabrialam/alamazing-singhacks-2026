# ALAMazing — Divergence Engine

Agent context. Read this first, then `.specify/memory/constitution.md`.

## What this is

SingHacks 2026, Julius Baer "Wealth Intelligence" challenge. Solo build,
~12 hours. An AI wealth intelligence layer that tells relationship manager
Priscilla Ong **which client to call first, what's wrong, and how to open
the conversation.**

Not a dashboard. The room is building dashboards.

## Read in this order

| File | Why |
|---|---|
| `alamazing-all-specs.md` | **The run sheet. Setup + all spec blocks, in order.** |
| `.specify/memory/constitution.md` | Governs every decision. Obey under time pressure. |
| `specs/001-divergence-engine/findings.md` | **The three clients with verified figures. Read this before writing code.** |
| `specs/001-divergence-engine/implementation.md` | **Step by step: every module, signatures, logic, expected output** |
| `specs/001-divergence-engine/spec.md` | Requirements, acceptance scenarios |
| `specs/001-divergence-engine/plan.md` | Architecture, pipeline stages |
| `specs/001-divergence-engine/tasks.md` | Ordered, timeboxed, with cut order |
| `design/design-notes.md` | Visual direction and component rules |
| `docs/demo-script.md` | The 3-minute pitch, beat by beat |

## The trap

`weight_pct` in `holdings.csv` is **per portfolio**, not per client. Sum it
across a client with several portfolios and the numbers are wrong. Always
recompute from `market_value_usd` at client level — see
`implementation.md` schema section.

## Architecture in one line

```
data/*.csv → pipeline (Python/pandas) → findings.json → Next.js (static)
```

Python computes. TypeScript presents. LLM calls happen at **build time**
and the output is committed, so the demo is deterministic and nothing runs
live on stage.

## Non-negotiables

- **The AI reads and writes. It never counts.** All arithmetic is pandas.
- **`event_log.csv` is authoritative.** If the model's memory disagrees
  with the file, the file wins. Cite events by date + description from the
  file only.
- **Every finding carries evidence.** Source file, row ids, values. A
  detector that cannot produce evidence returns nothing.
- **Never the word "recommend"** in RM-facing copy. Use "worth raising",
  "you may want to check".
- **Priscilla decides.** The system proposes. Keep / not useful / add a
  note on every finding.
- **Deterministic.** Same inputs, same findings. There is a test for this.

## The demo clients

| Client | The finding | Why it matters |
|---|---|---|
| **CL-0019 Abdullah Al-Mansoori** | 42.13% look-through in shipping+energy, against a stated objective of "outside the Gulf and outside shipping" | **Every mandate band is respected.** Existing controls see nothing. This is the hero. |
| CL-0003 Margarethe Voss-Brenner | 71.46% equity on a Conservative mandate, inherited February | Neither drift nor client-directed — a third class, `inherited` |
| CL-0014 Lau Chi Ming | 29.46% Golden Harbour across three asset classes | Accumulator doubles up as it falls; HKD 60m needed mid-2027 |

**Not CL-0012.** He is the brief's own worked example; every team will
demo him.

## Judging (4 × 25%)

Client-Centric Innovation · User Experience & Design · Technical &
Operational Feasibility · Strategic Impact.

**No technical-depth criterion exists.** Architecture for its own sake
earns nothing. Understanding earns everything. Design and presentation are
half the score.

## Stack

Python 3 + pandas for the pipeline. Next.js App Router + TypeScript +
Tailwind + shadcn/ui for the web. Responsive — no separate mobile app.
JSON files on disk, no database. Deploy to Vercel.

## Commands

```bash
# → web/public/findings.json. --series is required: the scenario is the
# question being asked, so it lives in the command, not in pipeline/.
python pipeline/build.py --data data/ \
  --clients CL-0019,CL-0003,CL-0014 --series BRENT_USD_BBL

pytest tests/test_determinism.py  # same inputs, same findings
cd web && npm run dev
```

Regenerating model output is explicit, never a side effect of the build.
`derived/claims.json`, `derived/briefs.json` and `derived/ranking.json`
are committed; the build reads them and makes **no** model call.

## Deadlines

Code freeze 16:00 Sat. Submit by 18:00 Sat — lateness is penalised.
