from datetime import datetime

import openpyxl

from config import MAESTRO_DP_PATH, MAESTRO_PMC_PATH
from db import get_conn


def _to_float(value):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def cargar_maestro_dp() -> int:
    """Lee MaestroDP.xlsx y reemplaza el cache en SQLite. Devuelve la cantidad de filas cargadas."""
    wb = openpyxl.load_workbook(MAESTRO_DP_PATH, data_only=True, read_only=True)
    ws = wb.worksheets[0]

    filas = []
    rows = ws.iter_rows(min_row=2, values_only=True)
    for row in rows:
        cod_rubro, comitente, marca, _refer_prov, sku, descripcion, precio_ppal = row[:7]
        costo_ppal = row[8]
        cod_srub = row[10]
        cod_comitente = row[15]
        if sku is None:
            continue
        filas.append(
            (
                int(sku),
                cod_rubro,
                comitente,
                cod_comitente,
                marca,
                descripcion,
                _to_float(precio_ppal),
                _to_float(costo_ppal),
                cod_srub,
            )
        )
    wb.close()

    with get_conn() as conn:
        conn.execute("DELETE FROM maestro_dp_cache")
        conn.executemany(
            """INSERT OR REPLACE INTO maestro_dp_cache
               (sku, cod_rubro, comitente, cod_comitente, marca, descripcion, precio_ppal, costo_ppal, cod_srub)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            filas,
        )
        conn.execute(
            """INSERT INTO maestros_meta (nombre, ultima_carga, filas) VALUES ('MaestroDP', ?, ?)
               ON CONFLICT(nombre) DO UPDATE SET ultima_carga = excluded.ultima_carga, filas = excluded.filas""",
            (datetime.now().isoformat(timespec="seconds"), len(filas)),
        )
    return len(filas)


def cargar_maestro_pmc() -> int:
    """Lee MaestroPMC.xlsx y reemplaza el cache en SQLite. Devuelve la cantidad de filas cargadas."""
    wb = openpyxl.load_workbook(MAESTRO_PMC_PATH, data_only=True, read_only=True)
    ws = wb.worksheets[0]

    filas = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        (
            fecha_pedido,
            responsable,
            rubro,
            proveedor,
            producto_marca,
            condicion_pago,
            valor_anticipado,
            importe,
        ) = row[:8]
        if proveedor is None:
            continue
        fecha_str = fecha_pedido.isoformat() if hasattr(fecha_pedido, "isoformat") else fecha_pedido
        filas.append(
            (
                fecha_str,
                responsable,
                rubro,
                proveedor,
                producto_marca,
                condicion_pago,
                valor_anticipado,
                _to_float(importe),
            )
        )
    wb.close()

    with get_conn() as conn:
        conn.execute("DELETE FROM maestro_pmc_cache")
        conn.executemany(
            """INSERT INTO maestro_pmc_cache
               (fecha_pedido, responsable_categoria, rubro, proveedor, producto_marca,
                condicion_pago, valor_anticipado, importe)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            filas,
        )
        conn.execute(
            """INSERT INTO maestros_meta (nombre, ultima_carga, filas) VALUES ('MaestroPMC', ?, ?)
               ON CONFLICT(nombre) DO UPDATE SET ultima_carga = excluded.ultima_carga, filas = excluded.filas""",
            (datetime.now().isoformat(timespec="seconds"), len(filas)),
        )
    return len(filas)


def estado_maestros():
    with get_conn() as conn:
        rows = conn.execute("SELECT nombre, ultima_carga, filas FROM maestros_meta").fetchall()
    return {r["nombre"]: dict(r) for r in rows}


def listar_comitentes():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT comitente FROM maestro_dp_cache WHERE comitente IS NOT NULL ORDER BY comitente"
        ).fetchall()
    return [r["comitente"] for r in rows]


def listar_rubros():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT cod_rubro FROM maestro_dp_cache WHERE cod_rubro IS NOT NULL ORDER BY cod_rubro"
        ).fetchall()
    return [r["cod_rubro"] for r in rows]


def buscar_producto_por_sku(sku: int):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM maestro_dp_cache WHERE sku = ?", (sku,)
        ).fetchone()
    return dict(row) if row else None


def ultimo_pedido_pmc(comitente: str):
    """Trae el pedido de PMC más reciente para un comitente (por nombre de proveedor)."""
    with get_conn() as conn:
        row = conn.execute(
            """SELECT * FROM maestro_pmc_cache
               WHERE UPPER(TRIM(proveedor)) = UPPER(TRIM(?))
               ORDER BY fecha_pedido DESC
               LIMIT 1""",
            (comitente,),
        ).fetchone()
    return dict(row) if row else None
