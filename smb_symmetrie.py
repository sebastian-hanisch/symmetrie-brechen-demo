"""Symmetriebrechung: zusätzliche Klauseln für Schur, Schubfach und Färbung, dazu Lösungszählung, Bahnen und Einheitspropagation.

Nicht Teil des Kern-Pakets der Linie, neu für dieses Stück. Jede Regel ist eine Liste **zusätzlicher** Klauseln; die Instanz bleibt unverändert,
`mit_brechung` hängt die Klauseln an. Alle Regeln erhalten die Erfüllbarkeit (Äquierfüllbarkeit), nicht die Menge der Lösungen.

Variablenschemata (aus `smb_instanzen.py`, hier nur gelesen):
  Schur      Variable (Zahl i = 1..n, Farbe c = 0..k-1) = (i - 1)·k + c + 1
  Schubfach  Variable (Taube p = 0..h, Loch l = 0..h-1) = p·h + l + 1
  Färbung    Variable (Knoten i = 0..n-1, Farbe c = 0..k-1) = i·k + c + 1   (ohne „höchstens eine Farbe“)

Regeln und Beweisskizzen der Äquierfüllbarkeit (jeweils: aus einer Lösung der Ausgangsformel entsteht durch Umbenennen eine Lösung mit der Regel;
umgekehrt ist jede Lösung mit der Regel eine Lösung der Ausgangsformel, weil nur Klauseln hinzukommen):
  Wertevorrang (Schur, Färbung)   Farbe c ≥ 1 darf nur vergeben werden, wenn schon eine frühere Zahl (Knoten) die Farbe c − 1 hat:
      ¬x(i, c) ∨ ⋁_{j < i} x(j, c − 1).  Umbenennung: Farben nach dem ersten Auftreten durchnummerieren; unbenutzte Farben kommen zuletzt.
  Lochvorrang (Schubfach)         Taube p darf Loch l ≥ 1 nur nehmen, wenn eine frühere Taube Loch l − 1 hat:
      ¬x(p, l) ∨ ⋁_{q < p} x(q, l − 1).  Umbenennung: besetzte Löcher nach der kleinsten Taube darin ordnen (jedes Loch hat höchstens eine Taube).
  Erste Kante fest (Färbung)      die Endpunkte a, b der ersten Kante bekommen die Farben 0 und 1: x(a, 0) und x(b, 1).  Umbenennung: eine Farbe von a und b
      zu 0 beziehungsweise 1 machen; a und b sind verschieden gefärbt, sonst wäre die Kante verletzt.
"""
import itertools
from math import factorial

from smb_instanzen import Instanz

REGEL_WERTEVORRANG = "wertevorrang"
REGEL_LOCHVORRANG = "lochvorrang"
REGEL_KANTE_FEST = "kante_fest"
REGELN = (REGEL_WERTEVORRANG, REGEL_LOCHVORRANG, REGEL_KANTE_FEST)


# ------------------------------------------------------------------ Variablen
def var_schur(i: int, c: int, k: int) -> int:
    return (i - 1) * k + c + 1


def var_schubfach(p: int, l: int, h: int) -> int:
    return p * h + l + 1


def var_faerbung(i: int, c: int, k: int) -> int:
    return i * k + c + 1


# ------------------------------------------------------------------ Regeln (zusätzliche Klauseln)
def wertevorrang_schur(n: int, k: int) -> list:
    """(k − 1)·n Klauseln: ¬x(i, c) ∨ x(1, c−1) ∨ … ∨ x(i−1, c−1) für i = 1..n, c = 1..k−1 (für i = 1 eine Einheitsklausel ¬x(1, c))."""
    return [tuple([-var_schur(i, c, k)] + [var_schur(j, c - 1, k) for j in range(1, i)]) for i in range(1, n + 1) for c in range(1, k)]


def wertevorrang_faerbung(n_knoten: int, k: int) -> list:
    """(k − 1)·n Klauseln wie beim Schur-Wertevorrang, Knoten 0..n−1 in der Reihenfolge der Nummern."""
    return [tuple([-var_faerbung(i, c, k)] + [var_faerbung(j, c - 1, k) for j in range(i)]) for i in range(n_knoten) for c in range(1, k)]


def lochvorrang(h: int, tauben: int | None = None) -> list:
    """(h − 1)·Tauben Klauseln: ¬x(p, l) ∨ x(0, l−1) ∨ … ∨ x(p−1, l−1) für p = 0..Tauben−1, l = 1..h−1 (Standard: h + 1 Tauben)."""
    t = h + 1 if tauben is None else tauben
    return [tuple([-var_schubfach(p, l, h)] + [var_schubfach(q, l - 1, h) for q in range(p)]) for p in range(t) for l in range(1, h)]


def kante_fest(kanten, k: int) -> list:
    """Zwei Einheitsklauseln für die erste Kante (a, b): Knoten a in Farbe 0, Knoten b in Farbe 1. Ohne Kanten (oder k < 2) gibt es nichts festzulegen."""
    kanten = list(kanten)
    if not kanten or k < 2:
        return []
    a, b = kanten[0]
    return [(var_faerbung(a, 0, k),), (var_faerbung(b, 1, k),)]


def zusatzklauseln(inst: Instanz, regel: str) -> list:
    """Die zusätzlichen Klauseln der Regel für diese Instanz (Fehler, wenn die Regel zur Art der Instanz nicht passt)."""
    art = inst.meta.get("art")
    if regel == REGEL_WERTEVORRANG and art == "schur":
        return wertevorrang_schur(inst.meta["n_zahlen"], inst.meta["k"])
    if regel == REGEL_WERTEVORRANG and art == "faerbung":
        return wertevorrang_faerbung(inst.meta["n_knoten"], inst.meta["k"])
    if regel == REGEL_LOCHVORRANG and art == "schubfach":
        return lochvorrang(inst.meta["h"], inst.meta.get("tauben"))
    if regel == REGEL_KANTE_FEST and art == "faerbung":
        return kante_fest(inst.meta["kanten"], inst.meta["k"])
    raise ValueError(f"Regel {regel!r} passt nicht zu einer Instanz der Art {art!r}")


def mit_brechung(inst: Instanz, regel: str) -> Instanz:
    """Dieselbe Aufgabe, Klauselliste um die Klauseln der Regel verlängert."""
    zusatz = zusatzklauseln(inst, regel)
    meta = dict(inst.meta)
    meta.update({"brechung": regel, "zusatzklauseln": len(zusatz)})
    return Instanz(inst.n, list(inst.klauseln) + zusatz, meta)


def schubfach(h: int, tauben: int | None = None) -> Instanz:
    """Schubfach mit `tauben` Tauben (Standard h + 1, unerfüllbar) auf h Löcher; Klauseln wie `smb_instanzen.pigeonhole`, Variable (p, l) = p·h + l + 1.
    Mit genau h Tauben ist die Aufgabe erfüllbar (h! Lösungen); `pigeonhole(h)` des Kerns kennt nur den unerfüllbaren Fall, dieser Erzeuger deckt beide ab."""
    t = h + 1 if tauben is None else tauben
    klauseln = [tuple(var_schubfach(p, l, h) for l in range(h)) for p in range(t)]
    for l in range(h):
        for p, q in itertools.combinations(range(t), 2):
            klauseln.append((-var_schubfach(p, l, h), -var_schubfach(q, l, h)))
    return Instanz(t * h, klauseln, {"art": "schubfach", "h": h, "tauben": t, "erfuellbar": t <= h})


# ------------------------------------------------------------------ Einheitspropagation (Schritt für Schritt)
def einheitspropagation(n: int, klauseln) -> dict:
    """Einheitspropagation auf Stufe 0, Klauseln in der Reihenfolge der Liste (erste passende zuerst).

    Rückgabe: `schritte` = [(Literal, Klauselindex)] in der Reihenfolge des Erzwingens, `konflikt` = Index der ersten verletzten Klausel oder None,
    `wert` = {Variable: bool} der belegten Variablen. Eigene Schleife, kein Code aus `smb_cdcl.py`."""
    wert, schritte = {}, []
    geaendert = True
    while geaendert:
        geaendert = False
        for ci, klausel in enumerate(klauseln):
            offen, erfuellt = [], False
            for lit in klausel:
                w = wert.get(abs(lit))
                if w is None:
                    offen.append(lit)
                elif w == (lit > 0):
                    erfuellt = True
                    break
            if erfuellt:
                continue
            if not offen:
                return {"schritte": schritte, "konflikt": ci, "wert": wert}
            if len(offen) == 1:
                lit = offen[0]
                wert[abs(lit)] = lit > 0
                schritte.append((lit, ci))
                geaendert = True
    return {"schritte": schritte, "konflikt": None, "wert": wert}


# ------------------------------------------------------------------ Lösungen zählen
def zaehle_loesungen(n: int, klauseln, behalte: int = 0, grenze: int | None = None):
    """Zählt alle Modelle der Formel (Variablen 1..n) durch Verzweigen mit Einheitspropagation; Rückgabe (Zahl, Liste der ersten `behalte` Modelle als
    Tupel von bool je Variable). Freie Variablen (in keiner offenen Klausel) zählen doppelt. Bricht bei `grenze` Modellen ab (dann ist die Zahl eine Untergrenze,
    `None` als dritter Wert, sonst `False`). Eigenes Verfahren, unabhängig vom CDCL."""
    klauseln = [tuple(dict.fromkeys(c)) for c in klauseln]
    zaehler, modelle, abgebrochen = [0], [], [False]

    def propagiere(wert):
        geaendert = True
        while geaendert:
            geaendert = False
            for c in klauseln:
                offen, erfuellt = [], False
                for lit in c:
                    w = wert[abs(lit)]
                    if w is None:
                        offen.append(lit)
                    elif w == (lit > 0):
                        erfuellt = True
                        break
                if erfuellt:
                    continue
                if not offen:
                    return False
                if len(offen) == 1:
                    wert[abs(offen[0])] = offen[0] > 0
                    geaendert = True
        return True

    def rec(wert):
        if abgebrochen[0]:
            return
        wert = list(wert)
        if not propagiere(wert):
            return
        # eine Variable aus einer noch nicht erfüllten Klausel verzweigen; gibt es keine, sind die übrigen frei
        wahl = None
        for c in klauseln:
            if any(wert[abs(l)] is not None and wert[abs(l)] == (l > 0) for l in c):
                continue
            wahl = next(abs(l) for l in c if wert[abs(l)] is None)
            break
        if wahl is None:
            frei = [v for v in range(1, n + 1) if wert[v] is None]
            for bits in itertools.product((False, True), repeat=len(frei)):
                if grenze is not None and zaehler[0] >= grenze:
                    abgebrochen[0] = True
                    return
                zaehler[0] += 1
                if len(modelle) < behalte:
                    voll = list(wert)
                    for v, b in zip(frei, bits):
                        voll[v] = b
                    modelle.append(tuple(voll[1:]))
            return
        for b in (False, True):
            w2 = list(wert)
            w2[wahl] = b
            rec(w2)

    rec([None] * (n + 1))
    return zaehler[0], modelle, abgebrochen[0]


def farben_je_zahl(modell, k: int, erste: int = 0) -> tuple:
    """Aus einem Modell (Tupel von bool, Variable 1 an Position 0) die Farbe je Zahl/Knoten (die einzige wahre Farbe; None, wenn keine oder mehrere)."""
    anzahl = len(modell) // k
    farben = []
    for i in range(anzahl):
        wahre = [c for c in range(k) if modell[i * k + c]]
        farben.append(wahre[0] if len(wahre) == 1 else None)
    return tuple(farben)


def kanonisch(farben) -> tuple:
    """Farben nach dem ersten Auftreten umbenannt (0, 1, 2, …): der Vertreter der Bahn unter allen Farbvertauschungen."""
    abbild = {}
    for c in farben:
        if c not in abbild:
            abbild[c] = len(abbild)
    return tuple(abbild[c] for c in farben)


def loesungen_und_bahnen(inst: Instanz, regel: str | None = None, behalte: int = 0) -> dict:
    """Zählt die Lösungen einer Schur-Instanz (oder einer Schubfach-Instanz mit ≤ h Tauben) ohne und mit Regel und die Bahnen der Farb-/Lochvertauschung.

    Rückgabe: `loesungen` (ohne Brechung), `mit_brechung` (mit der Regel; None ohne Regel), `bahnen` (Zahl der verschiedenen kanonischen Vertreter),
    `bahngroessen` (sortierte Menge der Bahngrößen), `vertreter_erfuellen_regel` (jede Lösung mit Regel ist kanonisch, jede kanonische Lösung erfüllt die Regel),
    `beispiele` (bis `behalte` Lösungen mit Regel als Farbtupel)."""
    art = inst.meta["art"]
    if art == "schur":
        k, einheiten = inst.meta["k"], inst.meta["n_zahlen"]
    elif art == "schubfach":
        k, einheiten = inst.meta["h"], inst.meta.get("tauben", inst.meta["h"] + 1)
    else:
        raise ValueError("Zählen geht nur für Schur und Schubfach (die Färbung hat kein „höchstens eine Farbe“)")
    alle_n, alle, _ = zaehle_loesungen(inst.n, _mit_hoechstens_eins(inst), behalte=10 ** 9)
    if art == "schur":
        ds = [farben_je_zahl(m, k) for m in alle]
    else:
        ds = [_loecher_je_taube(m, k, einheiten) for m in alle]
    bahnen = {}
    for d in ds:
        bahnen.setdefault(kanonisch(d), []).append(d)
    ergebnis = {"loesungen": alle_n, "bahnen": len(bahnen), "bahngroessen": sorted({len(v) for v in bahnen.values()}), "mit_brechung": None,
                "vertreter_erfuellen_regel": None, "beispiele": []}
    if regel is not None:
        zusatz = zusatzklauseln(inst, regel)
        n2, m2, _ = zaehle_loesungen(inst.n, _mit_hoechstens_eins(inst) + zusatz, behalte=10 ** 9)
        ds2 = [farben_je_zahl(m, k) if art == "schur" else _loecher_je_taube(m, k, einheiten) for m in m2]
        ergebnis["mit_brechung"] = n2
        ergebnis["vertreter_erfuellen_regel"] = set(ds2) == set(bahnen) and len(ds2) == len(bahnen)
        ergebnis["beispiele"] = ds2[:behalte]
    return ergebnis


def _mit_hoechstens_eins(inst: Instanz) -> list:
    """Schur-Klauseln enthalten „höchstens eine Farbe“ schon; für das Schubfach zählen wir Zuordnungen mit genau einem Loch je Taube
    (zusätzlich „höchstens ein Loch“), damit Lösungen = Abbildungen Tauben → Löcher sind."""
    klauseln = list(inst.klauseln)
    if inst.meta["art"] == "schubfach":
        h, t = inst.meta["h"], inst.meta.get("tauben", inst.meta["h"] + 1)
        for p in range(t):
            for l1, l2 in itertools.combinations(range(h), 2):
                klauseln.append((-var_schubfach(p, l1, h), -var_schubfach(p, l2, h)))
    return klauseln


def _loecher_je_taube(modell, h: int, tauben: int) -> tuple:
    return tuple(next((l for l in range(h) if modell[p * h + l]), None) for p in range(tauben))


def bahnengroesse(k: int) -> int:
    """k! (Größe einer Bahn, wenn mindestens k − 1 Farben benutzt sind)."""
    return factorial(k)
