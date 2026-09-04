"""Spec 008 — D7, what the portfolio did and why.

Building Block 1 of the challenge brief, and the one it lists first:
*"Explain what a portfolio did and why, connecting real market and
geopolitical events to the individual holdings that moved."*

The brief also calls the loop this closes *"the core of the whole
challenge"* — position, change, cause.

**The trap this module exists to avoid.** The hero client's portfolio is
+6.02m between the pre-conflict snapshot and today. Reported as one
number, the market appears to have given him six million. It did not:

    mid-window  Structured Product Subscription
                300,000 units @ HKD 100.00  =  HKD 30,000,000 paid in
    latest      holding                     =  HKD 32,460,000

He **paid in about USD 3.84m**. Only ~2.18m is market movement. A single
"portfolio change" figure is the wrong shape for the question regardless
of how carefully it is computed, and getting it wrong *flatters the bank*,
which is the class of error the brief warns about hardest.

So this detector reports **three buckets and never one total**: positions
held throughout, positions acquired in the window, positions disposed of.
Only the first is performance.

Reuses ``diff()`` and ``attribution()`` from spec 000 unchanged — they
were built and tested there and used nowhere until now.
"""

from __future__ import annotations

import pandas as pd

from pipeline.diff import attribution
from pipeline.events import events_touching
from pipeline.fx import to_usd
from pipeline.load import Book, latest, snapshots
from pipeline.divergence.d2_mandate import ACQUISITIONS, DISPOSALS

KIND = "D7"

# Below this share of the portfolio a mover is not worth naming in a
# briefing. A parameter, not a literal (Principle XI).
DEFAULT_MATERIAL_PCT = 1.0


def _flows(book: Book, client_id: str, date_then: str, date_now: str) -> dict:
    """Money in and out per instrument, inside the window.

    Keyed by instrument. The amount is in the transaction's own currency,
    converted to USD so it can be set against a market value — and if no
    rate exists the amount is carried unconverted and said so, never
    guessed (Principle IV).
    """
    transactions = book.transactions
    window = transactions[
        (transactions.client_id == client_id)
        & (transactions.trade_date > date_then)
        & (transactions.trade_date <= date_now)
        & (transactions.transaction_type.isin(ACQUISITIONS + DISPOSALS))
    ]

    out: dict[str, dict] = {}
    for _, row in window.iterrows():
        converted = to_usd(book, abs(float(row.amount)), row.currency, date_now)
        entry = out.setdefault(
            row.instrument_id,
            {"paid_in_usd": 0.0, "taken_out_usd": 0.0, "transactions": [],
             "unconverted": []},
        )
        if row.transaction_type in ACQUISITIONS:
            key = "paid_in_usd"
        else:
            key = "taken_out_usd"
        if converted["usd"] is None:
            entry["unconverted"].append(converted["note"])
        else:
            entry[key] += converted["usd"]
        entry["transactions"].append(
            {
                "transaction_id": row.transaction_id,
                "trade_date": row.trade_date,
                "transaction_type": row.transaction_type,
                "currency": row.currency,
                "amount": float(row.amount),
                "amount_usd": converted["usd"],
                "fx_note": converted["note"],
            }
        )
    return out


def explain(
    book: Book,
    client_id: str,
    date_then: str,
    date_now: str,
    material_pct: float = DEFAULT_MATERIAL_PCT,
) -> dict:
    """Three buckets. Never one number."""
    moves = attribution(book, client_id, date_then, date_now)
    if moves.empty:
        return {"held": [], "acquired": [], "disposed": []}

    flows = _flows(book, client_id, date_then, date_now)

    held, acquired, disposed = [], [], []
    for _, row in moves.iterrows():
        flow = flows.get(row.instrument_id)
        entry = {
            "instrument_id": row.instrument_id,
            "instrument_name": row.instrument_name,
            "asset_class": row.asset_class,
            "value_then_usd": float(row.value_a),
            "value_now_usd": float(row.value_b),
            "change_usd": float(row.d_value),
            "weight_change_pp": float(row.d_weight),
            "flow": flow,
        }

        appeared = row.value_a == 0 and row.value_b > 0
        vanished = row.value_b == 0 and row.value_a > 0

        if appeared or (flow and flow["paid_in_usd"] > 0 and row.value_a == 0):
            # Acquired in the window. Its value change is money, not
            # performance — and the market movement on it is only the
            # difference between what was paid and what it is now worth.
            paid = flow["paid_in_usd"] if flow else None
            entry["paid_in_usd"] = paid
            entry["market_movement_usd"] = (
                float(row.value_b) - paid if paid else None
            )
            entry["is_performance"] = False
            acquired.append(entry)
        elif vanished:
            entry["is_performance"] = False
            disposed.append(entry)
        else:
            # Held throughout. This, and only this, is performance.
            entry["is_performance"] = True
            held.append(entry)

    # Material movers only — a briefing that names every position is a
    # statement, not a briefing.
    total_now = float(moves.value_b.sum())
    threshold = total_now * material_pct / 100.0

    # Market movement on positions acquired inside the window: what they
    # are worth now, less what was paid. Small, but it belongs in the
    # market bucket rather than the money bucket, and including it is what
    # makes the three buckets reconcile to the total exactly.
    acquired_market = sum(
        a["market_movement_usd"] or 0.0
        for a in acquired
        if a.get("market_movement_usd") is not None
    )

    return {
        "date_then": date_then,
        "date_now": date_now,
        "held": [h for h in held if abs(h["change_usd"]) >= threshold],
        "acquired": acquired,
        "disposed": disposed,
        "market_movement_usd": sum(h["change_usd"] for h in held),
        "acquired_market_movement_usd": acquired_market,
        "paid_in_usd": sum(
            a.get("paid_in_usd") or 0.0 for a in acquired
        ),
        "taken_out_usd": sum(
            (d["flow"]["taken_out_usd"] if d.get("flow") else 0.0)
            for d in disposed
        ),
        "total_change_usd": float(moves.d_value.sum()),
        "portfolio_now_usd": total_now,
    }


def detect(
    book: Book,
    client_id: str,
    date_then: str | None = None,
    date_now: str | None = None,
    material_pct: float = DEFAULT_MATERIAL_PCT,
) -> list[dict]:
    """One finding explaining the window, or none if nothing moved."""
    dates = snapshots(book)
    date_now = date_now or latest(book)
    date_then = date_then or dates[1]
    date_then, date_now = sorted([date_then, date_now])

    for date in (date_then, date_now):
        if date not in dates:
            raise ValueError(f"{date!r} is not a snapshot in this book")

    result = explain(book, client_id, date_then, date_now, material_pct)
    if not result["held"] and not result["acquired"] and not result["disposed"]:
        return []

    events = events_touching(book, client_id, date_then, date_now)

    return [
        {
            "client_id": client_id,
            "kind": KIND,
            "severity": 3,
            "confidence": "high",
            "headline": _headline(result),
            "detail": _detail(result, events),
            "window": {"from": date_then, "to": date_now},
            "held": result["held"],
            "acquired": result["acquired"],
            "disposed": result["disposed"],
            "market_movement_usd": result["market_movement_usd"],
            "acquired_market_movement_usd": result[
                "acquired_market_movement_usd"
            ],
            "paid_in_usd": result["paid_in_usd"],
            "taken_out_usd": result["taken_out_usd"],
            "total_change_usd": result["total_change_usd"],
            "evidence": _evidence(result, events, date_then, date_now),
            "events": sorted(events.event_date) if not events.empty else [],
            "unsure_about": _unsure(result),
            "classification": None,
        }
    ]


def _headline(result: dict) -> str:
    movement = result["market_movement_usd"]
    paid = result["paid_in_usd"]

    if paid > 0:
        return (
            f"The portfolio is up {result['total_change_usd'] / 1e6:+.2f}m "
            f"since {result['date_then']} — but "
            f"{paid / 1e6:.2f}m of that is money paid in, not performance."
        )
    return (
        f"The portfolio moved {movement / 1e6:+.2f}m on market prices "
        f"since {result['date_then']}."
    )


def _detail(result: dict, events: pd.DataFrame) -> str:
    parts = []

    # The separation, stated before any figure is attributed to skill.
    if result["paid_in_usd"] > 0:
        parts.append(
            f"Of the {result['total_change_usd'] / 1e6:+.2f}m change since "
            f"{result['date_then']}, "
            f"{result['paid_in_usd'] / 1e6:.2f}m is new money and "
            f"{result['market_movement_usd'] / 1e6:+.2f}m is market "
            f"movement on positions held throughout. Those are different "
            f"things and the first is not performance."
        )
    else:
        parts.append(
            f"The portfolio moved {result['market_movement_usd'] / 1e6:+.2f}m "
            f"on market prices since {result['date_then']}, with no money "
            f"paid in or taken out."
        )

    movers = sorted(result["held"], key=lambda h: -abs(h["change_usd"]))[:4]
    if movers:
        parts.append(
            "What moved: "
            + "; ".join(
                f"{m['instrument_name']} {m['change_usd'] / 1e6:+.2f}m"
                for m in movers
            )
            + "."
        )

    for entry in result["acquired"]:
        paid = entry.get("paid_in_usd")
        if paid:
            parts.append(
                f"{entry['instrument_name']} was subscribed inside this "
                f"window — {paid / 1e6:.2f}m paid in, now worth "
                f"{entry['value_now_usd'] / 1e6:.2f}m. The "
                f"{entry['change_usd'] / 1e6:+.2f}m it adds to the "
                f"portfolio is almost all the subscription, not a gain."
            )

    if not events.empty:
        cited = events.head(3)
        parts.append(
            "Events touching this client in the window: "
            + "; ".join(
                f"{row.event_date} — {row.description[:90]}"
                for _, row in cited.iterrows()
            )
            + "."
        )

    return " ".join(parts)


def _evidence(
    result: dict, events: pd.DataFrame, date_then: str, date_now: str
) -> list[dict]:
    evidence = [
        {
            "file": "holdings.csv",
            "rows": sorted(
                h["instrument_id"]
                for h in result["held"] + result["acquired"] + result["disposed"]
            ),
            "note": (
                f"values at {date_then} and {date_now}; market movement "
                f"{result['market_movement_usd']:,.0f} USD on positions held "
                f"throughout"
            ),
        }
    ]

    flow_rows = [
        t["transaction_id"]
        for group in (result["acquired"], result["disposed"])
        for entry in group
        if entry.get("flow")
        for t in entry["flow"]["transactions"]
    ]
    if flow_rows:
        evidence.append(
            {
                "file": "transactions.csv",
                "rows": sorted(flow_rows),
                "note": (
                    f"{result['paid_in_usd']:,.0f} USD paid in, "
                    f"{result['taken_out_usd']:,.0f} USD taken out — "
                    f"excluded from performance"
                ),
            }
        )

    if not events.empty:
        evidence.append(
            {
                "file": "event_log.csv",
                "rows": sorted(events.event_date),
                "note": "; ".join(
                    f"{row.event_date} {row.description[:70]}"
                    for _, row in events.iterrows()
                ),
            }
        )

    return evidence


def _unsure(result: dict) -> str:
    parts = []

    unconverted = [
        note
        for group in (result["acquired"], result["disposed"])
        for entry in group
        if entry.get("flow")
        for note in entry["flow"]["unconverted"]
    ]
    if unconverted:
        parts.append(
            "Some flows could not be converted to USD: "
            + "; ".join(sorted(set(unconverted)))
            + "."
        )

    parts.append(
        "Events are matched to this client by the transmission channels "
        "named in the event log against the sectors and asset classes they "
        "hold. That is a keyword match, so an event may be listed here "
        "without having moved any particular position — the attribution "
        "above is arithmetic, the causal link is not."
    )
    return " ".join(parts)
