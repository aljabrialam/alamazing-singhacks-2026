# RUN SHEET — ALAMazing / Divergence Engine

**Team:** ALAMazing · **Product:** Divergence Engine · **Repo:** `alamazing-singhacks-2026`
**SingHacks 2026 · Julius Baer Wealth Intelligence · solo · ~10 hours**

Follow top to bottom. Every command is paste-ready. Do not skip a
verification — each one catches an error that gets expensive later.

---

# PART A — SETUP

## Step 1 — Create the project folder

```bash
cd ~/Documents/Projects
mkdir alamazing-singhacks-2026
cd alamazing-singhacks-2026
git init
pwd   # /Users/<you>/Documents/Projects/alamazing-singhacks-2026
```

## Step 2 — Unpack the Julius Baer data

Assumes `singhacks-jb-wealth-intelligence.zip` is in `~/Downloads`.

```bash
unzip ~/Downloads/singhacks-jb-wealth-intelligence.zip -d /tmp/jb
mv /tmp/jb/singhacks-jb-wealth-intelligence/data       ./data
mv /tmp/jb/singhacks-jb-wealth-intelligence/docs       ./jb-docs
mv /tmp/jb/singhacks-jb-wealth-intelligence/starter    ./jb-starter
rm -rf /tmp/jb
```

**Verify:**

```bash
ls data/
# clients.csv commitments.csv credit_facilities.csv event_log.csv
# holdings.csv instruments.csv mandates.csv market_context.csv
# planned_cash_needs.csv portfolios.csv rm_notes.json transactions.csv
```

Twelve files. If any are missing, stop and re-unzip.

## Step 3 — Unpack the spec bundle

Assumes `alamazing-specs.zip` is in `~/Downloads`.

```bash
unzip ~/Downloads/alamazing-specs.zip -d /tmp/spec
cp -r /tmp/spec/alamazing/. .
rm -rf /tmp/spec
```

**Verify:**

```bash
ls -a
# .specify/  AGENTS.md  CLAUDE.md  README.md  START-HERE.md
# alamazing-all-specs.md  alamazing-all-specs.md  data/  design/  docs/  jb-docs/
# jb-starter/  specs/
```

## Step 4 — Put the reference docs where the agent expects them

```bash
mkdir -p .alamazing
cp specs/001-divergence-engine/findings.md        .alamazing/
cp specs/001-divergence-engine/implementation.md  .alamazing/
cp design/mockup-visual.html                      .alamazing/mockup.html
cp design/design-notes.md                         .alamazing/
cp design/globals.css                             .alamazing/
cp docs/demo-script.md                            .alamazing/
```

**Which mockup?** `mockup-visual.html` is the one with the four-into-one
figure and the band chart. `design/mockup.html` is the quieter fallback if
you fall behind on the UI.

## Step 5 — Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install pandas pytest anthropic python-dotenv
pip freeze > requirements.txt
```

## Step 6 — Secrets and gitignore

```bash
cat > .env.local <<'EOF'
ANTHROPIC_API_KEY=
GROQ_API_KEY=
EOF

cat > .gitignore <<'EOF'
.venv/
.env.local
__pycache__/
*.pyc
.DS_Store
node_modules/
web/.next/
web/out/
.vercel
EOF
```

**Check before every commit** that `.env.local` is not staged.

## Step 7 — Folder skeleton

```bash
mkdir -p pipeline/divergence tests web docs
touch pipeline/__init__.py pipeline/divergence/__init__.py
cat > docs/gates.md <<'EOF'
# Gates

One line per gate, with the time it passed. Article XIV — a gate claimed
but not tagged did not pass.

| Gate | Time | Tag |
|---|---|---|
EOF
```

Target layout:

```
alamazing-singhacks-2026/
├─ .alamazing/            agent reference docs
├─ .specify/memory/       constitution (generated in step 10)
├─ data/                  Julius Baer files — never edit
├─ jb-docs/               DATA_DICTIONARY.md
├─ jb-starter/            their quickstart.py
├─ pipeline/
│  ├─ load.py             spec 000
│  ├─ diff.py             spec 000
│  ├─ events.py           spec 000
│  ├─ divergence/
│  │  ├─ d3_hidden.py     spec 001
│  │  ├─ d1_said.py       spec 002
│  │  ├─ d2_mandate.py    spec 003
│  │  ├─ d4_runway.py     spec 004
│  │  ├─ d5_unanswered.py spec 004
│  │  └─ d6_scenario.py   spec 005
│  ├─ brief.py            spec 006
│  └─ build.py            spec 006
├─ tests/
│  └─ test_determinism.py spec 006
├─ web/                   spec 007 — created at step 15
├─ specs/                 Spec Kit output
└─ design/                mockups and tokens
```

## Step 8 — Sanity check their data

```bash
python jb-starter/quickstart.py
```

Prints the book, the event timeline, the market table and one worked
client. Thirty seconds, and it confirms the files are intact.

## Step 9 — THE GATE

**Run this before writing any spec.**

```bash
python3 - <<'EOF'
import pandas as pd
h = pd.read_csv('data/holdings.csv')
t = h[(h.client_id=='CL-0019') & (h.snapshot_date=='2026-08-26')]
w = t.market_value_usd / t.market_value_usd.sum() * 100
print(round(w[t.instrument_id.isin(
    ['SYN-EQ-0025','SYN-ST-0104','SYN-EQ-0008','SYN-SP-0505'])].sum(), 4))
EOF
```

Must print **`42.1344`**.

If it doesn't, something is wrong with the data or the environment. Fix it
now — every spec below assumes this number.

## Step 10 — Spec Kit

```bash
specify check
specify init . --ai claude        # or --integration claude, per your version
specify version >> README.md      # pin it
git add -A && git commit -m "chore: setup, data, spec bundle"
```

---

# PART B — THE SPECS

Open `alamazing-all-specs.md`. Nine blocks. Run them in order.

After every `/speckit.specify`, run `/speckit.plan`, then `/speckit.tasks`,
then implement, then check the acceptance criteria before moving on.

## Step 11 — Constitution

Paste **block 1** from `alamazing-all-specs.md`.

**Then verify it survived generation:**

```bash
grep -c "MUST" .specify/memory/constitution.md          # expect 30+
grep -c "Rationale" .specify/memory/constitution.md     # expect 13
grep -n "Definition of Done" .specify/memory/constitution.md
grep -n "test_lookthrough_cl0019" .specify/memory/constitution.md
```

Spec Kit compresses. If Principle V (the model never counts), Principle
VIII (the pyramid table), or the Definition of Done came back thinner,
paste them back by hand before continuing.

```bash
git add -A && git commit -m "spec: constitution v1"
git tag constitution
```

## Step 12 — Spec 000, data layer · tonight

Paste **block 2**. Build `pipeline/load.py`, `diff.py`, `events.py`.

**Acceptance:**

```bash
python3 -c "
from pipeline.load import load_all
b = load_all()
assert len(b.holdings)==1015 and len(b.clients)==20
assert len(b.portfolios)==24 and len(b.notes)==28
print('imperfections:', len(b.imperfections))
print('OK')
"
```

```bash
git add -A && git commit -m "spec 000: data layer"
git tag g1
echo "| G1 — Data | $(date +%H:%M) | g1 |" >> docs/gates.md
git add docs/gates.md && git commit -m "docs: g1 recorded"
git push --tags
```

**Portability check** — run before tagging g1:

```bash
grep -rn "CL-00\|SYN-\|2026-0\|BRENT" pipeline/ | grep -v "^pipeline/.*test"
# expect: nothing. Client ids, instrument ids, dates and series are
# arguments, never literals. Principle XI.
```

**Definition of Done for every spec** — check all nine before moving on:
unit assertions pass · integration assertion matches `findings.md` ·
findings carry evidence · no model arithmetic · events resolve to
`event_log.csv` · no "recommend" in RM copy · unknowns in `unsure_about` ·
committed with the spec number.

**Stop here Friday night.** Do not build a screen.

## Step 13 — Specs 001–005 · Saturday 09:00–13:00

Paste blocks **3, 4, 5, 6, 7** in that order.

| Block | Spec | Check |
|---|---|---|
| 3 | 001 look-through | CL-0019 = 42.13%, `compliance_clean=True`; CL-0014 = 29.46% |
| 4 | 002 said vs held | CL-0019 claim `avoid_sector` / `shipping` |
| 5 | 003 mandate | CL-0003 = `inherited`; CL-0019 = no breach |
| 6 | 004 runway + unanswered | CL-0003 EUR 3.4m; note N-026 detected |
| 7 | 005 scenario | CL-0019 −2.5m, −7.8% |

Commit after each: `git commit -m "spec 00N: <name>"`

**The six required assertions** (Article VIII) — all must be green at G2:

```bash
pytest tests/ -v
# test_lookthrough_cl0019          42.1344
# test_lookthrough_cl0014          29.46
# test_mandate_cl0003_inherited    71.46 vs 10-30, class=inherited
# test_mandate_cl0019_clean        no breach, compliance_clean=True
# test_scenario_cl0019             -2.5m, -7.8%
# test_findings_are_deterministic  two builds identical
```

Pyramid target for the day: **~14 unit assertions, ~4 integration tests,
2 end-to-end.** Counts, not percentages — countable at 16:00 without
running a coverage tool.

**Build 001 before 002.** D1 reuses `look_through()`.

```bash
git tag g2
echo "| G2 — Findings | $(date +%H:%M) | g2 |" >> docs/gates.md
git add -A && git commit -m "docs: g2 recorded" && git push --tags
```

## Step 14 — Spec 006, briefs and build · 13:00

Paste **block 8**.

```bash
python pipeline/build.py
ls -la web/public/findings.json
pytest tests/test_determinism.py -v
```

**If credits are short:** run the detectors, print the findings, and
generate the four briefs by hand in Claude Code using the prompt from block
8. Paste the output into `findings.json` and commit it. Nothing about the
demo changes — the file was always going to be committed.

## Step 15 — Spec 007, the workbench · 13:30

```bash
npx create-next-app@latest web --typescript --tailwind --app --no-src-dir --no-eslint
cd web
npx shadcn@latest init
npx shadcn@latest add card button sheet table separator scroll-area
cp ../.alamazing/globals.css app/globals.css
cp ../web-public-findings.json public/findings.json   # if build.py wrote elsewhere
cd ..
```

Paste **block 9**.

**Build S2 first** — `/client/[id]`. It is the demo. Open
`.alamazing/mockup.html` beside your editor and follow it literally.

```bash
cd web && npx vercel --prod && cd ..
git tag g3
echo "| G3 — Screens | $(date +%H:%M) | g3 |" >> docs/gates.md
```

---

# PART C — SUBMISSION

## Step 16 — 16:00, code freeze

No new features. Demo-path bugs only.

## Step 17 — 16:00–16:30, record the video

Follow `.alamazing/demo-script.md`. Screen capture with voiceover, three
minutes. **One take.** This is both the submission video and your fallback
if the venue wifi dies.

## Step 18 — 16:30–17:00, README

Template is in `docs/submission-pack.md`. Sections, in order:

1. What it does — three paragraphs, no jargon
2. The finding — Abdullah, with the numbers
3. How it works — architecture diagram
4. Why you can trust it — traceability, determinism, the test screenshot
5. **Running this in a bank** — most teams skip this; it is a quarter of
   the score. Use this wording:

   > This runs as an overnight batch against the bank's own systems —
   > holdings from core banking, notes from CRM, events from research.
   > Today it reads a folder; in production it reads an adapter. The
   > detectors take a book and a date; nothing in them names a sector.
   >
   > The detection logic is production-shaped: deterministic, auditable,
   > evidence-carrying, no live inference. What is not built is the
   > integration layer and the deployment controls — known work, not
   > unknowns.
   >
   > First deployment would be the look-through and the scenario, because
   > they run on holdings and prices alone and need no notes. The notes
   > layer comes second, once the CRM is worth reading.
   >
   > The real dependency is note quality. This works because Priscilla
   > records what clients said, not just what was decided. An RM who
   > writes "annual review, all fine" gives the notes detector nothing.
   > That is change management, not engineering.

   **Never write "production ready".** Principle X.

6. What we didn't do — honest scope

## Step 19 — 17:00–17:45, rehearse

Three times, aloud, against a timer. Presentation is explicitly scored —
their own slide says so.

## Step 20 — 17:45, submit

```bash
# create the repo on GitHub first: alamazing-singhacks-2026 (public)
git add -A && git commit -m "submission" && git tag g4
git branch -M main
git remote add origin https://github.com/aljabrialam/alamazing-singhacks-2026.git
git push -u origin main --tags
```

**Public from the first commit.** Article XV — a methodology with no
evidence of having been followed is a blog post. Push after G1 tonight, not
just at the end.

Then the submission form. **18:00 is hard — lateness is penalised.**

---

# CUT ORDER

Decided now, calmly. Do not relitigate this at 15:00.

| Cut | When behind at |
|---|---|
| Spec 004 (D4 runway) | 11:00 |
| Spec 007 S3 uncertainty | 15:00 |
| Spec 007 S1 → static list | 16:00 |
| Third client, CL-0014 | 16:30 |
| **Never cut** | 000, 001, Abdullah, the mandate panel, evidence, rehearsal |

One client, one brief, one evidence panel, rehearsed three times, beats
everything else half-built.

# 14:00 SATURDAY

Second Julius Baer challenge drops. Read it — five minutes, no more. Your
pipeline is reusable. Sixty-minute box, and **only** if G2 is closed and
you have rehearsed once.

---

# THE SEVEN RULES

1. The model reads and writes. **It never counts.**
2. `event_log.csv` outranks the model. Always.
3. No evidence, no finding.
4. Never the word "recommend" in RM-facing copy.
5. Priscilla decides — keep, reject, or annotate.
6. Deterministic. Same inputs, same findings.
7. Never start a spec until the previous one's acceptance passes.

# THE PITCH, ONE LINE

> Every bank checks the portfolio against the mandate. Nobody checks it
> against what the client actually **said** — so Abdullah's portfolio
> passes every control and is still the opposite of what he asked for.
