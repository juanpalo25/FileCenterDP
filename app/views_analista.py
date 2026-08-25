from datetime import date

import streamlit as st

from config import PRIORIDADES
from generators import format_solicitud_id
from maestros import listar_comitentes, listar_rubros
from solicitudes import PlantillaInvalida, crear_solicitud, detectar_diferencias_costo, parsear_plantilla


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
        "ODC": "Columnas requeridas: SKU, Cantidad, Costo_actualizado",
        "ODR": "Columnas requeridas: SKU, Cantidad",
        "CDP": "Columnas requeridas: SKU, PVP, Costo",
        "FDP": "Subí la ficha de producto tal como la vas a pedir que se cargue.",
    }[tipo]
    archivo = st.file_uploader(f"Plantilla ({ayuda_plantilla})", type=["xlsx", "xls"])

    if "odc_preview" not in st.session_state:
        st.session_state["odc_preview"] = None

    if archivo is not None and tipo == "ODC" and st.button("Previsualizar diferencias de costo"):
        try:
            items = parsear_plantilla(tipo, archivo.getvalue())
            diferencias = detectar_diferencias_costo(items)
            st.session_state["odc_preview"] = {"items": items, "diferencias": diferencias}
        except PlantillaInvalida as e:
            st.error(str(e))

    preview = st.session_state.get("odc_preview")
    if tipo == "ODC" and preview and preview["diferencias"]:
        st.warning(f"Se detectaron {len(preview['diferencias'])} SKU con costo distinto al de MaestroDP:")
        st.dataframe(preview["diferencias"], use_container_width=True)

    if st.button("Cargar Solicitud", type="primary"):
        if archivo is None:
            st.error("Tenés que subir la plantilla.")
            return
        try:
            archivo_bytes = archivo.getvalue()
            items = parsear_plantilla(tipo, archivo_bytes)
            if tipo == "ODC":
                detectar_diferencias_costo(items)
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
            st.session_state["odc_preview"] = None
            st.success(
                f"Solicitud {format_solicitud_id(solicitud_id)} cargada correctamente. "
                f"Estado: Cargado (pendiente)."
            )
        except PlantillaInvalida as e:
            st.error(str(e))
