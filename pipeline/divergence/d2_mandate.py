"""Spec 003 — D2, mandate breaches and what caused them.

The brief asks us to separate **drift** from **client-directed**. Reading
the notes revealed a third case the brief does not name.

One client's portfolio is 71.46% equity against a 30% ceiling on a
Conservative mandate. She has never traded. It was transferred in as it
stood when her husband died. **Nobody chose this allocation for her** —
not the bank, and not her.

That is neither drift nor client direction, and it is a different
conversation with a different urgency. Drift you rebalance. Client
direction you discuss. An inherited portfolio you have to *explain* to
someone who has said twice that she does not understand what is in it.

Three classifications, three conversations. Which one to have is the
relationship manager's call (Principle IX).

The second reason this module exists is the opposite result: a client who
breaches **nothing**. That is not a null. It is the finding — the
portfolio passes every check the bank runs and is still 42% one bet — and
spec 001's `compliance_clean` is built from it.

Contract: ``specs/003-mandate-classification/contracts/classification.md``
"""

from __future__ import annotations

import pandas as pd

from pipeline.load import Book, latest, snapshots
from pipeline.mandate import (
    ABOVE,
    BELOW,
    WITHIN,
    check_bands,
    compliance_verdict,
    managed_portfolios,
)

KIND = "D2"

INHERITED = "inherited"
CLIENT_DIRECTED = "client_directed"
DRIFT = "drift"

# Transaction types, **as they appear in the data**.
#
# Both reference documents specify `transactions.type` with values
# `'BUY'` and `'SUBSCRIPTION'`. Neither the column nor the values exist —
# the column is `transaction_type` and the values are title-case and
# longer. Written as specified, the filter matches nothing, every client
# reads as having never traded, and **every breach in the book classifies
# as inherited**: the right answer for one client, for entirely the wrong
# reason, and invisible.
#
# Named constants rather than literals at the point of use, and asserted
# by a test that fails if the data stops containing them.
# See research.md R1.
ACQUISITIONS = ("Buy", "Structured Product Subscription")
DISPOSALS = ("Redemption Request", "Withdrawal")

# A transfer-in is not a client decision. It is the mechanism by which an
# inherited portfolio arrives.
TRANSFER_IN = "Transfer In"


def reporting_year(book: Book) -> str:
    """The year the book is reported as at, derived from the data.

    `inherited` means "inception in the current reporting year", and that
    year must not be written into the pipeline (Principle XI).
    """
    return latest(book)[:4]


def _movements(book: Book, client_id: str, portfolio_id: str) -> pd.DataFrame:
    t = book.transactions
    return t[(t.client_id == client_id) & (t.portfolio_id == portfolio_id)]


def _asset_class_of(book: Book, instrument_ids) -> dict:
    i = book.instruments
    return dict(zip(i.instrument_id, i.asset_class))


def classify(
    book: Book,
    client_id: str,
    portfolio_id: str,
    asset_class: str,
    verdict: str,
) -> dict:
    """Was this breach inherited, chosen, or drifted into?

    **The direction of the breach selects the direction of the evidence.**
    Block 5 specifies only "BUY or SUBSCRIPTION into the breached asset
    class", which is coherent for an above-maximum breach and wrong for a
    below-minimum one: buying *into* a class that is below its floor moves
    it back toward the band, so it is evidence *against* client direction.
    What would explain a below-min breach is a disposal out of the class.
    See research.md R3.

    Returns the classification and the evidence it was derived from — a
    classification without its workings is an assertion (Principle VI).
    """
    portfolio = book.portfolios[
        book.portfolios.portfolio_id == portfolio_id
    ].iloc[0]
    inception = str(portfolio.inception_date)

    movements = _movements(book, client_id, portfolio_id)
    classes = _asset_class_of(book, movements.instrument_id)

    relevant_types = ACQUISITIONS if verdict == ABOVE else DISPOSALS
    directed = movements[
        movements.transaction_type.isin(relevant_types)
        & movements.instrument_id.map(
            lambda i: classes.get(i) == asset_class
        )
    ]

    transferred_in = movements[movements.transaction_type == TRANSFER_IN]
    inception_this_year = inception.startswith(reporting_year(book))

    if not directed.empty:
        # A decision was taken in the direction of the breach. This wins
        # over inherited: a portfolio transferred in this year and then
        # bought into is not something nobody chose.
        classification = CLIENT_DIRECTED
    elif inception_this_year:
        classification = INHERITED
    else:
        classification = DRIFT

    return {
        "classification": classification,
        "inception_date": inception,
        "inception_in_reporting_year": bool(inception_this_year),
        "transactions_examined": sorted(movements.transaction_id),
        "directing_transactions": sorted(directed.transaction_id),
        "transfer_in_transactions": sorted(transferred_in.transaction_id),
        "evidence_direction": (
            "acquisitions into the class" if verdict == ABOVE
            else "disposals out of the class"
        ),
    }


_COPY = {
    INHERITED: (
        "The portfolio was transferred in as it stood and shows no "
        "client-initiated trade into this class. Nobody chose this "
        "allocation — not the bank, and not the client. Same breach as a "
        "drift, a different conversation."
    ),
    CLIENT_DIRECTED: (
        "The client traded in the direction of this breach, so the "
        "allocation reflects a decision rather than market movement. "
        "Worth raising as a decision to revisit, not an error to correct."
    ),
    DRIFT: (
        "No client-initiated trade explains this. The weights moved "
        "through market action, which means the exposure changed without "
        "anyone deciding it should."
    ),
}


def detect(
    book: Book, client_id: str, date: str | None = None
) -> list[dict]:
    """One finding per breach, plus a positive result when there are none."""
    date = date or latest(book)
    if date not in snapshots(book):
        raise ValueError(f"{date!r} is not a snapshot in this book")

    bands = check_bands(book, client_id, date)
    verdict = compliance_verdict(book, client_id, date)
    findings: list[dict] = []

    breached = bands[bands.verdict != WITHIN]

    for _, band in breached.iterrows():
        classified = classify(
            book,
            client_id,
            band.portfolio_id,
            band.asset_class,
            band.verdict,
        )
        low = band.verdict == BELOW
        limit = band.min_pct if low else band.max_pct

        findings.append(
            {
                "client_id": client_id,
                "kind": KIND,
                "portfolio_id": band.portfolio_id,
                "mandate_code": band.mandate_code,
                "asset_class": band.asset_class,
                "actual_pct": float(band.actual_pct),
                "min_pct": float(band.min_pct),
                "max_pct": float(band.max_pct),
                "verdict": band.verdict,
                "classification": classified["classification"],
                "severity": 5 if abs(band.actual_pct - limit) > 20 else 4,
                "confidence": "high",
                "headline": (
                    f"{band.asset_class} is {band.actual_pct:.2f}% against a "
                    f"{band.min_pct:.0f}-{band.max_pct:.0f} band — "
                    f"{'below the floor' if low else 'above the ceiling'}, "
                    f"classified {classified['classification'].replace('_', ' ')}."
                ),
                "detail": (
                    f"{band.mandate_code} allows {band.asset_class} between "
                    f"{band.min_pct:.0f}% and {band.max_pct:.0f}%. "
                    f"{band.portfolio_id} holds {band.actual_pct:.2f}%. "
                    + _COPY[classified["classification"]]
                ),
                "classification_evidence": classified,
                "compliance_clean": verdict["clean"],
                "breached_positions": verdict["breached_positions"],
                "over_limit_but_exempt": verdict["over_limit_but_exempt"],
                "custody": verdict["custody"],
                "evidence": _evidence(book, band, classified),
                "events": [],
                "unsure_about": _unsure(book, client_id, band),
            }
        )

    if not findings:
        clear = _checked_and_clear(client_id, bands, verdict)
        if clear:
            findings.append(clear)

    return sorted(
        findings,
        key=lambda f: (
            -abs(f.get("actual_pct", 0.0)),
            f.get("asset_class", ""),
        ),
    )


def _evidence(book: Book, band, classified: dict) -> list[dict]:
    out = [
        {
            "file": "mandates.csv",
            "rows": [f"{band.mandate_code}/{band.asset_class}"],
            "note": (
                f"{band.asset_class} band {band.min_pct:.0f}-"
                f"{band.max_pct:.0f}%, actual {band.actual_pct:.2f}%"
            ),
        },
        {
            "file": "portfolios.csv",
            "rows": [band.portfolio_id],
            "note": f"inception {classified['inception_date']}",
        },
    ]
    examined = classified["transactions_examined"]
    if examined:
        out.append(
            {
                "file": "transactions.csv",
                "rows": examined,
                "note": (
                    f"{len(examined)} transactions examined for "
                    f"{classified['evidence_direction']}; "
                    f"{len(classified['directing_transactions'])} found"
                ),
            }
        )
    return out


def _unsure(book: Book, client_id: str, band) -> str:
    """What would change this answer (Principle X)."""
    parts = []

    # A missing cost basis on a holding in the breached class matters: it
    # is one of the things that makes selling the position hard to advise
    # on, and it is exactly the imperfection spec 000 recorded.
    relevant = [
        i
        for i in book.imperfections
        if i.get("client_id") == client_id
        and i.get("kind") == "missing_cost_basis"
    ]
    if relevant:
        names = sorted({i["instrument_id"] for i in relevant})
        parts.append(
            f"{', '.join(names)} carries no cost basis, so the tax "
            f"consequence of selling it to correct this breach cannot be "
            f"stated from this data."
        )

    if not book.transactions[
        book.transactions.client_id == client_id
    ].shape[0]:
        parts.append(
            "No transactions exist for this client, so the "
            "classification rests on the portfolio inception date alone."
        )

    return " ".join(parts)


def _checked_and_clear(
    client_id: str, bands: pd.DataFrame, verdict: dict
) -> dict | None:
    """The positive result. Block 5: this is not a null.

    A client who breaches nothing is the strongest case the product makes —
    every control passed, and the concentration is still there. So the
    detector states it affirmatively and names every band it checked,
    which is what makes "nothing breached" auditable rather than asserted.
    """
    if bands.empty:
        return None

    checked = [
        {
            "portfolio_id": b.portfolio_id,
            "asset_class": b.asset_class,
            "actual_pct": float(b.actual_pct),
            "min_pct": float(b.min_pct),
            "max_pct": float(b.max_pct),
        }
        for _, b in bands.iterrows()
    ]
    largest = verdict["largest_position"]

    return {
        "client_id": client_id,
        "kind": KIND,
        "verdict": WITHIN,
        "classification": None,
        "severity": 1,
        "confidence": "high",
        "headline": (
            f"All {len(checked)} mandate bands respected and no position "
            f"exceeds its limit."
        ),
        "detail": (
            f"Every asset class held was compared to its band and all "
            f"{len(checked)} are within range: "
            + "; ".join(
                f"{c['asset_class']} {c['actual_pct']:.2f}% "
                f"({c['min_pct']:.0f}-{c['max_pct']:.0f})"
                for c in checked
            )
            + (
                f". The largest position is {largest['instrument_name']} at "
                f"{largest['actual_pct']:.2f}%"
                + (
                    f" against a {largest['limit_pct']:.0f}% limit"
                    if largest.get("limit_pct")
                    else ""
                )
                + "."
                if largest
                else "."
            )
            + " Nothing here is a breach, so no existing control would "
            "raise anything on this portfolio."
        ),
        "bands_checked": checked,
        "compliance_clean": verdict["clean"],
        "largest_position": largest,
        "over_limit_but_exempt": verdict["over_limit_but_exempt"],
        "custody": verdict["custody"],
        "evidence": [
            {
                "file": "mandates.csv",
                "rows": sorted(
                    {f"{b.mandate_code}/{b.asset_class}"
                     for _, b in bands.iterrows()}
                ),
                "note": "; ".join(
                    f"{c['asset_class']} {c['actual_pct']:.2f}% within "
                    f"{c['min_pct']:.0f}-{c['max_pct']:.0f}"
                    for c in checked
                ),
            }
        ],
        "events": [],
        "unsure_about": "",
    }
