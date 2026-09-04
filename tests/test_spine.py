"""Spec 000 — the integration assertion.

Article VIII: every integration assertion cites a figure recorded in
`.alamazing/findings.md`, which records how it was computed. An assertion
with no recorded derivation is not evidence-based and does not count.

Recorded figure: **42.13%** look-through concentration in shipping and
energy for CL-0019 at the 2026-08-26 snapshot
(`.alamazing/findings.md` § 1. Abdullah Al-Mansoori — The exposure).

Asserted with tolerance, never equality. Sums over floats vary in the last
decimal with summation order; 42.1343 and 42.1344 are both correct.
"""

import pandas as pd
import pytest

from pipeline.load import client_weights, latest
from tests.conftest import DATA, HERO, HERO_EXPOSURE

# .alamazing/findings.md § Abdullah Al-Mansoori — The exposure.
RECORDED_LOOKTHROUGH = 42.134
TOLERANCE = 0.001


def test_spine_cl0019_from_pipeline(book):
    """The whole product rests on this number being reachable.

    Constitution, Principle III: "the pipeline produces 42.134 (± 0.001)
    for CL-0019 from the raw files. That is the look-through concentration
    on which the entire product rests."
    """
    w = client_weights(book, HERO, latest(book))
    total = w[w.instrument_id.isin(HERO_EXPOSURE)].w.sum()

    assert total == pytest.approx(RECORDED_LOOKTHROUGH, abs=TOLERANCE)


def test_spine_matches_raw_files(book):
    """The same figure, computed a second way, straight from the CSV.

    If this passes and the test above fails, the bug is in the pipeline
    rather than the data — which is the only diagnostic worth having at
    15:00 on Saturday.
    """
    h = pd.read_csv(f"{DATA}holdings.csv")
    t = h[(h.client_id == HERO) & (h.snapshot_date == latest(book))]
    raw = (t.market_value_usd / t.market_value_usd.sum() * 100)[
        t.instrument_id.isin(HERO_EXPOSURE)
    ].sum()

    assert raw == pytest.approx(RECORDED_LOOKTHROUGH, abs=TOLERANCE)

    pipeline = client_weights(book, HERO, latest(book))
    through = pipeline[
        pipeline.instrument_id.isin(HERO_EXPOSURE)
    ].w.sum()
    assert through == pytest.approx(raw, abs=1e-9)


def test_every_exposure_instrument_is_held(book):
    """The four ids are real positions, not a list that stopped matching.

    A test asserting a sum over an empty selection passes at 0.0 against a
    tolerance of nothing. This makes the selection itself an assertion.
    """
    w = client_weights(book, HERO, latest(book))
    assert set(HERO_EXPOSURE) <= set(w.instrument_id)
