# Tasks: The Workbench (spec 007)

**Prerequisites**: [spec.md](./spec.md), [plan.md](./plan.md), [research.md](./research.md) · spec 006's `findings.json` committed

**Gate**: G3 · **Time box**: 150 min

**Cut order**: S3 at 15:00, S1 degraded at 16:00. **S2 and the mandate
panel are never cut.**

---

## Phase 1 — Scaffold

- [x] T001 Scaffold Next.js in `web/` with TypeScript, Tailwind and the App Router, no `src/` directory
- [x] T002 Install the shadcn components the design notes name: card, button, sheet, table, separator, scroll-area
- [x] T003 Install `web/app/globals.css` from `.alamazing/globals.css`, with the mockup's token values where the two documents differ ([research.md](./research.md) R1)
- [x] T004 Write `web/lib/findings.ts` giving typed access to the committed file, imported statically — no fetch, no loading state (FR-001)
- [x] T005 Write `web/lib/format.ts` for money, percent and long dates
- [x] T006 Write `web/app/layout.tsx` with the masthead showing the **snapshot date from the file**, never `new Date()` (FR-005, R2)

## Phase 2 — S2, the brief (BUILD FIRST)

- [x] T007 Write `web/components/sheet-section.tsx` — the paper primitive, two shadows per the design notes
- [x] T008 Render section 1 in `web/app/client/[id]/page.tsx`: name, age, mandate, AUM
- [x] T009 Render section 2: the client's objective, quoted
- [x] T010 Render section 3: the brief paragraphs in serif at 19px, 63ch measure
- [x] T011 Write `web/components/exposure-figure.tsx` — the four-into-one, using the D3 finding's `members` with **full instrument names** (R3)
- [x] T012 Write `web/components/mandate-panel.tsx` showing **every** band with its range and actual value (FR-003). **This carries the argument**
- [x] T013 Draw each band on a **0–100 track** so a narrow band renders narrow (FR-004, R4)
- [x] T014 Render the verdict block in the mandate panel — the tinted block, one of the two places boldness is spent
- [x] T015 Write `web/components/scenario-panel.tsx` — the repricing, itemised, with the total and the second-order effect
- [x] T016 Write `web/components/opening-line.tsx` — 27px navy serif with air around it (FR-007)
- [x] T017 Write `web/components/decisions.tsx` — keep, reject with a recorded reason, annotate, persisted to local storage and surviving a reload (FR-009, R6)
- [x] T018 Write `web/components/evidence.tsx` — a fixed column on desktop, a bottom sheet below 920px, monospace **only** here (FR-006, FR-008)
- [x] T019 Handle a client with no brief and a client with no findings without rendering an empty heading
- [x] T020 Handle an unknown client id with a not-found page naming the id

## Phase 3 — S1, the call list

- [x] T021 Render all clients ranked with their justification in `web/app/page.tsx` (FR-010)
- [x] T022 State the nothing-today count, **derived from the file** rather than written into the copy (FR-010, R5). **Block 9 estimated sixteen; the derived figure is seven**, because the mandate and look-through detectors run over the whole book. Claiming thirteen "conversations worth having" would be the overstatement block 9 warns against, so the heading leads with the three briefed clients and describes the rest accurately
- [x] T023 Make a row with nothing today visibly quieter than one with a finding
- [x] T024 Link each row to that client's brief

## Phase 4 — S3, uncertainty

- [x] T025 Render data imperfections and method limits as **two separate sections** in `web/app/uncertain/page.tsx` (FR-011)
- [x] T026 Show each imperfection's file, row and what is wrong
- [x] T027 Describe the private-market valuation lag as industry practice, not an error

## Phase 5 — Definition of Done

- [x] T028 Responsive pass: evidence to a bottom sheet at 920px, AUM column dropped, prose to 17.5px, opening line stays large (FR-013)
- [x] T029 Accessibility floor: visible focus rings, `prefers-reduced-motion` respected, colour never carrying meaning alone (FR-014)
- [x] T030 Run the production build and confirm no type errors (SC-007)
- [x] T031 [P] Confirm no occurrence of "recommend" in `web/` source (SC-008, FR-012)
- [x] T032 [P] Confirm no client id or figure is hardcoded in `web/` (SC-010, FR-015)
- [x] T033 Confirm 42.13% renders on the hero client's page, read from the file (SC-003)
- [x] T034 Confirm the layout holds at 375px (SC-009)
- [x] T035 Run `pytest tests/ -v` and confirm the pipeline is still green — item 1
- [x] T036 Commit with the spec number — item 8

---

## Dependencies

```
Phase 1  T001 … T006   scaffold
  └─> Phase 2  T007 … T020   S2   (BUILD FIRST — Principle I)
        ├─> Phase 3  T021 … T024   S1
        └─> Phase 4  T025 … T027   S3
              └─> Phase 5  T028 … T036
```

S1 and S3 depend on S2 only because they reuse its components. Neither
blocks the other.

## Article VIII budget

**No new automated tests.** Article VIII is explicit: *"What is NOT
tested: UI rendering."* The checks here are the production build passing
with no type errors, and the grep gates. The pipeline's 88 tests must
stay green, which T035 confirms.

That is a deliberate reading, not a shortcut — a rendering test that
prevents no bug costs time the demo needs, and this track has no
technical-depth criterion to reward it.

## Strategy

**MVP is Phase 1 + Phase 2.** S2 is the demo. If everything else were
cut, a single rendered brief with the mandate panel and the opening line
would still carry the pitch.
