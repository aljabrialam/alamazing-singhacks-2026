# Feature Specification: Mandate Classification

**Created**: 2026-09-04 · **Status**: Phase 0 complete, figures reproduced

**Input**: Block 5 of `alamazing-all-specs.md`, pasted unmodified.

**Spec number**: 003 · **Gate**: G2 · **Depends on**: spec 001
(`pipeline/mandate.py`), spec 000

Phase 0 findings: [research.md](./research.md). All three acceptance
figures reproduce; two errors were found in the reference documents and
one live defect in spec 001.

---

## Why this exists

The brief asks us to separate **drift** from **client-directed**. Reading
the notes revealed a third case the brief does not name.

Margarethe Voss-Brenner's portfolio is 71.46% equity against a 30%
ceiling on a Conservative mandate. She has never traded. The portfolio was
transferred in as it stood when her husband died. **Nobody chose this
allocation for her** — not the bank, and not her.

That is neither drift nor client direction, and it is a different
conversation with a different urgency. Drift you rebalance. Client
direction you discuss. An inherited portfolio you have to *explain* to
someone who has told you twice she does not understand what is in it and
has never taken a risk with money.

So the system reports **three** classifications, not two. Same breach,
three conversations.

The second reason this spec exists is the opposite result. **CL-0019
breaches nothing**, and that is not a null — it is the finding. His
portfolio passes every check the bank runs and is still 42% one bet. The
detector must be able to say "checked, nothing breached" as a positive
statement, because spec 001's `compliance_clean` depends on it.

---

## User Scenarios & Testing

### Story 1 — Classify the breach, not just flag it (P1)

For each breached band, the system decides whether the breach was
inherited, client-directed, or drift, from portfolio inception and
transaction history.

**Why P1**: This is the judgement the brief is testing. A flag is a
monitoring system; a classification is advice.

**Independent Test**: CL-0003's equity breach classifies `inherited`;
CL-0014's classifies `drift`.

**Acceptance Scenarios**:

1. **Given** a portfolio whose inception falls in the current reporting
   year and which shows no client-initiated acquisition into the breached
   class, **When** the breach is classified, **Then** it is `inherited`.
2. **Given** an above-maximum breach and a transaction acquiring into that
   asset class, **When** it is classified, **Then** it is
   `client_directed`.
3. **Given** a **below-minimum** breach, **When** it is classified,
   **Then** `client_directed` requires a **disposal out of** that class —
   an acquisition into it is evidence *against* client direction, not for
   it.
4. **Given** neither condition holds, **When** it is classified, **Then**
   it is `drift`, and the finding says the weights moved through market
   action rather than through any decision.
5. **Given** any classification, **When** it is read, **Then** it carries
   the evidence it was derived from — inception date, and the transaction
   rows examined.

---

### Story 2 — Say plainly that nothing is breached (P1)

For a client with no breach, the system emits a positive
checked-and-clear result naming every band it checked.

**Why P1**: Block 5 states it directly — the CL-0019 result is not a null.
It is also what `compliance_clean` is built from.

**Acceptance Scenarios**:

1. **Given** CL-0019, **When** every band is checked, **Then** all five
   are within range, the largest position is below its limit, and the
   result states this affirmatively.
2. **Given** a clean result, **When** it is read, **Then** it names each
   band checked and its actual value, so "nothing breached" is auditable
   rather than asserted.

---

### Story 3 — Do not measure what nobody manages (P1)

Portfolios held on a **custody** basis are excluded from band and
position-limit comparison, and reported separately as held-not-managed.

**Why P1**: Because getting this wrong produces confidently wrong output.
Three portfolios in this book are custody accounts, and comparing them to
a mandate band yields a 97.97% "equity breach" on a legacy holding and a
100% "alternatives breach" on a founder's own shareholding. Telling a
founder their portfolio breaches its limit when the position *is* the
company they founded is the confident fabrication the brief warns against.

**Independent Test**: The three custody portfolios produce no breach, and
CL-0001 and CL-0002 — whose only breaches were custody — become
compliance-clean.

**Acceptance Scenarios**:

1. **Given** a custody portfolio, **When** bands are checked, **Then** it
   is excluded from the comparison.
2. **Given** a custody portfolio, **When** the result is read, **Then**
   the portfolio is still reported, with its value and its
   held-not-managed status, so nothing disappears from view.
3. **Given** a client whose only breach was in a custody portfolio,
   **When** compliance is assessed, **Then** they are clean.
4. **Given** the three demo clients, **When** this exclusion is applied,
   **Then** none of their figures change — all three are advisory.

---

### Edge Cases

- **A client with several portfolios under different mandates.** Each is
  checked against its own mandate. Classification is per breach, per
  portfolio.
- **A below-minimum breach in a class the client never held.** Not a
  breach at all — absence of a holding is not a violation (spec 001,
  FR-011).
- **A mandate band for a class nobody holds.** Same.
- **A portfolio with inception in the current year *and* an acquisition
  into the breached class.** `client_directed` wins over `inherited` — a
  transfer-in followed by the client buying more is a decision.
- **A transfer-in with no cost basis.** Recorded as an imperfection by
  spec 000 and surfaced in `unsure_about`; it does not block
  classification.
- **A client with no transactions at all.** Classification proceeds on
  inception date alone.

---

## Requirements

- **FR-001**: The system MUST compare each asset class held in each
  Advisory or Discretionary portfolio against that portfolio's mandate
  band, and each position against the mandate's single-position limit.
- **FR-002**: The system MUST exclude custody portfolios from band and
  position-limit comparison, and MUST report them separately with their
  value and held-not-managed status.
- **FR-003**: The system MUST classify each breach as exactly one of
  `inherited`, `client_directed` or `drift`.
- **FR-004**: `inherited` MUST require both that the portfolio's inception
  falls in the current reporting year and that no client-initiated
  acquisition into the breached class exists.
- **FR-005**: `client_directed` MUST require, for an above-maximum breach,
  an acquisition into the breached class; and for a below-minimum breach,
  a disposal out of it.
- **FR-006**: `drift` MUST be the classification where neither of the
  above holds.
- **FR-007**: `client_directed` MUST take precedence over `inherited`
  where both would otherwise apply.
- **FR-008**: Acquisition and disposal transaction types MUST be defined
  as named constants matching the values present in the data, and MUST NOT
  be written as string literals at the point of use.
- **FR-009**: The system MUST emit a positive checked-and-clear result for
  a client with no breach, naming every band checked and its actual value.
- **FR-010**: Every finding MUST carry its evidence: the mandate rows, the
  portfolio's inception date, and the transaction rows examined.
- **FR-011**: The current reporting year MUST be derived from the data,
  not written as a literal (Principle XI).
- **FR-012**: The system MUST NOT call a language model.
- **FR-013**: Relationship-manager-facing copy MUST NOT contain the word
  "recommend".
- **FR-014**: Identical inputs MUST produce identical findings including
  order.
- **FR-015**: Anything the classification could not determine MUST be
  recorded in `unsure_about`.

### Key Entities

- **Breach** — one asset class in one portfolio outside its mandate band,
  with a direction (`above_max` or `below_min`).
- **Classification** — `inherited`, `client_directed` or `drift`. The
  judgement the brief is testing.
- **Service model** — `Advisory`, `Discretionary` or `Custody`. Determines
  whether a mandate band applies at all.
- **Checked-and-clear result** — the positive statement that every band
  was compared and none breached.

---

## Success Criteria

- **SC-001**: CL-0003 — Equity **71.46%** vs 10–30 (`above_max`), Fixed
  Income **9.15%** vs 45–75 (`below_min`), largest position **26.06%**,
  classification **`inherited`**.
- **SC-002**: CL-0014 — Equity **23.39%** vs 30–55, breached **low**,
  classification **`drift`**.
- **SC-003**: CL-0019 — **no breach.** Equity 57.97 vs 40–65, Structured
  12.90 vs 0–15, Fixed Income 15.67 vs 15–40, Cash 7.45 vs 2–15, largest
  position 13.30 vs limit 15. Emitted as a positive result.
- **SC-004**: The three custody portfolios produce **zero** breaches, and
  CL-0001 and CL-0002 are compliance-clean.
- **SC-005**: No demo client's figures change as a result of SC-004.
- **SC-006**: Every finding carries mandate rows, inception date and the
  transactions examined.
- **SC-007**: Every classification is one of the three permitted values.
- **SC-008**: Two runs produce identical findings.
- **SC-009**: No finding contains "recommend".
- **SC-010**: The portability grep over `pipeline/` returns nothing.

All figures asserted with `pytest.approx`, never equality.

---

## Assumptions

- `pipeline/mandate.py` from spec 001 is extended, not duplicated. Block 5
  requires the same comparison spec 001 already built.
- The current reporting year is taken from the latest snapshot date in the
  data.
- A `Transfer In` transaction is not a client-initiated acquisition. It is
  the mechanism by which an inherited portfolio arrives.
- Classification is per breach, not per client. A client may hold one
  inherited breach and one drift breach.
- `findings.md` records CL-0003's largest position as 26.06%; it also
  breaches the mandate's 10% single-position limit, which is reported
  alongside the band breaches.

---

## Out of Scope

- Rebalancing proposals, or any suggestion of what to hold instead. The
  system explains; Priscilla decides (Principle IX).
- Liquidity and runway — spec 004.
- Scenario repricing — spec 005.
- Any model call.
