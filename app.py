"""Evolutionäre Dynamik: warum Tit-for-Tat nicht stabil ist - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Viertes Stück der Wiederholte-Spiele-Linie: Strategien vermehren sich nach Erfolg. Replikatordynamik (unendliche Population), evolutionäre Stabilität
(ESS), Fixationswahrscheinlichkeiten und Drift in kleinen Populationen (Moran-Prozess).

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import rpl_constants as C
import rpl_evaluation as E
from rpl_evaluation import Settings, fmt, label
from rpl_presets import (
    apply_preset,
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sync_query_params,
)
from rpl_scenario import STRATEGIES
from rpl_visualization import build_basin, build_ess_map, build_fixation, build_shares

st.set_page_config(page_title="Evolutionäre Dynamik: warum Tit-for-Tat nicht stabil ist – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return E.analyse(settings)


@st.cache_data(show_spinner=False)
def _ess_map(keys):
    return E.ess_map(keys)


@st.cache_data(show_spinner=False)
def _basin(keys):
    return E.basin(keys) if "ALLD" in keys else None


@st.cache_data(show_spinner=False)
def _fixation(settings):
    return E.fixation(settings)


@st.cache_data(show_spinner=False)
def _drift(settings, mu, steps, seed):
    return E.drift(settings, mu, steps, seed)


@st.cache_data(show_spinner=False)
def _overview():
    return E.strategy_overview()


st.title("🧬 Evolutionäre Dynamik: warum Tit-for-Tat nicht stabil ist")
st.markdown(
    """
Bisher haben zwei Spediteure gegeneinander gespielt. Jetzt gibt es eine **ganze Population**: Wer in einer Runde mehr verdient, wird nachgeahmt, und die Anteile
der Strategien verschieben sich. Die Fragen sind dann andere: Welche Strategie kann **nicht mehr verdrängt** werden (**evolutionär stabil**)? Von welchem
Anfangsanteil an setzen sich die Defektierer durch? Und was passiert, wenn die Population klein ist und Zufall und Mutation mitspielen?

Der überraschende Teil: **Tit-for-Tat ist nicht evolutionär stabil**, obwohl es ein Gleichgewicht ist. Es gibt neutrale Eindringlinge, die sich ohne Nachteil
ausbreiten können, und eine Population, die dadurch driftet, wird für Defektierer angreifbar.

Weiter unten: **❓ Kernfrage**, drei Experimente (**🔬**), **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
Vorgänger ist [rauschen-kooperation-demo](https://sebastianhanisch-rauschen-kooperation-demo.streamlit.app/): dort ging es um Fehler zwischen zwei festen Partnern, hier
um Populationen.
"""
)

with st.expander("So funktioniert evolutionäre Dynamik", expanded=True):
    st.markdown(
        """
1. **Auszahlungsmatrix.** Für jedes Paar von Strategien steht fest, was die erste im Mittel je Runde gegen die zweite bekommt (aus dem Schatten der Zukunft δ,
   exakt gerechnet wie in [tit-for-tat-demo](https://sebastianhanisch-tit-for-tat-demo.streamlit.app/)).
2. **Replikatordynamik.** Der Anteil einer Strategie wächst, wenn sie im Moment mehr verdient als der Durchschnitt der Population, und schrumpft sonst.
3. **Evolutionäre Stabilität.** Eine Strategie ist stabil, wenn ein kleiner Anteil beliebiger Eindringlinge sie nie verdrängt. Bei **Gleichstand** (der
   Eindringling verdient gegen sie genau so viel wie sie selbst) entscheidet, wer gegen den Eindringling besser ist: ist sie es nicht, kann er sich
   ausbreiten.
        """
    )

with st.expander("Die sechs Strategien: wer macht was?", expanded=True):
    st.markdown(
        "Jede Strategie entscheidet jede Woche, ob sie **kooperiert (C)** oder **defektiert (D)**, und kennt dafür, was bisher passiert ist. Die beiden rechten "
        "Spalten zeigen, was die Strategie in den ersten zwölf Wochen **selbst tut**, wenn der Gegner immer defektiert beziehungsweise abwechselnd defektiert "
        "und kooperiert (D, C, D, C, …)."
    )
    rows_md = ["| Strategie | Verhalten | Gegen Immer-D | Gegen Abwechsler |", "|---|---|---|---|"]
    for r in _overview():
        rows_md.append(f"| **{r['label']}** | {r['description']} | `{r['vs_alld']}` | `{r['vs_alt']}` |")
    st.markdown("\n".join(rows_md))

st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
cols = st.columns(3)
for i, name in enumerate(C.PRESETS):
    with cols[i % 3]:
        st.button(name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP.get(name, ""), key=f"preset_{name}")

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    st.markdown("**Population**")
    field = st.multiselect("Strategien in der Population", C.STRATEGY_KEYS, key="field_select", format_func=label,
                           help="Wer in der Population vorkommt. Mindestens zwei. Anfangs sind alle gleich stark vertreten, außer Immer-Defektieren.")
    delta = st.slider("Schatten der Zukunft δ", *bounds("delta_slider"), step=C.DELTA_STEP, key="delta_slider",
                      help="Wahrscheinlichkeit, dass eine Beziehung eine Runde weiterläuft. Erwartete Dauer: 1 / (1 − δ) Runden.")
    alld = st.slider("Anfangsanteil Immer-Defektieren", *bounds("alld_slider"), step=C.ALLD_STEP, key="alld_slider",
                     help="Der Rest verteilt sich gleichmäßig auf die übrigen Strategien. Wirkt nur, wenn Immer-Defektieren in der Population ist.")
    st.markdown("**Kleine Population (Experimente 2 und 3)**")
    n_pop = st.slider("Populationsgröße N", *bounds("n_slider"), step=C.N_STEP, key="n_slider", help="Zahl der Spediteure.")
    w = st.slider("Selektionsstärke w", *bounds("w_slider"), step=C.W_STEP, key="w_slider",
                  help="0 = reiner Zufall, 1 = Fitness gleich Auszahlung. Fitness = 1 − w + w · Auszahlung.")
    mu = st.slider("Mutationsrate μ (Experiment 3)", *bounds("mu_slider"), step=C.MU_STEP, key="mu_slider", format="%.4f",
                   help="Wahrscheinlichkeit, dass ein Neugeborener eine zufällige Strategie wählt statt der des Vorbilds.")
    steps = st.slider("Schritte (Experiment 3)", *bounds("steps_slider"), step=C.STEPS_STEP, key="steps_slider",
                      help="Zahl der Geburts- und Todesereignisse im Moran-Lauf.")
    seed = st.number_input("Zufalls-Seed des Moran-Laufs", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neuen Lauf würfeln", width="stretch", on_click=randomize_seed)

field = tuple(k for k in C.STRATEGY_KEYS if k in field)
sync_query_params({"field_select": list(field), "delta_slider": round(float(delta), 2), "alld_slider": round(float(alld), 2), "n_slider": int(n_pop),
                   "w_slider": round(float(w), 2), "mu_slider": round(float(mu), 4), "steps_slider": int(steps), "seed_input": int(seed)})

if len(field) < 2:
    st.warning("Eine Population braucht mindestens zwei Strategien. Bitte in der Seitenleiste mindestens zwei wählen.")
    st.stop()

settings = Settings(field, round(float(delta), 2), round(float(alld), 2), int(n_pop), round(float(w), 2))
an = _analysis(settings)
labels = {k: label(k) for k in an.keys}

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎬 Replikatordynamik: Anteile über die Zeit")
m1, m2, m3 = st.columns(3)
winner_text = ", ".join(labels[k] for k in an.winners) if an.winners else "keine"
m1.metric("Setzen sich durch (Endanteil über 5 %)", f"{len(an.winners)} Strategien", delta=winner_text, delta_color="off")
if an.alld_wins is None:
    m2.metric("Immer-Defektieren", "nicht dabei")
else:
    m2.metric("Immer-Defektieren am Ende", f"{fmt(an.final[an.keys.index('ALLD')] * 100, 0)} %", delta="setzt sich durch" if an.alld_wins else "stirbt aus", delta_color="off")
m3.metric("Erwartete Beziehungsdauer", f"{fmt(1 / (1 - settings.delta), 1)} Runden", delta="1 / (1 − δ)", delta_color="off")
st.plotly_chart(build_shares(an.times, an.shares, an.keys, labels, "Zeit (Replikatordynamik)"), width="stretch", key="shares_chart")
st.caption("Gestapelt: der Anteil jeder Strategie an der Population über die Zeit. Ausgangspunkt: gleiche Anteile, außer Immer-Defektieren (Regler).")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Ist Tit-for-Tat evolutionär stabil?")
level, sentence = E.verdict_tft(an)
{"success": st.success, "warning": st.warning, "info": st.info}[level](sentence)

rows = ["| Strategie | Gleichgewicht? | evolutionär stabil? | wird verdrängt von | neutrale Eindringlinge |", "|---|---|---|---|---|"]
for r in E.class_rows(an):
    rows.append(f"| **{r['label']}** | {'ja' if r['nash'] else 'nein'} | {'ja' if r['ess'] else 'nein'} | {', '.join(r['strict']) or '–'} | {', '.join(r['neutral']) or '–'} |")
st.markdown("\n".join(rows))
st.caption("„Gleichgewicht“ gilt hier gegen die gewählten Strategien der Population, nicht gegen alle denkbaren (dafür siehe tit-for-tat-demo).")
st.plotly_chart(build_ess_map(_ess_map(an.keys), labels), width="stretch", key="ess_chart")
st.caption("Über den Schatten der Zukunft δ: hell = wird verdrängt, mittel = Gleichgewicht, aber ein neutraler Eindringling kann sich ausbreiten, dunkel = evolutionär stabil.")
st.markdown("---")

# --- Experiment 1 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment: Von welchem Anfangsanteil an setzen sich die Defektierer durch?")
basin = _basin(an.keys)
if basin is None:
    st.info("Dafür muss Immer-Defektieren in der Population sein.")
else:
    st.caption("Replikatordynamik für jede Kombination aus δ und Anfangsanteil von Immer-Defektieren (die übrigen Strategien gleich verteilt): Endanteil von Immer-Defektieren.")
    st.plotly_chart(build_basin(basin), width="stretch", key="basin_chart")
    th = dict(zip(basin["deltas"], basin["threshold"]))
    near = min(basin["deltas"], key=lambda d: abs(d - settings.delta))
    t_here = th[near]
    if t_here is None:
        st.info(f"Bei δ ≈ {fmt(near)} setzt sich Immer-Defektieren in keinem der gezeigten Anfangsanteile (bis {fmt(max(basin['shares']) * 100, 0)} %) durch.")
    else:
        st.info(f"Bei δ ≈ {fmt(near)} reicht ein Anfangsanteil von etwa {fmt(t_here * 100, 0)} % für Immer-Defektieren, um die Population zu übernehmen. "
                "Je länger die Beziehungen laufen, desto höher liegt die Grenze, bis sie aus dem gezeigten Bereich verschwindet.")
st.markdown("---")

# --- Experiment 2 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment: Wer erobert eine Population, wenn ein einzelner Mutant auftaucht?")
st.caption(f"Moran-Prozess, N = {settings.n_pop}, Selektionsstärke w = {fmt(settings.w)}: Wahrscheinlichkeit ρ, dass ein einzelner Mutant (Zeile) eine Population aus der Spalte übernimmt. "
           f"Neutral wäre ρ = 1/N = {fmt(1 / settings.n_pop, 3)}; ρ·N über 1 heißt begünstigt, darunter benachteiligt.")
rho = _fixation(settings)
st.plotly_chart(build_fixation(rho, an.keys, labels, settings.n_pop), width="stretch", key="fixation_chart")
if "TFT" in an.keys:
    ti = an.keys.index("TFT")
    neutral_pairs = [labels[k] for j, k in enumerate(an.keys) if j != ti and abs(rho[j, ti] - 1 / settings.n_pop) < 1e-6]
    if neutral_pairs:
        st.info(f"In eine reine Tit-for-Tat-Population kommen {', '.join(neutral_pairs)} mit genau ρ = 1/N = {fmt(1 / settings.n_pop, 3)}: "
                "weder begünstigt noch benachteiligt, ihr Anteil driftet also zufällig.")
    if "ALLD" in an.keys:
        ai = an.keys.index("ALLD")
        st.warning(f"Ein einzelner Defektierer erobert eine Tit-for-Tat-Population mit ρ = {fmt(rho[ai, ti], 4)}, eine Population aus Immer-Kooperieren mit "
                   f"{fmt(rho[ai, an.keys.index('ALLC')], 3) if 'ALLC' in an.keys else '–'}"
                   + (f", eine aus Pavlov mit {fmt(rho[ai, an.keys.index('PAVLOV')], 3)}." if "PAVLOV" in an.keys else "."))
st.markdown("---")

# --- Experiment 3 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment: Driftet eine Tit-for-Tat-Population in den Einbruch?")
st.caption(f"Ein Moran-Lauf mit Mutation (μ = {fmt(float(mu), 4)}), gestartet in einer reinen Tit-for-Tat-Population, {int(steps)} Schritte, N = {settings.n_pop}.")
with st.spinner("Moran-Lauf ..."):
    run = _drift(settings, round(float(mu), 4), int(steps), int(seed))
share = run["share"]
stride = max(1, len(share) // 800)
st.plotly_chart(build_shares(list(range(0, len(share), stride)), share[::stride], run["keys"], labels, "Schritt (Geburten und Todesfälle)"),
                width="stretch", key="drift_chart")
if "alld_majority_time" in run:
    st.warning(
        f"In diesem Lauf hat Immer-Defektieren {fmt(run['alld_majority_time'] * 100, 0)} % der Zeit die Mehrheit; die Population ist {run['breakdowns']}-mal in eine "
        "Defektierer-Mehrheit gekippt (ein Einbruch zählt von über 50 % bis unter 20 %). Ein einzelner Lauf zeigt, dass es vorkommt, nicht wie oft: Bei δ = 0,80 "
        "sind es mit N = 20 und μ = 0,002 über 60000 Schritte 3 von 6 Läufen mit mindestens einem Einbruch, mit N = 50 und μ = 0,01 über 6000 Schritte 5 von 20."
    )
st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Genau diese sechs Strategien** | „Gleichgewicht“ und „evolutionär stabil“ gelten nur gegen die gewählte Menge. Gegen alle denkbaren Strategien ist Tit-for-Tat erst ab δ = 2/3 ein Gleichgewicht, hier zeigt es sich schon früher. | `tit-for-tat-demo` rechnet gegen alle Strategien |
| **Kein Rauschen** | Fehler ändern die Auszahlungsmatrix und damit die Stabilität. | `rauschen-kooperation-demo` |
| **Paarweise Begegnungen, gut durchmischt** | Netzwerke, Orte und Wiederbegegnungen mit wenigen Partnern ändern, wer sich ausbreitet. | - |
| **Imitation nach Erfolg** | Andere Lernregeln (Bestantwort, Lernen aus Erfahrung) führen zu anderen Dynamiken. | `noregret-demo` |
| **„Evolutionär stabil“ im strengen Sinn** | Das ist ein sehr starker Begriff (kein Gleichstand darf zugunsten des Eindringlings ausgehen). Mit einem abgeschwächten Begriff oder mit Fehlern können Tit-for-Tat-artige Strategien stabil sein (Binmore und Samuelson 1992). | - |
| **Moran-Lauf: ein Lauf, ein Seed** | Der Einbruch ist ein Zufallsereignis; ein einzelner Lauf zeigt, dass er vorkommen kann, nicht wie oft. Die Zahlen im README stehen über sechs Läufe. | - |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Auszahlungsmatrix.** $M_{ij} = (1-\delta)\,V(i, j)$ mit dem diskontierten Wert $V$ aus dem linearen System über die gemeinsamen Automatenzustände.

**Replikatorgleichung.** Für die Anteile $x_i$: $\dot x_i = x_i\big((Mx)_i - x^\top M x\big)$. Gelöst mit dem Runge-Kutta-Verfahren 4. Ordnung (Schrittweite 0,05).

**Evolutionär stabile Strategie (Maynard Smith/Price 1973).** $i$ ist ESS, wenn für jedes $j \neq i$ gilt: $M_{ii} > M_{ji}$, oder $M_{ii} = M_{ji}$ und
$M_{ij} > M_{jj}$. Ein $j$ mit $M_{ji} = M_{ii}$ und $M_{ij} \le M_{jj}$ ist ein **neutraler Eindringling**: er verdrängt $i$ nicht, kann sich aber
ohne Nachteil ausbreiten. Das trifft für Tit-for-Tat zu: Immer-Kooperieren, Grim Trigger, Tit-for-Two-Tats und Pavlov verdienen gegen Tit-for-Tat und gegen
sich selbst genau 3,00, wie Tit-for-Tat gegen sie.

**Moran-Prozess.** Population der Größe $N$, Fitness $1 - w + w\,\pi$ mit der mittleren Auszahlung $\pi$ gegen die übrigen $N-1$. Geburt proportional
zur Fitness, Tod gleichverteilt. Die Fixationswahrscheinlichkeit eines einzelnen Mutanten ist
$\rho = \Big(1 + \sum_{k=1}^{N-1} \prod_{j=1}^{k} \tfrac{T^-_j}{T^+_j}\Big)^{-1}$ mit $T^-_j/T^+_j = f_B(j)/f_A(j)$. Neutral gilt $\rho = 1/N$.

**Literatur.** Maynard Smith und Price (1973), *The logic of animal conflict*, Nature 246, 15–18 (evolutionär stabile Strategie); Taylor und Jonker
(1978), *Evolutionarily stable strategies and game dynamics*, Mathematical Biosciences (Replikatorgleichung; Band und Seiten nicht eindeutig bestätigt);
Boyd und Lorberbaum (1987), *No pure strategy is evolutionarily stable in the repeated Prisoner's Dilemma game*, Nature 327, 58–59 (nur die
Zusammenfassung gelesen); Binmore und Samuelson (1992), *Evolutionary stability in repeated games played by finite automata*, Journal of Economic
Theory 57, 278–305 (ein abgeschwächter Stabilitätsbegriff, unter dem Tit-for-Tat-artige Automaten bestehen können); Nowak, Sasaki, Taylor und
Fudenberg (2004), *Emergence of cooperation and evolutionary stability in finite populations*, Nature 428, 646–650 (Fixationswahrscheinlichkeit gegen
den neutralen Wert 1/N im Moran-Prozess). Der Begriff „evolutionär stabil“ ist streng; schwächere Begriffe oder Fehler ändern die Aussage (siehe Grenzen).
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
