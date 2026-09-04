"""Spec 004 — D4, what meeting this obligation actually costs.

A client has a known bill and a known date. The naive check compares the
bill to liquid assets, finds it covered several times over, and reports
comfort. On this book that answer is wrong twice, in opposite directions:

**One client is more comfortable than recorded.** Block 6 calls her
liquidity "tight" on a cash-plus-fixed-income figure of 16.8%. By block
6's own rule — liquidity tier Daily or Weekly — she is 88.29% liquid,
because her equity is held in daily-dealing funds. She can pay easily.
What she cannot do is pay *without selling equity*, because cash plus
fixed income is almost exactly the size of the bill. That is the finding,
and it is worse than tight.

**One client is far less comfortable than the ratio suggests.** He shows
73% liquid against a 29% need — 2.5x coverage. But his only portfolio is
pledged as collateral against a facility sitting 0.59 percentage points
from a margin call. Selling to fund the obligation would push the
loan-to-value to 97.76% against a 70% trigger. **He cannot fund it by
selling.** A coverage ratio computed without the facility is exactly the
kind of confidently wrong number this project exists not to produce.

So this detector reports two liquidity figures, nets pledged collateral,
and computes what the loan-to-value becomes after the need is met.

See ``specs/004-liquidity-unanswered/research.md`` R2 and R3.
"""

from __future__ import annotations

import pandas as pd

from pipeline.fx import to_usd
from pipeline.load import Book, client_weights, latest, snapshots

KIND = "D4"

# Block 6: "Liquid = liquidity_tier in (Daily, Weekly). Illiquid and
# Monthly do not count toward a near-dated need."
LIQUID_TIERS = ("Daily", "Weekly")

# Asset classes that can meet an obligation without touching equity. Not a
# liquidity measure — a measure of what funding the bill consumes.
NEAR_CASH = ("Cash and Equivalents", "Fixed Income")

# Below this multiple of the need, the position is worth raising.
DEFAULT_COVER_THRESHOLD = 3.0


def _facility_history(book: Book, client_id: str, facility) -> list[dict]:
    """The facility at **every** snapshot, not just the latest.

    Spec 004 read one snapshot of five. That reports a position; it does
    not report a direction, and for a client walking toward a margin call
    the direction is the finding.

    A snapshot the facility does not carry is **omitted, never
    interpolated** — an invented loan-to-value is exactly the kind of
    plausible figure this project exists not to produce.
    """
    out = []
    for date in snapshots(book):
        row = {}
        for field in (
            "drawn",
            "collateral_market_value",
            "lending_value",
            "ltv_pct",
            "headroom",
        ):
            name = f"{field}_{date}"
            if name in facility.index and pd.notna(facility[name]):
                row[field] = float(facility[name])
        if "ltv_pct" not in row:
            continue
        out.append({"snapshot_date": date, **row})
    return out


def _read_trajectory(history: list[dict], margin_call_pct: float) -> dict:
    """What the trajectory says, in words rather than a chart.

    Two distinct causes, and telling them apart is the whole value:
    a rise while the drawn balance grew is a **decision**; a rise on an
    unchanged balance is the **collateral shrinking underneath the client**.
    """
    if len(history) < 2:
        return {}

    first, last = history[0], history[-1]
    change = last["ltv_pct"] - first["ltv_pct"]

    draws = []
    for previous, current in zip(history, history[1:]):
        before, after = previous.get("drawn"), current.get("drawn")
        if before is None or after is None or before == after:
            continue
        draws.append(
            {
                "snapshot_date": current["snapshot_date"],
                "from": before,
                "to": after,
                "delta": after - before,
                "kind": "drawdown" if after > before else "repayment",
            }
        )

    # Movement with no change in what is owed can only be the collateral.
    collateral_driven = []
    for previous, current in zip(history, history[1:]):
        if previous.get("drawn") != current.get("drawn"):
            continue
        rise = current["ltv_pct"] - previous["ltv_pct"]
        if rise <= 0:
            continue
        collateral_driven.append(
            {
                "snapshot_date": current["snapshot_date"],
                "ltv_rise_pp": rise,
                "collateral_fall": (
                    previous.get("collateral_market_value", 0)
                    - current.get("collateral_market_value", 0)
                ),
            }
        )

    return {
        "from_snapshot": first["snapshot_date"],
        "to_snapshot": last["snapshot_date"],
        "ltv_from": first["ltv_pct"],
        "ltv_to": last["ltv_pct"],
        "ltv_change_pp": change,
        "direction": "rising" if change > 0 else ("falling" if change < 0 else "flat"),
        "headroom_from": first.get("headroom"),
        "headroom_to": last.get("headroom"),
        "headroom_lost": (
            first.get("headroom", 0) - last.get("headroom", 0)
            if first.get("headroom") is not None
            and last.get("headroom") is not None
            else None
        ),
        "pp_to_margin_call": margin_call_pct - last["ltv_pct"],
        "balance_changes": draws,
        "collateral_driven_rises": collateral_driven,
    }


def _facility_for(book: Book, client_id: str, date: str):
    """The client's credit facility, if any, at this snapshot."""
    facilities = book.credit[book.credit.client_id == client_id]
    if facilities.empty:
        return None
    facility = facilities.iloc[0]

    def col(prefix):
        name = f"{prefix}_{date}"
        return float(facility[name]) if name in facility.index else None

    history = _facility_history(book, client_id, facility)

    return {
        "facility_id": facility.facility_id,
        "facility_type": facility.facility_type,
        "history": history,
        "trajectory": _read_trajectory(
            history, float(facility.margin_call_ltv_pct)
        ),
        "currency": facility.facility_ccy,
        "collateral_portfolio_id": facility.collateral_portfolio_id,
        "credit_limit": float(facility.credit_limit),
        "margin_call_ltv_pct": float(facility.margin_call_ltv_pct),
        "drawn": col("drawn"),
        "collateral_market_value": col("collateral_market_value"),
        "lending_value": col("lending_value"),
        "ltv_pct": col("ltv_pct"),
        "headroom": col("headroom"),
    }


def _ltv_after_sale(facility: dict, sale_amount_ccy: float) -> dict | None:
    """What the loan-to-value becomes if collateral is sold to fund a need.

    Selling pledged collateral reduces the lending value, which raises the
    loan-to-value on an unchanged drawn balance. The advance rate is
    implied from the facility's own numbers rather than assumed.
    """
    if not facility or not facility["lending_value"]:
        return None
    collateral = facility["collateral_market_value"]
    if not collateral:
        return None

    advance_rate = facility["lending_value"] / collateral
    remaining_lending_value = facility["lending_value"] - (
        sale_amount_ccy * advance_rate
    )
    if remaining_lending_value <= 0:
        return {
            "advance_rate_pct": advance_rate * 100.0,
            "lending_value_after": remaining_lending_value,
            "ltv_pct_after": None,
            "breaches_margin_call": True,
            "note": (
                "selling this much collateral would leave no lending value "
                "against the drawn balance"
            ),
        }

    ltv_after = facility["drawn"] / remaining_lending_value * 100.0
    return {
        "advance_rate_pct": advance_rate * 100.0,
        "lending_value_after": remaining_lending_value,
        "ltv_pct_after": ltv_after,
        "breaches_margin_call": ltv_after > facility["margin_call_ltv_pct"],
        "note": (
            f"funding the need from pledged collateral moves the "
            f"loan-to-value from {facility['ltv_pct']:.2f}% to "
            f"{ltv_after:.2f}% against a "
            f"{facility['margin_call_ltv_pct']:.0f}% margin-call threshold"
        ),
    }


def liquidity(book: Book, client_id: str, date: str) -> dict:
    """Two figures, because they answer two different questions."""
    weighted = client_weights(book, client_id, date)
    if weighted.empty:
        return {
            "total_usd": 0.0,
            "liquid_usd": 0.0,
            "liquid_pct": 0.0,
            "near_cash_usd": 0.0,
            "near_cash_pct": 0.0,
            "by_tier": {},
        }

    total = float(weighted.market_value_usd.sum())
    liquid = weighted[weighted.liquidity_tier.isin(LIQUID_TIERS)]
    near_cash = weighted[weighted.asset_class.isin(NEAR_CASH)]

    # Liquidity that is **not** pledged as collateral. This is the figure
    # that decides whether a facility actually constrains anything: a
    # client with an unpledged portfolio can fund an obligation from it
    # and never touch the collateral. One client here has only one
    # portfolio and it *is* the collateral — for him the facility governs
    # the whole answer, and for others it does not.
    pledged = set(
        book.credit[book.credit.client_id == client_id].collateral_portfolio_id
    )
    free = liquid[~liquid.portfolio_id.isin(pledged)]

    return {
        "total_usd": total,
        # Can this be funded by the date required?
        "liquid_usd": float(liquid.market_value_usd.sum()),
        "liquid_pct": float(liquid.w.sum()),
        "liquid_instrument_ids": sorted(liquid.instrument_id),
        # Can it be funded without touching pledged collateral?
        "free_liquid_usd": float(free.market_value_usd.sum()),
        "free_liquid_pct": float(free.w.sum()),
        "pledged_portfolio_ids": sorted(pledged),
        # What does funding it consume?
        "near_cash_usd": float(near_cash.market_value_usd.sum()),
        "near_cash_pct": float(near_cash.w.sum()),
        "by_tier": {
            tier: float(group.w.sum())
            for tier, group in weighted.groupby("liquidity_tier", sort=True)
        },
    }


def _obligations(book: Book, client_id: str, date: str) -> list[dict]:
    """Planned cash needs and uncalled commitments, converted to USD."""
    out = []

    needs = book.cash_needs[book.cash_needs.client_id == client_id]
    for _, need in needs.sort_values("need_id").iterrows():
        converted = to_usd(book, float(need.amount), need.currency, date)
        out.append(
            {
                "source": "planned_cash_needs.csv",
                "id": need.need_id,
                "description": need.description,
                "currency": need.currency,
                "amount": float(need.amount),
                "amount_usd": converted["usd"],
                "fx_note": converted["note"],
                "due_from": need.due_from,
                "due_to": need.due_to,
                "certainty": need.certainty,
                "recurrence": need.recurrence,
            }
        )

    commitments = book.commitments[book.commitments.client_id == client_id]
    for _, commitment in commitments.sort_values("commitment_id").iterrows():
        if float(commitment.uncalled) <= 0:
            continue
        converted = to_usd(
            book, float(commitment.uncalled), commitment.currency, date
        )
        out.append(
            {
                "source": "commitments.csv",
                "id": commitment.commitment_id,
                "description": (
                    f"uncalled commitment to {commitment.fund_name}"
                ),
                "currency": commitment.currency,
                "amount": float(commitment.uncalled),
                "amount_usd": converted["usd"],
                "fx_note": converted["note"],
                "due_from": commitment.expected_call_window,
                "due_to": commitment.expected_call_window,
                "certainty": "Expected",
                "recurrence": "Capital call",
            }
        )

    return out


def _concentration_theme(book: Book, client_id: str, date: str) -> str | None:
    """The issuer concentration D3 already found, if any.

    Named rather than restated: the collateral finding should say "it is
    the same concentration reported above", not compute it again.
    """
    from pipeline.divergence.d3_hidden import look_through

    resolved = look_through(book, client_id, date)
    if resolved.empty:
        return None
    themes = sorted(set(resolved.theme_issuer.dropna()))
    return themes[0] if themes else None


def detect(
    book: Book,
    client_id: str,
    date: str | None = None,
    cover_threshold: float = DEFAULT_COVER_THRESHOLD,
) -> list[dict]:
    """One finding per obligation worth raising."""
    date = date or latest(book)
    obligations = _obligations(book, client_id, date)
    if not obligations:
        return []

    funds = liquidity(book, client_id, date)
    facility = _facility_for(book, client_id, date)
    findings = []

    for obligation in obligations:
        amount_usd = obligation["amount_usd"]
        if amount_usd is None:
            # No rate, so no comparison. Reported rather than guessed.
            findings.append(
                _unconvertible(client_id, obligation, funds, facility)
            )
            continue

        cover = (
            funds["liquid_usd"] / amount_usd if amount_usd else float("inf")
        )
        near_cash_cover = (
            funds["near_cash_usd"] / amount_usd if amount_usd else float("inf")
        )
        need_pct = amount_usd / funds["total_usd"] * 100.0

        after_sale = None
        if facility and facility["collateral_portfolio_id"]:
            # The need is met in the facility's currency where they match,
            # otherwise convert back through USD.
            if obligation["currency"] == facility["currency"]:
                sale_ccy = obligation["amount"]
            else:
                rate = to_usd(book, 1.0, facility["currency"], date)
                sale_ccy = (
                    amount_usd / rate["usd"] if rate["usd"] else None
                )
            if sale_ccy:
                after_sale = _ltv_after_sale(facility, sale_ccy)

        # The facility only blocks funding if there is no *unpledged*
        # liquidity to meet the obligation from. Otherwise the client
        # simply pays from the other portfolio and the collateral is
        # never touched.
        must_use_collateral = funds["free_liquid_usd"] < amount_usd
        blocked = bool(
            must_use_collateral
            and after_sale
            and after_sale["breaches_margin_call"]
        )
        tight_on_near_cash = near_cash_cover < 1.5

        if cover >= cover_threshold and not blocked and not tight_on_near_cash:
            continue

        findings.append(
            _finding(
                client_id,
                obligation,
                funds,
                facility,
                after_sale,
                cover,
                near_cash_cover,
                need_pct,
                blocked,
                concentration_theme=_concentration_theme(book, client_id, date),
            )
        )

    return sorted(
        findings, key=lambda f: (-f.get("need_pct", 0.0), f["obligation"]["id"])
    )


def _trajectory_copy(facility: dict, concentration_theme: str | None) -> str:
    """The loan against the portfolio, over time, in words.

    Two causes, told apart: a rise while the balance grew is a decision;
    a rise on an unchanged balance is the collateral shrinking underneath
    the client. Reporting only the latest reading loses both.
    """
    t = facility.get("trajectory") or {}
    if not t or t.get("direction") != "rising":
        return ""

    parts = [
        f"Over the five snapshots the loan-to-value has moved from "
        f"{t['ltv_from']:.2f}% to {t['ltv_to']:.2f}% — "
        f"{t['ltv_change_pp']:+.2f} percentage points — leaving "
        f"{t['pp_to_margin_call']:.2f} of headroom against the "
        f"{facility['margin_call_ltv_pct']:.0f}% trigger."
    ]

    if t.get("headroom_lost"):
        parts.append(
            f"Borrowing capacity fell by "
            f"{t['headroom_lost']:,.0f} {facility['currency']} over that "
            f"period."
        )

    for change in t.get("balance_changes", []):
        if change["kind"] == "drawdown":
            parts.append(
                f"On {change['snapshot_date']} the drawn balance rose from "
                f"{change['from']:,.0f} to {change['to']:,.0f} "
                f"{facility['currency']} — a decision, taken while the "
                f"collateral was falling."
            )

    rises = t.get("collateral_driven_rises", [])
    if rises:
        total = sum(r["ltv_rise_pp"] for r in rises)
        parts.append(
            f"Since then nothing further has been drawn, and the "
            f"loan-to-value has still risen {total:.2f} percentage points"
            + (
                f" — the collateral is falling, and it is the same "
                f"{concentration_theme} concentration reported above."
                if concentration_theme
                else " because the collateral value is falling."
            )
        )

    return " ".join(parts)


def _finding(
    client_id,
    obligation,
    funds,
    facility,
    after_sale,
    cover,
    near_cash_cover,
    need_pct,
    blocked,
    concentration_theme=None,
) -> dict:
    detail = [
        f"{obligation['description']} — {obligation['currency']} "
        f"{obligation['amount']:,.0f} "
        f"(USD {obligation['amount_usd']:,.0f}), due by "
        f"{obligation['due_to']}. That is {need_pct:.2f}% of the portfolio."
    ]

    detail.append(
        f"Holdings sellable daily or weekly total "
        f"{funds['liquid_pct']:.2f}% of the portfolio, covering the "
        f"obligation {cover:.2f} times over."
    )

    # The distinction that matters: covered is not the same as painless.
    if near_cash_cover < 1.5:
        detail.append(
            f"But cash and fixed income together are only "
            f"{funds['near_cash_pct']:.2f}%, which covers it "
            f"{near_cash_cover:.2f} times — so meeting it means selling "
            f"into the rest of the portfolio rather than drawing on "
            f"near-cash holdings."
        )

    if blocked and after_sale:
        detail.append(
            f"There is no unpledged liquidity to meet this from — "
            f"free liquid holdings are USD "
            f"{funds['free_liquid_usd']:,.0f} against a need of USD "
            f"{obligation['amount_usd']:,.0f}."
        )
        detail.append(
            f"The portfolio is pledged as collateral under "
            f"{facility['facility_id']}, with "
            f"{facility['drawn']:,.0f} {facility['currency']} drawn and a "
            f"loan-to-value of {facility['ltv_pct']:.2f}% against a "
            f"{facility['margin_call_ltv_pct']:.0f}% margin-call "
            f"threshold — {facility['margin_call_ltv_pct'] - facility['ltv_pct']:.2f} "
            f"percentage points of headroom. {after_sale['note'].capitalize()}. "
            f"Funding this by selling collateral is therefore not "
            f"available on these numbers; it may be worth raising how "
            f"else it would be met."
        )
    elif facility:
        detail.append(
            f"The portfolio is pledged under {facility['facility_id']} at "
            f"{facility['ltv_pct']:.2f}% loan-to-value against a "
            f"{facility['margin_call_ltv_pct']:.0f}% threshold."
        )

    # The trajectory. A static reading says where he is; this says where he
    # is going, and separates the part he chose from the part that happened
    # to him. See specs/008-.../research.md R2.
    if facility:
        detail.append(_trajectory_copy(facility, concentration_theme))

    evidence = [
        {
            "file": obligation["source"],
            "rows": [obligation["id"]],
            "note": (
                f"{obligation['description']}, {obligation['currency']} "
                f"{obligation['amount']:,.0f}, due "
                f"{obligation['due_from']}..{obligation['due_to']}, "
                f"{obligation['certainty']}. {obligation['fx_note']}"
            ),
        },
        {
            "file": "holdings.csv",
            "rows": funds["liquid_instrument_ids"],
            "note": (
                f"sellable daily or weekly: "
                f"USD {funds['liquid_usd']:,.0f} "
                f"({funds['liquid_pct']:.2f}%)"
            ),
        },
    ]
    if facility:
        evidence.append(
            {
                "file": "credit_facilities.csv",
                "rows": [facility["facility_id"]],
                "note": (
                    f"{facility['drawn']:,.0f} {facility['currency']} drawn, "
                    f"loan-to-value {facility['ltv_pct']:.2f}%, margin call "
                    f"at {facility['margin_call_ltv_pct']:.0f}%"
                ),
            }
        )

    return {
        "client_id": client_id,
        "kind": KIND,
        "facility_trajectory": (facility or {}).get("trajectory") or None,
        "severity": 5 if blocked else 4,
        "confidence": "high",
        "headline": (
            f"{obligation['currency']} {obligation['amount']:,.0f} due by "
            f"{obligation['due_to']}"
            + (
                " cannot be funded by selling pledged collateral without "
                "breaching the facility's margin-call threshold."
                if blocked
                else f" — {need_pct:.2f}% of the portfolio."
            )
        ),
        "detail": " ".join(detail),
        "obligation": obligation,
        "need_pct": need_pct,
        "liquidity": funds,
        "cover_ratio": cover,
        "near_cash_cover_ratio": near_cash_cover,
        "facility": facility,
        "facility_after_sale": after_sale,
        "funding_blocked_by_facility": blocked,
        "evidence": evidence,
        "events": [],
        "unsure_about": _unsure(funds, obligation),
        "classification": None,
    }


def _unconvertible(client_id, obligation, funds, facility) -> dict:
    """A need whose currency has no rate. Reported, never estimated."""
    return {
        "client_id": client_id,
        "kind": KIND,
        "severity": 3,
        "confidence": "low",
        "headline": (
            f"{obligation['currency']} {obligation['amount']:,.0f} due by "
            f"{obligation['due_to']} could not be compared to the "
            f"portfolio."
        ),
        "detail": (
            f"{obligation['description']} is denominated in "
            f"{obligation['currency']}. {obligation['fx_note']}. No USD "
            f"figure is stated and no coverage ratio is computed."
        ),
        "obligation": obligation,
        "need_pct": 0.0,
        "liquidity": funds,
        "facility": facility,
        "evidence": [
            {
                "file": obligation["source"],
                "rows": [obligation["id"]],
                "note": obligation["fx_note"],
            }
        ],
        "events": [],
        "unsure_about": obligation["fx_note"],
        "classification": None,
    }


def _unsure(funds: dict, obligation: dict) -> str:
    parts = []

    # Block 6 is explicit: private-market valuations lag a quarter by
    # design. Industry practice, not an error — so it is noted where it
    # affects a conclusion and never flagged.
    monthly_or_illiquid = {
        tier: pct
        for tier, pct in funds["by_tier"].items()
        if tier not in LIQUID_TIERS
    }
    if monthly_or_illiquid:
        described = ", ".join(
            f"{pct:.2f}% {tier.lower()}"
            for tier, pct in sorted(monthly_or_illiquid.items())
        )
        parts.append(
            f"{described} is excluded from available funds. Private-market "
            f"valuations in that group lag by a quarter as a matter of "
            f"industry practice, so the excluded value is indicative "
            f"rather than current."
        )

    if obligation["certainty"] != "Confirmed":
        parts.append(
            f"This obligation is recorded as "
            f"{obligation['certainty'].lower()} rather than confirmed."
        )

    return " ".join(parts)
