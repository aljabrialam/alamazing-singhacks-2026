"""Spec 001 — D3, concentration that is hidden when the book is split.

Abdullah Al-Mansoori's portfolio respects **every** mandate band and
breaches **no** single-name limit. It is also 42% one bet.

An exception engine cannot raise that, because there is no exception. A
concentration report cannot raise it, because the exposure is split across
four instruments in three asset classes — one of them a structured note
whose booked classification says nothing about what it references.

The whole mechanism is one move: **resolve a structured product to the
names it references, not the asset class it is booked as.**

Two rules, both emitted, because the data supports two different findings
and neither rule alone reproduces both recorded figures:

    sector theme   what is he actually exposed to, once you look through
                   the note?
    issuer theme   how many ways does he own the same company?

Each rule reproduces one of the two figures recorded in
``.alamazing/findings.md``; neither rule alone reproduces both.

See ``specs/001-look-through/research.md`` R5 for why both are needed.

No model is called. The parse is a string split, the match a substring
test, the totals pandas.

Contract: ``specs/001-look-through/contracts/look-through.md``
"""

from __future__ import annotations

import re

import pandas as pd

from pipeline.load import Book, client_weights, latest, snapshots
from pipeline.mandate import compliance_verdict

# Findings are D3 in the recorded schema —
# specs/001-divergence-engine/contracts/finding.schema.json
KIND = "D3"

SECTOR_RULE = "sector"
ISSUER_RULE = "issuer"

# Default concentration threshold, from block 3. A parameter, not a
# literal, so "what about 20%?" is answered by typing (Principle XI).
DEFAULT_THRESHOLD_PCT = 25.0

# An issuer theme needs at least this many matched holdings besides the
# product itself to be worth reporting. One match is a note and the thing
# it references; two or more is a company owned several ways.
MIN_ISSUER_MATCHES = 2

# Names are matched on their first two words, lowercased. This is what
# survives the difference between "Global Energy Majors ADR" in a basket
# and "Global Energy Majors Equity Fund" in the book — verified in
# research.md R1 to reach exactly the two intended instruments.
_MATCH_WORDS = 2

# Where a referenced name hides inside an instrument's own name:
# "Accumulator ref. Golden Harbour Properties Ltd, 12M".
_NAME_REF_MARKER = re.compile(r"ref\.\s*([^,]+)", re.IGNORECASE)


def _match_key(name: str) -> str:
    return " ".join(str(name).split()[:_MATCH_WORDS]).lower()


def referenced_names(row: pd.Series) -> list[str]:
    """The names a holding references, from both places they can hide.

    Block 3 describes only the first source. That is incomplete against
    this data: one client's accumulator carries **no name** in its
    underlying reference — only strike, knock-out and double-up mechanics
    — and names its issuer in the instrument name instead. A parser
    reading only the reference cannot find that issuer at all, and a
    required assertion fails. See research.md R6.

    1. ``underlying_reference`` after the colon, split on ``/``
    2. ``instrument_name`` after a ``ref.`` marker, to the first comma

    Returns sorted names so downstream order does not depend on which
    source produced them (Principle VII).
    """
    names: set[str] = set()

    reference = row.get("underlying_reference")
    if isinstance(reference, str) and ":" in reference:
        _, listed = reference.split(":", 1)
        names.update(part.strip() for part in listed.split("/"))

    marker = _NAME_REF_MARKER.search(str(row.get("instrument_name", "")))
    if marker:
        names.add(marker.group(1).strip())

    return sorted(n for n in names if n)


def _resolve(weighted: pd.DataFrame, product: pd.Series) -> dict:
    """Match one product's referenced names against the client's holdings."""
    matched_ids: set[str] = set()
    matched_names: set[str] = set()
    sectors: set[str] = set()
    unresolved: list[str] = []
    loose: list[str] = []

    for name in referenced_names(product):
        key = _match_key(name)
        hits = weighted[
            weighted.instrument_name.str.lower().str.contains(key, regex=False)
            & (weighted.instrument_id != product.instrument_id)
        ]
        if not hits.empty:
            # The label comes from the reference as written, not from the
            # matched instrument names — "Golden Harbour Properties Ltd"
            # rather than "Golden Harbour Properties 5.25% Perpetual".
            matched_names.add(name)
        if hits.empty:
            # Either a name the client does not hold, or a reference that
            # describes a category rather than an issuer ("three Asian
            # banking majors"). Both are recorded, never guessed at.
            unresolved.append(name)
            continue
        for _, hit in hits.iterrows():
            matched_ids.add(hit.instrument_id)
            if pd.notna(hit.sector):
                sectors.add(hit.sector)
            # Matched on a prefix rather than the whole name, so the
            # exposure is the same underlying but not the same line.
            if _match_key(hit.instrument_name) != key or name.lower() not in str(
                hit.instrument_name
            ).lower():
                loose.append(f"{name} -> {hit.instrument_name}")

    return {
        "matched_ids": sorted(matched_ids),
        "matched_names": sorted(matched_names),
        "sectors": sorted(sectors),
        "unresolved": sorted(unresolved),
        "loose": sorted(set(loose)),
    }


def look_through(book: Book, client_id: str, date: str) -> pd.DataFrame:
    """Every holding, with the themes it belongs to once products resolve.

    Returns the client's weighted holdings plus two columns:

        ``theme_sector``  the sector theme this row belongs to, or None
        ``theme_issuer``  the issuer theme this row belongs to, or None

    A frame rather than theme totals, because spec 002 filters these rows
    against a claim's target and would otherwise have to recompute them.
    Totals are a ``groupby`` the caller performs.
    """
    weighted = client_weights(book, client_id, date)
    if weighted.empty:
        return weighted.assign(theme_sector=None, theme_issuer=None)

    weighted = weighted.copy()
    weighted["theme_sector"] = None
    weighted["theme_issuer"] = None

    products = weighted[weighted.underlying_reference.notna()]

    for _, product in products.iterrows():
        resolved = _resolve(weighted, product)

        if resolved["sectors"]:
            # Label from the data — the joined sector names as the files
            # spell them. No theme name is written in this module.
            label = " + ".join(resolved["sectors"])
            members = weighted.sector.isin(resolved["sectors"]) | (
                weighted.instrument_id == product.instrument_id
            )
            weighted.loc[members, "theme_sector"] = label

        if len(resolved["matched_ids"]) >= MIN_ISSUER_MATCHES:
            # Label from the reference as written — the name the bank used
            # for the underlying, not the longer name of any one line that
            # matched it. Where a basket references several names the
            # client holds, all are named: calling a two-company basket
            # after one of them would be misleading in RM-facing copy.
            label = " + ".join(resolved["matched_names"])
            members = weighted.instrument_id.isin(
                [*resolved["matched_ids"], product.instrument_id]
            )
            weighted.loc[members, "theme_issuer"] = label

    return weighted


def _theme_total(weighted: pd.DataFrame, column: str, label: str) -> pd.DataFrame:
    members = weighted[weighted[column] == label]
    if len(members) != members.instrument_id.nunique():
        raise ValueError(
            f"theme {label!r} counts an instrument twice — "
            f"this inflates every figure plausibly"
        )
    return members


def _evidence(members: pd.DataFrame) -> list[dict]:
    return [
        {
            "file": "holdings.csv",
            "rows": sorted(members.instrument_id.tolist()),
            "note": "; ".join(
                f"{r.instrument_id} {r.instrument_name} {r.w:.2f}% "
                f"[{r.asset_class}]"
                for _, r in members.sort_values(
                    "w", ascending=False
                ).iterrows()
            ),
        }
    ]


def trajectory(
    book: Book, client_id: str, instrument_ids: list[str]
) -> list[dict]:
    """This exposure's weight at every snapshot, chronologically.

    **Membership is fixed as resolved today, then measured backwards.**
    That is the question being asked — "this exposure grew from 29.41% to
    42.13%" — and it is not the same as re-resolving the theme at each
    date. Re-resolving gives zero before the structured product settled,
    because with no product there is nothing to look through, which would
    hide precisely the history the trajectory exists to show.

    For the hero client this yields two causes: appreciation through the
    the commodity spike, then a step change when the note settled. Both
    visible in the numbers rather than asserted.
    """
    out = []
    for date in snapshots(book):
        weighted = client_weights(book, client_id, date)
        if weighted.empty:
            out.append({"snapshot_date": date, "pct": 0.0})
            continue
        held = weighted[weighted.instrument_id.isin(instrument_ids)]
        out.append({"snapshot_date": date, "pct": float(held.w.sum())})
    return out


def detect(
    book: Book,
    client_id: str,
    date: str | None = None,
    threshold_pct: float = DEFAULT_THRESHOLD_PCT,
) -> list[dict]:
    """Findings for one client. Possibly none, which is a real answer.

    ``date`` and ``threshold_pct`` are arguments. Neither a client, an
    instrument, a sector nor a date is named in this module
    (Principle XI).
    """
    date = date or latest(book)
    weighted = look_through(book, client_id, date)
    if weighted.empty:
        return []

    verdict = compliance_verdict(book, client_id, date)
    findings: list[dict] = []

    unresolved: list[str] = []
    loose: list[str] = []
    for _, product in weighted[weighted.underlying_reference.notna()].iterrows():
        resolved = _resolve(weighted, product)
        unresolved.extend(resolved["unresolved"])
        loose.extend(resolved["loose"])

    for column, rule in ((("theme_sector"), SECTOR_RULE),
                         (("theme_issuer"), ISSUER_RULE)):
        for label in sorted(weighted[column].dropna().unique()):
            members = _theme_total(weighted, column, label)
            total = float(members.w.sum())
            if total <= threshold_pct:
                continue

            classes = sorted(members.asset_class.unique())
            findings.append(
                {
                    "client_id": client_id,
                    "kind": KIND,
                    "rule": rule,
                    "theme": label,
                    "severity": 5 if total >= 40 else 4,
                    "confidence": "high",
                    "headline": (
                        f"{total:.2f}% of the portfolio sits in "
                        f"{label}, across {len(classes)} asset "
                        f"{'class' if len(classes) == 1 else 'classes'} "
                        f"and {len(members)} positions."
                    ),
                    "detail": _detail(rule, label, total, members, verdict),
                    "theme_pct": total,
                    "asset_classes": classes,
                    "members": members[
                        ["instrument_id", "instrument_name", "asset_class", "w"]
                    ].to_dict("records"),
                    "trajectory": trajectory(
                        book, client_id, members.instrument_id.tolist()
                    ),
                    "compliance_clean": verdict["clean"],
                    "compliance_bands": verdict["bands"],
                    "largest_position": verdict["largest_position"],
                    "evidence": _evidence(members),
                    "events": [],
                    "unsure_about": _unsure(unresolved, loose),
                    "classification": None,
                }
            )

    findings.extend(
        _duplicate_underlying(book, client_id, date, weighted, verdict)
    )

    # Principle VI — a finding that cannot produce evidence is not emitted.
    findings = [f for f in findings if f["evidence"] and f["evidence"][0]["rows"]]

    return sorted(
        findings, key=lambda f: (-f["theme_pct"], f["rule"], f["theme"])
    )


def _duplicate_underlying(
    book: Book,
    client_id: str,
    date: str,
    weighted: pd.DataFrame,
    verdict: dict,
) -> list[dict]:
    """A structured product referencing names the client already holds.

    This is what makes the concentration *explicable* rather than merely
    true. "42% concentrated" invites argument. "Your note's basket contains
    two names you already own outright" ends it.

    Emitted regardless of threshold — it is a qualitative fact about the
    position, not a magnitude. It is **not** diversification: on the
    downside a worst-of basket pays on whichever underlying falls
    furthest, so it is added exposure to holdings already owned.
    """
    out = []
    for _, product in weighted[weighted.underlying_reference.notna()].iterrows():
        resolved = _resolve(weighted, product)
        if not resolved["matched_ids"]:
            continue

        duplicated = weighted[
            weighted.instrument_id.isin(resolved["matched_ids"])
        ]
        rows = sorted([product.instrument_id, *resolved["matched_ids"]])
        combined = float(
            weighted[weighted.instrument_id.isin(rows)].w.sum()
        )

        out.append(
            {
                "client_id": client_id,
                "kind": KIND,
                "rule": "duplicate_underlying",
                "theme": product.instrument_name,
                "severity": 4,
                "confidence": "high",
                "headline": (
                    f"{product.instrument_name} references "
                    f"{len(resolved['matched_ids'])} "
                    f"{'name' if len(resolved['matched_ids']) == 1 else 'names'} "
                    f"the client already holds outright."
                ),
                "detail": (
                    f"The product references "
                    f"{', '.join(resolved['matched_names'])}. "
                    f"{'That name is' if len(duplicated) == 1 else 'Those names are'} "
                    f"already held directly as "
                    + ", ".join(
                        f"{r.instrument_name} ({r.w:.2f}%)"
                        for _, r in duplicated.sort_values(
                            "w", ascending=False
                        ).iterrows()
                    )
                    + f". Together with the product itself that is "
                    f"{combined:.2f}% of the portfolio on the same "
                    f"underlying. On the downside a worst-of basket pays "
                    f"on whichever underlying falls furthest, so this "
                    f"adds to an existing position rather than spreading "
                    f"it — worth raising as part of the same conversation."
                ),
                "theme_pct": combined,
                "asset_classes": sorted(
                    weighted[weighted.instrument_id.isin(rows)].asset_class.unique()
                ),
                "members": weighted[weighted.instrument_id.isin(rows)][
                    ["instrument_id", "instrument_name", "asset_class", "w"]
                ].to_dict("records"),
                "duplicated_instrument_ids": resolved["matched_ids"],
                "referencing_instrument_id": product.instrument_id,
                "trajectory": trajectory(book, client_id, rows),
                "compliance_clean": verdict["clean"],
                "compliance_bands": verdict["bands"],
                "largest_position": verdict["largest_position"],
                "evidence": [
                    {
                        "file": "instruments.csv",
                        "rows": [product.instrument_id],
                        "note": (
                            f"underlying_reference: "
                            f"{product.underlying_reference}"
                        ),
                    },
                    *_evidence(duplicated),
                ],
                "events": [],
                "unsure_about": _unsure(
                    resolved["unresolved"], resolved["loose"]
                ),
                "classification": None,
            }
        )
    return out


def _detail(
    rule: str, label: str, total: float, members: pd.DataFrame, verdict: dict
) -> str:
    """RM-facing prose. The forbidden verb never appears (Principle IX)."""
    classes = sorted(members.asset_class.unique())
    lines = []

    if rule == ISSUER_RULE:
        lines.append(
            f"{label} is held {len(members)} different ways — as "
            f"{', '.join(classes)} — totalling {total:.2f}% of the "
            f"portfolio. Each line sits under a different limit, so no "
            f"single concentration check sees the whole position."
        )
    else:
        lines.append(
            f"Looking through the structured product to the names it "
            f"references, {total:.2f}% of the portfolio is exposed to "
            f"{label}. The exposure is spread over {len(members)} "
            f"positions in {len(classes)} asset "
            f"{'class' if len(classes) == 1 else 'classes'}, which is why "
            f"it does not read as concentration on the statement."
        )

    if verdict["clean"]:
        lines.append(
            "Every mandate band is respected and no single position "
            "exceeds its limit, so nothing here is a breach and no "
            "existing control would raise it. It may still be worth "
            "raising with the client."
        )
    else:
        lines.append(
            "This sits alongside a mandate breach, which is reported "
            "separately."
        )

    return " ".join(lines)


def _unsure(unresolved: list[str], loose: list[str]) -> str:
    """What would change the answer (Principle X, FR-016)."""
    parts = []
    if unresolved:
        parts.append(
            "References that name no instrument the client holds, so they "
            "could not be resolved: " + "; ".join(sorted(set(unresolved)))
        )
    if loose:
        parts.append(
            "Names matched on a prefix rather than in full, so the "
            "exposure is the same underlying but not the same line: "
            + "; ".join(sorted(set(loose)))
        )
    return ". ".join(parts) + ("." if parts else "")
