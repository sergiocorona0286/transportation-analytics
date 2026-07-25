"""
app.py — Dashboard de oportunidades de ahorro en la red de transporte
Proyecto: transportation-analytics  ·  Sergio Corona, 2026

Usa la capa comun ya construida: data.py (carga) y figuras.py (Plotly).
Organizado en PESTANAS para que cada vista quepa en pantalla (sin scroll largo).

Correr desde la RAIZ del proyecto, con el venv .venv-dashboard activo:
    streamlit run dashboard\\app.py
Abre en http://localhost:8501 . Detener con Ctrl+C.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
import data
import figuras

st.set_page_config(
    page_title="Ahorro en la red de transporte",
    page_icon="🚚",
    layout="wide",
)


@st.cache_data
def cargar():
    return data.cargar_tablas()


tablas = cargar()
oportunidades = tablas["oportunidades"]
scorecard = tablas["scorecard"]
rfp_top_lanes = tablas["rfp_top_lanes"]
parcel = tablas["parcel_ltl_resumen"]
claims = tablas["claims_recuperables"]
kpis = data.kpis_titulares(oportunidades)


# ---------------------------------------------------------------------------
# Barra lateral — segmentadores + glosario
# ---------------------------------------------------------------------------
st.sidebar.header("Filtros")

nivel_sel = st.sidebar.radio(
    "Nivel de confianza",
    options=["Ambos", "Medido", "Estimado"],
    index=0,
    help="Medido = comprobado con datos. Estimado = proyeccion razonada.",
)
tiers = sorted(scorecard["carrier_tier"].unique().tolist())
tier_sel = st.sidebar.selectbox(
    "Tier de transportista", options=["Todos"] + tiers, index=0,
    help="Filtra el mapa de transportistas.",
)
top_n = st.sidebar.slider(
    "Rutas en el Pareto", min_value=5, max_value=25, value=15, step=1,
    help="Cuantas rutas mostrar en la vista de licitacion.",
)

with st.sidebar.expander("¿Qué significa cada término?"):
    st.markdown(
        "- **Medido**: cifra comprobada con los datos.\n"
        "- **Estimado**: proyección bien fundada (aún por confirmar).\n"
        "- **Paquetería / parcel**: envío chico tipo mensajería, caro por kilo.\n"
        "- **LTL**: camión compartido; barato por kilo en cargas pesadas.\n"
        "- **Licitación / RFP**: proceso donde se asignan precios por ruta.\n"
        "- **Ruta (lane)**: origen→destino de un embarque.\n"
        "- **Tier**: importancia del transportista (Strategic > Core > Tactical).\n"
        "- **OTD**: entregas a tiempo (%).\n"
        "- **C006**: cargo por accesorios en la facturación."
    )

st.sidebar.markdown("---")
st.sidebar.caption(
    "Datos del notebook 03.\ngithub.com/sergiocorona0286/transportation-analytics"
)

# Filtros derivados
oportunidades_f = (oportunidades if nivel_sel == "Ambos"
                   else oportunidades[oportunidades["nivel"] == nivel_sel])
scorecard_f = (scorecard if tier_sel == "Todos"
               else scorecard[scorecard["carrier_tier"] == tier_sel])


# ---------------------------------------------------------------------------
# Encabezado + KPIs (siempre visibles, arriba de las pestanas)
# ---------------------------------------------------------------------------
st.title("Dónde pierde dinero la red de transporte")
st.caption(
    "Auditoría de 219 mil embarques. De las hipótesis iniciales, tres se "
    "descartaron por no resistir el análisis (combustible, un supuesto "
    "sobrecosto de facturación de 6.5 M y el premium por incoterm). Quedan "
    "cuatro fugas reales."
)

k1, k2, k3 = st.columns(3)
k1.metric("Ahorro total detectado", f"${kpis['total_usd']:,.0f}",
          f"{kpis['pct_gasto_red']:.2f}% del gasto de la red", delta_color="off")
k2.metric("Comprobado con datos", f"${kpis['medido_usd']:,.0f}",
          "licitación + facturación C006", delta_color="off")
k3.metric("Estimado (proyección)", f"${kpis['estimado_usd']:,.0f}",
          "paquetería + reclamaciones", delta_color="off")

st.markdown("")

# ---------------------------------------------------------------------------
# Pestanas — una vista por tema, cada una cabe en pantalla
# ---------------------------------------------------------------------------
(tab_exec, tab_resumen, tab_rfp, tab_carriers, tab_parcel,
 tab_claims) = st.tabs([
    "Resumen ejecutivo", "Panorama", "Licitación", "Transportistas",
    "Paquetería → LTL", "Reclamaciones",
])

with tab_exec:
    st.markdown("""
#### El contexto
Una red logística que mueve **219,000 embarques** y **464.5 M USD** anuales en
gasto de transporte cargaba una sospecha común: *"estamos tirando dinero en
fletes"*. El problema con esa sospecha es que casi siempre es cierta y casi
nunca es accionable. Decir que hay desperdicio no sirve; hay que decir **dónde
está, cuánto vale y si la cifra aguanta un escrutinio**. Ese fue el encargo.

#### El método: primero descartar
Antes de buscar oportunidades, el análisis se dedicó a *matarlas*. Se pusieron a
prueba las hipótesis más repetidas, y tres de las más populares se cayeron al
chocar con los datos: el supuesto sobrecosto por **combustible** no aparecía al
normalizar por distancia y peso; un cargo de **facturación de 6.5 M** que
"todos sabían" que estaba mal resultó correctamente aplicado; y el **premium por
incoterm** no tenía correlación real con el gasto. Este paso es el que le da
valor a lo demás: lo que sobrevivió no son corazonadas.

#### Las cuatro fugas reales: 5.42 M USD
Lo que quedó tras el escrutinio suma **5.42 M USD**, el **1.17%** del gasto total
de la red. No es un número inflado; es lo defendible. Se divide en dos capas
según qué tan dura es la evidencia:

**1.72 M están MEDIDOS** con datos duros, sin margen de interpretación:
- **1.23 M** en rutas licitadas por encima de su precio justo. La peor con
  diferencia es **Guadalajara → Newark (MXGDL-USNWK)**, con 128 mil de sobrecosto.
- **486 mil** de un cargo accesorial (C006) mal aplicado, detectado embarque
  por embarque.

**3.70 M están ESTIMADOS**, una proyección razonada aún por confirmar en
operación, pero con lógica sólida:
- **2.58 M** es la fuga más grande y es estructural: casi **5,000 envíos
  pesados** (mediana de 60 kg) viajan por paquetería a **10.67 USD/kg** cuando
  en LTL costarían **~1.54** — un factor de **7×** por kilo.
- **1.12 M** siguen siendo recuperables en reclamaciones por daños (100% de lo
  abierto + 50% de lo parcialmente pagado; lo negado se excluye por prudencia).

#### El riesgo escondido: un solo transportista
Más allá del dinero, hay un problema de calidad concentrado en un actor.
**Autolíneas Mexicanas**, táctico de bajo volumen (apenas **63 embarques**),
genera **~396 USD de daño por embarque: seis veces** el siguiente peor de la
red, con 15.9 reclamaciones por mil y solo **75.8%** de entregas a tiempo. Poco
volumen, daño desproporcionado.

#### Qué hacer con esto
- **Palanca más grande:** reconducir la paquetería pesada a LTL.
- **Lo más inmediato:** renegociar las rutas mal adjudicadas y cobrar las
  reclamaciones abiertas.
- **Lo más urgente en calidad:** poner a Autolíneas en plan de mejora, o sustituirlo.

#### Por qué se puede confiar
Cada cifra medida está validada contra los factores del propio generador de
datos, y el análisis **descartó tres de cuatro hipótesis** antes de quedarse con
estas. La disciplina no fue encontrar oportunidades, sino resistir la tentación
de contar como ahorro lo que no lo era. Ese es el entregable: no una lista de
ideas, sino un mapa de fugas que aguanta que lo cuestionen.
""")

with tab_resumen:
    st.markdown("#### Las 4 fugas de dinero, ordenadas por tamaño")
    st.markdown(
        "Cada barra es una oportunidad de ahorro. **Azul** = comprobado con "
        "datos; **arena** = estimado. Usa el filtro de la izquierda para ver "
        "solo lo comprobado."
    )
    if oportunidades_f.empty:
        st.info("No hay oportunidades para ese nivel de confianza.")
    else:
        st.plotly_chart(figuras.fig_titular(oportunidades_f), width="stretch")

with tab_rfp:
    st.markdown("#### Rutas donde la licitación quedó cara")
    st.markdown(
        "Al asignar los precios de transporte, algunas rutas quedaron más "
        "caras de lo que deberían. Cada barra es una ruta; **la de hasta "
        "arriba es la peor**. Total del problema: **1.23 M USD**."
    )
    st.plotly_chart(figuras.fig_pareto_rfp(rfp_top_lanes, top_n=top_n),
                    width="stretch")
    st.caption("La peor es MXGDL-USNWK (Guadalajara → Newark), ~128 mil USD.")

with tab_carriers:
    st.markdown("#### Mapa de transportistas: ¿quién sale caro y con daños?")
    st.markdown(
        "Cada burbuja es un transportista. **Hacia la derecha** = embarque más "
        "caro; **hacia arriba** = más pagas en daños. El tamaño es el volumen "
        "de embarques. El punto **rojo** es el problema."
    )
    if scorecard_f.empty:
        st.info("No hay transportistas para ese tier.")
    else:
        st.plotly_chart(figuras.fig_scorecard(scorecard_f), width="stretch")
    st.caption(
        "Autolíneas Mexicanas (Tactical) rompe la escala: ~396 USD de daño por "
        "embarque (6× el siguiente), 15.9 reclamaciones por mil y 75.8% de "
        "entregas a tiempo, en apenas 63 embarques."
    )

with tab_parcel:
    st.markdown("#### Paquetería pesada que debería ir en LTL")
    st.markdown(
        "Casi 5,000 envíos pesados viajan por paquetería (caro) cuando cabrían "
        "en LTL (barato). La diferencia es de **~7× por kilo**."
    )
    pl = parcel.iloc[0]
    p1, p2, p3 = st.columns(3)
    p1.metric("Envíos pesados mal ruteados", f"{int(pl['envios_pesados']):,}")
    p2.metric("Costo por kilo", f"${pl['usd_por_kg_parcel']:.2f}",
              "vs $1.54 en LTL (~7×)", delta_color="off")
    p3.metric("Ahorro estimado", f"${int(pl['ahorro_estimado_usd']):,}")
    st.caption(
        f"Mediana de peso: {pl['mediana_peso_kg']:.0f} kg por envío. "
        "Reconducirlos a LTL es la palanca de ahorro más grande del análisis."
    )

with tab_claims:
    st.markdown("#### Reclamaciones que todavía se pueden cobrar")
    st.markdown(
        "De lo que se puede reclamar por daños, esto es lo aún **recuperable**: "
        "100% de lo abierto (Open) + 50% de lo parcialmente pagado. Lo negado "
        "(Denied) se excluye por prudencia. Total: **1.12 M USD**."
    )
    st.plotly_chart(figuras.fig_claims(claims), width="stretch")
