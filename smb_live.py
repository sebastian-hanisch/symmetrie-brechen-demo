"""Live-Knöpfe: Zwischenspeicher und Fortschrittsanzeige.

Jede lange Aktion (Schubfach-Reihe, Löser-Zufalls-Seeds) besteht aus Einheiten (eine Zeile der Reihe, ein Lauf mit einem Seed). Jede Einheit ist eine reine Funktion ihrer
Parameter (die Aufgaben sind deterministisch, SplitMix64; der Löser-Zufalls-Seed steckt im Schlüssel) und liegt einzeln im Zwischenspeicher (`st.cache_data`, kleine
`max_entries`); die Anzeige zählt die fertigen Einheiten (`mit_fortschritt`). Ein zweiter Klick mit denselben Einstellungen antwortet aus dem Speicher; die Zeilen h = 3 bis 6
teilt sich eine Reihe bis h = 7 mit einer kürzeren. Die Ergebnisse sind bitgleich zu den ungespeicherten Funktionen (`tests/test_live.py`). Rechnung, Zahlen und Aussagen ändern
sich nicht; die Rechenzeit einer Einheit steht nur zur Anzeige im Ergebnis."""

import time

import streamlit as st

import smb_algorithm as A
import smb_constants as C
import smb_evaluation as E
import smb_instanzen as I
import smb_symmetrie as SY


def _dict(m):
    """Messung als Dictionary im Format der vorgerechneten Datei."""
    return {"antwort": m.antwort_text, "konflikte": m.konflikte}


def schubfach_einheit_ungespeichert(h: int, budget: int):
    """(Tabellenzeile, Rechenzeit in Sekunden) für ein h; die Zeit dient nur der Anzeige."""
    t0 = time.perf_counter()
    z = A.schubfach_zeile(h, budget)
    return E.zeile_aus(_dict(z["ohne"]), _dict(z["mit"]), h=z["h"]), time.perf_counter() - t0


@st.cache_data(show_spinner=False, max_entries=16)
def schubfach_einheit(h, budget):
    return schubfach_einheit_ungespeichert(h, budget)


def seed_einheit_ungespeichert(n: int, mit: bool, seed: int, budget: int):
    """(Konflikte, Antwort, Rechenzeit in Sekunden) eines Laufs der Schur-Aufgabe (k = `C.SCHADET_K`) mit Löser-Zufalls-Seed, ohne oder mit Wertevorrang."""
    t0 = time.perf_counter()
    konflikte, antwort = A.seed_lauf(I.schur(n, C.SCHADET_K), SY.REGEL_WERTEVORRANG if mit else None, seed, budget)
    return konflikte, antwort, time.perf_counter() - t0


@st.cache_data(show_spinner=False, max_entries=96)
def seed_einheit(n, mit, seed, budget):
    return seed_einheit_ungespeichert(n, mit, seed, budget)


def mit_fortschritt(titel: str, schritte: list, rechne) -> list:
    """Führt die Schritte nacheinander aus und zeigt, wie viele fertig sind. `schritte`: Liste aus (Beschriftung, Argumente); `rechne(*Argumente)` liefert das Ergebnis
    (aus dem Zwischenspeicher oder frisch gerechnet). Rückgabe: die Ergebnisse in der Reihenfolge der Schritte."""
    n = len(schritte)
    ergebnisse = []
    with st.status(titel, expanded=True) as status:
        balken = st.progress(0.0, text=f"0 von {n} fertig")
        for i, (beschriftung, args) in enumerate(schritte):
            balken.progress(i / n, text=f"{beschriftung} (Schritt {i + 1} von {n})")
            ergebnisse.append(rechne(*args))
        balken.progress(1.0, text=f"{n} von {n} fertig")
        status.update(label=f"{titel}: fertig", state="complete", expanded=False)
    return ergebnisse


def schubfach_zusammen(einheiten: list):
    """(Zeilen, Rechenzeit) aus den Einheiten."""
    return [z for z, _ in einheiten], sum(sek for _, sek in einheiten)


def schubfach(h_bis: int, budget: int):
    """Die Reihe h = 3 bis `h_bis` mit Fortschrittsanzeige (je h ein Schritt). Rückgabe: (Zeilen, Rechenzeit der Anzeige)."""
    schritte = [(f"h = {h}, ohne und mit Lochvorrang", (h, budget)) for h in range(C.H_REIHE_MIN, h_bis + 1)]
    return schubfach_zusammen(mit_fortschritt(f"Rechne h = {C.H_REIHE_MIN} bis {h_bis}, je ohne und mit Lochvorrang, bis zu {E.zahl(budget)} Konflikte je Lauf", schritte, schubfach_einheit))


def schubfach_aus_speicher(h_bis: int, budget: int):
    """Wie `schubfach`, ohne Anzeige (aus dem Zwischenspeicher; rechnet nur, was dort fehlt)."""
    return schubfach_zusammen([schubfach_einheit(h, budget) for h in range(C.H_REIHE_MIN, h_bis + 1)])


def schadet_zusammen(n: int, ohne: list, mit: list):
    """Das Ergebnis des Live-Laufs in der Form, die die App anzeigt: ({"ohne", "mit"}, Rechenzeit)."""
    out = {}
    for name, einheiten in (("ohne", ohne), ("mit", mit)):
        konflikte, antworten, abbrueche = A.seeds_zusammen((k, a) for k, a, _ in einheiten)
        out[name] = {"konflikte": konflikte, "abbrueche": abbrueche, "antworten": sorted(str(a) for a in antworten)}
    return out, sum(sek for _, _, sek in ohne + mit)


def schadet(n: int, seeds: int, budget: int):
    """Die Läufe mit den Löser-Zufalls-Seeds 1 bis `seeds`, je ohne und mit Wertevorrang, mit Fortschrittsanzeige (je Lauf ein Schritt)."""
    schritte = [(f"Seed {s}, {'mit Wertevorrang' if mit else 'ohne Regel'}", (n, mit, s, budget)) for mit in (False, True) for s in range(1, seeds + 1)]
    ergebnisse = mit_fortschritt(f"Rechne 2 × {seeds} Läufe, je bis zu {E.zahl(budget)} Konflikte", schritte, seed_einheit)
    return schadet_zusammen(n, ergebnisse[:seeds], ergebnisse[seeds:])


def schadet_aus_speicher(n: int, seeds: int, budget: int):
    """Wie `schadet`, ohne Anzeige."""
    ohne = [seed_einheit(n, False, s, budget) for s in range(1, seeds + 1)]
    mit = [seed_einheit(n, True, s, budget) for s in range(1, seeds + 1)]
    return schadet_zusammen(n, ohne, mit)
