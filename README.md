# Auditoría de calidad y pipeline de limpieza — Red de transporte Américas

Proyecto de análisis end-to-end sobre datos de un sistema de gestión de transporte (TMS)
de una manufacturera global. Red Estados Unidos–México–Canadá, seis modos de transporte,
220,000 embarques entre 2023 y 2026.

> **Los datos son sintéticos.** El dataset fue generado para replicar la estructura y los
> problemas de calidad típicos de un TMS real. Los hallazgos demuestran una metodología de
> auditoría, no condiciones operativas de una empresa existente.

---

## Estado

| Fase | Entregable | Estado |
|---|---|---|
| 1 | Diagnóstico de calidad | Completo |
| 2 | Pipeline de limpieza y validación | Completo |
| 3 | Análisis exploratorio y de negocio | En curso |
| 4 | Vistas SQL — KPI y carrier scorecard | Pendiente |
| 5 | Dashboard Power BI | Pendiente |

---

## Hallazgo principal

El dataset no documenta cómo se calcula el indicador de entregas a tiempo (OTD). Comparar
directamente la fecha de entrega contra la comprometida arroja **73.80%**, mientras que el
flag del sistema de origen reporta **83.92%** — una brecha de diez puntos sin que ninguna
de las dos cifras sea un error de cálculo.

La regla se derivó auditando 25 registros donde ambas fuentes discrepaban: **una entrega
se considera puntual si ocurre dentro de las 12 horas posteriores al compromiso.** Esa
tolerancia reproduce el flag oficial con exactitud del 100% sobre 217,377 entregas.

Un tablero construido sin esa regla contradiría los reportes del área de transporte.

---

## Estructura

    transportation-analytics/
    ├── notebooks/
    │   ├── 01_exploracion_calidad.ipynb    Diagnóstico y cinco hallazgos
    │   └── 02_pipeline_limpieza.ipynb      Implementación y validación
    ├── src/
    │   └── limpieza.py                     Clase LimpiadorEmbarques
    ├── sql/                                Vistas de KPI (fase 4)
    └── data/                               No versionado

---

## El pipeline

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

**Normalizar precede a deduplicar.** El diagnóstico detectó 134 pares de registros que
solo diferían en el formato de sus categóricas (`Mexico` frente a `MX`, `Truckload` frente
a `TL`). Deduplicar primero los dejaría sin detectar, inflando el conteo de embarques y el
gasto total.

**La deduplicación no usa `keep='first'`.** En once identificadores las dos copias
difieren en el valor de negocio: una sana y otra corrupta. Se conserva la que satisface
más reglas de validez, no la que aparece primero en el archivo.

**Los pesos se corrigen con un criterio relativo al modo.** Un umbral global no detecta un
paquete de 3 kg inflado a 3,000: es absurdo para paquetería pero invisible frente a un
límite calibrado con embarques marítimos. El criterio exige que el valor exceda el
percentil 99 de su modo *y* que dividido entre 1000 regrese a su rango legítimo.

---

## Validación

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

**Divergencias declaradas.** El dataset final tiene 880 filas menos que la referencia
oficial: son los embarques sin `carrier_id`, descartados porque no alimentan el scorecard
de transportistas. Y dos registros con error de unidad quedan sin corregir porque el valor
resultante caería por debajo del percentil 1 de su modo — una limitación estructural del
criterio, documentada en lugar de resuelta ajustando el umbral.

---

## Reproducir

    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt
    jupyter notebook

Los archivos de datos no están versionados. El pipeline espera encontrarlos en
`data/raw/`.

---

## Herramientas

Python 3.14 · pandas 3.0 · NumPy · Plotly · Jupyter · Git