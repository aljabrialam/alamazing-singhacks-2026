# Spec 009 — component contracts

No data model changes. `findings.json` is untouched and its hash is
asserted unchanged by the verification phase.

What this document fixes is the **props contract of the two new client
components**, because that boundary is where Principle V is enforced
structurally rather than by discipline. A client component that cannot see a
`Finding` cannot compute one.

---

## `ExposureMerge` — the orchestrated moment

**File**: `web/components/exposure-merge.tsx` · `"use client"`

```ts
/** One position, already formatted for display. */
type MergeBlock = {
  id: string;          // React key only. Never rendered.
  assetClass: string;  // "Structured Products"
  name: string;        // full instrument name, as the evidence panel spells it
  pctLabel: string;    // "12.9" — ALREADY FORMATTED. Not a number.
  bg: string;          // css var reference, e.g. "var(--e1)"
  fg: string;          // the AA-clearing pairing for that bg — research R6
};

type ExposureMergeProps = {
  blocks: MergeBlock[];
  combinedLabel: string;   // "42.1%" — already formatted
  sentence: string;        // derived server-side, no pronoun. research R3
  mergedBg: string;        // "var(--e3)" — every block on merge
  mergedFg: string;        // the AA pairing for mergedBg
  barBg: string;           // "var(--e4)" — the combined bar
  barFg: string;
  buttonLabel: string;     // "Look through the note"
  resetLabel: string;      // "Reset"
  hint: string;            // "They were always the same colour…"
};
```

**Why `pctLabel` and `combinedLabel` are strings, not numbers.** If they
were numbers the component would have to format them, which is arithmetic
in a client component, and the two figures could then diverge from what the
server rendered. Passing formatted strings makes SC-003 — that the combined
figure equals the sum of the blocks — a property of the server that computed
both from one record, not something the client could break.

**State**: exactly `useState(false)`. No other state, no effect, no ref, no
timer. FR-016.

**Behaviour**

| Press | `merged` | Gaps | Block bg | Labels | Bar | Button |
|---|---|---|---|---|---|---|
| initial | `false` | open | per-block `bg` | visible | absent | `buttonLabel` |
| 1st | `true` | closed | `mergedBg` | faded | present | `resetLabel` |
| 2nd | `false` | open | per-block `bg` | visible | absent | `buttonLabel` |

Press 2 returns to the *initial* row exactly, which is FR-015 and what
makes the moment rehearsable.

**Accessibility**: a real `<button>`; accessible name is the visible label,
which describes the action; `aria-pressed={merged}`; focus ring from the
global `:focus-visible`. The combined bar is `aria-hidden` while collapsed
so a screen reader is not told about a figure that is not yet shown.

---

## `BandReveal` — the one scroll reveal

**File**: `web/components/band-reveal.tsx` · `"use client"`

```ts
type BandRevealProps = {
  children: React.ReactNode;  // server-rendered band rows. Opaque.
};
```

**That is the whole contract, and the point.** It receives no band, no
percentage, no verdict — only children it never inspects. The component
cannot misreport a figure because it never holds one.

**Mechanism**

1. A `ref` on a wrapping `<div data-reveal="armed">`.
2. One `IntersectionObserver` at `threshold: 0.4`.
3. On first intersection: set `data-reveal="seen"`, then `disconnect()`.
4. Stagger comes from `--pin-delay`, set inline per row by `MandatePanel`
   from the row **index** — an ordinal, not a figure (Principle XI).

CSS, in `globals.css`:

```css
.pin { transform: scaleY(0); transition: transform .45s var(--ease) var(--pin-delay, 0ms); }
[data-reveal="seen"] .pin { transform: scaleY(1); }
@media (prefers-reduced-motion: reduce) { .pin { transform: scaleY(1); transition: none; } }
```

and in `layout.tsx`, so the argument survives without JavaScript:

```html
<noscript><style>{`.pin{transform:scaleY(1)!important}`}</style></noscript>
```

---

## The tint table

One table, defined once, in `globals.css` and mirrored as a typed constant
where the component needs both halves. Values from research R2 and the
pairings from R6.

| Token | Background | Text token | Measured ratio |
|---|---|---|---|
| `--e1` | `#C9A876` | `--on-e1` = `--ink` | 7.96 |
| `--e2` | `#B8945B` | `--on-e2` = `--ink` | 6.32 |
| `--e3` | `#A37F46` | `--on-e3` = `--ink` | 4.84 |
| `--e4` | `#8A6934` | `--on-e4` = `#FFFFFF` | 5.06 |

The merged state uses `--e3` / `--on-e3`, so the merge lands at 4.84:1 and
clears AA. Had the pairing been chosen per block index instead of per tint,
the merge would have been the moment the graphic stopped being readable.

---

## `ClientHero` — the navy panel (server)

**File**: `web/components/client-hero.tsx` · server component

```ts
type ClientHeroProps = {
  client: ClientRecord;
  exposure?: Finding;    // D3 sector rule. Absent for some clients.
  question?: Finding;    // D5. Absent for most.
  snapshotDate: string;
};
```

A server component, so it may hold `Finding` and call `pct()`. Renders
nothing where a part is missing, per the spec's edge cases:

| Absent | Behaviour |
|---|---|
| `exposure` | no headline figure, no caption. **Not** a zero, not an em-dash. |
| `client.objectives` | no quotebox at all, rather than empty quote marks |
| `question` | no flagline — the one crest element on the panel |
