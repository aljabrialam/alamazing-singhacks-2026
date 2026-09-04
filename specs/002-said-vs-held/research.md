# Phase 0 Research — Said vs Held (spec 002)

**Date**: 2026-09-04 · **Spec**: [spec.md](./spec.md) · **Plan**: [plan.md](./plan.md)

Four questions resolved before implementation, plus one **constitutional
conflict discovered during it** that had to be resolved rather than
ignored.

---

## R1 — Can `target = "shipping"` reach the recorded 42.134%?

**Decision**: Yes, via **seed on source fields, then expand to the
look-through theme**. Verified before the spec was written.

```
seed (instrument_name / sector / sub_asset_class / underlying_reference)
  SYN-SP-0505  12.90%   its reference names Pacific Orient Shipping
  SYN-ST-0104  11.41%   Pacific Orient Shipping Ltd
  SYN-EQ-0025   8.88%   Asia Pacific Shipping and Logistics Fund
               -------
                33.1979%   <- direct exposure

expand to the look_through theme those seeds sit in
  "Energy + Industrials"  ->  42.1343%   <- recorded 42.134  ✅
```

**Rationale**: The obvious implementation fails. `shipping` is **not a
sector** in this dataset — Pacific Orient Shipping is booked
`Industrials` — so `sector == target` finds nothing at all. And summing
only the positions that name shipping gives 33.20%, not the recorded
figure.

Both numbers are reported, because reporting only one is misleading in
opposite directions. 33.20% understates the position; 42.13% alone invites
"how is an energy fund shipping?". Together they tell the actual story:
three positions are shipping by name, and once the note is resolved to
what it references, the exposure they sit inside is 42% of the book.

---

## R2 — Do the required notes carry the required claims?

**Decision**: Yes, all of them, confirmed by reading the notes before
building.

| Source | Carries |
|---|---|
| CL-0019 objectives | *"Build wealth outside the Gulf region and outside the shipping sector"* |
| **N-025** | his view that charter rates stay elevated; that the Asia portfolio was meant to be uncorrelated with the Gulf business |
| **N-026** | his question about the Strait reopening; the 2027 family-office plan |
| **N-005** | *"never taken a risk with money"*, *"does not understand what is in the portfolio"* |
| **N-006** | *"something safe and boring"* |

---

## R3 — What did extraction actually produce?

**Decision**: Ship it. 114 claims across 20 clients, one call each.

Every acceptance criterion met on the first run:

- CL-0019 objectives → `avoid_sector` / `target=shipping` ✅ **and**
  `avoid_region` / `target=gulf region` — the other half of the same
  sentence, which the spec did not ask for.
- Claims drawn from **N-025** and **N-026** ✅
- CL-0003 **N-005** → `reduce_risk` *"someone who has never taken a risk
  with money"* ✅; **N-006** → `reduce_risk` *"she would prefer 'something
  safe and boring'"* ✅

Check distribution: `other` 76, `needs_liquidity_by` 21, `reduce_risk` 9,
`avoid_region` 3, `avoid_sector` 3, `refuse_realise_loss` 2.

**The quote guard fired zero times on real output.** All five rejections
across 20 clients were the *target-required* guard —
`needs_liquidity_by` claims with no date. So the model quoted faithfully
in all 114 claims and invented nothing.

Recorded honestly, because it cuts both ways: the guard that matters most
(Principle IV) is **currently unexercised by live output**. It is proven
by unit test against a fabricated quote, not by having caught the model
out. That is a weaker form of evidence than "it caught three", and the
distinction belongs in the record rather than being rounded up.

---

## R4 — Can seeds be matched against a derived theme label?

**Decision**: **No.** Source fields only. This is the subtlest trap in the
spec.

Matching the target against `theme_sector` / `theme_issuer` *also* reaches
42.1343% — so **the wrong implementation passes the acceptance test.** It
works only because spec 001 labels one theme
`"Global Energy Majors ADR + Pacific Orient Shipping"`, and that label
contains the word "Shipping". The energy fund would be pulled into the
finding by a string **this pipeline wrote**, not by anything the bank's
data says.

Three reasons it is excluded:

1. **Circular.** The evidence for the finding would partly be our own
   output.
2. **Fragile.** Rewording a label — a cosmetic change — silently changes a
   headline figure.
3. **Less explicable.** The two-step chain can be said out loud: *three
   positions are shipping by name; the theme they sit in is 42%.* The
   label match cannot.

Guarded by `test_seeds_never_match_a_derived_theme_label`, which asserts
against a constructed row whose only mention of the target is in the two
derived columns. Real data has no such row — every theme label is built
from words that also appear in a source field — so the guard needs a
synthetic case to be provable at all.

---

## R5 — Temperature 0 is not achievable. **Constitutional conflict.**

**Discovered during implementation**, not planned for. Recorded here
because it changes what the constitution can require.

The constitution's Technology Standards stated, **at version 1.1.0**
(quoted here as it read before the amendment this section prompted):

> Model calls MUST run at build time only, **at temperature 0**, with the
> prompt committed alongside its output.

**Temperature cannot be set on any current model.** Sampling parameters
were removed from the Messages API; passing `temperature` returns:

```
TypeError: Messages.create() got an unexpected keyword argument 'temperature'
```

and on the wire, a 400. The installed SDK is 1.3.0, and
`messages.create` accepts no `temperature`, `top_p` or `top_k` at all. The
replacement lever is `output_config: {effort: ...}`, which controls
thinking depth, not sampling.

**Resolution — the requirement is met by a different and stronger
mechanism, and the substitution is stated rather than hidden:**

| Constitution asks for | What is built |
|---|---|
| temperature 0 | not available; `output_config: {effort: "low"}` instead |
| build-time calls only | ✅ extraction is explicit, never a side effect of running the pipeline |
| prompt committed with output | ✅ `derived/claims.json` carries prompt, model id, effort, per-client fingerprint and provenance |
| **determinism** (the actual goal, Principle VII) | ✅ **the committed cache** — byte-identical every run |

The cache is the stronger guarantee. Temperature 0 reduces variance but
never eliminated it; a committed artifact is identical on every run
forever, which is what Principle VII actually asks for. The
`TEMPERATURE_NOTE` constant in `pipeline/claims.py` and the `determinism`
field in the cache both record this, so nobody reading either concludes
the requirement was quietly dropped.

**Amended — constitution 1.2.0, 22:47 SGT.** Flagged first, then amended
on the maintainer's instruction. Two things changed: the temperature
sentence was replaced with the committed-artifact requirement, and the
call inventory was corrected from "four calls" to 24 — the original text
omitted claim extraction entirely, though Principle V has always required
the model to "convert a stated wish into a testable claim". The duplicate
copy in `alamazing-all-specs.md` was brought into line in the same edit,
as Governance requires.

**One other API-drift correction.** The plan named Sonnet, on a
cost-per-token argument I invented. Current guidance is to default to the
most capable model and never downgrade for cost without being asked, so
the model is `claude-opus-5`. Extraction runs 20 times at build time and
is then committed forever, so per-token cost is close to irrelevant here
and I should not have optimised for it.

---

## Resolved

Four questions closed before implementation; one conflict surfaced during
it and resolved in the open. Two corrections to my own plan (model choice,
and the temperature assumption), and one trap identified where the wrong
code passes the test (R4).

The spec's figures reproduce exactly: **42.1343%** look-through,
**33.1979%** direct, **71.4606%** equity.
