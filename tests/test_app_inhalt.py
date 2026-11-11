"""Inhalt der App: Verdikt-Zeilen je Preset, Expander nach Titel (nie nach Index), Mathe-Blöcke, verbotene Wörter, Äquierfüllbarkeit der live gerechneten Zellen."""

import re
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import smb_constants as C

ROOT = Path(__file__).resolve().parent.parent
APP = str(ROOT / "app.py")


def _app() -> AppTest:
    at = AppTest.from_file(APP, default_timeout=300)
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _meldungen(at):
    return [m.value for art in (at.info, at.success, at.warning, at.error) for m in art]


def _expander(at, label):
    return next(e for e in at.expander if e.label == label)


def _preset(name):
    at = _app()
    at.sidebar.button(key=f"preset_{name}").click().run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def test_expander_reiter_und_ueberschriften_stehen_unter_ihrem_titel():
    at = _app()
    labels = [e.label for e in at.expander]
    assert "📐 Mathematische Formulierung" in labels and "So funktioniert das Brechen von Symmetrien" in labels
    assert any("🚧 Wo die Annahmen enden" in s.value for s in at.subheader)
    assert set(C.REITER_NAMEN) <= {t.label for t in at.tabs}              # die vier Reiter (dazu zwei Unterreiter im ersten)


def test_kernfrage_und_handbeispiel_beim_start():
    meldungen = _meldungen(_app())
    assert any(m.startswith("Schubfach, h = 3 bis 8: in 5 von 6 Aufgaben weniger Konflikte mit der Brechung (h = 8: 27 932 → 1).") for m in meldungen)
    assert any("Mit der Regel belegt sie 6 von 6 Variablen und endet in der leeren Klausel, ohne dass eine Entscheidung nötig ist." in m for m in meldungen)


def test_preset_wo_es_schadet_meldet_die_verschlechterung_im_standardlauf_und_die_zaehlung():
    meldungen = [m for m in _meldungen(_preset("Wo es schadet"))]
    zeile = next(m for m in meldungen if m.startswith("Verschlechterung"))
    assert "Schur mit 4 Mengen und den Zahlen 1 bis 43, 20 Löser-Zufalls-Seeds je Seite" in zeile
    assert "braucht 6 Konflikte ohne und 352 mit Wertevorrang" in zeile
    assert "Kontrolle mit 100 weiteren Seeds" in zeile
    assert any(m.startswith("Über alle 10 Zellen") for m in meldungen)


def test_preset_schur_14_zeigt_148_gegen_21():
    meldungen = _meldungen(_preset("Schur 14"))
    assert any("n = 14: 148 → 21 Konflikte (weniger, ×7,0)" in m for m in meldungen)


def test_preset_grenze_schur_44_zeigt_die_vorgerechneten_werte():
    at = _preset("Grenze Schur 44")
    assert any("n = 44: 108 775 → 3 844 Konflikte (weniger, ×28,3)" in m for m in _meldungen(at))
    assert any("Vorgerechnet (Vormessung, Python-CDCL, nicht live)" in m for m in _meldungen(at))
    metriken = {m.label: m.value for m in at.metric}
    assert metriken["Konflikte ohne Regel"] and metriken["Konflikte mit Wertevorrang"]


def test_handbeispiel_schubfach_h3_und_schur_n14_ohne_fehler():
    at = _app()
    at.slider(key="h_hand_slider").set_value(3).run()
    assert not at.exception
    assert any(m.startswith("Schubfach mit 4 Aufträgen auf 3 Rampen (") for m in _meldungen(at))
    at.slider(key="schur_hand_slider").set_value(14).run()
    assert not at.exception
    assert any("keine Lösung, weder ohne noch mit Wertevorrang" in m for m in _meldungen(at))


def test_live_laeufe_schubfach_stimmen_mit_den_vorgerechneten_ueberein():
    at = _app()
    at.slider(key="h_bis_slider").set_value(5).run()
    at.button(key="schubfach_rechnen").click().run()
    assert not at.exception
    assert any("stimmen mit den vorgerechneten überein" in c.value for c in at.caption)
    assert any(m.startswith("Ohne Brechung braucht der Löser für h = 3, 4, 5 Rampen 7 / 28 / 159 Konflikte.") and "Live gerechnet" in m for m in _meldungen(at))


def test_live_faerbung_gleiche_antworten_und_seeds():
    at = _app()
    at.select_slider(key="faerbung_n_select").set_value(60).run()
    at.number_input(key="seed_input").set_value(700).run()
    at.button(key="faerbung_rechnen").click().run()
    assert not at.exception, [str(e) for e in at.exception]
    assert any("Antworten aller Läufe gleich (Äquierfüllbarkeit): ja." in c.value for c in at.caption)
    assert any(m.startswith("Färbung mit n = 60 Aufträgen, 10 Graphen") for m in _meldungen(at))


def test_mathe_bloecke_je_gleichung_ein_dollar_block():
    """Je Display-Gleichung ein eigener $$-Block in eigener Zeile (sonst KaTeX-Fehler, nur im Browser sichtbar)."""
    text = "\n".join(m.value for m in _expander(_app(), "📐 Mathematische Formulierung").markdown)   # die Lesehilfe (Erklärseite) steht als erster Block
    zeilen = text.split("\n")
    blocks = [z for z in zeilen if "$$" in z]
    assert len(blocks) == 5                                                  # Schur-Aufgabe, Schubfach-Aufgabe, Wertevorrang, Lochvorrang, Bahnen
    for z in blocks:
        assert z.startswith("$$") and z.endswith("$$") and z.count("$$") == 2, z
    assert text.count("$$") % 2 == 0
    assert "| Symbol | Bedeutung |" in text


VERBOTEN = [r"\bträgt\b", r"\btragen\b", r"läuft lokal", r"\bSaatwert", r"\bPhase 0\b", r"\bStück\b", r"\bPreset", r"\bSchwanz\b"]


def test_verbotene_woerter_in_app_und_readme():
    quellen = {"app.py": (ROOT / "app.py").read_text(encoding="utf-8"), "README.md": (ROOT / "README.md").read_text(encoding="utf-8")}
    for datei, text in quellen.items():
        for muster in VERBOTEN:
            for treffer in re.finditer(muster, text):
                kontext = text[max(0, treffer.start() - 40): treffer.end() + 40].replace("\n", " ")
                if muster == r"\bStück\b" and datei == "README.md" and "Stück der **sat-constraint-programming**" in kontext + text[treffer.end(): treffer.end() + 40]:
                    continue                      # der Einleitungssatz aller Demos der Reihe („Stück der … Linie in der Konzepte-Reihe“)
                pytest.fail(f"{datei}: {muster!r} in „{kontext}“")


def test_zufalls_seed_schreibweise_und_keine_ascii_umlaute():
    text = (ROOT / "app.py").read_text(encoding="utf-8") + (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Zufalls-Seed" in text
    for falsch in ("Zufallsseed", "Zufalls Seed", "Auftraege", "Rueck", "Loeser-", "Erfuell", "unerfuell"):
        assert falsch not in text, falsch
