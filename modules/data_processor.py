# =============================================================================
# modules/data_processor.py — Lógica de filtrado y agregación
# =============================================================================

import pandas as pd
import numpy as np
from config import THRESHOLDS


def filter_estaciones(
    df: pd.DataFrame,
    sistemas: list[str],
    lineas: list[str],
    franja: str,
    motivos: list[str],
    estratos: list[int],
) -> pd.DataFrame:
    """
    Aplica todos los filtros activos sobre el DataFrame de estaciones.

    Args:
        df:       DataFrame completo de estaciones (enriquecido).
        sistemas: Lista de sistemas activos ("Metro", "Metrocable", etc.).
        lineas:   Lista de líneas activas (["A", "B", "K", ...]).
        franja:   Clave de franja horaria ("manana", "tarde", etc.).
        motivos:  Lista de motivos de viaje seleccionados.
        estratos: Lista de estratos socioeconómicos (1-6).

    Returns:
        DataFrame filtrado con columna `flujo_activo` según la franja.
    """
    result = df.copy()

    # --- Filtro por sistema -----------------------------------------------
    # "Vehículos Particulares" es un pseudo-sistema para análisis: no filtra estaciones
    sistemas_transit = [s for s in sistemas if "Vehículos" not in s]
    if sistemas_transit:
        result = result[result["sistema_label"].isin(sistemas_transit)]

    # --- Filtro por línea --------------------------------------------------
    if lineas:
        result = result[result["linea"].isin(lineas)]

    # --- Activar columna de flujo según franja -----------------------------
    flujo_col = f"flujo_{franja}" if franja else "flujo_base"
    if flujo_col in result.columns:
        result["flujo_activo"] = result[flujo_col]
    else:
        result["flujo_activo"] = result["flujo_base"]

    # --- Filtro por motivo de viaje ----------------------------------------
    if motivos:
        result = result[result["motivo_dominante"].isin(motivos)]

    # --- Etiqueta de congestión -------------------------------------------
    result["congestion"] = result["flujo_activo"].apply(_classify_congestion)

    return result


def _classify_congestion(flujo: float) -> str:
    """Clasifica el nivel de congestión por umbral."""
    if flujo >= THRESHOLDS["flujo_critico"]:
        return "crítica"
    if flujo >= THRESHOLDS["flujo_alto"]:
        return "alta"
    if flujo >= 0.50:
        return "media"
    return "baja"


def filter_paradas(
    df: pd.DataFrame,
    rutas: list[str] | None = None,
) -> pd.DataFrame:
    """Filtra paradas de alimentadoras por ruta."""
    if not rutas:
        return df
    return df[df["ruta"].isin(rutas)]


def aggregate_by_linea(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega métricas por línea para el panel de resumen.

    Returns:
        DataFrame con columnas: linea, n_estaciones, flujo_promedio,
        congestion_alta, motivo_dominante.
    """
    if df.empty:
        return pd.DataFrame()

    agg = (
        df.groupby("linea")
        .agg(
            n_estaciones=("label", "count"),
            flujo_promedio=("flujo_activo", "mean"),
            flujo_max=("flujo_activo", "max"),
            motivo_dominante=("motivo_dominante", lambda x: x.mode()[0] if len(x) > 0 else "N/A"),
        )
        .reset_index()
    )

    agg["congestion_alta"] = agg["flujo_promedio"] >= THRESHOLDS["flujo_alto"]
    agg["flujo_promedio_pct"] = (agg["flujo_promedio"] * 100).round(1)
    return agg.sort_values("flujo_promedio", ascending=False)


def get_estaciones_criticas(df: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
    """Retorna las N estaciones con mayor flujo activo."""
    if df.empty:
        return pd.DataFrame()
    return (
        df.nlargest(top_n, "flujo_activo")[
            ["label", "linea", "sistema_label", "flujo_activo", "congestion", "motivo_dominante"]
        ]
        .reset_index(drop=True)
    )


def compute_system_summary(df: pd.DataFrame) -> dict:
    """
    Calcula métricas globales del snapshot actual.

    Returns:
        Dict con KPIs: total estaciones, flujo promedio, estaciones en alerta,
        línea más cargada, motivo dominante global.
    """
    if df.empty:
        return {}

    flujo_prom = df["flujo_activo"].mean()
    en_alerta = (df["flujo_activo"] >= THRESHOLDS["flujo_alto"]).sum()
    linea_max = df.loc[df["flujo_activo"].idxmax(), "linea"] if not df.empty else "N/A"
    motivo_global = df["motivo_dominante"].mode()[0] if not df.empty else "N/A"

    return {
        "total_estaciones":   len(df),
        "flujo_promedio":     float(round(flujo_prom * 100, 1)),
        "en_alerta":          int(en_alerta),
        "pct_en_alerta":      float(round(en_alerta / len(df) * 100, 1)) if len(df) > 0 else 0.0,
        "linea_mas_cargada":  linea_max,
        "motivo_dominante":   motivo_global,
    }
