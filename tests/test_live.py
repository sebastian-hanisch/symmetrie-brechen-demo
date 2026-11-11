"""Live-Knöpfe: Zwischenspeicher und Fortschrittsanzeige (smb_live.py). Der Zwischenspeicher ändert keine Zahl: gespeichert gleich ungespeichert (bitgleich),
ein anderer Parameter kommt nie aus dem Speicher, ein zweiter Aufruf mit denselben Parametern rechnet nicht noch einmal."""

import smb_algorithm as A
import smb_constants as C
import smb_evaluation as E
import smb_instanzen as I
import smb_live as L
import smb_symmetrie as SY
from streamlit.testing.v1 import AppTest

BUDGET = 2000


def _zaehler(monkeypatch):
    aufrufe = []
    echt = A.lauf

    def zaehlend(inst, regel=None, **kwargs):
        aufrufe.append((regel, kwargs.get("seed", 0)))
        return echt(inst, regel, **kwargs)

    monkeypatch.setattr(A, "lauf", zaehlend)
    return aufrufe


def _alte_schubfach_zeilen(h_bis, budget):
    """Die Zeilen so, wie sie vor dem Zwischenspeicher gerechnet wurden (unabhängige Abschrift der früheren Fassung)."""
    zeilen = []
    for h in range(C.H_REIHE_MIN, h_bis + 1):
        inst = SY.schubfach(h)
        ohne, mit = A.messung(A.lauf(inst, None, budget=budget)), A.messung(A.lauf(inst, SY.REGEL_LOCHVORRANG, budget=budget))
        zeilen.append(E.zeile_aus({"antwort": ohne.antwort_text, "konflikte": ohne.konflikte}, {"antwort": mit.antwort_text, "konflikte": mit.konflikte}, h=h))
    return zeilen


def test_schubfach_gespeichert_gleich_ungespeichert_und_gleich_alter_fassung():
    L.schubfach_einheit.clear()
    alt = _alte_schubfach_zeilen(5, BUDGET)
    assert [L.schubfach_einheit_ungespeichert(h, BUDGET)[0] for h in range(C.H_REIHE_MIN, 6)] == alt
    erster, _ = L.schubfach_aus_speicher(5, BUDGET)
    zweiter, sek = L.schubfach_aus_speicher(5, BUDGET)
    assert erster == alt and zweiter == alt and sek >= 0


def test_schubfach_zweiter_aufruf_rechnet_nicht_anderer_parameter_schon(monkeypatch):
    L.schubfach_einheit.clear()
    aufrufe = _zaehler(monkeypatch)
    L.schubfach_einheit(3, BUDGET)
    L.schubfach_einheit(3, BUDGET)
    assert len(aufrufe) == 2                       # ohne und mit Regel, einmal
    z4 = L.schubfach_einheit(4, BUDGET)            # anderes h
    zb = L.schubfach_einheit(3, BUDGET + 1)        # anderes Budget
    assert len(aufrufe) == 6
    assert z4[0] == L.schubfach_einheit_ungespeichert(4, BUDGET)[0] and zb[0] == L.schubfach_einheit_ungespeichert(3, BUDGET + 1)[0]


def test_seeds_gespeichert_gleich_konflikte_je_seed():
    L.seed_einheit.clear()
    n, seeds = 38, 3
    inst = I.schur(n, C.SCHADET_K)
    ref_ohne = A.konflikte_je_seed(inst, None, range(1, seeds + 1), BUDGET)
    ref_mit = A.konflikte_je_seed(inst, SY.REGEL_WERTEVORRANG, range(1, seeds + 1), BUDGET)
    for _ in range(2):                                           # zweiter Durchlauf aus dem Speicher
        out, sek = L.schadet_aus_speicher(n, seeds, BUDGET)
        assert sek >= 0
        for name, ref in (("ohne", ref_ohne), ("mit", ref_mit)):
            assert out[name] == {"konflikte": ref[0], "abbrueche": ref[2], "antworten": sorted(str(a) for a in ref[1])}


def test_seed_einheit_anderer_parameter_kommt_nicht_aus_dem_speicher(monkeypatch):
    L.seed_einheit.clear()
    aufrufe = _zaehler(monkeypatch)
    L.seed_einheit(38, False, 1, BUDGET)
    L.seed_einheit(38, False, 1, BUDGET)
    assert aufrufe == [(None, 1)]
    a = L.seed_einheit(38, False, 2, BUDGET)       # anderer Löser-Zufalls-Seed
    b = L.seed_einheit(38, True, 1, BUDGET)        # mit Regel
    c = L.seed_einheit(40, False, 1, BUDGET)       # andere Aufgabe
    assert len(aufrufe) == 4
    assert a[:2] == L.seed_einheit_ungespeichert(38, False, 2, BUDGET)[:2] and b[:2] == L.seed_einheit_ungespeichert(38, True, 1, BUDGET)[:2]
    assert c[:2] == L.seed_einheit_ungespeichert(40, False, 1, BUDGET)[:2]


def test_fortschrittsanzeige_liefert_ergebnisse_in_reihenfolge_und_ohne_fehler():
    def skript():
        import streamlit as st
        import smb_live as L

        erg = L.mit_fortschritt("Probe", [("eins", (1,)), ("zwei", (2,)), ("drei", (3,))], lambda x: x * 10)
        st.write(f"ergebnis {erg}")

    at = AppTest.from_function(skript)
    at.run(timeout=60)
    assert not at.exception, [str(e) for e in at.exception]
    assert any("ergebnis [10, 20, 30]" in m.value for m in at.markdown)
