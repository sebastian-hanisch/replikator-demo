"""Kennzahlen, Verdikt-Logik und Auswertungen über den Kern (die Komposition der Einheiten aus rpl_algorithm)."""

from dataclasses import dataclass

import numpy as np

import rpl_algorithm as A
import rpl_constants as C
from rpl_scenario import STRATEGIES


def fmt(x: float, digits: int = 2) -> str:
    """Zahl mit deutschem Dezimalkomma."""
    return f"{x:.{digits}f}".replace(".", ",")


def label(key: str) -> str:
    return STRATEGIES[key].label


@dataclass(frozen=True)
class Settings:
    field: tuple[str, ...] = C.DEFAULT_FIELD
    delta: float = C.DEFAULT_DELTA
    alld: float = C.DEFAULT_ALLD
    n_pop: int = C.DEFAULT_N
    w: float = C.DEFAULT_W


@dataclass(frozen=True)
class Analysis:
    keys: tuple[str, ...]
    matrix: tuple[tuple[float, ...], ...]
    classes: tuple[dict, ...]
    times: tuple[float, ...]
    shares: tuple[tuple[float, ...], ...]           # Anteile über die Zeit, Form (Zeitpunkte, n)
    final: tuple[float, ...]
    winners: tuple[str, ...]                        # Strategien mit mehr als 5 % Endanteil
    alld_wins: bool | None                          # None, wenn Immer-Defektieren nicht im Feld ist


def analyse(settings: Settings) -> Analysis:
    keys = tuple(settings.field)
    if len(keys) < 2:
        raise ValueError("mindestens zwei Strategien")
    m = A.payoff_matrix(keys, settings.delta)
    alld = keys.index("ALLD") if "ALLD" in keys else None
    x0 = A.initial_mix(len(keys), alld, settings.alld)
    times, traj = A.integrate(m, x0)
    final = traj[-1]
    return Analysis(
        keys=keys,
        matrix=tuple(tuple(float(v) for v in row) for row in m),
        classes=tuple(A.classify(m)),
        times=tuple(float(t) for t in times),
        shares=tuple(tuple(float(v) for v in row) for row in traj),
        final=tuple(float(v) for v in final),
        winners=tuple(k for k, v in zip(keys, final) if v > 0.05),
        alld_wins=None if alld is None else bool(final[alld] > 0.5),
    )


def ess_map(keys=C.STRATEGY_KEYS, deltas=C.ESS_DELTAS) -> dict:
    """Je δ: welche Strategien sind (unter den gewählten) Nash-Gleichgewicht und welche evolutionär stabil."""
    nash = {k: [] for k in keys}
    ess = {k: [] for k in keys}
    for d in deltas:
        cl = A.classify(A.payoff_matrix(keys, d))
        for c in cl:
            nash[keys[c["index"]]].append(c["nash"])
            ess[keys[c["index"]]].append(c["ess"])
    return {"deltas": list(deltas), "nash": nash, "ess": ess}


def basin(keys=C.STRATEGY_KEYS, deltas=C.BASIN_DELTAS, shares=C.BASIN_SHARES) -> dict:
    """Endanteil von Immer-Defektieren je (δ, Anfangsanteil) und die Schwelle: kleinster Anfangsanteil, ab dem es sich durchsetzt."""
    keys = tuple(keys)
    alld = keys.index("ALLD")
    final = []
    thresholds = []
    for d in deltas:
        row = A.basin_final_shares(A.payoff_matrix(keys, d), alld, shares)
        final.append([float(v) for v in row])
        wins = [s for s, v in zip(shares, row) if v > 0.5]
        thresholds.append(min(wins) if wins else None)
    return {"deltas": list(deltas), "shares": list(shares), "final": final, "threshold": thresholds}


def fixation(settings: Settings) -> np.ndarray:
    return A.fixation_matrix(A.payoff_matrix(settings.field, settings.delta), settings.n_pop, settings.w)


def drift(settings: Settings, mu: float, steps: int, seed: int, start: str = "TFT") -> dict:
    """Ein Moran-Lauf mit Mutation, gestartet in einer reinen Tit-for-Tat-Population (falls im Feld, sonst erste Strategie)."""
    keys = tuple(settings.field)
    m = A.payoff_matrix(keys, settings.delta)
    s0 = keys.index(start) if start in keys else 0
    hist = A.moran_run(m, settings.n_pop, settings.w, mu, steps, seed, s0)
    share = hist / settings.n_pop
    out = {"keys": keys, "share": share, "mean": share.mean(axis=0)}
    if "ALLD" in keys:
        a = share[:, keys.index("ALLD")]
        out["alld_majority_time"] = float((a > 0.5).mean())
        out["breakdowns"] = count_episodes(a)
    return out


def count_episodes(share, high: float = 0.5, low: float = 0.2) -> int:
    """Zahl der Einbrüche: ein Einbruch beginnt, wenn der Anteil über `high` steigt, und endet erst, wenn er unter `low` fällt
    (Hysterese, damit Flackern um die Schwelle nicht mehrfach zählt)."""
    episodes, active = 0, False
    for v in share:
        if not active and v > high:
            active = True
            episodes += 1
        elif active and v < low:
            active = False
    return episodes


def verdict_tft(an: Analysis) -> tuple[str, str]:
    """(Stufe, Satz): ist Tit-for-Tat unter den gewählten Strategien evolutionär stabil?"""
    if "TFT" not in an.keys:
        return "info", "Tit-for-Tat ist nicht im Feld."
    c = next(cl for cl in an.classes if an.keys[cl["index"]] == "TFT")
    names = lambda idx: ", ".join(label(an.keys[j]) for j in idx)  # noqa: E731
    if c["strict_invaders"]:
        return "warning", f"Tit-for-Tat wird von {names(c['strict_invaders'])} verdrängt: kein Gleichgewicht."
    if c["neutral_invaders"]:
        return "warning", (f"Tit-for-Tat ist ein Gleichgewicht, aber **nicht evolutionär stabil**: {names(c['neutral_invaders'])} verdrängen es nicht, "
                           "können sich aber ohne Nachteil in einer Tit-for-Tat-Population ausbreiten (neutrale Eindringlinge).")
    return "success", "Tit-for-Tat ist unter den gewählten Strategien evolutionär stabil."


def action_string(actions) -> str:
    return " ".join("C" if a == C.COOPERATE else "D" for a in actions)


def strategy_overview(rounds: int = 12) -> list[dict]:
    """Je Strategie: Beschreibung und die eigenen ersten `rounds` Aktionen gegen Immer-Defektieren und gegen einen Abwechsler (D, C, D, C, …)."""
    from rpl_scenario import ALTERNATE

    rows = []
    for key in C.STRATEGY_KEYS:
        auto = STRATEGIES[key]
        vs_alld = [x for x, _ in A.play(auto, STRATEGIES["ALLD"], rounds)]
        vs_alt = [x for x, _ in A.play(auto, ALTERNATE, rounds)]
        rows.append({"key": key, "label": auto.label, "description": auto.description,
                     "vs_alld": action_string(vs_alld), "vs_alt": action_string(vs_alt)})
    return rows


def class_rows(an: Analysis) -> list[dict]:
    """Zeilen der Stabilitätstabelle: Strategie, Gleichgewicht, evolutionär stabil, verdrängt von, neutrale Eindringlinge."""
    rows = []
    for c in an.classes:
        key = an.keys[c["index"]]
        rows.append({
            "key": key, "label": label(key), "nash": c["nash"], "ess": c["ess"],
            "strict": [label(an.keys[j]) for j in c["strict_invaders"]],
            "neutral": [label(an.keys[j]) for j in c["neutral_invaders"]],
        })
    return rows
