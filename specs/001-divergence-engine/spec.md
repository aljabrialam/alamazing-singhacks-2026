# Feature Specification: Divergence Engine

**Feature Branch:** `001-divergence-engine`
**Created:** 2026-09-04
**Status:** Draft
**Constitution:** `.specify/memory/constitution.md` v3.0.0
**Input:** Julius Baer — Wealth Intelligence, SingHacks 2026

---

## User Scenarios

### Demo clients

Verified, with figures, in `findings.md`. Three divergences, three
different reasons today's tools miss them.

| Client | Divergence | Invisible because |
|---|---|---|
| Abdullah Al-Mansoori (CL-0019) | 42.13% look-through vs "outside shipping" objective | Every mandate band respected |
| Margarethe Voss-Brenner (CL-0003) | 71.46% equity on a Conservative mandate | Breach is neither drift nor directed |
| Lau Chi Ming (CL-0014) | 29.46% one name across three asset classes | Each instrument classes differently |

### Primary story

Priscilla Ong is a relationship manager on the Asia desk covering the
Singapore and Hong Kong booking centres. She looks after 20 clients,
ranging from a HNW individual with ~USD 8m to a multi-generational family
office at USD 88m. She has meetings over the next fortnight.

She can properly watch about three of them. The rest get attention
quarterly, or when something has already gone wrong.

Today is 26 August 2026. She opens the Divergence Engine and sees which
client to call first, what the system found, and one sentence she could
open the conversation with.

### Acceptance scenarios

1. **Given** Abdullah Al-Mansoori, whose stated objective is to build
   wealth outside the Gulf and outside shipping, **when** his look-through
   exposure to shipping and energy reaches 42.13%, **then** the system
   surfaces the contradiction with both the objective and the holdings
   shown — even though every mandate band is respected.

2. **Given** a client with more than one portfolio, **when** concentration
   is within limits in each individually but breaches when aggregated,
   **then** the system surfaces the aggregate risk.

3. **Given** SYN-SP-0505, whose `underlying_reference` names Pacific
   Orient Shipping and Global Energy Majors, **when** the client already
   holds both outright, **then** the system reports the combined
   look-through exposure rather than the stated asset class.

4. **Given** a mandate breach, **when** `transactions.csv` shows the
   client bought into the position, **then** it is classified as
   client-directed rather than drift.

5. **Given** Margarethe Voss-Brenner's inherited portfolio, breaching its
   Conservative equity band at 71.46% against 10-30, **when** no trade
   caused it and the client did not choose it, **then** it is classified
   `inherited` — neither drift nor client-directed.

6. **Given** any generated statement, **when** the RM opens the evidence
   drawer, **then** every claim resolves to source rows and to an
   `event_log.csv` entry.

7. **Given** a finding the RM disagrees with, **when** she dismisses it,
   **then** it is removed and the reason it fired is shown.

8. **Given** evidence that does not support a confident conclusion,
   **when** the system reports it, **then** it appears under uncertainty
   with what would need checking.

### Edge cases

- Private-market valuations lag a quarter. This is industry practice, not
  a data error, and must not be flagged as one.
- The dataset contains deliberate real-world imperfections. These are
  logged and surfaced, not silently dropped.
- RM notes sometimes disagree with the numbers. This is signal, not noise.

---

## Requirements

### Functional

- **FR-001** System MUST load all files in `data/` and join them at
  client level across all five snapshots.
- **FR-002** System MUST compare any two snapshots and attribute the
  change to individual holdings.
- **FR-003** System MUST detect contradictions between `rm_notes.json`
  and holdings or transactions (D1).
- **FR-004** System MUST detect mandate breaches and classify each as
  drift, client-directed, or inherited (D2). The third class exists
  because a transferred-in portfolio was chosen by nobody — see
  `findings.md` §2.
- **FR-005** System MUST detect concentration visible only when a
  client's portfolios are aggregated (D3).
- **FR-006** System MUST resolve structured products to their
  `underlying_reference` when computing exposure (D3).
- **FR-007** System MUST compare planned cash needs and uncalled
  commitments against sellable holdings (D4).
- **FR-008** Every finding MUST carry source rows and `event_log.csv`
  references.
- **FR-009** Explanations MUST cite only events present in
  `event_log.csv`. The file is authoritative over model memory.
- **FR-010** System MUST produce a written brief per client ending in an
  opening line for the conversation.
- **FR-011** System MUST rank all 20 clients with a defensible reason.
- **FR-012** RM MUST be able to accept, dismiss or annotate any finding.
- **FR-013** System MUST report low-confidence findings separately with
  what would need checking.
- **FR-014** System MUST NOT use the word "recommend" in RM-facing copy.
- **FR-015** Findings MUST be deterministic — identical inputs produce
  identical output.
- **FR-016** System MUST detect exposure that is within every mandate band
  yet concentrated once looked through. Compliance-clean is not risk-free.
- **FR-017** System MUST surface a client question recorded in
  `rm_notes.json` that has no recorded answer.
- **FR-018** System MUST answer the "what could happen next" question by
  repricing affected holdings to a prior market state drawn from
  `market_context.csv`, and MUST state the second-order effect on the
  client's own business or income where the objectives or notes describe
  one (D6).

### Key entities

- **Client** — person or family office; age, life stage, source of
  wealth, risk profile, tax domicile, stated objectives
- **Portfolio** — belongs to a client; a client may hold several
- **Holding** — instrument position at one of five snapshot dates
- **Mandate** — allocation bands and concentration limits per portfolio
- **Event** — a 2026 market or geopolitical event and its transmission
  channels
- **Finding** — a detected divergence with evidence, severity,
  confidence, and what it is unsure about

---

## Out of scope

Chat interface · authentication · database · real market data · portfolio
optimiser · mobile app · all twenty clients in depth · charts without a
finding attached

---

## Review checklist

- [ ] No implementation detail in this document
- [ ] Written for a private-banking reader, not a developer
- [ ] Every requirement testable
- [ ] Scope bounded to what one builder can ship in twelve hours
