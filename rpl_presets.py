"""Permalink (Begrenzen und Einrasten), Presets und Zufalls-Seed-Button."""

import random
from dataclasses import dataclass

import streamlit as st

import rpl_constants as C


@dataclass(frozen=True)
class SettingSpec:
    url_param: str
    caster: type
    default: object
    lo: float | None = None
    hi: float | None = None


SETTING_SPECS = {
    "field_select": SettingSpec("field", str, ",".join(C.DEFAULT_FIELD)),
    "delta_slider": SettingSpec("delta", float, C.DEFAULT_DELTA, C.DELTA_MIN, C.DELTA_MAX),
    "alld_slider": SettingSpec("alld", float, C.DEFAULT_ALLD, C.ALLD_MIN, C.ALLD_MAX),
    "n_slider": SettingSpec("n", int, C.DEFAULT_N, C.N_MIN, C.N_MAX),
    "w_slider": SettingSpec("w", float, C.DEFAULT_W, C.W_MIN, C.W_MAX),
    "mu_slider": SettingSpec("mu", float, C.DEFAULT_MU, C.MU_MIN, C.MU_MAX),
    "steps_slider": SettingSpec("steps", int, C.DEFAULT_STEPS, C.STEPS_MIN, C.STEPS_MAX),
    "seed_input": SettingSpec("seed", int, C.DEFAULT_SEED, 0, C.SEED_MAX),
}
PRESET_KEYS = {"field": "field_select", "delta": "delta_slider", "alld": "alld_slider", "n": "n_slider", "w": "w_slider"}


def parse_field(text: str) -> list[str]:
    """Aus der Adresszeile: gültige Strategienamen in der Reihenfolge von STRATEGY_KEYS; unbekannte fallen weg, zu wenige -> alle sechs."""
    wanted = {t.strip() for t in str(text).split(",") if t.strip()}
    keys = [k for k in C.STRATEGY_KEYS if k in wanted]
    return keys if len(keys) >= 2 else list(C.DEFAULT_FIELD)


def init_session_state_defaults():
    for state_key, spec in SETTING_SPECS.items():
        if state_key not in st.session_state:
            st.session_state[state_key] = parse_field(spec.default) if state_key == "field_select" else spec.default


def bounds(state_key):
    spec = SETTING_SPECS[state_key]
    return spec.lo, spec.hi


def clamp(spec: SettingSpec, value):
    if spec.lo is not None:
        value = max(spec.lo, value)
    if spec.hi is not None:
        value = min(spec.hi, value)
    return value


def load_permalink_settings():
    """Einmal je Sitzung: Werte aus der Adresszeile übernehmen, begrenzt bzw. auf gültige Strategien eingerastet."""
    if "permalink_loaded" in st.session_state:
        return
    qp = st.query_params
    for state_key, spec in SETTING_SPECS.items():
        if spec.url_param not in qp:
            continue
        raw = qp[spec.url_param]
        if isinstance(raw, list):
            raw = raw[0] if raw else ""
        if state_key == "field_select":
            st.session_state[state_key] = parse_field(raw)
            continue
        try:
            value = spec.caster(raw)
        except (ValueError, TypeError):
            continue
        st.session_state[state_key] = clamp(spec, value)
    st.session_state["permalink_loaded"] = True


def sync_query_params(values):
    try:
        for state_key, value in values.items():
            st.query_params[SETTING_SPECS[state_key].url_param] = ",".join(value) if state_key == "field_select" else str(value)
    except Exception:
        pass


def apply_preset(name):
    for key, state_key in PRESET_KEYS.items():
        if key in C.PRESETS[name]:
            value = C.PRESETS[name][key]
            st.session_state[state_key] = list(value) if key == "field" else value


def randomize_seed():
    st.session_state["seed_input"] = random.randint(0, C.SEED_MAX)
