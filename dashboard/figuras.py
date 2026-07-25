"""
figuras.py — Capa de figuras Plotly del dashboard
Proyecto: transportation-analytics

Cada funcion recibe una tabla ya cargada (ver data.py) y devuelve una figura
Plotly lista para st.plotly_chart. Interfaz identica a la version previa:
    fig_titular(oportunidades)
    fig_pareto_rfp(rfp_top_lanes, top_n=15)
    fig_scorecard(scorecard)
    fig_claims(claims_recuperables)

Cambios de esta version (claridad):
- Sin titulo de leyenda "undefined" (se fija texto explicito o vacio).
- Sin traza fantasma "trace 0" (px.bar con color por categoria).
- Scorecard: un color distinto por tier + rojo solo para el outlier real.
- Ejes con titulo en lenguaje claro y etiquetas de dato ($) donde ayudan.
"""

import plotly.express as px
import plotly.graph_objects as go

# --- Paleta (heredada del notebook) ---
AZUL_OSCURO = "#1F4E66"
AZUL_MEDIO  = "#4E8CA8"
AZUL_CLARO  = "#8FBFD9"
AZUL_PALIDO = "#C9DCE8"
ROJO        = "#C1443C"   # SOLO anomalias
GRIS        = "#A8A8A8"
ARENA       = "#D4B483"

COLOR_TIER = {
    "Strategic": AZUL_OSCURO,
    "Core":      AZUL_MEDIO,
    "Tactical":  AZUL_CLARO,
}


def _base_layout(fig, alto=380):
    fig.update_layout(
        template="plotly_white",
        height=alto,
        margin=dict(l=10, r=20, t=48, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="left", x=0, title_text=""),
        font=dict(size=13),
    )
    return fig


def fig_titular(oportunidades):
    d = oportunidades.sort_values("usd")
    color_map = {"Medido": AZUL_MEDIO, "Estimado": ARENA}
    fig = px.bar(
        d, x="usd", y="oportunidad", color="nivel",
        orientation="h", color_discrete_map=color_map,
        labels={"usd": "Ahorro identificado (USD)",
                "oportunidad": "", "nivel": "Nivel de confianza"},
    )
    fig.update_traces(texttemplate="$%{x:,.0f}", textposition="outside",
                      cliponaxis=False)
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(showticklabels=False)
    _base_layout(fig, alto=340)
    fig.update_layout(legend_title_text="")
    return fig


def fig_pareto_rfp(rfp_top_lanes, top_n=15):
    d = (rfp_top_lanes
         .sort_values("sobrecosto_total", ascending=False)
         .head(top_n)
         .sort_values("sobrecosto_total"))
    peor = d["sobrecosto_total"].idxmax()
    colores = [ARENA if i == peor else AZUL_MEDIO for i in d.index]
    fig = go.Figure(go.Bar(
        x=d["sobrecosto_total"], y=d["lane_id"], orientation="h",
        marker_color=colores,
        text=[f"${v:,.0f}" for v in d["sobrecosto_total"]],
        textposition="outside", cliponaxis=False,
        hovertemplate="%{y}: $%{x:,.0f}<extra></extra>",
    ))
    fig.update_xaxes(title_text="Sobrecosto acumulado (USD)",
                     showticklabels=False)
    fig.update_yaxes(title_text="")
    _base_layout(fig, alto=max(360, 26 * len(d)))
    return fig


def fig_scorecard(scorecard):
    d = scorecard.copy().reset_index(drop=True)
    orden = d["costo_dano_x_embarque"].sort_values(ascending=False)
    idx_outlier = None
    if len(orden) >= 2 and orden.iloc[0] > 2 * orden.iloc[1]:
        idx_outlier = orden.index[0]

    fig = go.Figure()
    for tier, sub in d.groupby("carrier_tier"):
        sub = sub[sub.index != idx_outlier] if idx_outlier is not None else sub
        if sub.empty:
            continue
        fig.add_trace(go.Scatter(
            x=sub["costo_real_x_embarque"], y=sub["costo_dano_x_embarque"],
            mode="markers", name=str(tier),
            marker=dict(size=sub["n_embarques"], sizemode="area",
                        sizeref=2.0 * d["n_embarques"].max() / (38 ** 2),
                        sizemin=6, color=COLOR_TIER.get(tier, AZUL_MEDIO),
                        line=dict(width=0.5, color="white")),
            text=sub["carrier_name"],
            hovertemplate="<b>%{text}</b><br>Costo real: $%{x:,.0f}"
                          "<br>Costo dano: $%{y:,.0f}<extra></extra>",
        ))

    if idx_outlier is not None:
        o = d.loc[idx_outlier]
        fig.add_trace(go.Scatter(
            x=[o["costo_real_x_embarque"]], y=[o["costo_dano_x_embarque"]],
            mode="markers+text", name="Anomalia",
            marker=dict(size=16, color=ROJO, line=dict(width=1, color="white")),
            text=[o["carrier_name"]], textposition="top center",
            textfont=dict(color=ROJO, size=12),
            hovertemplate="<b>%{text}</b><br>Costo real: $%{x:,.0f}"
                          "<br>Costo dano: $%{y:,.0f}<extra></extra>",
        ))

    fig.update_xaxes(title_text="Costo total por embarque (USD)  ->  mas caro")
    fig.update_yaxes(title_text="Costo por dano por embarque (USD)  ->  mas danos")
    _base_layout(fig, alto=460)
    return fig


def fig_claims(claims_recuperables):
    d = claims_recuperables
    fig = go.Figure()
    fig.add_bar(x=d["estado"], y=d["pendiente_usd"], name="Pendiente total",
                marker_color=GRIS,
                text=[f"${v:,.0f}" for v in d["pendiente_usd"]],
                textposition="outside")
    fig.add_bar(x=d["estado"], y=d["recuperable_usd"], name="Recuperable",
                marker_color=AZUL_MEDIO,
                text=[f"${v:,.0f}" for v in d["recuperable_usd"]],
                textposition="outside")
    fig.update_layout(barmode="group")
    fig.update_yaxes(title_text="USD", showticklabels=False)
    fig.update_xaxes(title_text="")
    _base_layout(fig, alto=380)
    return fig


if __name__ == "__main__":
    import data
    t = data.cargar_tablas()
    for nombre, fn, arg in [
        ("titular", fig_titular, t["oportunidades"]),
        ("pareto", lambda x: fig_pareto_rfp(x, 15), t["rfp_top_lanes"]),
        ("scorecard", fig_scorecard, t["scorecard"]),
        ("claims", fig_claims, t["claims_recuperables"]),
    ]:
        f = fn(arg)
        print(f"{nombre}: {len(f.data)} trazas OK")
