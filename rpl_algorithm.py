"""Kern der Demo (numpy): Replikatordynamik, evolutionäre Stabilität und Fixationswahrscheinlichkeiten im wiederholten Dilemma.

Einheiten (DEMO-PLAYBOOK §1b):

- `discounted_value`    diskontierter Wert eines Strategienpaares (lineares System über die gemeinsamen Zustände)
- `payoff_matrix`       mittlere Auszahlung je Runde, Zeile gegen Spalte: (1 − δ) · Wert
- `classify`            Nash, evolutionär stabil (ESS), strikte und neutrale Eindringlinge je Strategie
- `replicator_rhs`      rechte Seite der Replikatorgleichung, für viele Anfangswerte gleichzeitig
- `integrate`           Runge-Kutta 4. Ordnung, Spur der Anteile
- `fixation_probability` Wahrscheinlichkeit, dass ein einzelner Mutant eine Population der Größe N übernimmt (Moran-Prozess)"""

import numpy as np

import rpl_constants as C
from rpl_scenario import STRATEGIES, Automaton, stage_payoff


def play(a: Automaton, b: Automaton, rounds: int) -> list[tuple[int, int]]:
    """Die ersten `rounds` Aktionspaare; beide starten im Zustand 0."""
    sa = sb = 0
    out = []
    for _ in range(rounds):
        x, y = a.outputs[sa], b.outputs[sb]
        out.append((x, y))
        sa, sb = a.trans[sa][y], b.trans[sb][x]
    return out


def discounted_value(a: Automaton, b: Automaton, delta: float) -> float:
    """V = Σ δ^t · u_t für `a` gegen `b`: (I − δP) V = u über die gemeinsamen Zustände."""
    na, nb = a.size, b.size
    n = na * nb
    mat = np.eye(n)
    rhs = np.zeros(n)
    for sa in range(na):
        for sb in range(nb):
            i = sa * nb + sb
            x, y = a.outputs[sa], b.outputs[sb]
            rhs[i] = stage_payoff(x, y)
            mat[i, a.trans[sa][y] * nb + b.trans[sb][x]] -= delta
    return float(np.linalg.solve(mat, rhs)[0])


def payoff_matrix(keys, delta: float) -> np.ndarray:
    """M[i, j] = mittlere Auszahlung je Runde der Strategie i gegen j: (1 − δ) · V."""
    if not 0.0 <= delta < 1.0:
        raise ValueError("δ muss in [0, 1) liegen")
    return np.array([[(1.0 - delta) * discounted_value(STRATEGIES[i], STRATEGIES[j], delta) for j in keys] for i in keys])


def classify(m: np.ndarray, tol: float = C.TOL) -> list[dict]:
    """Je Strategie i:

    - `nash`: kein anderes j erzielt gegen i mehr als i selbst (M[j,i] ≤ M[i,i]);
    - `strict_invaders`: j mit M[j,i] > M[i,i] (j verdrängt i);
    - `neutral_invaders`: j mit M[j,i] = M[i,i] und M[i,j] ≤ M[j,j] (j kann sich ohne Nachteil ausbreiten);
    - `ess`: Nash und jeder Gleichstand wird zugunsten von i entschieden, also M[i,j] > M[j,j] (Maynard Smith)."""
    n = m.shape[0]
    out = []
    for i in range(n):
        strict, neutral = [], []
        for j in range(n):
            if j == i:
                continue
            if m[j, i] > m[i, i] + tol:
                strict.append(j)
            elif abs(m[j, i] - m[i, i]) <= tol and m[i, j] <= m[j, j] + tol:
                neutral.append(j)
        out.append({"index": i, "nash": not strict, "ess": not strict and not neutral, "strict_invaders": strict, "neutral_invaders": neutral})
    return out


def replicator_rhs(x: np.ndarray, m: np.ndarray) -> np.ndarray:
    """ẋ_i = x_i · ((M x)_i − x·M x). `x`: (n,) oder (G, n)."""
    x2 = np.atleast_2d(x)
    payoff = x2 @ m.T
    mean = np.sum(x2 * payoff, axis=1, keepdims=True)
    out = x2 * (payoff - mean)
    return out.reshape(x.shape)


def integrate(m: np.ndarray, x0: np.ndarray, t_max: float = C.TIME_MAX, dt: float = C.DT, record_every: int = C.RECORD_EVERY):
    """Runge-Kutta 4. Ordnung. Gibt (Zeiten, Anteile) zurück; Anteile haben die Form (Zeitpunkte, n) bzw. (Zeitpunkte, G, n)."""
    x = np.array(x0, dtype=float)
    steps = int(round(t_max / dt))
    times, traj = [0.0], [x.copy()]
    for k in range(1, steps + 1):
        k1 = replicator_rhs(x, m)
        k2 = replicator_rhs(x + 0.5 * dt * k1, m)
        k3 = replicator_rhs(x + 0.5 * dt * k2, m)
        k4 = replicator_rhs(x + dt * k3, m)
        x = x + dt / 6.0 * (k1 + 2 * k2 + 2 * k3 + k4)
        x = np.clip(x, 0.0, None)
        x = x / np.sum(x, axis=-1, keepdims=True)         # numerische Drift zurück auf das Simplex
        if k % record_every == 0 or k == steps:        # der Endzustand wird immer aufgenommen
            times.append(k * dt)
            traj.append(x.copy())
    return np.array(times), np.array(traj)


def initial_mix(n: int, alld_index: int | None, alld_share: float) -> np.ndarray:
    """Anfangsanteile: `alld_share` für Immer-Defektieren (falls dabei), der Rest gleich auf die übrigen verteilt."""
    if alld_index is None or n == 1:
        return np.full(n, 1.0 / n)
    x = np.full(n, (1.0 - alld_share) / (n - 1))
    x[alld_index] = alld_share
    return x


def fixation_probability(m: np.ndarray, mutant: int, resident: int, n_pop: int, w: float) -> float:
    """Wahrscheinlichkeit, dass ein einzelner `mutant` in einer Population aus n_pop − 1 `resident` die ganze Population übernimmt.

    Moran-Prozess: Fitness 1 − w + w · Auszahlung (Auszahlung gegen die jeweils anderen n_pop − 1 Mitglieder), Fortpflanzung proportional
    zur Fitness, Tod gleichverteilt. ρ = 1 / (1 + Σ_{k=1}^{N−1} Π_{j=1}^{k} (T⁻_j / T⁺_j)). Neutral (w = 0 oder gleiche Auszahlungen): 1/N."""
    if n_pop < 2:
        raise ValueError("Population mindestens 2")
    if not 0.0 <= w <= 1.0:
        raise ValueError("w muss in [0, 1] liegen")
    if mutant == resident:
        return 1.0 / n_pop
    n = n_pop
    total, prod = 0.0, 1.0
    for k in range(1, n):                               # k Mutanten
        pay_a = ((k - 1) * m[mutant, mutant] + (n - k) * m[mutant, resident]) / (n - 1)
        pay_b = (k * m[resident, mutant] + (n - k - 1) * m[resident, resident]) / (n - 1)
        fit_a, fit_b = 1.0 - w + w * pay_a, 1.0 - w + w * pay_b
        if fit_a <= 0.0 and fit_b <= 0.0:
            ratio = 1.0                                 # beide Typen ohne Fitness: kein Unterschied
        elif fit_a <= 0.0:
            return 0.0                                  # der Mutant pflanzt sich nie fort: er kann sich nicht ausbreiten
        else:
            ratio = fit_b / fit_a                       # T⁻ / T⁺ = f_B / f_A
        prod *= ratio
        total += prod
        if prod == float("inf") or total == float("inf"):
            return 0.0
    return float(1.0 / (1.0 + total))


def fixation_matrix(m: np.ndarray, n_pop: int, w: float) -> np.ndarray:
    """ρ[i, j]: Wahrscheinlichkeit, dass ein einzelner i eine Population aus j übernimmt (Diagonale: 1/N)."""
    n = m.shape[0]
    return np.array([[fixation_probability(m, i, j, n_pop, w) for j in range(n)] for i in range(n)])


def moran_run(m: np.ndarray, n_pop: int, w: float, mu: float, steps: int, seed: int, start: int) -> np.ndarray:
    """Ein Moran-Prozess mit Mutation: Anzahl je Strategie nach jedem Schritt, Form (steps, n).

    Je Schritt: Fortpflanzung proportional zur Fitness (1 − w + w · Auszahlung gegen die übrigen n_pop − 1), mit Wahrscheinlichkeit `mu` wird
    stattdessen eine zufällige Strategie geboren; ein zufälliges Individuum stirbt. Start: die ganze Population spielt `start`."""
    import random

    if n_pop < 2 or steps < 1:
        raise ValueError("Population mindestens 2, mindestens ein Schritt")
    rng = random.Random(seed)
    n = m.shape[0]
    counts = np.zeros(n, dtype=np.int64)
    counts[start] = n_pop
    diag = np.diag(m)
    hist = np.zeros((steps, n), dtype=np.int16)
    for t in range(steps):
        pay = (m @ counts - diag) / (n_pop - 1)
        fit = np.where(counts > 0, 1.0 - w + w * pay, 0.0)
        weights = fit * counts
        i = min(int(np.searchsorted(np.cumsum(weights), rng.random() * weights.sum())), n - 1)
        if rng.random() < mu:
            i = rng.randrange(n)
        j = min(int(np.searchsorted(np.cumsum(counts), rng.random() * n_pop, side="right")), n - 1)
        counts[j] -= 1
        counts[i] += 1
        hist[t] = counts
    return hist


def basin_final_shares(m: np.ndarray, alld_index: int, shares) -> np.ndarray:
    """Endanteil von Immer-Defektieren je Anfangsanteil (alle übrigen gleich verteilt), alle Anfangswerte gleichzeitig integriert."""
    n = m.shape[0]
    starts = np.array([initial_mix(n, alld_index, s) for s in shares])
    _, traj = integrate(m, starts, record_every=10 ** 9)
    return traj[-1][:, alld_index]
