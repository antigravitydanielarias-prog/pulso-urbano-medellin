# =============================================================================
# modules/rules_engine.py — Motor de reglas para conclusiones dinámicas
# =============================================================================
#
# Arquitectura desacoplada: recibe contexto de filtros + métricas,
# evalúa reglas, retorna mensajes con severidad y recomendaciones.
#
# Diseñado para evolucionar hacia inferencia automática o ML en el futuro.
# Cada regla es una función pura: (contexto) → Conclusión | None
# =============================================================================

from dataclasses import dataclass, field
from typing import Callable
import pandas as pd

from config import THRESHOLDS, SEVERITY_ICONS, SEVERITY_COLORS


# ---------------------------------------------------------------------------
# Tipos de datos
# ---------------------------------------------------------------------------

@dataclass
class Conclusion:
    """Unidad de resultado del motor de análisis."""
    titulo:         str
    mensaje:        str
    severidad:      str          # "normal" | "tendencia" | "alerta" | "atipico" | "recomend"
    recomendacion:  str = ""
    datos_apoyo:    dict = field(default_factory=dict)

    @property
    def icono(self) -> str:
        return SEVERITY_ICONS.get(self.severidad, "ℹ️")

    @property
    def color(self) -> str:
        return SEVERITY_COLORS.get(self.severidad, "#8892A4")


# ---------------------------------------------------------------------------
# Contexto que recibe el motor
# ---------------------------------------------------------------------------

@dataclass
class AnalysisContext:
    """Estado completo del dashboard en el momento del análisis."""
    df_filtrado:     pd.DataFrame
    summary:         dict
    franja:          str
    motivos:         list[str]
    estratos:        list[int]
    sistemas:        list[str]
    lineas:          list[str]
    df_parque:       pd.DataFrame


# ---------------------------------------------------------------------------
# Definición de reglas
# ---------------------------------------------------------------------------

def _regla_congestion_pico(ctx: AnalysisContext) -> Conclusion | None:
    """
    REGLA: flujo alto + hora pico + motivo laboral → alerta de congestión.
    """
    if ctx.summary.get("flujo_promedio", 0) < THRESHOLDS["flujo_alto"] * 100:
        return None
    if ctx.franja not in THRESHOLDS["hora_pico"]:
        return None
    if not any(m in THRESHOLDS["motivo_laboral"] for m in ctx.motivos):
        return None

    pct = ctx.summary["pct_en_alerta"]
    linea = ctx.summary.get("linea_mas_cargada", "N/A")
    return Conclusion(
        titulo="Congestión en hora pico laboral",
        mensaje=(
            f"El {pct:.0f}% de las estaciones analizadas supera el umbral de congestión. "
            f"La Línea {linea} concentra la mayor presión de demanda durante esta franja. "
            f"Los viajes con motivo laboral amplifican la saturación en los nodos de transferencia."
        ),
        severidad="alerta",
        recomendacion=(
            "Considerar refuerzo de frecuencias en la Línea A entre 6–9 am. "
            "Evaluar apertura anticipada de rutas alimentadoras en comunas 1–4."
        ),
        datos_apoyo={
            "flujo_promedio": ctx.summary.get("flujo_promedio"),
            "estaciones_alerta": ctx.summary.get("en_alerta"),
        },
    )


def _regla_cable_presion_social(ctx: AnalysisContext) -> Conclusion | None:
    """
    REGLA: cables activos + estratos bajos + alta demanda → presión social.
    """
    if "Metrocable" not in ctx.sistemas:
        return None
    if not any(e in ctx.estratos for e in THRESHOLDS["estratos_vulnerables"]):
        return None

    cables_df = ctx.df_filtrado[ctx.df_filtrado["sistema_label"] == "Metrocable"]
    if cables_df.empty:
        return None

    flujo_cables = cables_df["flujo_activo"].mean()
    if flujo_cables < 0.45:
        return None

    return Conclusion(
        titulo="Presión de movilidad en comunas de ladera",
        mensaje=(
            f"Las estaciones de Metrocable presentan un flujo promedio del {flujo_cables*100:.0f}%. "
            f"En estratos 1–3, el cable es el único acceso formal al sistema integrado. "
            f"Una falla operativa genera efecto cascada inmediato sobre las rutas alimentadoras C6."
        ),
        severidad="atipico",
        recomendacion=(
            "Priorizar mantenimiento preventivo en cables K, J y M. "
            "Activar protocolos de rutas alternas para comunas 1, 2 y 3 ante interrupciones."
        ),
        datos_apoyo={"flujo_cables": round(flujo_cables * 100, 1)},
    )


def _regla_parque_caida(ctx: AnalysisContext) -> Conclusion | None:
    """
    REGLA: caída interanual del parque automotor > umbral → tendencia preocupante.
    """
    if ctx.df_parque.empty or len(ctx.df_parque) < 2:
        return None

    df = ctx.df_parque.copy()
    df.columns = df.columns.str.strip()
    df = df.sort_values("AÑO")

    ultimo = df.iloc[-1]["Total"]
    penultimo = df.iloc[-2]["Total"]

    if penultimo == 0:
        return None

    delta = (ultimo - penultimo) / penultimo
    if delta > THRESHOLDS["delta_parque_caida"]:
        return None

    return Conclusion(
        titulo=f"Reducción del parque automotor ({delta*100:.1f}%)",
        mensaje=(
            f"El parque automotor registró una caída del {abs(delta)*100:.1f}% "
            f"respecto al año anterior (de {int(penultimo):,} a {int(ultimo):,} unidades). "
            f"Esto reduce la capacidad de las rutas alimentadoras y transfiere presión al sistema Metro."
        ),
        severidad="tendencia",
        recomendacion=(
            "Evaluar concesión temporal de flota adicional en rutas de mayor demanda. "
            "Revisar condiciones de operación de las cuencas C3 y C6."
        ),
        datos_apoyo={"delta_pct": round(delta * 100, 1), "ultimo_año": int(df.iloc[-1]["AÑO"])},
    )


def _regla_nodo_transferencia(ctx: AnalysisContext) -> Conclusion | None:
    """
    REGLA: nodos de transferencia (San Antonio, Acevedo) con flujo crítico.
    """
    nodos = ["San Antonio", "Acevedo"]
    df = ctx.df_filtrado
    if df.empty:
        return None

    nodos_df = df[df["label"].str.contains("|".join(nodos), na=False)]
    if nodos_df.empty:
        return None

    criticos = nodos_df[nodos_df["flujo_activo"] >= THRESHOLDS["flujo_critico"]]
    if criticos.empty:
        return None

    nombres = criticos["label"].str.extract(r"(San Antonio|Acevedo)")[0].dropna().unique()
    nombres_str = " y ".join(nombres)

    return Conclusion(
        titulo=f"Nodo crítico: {nombres_str}",
        mensaje=(
            f"Las estaciones de transferencia en {nombres_str} registran ocupación crítica "
            f"(>90% de capacidad). Estas son el eje de intercambio entre las Líneas A, B y T. "
            f"La saturación aquí propaga congestión secundaria hacia toda la red."
        ),
        severidad="atipico",
        recomendacion=(
            "Implementar gestión activa de acceso en torniquetes. "
            "Comunicar rutas alternas por canales digitales en tiempo real."
        ),
        datos_apoyo={"estaciones_criticas": list(criticos["label"].values)},
    )


def _regla_tranvia_demanda(ctx: AnalysisContext) -> Conclusion | None:
    """
    REGLA: Tranvía activo + motivo Estudio → oportunidad de refuerzo.
    """
    if "Tranvía" not in ctx.sistemas:
        return None
    if "Estudio" not in ctx.motivos:
        return None

    tranvia_df = ctx.df_filtrado[ctx.df_filtrado["sistema_label"] == "Tranvía"]
    if tranvia_df.empty:
        return None

    flujo = tranvia_df["flujo_activo"].mean()
    if flujo < 0.40:
        return Conclusion(
            titulo="Tranvía: capacidad disponible para viajes de estudio",
            mensaje=(
                f"El corredor del Tranvía Ayacucho presenta ocupación moderada ({flujo*100:.0f}%). "
                f"Con motivo de viaje predominantemente estudiantil, existe oportunidad de captar "
                f"más demanda desde las comunas 8 y 9 hacia la Universidad de Antioquia y el ITM."
            ),
            severidad="tendencia",
            recomendacion=(
                "Fortalecer la integración tarifaria con rutas C6-019 y C6-020. "
                "Campañas de comunicación en instituciones educativas del corredor."
            ),
        )
    return None


def _regla_sistema_normal(ctx: AnalysisContext) -> Conclusion | None:
    """
    REGLA DE CIERRE: si no hay alertas significativas, confirmar normalidad.
    """
    flujo = ctx.summary.get("flujo_promedio", 0)
    en_alerta = ctx.summary.get("pct_en_alerta", 0)

    if flujo > 60 or en_alerta > 20:
        return None

    return Conclusion(
        titulo="Sistema operando dentro de parámetros normales",
        mensaje=(
            f"Con los filtros actuales, el flujo promedio es de {flujo:.0f}% y solo "
            f"el {en_alerta:.0f}% de las estaciones presenta alta demanda. "
            f"No se detectan patrones atípicos en la combinación de variables seleccionada."
        ),
        severidad="normal",
        recomendacion="Monitorear cambios al activar la franja de tarde pico (5–8 pm).",
    )


# ---------------------------------------------------------------------------
# Motor principal
# ---------------------------------------------------------------------------

# Registro de reglas en orden de evaluación
RULES: list[Callable[[AnalysisContext], Conclusion | None]] = [
    _regla_congestion_pico,
    _regla_nodo_transferencia,
    _regla_cable_presion_social,
    _regla_parque_caida,
    _regla_tranvia_demanda,
    _regla_sistema_normal,   # siempre al final como fallback
]


def run_analysis(ctx: AnalysisContext) -> list[Conclusion]:
    """
    Ejecuta todas las reglas sobre el contexto dado.
    Retorna lista de conclusiones activas, sin duplicados de severidad crítica.

    Modo de extensión futura:
        - Reemplazar funciones de regla por modelos ML que retornen Conclusion.
        - Agregar reglas por API (GeoJSON de obras, eventos, clima).
    """
    resultados: list[Conclusion] = []

    for rule_fn in RULES:
        try:
            conclusion = rule_fn(ctx)
            if conclusion is not None:
                resultados.append(conclusion)
        except Exception as e:
            # Regla fallida no interrumpe el análisis completo
            resultados.append(Conclusion(
                titulo="Error en regla de análisis",
                mensaje=f"Una regla no pudo evaluarse: {str(e)}",
                severidad="normal",
            ))

    return resultados
