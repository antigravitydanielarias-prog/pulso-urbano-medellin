# =============================================================================
# modules/map_renderer.py — Renderizado del mapa con Folium + OpenStreetMap
# =============================================================================

import folium
from folium.plugins import MarkerCluster, MiniMap
import pandas as pd

from config import (
    MEDELLIN_CENTER, MEDELLIN_ZOOM,
    LINE_COLORS, SYSTEM_COLORS,
    MAP_TILE_DARK, MAP_TILE_LIGHT,
)


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _flujo_to_radius(flujo: float) -> int:
    """Radio del marcador proporcional al flujo (6–14px)."""
    return int(6 + flujo * 8)


def _flujo_to_opacity(flujo: float) -> float:
    """Opacidad del marcador proporcional al flujo."""
    return round(0.5 + flujo * 0.5, 2)


def _congestion_fill(congestion: str) -> str:
    """Color de relleno según nivel de congestión."""
    mapa = {
        "crítica": "#FF1744",
        "alta":    "#FF6D00",
        "media":   "#FFD600",
        "baja":    "#00E676",
    }
    return mapa.get(congestion, "#78909C")


def _popup_estacion(row: pd.Series) -> str:
    """HTML del popup de una estación."""
    flujo_pct = round(row.get("flujo_activo", 0) * 100, 1)
    congestion = row.get("congestion", "N/A")
    motivo = row.get("motivo_dominante", "N/A")
    color_cong = _congestion_fill(congestion)

    return f"""
    <div style="font-family:sans-serif;min-width:220px;padding:4px">
      <b style="font-size:13px">{row['label']}</b><br>
      <span style="color:#888;font-size:11px">{row['sistema_label']} · Línea {row['linea']}</span>
      <hr style="margin:6px 0;border-color:#333">
      <table style="font-size:12px;width:100%">
        <tr><td>🚦 Flujo</td>
            <td style="text-align:right;font-weight:bold">{flujo_pct}%</td></tr>
        <tr><td>⚡ Congestión</td>
            <td style="text-align:right">
              <span style="color:{color_cong};font-weight:bold">{congestion.upper()}</span>
            </td></tr>
        <tr><td>🎯 Motivo</td>
            <td style="text-align:right">{motivo}</td></tr>
      </table>
    </div>
    """


# ---------------------------------------------------------------------------
# Constructor principal del mapa
# ---------------------------------------------------------------------------

def build_map(
    df_estaciones:   pd.DataFrame,
    df_paradas:      pd.DataFrame,
    df_rutas_bus:    pd.DataFrame,
    active_layers:   dict,
    dark_mode:       bool = True,
) -> folium.Map:
    """
    Construye el mapa de Medellín con todas las capas configuradas.

    Args:
        df_estaciones:  DataFrame filtrado de estaciones (con lat/lon, flujo_activo, etc.).
        df_paradas:     DataFrame de paradas alimentadoras.
        df_rutas_bus:   DataFrame de rutas de bus.
        active_layers:  Dict {nombre_capa: bool} con capas activas.
        dark_mode:      Usar tiles oscuros (CartoDB Dark Matter).

    Returns:
        Objeto folium.Map listo para renderizar.
    """
    tile = MAP_TILE_DARK if dark_mode else MAP_TILE_LIGHT

    m = folium.Map(
        location=MEDELLIN_CENTER,
        zoom_start=MEDELLIN_ZOOM,
        tiles=tile,
        attr="© OpenStreetMap contributors | © CARTO",
        prefer_canvas=True,
    )

    # Mini mapa de referencia
    MiniMap(toggle_display=True, tile_layer=tile).add_to(m)

    # ── Capa: Rutas de bus ─────────────────────────────────────────────────
    if active_layers.get("rutas_bus") and not df_rutas_bus.empty:
        _add_bus_routes(m, df_rutas_bus)

    # ── Capa: Paradas alimentadoras ─────────────────────────────────────────
    if active_layers.get("paradas") and not df_paradas.empty:
        _add_paradas(m, df_paradas)

    # ── Capa: Estaciones del sistema Metro ──────────────────────────────────
    if active_layers.get("estaciones") and not df_estaciones.empty:
        _add_estaciones(m, df_estaciones)

    # ── Capa: Leyenda ──────────────────────────────────────────────────────
    _add_legend(m, dark_mode)

    return m


# ---------------------------------------------------------------------------
# Sub-renderers por capa
# ---------------------------------------------------------------------------

def _add_estaciones(m: folium.Map, df: pd.DataFrame) -> None:
    """Agrega marcadores de estaciones con color por línea y tamaño por flujo."""
    # Agrupar por sistema para separar en FeatureGroups
    sistemas = df["sistema_label"].unique()

    for sistema in sistemas:
        sub = df[df["sistema_label"] == sistema]
        group = folium.FeatureGroup(name=f"🚇 {sistema}", show=True)

        for _, row in sub.iterrows():
            color = LINE_COLORS.get(str(row.get("linea", "")), "#78909C")
            radio = _flujo_to_radius(row.get("flujo_activo", 0.3))
            fill  = _congestion_fill(row.get("congestion", "baja"))

            folium.CircleMarker(
                location=[row["lat"], row["lon"]],
                radius=radio,
                color=color,
                weight=2,
                fill=True,
                fill_color=fill,
                fill_opacity=_flujo_to_opacity(row.get("flujo_activo", 0.3)),
                popup=folium.Popup(_popup_estacion(row), max_width=280),
                tooltip=folium.Tooltip(
                    f"{row['label']} · {row.get('flujo_activo', 0)*100:.0f}%",
                    sticky=True,
                ),
            ).add_to(group)

        group.add_to(m)


def _add_paradas(m: folium.Map, df: pd.DataFrame) -> None:
    """Agrega paradas de alimentadoras como puntos pequeños agrupados."""
    group = folium.FeatureGroup(name="🚌 Paradas alimentadoras", show=True)

    # Usar cluster para rendimiento con muchos puntos
    cluster = MarkerCluster(
        name="paradas_cluster",
        options={
            "maxClusterRadius": 40,
            "disableClusteringAtZoom": 15,
        },
    )

    for _, row in df.iterrows():
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=3,
            color="#78909C",
            weight=1,
            fill=True,
            fill_color="#90A4AE",
            fill_opacity=0.7,
            tooltip=folium.Tooltip(
                row.get("label", "Parada"),
                sticky=False,
            ),
        ).add_to(cluster)

    cluster.add_to(group)
    group.add_to(m)


def _add_bus_routes(m: folium.Map, df: pd.DataFrame) -> None:
    """Dibuja rutas de bus como polilíneas con paradas."""
    group = folium.FeatureGroup(name="🚍 Rutas de bus", show=False)

    route_colors = {
        130: "#FF7043",
        132: "#26C6DA",
        133: "#AB47BC",
        190: "#66BB6A",
        191: "#FFA726",
        192: "#29B6F6",
        193: "#EC407A",
        287: "#FFCA28",
        302: "#8D6E63",
    }

    for route_id, sub in df.groupby("route_id"):
        sub = sub.sort_values("order")
        coords = list(zip(sub["lat"], sub["lon"]))
        if len(coords) < 2:
            continue

        color = route_colors.get(int(route_id), "#78909C")

        folium.PolyLine(
            locations=coords,
            color=color,
            weight=2.5,
            opacity=0.7,
            tooltip=f"Ruta {route_id}",
            dash_array="6 4",
        ).add_to(group)

        # Primera y última parada como marcador
        for idx, (_, stop) in enumerate([(0, sub.iloc[0]), (-1, sub.iloc[-1])]):
            folium.CircleMarker(
                location=[stop["lat"], stop["lon"]],
                radius=4,
                color=color,
                weight=2,
                fill=True,
                fill_color=color,
                fill_opacity=0.9,
                tooltip=stop.get("stop_name", f"Ruta {route_id}"),
            ).add_to(group)

    group.add_to(m)


def _add_legend(m: folium.Map, dark_mode: bool) -> None:
    """Agrega leyenda de congestión al mapa."""
    bg = "rgba(15,20,35,0.88)" if dark_mode else "rgba(255,255,255,0.88)"
    text_color = "#E8EDF5" if dark_mode else "#1A1A2E"

    legend_html = f"""
    <div style="
        position: fixed;
        bottom: 30px; right: 15px;
        background: {bg};
        backdrop-filter: blur(8px);
        border: 1px solid rgba(247,148,29,0.3);
        border-radius: 10px;
        padding: 12px 16px;
        z-index: 1000;
        font-family: 'SF Mono', 'Fira Mono', monospace;
        font-size: 11px;
        color: {text_color};
        min-width: 150px;
    ">
      <div style="font-weight:700;font-size:12px;margin-bottom:8px;
                  color:#F7941D;letter-spacing:0.05em">CONGESTIÓN</div>
      <div style="display:flex;align-items:center;gap:8px;margin:4px 0">
        <span style="width:10px;height:10px;border-radius:50%;
                     background:#00E676;display:inline-block"></span> Baja
      </div>
      <div style="display:flex;align-items:center;gap:8px;margin:4px 0">
        <span style="width:10px;height:10px;border-radius:50%;
                     background:#FFD600;display:inline-block"></span> Media
      </div>
      <div style="display:flex;align-items:center;gap:8px;margin:4px 0">
        <span style="width:10px;height:10px;border-radius:50%;
                     background:#FF6D00;display:inline-block"></span> Alta
      </div>
      <div style="display:flex;align-items:center;gap:8px;margin:4px 0">
        <span style="width:10px;height:10px;border-radius:50%;
                     background:#FF1744;display:inline-block"></span> Crítica
      </div>
      <hr style="border-color:rgba(255,255,255,0.15);margin:8px 0">
      <div style="color:#8892A4;font-size:10px">Tamaño = flujo activo</div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
