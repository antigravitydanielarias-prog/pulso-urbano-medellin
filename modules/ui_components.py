# =============================================================================
# modules/ui_components.py — Componentes reutilizables de interfaz
# =============================================================================

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from config import SEVERITY_COLORS, SEVERITY_ICONS


# ---------------------------------------------------------------------------
# Tarjetas de conclusión
# ---------------------------------------------------------------------------

def render_conclusion_card(conclusion) -> None:
    """
    Renderiza una conclusión del motor de análisis como tarjeta visual.
    Usa HTML/CSS inyectado para control total del diseño.
    """
    color = conclusion.color
    icono = conclusion.icono
    sev   = conclusion.severidad

    # Borde lateral con color de severidad
    border_css = f"border-left: 4px solid {color}"

    with st.container():
        st.markdown(
            f"""
            <div style="
                background: rgba(19,27,42,0.9);
                {border_css};
                border-radius: 8px;
                padding: 14px 18px;
                margin-bottom: 12px;
                backdrop-filter: blur(4px);
            ">
              <div style="display:flex;align-items:flex-start;gap:10px">
                <span style="font-size:20px;line-height:1.2">{icono}</span>
                <div style="flex:1">
                  <div style="
                    font-size:13px;
                    font-weight:700;
                    color:{color};
                    letter-spacing:0.04em;
                    margin-bottom:4px
                  ">{conclusion.titulo.upper()}</div>
                  <div style="
                    font-size:13px;
                    color:#C8D0DC;
                    line-height:1.55
                  ">{conclusion.mensaje}</div>
                  {"" if not conclusion.recomendacion else f'''
                  <div style="
                    margin-top:10px;
                    padding:8px 12px;
                    background:rgba(247,148,29,0.08);
                    border-radius:5px;
                    font-size:12px;
                    color:#F7941D;
                  ">💡 <b>Acción sugerida:</b> {conclusion.recomendacion}</div>
                  '''}
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# KPI chips en fila
# ---------------------------------------------------------------------------

def render_kpi_row(summary: dict) -> None:
    """Renderiza una fila de métricas clave del sistema."""
    if not summary:
        return

    cols = st.columns(4)
    kpis = [
        ("Estaciones",      summary.get("total_estaciones", 0),   "",    "#8892A4"),
        ("Flujo promedio",  f"{summary.get('flujo_promedio', 0):.0f}%", "", "#00C896"),
        ("En alerta",       summary.get("en_alerta", 0),          "estaciones", "#FF9800"),
        ("Línea crítica",   f"Línea {summary.get('linea_mas_cargada', 'N/A')}", "", "#F7941D"),
    ]

    for col, (label, value, unit, color) in zip(cols, kpis):
        with col:
            st.markdown(
                f"""
                <div style="
                    background:rgba(13,17,23,0.8);
                    border:1px solid rgba(255,255,255,0.07);
                    border-radius:8px;
                    padding:12px 14px;
                    text-align:center;
                ">
                  <div style="font-size:22px;font-weight:800;color:{color}">{value}</div>
                  <div style="font-size:11px;color:#8892A4;margin-top:2px;
                              letter-spacing:0.06em">{label.upper()}</div>
                  {"" if not unit else f'<div style="font-size:10px;color:#555">{unit}</div>'}
                </div>
                """,
                unsafe_allow_html=True,
            )


# ---------------------------------------------------------------------------
# Gráfico de parque automotor
# ---------------------------------------------------------------------------

def render_parque_chart(df: pd.DataFrame) -> None:
    """
    Mini gráfico de línea con la evolución del parque automotor 2012–2025.
    """
    if df.empty:
        st.caption("Sin datos de parque automotor.")
        return

    df = df.copy()
    df.columns = df.columns.str.strip()
    df = df.sort_values("AÑO")

    fig = go.Figure()

    # Área bajo la curva
    fig.add_trace(go.Scatter(
        x=df["AÑO"],
        y=df["Total"],
        mode="lines+markers",
        line=dict(color="#F7941D", width=2.5),
        marker=dict(size=6, color="#F7941D", line=dict(color="#0A0E1A", width=1.5)),
        fill="tozeroy",
        fillcolor="rgba(247,148,29,0.08)",
        name="Parque automotor",
        hovertemplate="<b>%{x}</b><br>%{y:,.0f} unidades<extra></extra>",
    ))

    # Marca de caída COVID
    fig.add_vline(x=2020, line_dash="dash", line_color="rgba(255,71,87,0.4)", line_width=1)
    fig.add_annotation(
        x=2020, y=df["Total"].max() * 0.95,
        text="COVID-19",
        showarrow=False,
        font=dict(size=9, color="rgba(255,71,87,0.7)"),
        bgcolor="rgba(0,0,0,0)",
    )

    fig.update_layout(
        height=160,
        margin=dict(l=0, r=0, t=8, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            showgrid=False,
            color="#8892A4",
            tickfont=dict(size=10),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(255,255,255,0.05)",
            color="#8892A4",
            tickfont=dict(size=10),
            tickformat=",",
        ),
        showlegend=False,
        hovermode="x unified",
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ---------------------------------------------------------------------------
# Estado vacío (empty state)
# ---------------------------------------------------------------------------

def render_empty_state(mensaje: str = "Ejecuta el análisis para ver resultados.") -> None:
    """Muestra un estado vacío elegante cuando no hay resultados."""
    st.markdown(
        f"""
        <div style="
            text-align:center;
            padding:40px 20px;
            color:#8892A4;
        ">
          <div style="font-size:36px;margin-bottom:12px">🗺️</div>
          <div style="font-size:14px;line-height:1.6">{mensaje}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Separador con etiqueta
# ---------------------------------------------------------------------------

def render_section_header(title: str, subtitle: str = "") -> None:
    """Encabezado de sección con línea divisoria."""
    st.markdown(
        f"""
        <div style="margin:18px 0 10px 0">
          <div style="
            font-size:11px;
            font-weight:700;
            letter-spacing:0.12em;
            color:#F7941D;
            text-transform:uppercase;
          ">{title}</div>
          {"" if not subtitle else f'<div style="font-size:11px;color:#8892A4;margin-top:2px">{subtitle}</div>'}
          <div style="height:1px;background:rgba(255,255,255,0.07);margin-top:6px"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Badge de línea
# ---------------------------------------------------------------------------

def linea_badge(linea: str, color: str) -> str:
    """Retorna HTML de un badge de línea para usar en tablas/cards."""
    return (
        f'<span style="background:{color};color:#fff;'
        f'padding:2px 7px;border-radius:10px;font-size:11px;'
        f'font-weight:700">L{linea}</span>'
    )
