"""Läufe und Messreihen (`smb_algorithm.py`): Handwerte des Handbeispiels, Aufbau der Reihen, Seeds, Budget."""

import pytest

import smb_algorithm as A
import smb_instanzen as I
import smb_symmetrie as SY


def test_handbeispiel_schubfach_h2_konfliktzaehler(php2):
    ohne, mit = A.lauf(php2), A.lauf(php2, SY.REGEL_LOCHVORRANG)
    assert (ohne.antwort, mit.antwort) == (False, False)
    assert mit.stat["konflikte"] == 1 and mit.stat["entscheidungen"] == 0        # leere Klausel auf Stufe 0: eine Konflikt, keine Entscheidung
    assert ohne.stat["konflikte"] == 2 and ohne.stat["entscheidungen"] == 1      # eine Entscheidung, dann zwei Konflikte (Standardlauf)


def test_wurzel_ohne_und_mit_regel(php2):
    ohne, mit = A.wurzel(php2), A.wurzel(php2, SY.REGEL_LOCHVORRANG)
    assert (ohne["konflikt"], ohne["belegt"], ohne["variablen"]) == (None, 0, 6)
    assert mit["konflikt"] == 8 and mit["belegt"] == 6 and len(mit["klauseln"]) == 12
    assert mit["klauseln"][9:] == SY.lochvorrang(2)


def test_messung_und_antworttext(php2):
    m = A.messung(A.lauf(php2, SY.REGEL_LOCHVORRANG))
    assert m.antwort is False and m.antwort_text == "unerfüllbar" and m.konflikte == 1
    assert A.messung(A.lauf(I.schur(13, 3))).antwort_text == "erfüllbar"
    assert A.messung(A.lauf(I.pigeonhole(7), budget=10)).antwort_text == "Abbruch am Budget"


def test_regel_der_aufgabe():
    assert A.regel_der_aufgabe(I.schur(5, 3)) == SY.REGEL_WERTEVORRANG
    assert A.regel_der_aufgabe(SY.schubfach(3)) == SY.REGEL_LOCHVORRANG
    assert A.regel_der_aufgabe(I.rampen_instanz(10, 3.0, 1, 3)) == SY.REGEL_KANTE_FEST


def test_lauf_prueft_das_modell_gegen_die_aufgabe(monkeypatch):
    """Ein Löser, der ein falsches Modell meldet, fällt auf: `lauf` wirft statt es durchzureichen."""
    import smb_cdcl

    echt = smb_cdcl.solve
    def falsch(n, klauseln, **kw):
        erg = echt(n, klauseln, **kw)
        erg.modell = {v: False for v in range(1, n + 1)}
        return erg
    monkeypatch.setattr(A, "solve", falsch)
    with pytest.raises(RuntimeError):
        A.lauf(I.schur(5, 3))


def test_schubfach_reihe_und_schur_reihe_aufbau():
    zeilen = A.schubfach_reihe(3, 5, 100000)
    assert [z["h"] for z in zeilen] == [3, 4, 5]
    assert [z["ohne"].konflikte for z in zeilen] == [7, 28, 159] and [z["mit"].konflikte for z in zeilen] == [1, 1, 1]
    s = A.schur_reihe([13, 14], 3, 100000)
    assert [(z["n"], z["ohne"].antwort, z["mit"].antwort) for z in s] == [(13, True, True), (14, False, False)]


def test_konflikte_je_seed_laenge_antworten_und_abbrueche():
    inst = I.schur(14, 3)
    konflikte, antworten, abbr = A.konflikte_je_seed(inst, None, range(1, 6), 100000)
    assert len(konflikte) == 5 and antworten == {False} and abbr == 0
    konflikte, antworten, abbr = A.konflikte_je_seed(I.pigeonhole(7), None, range(1, 4), 30)
    assert konflikte == [30, 30, 30] and antworten == set() and abbr == 3        # Abbrüche zählen mit dem Budget


def test_faerbung_zelle_aufbau_und_gleiche_antworten():
    z = A.faerbung_zelle(30, 500, 100000, anzahl=4)
    assert z["n"] == 30 and z["seed0"] == 500 and z["anzahl"] == 4
    assert set(z["regeln"]) == {"ohne", "kante_fest", "wertevorrang"} and all(len(v) == 4 for v in z["regeln"].values())
    assert z["antworten_gleich"] is True and set(z["abbrueche"]) == {"ohne", "kante_fest", "wertevorrang"}
    assert set(z["antworten"]) <= {"erfüllbar", "unerfüllbar", "Abbruch"}


def test_antworten_vertraeglich():
    assert A.antworten_vertraeglich([True, False, None], [True, None, False]) is True
    assert A.antworten_vertraeglich([True], [False]) is False
