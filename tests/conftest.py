"""Shared fixtures.

The twelve files are read once per test session, not once per test — the
book is immutable in practice and reading it 15 times is 15 times the I/O
for no extra confidence.

Client and instrument identifiers appear in this directory only. The
Definition of Done's portability grep is scoped to ``pipeline/`` precisely
so that tests may name the rows they assert against (Principle XI).
"""

import pytest

from pipeline.load import load_all

DATA = "data/"

# The hero client. His portfolio respects every mandate band and is 42% one
# bet — see .alamazing/findings.md § Abdullah Al-Mansoori.
HERO = "CL-0019"

# The four positions that make up that 42%: a shipping fund, a shipping
# single stock, an energy fund, and a structured note whose worst-of basket
# references two names he already holds outright.
HERO_EXPOSURE = ["SYN-EQ-0025", "SYN-ST-0104", "SYN-EQ-0008", "SYN-SP-0505"]

# The note. Settles between the pre-conflict snapshot and today, so it has
# no earlier row at all.
HERO_NOTE = "SYN-SP-0505"

# Transferred in on a death with no cost basis attached.
NO_COST_BASIS_CLIENT = "CL-0003"
NO_COST_BASIS_INSTRUMENT = "SYN-ST-0107"

# Holds three portfolios. Summing weight_pct for him gives 300%.
MULTI_PORTFOLIO_CLIENT = "CL-0017"

# Two rows of event_log.csv the hero's causal chain depends on.
STRAIT_CLOSED = "2026-03-04"
BLOCKADE_REIMPOSED = "2026-08-05"


@pytest.fixture(scope="session")
def book():
    return load_all(DATA)
