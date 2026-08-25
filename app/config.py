from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = ROOT_DIR / "db" / "filecenterdp.db"
MAESTRO_DP_PATH = ROOT_DIR / "MaestroDP.xlsx"
MAESTRO_PMC_PATH = ROOT_DIR / "MaestroPMC.xlsx"

TIPOS_SOLICITUD = ["ODC", "ODR", "CDP", "FDP"]
PRIORIDADES = ["alta", "media", "baja"]
ROLES = ["analista", "asistente", "administrador"]

ESTADO_PENDIENTE = "Cargado (pendiente)"
ESTADO_EMITIDO = "Emitido"
ESTADO_APLICADO = "Aplicado"

# Estado final que corresponde a cada tipo una vez que el asistente carga la referencia externa
ESTADO_FINAL_POR_TIPO = {
    "ODC": ESTADO_EMITIDO,
    "ODR": ESTADO_EMITIDO,
    "CDP": ESTADO_APLICADO,
    "FDP": ESTADO_APLICADO,
}

# Etiqueta del campo de referencia externa que carga el asistente al cerrar la solicitud
REFERENCIA_LABEL_POR_TIPO = {
    "ODC": "Nro. de OC",
    "ODR": "Nro. de OR",
    "CDP": "Nro. de Lote",
    "FDP": "Nro. de Lote / referencia",
}
