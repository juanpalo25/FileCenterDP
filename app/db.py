import sqlite3
from contextlib import contextmanager

from config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    usuario TEXT NOT NULL UNIQUE,
    rol TEXT NOT NULL CHECK(rol IN ('analista','asistente','administrador')),
    password_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS solicitudes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT NOT NULL CHECK(tipo IN ('ODC','ODR','CDP','FDP')),
    comitente TEXT NOT NULL,
    rubro TEXT,
    marca TEXT,
    prioridad TEXT NOT NULL CHECK(prioridad IN ('alta','media','baja')),
    fecha_vigencia TEXT,
    estado TEXT NOT NULL,
    fecha_creacion TEXT NOT NULL,
    fecha_emision TEXT,
    referencia_externa TEXT,
    archivo_origen_nombre TEXT NOT NULL,
    archivo_origen_datos BLOB NOT NULL,
    creado_por TEXT NOT NULL,
    actualizado_por TEXT
);

CREATE TABLE IF NOT EXISTS solicitud_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    solicitud_id INTEGER NOT NULL REFERENCES solicitudes(id),
    sku INTEGER,
    cantidad NUMERIC,
    costo_actualizado NUMERIC,
    costo_maestro NUMERIC,
    pvp NUMERIC,
    costo NUMERIC
);

CREATE TABLE IF NOT EXISTS historial_estados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    solicitud_id INTEGER NOT NULL REFERENCES solicitudes(id),
    estado TEXT NOT NULL,
    fecha TEXT NOT NULL,
    usuario TEXT NOT NULL,
    detalle TEXT
);

CREATE TABLE IF NOT EXISTS maestro_dp_cache (
    sku INTEGER PRIMARY KEY,
    cod_rubro TEXT,
    comitente TEXT,
    cod_comitente TEXT,
    marca TEXT,
    descripcion TEXT,
    precio_ppal NUMERIC,
    costo_ppal NUMERIC,
    cod_srub TEXT
);

CREATE TABLE IF NOT EXISTS maestros_meta (
    nombre TEXT PRIMARY KEY,
    ultima_carga TEXT,
    filas INTEGER
);
"""


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_conn() as conn:
        conn.executescript(SCHEMA)
        columnas = {row["name"] for row in conn.execute("PRAGMA table_info(solicitudes)")}
        if "marca" not in columnas:
            conn.execute("ALTER TABLE solicitudes ADD COLUMN marca TEXT")


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
