from datetime import date

import streamlit as st

from config import PRIORIDADES
from generators import format_solicitud_id
from maestros import listar_comitentes, listar_rubros
from solicitudes import (
    PlantillaInvalida,
    agrupar_por_marca,
    crear_solicitud,
    detectar_diferencias_costo,
    parsear_plantilla,
)


def render(usuario: dict):
    st.header("Cargar solicitud")

    comitentes = listar_comitentes()
    rubros = listar_rubros()
    if not comitentes:
        st.warning(
            "Todavía no hay datos de MaestroDP cargados. Pedile a un administrador "
            "que use 'Actualizar maestros' antes de cargar solicitudes."
        )
        return

    tipo = st.selectbox("Tipo de solicitud", ["ODC", "ODR", "CDP", "FDP"])
    comitente = st.selectbox("Comitente", comitentes)
    prioridad = st.selectbox("Prioridad", PRIORIDADES)

    rubro = None
    fecha_vigencia = None
    if tipo in ("ODC", "ODR"):
        rubro = st.selectbox("Rubro", rubros)
    if tipo == "CDP":
        fecha_vigencia = st.date_input("Fecha de vigencia", value=date.today())

    ayuda_plantilla = {
        "ODC": "Columnas requeridas: Marca, SKU, Cantidad, Costo_actualizado",
        "ODR": "Columnas requeridas: SKU, Cantidad",
        "CDP": "Columnas requeridas: SKU, PVP, Costo",
        "FDP": "Subí la ficha de producto tal como la vas a pedir que se cargue.",
    }[tipo]
    if tipo == "ODC":
        st.caption("Si la plantilla trae varias marcas, se crea una solicitud por cada una.")
    archivo = st.file_uploader(f"Plantilla ({ayuda_plantilla})", type=["xlsx", "xls"])

    if st.button("Cargar Solicitud", type="primary"):
        if archivo is None:
            st.error("Tenés que subir la plantilla.")
            return
        try:
            archivo_bytes = archivo.getvalue()
            items = parsear_plantilla(tipo, archivo_bytes)

            if tipo == "ODC":
                diferencias = detectar_diferencias_costo(items)
                grupos = agrupar_por_marca(items)
                solicitud_ids = []
                for marca, items_marca in grupos.items():
                    solicitud_id = crear_solicitud(
                        tipo=tipo,
                        comitente=comitente,
                        rubro=rubro,
                        prioridad=prioridad,
                        archivo_nombre=archivo.name,
                        archivo_bytes=archivo_bytes,
                        items=items_marca,
                        creado_por=usuario["usuario"],
                        marca=marca,
                    )
                    solicitud_ids.append((solicitud_id, marca))

                resumen = ", ".join(
                    f"{format_solicitud_id(sid)} ({marca})" for sid, marca in solicitud_ids
                )
                st.success(f"Se cargaron {len(solicitud_ids)} solicitud(es): {resumen}.")

                if diferencias:
                    skus = ", ".join(str(d["sku"]) for d in diferencias)
                    st.warning(
                        f"Los siguientes SKU presentan diferencia de costo versus MaestroDP: {skus}"
                    )
            else:
                solicitud_id = crear_solicitud(
                    tipo=tipo,
                    comitente=comitente,
                    rubro=rubro,
                    prioridad=prioridad,
                    archivo_nombre=archivo.name,
                    archivo_bytes=archivo_bytes,
                    items=items,
                    creado_por=usuario["usuario"],
                    fecha_vigencia=fecha_vigencia.isoformat() if fecha_vigencia else None,
                )
                st.success(
                    f"Solicitud {format_solicitud_id(solicitud_id)} cargada correctamente. "
                    f"Estado: Cargado (pendiente)."
                )
        except PlantillaInvalida as e:
            st.error(str(e))
