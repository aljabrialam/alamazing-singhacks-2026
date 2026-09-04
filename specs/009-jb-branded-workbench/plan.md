# Implementation Plan: Julius Bär Branded Workbench

**Branch**: `main` (spec dir `009-jb-branded-workbench`) | **Date**: 2026-09-05 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/009-jb-branded-workbench/spec.md`

## Summary

Re-skin the existing static workbench in Julius Bär's own visual language,
raise the type to projector scale, and add exactly one motion moment — four
exposure blocks merging into one bar on a button press. Presentation layer
only: no detector, no pipeline, no schema change, no new model call.

Six research questions are settled in [research.md](./research.md). Two of
them changed the specification rather than merely informing it: the mockup's
text-on-tint colours fail AA on the lighter two tints (2.25:1 and 2.83:1),
and the existing exposure component carries a hard-coded sentence that is
wrong on three of the five clients it renders for.

## Technical Context

**Language/Version**: TypeScript 5, React 19, Next.js 16.3.4 (App Router, Turbopack)

**Primary Dependencies**: Tailwind CSS v4 (`@theme inline`, no `tailwind.config.js`), shadcn/ui. **No animation library is added** — FR-016.

**Storage**: `web/public/findings.json`, committed. Read at build time only.

**Testing**: `pytest` for the pipeline (unchanged, 108 tests). For this spec: `next build` as the type and static-render gate, plus assertion scripts over the built HTML and the component sources for the checkable success criteria.

**Target Platform**: Static export served by Vercel. Chrome and Safari, projector at 1280×720 and above, down to 375px.

**Project Type**: Web application, frontend only. There is no backend.

**Performance Goals**: 25 prerendered pages, unchanged. No runtime data fetching. The merge is one class toggle, so it costs no measurable work.

**Constraints**: Static only — no `/api`, no server actions, no route handlers. Two new client components at most. No figure hard-coded in any component. AA contrast on every text-on-background pair. Code freeze 16:00 Saturday.

**Scale/Scope**: 20 clients, 25 pages, 9 components. This spec touches `globals.css`, `layout.tsx`, two page files and four components, and adds two.

## Constitution Check

Assessed against constitution v1.2.0, principle by principle. Named
explicitly because the gate requires it, and the two that are not clean are
listed first.

| Principle | Status | Note |
|---|---|---|
| **XIV. Design Is A Quarter Of The Score** | ⚠ **amendment required** | The principle pins the design system to `.alamazing/mockup.html`, which is byte-identical (MD5 `e072cb21`) to the mockup the design notes now demote to third preference. Resolved by amending to v1.3.0 — see below. **This is the one blocking item and it must be done before implementation, not after.** |
| **X. Honest Framing** | ⚠ **active risk this spec creates** | `mockup-jb.html` hard-codes "Four conversations worth having" and "Sixteen other clients have nothing that needs you today". Both are false here: three are briefed, seven have nothing worth raising, and no client has zero findings. Copying the mockup's copy would be a regression from a derived figure to a flattering one. FR-022 and SC-005 exist solely to prevent it. |
| I. Demo Primacy | ✅ | This spec *is* demo work — the framing a judge sees first and the one moment they remember. |
| II. Specification First, Time-Boxed | ✅ | specify → plan → tasks → implement, in order. |
| III. The Spine Rule | ✅ | No data path touched. |
| IV. Nothing Is Invented | ✅ | No logo is fabricated (FR-005). Brand colours are recorded as read from the challenge deck, with no claim that they are official. |
| V. The Model Reads and Writes, Never Counts | ✅ | No model call. Strengthened structurally: `ExposureMerge` receives formatted strings and holds no `Finding`, so it *cannot* compute. |
| VI. Evidence Over Assertion | ✅ | Evidence column stays visible without interaction (FR-025). |
| VII. Determinism | ✅ | `findings.json` unchanged; its hash is asserted before and after. |
| VIII. Evidence-Based Test Pyramid | ✅ | 108 pipeline tests must stay green untouched; new checks are assertions over built output, not screenshots. |
| IX. The Relationship Manager Decides | ✅ | Keep / not useful / add a note preserved on every finding (FR-027). No "recommend". |
| XI. Portable By Construction | ✅ | No client, instrument, sector, date or series name hard-coded (FR-023). The pin stagger uses a row **index**, an ordinal, not a figure. |
| XII. Vertical Slices Only | ✅ | Each user story ships a visible slice; P1 stories are independently demoable. |
| XIII. Declared Scope | ✅ | `mockup-demo.html` and any real brand asset are declared out of scope in the spec. |
| XV. Living Evidence | ⚠ **outstanding, not caused by this spec** | The repository is still **private**. Principle XV requires public from the first commit. The user has said they will flip it; it is recorded here because a gate item does not stop being outstanding by being someone else's action. |

### The Principle XIV amendment (blocking, do first)

Bump the constitution to **v1.3.0** and replace the pinned path:

> The design system exists in `design/` and is named in the mockup
> preference table at the head of `design/design-notes.md`. **The file that
> table marks as Default governs, and MUST be built against literally
> rather than improvised.** When the default changes, the design notes are
> the record of that change, and the specification acting on it MUST state
> which file it built against.

Rationale and the three rejected alternatives are in [research.md](./research.md) R1.
The intent of the principle — *build against the artefact, do not improvise*
— is unchanged; only the brittle path becomes a named role. The Sync Impact
Report, the version and the date are updated in the same edit, with the time
recorded, per the amendment procedure used for v1.2.0.

## Project Structure

### Documentation (this feature)

```
specs/009-jb-branded-workbench/
├── spec.md
├── plan.md              # this file
├── research.md          # R1–R6
├── data-model.md         # the props contracts for the two new components
├── quickstart.md         # how to verify each success criterion
├── checklists/
│   └── requirements.md
└── tasks.md              # written by /speckit.tasks
```

### Source code

```
web/
├── app/
│   ├── globals.css                 # MODIFY — tokens, projector type, .pin, noscript-safe
│   ├── layout.tsx                  # MODIFY — red topline, wordmark header, <noscript> pin style
│   ├── page.tsx                    # MODIFY — brand frame on the call list. COUNTS UNCHANGED.
│   └── client/[id]/page.tsx        # MODIFY — hero becomes a navy panel; one rgba literal re-pointed
├── components/
│   ├── exposure-figure.tsx         # MODIFY — server; computes, delegates the merge
│   ├── exposure-merge.tsx          # NEW — client; useState<boolean>, one className ternary
│   ├── band-reveal.tsx             # NEW — client; IntersectionObserver, one data attribute
│   ├── mandate-panel.tsx           # MODIFY — wrap bands in BandReveal; re-derive 3 rgba literals
│   ├── client-hero.tsx             # NEW — server; the navy hero panel
│   └── (scenario|explanation|collateral|evidence|decisions).tsx  # UNTOUCHED
└── public/
    └── {file,vercel,next,globe,window}.svg   # DELETE — unreferenced scaffold (SC-010)
```

**Structure Decision**: The existing frontend-only layout is kept exactly.
The one architectural decision is *where the client boundary falls*, and it
falls as low as possible in both new components: `ExposureMerge` receives
finished strings and a tint table, `BandReveal` receives server-rendered
children and no band data at all. Both are argued in research R3 and R4.

## Implementation phases

**Phase A — governance.** Amend Principle XIV to v1.3.0. Blocking: nothing
else starts until the constitution and the build agree about which mockup
governs.

**Phase B — tokens and type.** `globals.css`: the R2 migration table, the
R5 type scale, breakpoint 920px → 900px, `--on-e1..e4` from R6, `.pin`
base state, `--ease`. Re-derive the four `rgba()` literals in
`mandate-panel.tsx` and `client/[id]/page.tsx` that hard-code old palette
values.

**Phase C — brand frame.** `layout.tsx`: 3px red topline, wordmark header
with hairline divider and desk line, `<noscript>` pin fallback. Delete the
five scaffold SVGs.

**Phase D — the hero.** `client-hero.tsx`, wired into the brief page,
replacing the current first white band. Handles the no-look-through and
no-objective cases from the spec's edge cases.

**Phase E — the orchestrated moment.** `exposure-merge.tsx` plus the
`exposure-figure.tsx` split. Includes the two defect fixes from R3: the
derived sentence with no pronoun, and the gradient becoming a solid.

**Phase F — the band reveal.** `band-reveal.tsx`, wrapped around the band
rows in `mandate-panel.tsx`.

**Phase G — verification.** Every success criterion, with evidence. The
contrast sweep, the hard-coded-figure grep, the count check, the page count,
the 108 pipeline tests, `findings.json` hash unchanged before and after.

Phases B–F are ordered so that each leaves the build green and demoable.
If time runs out, the cut order is F, then E, then D — the brand frame and
the projector type (B and C) deliver most of the judged value and carry the
least risk.

## Complexity Tracking

| Item | Why it is worth it | Simpler alternative rejected because |
|---|---|---|
| Two new client components | The merge is the demo's centrepiece; the reveal draws the eye to the panel carrying the argument | Making `ExposureFigure` or `MandatePanel` wholly client-side would push `Finding` and formatting into the browser, where a figure could differ between server and client render |
| A `<noscript>` style block | Without it, pins start at `scaleY(0)` and the mandate panel — the element carrying the whole argument — renders with no markers when JS is unavailable | Arming the hidden state from JS flashes on the projector; `@media (scripting: enabled)` is the cleanest expression but too new to risk on a deadline |
| `--on-e1..e4` text tokens | Keeps the accessible pairing in one table beside the tints, so the merged state (all blocks → `--e3`) cannot silently become unreadable | A conditional in the component puts the accessibility decision where the next edit will overwrite it |

## Risks

- **The merge is the single point of demo failure.** It is one boolean and
  one class name precisely so there is nothing to debug at 15:00. It must be
  rehearsed with the reset, five times, on the machine that will present.
- **A token migration silently misses hard-coded colour literals.** Four are
  known from R2 and are in the plan; the verification phase greps for any
  remaining old hex value rather than trusting that the list was complete.
- **The mockup's false copy is genuinely tempting** because it is more
  quotable than the truth. FR-022 and SC-005 are the guard, and the check is
  automated rather than left to care.
