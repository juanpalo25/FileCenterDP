import streamlit as st

from auth import cerrar_sesion, render_login
from db import init_db

st.set_page_config(page_title="FileCenterDP", layout="wide")

init_db()

if not render_login():
    st.stop()

usuario = st.session_state["usuario_actual"]

PAGINAS_POR_ROL = {
    "analista": ["Cargar solicitud", "Dashboard"],
    "asistente": ["Pendientes / Descargar", "Dashboard"],
    "administrador": ["Cargar solicitud", "Pendientes / Descargar", "Dashboard", "Administración"],
}

with st.sidebar:
    st.write(f"**{usuario['nombre']}**")
    st.caption(f"Rol: {usuario['rol']}")
    pagina = st.radio("Navegación", PAGINAS_POR_ROL[usuario["rol"]])
    st.divider()
    if st.button("Cerrar sesión"):
        cerrar_sesion()

if pagina == "Cargar solicitud":
    import views_analista
    views_analista.render(usuario)
elif pagina == "Pendientes / Descargar":
    import views_asistente
    views_asistente.render(usuario)
elif pagina == "Dashboard":
    import views_dashboard
    views_dashboard.render(usuario)
elif pagina == "Administración":
    import views_admin
    views_admin.render(usuario)
