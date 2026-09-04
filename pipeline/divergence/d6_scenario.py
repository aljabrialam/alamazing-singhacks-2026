"""Spec 005 — D6, answering the question the client actually asked.

Spec 004 finds that on 12 August he asked what happens to his portfolio if
the Strait reopens and normalises, and that Priscilla's note records
*"We have not modelled this."*

**This module models it.**

That sequence is the product in two moves. Every other detector tells her
something about a portfolio. This one closes a loop with a person: he
asked in August, nobody replied, and she walks into the next meeting with
a number.

The answer is the uncomfortable one. He is not asking about a crash — he
is asking about **good news**, a de-escalation, the world calming down.
And good news costs him roughly 2.5 million in the portfolio *and* reduces
his business earnings in the same week, because the portfolio he asked to
be uncorrelated with his Gulf business is not uncorrelated with it.

**No model call, no forecast, no volatility assumption.** A ratio of two
stored prices applied to a market value. Block 7 says so three ways and it
is also what makes the answer defensible: there is no judgement in it to
argue with.

The series and both dates are parameters. "What if the Strait reopens" is
one call; "what if rates fall" is the same function with a different
series and two different dates (Principle XI).

Contract: ``specs/005-scenario/contracts/scenario.md``
"""

from __future__ import annotations

import pandas as pd

from pipeline.load import Book, client_weights, snapshots
from pipeline.divergence.d3_hidden import look_through, referenced_names

KIND = "D6"

# Match a referenced basket name to an instrument on its first two words,
# the same rule spec 001 verified reaches the intended instruments.
_MATCH_WORDS = 2


def _price(book: Book, instrument_id: str, date: str):
    """An instrument's price at a snapshot, or None."""
    column = f"price_{date}"
    if column not in book.instruments.columns:
        return None
    row = book.instruments[book.instruments.instrument_id == instrument_id]
    if row.empty:
        return None
    value = row.iloc[0][column]
    return None if pd.isna(value) or value == 0 else float(value)


def _ratio(book: Book, instrument_id: str, date_then: str, date_now: str):
    """then / now, from prices. **Not** from market values.

    Market value embeds quantity, which changes when a position is
    traded. Repricing an instrument to a past date is a question about
    price. The two differ measurably on this data.
    """
    then = _price(book, instrument_id, date_then)
    now = _price(book, instrument_id, date_now)
    if then is None or now is None:
        return None
    return then / now


def _match_key(name: str) -> str:
    return " ".join(str(name).split()[:_MATCH_WORDS]).lower()


def _basket_legs(book: Book, row: pd.Series) -> list[dict]:
    """Every leg of a structured product's basket, held or not.

    A leg the client does not hold still matters: a worst-of note pays on
    whichever underlying falls furthest, and that may be a name he never
    owned. Those legs cannot drive the headline — the recorded figure uses
    a held leg — but they are reported, because the uncertainty runs
    against him.
    """
    legs = []
    for name in referenced_names(row):
        key = _match_key(name)
        match = book.instruments[
            book.instruments.instrument_name.str.lower().str.contains(
                key, regex=False
            )
            & (book.instruments.instrument_id != row.instrument_id)
        ]
        if match.empty:
            continue
        legs.append(
            {
                "name": name,
                "instrument_id": match.iloc[0].instrument_id,
                "instrument_name": match.iloc[0].instrument_name,
            }
        )
    return legs


def reprice(
    book: Book,
    client_id: str,
    date_now: str,
    date_then: str,
    instrument_ids: list[str] | None = None,
) -> dict:
    """Reprice a client's positions from ``date_now`` back to ``date_then``."""
    available = snapshots(book)
    for date in (date_now, date_then):
        if date not in available:
            raise ValueError(
                f"{date!r} is not a snapshot in this book. "
                f"available: {available}"
            )

    # Order-independent: the earlier date is the comparison state whichever
    # way the arguments arrive. Reversed arguments must not silently invert
    # the sign of the answer.
    date_then, date_now = sorted([date_now, date_then])

    resolved = look_through(book, client_id, date_now)
    if resolved.empty:
        return {"positions": [], "total_impact_usd": 0.0, "notes": []}

    if instrument_ids is None:
        # The affected theme is the one spec 001's concentration finding
        # names, so the scenario reprices exactly the positions the client
        # is being told he is concentrated in.
        themed = resolved[resolved.theme_sector.notna()]
        instrument_ids = sorted(themed.instrument_id)

    held = resolved[resolved.instrument_id.isin(instrument_ids)]
    positions, notes = [], []
    held_ratios: dict[str, float] = {}

    # Which of these the client actually held at the earlier date.
    #
    # **This is the gate, not price availability.** Every structured
    # product in this book is par-indexed to exactly 100.0 at the first
    # snapshot, so the price column is populated for dates *before the
    # note existed*. A note subscribed in April has a February "price" of
    # 101.6 — a backfilled index, not an observable market value.
    #
    # Repricing off it looks correct and is badly wrong: the note barely
    # moves from 100, so it captures none of the ~20% fall in the basket
    # it references. On this book that understates the scenario by a third
    # (0.25m instead of 0.82m) and would report -6.04% where the true
    # answer is -7.79%. A plausible number, arrived at by using a column
    # that should not have been trusted.
    existed_then = set(
        book.holdings_at(client_id, date_then).instrument_id
    )

    # First pass: positions the client actually held at both dates.
    for _, row in held.iterrows():
        if row.instrument_id not in existed_then:
            continue
        ratio = _ratio(book, row.instrument_id, date_then, date_now)
        if ratio is None:
            continue
        held_ratios[row.instrument_id] = ratio
        value_now = float(row.market_value_usd)
        value_then = value_now * ratio
        positions.append(
            {
                "instrument_id": row.instrument_id,
                "instrument_name": row.instrument_name,
                "value_now_usd": value_now,
                "value_then_usd": value_then,
                "impact_usd": value_then - value_now,
                "ratio": ratio,
                "proxied_from": None,
            }
        )

    # Second pass: positions that did not exist at the earlier date.
    alternatives = []
    for _, row in held.iterrows():
        if row.instrument_id in held_ratios:
            continue

        legs = _basket_legs(book, row)
        if not legs:
            notes.append(
                f"{row.instrument_name} has no price at {date_then} and no "
                f"basket reference to proxy from, so it is excluded from "
                f"this scenario rather than estimated."
            )
            continue

        # A worst-of note pays on its worst leg. Among the legs the client
        # holds, choose the one that fell furthest.
        scored = []
        for leg in legs:
            ratio = _ratio(book, leg["instrument_id"], date_then, date_now)
            if ratio is None:
                continue
            scored.append({**leg, "ratio": ratio, "held": leg["instrument_id"] in held_ratios})
        if not scored:
            notes.append(
                f"{row.instrument_name} could not be proxied — no basket "
                f"leg has a price at {date_then}. Excluded."
            )
            continue

        held_legs = [s for s in scored if s["held"]]
        chosen = min(held_legs or scored, key=lambda s: s["ratio"])
        value_now = float(row.market_value_usd)
        value_then = value_now * chosen["ratio"]

        positions.append(
            {
                "instrument_id": row.instrument_id,
                "instrument_name": row.instrument_name,
                "value_now_usd": value_now,
                "value_then_usd": value_then,
                "impact_usd": value_then - value_now,
                "ratio": chosen["ratio"],
                "proxied_from": chosen["instrument_id"],
            }
        )
        notes.append(
            f"{row.instrument_name} was not held at {date_then}, so it is "
            f"repriced using {chosen['instrument_name']}, the "
            f"worst-performing leg of its basket that the client holds "
            f"({(chosen['ratio'] - 1) * 100:+.2f}%). Its own price series "
            f"is par-indexed and carries a value for dates before the note "
            f"existed, which would understate the move; that value is not "
            f"used."
        )

        # A leg he does not hold that fell further. The headline cannot use
        # it, but the client should know the direction.
        worse = [
            s
            for s in scored
            if not s["held"] and s["ratio"] < chosen["ratio"]
        ]
        for leg in sorted(worse, key=lambda s: s["ratio"]):
            alternatives.append(
                {
                    "instrument_id": row.instrument_id,
                    "leg_instrument_id": leg["instrument_id"],
                    "leg_name": leg["instrument_name"],
                    "leg_ratio": leg["ratio"],
                    "impact_usd": value_now * leg["ratio"] - value_now,
                }
            )

    positions.sort(key=lambda p: p["instrument_id"])
    return {
        "date_now": date_now,
        "date_then": date_then,
        "positions": positions,
        "total_impact_usd": sum(p["impact_usd"] for p in positions),
        "alternatives": alternatives,
        "notes": notes,
    }


def _series_at(book: Book, series_id: str, date: str):
    market = book.market
    row = market[
        (market.series_id == series_id) & (market.snapshot_date == date)
    ]
    if row.empty:
        return None
    return {
        "value": float(row.iloc[0].value),
        "unit": str(row.iloc[0].unit),
        "series_name": str(row.iloc[0].series_name),
    }


def _second_order(book: Book, client_id: str, themes: list[str]) -> dict | None:
    """Does the same event hit the client's business?

    **Quoted, never inferred.** The tempting version reasons about his
    industry — Gulf logistics, therefore charter rates, therefore earnings
    fall. That chain is plausible and this system must not make it. What it
    can do is report that *he said it*: a note records his own view that
    charter rates stay elevated while the situation is unresolved.

    The system cites him. That is the difference between an auditable
    finding and a model free-associating about geopolitics, which the brief
    names as the thing to avoid.
    """
    client = book.client(client_id)
    source_of_wealth = str(getattr(client, "source_of_wealth", "") or "")
    if not source_of_wealth:
        return None

    # **The link is established by the client's own words, not by matching
    # strings against their industry.**
    #
    # A first attempt tried to prove the overlap by tokens — theme words
    # against the source of wealth. It found nothing, and it was the wrong
    # idea anyway: the theme here is labelled from sectors ("Energy +
    # Industrials") while the business is described as "marine
    # chartering". No shared word, and a real connection.
    #
    # Closing that gap by reasoning about industries is exactly what
    # Principle IV forbids — the system would be asserting that shipping
    # equities and a chartering business move together, which is a market
    # view it has no standing to hold. What it can do is find where the
    # *client* said it. So the trigger is a note in which they linked the
    # two, and the source of wealth is reported as the context that makes
    # their statement legible.
    linked = []
    for note in book.notes_for(client_id):
        text = str(note.get("note", ""))
        lowered = text.lower()
        if any(
            marker in lowered
            for marker in (
                "operating business",
                "same conditions",
                "uncorrelated",
                "his business",
                "her business",
                "their business",
            )
        ):
            linked.append(note)

    if not linked:
        # No recorded statement, so no second-order claim. The source of
        # wealth alone is not evidence of a link.
        return None

    return {
        "source_of_wealth": source_of_wealth,
        "themes": themes,
        "basis": (
            "the client stated the link between their business and this "
            "exposure; the system reports their statement rather than "
            "inferring a relationship"
        ),
        "notes": [
            {
                "note_id": n.get("note_id"),
                "note_date": n.get("note_date"),
                "quote": str(n.get("note", "")).strip(),
            }
            for n in linked
        ],
    }


def detect(
    book: Book,
    client_id: str,
    series_id: str,
    date_now: str,
    date_then: str,
) -> list[dict]:
    """The scenario, as a finding.

    ``series_id``, ``date_now`` and ``date_then`` are arguments. Nothing
    is baked in (Principle XI, FR-001).
    """
    result = reprice(book, client_id, date_now, date_then)
    if not result["positions"]:
        return []

    weighted = client_weights(book, client_id, result["date_now"])
    total_portfolio = float(weighted.market_value_usd.sum())
    impact = result["total_impact_usd"]
    impact_pct = impact / total_portfolio * 100.0

    now = _series_at(book, series_id, result["date_now"])
    then = _series_at(book, series_id, result["date_then"])

    resolved = look_through(book, client_id, result["date_now"])
    themes = sorted(set(resolved.theme_sector.dropna()))
    second_order = _second_order(book, client_id, themes)

    alt_total = impact + sum(a["impact_usd"] - next(
        p["impact_usd"] for p in result["positions"]
        if p["instrument_id"] == a["instrument_id"]
    ) for a in result["alternatives"])

    return [
        {
            "client_id": client_id,
            "kind": KIND,
            "severity": 5,
            "confidence": "high",
            "headline": _headline(impact, impact_pct, series_id, now, then),
            "detail": _detail(
                result, impact, impact_pct, series_id, now, then, second_order
            ),
            "scenario": {
                "series_id": series_id,
                "series_name": now["series_name"] if now else None,
                "value_now": now["value"] if now else None,
                "value_then": then["value"] if then else None,
                "unit": now["unit"] if now else None,
                "date_now": result["date_now"],
                "date_then": result["date_then"],
            },
            "positions": result["positions"],
            "total_impact_usd": impact,
            "total_impact_pct": impact_pct,
            "portfolio_usd": total_portfolio,
            "alternatives": result["alternatives"],
            "alternative_total_impact_usd": (
                alt_total if result["alternatives"] else None
            ),
            "second_order": second_order,
            "evidence": _evidence(result, series_id, now, then, second_order,
                                  client_id),
            "events": [],
            "unsure_about": _unsure(result, impact, alt_total, total_portfolio),
            "classification": None,
        }
    ]


def _headline(impact, impact_pct, series_id, now, then) -> str:
    move = ""
    if now and then:
        move = (
            f" if {now['series_name']} returns from {now['value']:g} to "
            f"{then['value']:g} {now['unit']}"
        )
    return (
        f"Around USD {abs(impact):,.0f} comes off the portfolio"
        f"{move} — {abs(impact_pct):.2f}% of it."
    )


def _detail(result, impact, impact_pct, series_id, now, then, second_order):
    parts = []

    if now and then:
        parts.append(
            f"Repricing the affected positions to "
            f"{result['date_then']}, when {now['series_name']} was "
            f"{then['value']:g} {now['unit']} against {now['value']:g} "
            f"today:"
        )
    else:
        parts.append(f"Repricing the affected positions to {result['date_then']}:")

    itemised = [
        f"{position['instrument_name']} "
        f"{position['value_now_usd'] / 1e6:.2f}m to "
        f"{position['value_then_usd'] / 1e6:.2f}m "
        f"({position['impact_usd'] / 1e6:+.2f}m)"
        for position in sorted(
            result["positions"], key=lambda p: p["impact_usd"]
        )
    ]
    parts.append("; ".join(itemised) + ";")

    parts.append(
        f"a total of {impact / 1e6:+.2f}m, or {impact_pct:+.2f}% of the "
        f"portfolio."
    )

    parts.append(
        "This is the outcome most people would call good news, which is "
        "what makes it worth raising."
    )

    if second_order and second_order["notes"]:
        note = second_order["notes"][0]
        parts.append(
            f"The same event reaches the client twice. Their recorded "
            f"source of wealth is \"{second_order['source_of_wealth']}\", "
            f"and in note {note['note_id']} of {note['note_date']} they "
            f"said so themselves: \"{note['quote']}\" So a de-escalation "
            f"takes value from the portfolio and from the business in the "
            f"same week."
        )
    elif second_order:
        parts.append(
            f"The client's recorded source of wealth, "
            f"\"{second_order['source_of_wealth']}\", shares this theme, "
            f"so the same event may reach them twice. No note records "
            f"their own view of that link."
        )

    return " ".join(parts)


def _evidence(result, series_id, now, then, second_order, client_id):
    evidence = [
        {
            "file": "instruments.csv",
            "rows": sorted(p["instrument_id"] for p in result["positions"]),
            "note": "; ".join(
                f"{p['instrument_id']} {p['value_now_usd']:,.0f} -> "
                f"{p['value_then_usd']:,.0f}"
                + (
                    f" (proxied from {p['proxied_from']})"
                    if p["proxied_from"]
                    else ""
                )
                for p in result["positions"]
            ),
        }
    ]

    if now and then:
        evidence.append(
            {
                "file": "market_context.csv",
                "rows": [
                    f"{series_id}/{result['date_then']}",
                    f"{series_id}/{result['date_now']}",
                ],
                "note": (
                    f"{now['series_name']} {then['value']:g} at "
                    f"{result['date_then']}, {now['value']:g} at "
                    f"{result['date_now']} ({now['unit']})"
                ),
            }
        )

    if second_order:
        evidence.append(
            {
                "file": "clients.csv",
                "rows": [client_id],
                "note": f"source of wealth: {second_order['source_of_wealth']}",
            }
        )
        if second_order["notes"]:
            evidence.append(
                {
                    "file": "rm_notes.json",
                    "rows": [n["note_id"] for n in second_order["notes"]],
                    "note": "; ".join(
                        f"{n['note_id']} {n['note_date']}: \"{n['quote']}\""
                        for n in second_order["notes"]
                    ),
                }
            )

    return evidence


def _unsure(result, impact, alt_total, total_portfolio) -> str:
    parts = list(result["notes"])

    if result["alternatives"]:
        worst = min(result["alternatives"], key=lambda a: a["leg_ratio"])
        parts.append(
            f"On a strict worst-of reading the note would reprice off "
            f"{worst['leg_name']}, which fell "
            f"{(worst['leg_ratio'] - 1) * 100:+.2f}% — further than any leg "
            f"the client holds. That leg cannot be used for the headline "
            f"because the client does not hold it, but on that basis the "
            f"total impact would be nearer "
            f"{alt_total / 1e6:+.2f}m "
            f"({alt_total / total_portfolio * 100:+.2f}%). The uncertainty "
            f"runs against the client, not in their favour."
        )

    parts.append(
        "This is arithmetic over stored prices at two dates. It is not a "
        "forecast, carries no probability, and assumes no volatility."
    )
    return " ".join(parts)
