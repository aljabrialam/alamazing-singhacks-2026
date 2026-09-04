# Tasks: Julius Bär Branded Workbench

**Spec**: [spec.md](./spec.md) · **Plan**: [plan.md](./plan.md) · **Research**: [research.md](./research.md) · **Contracts**: [data-model.md](./data-model.md) · **Verification**: [quickstart.md](./quickstart.md)

**Total**: 41 tasks (2 already done) · **Estimated**: 3h10m · **Freeze**: 16:00 Saturday

Grouped by the plan's phases A–G. Story labels map to spec.md:
**US1** brand frame · **US2** the orchestrated moment · **US3** projector
scale · **US4** the band reveal.

---

## Phase A — Governance (blocking) · 10m · DONE

Nothing else could start until the constitution and the build agreed about
which mockup governs.

- [x] T001 Amend Principle XIV in `.specify/memory/constitution.md` to name the governing mockup by role rather than by path, per research.md R1
- [x] T002 Update the Sync Impact Report, bump to v1.3.0, and change the version and date fields in the same edit, recording the time (01:48 SGT, Saturday 5 September) per the amendment procedure

---

## Phase B — Tokens and type · 35m

Foundational. Every later phase depends on these tokens existing.

- [x] T003 Replace the `:root` palette in `web/app/globals.css` with the research.md R2 migration table — `--ground` `#EAECEF`, `--sheet` `#FFFFFF`, `--ink` `#101821`, `--navy` `#14284B`, `--jb-deep` `#0C1B33`, `--jb-red` `#C8102E`, `--crest` collapsed onto `#C8102E`, `--safe` `#2E6B52`, `--muted-ink` `#6B7280`, `--hair` `#E3E5E8`, `--prose` `#26303C`, `--e1..e4` `#C9A876`/`#B8945B`/`#A37F46`/`#8A6934`
- [x] T004 Set `--radius` to `2px` and add `--ease: cubic-bezier(.22,.8,.28,1)` in `web/app/globals.css`
- [x] T005 Add the four text-on-tint tokens `--on-e1..--on-e4` to `:root` in `web/app/globals.css` per research.md R6, with the measured ratios recorded as a comment beside them
- [x] T006 Expose `--color-jb-deep`, `--color-jb-red` and `--color-on-e1..e4` through `@theme inline` in `web/app/globals.css` so Tailwind utilities resolve them
- [x] T007 [US3] Apply the research.md R5 type scale in `web/app/globals.css` — add `.hero-name` 46px, `.hero-figure` 80px, raise `.opening-line` to 33px, and add `.tabular` to the new figure classes
- [x] T008 [US3] Move the responsive breakpoint from 920px to 900px in `web/app/globals.css` and set the small-screen values — `.hero-name` 32px, `.hero-figure` 58px, `.opening-line` 24px, `.prose-brief p` 17.5px
- [x] T009 [US4] Add the `.pin` base state, the `[data-reveal="seen"] .pin` rule and the `prefers-reduced-motion` override to `web/app/globals.css` per data-model.md
- [x] T010 Re-derive the three `rgba()` colour literals in `web/components/mandate-panel.tsx` from the new `--crest` and `--safe` values
- [x] T011 Re-point the `shadow-[inset_0_-8px_0_rgba(199,147,85,.22)]` objective highlight in `web/app/client/[id]/page.tsx` to the new `--e1` — the literal a search for `--e1` cannot find (research.md R2)

**Checkpoint** — `cd web && npm run build` green, 25 pages. Run quickstart §6 (`grep` for old palette values) and expect no output.

---

## Phase C — Brand frame · 25m · US1

- [x] T012 [US1] Add the 3px `--jb-red` topline above the page container in `web/app/layout.tsx`
- [x] T013 [US1] Replace the "Divergence Engine" header in `web/app/layout.tsx` with the wordmark bar — "Julius Bär" in `--font-read` navy, a hairline divider, the product name, and the desk line (`rm_name`, desk, `longDate(snapshot_date)`) opposite. **Set text only; no image, no logo file** (FR-005)
- [x] T014 [US1] Add the `<noscript>` style block forcing `.pin{transform:scaleY(1)!important}` to `web/app/layout.tsx` per research.md R4, so the mandate panel's markers survive without JavaScript
- [x] T015 [US1] Apply the 3px red left rule to the opening-line panel in `web/app/client/[id]/page.tsx` and switch its background to `--jb-deep`
- [x] T016 [US1] Delete the five unreferenced Next.js scaffold SVGs from `web/public/` (`file`, `vercel`, `next`, `globe`, `window`) per SC-010
- [x] T017 [US1] Apply the brand frame to the call list in `web/app/page.tsx`. **The derived counts and their explanatory comment MUST NOT change** — FR-022, and the mockup's "four"/"sixteen" must not appear

**Checkpoint** — quickstart §3 (`grep -niE 'sixteen|four conversations'`) returns nothing, and §5 confirms no image and no brand asset.

---

## Phase D — The hero panel · 30m · US1 + US3

- [x] T018 [US1] Create `web/components/client-hero.tsx` as a server component with the props contract in data-model.md — navy panel, red left rule, flagline, `.hero-name`, sub-line, gold-ruled quotebox, and the headline figure bottom-right
- [x] T019 [US1] Handle the three absent cases in `web/components/client-hero.tsx` — no `exposure` renders no figure and no caption (not a zero, not an em-dash), no `objectives` renders no quotebox, no `question` renders no flagline
- [x] T020 [US3] Position the headline figure absolute bottom-right at desktop in `web/components/client-hero.tsx` and reflow it below the content under 900px without overlap, per the mockup's `@media` block
- [x] T021 [US1] Wire `ClientHero` into `web/app/client/[id]/page.tsx`, replacing the current first white `<Band>`, keeping the objective sentence and its source-of-wealth lead-in

**Checkpoint** — the hero renders for all 20 clients. Spot-check one client with no D3 sector finding to confirm no empty gold slab.

---

## Phase E — The orchestrated moment · 40m · US2

The demo's centrepiece and its single point of failure.

- [x] T022 [US2] Create `web/components/exposure-merge.tsx` as a client component implementing the `ExposureMergeProps` contract in data-model.md — exactly `useState(false)`, one `className` ternary, no effect, no ref, no timer, **no animation library** (FR-016)
- [x] T023 [US2] Implement the reset in `web/components/exposure-merge.tsx` so a second press returns every element to the initial row of the data-model.md behaviour table and restores the button label (FR-015)
- [x] T024 [US2] Give the button in `web/components/exposure-merge.tsx` its visible label as accessible name plus `aria-pressed`, and mark the collapsed combined bar `aria-hidden` so a screen reader is not told about a figure not yet shown (FR-017)
- [x] T025 [US2] Split `web/components/exposure-figure.tsx` so it stays a server component, sorts members, reads `theme_pct`, builds the tint/text pairs from the data-model.md table, and passes **formatted strings** to `ExposureMerge` — it must pass no `Finding` and no number
- [x] T026 [US2] Fix the hard-coded sentence in `web/components/exposure-figure.tsx` per research.md R3 — derive the duplicated-name count from `duplicated_instrument_ids.length` and the position count from `members.length`, and **write it with no pronoun**. It is currently wrong on three of the five clients it renders for, including asserting "he" about a client recorded `F`
- [x] T027 [US2] Replace the `bg-gradient-to-r from-e1 to-e4` combined bar in `web/components/exposure-figure.tsx` with solid `--e4` and `--on-e4`, per the mockup and research.md R6
- [x] T028 [US2] Reorder each block's contents in `web/components/exposure-merge.tsx` to the mockup's order — asset class, instrument name, percentage — and apply the per-tint text colour from `--on-e1..e4`

**Checkpoint** — five merge/reset cycles with no reload and no stuck state (quickstart, SC-002). Then with reduced motion on: state still changes, nothing animates.

---

## Phase F — The band reveal · 20m · US4

- [x] T029 [US4] Create `web/components/band-reveal.tsx` as a client component taking only `children` — one ref, one `IntersectionObserver` at `threshold: 0.4`, sets `data-reveal="seen"` then calls `disconnect()` (FR-019)
- [x] T030 [US4] Wrap the band rows in `web/components/mandate-panel.tsx` with `BandReveal`, add the `.pin` class to each marker, and set `--pin-delay` inline per row from the row **index** — an ordinal, not a figure (FR-021, Principle XI)

**Checkpoint** — pins draw in once on first scroll, do not re-animate on scroll away and back, and are already drawn under reduced motion and with JavaScript disabled.

---

## Phase G — Verification · 30m

Each task names the quickstart.md section that produces its evidence. No
task here is complete without pasted output.

- [x] T031 Confirm nothing upstream moved — `md5 -q web/public/findings.json` unchanged from before the spec, and `pytest -q` green at 108 tests (quickstart §0)
- [x] T032 [P] Run `cd web && npm run build` and confirm 25 static pages with no route marked `ƒ` (quickstart §1, SC-008)
- [x] T033 [P] Run the hard-coded-figure sweep and confirm no output — percentages, currency amounts, client ids, instrument ids, dates, series names, in comments as well as code (quickstart §2, SC-004/FR-021/FR-023)
- [x] T034 [P] Run the contrast sweep and confirm `AA failures: 0`, including the merged state at `--e3` (quickstart §4, SC-011/FR-028/FR-031)
- [x] T035 [P] Confirm the derived counts still read three briefed, seven with nothing to raise, ten watching, and that "sixteen" and "four conversations" appear nowhere (quickstart §3, SC-005/FR-022)
- [x] T036 [P] Confirm exactly three non-`ui` client components — `decisions.tsx`, `exposure-merge.tsx`, `band-reveal.tsx` — and no `"use server"`, no `route.*`, no `actions.*`, no animation library (quickstart §7/§8/§9, FR-016/FR-026)
- [x] T037 [P] Confirm no brand asset and no `<img>`/`next/image` anywhere, and that the wordmark resolves to set text (quickstart §5, SC-010/FR-005)
- [ ] T038 Measure the rendered type in the browser and confirm 46px / 80px / 33px at desktop and 32px / 58px / 24px below 900px (quickstart, SC-001/FR-007–009)
- [x] T039 Confirm the spec 008 panels render unchanged on all three briefed clients — explanation buckets, collateral trajectory, tax band with its `unsure_about`, profile band — and the evidence column is still visible without interaction (quickstart, SC-009/FR-024/FR-025)
- [ ] T040 Check the 375px floor — no horizontal scroll, no clipped text, hero figure below content rather than overlapping (FR-030, SC-006)
- [x] T041 Commit with the spec number in the message, per Definition of Done item 8

---

## Dependencies

```
Phase A (done)
   └─> Phase B  tokens + type          [foundational: everything needs these]
         ├─> Phase C  brand frame       US1
         │     └─> Phase D  hero        US1 + US3   (needs the frame's tokens)
         ├─> Phase E  merge             US2         (needs --on-e* from T005)
         └─> Phase F  band reveal       US4         (needs .pin from T009)
                └─> Phase G  verification
```

Phases C, E and F are independent of each other once B is done. D depends
on C only for the wordmark header sitting above it.

## Parallel opportunities

- **T003–T006** are one file and must be sequential; **T007–T009** touch
  the same file and follow them.
- **T012–T016** are `layout.tsx` and `public/` — T016 is `[P]` against all
  of them.
- **Phase E and Phase F can run in parallel** — different files, no shared
  state, and both depend only on Phase B.
- **T032–T037 are all `[P]`** — independent read-only checks.

## Independent test criteria

| Story | Ships alone? | How you'd know |
|---|---|---|
| **US1** brand frame | Yes | Red topline, wordmark header, navy hero with red rule, at every breakpoint |
| **US2** the moment | Yes | Five merge/reset cycles; combined figure equals the blocks' sum |
| **US3** projector scale | Yes | 46/80/33 measured at desktop, 32/58/24 below 900px |
| **US4** band reveal | Yes | Draws once, never again; already drawn under reduced motion and no-JS |

## MVP scope

**Phases B and C** — the token migration and the brand frame. That alone
delivers the "reads as an internal Julius Bär tool" argument that moves two
of the four scoring criteria, and it carries the least risk of the four.

## Cut order, if time runs short

Cut **F first**, then **E**, then **D**.

- **F** goes first because the mandate panel is fully readable static; the
  reveal is a garnish.
- **E** goes second, and it hurts — it is the demo's centrepiece — but the
  four-block graphic still makes its argument standing still, and the
  presenter can say the sentence the merge would have shown.
- **D** goes third; the hero can stay a white band with the new tokens and
  the new type scale, which keeps most of Phase C's value.
- **B and C are never cut.** They are the spec.
