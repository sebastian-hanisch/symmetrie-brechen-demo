"""Randfälle, an denen Kernroutinen erfahrungsgemäß brechen (DEMO-PLAYBOOK §12): k = 1, n = 1, h = 1, Budget erreicht, weniger benutzte Farben als k, leere Eingaben."""

import pytest

import smb_algorithm as A
import smb_evaluation as E
import smb_instanzen as I
import smb_symmetrie as SY
from conftest import schur_loesungen_rueckverfolgung


def test_schur_mit_einer_menge_nur_n_bis_1_erfuellbar():
    assert A.lauf(I.schur(1, 1)).antwort is True          # 1 + 1 = 2 gibt es erst ab n = 2
    assert A.lauf(I.schur(2, 1)).antwort is False         # 1 + 1 = 2 in einer Menge
    for n in (1, 2, 5):
        assert SY.wertevorrang_schur(n, 1) == []         # (k − 1)·n = 0 Klauseln: nichts zu brechen
        assert A.lauf(I.schur(n, 1), SY.REGEL_WERTEVORRANG).antwort is A.lauf(I.schur(n, 1)).antwort


def test_schur_n_gleich_1_drei_mengen_bahn_der_groesse_3():
    erg = SY.loesungen_und_bahnen(I.schur(1, 3), SY.REGEL_WERTEVORRANG)
    # drei Lösungen (die Zahl 1 in einer der drei Mengen), eine Bahn der Größe 3 (nur eine Farbe benutzt, nicht 3! = 6), eine Lösung mit Wertevorrang
    assert (erg["loesungen"], erg["bahnen"], erg["bahngroessen"], erg["mit_brechung"]) == (3, 1, [3], 1)
    kind, text = E.verdict_hand_schur(1, 3, erg, len(SY.wertevorrang_schur(1, 3)))
    assert "Die Bahnen haben die Größen 3" in text and "/ 6" not in text        # der Text rechnet nicht mit k! = 6, wenn die Bahnen kleiner sind


def test_schubfach_h1_hat_keine_klauseln_der_regel():
    inst = SY.schubfach(1)                                  # 2 Aufträge auf 1 Rampe
    assert SY.lochvorrang(1) == []                          # (h − 1)·(h + 1) = 0
    assert A.lauf(inst).antwort is False and A.lauf(inst, SY.REGEL_LOCHVORRANG).antwort is False
    assert A.lauf(inst).stat["konflikte"] == A.lauf(inst, SY.REGEL_LOCHVORRANG).stat["konflikte"]
    assert A.lauf(SY.schubfach(1, 1)).antwort is True


def test_budget_erreicht_heisst_unbekannt_nie_unerfuellbar():
    inst = I.pigeonhole(7)
    erg = A.lauf(inst, None, budget=50)
    assert erg.antwort is None and erg.stat["konflikte"] == 50
    assert A.messung(erg).antwort_text == "Abbruch am Budget"
    # mit Lochvorrang endet die Einheitspropagation auf Stufe 0 in der leeren Klausel: ein Konflikt, keine Entscheidung
    mit = A.lauf(inst, SY.REGEL_LOCHVORRANG, budget=100)
    assert mit.antwort is False and mit.stat["konflikte"] == 1


def test_weniger_benutzte_farben_als_k():
    # Schur n = 3 mit 4 Mengen: jede Lösung benutzt höchstens 3 Farben, der Wertevorrang bleibt erfüllbar (Farben 0, 1, 2 in dieser Reihenfolge)
    inst = I.schur(3, 4)
    erg = A.lauf(inst, SY.REGEL_WERTEVORRANG)
    assert erg.antwort is True
    f = SY.farben_je_zahl(tuple(erg.modell[v] for v in range(1, inst.n + 1)), 4)
    assert max(f) <= 2 and f[0] == 0
    z = SY.loesungen_und_bahnen(inst, SY.REGEL_WERTEVORRANG)
    # m benutzte Farben von k = 4: Bahn der Größe 4!/(4 − m)!: m = 2 gibt 12, m = 3 gibt 24 (n = 3: 1 + 1 = 2 zwingt zwei Farben, mehr als drei braucht man nicht)
    benutzt = {len(set(f)) for f in schur_loesungen_rueckverfolgung(3, 4)}
    assert benutzt == {2, 3} and z["bahngroessen"] == [12, 24]
    assert z["loesungen"] != 24 * z["mit_brechung"]                    # „Lösungen / k!“ gilt nur, wenn jede Lösung mindestens k − 1 Farben benutzt


def test_faerbung_ohne_kanten_und_mit_einer_farbe():
    leer = I.faerbung(5, [], 3)
    assert SY.kante_fest([], 3) == []
    assert A.lauf(leer, SY.REGEL_KANTE_FEST).antwort is True and A.lauf(SY.mit_brechung(leer, SY.REGEL_KANTE_FEST)).antwort is True
    eine = I.faerbung(2, [(0, 1)], 1)
    assert A.lauf(eine).antwort is False and SY.kante_fest([(0, 1)], 1) == []
    assert A.lauf(I.faerbung(3, [(0, 1), (1, 2), (0, 2)], 3), SY.REGEL_WERTEVORRANG).antwort is True      # Dreieck: 3 Farben genügen genau


def test_dreieck_mit_zwei_farben_unerfuellbar_auch_mit_den_regeln():
    dreieck = I.faerbung(3, [(0, 1), (1, 2), (0, 2)], 2)
    for regel in (None, SY.REGEL_KANTE_FEST, SY.REGEL_WERTEVORRANG):
        assert A.lauf(dreieck, regel).antwort is False


def test_zaehlung_ohne_klauseln_und_leere_formel():
    assert SY.zaehle_loesungen(3, []) == (8, [], False)             # keine Klausel: 2^3 Modelle, alle frei
    assert SY.zaehle_loesungen(2, [()])[0] == 0                    # leere Klausel: kein Modell
    anzahl, _, abgebrochen = SY.zaehle_loesungen(10, [], grenze=5)
    assert anzahl == 5 and abgebrochen is True


def test_einheitspropagation_leere_klausel_am_anfang_und_ohne_klauseln():
    assert SY.einheitspropagation(2, [()])["konflikt"] == 0
    r = SY.einheitspropagation(3, [])
    assert r["konflikt"] is None and r["wert"] == {} and r["schritte"] == []


def test_regel_passt_nicht_zur_aufgabenart():
    with pytest.raises(ValueError):
        SY.loesungen_und_bahnen(I.faerbung(3, [(0, 1)], 3))                 # Färbung hat kein „höchstens eine Farbe“: nicht zählbar
    with pytest.raises(ValueError):
        A.lauf(I.rand3(10, 20, 1), SY.REGEL_WERTEVORRANG)
