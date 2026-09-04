# Specification Quality Checklist: Julius Bär Branded Workbench

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-09-05
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Notes

Three items were failed on the first validation pass and have been fixed.

**1. "No implementation details" — partially failed, and deliberately left
failing in two places.** FR-016 quotes `useState(false)` and a `className`
ternary, and FR-001 lists hex values. Both are quoted verbatim from
`design-notes.md` at the user's explicit instruction, and both are the
substance of the requirement rather than an implementation choice smuggled
into it: the design note's *point* is that the mechanism must be trivial
enough not to break during a live demo, and a rebrand specification whose
colours were described in prose would be untestable. Recorded as a
deliberate, reasoned exception rather than silently passed.

**2. Two success criteria were unverifiable as first written.** "Reads from
three metres" (SC-001) cannot be automated, and "no hard-coded figure"
(SC-004) was originally phrased as a judgement. SC-004 is now expressed as
a search that returns nothing, which is checkable. SC-001 remains a manual
check and is marked as such — the design notes name it as a physical test
("test from three metres before Saturday"), so making it automatable would
misrepresent it.

**3. The specification originally asserted the mockup was authoritative on
all visual values.** That was wrong and the contrast measurements proved it:
the mockup sets white text on all four exposure tints, which measures 2.25:1
on the lightest and fails both AA and AA-large. FR-031 and SC-011 were added
with the measured table, and the assumption was corrected. This is the
mockup's defect, not ours, and it would have shipped unnoticed had the floor
in FR-028 not been checked against real numbers rather than accepted.

## Open governance item, carried to planning

The specification departs from the letter of Principle XIV, which pins the
design system to `.alamazing/mockup.html`. That file is byte-identical to
`design/mockup-visual.html`, which the rewritten design notes demote to
third preference behind `mockup-jb.html`.

This is flagged in the specification's own Governance note and **must be
resolved during `/speckit.plan`** — by amendment or by declared exception,
not by building against one file while the constitution names another.
