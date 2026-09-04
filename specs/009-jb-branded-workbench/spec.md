# Feature Specification: Julius Bär Branded Workbench

**Feature Branch**: `main` (spec directory `009-jb-branded-workbench`)

**Created**: 2026-09-05

**Status**: Draft

**Input**: Rebrand the existing static workbench to Julius Bär's own visual
language, raise the type to projector scale, and add one orchestrated motion
moment for the demo. Source of truth: the rewritten `design/design-notes.md`
and the new `design/mockup-jb.html`, which supersedes the mockup spec 007
built against.

---

## Why this specification exists

Spec 007 built the workbench against `mockup-visual.html`. That mockup is a
good artefact and the wrong one: it reads as a well-made independent product.
The rewritten design notes make the argument plainly —

> **This framing is itself an answer to "differentiates Julius Baer's digital
> offering"** — it reads as something already inside the bank rather than a
> startup pitching at it.

Two of the four judging criteria are User Experience and Design and Strategic
Impact. A workbench that looks like an internal Julius Bär tool answers both
at once, before a word is spoken. That is the whole of this specification's
value, and it is presentation-layer only: **no detector changes, no pipeline
changes, no change to the shape of `findings.json`.**

### The trap this specification must not fall into

`mockup-jb.html` is illustrative markup. Every figure in it was typed by
hand, and **two of its sentences are false against our own derived data**:

| Mockup says | Derived truth | Source |
|---|---|---|
| "Four conversations worth having" | **Three** clients carry a drafted brief | `meta.deep_clients` |
| "Sixteen other clients have nothing that needs you today" | **Zero** clients have no findings at all; **seven** have nothing worth raising | all 20 carry ≥1 finding |

The current `web/app/page.tsx` already derives seven / three / ten correctly
and carries a comment recording that block 9's "sixteen" was an estimate.
**Reproducing the mockup's copy would be a regression from an honest figure
to a flattering one, which is exactly what Principle X forbids and exactly
what is scored.** This specification therefore treats the mockup as a
*visual* reference and never as a source of figures.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — The room sees a Julius Bär tool (Priority: P1)

A judge looks up at the projected screen from three metres away, before the
presenter has finished the first sentence. They see a navy panel with a thin
red rule down its left edge, the wordmark "Julius Bär" beside the product
name in the header the way an internal tool carries it, near-square corners,
and a client name large enough to read from the back of the room.

**Why this priority**: It is the only story that pays off with zero
interaction and zero explanation, and it is the first thing that happens. If
nothing else in this specification ships, this one still moves two of the
four scoring criteria.

**Acceptance scenarios**

1. **Given** the brief page for the hero client, **When** it is rendered at
   1280px width, **Then** the page carries a 3px red rule across the very
   top, the header shows the wordmark and product name separated by a
   hairline divider with the desk line opposite, and the client identity
   block is a navy panel with a 3px red rule on its left edge.
2. **Given** any dark panel on any page, **When** it is rendered, **Then**
   it carries the red rule on its left edge and no element anywhere uses the
   brand red as a background fill.
3. **Given** the wordmark, **When** it is inspected, **Then** it is set text
   and not an image, and no logo file has been added to the repository.

### User Story 2 — The orchestrated moment lands (Priority: P1)

At the point in the pitch where the presenter says "look through the note",
they press one button. The four coloured blocks — an equity fund, a single
stock, another equity fund, a structured product, four different things on
every allocation report the bank produces — close their gaps, converge to a
single colour, drop their labels, and a single bar slides out beneath them
carrying one combined figure. The whole product, in two seconds, while the
presenter is still talking.

**Why this priority**: The design notes call it "the one orchestrated
moment" and it is the argument of the entire system compressed into one
gesture. It is equal-P1 with Story 1 because the demo is scored on delivery.

**Acceptance scenarios**

1. **Given** the exposure figure with its four blocks separated, **When**
   the reveal button is pressed, **Then** the gaps close, all four blocks
   take the same tint, the class and instrument labels fade, and a combined
   bar appears showing the same combined percentage the four blocks sum to.
2. **Given** the merged state, **When** the button is pressed a second time,
   **Then** every element returns to its original separated state and the
   button returns to its original label, so the moment can be rehearsed
   repeatedly and re-run if a take is fumbled.
3. **Given** a visitor who has asked their operating system to reduce
   motion, **When** they press the button, **Then** the merge still happens
   and is still comprehensible, but no transition animates.
4. **Given** the combined figure shown in the merged bar, **When** it is
   compared against the sum of the four block percentages, **Then** they
   agree, because both are read from the same derived record rather than
   typed.

### User Story 3 — It reads from three metres (Priority: P2)

The presenter tests the screen from three metres before Saturday. The client
name, the headline exposure figure and the opening line are all legible from
that distance. Figures do not jitter as they change because every numeral is
tabular.

**Why this priority**: P2 rather than P1 because the current sizes are
legible on a laptop and would survive a close-up demo — but the design notes
name the room as the constraint, not the laptop, and a figure nobody can
read is a figure nobody is persuaded by.

**Acceptance scenarios**

1. **Given** the brief page at desktop width, **When** type is measured,
   **Then** the client name renders at 46px, the headline exposure figure at
   80px, and the opening line at 33px.
2. **Given** the same page below the 900px breakpoint, **When** type is
   measured, **Then** the client name is 32px, the headline figure 58px and
   the opening line 24px, and no text overflows its container at 375px.
3. **Given** any element displaying a figure, **When** it is inspected,
   **Then** it uses tabular numerals.

### User Story 4 — The bands draw themselves once (Priority: P3)

Scrolling to the mandate panel, the five band markers draw in from nothing,
staggered, over about half a second. Then they stay. Nothing else on the
page moves, ever.

**Why this priority**: Lowest, because the panel is fully readable static
and this is a garnish. It earns its place only because the reveal draws the
eye to the panel that carries the argument — every band respected, and still
one concentrated bet.

**Acceptance scenarios**

1. **Given** the mandate panel is scrolled into view for the first time,
   **When** the reveal fires, **Then** each band marker animates in turn
   with a staggered delay and the observer stops watching thereafter.
2. **Given** the panel is scrolled away and back, **When** it re-enters
   view, **Then** nothing re-animates.
3. **Given** reduced motion is requested, **When** the panel is rendered,
   **Then** the markers are already in their final position with no
   transition.

### Edge Cases

- **A client with no look-through finding.** The hero panel has no headline
  figure to show. The panel must render with the identity, the objective and
  no figure rather than a zero, an em-dash or an empty gold slab.
- **A client with no quoted objective on file.** The gold-ruled quotebox
  must be absent rather than empty-with-quotemarks.
- **A look-through finding with fewer than four contributing positions.**
  The merge must work for two or three blocks; "four" is this client's
  number, not the component's.
- **A client with nothing worth raising.** Their page must still carry the
  brand frame and must say plainly that every band was checked and is
  respected, without a hero figure implying a concentration.
- **The unanswered-question flagline.** It is the one crest-coloured element
  on the hero. Where a client has no unanswered question it must be absent,
  and where it is present the text must carry the meaning so that colour
  alone never does.
- **Very long client names or objectives** at 46px must wrap rather than
  overflow or ellipsise.
- **JavaScript disabled or not yet hydrated.** The exposure blocks must
  render in their separated, fully-labelled, fully-readable state, and the
  band markers must be visible. The reveal is an enhancement; the argument
  survives without it.

---

## Requirements *(mandatory)*

### Brand and tokens

- **FR-001**: The palette MUST be migrated to the values read from the
  challenge deck: navy `#14284B`, a deeper navy `#0C1B33` for the darkest
  panel, brand red `#C8102E`, ground `#EAECEF`, ink `#101821`, hairline
  `#E3E5E8`, and the four exposure tints `#C9A876`, `#B8945B`, `#A37F46`,
  `#8A6934`.
- **FR-002**: The brand red MUST appear only as a rule or a hairline border
  and MUST NOT be used as a background fill for any element.
- **FR-003**: Every dark panel MUST carry a 3px red rule on its left edge,
  and the page MUST carry a 3px red rule across its top edge.
- **FR-004**: Corner radii MUST be 2–3px. No element may exceed 3px.
- **FR-005**: The header MUST carry a text wordmark reading "Julius Bär" in
  the reading face, a hairline divider, and the product name, with the desk
  line opposite. The wordmark MUST be set text. **No logo file may be added
  to the repository.** Verbatim from the design notes: *"If a real brand
  asset surfaces before Saturday, swap the wordmark — do not invent a logo.
  A text wordmark is honest; a fabricated mark is not."*
- **FR-006**: The four exposure tints MUST remain one hue in four values, so
  that four positions reading as one bet is legible as a colour relationship
  before any figure is read.

### Projector scale

- **FR-007**: The client name MUST render at 46px at desktop width and 32px
  below the 900px breakpoint.
- **FR-008**: The headline exposure figure MUST render at 80px at desktop
  width and 58px below the breakpoint.
- **FR-009**: The opening line MUST render at 33px at desktop width and 24px
  below the breakpoint.
- **FR-010**: Every element displaying a numeric figure MUST use tabular
  numerals so that figures do not shift horizontally when their digits
  change.

### The hero panel

- **FR-011**: The client identity block MUST become a navy panel carrying,
  in order: the unanswered-question flagline where one exists, the client
  name, the identity sub-line, the quoted objective in a gold-ruled
  quotebox, and the headline exposure figure with its caption.
- **FR-012**: The headline exposure figure MUST be positioned at the
  bottom-right of the panel at desktop width and MUST reflow to below the
  content at narrow widths without overlapping it.
- **FR-013**: Where a client has no look-through finding, the panel MUST
  omit the figure and its caption entirely rather than render a placeholder.

### The one orchestrated moment

- **FR-014**: The exposure blocks MUST merge on a single button press:
  container gaps close, all blocks take the deepest tint, per-block class
  and instrument labels fade out, and a combined bar appears beneath
  carrying the combined figure and a one-sentence statement of what the
  blocks have in common.
- **FR-015**: A second press MUST return every element to its initial state
  and restore the button's original label. The moment MUST be repeatable
  without reloading the page.
- **FR-016**: The merge MUST be implemented as a single state flag driving a
  class name. **No animation library may be added.** Verbatim from the
  design notes: *"one CSS class toggle, `.merged` on the container. In React
  that is `useState(false)` and a `className` ternary. No animation library,
  nothing to debug at 15:00."*
- **FR-017**: The button MUST have an accessible name describing what it
  does, MUST be reachable and operable by keyboard, and MUST show a visible
  focus ring.
- **FR-018**: Nothing else on the page may animate on load, on hover or on
  scroll, other than the band reveal of FR-019. Verbatim: *"Everything else
  is still. Motion used once is a reveal; motion used everywhere is noise."*

### The band reveal

- **FR-019**: The mandate band markers MUST draw in once, staggered, the
  first time the panel enters the viewport, after which the reveal MUST NOT
  fire again for the life of the page.
- **FR-020**: Where reduced motion is requested, the markers MUST render in
  their final state with no transition, and the merge of FR-014 MUST still
  change state without animating.

### Honesty of every figure

- **FR-021**: Every figure, percentage, count, currency amount, date and
  instrument name displayed MUST be derived from `findings.json`. **No
  component may contain a hard-coded figure**, including the illustrative
  values carried in `mockup-jb.html`.
- **FR-022**: The call-list heading and its summary sentence MUST continue
  to derive their counts from the data. The mockup's "Four conversations
  worth having" and "Sixteen other clients have nothing that needs you
  today" MUST NOT be reproduced, because both are false against this book:
  three clients carry a brief, seven have nothing worth raising, and no
  client has no findings at all.
- **FR-023**: No client identifier, instrument identifier, sector name, date
  or market series name may be hard-coded in any component.

### Preservation

- **FR-024**: The panels delivered by spec 008 — the explanation panel, the
  collateral trajectory, the tax band and the profile band — MUST render
  after this change with no loss of content.
- **FR-025**: The evidence column MUST remain visible without interaction at
  desktop width, because hiding it undercuts the trust argument.
- **FR-026**: The build MUST remain fully static: no request handlers, no
  server actions, no data fetching at runtime. The merge control and the
  band reveal MUST be the only **new** interactive components — the
  keep/not-useful/add-a-note control is already one and is unchanged — and
  both MUST receive already-computed values as properties rather than
  reading or deriving any figure themselves.
- **FR-027**: Copy MUST contain no instance of the word "recommend", and the
  keep / not useful / add-a-note controls MUST remain on every finding.

### Accessibility floor

- **FR-028**: Body copy MUST meet AA contrast on its background, including
  all text placed on the navy and deep-navy panels.
- **FR-029**: Colour MUST NOT carry meaning alone. The crest-coloured
  flagline MUST always carry its text.
- **FR-030**: The layout MUST work down to 375px with no horizontal
  scrolling and no clipped text.
- **FR-031**: Text on an exposure tint MUST take whichever of dark ink or
  white clears AA on that tint. **The mockup sets white on all four tints
  and that fails on the lighter two**, measured against `#FFFFFF`:

  | Tint | Hex | White on it | Dark ink on it | Required |
  |---|---|---|---|---|
  | `--e1` | `#C9A876` | 2.25 — fails AA and AA-large | 7.96 | dark ink |
  | `--e2` | `#B8945B` | 2.83 — fails AA | 6.32 | dark ink |
  | `--e3` | `#A37F46` | 3.70 — large text only | 4.84 | dark ink |
  | `--e4` | `#8A6934` | 5.06 | 3.53 | white |

  The tint ramp itself MUST NOT be darkened to make white work, because
  that would compress the four values into near-indistinguishability and
  the ramp is carrying the argument that four positions are one bet. The
  text colour flips instead. Since the merge takes every block to `--e3`,
  the merged state uses dark ink.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A viewer three metres from the projected screen can read the
  client name, the headline exposure figure and the opening line.
- **SC-002**: The orchestrated moment can be triggered, reset and
  re-triggered at least five times in succession without a page reload and
  without visual artefacts, so the presenter can rehearse it and recover
  from a fumbled take.
- **SC-003**: The combined figure revealed by the merge equals the sum of
  the individual block figures, verified against the derived record rather
  than against the mockup.
- **SC-004**: Searching every component for a literal percentage, currency
  amount, client identifier or instrument identifier returns nothing.
- **SC-005**: The call-list summary reports three briefed, seven with
  nothing to raise and ten carrying something worth watching — the derived
  figures — and not the mockup's four and sixteen.
- **SC-006**: Every page renders with the red top rule, the wordmark header,
  and a red rule on the left edge of each dark panel, at every breakpoint
  from 375px to 1440px.
- **SC-007**: With reduced motion requested, no element transitions, and the
  band markers and merge state are both fully legible.
- **SC-008**: The whole site remains prerendered with no runtime data
  fetching, and the page count is unchanged from before this specification.
- **SC-009**: All spec 008 panels render with the same content as before the
  rebrand.
- **SC-010**: No Julius Bär logo or brand image asset exists anywhere in the
  repository, and the wordmark resolves to set text. The five unused Next.js
  scaffold SVGs in `web/public/` are referenced by nothing and MUST be
  removed, so that the absence of a brand asset is unambiguous rather than
  something a reader has to check file by file.
- **SC-011**: Every text-on-tint pair in the exposure figure clears AA,
  measured, including in the merged state — so the merge cannot be the
  moment the design stops being readable.

---

## Assumptions

- **The mockup governs visual values except where it fails the
  accessibility floor.** Its text-on-tint colours do fail it, measured, and
  FR-031 departs from the mockup on that one point and records the numbers.
  Everywhere else its values are adopted literally.
- **The mockup governs visual values; the data governs every figure.** Where
  `mockup-jb.html` and `findings.json` disagree about a number, the derived
  data wins without exception. Where they disagree about a colour, a size or
  a spacing, the mockup wins.
- **The brand colours are read from the challenge deck, not from a brand
  guide.** They are recorded as read, and the design notes say so plainly.
  No claim is made that these are Julius Bär's official brand values.
- **"Julius Bär" is set as text deliberately.** A text wordmark is an
  honest statement about what we had access to; a fabricated mark would not
  be. This is the same principle as never inventing a figure, applied to a
  brand asset.
- **The 900px breakpoint from the mockup is adopted** in preference to the
  920px breakpoint in the older design notes, because the mockup is the
  governing artefact and its media query is written at 900px.
- **The four-block merge is a property of the component, not of the hero
  client.** It is specified for *n* contributing positions even though the
  demo client has exactly four.
- **The existing type faces are retained** — Newsreader for reading,
  Archivo for chrome, IBM Plex Mono confined to the evidence panel. The
  mockup uses the same two primary faces, so only sizes change.
- **No pipeline run is required.** `findings.json` is unchanged by this
  specification, so its committed content and provenance stay as they are.

---

## Governance note — a conflict this specification creates

Principle XIV of the constitution reads:

> The design system exists at `.alamazing/mockup.html` and MUST be built
> against literally rather than improvised.

`.alamazing/mockup.html` is byte-identical to `design/mockup-visual.html`
(both MD5 `e072cb21…`), the mockup spec 007 built against. The
rewritten `design/design-notes.md` now names `mockup-jb.html` as the
default and demotes the visual mockup to third preference.

**This specification therefore departs from the letter of Principle XIV.**
That is a governance change and not a detail to be absorbed silently: the
constitution pins the design system to a named file, and this specification
changes which file that is. The conflict MUST be resolved explicitly during
planning — either by amending Principle XIV to name the governing mockup by
role rather than by path, or by recording a declared, dated exception under
Principle XIII. It MUST NOT be resolved by building against a different file
and leaving the constitution stating otherwise.

---

## Out of scope

- Any change to a detector, to the pipeline, or to the schema of
  `findings.json`.
- Any new model call. The three briefs and the ranking stay exactly as
  committed, with their recorded provenance.
- `mockup-demo.html`, listed in the design notes but not supplied. Only
  `mockup-jb.html` is implemented.
- Any real Julius Bär brand asset. If one surfaces, swapping the wordmark is
  a later, separate change.
- Rewriting the demo script. Noted as a follow-up: its Q&A concession about
  the worst-of basket is now backwards, since spec 005 reports the recorded
  −2.5m as slightly optimistic against a strict worst-of reading.
