"""Jede Zahl aus README und App wird hier über die echten Auswertungsfunktionen nachgerechnet (DEMO-PLAYBOOK §4)."""

import numpy as np
import pytest

import rpl_algorithm as A
import rpl_constants as C
import rpl_evaluation as E

KEYS = C.STRATEGY_KEYS
IDX = {k: i for i, k in enumerate(KEYS)}


def test_alld_is_the_only_ess_at_every_delta():
    emap = E.ess_map()
    for k in KEYS:
        if k == "ALLD":
            assert all(emap["ess"][k])
        else:
            assert not any(emap["ess"][k]), k


def test_tft_is_never_evolutionarily_stable_but_a_nash_equilibrium_from_delta_one_half():
    emap = E.ess_map()
    nash = dict(zip(emap["deltas"], emap["nash"]["TFT"]))
    assert not nash[0.45] and nash[0.5] and nash[0.8]


def test_neutral_invaders_of_tft_at_delta_0_8():
    an = E.analyse(E.Settings())
    row = next(r for r in E.class_rows(an) if r["key"] == "TFT")
    assert row["nash"] and not row["ess"] and row["strict"] == []
    assert sorted(row["neutral"]) == sorted(["Immer kooperieren", "Grim Trigger", "Tit-for-Two-Tats", "Pavlov (Win-Stay-Lose-Shift)"])
    assert E.verdict_tft(an)[0] == "warning" and "nicht evolutionär stabil" in E.verdict_tft(an)[1]


def test_tft_is_beaten_by_alld_at_a_short_shadow():
    an = E.analyse(E.Settings(delta=0.4))
    level, text = E.verdict_tft(an)
    assert level == "warning" and "verdrängt" in text


def test_replicator_end_state_at_delta_0_8_with_ten_percent_alld():
    an = E.analyse(E.Settings())
    final = dict(zip(an.keys, an.final))
    assert final["ALLD"] < 1e-3 and an.alld_wins is False
    assert final["ALLC"] == pytest.approx(0.148, abs=0.003)
    assert final["TFT"] == pytest.approx(0.227, abs=0.003) and final["GRIM"] == pytest.approx(0.227, abs=0.003)
    assert final["TF2T"] == pytest.approx(0.209, abs=0.003) and final["PAVLOV"] == pytest.approx(0.188, abs=0.003)
    assert len(an.winners) == 5


def test_a_short_shadow_ends_in_all_defect():
    an = E.analyse(E.Settings(delta=0.4))
    assert an.alld_wins is True and an.winners == ("ALLD",)


def test_basin_thresholds_by_delta():
    b = E.basin(deltas=[0.3, 0.6, 0.65, 0.7, 0.75, 0.8, 0.95], shares=[round(0.01 * i, 2) for i in range(0, 61)])
    th = dict(zip(b["deltas"], b["threshold"]))
    assert th[0.3] == pytest.approx(0.01, abs=0.011) and th[0.6] == pytest.approx(0.01, abs=0.011)
    assert th[0.65] == pytest.approx(0.04, abs=0.03)
    assert th[0.7] == pytest.approx(0.35, abs=0.011)
    assert th[0.75] == pytest.approx(0.55, abs=0.02)
    assert th[0.8] is None and th[0.95] is None


def test_the_two_threshold_presets_straddle_the_boundary():
    below = E.analyse(E.Settings(delta=0.70, alld=0.30))
    above = E.analyse(E.Settings(delta=0.70, alld=0.40))
    assert below.alld_wins is False and above.alld_wins is True


def test_no_alld_leaves_the_shares_unchanged():
    keys = ("ALLC", "TFT", "GRIM", "TF2T", "PAVLOV")
    an = E.analyse(E.Settings(field=keys, alld=0.0))
    assert an.alld_wins is None
    assert np.allclose(an.final, [0.2] * 5, atol=1e-6)


def test_fixation_probabilities_n_50_w_0_5_delta_0_8():
    rho = E.fixation(E.Settings())
    assert rho[IDX["ALLC"], IDX["TFT"]] == pytest.approx(0.02, abs=1e-9)
    assert rho[IDX["ALLD"], IDX["ALLC"]] == pytest.approx(0.3461, abs=0.0005)
    assert rho[IDX["ALLD"], IDX["PAVLOV"]] == pytest.approx(0.0882, abs=0.0005)
    assert rho[IDX["ALLD"], IDX["TFT"]] < 1e-4
    assert rho[IDX["TFT"], IDX["ALLD"]] == pytest.approx(0.0331, abs=0.0005)
    assert rho[IDX["ALLD"], IDX["TF2T"]] == pytest.approx(0.0040, abs=0.0005)
    for j in ("GRIM", "TF2T", "PAVLOV"):
        assert rho[IDX[j], IDX["TFT"]] == pytest.approx(0.02, abs=1e-9)


def test_drift_in_a_small_population_with_rare_mutation():
    """N = 20, μ = 0,002, δ = 0,80, w = 0,5, 60000 Schritte, Seeds 0 bis 5, Start reines Tit-for-Tat."""
    s = E.Settings(n_pop=20)
    runs = [E.drift(s, 0.002, 60000, seed) for seed in range(6)]
    alld = np.mean([r["mean"][IDX["ALLD"]] for r in runs])
    allc = np.mean([r["mean"][IDX["ALLC"]] for r in runs])
    episodes = [r["breakdowns"] for r in runs]
    time_major = np.mean([r["alld_majority_time"] for r in runs])
    assert alld == pytest.approx(0.070, abs=0.002) and allc == pytest.approx(0.015, abs=0.002)
    assert episodes == [2, 1, 0, 0, 0, 2]
    assert time_major == pytest.approx(0.070, abs=0.002)


def test_drift_in_a_larger_population_with_frequent_mutation():
    """N = 50, μ = 0,01, δ = 0,80, 6000 Schritte, Seeds 0 bis 19: auch hier kippt die Population, aber seltener und kürzer."""
    s = E.Settings(n_pop=50)
    runs = [E.drift(s, 0.01, 6000, seed) for seed in range(20)]
    assert sum(1 for r in runs if r["breakdowns"] > 0) == 5
    assert np.mean([r["alld_majority_time"] for r in runs]) == pytest.approx(0.066, abs=0.003)
    assert np.mean([r["mean"][IDX["TFT"]] for r in runs]) == pytest.approx(0.711, abs=0.005)


def test_count_episodes_uses_hysteresis():
    flicker = [0.1, 0.55, 0.45, 0.55, 0.45, 0.1, 0.6, 0.1]      # zweimal über 0,5 mit Flackern dazwischen, dann ein zweiter Einbruch
    assert E.count_episodes(flicker) == 2
    assert E.count_episodes([0.1, 0.3, 0.45, 0.3]) == 0
    assert E.count_episodes([0.9, 0.9, 0.9]) == 1


def test_strategy_overview_traces_by_hand():
    rows = {r["key"]: r for r in E.strategy_overview()}
    assert rows["TFT"]["vs_alld"] == "C D D D D D D D D D D D"
    assert rows["TFT"]["vs_alt"] == "C D C D C D C D C D C D"
    assert rows["GRIM"]["vs_alt"] == "C D D D D D D D D D D D"
    assert rows["TF2T"]["vs_alt"] == "C C C C C C C C C C C C"
    assert rows["PAVLOV"]["vs_alld"] == "C D C D C D C D C D C D"
    assert len(rows) == 6 and all(r["description"] for r in rows.values())
