# START HERE

You are in the IDE. Everything below is decided. Build.

## First three commands

```bash
unzip singhacks-jb-wealth-intelligence.zip
pip install -r requirements.txt pandas
python starter/quickstart.py
```

## Your working file

**`RUN-SHEET.md`** — every command from `mkdir` to `git push`, twenty steps,
with verification at each one. Start there.

Then `alamazing-all-specs.md` for the nine paste blocks.

## Reference

**`alamazing-all-specs.md`** — top to bottom, SETUP step 1 onward.
Setup, the `/speckit.constitution` block, and specs 000–007 as paste-ready
`/speckit.specify` blocks. Same pattern as Antabay.

Everything below is what that file tells you to open.

## Read these three, nothing else

1. `CLAUDE.md` — your agent loads this automatically
2. `specs/001-divergence-engine/findings.md` — the three clients, verified figures
3. `specs/001-divergence-engine/implementation.md` — **step by step, module
   by module, with the exact numbers to check against**

`implementation.md` is the one you work from. `tasks.md` is the clock;
`implementation.md` is the how.

Everything else is reference. Open it when a step points you there.

## Tonight (before 21:00)

| # | Task | Done when |
|---|---|---|
| 1 | `pipeline/load.py` | All 12 files joined, indexed by client_id |
| 2 | `pipeline/diff.py` | Any client, any two snapshots, per-instrument delta |
| 3 | **Reproduce 42.13%** | Your code prints CL-0019 look-through = 42.134 |

**Task 3 is the gate.** If your pipeline produces that number from the raw
files, the rest is assembly. Do not build a screen tonight.

## The number to reproduce

```
CL-0019, snapshot 2026-08-26, sum of weight_pct for:
  SYN-EQ-0025  Asia Pacific Shipping and Logistics Fund   8.8849
  SYN-ST-0104  Pacific Orient Shipping Ltd               11.4113
  SYN-EQ-0008  Global Energy Majors Equity Fund           8.9364
  SYN-SP-0505  Fixed Coupon Note ref. Basket C           12.9018
                                                    = 42.134 ± 0.001
```

SYN-SP-0505 belongs in that set because its `underlying_reference` names
Pacific Orient Shipping and Global Energy Majors ADR — two names he already
holds outright. That look-through is the whole product.

## Saturday, in order

- 09:00–13:00 detectors D1, D2, D3, D4, D5, D6 → `findings.json`
- 13:00–16:00 three screens, S2 first
- **16:00 code freeze**
- 16:00–17:00 video, README
- 17:00–17:45 rehearse ×3
- **18:00 submit — late is penalised**

Cut order is in `specs/001-divergence-engine/tasks.md`. It is already
decided; do not relitigate it at 15:00.

## Six things you cannot get wrong

1. The AI reads and writes. **It never counts.** All arithmetic in pandas.
2. `event_log.csv` outranks the model. If they disagree, the file wins.
3. Every finding carries evidence — file, rows, values. No evidence, no finding.
4. Never the word "recommend". Use "worth raising", "you may want to check".
5. Priscilla decides. Keep / Not useful / Add a note on every finding.
6. Deterministic. Same inputs, same findings. There is a test.

## The pitch, one line

> Every bank checks the portfolio against the mandate. Nobody checks it
> against what the client actually **said** — so Abdullah's portfolio passes
> every control and is still the opposite of what he asked for.

## Design

Open `design/mockup.html` in a browser and build against it literally.
Tokens are in `design/globals.css` — drop it in after `npx shadcn@latest init`.
Rules in `design/design-notes.md`.
