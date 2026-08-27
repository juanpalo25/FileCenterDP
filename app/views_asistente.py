from datetime import date

import pandas as pd
import streamlit as st

from config import ESTADO_PENDIENTE, ORDEN_PRIORIDAD, REFERENCIA_LABEL_POR_TIPO
from generators import construir_paquete_descarga, construir_paquete_descarga_masiva, format_solicitud_id
from maestros import buscar_producto_por_sku
from solicitudes import actualizar_estado, listar_solicitudes, obtener_solicitud


def _formato_arg(valor, decimales: int = 2) -> str:
    """Formatea un número en estilo argentino: punto de miles, coma decimal.
    Ej: 11430.2 -> '11.430,20'."""
    if valor is None:
        return "—"
    texto = f"{float(valor):,.{decimales}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def _color_dif(valor) -> str:
    if valor is None or valor == 0:
        return ""
    return "color: #2e7d32" if valor > 0 else "color: #c62828"


def _tabla_items_odc(items: list[dict]) -> pd.DataFrame:
    filas = []
    for i, it in enumerate(items, start=1):
        producto = buscar_producto_por_sku(it["sku"]) or {}
        costo_sistema = producto.get("costo_ppal")
        costo_actualizado = it.get("costo_actualizado")
        dif = (
            costo_sistema - costo_actualizado
            if costo_sistema is not None and costo_actualizado is not None
            else None
        )
        filas.append(
            {
                "ID": i,
                "SKU": str(it["sku"]),
                "Cantidad": it["cantidad"],
                "Costo Actualizado": costo_actualizado,
                "Costo en sistema": costo_sistema,
                "DIF vs Maestro": dif,
                "PVP": producto.get("precio_ppal"),
            }
        )
    df = pd.DataFrame(filas)
    return df.style.format(
        {
            "Costo Actualizado": _formato_arg,
            "Costo en sistema": _formato_arg,
            "DIF vs Maestro": _formato_arg,
            "PVP": lambda v: _formato_arg(v, decimales=0),
        }
    ).map(_color_dif, subset=["DIF vs Maestro"])


_COLUMNAS_SIMPLE_POR_TIPO = {
    "ODR": [("sku", "SKU"), ("cantidad", "Cantidad")],
    "CDP": [("sku", "SKU"), ("pvp", "PVP"), ("costo", "Costo")],
}


def _tabla_items_simple(tipo: str, items: list[dict]) -> pd.DataFrame:
    columnas = _COLUMNAS_SIMPLE_POR_TIPO.get(tipo, [("sku", "SKU"), ("cantidad", "Cantidad")])
    filas = []
    for i, it in enumerate(items, start=1):
        fila = {"ID": i}
        for clave, etiqueta in columnas:
            valor = it.get(clave)
            fila[etiqueta] = str(valor) if clave == "sku" else valor
        filas.append(fila)
    return pd.DataFrame(filas)


def render(usuario: dict):
    st.header("Solicitudes pendientes")

    pendientes = listar_solicitudes(estado=ESTADO_PENDIENTE)
    if not pendientes:
        st.info("No hay solicitudes pendientes.")
        return

    pendientes = sorted(pendientes, key=lambda s: (ORDEN_PRIORIDAD[s["prioridad"]], -s["id"]))

    detalles_pendientes = [obtener_solicitud(s["id"]) for s in pendientes]
    zip_masivo = construir_paquete_descarga_masiva(detalles_pendientes)
    st.download_button(
        "Descarga Masiva (todas las pendientes)",
        data=zip_masivo,
        file_name=f"Descarga_Masiva_{date.today().strftime('%d-%m-%Y')}.zip",
        mime="application/zip",
    )
    st.divider()

    for solicitud, detalle in zip(pendientes, detalles_pendientes):
        titulo = (
            f"{format_solicitud_id(solicitud['id'])} — {solicitud['tipo']} — "
            f"{solicitud['comitente']}"
            + (f" — {solicitud['marca']}" if solicitud.get("marca") else "")
            + f" — prioridad {solicitud['prioridad']}"
        )
        with st.expander(titulo):
            st.write(f"Cargada el {solicitud['fecha_creacion']} por {solicitud['creado_por']}")
            if detalle["items"]:
                if solicitud["tipo"] == "ODC":
                    st.dataframe(_tabla_items_odc(detalle["items"]), use_container_width=True)
                else:
                    st.dataframe(
                        _tabla_items_simple(solicitud["tipo"], detalle["items"]), use_container_width=True
                    )

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
