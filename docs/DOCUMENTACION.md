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
├── MaestroDP.xlsx / MaestroPMC.xlsx   ← maestros (los actualiza el usuario manualmente)
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
- **solicitudes**: id (correlativo global #0001, #0002…), tipo, comitente, rubro, prioridad, fecha_vigencia (solo CDP), estado, fecha_creacion, fecha_emision, referencia_externa, archivo_origen_nombre, archivo_origen_datos (el Excel subido, guardado tal cual), creado_por, actualizado_por
- **solicitud_items**: sku, cantidad, costo_actualizado, costo_maestro (para comparar), pvp, costo
- **historial_estados**: cada cambio de estado con fecha y usuario — es lo que alimenta la trazabilidad del dashboard
- **maestro_dp_cache / maestro_pmc_cache**: copia de los Excel en SQLite, para no leer el archivo entero en cada pantalla
- **maestros_meta**: cuándo fue la última carga de cada maestro y cuántas filas trajo

## Flujo por tipo de solicitud

### 1. Analista carga la solicitud
Elige tipo → comitente y rubro se autocompletan desde MaestroDP (no se tipean a mano) → prioridad → sube la plantilla Excel. El sistema valida que estén las columnas obligatorias:
- ODC: `SKU`, `Cantidad`, `Costo_actualizado`
- ODR: `SKU`, `Cantidad`
- CDP: `SKU`, `PVP`, `Costo` (Costo puede venir vacío)
- FDP: no tiene columnas fijas, se acepta el archivo tal cual

Si falta una columna obligatoria o un dato requerido, se corta la carga con un mensaje de error específico (no se guarda nada a medias).

Para ODC, además se compara el `Costo_actualizado` de la plantilla contra el `Costo Ppal` de MaestroDP por cada SKU, y se muestra una alerta si hay diferencias — para que el asistente las revise antes de emitir la orden.

Al confirmar, el sistema asigna el número de solicitud (correlativo, único entre los 4 tipos) y queda en estado **Cargado (pendiente)**.

### 2. Asistente descarga los archivos
En "Pendientes / Descargar" aparece cada solicitud pendiente con sus datos. Con un solo botón ("Descargar archivos") se genera y baja un `.zip` con el o los archivos que corresponden:

| Tipo | Archivos generados |
|---|---|
| ODC | `PMC ... .xlsx` + `ODC ... .prn` |
| ODR | `ODR ... .prn` |
| CDP | `CDP ... .prn` |
| FDP | el archivo original, renombrado |

Nombre de archivo: `TIPO Comitente #Solicitud Fecha.extensión` (ej. `ODC GUDYS SA #0012 24-08-2026.prn`).

**Formato `.prn`:** columnas de ancho fijo de 10 caracteres, justificadas a la derecha, sin separador, con salto de línea CRLF — calibrado y verificado **byte a byte** contra los archivos reales que dejaste en `Ejemplos/`. ODC y ODR llevan SKU + Cantidad; CDP lleva SKU + PVP (entero) + Costo (2 decimales, en blanco si no hay costo).

**Archivo PMC.xlsx:** una fila con los datos del último pedido de ese comitente en MaestroPMC (responsable, rubro, condición de pago, valor anticipado) más el "Producto/Marca" (las marcas de los SKU de la solicitud, según MaestroDP) y el "Importe" = suma de cantidad × costo actualizado de todos los ítems.

### 3. Asistente actualiza el estado
Una vez emitida la orden / aplicado el cambio en el sistema comercial, el asistente carga el número que le devolvió ese sistema (Nro. de OC / OR / Lote). El estado pasa a **Emitido** (ODC/ODR) o **Aplicado** (CDP/FDP), con la fecha, y queda registrado en el historial.

### 4. Dashboard
Filtros por tipo, comitente, rubro, prioridad y estado. Indicadores (total, pendientes, emitidas, aplicadas). Selección de una solicitud puntual para ver toda su trazabilidad (quién la cargó, cuándo, cuándo se emitió/aplicó y con qué referencia).

## Decisiones de diseño relevantes

- **Numeración global**: un solo contador para los 4 tipos, no uno por tipo — así lo pidió el usuario, siguiendo el ejemplo del modelo de datos del brief.
- **Un solo botón de descarga = un `.zip`**: para ODC, que necesita dos archivos (PMC + prn), se empaquetan juntos; para los demás tipos igual se entrega en `.zip` para mantener la misma mecánica en toda la app.
- **Maestros como Excel, no base de datos externa**: se evaluó usar la base Postgres de otro proyecto del usuario (Reposición), pero el usuario confirmó que los maestros de este proyecto siguen siendo los Excel de la carpeta raíz.
- **Refresh de maestros manual**: MaestroDP/MaestroPMC se actualizan una vez por semana y no hay forma confiable de detectarlo automáticamente, así que el refresh es un botón, no un proceso en segundo plano.

## Cómo se probó

- Los generadores de `.prn` se probaron leyendo los archivos reales de `Ejemplos/`, regenerándolos con el código de la app y comparando el resultado **byte a byte** contra el original — coincide exactamente para ODC, ODR y CDP.
- Se probó el flujo completo (login, carga de maestros, carga de solicitud, descarga, actualización de estado, dashboard) contra la aplicación corriendo en el navegador.
- Se probaron los 4 tipos de solicitud de punta a punta, incluyendo el caso de costo vacío en CDP y la numeración correlativa cruzando tipos.
