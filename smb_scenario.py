"""Szenario: die Aufgaben der Demo (Schubfach, Schur, Aufträge auf Rampen als 3-Färbung).

Alle Zufallsaufgaben stammen aus dem SplitMix64 (`smb_rng.py`) über `smb_instanzen.py`; gleiche Angaben geben dieselbe Aufgabe.
Literale sind ganze Zahlen (+v wahr, -v falsch).
"""

import smb_constants as C
import smb_instanzen as I
import smb_symmetrie as SY
from smb_instanzen import Instanz


def schur_aufgabe(n: int, k: int) -> Instanz:
    return I.schur(n, k)


def schubfach_aufgabe(h: int, tauben: int | None = None) -> Instanz:
    """h + 1 paarweise unverträgliche Aufträge auf h Rampen (unerfüllbar); mit `tauben = h` die erfüllbare Variante."""
    return SY.schubfach(h, tauben)


def faerbung_aufgabe(n: int, seed: int) -> Instanz:
    """n Aufträge, mittlerer Grad 5 im Konfliktgraphen, 3 Rampen."""
    return I.rampen_instanz(n, C.FAERBUNG_GRAD, seed, C.RAMPEN)


def faerbung_graphen(n: int, seed0: int, anzahl: int = C.FAERBUNG_GRAPHEN) -> list:
    """Die Graphen einer Zelle: Seeds seed0 bis seed0 + anzahl - 1."""
    return [faerbung_aufgabe(n, seed0 + i) for i in range(anzahl)]


def beschreibung(inst: Instanz) -> str:
    """Eine Zeile zur Aufgabe für die Anzeige."""
    meta = inst.meta
    art = meta.get("art")
    if art == "schur":
        return (f"Schur: die Zahlen 1 bis {meta['n_zahlen']} auf {meta['k']} Mengen ohne a + b = c in einer Menge (a = b erlaubt); "
                f"{inst.n} Variablen, {len(inst.klauseln)} Klauseln")
    if art == "schubfach":
        h = meta["h"]
        t = meta.get("tauben", h + 1)
        return f"Schubfach: {t} paarweise unverträgliche Aufträge auf {h} Rampen; {inst.n} Variablen, {len(inst.klauseln)} Klauseln"
    if art == "faerbung":
        return (f"{meta['n_knoten']} Aufträge auf {meta['k']} Rampen, {len(meta['kanten'])} Konflikte (mittlerer Grad {str(meta['grad']).replace('.', ',')}); "
                f"{inst.n} Variablen, {len(inst.klauseln)} Klauseln")
    return f"{inst.n} Variablen, {len(inst.klauseln)} Klauseln"


def literal_text(lit: int, art: str = "", parameter: int = 0) -> str:
    """Literal als Text. Schubfach (`parameter` = h): x(Auftrag, Rampe); Schur (`parameter` = k): x(Zahl, Menge); sonst x<Nummer>."""
    v = abs(lit)
    if art == "schubfach":
        name = f"x({(v - 1) // parameter},{(v - 1) % parameter})"
    elif art == "schur":
        name = f"x({(v - 1) // parameter + 1},{(v - 1) % parameter})"
    else:
        name = f"x{v}"
    return name if lit > 0 else "¬" + name


def klausel_text(klausel, art: str = "", parameter: int = 0) -> str:
    return " ∨ ".join(literal_text(l, art, parameter) for l in klausel) if klausel else "(leer)"
