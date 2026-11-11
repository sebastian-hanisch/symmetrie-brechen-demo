"""Handwerte der Brechungsregeln (Handbeispiel Stück 9: Schur mit 3 Mengen und Schubfach h = 2; `sat-cp-planung/handbeispiele/out_hb_09.txt`).

Jede Erwartung ist von Hand gerechnet (Kommentare), nicht aus dem Code übernommen."""

import itertools

import pytest

import smb_instanzen as I
import smb_symmetrie as SY
from conftest import wertevorrang_ok


# ---------------------------------------------------------------- Schubfach h = 2
def test_schubfach_h2_klauseln_von_hand(php2):
    # x(p, l) = 2p + l + 1: x00 = 1, x01 = 2, x10 = 3, x11 = 4, x20 = 5, x21 = 6
    assert php2.n == 6 and len(php2.klauseln) == 9 == 3 + 2 * 3
    assert php2.klauseln[:3] == [(1, 2), (3, 4), (5, 6)]
    assert (-1, -3) in php2.klauseln and (-2, -4) in php2.klauseln and (-4, -6) in php2.klauseln
    assert php2.klauseln == I.pigeonhole(2).klauseln          # derselbe Erzeuger wie im Kern, nur mit der Tauben-Zahl als Zusatz


def test_lochvorrang_h2_drei_klauseln_von_hand():
    # ¬x01; ¬x11 ∨ x00; ¬x21 ∨ x00 ∨ x10  (Handbeispiel)
    assert SY.lochvorrang(2) == [(-2,), (-4, 1), (-6, 1, 3)]
    assert len(SY.lochvorrang(2)) == (2 - 1) * (2 + 1)


def test_einheitspropagation_ohne_und_mit_lochvorrang(php2):
    ohne = SY.einheitspropagation(php2.n, php2.klauseln)
    assert ohne["konflikt"] is None and ohne["wert"] == {} and ohne["schritte"] == []          # keine Einheitsklausel: nichts folgt
    mit = SY.mit_brechung(php2, SY.REGEL_LOCHVORRANG)
    r = SY.einheitspropagation(mit.n, mit.klauseln)
    # von Hand: ¬x01 ⇒ x00 (Klausel x00 ∨ x01); Loch 0 höchstens ein Auftrag: ¬x10, ¬x20; x11 (x10 ∨ x11); x21 (x20 ∨ x21); Klausel ¬x11 ∨ ¬x21 verletzt
    assert r["wert"] == {1: True, 2: False, 3: False, 4: True, 5: False, 6: True}
    assert r["konflikt"] is not None and len(r["wert"]) == 6
    verletzt = mit.klauseln[r["konflikt"]]
    assert all(r["wert"][abs(l)] != (l > 0) for l in verletzt)               # alle Literale der Konfliktklausel sind falsch
    # jeder Schritt hat eine Begründung, die danach nur noch das erzwungene Literal offen hatte
    belegt = {}
    for lit, ci in r["schritte"]:
        andere = [x for x in mit.klauseln[ci] if x != lit]
        assert all(belegt.get(abs(x)) == (x < 0) for x in andere)
        belegt[abs(lit)] = lit > 0


def test_zwei_tauben_zwei_loecher_loesungen_von_hand():
    # Lösungen: Taube 0 in Loch 0 und Taube 1 in Loch 1 oder umgekehrt (2); der Lochvorrang lässt nur die erste zu (1)
    inst = SY.schubfach(2, 2)
    assert inst.meta["erfuellbar"] is True
    erg = SY.loesungen_und_bahnen(inst, SY.REGEL_LOCHVORRANG)
    assert (erg["loesungen"], erg["bahnen"], erg["mit_brechung"], erg["bahngroessen"]) == (2, 1, 1, [2])


@pytest.mark.parametrize("h", [3, 4])
def test_h_tauben_auf_h_loecher_h_fakultaet_loesungen(h):
    erg = SY.loesungen_und_bahnen(SY.schubfach(h, h), SY.REGEL_LOCHVORRANG)
    fak = {3: 6, 4: 24}[h]                      # 3! = 6, 4! = 24 Zuordnungen, eine Bahn, ein Vertreter
    assert (erg["loesungen"], erg["bahnen"], erg["mit_brechung"]) == (fak, 1, 1)


def test_schubfach_erzeuger_stimmt_mit_dem_kern_ueberein():
    for h in (1, 2, 3, 4, 5):
        assert SY.schubfach(h).klauseln == I.pigeonhole(h).klauseln
        assert SY.schubfach(h).n == I.pigeonhole(h).n


def test_klauselzahl_lochvorrang_ist_h_minus_1_mal_tauben():
    for h in range(1, 7):
        assert len(SY.lochvorrang(h)) == (h - 1) * (h + 1)
        assert len(SY.lochvorrang(h, tauben=h)) == (h - 1) * h


# ---------------------------------------------------------------- Schur mit 3 Mengen
@pytest.mark.parametrize("n, loesungen, mit", [(12, 114, 19), (13, 18, 3), (14, 0, 0)])
def test_schur3_zaehlung_von_hand(n, loesungen, mit):
    erg = SY.loesungen_und_bahnen(I.schur(n, 3), SY.REGEL_WERTEVORRANG)
    assert (erg["loesungen"], erg["mit_brechung"], erg["bahnen"]) == (loesungen, mit, mit)
    assert erg["vertreter_erfuellen_regel"] is True
    assert erg["bahngroessen"] == ([6] if loesungen else [])            # alle drei Farben benutzt: Bahnen der Größe 3! = 6
    assert loesungen == 6 * mit                                        # 114 = 6 · 19, 18 = 6 · 3


def test_schur3_n13_vertreter_von_hand():
    erg = SY.loesungen_und_bahnen(I.schur(13, 3), SY.REGEL_WERTEVORRANG, behalte=3)
    handvertreter = tuple(0 if i + 1 in (1, 4, 7, 10, 13) else 1 if i + 1 in (2, 3, 11, 12) else 2 for i in range(13))     # {1,4,7,10,13} | {2,3,11,12} | {5,6,8,9}
    assert len(erg["beispiele"]) == 3 and handvertreter in erg["beispiele"]            # drei Vertreter, einer davon der aus dem Handbeispiel
    assert all(wertevorrang_ok(f) for f in erg["beispiele"])


def test_wertevorrang_klauselzahl_k_minus_1_mal_n():
    assert [len(SY.wertevorrang_schur(n, 3)) for n in (12, 13, 14)] == [24, 26, 28]     # (k − 1) · n
    assert len(SY.wertevorrang_schur(10, 4)) == 30
    # für Zahl 1 ist die Klausel eine Einheitsklausel ¬x(1, c): Variable (i, c) = (i − 1)·k + c + 1
    assert SY.wertevorrang_schur(3, 3)[:2] == [(-2,), (-3,)]
    # Zahl 2, Farbe 1: ¬x(2, 1) ∨ x(1, 0) = ¬5 ∨ 1; Farbe 2: ¬x(2, 2) ∨ x(1, 1) = ¬6 ∨ 2
    assert SY.wertevorrang_schur(3, 3)[2:4] == [(-5, 1), (-6, 2)]


def test_schur4_n10_bahnen_von_hand():
    # 71 136 Lösungen = 2 964 Bahnen · 24 (auch Lösungen mit nur 3 von 4 Farben haben Bahnen der Größe 4·3·2 = 24)
    erg = SY.loesungen_und_bahnen(I.schur(10, 4), SY.REGEL_WERTEVORRANG)
    assert (erg["loesungen"], erg["mit_brechung"], erg["bahnen"], erg["bahngroessen"]) == (71136, 2964, 2964, [24])
    assert 71136 == 24 * 2964


def test_variablenschema_stimmt_mit_dem_kern_ueberein():
    for k in (2, 3):
        inst = I.schur(4, k)
        for i, c in itertools.product(range(1, 5), range(k)):
            assert SY.var_schur(i, c, k) == (i - 1) * k + c + 1
        assert inst.klauseln[0] == tuple(SY.var_schur(1, c, k) for c in range(k))               # „mindestens eine Farbe“ der Zahl 1
    inst = I.faerbung(3, [(0, 1)], 3)
    assert (-SY.var_faerbung(0, 2, 3), -SY.var_faerbung(1, 2, 3)) in inst.klauseln


# ---------------------------------------------------------------- Färbung
def test_kante_fest_zwei_einheitsklauseln_der_ersten_kante():
    kanten = [(1, 3), (0, 2)]
    # erste Kante (1, 3): Knoten 1 in Farbe 0 (Variable 1·3 + 0 + 1 = 4), Knoten 3 in Farbe 1 (3·3 + 1 + 1 = 11)
    assert SY.kante_fest(kanten, 3) == [(4,), (11,)]
    assert SY.kante_fest([], 3) == [] and SY.kante_fest(kanten, 1) == []


def test_wertevorrang_faerbung_klauseln_von_hand():
    # Knoten 0: ¬x(0, c) für c = 1, 2 (Variablen 2, 3); Knoten 1: ¬x(1, 1) ∨ x(0, 0) = ¬5 ∨ 1, ¬x(1, 2) ∨ x(0, 1) = ¬6 ∨ 2
    assert SY.wertevorrang_faerbung(2, 3) == [(-2,), (-3,), (-5, 1), (-6, 2)]


def test_zusatzklauseln_passen_zur_art_der_instanz():
    with pytest.raises(ValueError):
        SY.zusatzklauseln(I.schur(5, 3), SY.REGEL_LOCHVORRANG)
    with pytest.raises(ValueError):
        SY.zusatzklauseln(SY.schubfach(2), SY.REGEL_WERTEVORRANG)
    with pytest.raises(ValueError):
        SY.zusatzklauseln(I.rand3(5, 10, 1), SY.REGEL_KANTE_FEST)
    g = I.rampen_instanz(10, 3.0, 4, 3)
    assert len(SY.mit_brechung(g, SY.REGEL_KANTE_FEST).klauseln) == len(g.klauseln) + 2
    assert len(SY.mit_brechung(g, SY.REGEL_WERTEVORRANG).klauseln) == len(g.klauseln) + 2 * 10
    # die Ausgangsinstanz bleibt unverändert
    assert len(g.klauseln) == len(I.rampen_instanz(10, 3.0, 4, 3).klauseln)


def test_kanonisch_nach_erstem_auftreten():
    assert SY.kanonisch((2, 2, 0, 1, 0)) == (0, 0, 1, 2, 1)
    assert SY.kanonisch(()) == ()
    assert wertevorrang_ok(SY.kanonisch((1, 0, 2, 2, 1)))
