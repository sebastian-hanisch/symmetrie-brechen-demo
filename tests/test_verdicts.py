"""Verdikte an von Hand gesetzten Zeilen (DEMO-PLAYBOOK §12): jede Schwelle und jede Zahl im Text steht hier.

Schwellen (vor der Messung festgelegt): „weniger“ bei Quotient mit/ohne unter 0,8, „mehr“ über 1,2, dazwischen (Grenzen inklusive) „etwa gleich“; beide Zahlen höchstens 10: „etwa gleich“.
Der Test über viele Läufe (Rangsummen- beziehungsweise Vorzeichentest, p < 0,05) kam nach der ersten Messung hinzu (README „Befunde und Korrekturen gegenüber dem Plan“)."""

import random

import pytest

import smb_constants as C
import smb_evaluation as E


def z(ohne, mit, oa=False, ma=False, **kw):
    return {"ohne": ohne, "mit": mit, "ohne_abbruch": oa, "mit_abbruch": ma, **kw}


# ---------------------------------------------------------------- Schwellen und Format
def test_schwellen_stehen_fest():
    assert (C.HILFT_SCHWELLE, C.SCHADET_SCHWELLE, C.KLEIN_KONFLIKTE, C.ALPHA) == (0.8, 1.2, 10, 0.05)


def test_einordnung_grenzen_inklusive():
    assert E.einordnung(100, 80) == E.GLEICH and E.einordnung(100, 79) == E.WENIGER      # genau 0,8: etwa gleich
    assert E.einordnung(100, 120) == E.GLEICH and E.einordnung(100, 121) == E.MEHR       # genau 1,2: etwa gleich
    assert E.einordnung(27932, 1) == E.WENIGER and E.einordnung(6, 352) == E.MEHR and E.einordnung(108775, 3844) == E.WENIGER


def test_einordnung_kleine_zahlen_sind_gleich():
    assert E.einordnung(1, 2) == E.GLEICH and E.einordnung(7, 1) == E.GLEICH and E.einordnung(10, 1) == E.GLEICH      # beide höchstens 10
    assert E.einordnung(11, 1) == E.WENIGER and E.einordnung(0, 0) == E.GLEICH
    assert E.einordnung(0, 65) == E.MEHR                                    # ohne Konflikte, mit 65: mehr (Schur n = 38, Standardlauf)


def test_einordnung_abbrueche_sind_untere_schranken():
    assert E.einordnung(300000, 109523, ohne_abbruch=True) == E.WENIGER          # ohne ≥ 300 000, mit 109 523
    assert E.einordnung(300000, 300000, ohne_abbruch=True) == E.OFFEN            # ohne ≥ 300 000, mit nicht kleiner
    assert E.einordnung(1000, 5000, mit_abbruch=True) == E.MEHR                   # mit ≥ 5 000 gegen 1 000
    assert E.einordnung(1000, 100, mit_abbruch=True) == E.OFFEN
    assert E.einordnung(5, 5, ohne_abbruch=True, mit_abbruch=True) == E.OFFEN


def test_zahlenformat():
    assert E.zahl(1234567) == "1 234 567" and E.zahl(116.5) == "116,5" and E.zahl(49.0) == "49" and E.zahl(0) == "0"
    assert E.dezimal(0.4545, 2) == "0,45" and E.dezimal(1234.56) == "1 234,6"
    assert E.konflikt_wort(1) == "1 Konflikt" and E.konflikt_wort(27932) == "27 932 Konflikte"
    assert E.faktor_text(6, 352) == "×58,7" and E.faktor_text(108775, 3844) == "×28,3" and E.faktor_text(0, 5) == "ohne Faktor"
    assert E._prozent(302.5, 366) == "+21 %" and E._prozent(391.5, 287) == "−27 %" and E._prozent(5, 5) == "±0 %" and E._prozent(0, 4) == "ohne Vergleichswert"


# ---------------------------------------------------------------- Tests über viele Läufe gegen die Bibliothek
def test_mann_whitney_gegen_scipy_asymptotisch():
    stats = pytest.importorskip("scipy.stats")
    rng = random.Random(7)                                   # nur im Test: Python-random ist hier erlaubt (Stichproben für den Vergleich)
    for _ in range(40):
        a = [rng.randrange(0, 60) for _ in range(rng.randrange(8, 30))]
        b = [rng.randrange(10, 90) for _ in range(rng.randrange(8, 30))]
        erwartet = stats.mannwhitneyu(a, b, alternative="two-sided", method="asymptotic", use_continuity=True).pvalue
        assert E.mann_whitney_p(a, b) == pytest.approx(erwartet, rel=1e-9, abs=1e-12)
    assert E.mann_whitney_p([5] * 6, [5] * 7) == 1.0          # alle Werte gleich: kein Unterschied


def test_vorzeichentest_gegen_scipy_und_von_hand():
    stats = pytest.importorskip("scipy.stats")
    for w in range(0, 13):
        for m in range(0, 13):
            if w + m:
                assert E.vorzeichentest_p(w, m) == pytest.approx(stats.binomtest(w, w + m, 0.5).pvalue, abs=1e-12)
    # von Hand: 10 gegen 0: 2 · 1 / 1024; 9 gegen 1: 2 · (1 + 10) / 1024; 5 gegen 5: 1; keine Unterschiede: 1
    assert E.vorzeichentest_p(10, 0) == pytest.approx(2 / 1024) and E.vorzeichentest_p(9, 1) == pytest.approx(22 / 1024)
    assert E.vorzeichentest_p(5, 5) == 1.0 and E.vorzeichentest_p(0, 0) == 1.0
    assert E.p_text(2 / 1024) == "p = 0,002" and E.p_text(0.0004) == "p < 0,001" and E.p_text(0.2041) == "p = 0,204"


def test_einordnung_getestet_verlangt_den_test():
    ohne = [100, 120, 90, 300, 110, 95, 105, 98, 102, 99]
    mit = [150, 80, 200, 90, 250, 70, 400, 60, 310, 120]               # Median 135 gegen 102: Quotient 1,32, aber stark gestreut
    assert E.einordnung(sorted(ohne)[4] / 2 + sorted(ohne)[5] / 2, sorted(mit)[4] / 2 + sorted(mit)[5] / 2) == E.MEHR
    assert E.einordnung_getestet(ohne, mit) == E.NICHT_BELEGT
    klar = [x + 60 for x in ohne]
    assert E.einordnung_getestet(ohne, klar) == E.MEHR
    assert E.einordnung_getestet(klar, ohne) == E.WENIGER
    assert E.einordnung_getestet(ohne, [x + 1 for x in ohne]) == E.GLEICH
    # gepaart: 10 Graphen, überall weniger: Vorzeichentest p = 0,002
    assert E.einordnung_getestet([30, 40, 50, 60, 70, 80, 90, 100, 110, 120], [10, 15, 20, 30, 35, 40, 45, 50, 55, 60], gepaart=True) == E.WENIGER


# ---------------------------------------------------------------- Reiter 2
def test_verdict_schubfach_vorgerechnet_alle_weniger():
    zeilen = [z(7, 1, h=3), z(28, 1, h=4), z(159, 1, h=5), z(1004, 1, h=6)]
    kind, text = E.verdict_schubfach(zeilen, 100000, vorgerechnet=True)
    assert kind == "info"                        # h = 3 hat 7 gegen 1 Konflikt: beide höchstens 10, also „etwa gleich“; nicht alle Zeilen „weniger“
    assert text == ("Ohne Brechung braucht der Löser für h = 3, 4, 5, 6 Rampen 7 / 28 / 159 / 1 004 Konflikte. Je zusätzliche Rampe wächst die Zahl um den Faktor 4,0 bis 6,3. "
                    "Mit Lochvorrang sind es in jeder Zeile 1 Konflikt. Vorgerechnet, ein Lauf je Zeile mit dem Standard-Löser ohne Zufall (Löser-Zufalls-Seed 0), Budget 100 000 Konflikte.")
    kind, text = E.verdict_schubfach(zeilen[1:], 100000)
    assert kind == "success" and text.startswith("Ohne Brechung braucht der Löser für h = 4, 5, 6 Rampen 28 / 159 / 1 004 Konflikte.") and "Live gerechnet" in text


def test_verdict_schubfach_abbruch_und_verschiedene_mitwerte():
    zeilen = [z(159, 1, h=5), z(1000, 1, oa=True, h=6), z(1000, 1, oa=True, h=7)]
    kind, text = E.verdict_schubfach(zeilen, 1000)
    assert "Abbrüche am Budget von 1 000 Konflikten: h = 6, h = 7; dort ist die Zahl eine untere Schranke" in text
    assert "wächst die Zahl um den Faktor" not in text           # Abbrüche gehen in keinen Faktor ein
    kind, text = E.verdict_schubfach([z(159, 3, h=5), z(1004, 2, h=6)], 100000)
    assert "Mit Lochvorrang: 3 / 2 Konflikte." in text and "wächst die Zahl um den Faktor 6,3 bis 6,3." in text      # 1004 / 159 = 6,31


# ---------------------------------------------------------------- Reiter 3
def test_verdict_schur_zaehlt_klassen_und_nennt_faktoren():
    zeilen = [z(6, 352, n=43, k=4), z(108775, 3844, n=44, k=4), z(300000, 109523, oa=True, n=45, k=4)]
    kind, text = E.verdict_schur(zeilen, 4, 300000, True)
    assert kind == "warning"
    assert text == ("Schur mit 4 Mengen, 3 Aufgaben, je ein Lauf ohne und mit Wertevorrang: in 2 von 3 Aufgaben weniger Konflikte, in 1 mehr, in 0 etwa gleich viele. "
                    "n = 43: 6 → 352 Konflikte (mehr, ×58,7); n = 44: 108 775 → 3 844 Konflikte (weniger, ×28,3); n = 45: 300 000+ → 109 523 Konflikte (weniger). "
                    "„+“ markiert einen Abbruch am Budget von 300 000 Konflikten (untere Schranke). Vorgerechnet (Vormessung, Python-CDCL, nicht live). "
                    "Standard-Löser ohne Zufall (Löser-Zufalls-Seed 0), Budget 300 000 Konflikte.")


def test_verdict_schur_alle_weniger_ist_erfolg_und_live_gekennzeichnet():
    kind, text = E.verdict_schur([z(148, 21, n=14, k=3), z(18, 11, n=13, k=3)], 3, 300000, False)
    assert kind == "success" and "in 2 von 2 Aufgaben weniger Konflikte, in 0 mehr" in text        # 148 → 21 (0,14) und 18 → 11 (0,61): beide unter 0,8 und über 10
    assert " Live gerechnet." in text


# ---------------------------------------------------------------- Reiter 4
def test_verdict_schadet_standardlauf_schlecht_seeds_nicht_belegt():
    ohne = [102, 77, 1034, 38, 139, 455, 197, 316, 174, 5306, 171, 102, 303, 717, 90, 577, 762, 314, 302, 782]
    mit = [1711, 1094, 609, 680, 1460, 169, 139, 229, 365, 204, 1203, 367, 764, 339, 395, 112, 418, 99, 351, 203]
    kind, text = E.verdict_schadet(43, 4, ohne, mit, standard=(6, 352))
    assert kind == "warning" and text.startswith("Verschlechterung im Standardlauf, über die Seeds nicht belegt: ")
    assert "Median 302,5 Konflikte ohne, 366 mit Wertevorrang (+21 %; Maximum 5 306 gegen 1 711)" in text
    assert "Der eine Standardlauf ohne Zufall (Löser-Zufalls-Seed 0) braucht 6 Konflikte ohne und 352 mit Wertevorrang." in text
    assert "mit der Brechung mehr Konflikte in 10 von 20 Läufen, weniger in 10" in text and "Rangsummentest (Mann-Whitney, zweiseitig): p = 0,204." in text


def test_verdict_schadet_klare_faelle_und_kontrolle():
    ohne = [100 + i for i in range(20)]
    schlecht = [x * 3 for x in ohne]
    kind, text = E.verdict_schadet(43, 4, ohne, schlecht)
    assert kind == "warning" and text.startswith("Verschlechterung über die Seeds: ") and "(+200 %" in text and "mehr Konflikte in 20 von 20 Läufen" in text
    kind, text = E.verdict_schadet(43, 4, schlecht, ohne, kontrolle=(ohne, ohne))
    assert kind == "success" and text.startswith("Weniger Konflikte über die Seeds: ")
    assert "Kontrolle mit 20 weiteren Seeds: Median 109,5 gegen 109,5 (±0 %, p = 1,000), mit der Brechung mehr Konflikte in 0 von 20 Läufen." in text
    kind, text = E.verdict_schadet(43, 4, ohne, ohne)
    assert kind == "info" and text.startswith("Kein Unterschied über die Seeds: ")
    kind, text = E.verdict_schadet(43, 4, ohne, [x + 5 for x in ohne], abbrueche_ohne=2, abbrueche_mit=1, budget=1000)
    assert "Abbrüche am Budget (1 000): 2 ohne, 1 mit Brechung." in text


def test_verdict_faerbung_vorzeichentest_je_graph():
    zelle = {"regeln": {"ohne": [31, 33, 33, 48, 49, 49, 68, 85, 94, 103], "kante_fest": [7, 11, 24, 29, 30, 31, 37, 38, 39, 75], "wertevorrang": [7, 21, 23, 29, 32, 33, 51, 54, 55, 120]},
             "abbrueche": {"ohne": 0, "kante_fest": 0, "wertevorrang": 0}, "antworten": ["unerfüllbar"] * 10}
    zf = E.zusammenfassung_faerbung(zelle, "kante_fest")
    assert zf["klasse"] == E.WENIGER and zf["laeufe_weniger"] == 10 and zf["laeufe_mehr"] == 0 and zf["unerfuellbar"] == 10
    kind, text = E.verdict_faerbung(90, "erste Kante fest", zf, 100000)
    assert kind == "success"
    assert text == ("Färbung mit n = 90 Aufträgen, 10 Graphen, davon 10 unerfüllbar, ein Lauf je Graph: Median 49 Konflikte ohne, 30,5 mit „erste Kante fest“ (−38 %; Maximum 103 gegen 75); "
                    "mit der Regel mehr Konflikte in 0 von 10 Graphen, weniger in 10, gleich viele in 0. Vorzeichentest (je Graph gepaart, exakt, zweiseitig): p = 0,002.")
    zw = E.zusammenfassung_faerbung(zelle, "wertevorrang")
    assert zw["laeufe_weniger"] == 9 and zw["laeufe_mehr"] == 1 and zw["klasse"] == E.WENIGER and E.p_text(zw["p"]) == "p = 0,021"


def test_verdict_zellen_zaehlt():
    klassen = {"a": E.WENIGER, "b": E.WENIGER, "c": E.MEHR, "d": E.GLEICH, "e": E.NICHT_BELEGT}
    kind, text = E.verdict_zellen(klassen)
    assert kind == "warning" and text == ("Über alle 5 Zellen (Median je Zelle, Standard-Löser, Rangsummen- beziehungsweise Vorzeichentest): in 2 von 5 Zellen belegt weniger Konflikte mit der Brechung, "
                                          "in 1 belegt mehr, in 1 etwa gleich viele, in 1 ein Unterschied jenseits des Bandes, aber nicht belegt.")
    assert E.verdict_zellen({"a": E.WENIGER})[0] == "info"


# ---------------------------------------------------------------- Reiter 1
def test_verdict_hand_schubfach_drei_faelle():
    ohne, mit = {"konflikt": False, "belegt": 0, "variablen": 6}, {"konflikt": True, "belegt": 6, "variablen": 6}
    kind, text = E.verdict_hand_schubfach(2, ohne, mit, 9, 3, 2, 1)
    assert kind == "success"
    assert text == ("Schubfach mit 3 Aufträgen auf 2 Rampen (9 Klauseln, dazu 3 Klauseln des Lochvorrangs): Ohne die Regel belegt die Einheitspropagation 0 von 6 Variablen und findet keinen Widerspruch. "
                    "Mit der Regel belegt sie 6 von 6 Variablen und endet in der leeren Klausel, ohne dass eine Entscheidung nötig ist. "
                    "Zum Vergleich die erfüllbare Fassung mit 2 Aufträgen: 2 Lösungen ohne, 1 mit der Regel.")
    kind, text = E.verdict_hand_schubfach(2, mit, mit, 9, 3)
    assert kind == "info" and "findet schon ohne die Regel den Widerspruch" in text
    kind, text = E.verdict_hand_schubfach(1, ohne, ohne, 3, 0)
    assert kind == "info" and "findet auch mit dem Lochvorrang keinen Widerspruch" in text


def test_verdict_hand_schur_n13_n14():
    erg = {"loesungen": 18, "mit_brechung": 3, "bahnen": 3, "bahngroessen": [6]}
    kind, text = E.verdict_hand_schur(13, 3, erg, 26)
    assert kind == "success"
    assert text == ("Schur mit 3 Mengen und den Zahlen 1 bis 13: 18 Lösungen, 3 davon erfüllen den Wertevorrang (26 zusätzliche Klauseln); die Lösungen bilden 3 Bahnen unter den Vertauschungen der Mengen. "
                    "Alle 3 Bahnen haben die Größe 3! = 6, also 18 / 6 = 3 Lösungen mit Wertevorrang.")
    kind, text = E.verdict_hand_schur(14, 3, {"loesungen": 0, "mit_brechung": 0, "bahnen": 0, "bahngroessen": []}, 28)
    assert kind == "info" and "keine Lösung, weder ohne noch mit Wertevorrang" in text and "28 Klauseln" in text


# ---------------------------------------------------------------- Kernfrage aus der Datei
def test_verdict_kern_aus_den_vorgerechneten_reihen():
    daten = {"schubfach": [{"h": 7, "ohne": {"antwort": "unerfüllbar", "konflikte": 4811}, "mit": {"antwort": "unerfüllbar", "konflikte": 1}},
                           {"h": 8, "ohne": {"antwort": "unerfüllbar", "konflikte": 27932}, "mit": {"antwort": "unerfüllbar", "konflikte": 1}}],
             "schur4": [{"n": 44, "k": 4, "ohne": {"antwort": "erfüllbar", "konflikte": 108775}, "mit": {"antwort": "erfüllbar", "konflikte": 3844}}]}
    kind, text = E.verdict_kern(daten)
    assert kind == "info"
    assert text.startswith("Schubfach, h = 7 bis 8: in 2 von 2 Aufgaben weniger Konflikte mit der Brechung (h = 8: 27 932 → 1). Schur mit 4 Mengen, n = 44 bis 44: weniger Konflikte in 1 von 1 Aufgaben, mehr in 0.")
