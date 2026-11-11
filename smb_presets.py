"""Permalink (Begrenzen), Presets und Zufalls-Seed-Button (Standardmuster aus dem Demo-Portfolio)."""

import time
from dataclasses import dataclass

import streamlit as st

import smb_constants as C
from smb_rng import SplitMix64


@dataclass(frozen=True)
class SettingSpec:
    url_param: str
    caster: type
    default: object
    lo: float | None = None
    hi: float | None = None
    options: tuple | None = None


SETTING_SPECS = {
    "h_hand_slider": SettingSpec("hh", int, C.DEFAULT_H_HAND, C.H_HAND_MIN, C.H_HAND_MAX),
    "schur_hand_slider": SettingSpec("sh", int, C.DEFAULT_SCHUR_HAND, C.SCHUR_HAND_MIN, C.SCHUR_HAND_MAX),
    "h_bis_slider": SettingSpec("hb", int, C.DEFAULT_H_BIS, C.H_BIS_MIN, C.H_BIS_MAX),
    "schur3_select": SettingSpec("s3", int, C.DEFAULT_SCHUR3_N, options=C.SCHUR3_N),
    "schur4_select": SettingSpec("s4", int, C.DEFAULT_SCHUR4_N, options=C.SCHUR4_N),
    "schadet_n_select": SettingSpec("sn", int, C.DEFAULT_SCHADET_N, options=C.SCHADET_N_REIHE),
    "faerbung_n_select": SettingSpec("fn", int, C.DEFAULT_FAERBUNG_N, options=C.FAERBUNG_N),
    "seeds_slider": SettingSpec("seeds", int, C.DEFAULT_SEEDS, C.SEEDS_MIN, C.SEEDS_MAX),
    "seed_input": SettingSpec("seed", int, C.DEFAULT_SEED, 0, C.SEED_MAX),
    "budget_slider": SettingSpec("budget", int, C.DEFAULT_BUDGET, options=C.BUDGET_OPTIONEN),
}
PRESET_KEYS = {
    "h_hand": "h_hand_slider", "schur_hand": "schur_hand_slider", "h_bis": "h_bis_slider",
    "schur3_n": "schur3_select", "schur4_n": "schur4_select", "schadet_n": "schadet_n_select", "faerbung_n": "faerbung_n_select", "seeds": "seeds_slider", "seed": "seed_input", "budget": "budget_slider",
}


def init_session_state_defaults():
    for state_key, spec in SETTING_SPECS.items():
        if state_key not in st.session_state:
            st.session_state[state_key] = spec.default


def bounds(state_key):
    spec = SETTING_SPECS[state_key]
    return spec.lo, spec.hi


def _bereinige(spec, wert):
    """Wert aus der Adresszeile auf die Reglergrenzen begrenzen beziehungsweise auf erlaubte Optionen prüfen; None = verwerfen."""
    if spec.options is not None:
        return wert if wert in spec.options else None
    if spec.lo is not None:
        wert = max(spec.lo, wert)
    if spec.hi is not None:
        wert = min(spec.hi, wert)
    return wert


def load_permalink_settings():
    """Einmal je Sitzung: Werte aus der Adresszeile übernehmen, auf die Reglergrenzen begrenzt."""
    if "permalink_loaded" in st.session_state:
        return
    qp = st.query_params
    for state_key, spec in SETTING_SPECS.items():
        if spec.url_param in qp:
            try:
                wert = _bereinige(spec, spec.caster(qp[spec.url_param]))
            except (ValueError, TypeError):
                continue
            if wert is not None:
                st.session_state[state_key] = wert
    st.session_state["permalink_loaded"] = True


def sync_query_params(values):
    """`values`: {state_key: aktueller Wert}; die Adresszeile spiegelt die Konfiguration."""
    try:
        for state_key, value in values.items():
            st.query_params[SETTING_SPECS[state_key].url_param] = str(value)
    except Exception:
        pass


def apply_preset(name):
    """Ein Preset setzt alle Regler: was es nicht nennt, bekommt den Standardwert."""
    for key, state_key in PRESET_KEYS.items():
        st.session_state[state_key] = C.PRESETS[name].get(key, SETTING_SPECS[state_key].default)


def aktives_preset():
    """Name des Presets, dessen Werte GENAU den aktuellen Einstellungen entsprechen, sonst None.

    Zustandslos: verglichen wird jeder Regler aus SETTING_SPECS (ein Preset ohne Eintrag für einen Regler meint dessen
    Standardwert) mit dem Session State. Ein später ergänzter Regler braucht nur seinen Eintrag in SETTING_SPECS,
    dann hebt auch seine Änderung die Markierung auf (tests/test_layout.py prüft das für jeden Regler)."""
    preset_key_of = {state_key: key for key, state_key in PRESET_KEYS.items()}
    for name, preset in C.PRESETS.items():
        if all(
            st.session_state.get(state_key, spec.default) == preset.get(preset_key_of.get(state_key), spec.default)
            for state_key, spec in SETTING_SPECS.items()
        ):
            return name
    return None


def sidebar_presets():
    """Schnellstart oben in der Seitenleiste; das aktive Preset ist hervorgehoben (`type="primary"`)."""
    if not C.PRESETS:
        return
    st.header("🎯 Schnellstart")
    st.caption("Ein Beispielszenario laden:")
    aktiv = aktives_preset()
    for name in C.PRESETS:
        st.button(
            name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP.get(name, ""), key=f"preset_{name}",
            type="primary" if aktiv == name else "secondary",
        )


def randomize_seed():
    """Neuer Zufalls-Seed der Aufgabe; der Strom kommt aus dem SplitMix64 des Repos, gespeist von der Uhr."""
    st.session_state["seed_input"] = SplitMix64(time.time_ns()).below(C.SEED_MAX + 1)
