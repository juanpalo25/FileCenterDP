import streamlit as st

from auth import crear_usuario, eliminar_usuario, listar_usuarios
from config import MAESTRO_DP_PATH, ROLES
from maestros import cargar_maestro_dp, estado_maestros


def render(usuario: dict):
    st.header("Administración")

    tab_usuarios, tab_maestros = st.tabs(["Usuarios", "Maestros (MaestroDP)"])

    with tab_usuarios:
        st.subheader("Crear usuario")
        with st.form("crear_usuario"):
            nombre = st.text_input("Nombre")
            login = st.text_input("Usuario")
            rol = st.selectbox("Rol", ROLES)
            password = st.text_input("Contraseña", type="password")
            enviado = st.form_submit_button("Crear")
        if enviado:
            if not nombre or not login or not password:
                st.error("Completá todos los campos.")
            else:
                try:
                    crear_usuario(nombre, login, rol, password)
                    st.success(f"Usuario '{login}' creado.")
                    st.rerun()
                except Exception as e:
                    st.error(f"No se pudo crear el usuario: {e}")

        st.subheader("Usuarios existentes")
        usuarios = listar_usuarios()
        for u in usuarios:
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            col1.write(u["nombre"])
            col2.write(u["usuario"])
            col3.write(u["rol"])
            if u["usuario"] != usuario["usuario"]:
                if col4.button("Eliminar", key=f"del_{u['id']}"):
                    eliminar_usuario(u["id"])
                    st.rerun()

    with tab_maestros:
        st.write(f"Ruta MaestroDP: `{MAESTRO_DP_PATH}`")

        estado = estado_maestros()
        meta = estado.get("MaestroDP")
        st.metric("MaestroDP - filas cargadas", meta["filas"] if meta else 0)
        st.caption(f"Última carga: {meta['ultima_carga'] if meta else 'nunca'}")
        if st.button("Actualizar MaestroDP"):
            try:
                n = cargar_maestro_dp()
                st.success(f"MaestroDP actualizado: {n} filas.")
                st.rerun()
            except FileNotFoundError:
                st.error(f"No se encontró el archivo en {MAESTRO_DP_PATH}")
