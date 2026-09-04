# Implementation Plan: The Workbench

**Date**: 2026-09-05 | **Spec**: [spec.md](./spec.md) | **Gate**: G3

**Time box**: 150 minutes (run sheet step 15, 13:30 onward)

## Summary

Next.js App Router, three routes, one static JSON import. No server, no
API route, no runtime fetch — the file is imported at build time and the
whole app is static.

**S2 first.** The constitution requires it and the demo spends five of its
seven beats there. S1 and S3 are comparatively simple once S2's components
exist.

The design work is not decoration here: half the rubric is design and
presentation, and the mockup is specific enough to build against
literally rather than interpret.

## Technical Context

**Stack**: Next.js App Router + TypeScript + Tailwind + shadcn/ui, per the
constitution's Technology Standards. `card button sheet table separator
scroll-area`.

**Data**: `web/public/findings.json`, imported directly. No fetch, no
loading state — it is static and committed.

**Constraints**: No "recommend". Responsive at 920px, readable to 375px.
Serif for everything read, monospace only in evidence. No client id or
figure hardcoded in `web/`.

## Constitution Check

| Article | Status |
|---|---|
| I. Demo Primacy | **PASS** — this is the half of the rubric assessed from the screen. S2 built first, as required |
| VI. Evidence | **PASS** — FR-008: visible without interaction on desktop. Hiding it undercuts the trust story, which is why the notes make it a fixed column rather than a drawer |
| VII. Determinism | **PASS** — a static file, imported. Nothing to vary |
| IX. RM Decides | **PASS** — FR-009. Real keep/reject/annotate with a recorded reason, persisted locally, and the README says where it persists |
| X. Honest Framing | **PASS** — S3 exists for this; the masthead shows the snapshot date rather than today (R2); the actions' scope is stated rather than implied |
| XI. Portable | **PASS** — FR-015. Nothing about a client is in the source |
| XII. Vertical Slices | **PASS** — S2 renders end to end before S1 or S3 is started |
| XIII. Declared Scope | **PASS** — no auth, no database, no chat, no second app |
| XIV. Design Is A Quarter | **PASS** — built against the mockup literally, per the article's instruction |

**No violations.**

Two notes:

**Article X is why the masthead shows 26 August.** The temptation is
`new Date()`, which looks fresher. But the brief is *as at* the latest
snapshot, and a page that says "today" above August figures is a small
dishonesty that invites exactly the question you least want. See R2.

**Article IX is why the actions are real.** There is no server, so they
could only ever be local — and a disabled button that looks interactive is
worse than a working one that is scoped. Strategic Impact is assessed on
whether Priscilla retains control, which a working keep/reject
demonstrates and a mock does not. The scope goes in the README.

## Structure

```text
web/
├── app/
│   ├── layout.tsx            masthead, ground, fonts
│   ├── globals.css            from .alamazing/globals.css + mockup tokens
│   ├── page.tsx               S1 call list
│   ├── client/[id]/page.tsx   S2 the brief          <- FIRST
│   └── uncertain/page.tsx     S3 uncertainty
├── components/
│   ├── sheet-section.tsx      the paper primitive
│   ├── exposure-figure.tsx    four-into-one
│   ├── mandate-panel.tsx      bands + verdict       <- carries the argument
│   ├── scenario-panel.tsx
│   ├── opening-line.tsx       + actions
│   ├── evidence.tsx           column / bottom sheet
│   └── decisions.tsx          local-storage state
├── lib/
│   ├── findings.ts            typed access to the file
│   └── format.ts              money, percent, dates
└── public/findings.json       committed by spec 006
```

## Phase 0 — complete

Six questions — [research.md](./research.md).

| # | Finding |
|---|---|
| R1 | **The two design documents disagree on tokens.** The mockup governs where it specifies; the notes govern elsewhere. The run sheet identifies the visual mockup as the intended direction, not an alternative |
| R2 | The masthead date is the **snapshot date**, not today. Never `new Date()` |
| R3 | The four-into-one figure's data is already in the D3 finding's `members`. Render full instrument names, not the mockup's abbreviations — the screen and the evidence panel must agree |
| R4 | **The band track needs a scale the data does not give.** 0–100, so a 0–15 band renders narrow and a 40–65 band renders wide. Scaling each row to its own band would flatter the tight one |
| R5 | The nothing-today count is **derived at render time**, so the sentence cannot drift out of date |
| R6 | The actions are **real local state**, and the README says where they persist |

## Design decisions

**One static import, no fetch.** `import findings from "@/public/findings.json"`
makes the whole app static and the data type-checked. A fetch would add a
loading state to a file that ships with the page.

**The band track is 0–100.** R4. It is the one place the mockup left a
scale unspecified and the choice is visible on screen.

**Full instrument names.** R3.

**Two shadows on every sheet**, per the notes — that is what makes paper
look like paper rather than a card component.

**Boldness in exactly two places**: the mandate panel's tinted block and
the opening line's navy. Everything else quiet, as the notes insist.

## Time box

| Step | Work | Budget |
|---|---|---|
| 1 | Scaffold, tokens, layout, typed access | 25 min |
| 2 | **S2** — all eight sections | 70 min |
| 3 | S1 — call list | 25 min |
| 4 | S3 — uncertainty | 15 min |
| 5 | Responsive pass, build, checks | 15 min |
| | **Total** | **150 min** |

**Cut order** (run sheet): S3 at 15:00, S1 degraded to a static list at
16:00. **S2 and the mandate panel are never cut.**
