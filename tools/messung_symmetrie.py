"""Messskript der vorgerechneten Reihen: schreibt `smb_messung_vorgerechnet.json` (**vorgerechnet, nicht live**).

Aufruf (Test-venv, aus dem Repo-Ordner):
    python -X utf8 tools/messung_symmetrie.py --teil schubfach --out TEIL1.json
    python -X utf8 tools/messung_symmetrie.py --teil schur3    --out TEIL2.json
    python -X utf8 tools/messung_symmetrie.py --teil schur4    --out TEIL3.json
    python -X utf8 tools/messung_symmetrie.py --teil schadet   --out TEIL4.json
    python -X utf8 tools/messung_symmetrie.py --teil faerbung  --out TEIL5.json
    python -X utf8 tools/messung_symmetrie.py --teil kontrolle --out TEIL6.json
    python -X utf8 tools/messung_symmetrie.py --zusammen TEIL1.json TEIL2.json ...          # schreibt smb_messung_vorgerechnet.json

Teile:
  schubfach  h = 3 bis 8 (h + 1 Aufträge auf h Rampen): Standardlauf (Löser-Zufalls-Seed 0, ohne `noise`) ohne und mit Lochvorrang, Budget 100 000 Konflikte.
  schur3     Schur mit 3 Mengen, n = 11 bis 14: Standardlauf ohne und mit Wertevorrang, Budget 100 000.
  schur4     Schur mit 4 Mengen, n = 43, 44, 45: Standardlauf ohne und mit Wertevorrang, Budget 300 000 (ein Lauf je Zelle).
  schadet    Schur mit 4 Mengen, n = 38, 40, 42, 43: Standardlauf und 20 Löser-Zufalls-Seeds (1 bis 20, mit `noise`, zufälliger Start der Aktivitäten) ohne und mit Wertevorrang, Budget 100 000.
  kontrolle  Schur mit 4 Mengen, n = 43: weitere 100 Löser-Zufalls-Seeds (21 bis 120) ohne und mit Wertevorrang, Budget 100 000 (Stabilitätsprobe der Zahl aus `schadet`).
  faerbung   3-Färbung, Grad 5, n = 60 / 90 / 120, 10 Graphen (Seeds 500 bis 509): Standardlauf ohne, mit „erste Kante fest“ und mit Wertevorrang, Budget 100 000.
Aufwand wird nur in Konflikten gemessen; Sekunden stehen nirgends im Ergebnis.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import smb_algorithm as A  # noqa: E402
import smb_constants as C  # noqa: E402
import smb_instanzen as I  # noqa: E402
import smb_symmetrie as SY  # noqa: E402


def _m(m: A.Messung) -> dict:
    return {"antwort": m.antwort_text, "konflikte": m.konflikte, "entscheidungen": m.entscheidungen, "propagationen": m.propagationen, "gelernt": m.gelernt}


def teil_schubfach() -> dict:
    out = []
    for h in range(C.H_REIHE_MIN, C.H_VORGERECHNET + 1):
        inst = SY.schubfach(h)
        out.append({"h": h, "ohne": _m(A.messung(A.lauf(inst, None, budget=C.BUDGET_SCHUBFACH))),
                    "mit": _m(A.messung(A.lauf(inst, SY.REGEL_LOCHVORRANG, budget=C.BUDGET_SCHUBFACH)))})
        print("schubfach", h, out[-1]["ohne"]["konflikte"], out[-1]["mit"]["konflikte"], flush=True)
    return {"schubfach": out}


def _schur_teil(name: str, ns, k: int, budget: int) -> dict:
    out = []
    for n in ns:
        inst = I.schur(n, k)
        out.append({"n": n, "k": k, "ohne": _m(A.messung(A.lauf(inst, None, budget=budget))),
                    "mit": _m(A.messung(A.lauf(inst, SY.REGEL_WERTEVORRANG, budget=budget)))})
        print(name, n, out[-1]["ohne"]["konflikte"], out[-1]["mit"]["konflikte"], flush=True)
    return {name: out}


def teil_schadet() -> dict:
    out = []
    for n in C.SCHADET_N_REIHE:
        inst = I.schur(n, C.SCHADET_K)
        zelle = {"n": n, "k": C.SCHADET_K, "standard": {"ohne": _m(A.messung(A.lauf(inst, None, budget=C.BUDGET_SCHADET))),
                                                        "mit": _m(A.messung(A.lauf(inst, SY.REGEL_WERTEVORRANG, budget=C.BUDGET_SCHADET)))}}
        seeds = list(range(1, C.SCHADET_SEEDS + 1))
        for name, regel in (("ohne", None), ("mit", SY.REGEL_WERTEVORRANG)):
            konf, antworten, abbr = A.konflikte_je_seed(inst, regel, seeds, C.BUDGET_SCHADET)
            zelle[name] = {"konflikte": konf, "antworten": sorted(str(a) for a in antworten), "abbrueche": abbr}
        out.append(zelle)
        print("schadet", n, zelle["standard"]["ohne"]["konflikte"], zelle["standard"]["mit"]["konflikte"], flush=True)
    return {"schadet": out}


def teil_kontrolle() -> dict:
    inst = I.schur(C.SCHADET_N, C.SCHADET_K)
    seeds = list(C.KONTROLLE_SEEDS)
    zelle = {"n": C.SCHADET_N, "k": C.SCHADET_K, "seeds": [seeds[0], seeds[-1]]}
    for name, regel in (("ohne", None), ("mit", SY.REGEL_WERTEVORRANG)):
        konf, antworten, abbr = A.konflikte_je_seed(inst, regel, seeds, C.BUDGET_SCHADET)
        zelle[name] = {"konflikte": konf, "antworten": sorted(str(a) for a in antworten), "abbrueche": abbr}
    print("kontrolle", {k: sorted(zelle[k]["konflikte"])[len(seeds) // 2] for k in ("ohne", "mit")}, flush=True)
    return {"kontrolle": zelle}


def teil_faerbung() -> dict:
    out = []
    for n in C.FAERBUNG_N:
        z = A.faerbung_zelle(n, C.MESS_FAERBUNG_SEED, C.BUDGET_FAERBUNG)
        out.append(z)
        print("faerbung", n, {k: sorted(v) for k, v in z["regeln"].items()}, flush=True)
    return {"faerbung": out}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--teil", choices=["schubfach", "schur3", "schur4", "schadet", "kontrolle", "faerbung"])
    ap.add_argument("--out")
    ap.add_argument("--zusammen", nargs="+")
    a = ap.parse_args()
    if a.zusammen:
        ganz = {"meta": {
            "skript": C.MESSSKRIPT, "kern": "smb_cdcl.py (Kern-Version 832b2c10dfdea62d, unverändert)",
            "einheit": "Konflikte bis zur Antwort; Abbrüche zählen mit dem Budget (untere Schranke); keine Sekunden",
            "budget_schubfach": C.BUDGET_SCHUBFACH, "budget_schur4": C.BUDGET_SCHUR4, "budget_schadet": C.BUDGET_SCHADET, "budget_faerbung": C.BUDGET_FAERBUNG,
            "schadet_seeds": list(range(1, C.SCHADET_SEEDS + 1)), "kontrolle_seeds": [C.KONTROLLE_SEEDS[0], C.KONTROLLE_SEEDS[-1]], "faerbung": {"grad": C.FAERBUNG_GRAD, "rampen": C.RAMPEN, "seeds": list(range(C.MESS_FAERBUNG_SEED, C.MESS_FAERBUNG_SEED + C.FAERBUNG_GRAPHEN))},
            "loeser": "Standardlauf: Aktivität (VSIDS), Phasenspeicher, Luby (Einheit 32), Löser-Zufalls-Seed 0 ohne noise; die Seeds 1 bis 20 mit noise (zufälliger Start der Aktivitäten)"}}
        for datei in a.zusammen:
            ganz.update(json.loads(Path(datei).read_text(encoding="utf-8")))
        (ROOT / C.MESSUNG_DATEI).write_text(json.dumps(ganz, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
        print("geschrieben:", ROOT / C.MESSUNG_DATEI)
        return
    teil = {"schubfach": teil_schubfach, "schur3": lambda: _schur_teil("schur3", C.SCHUR3_N, 3, 100000),
            "schur4": lambda: _schur_teil("schur4", C.SCHUR4_N, 4, C.BUDGET_SCHUR4), "schadet": teil_schadet, "kontrolle": teil_kontrolle, "faerbung": teil_faerbung}[a.teil]()
    Path(a.out).write_text(json.dumps(teil, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
