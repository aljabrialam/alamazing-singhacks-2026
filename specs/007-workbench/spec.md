# Feature Specification: The Workbench

**Created**: 2026-09-05 · **Status**: Phase 0 complete

**Input**: Block 9 of `alamazing-all-specs.md`, pasted unmodified.

**Spec number**: 007 · **Gate**: G3 · **Depends on**: spec 006's
`findings.json`

Phase 0: [research.md](./research.md).

---

## Why this exists

Two of the four judging criteria are assessed entirely from what appears
on screen in three minutes. A correct pipeline with no rendered brief
scores zero on half the rubric (Principle I).

Three screens, reading one static file. No server, no API, no model call
at runtime — the whole point of committing `findings.json` was that
nothing runs on stage.

**S2 is built first.** It is the demo. The constitution says so and the
demo script spends five of its seven beats there.

---

## User Scenarios & Testing

### Story 1 — The brief (P1) · `/client/[id]` · BUILD FIRST

A document, not a dashboard. In the order block 9 gives:

1. Name, age, mandate, AUM
2. The client's objective, quoted
3. Three or four paragraphs of brief, in serif
4. **The mandate panel** — every band with its range, and the verdict
5. **The scenario panel** — what happens if the Strait reopens
6. The opening line, large, navy
7. Keep for the meeting / Not useful / Add a note
8. Evidence — always visible on desktop, a bottom sheet on mobile

**Why P1**: Items 4 and 6 are the two things a judge remembers.

**Acceptance Scenarios**:

1. **Given** a client id, **When** the page renders, **Then** it shows the
   eight sections in that order.
2. **Given** the hero client, **When** the mandate panel renders, **Then**
   **every** band appears with its permitted range and its actual value,
   and the verdict states that nothing breaches.
3. **Given** the mandate panel, **When** a band is read, **Then** the
   track is a 0–100 scale so a narrow band renders narrow.
4. **Given** the brief, **When** it renders, **Then** the paragraphs are
   serif and the opening line is large and navy.
5. **Given** the evidence, **When** viewed on desktop, **Then** it is
   visible without interaction.
6. **Given** the page, **When** the masthead renders, **Then** it shows
   the **snapshot date** from the file, never today's date.
7. **Given** a finding, **When** an action is taken, **Then** the decision
   persists across a reload, and rejection records a reason.

---

### Story 2 — The call list (P1) · `/`

Twenty clients ranked, one defensible sentence each, and an explicit
statement of how many have nothing today.

**Why P1**: The first and last screen of the demo.

**Acceptance Scenarios**:

1. **Given** the file, **When** the list renders, **Then** all twenty
   clients appear in ranked order with their justification.
2. **Given** the clients with no findings, **When** the list renders,
   **Then** the count is stated, **derived from the data** rather than
   written into the copy.
3. **Given** a row, **When** it is clicked, **Then** it opens that
   client's brief.
4. **Given** a client with nothing today, **When** the row renders,
   **Then** it is visibly quieter than one with a finding.

---

### Story 3 — Uncertainty (P1) · `/uncertain`

The data imperfections and the method limits, each with what we would
check.

**Why P1**: The brief asks for it explicitly, and it is a demo beat.

**Acceptance Scenarios**:

1. **Given** the file, **When** the page renders, **Then** data
   imperfections and method limits appear as **two separate sections**.
2. **Given** an imperfection, **When** it renders, **Then** it names the
   file, the row and what is wrong.
3. **Given** the private-market valuation lag, **When** it renders,
   **Then** it is described as industry practice rather than an error.

---

### Edge Cases

- **A client id not in the file.** A not-found page naming the id.
- **A client with no brief** (the seventeen shallow ones). The page shows
  the mandate panel and findings without a brief section, rather than an
  empty heading.
- **A client with no findings at all.** The page says so plainly.
- **A finding with no scenario.** The scenario panel is omitted, not
  rendered empty.
- **Local storage unavailable.** Actions still render; the decision is not
  persisted and that is not an error.
- **375px width.** Everything readable; the opening line stays large.

---

## Requirements

- **FR-001**: The app MUST read a single static JSON file and MUST make no
  network request at runtime beyond loading the page.
- **FR-002**: `/client/[id]` MUST render the eight sections in block 9's
  order.
- **FR-003**: The mandate panel MUST show **every** band with its
  permitted range and actual value, and state the verdict.
- **FR-004**: Band tracks MUST use a 0–100 scale so band widths are
  comparable.
- **FR-005**: The masthead MUST show the snapshot date from the file.
- **FR-006**: Everything the relationship manager reads MUST be set in the
  serif; chrome in the sans; monospace **only** in the evidence panel.
- **FR-007**: The opening line MUST be large and navy.
- **FR-008**: Evidence MUST be visible without interaction on desktop and
  a bottom sheet below 920px.
- **FR-009**: Every finding MUST offer keep, reject and annotate.
  Rejection MUST record a reason. Decisions MUST persist across reload.
- **FR-010**: The call list MUST show all clients ranked with their
  justification, and MUST state the count with nothing today, **derived**.
- **FR-011**: The uncertainty screen MUST keep data imperfections and
  method limits in separate sections.
- **FR-012**: Copy MUST NOT contain "recommend". Sentence case
  throughout. No all-caps labels, no arrows on buttons.
- **FR-013**: The layout MUST be responsive at 920px and readable to
  375px. No separate mobile application.
- **FR-014**: Focus rings MUST be visible, `prefers-reduced-motion`
  respected, and colour MUST NOT carry meaning alone.
- **FR-015**: No client id, figure or finding text may be hardcoded in
  the web source. Everything comes from the file.

---

## Success Criteria

- **SC-001**: `/client/CL-0019` renders all eight sections in order.
- **SC-002**: The mandate panel shows five bands and the verdict that
  nothing breaches.
- **SC-003**: **42.13%** appears on the hero client's page, read from the
  file.
- **SC-004**: The opening line renders at 27px or larger in navy.
- **SC-005**: `/` lists twenty clients ranked, and states the
  nothing-today count derived from the file.
- **SC-006**: `/uncertain` shows both sections, with the private-market
  lag described as industry practice.
- **SC-007**: A build of the web app succeeds with no type errors.
- **SC-008**: No occurrence of "recommend" in the web source or the
  rendered output.
- **SC-009**: The layout holds at 375px.
- **SC-010**: No client id or figure is hardcoded in `web/`.

---

## Assumptions

- The mockup governs where it specifies; the design notes govern
  elsewhere ([research.md](./research.md) R1).
- Actions persist to local storage, and the README says so plainly — there
  is no server by design (R6).
- The seventeen shallow clients have no brief, which is correct: a brief
  is worth writing where there is something to write about.

---

## Out of Scope

- Authentication, a database, a chat interface (Principle XIII).
- A separate mobile application.
- Charts without a finding attached (Principle I).
- Writing decisions to any external system.
