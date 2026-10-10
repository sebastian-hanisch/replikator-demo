"""Orakel-Tests replikator-demo: der Kern wird gegen UNABHÄNGIGE Rechenwege geprüft (DEMO-PLAYBOOK §12, ORACLE-PLAYBOOK §2).

1. Wert eines Paares: abgeschnittene Summe über 400 simulierte Runden.
2. Replikatordynamik: scipy.integrate.solve_ivp (RK45, enge Toleranz) gegen das eigene Runge-Kutta-Verfahren.
3. Evolutionäre Stabilität: Maynard Smiths Originaldefinition per kleinem ε (Fitness des Mutanten in (1 − ε) i + ε j), ohne Fallunterscheidung.
4. Fixationswahrscheinlichkeit: Absorptionswahrscheinlichkeit der Geburts-Tod-Kette als lineares System UND Monte-Carlo-Simulation des Moran-Prozesses."""

import itertools
import random

import numpy as np
import pytest

import rpl_algorithm as A
import rpl_constants as C
from rpl_scenario import STRATEGIES

KEYS = C.STRATEGY_KEYS


@pytest.mark.parametrize("delta", [0.3, 0.6, 0.9])
def test_pair_value_matches_the_truncated_sum(delta):
    for ka, kb in itertools.product(KEYS, KEYS):
        a, b = STRATEGIES[ka], STRATEGIES[kb]
        trunc = sum(delta ** t * stage for t, stage in enumerate(
            np.array([C.R, C.S, C.T, C.P])[[0 if (x, y) == (0, 0) else 1 if (x, y) == (0, 1) else 2 if (x, y) == (1, 0) else 3
                                              for x, y in A.play(a, b, 400)]]))
        assert A.discounted_value(a, b, delta) == pytest.approx(trunc, abs=1e-6), (ka, kb)


@pytest.mark.parametrize("delta,alld", [(0.8, 0.1), (0.4, 0.1), (0.7, 0.3), (0.7, 0.4)])
def test_replicator_matches_scipy(delta, alld):
    solve_ivp = pytest.importorskip("scipy.integrate").solve_ivp
    m = A.payoff_matrix(KEYS, delta)
    x0 = A.initial_mix(6, KEYS.index("ALLD"), alld)
    times, traj = A.integrate(m, x0, t_max=30.0, dt=0.05, record_every=20)
    sol = solve_ivp(lambda t, x: A.replicator_rhs(x, m), (0.0, 30.0), x0, t_eval=times, rtol=1e-10, atol=1e-12)
    assert np.max(np.abs(sol.y.T - traj)) < 1e-5


def test_replicator_matches_scipy_on_a_random_matrix():
    solve_ivp = pytest.importorskip("scipy.integrate").solve_ivp
    rng = np.random.default_rng(4)
    m = rng.uniform(0.0, 5.0, size=(4, 4))
    x0 = np.array([0.4, 0.3, 0.2, 0.1])
    times, traj = A.integrate(m, x0, t_max=10.0, dt=0.02, record_every=25)
    sol = solve_ivp(lambda t, x: A.replicator_rhs(x, m), (0.0, 10.0), x0, t_eval=times, rtol=1e-10, atol=1e-12)
    assert np.max(np.abs(sol.y.T - traj)) < 1e-6


def ess_by_epsilon(m, i, eps=1e-6):
    """i ist ESS, wenn gegen JEDEN Mutanten j bei kleinem ε der Resident mehr verdient (Maynard Smith/Price)."""
    n = m.shape[0]
    for j in range(n):
        if j == i:
            continue
        pay_i = (1 - eps) * m[i, i] + eps * m[i, j]
        pay_j = (1 - eps) * m[j, i] + eps * m[j, j]
        if pay_i - pay_j <= 1e-12:
            return False
    return True


@pytest.mark.parametrize("delta", [0.2, 0.45, 0.5, 0.6, 0.67, 0.8, 0.95])
def test_ess_classification_matches_the_epsilon_definition(delta):
    m = A.payoff_matrix(KEYS, delta)
    for c in A.classify(m):
        assert c["ess"] == ess_by_epsilon(m, c["index"]), (delta, KEYS[c["index"]])


def absorption_probability(m, mutant, resident, n, w):
    """ρ als Lösung des linearen Gleichungssystems der Geburts-Tod-Kette (Zustand k = Zahl der Mutanten), unabhängig von der Produktformel."""
    def fitness(k):
        pa = ((k - 1) * m[mutant, mutant] + (n - k) * m[mutant, resident]) / (n - 1)
        pb = (k * m[resident, mutant] + (n - k - 1) * m[resident, resident]) / (n - 1)
        return 1 - w + w * pa, 1 - w + w * pb

    size = n - 1                      # transiente Zustände k = 1 .. n−1
    mat = np.zeros((size, size))
    rhs = np.zeros(size)
    for k in range(1, n):
        fa, fb = fitness(k)
        total = k * fa + (n - k) * fb
        up = (k * fa / total) * ((n - k) / n)
        down = ((n - k) * fb / total) * (k / n)
        stay = 1.0 - up - down
        row = k - 1
        mat[row, row] = 1.0 - stay
        if k - 1 >= 1:
            mat[row, row - 1] = -down
        if k + 1 <= n - 1:
            mat[row, row + 1] = -up
        else:
            rhs[row] = up                   # Absorption bei n Mutanten
    return float(np.linalg.solve(mat, rhs)[0])


@pytest.mark.parametrize("mutant,resident", [("ALLD", "ALLC"), ("ALLD", "PAVLOV"), ("TFT", "ALLD"), ("ALLD", "TFT"), ("TF2T", "ALLD"), ("ALLC", "TFT")])
@pytest.mark.parametrize("n,w", [(10, 0.5), (50, 0.5), (30, 1.0), (20, 0.1)])
def test_fixation_matches_the_linear_system(mutant, resident, n, w):
    m = A.payoff_matrix(KEYS, 0.8)
    got = A.fixation_probability(m, KEYS.index(mutant), KEYS.index(resident), n, w)
    assert got == pytest.approx(absorption_probability(m, KEYS.index(mutant), KEYS.index(resident), n, w), abs=1e-9)


def test_fixation_matches_a_monte_carlo_moran_process():
    m = A.payoff_matrix(KEYS, 0.8)
    mutant, resident, n, w = KEYS.index("ALLD"), KEYS.index("ALLC"), 6, 0.8
    rng = random.Random(21)
    wins, runs = 0, 6000
    for _ in range(runs):
        k = 1
        while 0 < k < n:
            pa = ((k - 1) * m[mutant, mutant] + (n - k) * m[mutant, resident]) / (n - 1)
            pb = (k * m[resident, mutant] + (n - k - 1) * m[resident, resident]) / (n - 1)
            fa, fb = 1 - w + w * pa, 1 - w + w * pb
            born_mutant = rng.random() < k * fa / (k * fa + (n - k) * fb)
            dies_mutant = rng.random() < k / n
            k += (1 if born_mutant else 0) - (1 if dies_mutant else 0)
        wins += k == n
    expected = A.fixation_probability(m, mutant, resident, n, w)
    assert wins / runs == pytest.approx(expected, abs=0.02)


def test_basin_threshold_matches_direct_integration():
    from rpl_evaluation import basin
    b = basin(deltas=[0.5, 0.7, 0.8], shares=[round(0.01 * i, 2) for i in range(0, 61)])
    a = KEYS.index("ALLD")
    for d, th in zip(b["deltas"], b["threshold"]):
        m = A.payoff_matrix(KEYS, d)
        end = lambda s: A.integrate(m, A.initial_mix(6, a, s))[1][-1][a]   # noqa: E731
        if th is None:
            assert end(0.6) < 0.5
        else:
            assert end(th) > 0.5
            below = round(th - 0.01, 2)
            if below >= 0:
                assert end(below) <= 0.5
