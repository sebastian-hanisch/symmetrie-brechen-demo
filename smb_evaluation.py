"""Kennzahlen, Verdikte (reine Funktionen) und Auswertung der vorgerechneten Messreihen.

Jedes Verdikt ist `verdict_*(...) -> (Art, Text)`; die App ruft `getattr(st, Art)(Text)`. Jede Zahl im Text stammt aus den übergebenen Werten.
Schwellen (vor der Messung festgelegt, `tests/test_verdicts.py` schreibt sie fest):
  - Einordnung zweier Konfliktzahlen (oder Mediane) ohne und mit Brechung über den Quotienten q = mit / ohne:
    „weniger“ bei q < 0,8, „mehr“ bei q > 1,2, dazwischen (Grenzen inklusive) „etwa gleich“; ohne Konflikte auf beiden Seiten „etwa gleich“, nur ohne Brechung 0: „mehr“;
  - sind beide Konfliktzahlen höchstens KLEIN_KONFLIKTE (10) und ohne Abbruch, gilt „etwa gleich“ (ein Unterschied von 1 auf 2 Konflikte ist kein Befund);
  - ein Abbruch am Budget ist eine untere Schranke: bricht nur die Seite ohne Brechung ab und liegt die Seite mit Brechung darunter, gilt „weniger“;
    bricht nur die Seite mit Brechung ab und liegt sie über der ohne, gilt „mehr“; in allen anderen Fällen mit Abbruch „offen“.
  - Einordnung über viele Läufe (Löser-Zufalls-Seeds, Graphen): wie oben nach den Medianen; „weniger“ und „mehr“ gelten nur, wenn der Test p < 0,05 ergibt (Rangsummentest nach Mann-Whitney, zweiseitig,
    bei Löser-Zufalls-Seeds; exakter Vorzeichentest, zweiseitig, bei den Graphen der Färbung, weil dort jeder Graph ohne und mit Regel gerechnet wird),
    sonst „nicht belegt“ (der Quotient liegt außerhalb des Bandes, der Unterschied ist aber nicht von der Streuung zu trennen). Der Test ist nach der ersten Messung hinzugekommen
    (siehe README „Befunde und Korrekturen gegenüber dem Plan“); die Schwellen 0,8 und 1,2 standen vorher fest.
Eine Zeile einer Reihe ist ein Dictionary mit den Schlüsseln `ohne`, `mit` (Konflikte) und `ohne_abbruch`, `mit_abbruch` (Wahrheitswerte).
"""

import json
import math
import statistics
from pathlib import Path

import smb_constants as C

WENIGER, GLEICH, MEHR, OFFEN, NICHT_BELEGT = "weniger", "etwa gleich", "mehr", "offen", "nicht belegt"
_DATEI = Path(__file__).resolve().parent / C.MESSUNG_DATEI
_cache: dict = {}


# ---------------------------------------------------------------------------------------------------------------- Zahlenformat
def zahl(x) -> str:
    """Ganze Zahl mit Leerzeichen als Tausendertrenner, Halbe mit Dezimalkomma."""
    if isinstance(x, float) and not x.is_integer():
        return dezimal(x)
    return f"{int(x):,}".replace(",", " ")


def dezimal(x: float, stellen: int = 1) -> str:
    return f"{x:,.{stellen}f}".replace(",", " ").replace(".", ",")


def konflikt_wort(k) -> str:
    return f"{zahl(k)} Konflikt" if k == 1 else f"{zahl(k)} Konflikte"


def faktor_text(a: float, b: float) -> str:
    """Verhältnis des größeren zum kleineren Wert als „×12,3“ (bei 0 auf einer Seite: kein Faktor)."""
    if a <= 0 or b <= 0:
        return "ohne Faktor"
    return "×" + dezimal(max(a, b) / min(a, b))


# ---------------------------------------------------------------------------------------------------------------- Einordnung
def einordnung(ohne: float, mit: float, ohne_abbruch: bool = False, mit_abbruch: bool = False) -> str:
    """Siehe Modulkopf: Quotient mit / ohne unter 0,8 „weniger“, über 1,2 „mehr“, sonst „etwa gleich“; Abbrüche als untere Schranken."""
    if not ohne_abbruch and not mit_abbruch and max(ohne, mit) <= C.KLEIN_KONFLIKTE:
        return GLEICH
    if ohne_abbruch and mit_abbruch:
        return OFFEN
    if ohne_abbruch:
        return WENIGER if mit < ohne else OFFEN
    if mit_abbruch:
        return MEHR if mit > ohne else OFFEN
    if ohne == 0:
        return GLEICH if mit == 0 else MEHR
    q = round(mit / ohne, 9)
    if q < C.HILFT_SCHWELLE:
        return WENIGER
    if q > C.SCHADET_SCHWELLE:
        return MEHR
    return GLEICH


def zaehle_klassen(klassen) -> dict:
    z = {WENIGER: 0, GLEICH: 0, MEHR: 0, OFFEN: 0, NICHT_BELEGT: 0}
    for k in klassen:
        z[k] += 1
    return z


def zeile_aus(m_ohne: dict, m_mit: dict, **schluessel) -> dict:
    """Zeile einer Reihe aus zwei Messungen (Dictionaries mit `konflikte` und `antwort`, Abbruch = Antwort „Abbruch am Budget“ bzw. „Abbruch“)."""
    zeile = dict(schluessel)
    zeile.update({"ohne": m_ohne["konflikte"], "mit": m_mit["konflikte"],
                  "ohne_abbruch": m_ohne["antwort"].startswith("Abbruch"), "mit_abbruch": m_mit["antwort"].startswith("Abbruch"),
                  "antwort_ohne": m_ohne["antwort"], "antwort_mit": m_mit["antwort"]})
    return zeile


def klasse_der_zeile(z: dict) -> str:
    return einordnung(z["ohne"], z["mit"], z["ohne_abbruch"], z["mit_abbruch"])


def lade_messung() -> dict:
    """Die vorgerechneten Messreihen (Datei `smb_messung_vorgerechnet.json`, Messskript `tools/messung_symmetrie.py`)."""
    if "daten" not in _cache:
        _cache["daten"] = json.loads(_DATEI.read_text(encoding="utf-8"))
    return _cache["daten"]


def zeilen_schubfach(daten: dict) -> list:
    return [zeile_aus(z["ohne"], z["mit"], h=z["h"]) for z in daten["schubfach"]]


def zeilen_schur(daten: dict, schluessel: str) -> list:
    return [zeile_aus(z["ohne"], z["mit"], n=z["n"], k=z["k"]) for z in daten[schluessel]]


# ---------------------------------------------------------------------------------------------------------------- Reiter 1
def verdict_hand_schubfach(h: int, ohne: dict, mit: dict, klauseln: int, zusatz: int, loesungen: int | None = None, loesungen_mit: int | None = None) -> tuple:
    """Handbeispiel Schubfach: Einheitspropagation auf Stufe 0 ohne und mit Lochvorrang. `ohne`/`mit` = {konflikt: bool, belegt: int, variablen: int}."""
    if mit["konflikt"] and not ohne["konflikt"]:
        text = (f"Schubfach mit {h + 1} Aufträgen auf {h} Rampen ({klauseln} Klauseln, dazu {zusatz} Klauseln des Lochvorrangs): Ohne die Regel belegt die Einheitspropagation "
                f"{ohne['belegt']} von {ohne['variablen']} Variablen und findet keinen Widerspruch. Mit der Regel belegt sie {mit['belegt']} von {mit['variablen']} Variablen "
                f"und endet in der leeren Klausel, ohne dass eine Entscheidung nötig ist.")
        kind = "success"
    elif mit["konflikt"] and ohne["konflikt"]:
        text = f"Schubfach mit {h + 1} Aufträgen auf {h} Rampen: Die Einheitspropagation findet schon ohne die Regel den Widerspruch."
        kind = "info"
    else:
        text = (f"Schubfach mit {h + 1} Aufträgen auf {h} Rampen: Die Einheitspropagation findet auch mit dem Lochvorrang keinen Widerspruch auf Stufe 0 "
                f"({mit['belegt']} von {mit['variablen']} Variablen belegt); der Löser muss entscheiden.")
        kind = "info"
    if loesungen is not None and loesungen_mit is not None:
        text += f" Zum Vergleich die erfüllbare Fassung mit {h} Aufträgen: {zahl(loesungen)} Lösungen ohne, {zahl(loesungen_mit)} mit der Regel."
    return kind, text


def verdict_hand_schur(n: int, k: int, erg: dict, zusatz: int) -> tuple:
    """Handbeispiel Schur: `erg` = Ergebnis von `smb_symmetrie.loesungen_und_bahnen` mit Regel."""
    l, m, b = erg["loesungen"], erg["mit_brechung"], erg["bahnen"]
    if l == 0:
        return "info", (f"Schur mit {k} Mengen und den Zahlen 1 bis {n}: keine Lösung, weder ohne noch mit Wertevorrang (Aufzählung aller Färbungen); die Regel fügt {zusatz} Klauseln hinzu.")
    gleich_gross = erg["bahngroessen"] == [_fak(k)]
    teil = (f"Alle {b} Bahnen haben die Größe {k}! = {_fak(k)}, also {zahl(l)} / {_fak(k)} = {zahl(l // _fak(k))} Lösungen mit Wertevorrang."
            if gleich_gross else f"Die Bahnen haben die Größen {', '.join(str(g) for g in erg['bahngroessen'])}.")
    return "success", (f"Schur mit {k} Mengen und den Zahlen 1 bis {n}: {zahl(l)} Lösungen, {zahl(m)} davon erfüllen den Wertevorrang ({zusatz} zusätzliche Klauseln); "
                       f"die Lösungen bilden {zahl(b)} Bahnen unter den Vertauschungen der Mengen. {teil}")


def _fak(k: int) -> int:
    r = 1
    for i in range(2, k + 1):
        r *= i
    return r


# ---------------------------------------------------------------------------------------------------------------- Reiter 2
def verdict_schubfach(zeilen: list, budget: int, vorgerechnet: bool = False) -> tuple:
    """Schubfach wächst: Faktor je zusätzliche Rampe ohne Brechung, Konflikte mit Lochvorrang. Ein Lauf je Zeile."""
    if not zeilen:
        return "info", "Noch keine Zeilen."
    ohne = [z["ohne"] for z in zeilen]
    abbruch = [z for z in zeilen if z["ohne_abbruch"]]
    hs = [z["h"] for z in zeilen]
    mit_alle = [z["mit"] for z in zeilen]
    teile = [f"Ohne Brechung braucht der Löser für h = {', '.join(str(h) for h in hs)} Rampen {' / '.join(zahl(z['ohne']) for z in zeilen)} Konflikte"
             + (f" (Abbrüche am Budget von {zahl(budget)} Konflikten: {', '.join('h = ' + str(z['h']) for z in abbruch)}; dort ist die Zahl eine untere Schranke)." if abbruch else ".")]
    paare = [(zeilen[i]["ohne"], zeilen[i + 1]["ohne"]) for i in range(len(zeilen) - 1) if not zeilen[i]["ohne_abbruch"] and not zeilen[i + 1]["ohne_abbruch"] and zeilen[i]["ohne"] > 0]
    if paare:
        f = [b / a for a, b in paare]
        teile.append(f"Je zusätzliche Rampe wächst die Zahl um den Faktor {dezimal(min(f))} bis {dezimal(max(f))}.")
    if all(m == mit_alle[0] for m in mit_alle) and not any(z["mit_abbruch"] for z in zeilen):
        teile.append(f"Mit Lochvorrang sind es in jeder Zeile {konflikt_wort(mit_alle[0])}.")
    else:
        teile.append(f"Mit Lochvorrang: {' / '.join(zahl(z['mit']) + ('+' if z['mit_abbruch'] else '') for z in zeilen)} Konflikte.")
    teile.append(("Vorgerechnet, " if vorgerechnet else "Live gerechnet, ") + f"ein Lauf je Zeile mit dem Standard-Löser ohne Zufall (Löser-Zufalls-Seed 0), Budget {zahl(budget)} Konflikte.")
    return ("success" if all(klasse_der_zeile(z) == WENIGER for z in zeilen) else "info"), " ".join(teile)


# ---------------------------------------------------------------------------------------------------------------- Reiter 3
def verdict_schur(zeilen: list, k: int, budget: int, vorgerechnet: bool) -> tuple:
    """Schur mit k Mengen: je n die Konflikte ohne und mit Wertevorrang, Zählung der Klassen."""
    if not zeilen:
        return "info", "Noch keine Zeilen."
    klassen = [klasse_der_zeile(z) for z in zeilen]
    z = zaehle_klassen(klassen)
    teile = []
    for zz, kl in zip(zeilen, klassen):
        a = zahl(zz["ohne"]) + ("+" if zz["ohne_abbruch"] else "")
        b = zahl(zz["mit"]) + ("+" if zz["mit_abbruch"] else "")
        teile.append(f"n = {zz['n']}: {a} → {b} Konflikte ({kl}" + (f", {faktor_text(zz['ohne'], zz['mit'])}" if kl in (WENIGER, MEHR) and not (zz["ohne_abbruch"] or zz["mit_abbruch"]) else "") + ")")
    kopf = (f"Schur mit {k} Mengen, {len(zeilen)} Aufgaben, je ein Lauf ohne und mit Wertevorrang: in {z[WENIGER]} von {len(zeilen)} Aufgaben weniger Konflikte, in {z[MEHR]} mehr, "
            f"in {z[GLEICH]} etwa gleich viele" + (f", in {z[OFFEN]} offen (Abbruch auf beiden Seiten)" if z[OFFEN] else "") + ". ")
    schluss = (f" „+“ markiert einen Abbruch am Budget von {zahl(budget)} Konflikten (untere Schranke)." if any(zz["ohne_abbruch"] or zz["mit_abbruch"] for zz in zeilen) else "")
    quelle = " Vorgerechnet (Vormessung, Python-CDCL, nicht live)." if vorgerechnet else " Live gerechnet."
    kind = "warning" if z[MEHR] else ("success" if z[WENIGER] == len(zeilen) else "info")
    return kind, kopf + "; ".join(teile) + "." + schluss + quelle + f" Standard-Löser ohne Zufall (Löser-Zufalls-Seed 0), Budget {zahl(budget)} Konflikte."


# ---------------------------------------------------------------------------------------------------------------- Reiter 4
def mann_whitney_p(a, b) -> float:
    """Zweiseitiger p-Wert des Mann-Whitney-Tests (Rangsummentest) für zwei unabhängige Stichproben: Normalnäherung mit Korrektur für gleiche Werte und Stetigkeitskorrektur.
    Eigene Rechnung (Mittelränge), im Test gegen `scipy.stats.mannwhitneyu(method="asymptotic")` geprüft. Sind alle Werte gleich, ist der p-Wert 1."""
    n1, n2 = len(a), len(b)
    gesamt = sorted(list(a) + list(b))
    n = n1 + n2
    rang, i, tie = {}, 0, 0.0
    while i < n:
        j = i
        while j + 1 < n and gesamt[j + 1] == gesamt[i]:
            j += 1
        rang[gesamt[i]] = (i + j) / 2 + 1
        t = j - i + 1
        tie += t ** 3 - t
        i = j + 1
    u1 = sum(rang[x] for x in a) - n1 * (n1 + 1) / 2
    mu = n1 * n2 / 2
    var = n1 * n2 / 12 * ((n + 1) - tie / (n * (n - 1)))
    if var <= 0:
        return 1.0
    z = max(abs(u1 - mu) - 0.5, 0.0) / math.sqrt(var)
    return math.erfc(z / math.sqrt(2))


def vorzeichentest_p(weniger: int, mehr: int) -> float:
    """Exakter zweiseitiger Vorzeichentest für gepaarte Läufe (gleicher Graph ohne und mit Regel): unter der Annahme „keine Richtung“ ist die Zahl der Graphen mit weniger Konflikten
    binomialverteilt (Erfolgswahrscheinlichkeit 1/2 unter den Graphen mit verschiedenen Konfliktzahlen); p = Wahrscheinlichkeit, mindestens so ungleich zu zählen, zweiseitig, höchstens 1.
    Gleichstände zählen nicht. Ohne Graphen mit Unterschied ist p = 1."""
    n = weniger + mehr
    if n == 0:
        return 1.0
    k = min(weniger, mehr)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)


def p_text(p: float) -> str:
    return "p < 0,001" if p < 0.001 else "p = " + dezimal(p, 3)


def p_wert(ohne: list, mit: list, gepaart: bool = False) -> float:
    """p-Wert des Vergleichs: gepaart (gleiche Aufgabe ohne und mit Regel, Index = Aufgabe) der exakte Vorzeichentest, sonst der Rangsummentest (Mann-Whitney)."""
    if gepaart:
        return vorzeichentest_p(sum(1 for a, b in zip(ohne, mit) if b < a), sum(1 for a, b in zip(ohne, mit) if b > a))
    return mann_whitney_p(ohne, mit)


def einordnung_getestet(ohne: list, mit: list, ohne_abbruch: int = 0, mit_abbruch: int = 0, gepaart: bool = False) -> str:
    """Einordnung über viele Läufe: zuerst nach den Medianen (`einordnung`); liegt der Quotient außerhalb des Bandes „etwa gleich“, gilt „weniger“ beziehungsweise „mehr“
    nur, wenn der Test p < ALPHA (0,05) ergibt (`p_wert`), sonst „nicht belegt“. Bricht mehr als die Hälfte der Läufe einer Seite ab, gilt die Regel für Abbrüche."""
    klasse = einordnung(statistics.median(ohne), statistics.median(mit), ohne_abbruch * 2 > len(ohne), mit_abbruch * 2 > len(mit))
    if klasse in (WENIGER, MEHR) and not (ohne_abbruch * 2 > len(ohne) or mit_abbruch * 2 > len(mit)) and p_wert(ohne, mit, gepaart) >= C.ALPHA:
        return NICHT_BELEGT
    return klasse


def zusammenfassung_seeds(konflikte_ohne: list, konflikte_mit: list, gepaart: bool = False) -> dict:
    """Median, Maximum, Minimum je Seite, p-Wert (`p_wert`) und die Zahl der Läufe (gleicher Index), in denen die Seite mit Brechung mehr / weniger Konflikte hat."""
    paare = list(zip(konflikte_ohne, konflikte_mit))
    return {"n": len(paare), "median_ohne": statistics.median(konflikte_ohne), "median_mit": statistics.median(konflikte_mit),
            "max_ohne": max(konflikte_ohne), "max_mit": max(konflikte_mit), "min_ohne": min(konflikte_ohne), "min_mit": min(konflikte_mit),
            "p": p_wert(konflikte_ohne, konflikte_mit, gepaart), "gepaart": gepaart,
            "laeufe_mehr": sum(1 for a, b in paare if b > a), "laeufe_weniger": sum(1 for a, b in paare if b < a),
            "laeufe_gleich": sum(1 for a, b in paare if b == a)}


def _prozent(ohne: float, mit: float) -> str:
    if ohne == 0:
        return "ohne Vergleichswert"
    p = round((mit / ohne - 1.0) * 100)
    return ("+" if p > 0 else "−" if p < 0 else "±") + f"{abs(p)} %"


def verdict_schadet(n: int, k: int, konflikte_ohne: list, konflikte_mit: list, abbrueche_ohne: int = 0, abbrueche_mit: int = 0, budget: int | None = None,
                    standard: tuple | None = None, kontrolle: tuple | None = None) -> tuple:
    """Schur mit k Mengen und n Zahlen, Konflikte je Löser-Zufalls-Seed ohne und mit Wertevorrang (gleiche Seeds).
    `standard` = (Konflikte ohne, Konflikte mit) des einen Standardlaufs ohne Zufall; `kontrolle` = (Konflikte ohne, Konflikte mit) weiterer Seeds (Stabilitätsprobe).
    Warnung („Verschlechterung“), wenn der Median mit Brechung über den Seeds über dem 1,2-Fachen liegt und der Test p < 0,05 ergibt; ist nur der Standardlauf schlechter,
    steht das im Text („Verschlechterung im Standardlauf, über die Seeds nicht belegt“); nichts davon: Information oder Erfolg."""
    z = zusammenfassung_seeds(konflikte_ohne, konflikte_mit)
    klasse = einordnung_getestet(konflikte_ohne, konflikte_mit, abbrueche_ohne, abbrueche_mit)
    teile = [f"Schur mit {k} Mengen und den Zahlen 1 bis {n}, {z['n']} Löser-Zufalls-Seeds je Seite: Median {zahl(z['median_ohne'])} Konflikte ohne, {zahl(z['median_mit'])} mit Wertevorrang "
             f"({_prozent(z['median_ohne'], z['median_mit'])}; Maximum {zahl(z['max_ohne'])} gegen {zahl(z['max_mit'])}); mit der Brechung mehr Konflikte in {z['laeufe_mehr']} von {z['n']} Läufen, "
             f"weniger in {z['laeufe_weniger']}. Rangsummentest (Mann-Whitney, zweiseitig): {p_text(z['p'])}."]
    std_klasse = None
    if standard is not None:
        std_klasse = einordnung(standard[0], standard[1])
        teile.append(f"Der eine Standardlauf ohne Zufall (Löser-Zufalls-Seed 0) braucht {zahl(standard[0])} Konflikte ohne und {zahl(standard[1])} mit Wertevorrang.")
    if kontrolle is not None:
        zk = zusammenfassung_seeds(kontrolle[0], kontrolle[1])
        teile.append(f"Kontrolle mit {zk['n']} weiteren Seeds: Median {zahl(zk['median_ohne'])} gegen {zahl(zk['median_mit'])} ({_prozent(zk['median_ohne'], zk['median_mit'])}, {p_text(zk['p'])}), "
                     f"mit der Brechung mehr Konflikte in {zk['laeufe_mehr']} von {zk['n']} Läufen.")
    if abbrueche_ohne or abbrueche_mit:
        teile.append(f"Abbrüche am Budget ({zahl(budget)}): {abbrueche_ohne} ohne, {abbrueche_mit} mit Brechung.")
    text = " ".join(teile)
    if klasse == MEHR:
        return "warning", "Verschlechterung über die Seeds: " + text
    if klasse == WENIGER:
        return "success", "Weniger Konflikte über die Seeds: " + text
    if std_klasse == MEHR:
        return "warning", "Verschlechterung im Standardlauf, über die Seeds nicht belegt: " + text
    if klasse == NICHT_BELEGT:
        return "info", "Unterschied über die Seeds nicht belegt: " + text
    return "info", "Kein Unterschied über die Seeds: " + text


def zusammenfassung_faerbung(zelle: dict, regel: str) -> dict:
    """Je Graph der Zelle die Konflikte ohne und mit der Regel; Median, Maximum, p-Wert und Zahl der Graphen mit weniger / mehr / gleich vielen Konflikten."""
    ohne, mit = zelle["regeln"]["ohne"], zelle["regeln"][regel]
    z = zusammenfassung_seeds(ohne, mit, gepaart=True)
    z["abbrueche_ohne"], z["abbrueche_mit"] = zelle["abbrueche"]["ohne"], zelle["abbrueche"].get(regel, 0)
    z["unerfuellbar"] = sum(1 for a in zelle["antworten"] if a == "unerfüllbar")
    z["klasse"] = einordnung_getestet(ohne, mit, z["abbrueche_ohne"], z["abbrueche_mit"], gepaart=True)
    return z


def verdict_faerbung(n: int, regel_name: str, z: dict, budget: int) -> tuple:
    """Färbung (3 Rampen, Grad 5, n Aufträge): Median über die Graphen ohne und mit der Regel, Rangsummentest; `z` = `zusammenfassung_faerbung`."""
    klasse = z["klasse"]
    text = (f"Färbung mit n = {n} Aufträgen, {z['n']} Graphen, davon {z['unerfuellbar']} unerfüllbar, ein Lauf je Graph: Median {zahl(z['median_ohne'])} Konflikte ohne, "
            f"{zahl(z['median_mit'])} mit „{regel_name}“ ({_prozent(z['median_ohne'], z['median_mit'])}; Maximum {zahl(z['max_ohne'])} gegen {zahl(z['max_mit'])}); mit der Regel mehr Konflikte "
            f"in {z['laeufe_mehr']} von {z['n']} Graphen, weniger in {z['laeufe_weniger']}, gleich viele in {z['laeufe_gleich']}. Vorzeichentest (je Graph gepaart, exakt, zweiseitig): {p_text(z['p'])}.")
    if z["abbrueche_ohne"] or z["abbrueche_mit"]:
        text += f" Abbrüche am Budget ({zahl(budget)}): {z['abbrueche_ohne']} ohne, {z['abbrueche_mit']} mit der Regel."
    return ("warning" if klasse == MEHR else "success" if klasse == WENIGER else "info"), text


def zellen_klassen(daten: dict) -> dict:
    """Die Zellen des Reiters 4 aus den vorgerechneten Reihen: Schur mit 4 Mengen je n (20 Seeds, Rangsummentest) und Färbung je n und Regel (10 Graphen, Vorzeichentest), je mit `einordnung_getestet`."""
    klassen = {}
    for z in daten["schadet"]:
        klassen[f"Schur mit {z['k']} Mengen, n = {z['n']}"] = einordnung_getestet(z["ohne"]["konflikte"], z["mit"]["konflikte"], z["ohne"]["abbrueche"], z["mit"]["abbrueche"])
    for z in daten["faerbung"]:
        for regel, name in (("kante_fest", "erste Kante fest"), ("wertevorrang", "Wertevorrang")):
            klassen[f"Färbung, n = {z['n']}, {name}"] = zusammenfassung_faerbung(z, regel)["klasse"]
    return klassen


def verdict_zellen(klassen: dict) -> tuple:
    """Zählung über alle Zellen des Reiters 4 ({Name der Zelle: Klasse}): „in x von y Zellen weniger Konflikte, in z mehr“."""
    z = zaehle_klassen(klassen.values())
    text = (f"Über alle {len(klassen)} Zellen (Median je Zelle, Standard-Löser, Rangsummen- beziehungsweise Vorzeichentest): in {z[WENIGER]} von {len(klassen)} Zellen belegt weniger Konflikte mit der Brechung, in {z[MEHR]} belegt mehr, "
            f"in {z[GLEICH]} etwa gleich viele, in {z[NICHT_BELEGT]} ein Unterschied jenseits des Bandes, aber nicht belegt" + (f", in {z[OFFEN]} offen" if z[OFFEN] else "") + ".")
    return ("warning" if z[MEHR] else "info"), text


def _seeds_satz(daten: dict, n: int) -> str:
    """Satzteil zur Gegenprobe über Löser-Zufalls-Seeds (Reiter „Wo es schadet“) für Schur mit 4 Mengen und n Zahlen; leer, wenn dafür nichts gemessen ist."""
    zellen = [z for z in daten.get("schadet", []) if z["n"] == n]
    if not zellen:
        return ""
    z = zellen[0]
    klasse = einordnung_getestet(z["ohne"]["konflikte"], z["mit"]["konflikte"], z["ohne"]["abbrueche"], z["mit"]["abbrueche"])
    wort = {NICHT_BELEGT: "nicht belegt", MEHR: "belegt mehr", WENIGER: "belegt weniger", GLEICH: "etwa gleich viele", OFFEN: "offen"}[klasse]
    return f"; im Median über {len(z['ohne']['konflikte'])} Löser-Zufalls-Seeds (Reiter „Wo es schadet“): {wort}"


def verdict_kern(daten: dict) -> tuple:
    """Kernfrage auf der Seite: Zählung aus den vorgerechneten Reihen (Schubfach h = 3 bis 8, Schur k = 4 n = 43 bis 45; je ein Lauf)."""
    sf = zeilen_schubfach(daten)
    s4 = zeilen_schur(daten, "schur4")
    k_sf = zaehle_klassen(klasse_der_zeile(z) for z in sf)
    k_s4 = zaehle_klassen(klasse_der_zeile(z) for z in s4)
    schadet = [z for z in s4 if klasse_der_zeile(z) == MEHR]
    teile = [f"Schubfach, h = {sf[0]['h']} bis {sf[-1]['h']}: in {k_sf[WENIGER]} von {len(sf)} Aufgaben weniger Konflikte mit der Brechung (h = {sf[-1]['h']}: {zahl(sf[-1]['ohne'])} → {zahl(sf[-1]['mit'])}).",
             f"Schur mit 4 Mengen, n = {s4[0]['n']} bis {s4[-1]['n']}: weniger Konflikte in {k_s4[WENIGER]} von {len(s4)} Aufgaben, mehr in {k_s4[MEHR]}"
             + (f" (n = {schadet[0]['n']}: {zahl(schadet[0]['ohne'])} → {zahl(schadet[0]['mit'])}, ein Lauf{_seeds_satz(daten, schadet[0]['n'])})" if schadet else "") + "."]
    return "info", " ".join(teile) + " Je ein Lauf, vorgerechnet (Vormessung, Python-CDCL, nicht live); die Brechung erhält die Erfüllbarkeit, nicht die Lösungen."
