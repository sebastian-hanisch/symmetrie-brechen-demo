"""Orakel-Tests der Symmetriebrechung (ORACLE-PLAYBOOK §5, DEMO-PLAYBOOK §12): jede Kernroutine gegen einen anderen Rechenweg.

1. Lösungszählung (`smb_symmetrie.zaehle_loesungen`) und Zählung mit Regel gegen die Rückverfolgung über Färbungen (ohne Klauseln, Handbeispiel hb_09), Schur k = 2, 3.
2. Bahnen gegen explizite Anwendung aller k! Farbvertauschungen (statt der kanonischen Umbenennung des Codes).
3. Antwort des CDCL mit und ohne Regel gegen die Aufzählung (Schur), gegen alle 2^n Belegungen (Schubfach h ≤ 3), gegen alle k^n Färbungen (zufällige Graphen).
4. OR-Tools CP-SAT mit **ganzzahligen Variablen** (keine Klauseln, keine Variablen x(i, c)): Schur, Färbung, Schubfach, jeweils mit und ohne Regel als ganzzahlige Nebenbedingung
   (Farbe von i höchstens Maximum der früheren plus 1); Lösungszählung und Erfüllbarkeit (`importorskip`; im Scratch-Lauf auf mehr als 200 Instanzen, im Repo 32: 12 Schur, 14 Färbung, 6 Schubfach).
5. Modellprüfung jeder erfüllbaren Antwort aus der Definition (a + b = c, Wertevorrang), nicht aus den Klauseln.
6. Einheitspropagation (eigene Schleife) gegen die Propagation des Lösers auf Stufe 0.
7. Angezeigte Kennzahlen: Klauselzahlen der Aufgaben gegen eine Formel, Schur-Zahlen S(1) = 1, S(2) = 4, S(3) = 13 durch Aufzählung (S(4) = 44 nur als zitierter Wert).
Der große Lauf (mehr als 200 Zufallsinstanzen) steht nicht im Repo, nur diese schnelle Fassung."""

import itertools
from math import comb

import pytest

import smb_algorithm as A
import smb_instanzen as I
import smb_symmetrie as SY
from conftest import alle_belegungen_erfuellend, schur_gueltig, schur_loesungen_rueckverfolgung, wertevorrang_ok
from smb_cdcl import Loeser, solve
from smb_rng import SplitMix64


# ---------------------------------------------------------------- 1. Lösungen zählen
@pytest.mark.parametrize("k, n_max", [(2, 6), (3, 14)])
def test_loesungszaehlung_gegen_rueckverfolgung(k, n_max):
    for n in range(1, n_max + 1):
        erwartet = schur_loesungen_rueckverfolgung(n, k)
        erg = SY.loesungen_und_bahnen(I.schur(n, k), SY.REGEL_WERTEVORRANG)
        assert erg["loesungen"] == len(erwartet), (n, k)
        assert erg["mit_brechung"] == sum(1 for f in erwartet if wertevorrang_ok(f)), (n, k)


def test_modellmenge_gleich_der_rueckverfolgung_n13():
    inst = I.schur(13, 3)
    anzahl, modelle, _ = SY.zaehle_loesungen(inst.n, inst.klauseln, behalte=10 ** 6)
    mein = {SY.farben_je_zahl(m, 3) for m in modelle}
    assert anzahl == len(modelle) == len(mein) == 18
    assert mein == set(schur_loesungen_rueckverfolgung(13, 3))


def test_zaehler_gegen_alle_belegungen_kleine_formeln():
    rng = SplitMix64(11)
    for _ in range(40):
        n = 4 + rng.below(5)
        klauseln = I.rand3(n, 2 + rng.below(14), rng.next() & 0xFFFF).klauseln
        assert SY.zaehle_loesungen(n, klauseln)[0] == len(alle_belegungen_erfuellend(n, klauseln))


# ---------------------------------------------------------------- 2. Bahnen
@pytest.mark.parametrize("n", [5, 8, 11, 12, 13])
def test_bahnen_gegen_explizite_permutationen(n):
    k = 3
    loesungen = schur_loesungen_rueckverfolgung(n, k)
    menge, bahnen = set(loesungen), []
    gesehen = set()
    for f in loesungen:
        if f in gesehen:
            continue
        bahn = {tuple(p[c] for c in f) for p in itertools.permutations(range(k))}
        assert bahn <= menge                                  # eine Farbvertauschung einer Lösung ist wieder eine Lösung
        gesehen |= bahn
        bahnen.append(bahn)
    erg = SY.loesungen_und_bahnen(I.schur(n, k), SY.REGEL_WERTEVORRANG)
    assert erg["bahnen"] == len(bahnen) == erg["mit_brechung"]
    assert erg["bahngroessen"] == sorted({len(b) for b in bahnen})
    # genau ein Vertreter je Bahn erfüllt den Wertevorrang
    assert all(sum(1 for f in b if wertevorrang_ok(f)) == 1 for b in bahnen)


# ---------------------------------------------------------------- 3. Antwort des CDCL
@pytest.mark.parametrize("k, n_max", [(1, 4), (2, 7), (3, 16)])
def test_cdcl_antwort_schur_gegen_aufzaehlung_mit_und_ohne_regel(k, n_max):
    for n in range(1, n_max + 1):
        erwartet = bool(schur_loesungen_rueckverfolgung(n, k))
        for regel in (None, SY.REGEL_WERTEVORRANG):
            erg = A.lauf(I.schur(n, k), regel)
            assert erg.antwort is erwartet, (n, k, regel)
            if erwartet:
                f = SY.farben_je_zahl(tuple(erg.modell[v] for v in range(1, n * k + 1)), k)
                assert None not in f and schur_gueltig(f)                       # aus der Definition geprüft
                assert regel is None or wertevorrang_ok(f)


@pytest.mark.parametrize("h", [1, 2, 3])
@pytest.mark.parametrize("tauben", ["h", "h+1"])
def test_cdcl_schubfach_gegen_alle_belegungen(h, tauben):
    t = h if tauben == "h" else h + 1
    inst = SY.schubfach(h, t)
    erwartet = bool(alle_belegungen_erfuellend(inst.n, inst.klauseln))
    assert erwartet is (t <= h)
    for regel in (None, SY.REGEL_LOCHVORRANG):
        assert A.lauf(inst, regel).antwort is erwartet
        mit = SY.mit_brechung(inst, regel) if regel else inst
        assert bool(alle_belegungen_erfuellend(mit.n, mit.klauseln)) is erwartet     # auch die Aufzählung bestätigt: Erfüllbarkeit bleibt


def _zufallsgraph(rng, n, kanten):
    paare = [(a, b) for a in range(n) for b in range(a + 1, n)]
    rng.shuffle(paare)
    return sorted(paare[:kanten])


def _faerbbar(n, kanten, k=3):
    """Alle k^n Färbungen (unabhängig von Klauseln)."""
    return any(all(f[a] != f[b] for a, b in kanten) for f in itertools.product(range(k), repeat=n))


def test_cdcl_faerbung_gegen_alle_faerbungen_mit_und_ohne_regeln():
    rng = SplitMix64(21)
    gesehen = set()
    for _ in range(50):
        n = 4 + rng.below(4)                                   # 4 bis 7 Knoten
        kanten = _zufallsgraph(rng, n, rng.below(min(15, n * (n - 1) // 2) + 1))
        erwartet = _faerbbar(n, kanten)
        gesehen.add(erwartet)
        inst = I.faerbung(n, kanten, 3)
        for regel in (None, SY.REGEL_KANTE_FEST, SY.REGEL_WERTEVORRANG):
            assert A.lauf(inst, regel).antwort is erwartet, (n, kanten, regel)
    assert gesehen == {True, False}                            # die Stichprobe enthält erfüllbare und unerfüllbare Aufgaben


# ---------------------------------------------------------------- 4. OR-Tools CP-SAT mit ganzzahligen Variablen
def _cp():
    return pytest.importorskip("ortools.sat.python.cp_model")


def _zaehle(cp_model, modell):
    class Zaehler(cp_model.CpSolverSolutionCallback):
        def __init__(self):
            super().__init__()
            self.anzahl = 0

        def on_solution_callback(self):
            self.anzahl += 1

    loeser = cp_model.CpSolver()
    loeser.parameters.enumerate_all_solutions = True
    loeser.parameters.num_workers = 1
    z = Zaehler()
    loeser.Solve(modell, z)
    return z.anzahl


def _cp_schur(cp_model, n, k, regel):
    m = cp_model.CpModel()
    f = {i: m.NewIntVar(0, k - 1, f"f{i}") for i in range(1, n + 1)}
    for a in range(1, n + 1):
        for b in range(a, n + 1):
            if a + b <= n:
                c = a + b                                   # verboten: f(a) = f(b) = f(c) (für a = b nur f(a) = f(c))
                if a == b:
                    m.AddForbiddenAssignments([f[a], f[c]], [(v, v) for v in range(k)])
                else:
                    m.AddForbiddenAssignments([f[a], f[b], f[c]], [(v, v, v) for v in range(k)])
    if regel:                                               # Wertevorrang als ganzzahlige Nebenbedingung: f(i) ≤ (Maximum der früheren) + 1, f(1) = 0
        m.Add(f[1] == 0)
        letzt = f[1]
        for i in range(2, n + 1):
            m.Add(f[i] <= letzt + 1)
            mx = m.NewIntVar(0, k - 1, f"mx{i}")
            m.AddMaxEquality(mx, [letzt, f[i]])
            letzt = mx
    return m


def test_cpsat_zaehlt_dieselben_loesungen_schur3():
    cp_model = _cp()
    for n in (12, 13, 14):
        erwartet = SY.loesungen_und_bahnen(I.schur(n, 3), SY.REGEL_WERTEVORRANG)
        assert _zaehle(cp_model, _cp_schur(cp_model, n, 3, False)) == erwartet["loesungen"], n
        assert _zaehle(cp_model, _cp_schur(cp_model, n, 3, True)) == erwartet["mit_brechung"], n


def test_cpsat_erfuellbarkeit_schur_mit_und_ohne_regel_12_instanzen():
    cp_model = _cp()
    faelle = [(n, k) for k in (2, 3, 4) for n in {2: (3, 4, 5, 6), 3: (10, 12, 13, 14, 15), 4: (20, 30, 38)}[k]]
    assert len(faelle) == 12
    for n, k in faelle:
        status = cp_model.CpSolver().Solve(_cp_schur(cp_model, n, k, False))
        erwartet = status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
        for regel in (None, SY.REGEL_WERTEVORRANG):
            assert A.lauf(I.schur(n, k), regel, budget=20000).antwort is erwartet, (n, k, regel)


def test_cpsat_faerbung_und_schubfach_erfuellbarkeit():
    cp_model = _cp()
    rng = SplitMix64(5)
    n_faelle = 0
    for _ in range(14):                                            # 14 Graphen mit 8 bis 11 Knoten, Kantenzahl so, dass beide Antworten vorkommen
        n = 8 + rng.below(4)
        kanten = _zufallsgraph(rng, n, n + rng.below(2 * n))
        m = cp_model.CpModel()
        c = [m.NewIntVar(0, 2, f"c{i}") for i in range(n)]
        for a, b in kanten:
            m.Add(c[a] != c[b])
        status = cp_model.CpSolver().Solve(m)
        erwartet = status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
        inst = I.faerbung(n, kanten, 3)
        for regel in (None, SY.REGEL_KANTE_FEST, SY.REGEL_WERTEVORRANG):
            assert A.lauf(inst, regel).antwort is erwartet, (n, kanten, regel)
        n_faelle += 1
    assert n_faelle == 14
    for h in (2, 3, 4):                                            # Schubfach: AllDifferent der Löcher, h + 1 Aufträge unmöglich, h Aufträge h! Zuordnungen
        for t in (h, h + 1):
            m = cp_model.CpModel()
            loch = [m.NewIntVar(0, h - 1, f"l{p}") for p in range(t)]
            m.AddAllDifferent(loch)
            status = cp_model.CpSolver().Solve(m)
            erwartet = status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
            assert erwartet is (t <= h)
            for regel in (None, SY.REGEL_LOCHVORRANG):
                assert A.lauf(SY.schubfach(h, t), regel).antwort is erwartet
    # Lochvorrang als ganzzahlige Nebenbedingung (Loch von Auftrag p höchstens Maximum der früheren + 1) lässt genau eine der h! Zuordnungen übrig
    h = 4
    m = cp_model.CpModel()
    loch = [m.NewIntVar(0, h - 1, f"l{p}") for p in range(h)]
    m.AddAllDifferent(loch)
    m.Add(loch[0] == 0)
    letzt = loch[0]
    for p in range(1, h):
        m.Add(loch[p] <= letzt + 1)
        mx = m.NewIntVar(0, h - 1, f"mx{p}")
        m.AddMaxEquality(mx, [letzt, loch[p]])
        letzt = mx
    assert _zaehle(cp_model, m) == 1 == SY.loesungen_und_bahnen(SY.schubfach(h, h), SY.REGEL_LOCHVORRANG)["mit_brechung"]


# ---------------------------------------------------------------- 6. Einheitspropagation gegen den Löser
def _wurzel_des_loesers(n, klauseln):
    s = Loeser(n, klauseln)
    if not s.ok:
        return True, None
    k = s.propagiere()
    return k is not None, len(s.spur_lit)


def test_einheitspropagation_gegen_loeser_stufe_0():
    faelle = [SY.mit_brechung(SY.schubfach(h), SY.REGEL_LOCHVORRANG) for h in (2, 3, 4, 5)] + [SY.schubfach(h) for h in (2, 3)]
    faelle += [SY.mit_brechung(I.schur(n, 3), SY.REGEL_WERTEVORRANG) for n in (5, 13, 14)] + [I.schur(8, 3)]
    faelle += [SY.mit_brechung(I.rampen_instanz(20, 4.0, s, 3), SY.REGEL_KANTE_FEST) for s in (1, 2)]
    for inst in faelle:
        eigene = SY.einheitspropagation(inst.n, inst.klauseln)
        konflikt, belegt = _wurzel_des_loesers(inst.n, inst.klauseln)
        assert (eigene["konflikt"] is not None) == konflikt, inst.meta
        if not konflikt:
            assert len(eigene["wert"]) == belegt                      # dieselbe Menge belegter Variablen (Fixpunkt)


# ---------------------------------------------------------------- 7. Angezeigte Kennzahlen
def _schur_klauselzahl(n, k):
    tripel = sum(1 for a in range(1, n + 1) for b in range(a, n + 1) if a + b <= n)
    return n + n * comb(k, 2) + k * tripel


def test_klauselzahlen_der_aufgaben_gegen_formel():
    for n, k in ((5, 2), (13, 3), (14, 3), (43, 4)):
        assert len(I.schur(n, k).klauseln) == _schur_klauselzahl(n, k)
    for h in range(1, 9):
        assert len(SY.schubfach(h).klauseln) == (h + 1) + h * comb(h + 1, 2)       # je Auftrag eine Klausel, je Rampe alle Paare
    assert len(SY.schubfach(2).klauseln) == 9


def test_schur_zahlen_durch_aufzaehlung():
    erste_ohne_loesung = {k: next(n for n in range(1, 40) if not schur_loesungen_rueckverfolgung(n, k)) for k in (1, 2, 3)}
    assert {k: n - 1 for k, n in erste_ohne_loesung.items()} == {1: 1, 2: 4, 3: 13}          # S(1) = 1, S(2) = 4, S(3) = 13
    assert solve(*I.schur(13, 3)[:2]).antwort is True and solve(*I.schur(14, 3)[:2]).antwort is False
