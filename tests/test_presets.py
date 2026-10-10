"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, Permalink-Begrenzen/Einrasten."""

import rpl_constants as C
import rpl_evaluation as ev
import rpl_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_slider_bounds():
    for name, preset in C.PRESETS.items():
        assert C.DELTA_MIN <= preset["delta"] <= C.DELTA_MAX, name
        assert C.ALLD_MIN <= preset["alld"] <= C.ALLD_MAX, name
        assert C.N_MIN <= preset["n"] <= C.N_MAX and C.W_MIN <= preset["w"] <= C.W_MAX, name
        assert len(preset["field"]) >= 2 and set(preset["field"]) <= set(C.STRATEGY_KEYS), name


def test_default_preset_equals_the_default_settings():
    first = next(iter(C.PRESETS.values()))
    s = ev.Settings(field=tuple(first["field"]), delta=first["delta"], alld=first["alld"], n_pop=first["n"], w=first["w"])
    assert s == ev.Settings()


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) <= set(P.SETTING_SPECS)


def test_parse_field_keeps_valid_names_in_order_and_falls_back():
    assert P.parse_field("GRIM,TFT") == ["TFT", "GRIM"]
    assert P.parse_field("TFT,gibt-es-nicht,ALLD") == ["ALLD", "TFT"]
    assert P.parse_field("TFT") == list(C.DEFAULT_FIELD)
    assert P.parse_field("") == list(C.DEFAULT_FIELD)


def test_clamp_limits_numbers():
    spec = P.SETTING_SPECS["delta_slider"]
    assert P.clamp(spec, 2.0) == C.DELTA_MAX and P.clamp(spec, 0.0) == C.DELTA_MIN


def test_presets_make_their_story_true():
    """Die Presets behaupten etwas über Gleichgewicht, Grenze und Drift; hier steht, dass es stimmt."""
    def run(name):
        p = C.PRESETS[name]
        return ev.analyse(ev.Settings(tuple(p["field"]), p["delta"], p["alld"], p["n"], p["w"]))

    assert run("Alle sechs, 10 % Immer-Defektieren (δ = 0,80)").alld_wins is False
    assert run("Kurzer Schatten (δ = 0,40)").alld_wins is True
    assert run("Knapp unter der Grenze (δ = 0,70, 30 %)").alld_wins is False
    assert run("Knapp über der Grenze (δ = 0,70, 40 %)").alld_wins is True
    small = run("Nur Tit-for-Tat, Immer-Kooperieren, Immer-Defektieren")
    tft = next(r for r in ev.class_rows(small) if r["key"] == "TFT")
    assert tft["neutral"] == ["Immer kooperieren"] and not tft["ess"]
    none = run("Ohne Immer-Defektieren")
    assert none.alld_wins is None and max(none.final) - min(none.final) < 1e-6
