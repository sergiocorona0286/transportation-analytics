# Analítica de transporte end-to-end — Red Américas

Análisis end-to-end sobre datos de un sistema de gestión de transporte (TMS) de una
manufacturera global. Red Estados Unidos–México–Canadá, seis modos de transporte,
219,120 embarques entre 2023 y 2026, USD 464.5M de gasto anual.

> **Los datos son sintéticos.** El dataset fue generado para replicar la estructura y los
> problemas de calidad típicos de un TMS real. Los hallazgos demuestran una metodología de
> análisis, no condiciones operativas de una empresa existente.

---

## En una línea

**USD 5.42M en ahorro anual identificado (1.17% del gasto de red)** — y tres oportunidades
mayores descartadas por no resistir el escrutinio. El proyecto va del diagnóstico de calidad
de datos hasta un caso de negocio cuantificado y cuatro modelos de machine learning,
priorizando cifras defendibles sobre cifras grandes.

**[Dashboard interactivo →](https://sergiocorona0286.github.io/transportation-analytics/)**
Análisis de negocio + modelos predictivos, con gráficas interactivas.

El resultado se presenta por **nivel de confianza**, no como un número monolítico:

| Nivel | Monto | Contenido |
|---|---|---|
| **Núcleo medido** (alta certeza) | **USD 1.72M** | Sobrecosto de accesoriales + lanes RFP mal adjudicadas |
| **Capa estimada** (supuestos explícitos) | **USD 3.70M** | Reasignación de modo + recuperación de reclamaciones |
| **Potencial total** | **USD 5.42M** | 1.17% del gasto anual de la red |

---

## Estado

| Fase | Entregable | Estado |
|---|---|---|
| 1 | Diagnóstico de calidad | Completo |
| 2 | Pipeline de limpieza y validación | Completo |
| 3 | Análisis exploratorio y de negocio | Completo |
| 4 | Modelos de machine learning (4 módulos) | Completo |
| 5 | Dashboard interactivo (Streamlit + HTML) | Completo |
| 6 | Vistas SQL — KPI y carrier scorecard | Pendiente |

---

## Rigor antes que impacto

Lo que distingue este análisis no es la cifra final, sino lo que quedó fuera de ella. El
planteamiento inicial sugería cuatro grandes bolsas de ahorro adicionales. **Tres no
sobrevivieron al análisis** y fueron descartadas:

- **Subcobro de combustible (Ocean).** El aparente subcobro del 10.6% resultó ser una
  comparación inválida: Ocean se indexa al *bunker fuel*, no al diésel de carretera. No es
  un sobrecosto, es otra referencia.
- **Facturación bruta (USD 6.5M).** La varianza de facturación resultó ser ruido uniforme
  del 0.42%, idéntico en los seis modos. No hay concentración que disputar; solo válido bajo
  el supuesto —desmentido— de que el modelo de costo es exacto.
- **Premium por incoterm.** El sobreprecio cross-border se disuelve al controlar por
  distancia. El incoterm no incide: todos los modos cuestan ~USD 0.14/km sin importar el
  término comercial.

Descartar estas cifras es lo que hace creíbles las que quedaron. Un ahorro identificado que
no resiste una pregunta difícil no sirve en un comité.

---

## Las cuatro oportunidades que sí resistieron

**1. Sobrecosto de accesoriales — Fletes Del Golfo (C006): USD 486,132.**
Un transportista duplicó sus cargos accesoriales en marzo de 2025 (de USD 145 a USD 349 por
embarque, 2.4×) y sostuvo el nivel durante 16 meses, sin correlato de mercado. Cuantificado
contra la línea base histórica del propio transportista y verificado por dos métodos
independientes con resultado idéntico. *Cifra medida.*

**2. Lanes de paquetería mal adjudicadas en el RFP: USD 1,229,096.**
De 360 adjudicaciones lane-ronda, 68 (18.9%) se otorgaron a un transportista que no era el
más barato disponible — sobrecosto de USD 117.56 por envío, multiplicado por el tráfico real
de cada lane. El dinero se concentra: 15 lanes acumulan el 68% del total, y 12 lanes fueron
mal adjudicadas en más de una ronda, señal de un criterio de adjudicación que privilegia al
transportista vigente sobre el precio. *Cifra medida.*

**3. Reasignación de Parcel pesado a LTL: USD 2,583,514.**
4,925 envíos de paquetería pesan más de 45 kg (mediana 60 kg) y pagan USD 10.67/kg, casi 7×
el costo del LTL. Reasignados al modo correcto, ahorrarían un 80%. Estimado con la referencia
LTL conservadora (percentil 75), lo que subestima el ahorro a propósito. *Cifra estimada:
depende de que cada lane admita servicio LTL.*

**4. Recuperación de reclamaciones: USD 1,117,280.**
De USD 2.76M reclamados sin recuperar, solo la mitad es realistamente perseguible una vez
descompuesta por estado: los claims *Open* (en proceso) y una fracción de los *Partially
Paid*, excluyendo por completo los *Denied* (USD 1.34M que probablemente no se cobran).
*Cifra estimada y deliberadamente conservadora.*

---

## Método destacado — validación contra la verdad conocida

El scorecard de transportistas mide el "costo real" de cada carrier (tarifa + daño), más
allá de su tarifa nominal. Como el dataset es sintético, su generador dejó tres parámetros
ocultos en `dim_carrier` (`cost_factor`, `service_factor`, `damage_factor`) que representan
la verdad de diseño de cada transportista.

El scorecard se construyó **a ciegas**, solo con hechos observables, sin mirar esos
parámetros. Al enfrentarlos después, las métricas derivadas los reproducen:

| Métrica derivada | Factor del generador | Correlación |
|---|---|---|
| Costo por embarque (norm. por modo) | `cost_factor` | **r = +0.895** |
| OTD (norm. por modo) | `service_factor` | **r = −0.885** |
| Tasa de reclamación (norm. por modo) | `damage_factor` | r = +0.327 |

Dos de tres se alinean con altísima fidelidad. La tercera es más débil por una razón
estadística legítima —el daño es un evento raro (<1% de los envíos), y una señal escasa se
estima con más varianza— no por un fallo del método. La normalización por modo fue
indispensable: sin ella, la correlación de costo caía a 0.03. El método queda validado: el
scorecard no inventa una jerarquía, la recupera.

---

## Hallazgo de la fase de calidad — la regla no escrita del OTD

El dataset no documenta cómo se calcula el indicador de entregas a tiempo (OTD). Comparar
directamente la fecha de entrega contra la comprometida arroja **73.80%**, mientras que el
flag del sistema de origen reporta **83.92%** — una brecha de diez puntos sin que ninguna de
las dos cifras sea un error de cálculo.

La regla se derivó auditando registros donde ambas fuentes discrepaban: **una entrega se
considera puntual si ocurre dentro de las 12 horas posteriores al compromiso.** Esa
tolerancia reproduce el flag oficial con exactitud del 100% sobre 217,377 entregas. Un
tablero construido sin esa regla contradiría los reportes del área de transporte.

---

## Modelos de machine learning

Sobre la base de datos limpia, cuatro modelos cubren las grandes ramas del aprendizaje
automático aplicado. Cada uno se documenta con su metodología, la justificación de por qué
se eligió esa técnica y no otra, y su interpretación de negocio.

**1. Pronóstico del gasto de flete — series de tiempo (Prophet).**
Proyecta el gasto mensual a 6 meses capturando tendencia y estacionalidad. La serie muestra
crecimiento sostenido (+189% en el periodo) y un patrón anual claro: temporada alta en verano,
baja al inicio del año. Se eligió Prophet sobre ARIMA/Holt-Winters por su manejo explícito de
estacionalidad y sus intervalos de confianza interpretables. Se documenta un ligero
sobreajuste estacional en lugar de ocultarlo. *Notebook 04.*

**2. Predicción del costo de embarque — regresión (Random Forest).**
Predice el costo esperado de un embarque con **R² = 0.94** y error promedio de USD 341. El
baseline lineal falló (R² negativo, hundido por outliers), lo que justificó el modelo no
lineal. La importancia de variables revela que peso cobrable (50%) y distancia (25%) dominan
el costo. Aplicado como **detector de anomalías**: comparando costo real vs. predicho, señala
sobrecostos concentrados en dos carriers (C022, C023). *Notebook 05.*

**3. Riesgo de retraso — clasificación (investigación de sus límites).**
Un resultado negativo, correctamente diagnosticado. Ningún modelo (Regresión Logística,
Random Forest, XGBoost) superó un AUC de ~0.64. En vez de inflar el resultado, se demostró
con rigor que **el límite está en los datos, no en el modelo**: que los tres algoritmos
converjan al mismo techo prueba que faltan variables predictivas (clima, congestión aduanal,
disponibilidad de unidades). El hallazgo se traduce en una recomendación de captura de datos.
*Notebook 06.*

**4. Segmentación de transportistas — clustering (K-Means).**
Agrupa los 30 carriers en 4 perfiles estratégicos según costo, confiabilidad y volumen. El
número de grupos se eligió balanceando criterio estadístico (método del codo, silueta) con
utilidad de negocio: K=4 sobre el K=8 que sugería la silueta, porque sobre-segmentar 30
carriers no es accionable. Los grupos emergen nítidos: núcleo confiable, paquetería ligera,
gigantes de carga pesada y un grupo problemático de baja puntualidad. *Notebook 07.*

---

## Dashboard

Dos presentaciones desde una única capa de datos, sin re-entrenar modelos: los notebooks
exportan resultados ligeros (CSV/JSON, ~150 KB) que ambas vistas consumen.

- **Interactivo (Streamlit):** diez pestañas —seis de negocio, cuatro de ML— con filtros.
- **Estático (GitHub Pages):** página autocontenida con gráficas Plotly, siempre encendida.
  [Ver en vivo →](https://sergiocorona0286.github.io/transportation-analytics/)

---

## Estructura

    transportation-analytics/
    ├── notebooks/
    │   ├── 01_exploracion_calidad.ipynb     Diagnóstico y cinco hallazgos
    │   ├── 02_pipeline_limpieza.ipynb       Implementación y validación
    │   ├── 03_analisis_negocio.ipynb        Análisis de negocio y caso cuantificado
    │   ├── 04_pronostico_series.ipynb       ML: pronóstico con Prophet
    │   ├── 05_regresion_costo.ipynb         ML: regresión y detección de anomalías
    │   ├── 06_clasificacion_riesgo.ipynb    ML: clasificación e investigación de límites
    │   └── 07_segmentacion_carriers.ipynb   ML: clustering K-Means
    ├── dashboard/
    │   ├── app.py                            App Streamlit (10 pestañas)
    │   ├── data.py, figuras.py               Capa de negocio
    │   ├── data_ml.py, figuras_ml.py         Capa de machine learning
    │   ├── exportar_html.py                  Generador del HTML estático
    │   └── data_ml/                          Resultados ML exportados
    ├── src/
    │   └── limpieza.py                       Clase LimpiadorEmbarques
    ├── docs/                                 HTML publicado (GitHub Pages)
    ├── sql/                                  Vistas de KPI (fase 6)
    └── data/                                 No versionado

---

## El pipeline de limpieza

`src/limpieza.py` implementa ocho pasos cuyo orden no es intercambiable. Cada método
registra su efecto en una bitácora que se exporta como evidencia del proceso.

| # | Paso | Registros afectados |
|---|---|---|
| 1 | Normalizar categóricas | 11,124 |
| 2 | Deduplicar por validez de negocio | 1,320 |
| 3 | Convertir tipos temporales | 220,000 |
| 4 | Reconstruir fechas imposibles | 298 |
| 5 | Corregir costos con signo invertido | 393 |
| 6 | Corregir pesos con error de unidad | 242 |
| 7 | Tratar nulos por criterio diferenciado | 19,540 |
| 8 | Derivar métricas analíticas | 219,120 |

Tres decisiones de diseño que el orden vuelve necesarias:

**Normalizar precede a deduplicar.** El diagnóstico detectó 134 pares de registros que solo
diferían en el formato de sus categóricas (`Mexico` frente a `MX`, `Truckload` frente a
`TL`). Deduplicar primero los dejaría sin detectar, inflando el conteo de embarques y el
gasto total.

**La deduplicación no usa `keep='first'`.** En once identificadores las dos copias difieren
en el valor de negocio: una sana y otra corrupta. Se conserva la que satisface más reglas de
validez, no la que aparece primero en el archivo.

**Los pesos se corrigen con un criterio relativo al modo.** Un umbral global no detecta un
paquete de 3 kg inflado a 3,000: es absurdo para paquetería pero invisible frente a un límite
calibrado con embarques marítimos. El criterio exige que el valor exceda el percentil 99 de
su modo *y* que dividido entre 1000 regrese a su rango legítimo.

---

## Validación del pipeline

El resultado se contrasta contra `fact_shipments_clean.csv`, la versión limpia oficial del
dataset, que no se consulta durante la construcción del pipeline.

| Columna | Coincidencia |
|---|---|
| `mode`, `origin_country`, `dest_country` | 100.00% |
| `total_cost_usd`, `distance_km` | 100.00% |
| Las cinco columnas temporales | 100.00% |
| `weight_kg` | 98.81% |

La divergencia en `weight_kg` corresponde en 2,616 de 2,618 casos a la imputación por
mediana, que por definición no reproduce un valor ausente en el origen.

**Divergencias declaradas.** El dataset final tiene 880 filas menos que la referencia oficial:
son los embarques sin `carrier_id`, descartados porque no alimentan el scorecard de
transportistas. Y dos registros con error de unidad quedan sin corregir porque el valor
resultante caería por debajo del percentil 1 de su modo — una limitación estructural del
criterio, documentada en lugar de resuelta ajustando el umbral.

---

## Reproducir

    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt
    jupyter notebook

Para el dashboard interactivo, desde la raíz del proyecto:

    streamlit run dashboard\app.py

Los archivos de datos no están versionados. El pipeline espera encontrarlos en `data/raw/`.

---

## Herramientas

Python 3.12 · pandas · NumPy · scikit-learn · Prophet · XGBoost · Plotly ·
Streamlit · Jupyter · Git
