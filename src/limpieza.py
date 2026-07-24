"""
Pipeline de limpieza para fact_shipments.

Implementa las 8 reglas derivadas del diagnóstico de calidad documentado en
notebooks/01_exploracion_calidad.ipynb. El orden de los pasos no es
intercambiable: la normalización de categóricas debe preceder a la
deduplicación, y la reconstrucción de fechas depende de la conversión de tipos.

Uso:
    from limpieza import LimpiadorEmbarques

    limpiador = LimpiadorEmbarques(df_raw)
    df_limpio = limpiador.ejecutar()
    limpiador.reporte()

Autor: Sergio Corona
"""

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Diccionarios de normalización
# ---------------------------------------------------------------------------
# Derivados del inventario de valores categóricos (notebook 01, sección 5.4).
# Se aplican tras .str.strip().str.upper(), por lo que las claves van en
# mayúsculas. El uso de .map() es deliberado: deja NaN en cualquier valor no
# contemplado, lo que convierte un vacío no previsto en un error visible en
# lugar de una corrupción silenciosa.

MAPA_MODO = {
    "TL": "TL",
    "TRUCKLOAD": "TL",
    "LTL": "LTL",
    "PARCEL": "Parcel",
    "AIR": "Air",
    "OCEAN": "Ocean",
    "OCEAN FCL": "Ocean",
    "DRAYAGE": "Drayage",
}

MAPA_PAIS = {
    "US": "US",
    "USA": "US",
    "MX": "MX",
    "MEXICO": "MX",
    "CA": "CA",
    "CANADA": "CA",
}

COLUMNAS_FECHA = [
    "ship_date",
    "planned_pickup_ts",
    "planned_delivery_ts",
    "actual_pickup_ts",
    "actual_delivery_ts",
]

TOLERANCIA_OTD_HORAS = 12


# ---------------------------------------------------------------------------
# Clase principal
# ---------------------------------------------------------------------------


class LimpiadorEmbarques:
    """Aplica el pipeline de limpieza a un DataFrame de embarques.

    Cada paso se implementa como un método independiente que registra su
    efecto en la bitácora interna. Los métodos operan sobre una copia del
    DataFrame original, que nunca se modifica.
    """

    def __init__(self, df):
        self.df_original = df
        self.df = df.copy()
        self.bitacora = []

    def _registrar(self, paso, detalle, afectados):
        """Añade una entrada a la bitácora de ejecución."""
        self.bitacora.append(
            {"paso": paso, "detalle": detalle, "afectados": afectados}
        )
        print(f"[{paso}] {detalle}: {afectados:,}")

    def reporte(self):
        """Devuelve la bitácora como DataFrame."""
        return pd.DataFrame(self.bitacora)

        # -- Paso 1 -------------------------------------------------------------

    def normalizar_categoricas(self):
        """Unifica variantes de formato en mode, origin_country y dest_country.

        Debe ejecutarse ANTES de deduplicar. En el diagnóstico se detectaron
        134 pares de registros que solo diferían en el formato de estas
        columnas ('Mexico' vs 'MX', 'Truckload' vs 'TL'); deduplicar primero
        los dejaría sin detectar, inflando el conteo de embarques y el gasto.
        """
        columnas = {
            "mode": MAPA_MODO,
            "origin_country": MAPA_PAIS,
            "dest_country": MAPA_PAIS,
        }

        total_modificados = 0

        for col, mapa in columnas.items():
            antes = self.df[col].copy()

            normalizada = self.df[col].str.strip().str.upper().map(mapa)

            # .map() deja NaN en valores no contemplados por el diccionario.
            # Si aparece alguno, se interrumpe: es un valor nuevo que exige
            # revisión, no algo que deba resolverse en silencio.
            sin_mapear = normalizada.isna() & self.df[col].notna()
            if sin_mapear.any():
                valores = self.df.loc[sin_mapear, col].unique()
                raise ValueError(
                    f"Valores no contemplados en '{col}': {list(valores)}"
                )

            self.df[col] = normalizada

            modificados = (antes != self.df[col]).sum()
            total_modificados += modificados
            self._registrar("1-normalizar", f"{col}", modificados)

        return self

        # -- Paso 2 -------------------------------------------------------------

    def deduplicar(self):
        """Elimina identificadores repetidos conservando la versión más válida.

        Requiere que las categóricas ya estén normalizadas (paso 1).

        No se usa keep='first': el diagnóstico detectó 11 identificadores donde
        las dos copias difieren en el valor de negocio (signo invertido en el
        costo, peso multiplicado por 1000, entrega anterior al pickup). En esos
        casos el orden de aparición no es criterio: se conserva la copia que
        satisface más reglas de validez.
        """
        antes = len(self.df)

        # Puntaje de validez: una regla cumplida suma un punto. Las
        # comparaciones se hacen sobre texto porque las fechas aún no se
        # convierten (eso es el paso 3); el formato ISO permite ordenar
        # lexicográficamente con el mismo resultado.
        puntaje = (
            (self.df["total_cost_usd"] > 0).astype(int)
            + (self.df["weight_kg"].between(0, 50_000)).astype(int)
            + (self.df["actual_delivery_ts"] >= self.df["actual_pickup_ts"]).astype(int)
        )

        self.df = self.df.assign(_valido=puntaje)

        # Orden descendente por puntaje: la copia más válida queda primero
        # dentro de cada grupo de identificador repetido.
        self.df = (
            self.df.sort_values("_valido", ascending=False, kind="stable")
            .drop_duplicates(subset="shipment_id", keep="first")
            .drop(columns="_valido")
            .sort_index()
        )

        eliminados = antes - len(self.df)
        self._registrar("2-deduplicar", "registros eliminados", eliminados)

        # Verificación explícita: en pandas 3 una operación que no surte
        # efecto puede pasar inadvertida.
        if self.df["shipment_id"].duplicated().any():
            raise ValueError("Quedan identificadores duplicados tras la deduplicación")

        return self

        # -- Paso 3 -------------------------------------------------------------

    def convertir_fechas(self):
        """Convierte las 5 columnas temporales de texto a datetime.

        Se usa errors='coerce' para que un valor no parseable se convierta en
        NaT en lugar de interrumpir la ejecución. El diagnóstico reportó cero
        valores no parseables, por lo que cualquier NaT nuevo indicaría un
        cambio en el archivo de origen: se verifica explícitamente.
        """
        for col in COLUMNAS_FECHA:
            nulos_antes = self.df[col].isna().sum()

            # Resolución fijada explícitamente: pandas 3 la infiere de los
            # datos y asignaría [us] a las columnas con horas redondas y [ns]
            # a las que traen segundos. Unificar evita fricción al exportar.
            self.df[col] = pd.to_datetime(
                self.df[col], errors="coerce"
            ).astype("datetime64[us]")

            nulos_despues = self.df[col].isna().sum()
            no_parseables = nulos_despues - nulos_antes

            if no_parseables > 0:
                raise ValueError(
                    f"'{col}': {no_parseables} valores no parseables como fecha"
                )

            self._registrar("3-fechas", f"{col} → datetime", len(self.df))

        return self

        # -- Paso 4 -------------------------------------------------------------

    def reconstruir_fechas_imposibles(self):
        """Recalcula actual_delivery_ts en los registros con secuencia inválida.

        Requiere que las fechas ya estén convertidas a datetime (paso 3).

        En los 298 casos afectados la entrega figura exactamente 48 horas antes
        del pickup, con desviación estándar cero: es sobrescritura sistemática,
        no ruido. Sumar 48 horas daría un tránsito de cero días, por lo que el
        valor original no está desplazado sino borrado.

        La reconstrucción usa actual_transit_days, columna que la corrupción no
        alteró (media 6.58 días frente a 7.24 planeados, distribución plausible).
        """
        invalidos = self.df["actual_delivery_ts"] < self.df["actual_pickup_ts"]
        n = int(invalidos.sum())

        if n == 0:
            self._registrar("4-fechas-imposibles", "sin casos por reconstruir", 0)
            return self

        # El timedelta resultante es de resolución [ns]; la columna destino es
        # [us]. Pandas 3 rechaza la escritura entre resoluciones distintas, por
        # lo que se convierte el resultado antes de asignarlo.
        reconstruida = (
            self.df.loc[invalidos, "actual_pickup_ts"]
            + pd.to_timedelta(self.df.loc[invalidos, "actual_transit_days"], unit="D")
        ).astype("datetime64[us]")

        self.df.loc[invalidos, "actual_delivery_ts"] = reconstruida

        self._registrar("4-fechas-imposibles", "entregas reconstruidas", n)

        # Verificación: en pandas 3 una asignación mal formulada puede no
        # surtir efecto sin emitir advertencia.
        restantes = int(
            (self.df["actual_delivery_ts"] < self.df["actual_pickup_ts"]).sum()
        )
        if restantes > 0:
            raise ValueError(
                f"Persisten {restantes} registros con entrega anterior al pickup"
            )

        return self

        # -- Paso 5 -------------------------------------------------------------

    def corregir_costos_negativos(self):
        """Invierte el signo de los costos totales negativos.

        El diagnóstico estableció que ningún componente del costo (linehaul,
        fuel, accessorial, customs, detention) presenta valores negativos: la
        corrupción afecta únicamente a la columna agregada. Esto permite
        validar la corrección de forma independiente, comparando el valor
        corregido contra la suma de sus componentes.
        """
        componentes = [
            "linehaul_cost_usd",
            "fuel_surcharge_usd",
            "accessorial_usd",
            "customs_fee_usd",
            "detention_usd",
        ]

        negativos = self.df["total_cost_usd"] < 0
        n = int(negativos.sum())

        if n == 0:
            self._registrar("5-costos", "sin costos negativos", 0)
            return self

        self.df.loc[negativos, "total_cost_usd"] = self.df.loc[
            negativos, "total_cost_usd"
        ].abs()

        self._registrar("5-costos", "signos invertidos", n)

        # Validación independiente: el valor corregido debe aproximarse a la
        # suma de sus componentes. Los registros con algún componente nulo se
        # excluyen: .sum() los trataría como cero y produciría un desvío que
        # refleja el dato ausente, no un error de corrección.
        completos = self.df.loc[negativos, componentes].notna().all(axis=1)
        idx_completos = self.df.loc[negativos].index[completos]

        suma = self.df.loc[idx_completos, componentes].sum(axis=1)
        desvio = (self.df.loc[idx_completos, "total_cost_usd"] - suma).abs()
        fuera = int((desvio > 1).sum())

        self._registrar("5-costos", "validados contra sus componentes", len(idx_completos))
        self._registrar("5-costos", "no validables por componente nulo", int((~completos).sum()))
        self._registrar("5-costos", "corregidos que no cuadran", fuera)

        if (self.df["total_cost_usd"] < 0).any():
            raise ValueError("Persisten costos negativos tras la corrección")

        return self

        # -- Paso 6 -------------------------------------------------------------

    def corregir_pesos_inflados(self):
        """Divide entre 1000 los pesos con error de unidad, por modo de transporte.

        Un umbral global es insuficiente: la mediana de Parcel es de 11 kg y la
        de Ocean de 14,689 kg. Un paquete de 3 kg inflado a 3,000 kg resulta
        absurdo para paquetería pero queda invisible frente a un umbral
        construido sobre embarques marítimos.

        El criterio tiene dos condiciones simultáneas:
          1. El valor excede el percentil 99 de su propio modo.
          2. Dividido entre 1000, regresa al rango [p01, p99] de ese modo.

        La segunda es la que sostiene la corrección: no se declara atípico un
        valor, se demuestra que la hipótesis del error de unidad lo explica.
        """
        limites = self.df.groupby("mode")["weight_kg"].quantile([0.01, 0.99]).unstack()
        limites.columns = ["p01", "p99"]

        p01 = self.df["mode"].map(limites["p01"])
        p99 = self.df["mode"].map(limites["p99"])

        excede = self.df["weight_kg"] > p99
        regresa = (self.df["weight_kg"] / 1000).between(p01, p99)

        inflados = excede & regresa
        n = int(inflados.sum())

        if n == 0:
            self._registrar("6-pesos", "sin pesos inflados", 0)
            return self

        mediana_antes = float(self.df.loc[inflados, "weight_kg"].median())
        maximo_antes = float(self.df.loc[inflados, "weight_kg"].max())

        self.df.loc[inflados, "weight_kg"] = self.df.loc[inflados, "weight_kg"] / 1000

        self._registrar("6-pesos", "corregidos por división entre 1000", n)

        # Distribución por modo: documenta que la detección alcanza los modos
        # ligeros, que un umbral global no cubriría.
        por_modo = self.df.loc[inflados, "mode"].value_counts()
        for modo, cuenta in por_modo.items():
            self._registrar("6-pesos", f"  {modo}", int(cuenta))

        self._detalle_pesos = {
            "mediana_antes": mediana_antes,
            "mediana_despues": float(self.df.loc[inflados, "weight_kg"].median()),
            "maximo_antes": maximo_antes,
            "maximo_despues": float(self.df.loc[inflados, "weight_kg"].max()),
        }

        return self

        # -- Paso 7 -------------------------------------------------------------

    def tratar_nulos(self):
        """Aplica un criterio diferenciado por columna según su uso analítico.

        Debe ejecutarse DESPUÉS del paso 6: la imputación de weight_kg usa la
        mediana por modo, y calcularla con los valores inflados sin corregir
        la desplazaría hacia arriba.

        El descarte de registros sin carrier_id hace que el resultado tenga
        menos filas que fact_shipments_clean.csv, que los conserva. Es una
        divergencia deliberada: sin transportista el registro no alimenta el
        scorecard, que es el eje del análisis.
        """
        # -- carrier_id: descartar --------------------------------------
        sin_carrier = self.df["carrier_id"].isna()
        n_carrier = int(sin_carrier.sum())
        self.df = self.df.loc[~sin_carrier].copy()
        self._registrar("7-nulos", "carrier_id ausente → registro descartado", n_carrier)

        # -- incoterm: etiquetar ----------------------------------------
        n_inco = int(self.df["incoterm"].isna().sum())
        self.df["incoterm"] = self.df["incoterm"].fillna("NO_APLICA")
        self._registrar("7-nulos", "incoterm ausente → NO_APLICA", n_inco)

        # -- accessorial_usd: imputar cero ------------------------------
        n_acc = int(self.df["accessorial_usd"].isna().sum())
        self.df["accessorial_usd"] = self.df["accessorial_usd"].fillna(0.0)
        self._registrar("7-nulos", "accessorial_usd ausente → 0", n_acc)

        # -- weight_kg y volume_cbm: mediana por modo -------------------
        for col in ["weight_kg", "volume_cbm"]:
            n = int(self.df[col].isna().sum())
            medianas = self.df.groupby("mode")[col].transform("median")
            self.df[col] = self.df[col].fillna(medianas)
            self._registrar("7-nulos", f"{col} ausente → mediana de su modo", n)

        # -- actual_delivery_ts: conservar ------------------------------
        n_entrega = int(self.df["actual_delivery_ts"].isna().sum())
        self._registrar(
            "7-nulos", "actual_delivery_ts ausente → se conserva nulo", n_entrega
        )

        # Verificación: solo actual_delivery_ts debe quedar con nulos.
        restantes = self.df.isna().sum()
        con_nulos = restantes[restantes > 0].drop("actual_delivery_ts", errors="ignore")
        if not con_nulos.empty:
            raise ValueError(f"Columnas con nulos no previstos:\n{con_nulos}")

        return self

        # -- Paso 8 -------------------------------------------------------------

    def derivar_metricas(self):
        """Calcula las columnas analíticas: OTD, costo por kg y costo por km.

        El cálculo de OTD aplica una tolerancia de 12 horas sobre
        planned_delivery_ts. Esa regla no está documentada en el dataset: se
        derivó auditando los 25 registros donde la reconstrucción de fechas
        discrepaba del flag original. Reproduce el flag oficial con exactitud
        del 100%.

        La comparación directa de timestamps daría un OTD de 73.80%, diez
        puntos por debajo del 83.92% que reportan los sistemas de origen.
        """
        # -- OTD ---------------------------------------------------------
        limite = self.df["planned_delivery_ts"] + pd.Timedelta(
            hours=TOLERANCIA_OTD_HORAS
        )
        entregado = self.df["actual_delivery_ts"].notna()

        # pd.NA en los no entregados: el OTD no es cero, es indeterminado.
        self.df["otd"] = pd.Series(pd.NA, index=self.df.index, dtype="boolean")
        self.df.loc[entregado, "otd"] = (
            self.df.loc[entregado, "actual_delivery_ts"] <= limite[entregado]
        )

        # -- Retraso en horas --------------------------------------------
        self.df["retraso_horas"] = (
            self.df["actual_delivery_ts"] - self.df["planned_delivery_ts"]
        ).dt.total_seconds() / 3600

        # -- Costo unitario ----------------------------------------------
        # Se evita la división por cero dejando nulo el resultado.
        self.df["costo_por_kg"] = self.df["total_cost_usd"] / self.df["weight_kg"].replace(0, np.nan)
        self.df["costo_por_km"] = self.df["total_cost_usd"] / self.df["distance_km"].replace(0, np.nan)

        self._registrar("8-metricas", "columnas derivadas", 4)
        self._registrar("8-metricas", "entregas con OTD calculable", int(entregado.sum()))
        self._registrar("8-metricas", "OTD indeterminado (sin entrega)", int((~entregado).sum()))

        return self

        # -- Orquestación -------------------------------------------------------

    def ejecutar(self):
        """Aplica el pipeline completo en el orden requerido.

        La secuencia no es intercambiable:
          · El paso 1 precede al 2: normalizar después de deduplicar dejaría
            sin detectar 134 duplicados enmascarados por formato.
          · El paso 4 depende del 3: la reconstrucción opera sobre datetime.
          · El paso 7 sigue al 6: imputar la mediana de weight_kg con los
            valores inflados aún presentes la desplazaría hacia arriba.
        """
        return (
            self.normalizar_categoricas()
            .deduplicar()
            .convertir_fechas()
            .reconstruir_fechas_imposibles()
            .corregir_costos_negativos()
            .corregir_pesos_inflados()
            .tratar_nulos()
            .derivar_metricas()
        )