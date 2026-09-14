from datetime import date, datetime

from config import ESTADO_EMITIDO
from db import get_conn
from maestros import listar_rubros


def periodo_actual() -> str:
    return date.today().strftime("%Y-%m")


def periodos_disponibles(atras: int = 6, adelante: int = 3) -> list[str]:
    """Lista de períodos 'YYYY-MM' en orden cronológico, centrada en el mes actual."""
    hoy = date.today()
    periodos = []
    for delta in range(-atras, adelante + 1):
        mes_index = hoy.month - 1 + delta
        anio = hoy.year + mes_index // 12
        mes = mes_index % 12 + 1
        periodos.append(f"{anio:04d}-{mes:02d}")
    return periodos


def establecer_presupuesto(rubro: str, periodo: str, monto: float, usuario: str):
    ahora = datetime.now().isoformat(timespec="seconds")
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO presupuestos_pmc (rubro, periodo, monto_asignado, actualizado_por, fecha_actualizacion)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(rubro, periodo) DO UPDATE SET
                   monto_asignado = excluded.monto_asignado,
                   actualizado_por = excluded.actualizado_por,
                   fecha_actualizacion = excluded.fecha_actualizacion""",
            (rubro, periodo, monto, usuario, ahora),
        )


def obtener_presupuestos(periodo: str) -> dict[str, float]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT rubro, monto_asignado FROM presupuestos_pmc WHERE periodo = ?", (periodo,)
        ).fetchall()
    return {r["rubro"]: r["monto_asignado"] for r in rows}


def calcular_consumido(periodo: str) -> dict[str, float]:
    """Suma cantidad * costo_actualizado de los ítems de ODC en estado Emitido,
    agrupado por rubro, para las ODC cuyo mes de emisión coincide con el período."""
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT s.rubro AS rubro, SUM(i.cantidad * i.costo_actualizado) AS consumido
               FROM solicitudes s
               JOIN solicitud_items i ON i.solicitud_id = s.id
               WHERE s.tipo = 'ODC' AND s.estado = ? AND strftime('%Y-%m', s.fecha_emision) = ?
               GROUP BY s.rubro""",
            (ESTADO_EMITIDO, periodo),
        ).fetchall()
    return {r["rubro"]: (r["consumido"] or 0) for r in rows}


def resumen_pmc(periodo: str) -> list[dict]:
    """Presupuesto, consumido y saldo por rubro para un período, para todos los rubros de MaestroDP."""
    asignados = obtener_presupuestos(periodo)
    consumidos = calcular_consumido(periodo)
    resumen = []
    for rubro in listar_rubros():
        presupuesto = asignados.get(rubro) or 0
        consumido = consumidos.get(rubro) or 0
        resumen.append(
            {
                "rubro": rubro,
                "presupuesto": presupuesto,
                "consumido": consumido,
                "saldo": presupuesto - consumido,
            }
        )
    return resumen
