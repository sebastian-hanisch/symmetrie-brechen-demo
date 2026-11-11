"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import plotly.graph_objects as go

import smb_constants as C


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=360):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", y=-0.25), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def build_balken(beschriftungen, ohne, mit, abbrueche_ohne=(), abbrueche_mit=(), x_titel="", name_mit="mit Brechung"):
    """Gruppierte Balken der Konflikte je Aufgabe, ohne und mit Brechung, logarithmische Achse (linear, falls ein Wert 0 ist). Abbrüche am Budget sind schraffiert (untere Schranke)."""
    fig = go.Figure()
    for name, werte, farbe, abbr in (("ohne Brechung", ohne, C.COLOR_OHNE, abbrueche_ohne), (name_mit, mit, C.COLOR_MIT, abbrueche_mit)):
        abbr = list(abbr) if len(abbr) else [False] * len(werte)
        fig.add_trace(go.Bar(x=[str(b) for b in beschriftungen], y=werte, name=name, marker=dict(color=farbe, pattern_shape=["/" if a else "" for a in abbr]),
                             text=[(">= " if a else "") + f"{w:,}".replace(",", " ") for w, a in zip(werte, abbr)], textposition="outside",
                             hovertemplate="%{x}: %{y} Konflikte<extra>" + name + "</extra>"))
    fig.update_layout(barmode="group")
    fig.update_xaxes(title_text=x_titel, type="category")
    log = min(list(ohne) + list(mit)) > 0
    fig.update_yaxes(title_text="Konflikte (logarithmisch)" if log else "Konflikte", type="log" if log else "linear")
    return _base(fig, 380)


def build_streuung(konflikte_je_variante: dict, titel_y="Konflikte (Löser-Zufalls-Seeds)"):
    """Kastendiagramm der Konflikte über die Löser-Zufalls-Seeds, eine Spur je Variante ({Name: Liste}), alle Punkte sichtbar, logarithmische Achse (linear, falls ein Wert 0 ist)."""
    fig = go.Figure()
    farben = [C.COLOR_OHNE, C.COLOR_MIT, C.COLOR_LINE]
    for i, (name, werte) in enumerate(konflikte_je_variante.items()):
        fig.add_trace(go.Box(y=werte, name=name, boxpoints="all", jitter=0.4, pointpos=0, marker=dict(color=farben[i % len(farben)], size=5),
                             line=dict(color=farben[i % len(farben)]), boxmean=False, hovertemplate="%{y} Konflikte<extra></extra>"))
    log = min(min(w) for w in konflikte_je_variante.values()) > 0
    fig.update_yaxes(title_text=titel_y + (", logarithmisch" if log else ""), type="log" if log else "linear")
    fig.update_layout(showlegend=False)
    return _base(fig, 380)
