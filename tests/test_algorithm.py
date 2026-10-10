"""Mini-Instanz-Tests je Einheit (DEMO-PLAYBOOK §1b): alles von Hand gerechnet, Auszahlungen 5/3/1/0."""

import numpy as np
import pytest

import rpl_algorithm as A
import rpl_constants as C
from rpl_scenario import ALTERNATE, STRATEGIES, stage_payoff

S = STRATEGIES


def test_stage_payoffs():
    assert stage_payoff(0, 0) == 3 and stage_payoff(0, 1) == 0 and stage_payoff(1, 0) == 5 and stage_payoff(1, 1) == 1


def test_play_traces():
    assert A.play(S["TFT"], S["ALLD"], 4) == [(0, 1), (1, 1), (1, 1), (1, 1)]
    assert A.play(S["TF2T"], S["ALLD"], 4) == [(0, 1), (0, 1), (1, 1), (1, 1)]
    assert A.play(S["GRIM"], ALTERNATE, 4) == [(0, 1), (1, 0), (1, 1), (1, 0)]
    assert A.play(S["PAVLOV"], S["ALLD"], 4) == [(0, 1), (1, 1), (0, 1), (1, 1)]


def test_discounted_values_by_hand():
    d = 0.5
    assert A.discounted_value(S["TFT"], S["TFT"], d) == pytest.approx(6.0)          # R / (1 − δ)
    assert A.discounted_value(S["ALLD"], S["ALLD"], d) == pytest.approx(2.0)        # P / (1 − δ)
    assert A.discounted_value(S["TFT"], S["ALLD"], d) == pytest.approx(1.0)         # S + δ P / (1 − δ)
    assert A.discounted_value(S["ALLD"], S["TFT"], d) == pytest.approx(6.0)         # T + δ P / (1 − δ)
    assert A.discounted_value(S["ALLD"], S["ALLC"], d) == pytest.approx(10.0)       # T / (1 − δ)
    assert A.discounted_value(S["ALLC"], S["ALLD"], d) == pytest.approx(0.0)


def test_payoff_matrix_by_hand(m08, idx):
    i = idx
    assert m08[i["TFT"], i["TFT"]] == pytest.approx(3.0)
    assert m08[i["ALLD"], i["TFT"]] == pytest.approx(1.8)            # (1 − δ) · (T + δ P / (1 − δ)) = 0,2 · 9
    assert m08[i["TFT"], i["ALLD"]] == pytest.approx(0.8)            # 0,2 · (0 + 0,8 · 5)
    assert m08[i["TF2T"], i["ALLD"]] == pytest.approx(0.64)          # 0,2 · 0,64 · 5
    assert m08[i["ALLD"], i["ALLC"]] == pytest.approx(5.0)
    assert m08[i["ALLD"], i["ALLD"]] == pytest.approx(1.0)
    assert m08[i["PAVLOV"], i["ALLD"]] == pytest.approx(0.8 / 0.36 * 0.2)   # C,D,C,D, ... gegen Immer-D


def test_payoff_matrix_validates_delta():
    with pytest.raises(ValueError):
        A.payoff_matrix(C.STRATEGY_KEYS, 1.0)
    with pytest.raises(ValueError):
        A.payoff_matrix(C.STRATEGY_KEYS, -0.1)


def test_classify_at_delta_0_8(m08, idx):
    cl = A.classify(m08)
    by = {C.STRATEGY_KEYS[c["index"]]: c for c in cl}
    assert by["ALLD"]["ess"] and by["ALLD"]["nash"]
    assert not by["TFT"]["ess"] and by["TFT"]["nash"]
    assert sorted(by["TFT"]["neutral_invaders"]) == sorted(idx[k] for k in ("ALLC", "GRIM", "TF2T", "PAVLOV"))
    assert by["ALLC"]["strict_invaders"] == [idx["ALLD"]]
    assert by["PAVLOV"]["strict_invaders"] == [idx["ALLD"]]
    assert not by["ALLC"]["nash"]


def test_classify_at_a_short_shadow_alld_beats_tft(idx):
    cl = {C.STRATEGY_KEYS[c["index"]]: c for c in A.classify(A.payoff_matrix(C.STRATEGY_KEYS, 0.3))}
    assert idx["ALLD"] in cl["TFT"]["strict_invaders"] and not cl["TFT"]["nash"]
    assert cl["ALLD"]["ess"]


def test_replicator_rhs_conserves_the_total_and_vanishes_at_pure_states(m08):
    x = np.array([0.1, 0.2, 0.3, 0.1, 0.2, 0.1])
    assert A.replicator_rhs(x, m08).sum() == pytest.approx(0.0, abs=1e-12)
    for i in range(6):
        e = np.zeros(6)
        e[i] = 1.0
        assert np.allclose(A.replicator_rhs(e, m08), 0.0)


def test_replicator_two_strategies_by_hand():
    """2 × 2 mit a > c, d > b (Koordination): ẋ = x (1 − x) ((a − c) x − (d − b) (1 − x)). Hier a = 3, b = 0, c = 1, d = 1."""
    m = np.array([[3.0, 0.0], [1.0, 1.0]])
    x = np.array([0.4, 0.6])
    expected = 0.4 * 0.6 * ((3.0 - 1.0) * 0.4 - (1.0 - 0.0) * 0.6)
    assert A.replicator_rhs(x, m)[0] == pytest.approx(expected)


def test_replicator_batch_equals_single(m08):
    xs = np.array([[0.1, 0.2, 0.3, 0.1, 0.2, 0.1], [1 / 6] * 6])
    batch = A.replicator_rhs(xs, m08)
    assert batch[0] == pytest.approx(A.replicator_rhs(xs[0], m08))
    assert batch[1] == pytest.approx(A.replicator_rhs(xs[1], m08))


def test_integrate_keeps_the_simplex_and_records_the_end_state(m08):
    x0 = A.initial_mix(6, 1, 0.1)
    times, traj = A.integrate(m08, x0, t_max=5.0, dt=0.05, record_every=7)
    assert traj.shape[1] == 6
    assert np.allclose(traj.sum(axis=1), 1.0) and (traj >= 0).all()
    assert times[-1] == pytest.approx(5.0)                           # Endzustand auch bei schiefem record_every
    assert traj[0] == pytest.approx(x0)


def test_alld_dies_out_at_a_long_shadow_and_wins_at_a_short_one():
    keys = C.STRATEGY_KEYS
    a = keys.index("ALLD")
    long_run = A.integrate(A.payoff_matrix(keys, 0.8), A.initial_mix(6, a, 0.1))[1][-1]
    short_run = A.integrate(A.payoff_matrix(keys, 0.4), A.initial_mix(6, a, 0.1))[1][-1]
    assert long_run[a] < 1e-3 and short_run[a] > 0.999


def test_initial_mix():
    x = A.initial_mix(6, 1, 0.1)
    assert x.sum() == pytest.approx(1.0) and x[1] == pytest.approx(0.1) and x[0] == pytest.approx(0.18)
    assert A.initial_mix(3, None, 0.5) == pytest.approx([1 / 3] * 3)


def test_fixation_neutral_and_validation(m08, idx):
    n = 50
    assert A.fixation_probability(m08, idx["ALLC"], idx["TFT"], n, 0.5) == pytest.approx(1 / n)    # gleiche Auszahlung gegen TFT
    assert A.fixation_probability(m08, idx["ALLD"], idx["TFT"], n, 0.0) == pytest.approx(1 / n)    # w = 0: reiner Zufall
    assert A.fixation_probability(m08, idx["TFT"], idx["TFT"], n, 0.5) == pytest.approx(1 / n)
    with pytest.raises(ValueError):
        A.fixation_probability(m08, 0, 1, 1, 0.5)
    with pytest.raises(ValueError):
        A.fixation_probability(m08, 0, 1, 10, 1.5)


def test_fixation_by_hand_two_strategies():
    """N = 2: ein Mutant, ein Resident. Fitness a = 1 − w + w · M[a,b], b = 1 − w + w · M[b,a]; ρ = a / (a + b)."""
    m = np.array([[2.0, 4.0], [1.0, 3.0]])
    w = 0.5
    fa, fb = 1 - w + w * 4.0, 1 - w + w * 1.0
    assert A.fixation_probability(m, 0, 1, 2, w) == pytest.approx(fa / (fa + fb))


def test_moran_run_counts_and_reproducibility(m08):
    h = A.moran_run(m08, 20, 0.5, 0.01, 500, seed=3, start=2)
    assert h.shape == (500, 6)
    assert (h.sum(axis=1) == 20).all()
    assert (A.moran_run(m08, 20, 0.5, 0.01, 500, seed=3, start=2) == h).all()
    assert not (A.moran_run(m08, 20, 0.5, 0.01, 500, seed=4, start=2) == h).all()


def test_moran_without_mutation_stays_monomorphic(m08):
    h = A.moran_run(m08, 15, 0.5, 0.0, 300, seed=1, start=2)
    assert (h[:, 2] == 15).all()


def test_moran_run_validates():
    with pytest.raises(ValueError):
        A.moran_run(np.eye(2), 1, 0.5, 0.0, 10, 1, 0)
