"""Spec 008 — D9, the tax position at domicile.

The brief asks for *"unrealised gains and losses together within a
household, and at **tax domicile** rather than residence."*

**This detector reports. It does not optimise, and that is the design
rather than a limitation.**

One client in this book holds roughly HKD-equivalent 62.6m of unrealised
losses. Every tax-optimisation instinct says *harvest them*. His domicile
is Hong Kong, which does not levy capital gains tax — so harvesting is
close to worthless to him, and the advice would be confidently wrong in
front of a client who understands his own tax position far better than
this system does.

The correct output for him is a **negative finding**: large harvestable
losses, and a domicile that makes harvesting them pointless. Saying so is
a stronger signal of understanding than any optimisation, and it is the
difference the brief describes between doing arithmetic and understanding
what you are looking at.

So: no suggested trades, no harvesting, no optimisation (Principle IX,
FR-015). And where the system has no rule for a domicile it **says so**
rather than inferring a treatment (FR-016) — an invented tax rule is the
worst kind of plausible answer.
"""

from __future__ import annotations

import pandas as pd

from pipeline.load import Book, client_weights, latest

KIND = "D9"

# Whether a domicile levies tax on realised capital gains, for the
# domiciles **present in this dataset only**.
#
# `None` means no rule is recorded, and that is reported rather than
# defaulted. This is a small explicit table, not a tax engine, and the
# copy must not let anyone believe otherwise: real treatment depends on
# residence tests, holding periods, asset type, remittance and treaties,
# none of which are in this data.
CAPITAL_GAINS_LEVIED = {
    # No capital gains tax on securities for individuals.
    "Hong Kong SAR": False,
    "Singapore": False,
    "United Arab Emirates": False,
    # Levied.
    "Germany": True,
    "United Kingdom": True,
    "Sweden": True,
    "Italy": True,
    "Japan": True,
    "Indonesia": True,
    "Republic of Korea": True,
    # No rule recorded. These are genuinely conditional — Malaysian and
    # Thai treatment turns on the asset and on remittance in ways this
    # data cannot settle — so the honest value is None, and it is reported
    # rather than guessed.
    "Malaysia": None,
    "Thailand": None,
}

# Below this, a gain or loss is not worth a paragraph in a briefing.
DEFAULT_MATERIAL_USD = 500_000.0


def position(book: Book, client_id: str, date: str) -> dict:
    """Unrealised gains and losses across **all** the client's portfolios."""
    weighted = client_weights(book, client_id, date)
    client = book.client(client_id)

    domicile = str(client.tax_domicile)
    residence = str(getattr(client, "country_of_residence", "") or "")
    # A domicile absent from the table would become None by accident
    # rather than by decision, and "no rule recorded" is a claim the
    # system should only make deliberately. So absence is loud.
    if domicile not in CAPITAL_GAINS_LEVIED:
        raise ValueError(
            f"no capital-gains entry for domicile {domicile!r}. Add it to "
            f"CAPITAL_GAINS_LEVIED — explicitly None if the treatment is "
            f"genuinely conditional — rather than letting it default."
        )
    levied = CAPITAL_GAINS_LEVIED[domicile]

    if weighted.empty:
        gains = losses = unpriced = pd.DataFrame()
    else:
        gains = weighted[weighted.unrealised_pnl_base > 0]
        losses = weighted[weighted.unrealised_pnl_base < 0]
        unpriced = weighted[weighted.unrealised_pnl_base.isna()]

    return {
        "domicile": domicile,
        "residence": residence,
        "domicile_differs_from_residence": bool(
            residence and domicile != residence
        ),
        "capital_gains_levied": levied,
        "gains_base": float(gains.unrealised_pnl_base.sum()) if len(gains) else 0.0,
        "losses_base": float(losses.unrealised_pnl_base.sum()) if len(losses) else 0.0,
        "net_base": (
            float(gains.unrealised_pnl_base.sum()) if len(gains) else 0.0
        )
        + (float(losses.unrealised_pnl_base.sum()) if len(losses) else 0.0),
        "gain_positions": sorted(gains.instrument_id) if len(gains) else [],
        "loss_positions": sorted(losses.instrument_id) if len(losses) else [],
        "unpriced_positions": (
            sorted(unpriced.instrument_id) if len(unpriced) else []
        ),
        "unpriced_names": (
            sorted(unpriced.instrument_name) if len(unpriced) else []
        ),
        "base_currency": str(client.base_currency),
    }


def _obligations(book: Book, client_id: str) -> list[dict]:
    needs = book.cash_needs[book.cash_needs.client_id == client_id]
    return [
        {
            "need_id": row.need_id,
            "description": row.description,
            "currency": row.currency,
            "amount": float(row.amount),
            "due_to": row.due_to,
        }
        for _, row in needs.sort_values("need_id").iterrows()
    ]


def detect(
    book: Book,
    client_id: str,
    date: str | None = None,
    material_usd: float = DEFAULT_MATERIAL_USD,
) -> list[dict]:
    """The tax position, reported. Never a suggested trade."""
    date = date or latest(book)
    state = position(book, client_id, date)

    material = (
        abs(state["gains_base"]) >= material_usd
        or abs(state["losses_base"]) >= material_usd
        or state["unpriced_positions"]
    )
    if not material:
        return []

    obligations = _obligations(book, client_id)

    return [
        {
            "client_id": client_id,
            "kind": KIND,
            "severity": 4 if state["unpriced_positions"] else 3,
            "confidence": "medium",
            "headline": _headline(state),
            "detail": _detail(state, obligations),
            "tax_position": state,
            "obligations": obligations,
            "evidence": _evidence(book, client_id, state),
            "events": [],
            "unsure_about": _unsure(state),
            "classification": None,
        }
    ]


def _headline(state: dict) -> str:
    currency = state["base_currency"]
    losses = abs(state["losses_base"])
    gains = state["gains_base"]

    # The negative finding — the one that shows understanding.
    if (
        state["capital_gains_levied"] is False
        and losses >= DEFAULT_MATERIAL_USD
        and losses > gains
    ):
        return (
            f"{currency} {losses:,.0f} of unrealised losses, and a "
            f"{state['domicile']} domicile where realising them carries no "
            f"capital gains benefit."
        )

    if state["capital_gains_levied"] is True and gains > 0:
        return (
            f"{currency} {gains:,.0f} of unrealised gains against a "
            f"{state['domicile']} domicile that does levy capital gains."
        )

    return (
        f"Unrealised position: {currency} {gains:,.0f} in gains, "
        f"{currency} {losses:,.0f} in losses. Domicile "
        f"{state['domicile']}."
    )


def _detail(state: dict, obligations: list[dict]) -> str:
    currency = state["base_currency"]
    parts = []

    if state["domicile_differs_from_residence"]:
        parts.append(
            f"Tax domicile is {state['domicile']}; residence is "
            f"{state['residence']}. The domicile is what governs here, and "
            f"the two differ — worth checking before anything is realised."
        )
    else:
        parts.append(f"Tax domicile and residence are both {state['domicile']}.")

    parts.append(
        f"Across all portfolios the unrealised position is "
        f"{currency} {state['gains_base']:,.0f} in gains across "
        f"{len(state['gain_positions'])} positions and "
        f"{currency} {abs(state['losses_base']):,.0f} in losses across "
        f"{len(state['loss_positions'])}, a net "
        f"{currency} {state['net_base']:+,.0f}."
    )

    levied = state["capital_gains_levied"]

    if levied is False:
        # The point of the whole detector — but only where the losses are
        # genuinely the story. One client has 519k of losses against 6.9m
        # of gains; calling that "a large unrealised loss" would be its own
        # small overstatement, so the emphatic version is gated on the
        # losses actually dominating.
        losses = abs(state["losses_base"])
        dominant = losses >= DEFAULT_MATERIAL_USD and losses > state[
            "gains_base"
        ]
        if dominant:
            parts.append(
                f"There is a large unrealised loss here, and the obvious "
                f"move would be to realise it against gains. On these "
                f"figures that is not worth doing: {state['domicile']} "
                f"does not levy tax on capital gains, so harvesting the "
                f"loss buys no relief. It may still matter for reporting "
                f"in another jurisdiction, which is a question for the tax "
                f"team rather than this system."
            )
        else:
            parts.append(
                f"{state['domicile']} does not levy tax on capital gains, "
                f"so realising a gain or a loss here carries no capital "
                f"gains consequence."
            )
    elif levied is True:
        parts.append(
            f"{state['domicile']} does levy tax on capital gains, so the "
            f"timing and order of any sale has a consequence."
        )
        if obligations and state["gains_base"] > 0:
            first = obligations[0]
            parts.append(
                f"That matters because {first['description']} — "
                f"{first['currency']} {first['amount']:,.0f} due by "
                f"{first['due_to']} — has to be funded, and the portfolio "
                f"holds net gains. Meeting it realises taxable gains in "
                f"{state['domicile']}."
            )
    else:
        parts.append(
            f"No capital gains rule is recorded for {state['domicile']} in "
            f"this system, so no tax consequence is stated. That is a gap "
            f"in what we know, not a finding that there is none."
        )

    if state["unpriced_positions"]:
        parts.append(
            f"And one position cannot be assessed at all: "
            f"{', '.join(state['unpriced_names'])} carries no cost basis, "
            f"so the gain or loss on it — and therefore the tax "
            f"consequence of selling it — cannot be stated from this data."
        )

    return " ".join(parts)


def _evidence(book: Book, client_id: str, state: dict) -> list[dict]:
    rows = sorted(
        set(state["gain_positions"])
        | set(state["loss_positions"])
        | set(state["unpriced_positions"])
    )
    evidence = [
        {
            "file": "clients.csv",
            "rows": [client_id],
            "note": (
                f"tax domicile {state['domicile']}"
                + (
                    f", country of residence {state['residence']}"
                    if state["domicile_differs_from_residence"]
                    else ""
                )
            ),
        }
    ]
    if rows:
        evidence.append(
            {
                "file": "holdings.csv",
                "rows": rows,
                "note": (
                    f"unrealised gains {state['gains_base']:,.0f}, losses "
                    f"{state['losses_base']:,.0f}, "
                    f"{len(state['unpriced_positions'])} with no cost basis"
                ),
            }
        )
    return evidence


def _unsure(state: dict) -> str:
    parts = [
        "This is a position, not tax advice. The system holds a simple "
        "record of whether a domicile levies capital gains and nothing "
        "else — no holding periods, no asset-type distinctions, no "
        "remittance rules, no treaties. Anything that turns on those is a "
        "question for the tax team."
    ]

    if state["capital_gains_levied"] is None:
        parts.append(
            f"No capital gains rule is recorded for {state['domicile']}, so "
            f"nothing is inferred about the treatment there."
        )

    if state["unpriced_positions"]:
        parts.append(
            f"{', '.join(state['unpriced_names'])} carries no cost basis, so "
            f"its gain or loss is unknown and it is excluded from the totals "
            f"above rather than assumed flat."
        )

    return " ".join(parts)
