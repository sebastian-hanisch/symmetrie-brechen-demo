"""Eigenschaftstests (Plan: Äquierfüllbarkeit, Bahnen, Lösungen mit Regel sind Lösungen der Aufgabe, Farbvertauschung, Löser-Zufalls-Seed ändert die Antwort nie).

Der große Lauf mit mehr als 200 zufälligen Färbungsaufgaben steht nicht im Repo (Scratch-Lauf, README „Verifikation“); hier die schnelle Fassung."""

import itertools

import pytest

import smb_algorithm as A
import smb_instanzen as I
import smb_symmetrie as SY
from conftest import schur_gueltig, wertevorrang_ok
from smb_cdcl import solve
from smb_rng import SplitMix64


def _antworten(inst, regeln, budget=50000):
    return [A.lauf(inst, r, budget=budget).antwort for r in regeln]


# ---------------------------------------------------------------- Äquierfüllbarkeit
@pytest.mark.parametrize("k", [1, 2, 3])
def test_aequierfuellbarkeit_schur_n_bis_20(k):
    for n in range(1, 21):
        a, b = _antworten(I.schur(n, k), (None, SY.REGEL_WERTEVORRANG))
        assert a is not None and a == b, (n, k)


def test_aequierfuellbarkeit_schubfach_h_bis_4():
    for h in range(1, 5):
        for t in range(1, h + 3):
            a, b = _antworten(SY.schubfach(h, t), (None, SY.REGEL_LOCHVORRANG))
            assert a is not None and a == b == (t <= h), (h, t)


def test_aequierfuellbarkeit_60_zufaellige_faerbungen():
    rng = SplitMix64(2026)
    gesehen = set()
    for i in range(60):
        n = 5 + rng.below(6)                                       # 5 bis 10 Knoten
        maximal = n * (n - 1) // 2
        g = I.faerbung(n, I.zufallskanten(n, min(maximal, n + rng.below(2 * n)), rng.next() & 0xFFFFF), 3)
        antworten = _antworten(g, (None, SY.REGEL_KANTE_FEST, SY.REGEL_WERTEVORRANG))
        gesehen.add(antworten[0])
        assert None not in antworten and len(set(antworten)) == 1, (i, antworten)
    assert gesehen == {True, False}


# ---------------------------------------------------------------- Lösungen mit Regel sind Lösungen der Aufgabe
def test_jede_loesung_mit_regel_ist_loesung_der_aufgabe():
    for n in (6, 10, 13):
        for regel in (None, SY.REGEL_WERTEVORRANG):
            inst = I.schur(n, 3)
            erg = A.lauf(inst, regel)           # `lauf` prüft das Modell gegen die Klauseln der Ausgangsaufgabe und wirft sonst
            assert erg.antwort is True and I.pruefe_modell(inst.klauseln, erg.modell)
    inst = I.rampen_instanz(30, 3.0, 7, 3)
    for regel in (SY.REGEL_KANTE_FEST, SY.REGEL_WERTEVORRANG):
        erg = A.lauf(inst, regel)
        assert erg.antwort is True and I.pruefe_modell(inst.klauseln, erg.modell)


def test_modelle_mit_regel_erfuellen_die_regel():
    inst = SY.mit_brechung(I.schur(13, 3), SY.REGEL_WERTEVORRANG)
    erg = solve(inst.n, inst.klauseln)
    f = SY.farben_je_zahl(tuple(erg.modell[v] for v in range(1, inst.n + 1)), 3)
    assert wertevorrang_ok(f) and schur_gueltig(f)
    g = I.rampen_instanz(25, 3.0, 5, 3)
    kanten = g.meta["kanten"]
    erg = A.lauf(g, SY.REGEL_KANTE_FEST)
    farben = I.faerbung_aus_modell(g, erg.modell)
    a, b = kanten[0]
    assert farben[a] == 0 and farben[b] == 1                    # die erste Kante hat die Farben 0 und 1
    assert all(farben[x] != farben[y] for x, y in kanten)       # und die Färbung ist gültig


# ---------------------------------------------------------------- Farbvertauschung und Bahnen
def test_farbpermutation_einer_loesung_bleibt_loesung():
    inst = I.schur(13, 3)
    erg = solve(inst.n, inst.klauseln)
    f = SY.farben_je_zahl(tuple(erg.modell[v] for v in range(1, inst.n + 1)), 3)
    for p in itertools.permutations(range(3)):
        assert schur_gueltig(tuple(p[c] for c in f))
        # und als Modell: die permutierte Belegung erfüllt die Klauseln der Aufgabe
        modell = {SY.var_schur(i + 1, c, 3): (p[f[i]] == c) for i in range(13) for c in range(3)}
        assert I.pruefe_modell(inst.klauseln, modell)


def test_zahl_der_loesungen_mit_regel_ist_die_zahl_der_bahnen():
    for n in range(1, 14):
        erg = SY.loesungen_und_bahnen(I.schur(n, 3), SY.REGEL_WERTEVORRANG)
        assert erg["mit_brechung"] == erg["bahnen"] and erg["vertreter_erfuellen_regel"] is True, n
    for h in (1, 2, 3):
        erg = SY.loesungen_und_bahnen(SY.schubfach(h, h), SY.REGEL_LOCHVORRANG)
        assert erg["mit_brechung"] == erg["bahnen"] == 1


def test_loesungen_durch_k_fakultaet_wenn_alle_bahnen_so_gross_sind():
    for n in range(2, 14):
        erg = SY.loesungen_und_bahnen(I.schur(n, 3), SY.REGEL_WERTEVORRANG)
        if erg["bahngroessen"] == [6]:
            assert erg["loesungen"] == 6 * erg["mit_brechung"]
    # bis n = 4 genügen schon 2 Farben: Bahnen der Größe 3·2 = 6 (zwei benutzte Farben von drei), n = 1: eine Farbe von drei, Bahn der Größe 3
    assert SY.loesungen_und_bahnen(I.schur(1, 3), SY.REGEL_WERTEVORRANG)["bahngroessen"] == [3]


# ---------------------------------------------------------------- Löser-Zufalls-Seed
def test_loeser_zufalls_seed_aendert_die_antwort_nie():
    faelle = [(I.schur(13, 3), True), (I.schur(14, 3), False), (I.schur(38, 4), True), (I.rampen_instanz(60, 5.0, 500, 3), False)]
    for inst, erwartet in faelle:
        for regel in (None, A.regel_der_aufgabe(inst)):
            for seed in range(1, 6):
                assert A.lauf_seed(inst, regel, seed, 20000).antwort is erwartet, (inst.meta.get("art"), regel, seed)


def test_zwei_seeds_geben_mindestens_einmal_verschiedene_konfliktzahlen():
    """Ohne `noise` wären alle Seeds derselbe Lauf (Kern-Docstring); die 20 Seeds des Reiters „Wo es schadet“ wären dann eine Scheinzahl."""
    inst = I.schur(38, 4)
    konflikte = {s: A.lauf_seed(inst, None, s, 20000).stat["konflikte"] for s in (1, 2, 3, 4)}
    assert len(set(konflikte.values())) > 1
    ohne_rauschen = {A.lauf(inst, None, seed=s, noise=False).stat["konflikte"] for s in (1, 2, 3)}
    assert len(ohne_rauschen) == 1                             # nur mit noise wirkt der Seed
