import streamlit as st

from config import ESTADO_PENDIENTE, REFERENCIA_LABEL_POR_TIPO
from generators import construir_paquete_descarga, format_solicitud_id
from solicitudes import actualizar_estado, listar_solicitudes, obtener_solicitud


def render(usuario: dict):
    st.header("Solicitudes pendientes")

    pendientes = listar_solicitudes(estado=ESTADO_PENDIENTE)
    if not pendientes:
        st.info("No hay solicitudes pendientes.")
        return

    for solicitud in pendientes:
        titulo = (
            f"{format_solicitud_id(solicitud['id'])} — {solicitud['tipo']} — "
            f"{solicitud['comitente']} — prioridad {solicitud['prioridad']}"
        )
        with st.expander(titulo):
            detalle = obtener_solicitud(solicitud["id"])
            st.write(f"Cargada el {solicitud['fecha_creacion']} por {solicitud['creado_por']}")
            if detalle["items"]:
                st.dataframe(detalle["items"], use_container_width=True)

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Descargar")
                zip_bytes, zip_nombre = construir_paquete_descarga(detalle)
                st.download_button(
                    "Descargar archivos",
                    data=zip_bytes,
                    file_name=zip_nombre,
                    mime="application/zip",
                    key=f"descarga_{solicitud['id']}",
                )

            with col2:
                st.subheader("Actualizar estado")
                label = REFERENCIA_LABEL_POR_TIPO[solicitud["tipo"]]
                with st.form(f"form_estado_{solicitud['id']}"):
                    referencia = st.text_input(label)
                    enviado = st.form_submit_button("Confirmar emisión / aplicación")
                if enviado:
                    if not referencia:
                        st.error(f"Ingresá el {label.lower()}.")
                    else:
                        actualizar_estado(solicitud["id"], referencia, usuario["usuario"])
                        st.success("Estado actualizado.")
                        st.rerun()
