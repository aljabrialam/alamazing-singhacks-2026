# Feature Specification: Briefs and Build

**Created**: 2026-09-04 · **Status**: Phase 0 complete

**Input**: Block 8 of `alamazing-all-specs.md`, pasted unmodified.

**Spec number**: 006 · **Gate**: G3 · **Depends on**: specs 000–005

Phase 0: [research.md](./research.md). Block 8 needed no corrections.

---

## Why this exists

Six detectors produce 62 findings. A relationship manager with twenty
clients and a morning does not read 62 findings.

This spec does two things with them. It **writes** — one briefing per demo
client, three or four paragraphs and one sentence she could say aloud. And
it **ranks** — all twenty clients by how soon a conversation is worth
having, which is not the same as by portfolio size.

Then it assembles everything into one committed file, and proves that
building it twice gives the same answer.

This is the second and last place a model is called. Between them, spec
002 and this spec account for all 24 calls in the system, and every one
runs at build time with its output committed.

**The prose is the product.** The demo's closing beat is Priscilla reading
the opening line aloud. If the brief reads like a risk report, the pitch
loses its last twenty seconds — so block 8's instruction is to tighten
the prompt rather than edit the output by hand.

---

## User Scenarios & Testing

### Story 1 — Write the brief (P1)

For each demo client, one model call turns the findings into three or four
short paragraphs naming the person and their situation, ending in one
sentence the relationship manager could open with.

**Why P1**: The 2:40 beat of the demo is reading that sentence aloud.

**Acceptance Scenarios**:

1. **Given** a client's findings and notes, **When** the brief is
   written, **Then** exactly one model call is made, at build time.
2. **Given** the brief, **When** it is read, **Then** it contains three or
   four paragraphs and exactly one opening line.
3. **Given** the brief, **When** it is checked, **Then** it contains no
   instance of the word "recommend".
4. **Given** an event referenced in the brief, **When** it is checked,
   **Then** it resolves to a row in the event log by date and
   description.
5. **Given** the brief has been written once, **When** the build runs
   again, **Then** the committed brief is reused and **no model call is
   made**.
6. **Given** no API key, **When** the build runs, **Then** committed
   briefs are used and the build completes.

---

### Story 2 — Rank the call list (P1)

One model call orders all twenty clients by how soon a conversation is
worth having, each with one sentence of justification.

**Why P1**: S1 is the first and last screen of the demo. "Who do I call
first" is the product's opening claim.

**Acceptance Scenarios**:

1. **Given** all twenty clients, **When** the ranking is produced,
   **Then** every client appears **exactly once** and none is dropped.
2. **Given** the model omits or duplicates a client, **When** the ranking
   is validated, **Then** the omission is corrected in code and recorded —
   the model's output is never trusted to be complete.
3. **Given** the ranking, **When** each entry is read, **Then** it carries
   one sentence of justification.
4. **Given** the ranking inputs, **When** they are assembled, **Then** the
   model receives **derived findings only** — never a raw client record.
5. **Given** the ranking, **When** it is compared to portfolio size,
   **Then** the order is **not** by AUM.

---

### Story 3 — Build the file (P1)

A command-line build runs the detectors over a given set of clients and
writes one JSON file for the web app.

**Why P1**: It is the artifact the whole web layer reads, and the answer
to "run it on someone else" is typing a different id.

**Acceptance Scenarios**:

1. **Given** `--data` and `--clients` arguments, **When** the build runs,
   **Then** both are honoured and neither is hardcoded.
2. **Given** the demo client set, **When** the build runs, **Then** all
   six detectors run over those clients, and the mandate and look-through
   detectors run over **every** client so the call list is real.
3. **Given** the build completes, **When** the output is inspected,
   **Then** it contains the call list, per-client briefs, findings with
   evidence, and the uncertainty record.
4. **Given** the build completes, **When** the file is read, **Then** it
   is valid JSON and every finding validates against the Finding schema.
5. **Given** a client id that does not exist, **When** the build runs,
   **Then** it fails with that id named rather than silently producing an
   empty entry.

---

### Story 4 — Prove it is deterministic (P1)

Building twice from the same inputs produces identical output, and the
build makes no model call.

**Why P1**: Block 8 calls this the only test that matters, and Principle
VII is the answer to the correctness question a banking judge will ask.

**Acceptance Scenarios**:

1. **Given** two builds from the same inputs, **When** the outputs are
   compared, **Then** the serialised bytes are identical.
2. **Given** the build runs with no API key, **When** it completes,
   **Then** it produces the same output as with one — proving the
   determinism comes from committed artifacts and not from luck.
3. **Given** the written file, **When** the recorded figures are checked,
   **Then** 42.134, the compliance verdict, the inherited classification
   and the scenario total are all present and correct — because a
   deterministic build of wrong numbers is still deterministic.

---

### Edge Cases

- **A client with no findings.** Appears in the call list with a
  justification saying nothing was found; no brief is written.
- **A model returning fewer paragraphs than asked.** Accepted and
  recorded; the brief is not padded.
- **A model returning the forbidden word.** The brief is rejected and the
  committed one retained, with the rejection recorded. Never silently
  edited.
- **A model inventing an event.** The brief's event references are checked
  against the event log; an unresolvable reference is recorded in
  `unsure_about`.
- **A ranking that omits a client.** Corrected in code, deterministically.
- **The output directory not existing.** Created.
- **A build over one client.** Works; the call list is that client.

---

## Requirements

- **FR-001**: `write_brief` MUST make exactly one model call per client, at
  build time, and MUST receive derived findings rather than raw records.
- **FR-002**: The brief MUST contain three or four paragraphs and exactly
  one opening line.
- **FR-003**: The brief MUST NOT contain the word "recommend". A brief
  that does MUST be rejected rather than edited, and the rejection
  recorded.
- **FR-004**: Any event the brief references MUST resolve to a row in the
  event log. An unresolvable reference MUST be recorded.
- **FR-005**: `rank` MUST make exactly one model call covering all
  clients, and MUST receive derived findings only.
- **FR-006**: The ranking MUST contain every client exactly once. Omissions
  and duplicates MUST be corrected in code, deterministically, and
  recorded.
- **FR-007**: Each ranking entry MUST carry one sentence of justification.
- **FR-008**: Model output MUST be committed to disk with the prompt, the
  model identifier and the settings that produced it. Regenerating MUST be
  an explicit action.
- **FR-009**: The build MUST make no model call when reading committed
  artifacts, and MUST complete with no API key present.
- **FR-010**: `build` MUST take the data directory and the client list as
  command-line arguments.
- **FR-011**: The build MUST run all six detectors over the named clients,
  and the mandate and look-through detectors over every client.
- **FR-012**: The build MUST fail with the offending id named when given a
  client that does not exist.
- **FR-013**: The written file MUST contain the call list, per-client
  briefs, findings with evidence, and the uncertainty record, and every
  finding MUST validate against the Finding schema.
- **FR-014**: The uncertainty record MUST distinguish data imperfections
  from method limits — they are different kinds of not-knowing.
- **FR-015**: Two builds from the same inputs MUST produce byte-identical
  output.
- **FR-016**: No client id, instrument id, sector, date or series may
  appear as a literal in the pipeline.
- **FR-017**: The build MUST NOT write to `data/`.

### Key Entities

- **Brief** — three or four paragraphs and one opening line, for one
  client, written from findings.
- **Ranking** — an ordered list of every client with one sentence each,
  ordered by urgency of conversation rather than by size.
- **Findings file** — the single committed artifact the web app reads.
- **Uncertainty record** — data imperfections and method limits, kept
  apart.

---

## Success Criteria

- **SC-001**: Exactly **4** model calls are added by this spec — 3 briefs
  and 1 ranking — bringing the system total to **24**.
- **SC-002**: Every brief contains 3–4 paragraphs, one opening line, and
  no instance of "recommend".
- **SC-003**: The ranking contains all 20 clients exactly once.
- **SC-004**: The ranking order differs from the order by AUM.
- **SC-005**: `python pipeline/build.py --data data/ --clients CL-0019`
  succeeds and produces a call list containing that client.
- **SC-006**: The written file contains the look-through figure **42.134 ±
  0.001**, `compliance_clean` true for the hero client, the `inherited`
  classification for CL-0003, and the scenario total **−2.5m ± 0.1m**.
- **SC-007**: Two builds produce byte-identical output.
- **SC-008**: A build with no API key produces the same output as one
  with a key.
- **SC-009**: Every finding in the file validates against the Finding
  schema.
- **SC-010**: A non-existent client id fails the build with that id named.
- **SC-011**: The portability grep over `pipeline/` returns nothing.

---

## Assumptions

- Briefs are written for the demo clients only. Twenty briefs would cost
  twenty calls to say little for the fourteen clients with no findings.
- The ranking covers all twenty, because S1 is her whole book.
- `derived/briefs.json` and `derived/ranking.json` sit beside
  `derived/claims.json`, committed, keyed by content hash.
- `clients.csv`'s `total_aum_usd` agrees with the computed client-level sum
  ([research.md](./research.md) R2), so either may be quoted.
- The findings file is written to `web/public/findings.json`, per the
  constitution's Technology Standards.

---

## Out of Scope

- The web app — spec 007.
- Any model call at demo time.
- Scoring or evaluating brief quality (Article VIII excludes it).
- Briefs for all twenty clients.
