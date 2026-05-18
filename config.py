# =============================================================================
# config.py — Configuración central del dashboard
# =============================================================================

import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

DATA_FILES = {
    "estaciones":    "Estaciones_Sistema_Metro.csv",
    "lineas":        "Lineas_Sistema_Metro.csv",
    "alimentadoras": "Rutas_Alimentadoras.csv",
    "paradas":       "alimentadora_parada.csv",
    "parque":        "Parque_automotor_historico.csv",
    "rutas_bus":     "rutas_medellin_dataset.csv",
}

MEDELLIN_CENTER = [6.2442, -75.5812]
MEDELLIN_ZOOM   = 12

MAP_TILE_DARK  = "CartoDB dark_matter"
MAP_TILE_LIGHT = "CartoDB positron"

LINE_COLORS = {
    "A": "#F7941D",
    "B": "#2196F3",
    "K": "#9C27B0",
    "J": "#00BCD4",
    "L": "#4CAF50",
    "M": "#E91E63",
    "H": "#FF5722",
    "T": "#FFEB3B",
    "P": "#795548",
    "1": "#00E676",
    "2": "#40C4FF",
    "O": "#FF6F00",
}

SYSTEM_COLORS = {
    "Metro":      "#F7941D",
    "Metrocable": "#9C27B0",
    "Tranvía":    "#FFEB3B",
    "Metro Plus": "#00E676",
}

THRESHOLDS = {
    "flujo_alto":            0.75,
    "flujo_critico":         0.90,
    "hora_pico":             ["manana", "tarde"],
    "motivo_laboral":        ["Trabajo", "Estudio"],
    "estratos_vulnerables":  [1, 2, 3],
    "delta_parque_caida":    -0.10,
}

MOTIVOS_VIAJE = ["Trabajo", "Estudio", "Salud", "Recreación", "Compras", "Otro"]

FRANJAS_HORARIAS = {
    "manana":    "🌅 Mañana (5 – 9 am)",
    "mediodia":  "☀️ Mediodía (9 am – 1 pm)",
    "tarde":     "🌆 Tarde (1 – 8 pm)",
    "noche":     "🌙 Noche (8 pm – 12 am)",
    "madrugada": "🌑 Madrugada (12 – 5 am)",
}

ESTRATOS = list(range(1, 7))

SEVERITY_ICONS = {
    "normal":    "✅",
    "tendencia": "📈",
    "alerta":    "⚠️",
    "atipico":   "🔴",
    "recomend":  "💡",
}

SEVERITY_COLORS = {
    "normal":    "#00C896",
    "tendencia": "#40C4FF",
    "alerta":    "#FF9800",
    "atipico":   "#FF4B5C",
    "recomend":  "#F7941D",
}
