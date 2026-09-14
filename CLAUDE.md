# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Qué es

FileCenterDP es una app web local (Streamlit + SQLite) que centraliza 4 tipos de solicitudes que hoy circulan por WhatsApp entre analistas y asistentes comerciales de retail aeroportuario: **ODC** (Orden de Compra), **ODR** (Orden de Reposición), **CDP** (Cambio de Precio) y **FDP** (Ficha de Producto). Genera los archivos de ancho fijo (`.prn`) que el sistema comercial externo necesita, y da trazabilidad completa vía dashboard.

Documentación completa en `docs/`:
- [docs/DOCUMENTACION.md](docs/DOCUMENTACION.md) — qué está construido, modelo de datos, flujo por tipo de solicitud. **Leer primero.**
- [docs/PLAN_EJECUCION.md](docs/PLAN_EJECUCION.md) — plan original acordado con el usuario.
- [docs/PROGRESO.md](docs/PROGRESO.md) — qué fase está hecha.
- [docs/PENDIENTE.md](docs/PENDIENTE.md) — qué falta, incluidas decisiones no cerradas (rubro en CDP/FDP, notificaciones, despliegue compartido F3).
- [bitacora.md](bitacora.md) — registro cronológico de avances; agregar una entrada acá al terminar trabajo significativo.

## Comandos

Correr la app (venv propio del proyecto, no usa el Python global):

```bash
"C:\Users\dp887\Desktop\FileCenterDP\.venv\Scripts\python.exe" -m streamlit run "C:\Users\dp887\Desktop\FileCenterDP\app\main.py"
```

Se abre en `http://localhost:8501`. También hay un `.claude/launch.json` en `C:\Users\dp887\.claude\launch.json` para levantarla como preview desde Claude Code.

Instalar dependencias (si hace falta recrear el venv):

```bash
"C:\Users\dp887\Desktop\FileCenterDP\.venv\Scripts\python.exe" -m pip install -r requirements.txt
```

Si falla por SSL (proxy corporativo interceptando), agregar `--trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host pypi.python.org`.

No hay tests automatizados. La verificación de los generadores `.prn` es manual y **byte a byte** contra los archivos reales en `Ejemplos/` (ver sección siguiente) — no alcanza con revisar el código "a ojo".

## Arquitectura

Todo el código vive en `app/`, sin subpaquetes; cada módulo es una capa:

- `main.py` — entrypoint Streamlit. Inicializa la DB, resuelve login y arma la navegación por rol (`analista` / `asistente` / `administrador`), importando la vista correspondiente de forma perezosa (`import views_x` dentro del branch).
- `config.py` — único lugar con rutas (`ROOT_DIR`, `DB_PATH`, ruta del maestro) y constantes de dominio (tipos de solicitud, prioridades y su orden de clasificación, estados, mapeo tipo→estado final, etiquetas de referencia externa por tipo).
- `db.py` — schema SQLite embebido como string (`SCHEMA`) + `init_db()` (idempotente, `CREATE TABLE IF NOT EXISTS`, más una migración manual con `ALTER TABLE` para columnas agregadas después de la primera versión — ver `init_db()`) + `get_conn()`, context manager que abre conexión, hace commit al salir y cierra.
- `auth.py` — login, alta de usuarios, hash de contraseñas con bcrypt. El primer usuario creado queda administrador automáticamente.
- `maestros.py` — lee `MaestroDP.xlsx` (~71.000 SKU) desde la carpeta raíz y lo cachea en SQLite (`maestro_dp_cache`, `maestros_meta`). El refresh es manual (botón en Administración), no automático — se decidió así porque no hay forma confiable de detectar la actualización semanal.
- `solicitudes.py` — parseo de la plantilla Excel que sube el analista, validación de columnas obligatorias por tipo, agrupamiento por marca para ODC (`agrupar_por_marca`), detección de diferencias de costo vs MaestroDP (`detectar_diferencias_costo`, con tolerancia — ver convenciones), alta de solicitud + ítems, cambio de estado.
- `presupuestos.py` — presupuesto mensual por rubro (PMC): alta/lectura del monto asignado por rubro y período (`presupuestos_pmc`), cálculo en vivo de lo consumido (ODC en estado Emitido) y armado del resumen presupuesto/consumido/saldo (`resumen_pmc`). No confundir con el PMC viejo eliminado — ver convenciones.
- `generators.py` — genera los archivos de salida: `.prn` de ancho fijo (`generar_odc_odr_prn`, `generar_cdp_prn`) y los empaqueta en `.zip`, ya sea de una solicitud (`construir_paquete_descarga`) o de todas las pendientes juntas (`construir_paquete_descarga_masiva`, usada por el botón "Descarga Masiva").
- `views_analista.py`, `views_asistente.py`, `views_dashboard.py`, `views_admin.py` — una pantalla Streamlit por rol/función, cada una con su propio `render(usuario)`. `views_admin.py` tiene 3 pestañas: Usuarios, Maestros (MaestroDP) y PMC (presupuesto mensual por rubro, solo administrador). `views_dashboard.py` incluye la sección de presupuesto PMC, visible para todos los roles que ven el Dashboard.

### Convenciones que hay que respetar

- **Formato `.prn`**: columnas de ancho fijo de 10 caracteres, justificadas a la derecha (`_campo()` en `generators.py`), sin separador, encoding `latin-1`, salto de línea `\r\n` explícito (no depender del `open()` en modo texto). ODC/ODR llevan SKU + Cantidad; CDP lleva SKU + PVP (entero) + Costo (2 decimales, en blanco — no `"0"` — si no hay costo). Este formato está calibrado byte a byte contra `Ejemplos/*.prn`: cualquier cambio en `generators.py` debe re-verificarse contra esos archivos reales, no solo revisado en el código.
- **Numeración de solicitud**: un solo correlativo global (`solicitudes.id`, autoincrement) compartido entre los 4 tipos, no uno por tipo — es una decisión de negocio explícita, no un descuido. Una ODC con varias marcas se reparte en varias solicitudes (una por marca), cada una con su propio correlativo.
- **Marca opcional en ODC**: la columna `Marca` de la plantilla debe existir como encabezado, pero puede venir vacía por renglón (`solicitudes.parsear_plantilla` ya no la exige). Los renglones sin marca se agrupan en una solicitud aparte nombrada con el **comitente** en vez de una marca (`agrupar_por_marca(items, comitente)`) — decisión del usuario (2026-09-14) para no bloquear cargas de comitentes que no manejan varias marcas.
- **Tolerancia en alerta de costo (ODC)**: `detectar_diferencias_costo` solo alerta si `|Costo_actualizado − Costo Ppal| >= config.UMBRAL_DIFERENCIA_COSTO` (hoy $1). Diferencias de centavos se consideran redondeo y no se muestran. No tocar este umbral sin pedido explícito del usuario.
- **PMC (presupuesto mensual por rubro) — nuevo, no confundir con el PMC eliminado**: agregado el 2026-09-14 a pedido del usuario. Es un presupuesto en pesos por rubro y mes (`presupuestos_pmc`, módulo `presupuestos.py`), cargado a mano en Administración → PMC, que se descuenta en vivo con el total (`cantidad × costo_actualizado`) de las ODC que llegan a estado Emitido ese mes; se ve en el Dashboard con el saldo en rojo si es negativo. Cada mes arranca en $0 (sin arrastre) y el monto se puede corregir a mano en cualquier momento (p. ej. si se anula una ODC) — no hay lógica de reversión automática. Esto es un concepto totalmente distinto del PMC del bullet siguiente (que sigue eliminado y no debe reintroducirse).
- **El PMC viejo (archivo) no existe**: se evaluó y se sacó por completo (2026-08-27) — no reintroducir `generar_pmc_xlsx`, `MaestroPMC.xlsx`, ni la tabla `maestro_pmc_cache` salvo pedido explícito del usuario. Esto es distinto del **PMC nuevo (presupuesto por rubro)** del bullet anterior, agregado el 2026-09-14, que sí existe y hay que mantener; la sigla se reusó para otra cosa a pedido del usuario, no es un error.
- **Nombre de archivo de salida**: `TIPO Comitente #Solicitud Fecha.ext` (ver `nombre_archivo()` en `generators.py`), p. ej. `ODC GUDYS SA #0012 24-08-2026.prn` — no incluye la marca aunque la solicitud sea de una sola, para no arriesgar el formato ya calibrado contra el sistema comercial.
- **Maestro como Excel, no DB externa**: se evaluó y se descartó usar la base Postgres de otro proyecto del usuario (Reposición) como fuente de datos maestros. `MaestroDP.xlsx` en la raíz del repo es la fuente de verdad; SQLite solo lo cachea.
- **Costo/PVP en la previsualización de ODC son en vivo**: `views_asistente.py` los consulta contra `maestro_dp_cache` en el momento de mostrar la solicitud pendiente, no contra el `costo_maestro` guardado en `solicitud_items` (ese es el snapshot histórico usado solo para la alerta de diferencias al cargar).
- **`db/filecenterdp.db` no está versionado y no tiene backup automático** — antes de cualquier cambio de esquema en `db.py`, guardar una copia del archivo.
- Archivos con datos reales del negocio (`MaestroDP.xlsx`, `Ejemplos/`, la DB, el brief `.docx`) están en `.gitignore` a propósito — no forzar su versionado.
- **Validación numérica de la plantilla**: `parsear_plantilla` valida que Cantidad (ODC/ODR), Costo_actualizado (ODC), PVP y Costo (CDP) sean numéricos cuando están presentes (helper `_numero()` en `solicitudes.py`) y rechaza toda la plantilla con un mensaje claro si no lo son — decisión del usuario (2026-09-14) para no dejar pasar un valor no numérico y que explote más tarde en `generators.py` con un traceback crudo, a veces en la persona equivocada (el asistente, no el analista que cargó el dato malo).
- **Redondeo, no truncado, en el `.prn`**: `_campo()` usa `round(float(valor))` para los campos sin decimales (Cantidad, PVP), no `int(valor)` — el usuario confirmó (2026-09-14) que los decimales son válidos en esos campos de origen, así que hay que redondear al convertirlos al formato entero del `.prn`, no truncar en silencio. Sigue calibrado byte a byte contra `Ejemplos/*.prn` (los datos reales ya eran enteros).
- **FDP restringido a `.xlsx`/`.xls` — es intencional, no un bug**: se evaluó ampliarlo a cualquier tipo de archivo (parecía inconsistente con que `generators.py` preserve la extensión original) pero el usuario confirmó (2026-09-14) que FDP debe seguir aceptando solo Excel. No cambiar el `type=["xlsx", "xls"]` del `file_uploader` en `views_analista.py` sin pedido explícito.
- **Borrar un usuario pide confirmación**: en `views_admin.py`, "Eliminar" ya no actúa al instante — primero muestra un aviso con "Sí, eliminar"/"Cancelar" (estado en `st.session_state["confirmar_baja_usuario"]`). No volver al borrado directo: no hay backup de la base ni recuperación de contraseña.
- **Anular/editar una solicitud ya cargada no existe** — es la limitación más grande identificada en la revisión de usabilidad del 2026-09-14 (ver [docs/PENDIENTE.md](docs/PENDIENTE.md), sección 5) y quedó pospuesta a propósito para una ronda de trabajo aparte porque necesita decisiones de negocio (quién puede anular, desde qué estados, y si afecta el presupuesto PMC ya descontado) antes de programarla — no improvisarla como parte de otro pedido.

## Estado del proyecto

MVP local construido y probado de punta a punta (Fases 0–4 completas), más varias mejoras post-MVP a partir del uso real (2026-08-27 y 2026-09-14, ver [bitacora.md](bitacora.md) para el detalle cronológico completo). Falta la entrega/capacitación real con el equipo (Fase 5) y definir el despliegue compartido (F3) — ver [docs/PENDIENTE.md](docs/PENDIENTE.md) para el detalle accionable antes de dar por cerrado cualquier trabajo relacionado con puesta en producción.
