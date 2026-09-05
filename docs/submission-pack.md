# Submission Pack — ALAMazing

**Julius Baer — Wealth Intelligence · Submit by 18:00 Sat, lateness penalised**
**Companion to:** `JB-CONSTITUTION.md`, `IMPLEMENTATION-SPEC.md`

---

## 1. What actually scores

Four criteria, 25% each. No technical-depth criterion exists.

| Deliverable | Client-Centric | UX & Design | Feasibility | Strategic Impact |
|---|---|---|---|---|
| The finding itself | ●●● | | | ● |
| S2 brief screen | ●● | ●●● | | ● |
| Evidence drawer | | ● | ●●● | |
| Accept/dismiss | | ● | | ●●● |
| S3 uncertain | ●● | | ●● | ● |
| README | | | ●●● | ●● |
| [Production feasibility](production-feasibility.md) | | | ●●● | ●●● |
| Demo video | ●● | ●● | | ●● |

**Testing:** three things only — determinism test, traceability, and the
"runs in a bank" README section. A full pyramid earns nothing here.

---

## 2. The 3-minute video

**Record once. This is both the submission video and the wifi-failure
fallback.** Screen capture with voiceover. Record it at ~16:00, before the
freeze, while you still have room to redo one take.

Tone: explaining to a smart friend who doesn't work in banking. Not
technical. Their brief says do not spend long on the problem — get to the
solution.

| Time | Beat | On screen | Script |
|---|---|---|---|
| 0:00–0:20 | **The person** | S1 call list | "This is Priscilla. She's a relationship manager at a private bank, and she looks after twenty wealthy families. She can properly watch about three of them. The other seventeen get a call once a quarter — or when something's already gone wrong." |
| 0:20–0:35 | **The idea** | S1, hover a row | "Julius Baer says every client gets a relationship manager supported by a team of specialists. We built one more specialist — one that reads everything, every day, and brings her what doesn't add up." |
| 0:35–1:45 | **The finding** | S2, read the brief | "Here's what it found this morning." *Read the brief aloud, slowly.* "He told her in June he wouldn't sell at a loss. His bonds are down 5.6 million since February, after yields rose. He draws 1.1 million a year. His longest bond matures in 2045. Waiting for it to recover isn't a plan he can outlive." |
| 1:45–2:05 | **Why you can trust it** | Evidence drawer | "Every sentence traces. These are the actual holdings, and this is the event that caused it — from the bank's own event log, not the model's memory. Nothing here is invented." |
| 2:05–2:25 | **She's still in charge** | Accept / dismiss | "It doesn't advise the client. It brings findings to Priscilla. She accepts, edits, or throws it out. She owns the relationship and she owns the advice." |
| 2:25–2:45 | **Honesty** | S3 | "And here's what it isn't sure about — the things it would want checked before she uses them. We'd rather say we don't know than sound confident and be wrong." |
| 2:45–3:00 | **Close** | S2 | "Twenty clients. One relationship manager. Now she knows who to call first, and what to say." |

**Rules for the recording**

- Read the brief aloud at 0:35. Don't summarise it — let the judge hear
  the prose. That's the product.
- No architecture diagram in the video. It goes in the README.
- Do not say "AI-powered," "leverage," or "seamless."
- One take, minor stumbles fine. Polish costs time you need for rehearsal.

**Memorise the first and last lines.** Everything between can be natural.

---

## 3. README structure

Judges are technical and non-technical. Split it explicitly.

```markdown
# ALAMazing — Divergence Engine

> Priscilla has 20 clients and can properly watch three.
> This is a specialist for the other 17.

[3-min demo video](link)  ·  [Live demo](link)

## What it does
Three short paragraphs, no jargon. What the RM sees, what it found,
why it matters. A non-technical judge should stop here satisfied.

## The finding
Your actual worked example. The client, the contradiction, the event,
the opening line. This is the strongest thing in the repo — put it high.

## How it works
Architecture diagram (Mermaid). Pipeline stages. Where the LLM sits
and, more importantly, where it doesn't.

## Why you can trust it
- **Nothing the model produces is a figure.** Every number is a pandas
  computation — reproducible, and the same class of calculation as the
  bank's existing portfolio system.
- Every claim traces to source rows — screenshot the evidence panel.
  This is checkability, not just accuracy: an auditor wants a wrong answer
  they can trace, not a correct black box.
- Explanations grounded in `event_log.csv`, authoritative over model memory
- Deterministic — findings computed at build time and committed. Screenshot
  `test_findings_are_deterministic` passing.
- The RM keeps, rejects or annotates. Nothing reaches a client unreviewed.
- **What is not automatic:** the judgement about which findings matter, and
  the modelling choice of treating a worst-of basket as full exposure. Both
  stated on the uncertainty screen.
- **How you would prove it in production:** shadow mode for a quarter,
  every finding logged against the RM's decision, yielding measured
  precision. That is the confusion matrix a bank would require.

## Running this in a bank
- Client data never leaves the pipeline; the model receives derived
  findings, not raw records
- No live inference at read time — auditable, reviewable output
- Findings are versioned artifacts, not chat logs
- Where this would integrate, and what would need hardening

## What we didn't do
Honest scope. What's stubbed, what we'd build next, what we're unsure of.

## Setup
git clone / pip install -r requirements.txt / python pipeline/build.py
cd web && npm install && npm run dev
```

**"Running this in a bank" is the section most teams won't write**, and
it's a quarter of the score.

---

## 4. Saturday deliverables checklist

| Time | Deliverable | Est. |
|---|---|---|
| 15:30 | Determinism test written and passing | 15m |
| 15:45 | Architecture diagram (Mermaid) | 15m |
| 16:00 | **Record the 3-min video** | 25m |
| 16:30 | README written | 30m |
| 17:00 | Deploy verified from phone on mobile data | 10m |
| 17:10 | Rehearse live pitch ×3, timed | 30m |
| 17:45 | **Submit** | 10m |
| 18:00 | Hard deadline | — |

**Freeze code at 16:00.** Everything after that is packaging, and
packaging is 50% of the score here.

---

## 5. The determinism test

The only test worth writing. Serves Feasibility directly.

```python
def test_findings_are_deterministic():
    """Same inputs must produce identical findings. A regulated
    advisory system cannot give different answers on different runs."""
    a = build_findings(load_all("data/"))
    b = build_findings(load_all("data/"))
    assert a == b
```

Screenshot it passing. Put it in the README under "Why you can trust it."

Add two more only if time permits: one D1 detector case, one evidence
completeness check (every finding has at least one source row).

---

## 6. Cut order for the submission pack

| Cut | When |
|---|---|
| Extra unit tests | Always — three is enough |
| README "what we didn't do" | Behind at 16:45 |
| S3 screenshot in README | Behind at 17:00 |
| **Never cut** | Video, "runs in a bank" section, rehearsal | — |

A working demo with no video scores worse than a rougher demo with a clear
three-minute story. Presentation is explicitly scored — their own slide
says so.
