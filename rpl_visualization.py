"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import numpy as np
import plotly.graph_objects as go

import rpl_constants as C


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=380, legend=True):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=30, b=10), plot_bgcolor="rgba(0,0,0,0)", showlegend=legend,
                      legend=dict(orientation="h", y=-0.25))
    return lock_axes(fig)


def build_shares(times, shares, keys, labels, x_title="Zeit"):
    """Gestapelte Anteile über die Zeit (Replikatordynamik oder Moran-Lauf)."""
    arr = np.asarray(shares)
    fig = go.Figure()
    for idx, key in enumerate(keys):
        fig.add_trace(go.Scatter(x=list(times), y=arr[:, idx], mode="lines", name=labels[key], stackgroup="one",
                                 line=dict(width=0.5, color=C.COLORS[key]), fillcolor=C.COLORS[key],
                                 hovertemplate=labels[key] + ": %{y:.2f}<extra></extra>"))
    fig.update_xaxes(title_text=x_title)
    fig.update_yaxes(title_text="Anteil in der Population", range=[0, 1])
    return _base(fig, height=380)


def build_ess_map(emap, labels):
    """Je Strategie und δ: 0 = Eindringling setzt sich durch, 1 = Gleichgewicht (kein Eindringling gewinnt), 2 = evolutionär stabil."""
    keys = list(emap["nash"])
    z, text = [], []
    for k in keys:
        row, trow = [], []
        for nash, ess in zip(emap["nash"][k], emap["ess"][k]):
            row.append(2 if ess else (1 if nash else 0))
            trow.append("evolutionär stabil" if ess else ("Gleichgewicht, aber nicht stabil" if nash else "wird verdrängt"))
        z.append(row)
        text.append(trow)
    fig = go.Figure(go.Heatmap(z=z, x=[f"{d:.2f}".replace(".", ",") for d in emap["deltas"]], y=[labels[k] for k in keys], text=text, zmin=0, zmax=2,
                               colorscale=[[0, "#E9D5D0"], [0.5, "#c9d9d6"], [1, C.COLORS["TFT"]]], xgap=2, ygap=2, showscale=False,
                               hovertemplate="%{y}, δ = %{x}: %{text}<extra></extra>"))
    fig.update_yaxes(autorange="reversed", type="category")
    fig.update_xaxes(title_text="Diskontfaktor δ", type="category")
    return _base(fig, height=330, legend=False)


def build_basin(b):
    """Endanteil von Immer-Defektieren je Beziehungsdauer δ (Zeilen) und Anfangsanteil (Spalten)."""
    z = b["final"]
    fig = go.Figure(go.Heatmap(z=z, x=[f"{s * 100:.0f}" for s in b["shares"]], y=[f"{d:.2f}".replace(".", ",") for d in b["deltas"]],
                               zmin=0, zmax=1, colorscale=[[0, C.COLORS["TFT"]], [0.5, "#f3eadc"], [1, C.COLORS["ALLD"]]], xgap=1, ygap=1,
                               colorbar=dict(title="Endanteil<br>Immer-Defektieren"),
                               hovertemplate="δ = %{y}, Anfangsanteil %{x} %: Endanteil %{z:.2f}<extra></extra>"))
    fig.update_xaxes(title_text="Anfangsanteil von Immer-Defektieren (%)", type="category", dtick=5)
    fig.update_yaxes(title_text="Diskontfaktor δ", type="category", autorange="reversed")
    return _base(fig, height=420, legend=False)


def build_fixation(rho, keys, labels, n_pop):
    """ρ·N: 1 = neutral (so wahrscheinlich wie Zufall), darüber begünstigt, darunter benachteiligt. Zeile erobert Spalte."""
    names = [labels[k] for k in keys]
    rel = rho * n_pop
    fig = go.Figure(go.Heatmap(z=rel, x=names, y=names, zmin=0, zmax=3, zmid=1, colorscale="RdBu_r", xgap=1, ygap=1, showscale=True,
                               colorbar=dict(title="ρ · N"),
                               text=[[f"{v:.3f}".replace(".", ",") for v in row] for row in rho], texttemplate="%{text}",
                               hovertemplate="Ein %{y} erobert eine Population aus %{x}: ρ = %{text}<extra></extra>"))
    fig.update_yaxes(autorange="reversed", type="category", title_text="Mutant (einzeln)")
    fig.update_xaxes(type="category", title_text="Bestehende Population")
    return _base(fig, height=420, legend=False)
