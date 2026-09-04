# Spec 009 — Phase 0 research

Six questions were settled before any file changed, and a seventh (R7) was
forced by the implementation. Each is recorded as decision, rationale,
alternatives — and where a measurement settled it, the measurement is here
rather than in a commit message.

---

## R1 — The Principle XIV conflict. Which mockup governs?

**The conflict, stated exactly.** Principle XIV reads:

> The design system exists at `.alamazing/mockup.html` and MUST be built
> against literally rather than improvised.

Verified by hash:

```
e072cb210dd174bb1662d0ef64b52ba7  .alamazing/mockup.html
e072cb210dd174bb1662d0ef64b52ba7  design/mockup-visual.html
3dc5a6981245f61b3d9210106c83ac54  design/mockup.html
```

So the file the constitution names is byte-identical to
`design/mockup-visual.html` — the artefact the rewritten `design-notes.md`
now lists **third**, behind `mockup-jb.html` (marked "Default") and
`mockup-demo.html`.

**Decision: amend Principle XIV to name the governing mockup by role rather
than by path, and record the amendment as v1.3.0.**

The operative sentence becomes:

> The design system exists in `design/` and is named in the mockup
> preference table at the head of `design/design-notes.md`. **The file that
> table marks as Default governs, and MUST be built against literally
> rather than improvised.** When the default changes, the design notes are
> the record of that change and the specification that acts on it MUST say
> which file it built against.

**Rationale.** The principle's intent is *build against the artefact, do not
improvise* — and that intent is entirely intact. What has changed is which
artefact is current, which is exactly the kind of fact a constitution should
not hard-code by path. Pinning the path made the principle brittle in a way
that has now bitten twice: spec 007 already had to resolve a disagreement
between two design documents (its research R1), and this is the second.

**Why this is not a licence to drift.** The amendment moves the pin from a
path to a *named role in a specific table*. There is still exactly one
governing file at any moment and it is still identified in writing. What it
stops doing is going stale silently.

**Alternatives considered.**

- *Build against `mockup-jb.html` and leave the constitution as it is.* The
  worse option by a distance, and the reason this research item exists at
  all. It would leave the governing document asserting something false
  about the build. "It is only a line in a document nobody greps" is how a
  checkable gate erodes.
- *Record a declared exception under Principle XIII instead of amending.*
  Legitimate, and rejected because an exception is the right instrument for
  a one-off departure, not for a permanent change of default. Using it here
  would mean the constitution keeps naming the wrong file forever with a
  footnote beside it.
- *Copy `mockup-jb.html` over `.alamazing/mockup.html` so the path becomes
  true again.* Rejected: it makes the constitution true by destroying the
  artefact spec 007 was built against, and the git history of that file
  would be the only remaining record. Falsifying the past to satisfy a
  present check is the wrong trade.

---

## R2 — Token migration map

Every token, old value to new, with the reason. Sourced from
`design/mockup-jb.html` `:root`.

| Token | Spec 007 value | Spec 009 value | Note |
|---|---|---|---|
| `--ground` | `#f0f1ed` sage | `#EAECEF` | Cool corporate grey. The sage read warm and independent; this reads institutional. |
| `--sheet` | `#ffffff` | `#FFFFFF` | Unchanged. |
| `--ink` | `#131b26` | `#101821` | Marginally deeper and cooler. |
| `--navy` | `#16325c` | `#14284B` | **The brand value.** Read from the challenge deck. |
| `--jb-deep` | — | `#0C1B33` | **New.** The darkest panel, for the opening line. |
| `--jb-red` | — | `#C8102E` | **New.** A rule only, never a fill. |
| `--crest` | `#a4343a` | `#C8102E` | Collapses onto the brand red. One urgency colour, not two. |
| `--safe` | `#2e6b52` | `#2E6B52` | Unchanged — the mockup keeps it. |
| `--muted-ink` | `#6e7681` | `#6B7280` | |
| `--hair` | `#e4e5e1` | `#E3E5E8` | Cooler, to match the new ground. |
| `--prose` | `#26303c` | `#26303C` | Unchanged. |
| `--e1` | `#c79355` | `#C9A876` | The ramp shifts from amber to a colder gold. |
| `--e2` | `#b58141` | `#B8945B` | |
| `--e3` | `#a0702f` | `#A37F46` | |
| `--e4` | `#8a5e23` | `#8A6934` | |
| `--radius` | `3px` | `2px` | Design notes: "Corners are 2–3px, not rounded." |
| `--ease` | — | `cubic-bezier(.22,.8,.28,1)` | **New.** The one easing curve, for the one moment. |

**`--crest` collapsing onto the brand red is the only judgement call here.**
The old crest `#A4343A` is a muted oxblood; the brand red `#C8102E` is
brighter and more saturated. Keeping both would put two urgency reds on one
page, which the design notes forbid by implication ("Urgency. **Once per
screen at most**"). Contrast is fine either way: `#C8102E` on white
measures **5.88:1**, and the pale flagline `#F2B8C0` on navy measures
**8.64:1**.

**Files that read these tokens** — established by grep, so the migration is
a closed set rather than a hunt:

- `web/app/globals.css` — the only definition site. `:root` and
  `@theme inline`.
- `web/components/mandate-panel.tsx` — `var(--crest)`, `var(--safe)`, and
  three `rgba()` literals that must be re-derived from the new values.
- `web/components/scenario-panel.tsx`, `explanation-panel.tsx`,
  `collateral-trajectory.tsx`, `evidence.tsx`, `decisions.tsx` — via
  Tailwind utility classes (`bg-navy`, `text-crest`, `bg-e4`), which
  re-point automatically once `@theme inline` is updated.
- `web/app/client/[id]/page.tsx` — one `rgba(199,147,85,.22)` literal, the
  objective's highlight, hard-coded from the **old** `--e1`. Must move to
  the new one.

That last item is the kind of thing a token migration misses: a colour
written as a literal inside a `shadow-[…]` arbitrary value, invisible to a
search for `--e1`.

---

## R3 — The merge, against a server component

`ExposureFigure` is a server component today and computes `members`,
`classes` and the combined figure inline. The merge needs client state.

**Decision: split at the smallest possible seam. `ExposureFigure` stays a
server component and does every computation; a new client component
`ExposureMerge` receives finished values and owns only a boolean.**

```
ExposureFigure            (server — unchanged role)
  ├─ sorts members, reads theme_pct, builds the merge sentence
  └─ <ExposureMerge blocks={…} combinedLabel={…} sentence={…} />
                          (client — "use client", one useState<boolean>)
```

`ExposureMerge` receives an array of `{ id, name, assetClass, pctLabel,
tint }` and two strings. **It receives no `Finding` and performs no
arithmetic**, so Principle V holds structurally rather than by discipline:
there is nothing in the component that could count even if someone tried.

**Rationale.** The alternative — marking `ExposureFigure` itself
`"use client"` — would push `Finding` and `pct()` into the client bundle
and put the sorting and the percentage formatting on the client, where a
figure could in principle differ between server and client render. Keeping
the seam below the computation makes that impossible.

**The reset is a requirement, not a nicety.** `useState(false)` with a
plain toggle satisfies FR-015 for free, which is the design note's whole
point about not needing a library.

**Two defects in the current component found while reading it**, both
fixed as part of this spec rather than left:

1. **Hard-coded prose asserting a figure and a gender.** Line 76 reads:

   > "The note's underlying is a worst-of basket on two names he already
   > owns. It is one bet, held four ways."

   "two" and "four" are typed constants, and "he" is a pronoun asserted
   about whichever client the page happens to be rendering. The sentence
   renders for every client carrying **both** a sector finding and a
   duplicate-underlying finding — five of them — and it is wrong on three:

   | Client | Name | Gender on file | Duplicated names | Positions | "two / four / he" |
   |---|---|---|---|---|---|
   | CL-0001 | Hartono Wijaya Kusuma | M | **one** | **2** | wrong ×2 |
   | CL-0002 | Ravi Chandrasekaran | M | **one** | **5** | wrong ×2 |
   | CL-0013 | Zhang Meiling | **F** | **one** | 4 | wrong ×2 |
   | CL-0014 | Lau Chi Ming | M | two | 4 | correct |
   | CL-0019 | Abdullah Al-Mansoori | M | two | 4 | correct |

   `clients.csv` has a `gender` column and it records CL-0013 as `F`, so
   the page tells a relationship manager that Zhang Meiling owns two names
   "he" already owns, when the figure is one and the pronoun is wrong. It
   was right for the hero client, which is why it survived review.

   Both counts are now derived — `duplicated_instrument_ids.length` and
   `members.length` — and **the sentence is rewritten with no pronoun at
   all** rather than by reading the gender column. Nothing in this sentence
   needs to know the client's gender, and a system that reaches for a
   pronoun it does not need is a system that will eventually get one wrong.

2. **A gradient where the mockup has a solid.** The combined bar is
   `bg-gradient-to-r from-e1 to-e4`. The mockup's merge bar is solid
   `--e4`. The gradient is also why nobody noticed the contrast problem in
   R6 — white on a gradient that starts at `--e1` is unreadable at its left
   end.

**Verified arithmetic for the hero.** The four members are 12.90, 11.41,
8.94, 8.88; `theme_pct` is 42.1343. The blocks and the combined bar
therefore agree because both trace to the same record, which is what
SC-003 asks for. The mockup's hand-typed 8.9 / 11.4 / 8.9 / 12.9 sum to
42.1 by luck of rounding, not by construction.

---

## R4 — The band reveal, without making the panel a client component

`MandatePanel` renders each band's pin at lines 74–82 as an absolutely
positioned div with an inline `left` and `background`.

**Decision: one client wrapper, `BandReveal`, that owns no band data at
all. It renders a `<div>` around server-rendered children and flips one
`data-` attribute when the group first enters the viewport. CSS descendant
selectors do the rest.**

```
MandatePanel               (server — unchanged)
  └─ <BandReveal>          (client — a ref, an observer, one attribute)
       └─ …server-rendered band rows, each pin carrying --pin-delay…
```

- Base: `.pin { transform: scaleY(0); transition: transform .45s var(--ease) var(--pin-delay, 0ms) }`
- Revealed: `[data-reveal="seen"] .pin { transform: scaleY(1) }`
- The stagger is `--pin-delay`, set inline per row from the row **index** —
  an ordinal, not a figure, so FR-021 is untouched.
- The observer calls `disconnect()` on first intersection, satisfying
  FR-019's "MUST NOT fire again".

**The progressive-enhancement problem, and why it needed solving.** Pins
starting at `scaleY(0)` means that with JavaScript unavailable they never
appear — the mandate panel, the element that carries the entire argument,
would render with no markers at all. The spec's own edge case demands they
be visible.

**Resolution: a `<noscript>` style block in the root layout** forcing
`.pin { transform: scaleY(1) !important }`. Chosen over the alternatives:

- *Arm the hidden state from JavaScript on mount.* Rejected — between
  hydration and the observer firing, pins would appear, vanish, then redraw.
  A flash on the panel that carries the argument, on a projector.
- *`@media (scripting: enabled)`.* Correct in principle and the cleanest
  expression of the idea, rejected on support risk for a Saturday deadline.
- *Reveal via React state only, no CSS.* Would require `MandatePanel` to be
  a client component, which is what this whole item exists to avoid.

`prefers-reduced-motion` is handled by the existing global rule, which
already collapses transition durations; the pins are additionally pinned to
`scaleY(1)` under that query so the final state is correct and not merely
fast, matching the mockup's own `@media (prefers-reduced-motion:reduce)`
block.

---

## R5 — Projector-scale type audit

Measured from the current build against the mockup's values.

| Element | Now | Desktop target | ≤900px target | Source |
|---|---|---|---|---|
| Client name | 26px / 32px md | **46px** | 32px | `.hero h1` |
| Headline exposure figure | — (none) | **80px** | 58px | `.heronum .big` |
| Opening line | 29px / 23px | **33px** | 24px | `.say blockquote` |
| Combined merge figure | 40px / 44px md | 36px | — | `.mergeinner .r` |
| Per-block percentage | 24px | 26px | — | `.blk .pc` |
| Section heading | 20px | 26px | — | `.sec h2` |
| Brief prose | 19px / 17.5px | 18.5px | 17.5px | `.sec .lede` |
| Objective quote | 17px / 19px md | 22px | — | `.quotebox .q` |
| Wordmark | 25px | 23px | — | `.wordmark .jb` |
| Band row label | 12.5px / 13.5px | 14px | — | `.brow .lab` |

Two notes on this table.

**The combined merge figure gets *smaller*** (44px → 36px). That looks
wrong for a "projector scale" specification and is right: the mockup moves
the biggest figure to the hero at 80px, so a second 44px figure lower down
competes with it. One headline number per screen.

**The breakpoint moves from 920px to 900px.** The old design notes said
920px; the mockup's media query is written at 900px. The mockup governs
(R1), so 900px it is — a 20px change that matters only because leaving both
values in the codebase would mean prose and the opening line stepping down
at different widths.

`.tabular` already exists as a utility and is applied in seven places. The
audit found figures **not** carrying it: the hero figure (new), the per-block
percentages (present), and the band `actual_pct` readout (present). FR-010
is satisfied by adding it to the new hero and merge elements.

---

## R6 — The text-on-tint contrast defect

Computed with the WCAG 2.1 relative-luminance formula against `#FFFFFF`
and against `--ink` `#101821`:

| Tint | Hex | White | Dark ink | Verdict |
|---|---|---|---|---|
| `--e1` | `#C9A876` | **2.25** | 7.96 | white fails AA **and** AA-large |
| `--e2` | `#B8945B` | **2.83** | 6.32 | white fails AA and AA-large |
| `--e3` | `#A37F46` | 3.70 | 4.84 | white is large-text-only |
| `--e4` | `#8A6934` | 5.06 | 3.53 | white passes |

`mockup-jb.html` sets `.blk{color:#fff}` on all four blocks. **On the
lightest tint that is 2.25:1 — worse than AA-large, on the graphic that
carries the demo's central argument.** The current build has the same
defect, inherited from the previous mockup.

**Decision: keep the tint ramp exactly as the mockup specifies and flip the
text colour per tint. Dark ink on `--e1`, `--e2`, `--e3`; white on `--e4`.**

Expressed as two Tailwind-visible tokens rather than a conditional in the
component:

```css
--on-e1: var(--ink);  --on-e2: var(--ink);
--on-e3: var(--ink);  --on-e4: #ffffff;
```

so the component reads `style={{ background: tint.bg, color: tint.fg }}`
from a single table and there is one place to change if the ramp moves.

**Rationale for keeping the ramp.** The obvious alternative is to darken
`--e1` and `--e2` until white clears 4.5:1. That requires pushing both
below roughly 0.175 relative luminance, which puts all four values within a
narrow dark band — and the four-tints-of-one-hue relationship is not
decoration here, it is the argument that four positions are one bet. Making
the ramp accessible by destroying its gradation would trade a real
communicative property for a compliance number.

**The merged state matters and is easy to miss.** The merge sets every
block to `--e3`, so the merged blocks take dark ink (4.84:1). Had the text
colour been decided per-block-index rather than per-tint, the merge would
have been the moment the graphic became unreadable — the one moment the
whole room is watching.

---

## What this research changed in the specification

- FR-031 and SC-011 were added for R6, with the measured table.
- FR-026 was corrected: `decisions.tsx` is already a client component, so
  the constraint is on **new** ones. The specification had asserted
  otherwise.
- The Governance note's "byte-identical in size" became "byte-identical",
  once hashed.

---

## R7 — Found during implementation: the class-swap trap

**This was not anticipated in Phase 0 and it would have broken the demo.**

The design notes prescribe the merge as "one CSS class toggle, `.merged` on
the container… a `className` ternary". Implemented literally in Tailwind,
that means a base utility beside a conditional one:

```jsx
<div className={`text-[11.5px] opacity-80 ${merged ? "opacity-0" : ""}`}>
```

**Conflicting Tailwind utilities resolve by declaration order in the
compiled stylesheet, not by the order they appear in the class string.**
Measured in this build's compiled CSS:

| Class | Byte offset | Consequence |
|---|---|---|
| `.opacity-0` | 19432 | declared first |
| `.opacity-80` | 19476 | **declared later — always wins** |
| `.opacity-100` | 19499 | declared later — always wins |

So `opacity-80` beats the conditional `opacity-0`: **the labels would never
fade.** And `opacity-100` beats `opacity-0` on the hint, so the hint would
be permanently visible instead of appearing on the merge. Two of the four
things the moment does would have silently not happened — while the source
read correctly. The same trap applies to the `gap-0`/`gap-2.5` and
`rounded-none`/`rounded-[2px]` pairs.

**Decision: every property the merge toggles is an inline style. Classes
are kept only for static properties.**

This departs from the letter of the design note's `className` ternary while
keeping its actual requirement — *one boolean, no library, nothing to debug
at 15:00*. There is still exactly one piece of state and no dependency
added. Inline styles have no cascade-order ambiguity, so the mechanism is
in fact *more* predictable than the prescribed one, which is the property
the design note was buying.

**Why the ordering is not merely fragile but unusable here.** It is not
fixable by reordering the class string, and it can change between builds as
the set of utilities in the project changes — a utility added by an
unrelated component can flip which declaration comes last. A demo mechanism
whose correctness depends on the alphabetical accident of the compiled
stylesheet is not a mechanism.

Conditional pairs where **both** branches supply a value and no base class
of the same family is present — `nothing ? "bg-hair" : "bg-crest"` in the
call list, `onDark ? "text-white/70" : "text-muted-foreground"` in the
decisions control — are unaffected: exactly one ever applies. Those were
swept and left alone.
