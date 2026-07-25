"""
data.py — Capa de datos del dashboard de analitica de transporte.

Lee las seis tablas pre-cocidas exportadas desde el notebook 03
(carpeta dashboard/datos/) y las deja listas para consumo tanto de
la app de Streamlit como del export a HTML estatico.

Una sola fuente de verdad: si se re-exporta una tabla desde el notebook,
el dashboard la toma automaticamente.

Tablas:
    oportunidades        tabla titular 5.4 (4 oportunidades, USD 5.42M)
    scorecard            scorecard costo real 4.3 (30 carriers)
    rfp_detalle          detalle RFP por lane-ronda (68 filas)
    rfp_top_lanes        RFP consolidado por lane para el Pareto (55 lanes)
    parcel_ltl_resumen   resumen Parcel->LTL 5.2
    claims_recuperables  claims recuperables 5.3
"""

from pathlib import Path
import pandas as pd

# Ruta a las tablas pre-cocidas, relativa a este archivo.
# __file__ vive en dashboard/, los datos en dashboard/datos/.
RUTA_DATOS = Path(__file__).parent / "datos"

# Cifra de referencia para porcentajes (gasto total de la red).
GASTO_RED_USD = 464_533_185


def _leer(nombre: str) -> pd.DataFrame:
    """Lee un pickle de la carpeta de datos. Error claro si falta."""
    ruta = RUTA_DATOS / f"{nombre}.pkl"
    if not ruta.exists():
        raise FileNotFoundError(
            f"No se encontro {ruta}. "
            f"Re-exporta las tablas desde el notebook 03 (fase de export)."
        )
    return pd.read_pickle(ruta)


def cargar_tablas() -> dict:
    """
    Carga las seis tablas y devuelve un diccionario.
    Punto de entrada unico para Streamlit y para el export HTML.
    """
    return {
        "oportunidades": _leer("oportunidades"),
        "scorecard": _leer("scorecard"),
        "rfp_detalle": _leer("rfp_detalle"),
        "rfp_top_lanes": _leer("rfp_top_lanes"),
        "parcel_ltl_resumen": _leer("parcel_ltl_resumen"),
        "claims_recuperables": _leer("claims_recuperables"),
    }


def kpis_titulares(oportunidades: pd.DataFrame) -> dict:
    """
    Calcula las cifras de cabecera a partir de la tabla de oportunidades.
    Devuelve total, desglose medido/estimado y porcentaje del gasto de red.
    """
    total = oportunidades["usd"].sum()
    medido = oportunidades.loc[oportunidades["nivel"] == "Medido", "usd"].sum()
    estimado = oportunidades.loc[oportunidades["nivel"] == "Estimado", "usd"].sum()
    return {
        "total_usd": total,
        "medido_usd": medido,
        "estimado_usd": estimado,
        "pct_gasto_red": total / GASTO_RED_USD * 100,
        "gasto_red_usd": GASTO_RED_USD,
    }


if __name__ == "__main__":
    # Auto-prueba: correr `python data.py` para verificar que todo carga.
    tablas = cargar_tablas()
    print("Tablas cargadas correctamente:\n")
    for nombre, df in tablas.items():
        print(f"  {nombre:22s} {df.shape}")

    print()
    k = kpis_titulares(tablas["oportunidades"])
    print(f"Total identificado:  USD {k['total_usd']:>12,.0f}")
    print(f"  Nucleo medido:     USD {k['medido_usd']:>12,.0f}")
    print(f"  Capa estimada:     USD {k['estimado_usd']:>12,.0f}")
    print(f"  % del gasto red:        {k['pct_gasto_red']:>8.2f}%")
