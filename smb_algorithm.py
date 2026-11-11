"""Läufe des CDCL ohne und mit Symmetriebrechung und die Messreihen der Reiter.

Der Löser ist die Kopie des Kern-Pakets (`smb_cdcl.py`: 1-UIP, Aktivität, Phasenspeicher, Luby-Neustarts mit Einheit 32, Watched Literals).
Aufwand wird in Konflikten, Entscheidungen und Propagationen gezählt, nie in Sekunden.

Ein Löser-Zufalls-Seed wirkt nur mit `noise=True` (zufälliger Start der Aktivitäten, SplitMix64); ohne `noise` sind alle Seeds derselbe Lauf. `lauf_seed` rechnet deshalb
immer mit `noise=True`, der Seed-lose Standardlauf (Seed 0) mit `noise=False`.
"""

import statistics
from dataclasses import dataclass

import smb_instanzen as I
import smb_symmetrie as SY
from smb_cdcl import Ergebnis, solve
from smb_instanzen import Instanz

REGEL_OHNE = None
ANTWORT_TEXT = {True: "erfüllbar", False: "unerfüllbar", None: "Abbruch"}


@dataclass(frozen=True)
class Messung:
    antwort: bool | None
    konflikte: int
    entscheidungen: int
    propagationen: int
    gelernt: int

    @property
    def antwort_text(self) -> str:
        return {True: "erfüllbar", False: "unerfüllbar", None: "Abbruch am Budget"}[self.antwort]


def messung(erg: Ergebnis) -> Messung:
    s = erg.stat
    return Messung(erg.antwort, s["konflikte"], s["entscheidungen"], s["propagationen"], s["gelernt"])


def lauf(inst: Instanz, regel: str | None = REGEL_OHNE, *, budget: int | None = None, seed: int = 0, noise: bool = False, trace: bool = False) -> Ergebnis:
    """Ein Lauf des CDCL auf der Aufgabe, mit der Regel (sonst ohne). Ein erfüllendes Modell wird gegen die Klauseln der **Ausgangs**aufgabe geprüft."""
    aufgabe = inst if regel is None else SY.mit_brechung(inst, regel)
    erg = solve(aufgabe.n, aufgabe.klauseln, conflict_budget=budget, seed=seed, noise=noise, trace=trace)
    if erg.antwort is True and not I.pruefe_modell(inst.klauseln, erg.modell):
        raise RuntimeError("das Modell des Lösers verletzt eine Klausel der Aufgabe")
    return erg


def lauf_seed(inst: Instanz, regel: str | None, seed: int, budget: int | None) -> Ergebnis:
    """Ein Lauf mit Löser-Zufalls-Seed (zufälliger Start der Aktivitäten, `noise=True`)."""
    return lauf(inst, regel, budget=budget, seed=seed, noise=True)


def konflikte_je_seed(inst: Instanz, regel: str | None, seeds, budget: int | None) -> tuple:
    """(Konflikte je Seed als Liste, Menge der Antworten ohne Abbruch, Zahl der Abbrüche). Abbrüche zählen mit dem Budget."""
    konflikte, antworten, abbrueche = [], set(), 0
    for s in seeds:
        erg = lauf_seed(inst, regel, s, budget)
        konflikte.append(erg.stat["konflikte"])
        if erg.antwort is None:
            abbrueche += 1
        else:
            antworten.add(erg.antwort)
    return konflikte, antworten, abbrueche


def regel_der_aufgabe(inst: Instanz) -> str:
    """Die Regel, die zur Aufgabe passt (Wertevorrang für Schur, Lochvorrang für Schubfach; Färbung: erste Kante fest)."""
    return {"schur": SY.REGEL_WERTEVORRANG, "schubfach": SY.REGEL_LOCHVORRANG, "faerbung": SY.REGEL_KANTE_FEST}[inst.meta["art"]]


def wurzel(inst: Instanz, regel: str | None = None) -> dict:
    """Einheitspropagation auf Stufe 0 (eigene Schleife): Konflikt, Zahl belegter Variablen, Schritte."""
    aufgabe = inst if regel is None else SY.mit_brechung(inst, regel)
    r = SY.einheitspropagation(aufgabe.n, aufgabe.klauseln)
    return {"konflikt": r["konflikt"], "belegt": len(r["wert"]), "variablen": aufgabe.n, "schritte": r["schritte"], "klauseln": aufgabe.klauseln}


def schubfach_reihe(h_von: int, h_bis: int, budget: int) -> list:
    """Je h von h_von bis h_bis: Konflikte des Standardlaufs ohne und mit Lochvorrang auf h + 1 Aufträgen und h Rampen. [{h, ohne, mit}] (Messung-Objekte)."""
    zeilen = []
    for h in range(h_von, h_bis + 1):
        inst = SY.schubfach(h)
        zeilen.append({"h": h, "ohne": messung(lauf(inst, None, budget=budget)), "mit": messung(lauf(inst, SY.REGEL_LOCHVORRANG, budget=budget))})
    return zeilen


def schur_reihe(ns, k: int, budget: int) -> list:
    """Je n: Konflikte des Standardlaufs ohne und mit Wertevorrang auf Schur (k Mengen). [{n, ohne, mit}]."""
    zeilen = []
    for n in ns:
        inst = I.schur(n, k)
        zeilen.append({"n": n, "ohne": messung(lauf(inst, None, budget=budget)), "mit": messung(lauf(inst, SY.REGEL_WERTEVORRANG, budget=budget))})
    return zeilen


def faerbung_zelle(n: int, seed0: int, budget: int, regeln=(None, SY.REGEL_KANTE_FEST, SY.REGEL_WERTEVORRANG), anzahl: int = 10) -> dict:
    """Eine Zelle der Färbung (n Aufträge, Grad 5, 3 Rampen, `anzahl` Graphen mit den Seeds seed0 …): je Regel die Konflikte je Graph (Standardlauf, Seed 0)
    und die Antworten. Die Antworten müssen für alle Regeln gleich sein (Äquierfüllbarkeit)."""
    from smb_scenario import faerbung_graphen
    graphen = faerbung_graphen(n, seed0, anzahl)
    zeile = {"n": n, "seed0": seed0, "anzahl": anzahl, "regeln": {}}
    antworten_je_regel = {}
    for regel in regeln:
        konf, ant = [], []
        for g in graphen:
            m = messung(lauf(g, regel, budget=budget))
            konf.append(m.konflikte)
            ant.append(m.antwort)
        name = regel or "ohne"
        zeile["regeln"][name] = konf
        antworten_je_regel[name] = ant
    zeile["antworten"] = [ANTWORT_TEXT[a] for a in antworten_je_regel["ohne"]]
    zeile["antworten_gleich"] = all(antworten_vertraeglich(antworten_je_regel["ohne"], ant) for ant in antworten_je_regel.values())
    zeile["abbrueche"] = {name: sum(1 for a in ant if a is None) for name, ant in antworten_je_regel.items()}
    return zeile


def antworten_vertraeglich(a, b) -> bool:
    """Zwei Antwortlisten (True/False/None je Aufgabe) widersprechen sich nirgends: wo beide eine Antwort haben, ist sie gleich (None = Abbruch, keine Antwort)."""
    return all(x == y for x, y in zip(a, b) if x is not None and y is not None)


# ------------------------------------------------------------------ Statistik
def median(werte) -> float:
    return statistics.median(werte)
