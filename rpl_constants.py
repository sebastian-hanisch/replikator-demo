"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""

COOPERATE, DEFECT = 0, 1

# Auszahlungen je Runde (Axelrod), fest.
T, R, P, S = 5.0, 3.0, 1.0, 0.0

DELTA_MIN, DELTA_MAX, DEFAULT_DELTA, DELTA_STEP = 0.30, 0.95, 0.80, 0.01
ALLD_MIN, ALLD_MAX, DEFAULT_ALLD, ALLD_STEP = 0.0, 0.60, 0.10, 0.01
N_MIN, N_MAX, DEFAULT_N, N_STEP = 10, 200, 50, 10
W_MIN, W_MAX, DEFAULT_W, W_STEP = 0.05, 1.0, 0.50, 0.05

TIME_MAX = 60.0                      # Zeithorizont der Replikatordynamik (Zeiteinheit: eine Fitnessdifferenz von 1 je Zeiteinheit)
DT = 0.05                            # Schrittweite des Runge-Kutta-Verfahrens
RECORD_EVERY = 10                    # jede 10. Schritt in der Spur speichern

STRATEGY_KEYS = ("ALLC", "ALLD", "TFT", "GRIM", "TF2T", "PAVLOV")
DEFAULT_FIELD = STRATEGY_KEYS
FOCUS = "TFT"

TOL = 1e-9                           # Toleranz für „gleich“ bei Auszahlungsvergleichen

MU_MIN, MU_MAX, DEFAULT_MU, MU_STEP = 0.0005, 0.02, 0.002, 0.0005
STEPS_MIN, STEPS_MAX, DEFAULT_STEPS, STEPS_STEP = 5000, 60000, 30000, 5000
SEED_MAX, DEFAULT_SEED = 999999, 20264

BASIN_DELTAS = tuple(round(0.30 + 0.05 * i, 2) for i in range(14))      # 0,30 bis 0,95
BASIN_SHARES = tuple(round(0.02 * i, 2) for i in range(0, 31))          # Anfangsanteil von Immer-Defektieren, 0 bis 0,60
ESS_DELTAS = tuple(round(0.05 * i, 2) for i in range(1, 20))            # 0,05 bis 0,95

COLORS = {
    "ALLC": "#9aa5b1", "ALLD": "#B5483A", "TFT": "#4c78a8", "GRIM": "#7b5ea7", "TF2T": "#6fa8a0", "PAVLOV": "#e08a2c",
}

PRESETS = {
    "Alle sechs, 10 % Immer-Defektieren (δ = 0,80)": {"field": STRATEGY_KEYS, "delta": 0.80, "alld": 0.10, "n": 50, "w": 0.5},
    "Kurzer Schatten (δ = 0,40)": {"field": STRATEGY_KEYS, "delta": 0.40, "alld": 0.10, "n": 50, "w": 0.5},
    "Knapp unter der Grenze (δ = 0,70, 30 %)": {"field": STRATEGY_KEYS, "delta": 0.70, "alld": 0.30, "n": 50, "w": 0.5},
    "Knapp über der Grenze (δ = 0,70, 40 %)": {"field": STRATEGY_KEYS, "delta": 0.70, "alld": 0.40, "n": 50, "w": 0.5},
    "Nur Tit-for-Tat, Immer-Kooperieren, Immer-Defektieren": {"field": ("ALLC", "ALLD", "TFT"), "delta": 0.80, "alld": 0.05, "n": 50, "w": 0.5},
    "Ohne Immer-Defektieren": {"field": ("ALLC", "TFT", "GRIM", "TF2T", "PAVLOV"), "delta": 0.80, "alld": 0.0, "n": 50, "w": 0.5},
}
PRESET_HELP = {
    "Alle sechs, 10 % Immer-Defektieren (δ = 0,80)": "Die Beziehung läuft im Mittel fünf Runden weiter: Die Kooperierenden setzen sich gegen Immer-Defektieren durch.",
    "Kurzer Schatten (δ = 0,40)": "Kurze Beziehungen: Schon 10 % Immer-Defektieren verdrängen alle, obwohl alle anderen miteinander besser führen.",
    "Knapp unter der Grenze (δ = 0,70, 30 %)": "Bei δ = 0,70 liegt die Anfangsgrenze bei etwa 35 %: mit 30 % Defektierern setzt sich die Kooperation noch durch.",
    "Knapp über der Grenze (δ = 0,70, 40 %)": "Dieselbe Beziehungsdauer, aber 40 % Defektierer: jetzt kippt die Population zu Immer-Defektieren.",
    "Nur Tit-for-Tat, Immer-Kooperieren, Immer-Defektieren": "Das kleinste Feld, in dem Tit-for-Tat nicht evolutionär stabil ist: Immer-Kooperieren ist gegen Tit-for-Tat ein neutraler Eindringling.",
    "Ohne Immer-Defektieren": "Ohne Ausbeuter bekommen alle Kooperierenden dasselbe: die Anteile bleiben, wie sie sind.",
}
