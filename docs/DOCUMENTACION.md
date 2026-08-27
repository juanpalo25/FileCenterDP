# Documentación técnica — FileCenterDP (MVP local)

> Qué es y cómo está armado lo que ya está construido y funcionando. Para el plan original ver [PLAN_EJECUCION.md](PLAN_EJECUCION.md); para el estado actual ver [PROGRESO.md](PROGRESO.md); para lo que falta ver [PENDIENTE.md](PENDIENTE.md).

## Qué es

Una aplicación web local (Streamlit) que centraliza la carga, generación de archivos y seguimiento de las 4 solicitudes que hoy se manejan por WhatsApp entre analistas y asistentes comerciales:

- **ODC** — Orden de Compra
- **ODR** — Orden de Reposición
- **CDP** — Cambio de Precio
- **FDP** — Ficha de Producto

## Cómo correrla

```bash
"C:\Users\dp887\Desktop\FileCenterDP\.venv\Scripts\python.exe" -m streamlit run "C:\Users\dp887\Desktop\FileCenterDP\app\main.py"
```

Se abre en `http://localhost:8501`. El primer usuario que se crea en la pantalla de login queda como **administrador** automáticamente. Desde el menú **Administración → Maestros** hay que cargar `MaestroDP.xlsx` y `MaestroPMC.xlsx` (botones "Actualizar MaestroDP" / "Actualizar MaestroPMC") antes de poder cargar solicitudes, porque de ahí salen los comitentes, rubros y costos.

También hay un `.claude/launch.json` configurado (`C:\Users\dp887\.claude\launch.json`) para levantarla como preview desde Claude Code sin escribir el comando a mano.

## Estructura de archivos

```
FileCenterDP/
├── MaestroDP.xlsx                     ← maestro (lo actualiza el usuario manualmente)
├── Ejemplos/                          ← plantillas y .prn reales usados para calibrar el formato
├── app/
│   ├── main.py            ← entrypoint Streamlit, login + navegación por rol
│   ├── config.py           ← rutas, constantes (tipos, prioridades, estados)
│   ├── db.py                ← esquema SQLite + conexión
│   ├── auth.py              ← login, alta de usuarios, hash de contraseñas (bcrypt)
│   ├── maestros.py         ← lee MaestroDP/MaestroPMC y los cachea en SQLite
│   ├── solicitudes.py      ← parseo de plantillas, alta de solicitudes, cambio de estado
│   ├── generators.py       ← generación de .prn / PMC.xlsx / paquete .zip de descarga
│   ├── views_analista.py   ← pantalla "Cargar solicitud"
│   ├── views_asistente.py  ← pantalla "Pendientes / Descargar"
│   ├── views_dashboard.py  ← pantalla "Dashboard"
│   └── views_admin.py      ← pantalla "Administración" (usuarios + maestros)
├── db/filecenterdp.db      ← base SQLite (se crea sola al arrancar)
├── docs/                   ← esta documentación
├── bitacora.md             ← registro de avances del proyecto
└── requirements.txt
```

## Roles y permisos

| Rol | Puede |
|---|---|
| Analista | Cargar solicitud, ver Dashboard |
| Asistente | Ver Pendientes / Descargar, ver Dashboard |
| Administrador | Todo lo anterior + Administración (usuarios y maestros) |

## Modelo de datos (SQLite, `db/filecenterdp.db`)

- **usuarios**: nombre, usuario, rol, password_hash
- **solicitudes**: id (correlativo global #0001, #0002…), tipo, comitente, rubro, marca (solo ODC — ver "Solicitudes ODC por marca" más abajo), prioridad, fecha_vigencia (solo CDP), estado, fecha_creacion, fecha_emision, referencia_externa, archivo_origen_nombre, archivo_origen_datos (el Excel subido, guardado tal cual), creado_por, actualizado_por
- **solicitud_items**: sku, cantidad, costo_actualizado, costo_maestro (snapshot al momento de cargar, para el historial de la alerta), pvp, costo
- **historial_estados**: cada cambio de estado con fecha y usuario — es lo que alimenta la trazabilidad del dashboard
- **maestro_dp_cache**: copia de MaestroDP.xlsx en SQLite, para no leer el archivo entero en cada pantalla
- **maestros_meta**: cuándo fue la última carga del maestro y cuántas filas trajo

## Flujo por tipo de solicitud

### 1. Analista carga la solicitud
Elige tipo → comitente y rubro se autocompletan desde MaestroDP (no se tipean a mano) → prioridad → sube la plantilla Excel. El sistema valida que estén las columnas obligatorias:
- ODC: `Marca`, `SKU`, `Cantidad`, `Costo_actualizado`
- ODR: `SKU`, `Cantidad`
- CDP: `SKU`, `PVP`, `Costo` (Costo puede venir vacío)
- FDP: no tiene columnas fijas, se acepta el archivo tal cual

Si falta una columna obligatoria o un dato requerido, se corta la carga con un mensaje de error específico (no se guarda nada a medias).

Para ODC, además se compara el `Costo_actualizado` de la plantilla contra el `Costo Ppal` de MaestroDP por cada SKU al momento de confirmar la carga; si hay diferencias, se muestra una leyenda de alerta con los SKU afectados — **no bloquea la carga**, es solo para que el asistente las revise antes de emitir la orden.

Al confirmar, el sistema asigna el número de solicitud (correlativo, único entre los 4 tipos) y queda en estado **Cargado (pendiente)**.

#### Solicitudes ODC por marca
La plantilla de ODC trae una columna `Marca` por SKU. Al cargar, el sistema agrupa los ítems por marca y **crea una solicitud independiente por cada marca** (cada una con su propio número correlativo), aunque el analista haya subido un solo archivo con varias marcas mezcladas. El mensaje de confirmación lista todos los números de solicitud creados. La comparación de costo contra MaestroDP se hace una sola vez sobre el archivo completo, antes de repartir los ítems entre las solicitudes.

### 2. Asistente descarga los archivos
En "Pendientes / Descargar" aparecen las solicitudes pendientes, ordenadas por prioridad (alta primero) y luego por más recientes. Arriba de la lista hay un botón **"Descarga Masiva"** que arma un único `.zip` con el archivo de cada solicitud pendiente (mismo criterio de nombre y contenido que la descarga individual).

Cada solicitud también tiene su propio botón ("Descargar archivos") que genera y baja un `.zip` con el o los archivos que corresponden:

| Tipo | Archivos generados |
|---|---|
| ODC | `ODC ... .prn` |
| ODR | `ODR ... .prn` |
| CDP | `CDP ... .prn` |
| FDP | el archivo original, renombrado |

Nombre de archivo: `TIPO Comitente #Solicitud Fecha.extensión` (ej. `ODC GUDYS SA #0012 24-08-2026.prn`). El nombre no incluye la marca aunque la solicitud sea de una sola marca — se mantiene el formato original para no afectar cómo lo procesa el sistema comercial.

**Formato `.prn`:** columnas de ancho fijo de 10 caracteres, justificadas a la derecha, sin separador, con salto de línea CRLF — calibrado y verificado **byte a byte** contra los archivos reales que dejaste en `Ejemplos/`. ODC y ODR llevan SKU + Cantidad; CDP lleva SKU + PVP (entero) + Costo (2 decimales, en blanco si no hay costo).

No se genera ningún archivo PMC — esa funcionalidad se sacó de la app (ver "Decisiones de diseño relevantes").

#### Previsualización de una solicitud (detalle de ítems)
Al desplegar una solicitud pendiente se muestra una tabla con sus ítems. Para ODC trae columnas específicas:

| Columna | Contenido |
|---|---|
| ID | Numeración correlativa propia de la tabla (1, 2, 3…), no el id interno de la base |
| SKU | Sin separador de miles |
| Cantidad | Tal cual la plantilla |
| Costo Actualizado | El de la plantilla, formato `11.430,23` (2 decimales, estilo argentino) |
| Costo en sistema | `Costo Ppal` **vigente** en MaestroDP para ese SKU (se recalcula en el momento, no es el valor guardado al cargar la solicitud) |
| DIF vs Maestro | Costo en sistema − Costo Actualizado; en verde si es positivo, en rojo si es negativo |
| PVP | `Precio Ppal` vigente en MaestroDP para ese SKU |

Para ODR y CDP la tabla es la simple de siempre (SKU sin comas + sus columnas propias), con la misma numeración local de ID.

### 3. Asistente actualiza el estado
Una vez emitida la orden / aplicado el cambio en el sistema comercial, el asistente carga el número que le devolvió ese sistema (Nro. de OC / OR / Lote). El estado pasa a **Emitido** (ODC/ODR) o **Aplicado** (CDP/FDP), con la fecha, y queda registrado en el historial.

### 4. Dashboard
Filtros por tipo, comitente, rubro, prioridad y estado. Indicadores (total, pendientes, emitidas, aplicadas). Selección de una solicitud puntual para ver toda su trazabilidad (quién la cargó, cuándo, cuándo se emitió/aplicó y con qué referencia).

## Decisiones de diseño relevantes

- **Numeración global**: un solo contador para los 4 tipos, no uno por tipo — así lo pidió el usuario, siguiendo el ejemplo del modelo de datos del brief.
- **Un solo botón de descarga = un `.zip`**: se mantiene la misma mecánica en toda la app, incluso para los tipos que hoy generan un solo archivo.
- **PMC eliminado por completo**: la primera versión generaba un `PMC.xlsx` por cada ODC cruzando MaestroPMC + MaestroDP. El usuario decidió (2026-08-27) que no lo van a usar más — se sacó la generación del archivo, el loader de MaestroPMC en Administración, la lectura de `MaestroPMC.xlsx` y las tablas relacionadas.
- **Maestros como Excel, no base de datos externa**: se evaluó usar la base Postgres de otro proyecto del usuario (Reposición), pero el usuario confirmó que el maestro de este proyecto sigue siendo el Excel de la carpeta raíz.
- **Refresh de maestro manual**: MaestroDP se actualiza una vez por semana y no hay forma confiable de detectarlo automáticamente, así que el refresh es un botón, no un proceso en segundo plano.
- **ODC dividida por marca al cargar, no al descargar**: se decidió repartir los ítems en solicitudes separadas ya en el momento de la carga (una por marca), en vez de guardar una sola solicitud multi-marca y separarla recién al generar el `.prn` — así cada solicitud tiene su propio número, estado y trazabilidad independientes.
- **Nombre de archivo sin la marca**: aunque cada solicitud ODC ahora es de una sola marca, el nombre de archivo de salida no la incluye — se mantiene el formato `TIPO Comitente #Solicitud Fecha.ext` ya calibrado contra el sistema comercial, para no arriesgar que deje de reconocerlo.
- **Costo/PVP del detalle de ODC son en vivo, no snapshot**: la tabla de previsualización de una solicitud pendiente consulta MaestroDP en el momento (no el valor guardado cuando se cargó la solicitud), porque el maestro puede haberse actualizado entre la carga y la revisión del asistente. El `costo_maestro` que sí queda guardado en `solicitud_items` es el snapshot histórico usado para la alerta de diferencias en el momento de la carga.

## Cómo se probó

- Los generadores de `.prn` se probaron leyendo los archivos reales de `Ejemplos/`, regenerándolos con el código de la app y comparando el resultado **byte a byte** contra el original — coincide exactamente para ODC, ODR y CDP.
- Se probó el flujo completo (login, carga de maestros, carga de solicitud, descarga, actualización de estado, dashboard) contra la aplicación corriendo en el navegador.
- Se probaron los 4 tipos de solicitud de punta a punta, incluyendo el caso de costo vacío en CDP y la numeración correlativa cruzando tipos.
- (2026-08-27) Se probó el split de ODC por marca, la migración de esquema (columna `marca` agregada a una base ya existente), la generación de archivos sin PMC, el `.zip` de Descarga Masiva y el orden por prioridad, todo contra una copia de trabajo de los datos reales y limpiando los registros de prueba después.
