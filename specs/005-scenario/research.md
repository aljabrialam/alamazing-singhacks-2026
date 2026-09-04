# Phase 0 Research — Scenario (spec 005)

**Date**: 2026-09-04 · Run before the spec was written.

Five questions. Every acceptance figure reproduces. One finding refines
block 7's proxy instruction in a way worth stating on stage.

---

## R1 — Every figure in block 7's table reproduces

Repricing each holding to its pre-conflict snapshot, using
`price_<date>` from `instruments.csv`:

```
                                 now         then      impact    block 7
SYN-EQ-0025  Shipping fund   2,862,200    2,431,000   -431,200   -0.43m  ✅
SYN-ST-0104  Pacific Orient  3,676,056    2,953,846   -722,210   -0.72m  ✅
SYN-EQ-0008  Energy majors   2,878,800    2,343,600   -535,200   -0.54m  ✅
SYN-SP-0505  FCN Basket C    4,156,210    (no row)    see R2     -0.82m
                                          --------------------
                                    total  -2,509,429  = -2.509m  -2.5m  ✅
                                                        -7.790%   -7.8%  ✅
```

Portfolio total **USD 32,214,266** — `findings.md` records USD 32.2m. ✅

The series moves as recorded: **BRENT_USD_BBL 101.5** at the latest
snapshot, **72.4** at the pre-conflict one.

---

## R2 — The FCN has no pre-war row, and the proxy is right for a reason block 7 does not give

`SYN-SP-0505` settled in June, so it has no 2026-02-27 holdings row and no
pre-conflict price. Block 7 instructs: *"Proxy off SYN-ST-0104's ratio and
state this in the finding's `unsure_about`."*

That instruction is correct, and the reason is better than "pick one of
the underlyings". The note is a **worst-of basket** — on the downside it
pays on whichever underlying falls furthest, not the average. So the right
leg to proxy from is the *worst* performer among the basket, and among the
two he holds, Pacific Orient is worse:

```
SYN-ST-0104  Pacific Orient          -19.75%   <- worse of the two he holds
SYN-EQ-0008  Global Energy Majors    -18.59%
```

So block 7's proxy is not arbitrary; it is the structurally correct leg
among the names he owns. Worth saying out loud, because "we proxied off
one of the underlyings" invites a challenge and "a worst-of note reprices
off its worst leg" answers it.

**Use price ratios, not market-value ratios.** `market_value_usd` embeds
quantity, which changes when a position is traded; repricing an instrument
to a past date is a question about price. The two differ slightly here —
0.80251 on price against 0.80354 on market value — and the price-based
figure lands closer to the record (−7.790% against a recorded −7.8%).

---

## R3 — The third leg is in the book, and it fell furthest

**This refines the answer and block 7 does not mention it.**

The basket references three names: *Pacific Orient Shipping / Global
Energy Majors ADR / **Bara Nusantara Energy***. He holds the first two.
The third, `SYN-ST-0101`, **exists in the instrument file** — another
client holds it — and it moved more than either:

```
SYN-ST-0101  Bara Nusantara Energy   -23.10%   <- the true worst leg
```

So on a strict worst-of reading, the note reprices off Bara, not Pacific
Orient:

| Proxy leg | FCN impact | Total | Share of portfolio |
|---|---|---|---|
| Pacific Orient — block 7 | −820,819 | **−2,509,429** | **−7.790%** |
| Bara Nusantara — true worst-of | −960,253 | −2,648,863 | −8.223% |

The difference is **USD 139,000**, and it is outside the recorded
tolerance (−2.5m ± 0.1m; −7.8% ± 0.2).

**Decision**: the headline figure is block 7's — **−2.509m, −7.790%** —
because it is the recorded acceptance criterion and an Article VIII named
assertion. The worst-of figure is computed and reported in
`unsure_about`, stating that the strictly correct leg is a name he does
not hold, so the impact may be nearer −2.65m.

That is the honest handling: the recorded number is the headline, and the
direction of the uncertainty is stated. The uncertainty runs *against*
him — the true impact is likely slightly worse, not better — which is the
direction worth flagging to a client.

---

## R4 — The second-order effect is in the data, not inferred

```
source_of_wealth: "Entrepreneur - Gulf logistics, port services and
                   marine chartering"
```

And note **N-025**, in Priscilla's words:

> Client subscribed the shipping and energy FCN. **His view is that
> charter rates stay elevated while the Strait situation is unresolved.**
> Noted that his operating business benefits from the same conditions.
> **He said the point of the Asia portfolio was to be uncorrelated with
> the Gulf business. It currently is not.**

So the second-order effect is not an inference the system makes about his
business. It is **his own recorded view**, cited by note id: a
de-escalation lowers charter rates, which lowers his business earnings, in
the same week the portfolio loses 2.5m. Both halves are sourced —
`clients.csv` for the source of wealth, `rm_notes.json` N-025 for his
view.

This matters for Principle IV. The system is not modelling his company;
it is quoting him.

And the closing line writes itself from what is already in the file: the
diversification he asked for in 2014 — *"outside the Gulf region and
outside the shipping sector"* — is precisely what would have covered
this.

---

## R5 — The signature must not name the series or the dates

Block 7 is explicit, and Principle XI requires it:

```python
detect(book, client_id, series_id, date_now, date_then)
```

`BRENT_USD_BBL` and the two dates are **arguments**. The demo call passes
`latest(book)` and `snapshots(book)[1]` positionally, so the same function
answers "what if rates fall" with `UST_10Y_PCT` and two different dates.

**One design consequence worth recording.** The series is not actually
used in the arithmetic — the repricing runs off `price_<date>` columns,
not off the series value. The series is *context*: it names what changed
and by how much, so the finding can say "Brent 101.5 → 72.4" rather than
"prices were different". Passing it as a parameter is still right, because
the finding cites it as evidence and a different scenario cites a
different series.

Stated plainly so nobody later concludes the parameter is decorative: it
is evidence, not input.

---

## Resolved

Five questions. Every recorded figure reproduces. One refinement (R3) —
the true worst-of leg is a name he does not hold and fell further, so the
recorded −2.5m is very slightly optimistic; both figures are reported and
the recorded one is the headline.

No model call, no forecast, no volatility assumption. Arithmetic over
stored prices, as block 7 requires.
