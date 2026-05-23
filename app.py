# =============================================================================
# app.py — Pulso Urbano · Valle de Aburrá — Dashboard de Movilidad
# =============================================================================
#
# Punto de entrada principal. Para correr:
#   streamlit run app.py
#
# =============================================================================

import streamlit as st

# ── Page config — DEBE IR PRIMERO ────────────────────────────────────────────
st.set_page_config(
    page_title="Pulso Urbano · Valle de Aburrá",
    page_icon="🚇",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Imports propios ──────────────────────────────────────────────────────────
from streamlit_folium import st_folium

from config import (
    MOTIVOS_VIAJE, FRANJAS_HORARIAS, ESTRATOS,
    LINE_COLORS, SYSTEM_COLORS, AMVA_MUNICIPIOS,
)
from modules.data_loader    import load_all
from modules.data_processor import filter_estaciones, compute_system_summary
from modules.rules_engine   import run_analysis, AnalysisContext
from modules.map_renderer   import build_map
from modules.ui_components  import (
    render_conclusion_card,
    render_kpi_row,
    render_parque_chart,
    render_empty_state,
    render_section_header,
    render_amva_kpis,
    render_distribucion_horaria_chart,
    render_modal_share_chart,
)


# ── CSS personalizado ─────────────────────────────────────────────────────────
def _inject_css():
    try:
        with open("assets/style.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.markdown("""
        <style>
        [data-testid="stAppViewContainer"] { background: #0A0E1A; }
        [data-testid="stSidebar"] { background: #0D1117; }
        </style>
        """, unsafe_allow_html=True)


_inject_css()


# ── Session state ─────────────────────────────────────────────────────────────
if "conclusiones"   not in st.session_state: st.session_state.conclusiones   = []
if "summary"        not in st.session_state: st.session_state.summary        = {}
if "df_filtrado"    not in st.session_state: st.session_state.df_filtrado    = None
if "analisis_listo" not in st.session_state: st.session_state.analisis_listo = False


# ── Carga de datos (cacheada) ─────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def get_data():
    return load_all()


with st.spinner("Cargando sistema de movilidad…"):
    DATA = get_data()


# =============================================================================
# SIDEBAR — Controles
# =============================================================================

with st.sidebar:

    # Logo / header
    st.markdown("""
    <div style="padding:8px 0 20px 0">
      <div style="font-size:22px;font-weight:900;letter-spacing:-0.02em;
                  color:#F7941D;line-height:1.1">PULSO URBANO</div>
      <div style="font-size:11px;color:#8892A4;letter-spacing:0.12em">
        VALLE DE ABURRÁ · MOVILIDAD
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Capas del mapa ────────────────────────────────────────────────────────
    render_section_header("Capas del mapa")

    capas = {
        "estaciones": st.checkbox("🚇 Estaciones Metro/Cable/Tranvía", value=True),
        "paradas":    st.checkbox("🚌 Paradas alimentadoras",          value=True),
        "rutas_bus":  st.checkbox("🛣️ Rutas de bus (130, 190, 302…)",  value=False),
    }

    modo_oscuro = st.toggle("🌙 Mapa oscuro", value=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── Filtros de análisis ───────────────────────────────────────────────────
    render_section_header("Filtros de análisis")

    # Sistemas activos
    todos_sistemas = sorted(DATA["estaciones"]["sistema_label"].unique().tolist())
    sistemas_sel = st.multiselect(
        "Sistema",
        options=todos_sistemas,
        default=todos_sistemas,
        help="Filtra qué sistemas incluir en el análisis.",
    )

    # Líneas
    lineas_disponibles = sorted(DATA["estaciones"]["linea"].unique().tolist())
    lineas_sel = st.multiselect(
        "Líneas",
        options=lineas_disponibles,
        default=lineas_disponibles,
        help="Selecciona líneas específicas.",
    )

    # Franja horaria
    franja_labels = list(FRANJAS_HORARIAS.values())
    franja_keys   = list(FRANJAS_HORARIAS.keys())
    franja_idx = st.selectbox(
        "Franja horaria",
        options=range(len(franja_keys)),
        format_func=lambda i: franja_labels[i],
        index=2,   # Tarde por defecto
    )
    franja_sel = franja_keys[franja_idx]

    # Motivos de viaje
    motivos_sel = st.multiselect(
        "Motivo de viaje",
        options=MOTIVOS_VIAJE,
        default=["Trabajo", "Estudio"],
    )

    # Estratos socioeconómicos
    estratos_sel = st.multiselect(
        "Estrato socioeconómico",
        options=ESTRATOS,
        default=ESTRATOS,
        format_func=lambda e: f"Estrato {e}",
    )

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ── Botón de análisis ─────────────────────────────────────────────────────
    ejecutar = st.button(
        "⚡ Ejecutar análisis",
        use_container_width=True,
        type="primary",
    )

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    render_section_header("Tendencia histórica", "Parque automotor")
    render_parque_chart(DATA["parque"])


# =============================================================================
# ANÁLISIS — cuando se presiona el botón
# =============================================================================

if ejecutar:
    with st.spinner("Analizando sistema…"):
        df_filtrado = filter_estaciones(
            df=DATA["estaciones"],
            sistemas=sistemas_sel,
            lineas=lineas_sel,
            franja=franja_sel,
            motivos=motivos_sel,
            estratos=estratos_sel,
        )

        summary = compute_system_summary(df_filtrado)

        ctx = AnalysisContext(
            df_filtrado=df_filtrado,
            summary=summary,
            franja=franja_sel,
            motivos=motivos_sel,
            estratos=estratos_sel,
            sistemas=sistemas_sel,
            lineas=lineas_sel,
            df_parque=DATA["parque"],
        )

        conclusiones = run_analysis(ctx)

    st.session_state.conclusiones   = conclusiones
    st.session_state.summary        = summary
    st.session_state.df_filtrado    = df_filtrado
    st.session_state.analisis_listo = True


# =============================================================================
# ÁREA PRINCIPAL
# =============================================================================

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    '<div style="padding:0 0 12px 0">'
    '<h1 style="margin:0;font-size:26px;font-weight:900;'
    'letter-spacing:-0.02em;color:#E8EDF5">'
    'Sistema de Movilidad · Valle de Aburrá'
    '</h1>'
    '<p style="margin:4px 0 0 0;color:#8892A4;font-size:13px">'
    'SITVA · Metro, Metrocable, Tranvía, Metro Plus · '
    'Encuesta OD AMVA 2025 · Flujos calibrados · Motor de reglas urbanas'
    '</p>'
    '</div>',
    unsafe_allow_html=True,
)

# ── KPIs AMVA (siempre visibles) ──────────────────────────────────────────────
render_amva_kpis()
st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

# ── KPI row del análisis (solo si hay análisis) ───────────────────────────────
if st.session_state.analisis_listo and st.session_state.summary:
    render_kpi_row(st.session_state.summary)
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

# ── Mapa ──────────────────────────────────────────────────────────────────────
df_para_mapa = (
    st.session_state.df_filtrado
    if st.session_state.analisis_listo and st.session_state.df_filtrado is not None
    else DATA["estaciones"].assign(
        flujo_activo=lambda d: d["flujo_tarde"] if "flujo_tarde" in d.columns else d.get("flujo_base", 0.4),
        congestion="baja",
    )
)

mapa = build_map(
    df_estaciones=df_para_mapa,
    df_paradas=DATA["paradas"],
    df_rutas_bus=DATA["rutas_bus"],
    active_layers=capas,
    dark_mode=modo_oscuro,
)

st_folium(
    mapa,
    width="100%",
    height=500,
    returned_objects=[],
    key="mapa_principal",
)

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ── Contexto AMVA — gráficas con datos reales ─────────────────────────────────
render_section_header(
    "Contexto AMVA · Valle de Aburrá",
    "Encuesta Origen-Destino 2025 · 6,49M viajes/día hábil · 10 municipios",
)

col_horario, col_modal = st.columns([3, 2], gap="large")

with col_horario:
    st.markdown(
        '<div style="font-size:11px;color:#8892A4;margin-bottom:4px">'
        'DISTRIBUCIÓN HORARIA — todos los modos · '
        '<span style="color:#F7941D">banda naranja = franja seleccionada</span>'
        '</div>',
        unsafe_allow_html=True,
    )
    render_distribucion_horaria_chart(franja_sel)

with col_modal:
    st.markdown(
        '<div style="font-size:11px;color:#8892A4;margin-bottom:4px">'
        'MODO PRINCIPAL — % del total de viajes'
        '</div>',
        unsafe_allow_html=True,
    )
    render_modal_share_chart()

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ── Columnas: conclusiones + tabla estaciones ─────────────────────────────────
col_conclusiones, col_tabla = st.columns([3, 2], gap="large")

with col_conclusiones:
    render_section_header(
        "Conclusiones del análisis",
        "Generadas por el motor de reglas urbanas",
    )

    if st.session_state.analisis_listo and st.session_state.conclusiones:
        for c in st.session_state.conclusiones:
            render_conclusion_card(c)
    else:
        render_empty_state(
            "Configura los filtros en el panel lateral<br>y presiona <b>Ejecutar análisis</b> para ver conclusiones."
        )

with col_tabla:
    render_section_header(
        "Estaciones con mayor flujo",
        "Top 8 por demanda activa",
    )

    if st.session_state.analisis_listo and st.session_state.df_filtrado is not None:
        top = (
            st.session_state.df_filtrado
            .nlargest(8, "flujo_activo")[
                ["label", "linea", "flujo_activo", "congestion", "motivo_dominante"]
            ]
            .rename(columns={
                "label":            "Estación",
                "linea":            "Línea",
                "flujo_activo":     "Flujo",
                "congestion":       "Estado",
                "motivo_dominante": "Motivo",
            })
            .reset_index(drop=True)
        )
        top["Flujo"] = (top["Flujo"] * 100).round(1).astype(str) + "%"

        st.dataframe(
            top,
            use_container_width=True,
            hide_index=True,
            height=300,
        )
    else:
        render_empty_state("Ejecuta el análisis para ver la tabla.")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    '<div style="text-align:center;color:#3A4558;font-size:11px;'
    'margin-top:30px;padding-top:16px;'
    'border-top:1px solid rgba(255,255,255,0.05)">'
    'Pulso Urbano · Datos: Metro de Medellín, OpenStreetMap · '
    'Encuesta OD AMVA 2025 · Flujos calibrados con base en patrones reales'
    '</div>',
    unsafe_allow_html=True,
)
