"""Konstanten: Regler-Grenzen, feste Annahmen, Aufgaben, Schwellen der Verdikte, Farben und Presets."""

# --- Reiter (Experimente) ------------------------------------------------------------------------------------------------------------------
REITER_NAMEN = ("🔬 Von Hand", "🔬 Schubfach wächst", "🔬 Schur", "🔬 Wo es schadet")

# --- Aufgaben --------------------------------------------------------------------------------------------------------------------------
H_HAND_MIN, H_HAND_MAX, DEFAULT_H_HAND = 2, 3, 2           # Reiter 1: Schubfach h (h + 1 Aufträge auf h Rampen)
SCHUR_HAND_MIN, SCHUR_HAND_MAX, DEFAULT_SCHUR_HAND = 8, 14, 13   # Reiter 1: Schur k = 3, n Zahlen
SCHUR_K_HAND = 3
H_BIS_MIN, H_BIS_MAX, DEFAULT_H_BIS = 5, 7, 7              # Reiter 2: live bis h Rampen (h = 8 vorgerechnet)
H_REIHE_MIN = 3
H_VORGERECHNET = 8
SCHUR3_N = (11, 12, 13, 14)                                # Reiter 3: live, k = 3
DEFAULT_SCHUR3_N = 13
SCHUR4_N = (43, 44, 45)                                    # Reiter 3: vorgerechnet, k = 4
DEFAULT_SCHUR4_N = 43
SCHADET_N = 43                                             # Reiter 4: die leichte Aufgabe (Schur k = 4), Voreinstellung des Presets „Wo es schadet“
DEFAULT_SCHADET_N = 40
SCHADET_K = 4
SCHADET_SEEDS = 20                                         # Löser-Zufalls-Seeds 1 bis 20
KONTROLLE_SEEDS = tuple(range(21, 121))                    # Stabilitätsprobe: 100 weitere Löser-Zufalls-Seeds für n = 43
SEEDS_MIN, SEEDS_MAX, DEFAULT_SEEDS = 5, 20, 20
FAERBUNG_N = (60, 90, 120)
DEFAULT_FAERBUNG_N = 90
FAERBUNG_GRAD = 5.0                                        # mittlerer Grad des Konfliktgraphen (3-Färbung, meist unerfüllbar)
RAMPEN = 3
FAERBUNG_GRAPHEN = 10                                      # Zahl der Graphen je Zelle
SEED_MAX, DEFAULT_SEED = 999999, 500                       # Zufalls-Seed der Aufgabe: der erste Graph; die zehn Graphen haben die Seeds Seed bis Seed + 9
BUDGET_OPTIONEN = (1000, 5000, 20000, 100000)
DEFAULT_BUDGET = 100000

# --- Vorgerechnete Messreihen -------------------------------------------------------------------------------------------------------------
MESSUNG_DATEI = "smb_messung_vorgerechnet.json"
MESSSKRIPT = "tools/messung_symmetrie.py"
BUDGET_SCHUBFACH = 100000
BUDGET_SCHUR4 = 300000
BUDGET_SCHADET = 100000
BUDGET_FAERBUNG = 100000
SCHADET_N_REIHE = (38, 40, 42, 43)                         # Schur k = 4: n, für die 20 Löser-Zufalls-Seeds gemessen sind (Auswahl des Reglers in Reiter 4)
MESS_FAERBUNG_SEED = 500

# --- Schwellen der Verdikte (vor der Messung festgelegt, im Test festgeschrieben) -----------------------------------------------------------
HILFT_SCHWELLE = 0.8               # Quotient Median(mit) / Median(ohne) unter 0,8: „weniger Konflikte“; über 1,2: „mehr Konflikte“; dazwischen „etwa gleich“
SCHADET_SCHWELLE = 1.2
ALPHA = 0.05                       # Rangsummentest über viele Läufe: „weniger“/„mehr“ nur bei p < 0,05
KLEIN_KONFLIKTE = 10               # sind beide Konfliktzahlen höchstens so groß (ohne Abbruch), gilt „etwa gleich“

# --- Farben ----------------------------------------------------------------------------------------------------------------------------
COLOR_OHNE = "#8d8d8d"
COLOR_MIT = "#2F6B65"
COLOR_SCHADET = "#c0392b"
COLOR_LINE = "#4c78a8"

# --- Presets ---------------------------------------------------------------------------------------------------------------------------
PRESETS = {
    "Handbeispiel Schubfach": {"h_hand": 2},
    "Schur 14": {"schur3_n": 14},
    "Grenze Schur 44": {"schur4_n": 44},
    "Wo es schadet": {"schadet_n": SCHADET_N, "seeds": SCHADET_SEEDS},
}
PRESET_HELP = {
    "Handbeispiel Schubfach": "Reiter „Von Hand“: 3 paarweise unverträgliche Aufträge auf 2 Rampen (unerfüllbar), Einheitspropagation ohne und mit der Regel „Lochvorrang“ (die Voreinstellung der Seite).",
    "Schur 14": "Reiter „Schur“, Teil 1: Zahlen 1 bis 14 auf 3 Mengen ohne a + b = c (a = b erlaubt); unerfüllbar, ohne und mit Wertevorrang, live gerechnet.",
    "Grenze Schur 44": "Reiter „Schur“, Teil 2: 4 Mengen, n = 44 an der Grenze; vorgerechnete Werte (Vormessung, Python-CDCL, nicht live) ohne und mit Wertevorrang.",
    "Wo es schadet": "Reiter „Wo es schadet“: Schur mit 4 Mengen und 43 Zahlen, eine leichte Aufgabe, mit 20 Löser-Zufalls-Seeds ohne und mit Wertevorrang; die Verdikte nennen die Verschlechterung.",
}
