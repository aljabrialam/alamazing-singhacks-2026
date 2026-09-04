# Feature Specification: Liquidity Runway and the Unanswered Question

**Created**: 2026-09-04 · **Status**: Phase 0 complete, figures verified

**Input**: Block 6 of `alamazing-all-specs.md`, pasted unmodified.

**Spec number**: 004 · **Gate**: G2 · **Depends on**: specs 000–003

Phase 0: [research.md](./research.md). Six questions, four corrections,
one new finding of substance.

> **Cut status.** Spec 004 is first on the cut list (11:00 checkpoint).
> **D5 is not cuttable** — block 6: *"D5 is roughly twenty lines. It is
> what converts the demo from analytics to advisory. Do not cut it."* If
> this spec must be reduced, D4 goes and D5 stays.

---

## Why this exists

Two detectors that answer questions a portfolio report cannot.

**D4 — liquidity runway.** A client has a known bill and a known date. Can
they meet it, and what does meeting it cost them? Not "how liquid is the
portfolio" but "what happens when this specific obligation lands".

**D5 — the unanswered question.** A client asked something and nobody
answered. This is twenty lines of code and it is the emotional centre of
the demo: it is the difference between a system that describes a portfolio
and one that notices a person is waiting for a reply.

The hero client asked, on 12 August, what happens to his portfolio if the
Strait reopens and normalises. Priscilla's own note records: *"We have not
modelled this."* Spec 005 answers it. This spec is what finds that it was
asked.

---

## User Scenarios & Testing

### Story 1 — What does paying this actually cost? (P1, D4)

For each planned cash need and uncalled commitment, the system compares the
amount to what is genuinely sellable by the date required, nets off pledged
collateral, and reports what funding it would consume.

**Why P1**: Both demo clients have a dated obligation, and in both cases
the interesting answer is not "can they pay" but "what does paying take".

**Acceptance Scenarios**:

1. **Given** a need in a foreign currency, **When** it is compared to the
   portfolio, **Then** it is converted to USD using the rate from the
   market context, **choosing the operation from the rate's stated unit**.
2. **Given** a need and a date, **When** available funds are computed,
   **Then** only holdings whose liquidity tier is Daily or Weekly count;
   Monthly and Illiquid do not.
3. **Given** a portfolio pledged as collateral against a facility,
   **When** available funds are computed, **Then** the pledge is netted
   off and the facility's loan-to-value headroom is reported.
4. **Given** a need that would be funded by selling pledged collateral,
   **When** the effect is computed, **Then** the resulting loan-to-value
   is reported alongside the margin-call threshold.
5. **Given** CL-0003, **When** her instalment is assessed, **Then** the
   system reports both that liquid assets cover it several times over
   **and** that cash plus fixed income is approximately the size of the
   bill — so meeting it consumes her non-equity holdings or comes from
   equity.
6. **Given** a private-market valuation that lags a quarter, **When** it
   affects a conclusion, **Then** the lag is noted in `unsure_about` and
   **not** reported as an error.

---

### Story 2 — Somebody asked and nobody answered (P1, D5)

The system scans the relationship manager's notes for a question the
client asked with no answer, and for the manager's own admissions that
something was not done.

**Why P1**: Block 6 — do not cut it.

**Acceptance Scenarios**:

1. **Given** note **N-026** for the hero client, **When** notes are
   scanned, **Then** it is surfaced as an open question, carrying his
   question and the admission that it was not modelled.
2. **Given** note **N-028**, **When** notes are scanned, **Then** it is
   surfaced, carrying *"Have not yet replied."*
3. **Given** a question asked **and answered in the same note**, **When**
   notes are scanned, **Then** it is **not** surfaced.
4. **Given** the word "unresolved" describing market conditions rather
   than an open item, **When** notes are scanned, **Then** it is **not**
   surfaced.
5. **Given** an admission containing an answer word — *"Have not yet
   replied"* — **When** it is assessed, **Then** the admission takes
   precedence and the note is surfaced.
6. **Given** an open question, **When** it is reported, **Then** it cites
   the note id and the date, and quotes the note.

---

### Edge Cases

- **A need with no rate available for its currency.** No figure is
  invented; the need is reported with the conversion recorded as unknown
  in `unsure_about`.
- **A need already past.** Reported as due, not silently dropped.
- **A client with no needs and no commitments.** No D4 finding.
- **A commitment whose call window is beyond every need.** Reported, but
  not netted against a near-dated need.
- **A facility with no margin-call threshold.** Pledge is netted; no
  loan-to-value warning is fabricated.
- **A client with no notes.** No D5 finding.
- **A note answered by a *later* note rather than the same one.** Treated
  as answered.

---

## Requirements

- **FR-001**: The system MUST convert every need to USD using the rate
  from the market context, selecting multiplication or division from the
  rate's stated unit rather than from the series identifier.
- **FR-002**: The system MUST NOT invent a rate. A need whose currency has
  no rate MUST be reported with the conversion recorded as unknown.
- **FR-003**: Available funds MUST count only holdings whose liquidity
  tier is Daily or Weekly.
- **FR-004**: The system MUST net off collateral pledged under a credit
  facility, and MUST report the facility's loan-to-value against its
  margin-call threshold.
- **FR-005**: Where meeting a need would require selling pledged
  collateral, the system MUST report the resulting loan-to-value.
- **FR-006**: The system MUST report both tier-based available funds and
  the cash-plus-fixed-income figure, because they answer different
  questions.
- **FR-007**: A private-market valuation lagging by a quarter MUST NOT be
  reported as an error, and MUST be noted in `unsure_about` where it
  affects a conclusion.
- **FR-008**: The system MUST surface a question the client asked for
  which no answer is recorded, and the manager's own admission that
  something was not done.
- **FR-009**: A question answered in the same note or a later note MUST
  NOT be surfaced.
- **FR-010**: An admission MUST take precedence over an answer marker.
- **FR-011**: Every open question MUST cite its note id and date and quote
  the note.
- **FR-012**: Every finding MUST carry file, row identifiers and values.
- **FR-013**: The system MUST NOT call a language model.
- **FR-014**: Copy MUST NOT contain the word "recommend".
- **FR-015**: Identical inputs MUST produce identical findings.
- **FR-016**: No client id, instrument id, currency, date or series may
  appear as a literal in the pipeline.

### Key Entities

- **Need** — a dated, known obligation with an amount, a currency, a
  window and a certainty.
- **Commitment** — an uncalled private-market obligation with an expected
  call window.
- **Available funds** — holdings sellable by the date required, after
  netting pledged collateral.
- **Facility headroom** — how far a pledged portfolio's loan-to-value sits
  from its margin-call threshold, before and after a need is met.
- **Open question** — something the client asked, or the manager admitted
  not doing, with no recorded answer.

---

## Success Criteria

- **SC-001**: CL-0003's EUR 3.4m instalment converts to **USD 3,712,800 ±
  1,000** using the EUR rate and its stated unit.
- **SC-002**: CL-0003's tier-based available funds are **88.29% ± 0.01**
  and cash-plus-fixed-income is **16.83% ± 0.01**; the need is **16.74% ±
  0.01** of the portfolio. Both figures reported.
- **SC-003**: CL-0014's HKD 60m converts to **USD 7,682,458 ± 1,000**.
- **SC-004**: CL-0014's facility is reported at **69.41% ± 0.01**
  loan-to-value against a **70%** margin-call threshold, and the
  post-sale loan-to-value is reported as **above the threshold**.
- **SC-005**: CL-0014's illiquid holdings total **26.62% ± 0.01**,
  comprising the direct property at 19.58% and the accumulator at 7.05%.
- **SC-006**: D5 surfaces **N-026** and **N-028**, and does **not**
  surface N-002, N-006 or N-025.
- **SC-007**: Every finding carries evidence and validates against the
  Finding schema.
- **SC-008**: Two runs produce identical findings.
- **SC-009**: No finding contains "recommend".
- **SC-010**: The portability grep over `pipeline/` returns nothing.

All figures asserted with `pytest.approx`.

---

## Assumptions

- The Finding schema's `kind` enum is extended to admit D5 and D6
  ([research.md](./research.md) R6). Without it this spec cannot emit a
  schema-valid finding.
- Block 6's "Tight" characterisation of CL-0003 is not reproduced, because
  the data does not support it under block 6's own liquidity rule. The
  correct and stronger statement is reported instead — R2.
- Uncalled commitments are compared to their expected call window as
  free text; no attempt is made to parse a quarter into a date.
- A need's `due_to` is treated as the date required.

---

## Out of Scope

- Proposing what to sell. The system reports what funding costs;
  Priscilla decides (Principle IX).
- Scenario repricing — spec 005.
- Any model call.
