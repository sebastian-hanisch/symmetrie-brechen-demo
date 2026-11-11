"""Die kopierten Kern-Module sind unverändert gegenüber der Kern-Version, die im Modulkopf steht (Hash der Datei ohne Kopfzeilen und mit rückübersetzten Importen).

`smb_rng.py`, `smb_instanzen.py` und `smb_cdcl.py` sind Kopien von `rng.py`, `instanzen.py` und `cdcl.py` aus `sat-cp-planung/kern/` ohne inhaltliche Abweichung (nur die
Kopfzeilen und der Import `from smb_rng import` statt `from rng import`). Der Test setzt den Import zurück und vergleicht mit dem Kern-Hash aus dem Kopf; der Kern-Ordner
selbst wird nicht gebraucht."""

import hashlib
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
MODULE = ["rng", "instanzen", "cdcl"]


def _kern_text(modul: str) -> tuple[str, str]:
    """(Kern-Version aus dem Kopf, Text im Zustand des Kerns)."""
    text = (ROOT / f"smb_{modul}.py").read_text(encoding="utf-8").replace("\r\n", "\n")
    version = re.match(r"# Herkunft: Kopie von sat-cp-planung/kern/\w+\.py \(Kern-Version ([0-9a-f]{16})", text).group(1)
    zeilen = text.split("\n")
    i = 0
    while zeilen[i].startswith("#"):
        i += 1
    return version, "\n".join(zeilen[i:]).replace("from smb_rng import", "from rng import")


@pytest.mark.parametrize("modul", MODULE)
def test_kopie_gleicht_der_kern_version(modul):
    version, text = _kern_text(modul)
    assert hashlib.sha256(text.encode("utf-8")).hexdigest()[:16] == version


def test_kern_versionen_stehen_im_kopf_und_sind_die_aus_dem_kern_paket():
    """Die drei Hashes (HASHES.txt des Kern-Pakets, Stand 2026-11-10)."""
    erwartet = {"rng": "5d5d8f45d0e1eddf", "instanzen": "6795de796b66fff8", "cdcl": "832b2c10dfdea62d"}
    assert {m: _kern_text(m)[0] for m in MODULE} == erwartet


def test_kopien_importieren_nichts_aus_dem_kern_oder_anderen_demos():
    for modul in MODULE:
        quelle = (ROOT / f"smb_{modul}.py").read_text(encoding="utf-8")
        for zeile in quelle.splitlines():
            if zeile.startswith(("import ", "from ")):
                assert zeile.split()[1] in {"heapq", "itertools", "dataclasses", "typing", "smb_rng"}, (modul, zeile)


def test_eigene_module_importieren_nur_kopien_und_standardbibliothek():
    erlaubt = {"heapq", "itertools", "math", "json", "statistics", "dataclasses", "pathlib", "time", "streamlit", "pandas", "plotly", "typing"}
    for datei in sorted(ROOT.glob("smb_*.py")) + [ROOT / "app.py"]:
        for zeile in datei.read_text(encoding="utf-8").splitlines():
            if zeile.startswith(("import ", "from ")):
                name = zeile.split()[1].split(".")[0]
                assert name in erlaubt or name.startswith("smb_"), (datei.name, zeile)
