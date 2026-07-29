"""
figuras_ml.py — Capa de figuras Plotly de los modulos de machine learning.
Proyecto: transportation-analytics

Misma interfaz y paleta que figuras.py: cada funcion recibe tablas ya
cargadas (ver data_ml.py) y devuelve una figura Plotly lista para
st.plotly_chart. Hereda la paleta azul del dashboard para coherencia visual.

Modulo 1 (series):    fig_pronostico(serie, pronostico)
Modulo 2 (regresion): fig_comparacion_r2(comp), fig_importancia(imp),
                      fig_scatter_pred(scatter)
Modulo 3 (clasif):    fig_balance(balance), fig_comparacion_auc(comp),
                      fig_matriz_confusion(matriz), fig_roc(roc)
Modulo 4 (cluster):   fig_seleccion_k(sel), fig_pca(pca, nombres),
                      fig_perfil_grupos(resumen)
"""

import plotly.express as px
import plotly.graph_objects as go

# --- Paleta (heredada de figuras.py para coherencia) ---
AZUL_OSCURO = "#1F4E66"
AZUL_MEDIO  = "#4E8CA8"
AZUL_CLARO  = "#8FBFD9"
AZUL_PALIDO = "#C9DCE8"
ROJO        = "#C1443C"   # SOLO anomalias / alertas
GRIS        = "#A8A8A8"
ARENA       = "#D4B483"
VERDE       = "#5B8C5A"   # SOLO para "bueno" (a tiempo, confiable)

# Colores por grupo del clustering (modulo 4)
COLOR_GRUPO = {
    0: ROJO,          # Problematicos
    1: ARENA,         # Parcel
    2: AZUL_OSCURO,   # Gigantes
    3: AZUL_MEDIO,    # Nucleo confiable
}


def _base_layout(fig, alto=380):
    """Layout base identico al de figuras.py."""
    fig.update_layout(
        template="plotly_white",
        height=alto,
        margin=dict(l=10, r=20, t=48, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="left", x=0, title_text=""),
        font=dict(size=13),
    )
    return fig


# ===========================================================================
# MODULO 1 — Series de tiempo
# ===========================================================================

def fig_pronostico(serie, pronostico):
    """Historico real + pronostico con banda de confianza."""
    # Separar historico de futuro usando la ultima fecha real
    ultima_real = serie["ds"].max()
    futuro = pronostico[pronostico["ds"] > ultima_real]

    fig = go.Figure()

    # Banda de confianza (primero, para que quede al fondo)
    fig.add_trace(go.Scatter(
        x=list(pronostico["ds"]) + list(pronostico["ds"][::-1]),
        y=list(pronostico["yhat_upper"]) + list(pronostico["yhat_lower"][::-1]),
        fill="toself", fillcolor="rgba(78,140,168,0.15)",
        line=dict(color="rgba(0,0,0,0)"), hoverinfo="skip",
        showlegend=True, name="Intervalo 95%",
    ))

    # Linea del pronostico (modelo)
    fig.add_trace(go.Scatter(
        x=pronostico["ds"], y=pronostico["yhat"],
        mode="lines", line=dict(color=AZUL_MEDIO, width=2),
        name="Pronostico",
        hovertemplate="%{x|%b %Y}: $%{y:,.0f}<extra></extra>",
    ))

    # Puntos del historico real
    fig.add_trace(go.Scatter(
        x=serie["ds"], y=serie["y"],
        mode="markers", marker=dict(color=AZUL_OSCURO, size=6),
        name="Gasto real",
        hovertemplate="%{x|%b %Y}: $%{y:,.0f}<extra></extra>",
    ))

    # Linea vertical: inicio del pronostico
    fig.add_vline(x=ultima_real, line=dict(color=ROJO, width=1.5, dash="dot"))

    fig.update_yaxes(title_text="Gasto mensual de flete (USD)",
                     tickformat="$,.0s")
    fig.update_xaxes(title_text="")
    _base_layout(fig, alto=420)
    return fig


# ===========================================================================
# MODULO 2 — Regresion
# ===========================================================================

def fig_comparacion_r2(comparacion):
    """Barras de R2: modelo lineal (malo) vs random forest (bueno)."""
    d = comparacion.copy()
    colores = [ROJO if r < 0 else AZUL_MEDIO for r in d["r2"]]
    fig = go.Figure(go.Bar(
        x=d["modelo"], y=d["r2"], marker_color=colores,
        text=[f"{r:.3f}" for r in d["r2"]], textposition="outside",
        cliponaxis=False,
        hovertemplate="%{x}: R2 = %{y:.4f}<extra></extra>",
    ))
    fig.add_hline(y=0, line=dict(color=GRIS, width=1))
    fig.update_yaxes(title_text="R2 (proporcion de varianza explicada)")
    fig.update_xaxes(title_text="")
    _base_layout(fig, alto=360)
    return fig


def fig_importancia(importancia):
    """Barras horizontales de importancia de variables."""
    d = importancia.sort_values("importancia")
    fig = go.Figure(go.Bar(
        x=d["importancia"], y=d["variable"], orientation="h",
        marker_color=AZUL_MEDIO,
        text=[f"{v*100:.1f}%" for v in d["importancia"]],
        textposition="outside", cliponaxis=False,
        hovertemplate="%{y}: %{x:.1%}<extra></extra>",
    ))
    fig.update_xaxes(title_text="Importancia relativa", showticklabels=False)
    fig.update_yaxes(title_text="")
    _base_layout(fig, alto=max(360, 30 * len(d)))
    return fig


def fig_scatter_pred(scatter):
    """Predicho vs real, con linea de prediccion perfecta."""
    d = scatter
    lim = max(d["costo_real"].max(), d["costo_predicho"].max())
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=d["costo_real"], y=d["costo_predicho"],
        mode="markers", marker=dict(color=AZUL_MEDIO, size=4, opacity=0.3),
        name="Embarques",
        hovertemplate="Real: $%{x:,.0f}<br>Predicho: $%{y:,.0f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=[0, lim], y=[0, lim], mode="lines",
        line=dict(color=ROJO, width=2, dash="dash"),
        name="Prediccion perfecta", hoverinfo="skip",
    ))
    fig.update_xaxes(title_text="Costo real (USD)", tickformat="$,.0s")
    fig.update_yaxes(title_text="Costo predicho (USD)", tickformat="$,.0s")
    _base_layout(fig, alto=420)
    return fig


# ===========================================================================
# MODULO 3 — Clasificacion
# ===========================================================================

def fig_balance(balance):
    """Barras del balance de clases (a tiempo vs tarde)."""
    d = balance
    colores = [VERDE if c == "A tiempo" else ARENA for c in d["clase"]]
    fig = go.Figure(go.Bar(
        x=d["clase"], y=d["cantidad"], marker_color=colores,
        text=[f"{p}%" for p in d["porcentaje"]],
        textposition="outside", cliponaxis=False,
        hovertemplate="%{x}: %{y:,} embarques<extra></extra>",
    ))
    fig.update_yaxes(title_text="Numero de embarques", showticklabels=False)
    fig.update_xaxes(title_text="")
    _base_layout(fig, alto=360)
    return fig


def fig_comparacion_auc(comparacion):
    """Barras de AUC de los tres modelos (todos parecidos = limite en datos)."""
    d = comparacion.sort_values("AUC-ROC")
    fig = go.Figure(go.Bar(
        x=d["AUC-ROC"], y=d["Modelo"], orientation="h",
        marker_color=AZUL_MEDIO,
        text=[f"{v:.3f}" for v in d["AUC-ROC"]],
        textposition="outside", cliponaxis=False,
        hovertemplate="%{y}: AUC = %{x:.4f}<extra></extra>",
    ))
    # Linea del azar (0.5)
    fig.add_vline(x=0.5, line=dict(color=ROJO, width=1.5, dash="dot"),
                  annotation_text="Azar (0.5)", annotation_position="top")
    fig.update_xaxes(title_text="AUC-ROC", range=[0, 0.75])
    fig.update_yaxes(title_text="")
    _base_layout(fig, alto=340)
    return fig


def fig_matriz_confusion(matriz):
    """Heatmap de la matriz de confusion."""
    d = matriz
    fig = go.Figure(go.Heatmap(
        z=d.values, x=list(d.columns), y=list(d.index),
        colorscale=[[0, AZUL_PALIDO], [1, AZUL_OSCURO]],
        text=d.values, texttemplate="%{text:,}",
        textfont=dict(size=16), showscale=False,
        hovertemplate="%{y} / %{x}: %{z:,}<extra></extra>",
    ))
    fig.update_yaxes(title_text="", autorange="reversed")
    fig.update_xaxes(title_text="")
    _base_layout(fig, alto=360)
    return fig


def fig_roc(roc):
    """Curva ROC vs linea del azar."""
    d = roc
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=d["fpr"], y=d["tpr"], mode="lines",
        line=dict(color=AZUL_MEDIO, width=2.5), name="Modelo",
        hovertemplate="FPR: %{x:.2f}<br>TPR: %{y:.2f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=[0, 1], y=[0, 1], mode="lines",
        line=dict(color=ROJO, width=2, dash="dash"), name="Azar",
        hoverinfo="skip",
    ))
    fig.update_xaxes(title_text="Tasa de falsos positivos")
    fig.update_yaxes(title_text="Tasa de verdaderos positivos")
    _base_layout(fig, alto=380)
    return fig


# ===========================================================================
# MODULO 4 — Segmentacion (clustering)
# ===========================================================================

def fig_seleccion_k(seleccion_k):
    """Metodo del codo + silueta, en dos ejes Y."""
    d = seleccion_k
    fig = go.Figure()
    # Inercia (eje izquierdo)
    fig.add_trace(go.Scatter(
        x=d["k"], y=d["inercia"], mode="lines+markers",
        line=dict(color=AZUL_OSCURO, width=2), name="Inercia (codo)",
        yaxis="y1", hovertemplate="K=%{x}: inercia %{y:.0f}<extra></extra>",
    ))
    # Silueta (eje derecho)
    fig.add_trace(go.Scatter(
        x=d["k"], y=d["silueta"], mode="lines+markers",
        line=dict(color=ARENA, width=2), name="Silueta",
        yaxis="y2", hovertemplate="K=%{x}: silueta %{y:.3f}<extra></extra>",
    ))
    # Marca la eleccion K=4
    fig.add_vline(x=4, line=dict(color=ROJO, width=1.5, dash="dot"),
                  annotation_text="K=4 elegido", annotation_position="top")
    fig.update_layout(
        yaxis=dict(title="Inercia", side="left"),
        yaxis2=dict(title="Silueta", side="right", overlaying="y"),
    )
    fig.update_xaxes(title_text="Numero de grupos (K)")
    _base_layout(fig, alto=380)
    return fig


def fig_pca(pca, nombres_grupos):
    """Scatter PCA 2D coloreado por grupo, con etiquetas de carrier."""
    d = pca
    fig = go.Figure()
    for g in sorted(d["grupo"].unique()):
        sub = d[d["grupo"] == g]
        nombre = nombres_grupos.get(str(g), f"Grupo {g}")
        fig.add_trace(go.Scatter(
            x=sub["pca_x"], y=sub["pca_y"], mode="markers+text",
            marker=dict(size=13, color=COLOR_GRUPO.get(g, AZUL_MEDIO),
                        line=dict(width=1, color="white")),
            text=sub["carrier_id"], textposition="top center",
            textfont=dict(size=8), name=nombre,
            hovertemplate="<b>%{text}</b><extra></extra>",
        ))
    fig.update_xaxes(title_text="Componente principal 1")
    fig.update_yaxes(title_text="Componente principal 2")
    _base_layout(fig, alto=460)
    return fig


def fig_perfil_grupos(resumen):
    """Heatmap normalizado del perfil de cada grupo."""
    d = resumen.copy()
    # Columnas de metricas (excluye n_carriers)
    cols = ["costo_prom_embarque", "costo_prom_kg", "pct_a_tiempo",
            "pct_danados", "num_embarques", "peso_total"]
    cols = [c for c in cols if c in d.columns]
    m = d[cols]
    # Normalizar cada columna 0-1 para comparar en color
    m_norm = (m - m.min()) / (m.max() - m.min())

    etiquetas_cols = {
        "costo_prom_embarque": "Costo/embarque",
        "costo_prom_kg": "Costo/kg",
        "pct_a_tiempo": "% a tiempo",
        "pct_danados": "% danados",
        "num_embarques": "Volumen",
        "peso_total": "Peso total",
    }
    x_labels = [etiquetas_cols.get(c, c) for c in cols]
    y_labels = [f"Grupo {i}" for i in d.index]

    fig = go.Figure(go.Heatmap(
        z=m_norm.values, x=x_labels, y=y_labels,
        colorscale=[[0, AZUL_PALIDO], [0.5, AZUL_MEDIO], [1, AZUL_OSCURO]],
        text=m.values, texttemplate="%{text:,.1f}",
        textfont=dict(size=11), showscale=False,
        hovertemplate="%{y} · %{x}: %{text:,.1f}<extra></extra>",
    ))
    fig.update_yaxes(title_text="", autorange="reversed")
    fig.update_xaxes(title_text="", side="bottom")
    _base_layout(fig, alto=360)
    return fig


if __name__ == "__main__":
    import data_ml
    ml = data_ml.cargar_ml()
    pruebas = [
        ("m1 pronostico", fig_pronostico, (ml["m1"]["serie"], ml["m1"]["pronostico"])),
        ("m2 r2", fig_comparacion_r2, (ml["m2"]["comparacion"],)),
        ("m2 importancia", fig_importancia, (ml["m2"]["importancia"],)),
        ("m2 scatter", fig_scatter_pred, (ml["m2"]["scatter"],)),
        ("m3 balance", fig_balance, (ml["m3"]["balance"],)),
        ("m3 auc", fig_comparacion_auc, (ml["m3"]["comparacion"],)),
        ("m3 matriz", fig_matriz_confusion, (ml["m3"]["matriz"],)),
        ("m3 roc", fig_roc, (ml["m3"]["roc"],)),
        ("m4 seleccion_k", fig_seleccion_k, (ml["m4"]["seleccion_k"],)),
        ("m4 pca", fig_pca, (ml["m4"]["pca"], ml["m4"]["metricas"]["nombres_grupos"])),
        ("m4 perfil", fig_perfil_grupos, (ml["m4"]["resumen"],)),
    ]
    for nombre, fn, args in pruebas:
        f = fn(*args)
        print(f"{nombre:18s} {len(f.data)} trazas OK")
