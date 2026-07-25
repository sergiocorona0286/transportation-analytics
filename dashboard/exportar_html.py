# -*- coding: utf-8 -*-
"""
exportar_html.py — Genera un index.html estatico y autocontenido del dashboard.

Para que sirve: GitHub no renderiza figuras Plotly interactivas dentro de un
notebook. Este script arma una pagina unica (index.html) con un RESUMEN
EJECUTIVO tipo storytelling + las 4 figuras + los textos, usando plotly.js
desde CDN. Es el respaldo siempre-encendido / vitrina para GitHub Pages.
La version con filtros vive en el deploy de Streamlit.

Reutiliza la MISMA capa comun: data.py (carga) y figuras.py (Plotly).

Correr desde la RAIZ del proyecto:
    python dashboard\\exportar_html.py
Genera:  dashboard\\index.html   (abrelo con doble clic para previsualizar)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import data
import figuras

AZUL_OSCURO = "#1F4E66"
AZUL_MEDIO = "#4E8CA8"
ARENA = "#D4B483"
GRIS_TXT = "#3f3f3f"
GRIS_SUAVE = "#8a8a8a"

CONFIG = {"displayModeBar": False, "responsive": True}


def fig_div(fig):
    return fig.to_html(full_html=False, include_plotlyjs=False, config=CONFIG)


def kpi(label, valor, sub):
    return f"""
      <div class="kpi">
        <div class="kpi-label">{label}</div>
        <div class="kpi-valor">{valor}</div>
        <div class="kpi-sub">{sub}</div>
      </div>"""


def seccion(titulo, intro, cuerpo_html, caption=""):
    cap = f'<p class="caption">{caption}</p>' if caption else ""
    return f"""
    <section>
      <h2>{titulo}</h2>
      <p class="intro">{intro}</p>
      {cuerpo_html}
      {cap}
    </section>"""


RESUMEN_EJECUTIVO = """
    <section class="resumen">
      <h2>Resumen ejecutivo</h2>

      <h3>El contexto</h3>
      <p>Una red logística que mueve <b>219,000 embarques</b> y
      <b>464.5 M USD</b> anuales en gasto de transporte cargaba una sospecha
      común: <i>"estamos tirando dinero en fletes"</i>. El problema con esa
      sospecha es que casi siempre es cierta y casi nunca es accionable. Decir
      que hay desperdicio no sirve; hay que decir <b>dónde está, cuánto vale y
      si la cifra aguanta un escrutinio</b>. Ese fue el encargo.</p>

      <h3>El método: primero descartar</h3>
      <p>Antes de buscar oportunidades, el análisis se dedicó a <i>matarlas</i>.
      Se pusieron a prueba las hipótesis más repetidas, y tres de las más
      populares se cayeron al chocar con los datos: el supuesto sobrecosto por
      <b>combustible</b> no aparecía al normalizar por distancia y peso; un cargo
      de <b>facturación de 6.5 M</b> que "todos sabían" que estaba mal resultó
      correctamente aplicado; y el <b>premium por incoterm</b> no tenía
      correlación real con el gasto. Este paso es el que le da valor a lo demás:
      lo que sobrevivió no son corazonadas.</p>

      <h3>Las cuatro fugas reales: 5.42 M USD</h3>
      <p>Lo que quedó tras el escrutinio suma <b>5.42 M USD</b>, el <b>1.17%</b>
      del gasto total de la red. No es un número inflado; es lo defendible. Se
      divide en dos capas según qué tan dura es la evidencia:</p>
      <p><b>1.72 M están MEDIDOS</b> con datos duros, sin margen de
      interpretación:</p>
      <ul>
        <li><b>1.23 M</b> en rutas licitadas por encima de su precio justo. La
        peor con diferencia es <b>Guadalajara → Newark (MXGDL-USNWK)</b>, con
        128 mil de sobrecosto.</li>
        <li><b>486 mil</b> de un cargo accesorial (C006) mal aplicado, detectado
        embarque por embarque.</li>
      </ul>
      <p><b>3.70 M están ESTIMADOS</b>, una proyección razonada aún por confirmar
      en operación, pero con lógica sólida:</p>
      <ul>
        <li><b>2.58 M</b> es la fuga más grande y es estructural: casi
        <b>5,000 envíos pesados</b> (mediana de 60 kg) viajan por paquetería a
        <b>10.67 USD/kg</b> cuando en LTL costarían <b>~1.54</b> — un factor de
        <b>7×</b> por kilo.</li>
        <li><b>1.12 M</b> siguen siendo recuperables en reclamaciones por daños
        (100% de lo abierto + 50% de lo parcialmente pagado; lo negado se excluye
        por prudencia).</li>
      </ul>

      <h3>El riesgo escondido: un solo transportista</h3>
      <p>Más allá del dinero, hay un problema de calidad concentrado en un actor.
      <b>Autolíneas Mexicanas</b>, táctico de bajo volumen (apenas
      <b>63 embarques</b>), genera <b>~396 USD de daño por embarque: seis
      veces</b> el siguiente peor de la red, con 15.9 reclamaciones por mil y
      solo <b>75.8%</b> de entregas a tiempo. Poco volumen, daño
      desproporcionado.</p>

      <h3>Qué hacer con esto</h3>
      <ul>
        <li><b>Palanca más grande:</b> reconducir la paquetería pesada a LTL.</li>
        <li><b>Lo más inmediato:</b> renegociar las rutas mal adjudicadas y
        cobrar las reclamaciones abiertas.</li>
        <li><b>Lo más urgente en calidad:</b> poner a Autolíneas en plan de
        mejora, o sustituirlo.</li>
      </ul>

      <h3>Por qué se puede confiar</h3>
      <p>Cada cifra medida está validada contra los factores del propio generador
      de datos, y el análisis <b>descartó tres de cuatro hipótesis</b> antes de
      quedarse con estas. La disciplina no fue encontrar oportunidades, sino
      resistir la tentación de contar como ahorro lo que no lo era. Ese es el
      entregable: no una lista de ideas, sino un mapa de fugas que aguanta que lo
      cuestionen.</p>
    </section>"""


def main():
    t = data.cargar_tablas()
    k = data.kpis_titulares(t["oportunidades"])
    pl = t["parcel_ltl_resumen"].iloc[0]

    div_titular = fig_div(figuras.fig_titular(t["oportunidades"]))
    div_pareto = fig_div(figuras.fig_pareto_rfp(t["rfp_top_lanes"], top_n=15))
    div_score = fig_div(figuras.fig_scorecard(t["scorecard"]))
    div_claims = fig_div(figuras.fig_claims(t["claims_recuperables"]))

    kpis_html = (
        kpi("Ahorro total detectado", f"${k['total_usd']:,.0f}",
            f"{k['pct_gasto_red']:.2f}% del gasto de la red")
        + kpi("Comprobado con datos", f"${k['medido_usd']:,.0f}",
              "licitación + facturación C006")
        + kpi("Estimado (proyección)", f"${k['estimado_usd']:,.0f}",
              "paquetería + reclamaciones")
    )

    parcel_cards = f"""
      <div class="kpi-row">
        {kpi("Envíos pesados mal ruteados", f"{int(pl['envios_pesados']):,}", "por paquetería")}
        {kpi("Costo por kilo", f"${pl['usd_por_kg_parcel']:.2f}", "vs $1.54 en LTL (~7×)")}
        {kpi("Ahorro estimado", f"${int(pl['ahorro_estimado_usd']):,}", f"mediana {pl['mediana_peso_kg']:.0f} kg/envío")}
      </div>"""

    cuerpo = "".join([
        seccion(
            "Las 4 fugas de dinero, ordenadas por tamaño",
            "Cada barra es una oportunidad de ahorro. <b>Azul</b> = comprobado "
            "con datos; <b>arena</b> = estimado.",
            f'<div class="chart">{div_titular}</div>',
        ),
        seccion(
            "Rutas donde la licitación quedó cara",
            "Al asignar los precios de transporte, algunas rutas quedaron más "
            "caras de lo debido. Cada barra es una ruta; la de arriba es la peor.",
            f'<div class="chart">{div_pareto}</div>',
            "La peor es MXGDL-USNWK (Guadalajara → Newark), ~128 mil USD. "
            "Sobrecosto total de licitación: 1.23 M USD.",
        ),
        seccion(
            "Mapa de transportistas: quién sale caro y con daños",
            "Cada burbuja es un transportista. Hacia la <b>derecha</b> = "
            "embarque más caro; hacia <b>arriba</b> = más daños. El tamaño es "
            "el volumen. El punto rojo es el problema.",
            f'<div class="chart">{div_score}</div>',
            "Autolíneas Mexicanas (Tactical) rompe la escala: ~396 USD de daño "
            "por embarque (6× el siguiente), 15.9 reclamaciones por mil y 75.8% "
            "de entregas a tiempo, en apenas 63 embarques.",
        ),
        seccion(
            "Paquetería pesada que debería ir en LTL",
            "Casi 5,000 envíos pesados viajan por paquetería (caro) cuando "
            "cabrían en LTL (barato). La diferencia es de ~7× por kilo.",
            parcel_cards,
            "Reconducirlos a LTL es la palanca de ahorro más grande del análisis.",
        ),
        seccion(
            "Reclamaciones que todavía se pueden cobrar",
            "De lo reclamable por daños, esto es lo aún <b>recuperable</b>: "
            "100% de lo abierto (Open) + 50% de lo parcialmente pagado. Lo "
            "negado (Denied) se excluye por prudencia. Total: 1.12 M USD.",
            f'<div class="chart">{div_claims}</div>',
        ),
    ])

    html = PLANTILLA.format(
        azul=AZUL_OSCURO, azul_medio=AZUL_MEDIO, gris=GRIS_TXT,
        gris_suave=GRIS_SUAVE, resumen=RESUMEN_EJECUTIVO,
        kpis=kpis_html, cuerpo=cuerpo,
    )

    # Se publica en docs/ (raiz del repo) porque GitHub Pages solo sirve
    # desde la raiz o desde /docs, no desde subcarpetas como dashboard/.
    docs = Path(__file__).parent.parent / "docs"
    docs.mkdir(exist_ok=True)
    salida = docs / "index.html"
    salida.write_text(html, encoding="utf-8")
    print(f"OK -> {salida}  ({salida.stat().st_size/1024:.0f} KB)")


PLANTILLA = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ahorro en la red de transporte</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js" charset="utf-8"></script>
<style>
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; font-family: Arial, Helvetica, sans-serif;
    color: {gris}; background: #fafafa; line-height: 1.55; }}
  .wrap {{ max-width: 1080px; margin: 0 auto; padding: 40px 24px 64px; }}
  header h1 {{ color: {azul}; font-size: 34px; margin: 0 0 8px; }}
  header p.sub {{ color: {gris_suave}; font-size: 15px; margin: 0 0 26px;
    max-width: 860px; }}
  .kpi-row {{ display: flex; gap: 16px; flex-wrap: wrap; margin: 0 0 8px; }}
  .kpi {{ flex: 1 1 220px; background: #fff; border: 1px solid #e6e6e6;
    border-left: 4px solid {azul_medio}; border-radius: 8px; padding: 16px 18px; }}
  .kpi-label {{ color: {gris_suave}; font-size: 13px; }}
  .kpi-valor {{ color: {azul}; font-size: 28px; font-weight: bold; margin: 4px 0; }}
  .kpi-sub {{ color: {gris_suave}; font-size: 12px; }}
  section {{ background: #fff; border: 1px solid #e6e6e6; border-radius: 8px;
    padding: 24px 26px; margin: 22px 0; }}
  section h2 {{ color: {azul}; font-size: 21px; margin: 0 0 6px; }}
  section.resumen {{ border-left: 4px solid {azul}; }}
  section.resumen h3 {{ color: {azul_medio}; font-size: 16px;
    margin: 20px 0 4px; }}
  section.resumen p {{ margin: 6px 0; font-size: 15px; }}
  section.resumen ul {{ margin: 6px 0 6px; padding-left: 22px; }}
  section.resumen li {{ margin: 4px 0; font-size: 15px; }}
  p.intro {{ margin: 0 0 14px; font-size: 15px; }}
  p.caption {{ color: {gris_suave}; font-size: 13px; font-style: italic;
    margin: 12px 0 0; }}
  .chart {{ width: 100%; }}
  footer {{ color: {gris_suave}; font-size: 12px; margin-top: 32px;
    text-align: center; }}
  footer a {{ color: {azul_medio}; }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Dónde pierde dinero la red de transporte</h1>
    <p class="sub">Auditoría de 219 mil embarques y 464.5 M USD de gasto anual.
    Cuatro fugas reales, dimensionadas y validadas — el detalle, abajo.</p>
  </header>
  {resumen}
  <div class="kpi-row">{kpis}</div>
  {cuerpo}
  <footer>
    Metodología completa en el
    <a href="https://github.com/sergiocorona0286/transportation-analytics">repositorio</a>.
    Cada cifra medida está validada contra los factores del generador de datos.
  </footer>
</div>
</body>
</html>"""


if __name__ == "__main__":
    main()
