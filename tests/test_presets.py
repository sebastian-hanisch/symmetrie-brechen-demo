"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, Permalink-Begrenzung."""

import pytest

import smb_constants as C
import smb_presets as P


def test_every_preset_has_help_and_only_known_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) <= set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_regler_bounds():
    for name, preset in C.PRESETS.items():
        for key, wert in preset.items():
            spec = P.SETTING_SPECS[P.PRESET_KEYS[key]]
            if spec.options is not None:
                assert wert in spec.options, (name, key)
            else:
                assert spec.lo <= wert <= spec.hi, (name, key)


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_url_params_are_unique():
    params = [s.url_param for s in P.SETTING_SPECS.values()]
    assert len(params) == len(set(params))


def test_default_preset_equals_the_default_settings():
    """„Handbeispiel Schubfach“ sagt nur, was ohnehin Voreinstellung ist (Schubfach mit h = 2): beim Start ist genau dieses Preset hervorgehoben."""
    erstes = next(iter(C.PRESETS))
    assert erstes == "Handbeispiel Schubfach"
    for key, wert in C.PRESETS[erstes].items():
        assert P.SETTING_SPECS[P.PRESET_KEYS[key]].default == wert


def test_presets_unterscheiden_sich_in_mindestens_einem_regler():
    """Zustandslose Hervorhebung: zwei Presets mit denselben Reglerwerten würden beide hervorgehoben."""
    def werte(preset):
        return tuple(preset.get(key, P.SETTING_SPECS[state].default) for key, state in sorted(P.PRESET_KEYS.items()))
    alle = [werte(p) for p in C.PRESETS.values()]
    assert len(set(alle)) == len(alle)


def test_preset_inhalte_nennen_ihre_zahlen_wie_die_konstanten():
    assert C.PRESETS["Schur 14"]["schur3_n"] == 14 and C.PRESETS["Grenze Schur 44"]["schur4_n"] == 44
    assert C.PRESETS["Wo es schadet"]["schadet_n"] == C.SCHADET_N == 43 and C.PRESETS["Wo es schadet"]["seeds"] == 20
    assert C.PRESETS["Handbeispiel Schubfach"]["h_hand"] == 2


@pytest.mark.parametrize("name", list(P.SETTING_SPECS))
def test_defaults_liegen_in_ihren_grenzen(name):
    spec = P.SETTING_SPECS[name]
    if spec.options is not None:
        assert spec.default in spec.options
    elif spec.lo is not None:
        assert spec.lo <= spec.default <= spec.hi


def test_bereinige_begrenzt_und_verwirft():
    spec = P.SETTING_SPECS["h_bis_slider"]
    assert P._bereinige(spec, 99) == C.H_BIS_MAX and P._bereinige(spec, -3) == C.H_BIS_MIN
    options = P.SETTING_SPECS["schur4_select"]
    assert P._bereinige(options, 44) == 44 and P._bereinige(options, 50) is None
