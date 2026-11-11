"""Symmetrie brechen – aus 27 932 Konflikten wird einer, und manchmal wird es schlimmer - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Vertauschbare Rampen, Farben oder Löcher machen jede Sackgasse mehrfach: der Löser kann sie in jeder Vertauschung noch einmal suchen. Eine Regel wie „Farbe 1 erst, wenn Farbe 0 schon vorkam“
streicht die Vertauschungen. Vier Experimente: von Hand, Schubfach wächst, Schur, wo es schadet.
Aufwand wird in Konflikten, Entscheidungen und Propagationen gezählt, nie in Sekunden.

Lauffähig mit: streamlit run app.py
"""

import time

import pandas as pd
import streamlit as st

import smb_algorithm as A
import smb_constants as C
import smb_evaluation as E
import smb_instanzen as I
import smb_live as L
import smb_scenario as S
import smb_symmetrie as SY
import smb_visualization as V
from smb_layout import dunkles_design, kopf_css
from smb_presets import (
    SETTING_SPECS,
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)

st.set_page_config(page_title="Symmetrie brechen – Sebastian Hanisch", layout="wide")

LOCH, WERT, KANTE = SY.REGEL_LOCHVORRANG, SY.REGEL_WERTEVORRANG, SY.REGEL_KANTE_FEST
REGEL_NAMEN = {LOCH: "Lochvorrang", WERT: "Wertevorrang", KANTE: "erste Kante fest"}


@st.cache_data(show_spinner=False)
def _hand_schubfach(h):
    inst = S.schubfach_aufgabe(h)
    ohne, mit = A.wurzel(inst), A.wurzel(inst, LOCH)
    m_ohne, m_mit = A.messung(A.lauf(inst)), A.messung(A.lauf(inst, LOCH))
    voll = SY.loesungen_und_bahnen(S.schubfach_aufgabe(h, h), LOCH)
    return ohne, mit, m_ohne, m_mit, voll


@st.cache_data(show_spinner=False)
def _hand_schur(n):
    return SY.loesungen_und_bahnen(I.schur(n, C.SCHUR_K_HAND), WERT, behalte=3)


@st.cache_data(show_spinner=False)
def _schur3_zeilen(ns, budget):
    zeilen = A.schur_reihe(ns, 3, budget)
    return [E.zeile_aus(_dict(z["ohne"]), _dict(z["mit"]), n=z["n"], k=3) for z in zeilen]


@st.cache_data(show_spinner=False, max_entries=12)
def _faerbung_live(n, seed0, budget):
    t0 = time.perf_counter()
    return A.faerbung_zelle(n, seed0, budget), time.perf_counter() - t0


@st.cache_data(show_spinner=False)
def _daten():
    return E.lade_messung()


def _dict(m):
    """Messung als Dictionary im Format der vorgerechneten Datei."""
    return {"antwort": m.antwort_text, "konflikte": m.konflikte}


def _tabelle(daten, spalten):
    st.dataframe(pd.DataFrame(daten, columns=spalten), hide_index=True, width="stretch")


def _plus(z, abbruch):
    return E.zahl(z) + ("+" if abbruch else "")


def _mengen_text(farben, k):
    return "  |  ".join("{" + ", ".join(str(i + 1) for i, f in enumerate(farben) if f == c) + "}" for c in range(k))


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in smb_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("♾️ Symmetrie brechen – aus 27 932 Konflikten wird einer")
st.markdown(
    """
**Wenn man vertauschbare Dinge nicht auseinanderhält, kann der Löser dieselbe Sackgasse in jeder Vertauschung noch einmal suchen.** Vertauschbar sind hier die **Rampen** (Farben), auf die Aufträge mit
Unverträglichkeiten verteilt werden, die **Löcher** beim Schubfach und die **Mengen** bei den Schur-Zahlen. Eine zusätzliche Regel wie „Farbe 1 erst, wenn Farbe 0 schon vorkam“ streicht die
Vertauschungen, **ändert die Erfüllbarkeit nicht** und verändert die Suche, manchmal um Größenordnungen, **manchmal zum Schlechteren**. Der Aufwand wird in **Konflikten, Entscheidungen und
Propagationen** gezählt, nie in Sekunden.

Weiter unten: vier Experimente (Reiter), **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

# erklaerseite:einfach:start (erzeugt von tools/set_demo_explainer.py (Website-Repo) aus tools/content/explainers/symmetrie-brechen-erklaert.json, nicht von Hand ändern)
with st.expander("💬 In einfachen Worten"):
    st.markdown(
        """
Manche Aufgaben enthalten **vertauschbare Dinge**: gleiche Rampen, gleiche Farben, gleiche Fächer. Ein Löser, der das nicht weiß, sucht dieselbe Sackgasse in jeder Vertauschung noch einmal. Eine zusätzliche Regel, etwa „eine Rampe erst, wenn die vorige schon benutzt wird“, lässt von jeder Vertauschung nur eine zu. Die Aufgabe bleibt gleich lösbar oder unlösbar, nur die Zahl der Lösungen sinkt.

Die Demo zählt, wie viele **Konflikte** (Sackgassen) der Löser mit und ohne Regel braucht. Beim Schubfach sinken sie auf einen einzigen. Bei leichten Aufgaben kann die Regel im einzelnen Lauf mehr Konflikte kosten; über viele Löser-Zufalls-Seeds ist das nicht belegt. Gezählt werden Konflikte, keine Sekunden, und alles gilt nur für diesen Löser und diese drei Aufgabenarten.

[Ausführlich und verständlich erklärt, mit Fachteil](https://sebastianhanisch.net/symmetrie-brechen-erklaert.html)
        """
    )
# erklaerseite:einfach:end

with st.expander("So funktioniert das Brechen von Symmetrien", expanded=True):
    st.markdown(
        """
Eine **Symmetrie** ist eine Umbenennung, die jede Lösung wieder in eine Lösung verwandelt: Vertauscht man in einer gültigen Aufteilung auf Rampen die Namen zweier Rampen, bleibt sie gültig.
Bei $k$ Farben gibt es $k!$ solche Vertauschungen. Ein Löser, der davon nichts weiß, hält jede für eine eigene Aufgabe: Findet er für eine Zuordnung keine Lösung, kann er dieselbe Sackgasse
für jede Vertauschung noch einmal beweisen müssen. Die **Brechung** fügt Klauseln hinzu, die aus jeder Gruppe vertauschter Lösungen nur **einen Vertreter** erlauben:

| Regel | Aufgabe | Klauseln, die hinzukommen | Was sie festlegt |
|---|---|---|---|
| **Wertevorrang** | Schur, Färbung | „Farbe $c \\ge 1$ nur, wenn eine frühere Zahl (ein früherer Knoten) Farbe $c-1$ hat“: $(k-1) \\cdot n$ Klauseln | Farben erscheinen in der Reihenfolge ihres ersten Auftretens; Zahl 1 liegt in Farbe 0 |
| **Lochvorrang** | Schubfach | „Auftrag $p$ nur in Rampe $l \\ge 1$, wenn ein früherer Auftrag Rampe $l-1$ hat“: $(h-1)(h+1)$ Klauseln | besetzte Rampen sind nach ihrem frühesten Auftrag geordnet |
| **erste Kante fest** | Färbung | zwei Einheitsklauseln | die Endpunkte der ersten Kante haben die Farben 0 und 1 |

Zur Sprache: Eine Formel besteht aus **Klauseln**, Oder-Verknüpfungen von Aussagen wie $x(p,l)$ („Auftrag $p$ fährt Rampe $l$ an“; $\\neg$ heißt „nicht“). Die **Einheitspropagation** ist der erste Schritt jedes Lösers:
Hat eine Klausel nur noch eine offene Aussage, muss sie wahr sein; das wird wiederholt, ohne zu raten. Ein **Konflikt** liegt vor, wenn eine Klausel nur noch falsche Aussagen hat.

Die Regeln **erhalten die Erfüllbarkeit** (aus jeder Lösung entsteht durch Umbenennen eine, die die Regel erfüllt, und jede Lösung mit Regel ist eine ohne), **nicht die Menge der Lösungen**:
Von $k!$ vertauschten Lösungen bleibt eine übrig. Ob die Suche dadurch kürzer wird, ist eine Messung, kein Satz.
        """
    )

load_permalink_settings()
init_session_state_defaults()
st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Szenario ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Zufall und Budget** (für die Läufe, die auf Knopfdruck gerechnet werden)")
    seed = st.number_input("Zufalls-Seed der Aufgabe", *bounds("seed_input"), key="seed_input", step=1,
                           help="Bestimmt die zehn Konfliktgraphen im Reiter „Wo es schadet“ (Färbung): ihre Seeds sind dieser Wert bis dieser Wert + 9. Die Löser-Zufalls-Seeds sind davon getrennt.")
    st.button("🎲 Neuer Zufalls-Seed", width="stretch", on_click=randomize_seed)
    budget = st.select_slider("Konfliktbudget", options=C.BUDGET_OPTIONEN, key="budget_slider",
                              help="Nach so vielen Konflikten bricht ein live gerechneter Lauf ab; die Konfliktzahl ist dann eine untere Schranke. Die vorgerechneten Reihen haben eigene Budgets.")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Was ändert das Brechen von Symmetrien an der Zahl der Konflikte?")
daten = _daten()
kind, text = E.verdict_kern(daten)
getattr(st, kind)(text)
st.caption("Die Zählung stammt aus den vorgerechneten Reihen (Datei `" + C.MESSUNG_DATEI + "`, Messskript `" + C.MESSSKRIPT + "`), nicht aus einem Lauf dieser Sitzung.")
sf_zeilen = E.zeilen_schubfach(daten)
s4_zeilen = E.zeilen_schur(daten, "schur4")
z_sf, z_44 = sf_zeilen[-1], next(z for z in s4_zeilen if z["n"] == 44)
z_43 = next(z for z in s4_zeilen if z["n"] == 43)
c1, c2, c3 = st.columns(3)
c1.metric(f"Schubfach h = {z_sf['h']}: Konflikte ohne → mit", f"{E.zahl(z_sf['ohne'])} → {E.zahl(z_sf['mit'])}")
c2.metric("Schur, 4 Mengen, n = 44 (ein Lauf)",f"{E.zahl(z_44['ohne'])} → {E.zahl(z_44['mit'])}")
c3.metric("Schur, 4 Mengen, n = 43 (ein Lauf)", f"{E.zahl(z_43['ohne'])} → {E.zahl(z_43['mit'])}")

st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(list(C.REITER_NAMEN))

# --- Experiment 1 --------------------------------------------------------------------------------------------------------------------------

with tab1:
    st.subheader("🔬 Von Hand: kleine Aufgaben, alles nachzählbar")
    st.caption("Schubfach: Einheitspropagation ohne und mit der Regel auf Stufe 0, Schritt für Schritt. Schur: alle Lösungen zählen, Bahnen unter den Vertauschungen der Mengen, Vertreter anzeigen. "
               "Die Zählung der Lösungen ist exakt (eigene Aufzählung, unabhängig vom CDCL).")
    sub1, sub2 = st.tabs(["Schubfach: Aufträge auf Rampen", "Schur: Zahlen auf drei Mengen"])
    with sub1:
        h = st.slider("Rampen h (es gibt h + 1 paarweise unverträgliche Aufträge)", *bounds("h_hand_slider"), key="h_hand_slider",
                      help="Variable x(p, l) heißt: Auftrag p fährt Rampe l an (p ab 0, l ab 0). Mit h + 1 Aufträgen auf h Rampen gibt es keine Lösung.")
        inst = S.schubfach_aufgabe(h)
        w_ohne, w_mit, m_ohne, m_mit, voll = _hand_schubfach(h)
        zusatz = SY.lochvorrang(h)
        st.markdown(f"**Aufgabe:** {S.beschreibung(inst)}.")
        kind, text = E.verdict_hand_schubfach(h, {"konflikt": w_ohne["konflikt"] is not None, "belegt": w_ohne["belegt"], "variablen": w_ohne["variablen"]},
                                              {"konflikt": w_mit["konflikt"] is not None, "belegt": w_mit["belegt"], "variablen": w_mit["variablen"]},
                                              len(inst.klauseln), len(zusatz), voll["loesungen"], voll["mit_brechung"])
        getattr(st, kind)(text)
        a, b, c = st.columns(3)
        a.metric("Klauseln der Aufgabe", len(inst.klauseln))
        b.metric("Klauseln des Lochvorrangs", len(zusatz), help="(h − 1)·(h + 1): für jeden Auftrag und jede Rampe ab 1 eine Klausel.")
        c.metric("Vertauschungen", f"{SY.bahnengroesse(h + 1)} · {SY.bahnengroesse(h)} = {SY.bahnengroesse(h + 1) * SY.bahnengroesse(h)}",
                 help="Die Aufträge lassen sich untereinander vertauschen ((h + 1)!), die Rampen auch (h!). Der Lochvorrang bricht die Vertauschungen der Rampen.")
        with st.expander("Alle Klauseln der Aufgabe", expanded=False):
            for i, k in enumerate(inst.klauseln, 1):
                st.markdown(f"{i}. {S.klausel_text(k, 'schubfach', h)}")
        st.markdown("**Die Regel in Klauseln** (Lochvorrang: Auftrag p nur in Rampe l ≥ 1, wenn ein früherer Auftrag Rampe l − 1 hat)")
        for i, k in enumerate(zusatz, len(inst.klauseln) + 1):
            st.markdown(f"{i}. {S.klausel_text(k, 'schubfach', h)}")
        st.markdown("**Einheitspropagation auf Stufe 0**")
        links, rechts = st.columns(2)
        with links:
            st.markdown("*Ohne die Regel*")
            if not w_ohne["schritte"]:
                st.info(f"Keine Klausel hat ein einziges offenes Literal: nichts folgt, {w_ohne['belegt']} von {w_ohne['variablen']} Variablen belegt, kein Widerspruch.")
            else:
                st.write(f"{len(w_ohne['schritte'])} Schritte")
        with rechts:
            st.markdown("*Mit der Regel*")
            schritte = w_mit["schritte"]
            gesamt = len(schritte)
            schritt = st.slider("Schritt", 0, gesamt, gesamt, key=f"schritt_hand_{h}", help="Zeigt die Folgerungen bis zum gewählten Schritt; Schritt 0 ist der Anfang.")
            zeilen = []
            for nr, (lit, ci) in enumerate(schritte[:schritt], 1):
                zeilen.append([nr, S.literal_text(lit, "schubfach", h) + " (erzwungen)", f"Klausel {ci + 1}: {S.klausel_text(w_mit['klauseln'][ci], 'schubfach', h)}"])
            if zeilen:
                _tabelle(zeilen, ["Schritt", "Folgerung", "wegen"])
            if schritt == gesamt and w_mit["konflikt"] is not None:
                ci = w_mit["konflikt"]
                st.success(f"Widerspruch gefunden: Klausel {ci + 1} ({S.klausel_text(w_mit['klauseln'][ci], 'schubfach', h)}) ist verletzt, ohne dass der Löser eine Entscheidung getroffen hat. "
                         f"Belegt sind {w_mit['belegt']} von {w_mit['variablen']} Variablen.")
        st.markdown("**Der CDCL-Löser auf derselben Aufgabe** (Standardlauf, Löser-Zufalls-Seed 0)")
        _tabelle([["ohne Regel", m_ohne.antwort_text, E.zahl(m_ohne.konflikte), E.zahl(m_ohne.entscheidungen)],
                  ["mit Lochvorrang", m_mit.antwort_text, E.zahl(m_mit.konflikte), E.zahl(m_mit.entscheidungen)]], ["Aufgabe", "Antwort", "Konflikte", "Entscheidungen"])
        st.markdown(f"**Lösungen zählen: die erfüllbare Fassung** ({h} Aufträge auf {h} Rampen)")
        _tabelle([[h, E.zahl(voll["loesungen"]), E.zahl(voll["bahnen"]), E.zahl(voll["mit_brechung"])]], ["Aufträge = Rampen", "Lösungen ohne Regel", "Bahnen", "Lösungen mit Lochvorrang"])
        st.caption(f"Jede Zuordnung der {h} Aufträge auf die {h} Rampen ist eine Lösung ({h}! Zuordnungen); sie gehen durch Vertauschen der Rampen ineinander über (eine Bahn). "
                   "Mit Lochvorrang bleibt genau ein Vertreter je Bahn: Erfüllbarkeit bleibt, die Lösungen schrumpfen.")
    with sub2:
        n = st.slider("Zahlen 1 bis n", *bounds("schur_hand_slider"), key="schur_hand_slider",
                      help="Die Zahlen 1 bis n sollen auf 3 Mengen verteilt werden, sodass in keiner Menge a + b = c gilt (a = b erlaubt). Ab n = 14 gibt es keine Lösung (S(3) = 13).")
        erg = _hand_schur(n)
        zusatz = SY.wertevorrang_schur(n, C.SCHUR_K_HAND)
        st.markdown(f"**Aufgabe:** {S.beschreibung(I.schur(n, C.SCHUR_K_HAND))}.")
        kind, text = E.verdict_hand_schur(n, C.SCHUR_K_HAND, erg, len(zusatz))
        getattr(st, kind)(text)
        a, b, c, d = st.columns(4)
        a.metric("Lösungen", E.zahl(erg["loesungen"]))
        b.metric("Bahnen", E.zahl(erg["bahnen"]))
        c.metric("Lösungen mit Wertevorrang", E.zahl(erg["mit_brechung"]))
        d.metric("Klauseln des Wertevorrangs", len(zusatz), help="(k − 1)·n: für jede Zahl und jede Farbe ab 1 eine Klausel; für Zahl 1 eine Einheitsklausel.")
        if erg["beispiele"]:
            st.markdown("**Lösungen mit Wertevorrang** (bis zu drei; Mengen durch | getrennt)")
            for f in erg["beispiele"]:
                st.markdown(f"- {_mengen_text(f, C.SCHUR_K_HAND)}")
            st.caption("Jede dieser Lösungen ist der Vertreter einer Bahn: Die Menge mit der Zahl 1 steht vorn, danach die Menge mit der kleinsten übrigen Zahl, und so weiter.")
        st.markdown("**Drei Aufgaben nebeneinander**")
        zeilen = []
        for m in (12, 13, 14):
            e = _hand_schur(m)
            zeilen.append([m, E.zahl(e["loesungen"]), E.zahl(e["bahnen"]), E.zahl(e["mit_brechung"]), len(SY.wertevorrang_schur(m, C.SCHUR_K_HAND))])
        _tabelle(zeilen, ["n", "Lösungen", "Bahnen", "Lösungen mit Wertevorrang", "Klauseln der Regel"])
        with st.expander("Die Klauseln des Wertevorrangs", expanded=False):
            for i, k in enumerate(zusatz, 1):
                st.markdown(f"{i}. {S.klausel_text(k, 'schur', C.SCHUR_K_HAND)}")

# --- Experiment 2 --------------------------------------------------------------------------------------------------------------------------

with tab2:
    st.subheader("🔬 Schubfach wächst: jede Rampe mehr kostet ein Mehrfaches, mit Lochvorrang bleibt es ein Konflikt")
    st.caption("h + 1 paarweise unverträgliche Aufträge auf h Rampen: unerfüllbar. Ohne Regel zählt der Löser für jede weitere Rampe ein Mehrfaches an Konflikten (Faktor in der Meldung unten); "
               "mit dem Lochvorrang findet die Einheitspropagation den Widerspruch ohne Entscheidung. Ein Lauf je Zeile mit dem Standard-Löser ohne Zufall (Löser-Zufalls-Seed 0).")
    sf_meta = daten["meta"]
    kind, text = E.verdict_schubfach(sf_zeilen, sf_meta["budget_schubfach"], vorgerechnet=True)
    getattr(st, kind)(text)
    st.plotly_chart(V.build_balken([z["h"] for z in sf_zeilen], [z["ohne"] for z in sf_zeilen], [z["mit"] for z in sf_zeilen], [z["ohne_abbruch"] for z in sf_zeilen],
                                   [z["mit_abbruch"] for z in sf_zeilen], "Rampen h", "mit Lochvorrang"), width="stretch", key="schubfach_vorgerechnet")
    st.caption(f"Vorgerechnet mit `{sf_meta['skript']}` (Datei `{C.MESSUNG_DATEI}`), **nicht live**: Budget {E.zahl(sf_meta['budget_schubfach'])} Konflikte. "
               "Für h = 8 dauert der Lauf ohne Regel mit dem Python-CDCL Minuten; deshalb steht h = 8 nur hier, live reicht der Regler bis h = 7.")
    st.markdown("**Selbst nachrechnen** (live, mit dem Konfliktbudget der Seitenleiste)")
    h_bis = st.slider("Live bis h", *bounds("h_bis_slider"), key="h_bis_slider", help="Gerechnet werden h = 3 bis zu diesem Wert, je ohne und mit Lochvorrang.")
    if h_bis >= 7:
        st.caption("Bei h = 7 braucht der Lauf ohne Regel mehrere tausend Konflikte; ein Fortschrittsbalken zählt die fertigen Zeilen, ein zweiter Klick mit denselben Einstellungen antwortet aus dem Zwischenspeicher.")
    sf_schluessel = (h_bis, budget)
    if st.button("▶ Läufe rechnen", key="schubfach_rechnen"):
        st.session_state["schubfach_ergebnis"] = (sf_schluessel, *L.schubfach(*sf_schluessel))
    erg = st.session_state.get("schubfach_ergebnis")
    if erg is None or erg[0] != sf_schluessel:
        st.info("Für diese Einstellung ist noch nichts gerechnet. Mit „Läufe rechnen“ starten.")
    else:
        _, live, sek = erg
        kind, text = E.verdict_schubfach(live, budget, vorgerechnet=False)
        getattr(st, kind)(text)
        _tabelle([[z["h"], _plus(z["ohne"], z["ohne_abbruch"]), _plus(z["mit"], z["mit_abbruch"])] for z in live], ["Rampen h", "Konflikte ohne Regel", "Konflikte mit Lochvorrang"])
        vorg = {z["h"]: z for z in sf_zeilen}
        if budget == sf_meta["budget_schubfach"]:
            gleich = all(vorg[z["h"]]["ohne"] == z["ohne"] and vorg[z["h"]]["mit"] == z["mit"] for z in live)
            st.caption("Die live gerechneten Zahlen " + ("stimmen mit den vorgerechneten überein (der Standardlauf ist deterministisch)." if gleich else "weichen von den vorgerechneten ab."))
        st.caption(f"Rechenzeit dieser Läufe: {sek:.1f} s (nur Anzeige, kein Befund).")

# --- Experiment 3 --------------------------------------------------------------------------------------------------------------------------

with tab3:
    st.subheader("🔬 Schur: Zahlen auf Mengen ohne a + b = c")
    st.caption("Teil 1 rechnet live (3 Mengen, n = 11 bis 14). Teil 2 zeigt vorgerechnete Werte für 4 Mengen an der Grenze (n = 43, 44, 45); der Python-CDCL braucht dort Minuten bis Stunden. "
               "Ein Lauf je Zeile mit dem Standard-Löser ohne Zufall (Löser-Zufalls-Seed 0).")
    st.markdown("**Teil 1: 3 Mengen, live** (S(3) = 13: bis n = 13 erfüllbar, ab n = 14 nicht)")
    s3 = _schur3_zeilen(C.SCHUR3_N, C.BUDGET_SCHUR4)
    kind, text = E.verdict_schur(s3, 3, C.BUDGET_SCHUR4, vorgerechnet=False)
    getattr(st, kind)(text)
    n3 = st.select_slider("Zahlen 1 bis n (Einzelheiten)", options=C.SCHUR3_N, key="schur3_select", help="Wählt die Zeile, die unten mit allen Zählern gezeigt wird; die Tabelle zeigt alle vier.")
    z3 = next(z for z in s3 if z["n"] == n3)
    a, b, c = st.columns(3)
    a.metric(f"n = {n3}: Antwort", z3["antwort_ohne"])
    b.metric("Konflikte ohne Regel", E.zahl(z3["ohne"]))
    c.metric("Konflikte mit Wertevorrang", E.zahl(z3["mit"]))
    st.plotly_chart(V.build_balken([z["n"] for z in s3], [z["ohne"] for z in s3], [z["mit"] for z in s3], x_titel="Zahlen 1 bis n", name_mit="mit Wertevorrang"),
                    width="stretch", key="schur3_balken")
    _tabelle([[z["n"], z["antwort_ohne"], E.zahl(z["ohne"]), E.zahl(z["mit"]), klasse] for z, klasse in zip(s3, (E.klasse_der_zeile(z) for z in s3))],
             ["n", "Antwort", "Konflikte ohne", "Konflikte mit Wertevorrang", "mit Regel"])
    st.caption("Bei höchstens 10 Konflikten auf beiden Seiten gilt „etwa gleich“ (1 gegen 2 Konflikte ist kein Befund).")

    st.markdown("**Teil 2: 4 Mengen, vorgerechnet** (S(4) = 44 nach Golomb und Baumert 1965, als zitierter Wert; hier an den drei Aufgaben gemessen)")
    s4m = daten["meta"]
    kind, text = E.verdict_schur(s4_zeilen, 4, s4m["budget_schur4"], vorgerechnet=True)
    getattr(st, kind)(text)
    n4 = st.select_slider("Zahlen 1 bis n (Einzelheiten)", options=C.SCHUR4_N, key="schur4_select", help="Wählt die Zeile, die unten mit allen Zählern gezeigt wird.")
    z4 = next(z for z in daten["schur4"] if z["n"] == n4)
    a, b, c = st.columns(3)
    a.metric(f"n = {n4}: Antwort mit Wertevorrang", z4["mit"]["antwort"])
    b.metric("Konflikte ohne Regel", _plus(z4["ohne"]["konflikte"], z4["ohne"]["antwort"].startswith("Abbruch")))
    c.metric("Konflikte mit Wertevorrang", _plus(z4["mit"]["konflikte"], z4["mit"]["antwort"].startswith("Abbruch")))
    st.plotly_chart(V.build_balken([z["n"] for z in s4_zeilen], [z["ohne"] for z in s4_zeilen], [z["mit"] for z in s4_zeilen], [z["ohne_abbruch"] for z in s4_zeilen],
                                   [z["mit_abbruch"] for z in s4_zeilen], "Zahlen 1 bis n", "mit Wertevorrang"), width="stretch", key="schur4_balken")
    _tabelle([[z["n"], z["antwort_ohne"], _plus(z["ohne"], z["ohne_abbruch"]), z["antwort_mit"], _plus(z["mit"], z["mit_abbruch"]), E.klasse_der_zeile(z)] for z in s4_zeilen],
             ["n", "Antwort ohne Regel", "Konflikte ohne", "Antwort mit Regel", "Konflikte mit Wertevorrang", "mit Regel"])
    st.caption(f"Vorgerechnet mit `{s4m['skript']}` (Datei `{C.MESSUNG_DATEI}`), **nicht live**: Vormessung mit dem Python-CDCL, Budget {E.zahl(s4m['budget_schur4'])} Konflikte; „+“ heißt Abbruch am Budget "
               "(untere Schranke). Dass S(4) = 44 ist, ist ein zitierter Wert; die Messung zeigt nur, was der Löser an diesen Aufgaben braucht.")

# --- Experiment 4 --------------------------------------------------------------------------------------------------------------------------

with tab4:
    st.subheader("🔬 Wo es schadet: leichte Aufgaben und der Unterschied zwischen einem Lauf und vielen")
    st.caption("Schur mit 4 Mengen, n zwischen 38 und 43: leicht erfüllbar. Der Standardlauf ohne Zufall braucht dort 0 bis 6 Konflikte; mit 20 Löser-Zufalls-Seeds (zufälliger Start der Aktivitäten) "
               "sieht das Bild anders aus. Darunter die Färbung unerfüllbarer Aufgaben. Zufalls-3-SAT hat typischerweise keine Farbsymmetrie (nicht gemessen): dort gibt es meist nichts zu brechen.")
    st.markdown("**Teil 1: Schur mit 4 Mengen, 20 Löser-Zufalls-Seeds (vorgerechnet)**")
    n_s = st.select_slider("Zahlen 1 bis n", options=C.SCHADET_N_REIHE, key="schadet_n_select", help="n = 43 ist die Aufgabe, an der die Plan-Vormessung 6 → 352 Konflikte zeigte (ein Lauf).")
    zs_daten = next(z for z in daten["schadet"] if z["n"] == n_s)
    standard = (zs_daten["standard"]["ohne"]["konflikte"], zs_daten["standard"]["mit"]["konflikte"])
    kontrolle = None
    if n_s == C.SCHADET_N and "kontrolle" in daten:
        k_d = daten["kontrolle"]
        kontrolle = (k_d["ohne"]["konflikte"], k_d["mit"]["konflikte"])
    kind, text = E.verdict_schadet(n_s, C.SCHADET_K, zs_daten["ohne"]["konflikte"], zs_daten["mit"]["konflikte"], zs_daten["ohne"]["abbrueche"], zs_daten["mit"]["abbrueche"],
                                   daten["meta"]["budget_schadet"], standard, kontrolle)
    getattr(st, kind)(text)
    st.plotly_chart(V.build_streuung({"ohne Regel": zs_daten["ohne"]["konflikte"], "mit Wertevorrang": zs_daten["mit"]["konflikte"]}), width="stretch", key="schadet_box")
    st.caption("Jeder Punkt ist ein Lauf mit einem Löser-Zufalls-Seed (1 bis 20); Seed s ohne und Seed s mit Regel starten dieselben zufälligen Aktivitäten, rechnen aber auf verschiedenen Formeln.")
    _tabelle([[z["n"], E.zahl(z["standard"]["ohne"]["konflikte"]), E.zahl(z["standard"]["mit"]["konflikte"]),
               *(lambda zz: [E.zahl(zz["median_ohne"]), E.zahl(zz["median_mit"]), E.zahl(zz["max_ohne"]), E.zahl(zz["max_mit"]), f"{zz['laeufe_mehr']} von {zz['n']}", E.p_text(zz["p"])])(
                   E.zusammenfassung_seeds(z["ohne"]["konflikte"], z["mit"]["konflikte"]))]
              for z in daten["schadet"]],
             ["n", "Standardlauf ohne", "Standardlauf mit", "Median ohne (20 Seeds)", "Median mit", "Maximum ohne", "Maximum mit", "Läufe mit mehr Konflikten", "Rangsummentest"])
    st.markdown("**Selbst nachrechnen** (live, mit dem Konfliktbudget der Seitenleiste)")
    seeds = st.slider("Löser-Zufalls-Seeds", *bounds("seeds_slider"), key="seeds_slider", help="Je Seite so viele Läufe (Seeds 1 bis zu diesem Wert) derselben Aufgabe.")
    live_schluessel = (n_s, seeds, budget)
    if st.button("▶ Seeds rechnen", key="schadet_rechnen"):
        st.session_state["schadet_ergebnis"] = (live_schluessel, *L.schadet(*live_schluessel))
    erg = st.session_state.get("schadet_ergebnis")
    if erg is None or erg[0] != live_schluessel:
        st.info("Für diese Einstellung ist noch nichts gerechnet. Mit „Seeds rechnen“ starten.")
    else:
        _, live, sek = erg
        kind, text = E.verdict_schadet(n_s, C.SCHADET_K, live["ohne"]["konflikte"], live["mit"]["konflikte"], live["ohne"]["abbrueche"], live["mit"]["abbrueche"], budget)
        getattr(st, kind)(text)
        st.plotly_chart(V.build_streuung({"ohne Regel": live["ohne"]["konflikte"], "mit Wertevorrang": live["mit"]["konflikte"]}), width="stretch", key="schadet_box_live")
        st.caption(f"Rechenzeit dieser Läufe: {sek:.1f} s (nur Anzeige, kein Befund).")

    st.markdown("**Teil 2: Färbung unerfüllbarer Aufgaben, 10 Graphen je Zelle**")
    n_f = st.select_slider("Aufträge n (3 Rampen, mittlerer Grad 5)", options=C.FAERBUNG_N, key="faerbung_n_select", help="Zehn Konfliktgraphen mit den Seeds Zufalls-Seed bis Zufalls-Seed + 9 (Seitenleiste).")
    f_schluessel = (n_f, int(seed), budget)
    if st.button("▶ Graphen rechnen", key="faerbung_rechnen"):
        with st.spinner(f"Rechne 3 × {C.FAERBUNG_GRAPHEN} Läufe, je bis zu {E.zahl(budget)} Konflikte …"):
            st.session_state["faerbung_ergebnis"] = (f_schluessel, *_faerbung_live(*f_schluessel))
    erg_f = st.session_state.get("faerbung_ergebnis")
    zelle, quelle, f_budget = None, "", budget
    if erg_f is not None and erg_f[0] == f_schluessel:
        zelle, quelle = erg_f[1], f"live gerechnet in {erg_f[2]:.1f} s (nur Anzeige, kein Befund)"
    elif int(seed) == C.MESS_FAERBUNG_SEED:
        zelle = next(z for z in daten["faerbung"] if z["n"] == n_f)
        f_budget = daten["meta"]["budget_faerbung"]
        quelle = f"vorgerechnet mit `{daten['meta']['skript']}`, **nicht live**"
    if zelle is None:
        st.info("Für diesen Zufalls-Seed ist nichts vorgerechnet. Mit „Graphen rechnen“ starten.")
    else:
        for regel in (KANTE, WERT):
            zf = E.zusammenfassung_faerbung(zelle, regel)
            kind, text = E.verdict_faerbung(n_f, REGEL_NAMEN[regel], zf, f_budget)
            getattr(st, kind)(text)
        st.plotly_chart(V.build_streuung({"ohne Regel": zelle["regeln"]["ohne"], "erste Kante fest": zelle["regeln"][KANTE], "Wertevorrang": zelle["regeln"][WERT]},
                                         "Konflikte je Graph"), width="stretch", key="faerbung_box")
        st.caption(f"Standardlauf ohne Zufall, ein Lauf je Graph und Regel, Budget {E.zahl(f_budget)} Konflikte; Zelle {quelle}. Antworten aller Läufe gleich (Äquierfüllbarkeit): "
                   f"{'ja' if zelle['antworten_gleich'] else 'nein'}.")

    st.markdown("**Zählung über alle Zellen** (aus den vorgerechneten Reihen)")
    kind, text = E.verdict_zellen(E.zellen_klassen(daten))
    getattr(st, kind)(text)
    _tabelle([[name, klasse] for name, klasse in E.zellen_klassen(daten).items()], ["Zelle", "mit Brechung (Median)"])

sync_query_params({k: st.session_state.get(k, spec.default) for k, spec in SETTING_SPECS.items()})

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist |
|---|---|
| **Drei Aufgabenfamilien** (Schubfach h bis 8, Schur mit 3 und 4 Mengen, 3-Färbung mit Grad 5 und n = 60 bis 120) | Die Aussagen gelten für diese Familien und Größen. Zufalls-3-SAT hat typischerweise keine Farbsymmetrie (nicht gemessen), industrielle Formeln und andere Größen sind nicht gemessen. |
| **Handgeschriebene Regeln für drei Aufgabenarten** | Es gibt keine automatische Symmetrieerkennung (Graphautomorphismen), keine allgemeine lexikographische Ordnung und keine dynamische Brechung während der Suche; wo die Regel nicht zur Symmetrie passt, bricht sie nichts. |
| **Ein Standardlauf je Zeile** (Schubfach, Schur mit 3 und 4 Mengen, Färbung) | Der Standardlauf ohne Zufall ist ein einzelner Lauf. Der Reiter „Wo es schadet“ zeigt, dass ein einzelner Lauf (6 Konflikte ohne Regel bei n = 43) vom Median über Löser-Zufalls-Seeds weit abweichen kann. |
| **Schubfach: eigene Messung** | Dass der Lochvorrang das Schubfach durch Einheitspropagation erledigt, ist hier gemessen; eine Literaturquelle dazu wurde nicht gelesen. |
| **Zählgrößen statt Sekunden** | Gezählt werden Konflikte, Entscheidungen und Propagationen. Konflikte sind nicht gleich teuer; eine Aussage über die Laufzeit machen die Zahlen nicht. Mit der Regel kommen Klauseln hinzu. |
| **Ein Löser** (CDCL mit Aktivität, Phasenspeicher, Luby-Neustarts, ohne Löschen) | Andere Einstellungen, andere Löser und Cube-and-Conquer sind nicht gemessen; „schadet“ und „hilft“ gelten für diesen Löser. |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    # erklaerseite:lesehilfe:start (erzeugt von tools/set_demo_explainer.py (Website-Repo) aus tools/content/explainers/symmetrie-brechen-erklaert.json, nicht von Hand ändern)
    st.markdown(
        r"""
**Lesehilfe.** Gegeben ist eine Formel $F$ in konjunktiver Normalform und eine Gruppe $G$ von Umbenennungen der Variablen, die jede Lösung von $F$ in eine Lösung überführen. Gesucht sind zusätzliche Klauseln $R$, sodass $F \wedge R$ genau dann erfüllbar ist, wenn $F$ erfüllbar ist, und von jeder Bahn nur einen Vertreter zulässt. Gemessen wird der Aufwand in Konflikten, nicht in Sekunden.

| Symbol | Bedeutung |
|---|---|
| $F,\ G$ | die Formel und die Gruppe der Umbenennungen (Symmetrien) |
| $R$ | die zusätzlichen Klauseln der Brechung |
| $k,\ n,\ h$ | Zahl der Farben, Mengen oder Rampen; Zahl der Zahlen bzw. Knoten; Zahl der Rampen beim Schubfach |
| $x_{i,c}$ | Zahl bzw. Knoten $i$ hat Farbe $c$ |
| $x_{p,l}$ | Auftrag $p$ fährt Rampe $l$ an |

[Schritt für Schritt erklärt, mit Herleitung und Literatur](https://sebastianhanisch.net/symmetrie-brechen-erklaert.html#fachleute)
        """
    )
    # erklaerseite:lesehilfe:end
    st.markdown(
        r"""
**Gegeben und gesucht.** Gegeben ist eine Formel $F$ in konjunktiver Normalform und eine Gruppe $G$ von Umbenennungen der Variablen, die jede Lösung von $F$ in eine Lösung von $F$ überführen
(eine **Symmetrie**). Gesucht ist eine Formel $F' = F \wedge R$, die genauso erfüllbar ist wie $F$ und von jeder Bahn der Gruppe nur einen Vertreter zulässt. Zu jeder der drei Aufgabenarten
ist $R$ eine Liste zusätzlicher Klauseln.

| Symbol | Bedeutung |
|---|---|
| $k$ | Zahl der Farben, Mengen oder Rampen |
| $n$ | Zahl der Zahlen (Schur) bzw. Knoten (Färbung) |
| $h$ | Zahl der Rampen beim Schubfach (es gibt $h+1$ Aufträge) |
| $x_{i,c}$ | Zahl bzw. Knoten $i$ hat Farbe $c$ (Schur: $i = 1, \dots, n$; Färbung: $i = 0, \dots, n-1$) |
| $x_{p,l}$ | Auftrag $p = 0, \dots, h$ fährt Rampe $l = 0, \dots, h-1$ an |
| $R$ | die zusätzlichen Klauseln der Brechung |

**Aufgaben.** Schur: jede Zahl hat genau eine Farbe, und für $a + b = c$ (mit $a = b$) liegen nie alle drei in derselben Farbe,

$$\neg x_{a,c} \vee \neg x_{b,c} \vee \neg x_{a+b,c} \qquad \text{für alle } a \le b,\ a + b \le n,\ c = 0, \dots, k-1.$$

Schubfach: jeder Auftrag hat mindestens eine Rampe, jede Rampe höchstens einen Auftrag,

$$\bigvee_{l=0}^{h-1} x_{p,l} \quad (p = 0, \dots, h), \qquad \neg x_{p,l} \vee \neg x_{q,l} \quad (p < q).$$

**Wertevorrang** (Schur und Färbung): Farbe $c \ge 1$ darf nur vergeben werden, wenn eine frühere Zahl die Farbe $c-1$ hat,

$$\neg x_{i,c} \vee \bigvee_{j < i} x_{j,c-1} \qquad \text{für } i \text{ in der Reihenfolge der Zahlen},\ c = 1, \dots, k-1.$$

Das sind $(k-1)\,n$ Klauseln; für die erste Zahl ist die Klausel die Einheitsklausel $\neg x_{1,c}$.

**Lochvorrang** (Schubfach): Auftrag $p$ darf Rampe $l \ge 1$ nur anfahren, wenn ein früherer Auftrag Rampe $l-1$ anfährt,

$$\neg x_{p,l} \vee \bigvee_{q < p} x_{q,l-1} \qquad \text{für } p = 0, \dots, h,\ l = 1, \dots, h-1.$$

Das sind $(h-1)(h+1)$ Klauseln.

**Erste Kante fest** (Färbung): für die erste Kante $\{a, b\}$ des Graphen die Einheitsklauseln $x_{a,0}$ und $x_{b,1}$.

**Erhält die Erfüllbarkeit.** Sei $\sigma$ eine Lösung von $F$. Beim Wertevorrang nummeriert man die Farben nach ihrem ersten Auftreten um (nicht benutzte Farben zuletzt): die neue Belegung ist
eine Lösung von $F$ (eine Vertauschung der Farben ist eine Symmetrie) und erfüllt $R$. Beim Lochvorrang ordnet man die besetzten Rampen nach dem kleinsten Auftrag darin; jede Rampe hat höchstens
einen Auftrag, daher hat die Rampe $l-1$ einen früheren Auftrag als die Rampe $l$. Bei der ersten Kante sind $a$ und $b$ verschieden gefärbt; man macht ihre Farben zu 0 und 1. Umgekehrt ist jede
Lösung von $F \wedge R$ eine Lösung von $F$, weil nur Klauseln hinzukommen. Also gilt: $F$ ist genau dann erfüllbar, wenn $F \wedge R$ erfüllbar ist.

**Bahnen.** Benutzt eine Lösung $m$ der $k$ Farben, hat ihre Bahn unter den $k!$ Farbvertauschungen $k!/(k-m)!$ Elemente; für $m \ge k-1$ sind das $k!$. Wenn jede Lösung mindestens $k-1$ Farben benutzt,
gilt also

$$\#\text{Lösungen mit Wertevorrang} = \#\text{Bahnen} = \frac{\#\text{Lösungen}}{k!}.$$

Beispiel: Schur mit $k = 3$ und $n = 13$ hat $18$ Lösungen, also $18/3! = 3$ Bahnen und 3 Lösungen mit Wertevorrang.

**Annahmen der Messung.**

| Annahme | Wert |
|---|---|
| Löser | CDCL mit 1-UIP, Aktivität (VSIDS in der MiniSat-Variante, Zerfall 0,95), Phasenspeicher, Luby-Neustarts (Einheit 32), Watched Literals, ohne Löschen |
| Standardlauf | Löser-Zufalls-Seed 0, ohne zufälligen Start der Aktivitäten |
| Löser-Zufalls-Seeds | zufälliger Start der Aktivitäten aus dem SplitMix64; nur mit diesem Start wirkt der Seed |
| Budget | Schubfach 100 000, Schur mit 4 Mengen 300 000, Färbung 100 000 Konflikte; ein Abbruch zählt mit dem Budget |
| Messgröße | Konflikte bis zur Antwort |

**Literatur.** M. J. H. Heule: Schur Number Five. arXiv 1711.08076, 2017 (Volltext gelesen: die Vertauschung der 5 Farben, 5! = 120, wird durch eine lexikographische Ordnung der Farben gebrochen; der Wertevorrang dieser Demo ist dieselbe Familie; S(3) = 13 und S(4) = 44 werden dort nach Golomb und Baumert 1965 zitiert).
Crawford u. a. 1996 (nicht gelesen; im Heule-Papier als Quelle der lexikographischen Ordnung der Farben genannt).
Für das Schubfach mit Symmetriebrechung wurde keine Quelle gelesen: die Aussage dieser Demo ist eine eigene Messung.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [SAT und CP: Konfliktlernen bis Wahl](https://sebastianhanisch.net/konzepte-sat-constraint-programming.html)."
)
