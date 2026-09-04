# Design notes

**Three mockups, in order of preference:**

| File | When |
|---|---|
| `mockup-jb.html` | **Default.** Julius Bär branded — navy, red rule, wordmark header |
| `mockup-demo.html` | Same interaction, neutral brand |
| `mockup-visual.html` | Same argument, static. Faster to build |
| `mockup.html` (quiet) | Prose-led fallback if behind at 15:00 |

## Julius Bär framing

The header carries the wordmark beside the product name, the way an
internal bank tool would. Dark panels take a 3px red rule on their left
edge; the page takes one across the top. Corners are 2–3px, not rounded.

**This framing is itself an answer to "differentiates Julius Baer's digital
offering"** — it reads as something already inside the bank rather than a
startup pitching at it.

**Colours are read from their challenge deck, not a brand guide.** Navy
`#14284B`, red `#C8102E`, white. If a real brand asset surfaces before
Saturday, swap the wordmark — **do not invent a logo**. A text wordmark is
honest; a fabricated mark is not.

## The one orchestrated moment

The four blocks merge into one bar when the button is pressed — at the
exact point in the pitch where you say "look through the note". That is
the whole product in two seconds, and it happens *while you are talking*.

Implementation: one CSS class toggle, `.merged` on the container. In React
that is `useState(false)` and a `className` ternary. No animation library,
nothing to debug at 15:00.

The button resets on second press so the demo can be rehearsed repeatedly
and re-run if the first take is fumbled.

**Everything else is still.** The band pins draw in once on scroll, and
that is it. Motion used once is a reveal; motion used everywhere is noise.

## Projector scale

46px client name · 82px headline figure · 34px opening line · tabular
numerals throughout so figures do not jitter. Test from three metres
before Saturday — the room is the constraint, not the laptop.


**Reference:** a printed advisory note from a Swiss private bank. Not a
dashboard, not a trading console.

An earlier draft went the console route — dense rules, monospace figures, a
tight grid. Wrong for the audience. Julius Baer's own positioning is
high-touch and relationship-driven; the artefact Priscilla actually wants is
something she can read in a lift before a meeting.

## Tokens

| Token | Hex | Role |
|---|---|---|
| ground | `#E7E9E5` | The desk. Soft sage-grey, deliberately not warm cream. |
| sheet | `#FFFFFF` | Paper. Pure white reads as printed, not as a UI panel. |
| ink | `#16202E` | Text |
| navy | `#16325C` | The one accent. Opening line, primary button. |
| crest | `#A4343A` | Urgency. **Once per screen at most.** |
| muted | `#6E7681` | Metadata |
| hair | `#E2E3DF` | Dividers, softer than a rule |

## Type

| Role | Face | Notes |
|---|---|---|
| Everything Priscilla reads | Newsreader | Findings, briefs, the opening line, and figures inside prose |
| Chrome | Archivo | Buttons, labels, metadata |
| Evidence only | IBM Plex Mono | File names and weights in the drawer |

**Monospace appears only in the evidence panel.** Elsewhere, figures are set
in the serif alongside the prose — a percentage in the middle of a sentence
is part of the sentence, not a data point.

No all-caps labels. No eyebrow text above headings. No `→` on buttons.

## Layout

White sheets floating on the ground, generous margins, one column of prose at
63ch. Sections are separated by italic captions in the ground colour rather
than by boxed headers — the captions read as annotations on a desk, which is
the metaphor.

**Two shadows, not one:** a 1px contact shadow plus a wide soft one. That is
what makes paper look like paper rather than a card component.

## Where the boldness goes

Two places, and only two.

**The mandate panel** gets a tinted block because it carries the argument —
every band respected, and still 42% one bet. It is the only boxed element in
the brief.

**The opening line** gets 27px navy serif and a lot of air. It is the last
thing on the page before the actions, and the thing a judge should remember.

Everything else is quiet on purpose.

## Components — shadcn/ui

```bash
npx shadcn@latest add card button sheet table separator scroll-area
```

| Element | Component | Note |
|---|---|---|
| Sheets | `card` | One per document. Never one per paragraph. |
| Call list rows | plain `div` grid | Not cards — a ranked list wants continuity |
| Actions | `button` | `default` for Keep, `outline` for the rest |
| Evidence (desktop) | fixed column | Always visible; hiding it undercuts the trust story |
| Evidence (mobile) | `sheet` | Slides up |
| Evidence rows | `table` | Unstyled, monospace weights |

**Not `badge` for urgency.** A short line of text in crest colour reads as a
note; a badge reads as a status chip.

## Mobile

Responsive, not a second app. Same codebase, two layouts. RMs work off
phones and tablets between meetings, which is the actual use case.

Breakpoint at 920px. Evidence moves from a fixed column to a bottom sheet.
The AUM column drops. Prose steps down to 17.5px. The opening line stays
large — it is the point on any screen.

## Copy

Never "recommend". "Worth raising", "you may want to check".

| Instead of | Write |
|---|---|
| Recommended action | Worth opening with |
| Dismiss | Not useful |
| Alerts (4) | Four conversations worth having this week |
| Confidence: LOW | What we would check |
| Submit | Keep for the meeting |

Sentence case throughout. Numbers spelled out where they read better in
prose — "seventy-one per cent equity against a thirty per cent ceiling" is a
sentence a banker says aloud.

## Accessibility floor

Focus rings visible. `prefers-reduced-motion` respected. Body copy meets AA
on white. Works to 375px. Colour never carries meaning alone — the crest
flag always has text beside it.
