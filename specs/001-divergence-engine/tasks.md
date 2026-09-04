# Tasks: Divergence Engine

**Feature:** `001-divergence-engine`
**Constitution:** `.specify/memory/constitution.md` v3.0.0
**Plan:** `plan.md`

---

> **This file is the clock.** For *how* to build each module — signatures,
> logic, and the exact figure to verify against — work from
> `implementation.md`.

## Task sequence

### Tonight — until 21:00

Reading is **done**. Clients chosen, figures verified — see `findings.md`.
Tonight is the data layer only.

| # | Task | Time |
|---|---|---|
| 1 | Unzip, `pip install -r requirements.txt`, run `starter/quickstart.py` | 10m |
| 2 | Skim `docs/DATA_DICTIONARY.md` for field definitions | 10m |
| 3 | Read `findings.md` — the three clients and their numbers | 10m |
| 4 | Reproduce the 42.13% figure for CL-0019 yourself | 20m |
| 5 | `load.py` | 40m |
| 6 | `diff.py` | 30m |
| 7 | Confirm offsite access after venue close | — |

**Do not write a screen tonight.** Task 4 matters: reproduce the headline
number yourself before building anything on top of it. If your pipeline
can produce 42.13% for CL-0019 from the raw files, the rest is assembly.

### Saturday 09:00–13:00 — G2

Clients and target figures are in `findings.md`. Each detector has a known
expected output — that is your test.

| # | Task | Expected result | Time |
|---|---|---|---|
| 8 | `events.py` — lookup + attribution | 2026-03-04 and 2026-08-05 attach to CL-0019 | 45m |
| 9 | `d3_hidden.py` — look-through via `underlying_reference` | CL-0019 = 42.13%; CL-0014 Golden Harbour = 29.46% | 60m |
| 10 | `d1_said_vs_held.py` — objective + notes vs holdings | CL-0019 objective says "outside shipping"; holds 42% | 60m |
| 11 | `d2_mandate.py` — drift / client-directed / **inherited** | CL-0003 equity 71.46% vs 10–30, class `inherited` | 45m |
| 12 | `d4_runway.py` — needs vs sellable | CL-0003 EUR 3.4m vs 16.8% liquid; CL-0014 HKD 60m | 40m |
| 13 | Unanswered-question detector (FR-017) | N-026 "We have not modelled this" | 25m |
| 13b | `d6_scenario.py` — reprice to a prior market state | CL-0019: −2.5m, −7.8% on Brent 101.5 → 72.4 | 40m |

**Task 13 is small and it is the emotional core of the demo.** Do not cut
it — it is what makes the pitch advisory rather than analytical.

**Task 13b closes their middle requirement.** Their goal is "what is
happening → what could happen next → what actions". Without D6 we answer
the first and third and skip the second. It is 40 minutes and it answers
the client's own question with a number.

**Compliance-clean flag.** D3 must mark a finding where every mandate band
is respected. That is the strongest line in the pitch, and it needs to be
visible on screen, not just said aloud.

### Saturday 13:00–16:30 — G3

| # | Task | Time |
|---|---|---|
| 13 | `brief.py` — prompt, iterate until the prose is good | 60m |
| 14 | `build.py` → `findings.json` | 20m |
| 15 | Next.js scaffold + tokens | 30m |
| 16 | S2 the brief — **build this first, it's the demo** | 60m |
| 16b | Mandate panel on S2 — bands respected, exposure still 42% | 25m |
| 17 | S1 call list | 40m |
| 18 | S3 uncertain | 25m |
| 19 | Evidence drawer + accept/dismiss | 30m |

**14:00 — second JB challenge drops.** Read it, 5 minutes. Your pipeline
is reusable. 60-minute box, only if the above is on track.

### Saturday 16:30–18:00 — G4

| # | Task |
|---|---|
| 20 | Deploy to Vercel, verify from phone |
| 21 | README: overview, architecture diagram, setup |
| 22 | Record fallback video |
| 23 | Rehearse ×3, timed |
| 24 | **Submit by 18:00 — lateness is penalised** |

---

## Cut order

When behind — decided now, not at 15:00.

| Cut | When |
|---|---|
| D4 | Behind at Sat 11:00 |
| S3 | Behind at Sat 15:00 |
| S1 → static list | Behind at Sat 16:00 |
| Third client | Behind at Sat 16:30 |
| **Never cut** | Abdullah, the mandate panel, evidence drawer, rehearsal | — |

One client, one brief, one evidence drawer, rehearsed three times, beats
everything else half-built.
