# =============================================================================
# modules/rules_engine.py — Motor de reglas para conclusiones dinámicas
# =============================================================================
#
# Arquitectura desacoplada: recibe contexto de filtros + métricas,
# evalúa reglas, retorna mensajes con severidad y recomendaciones.
#
# Reglas divididas en dos capas:
#   Capa 1 — Operacional: estado del SITVA (flujos, congestión, nodos)
#   Capa 2 — Estructural: hallazgos de la Encuesta OD AMVA 2025
# =============================================================================

from dataclasses import dataclass, field
from typing import Callable
import pandas as pd

from config import (
    THRESHOLDS, SEVERITY_ICONS, SEVERITY_COLORS,
    AMVA_KPIS, AMVA_ESTRATOS_PCT, AMVA_HORARIO,
)


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


# ===========================================================================
# CAPA 1 — Reglas operacionales (estado del SITVA)
# ===========================================================================

def _regla_congestion_pico(ctx: AnalysisContext) -> Conclusion | None:
    """REGLA: flujo alto + hora pico + motivo laboral → alerta de congestión."""
    if ctx.summary.get("flujo_promedio", 0) < THRESHOLDS["flujo_alto"] * 100:
        return None
    if ctx.franja not in THRESHOLDS["hora_pico"]:
        return None
    if not any(m in THRESHOLDS["motivo_laboral"] for m in ctx.motivos):
        return None

    pct   = ctx.summary["pct_en_alerta"]
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
            "flujo_promedio":     ctx.summary.get("flujo_promedio"),
            "estaciones_alerta":  ctx.summary.get("en_alerta"),
        },
    )


def _regla_nodo_transferencia(ctx: AnalysisContext) -> Conclusion | None:
    """REGLA: nodos de transferencia (San Antonio, Acevedo) con flujo crítico."""
    nodos = ["San Antonio", "Acevedo"]
    df    = ctx.df_filtrado
    if df.empty:
        return None

    nodos_df = df[df["label"].str.contains("|".join(nodos), na=False)]
    if nodos_df.empty:
        return None

    criticos = nodos_df[nodos_df["flujo_activo"] >= THRESHOLDS["flujo_critico"]]
    if criticos.empty:
        return None

    nombres    = criticos["label"].str.extract(r"(San Antonio|Acevedo)")[0].dropna().unique()
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


def _regla_cable_presion_social(ctx: AnalysisContext) -> Conclusion | None:
    """REGLA: cables activos + estratos bajos + alta demanda → presión social."""
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
    """REGLA: caída interanual del parque automotor > umbral → tendencia preocupante."""
    if ctx.df_parque.empty or len(ctx.df_parque) < 2:
        return None

    df = ctx.df_parque.copy()
    df.columns = df.columns.str.strip()
    df = df.sort_values("AÑO")

    ultimo    = df.iloc[-1]["Total"]
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


def _regla_tranvia_demanda(ctx: AnalysisContext) -> Conclusion | None:
    """REGLA: Tranvía activo + motivo Estudio → oportunidad de refuerzo."""
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


# ===========================================================================
# CAPA 2 — Reglas estructurales (Encuesta OD AMVA 2025)
# ===========================================================================

def _regla_brecha_equidad(ctx: AnalysisContext) -> Conclusion | None:
    """
    REGLA: estratos 1-3 seleccionados + sistema público activo →
    revela la penalización de tiempo que recae sobre la población de menores ingresos.
    """
    if not any(e in ctx.estratos for e in [1, 2, 3]):
        return None
    if not any(s in ctx.sistemas for s in ["Metro", "Metrocable", "Tranvía"]):
        return None

    # Datos reales OD 2025
    pct_123     = AMVA_ESTRATOS_PCT[1] + AMVA_ESTRATOS_PCT[2] + AMVA_ESTRATOS_PCT[3]  # 82.71%
    t_publico   = 56.58   # min promedio en transporte público
    t_privado   = 39.03   # min promedio en transporte privado
    penalizacion = t_publico - t_privado  # 17.55 min
    dias_habiles = 240
    horas_perdidas_año = penalizacion * 2 * dias_habiles / 60  # viaje ida-vuelta

    return Conclusion(
        titulo="Brecha de equidad: 17.6 min de penalización diaria",
        mensaje=(
            f"Los estratos 1–3 concentran el {pct_123:.1f}% de los viajes en el AMVA "
            f"y dependen principalmente del transporte público. "
            f"Sin embargo, un viaje en transporte público toma en promedio {t_publico} min, "
            f"frente a {t_privado} min en transporte privado. "
            f"Esta penalización de {penalizacion:.0f} min/viaje (×2 por ida-vuelta) equivale a "
            f"perder ~{horas_perdidas_año:.0f} horas al año por persona solo en tiempos de desplazamiento. "
            f"La inequidad del sistema se mide en tiempo, no solo en dinero."
        ),
        severidad="alerta",
        recomendacion=(
            f"Reducir tiempos de ciclo en los corredores de estratos 1–3. "
            f"Implementar carriles exclusivos en rutas con alta concentración de viajes de estrato bajo. "
            f"Objetivo: reducir la brecha a menos de 10 min."
        ),
        datos_apoyo={
            "pct_estratos_123":   round(pct_123, 1),
            "tiempo_publico_min": t_publico,
            "tiempo_privado_min": t_privado,
            "penalizacion_min":   round(penalizacion, 1),
            "horas_perdidas_año": round(horas_perdidas_año),
        },
    )


def _regla_dominio_moto(ctx: AnalysisContext) -> Conclusion | None:
    """
    REGLA: franja pico + motivo trabajo → señal de dominio de la motocicleta
    como solución individual ante déficit del sistema público.
    """
    if ctx.franja not in ["manana", "tarde"]:
        return None
    if "Trabajo" not in ctx.motivos:
        return None

    motos_1000  = AMVA_KPIS["motos_por_1000"]   # 120.5
    autos_1000  = AMVA_KPIS["autos_por_1000"]   # 67.13
    ratio       = motos_1000 / autos_1000
    pct_viajes_moto = 14.57
    pct_viajes_auto = 11.70

    return Conclusion(
        titulo="La moto supera al auto: señal de quiebre del sistema",
        mensaje=(
            f"El AMVA registra {motos_1000} motocicletas por 1.000 habitantes, "
            f"{ratio:.1f}× más que automóviles ({autos_1000}/1.000). "
            f"Las motos generan el {pct_viajes_moto}% de los viajes, superando al automóvil ({pct_viajes_auto}%). "
            f"Este fenómeno no es preferencia cultural: es la respuesta racional de los ciudadanos "
            f"ante un sistema de transporte público que tarda 17.6 min más por viaje que el privado. "
            f"La moto llena el vacío, a costa de la siniestralidad vial más alta de la región."
        ),
        severidad="atipico",
        recomendacion=(
            "Fortalecer la cobertura y velocidad del sistema masivo en franjas pico laborales. "
            "Crear corredores de motocicletas seguros en los accesos norte y sur del Valle. "
            "Evaluar incentivos de integración modal moto–SITVA."
        ),
        datos_apoyo={
            "motos_por_1000":    motos_1000,
            "autos_por_1000":    autos_1000,
            "ratio_moto_auto":   round(ratio, 2),
            "pct_viajes_moto":   pct_viajes_moto,
            "pct_viajes_auto":   pct_viajes_auto,
        },
    )


def _regla_ciudad_peatonal(ctx: AnalysisContext) -> Conclusion | None:
    """
    REGLA: siempre activa — muestra la paradoja de que el AMVA es una ciudad
    peatonal por necesidad, con subinversión crónica en espacio peatonal.
    """
    # Solo disparar si el análisis cubre estratos vulnerables (caminan más)
    if not any(e in ctx.estratos for e in [1, 2, 3]):
        return None

    pct_pie        = 14.94 + 32.68   # TPC + A pie → modos no motorizados/lentos
    viajes_pie     = round(AMVA_KPIS["viajes_no_motorizados"])
    tiempo_pie_min = 22.1
    tiempo_pub_min = 56.58
    eficiencia_ratio = tiempo_pub_min / tiempo_pie_min

    return Conclusion(
        titulo="Paradoja peatonal: el modo más eficiente, el más descuidado",
        mensaje=(
            f"'A pie' es el modo de transporte más usado en el AMVA con el 32.7% de los viajes "
            f"(~{viajes_pie/1e6:.2f}M viajes/día). "
            f"El tiempo promedio caminando es {tiempo_pie_min} min, "
            f"{eficiencia_ratio:.1f}× más eficiente que el transporte público ({tiempo_pub_min} min). "
            f"Sumando TPC, el 47.6% de los viajes ocurren en modos activos o de baja velocidad. "
            f"Sin embargo, la inversión en infraestructura sigue priorizando el automóvil "
            f"que mueve solo el {11.70}% de los viajes."
        ),
        severidad="tendencia",
        recomendacion=(
            "Ampliar y mejorar andenes, pasos peatonales seguros y conectividad directa con estaciones SITVA. "
            "Evaluar cicloinfrastructura en los 3–5 km alrededor de cada estación de metro para "
            "capturar viajes actualmente hechos a pie o en moto."
        ),
        datos_apoyo={
            "pct_a_pie":          32.68,
            "pct_tpc":            14.94,
            "viajes_no_motor":    viajes_pie,
            "tiempo_pie_min":     tiempo_pie_min,
            "eficiencia_ratio":   round(eficiencia_ratio, 1),
        },
    )


def _regla_saturacion_sistemica(ctx: AnalysisContext) -> Conclusion | None:
    """
    REGLA: franja pico + sistema metro activo →
    cuantifica las horas diarias en las que el sistema opera sobre umbral crítico.
    Responde a la pregunta: ¿qué tan colapsado está el sistema realmente?
    """
    if ctx.franja not in ["manana", "tarde"]:
        return None
    if "Metro" not in ctx.sistemas:
        return None

    publico     = AMVA_HORARIO["publico"]
    max_pub     = max(publico)
    horas_altas = sum(1 for v in publico if v / max_pub >= 0.75)   # >= 75% del pico
    horas_crit  = sum(1 for v in publico if v / max_pub >= 0.90)   # >= 90% del pico

    # El pico absoluto ocurre a las 6am
    hora_pico1 = 6
    hora_pico2 = 17
    viajes_pico = max_pub
    total_diario = AMVA_KPIS["total_viajes"]
    pct_pub_total = round(AMVA_KPIS["viajes_publicos"] / total_diario * 100, 1)

    return Conclusion(
        titulo=f"Sistema bajo estrés {horas_altas}h/día — colapso estructural, no eventual",
        mensaje=(
            f"El análisis de la distribución horaria real (OD AMVA 2025) muestra que "
            f"el transporte público opera sobre el 75% de su carga máxima durante {horas_altas} horas al día, "
            f"y supera el 90% durante {horas_crit} hora(s). "
            f"Los picos absolutos ocurren a las {hora_pico1}:00 am ({viajes_pico:,} viajes/hora) "
            f"y a las {hora_pico2}:00 pm. "
            f"Con {pct_pub_total}% de los {total_diario/1e6:.2f}M viajes diarios en modos públicos, "
            f"la saturación no es un evento ocasional: es la condición normal del sistema."
        ),
        severidad="atipico",
        recomendacion=(
            "Implementar gestión dinámica de demanda: tarifa diferencial en horas pico, "
            "incentivos para viaje en valle (9am–12pm). "
            "Ampliar flota efectiva en las 2 horas más críticas (6am y 5pm) con buses expresos "
            "en los corredores Metro A y alimentadoras norte."
        ),
        datos_apoyo={
            "horas_sobre_75pct":  horas_altas,
            "horas_sobre_90pct":  horas_crit,
            "viajes_pico_hora":   viajes_pico,
            "pct_publico_total":  pct_pub_total,
            "total_viajes_dia":   total_diario,
        },
    )


def _regla_sistema_normal(ctx: AnalysisContext) -> Conclusion | None:
    """REGLA DE CIERRE: si no hay alertas significativas, confirmar normalidad."""
    flujo    = ctx.summary.get("flujo_promedio", 0)
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


# ===========================================================================
# Motor principal
# ===========================================================================

RULES: list[Callable[[AnalysisContext], Conclusion | None]] = [
    # Capa 1 — Operacional
    _regla_congestion_pico,
    _regla_nodo_transferencia,
    _regla_cable_presion_social,
    _regla_parque_caida,
    _regla_tranvia_demanda,
    # Capa 2 — Estructural (OD AMVA 2025)
    _regla_saturacion_sistemica,
    _regla_brecha_equidad,
    _regla_dominio_moto,
    _regla_ciudad_peatonal,
    # Fallback
    _regla_sistema_normal,
]


def run_analysis(ctx: AnalysisContext) -> list[Conclusion]:
    """
    Ejecuta todas las reglas sobre el contexto dado.
    Retorna lista de conclusiones activas (Capa 1 + Capa 2).

    Modo de extensión futura:
        - Reemplazar funciones de regla por modelos ML que retornen Conclusion.
        - Agregar reglas por API (GeoJSON de obras, eventos, clima, alertas Metro).
    """
    resultados: list[Conclusion] = []

    for rule_fn in RULES:
        try:
            conclusion = rule_fn(ctx)
            if conclusion is not None:
                resultados.append(conclusion)
        except Exception as e:
            resultados.append(Conclusion(
                titulo="Error en regla de análisis",
                mensaje=f"Una regla no pudo evaluarse: {str(e)}",
                severidad="normal",
            ))

    return resultados
