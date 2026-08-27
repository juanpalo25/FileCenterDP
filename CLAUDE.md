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
- `solicitudes.py` — parseo de la plantilla Excel que sube el analista, validación de columnas obligatorias por tipo, agrupamiento por marca para ODC (`agrupar_por_marca`), alta de solicitud + ítems, cambio de estado.
- `generators.py` — genera los archivos de salida: `.prn` de ancho fijo (`generar_odc_odr_prn`, `generar_cdp_prn`) y los empaqueta en `.zip`, ya sea de una solicitud (`construir_paquete_descarga`) o de todas las pendientes juntas (`construir_paquete_descarga_masiva`, usada por el botón "Descarga Masiva").
- `views_analista.py`, `views_asistente.py`, `views_dashboard.py`, `views_admin.py` — una pantalla Streamlit por rol/función, cada una con su propio `render(usuario)`.

### Convenciones que hay que respetar

- **Formato `.prn`**: columnas de ancho fijo de 10 caracteres, justificadas a la derecha (`_campo()` en `generators.py`), sin separador, encoding `latin-1`, salto de línea `\r\n` explícito (no depender del `open()` en modo texto). ODC/ODR llevan SKU + Cantidad; CDP lleva SKU + PVP (entero) + Costo (2 decimales, en blanco — no `"0"` — si no hay costo). Este formato está calibrado byte a byte contra `Ejemplos/*.prn`: cualquier cambio en `generators.py` debe re-verificarse contra esos archivos reales, no solo revisado en el código.
- **Numeración de solicitud**: un solo correlativo global (`solicitudes.id`, autoincrement) compartido entre los 4 tipos, no uno por tipo — es una decisión de negocio explícita, no un descuido. Una ODC con varias marcas se reparte en varias solicitudes (una por marca), cada una con su propio correlativo.
- **Nombre de archivo de salida**: `TIPO Comitente #Solicitud Fecha.ext` (ver `nombre_archivo()` en `generators.py`), p. ej. `ODC GUDYS SA #0012 24-08-2026.prn` — no incluye la marca aunque la solicitud sea de una sola, para no arriesgar el formato ya calibrado contra el sistema comercial.
- **PMC no existe**: se evaluó y se sacó por completo (2026-08-27) — no reintroducir `generar_pmc_xlsx`, `MaestroPMC.xlsx`, ni la tabla `maestro_pmc_cache` salvo pedido explícito del usuario.
- **Maestro como Excel, no DB externa**: se evaluó y se descartó usar la base Postgres de otro proyecto del usuario (Reposición) como fuente de datos maestros. `MaestroDP.xlsx` en la raíz del repo es la fuente de verdad; SQLite solo lo cachea.
- **Costo/PVP en la previsualización de ODC son en vivo**: `views_asistente.py` los consulta contra `maestro_dp_cache` en el momento de mostrar la solicitud pendiente, no contra el `costo_maestro` guardado en `solicitud_items` (ese es el snapshot histórico usado solo para la alerta de diferencias al cargar).
- **`db/filecenterdp.db` no está versionado y no tiene backup automático** — antes de cualquier cambio de esquema en `db.py`, guardar una copia del archivo.
- Archivos con datos reales del negocio (`MaestroDP.xlsx`, `Ejemplos/`, la DB, el brief `.docx`) están en `.gitignore` a propósito — no forzar su versionado.

## Estado del proyecto

MVP local construido y probado de punta a punta (Fases 0–4 completas). Falta la entrega/capacitación real con el equipo (Fase 5) y definir el despliegue compartido (F3) — ver [docs/PENDIENTE.md](docs/PENDIENTE.md) para el detalle accionable antes de dar por cerrado cualquier trabajo relacionado con puesta en producción.
