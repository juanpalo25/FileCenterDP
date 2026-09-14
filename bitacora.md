# Bitácora del proyecto FileCenterDP

## 2026-09-14 — Revisión de usabilidad/robustez y primera ronda de correcciones

Se hizo una revisión de punta a punta de la app (lectura de todo `app/`, pruebas aisladas de casos borde y una recorrida en vivo en el navegador contra la base real, sin modificar datos) y se armó un reporte de 17 hallazgos ordenados por gravedad. El detalle completo del reporte quedó en esta conversación; lo accionable pendiente está en [docs/PENDIENTE.md](docs/PENDIENTE.md) → "Mejoras de la revisión de usabilidad (2026-09-14)".

Con el usuario se acordó: dejar para una ronda aparte el hallazgo más grande (no se puede anular/editar una solicitud ya cargada — necesita estado nuevo, permisos y definir el impacto en el presupuesto PMC), confirmar que FDP debe seguir restringido a `.xlsx`/`.xls` (no era un bug, era intencional), y resolver ahora los siguientes 4 puntos:

- **Validación numérica en la plantilla**: si `Cantidad` (ODC/ODR), `Costo_actualizado` (ODC), `PVP` o `Costo` (CDP) vienen con un valor no numérico, `parsear_plantilla` ahora rechaza toda la plantilla con un mensaje claro (columna + SKU afectado) en vez de dejarlo pasar y romper más tarde con un traceback crudo — antes esto explotaba en el momento de cargar (ODC) o recién al descargar el `.prn` días después (ODR/CDP), en la persona equivocada. Nueva función `_numero()` en `solicitudes.py`.
- **Redondeo en vez de truncado en el `.prn`**: `_campo()` en `generators.py` usaba `int(valor)` para los campos sin decimales (Cantidad, PVP), truncando en silencio (5,9 → "5"). El usuario confirmó que los decimales son válidos en esos campos, así que ahora se redondea correctamente (`round(float(valor))`, 5,9 → "6"). Re-verificado byte a byte contra los 3 `.prn` reales de `Ejemplos/` — idéntico, porque los datos reales ya eran enteros.
- **Confirmación antes de borrar un usuario**: en Administración → Usuarios, "Eliminar" ya no borra al instante — ahora pide confirmar ("¿Confirmás eliminar a X? Esta acción no se puede deshacer." con botones "Sí, eliminar" / "Cancelar"). Antes un solo click borraba la cuenta para siempre, sin backup ni forma de recuperar la contraseña.
- **Anti-duplicado en "Cargar solicitud"**: el `file_uploader` se resetea (via una key dinámica en `session_state`) después de cada carga exitosa, así el archivo no queda "cargado" en pantalla invitando a un doble click o un reenvío accidental que generaría una solicitud duplicada. Los mensajes de éxito/alerta se guardan en `session_state` y se muestran después del `st.rerun()`.

Verificado: pruebas aisladas de los 3 casos de valor no numérico (ahora rechazan con mensaje claro), prueba de redondeo, re-verificación byte a byte de los `.prn`, y en el navegador (con usuarios de prueba creados y borrados al terminar, sin tocar la base real): el flujo completo de confirmar/cancelar/eliminar un usuario, y que la pantalla de carga sigue funcionando igual que antes.

## 2026-09-14 — Tolerancia de centavos en alerta de diferencia de costo (ODC)

- `detectar_diferencias_costo` ya no alerta diferencias de costo menores a $1 entre `Costo_actualizado` y el `Costo Ppal` de MaestroDP (antes marcaba cualquier diferencia, incluso de centavos). Umbral configurable en `config.UMBRAL_DIFERENCIA_COSTO`.
- No afecta la columna "DIF vs Maestro" que ve el asistente en la previsualización (`views_asistente.py`) — esa sigue mostrando el valor exacto de la diferencia; el cambio es solo sobre la alerta que dispara al cargar la ODC.

## 2026-09-14 — Presupuesto mensual por rubro (PMC)

- **Pestaña "PMC" en Administración** (solo administrador): permite cargar/editar en cualquier momento el presupuesto mensual de cada rubro (selector de mes, un campo numérico por rubro de MaestroDP). Tabla nueva `presupuestos_pmc` (rubro, período `YYYY-MM`, monto asignado) — cada mes arranca en $0 si no se cargó nada, sin arrastre del mes anterior.
- **Descuento automático**: el "consumido" de cada rubro se calcula en vivo como la suma de `cantidad × costo_actualizado` de los ítems de las ODC en estado *Emitido* cuyo mes de emisión coincide con el período — no se persiste, se recalcula siempre desde `solicitudes`/`solicitud_items`. Si una ODC se anula o hay que corregir algo, el administrador ajusta a mano el monto asignado (no hay lógica de reversión automática, fue decisión explícita del usuario porque el sistema hoy no anula solicitudes).
- **Sección "Presupuesto PMC" en el Dashboard**: visible para todos los roles que ya ven esa pantalla (analista, asistente, administrador). Muestra Presupuesto / Consumido / Saldo por rubro para el mes elegido, con el saldo en rojo si queda negativo.
- Nuevo módulo `presupuestos.py` con la lógica (`establecer_presupuesto`, `obtener_presupuestos`, `calcular_consumido`, `resumen_pmc`, manejo de períodos).
- Verificado de punta a punta en el navegador con un usuario administrador de prueba: carga de presupuesto por rubro, ODC emitida ficticia del mes en curso reflejada como consumido y saldo negativo en rojo. Se usó la base real (no una copia) porque el cambio de esquema es aditivo (`CREATE TABLE IF NOT EXISTS`); se limpiaron el usuario, la solicitud y los presupuestos de prueba al terminar.

## 2026-09-14 — Marca opcional en ODC

- **Marca vacía permitida en ODC**: `parsear_plantilla` ya no rechaza la plantilla si la columna `Marca` viene sin valor en algún renglón (sigue exigiendo que la columna exista como encabezado). `agrupar_por_marca` ahora recibe el comitente y agrupa los renglones sin marca en una única solicitud aparte, nombrada con el comitente en vez de una marca — el resto de los renglones sigue agrupándose por marca como antes.
- Verificado con un caso aislado (`parsear_plantilla` + `agrupar_por_marca` sobre un Excel armado con filas con y sin `Marca`): los renglones con marca se agrupan por marca y los que vienen vacíos caen todos juntos bajo el nombre del comitente.

## 2026-08-27 — Mejoras a partir del uso real

Ajustes pedidos por el usuario tras empezar a usar el MVP:

- **ODC por marca**: la plantilla de ODC ahora incluye columna `Marca`; al cargar, el sistema agrupa los ítems por marca y crea una solicitud independiente por cada una (con su propio número correlativo), en vez de una sola solicitud multi-marca.
- **Alerta de costo no bloqueante**: el cruce Costo_actualizado vs MaestroDP ahora se hace directo al confirmar la carga (se sacó el botón separado de "Previsualizar diferencias") y solo muestra una leyenda con los SKU afectados — nunca impide guardar la solicitud.
- **SKU sin separador de miles**: en todas las tablas de previsualización de ítems.
- **PMC eliminado por completo**: se sacó la generación de `PMC.xlsx` en la descarga de ODC, el loader de MaestroPMC en Administración, la lectura de `MaestroPMC.xlsx` y las tablas relacionadas en la base. ODC ahora descarga solo su `.prn`.
- **Descarga Masiva**: nuevo botón en "Pendientes / Descargar" que arma un solo `.zip` con el archivo de cada solicitud pendiente.
- **Orden por prioridad**: la lista de pendientes ordena primero las de prioridad alta.
- **Detalle de ODC ampliado**: la tabla de previsualización de una solicitud ODC pendiente ahora muestra ID local, SKU, Cantidad, Costo Actualizado (formato `11.430,23`), Costo en sistema y PVP (ambos consultados en vivo contra MaestroDP, no el valor guardado al cargar) y DIF vs Maestro (Costo en sistema − Costo Actualizado, en rojo si es negativo y verde si es positivo).

No incluido en esta ronda: filtrar el Comitente de ODC/ODR por si opera en COMPRA o CONSIGNA — se revisó MaestroDP a fondo y esa clasificación no está en ninguna columna del maestro; el usuario decidió omitirlo por ahora.

Ver el detalle técnico actualizado en [docs/DOCUMENTACION.md](docs/DOCUMENTACION.md). Cambios verificados con pruebas de los módulos (`solicitudes`, `generators`, `db`, formateo de `views_asistente`) y en la app corriendo en el navegador, usando una copia de trabajo de la base real y limpiando los registros de prueba al terminar.

## 2026-08-24 — Inicio y build del MVP local

Se relevó el brief (`Plantilla_Proyecto_FileCenterDP.docx`), los archivos maestros (`MaestroDP.xlsx`, `MaestroPMC.xlsx`) y los ejemplos reales de `Ejemplos/`. Se descartó usar la base Postgres del proyecto de Reposición como fuente de datos: se confirmó que los maestros siguen siendo Excel en la carpeta raíz.

Decisiones tomadas con el usuario:
- Login simple desde el MVP (no se pospone a la fase compartida).
- Numeración de solicitud correlativa y global entre los 4 tipos (ODC/ODR/CDP/FDP).
- Nombre de archivo de salida: `TIPO + Comitente + #Solicitud + Fecha`.
- Despliegue compartido (F3) queda pendiente de definición; este build cubre solo el MVP local.

Se construyó el MVP completo:
- Backend Python (`app/`) con SQLite (`db/filecenterdp.db`) para solicitudes, ítems, historial de estados, usuarios y cache de maestros.
- Generadores de `.prn` (ODC, ODR, CDP) calibrados **byte a byte** contra los archivos reales de `Ejemplos/` (ancho fijo de 10 caracteres por columna, CRLF).
- Generador de `PMC.xlsx` que cruza MaestroPMC (condiciones del último pedido del comitente) y MaestroDP (marcas de los SKUs).
- Interfaz Streamlit con login, roles (analista/asistente/administrador), carga de solicitudes, descarga en un click (zip con los archivos correspondientes), actualización de estado y dashboard con filtros y trazabilidad.

Se probó de punta a punta (backend y navegador): carga de maestros reales (71.004 SKU y 2.156 pedidos PMC), creación de solicitudes de los 4 tipos, descarga de archivos y actualización de estado, verificando que el `.prn`/`.xlsx` generado coincide exactamente con el formato esperado por el sistema comercial.

### Cómo levantar la app
```
C:\Users\dp887\Desktop\FileCenterDP\.venv\Scripts\python.exe -m streamlit run C:\Users\dp887\Desktop\FileCenterDP\app\main.py
```
El primer usuario que se crea en el login queda como administrador. Desde Administración → Maestros hay que cargar MaestroDP y MaestroPMC antes de cargar solicitudes.

### Oportunidades de mejora (post-MVP)
- Definir destino de despliegue compartido (F3) para que lo use todo el equipo.
- Automatizar la detección de actualización semanal de MaestroDP/MaestroPMC (hoy el refresh es manual).
- Evaluar notificaciones a analistas cuando cambia el estado de una solicitud (hoy solo se ve en el dashboard).
- Revisar si conviene texto libre de "Rubro" para CDP/FDP (hoy solo ODC/ODR lo piden, siguiendo el brief).
- Fases 2 y 3 del brief (mejoras de UI sugeridas por uso real, ChatBot/Agente) quedan fuera de este MVP.
