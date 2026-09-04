"""Spec 006 — assemble the one file the web layer reads.

    python pipeline/build.py --data data/ --clients <id>,<id>,<id>

Both arguments are arguments. A judge asking "run it on someone else" is
answered by typing a different id (Principle XI) — which is also why no
identifier appears in this file, not even in this example.

The shape of the output is dictated by the demo script's seven beats
rather than by what the detectors happen to emit — see
``specs/006-briefs-build/research.md`` R1. Two consequences worth knowing
before reading the assembly code:

**The mandate panel carries every band, not just the breaches.** The
demo's central claim is *"every mandate band is respected"*, and that
sentence needs the bands on screen.

**The uncertainty record has two halves.** Spec 000's imperfections say
*the data cannot tell us this*; the detectors' ``unsure_about`` strings say
*our method has this limit*. Collapsing them into one list would turn the
honest thing into a single caveat blob.

No model call happens here. Briefs and the ranking are read from
``derived/``, committed by an explicit earlier run.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# `python pipeline/build.py` is the documented command (CLAUDE.md), and it
# puts pipeline/ on the path rather than the repo root — so the package
# imports below would fail. Running as `python -m pipeline.build` works
# either way, but the documented command has to work as written.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.brief import rank, write_brief  # noqa: E402
from pipeline.load import Book, client_weights, latest, load_all, snapshots  # noqa: E402
from pipeline.mandate import compliance_verdict  # noqa: E402
from pipeline.divergence import (  # noqa: E402
    d1_said,
    d2_mandate,
    d3_hidden,
    d4_runway,
    d5_unanswered,
    d6_scenario,
)

OUTPUT_PATH = Path(__file__).parent.parent / "web" / "public" / "findings.json"

# There is deliberately **no default market series** here.
#
# A named default read naturally at first — the build choosing which
# question to ask. But it put a series identifier in `pipeline/`, and the
# scenario is an input to the question, not a property of the pipeline.
# Deriving a default from the data was worse: the largest market move in
# this window is European gas at 97%, so the demo's answer would have
# changed silently depending on which series happened to move most.
#
# So `--series` is required, and the choice of scenario lives in the
# command that asks it (Principle XI).


def _scenario_dates(book: Book) -> tuple[str, str]:
    """Today, and the comparison state. Positional, never literal.

    ``snapshots(book)[1]`` is the second snapshot — the day before the
    conflict in this book. Read from the data so the pipeline runs on any
    book with any dates.
    """
    dates = snapshots(book)
    return dates[-1], dates[1]


def detect_all(book: Book, client_id: str, series_id: str) -> list[dict]:
    """Every detector, for one client."""
    date_now, date_then = _scenario_dates(book)
    findings: list[dict] = []
    findings += d3_hidden.detect(book, client_id)
    findings += d1_said.detect(book, client_id)
    findings += d2_mandate.detect(book, client_id)
    findings += d4_runway.detect(book, client_id)
    findings += d5_unanswered.detect(book, client_id)
    findings += d6_scenario.detect(
        book, client_id, series_id, date_now, date_then
    )
    return findings


def detect_shallow(book: Book, client_id: str) -> list[dict]:
    """Mandate and look-through only.

    Block 8: run these over the other clients "so the call list is real
    rather than a mock of three". They are the two detectors that need no
    notes and no model output, so they are cheap and they apply to
    everyone.
    """
    return d3_hidden.detect(book, client_id) + d2_mandate.detect(
        book, client_id
    )


def _summary_for_ranking(findings: list[dict]) -> list[dict]:
    """What the ranking model sees. Derived only (Principle V)."""
    return [
        {
            "kind": f.get("kind"),
            "headline": f.get("headline"),
            "classification": f.get("classification"),
            "compliance_clean": f.get("compliance_clean"),
        }
        for f in findings
    ]


def _client_header(book: Book, client_id: str, date: str) -> dict:
    client = book.client(client_id)
    weighted = client_weights(book, client_id, date)
    portfolios = book.portfolios[book.portfolios.client_id == client_id]
    return {
        "client_id": client_id,
        "name": client.client_name,
        "age": int(client.age) if client.age == client.age else None,
        "life_stage": client.life_stage,
        "risk_profile": client.risk_profile,
        "source_of_wealth": client.source_of_wealth,
        # Quoted verbatim — the demo reads it off the screen.
        "objectives": str(client.objectives),
        "tax_domicile": client.tax_domicile,
        "base_currency": client.base_currency,
        "client_since": client.client_since,
        "aum_usd": float(weighted.market_value_usd.sum()),
        "mandate_codes": sorted(portfolios.mandate_code.dropna().unique()),
        "service_models": sorted(portfolios.service_model.dropna().unique()),
        "rm_name": client.rm_name,
    }


def _uncertainty(book: Book, all_findings: dict) -> dict:
    """Two kinds of not-knowing, kept apart (FR-014)."""
    method_limits = []
    for client_id, findings in sorted(all_findings.items()):
        for finding in findings:
            text = str(finding.get("unsure_about") or "").strip()
            if text:
                method_limits.append(
                    {
                        "client_id": client_id,
                        "kind": finding.get("kind"),
                        "headline": finding.get("headline"),
                        "unsure_about": text,
                    }
                )
    return {
        "data_imperfections": book.imperfections,
        "method_limits": method_limits,
    }


def build(
    series_id: str,
    data_dir: str = "data/",
    client_ids: list[str] | None = None,
    output_path: Path | None = None,
    write: bool = True,
) -> dict:
    """Run the detectors, assemble the payload, optionally write it."""
    book = load_all(data_dir)
    date = latest(book)
    known = set(book.clients.client_id)

    if client_ids is None:
        client_ids = sorted(known)

    unknown = [c for c in client_ids if c not in known]
    if unknown:
        # Named, not silently skipped — an empty entry for a typo'd id
        # would look like a client with nothing wrong.
        raise ValueError(
            f"unknown client id(s): {', '.join(unknown)}. "
            f"known: {sorted(known)}"
        )

    deep = sorted(client_ids)
    shallow = sorted(known - set(deep))

    findings: dict[str, list[dict]] = {}
    for client_id in deep:
        findings[client_id] = detect_all(book, client_id, series_id)
    for client_id in shallow:
        findings[client_id] = detect_shallow(book, client_id)

    # One model call, reading from the committed ranking.
    ranking = rank(
        book,
        {cid: _summary_for_ranking(f) for cid, f in findings.items()},
    )

    briefs = {}
    for client_id in deep:
        briefs[client_id] = write_brief(book, client_id, findings[client_id])

    date_now, date_then = _scenario_dates(book)

    call_list = []
    for position, entry in enumerate(ranking["order"], start=1):
        client_id = entry["client_id"]
        client = book.client(client_id)
        client_findings = findings.get(client_id, [])
        call_list.append(
            {
                "rank": position,
                "client_id": client_id,
                "name": client.client_name,
                "aum_usd": float(client.total_aum_usd),
                "why": entry["why"],
                "finding_count": len(client_findings),
                "has_brief": client_id in briefs,
                "compliance_clean": next(
                    (
                        f["compliance_clean"]
                        for f in client_findings
                        if "compliance_clean" in f
                    ),
                    None,
                ),
            }
        )

    clients = {}
    for client_id in sorted(findings):
        verdict = compliance_verdict(book, client_id, date)
        clients[client_id] = {
            **_client_header(book, client_id, date),
            "brief": briefs.get(client_id),
            "findings": findings[client_id],
            # All bands, not just breaches — the demo's central claim.
            "mandate_panel": {
                "bands": verdict["bands"],
                "clean": verdict["clean"],
                "breached_bands": verdict["breached_bands"],
                "breached_positions": verdict["breached_positions"],
                "over_limit_but_exempt": verdict["over_limit_but_exempt"],
                "largest_position": verdict["largest_position"],
                "custody": verdict["custody"],
            },
            "notes": book.notes_for(client_id),
            "depth": "full" if client_id in set(deep) else "mandate_and_lookthrough",
        }

    payload = {
        "meta": {
            "snapshot_date": date,
            "snapshots": snapshots(book),
            "scenario": {
                "series_id": series_id,
                "date_now": date_now,
                "date_then": date_then,
            },
            "rm_name": book.clients.rm_name.iloc[0],
            "client_count": len(book.clients),
            "deep_clients": deep,
            "brief_provenance": {
                cid: (briefs[cid] or {}).get("provenance") for cid in briefs
            },
            "ranking_provenance": ranking["provenance"],
            "ranking_corrections": ranking["corrections"],
        },
        "call_list": call_list,
        "clients": clients,
        "uncertainty": _uncertainty(book, findings),
    }

    if write:
        target = output_path or OUTPUT_PATH
        target.parent.mkdir(parents=True, exist_ok=True)
        # Sorted keys and a fixed indent, so byte equality across runs is a
        # real property rather than an accident of dict ordering.
        with target.open("w") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True, default=str)
            handle.write("\n")

    return payload


def serialise(payload: dict) -> str:
    """The exact bytes the build writes. Used by the determinism test."""
    return json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build web/public/findings.json from the data folder."
    )
    parser.add_argument("--data", default="data/", help="the data directory")
    parser.add_argument(
        "--clients",
        default=None,
        help=(
            "comma-separated client ids to run every detector over. "
            "Others get mandate and look-through only. Defaults to all."
        ),
    )
    parser.add_argument(
        "--series",
        required=True,
        help=(
            "market series id for the scenario, from market_context.csv. "
            "Required: the scenario is the question being asked, not a "
            "property of the pipeline."
        ),
    )
    parser.add_argument("--out", default=None, help="output path")
    args = parser.parse_args()

    client_ids = (
        [c.strip() for c in args.clients.split(",") if c.strip()]
        if args.clients
        else None
    )
    payload = build(
        data_dir=args.data,
        client_ids=client_ids,
        series_id=args.series,
        output_path=Path(args.out) if args.out else None,
    )

    target = Path(args.out) if args.out else OUTPUT_PATH
    total = sum(len(c["findings"]) for c in payload["clients"].values())
    print(f"wrote {target}")
    print(
        f"  {len(payload['call_list'])} clients ranked, "
        f"{len(payload['meta']['deep_clients'])} in full, "
        f"{total} findings"
    )
    print(
        f"  uncertainty: "
        f"{len(payload['uncertainty']['data_imperfections'])} data "
        f"imperfections, "
        f"{len(payload['uncertainty']['method_limits'])} method limits"
    )
    if payload["meta"]["ranking_corrections"]:
        print("  ranking corrections:")
        for correction in payload["meta"]["ranking_corrections"]:
            print(f"    - {correction}")


if __name__ == "__main__":
    main()
