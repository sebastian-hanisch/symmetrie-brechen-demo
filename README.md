# Symmetrie brechen – aus 27 932 Konflikten wird einer – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-symmetrie-brechen-demo.streamlit.app/)**

Stück der **sat-constraint-programming**-Linie in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“, im SAT-Arm. Vorgänger in der Linie ist `kardinalitaet-kodieren-demo` (Zählbedingungen als Klauseln; Kante „fix“: vertauschbare Rampen, Farben oder Löcher machen jede Lösung und jede Sackgasse mehrfach, ohne dass der Löser es merkt). Nachbarn: `konfliktlernen-demo` (Lernen ohne Brechung; das Schubfach ist dort die Grenze des Lernens, hier der Ausweg), `graph-coloring-demo` (dieselbe Färbung, andere Frage) und `sat-phasenuebergang-demo` (Schubfach und Störung). Vehikel der Linie: **Aufträge mit Unverträglichkeiten auf Rampen**, das ist die Färbung eines Konfliktgraphen; Rampen sind austauschbar, also Farben. Dazu die Grenzbeispiele **Schubfach** und **Schur-Zahlen**.

## Warum dieses Problem

**Wenn man vertauschbare Dinge nicht auseinanderhält, kann der Löser dieselbe Sackgasse in jeder Vertauschung noch einmal suchen.** Eine zusätzliche Regel wie „Farbe 1 erst, wenn Farbe 0 schon vorkam“ streicht die Vertauschungen. Die Kernfrage der Demo: **Was ändert das an der Zahl der Konflikte, und wann wird es nicht besser, sondern schlechter?** Aufwand wird in Konflikten, Entscheidungen und Propagationen gezählt, nie in Sekunden. Die Antwort steht im Abschnitt „Befunde“; sie gilt für diese drei Aufgabenfamilien und diesen Löser.

Das Ergebnis in kurzer Form: Beim Schubfach (h + 1 paarweise unverträgliche Aufträge auf h Rampen) braucht der Löser ohne die Regel 159 / 1 004 / 4 811 / 27 932 Konflikte für h = 5 bis 8 und mit dem Lochvorrang jedes Mal 1; bei den Schur-Zahlen mit 4 Mengen sinkt der Aufwand an der Grenze (n = 44) im Standardlauf (ein Lauf) von 108 775 auf 3 844 Konflikte. **Die Gegenseite hält der Nachmessung nur halb stand:** Bei den leichten Aufgaben (n = 43) verschlechtert die Regel den einen Standardlauf von 6 auf 352 Konflikte; über 20 Löser-Zufalls-Seeds ist die Verschlechterung nicht belegt, und eine Kontrolle mit 100 weiteren Seeds zeigt das Gegenteil (siehe „Befunde und Korrekturen gegenüber dem Plan“).

## Modell

- **Aufgaben.** *Schubfach:* h + 1 Aufträge, h Rampen, jeder Auftrag mindestens eine Rampe, jede Rampe höchstens einen Auftrag (Variable x(p, l)); unerfüllbar. Mit genau h Aufträgen ist die Aufgabe erfüllbar und hat h! Lösungen (Reiter „Von Hand“). *Schur:* die Zahlen 1 bis n auf k Mengen, in keiner Menge a + b = c (a = b erlaubt), jede Zahl genau eine Menge; für k = 3 ist die Aufgabe bis n = 13 erfüllbar (Aufzählung, in den Tests; S(3) = 13), für k = 4 nach Golomb und Baumert 1965 (als zitierter Wert, Quelle nicht gelesen) bis n = 44. *Färbung:* n Aufträge, Konfliktgraph mit mittlerem Grad 5 (SplitMix64), 3 Rampen; „höchstens eine Rampe“ fehlt bewusst (eine zweite Rampe schadet nicht).
- **Regeln.** *Wertevorrang* (Schur, Färbung): Farbe c ≥ 1 darf nur vergeben werden, wenn eine frühere Zahl (ein früherer Knoten) die Farbe c − 1 hat; (k − 1)·n Klauseln. *Lochvorrang* (Schubfach): Auftrag p darf Rampe l ≥ 1 nur anfahren, wenn ein früherer Auftrag Rampe l − 1 anfährt; (h − 1)·(h + 1) Klauseln. *Erste Kante fest* (Färbung): die Endpunkte der ersten Kante haben die Farben 0 und 1; zwei Einheitsklauseln. Jede Regel ist eine Liste zusätzlicher Klauseln (`smb_symmetrie.py`); die Aufgabe bleibt unverändert.
- **Was erhalten bleibt.** Die **Erfüllbarkeit** (Beweisskizzen im Kopf von `smb_symmetrie.py` und im Expander „📐 Mathematische Formulierung“), **nicht die Menge der Lösungen**: Von Hand gezählt hat Schur mit k = 3 und n = 13 18 Lösungen in 3 Bahnen der Größe 3! = 6 und 3 Lösungen mit Wertevorrang, genau eine je Bahn. „Lösungen / k!“ ist nur die Zahl der Bahnen, wenn jede Lösung mindestens k − 1 Farben benutzt (bei n = 1 und k = 3 ist die Bahn nur 3 groß).
- **Löser.** CDCL mit 1-UIP-Lernen, Aktivität je Variable (VSIDS in der MiniSat-Variante, Zerfall 0,95), Phasenspeicher, Luby-Neustarts (Einheit 32), Watched Literals, ohne Löschen. Der **Standardlauf** hat den Löser-Zufalls-Seed 0 ohne zufälligen Start der Aktivitäten; die **Löser-Zufalls-Seeds** 1 und höher starten die Aktivitäten zufällig (SplitMix64, `noise`): ohne diesen Start wirkt der Seed nicht (Test unten), alle Seeds wären derselbe Lauf.
- **Messgröße.** Konflikte bis zur Antwort; ein Abbruch am Budget zählt mit dem Budget (untere Schranke). Budgets: Schubfach 100 000, Schur mit 4 Mengen 300 000, Reiter „Wo es schadet“ und Färbung 100 000; live das Budget der Seitenleiste.
- **Einordnung** (Schwellen vor der Messung festgelegt): Quotient Konflikte mit / ohne Regel unter 0,8 „weniger“, über 1,2 „mehr“, sonst „etwa gleich“; sind beide Zahlen höchstens 10, gilt „etwa gleich“. Über viele Läufe gelten „weniger“ und „mehr“ nur bei einem Test mit p < 0,05 (Rangsummentest nach Mann-Whitney für die Löser-Zufalls-Seeds, exakter Vorzeichentest für die Graphen der Färbung, weil jeder Graph ohne und mit Regel gerechnet wird), sonst „nicht belegt“. Der Test kam nach der ersten Messung hinzu (siehe unten).
- Mathematik, Symboltabelle und Quellen: Expander **📐 Mathematische Formulierung** in der App.

## Methodik

| Baustein | Datei | Anmerkung |
|---|---|---|
| CDCL (Kopie des Kern-Pakets) | `smb_cdcl.py` | Kern-Version 832b2c10dfdea62d, unverändert bis auf die Kopfzeilen und den Import |
| SplitMix64, Instanzerzeuger (Kopien) | `smb_rng.py`, `smb_instanzen.py` | Kern-Versionen 5d5d8f45d0e1eddf und 6795de796b66fff8 im Modulkopf; Zufall nie über Pythons `random` oder `hash()` |
| Brechungsregeln, Lösungszählung, Bahnen, Einheitspropagation | `smb_symmetrie.py` | neu für diese Demo, nicht im Kern; eigene Zählung der Modelle (unabhängig vom CDCL) |
| Läufe, Reihen, Statistik | `smb_algorithm.py` | Standardlauf, Läufe mit Löser-Zufalls-Seed, Reihen für Schubfach, Schur, Färbung |
| Aufgaben, Beschreibungen | `smb_scenario.py` | Schubfach, Schur, Aufträge auf Rampen |
| Verdikte, Tests über viele Läufe, Auswertung der Messdatei | `smb_evaluation.py` | alle Verdikte als reine Funktionen; Rangsummen- und Vorzeichentest in eigener Rechnung (gegen SciPy getestet) |
| Messskript der vorgerechneten Reihen | `tools/messung_symmetrie.py` | schreibt `smb_messung_vorgerechnet.json` (**vorgerechnet, nicht live**) |

## Befunde und Korrekturen gegenüber dem Plan

Der Plan für diese Demo stützte sich auf eine Vormessung mit Python-`random`-Graphen und einem Lauf je Zelle. Der Bau hat nachgemessen; was sich nicht reproduziert, ist hier korrigiert.

1. **„Schadet bei Schur n = 43“ ist als allgemeine Aussage nicht belegt.** Reproduziert ist die Vormessung des einen Standardlaufs: 6 Konflikte ohne, 352 mit Wertevorrang (Zählung des deterministischen Lösers). Der Plan nannte diese Aussage ausdrücklich nur als „ein Lauf“ und verlangte 20 Löser-Zufalls-Seeds. Gemessen: **Median 302,5 ohne, 366 mit Wertevorrang (+21 %, knapp über der Schwelle 1,2); mit der Regel mehr Konflikte in 10 von 20 Läufen, weniger in 10; Rangsummentest p = 0,20: nicht belegt.** Der Standardlauf ohne Regel (6 Konflikte) liegt weit unter dem kleinsten der 20 Seed-Läufe (38): Er ist ein außergewöhnlich günstiger Lauf, kein typischer. Eine **Kontrolle mit 100 weiteren Seeds** (21 bis 120) kehrt das Vorzeichen um: Median 391,5 ohne, 287 mit Wertevorrang (−27 %), p = 0,011; alle 120 Seeds zusammen 342 gegen 318 (−7 %), p = 0,071. Die Zahl aus 20 Läufen ist also nicht stabil (Playbook §11a Punkt 5). Das Szenario „Wo es schadet“ im Schnellstart meldet deshalb „Verschlechterung im Standardlauf, über die Seeds nicht belegt“ und nicht eine belegte Verschlechterung.
2. **Auch bei n = 38, 40, 42 verschlechtert der Standardlauf (0 → 65, 6 → 184, 6 → 352), über Seeds ist kein Unterschied belegt.** Median ohne / mit: 131,5 / 95,5 (n = 38), 323 / 363 (n = 40), 278 / 366 (n = 42); p = 0,26 / 0,74 / 0,48. Über alle 10 Zellen des Reiters 4 (diese vier Schur-Zellen und die sechs Färbungs-Zellen) ist die Brechung in **6 Zellen belegt besser, in 0 belegt schlechter**, in 1 etwa gleich, in 3 jenseits des Bandes aber nicht belegt.
3. **Färbung.** Mit SplitMix64-Graphen (Grad 5, alle 30 Graphen unerfüllbar) sind die Konfliktzahlen andere als in der Vormessung (dort Median 62 → 16 bei n = 90, andere Graphen): n = 60 / 90 / 120: Median 21,5 / 49 / 73 ohne Regel, 7 / 30,5 / 28,5 mit „erste Kante fest“, 9 / 32,5 / 35,5 mit Wertevorrang. Der Wertevorrang für die Färbung kam im Bau hinzu (im Plan nur „erste Kante fest“).
4. **Schubfach h = 8 nicht live.** Der Plan sah h = 8 auf Knopfdruck vor; der Python-CDCL braucht dafür Minuten. Live reicht der Regler bis h = 7, h = 8 steht in der vorgerechneten Reihe (27 932 → 1).
5. **Schubfach-Erzeuger.** `pigeonhole(h)` des Kerns kennt nur h + 1 Aufträge; `smb_symmetrie.schubfach(h, tauben)` erzeugt dieselben Klauseln (Test) und deckt zusätzlich die erfüllbare Fassung mit h Aufträgen ab. Zum Zählen der Lösungen kommt „höchstens eine Rampe je Auftrag“ hinzu (nur in der Zählung, nicht in den Läufen).
6. **Test über viele Läufe.** Die Schwellen 0,8 und 1,2 standen vor der Messung fest; der Rangsummen- und der Vorzeichentest kamen nach der ersten Messung hinzu, weil die Mediane der 20 Seeds die Aussage sonst scheinbar bestätigt hätten (Quotient 1,21).
7. **Reproduziert** sind ohne Abweichung: Schubfach h = 5 bis 8 (159 / 1 004 / 4 811 / 27 932 → 1), Schur k = 3, n = 14 (148 → 21), k = 4, n = 44 (108 775 → 3 844), das Handbeispiel (Einheitspropagation, 18 Lösungen, 3 Vertreter, 2 964 Bahnen bei k = 4, n = 10).
8. **Reiter-Aufbau.** Die Reiter sind statt einer Auswahl immer alle gezeichnet (Streamlit-Fallstrick „ausblendbare Regler“); Die Szenarien des Schnellstarts stellen nur Werte ein, sie schalten den Reiter nicht um.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen stammen aus `smb_messung_vorgerechnet.json` (Messung dieses Repos mit `tools/messung_symmetrie.py`, **vorgerechnet, nicht live**) oder sind exakte Zählungen des deterministischen Standardlaufs; jede steht in dem genannten Test.

| Frage | Befund | Test |
|---|---|---|
| **Handbeispiel Schubfach h = 2** (3 Aufträge, 2 Rampen) | 9 Klauseln, 3 Klauseln des Lochvorrangs. Einheitspropagation ohne Regel: 0 von 6 Variablen belegt, kein Widerspruch; mit Regel: 6 von 6 belegt, Widerspruch ohne Entscheidung. CDCL: 2 Konflikte (1 Entscheidung) ohne, 1 Konflikt (0 Entscheidungen) mit Regel. Erfüllbare Fassung (2 Aufträge): 2 Lösungen, mit Regel 1. | `test_claim_handbeispiel_schubfach_h2` |
| **Schur mit 3 Mengen, Lösungen zählen** | n = 12: 114 Lösungen, 19 mit Wertevorrang; n = 13: 18 Lösungen in 3 Bahnen der Größe 6, 3 mit Wertevorrang; n = 14: keine. Klauseln der Regel 24 / 26 / 28. Schur mit 4 Mengen, n = 10: 71 136 Lösungen = 2 964 Bahnen · 24. | `test_claim_schur3_zaehlung_n12_n13_n14`, `test_schur4_n10_bahnen_von_hand` |
| **Schubfach, live** | Standardlauf ohne Regel: 7 / 28 / 159 / 1 004 / 4 811 Konflikte für h = 3 bis 7; mit Lochvorrang je 1 Konflikt, 0 Entscheidungen. | `test_claim_schubfach_konflikte_h3_bis_h7_live` |
| **Schubfach, vorgerechnet** | h = 3 bis 8: ohne Regel 7 / 28 / 159 / 1 004 / 4 811 / 27 932, mit Lochvorrang überall 1; Faktor je zusätzliche Rampe 4,0 bis 6,3 (ein Lauf je h, Budget 100 000, kein Abbruch). | `test_claim_schubfach_reihe_h3_bis_h8`, `test_claim_schubfach_datei_stimmt_mit_dem_heutigen_code_ueberein` |
| **Schur mit 3 Mengen, live** | n = 11 / 12 / 13 / 14: ohne Regel 1 / 1 / 18 / 148 Konflikte, mit Wertevorrang 2 / 2 / 11 / 21 (n = 14 unerfüllbar). 1 → 2 gilt als „etwa gleich“ (beide höchstens 10). | `test_claim_schur3_konflikte_n11_bis_n14_live` |
| **Schur mit 4 Mengen, vorgerechnet** | n = 43: 6 → 352 Konflikte; n = 44: 108 775 → 3 844 (Faktor 28,3, je ein Standardlauf, keine Verteilung), beide erfüllbar; n = 45: **vorläufig, noch nicht nachgemessen** (Eintrag in der Datei aus der Vormessung der Planung: mit Wertevorrang unerfüllbar nach 109 523 Konflikten, ohne Regel Abbruch am Budget; die Nachmessung ist noch nicht abgeschlossen) | `test_claim_schur_datei_k3_und_k4`, `test_claim_schur_k4_n43_live`, `test_claim_schur_k4_n44_mit_wertevorrang_slow`, `test_claim_schur_k4_n44_ohne_und_n45_voll_slow` |
| **Standardlauf bei leichten Schur-Aufgaben** | n = 38 / 40 / 42 / 43: ohne Regel 0 / 6 / 6 / 6 Konflikte, mit Wertevorrang 65 / 184 / 352 / 352. | `test_claim_standardlaeufe_n38_bis_n43_live` |
| **Dieselben Aufgaben mit 20 Löser-Zufalls-Seeds** | Median ohne / mit: 131,5 / 95,5 (n = 38), 323 / 363 (n = 40), 278 / 366 (n = 42), 302,5 / 366 (n = 43); mit der Regel mehr Konflikte in 5 / 10 / 12 / 10 von 20 Läufen; Rangsummentest p = 0,26 / 0,74 / 0,48 / 0,20: kein Unterschied belegt. | `test_claim_20_seeds_je_n_median_maximum_laeufe_p`, `test_claim_seeds_datei_stimmt_mit_dem_heutigen_code_ueberein` |
| **n = 43: Quotient und Standardlauf** | 366 / 302,5 = 1,21 (+21 %), außerhalb des Bandes, nicht belegt; kleinster Seed-Lauf ohne Regel 38, der Standardlauf 6. | `test_claim_n43_20_seeds_quotient_und_klasse` |
| **n = 43: Kontrolle mit 100 weiteren Seeds** | Median 391,5 ohne, 287 mit Wertevorrang (−27 %); mit der Regel mehr Konflikte in 36, weniger in 63, gleich viele in 1 von 100 Läufen; Maximum 3 509 gegen 4 181; p = 0,011. Alle 120 Seeds: 342 gegen 318 (−7 %), p = 0,071. | `test_claim_kontrolle_100_seeds_n43` |
| **Färbung** (3 Rampen, Grad 5, 10 Graphen je n, alle unerfüllbar) | Median ohne Regel / erste Kante fest / Wertevorrang: n = 60: 21,5 / 7 / 9; n = 90: 49 / 30,5 / 32,5; n = 120: 73 / 28,5 / 35,5. Graphen mit weniger Konflikten mit erster Kante fest: 9 / 10 / 10 von 10 (mehr: 0), mit Wertevorrang 10 / 9 / 9 (mehr: 0 / 1 / 1); Vorzeichentest p = 0,004 / 0,002 / 0,002 bzw. 0,002 / 0,021 / 0,021; Antworten in allen Regeln gleich. | `test_claim_faerbung_zellen`, `test_claim_faerbung_datei_stimmt_mit_dem_heutigen_code_ueberein` |
| **Zählung über alle Zellen** | 10 Zellen: belegt weniger in 6, belegt mehr in 0, etwa gleich in 1 (Schur n = 40), nicht belegt in 3 (Schur n = 38, 42, 43). | `test_claim_zaehlung_ueber_zellen` |
| **Aufbau der Messdatei** | Budgets 100 000 / 300 000, 20 + 100 Löser-Zufalls-Seeds, 10 Graphen mit den Seeds 500 bis 509, keine Abbrüche in Reiter 4, 30 von 30 Graphen unerfüllbar. | `test_claim_aufbau_der_messdatei` |
| **Der Seed wirkt nur mit zufälligem Start** | Ohne `noise` sind die Löser-Zufalls-Seeds 1 bis 3 derselbe Lauf; mit `noise` geben die Seeds 1 bis 4 bei Schur n = 38 mindestens zwei verschiedene Konfliktzahlen; die Antwort ändert sich in keinem Lauf. | `test_zwei_seeds_geben_mindestens_einmal_verschiedene_konfliktzahlen`, `test_loeser_zufalls_seed_aendert_die_antwort_nie` |
| **Verdikte nennen dieselben Zahlen** | Der Text der Kernfrage zählt „in 5 von 6 Aufgaben weniger“ (h = 3: 7 gegen 1 ist „etwa gleich“); das Szenario „Wo es schadet“ meldet „Verschlechterung im Standardlauf, über die Seeds nicht belegt“. | `test_claim_verdikt_der_kernfrage_nennt_die_zaehlung`, `test_claim_preset_wo_es_schadet_verdikt` |

## Ehrliche Grenzen

- **Ein Löser, drei Familien.** „Weniger“ und „mehr“ gelten für diesen CDCL (Aktivität, Phasenspeicher, Luby-Neustarts) und diese Aufgaben. Andere Löser, andere Einstellungen, Zufalls-3-SAT (hat typischerweise keine Farbsymmetrie, nicht gemessen) und industrielle Formeln sind nicht gemessen.
- **Ein Standardlauf ist ein Lauf.** Der Standardlauf ohne Zufall zeigt für n = 43 „6 → 352“; der Median über Löser-Zufalls-Seeds sagt etwas anderes (302,5 → 366, nicht belegt). Wo die Demo einen Lauf je Zelle zeigt (Schubfach, Schur mit 3 Mengen, Schur mit 4 Mengen n = 43 bis 45), steht „ein Lauf“ dabei. Bei den großen Unterschieden (Schubfach 27 932 → 1, Schur n = 44: Faktor 28) ist ein Lauf aussagekräftiger als ein Quotient von 1,2, aber auch dort ist es eine Zählung des Standardlaufs, keine Verteilung.
- **20 Seeds sind wenig.** Der Median der 20 Seeds von n = 43 liegt bei +21 %, die 100 Kontroll-Seeds bei −27 %: Zahlen aus 20 Läufen können das Vorzeichen wechseln. Die Rangsummentests (p = 0,20 und 0,011) sind eine Normalnäherung auf Läufen mit stark streuenden Konfliktzahlen (Maximum bis 5 306).
- **„Erhält die Erfüllbarkeit, nicht die Lösungen“.** Wer alle Lösungen braucht (zählen, Modelle aufzählen), kann die Regeln nicht verwenden; wer nur wissen will, ob eine Lösung existiert, kann es.
- **Schubfach: eigene Messung.** „Mit Lochvorrang erledigt die Einheitspropagation das Schubfach“ ist hier gemessen (Konflikt auf Stufe 0, h = 3 bis 8). Krishnamurthy 1985 und Aloul u. a. (Shatter) wurden nicht gelesen; die Demo behauptet nichts über deren Ergebnisse.
- **Quellen.** Heule 2017 (Schur Number Five, Volltext gelesen) nennt die lexikographische Ordnung der Farben als Symmetriebrechung; der Wertevorrang dieser Demo ist dieselbe Familie. Crawford u. a. 1996 (dort als Quelle der Technik genannt) und Golomb und Baumert 1965 (S(3) = 13, S(4) = 44) sind nicht gelesen; S(3) = 13 ist hier durch Aufzählung bestätigt, S(4) = 44 nur zitiert.
- **Zählgrößen statt Sekunden.** Mit der Regel kommen Klauseln hinzu, und Konflikte sind nicht gleich teuer. Dass der Aufwand in Konflikten sinkt, heißt nicht, dass die Laufzeit im gleichen Verhältnis sinkt.
- **Die Verdikte der Seite sind Zählungen der vorgerechneten Reihen**, nicht Läufe der Sitzung; die live gerechneten Reihen (Schubfach bis h = 7, Schur mit 3 Mengen, Seeds, Graphen) zeigen ihre eigenen Zahlen und vergleichen sich, wo es sie gibt, mit der Datei.

## Verifikation

- **Kern-Kopien:** `tests/test_copies.py` vergleicht `smb_rng.py`, `smb_instanzen.py` und `smb_cdcl.py` mit dem Kern-Hash im Kopf (Kopfzeilen und Import zurückgesetzt) und prüft, dass nichts aus dem Kern oder aus anderen Demos importiert wird. Die Regressionstests des Kern-Pakets (SplitMix64-Referenzwerte, Schubfach h = 3 bis 5: 7 / 28 / 159 Konflikte, Handrechnungen zu Propagation, 1-UIP, Rücksprung, Beobachter, Budget) laufen in `tests/test_kern_*.py` mit.
- **Handwerte:** `tests/test_symmetrie.py` (Handbeispiel: Klauseln, Einheitspropagation, Lösungen, Bahnen, Vertreter).
- **Orakel** (`tests/test_oracle_symmetrie_brechen.py`, anderer Rechenweg): Lösungszählung gegen die Rückverfolgung über Färbungen (Schur k = 2, 3), Bahnen gegen explizite Anwendung aller k! Vertauschungen, Antwort des CDCL mit und ohne Regel gegen Aufzählung (Schur), gegen alle 2^n Belegungen (Schubfach h ≤ 3) und gegen alle 3^n Färbungen (50 Zufallsgraphen), **OR-Tools CP-SAT mit ganzzahligen Variablen** (Schur, Färbung, Schubfach; Lösungen zählen und Erfüllbarkeit, mit und ohne Regel als ganzzahlige Nebenbedingung; 32 Instanzen im Repo, `importorskip`), Einheitspropagation gegen die Propagation des Lösers auf Stufe 0, Klauselzahlen gegen eine Formel, S(1) = 1, S(2) = 4, S(3) = 13. Der große Lauf mit mehr als 200 Zufallsinstanzen steht nicht im Repo (Scratch-Lauf, nächster Punkt).
- **Eigenschaften** (`tests/test_properties.py`): Äquierfüllbarkeit für Schur n ≤ 20 mit k = 1, 2, 3, für Schubfach h ≤ 4 und 60 zufällige Färbungen; jede Lösung mit Regel ist eine Lösung der Aufgabe; Farbvertauschung einer Lösung bleibt eine Lösung; Zahl der Lösungen mit Regel = Zahl der Bahnen; der Löser-Zufalls-Seed ändert die Antwort nie.
- **Randfälle** (`tests/test_edge_cases.py`): k = 1, n = 1, h = 1, Budget erreicht (Antwort „unbekannt“, nie „unerfüllbar“), weniger benutzte Farben als k, Graph ohne Kanten.
- **Verdikte** (`tests/test_verdicts.py`): Schwellen inklusive Grenzen, jede Zahl im Text an handgesetzten Zeilen; Rangsummen- und Vorzeichentest gegen SciPy; **Claims** (`tests/test_claims.py`): jede Zahl der README, auch gegen den heutigen Code nachgerechnet; langsame Nachmessungen mit dem Marker `slow`.
- **Oberfläche:** AppTest-Rauchtest (jeder Knopf, jeder Regler am Rand), Inhalt je Szenario des Schnellstarts, Layout (Schnellstart in der Seitenleiste, fester Kopf, Hervorhebung), Footer, Laufzeit-Importe.
- **Scratch-Lauf zum Bau** (Messung dieser README, nicht im Test, Skript nicht im Repo): 430 Zufallsinstanzen, nämlich 250 Färbungen (6 bis 15 Knoten, 3 Farben; 71 erfüllbar), 120 Schur-Aufgaben (k = 2 bis 4; 104 erfüllbar) und 60 Schubfach-Aufgaben (h = 1 bis 5 mit 1 bis h + 1 Aufträgen; 24 erfüllbar). Die Antwort des CDCL ohne und mit jeder passenden Regel stimmt in allen 430 Aufgaben mit OR-Tools CP-SAT (ganzzahlige Variablen) überein: 0 Abweichungen.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary (ohne die langsamen Tests) |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App |
| `smb_cdcl.py` | CDCL-Löser (Kopie des Kern-Pakets, Kern-Version im Kopf) |
| `smb_rng.py` | SplitMix64 (Kopie des Kern-Pakets) |
| `smb_instanzen.py` | Instanzerzeuger (Kopie des Kern-Pakets): Zufalls-3-SAT, Schubfach, Schur, Färbung, Rampen |
| `smb_symmetrie.py` | Brechungsregeln, Lösungszählung, Bahnen, Einheitspropagation |
| `smb_algorithm.py` | Läufe und Reihen |
| `smb_scenario.py` | Aufgaben und Beschreibungen |
| `smb_constants.py` | Regler-Grenzen, Schwellen der Verdikte, Budgets, Farben, Szenarien des Schnellstarts |
| `smb_evaluation.py` | Verdikte (reine Funktionen), Tests über viele Läufe, Auswertung der Messdatei |
| `smb_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `smb_layout.py` | Fester Kopf (Stylesheet) |
| `smb_presets.py` | Permalink (Begrenzen), Szenarien des Schnellstarts (Seitenleiste, aktives Szenario hervorgehoben), Zufalls-Seed-Knopf |
| `smb_messung_vorgerechnet.json` | vorgerechnete Messreihen (Messung dieses Repos) |
| `tools/messung_symmetrie.py` | Messskript der Reihen |
| `requirements.txt` | Laufzeit-Bibliotheken: streamlit, pandas, plotly (ungepinnt) |
| `requirements-dev.txt` | Laufzeit plus pytest, OR-Tools und SciPy (nur Gegenproben in den Tests) |
| `tests/` | Kern-Kopien, Handwerte, Orakel, Eigenschaften, Randfälle, Claims, Verdikte, Szenarien, Layout, AppTest, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Allgemeine Symmetrieerkennung** (Graphautomorphismen, Shatter), **dynamische Symmetriebrechung** während der Suche und die **allgemeine lexikographische Ordnung** (Lex-Leader): nur drei handgeschriebene Regeln.
- **Cube-and-Conquer** und **Beweise der Brechung** (DRAT): Ausblick, nicht Teil dieser Demo.
- **Zählen von Lösungen bei der Färbung:** die Färbungs-Kodierung hat kein „höchstens eine Farbe“, Lösungen und Bahnen zählen nur bei Schur und Schubfach.
- **Zufalls-3-SAT:** hat typischerweise keine Farbsymmetrie, deshalb keine Messung dazu.
- **Mehr als einen Löser** und Einstellungen (Neustarts, Phasenspeicher aus) mit und ohne Brechung: nicht gemessen.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v -m "not slow"          # wie die CI
pytest tests/ -m slow                   # langsame Nachmessungen (Minuten)
```

Gebaut mit Streamlit, Plotly und pandas.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [SAT und CP: Konfliktlernen bis Wahl](https://sebastianhanisch.net/konzepte-sat-constraint-programming.html).
