import streamlit as st

from auth import crear_usuario, eliminar_usuario, listar_usuarios
from config import MAESTRO_DP_PATH, ROLES
from maestros import cargar_maestro_dp, estado_maestros, listar_rubros
from presupuestos import establecer_presupuesto, obtener_presupuestos, periodo_actual, periodos_disponibles


def render(usuario: dict):
    st.header("Administración")

    tab_usuarios, tab_maestros, tab_pmc = st.tabs(["Usuarios", "Maestros (MaestroDP)", "PMC"])

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
            if u["usuario"] == usuario["usuario"]:
                continue
            if st.session_state.get("confirmar_baja_usuario") == u["id"]:
                st.warning(
                    f"¿Confirmás eliminar a **{u['nombre']}** ({u['usuario']})? "
                    "Esta acción no se puede deshacer."
                )
                col_si, col_no = st.columns(2)
                if col_si.button("Sí, eliminar", key=f"confirmar_del_{u['id']}", type="primary"):
                    eliminar_usuario(u["id"])
                    st.session_state.pop("confirmar_baja_usuario", None)
                    st.rerun()
                if col_no.button("Cancelar", key=f"cancelar_del_{u['id']}"):
                    st.session_state.pop("confirmar_baja_usuario", None)
                    st.rerun()
            elif col4.button("Eliminar", key=f"del_{u['id']}"):
                st.session_state["confirmar_baja_usuario"] = u["id"]
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

    with tab_pmc:
        st.subheader("Presupuesto mensual por rubro")
        rubros = listar_rubros()
        if not rubros:
            st.warning(
                "Todavía no hay rubros cargados. Actualizá MaestroDP antes de cargar presupuestos."
            )
        else:
            periodos = periodos_disponibles()
            periodo = st.selectbox("Mes", periodos, index=periodos.index(periodo_actual()))
            st.caption(
                "El presupuesto de cada rubro se puede modificar en cualquier momento "
                "(por ejemplo, para corregirlo a mano si se anula una ODC)."
            )
            asignados = obtener_presupuestos(periodo)
            with st.form(f"form_pmc_{periodo}"):
                montos = {}
                for rubro in rubros:
                    montos[rubro] = st.number_input(
                        f"Rubro {rubro}",
                        min_value=0.0,
                        value=float(asignados.get(rubro) or 0),
                        step=1000.0,
                        format="%.2f",
                        key=f"pmc_{periodo}_{rubro}",
                    )
                enviado = st.form_submit_button("Guardar presupuestos")
            if enviado:
                for rubro, monto in montos.items():
                    establecer_presupuesto(rubro, periodo, monto, usuario["usuario"])
                st.success(f"Presupuestos de {periodo} actualizados.")
                st.rerun()
