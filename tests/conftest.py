"""Gemeinsame Fixtures (DEMO-PLAYBOOK §1b): feste Zufallsquelle, Auszahlungen 5/3/1/0."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import rpl_algorithm as A  # noqa: E402
import rpl_constants as C  # noqa: E402


@pytest.fixture(scope="session")
def m08():
    """Auszahlungsmatrix der sechs Strategien bei δ = 0,80 (Zeile gegen Spalte, Reihenfolge C.STRATEGY_KEYS)."""
    return A.payoff_matrix(C.STRATEGY_KEYS, 0.80)


@pytest.fixture(scope="session")
def idx():
    return {k: i for i, k in enumerate(C.STRATEGY_KEYS)}
