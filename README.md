# Evolutionäre Dynamik: warum Tit-for-Tat nicht stabil ist – Streamlit-Demo

<!-- Nach dem Deploy direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-replikator-demo.streamlit.app/)** -->

Viertes Stück der **Wiederholte-Spiele-Linie** in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“.
Nachfolger von [rauschen-kooperation-demo](https://sebastianhanisch-rauschen-kooperation-demo.streamlit.app/): dort ging es um Fehler zwischen zwei festen Partnern, hier
um **Populationen**, in denen sich Strategien nach Erfolg ausbreiten. Die Kante ist ein `fix`: Stück 1 bis 3 vergleichen Strategien paarweise; hier geht es um die Frage, welche
sich in einer ganzen Population hält.

Vehikel: ein Markt aus Spediteuren, die jede Woche Rückladungen tauschen (Auszahlungen 5/3/1/0, gewählt). Wer mehr verdient, wird nachgeahmt. Eigennutz und Imitation sind
Modellannahmen.

## Warum dieses Problem

Tit-for-Tat gilt als stabile Kooperation, ist aber **nicht evolutionär stabil**. Ein Eindringling, der gegen Tit-for-Tat genau so viel verdient wie Tit-for-Tat selbst, wird nicht
verdrängt und kann sich ohne Nachteil ausbreiten. Eine Population driftet dadurch zu Strategien, die für Defektierer angreifbar sind. Die Demo zeigt, **was daran
exakt stimmt, was in der Dynamik passiert, und wie stark es von der Populationsgröße abhängt**.

## Modell

Sechs Strategien als Automaten (wie in tit-for-tat-demo): Immer kooperieren, Immer defektieren, Tit-for-Tat, Grim Trigger, Tit-for-Two-Tats, Pavlov. Die Auszahlungsmatrix
`M[i,j]` ist die mittlere Auszahlung je Runde von i gegen j bei Schatten der Zukunft δ, exakt aus einem linearen System. Daraus folgen drei Sichten: die **Replikatordynamik**
(unendliche Population, deterministisch), die **evolutionäre Stabilität** (exakt aus der Matrix) und der **Moran-Prozess** (endliche Population, Zufall, Mutation).

## Methodik

- **Stabilität:** `classify`: Gleichgewicht, strikte und neutrale Eindringlinge, ESS nach Maynard Smith (Gleichstand wird über das Verhalten gegen den Eindringling entschieden).
- **Dynamik:** `integrate`: Runge-Kutta 4. Ordnung, Schrittweite 0,05, für viele Anfangswerte gleichzeitig (`basin_final_shares`).
- **Fixation:** `fixation_probability`: Wahrscheinlichkeit, dass ein einzelner Mutant eine Population der Größe N übernimmt; neutral 1/N.
- **Drift:** `moran_run`: Moran-Prozess mit Mutation; ein Einbruch zählt von Defektierer-Anteil über 50 % bis unter 20 % (Hysterese, damit Flackern nicht mehrfach zählt).

## Befunde (gemessen, keine Behauptungen)

Auszahlungen 5/3/1/0; Population aus den sechs Strategien, wenn nicht anders genannt.

| Frage | Befund | Test |
|---|---|---|
| Welche Strategie ist evolutionär stabil? | **Nur Immer-Defektieren, bei jedem δ.** Keine der kooperierenden ist es: unter ihnen gibt es immer neutrale Eindringlinge (Gleichstand gegeneinander). | `test_alld_is_the_only_ess_at_every_delta` |
| Und Tit-for-Tat? | Ein Gleichgewicht gegen die sechs ab δ = 0,5, aber nicht stabil: Immer kooperieren, Grim Trigger, Tit-for-Two-Tats und Pavlov verdienen gegen es und gegen sich selbst genau 3,00 und sind neutrale Eindringlinge. | `test_tft_is_never_evolutionarily_stable_but_a_nash_equilibrium_from_delta_one_half`, `test_neutral_invaders_of_tft_at_delta_0_8` |
| Was macht die Replikatordynamik bei δ = 0,80 mit 10 % Immer-Defektieren? | Immer-Defektieren stirbt aus. Endanteile: Immer kooperieren 14,8 %, Tit-for-Tat 22,7 %, Grim 22,7 %, Tit-for-Two-Tats 20,9 %, Pavlov 18,8 %. Immer kooperieren verliert am meisten, weil es ausgebeutet wird, solange Defektierer da sind. | `test_replicator_end_state_at_delta_0_8_with_ten_percent_alld` |
| Und bei δ = 0,40? | Immer-Defektieren verdrängt alle (Endanteil 100 %), schon aus 10 %. | `test_a_short_shadow_ends_in_all_defect` |
| Ab welchem Anfangsanteil setzen sich die Defektierer durch? | Bei δ ≤ 0,6 reichen etwa 1 bis 2 %; bei δ = 0,65 rund 4 %; bei δ = 0,70 rund 35 %; bei δ = 0,75 rund 55 %; ab δ = 0,80 setzen sie sich bis 60 % Anfangsanteil nicht mehr durch. | `test_basin_thresholds_by_delta`, `test_the_two_threshold_presets_straddle_the_boundary` |
| Wer erobert wen im Moran-Prozess (N = 50, w = 0,5, δ = 0,80)? | Ein einzelner Immer kooperieren, Grim, Tit-for-Two-Tats oder Pavlov in einer Tit-for-Tat-Population: genau ρ = 1/N = 0,020 (neutral). Ein einzelner Defektierer erobert Immer kooperieren mit 0,346, Pavlov mit 0,088, Tit-for-Two-Tats mit 0,004 und Tit-for-Tat mit weniger als 0,0001. Ein einzelnes Tit-for-Tat erobert eine Defektierer-Population mit 0,033 (über 1/N). | `test_fixation_probabilities_n_50_w_0_5_delta_0_8` |
| Driftet eine Tit-for-Tat-Population in den Einbruch? | In kleinen Populationen mit seltener Mutation ja, aber nicht in jedem Lauf: N = 20, μ = 0,002, 60000 Schritte, 6 Läufe: 3 von 6 mit mindestens einem Einbruch (2, 1, 0, 0, 0, 2), Immer-Defektieren hat im Mittel 7 % der Zeit die Mehrheit. Bei N = 50, μ = 0,01, 6000 Schritte, 20 Läufe: 5 von 20, im Mittel 6,6 % der Zeit, Tit-for-Tat hat im Mittel 71 % Anteil. | `test_drift_in_a_small_population_with_rare_mutation`, `test_drift_in_a_larger_population_with_frequent_mutation` |

### Befunde gegenüber dem Plan

Der Plan der Linie erwartete: „TFT ist keine ESS (neutrale Drift zu ALLC, dann Einbruch durch ALLD)“. Das stimmt im Kern, mit drei Präzisierungen:
(1) Die **deterministische** Replikatordynamik zeigt **keinen** Einbruch: Von gleichen Anfangsanteilen aus stirbt Immer-Defektieren bei δ ≥ 0,8 aus, die kooperierenden Anteile
verschieben sich nur leicht. Die Instabilität zeigt sich erst im **Zufallsprozess** der endlichen Population. (2) Der Einbruch geht nicht nur über Immer kooperieren: Eine
Pavlov-Population ist für einen einzelnen Defektierer mit ρ = 0,088 ebenfalls angreifbar, eine Tit-for-Tat-Population mit ρ < 0,0001 nicht. Angreifbar wird sie erst, wenn sie
durch Drift viele Immer kooperieren oder Pavlov enthält. (3) Ein Einbruch ist **kein** Dauerzustand und kein sicheres Ereignis: In meinen Läufen kippen etwa die Hälfte (N = 20)
beziehungsweise ein Viertel (N = 50) der Läufe mindestens einmal. Meine erste Einzelmessung bei N = 50 zeigte gar keinen Einbruch; erst 20 Läufe haben das korrigiert.

## Ehrliche Grenzen

- **Nur diese sechs Strategien:** „Gleichgewicht“ und „stabil“ gelten gegen die gewählte Menge. Gegen alle denkbaren Strategien ist Tit-for-Tat erst ab δ = 2/3 ein Gleichgewicht (tit-for-tat-demo).
- **Strenger Begriff:** evolutionär stabil im Sinn von Maynard Smith ist sehr stark. Mit einem abgeschwächten Begriff (Binmore/Samuelson 1992) oder mit Fehlern können Tit-for-Tat-artige
  Strategien bestehen.
- **Kein Rauschen** in der Matrix; **paarweise, gut durchmischte Begegnungen**, keine Netzwerke oder Orte; **Imitation nach Erfolg** als einzige Lernregel.
- **Moran-Läufe sind Zufall:** ein Lauf zeigt, dass ein Einbruch vorkommen kann, nicht wie oft. Die Zahlen stehen über 6 beziehungsweise 20 Läufe.
- **Literatur nur über Zusammenfassungen gelesen**, Band und Seiten von Taylor/Jonker (1978) nicht eindeutig bestätigt.

## Verifikation

- **Kern:** je Einheit eine Handrechnung (Auszahlungsmatrix, Klassifikation bei δ = 0,3 und 0,8, Replikatorgleichung 2×2 und Erhaltung der Summe, Fixation für N = 2, Moran-Lauf).
- **Orakel** (`tests/test_oracle_replikator.py`): (1) Paarwerte gegen die abgeschnittene Summe; (2) Replikatordynamik gegen `scipy.integrate.solve_ivp` (RK45, enge Toleranz);
  (3) die ESS-Einstufung gegen Maynard Smiths Originaldefinition per kleinem ε, ohne Fallunterscheidung; (4) die Fixationswahrscheinlichkeit gegen die Absorptionswahrscheinlichkeit
  der Geburts-Tod-Kette (lineares System) und gegen eine Monte-Carlo-Simulation.
- **Claims:** jede Zahl dieses READMEs in `tests/test_claims.py`.
- **Oberfläche:** AppTest (jeder Button, jeder Regler am Minimum und Maximum, Permalink begrenzt und rastet ein, eine Strategie allein zeigt eine Warnung, jede Strategie erklärt) und Footer-Test.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App |
| `requirements-dev.txt` | Laufzeit plus pytest und scipy (nur für das Orakel) |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `rpl_algorithm.py` | Kern: Paarwert, Matrix, Klassifikation, Replikatordynamik, Fixation, Moran-Lauf |
| `rpl_constants.py` | Regler-Grenzen, feste Annahmen, Farben, Presets |
| `rpl_evaluation.py` | Analyse, ESS-Karte, Basin, Fixationsmatrix, Drift, Strategieübersicht, Verdikt |
| `rpl_presets.py` | Permalink (Begrenzen und Einrasten), Presets |
| `rpl_scenario.py` | Das Spiel und die sechs Strategien als Automaten |
| `rpl_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `tests/` | Handrechnung, Orakel, Claims, Presets, AppTest-Smoke-Test, Footer |

## Bewusst nicht umgesetzt

- **Netzwerke und räumliche Strukturen** (wer wen trifft): eigenes Modell mit anderer Aussage.
- **Rauschen in der Matrix:** zeigt [rauschen-kooperation-demo](https://sebastianhanisch-rauschen-kooperation-demo.streamlit.app/) für zwei Partner.
- **Mehr als sechs Strategien oder eine Strategienmenge, die sich selbst entwickelt:** das wäre ein Evolutionsverfahren für Strategien, nicht die Dynamik einer gegebenen Menge.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly und NumPy.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
