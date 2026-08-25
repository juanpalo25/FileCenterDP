import bcrypt
import streamlit as st

from db import get_conn


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def crear_usuario(nombre: str, usuario: str, rol: str, password: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO usuarios (nombre, usuario, rol, password_hash) VALUES (?, ?, ?, ?)",
            (nombre, usuario, rol, hash_password(password)),
        )


def listar_usuarios():
    with get_conn() as conn:
        return conn.execute(
            "SELECT id, nombre, usuario, rol FROM usuarios ORDER BY nombre"
        ).fetchall()


def eliminar_usuario(usuario_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))


def autenticar(usuario: str, password: str):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM usuarios WHERE usuario = ?", (usuario,)
        ).fetchone()
    if row is None:
        return None
    if not verify_password(password, row["password_hash"]):
        return None
    return dict(row)


def hay_usuarios() -> bool:
    with get_conn() as conn:
        row = conn.execute("SELECT COUNT(*) AS n FROM usuarios").fetchone()
    return row["n"] > 0


def render_login():
    """Renderiza el formulario de login. Devuelve True si hay una sesión activa."""
    if "usuario_actual" in st.session_state:
        return True

    st.title("FileCenterDP — Ingreso")

    if not hay_usuarios():
        st.info(
            "No hay usuarios creados todavía. Creá el primer usuario "
            "(quedará como administrador)."
        )
        with st.form("crear_admin"):
            nombre = st.text_input("Nombre")
            usuario = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            enviado = st.form_submit_button("Crear administrador")
        if enviado:
            if not nombre or not usuario or not password:
                st.error("Completá todos los campos.")
            else:
                crear_usuario(nombre, usuario, "administrador", password)
                st.success("Administrador creado. Iniciá sesión.")
                st.rerun()
        return False

    with st.form("login"):
        usuario = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        enviado = st.form_submit_button("Ingresar")
    if enviado:
        datos = autenticar(usuario, password)
        if datos is None:
            st.error("Usuario o contraseña incorrectos.")
        else:
            st.session_state["usuario_actual"] = datos
            st.rerun()
    return False


def cerrar_sesion():
    st.session_state.pop("usuario_actual", None)
    st.rerun()
