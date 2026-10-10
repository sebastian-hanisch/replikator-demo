"""Szenario: das Gefangenendilemma 5/3/1/0 und die sechs Strategien als endliche Automaten (wie in tit-for-tat-demo).

Ein Automat hat je Zustand eine Aktion; der Folgezustand hängt von der Aktion des Gegners ab. Zwei Automaten bilden einen gemeinsamen Zustand,
aus dem sich der diskontierte Wert eines Paares als lineares System ergibt."""

from dataclasses import dataclass

import rpl_constants as C


def stage_payoff(own: int, other: int) -> float:
    """Auszahlung einer Runde für die eigene Aktion gegen die des anderen (0 = C, 1 = D)."""
    if own == C.COOPERATE:
        return C.R if other == C.COOPERATE else C.S
    return C.T if other == C.COOPERATE else C.P


@dataclass(frozen=True)
class Automaton:
    key: str
    label: str
    outputs: tuple[int, ...]                 # Aktion je Zustand
    trans: tuple[tuple[int, int], ...]       # trans[zustand][Aktion des Gegners] = nächster Zustand
    description: str

    @property
    def size(self) -> int:
        return len(self.outputs)


def _automata() -> dict[str, Automaton]:
    c, d = C.COOPERATE, C.DEFECT
    items = [
        Automaton("ALLC", "Immer kooperieren", (c,), ((0, 0),), "Bietet jede Woche eine Rückladung an, egal was der andere tut."),
        Automaton("ALLD", "Immer defektieren", (d,), ((0, 0),), "Nutzt nur, bietet nie an."),
        Automaton("TFT", "Tit-for-Tat", (c, d), ((0, 1), (0, 1)),
                  "Beginnt mit Kooperation und macht danach exakt das, was der andere zuletzt getan hat."),
        Automaton("GRIM", "Grim Trigger", (c, d), ((0, 1), (1, 1)),
                  "Kooperiert, bis der andere einmal defektiert; danach nie wieder."),
        Automaton("TF2T", "Tit-for-Two-Tats", (c, c, d), ((0, 1), (0, 2), (0, 2)),
                  "Verzeiht eine einzelne Defektion; defektiert erst nach zwei Defektionen in Folge."),
        Automaton("PAVLOV", "Pavlov (Win-Stay-Lose-Shift)", (c, d), ((0, 1), (1, 0)),
                  "Behält die letzte Aktion bei, wenn der andere kooperiert hat, und wechselt sie, wenn er defektiert hat."),
    ]
    return {a.key: a for a in items}


STRATEGIES = _automata()
assert tuple(STRATEGIES) == C.STRATEGY_KEYS

# Hilfsautomat für die Erklärspur (nicht in der Strategienwahl): defektiert und kooperiert im Wechsel, beginnend mit Defektion.
ALTERNATE = Automaton("ALT", "Abwechsler", (C.DEFECT, C.COOPERATE), ((1, 1), (0, 0)), "Defektiert und kooperiert im Wechsel.")
