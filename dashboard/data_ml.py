"""
data_ml.py — Capa de datos de los modulos de machine learning del dashboard.
Proyecto: transportation-analytics  ·  Sergio Corona, 2026

Lee los resultados pre-calculados que exportan los notebooks 04-07
(carpeta dashboard/data_ml/) y los deja listos para consumo de la app.

Misma filosofia que data.py: una sola fuente de verdad. Si se re-exporta
un resultado desde un notebook, el dashboard lo toma automaticamente.

A diferencia de data.py (que lee pickles del notebook 03), aqui leemos
CSV y JSON ligeros: los modelos NO se cargan ni se re-entrenan en la app,
solo se muestran sus resultados ya calculados. Esto mantiene el dashboard
rapido y ligero (~150 KB en total).

Modulos:
    m1  Pronostico de series de tiempo (Prophet)
    m2  Regresion y deteccion de anomalias (Random Forest)
    m3  Clasificacion de riesgo de retraso (comparacion de 3 modelos)
    m4  Segmentacion de carriers (K-Means)
"""

from pathlib import Path
import json
import pandas as pd

# Ruta a los resultados de ML, relativa a este archivo.
# __file__ vive en dashboard/, los datos en dashboard/data_ml/.
RUTA_ML = Path(__file__).parent / "data_ml"


def _leer_csv(nombre: str, **kwargs) -> pd.DataFrame:
    """Lee un CSV de la carpeta de datos ML. Error claro si falta."""
    ruta = RUTA_ML / nombre
    if not ruta.exists():
        raise FileNotFoundError(
            f"No se encontro {ruta}. "
            f"Re-exporta los resultados desde los notebooks 04-07 "
            f"(celda de export al final de cada uno)."
        )
    return pd.read_csv(ruta, **kwargs)


def _leer_json(nombre: str) -> dict:
    """Lee un JSON de metricas de la carpeta de datos ML."""
    ruta = RUTA_ML / nombre
    if not ruta.exists():
        raise FileNotFoundError(
            f"No se encontro {ruta}. "
            f"Re-exporta los resultados desde los notebooks 04-07."
        )
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def cargar_ml() -> dict:
    """
    Carga todos los resultados de los cuatro modulos de ML.
    Punto de entrada unico para Streamlit.
    Devuelve un diccionario anidado por modulo.
    """
    return {
        # --- Modulo 1: Series de tiempo ---
        "m1": {
            "serie": _leer_csv("m1_serie_historica.csv", parse_dates=["ds"]),
            "pronostico": _leer_csv("m1_pronostico.csv", parse_dates=["ds"]),
            "metricas": _leer_json("m1_metricas.json"),
        },
        # --- Modulo 2: Regresion ---
        "m2": {
            "comparacion": _leer_csv("m2_comparacion_modelos.csv"),
            "importancia": _leer_csv("m2_importancia_variables.csv"),
            "anomalias": _leer_csv("m2_anomalias.csv"),
            "scatter": _leer_csv("m2_scatter.csv"),
            "metricas": _leer_json("m2_metricas.json"),
        },
        # --- Modulo 3: Clasificacion ---
        "m3": {
            "balance": _leer_csv("m3_balance_clases.csv"),
            "comparacion": _leer_csv("m3_comparacion_modelos.csv"),
            "matriz": _leer_csv("m3_matriz_confusion.csv", index_col=0),
            "roc": _leer_csv("m3_curva_roc.csv"),
            "metricas": _leer_json("m3_metricas.json"),
        },
        # --- Modulo 4: Segmentacion ---
        "m4": {
            "perfil": _leer_csv("m4_perfil_carriers.csv"),
            "resumen": _leer_csv("m4_resumen_grupos.csv", index_col=0),
            "pca": _leer_csv("m4_pca_coords.csv"),
            "seleccion_k": _leer_csv("m4_seleccion_k.csv"),
            "metricas": _leer_json("m4_metricas.json"),
        },
    }


if __name__ == "__main__":
    # Auto-prueba: correr `python data_ml.py` para verificar que todo carga.
    ml = cargar_ml()
    print("Resultados de ML cargados correctamente:\n")
    for modulo, contenido in ml.items():
        print(f"  [{modulo}]")
        for clave, valor in contenido.items():
            if isinstance(valor, pd.DataFrame):
                print(f"    {clave:14s} DataFrame {valor.shape}")
            else:
                print(f"    {clave:14s} dict ({len(valor)} metricas)")
        print()
