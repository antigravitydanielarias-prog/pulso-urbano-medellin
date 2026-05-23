# =============================================================================
# modules/ui_components.py — Componentes reutilizables de interfaz
# =============================================================================

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from config import (
    SEVERITY_COLORS, SEVERITY_ICONS,
    AMVA_HORARIO, AMVA_FRANJA_HORAS,
    AMVA_MODOS, AMVA_MODOS_COLORES,
    AMVA_KPIS, AMVA_MACROZONAS_TOP,
)


# ---------------------------------------------------------------------------
# Tarjetas de conclusión
# ---------------------------------------------------------------------------

def render_conclusion_card(conclusion) -> None:
    """
    Renderiza una conclusión del motor de análisis como tarjeta visual.
    Construye el HTML completo antes de llamar a st.markdown para evitar
    problemas con f-strings anidados y el parser de Streamlit.
    """
    color = conclusion.color
    icono = conclusion.icono

    rec_html = ""
    if conclusion.recomendacion:
        rec_html = (
            '<div style="margin-top:10px;padding:8px 12px;'
            'background:rgba(247,148,29,0.08);border-radius:5px;'
            'font-size:12px;color:#F7941D;">'
            '💡 <b>Acción sugerida:</b> ' + conclusion.recomendacion +
            '</div>'
        )

    html = (
        '<div style="background:rgba(19,27,42,0.9);'
        'border-left:4px solid ' + color + ';'
        'border-radius:8px;padding:14px 18px;margin-bottom:12px;">'
        '<div style="display:flex;align-items:flex-start;gap:10px">'
        '<span style="font-size:20px;line-height:1.2">' + icono + '</span>'
        '<div style="flex:1">'
        '<div style="font-size:13px;font-weight:700;color:' + color + ';'
        'letter-spacing:0.04em;margin-bottom:4px">'
        + conclusion.titulo.upper() +
        '</div>'
        '<div style="font-size:13px;color:#C8D0DC;line-height:1.55">'
        + conclusion.mensaje +
        '</div>'
        + rec_html +
        '</div></div></div>'
    )

    st.markdown(html, unsafe_allow_html=True)


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
            unit_html = f'<div style="font-size:10px;color:#555">{unit}</div>' if unit else ""
            st.markdown(
                '<div style="background:rgba(13,17,23,0.8);'
                'border:1px solid rgba(255,255,255,0.07);'
                'border-radius:8px;padding:12px 14px;text-align:center;">'
                '<div style="font-size:22px;font-weight:800;color:' + color + '">' + str(value) + '</div>'
                '<div style="font-size:11px;color:#8892A4;margin-top:2px;'
                'letter-spacing:0.06em">' + label.upper() + '</div>'
                + unit_html +
                '</div>',
                unsafe_allow_html=True,
            )


# ---------------------------------------------------------------------------
# KPIs AMVA (siempre visibles, no requieren análisis)
# ---------------------------------------------------------------------------

def render_amva_kpis() -> None:
    """Fila de KPIs reales del Valle de Aburrá — Encuesta OD 2025."""
    viajes_M = AMVA_KPIS["total_viajes"] / 1_000_000
    pct_pub = round(AMVA_KPIS["viajes_publicos"] / AMVA_KPIS["total_viajes"] * 100, 1)
    pct_nm  = round(AMVA_KPIS["viajes_no_motorizados"] / AMVA_KPIS["total_viajes"] * 100, 1)

    items = [
        (f"{viajes_M:.2f}M",              "Viajes/día hábil AMVA",      "#F7941D"),
        (f"{pct_pub}%",                   "En transporte público",       "#00C896"),
        (f"{AMVA_KPIS['tiempo_promedio_min']:.0f} min", "Tiempo promedio viaje", "#40C4FF"),
        (f"{pct_nm}%",                    "Viajes no motorizados",       "#9C27B0"),
        (f"{AMVA_KPIS['motos_por_1000']}", "Motos por 1.000 hab.",       "#FF9800"),
    ]

    cols = st.columns(len(items))
    for col, (valor, label, color) in zip(cols, items):
        with col:
            st.markdown(
                '<div style="background:rgba(247,148,29,0.05);'
                'border:1px solid rgba(247,148,29,0.15);'
                'border-radius:8px;padding:10px 12px;text-align:center;">'
                '<div style="font-size:18px;font-weight:800;color:' + color + '">' + str(valor) + '</div>'
                '<div style="font-size:10px;color:#8892A4;margin-top:2px;letter-spacing:0.05em">'
                + label.upper() + '</div>'
                '</div>',
                unsafe_allow_html=True,
            )


# ---------------------------------------------------------------------------
# Línea de tiempo de saturación del sistema (datos reales AMVA 2025)
# ---------------------------------------------------------------------------

def render_timeline_saturacion(franja_sel: str = "tarde") -> None:
    """
    Línea de tiempo que muestra el % de carga del transporte público
    sobre su máximo horario (hora 6am = 100%).

    Destaca zonas de alerta (>75%) y crítica (>90%), y resalta la
    franja horaria seleccionada en los filtros.

    Responde a: ¿cuántas horas al día el sistema está realmente colapsado?
    """
    horas   = AMVA_HORARIO["hora"]
    publico = AMVA_HORARIO["publico"]
    max_pub = max(publico)
    carga   = [round(v / max_pub * 100, 1) for v in publico]

    h_start, h_end = AMVA_FRANJA_HORAS.get(franja_sel, (13, 20))

    horas_sobre_75 = sum(1 for c in carga if c >= 75)
    horas_sobre_90 = sum(1 for c in carga if c >= 90)

    fig = go.Figure()

    # Zonas de alerta (fondos)
    fig.add_hrect(y0=90, y1=107,
                  fillcolor="rgba(255,75,92,0.07)",  line_width=0, layer="below")
    fig.add_hrect(y0=75, y1=90,
                  fillcolor="rgba(255,152,0,0.07)", line_width=0, layer="below")

    # Líneas de umbral
    fig.add_hline(y=90, line_dash="dash",
                  line_color="rgba(255,75,92,0.55)", line_width=1.2)
    fig.add_hline(y=75, line_dash="dash",
                  line_color="rgba(255,152,0,0.55)", line_width=1.2)

    fig.add_annotation(x=22.8, y=92, text="Crítico 90%", showarrow=False,
                       font=dict(size=9, color="rgba(255,75,92,0.9)"), xanchor="right")
    fig.add_annotation(x=22.8, y=77, text="Alerta 75%", showarrow=False,
                       font=dict(size=9, color="rgba(255,152,0,0.9)"), xanchor="right")

    # Área bajo la curva
    fig.add_trace(go.Scatter(
        x=horas, y=carga,
        fill="tozeroy",
        fillcolor="rgba(64,196,255,0.10)",
        line=dict(color="#40C4FF", width=2.2, shape="spline"),
        mode="lines",
        name="Carga sistema público",
        hovertemplate="<b>%{x}:00 h</b> — carga: <b>%{y:.0f}%</b><extra></extra>",
    ))

    # Marcadores: puntos sobre umbral
    criticos_x = [h for h, c in zip(horas, carga) if c >= 75]
    criticos_y = [c for c in carga if c >= 75]
    criticos_c = ["#FF4B5C" if c >= 90 else "#FF9800" for c in criticos_y]
    fig.add_trace(go.Scatter(
        x=criticos_x, y=criticos_y,
        mode="markers",
        marker=dict(size=8, color=criticos_c,
                    line=dict(color="#0A0E1A", width=1.5)),
        showlegend=False,
        hovertemplate="%{x}:00 h — %{y:.0f}%<extra></extra>",
    ))

    # Franja seleccionada
    fig.add_vrect(x0=h_start, x1=h_end,
                  fillcolor="rgba(247,148,29,0.09)", line_width=0)
    fig.add_vline(x=h_start, line_dash="dot",
                  line_color="rgba(247,148,29,0.7)", line_width=1.5)
    fig.add_vline(x=h_end,   line_dash="dot",
                  line_color="rgba(247,148,29,0.7)", line_width=1.5)

    # Anotación de resumen
    fig.add_annotation(
        x=0.01, y=0.96, xref="paper", yref="paper",
        text=f"⚠ <b>{horas_sobre_75}h</b>/día sobre 75%  ·  <b>{horas_sobre_90}h</b>/día sobre 90%",
        showarrow=False,
        font=dict(size=10, color="#FF9800"),
        bgcolor="rgba(13,17,23,0.75)",
        borderpad=5,
        align="left",
    )

    tick_vals  = list(range(0, 24, 3))
    tick_texts = ["12am", "3am", "6am", "9am", "12pm", "3pm", "6pm", "9pm"]

    fig.update_layout(
        height=215,
        margin=dict(l=0, r=0, t=4, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            showgrid=False, color="#8892A4", tickfont=dict(size=9),
            tickmode="array", tickvals=tick_vals, ticktext=tick_texts,
            range=[-0.5, 23.5],
        ),
        yaxis=dict(
            showgrid=True, gridcolor="rgba(255,255,255,0.05)",
            color="#8892A4", tickfont=dict(size=9),
            ticksuffix="%", range=[0, 108],
        ),
        showlegend=False,
        hovermode="x unified",
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ---------------------------------------------------------------------------
# Gráfico distribución horaria apilada (datos reales AMVA 2025)
# ---------------------------------------------------------------------------

def render_distribucion_horaria_chart(franja_sel: str = "tarde") -> None:
    """
    Área apilada con los viajes por hora del día desglosados por modo.
    Destaca visualmente la franja horaria actualmente seleccionada.
    Fuente: Encuesta OD AMVA 2025.
    """
    horas = AMVA_HORARIO["hora"]
    h_start, h_end = AMVA_FRANJA_HORAS.get(franja_sel, (13, 20))

    trazas = [
        ("no_motorizado", "No motorizado", "#00C896"),
        ("informal",      "Informal/Taxi", "#8892A4"),
        ("privado",       "Privado",       "#40C4FF"),
        ("publico",       "Público/Masivo","#F7941D"),
    ]

    fig = go.Figure()

    for key, name, color in trazas:
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        fig.add_trace(go.Scatter(
            x=horas,
            y=AMVA_HORARIO[key],
            name=name,
            stackgroup="one",
            line=dict(color=color, width=0.8),
            fillcolor=f"rgba({r},{g},{b},0.75)",
            mode="lines",
            hovertemplate=f"<b>{name}</b>: %{{y:,.0f}} viajes<extra></extra>",
        ))

    # Banda de franja seleccionada
    fig.add_vrect(
        x0=h_start, x1=h_end,
        fillcolor="rgba(247,148,29,0.10)",
        line_width=0, layer="above",
    )
    fig.add_vline(x=h_start, line_dash="dot",
                  line_color="rgba(247,148,29,0.6)", line_width=1.2)
    fig.add_vline(x=h_end,   line_dash="dot",
                  line_color="rgba(247,148,29,0.6)", line_width=1.2)

    tick_vals  = list(range(0, 24, 3))
    tick_texts = ["12am","3am","6am","9am","12pm","3pm","6pm","9pm"]

    fig.update_layout(
        height=210,
        margin=dict(l=0, r=0, t=4, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            showgrid=False, color="#8892A4", tickfont=dict(size=9),
            tickmode="array", tickvals=tick_vals, ticktext=tick_texts,
        ),
        yaxis=dict(
            showgrid=True, gridcolor="rgba(255,255,255,0.05)",
            color="#8892A4", tickfont=dict(size=9), tickformat=",",
        ),
        legend=dict(
            orientation="h", x=0, y=1.08,
            font=dict(size=9, color="#8892A4"),
            bgcolor="rgba(0,0,0,0)",
        ),
        hovermode="x unified",
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ---------------------------------------------------------------------------
# Gráfico modal share (datos reales AMVA 2025)
# ---------------------------------------------------------------------------

def render_modal_share_chart() -> None:
    """
    Barras horizontales con el % de viajes por modo de transporte.
    Fuente: Encuesta OD AMVA 2025.
    """
    modos   = list(AMVA_MODOS.keys())
    valores = list(AMVA_MODOS.values())
    colores = [AMVA_MODOS_COLORES.get(m, "#8892A4") for m in modos]

    fig = go.Figure(go.Bar(
        y=modos,
        x=valores,
        orientation="h",
        marker_color=colores,
        text=[f"{v}%" for v in valores],
        textposition="outside",
        textfont=dict(size=10, color="#8892A4"),
        hovertemplate="%{y}: %{x:.2f}%<extra></extra>",
    ))

    fig.update_layout(
        height=230,
        margin=dict(l=0, r=45, t=4, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            showgrid=True, gridcolor="rgba(255,255,255,0.05)",
            color="#8892A4", tickfont=dict(size=9),
            ticksuffix="%", range=[0, 42],
        ),
        yaxis=dict(
            color="#8892A4", tickfont=dict(size=10),
            categoryorder="total ascending",
        ),
        showlegend=False,
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


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
        '<div style="text-align:center;padding:40px 20px;color:#8892A4;">'
        '<div style="font-size:36px;margin-bottom:12px">🗺️</div>'
        '<div style="font-size:14px;line-height:1.6">' + mensaje + '</div>'
        '</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Separador con etiqueta
# ---------------------------------------------------------------------------

def render_section_header(title: str, subtitle: str = "") -> None:
    """Encabezado de sección con línea divisoria."""
    subtitle_html = (
        f'<div style="font-size:11px;color:#8892A4;margin-top:2px">{subtitle}</div>'
        if subtitle else ""
    )
    st.markdown(
        '<div style="margin:18px 0 10px 0">'
        '<div style="font-size:11px;font-weight:700;letter-spacing:0.12em;'
        'color:#F7941D;text-transform:uppercase;">' + title + '</div>'
        + subtitle_html +
        '<div style="height:1px;background:rgba(255,255,255,0.07);margin-top:6px"></div>'
        '</div>',
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
