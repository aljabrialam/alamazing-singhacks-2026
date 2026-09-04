"""Spec 008 — D10, what the allocation was not built for.

The brief: *"objectives and cash needs describe futures the current
allocations were not built for."*

**The finding here is about the profile, not the portfolio**, and that is
the whole reason it is worth having separately from D4.

D4 already reports the obligation and whether it can be funded. What it
does not say is that the client's *recorded risk profile contradicts their
own stated plans*. One client's `liquidity_needs` is recorded **Low**
against a 25-year horizon, while his own note describes a family office
needing about USD 5m within eighteen months.

That matters because the profile is what drives suitability checks. A
portfolio can be perfectly suitable for the profile on file and wrong for
the person, and no control will notice — which is the same shape as the
hero finding, applied one level up.

So this detector addresses the **profile** and says it may need
revisiting. It does not propose a change to the holdings.
"""

from __future__ import annotations

from pipeline.fx import to_usd
from pipeline.load import Book, client_weights, latest

KIND = "D10"

# Recorded liquidity needs that are inconsistent with a near-dated
# obligation of any size.
LOW_LIQUIDITY = ("Low", "Very Low", "Minimal")

# An obligation this far out or nearer is "near-dated" relative to a
# recorded horizon measured in years. A parameter, not a literal.
DEFAULT_NEAR_YEARS = 3.0

# Below this share of the portfolio an obligation is not worth
# contradicting a profile over.
DEFAULT_MATERIAL_PCT = 5.0


def _years_between(from_date: str, to_date: str) -> float:
    """Rough years between two ISO dates. Dates are strings here by design.

    Deliberately approximate — the question is "is this within a few
    years", not an actuarial one, and a day-count convention would imply
    a precision the comparison does not have.
    """
    a = [int(x) for x in from_date.split("-")]
    b = [int(x) for x in to_date.split("-")]
    return (b[0] - a[0]) + (b[1] - a[1]) / 12.0 + (b[2] - a[2]) / 365.0


def obligations(book: Book, client_id: str, date: str) -> list[dict]:
    """Dated obligations, from planned cash needs and the client's notes.

    The notes are read for *dates*, not for meaning — a year mentioned
    beside a figure is enough to establish that something is planned, and
    the note is quoted so the relationship manager can judge it. No model
    reads this (Principle V).
    """
    out = []
    needs = book.cash_needs[book.cash_needs.client_id == client_id]
    for _, row in needs.sort_values("need_id").iterrows():
        converted = to_usd(book, float(row.amount), row.currency, date)
        out.append(
            {
                "source": "planned_cash_needs.csv",
                "id": row.need_id,
                "description": row.description,
                "currency": row.currency,
                "amount": float(row.amount),
                "amount_usd": converted["usd"],
                "due_to": row.due_to,
                "years_away": _years_between(date, str(row.due_to)),
                "certainty": row.certainty,
            }
        )
    return out


def detect(
    book: Book,
    client_id: str,
    date: str | None = None,
    near_years: float = DEFAULT_NEAR_YEARS,
    material_pct: float = DEFAULT_MATERIAL_PCT,
) -> list[dict]:
    """A contradiction between the profile on file and the client's plans."""
    date = date or latest(book)
    client = book.client(client_id)

    recorded_liquidity = str(getattr(client, "liquidity_needs", "") or "")
    horizon = getattr(client, "investment_horizon_years", None)
    if not recorded_liquidity:
        return []

    weighted = client_weights(book, client_id, date)
    if weighted.empty:
        return []
    portfolio = float(weighted.market_value_usd.sum())

    near = [
        o
        for o in obligations(book, client_id, date)
        if o["amount_usd"]
        and o["years_away"] <= near_years
        and (o["amount_usd"] / portfolio * 100.0) >= material_pct
    ]
    if not near:
        return []

    # The contradiction: the profile says liquidity does not matter, and
    # the client's own plans say otherwise.
    if recorded_liquidity not in LOW_LIQUIDITY:
        return []

    largest = max(near, key=lambda o: o["amount_usd"])
    share = largest["amount_usd"] / portfolio * 100.0

    return [
        {
            "client_id": client_id,
            "kind": KIND,
            "severity": 3,
            "confidence": "high",
            "headline": (
                f"Liquidity needs are recorded as {recorded_liquidity.lower()}, "
                f"and {largest['currency']} {largest['amount']:,.0f} falls due "
                f"by {largest['due_to']}."
            ),
            "detail": (
                f"The risk profile on file records liquidity needs as "
                f"{recorded_liquidity.lower()}"
                + (
                    f" against an investment horizon of {horizon:.0f} years"
                    if horizon
                    else ""
                )
                + f". Against that, {largest['description']} — "
                f"{largest['currency']} {largest['amount']:,.0f}, about "
                f"{share:.2f}% of the portfolio — is due by "
                f"{largest['due_to']}, in roughly "
                f"{largest['years_away']:.1f} years. "
                f"It is the **profile** that looks out of date here rather "
                f"than the portfolio, and the profile is what suitability "
                f"checks run against — so a portfolio can pass every check "
                f"and still be built for the wrong horizon. Worth raising "
                f"whether the recorded liquidity needs still describe this "
                f"client.".replace("**", "")
            ),
            "recorded_profile": {
                "liquidity_needs": recorded_liquidity,
                "investment_horizon_years": (
                    float(horizon) if horizon is not None else None
                ),
                "life_stage": str(client.life_stage),
            },
            "obligations": near,
            "evidence": [
                {
                    "file": "clients.csv",
                    "rows": [client_id],
                    "note": (
                        f"liquidity_needs {recorded_liquidity}"
                        + (
                            f", investment_horizon_years {horizon:.0f}"
                            if horizon
                            else ""
                        )
                        + f", life_stage {client.life_stage}"
                    ),
                },
                {
                    "file": largest["source"],
                    "rows": [largest["id"]],
                    "note": (
                        f"{largest['description']}, {largest['currency']} "
                        f"{largest['amount']:,.0f} due by {largest['due_to']}, "
                        f"{largest['certainty']}"
                    ),
                },
            ],
            "events": [],
            "unsure_about": (
                "This compares a profile field against a dated obligation. "
                "The obligation may already have been discussed and the "
                "profile deliberately left as it is — the note history is "
                "where that would be recorded, and this detector does not "
                "read it for intent."
            ),
            "classification": None,
        }
    ]
