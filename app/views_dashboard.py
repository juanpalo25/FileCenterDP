import streamlit as st

from config import ESTADO_APLICADO, ESTADO_EMITIDO, ESTADO_PENDIENTE, PRIORIDADES, TIPOS_SOLICITUD
from generators import format_solicitud_id
from maestros import listar_comitentes, listar_rubros
from solicitudes import listar_solicitudes, obtener_solicitud


def render(usuario: dict):
    st.header("Dashboard de solicitudes")

    col1, col2, col3, col4, col5 = st.columns(5)
    tipo = col1.selectbox("Tipo", ["(todos)"] + TIPOS_SOLICITUD)
    comitente = col2.selectbox("Comitente", ["(todos)"] + listar_comitentes())
    rubro = col3.selectbox("Rubro", ["(todos)"] + listar_rubros())
    prioridad = col4.selectbox("Prioridad", ["(todas)"] + PRIORIDADES)
    estado = col5.selectbox("Estado", ["(todos)", ESTADO_PENDIENTE, ESTADO_EMITIDO, ESTADO_APLICADO])

    filtros = dict(
        tipo=None if tipo == "(todos)" else tipo,
        comitente=None if comitente == "(todos)" else comitente,
        rubro=None if rubro == "(todos)" else rubro,
        prioridad=None if prioridad == "(todas)" else prioridad,
        estado=None if estado == "(todos)" else estado,
    )
    solicitudes = listar_solicitudes(**filtros)

    pendientes = sum(1 for s in solicitudes if s["estado"] == ESTADO_PENDIENTE)
    emitidas = sum(1 for s in solicitudes if s["estado"] == ESTADO_EMITIDO)
    aplicadas = sum(1 for s in solicitudes if s["estado"] == ESTADO_APLICADO)
    ind1, ind2, ind3, ind4 = st.columns(4)
    ind1.metric("Total", len(solicitudes))
    ind2.metric("Pendientes", pendientes)
    ind3.metric("Emitidas", emitidas)
    ind4.metric("Aplicadas", aplicadas)

    if not solicitudes:
        st.info("No hay solicitudes con esos filtros.")
        return

    tabla = [
        {
            "Solicitud": format_solicitud_id(s["id"]),
            "Tipo": s["tipo"],
            "Comitente": s["comitente"],
            "Rubro": s["rubro"],
            "Prioridad": s["prioridad"],
            "Estado": s["estado"],
            "Creada": s["fecha_creacion"],
            "Emitida/Aplicada": s["fecha_emision"] or "",
            "Referencia": s["referencia_externa"] or "",
        }
        for s in solicitudes
    ]
    st.dataframe(
        tabla,
        use_container_width=True,
        column_config={
            "Estado": st.column_config.TextColumn("Estado", help="Verde = Emitido/Aplicado")
        },
    )

    st.subheader("Trazabilidad de una solicitud")
    opciones = {format_solicitud_id(s["id"]): s["id"] for s in solicitudes}
    seleccion = st.selectbox("Elegí una solicitud", list(opciones.keys()))
    if seleccion:
        detalle = obtener_solicitud(opciones[seleccion])
        for h in detalle["historial"]:
            st.write(f"**{h['fecha']}** — {h['estado']} — {h['usuario']}" + (f" ({h['detalle']})" if h["detalle"] else ""))
