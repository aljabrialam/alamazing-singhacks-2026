# Research: Divergence Engine

**Feature:** `001-divergence-engine`
Decisions taken before implementation, with rationale and alternatives.

---

## R1 — Track selection

**Decision:** Julius Baer — Wealth Intelligence.

**Rationale:** dataset supplied, so no data-engineering risk and no
failure mode where the submission is invalid. Julius Baer holds a booth
all day Saturday and a second challenge at 14:00. Their assessment
language — "reasoning you can defend", "judgement about what matters",
"honesty about uncertainty", "confident fabrication scores badly" — reads
as a hiring rubric, and rewards domain judgement over implementation.

**Alternative considered:** Ripple — Agentic Finance on XRP. Rejected on
two grounds: mandatory XRPL transaction creates a hard failure mode
(no transaction, no valid submission), and no Ripple booth on Saturday.

---

## R2 — Product concept

**Decision:** detect divergences — contradictions between what a client
says, what their mandate permits, and what they hold.

**Rationale:** the brief plants this twice.

> "The RM notes sometimes disagree with the numbers. That is not a bug.
> Where a client says one thing and their portfolio says another is
> usually where the real advice is."

> "A risk can be invisible in each one individually and obvious once you
> combine them."

**Competitive read:** the expected build for this brief is a portfolio
dashboard with an AI summary sidebar. Most teams will treat the CSVs as
truth and `rm_notes.json` as flavour, because prose in JSON reads as
secondary. Building the core insight from the notes is the least likely
convergence point.

---

## R3 — Output as prose, not panels

**Decision:** the primary screen is a written brief, not a dashboard.

**Rationale:** the brief's own worked example is a paragraph about a
person, not a chart. It contrasts "this client's bond portfolio is down
USD 5.6m" (arithmetic) against a paragraph naming his age, his drawdown,
his stated refusal to sell, and the maturity date that makes waiting
untenable — and says the second wins even if the first number is more
precise.

**Secondary benefit:** a document-shaped main screen is distinguishable
from a dashboard at a glance, which matters when judges compare demos.

---

## R4 — Python computes, TypeScript presents

**Decision:** pandas pipeline emitting `findings.json`; Next.js reads it
statically.

**Rationale:**
- Five-snapshot diffing is a groupby/pivot in pandas; rewriting in
  TypeScript costs an hour that isn't available
- Repo ships Python and `starter/quickstart.py`
- Nothing runs at demo time, so nothing can fail on stage
- UX & Design is 25%; Streamlit concedes it

**Alternatives rejected:** Streamlit (design weight), all-TypeScript
(diffing cost), live API (demo fragility).

---

## R5 — LLM at build time only

**Decision:** brief generation runs in the pipeline, output committed.

**Rationale:** the brief states `event_log.csv` is authoritative and that
"a real advisory system cannot let a language model free-associate about
geopolitics in front of a client." Build-time generation makes findings
deterministic, reviewable, and version-controlled — closer to how a
regulated bank would actually deploy this.

**Prior art in own work:** Antabay used a locked demo route (SEL→TYO) for
the same reason. Determinism on stage is worth more than flexibility.

---

## R6 — RM authority made visible

**Decision:** no "recommend" in RM-facing copy; accept/dismiss/note on
every finding; RM notes outrank system inference.

**Rationale:** Strategic Impact (25%) is explicitly about preserving the
RM's central role. Julius Baer's own positioning describes an RM
"supported by a team of specialists" and characterises wealth management
as "high-touch, relationship-driven, digital assisted" — against retail
banking's "digital-first". A solution that reads as automating advice
fights their stated identity.

**Framing adopted:** the system is one more specialist on Priscilla's
bench, not an advisor.

---

## R7 — Testing scope

**Decision:** determinism test, evidence-completeness check, one detector
case. No broader pyramid.

**Rationale:** this track has no technical-depth criterion. Technical &
Operational Feasibility (25%) means realism inside a bank — security,
scalability, compliance. A determinism proof argues that directly; unit
coverage does not.

---

## R8 — Client selection

**Decision:** Abdullah Al-Mansoori (CL-0019) as hero, Margarethe
Voss-Brenner (CL-0003) and Lau Chi Ming (CL-0014) as support. Figures in
`findings.md`.

**Rationale:** each is invisible to a *different* existing control, so
together they argue that the gap is structural rather than one missed
alert. Abdullah leads because his portfolio passes every mandate check
while sitting 42% in one bet — the strongest possible version of "your
current tools would not catch this."

**Deliberately not used:** Cheung Kwok Wing (CL-0012), the retiree who
will not sell at a loss. He is the brief's own worked example, so every
team that read the README will demo him. Say this aloud if asked.

**A design change came out of the reading.** The brief asks us to split
mandate breaches into drift and client-directed. Margarethe's portfolio is
neither — it was transferred in as it stood. We added a third
classification, `inherited`. Finding this required reading the notes
rather than querying the tables, which is itself the argument for the
approach.

---

## Open questions
- Nordvind Industrial AB (CL-0003) carries no cost basis through the
  transfer-in, so its gain or loss is unknown. This matters because
  selling it is one route to the EUR 3.4m tax instalment. Surfaced on the
  uncertainty screen rather than guessed.
- Does the 14:00 side challenge reuse this dataset? If so the pipeline is
  reusable; assess at 14:00, 60-minute box.
