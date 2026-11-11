"""Gemeinsame Fixtures und Hilfen: Handbeispiel Schubfach h = 2 und eine unabhängige Aufzählung (DEMO-PLAYBOOK §1b)."""

import itertools
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import smb_symmetrie as SY  # noqa: E402


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: Nachmessung der vorgerechneten Reihen, Minuten (lokal: pytest -m slow; die CI lässt sie aus)")


@pytest.fixture
def php2():
    """Handbeispiel: 3 Aufträge auf 2 Rampen (Variable x(p, l) = 2p + l + 1), 9 Klauseln, unerfüllbar."""
    return SY.schubfach(2)


def alle_belegungen_erfuellend(n, klauseln):
    """Alle Modelle durch Aufzählung aller 2^n Belegungen (nur für n ≤ 20); eigene Schleife, kein Code aus smb_*."""
    modelle = []
    for bits in itertools.product((False, True), repeat=n):
        if all(any(bits[abs(l) - 1] == (l > 0) for l in c) for c in klauseln):
            modelle.append(bits)
    return modelle


def schur_loesungen_rueckverfolgung(n, k):
    """Alle Färbungen 1..n -> 0..k-1 ohne a + b = c (a = b erlaubt) in einer Farbe, durch Rückverfolgung nach Zahl geordnet.
    Eigener Rechenweg (Handbeispiel `sat-cp-planung/handbeispiele/hb_09.py`), ohne Klauseln."""
    col = [None] * (n + 1)
    out = []

    def ok(i):
        c = col[i]
        for a in range(1, i):
            b = i - a
            if b < a:
                break
            if col[a] == c and col[b] == c:
                return False
        return not (2 * i <= n and col[2 * i] is not None and col[2 * i] == c)

    def rec(i):
        if i > n:
            out.append(tuple(col[1:]))
            return
        for c in range(k):
            col[i] = c
            if ok(i):
                rec(i + 1)
        col[i] = None

    rec(1)
    return out


def schur_gueltig(f):
    """Schur-Eigenschaft aus der Definition: kein a + b = c (a ≤ b) mit f(a) = f(b) = f(c)."""
    n = len(f)
    return all(not (f[a - 1] == f[b - 1] == f[a + b - 1]) for a in range(1, n + 1) for b in range(a, n + 1) if a + b <= n)


def wertevorrang_ok(f):
    """Zahl i mit Farbe c ≥ 1 verlangt eine kleinere Zahl mit Farbe c − 1 (aus der Definition, nicht aus den Klauseln)."""
    return all(c == 0 or any(f[j] == c - 1 for j in range(i)) for i, c in enumerate(f))
