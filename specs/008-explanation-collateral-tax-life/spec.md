# Feature Specification: Explanation, Collateral, Tax and Life Events

**Created**: 2026-09-05 · **Status**: Phase 0 complete

**Input**: Four gaps found by auditing the build against the official
challenge brief's *"Directions the Data Supports"*.

**Spec number**: 008 · **Gate**: none — this is post-G3 extension work
inside the feature freeze · **Depends on**: specs 000–007

Phase 0: [research.md](./research.md).

---

## Why this exists

Seven specs closed the brief's core: hidden risk, mandate governance,
liquidity, scenario and prioritisation. An audit against the brief's own
menu found four directions we had not addressed — and two of them we had
already built the machinery for and left unused.

**The brief's warning governs the scope of this spec:**

> A menu, not a checklist. Two or three done well beats all of them done
> thinly.

So all four are specified here, in priority order, and **not all four
will be built**. What ships by the freeze ships; what does not is
labelled roadmap in the README. Specifying something and declining to
build it with a stated reason is honest; building four detectors thinly
to tick a list is the failure the brief is describing.

Two of the four carry a real risk of being **confidently wrong**, and
both errors would flatter us:

- Attribution that credits the market with money the client paid in.
- Tax optimisation that tells a Hong Kong domiciliary to harvest losses.

Those are the reason this needs a spec rather than four quick commits.

---

## User Scenarios & Testing

### Story 1 — Trace the loan against the portfolio over time (P1, D8)

For a client whose portfolio is pledged as collateral, the system reports
loan-to-value at every snapshot, the headroom at each, and whether the
direction of travel is toward the margin-call threshold.

**Why P1**: Lowest cost of the four and the highest value. It upgrades
the weakest of the three demo clients from a static warning into a story
with direction and a date.

**Acceptance Scenarios**:

1. **Given** a pledged portfolio, **When** the facility is reported,
   **Then** loan-to-value, drawn balance and headroom appear for **every
   snapshot**, not only the latest.
2. **Given** the trajectory, **When** it is read, **Then** it states
   whether loan-to-value is rising or falling and by how much.
3. **Given** a snapshot at which the drawn balance increased, **When** it
   is reported, **Then** the increase is identified as a **decision**
   rather than market movement, and the transaction is cited.
4. **Given** loan-to-value rising while the drawn balance is unchanged,
   **When** it is reported, **Then** it is attributed to falling
   collateral value.
5. **Given** the trajectory and the concentration finding, **When** both
   exist for one client, **Then** the collateral finding names the
   concentration as the cause rather than restating it.
6. **Given** a client with no facility, **When** detection runs, **Then**
   no finding is emitted.

---

### Story 2 — Explain what the portfolio did, and why (P2, D7)

Between two snapshots, the system reports which positions moved the
portfolio, separating **market movement** from **money paid in or taken
out**, and names the events that touched the client in that window.

**Why P2**: Building Block 1, which the brief lists first, and the
*position → change → cause* loop it calls *"the core of the whole
challenge"*. The machinery already exists and is tested.

**Acceptance Scenarios**:

1. **Given** two snapshots, **When** the change is attributed, **Then**
   positions are reported in **three separate buckets** — held
   throughout, acquired in the window, disposed of in the window.
2. **Given** a position acquired in the window, **When** the change is
   reported, **Then** its value change is **explicitly not** described as
   performance, and the acquiring transaction is cited.
3. **Given** the hero client's window, **When** the total is reported,
   **Then** the portfolio's gain is separated into money paid in
   (≈ USD 3.84m) and market movement (≈ USD 2.18m), and **not** reported
   as a single +6.02m.
4. **Given** the window, **When** causes are named, **Then** they come
   from `event_log.csv` by date and description only.
5. **Given** a position with no flow and no price change, **When** it is
   attributed, **Then** it is omitted rather than reported as zero.

---

### Story 3 — Tax, at domicile rather than residence (P3, D9)

The system reports unrealised gains and losses together, assessed against
the client's **tax domicile** rather than residence, and states where a
tax consequence **cannot** be computed.

**Why P3**: High on understanding, and it compounds two findings already
on CL-0003. But it is the detector most easily made wrong.

**Acceptance Scenarios**:

1. **Given** a client, **When** the tax position is reported, **Then**
   gains and losses are aggregated across **all** their portfolios, and
   the domicile is stated.
2. **Given** a domicile that differs from residence, **When** it is
   reported, **Then** both are named and the domicile is identified as
   the one that governs.
3. **Given** a client domiciled where capital gains are not levied,
   **When** large unrealised losses exist, **Then** the system reports
   that harvesting them is **of little value to this client** — it does
   **not** suggest harvesting.
4. **Given** a position with no cost basis, **When** the tax position is
   reported, **Then** it is named as unquantifiable rather than excluded
   or assumed to be flat.
5. **Given** a client facing a dated obligation and holding net gains,
   **When** both exist, **Then the finding states that meeting the
   obligation realises taxable gains in the domicile named.**
6. **Given** any tax finding, **When** it is read, **Then** it proposes
   no trade and contains no suggested action.

---

### Story 4 — What the allocation was not built for (P4, D10)

The system compares the client's recorded liquidity needs and investment
horizon against the dated obligations in their notes and cash needs, and
reports a contradiction between the two.

**Why P4**: Real, but D4 already surfaces the underlying cash need, so
the marginal contribution is the **profile contradiction** rather than the
obligation. Lowest priority, and the honest reason is the overlap.

**Acceptance Scenarios**:

1. **Given** a client whose recorded liquidity needs are low and who has
   a dated obligation within a short horizon, **When** detection runs,
   **Then** the contradiction is reported, citing both the profile field
   and the source of the obligation.
2. **Given** a profile consistent with the obligations, **When**
   detection runs, **Then** no finding is emitted.
3. **Given** a finding, **When** it is read, **Then** it says the
   **profile** may need revisiting — not the portfolio — because the
   profile is what drives suitability checks.

---

### Edge Cases

- **A facility with no history at a snapshot.** That snapshot is omitted
  from the trajectory; it is not interpolated.
- **A drawn balance that decreases.** Reported as a repayment, with the
  same treatment as an increase.
- **A window with no flows.** Attribution reports one bucket and says so.
- **A position acquired *and* disposed of inside the window.** Reported in
  both buckets, and the net effect stated once.
- **A client with no unrealised figures at all.** No tax finding.
- **A domicile the system has no rule for.** The position is reported and
  the absence of a rule is stated — never a guessed tax treatment.
- **A profile with no recorded liquidity needs or horizon.** No life-event
  finding.

---

## Requirements

### D8 — Collateral

- **FR-001**: The system MUST report loan-to-value, drawn balance,
  collateral value and headroom at every snapshot the facility carries.
- **FR-002**: The system MUST state the direction and magnitude of the
  loan-to-value change across the window.
- **FR-003**: An increase in the drawn balance MUST be identified as a
  decision and MUST cite the transaction where one exists.
- **FR-004**: Loan-to-value rising on an unchanged drawn balance MUST be
  attributed to falling collateral value.
- **FR-005**: Where a concentration finding exists for the same client,
  the collateral finding MUST name it as the cause rather than restate it.

### D7 — Explanation

- **FR-006**: Attribution MUST report positions in three buckets — held
  throughout, acquired, disposed.
- **FR-007**: The value change of an acquired position MUST NOT be
  described as performance, and the acquiring transaction MUST be cited.
- **FR-008**: The portfolio's total change MUST be separated into flows
  and market movement, and MUST NOT be reported as a single figure.
- **FR-009**: Causes MUST come from the event log by date and description
  only.
- **FR-010**: Flow transaction types MUST reuse the named constants
  established in spec 003 rather than new literals.

### D9 — Tax

- **FR-011**: Gains and losses MUST be aggregated across all of a
  client's portfolios.
- **FR-012**: The assessment MUST use **tax domicile**, and MUST name
  both domicile and residence where they differ.
- **FR-013**: Where the domicile does not levy capital gains, the system
  MUST report that harvesting losses is of little value, and MUST NOT
  suggest harvesting.
- **FR-014**: A position with no cost basis MUST be named as
  unquantifiable.
- **FR-015**: The system MUST NOT propose a trade, a sale, or an
  optimisation.
- **FR-016**: Where the system has no rule for a domicile, it MUST say so
  rather than infer a treatment.

### D10 — Life events

- **FR-017**: The system MUST compare recorded liquidity needs and
  investment horizon against dated obligations.
- **FR-018**: A finding MUST cite the profile field and the source of the
  obligation.
- **FR-019**: The finding MUST address the **profile**, not the
  portfolio.

### Across all four

- **FR-020**: Every finding MUST carry file, row identifiers and values,
  and MUST validate against the Finding schema.
- **FR-021**: No detector may call a language model.
- **FR-022**: Copy MUST NOT contain the word "recommend".
- **FR-023**: Identical inputs MUST produce identical findings.
- **FR-024**: No client id, instrument id, sector, domicile, date or
  series may appear as a literal in the pipeline.
- **FR-025**: Anything a detector cannot determine MUST be recorded in
  `unsure_about`.

---

## Success Criteria

- **SC-001**: CL-0014's facility trajectory reports all five snapshots,
  loan-to-value **53.93 → 53.53 → 65.62 → 67.96 → 69.41** each ± 0.01,
  and headroom falling from **44,420,170 to 25,565,930**.
- **SC-002**: The March increase in the drawn balance from 52m to 58m is
  identified as a decision.
- **SC-003**: The rise from 65.62% to 69.41% on an unchanged balance is
  attributed to falling collateral.
- **SC-004**: The hero client's window is reported as **≈ USD 3.84m paid
  in** and **≈ USD 2.18m market movement**, not as a single +6.02m.
- **SC-005**: The FCN's +4,156,210 appears in the **acquired** bucket and
  is not described as performance.
- **SC-006**: CL-0014's tax finding reports large unrealised losses **and**
  that harvesting them is of little value at his domicile.
- **SC-007**: CL-0003's tax finding names Germany as domicile, Singapore
  as residence, and `SYN-ST-0107` as unquantifiable.
- **SC-008**: The hero client's profile contradiction is reported —
  liquidity needs recorded low against a dated obligation inside the
  horizon.
- **SC-009**: No finding contains "recommend" or proposes a trade.
- **SC-010**: The portability grep over `pipeline/` returns nothing.
- **SC-011**: Two builds produce identical findings.

All figures asserted with `pytest.approx`.

---

## Assumptions

- This spec runs **after G3**, inside the feature freeze window. Anything
  unbuilt at the freeze is roadmap, labelled as such in the README, per
  Principle X.
- Capital-gains treatment by domicile is a **small, explicit table** of
  the domiciles present in the data, with an honest default of "no rule
  recorded". It is not a tax engine and must not read as one.
- D7 reuses `diff()` and `attribution()` from spec 000 unchanged.
- D8 extends `d4_runway.py`'s facility block rather than adding a module.

---

## Out of Scope

- A tax engine, rate tables, or jurisdiction rules beyond the domiciles in
  this dataset.
- Rebalancing, harvesting or any suggested trade — Principle IX.
- Retirement or succession *planning*. D10 reports a profile
  contradiction; it does not build a plan.
- Any model call.
