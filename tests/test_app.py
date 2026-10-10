"""End-to-end Smoke-Test via Streamlits offiziellem AppTest-Framework: laedt app.py mit den
Standardeinstellungen, klickt jeden Preset-Button und faehrt jeden Slider an seine Grenzen und prueft, dass
kein Python-Fehler auftritt - insbesondere `streamlit.errors.StreamlitDuplicateElementId` (mehrere
st.plotly_chart-Aufrufe ohne eindeutiges key= koennen zufaellig identischen Inhalt rendern und kollidieren)
und `StreamlitAPIException` bei Slidern mit berechneten Grenzen (min == max)."""

import os

from streamlit.testing.v1 import AppTest

APP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
TIMEOUT = 180
AUTOPLAY_MARKER = "\u25b6"  # Auto-Play-Buttons (Animation mit sleep) im Smoke-Test auslassen


def _fresh_app() -> AppTest:
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    return at


def test_app_loads_without_exception():
    _fresh_app()


def test_every_button_click_does_not_raise():
    labels = [b.label for b in _fresh_app().button]
    assert labels, "keine Buttons gefunden"
    for index, label in enumerate(labels):
        if AUTOPLAY_MARKER in label:
            continue
        at = _fresh_app()
        at.button[index].click().run(timeout=TIMEOUT)
        assert not at.exception, (label, [str(e) for e in at.exception])


def test_every_slider_at_its_min_and_max_does_not_raise():
    labels = [s.label for s in _fresh_app().slider]
    assert labels, "keine Slider gefunden"
    for index, label in enumerate(labels):
        for edge in ("min", "max"):
            at = _fresh_app()
            slider = at.slider[index]
            value = slider.min if edge == "min" else slider.max
            if isinstance(slider.value, int):
                value = int(value)
            slider.set_value(value).run(timeout=TIMEOUT)
            assert not at.exception, (label, edge, [str(e) for e in at.exception])


def test_permalink_is_clamped_and_snapped():
    at = AppTest.from_file(APP_PATH)
    at.query_params["delta"] = "0.99"
    at.query_params["n"] = "7"
    at.query_params["field"] = "TFT,gibt-es-nicht,ALLD,ALLC"
    at.query_params["steps"] = "1"
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    assert at.session_state["delta_slider"] == 0.95
    assert at.session_state["n_slider"] == 10
    assert at.session_state["steps_slider"] == 5000
    assert at.session_state["field_select"] == ["ALLC", "ALLD", "TFT"]


def test_a_population_of_one_strategy_shows_a_warning_not_an_exception():
    at = AppTest.from_file(APP_PATH)
    at.query_params["field"] = "TFT,ALLD"
    at.run(timeout=TIMEOUT)
    at.multiselect[0].set_value(["TFT"]).run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    assert any("mindestens zwei" in w.value for w in at.warning)


def test_every_strategy_is_explained_on_the_page():
    from rpl_scenario import STRATEGIES
    at = _fresh_app()
    text = " ".join(m.value for m in at.markdown)
    for s in STRATEGIES.values():
        assert s.description in text, s.key


def test_the_headline_verdict_says_tft_is_not_stable():
    at = _fresh_app()
    assert any("nicht evolutionär stabil" in w.value for w in at.warning)
