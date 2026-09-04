# Feature Specification: Scenario

**Created**: 2026-09-04 · **Status**: Phase 0 complete, all figures reproduced

**Input**: Block 7 of `alamazing-all-specs.md`, pasted unmodified.

**Spec number**: 005 · **Gate**: G2 (closes it) · **Depends on**: specs
000, 001, 004

Phase 0: [research.md](./research.md).

---

## Why this exists

On 12 August the client asked what happens to his portfolio if the Strait
reopens and normalises. Priscilla's note records the answer: *"We have not
modelled this."*

Spec 004 finds that the question was asked. **This spec answers it.**

That sequence is the whole product in two moves. Every other detector
tells Priscilla something about a portfolio. This one closes a loop with a
person: he asked in August, nobody replied, and she walks into the next
meeting with a number.

The answer is also the uncomfortable one. He is not asking about a crash.
He is asking about **good news** — a de-escalation, the Strait reopening,
the world calming down. And the answer is that good news costs him
roughly 2.5 million in the portfolio and reduces his business earnings in
the same week, because the portfolio he asked to be uncorrelated with his
Gulf business is not uncorrelated with it.

**No model call. No forecast. No volatility assumption.** Arithmetic over
prices already in the file.

---

## User Scenarios & Testing

### Story 1 — Reprice the exposure to a past state (P1)

Given a market series and two dates, the system reprices each holding in
the affected theme from its price at the later date to its price at the
earlier one, and reports the impact in money and as a share of the
portfolio.

**Why P1**: It is the answer to the question, and the last of Article
VIII's six named assertions.

**Acceptance Scenarios**:

1. **Given** a series identifier and two dates as **arguments**, **When**
   the scenario runs, **Then** neither the series nor either date appears
   as a literal in the pipeline.
2. **Given** a holding with a price at both dates, **When** it is
   repriced, **Then** its impact is its current market value scaled by the
   ratio of the two **prices**, not of the two market values.
3. **Given** the hero client and the pre-conflict date, **When** the
   scenario runs, **Then** the total impact is **−2.5m ± 0.1m** and
   **−7.8% ± 0.2** of the portfolio.
4. **Given** the scenario result, **When** it is read, **Then** each
   position's before, after and impact are itemised.
5. **Given** the named series, **When** the finding is written, **Then** it
   cites the series value at both dates as evidence.

---

### Story 2 — Handle the position that has no past (P1)

The structured note settled between the two dates and has no earlier
price. The system proxies it off the worst-performing leg of its basket
that the client holds, and says so.

**Why P1**: It is 12.90% of the portfolio and a third of the impact.
Omitting it would understate the answer by a third; guessing silently
would be worse.

**Acceptance Scenarios**:

1. **Given** a holding with no price at the earlier date, **When** it is
   repriced, **Then** the ratio of the worst-performing basket leg the
   client holds is used, and the substitution is recorded in
   `unsure_about`.
2. **Given** a worst-of basket, **When** the proxy leg is chosen,
   **Then** it is the leg with the largest adverse move among those the
   client holds — because that is what a worst-of structure pays on.
3. **Given** a basket leg the client does **not** hold whose move is
   larger still, **When** the finding is written, **Then** the impact
   under that leg is computed and reported alongside, with the note that
   the strictly correct leg is a name the client does not hold.
4. **Given** a holding with no price at the earlier date and no basket
   reference, **When** it is repriced, **Then** it is excluded and the
   exclusion is recorded — no ratio is invented.

---

### Story 3 — Say that it hits his business too (P1)

Where the client's recorded source of wealth shares the theme, the system
states that the same event affects both, citing the source of wealth and
the note in which the client said so.

**Why P1**: This is the difference between a repricing and an insight. The
portfolio number alone is a risk report. The portfolio number plus *"and
your charter rates fall in the same week"* is the reason he cannot wait.

**Acceptance Scenarios**:

1. **Given** a client whose source of wealth shares the scenario's theme,
   **When** the finding is written, **Then** it states that the event
   affects both the portfolio and the business.
2. **Given** a note in which the client recorded his own view of that
   link, **When** the finding is written, **Then** it quotes the note and
   cites its id — the system does not infer the link, it reports his
   statement of it.
3. **Given** a client whose source of wealth does not share the theme,
   **When** the finding is written, **Then** no second-order claim is
   made.

---

### Edge Cases

- **A series with no value at one of the dates.** The scenario still
  reprices from the price columns; the series citation records the missing
  value rather than omitting the finding.
- **A date that is not a snapshot.** Rejected explicitly.
- **The two dates given in reverse order.** Handled — the earlier is the
  comparison state regardless of argument order.
- **A theme with no holdings.** No finding.
- **A holding whose price is zero or missing at the later date.** Excluded
  from repricing and recorded; no division by zero.
- **A client with no source of wealth recorded.** No second-order claim.

---

## Requirements

- **FR-001**: `detect` MUST take the market series identifier and both
  dates as arguments. Neither may appear as a literal in the pipeline.
- **FR-002**: Repricing MUST use the ratio of instrument **prices** at the
  two dates, not the ratio of market values.
- **FR-003**: The system MUST itemise each position's value before, value
  after and impact.
- **FR-004**: The system MUST report the total impact in USD and as a
  share of the client's portfolio.
- **FR-005**: A holding with no price at the earlier date MUST be proxied
  from the worst-performing leg of its basket that the client holds, and
  the substitution MUST be recorded in `unsure_about`.
- **FR-006**: Where a basket leg the client does not hold has a larger
  adverse move, the impact under that leg MUST be computed and reported
  alongside the headline.
- **FR-007**: A holding with no price at the earlier date and no basket
  reference MUST be excluded, and the exclusion recorded. No ratio may be
  invented.
- **FR-008**: The finding MUST cite the named series and its value at both
  dates as evidence.
- **FR-009**: Where the client's recorded source of wealth shares the
  theme, the finding MUST state that the event affects both, citing the
  source of wealth and any note in which the client recorded that view.
- **FR-010**: The system MUST NOT infer a link between portfolio and
  business that the data does not record.
- **FR-011**: The system MUST NOT call a language model, forecast, or
  apply any volatility assumption.
- **FR-012**: Every finding MUST carry file, row identifiers and values.
- **FR-013**: Copy MUST NOT contain the word "recommend".
- **FR-014**: Identical inputs MUST produce identical findings.

### Key Entities

- **Scenario** — a named market series and two dates. "What if the Strait
  reopens" and "what if rates fall" are the same object with different
  arguments.
- **Repricing** — one holding's value at the later date scaled by the
  ratio of its prices at the two dates.
- **Proxy** — the substitute ratio used for a position that did not exist
  at the earlier date, and the leg it came from.
- **Second-order effect** — the recorded overlap between the scenario's
  theme and the client's source of wealth, with the client's own
  statement of it.

---

## Success Criteria

- **SC-001**: The hero client's total impact is **−2.5m ± 0.1m** and
  **−7.8% ± 0.2** of the portfolio. *(Article VIII:
  `test_scenario_cl0019`.)*
- **SC-002**: The four positions are itemised as
  −0.43m / −0.72m / −0.54m / −0.82m, each ± 0.01m.
- **SC-003**: The structured note's proxy is recorded in `unsure_about`,
  naming the leg used.
- **SC-004**: The worst-of alternative is computed and reported as
  approximately **−2.65m**, with the note that the leg is a name the
  client does not hold.
- **SC-005**: The finding cites **BRENT_USD_BBL at 101.5 and 72.4**.
- **SC-006**: The second-order effect cites `clients.csv` for the source
  of wealth and **N-025** for the client's own view.
- **SC-007**: Passing a different series and dates produces a different,
  non-erroring result — the portability demonstration.
- **SC-008**: Two runs produce identical findings.
- **SC-009**: No finding contains "recommend".
- **SC-010**: The portability grep over `pipeline/` returns nothing.

---

## Assumptions

- The affected theme comes from spec 001's `look_through`, so the scenario
  reprices the same four positions the concentration finding names.
- Prices come from the `price_<date>` columns in `instruments.csv`.
- The headline uses block 7's proxy leg; the worst-of alternative is
  reported rather than substituted — [research.md](./research.md) R3.
- The series is **evidence, not input**: the arithmetic runs off price
  columns. It is still a parameter because the finding cites it and a
  different scenario cites a different series — R5.

---

## Out of Scope

- Forecasting, probability, or any volatility model. Block 7 is explicit.
- Suggesting what to do about it (Principle IX).
- Any model call.
