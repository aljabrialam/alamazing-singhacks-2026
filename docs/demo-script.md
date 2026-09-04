# Demo Script

**3 minutes. Rehearsed, not improvised — their slide says presentation
impacts scoring.**

Record once at ~16:00. This is both the submission video and the
wifi-failure fallback.

---

## The run

| Time | Screen | Say |
|---|---|---|
| 0:00–0:20 | S1 call list | "This is Priscilla Ong. She runs the Asia desk and looks after twenty families, from eight million to eighty-eight. She can properly watch about three of them." |
| 0:20–0:35 | S1 | "Julius Baer says every client gets a relationship manager supported by a team of specialists. We built one more — one that reads everything overnight and tells her what doesn't add up." |
| 0:35–1:00 | S2 open | "Top of her list this morning is Abdullah Al-Mansoori. He built his money in Gulf logistics and marine chartering. His stated objective, in the bank's own file, is to build wealth **outside** the Gulf and **outside** shipping." |
| 1:00–1:30 | S2 exposure | "Today, 42% of his portfolio is shipping and energy. A shipping fund, a shipping stock, an energy fund — and a note whose underlying is a worst-of basket on two names he already owns. It isn't diversification. It's leverage on the same bet." |
| 1:30–1:50 | S2 mandate panel | "Here's the part that matters. Every mandate band is respected. Equity 58 against a 40-to-65 range. Structured products 12.9 against a 15 cap. No position over the single-name limit. **His portfolio passes every compliance check this bank runs, and it's 42% one bet.**" |
| 1:50–2:15 | Evidence drawer | "Every sentence traces. These are the holdings rows. This is the event — the Strait of Hormuz closing in March — from the bank's own event log, not the model's memory. And this is Priscilla's note from April, where she wrote that his portfolio isn't uncorrelated with his business." |
| 2:15–2:40 | S2 opening line | "On the twelfth of August he asked her what happens if the Strait reopens. Her note says: we have not modelled this. Two weeks later, nobody has answered him. So the brief ends with the sentence she could open with." *Read it aloud.* |
| 2:40–2:52 | Actions + S3 | "She keeps it, rejects it, or annotates it. She owns the advice. And this screen is what the system isn't sure about — because we'd rather say we don't know than sound confident and be wrong." |
| 2:52–3:00 | S1 | "Twenty clients. One relationship manager. Now she knows who to call first, and what to say." |

---

## The three beats that carry it

**1:30 — compliance-clean, 42% one bet.** This is the argument. Every
other team will show a mandate breach. We show a portfolio with no breach
at all that is still dangerous. Slow down here.

**2:15 — the unanswered question.** He asked something on 12 August and
nobody replied. That converts the demo from analytics into advisory in one
sentence.

**2:40 — she decides.** Twelve seconds, and it answers Strategic Impact.

---

## Memorised, verbatim

**Open:** "This is Priscilla Ong. She runs the Asia desk and looks after
twenty families. She can properly watch about three of them."

**Close:** "Twenty clients. One relationship manager. Now she knows who to
call first, and what to say."

---

## Rules

- Read the opening line aloud at 2:40. Don't paraphrase it — the prose is
  the product.
- Don't show the architecture diagram. It's in the README.
- Don't say "AI-powered", "leverage", "seamless", or "recommend".
- If a judge asks why not the retiree who won't sell at a loss: that's
  their worked example, so every team will demo it. Say so plainly.

## If you have 5 minutes instead of 3

Add Margarethe Voss-Brenner after the Abdullah beat:

> "Second on the list is a widow who inherited her husband's portfolio in
> February. She's profiled Conservative. The portfolio is 71% equity
> against a 30% ceiling. Nobody chose that — it arrived that way. So we
> classify it neither as drift nor as client-directed, but as inherited,
> because it's a different conversation. And she has a 3.4 million euro
> tax bill due before year end against 17% liquidity."


---

## Q&A — the correctness question

A banking judge will ask how the RM knows the output is right. This is the
answer. **Do not put it in the three minutes** — the evidence panel already
shows the proof, and explaining determinism on stage costs twenty seconds
the run does not have.

### The short answer, if asked

> "The facts are reproducible — same inputs, same output, and there is a
> test for it. What is not automatic is the judgement about which findings
> matter, which is why Priscilla can reject any of them and why nothing
> reaches a client without her."

### If pushed further

> "Before this went near production you would run it in shadow mode for a
> quarter. Every finding logged, every RM decision recorded. At the end you
> have measured precision — how often it flagged something she agreed was
> worth a call. That is the confusion matrix a bank would actually require,
> and it is a real number rather than a claim."

### The three layers, if they want detail

**Nothing the model produces is a figure.** 42.13% is a groupby. The band
comparison is `actual > max_pct`. The scenario is arithmetic over stored
prices. Same class of computation as the bank's existing portfolio system.

**Every claim resolves to rows.** Click a sentence, see the holdings rows
and the values summed. That is stronger than accuracy — it is
*checkability*. An auditor does not want a correct black box; they want a
wrong answer they can trace.

**Determinism.** Same inputs, same output, forever, proven by test. A
system that answers differently on Tuesday than Monday cannot be signed off.

### Say the limit yourself

The facts are verifiable. The **selection** is a modelling choice — we
treat the note's worst-of basket as full exposure to all three underlyings,
which overstates it. That is on the uncertainty screen, and naming it
before a judge does is worth more than the extra decimal place.

### The structural reassurance

The system never touches money, never contacts a client, and never decides.
It produces a briefing an experienced banker reads and either uses or bins.
**The failure mode of a wrong finding is two wasted minutes, not a wrong
trade.**
