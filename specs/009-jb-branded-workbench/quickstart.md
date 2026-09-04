# Spec 009 — verification guide

Every success criterion, and the command that settles it. Written so that a
claim of "done" is backed by output rather than by a look at the screen.

## Prerequisites

```bash
cd /Users/aljabri.alam/Documents/Projects/alamazing-singhacks-2026
python3 -c "import pandas"            # pipeline deps present
cd web && npm ci                      # if node_modules is cold
```

## The gate, in order

### 0. Nothing upstream moved

`findings.json` must be byte-identical before and after this spec — it is
the proof that a presentation change stayed a presentation change.

```bash
md5 -q web/public/findings.json        # record before, compare after
pytest -q                              # 108 tests, all green, untouched
```

### 1. Build and page count — SC-008

```bash
cd web && npm run build
```

Expect `Generating static pages (25/25)`, all routes marked `○` or `●`, and
no route marked `ƒ` (dynamic). A `ƒ` means something became server-rendered
and the static guarantee is gone.

### 2. No hard-coded figure anywhere — SC-004, FR-021, FR-023

```bash
cd web
# percentages, currency amounts, ids, dates, series names in components
grep -rnE '[0-9]+\.[0-9]+%|USD [0-9]|CL-00|SYN-|BRENT|20[0-9]{2}-[0-9]{2}-[0-9]{2}' \
  components/ app/ --include=*.tsx
```

Expect **no output**. Matches inside a comment count as failures — "it is
only a comment" is how a checkable gate erodes.

### 3. The mockup's false counts are absent — SC-005, FR-022

```bash
cd web
grep -rniE 'sixteen|four conversations' components/ app/    # expect nothing
```

Then confirm the derived figures still render:

```bash
grep -oE '(Three|Seven|[0-9]+) (conversations?|clients?)' .next/server/app/index.html 2>/dev/null \
  || node -e "1"   # or read the rendered call list directly
```

The rendered call list must state **three** briefed, **seven** with nothing
to raise, **ten** watching. Derived, in `app/page.tsx`, not typed.

### 4. Contrast — SC-011, FR-028, FR-031

```bash
python3 - <<'PY'
def lum(h):
    h=h.lstrip('#'); c=[int(h[i:i+2],16)/255 for i in (0,2,4)]
    c=[(v/12.92 if v<=0.03928 else ((v+0.055)/1.055)**2.4) for v in c]
    return .2126*c[0]+.7152*c[1]+.0722*c[2]
def cr(a,b):
    la,lb=lum(a),lum(b); return (max(la,lb)+.05)/(min(la,lb)+.05)
INK='#101821'
pairs=[('ink on e1','#101821','#C9A876'),('ink on e2','#101821','#B8945B'),
       ('ink on e3 (MERGED STATE)','#101821','#A37F46'),('white on e4 (bar)','#FFFFFF','#8A6934'),
       ('white on navy','#FFFFFF','#14284B'),('white on deep navy','#FFFFFF','#0C1B33'),
       ('ink on ground','#101821','#EAECEF'),('muted on sheet','#6B7280','#FFFFFF'),
       ('red on white','#C8102E','#FFFFFF'),('flagline on navy','#F2B8C0','#14284B'),
       ('gold on navy','#C9A876','#14284B')]
bad=0
for n,a,b in pairs:
    r=cr(a,b); ok=r>=4.5
    bad += 0 if ok else 1
    print(f'{"PASS" if ok else "FAIL"}  {r:5.2f}  {n}')
print('\nAA failures:', bad)
PY
```

Expect `AA failures: 0`.

### 5. No fabricated brand asset — SC-010, FR-005

```bash
cd web
ls public/                                    # findings.json only
grep -rn 'Julius B' app/layout.tsx            # set text, not an <img>
grep -rniE '<img|next/image' app/ components/ # expect nothing
```

### 6. Old palette values fully migrated — FR-001, R2

```bash
cd web
grep -rniE '16325c|a4343a|f0f1ed|131b26|c79355|b58141|a0702f|8a5e23|e4e5e1|199,147,85' \
  app/ components/
```

Expect **no output**. This catches the colour literals that a search for
`--e1` cannot see — one of them lives inside a `shadow-[…]` arbitrary value
in the brief page.

### 7. Only the two intended new client components — FR-026

```bash
cd web
grep -rln '"use client"' app/ components/ --include=*.tsx | grep -v components/ui/
```

Expect exactly three: `decisions.tsx` (pre-existing), `exposure-merge.tsx`,
`band-reveal.tsx`.

### 8. Still no server surface — FR-026

```bash
cd web
find app -name 'route.*' -o -name 'actions.*' | head    # expect nothing
grep -rn '"use server"' app/ components/                # expect nothing
```

### 9. No animation library — FR-016

```bash
cd web
grep -iE 'framer|motion|gsap|animejs|lottie|react-spring' package.json  # expect nothing
```

## Manual checks — the ones that cannot be automated, marked as such

### The orchestrated moment — SC-002

```bash
cd web && npm run dev
```

Open the hero client's brief. Then, five times in a row:

1. Press **Look through the note**. Gaps close, all four blocks go to one
   tint, labels fade, the combined bar slides out with the combined figure.
2. Press **Reset**. Everything returns to the separated, labelled state.

Pass condition: five cycles, no reload, no visual artefact, no state stuck.
This is the demo's single point of failure — rehearse it on the machine that
will present, not this one.

Then with reduced motion on (macOS: System Settings → Accessibility →
Display → Reduce motion): the merge must still change state, with no
animation, and the band pins must already be drawn.

### Projector scale — SC-001

The design notes name this as a physical test and it stays one:

> Test from three metres before Saturday — the room is the constraint, not
> the laptop.

Project the hero brief. From three metres, the client name, the headline
figure and the opening line must all be readable. Measure the rendered sizes
to confirm the CSS landed:

```js
// in the browser console on a client brief page
[['h1','client name'],['.hero-figure','headline figure'],['.opening-line','opening line']]
  .forEach(([s,n]) => { const e=document.querySelector(s);
    if(e) console.log(n, getComputedStyle(e).fontSize); });
```

Expect 46px, 80px, 33px at desktop width; 32px, 58px, 24px below 900px.

### Responsive floor — FR-030, SC-006

At 375px: no horizontal scrollbar, no clipped text, the hero figure below
the content rather than overlapping it, the red topline and wordmark intact.

### Spec 008 panels — SC-009, FR-024

On the three briefed clients, confirm each still renders with the same
content as before: the explanation panel's three buckets, the collateral
trajectory, the tax band and its `unsure_about` line, the profile band.
Nothing may have been lost to the re-skin.
