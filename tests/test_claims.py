"""Jede Zahl der README (Abschnitte „Befunde“ und „Befunde und Korrekturen“) wird hier nachgerechnet. Zahl -> Test steht in der Tabelle „Befunde“ der README.

Zwei Arten von Zahlen: (1) exakte Zählungen des deterministischen Lösers (Standardlauf ohne Zufall; Handbeispiel, Schubfach, Schur mit 3 Mengen; ganzzahlig, auf jeder Plattform gleich);
(2) die vorgerechneten Messreihen `smb_messung_vorgerechnet.json` (Messung dieses Repos mit `tools/messung_symmetrie.py`; Löser-Zufalls-Seeds 1 bis 20 und 21 bis 120 mit zufälligem Start
der Aktivitäten, Graphen der Färbung mit den Seeds 500 bis 509). Ein Teil der Zellen wird hier live nachgerechnet, um zu zeigen, dass die Datei dem heutigen Code entspricht;
die übrigen werden aus der Datei gezählt. Die Zahlen der Vormessung der Planung (`out_v14.txt`) stammen bei der Färbung von anderen Zufallsfolgen (Python-`random`) und gelten nicht als Ersatz.
Die langsamen Nachmessungen (Schur mit 4 Mengen, n = 44 und 45, Minuten) tragen den Marker `slow`: `python -m pytest tests -m slow`; n = 44 ohne Regel und n = 45 nur mit `SMB_VOLLE_NACHMESSUNG=1`
(zehn bis dreißig Minuten). Sekunden werden nirgends geprüft."""

import os
import re
import statistics
from pathlib import Path

import pytest

import smb_algorithm as A
import smb_constants as C
import smb_evaluation as E
import smb_instanzen as I
import smb_symmetrie as SY

ROOT = Path(__file__).resolve().parent.parent
LOCH, WERT, KANTE = SY.REGEL_LOCHVORRANG, SY.REGEL_WERTEVORRANG, SY.REGEL_KANTE_FEST


@pytest.fixture(scope="module")
def daten():
    return E.lade_messung()


def _k(m):
    return m["konflikte"]


# ---------------------------------------------------------------- Handbeispiel und exakte Zählungen
def test_claim_handbeispiel_schubfach_h2(php2):
    """3 Aufträge auf 2 Rampen: 9 Klauseln, 3 des Lochvorrangs; Einheitspropagation ohne Regel belegt 0 von 6, mit Regel 6 von 6 (Widerspruch ohne Entscheidung); CDCL 2 Konflikte
    (1 Entscheidung) ohne, 1 Konflikt (0 Entscheidungen) mit Regel; erfüllbare Fassung (2 Aufträge): 2 Lösungen, mit Regel 1."""
    assert (len(php2.klauseln), len(SY.lochvorrang(2))) == (9, 3)
    assert (A.wurzel(php2)["belegt"], A.wurzel(php2, LOCH)["belegt"], A.wurzel(php2, LOCH)["konflikt"] is not None) == (0, 6, True)
    ohne, mit = A.lauf(php2), A.lauf(php2, LOCH)
    assert (ohne.stat["konflikte"], ohne.stat["entscheidungen"], mit.stat["konflikte"], mit.stat["entscheidungen"]) == (2, 1, 1, 0)
    e = SY.loesungen_und_bahnen(SY.schubfach(2, 2), LOCH)
    assert (e["loesungen"], e["mit_brechung"]) == (2, 1)


def test_claim_schur3_zaehlung_n12_n13_n14():
    """Schur mit 3 Mengen: n = 12: 114 Lösungen, 19 mit Wertevorrang; n = 13: 18 Lösungen in 3 Bahnen der Größe 6, 3 mit Wertevorrang; n = 14: keine (S(3) = 13);
    Klauseln der Regel (k − 1)·n = 24 / 26 / 28; Schur mit 4 Mengen, n = 10: 71 136 Lösungen = 2 964 Bahnen · 24 (siehe tests/test_symmetrie.py)."""
    ergebnisse = {n: SY.loesungen_und_bahnen(I.schur(n, 3), WERT) for n in (12, 13, 14)}
    assert [(e["loesungen"], e["mit_brechung"]) for e in ergebnisse.values()] == [(114, 19), (18, 3), (0, 0)]
    assert ergebnisse[13]["bahngroessen"] == [6] and ergebnisse[13]["bahnen"] == 3
    assert [len(SY.wertevorrang_schur(n, 3)) for n in (12, 13, 14)] == [24, 26, 28]


def test_claim_schubfach_konflikte_h3_bis_h7_live():
    """Standardlauf ohne Zufall, h + 1 Aufträge auf h Rampen: ohne Regel 7 / 28 / 159 / 1 004 / 4 811 Konflikte für h = 3 bis 7; mit Lochvorrang je 1 Konflikt (Wurzel, 0 Entscheidungen)."""
    zeilen = A.schubfach_reihe(3, 7, 100000)
    assert [z["ohne"].konflikte for z in zeilen] == [7, 28, 159, 1004, 4811]
    assert all(z["mit"].konflikte == 1 and z["mit"].entscheidungen == 0 and z["mit"].antwort is False and z["ohne"].antwort is False for z in zeilen)


def test_claim_schur3_konflikte_n11_bis_n14_live():
    """Standardlauf, Schur mit 3 Mengen: n = 11 / 12 / 13 / 14: ohne Regel 1 / 1 / 18 / 148 Konflikte, mit Wertevorrang 2 / 2 / 11 / 21; n = 14 ist unerfüllbar (Konfliktzahlen sind Zählungen des Standardlaufs)."""
    zeilen = A.schur_reihe((11, 12, 13, 14), 3, 100000)
    assert [(z["ohne"].konflikte, z["mit"].konflikte) for z in zeilen] == [(1, 2), (1, 2), (18, 11), (148, 21)]
    assert [z["ohne"].antwort for z in zeilen] == [True, True, True, False] == [z["mit"].antwort for z in zeilen]
    klassen = [E.klasse_der_zeile(E.zeile_aus({"konflikte": z["ohne"].konflikte, "antwort": z["ohne"].antwort_text}, {"konflikte": z["mit"].konflikte, "antwort": z["mit"].antwort_text})) for z in zeilen]
    assert klassen == [E.GLEICH, E.GLEICH, E.WENIGER, E.WENIGER]          # 1 → 2 sind beide höchstens 10 Konflikte: „etwa gleich“


# ---------------------------------------------------------------- Messreihen aus der Datei
def test_claim_aufbau_der_messdatei(daten):
    """Budgets 100 000 (Schubfach, Reiter 4, Färbung) und 300 000 (Schur mit 4 Mengen); 20 + 100 Löser-Zufalls-Seeds; 10 Graphen (Seeds 500 bis 509) je Zelle; 0 Abbrüche in Reiter 4."""
    m = daten["meta"]
    assert (m["budget_schubfach"], m["budget_schur4"], m["budget_schadet"], m["budget_faerbung"]) == (100000, 300000, 100000, 100000)
    assert m["schadet_seeds"] == list(range(1, 21)) and m["kontrolle_seeds"] == [21, 120] and m["faerbung"]["seeds"] == list(range(500, 510))
    assert [z["n"] for z in daten["schadet"]] == [38, 40, 42, 43] and [z["n"] for z in daten["faerbung"]] == [60, 90, 120]
    assert all(len(z["ohne"]["konflikte"]) == 20 == len(z["mit"]["konflikte"]) and z["ohne"]["abbrueche"] == z["mit"]["abbrueche"] == 0 for z in daten["schadet"])
    assert len(daten["kontrolle"]["ohne"]["konflikte"]) == 100 == len(daten["kontrolle"]["mit"]["konflikte"])
    assert all(z["ohne"]["antworten"] == z["mit"]["antworten"] == ["True"] for z in daten["schadet"])           # Schur mit 4 Mengen, n ≤ 43: in allen Läufen erfüllbar
    assert all(a == "unerfüllbar" and z["antworten_gleich"] for z in daten["faerbung"] for a in z["antworten"])     # alle 30 Graphen unerfüllbar, Antwort in allen Regeln gleich
    assert sum(len(z["antworten"]) for z in daten["faerbung"]) == 30 and all(sum(z["abbrueche"].values()) == 0 for z in daten["faerbung"])


def test_claim_schubfach_reihe_h3_bis_h8(daten):
    """Vorgerechnet: ohne Regel 7 / 28 / 159 / 1 004 / 4 811 / 27 932 Konflikte für h = 3 bis 8, mit Lochvorrang überall 1 (ohne Entscheidung); Faktor je zusätzliche Rampe 4,0 bis 6,3."""
    sf = daten["schubfach"]
    assert [z["h"] for z in sf] == [3, 4, 5, 6, 7, 8]
    assert [_k(z["ohne"]) for z in sf] == [7, 28, 159, 1004, 4811, 27932] and [_k(z["mit"]) for z in sf] == [1] * 6
    f = [b / a for a, b in zip([_k(z["ohne"]) for z in sf], [_k(z["ohne"]) for z in sf][1:])]
    assert (round(min(f), 1), round(max(f), 1)) == (4.0, 6.3)
    assert all(z["ohne"]["antwort"] == z["mit"]["antwort"] == "unerfüllbar" for z in sf)
    assert all(z["mit"]["entscheidungen"] == 0 for z in sf)                 # mit Lochvorrang endet schon die Einheitspropagation auf Stufe 0 im Widerspruch


def test_claim_schubfach_datei_stimmt_mit_dem_heutigen_code_ueberein(daten):
    live = {z["h"]: z for z in A.schubfach_reihe(3, 6, 100000)}
    for z in daten["schubfach"]:
        if z["h"] in live:
            assert (_k(z["ohne"]), _k(z["mit"])) == (live[z["h"]]["ohne"].konflikte, live[z["h"]]["mit"].konflikte)


def test_claim_schur_datei_k3_und_k4(daten):
    """Schur mit 3 Mengen (Datei): wie live. Schur mit 4 Mengen: n = 43: 6 → 352 Konflikte, n = 44: 108 775 → 3 844 (beide erfüllbar), n = 45: siehe README."""
    assert [(z["n"], _k(z["ohne"]), _k(z["mit"])) for z in daten["schur3"]] == [(11, 1, 2), (12, 1, 2), (13, 18, 11), (14, 148, 21)]
    s4 = {z["n"]: z for z in daten["schur4"]}
    assert (_k(s4[43]["ohne"]), _k(s4[43]["mit"]), s4[43]["ohne"]["antwort"], s4[43]["mit"]["antwort"]) == (6, 352, "erfüllbar", "erfüllbar")
    assert (_k(s4[44]["ohne"]), _k(s4[44]["mit"]), s4[44]["ohne"]["antwort"], s4[44]["mit"]["antwort"]) == (108775, 3844, "erfüllbar", "erfüllbar")
    assert 108775 / 3844 == pytest.approx(28.3, abs=0.05)                         # „Faktor 28“
    assert [z["n"] for z in daten["schur4"]] == [43, 44, 45]


def test_claim_schur_k4_n43_live():
    inst = I.schur(43, 4)
    assert A.lauf(inst, None, budget=300000).stat["konflikte"] == 6
    assert A.lauf(inst, WERT, budget=300000).stat["konflikte"] == 352


@pytest.mark.slow
def test_claim_schubfach_h8_live_slow():
    """Nachmessung: Schubfach h = 8 ohne Regel 27 932 Konflikte (Minuten), mit Lochvorrang 1."""
    inst = SY.schubfach(8)
    assert A.lauf(inst, LOCH, budget=100000).stat["konflikte"] == 1
    assert A.lauf(inst, None, budget=100000).stat["konflikte"] == 27932


@pytest.mark.slow
def test_claim_schur_k4_n44_mit_wertevorrang_slow():
    """Nachmessung: n = 44 mit Wertevorrang: 3 844 Konflikte (Zählung, Minuten)."""
    erg = A.lauf(I.schur(44, 4), WERT, budget=300000)
    assert erg.antwort is True and erg.stat["konflikte"] == 3844


@pytest.mark.slow
@pytest.mark.skipif(not os.environ.get("SMB_VOLLE_NACHMESSUNG"), reason="zehn bis dreißig Minuten; nur mit SMB_VOLLE_NACHMESSUNG=1")
def test_claim_schur_k4_n44_ohne_und_n45_voll_slow(daten):
    s4 = {z["n"]: z for z in daten["schur4"]}
    assert A.lauf(I.schur(44, 4), None, budget=300000).stat["konflikte"] == _k(s4[44]["ohne"])
    for regel, schluessel in ((WERT, "mit"), (None, "ohne")):
        erg = A.lauf(I.schur(45, 4), regel, budget=300000)
        assert erg.stat["konflikte"] == _k(s4[45][schluessel]) and A.messung(erg).antwort_text == s4[45][schluessel]["antwort"]


# ---------------------------------------------------------------- Reiter 4: Schur n = 38 bis 43 mit Löser-Zufalls-Seeds
def test_claim_standardlaeufe_n38_bis_n43_live(daten):
    """Standardlauf ohne Zufall, Schur mit 4 Mengen: n = 38 / 40 / 42 / 43: ohne Regel 0 / 6 / 6 / 6 Konflikte, mit Wertevorrang 65 / 184 / 352 / 352 (Datei und live)."""
    for z in daten["schadet"]:
        inst = I.schur(z["n"], 4)
        live = (A.lauf(inst, None, budget=100000).stat["konflikte"], A.lauf(inst, WERT, budget=100000).stat["konflikte"])
        assert live == (_k(z["standard"]["ohne"]), _k(z["standard"]["mit"]))
    assert [(_k(z["standard"]["ohne"]), _k(z["standard"]["mit"])) for z in daten["schadet"]] == [(0, 65), (6, 184), (6, 352), (6, 352)]


def test_claim_20_seeds_je_n_median_maximum_laeufe_p(daten):
    """Schur mit 4 Mengen, je 20 Löser-Zufalls-Seeds (1 bis 20) ohne und mit Wertevorrang; Median ohne / mit (Maximum ohne / mit; Läufe mit mehr Konflikten mit Regel; Rangsummentest p):
    n = 38: 131,5 / 95,5 (631 / 698; 5; 0,26); n = 40: 323 / 363 (2 717 / 1 825; 10; 0,74); n = 42: 278 / 366 (5 363 / 1 875; 12; 0,48); n = 43: 302,5 / 366 (5 306 / 1 711; 10; 0,20)."""
    erwartet = {38: (131.5, 95.5, 631, 698, 5, 0.26), 40: (323.0, 363.0, 2717, 1825, 10, 0.74), 42: (278.0, 366.0, 5363, 1875, 12, 0.48), 43: (302.5, 366.0, 5306, 1711, 10, 0.20)}
    for z in daten["schadet"]:
        s = E.zusammenfassung_seeds(z["ohne"]["konflikte"], z["mit"]["konflikte"])
        mo, mm, xo, xm, mehr, p = erwartet[z["n"]]
        assert (s["median_ohne"], s["median_mit"], s["max_ohne"], s["max_mit"], s["laeufe_mehr"]) == (mo, mm, xo, xm, mehr), z["n"]
        assert s["p"] == pytest.approx(p, abs=0.005), z["n"]


def test_claim_n43_20_seeds_quotient_und_klasse(daten):
    """n = 43: Median mit / ohne = 366 / 302,5 = 1,21 (+21 %), außerhalb des Bandes ±20 %, aber nicht belegt (p = 0,20); der Standardlauf (6 → 352) liegt weit unter dem kleinsten Seed-Wert ohne Regel (38)."""
    z = next(z for z in daten["schadet"] if z["n"] == 43)
    ohne, mit = z["ohne"]["konflikte"], z["mit"]["konflikte"]
    assert statistics.median(mit) / statistics.median(ohne) == pytest.approx(1.21, abs=0.005)
    assert E.einordnung(statistics.median(ohne), statistics.median(mit)) == E.MEHR and E.einordnung_getestet(ohne, mit) == E.NICHT_BELEGT
    assert min(ohne) == 38 and _k(z["standard"]["ohne"]) == 6 < min(ohne)
    assert E._prozent(statistics.median(ohne), statistics.median(mit)) == "+21 %"


def test_claim_kontrolle_100_seeds_n43(daten):
    """Kontrolle n = 43 mit 100 weiteren Seeds (21 bis 120): Median 391,5 ohne, 287 mit Wertevorrang (−27 %), mit der Regel mehr Konflikte in 36 von 100 Läufen, weniger in 63, Maximum 3 509 gegen 4 181,
    Rangsummentest p = 0,011: dort weniger Konflikte, entgegengesetzt zu den ersten 20 Seeds. Alle 120 Seeds zusammen: Median 342 gegen 318 (−7 %), p = 0,071."""
    k = daten["kontrolle"]
    s = E.zusammenfassung_seeds(k["ohne"]["konflikte"], k["mit"]["konflikte"])
    assert (s["n"], s["median_ohne"], s["median_mit"], s["laeufe_mehr"], s["laeufe_weniger"], s["max_ohne"], s["max_mit"]) == (100, 391.5, 287.0, 36, 63, 3509, 4181)
    assert s["p"] == pytest.approx(0.011, abs=0.0005) and E._prozent(391.5, 287.0) == "−27 %"
    assert E.einordnung_getestet(k["ohne"]["konflikte"], k["mit"]["konflikte"]) == E.WENIGER
    z20 = next(z for z in daten["schadet"] if z["n"] == 43)
    alle = E.zusammenfassung_seeds(z20["ohne"]["konflikte"] + k["ohne"]["konflikte"], z20["mit"]["konflikte"] + k["mit"]["konflikte"])
    assert (alle["n"], alle["median_ohne"], alle["median_mit"]) == (120, 342.0, 318.0) and alle["p"] == pytest.approx(0.071, abs=0.0005)
    assert E._prozent(342.0, 318.0) == "−7 %"


def test_claim_seeds_datei_stimmt_mit_dem_heutigen_code_ueberein(daten):
    """Live nachgerechnet: n = 43, Seeds 1 und 2 (ohne: 102, 77; mit: 1 711, 1 094) und n = 38, Seed 1 (ohne 120, mit 193)."""
    z43 = next(z for z in daten["schadet"] if z["n"] == 43)
    inst = I.schur(43, 4)
    assert [A.lauf_seed(inst, None, s, 100000).stat["konflikte"] for s in (1, 2)] == z43["ohne"]["konflikte"][:2] == [102, 77]
    assert [A.lauf_seed(inst, WERT, s, 100000).stat["konflikte"] for s in (1, 2)] == z43["mit"]["konflikte"][:2] == [1711, 1094]
    z38 = next(z for z in daten["schadet"] if z["n"] == 38)
    inst = I.schur(38, 4)
    assert (A.lauf_seed(inst, None, 1, 100000).stat["konflikte"], A.lauf_seed(inst, WERT, 1, 100000).stat["konflikte"]) == (z38["ohne"]["konflikte"][0], z38["mit"]["konflikte"][0]) == (120, 193)


# ---------------------------------------------------------------- Reiter 4: Färbung
def test_claim_faerbung_zellen(daten):
    """3-Färbung, Grad 5, 10 Graphen (Seeds 500 bis 509), alle unerfüllbar: Median der Konflikte ohne Regel / erste Kante fest / Wertevorrang: n = 60: 21,5 / 7 / 9; n = 90: 49 / 30,5 / 32,5;
    n = 120: 73 / 28,5 / 35,5. Graphen mit weniger Konflikten (mehr) mit erster Kante fest: 9 (0) / 10 (0) / 10 (0), gleich viele 1 / 0 / 0; mit Wertevorrang 10 (0) / 9 (1) / 9 (1).
    Vorzeichentest p: erste Kante fest 0,004 / 0,002 / 0,002; Wertevorrang 0,002 / 0,021 / 0,021."""
    erwartet = {60: {"kante_fest": (21.5, 7.0, 9, 0, 1), "wertevorrang": (21.5, 9.0, 10, 0, 0)}, 90: {"kante_fest": (49.0, 30.5, 10, 0, 0), "wertevorrang": (49.0, 32.5, 9, 1, 0)},
                120: {"kante_fest": (73.0, 28.5, 10, 0, 0), "wertevorrang": (73.0, 35.5, 9, 1, 0)}}
    ps = {60: {"kante_fest": 0.004, "wertevorrang": 0.002}, 90: {"kante_fest": 0.002, "wertevorrang": 0.0215}, 120: {"kante_fest": 0.002, "wertevorrang": 0.0215}}
    for z in daten["faerbung"]:
        for regel in ("kante_fest", "wertevorrang"):
            f = E.zusammenfassung_faerbung(z, regel)
            assert (f["median_ohne"], f["median_mit"], f["laeufe_weniger"], f["laeufe_mehr"], f["laeufe_gleich"]) == erwartet[z["n"]][regel], (z["n"], regel)
            assert f["p"] == pytest.approx(ps[z["n"]][regel], abs=0.0006) and f["klasse"] == E.WENIGER
    # Maxima: ohne Regel 72 / 103 / 172, erste Kante fest 23 / 75 / 58, Wertevorrang 20 / 65 / 79
    assert [max(z["regeln"][r]) for r in ("ohne", "kante_fest", "wertevorrang") for z in daten["faerbung"]] == [72, 103, 172, 23, 75, 58, 20, 65, 79]


def test_claim_faerbung_datei_stimmt_mit_dem_heutigen_code_ueberein(daten):
    """Live: n = 60, die ersten 3 Graphen (Seeds 500 bis 502), alle drei Regeln."""
    live = A.faerbung_zelle(60, 500, 100000, anzahl=3)
    z60 = daten["faerbung"][0]
    assert {r: v for r, v in live["regeln"].items()} == {r: v[:3] for r, v in z60["regeln"].items()}
    assert live["antworten"] == ["unerfüllbar"] * 3 and live["antworten_gleich"] is True


def test_claim_zaehlung_ueber_zellen(daten):
    """Über die 10 Zellen (Schur n = 38 / 40 / 42 / 43 mit je 20 Seeds, Färbung n = 60 / 90 / 120 mit zwei Regeln und je 10 Graphen): belegt weniger in 6, belegt mehr in 0, etwa gleich in 1 (Schur n = 40),
    jenseits des Bandes aber nicht belegt in 3 (Schur n = 38, 42, 43)."""
    klassen = E.zellen_klassen(daten)
    assert len(klassen) == 10
    z = E.zaehle_klassen(klassen.values())
    assert (z[E.WENIGER], z[E.MEHR], z[E.GLEICH], z[E.NICHT_BELEGT], z[E.OFFEN]) == (6, 0, 1, 3, 0)
    assert [n for n, k in klassen.items() if k == E.NICHT_BELEGT] == ["Schur mit 4 Mengen, n = 38", "Schur mit 4 Mengen, n = 42", "Schur mit 4 Mengen, n = 43"]
    assert [n for n, k in klassen.items() if k == E.GLEICH] == ["Schur mit 4 Mengen, n = 40"]


# ---------------------------------------------------------------- Verdikte, die dieselben Zahlen nennen
def test_claim_verdikt_der_kernfrage_nennt_die_zaehlung(daten):
    kind, text = E.verdict_kern(daten)
    assert "Schubfach, h = 3 bis 8: in 5 von 6 Aufgaben weniger Konflikte mit der Brechung (h = 8: 27 932 → 1)." in text
    assert "Schur mit 4 Mengen, n = 43 bis 45:" in text and "n = 43: 6 → 352, ein Lauf" in text and "nicht belegt" in text
    # 5 von 6: h = 3 hat 7 gegen 1 Konflikt, beide höchstens 10 Konflikte, also „etwa gleich“
    assert E.klasse_der_zeile(E.zeilen_schubfach(daten)[0]) == E.GLEICH


def test_claim_preset_wo_es_schadet_verdikt(daten):
    z = next(z for z in daten["schadet"] if z["n"] == 43)
    kind, text = E.verdict_schadet(43, 4, z["ohne"]["konflikte"], z["mit"]["konflikte"], 0, 0, 100000, (6, 352), (daten["kontrolle"]["ohne"]["konflikte"], daten["kontrolle"]["mit"]["konflikte"]))
    assert kind == "warning" and text.startswith("Verschlechterung im Standardlauf, über die Seeds nicht belegt: ")
    assert "Median 302,5 Konflikte ohne, 366 mit Wertevorrang (+21 %; Maximum 5 306 gegen 1 711)" in text
    assert "Kontrolle mit 100 weiteren Seeds: Median 391,5 gegen 287 (−27 %, p = 0,011)" in text


# ---------------------------------------------------------------- Die README nennt nur vorhandene Tests
def test_readme_nennt_nur_vorhandene_tests():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    vorhanden = {}
    for datei in (ROOT / "tests").glob("test_*.py"):
        vorhanden[datei.name] = set(re.findall(r"^def (test_\w+)", datei.read_text(encoding="utf-8"), flags=re.M))
    alle = set().union(*vorhanden.values())
    genannt = set(re.findall(r"`(test_\w+)`", readme))
    assert genannt, "die README nennt keine Tests"
    assert genannt <= alle, sorted(genannt - alle)
    for datei in re.findall(r"`tests/(test_\w+\.py)`", readme):
        assert datei in vorhanden, datei
