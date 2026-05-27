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
    "rutas_bus":     "rutas_medellin_dataset.json",
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

MOTIVOS_VIAJE = ["Trabajo", "Estudio", "Regreso al hogar", "Salud", "Recreación", "Ocio", "Compras", "Otro"]

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

# =============================================================================
# Datos reales AMVA — Encuesta Origen-Destino 2025
# =============================================================================

AMVA_MUNICIPIOS = [
    "Medellín", "Bello", "Itagüí", "Envigado", "Sabaneta",
    "La Estrella", "Caldas", "Copacabana", "Girardota", "Barbosa",
]

AMVA_KPIS = {
    "total_viajes":          6_490_299,
    "pct_no_viajan":         31.59,
    "tiempo_promedio_min":   39.28,
    "viajes_privados":       1_879_454,
    "viajes_no_motorizados": 2_179_415,
    "viajes_publicos":       2_196_961,
    "viajes_per_capita":     1.6,
    "motos_por_1000":        120.5,
    "autos_por_1000":        67.13,
}

# Distribución horaria — viajes por hora de inicio (todos los modos) — AMVA 2025
AMVA_HORARIO = {
    "hora":          list(range(24)),
    "informal":      [578,1037,1761,976,1995,6721,16546,19532,14244,17450,
                      20025,14478,12339,11715,14096,13933,15674,17909,10814,
                      8178,3953,4581,4130,1803],
    "publico":       [2927,1347,3113,5859,64220,148582,239034,175367,118392,98624,
                      113663,100227,119082,105322,131900,116221,157919,212837,130453,
                      60774,41998,27155,19844,2100],
    "privado":       [1775,3685,6873,7442,26723,114380,230844,200941,100780,65839,
                      72142,69099,123540,85686,98803,92947,130123,181714,97205,
                      54753,50848,27630,22793,12888],
    "no_motorizado": [1778,1530,1883,2343,9845,74270,230544,123771,113922,110015,
                      135481,151333,341052,110943,102425,95026,107067,225683,111277,
                      58162,31118,17632,16028,6287],
}

# Rango de horas por franja para highlighting en gráfica
AMVA_FRANJA_HORAS = {
    "madrugada": (0,  5),
    "manana":    (5,  9),
    "mediodia":  (9,  13),
    "tarde":     (13, 20),
    "noche":     (20, 24),
}

# Modal share real — % de viajes por modo principal (OD 2025)
AMVA_MODOS = {
    "A pie":        32.68,
    "Masivo":       16.44,
    "TPC":          14.94,
    "Motocicleta":  14.57,
    "Automóvil":    11.70,
    "Otros":         6.33,
    "Taxi":          2.47,
    "Bicicleta":     0.86,
}

AMVA_MODOS_COLORES = {
    "A pie":       "#00C896",
    "Masivo":      "#F7941D",
    "TPC":         "#FF9800",
    "Motocicleta": "#8892A4",
    "Automóvil":   "#FF4B5C",
    "Taxi":        "#607D8B",
    "Bicicleta":   "#00BCD4",
    "Otros":       "#546E7A",
}

# % de viajes por estrato socioeconómico
AMVA_ESTRATOS_PCT = {1: 13.38, 2: 39.89, 3: 29.44, 4: 5.87, 5: 7.02, 6: 4.40}

# =============================================================================
# Datos vehiculares — Encuesta Origen-Destino AMVA 2025
# =============================================================================

AMVA_VEHICULOS = {
    # Tipología del parque vehicular privado (% sobre total vehículos)
    "tipologia": {
        "Motocicleta": 59.94,
        "Automóvil":   31.28,
        "Bicicleta":    5.20,
        "Camioneta":    2.90,
        "Otro":         0.69,
    },
    # Tenencia de vehículos por hogar (% hogares)
    "por_hogar": {
        "Sin vehículo":  60.11,
        "Un vehículo":   31.97,
        "Dos o más":      7.92,
    },
    # Vehículos por estrato socioeconómico (% del parque total)
    "por_estrato": {1: 8.87, 2: 37.33, 3: 32.37, 4: 6.85, 5: 9.33, 6: 5.25},
    # Antigüedad del parque vehicular (% sobre total)
    "modelo": {
        "< 5 años":   22.05,
        "5-10 años":  18.98,
        "11-15 años":  7.43,
        "> 15 años":   5.26,
    },
    # Tiempo promedio de viaje por modo (minutos)
    "tiempo_modo": {
        "Público":        56.58,
        "Privado":        39.03,
        "Informal":       38.87,
        "No motorizado":  22.10,
    },
    # Indicadores de motorización
    "total_vehiculos": 815_414,
    "motos_1000":       120.5,
    "autos_1000":        67.13,
    "bici_1000":         10.46,
}

# Líneas del sistema SITVA con características de carga
# base_load: fracción de carga relativa frente a Línea A (referencia 1.0)
SITVA_LINEAS = {
    "A":  {"nombre": "Línea A",    "tipo": "Metro",       "base_load": 1.00, "color": "#F7941D"},
    "B":  {"nombre": "Línea B",    "tipo": "Metro",       "base_load": 0.72, "color": "#2196F3"},
    "K":  {"nombre": "Cable K",    "tipo": "Metrocable",  "base_load": 0.55, "color": "#9C27B0"},
    "J":  {"nombre": "Cable J",    "tipo": "Metrocable",  "base_load": 0.48, "color": "#00BCD4"},
    "L":  {"nombre": "Cable L",    "tipo": "Metrocable",  "base_load": 0.31, "color": "#4CAF50"},
    "M":  {"nombre": "Cable M",    "tipo": "Metrocable",  "base_load": 0.42, "color": "#E91E63"},
    "H":  {"nombre": "Cable H",    "tipo": "Metrocable",  "base_load": 0.38, "color": "#FF5722"},
    "T":  {"nombre": "Tranvía T",  "tipo": "Tranvía",     "base_load": 0.61, "color": "#FFEB3B"},
    "P":  {"nombre": "Metro Plus P","tipo": "Metro Plus", "base_load": 0.53, "color": "#795548"},
    "1":  {"nombre": "Metro Plus 1","tipo": "Metro Plus", "base_load": 0.46, "color": "#00E676"},
    "2":  {"nombre": "Metro Plus 2","tipo": "Metro Plus", "base_load": 0.44, "color": "#40C4FF"},
}

# Top zonas generadoras de viajes (Macrozonas OD)
AMVA_MACROZONAS_TOP = [
    {"municipio": "Medellín",   "zona": "La Candelaria",     "pct": 8.64},
    {"municipio": "Medellín",   "zona": "El Poblado",        "pct": 6.88},
    {"municipio": "Medellín",   "zona": "Robledo",           "pct": 5.11},
    {"municipio": "Medellín",   "zona": "Belén",             "pct": 5.09},
    {"municipio": "Medellín",   "zona": "Laureles-Estadio",  "pct": 4.57},
    {"municipio": "Sabaneta",   "zona": "Urbana Sabaneta",   "pct": 2.44},
    {"municipio": "Bello",      "zona": "Comuna 04",         "pct": 2.44},
    {"municipio": "Itagüí",     "zona": "Comuna 01",         "pct": 2.12},
    {"municipio": "Envigado",   "zona": "Urbana Envigado",   "pct": 1.98},
    {"municipio": "Copacabana", "zona": "Urbana Copacabana", "pct": 1.23},
]
