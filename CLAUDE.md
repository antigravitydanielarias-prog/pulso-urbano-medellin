# CLAUDE.md — Pulso Urbano · Medellín

Contexto para Claude Code. Lee esto antes de tocar cualquier archivo.

## ¿Qué es este proyecto?

Dashboard de movilidad urbana para Medellín construido en **Streamlit**.
Visualiza el sistema integrado de transporte (Metro, Metrocable, Tranvía, Metro Plus)
con datos reales de infraestructura y flujos de demanda simulados.

Para correrlo:
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Arquitectura

```
app.py                  → Entrada principal. Page config PRIMERO. NO mover st.set_page_config().
config.py               → Todas las constantes: rutas, colores, umbrales. Editar aquí, no hardcodear.
modules/
  data_loader.py        → Carga CSVs + conversión EPSG:3857 → WGS84 + datos sintéticos.
  data_processor.py     → Filtrado y agregación. filter_estaciones() es la función central.
  rules_engine.py       → Motor de análisis por reglas. Retorna lista de Conclusion.
  map_renderer.py       → Construye el mapa Folium con capas configurables.
  ui_components.py      → Componentes HTML reutilizables (cards, KPIs, charts).
assets/style.css        → CSS para override del tema oscuro de Streamlit.
data/                   → CSVs reales del Metro de Medellín (NO modificar).
```

## Datos

Todos los CSVs tienen coordenadas en **EPSG:3857 (Web Mercator)**, excepto `rutas_medellin_dataset.csv` que ya está en WGS84.

Conversión validada en `data_loader._wm_to_latlon(x, y)`:
```python
lon = x * 180 / 20037508.34
lat = degrees(atan(sinh(y * pi / 20037508.34)))
```

Estaciones de referencia verificadas:
- Acevedo: lat=6.2999, lon=-75.5586
- San Antonio: lat=6.2472, lon=-75.5697

## Diseño UI

Tema oscuro, acento **naranja Metro #F7941D**.

| Variable    | Valor         |
|-------------|---------------|
| bg-main     | `#0A0E1A`     |
| bg-sidebar  | `#0D1117`     |
| primary     | `#F7941D`     |
| success     | `#00C896`     |
| danger      | `#FF4B5C`     |
| muted       | `#8892A4`     |

Fonts: Syne (headers) + Inter (body) + JetBrains Mono (datos).

## Flujo de uso

1. Usuario activa/desactiva capas del mapa
2. Configura filtros: sistema, línea, franja horaria, motivos, estratos
3. Presiona **"Ejecutar análisis"** (NO auto-refresh — fue decisión de diseño)
4. `rules_engine.run_analysis(ctx)` evalúa el contexto
5. Se muestran tarjetas con conclusiones + tabla de estaciones críticas

## Convenciones

- Toda la carga de datos va en `data_loader.py` con `@st.cache_data`
- Toda la lógica de negocio va en `data_processor.py` o `rules_engine.py`
- El mapa **nunca** se reconstruye en tiempo real → solo al ejecutar análisis
- Los datos sintéticos (flujos, motivos) se generan con seed fijo para reproducibilidad

## Extensiones posibles

- Conectar a API real del Metro (feed GTFS cuando esté disponible)
- Agregar capa de obras/eventos desde GeoJSON municipal
- Exportar informe PDF con conclusiones del análisis
- Modo comparación: dos franjas horarias lado a lado
- Panel de administrador con edición de umbrales de reglas

## Posibles problemas

| Síntoma | Causa probable | Fix |
|---------|---------------|-----|
| Mapa no carga | streamlit-folium version mismatch | `pip install streamlit-folium==0.21.0` |
| `FileNotFoundError` en CSVs | Ruta relativa incorrecta | Correr desde `medellin_movilidad/` |
| Estaciones fuera de Medellín | Coordenada X/Y inválida en CSV | Revisar filtro bbox en `load_estaciones()` |
| Tema claro persiste | CSS no cargado | Verificar que existe `assets/style.css` |
