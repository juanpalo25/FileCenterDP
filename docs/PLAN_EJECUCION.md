# Plan de ejecución — FileCenterDP

> Este es el plan que se acordó con el usuario y se usó para construir el MVP (definido el 24-08-2026, antes de empezar a programar). Para ver qué de este plan ya está hecho, ver [PROGRESO.md](PROGRESO.md). Para el detalle técnico de lo que quedó construido, ver [DOCUMENTACION.md](DOCUMENTACION.md).

## Contexto

El área Asistencia Comercial (retail aeroportuario) hoy comparte por WhatsApp los archivos con los que los analistas piden a los asistentes que carguen Órdenes de Compra (ODC), Órdenes de Reposición (ODR), Cambios de Precio (CDP) y Fichas de Producto (FDP) en el sistema comercial externo. Eso genera pérdida de seguimiento, errores y olvidos. El objetivo es un sistema propio que centralice la carga de solicitudes, genere automáticamente los archivos que el sistema comercial necesita (.prn / PMC.xlsx), y deje trazabilidad completa de cada solicitud vía un dashboard. Fecha límite de MVP: **15-09-2026** (~3 semanas desde el inicio, 24-08-2026).

Fuentes revisadas antes de planificar: `Plantilla_Proyecto_FileCenterDP.docx` (brief), `MaestroDP.xlsx` (~71.000 SKU, actualizado semanalmente), `MaestroPMC.xlsx` (~2.150 pedidos de presupuesto históricos), y los archivos reales de `Ejemplos/` (plantillas y `.prn` de salida). Se verificó además la base Postgres del proyecto de Reposición (`marts.dim_producto`, `core.stock`, `core.ventas`) como posible fuente de datos maestros — **se descartó**: el usuario confirmó que MaestroDP y MaestroPMC se mantienen como Excel en la carpeta raíz del proyecto, no desde esa base.

### Decisiones acordadas con el usuario antes de construir
- **Autenticación:** login simple desde el MVP (usuario/contraseña), no se pospone a la fase compartida.
- **Numeración de solicitud:** correlativo global único entre los 4 tipos (ODC/ODR/CDP/FDP), tal como sugiere el modelo de datos del brief (#0001, #0002, #0003…).
- **Nombre de archivo de salida:** `TIPO + Comitente + #Solicitud + Fecha` (ej. `ODC Gudys #0012 14-08-2026.prn`), siguiendo la especificación del brief aunque los ejemplos reales no incluían el número.
- **Despliegue compartido (F3):** no definido al momento de planificar dónde se aloja; **el plan cubrió solo el MVP local** para Juan Pablo y Santiago. La fase de despliegue compartido se retoma después del MVP, cuando haya destino definido.

## Arquitectura propuesta

| Capa | Elección | Por qué |
|---|---|---|
| Lenguaje | Python 3.11 | Ya instalado en el entorno; manejo maduro de Excel (`openpyxl`) y archivos de ancho fijo |
| Persistencia operativa | SQLite | Cero instalación, un solo archivo, encaja con "primero de forma local"; mismo patrón que el proyecto de Recuperos de Promociones del usuario |
| Datos maestros | Lectura directa de `MaestroDP.xlsx` / `MaestroPMC.xlsx` en la carpeta raíz, cacheados en SQLite con botón manual "Actualizar maestros" (se actualizan semanalmente y no hay trigger automático confiable) | Evita depender de una integración externa que no existe hoy |
| Frontend / Dashboard | Streamlit | Permite formularios, tablas y dashboard funcional en pocos días; soporta login básico (contraseñas hasheadas) — ajustado al plazo de 3 semanas |
| Generación de archivos | `.prn` de ancho fijo (writer propio, calibrado byte a byte contra los ejemplos reales) + `PMC.xlsx` vía `openpyxl` cruzando Comitente↔MaestroPMC y SKU↔MaestroDP | Debe calzar exactamente con lo que hoy carga el sistema comercial |
| Despliegue | Local (`streamlit run`) en la máquina del usuario para el MVP | F3 (compartido) queda pendiente de definición |

## Modelo de datos (SQLite)

- **usuarios**: id, nombre, rol (`analista` / `asistente` / `administrador`), password_hash
- **solicitudes**: id (#0001 correlativo global), tipo (ODC/ODR/CDP/FDP), comitente, rubro, prioridad, fecha_creacion, estado (`Cargado (pendiente)` / `Emitido` / `Aplicado`), fecha_emision, referencia_externa (nro. ODC/ODR/Lote), archivo_origen
- **solicitud_items**: solicitud_id (FK), sku, cantidad, costo_actualizado, pvp, costo — columnas nullable según tipo
- **historial_estados**: solicitud_id (FK), estado, fecha, usuario — soporta la trazabilidad
- **maestro_dp_cache / maestro_pmc_cache**: snapshot de los Excel, con timestamp de última carga

## Flujos funcionales planeados (uno por tipo, según brief §6.2)

1. **Carga de solicitud (Analista):** elige tipo → sube plantilla Excel (SKU/Cantidad[/Costo]) → completa Comitente y Rubro (autocompletados desde MaestroDP) y Prioridad → valida campos obligatorios → sistema asigna # solicitud global y estado `Cargado (pendiente)` → aparece en el dashboard.
2. **Validación cruzada de costo (solo ODC):** compara `Costo_actualizado` de la plantilla contra `Costo Ppal` de MaestroDP por SKU y resalta diferencias para que el asistente las revise antes de emitir.
3. **Descarga (Asistente), un botón por solicitud:**
   - ODC → `PMC.xlsx` (cruza MaestroPMC + MaestroDP) + `ODC…prn`
   - ODR → `ODR…prn`
   - CDP → `CDP…prn`
   - FDP → copia del archivo tal cual lo subió el analista, renombrado
4. **Actualización de estado (Asistente):** carga el nro. de ODC/ODR/Lote que devolvió el sistema comercial → estado pasa a `Emitido`/`Aplicado` (verde) con fecha → dashboard y trazabilidad se actualizan.
5. **Dashboard:** pendientes por tipo/comitente/rubro/prioridad/estado, indicadores generales e historial completo por solicitud.

Permisos por rol: Analista carga solicitudes y consulta estado; Asistente descarga archivos y actualiza estados; Administrador tiene ambos permisos + gestión de usuarios.

## Cronograma planeado (24-08 → 15-09-2026)

**Fase 0 — Setup (día 1-2):** estructura del proyecto, esquema SQLite inicial, mapeo exacto de columnas de MaestroDP/MaestroPMC, calibración de anchos de columna de los `.prn` de ejemplo.

**Fase 1 — Núcleo de datos y lógica (día 3-7):** cargador de maestros con refresh manual; generador de # solicitud correlativo; validaciones; generadores de `.prn` y `PMC.xlsx`.

**Fase 2 — Interfaz Analista (día 6-9):** login y roles; formulario de carga por tipo; alerta visual de diferencia de costo en ODC.

**Fase 3 — Interfaz Asistente + Dashboard (día 9-13):** vista de pendientes con descarga en un click; actualización de estado; dashboard con filtros, indicadores y trazabilidad.

**Fase 4 — Endurecimiento y pruebas (día 13-16):** pruebas end-to-end con archivos reales; comparación byte a byte; manejo de errores; bitácora del proyecto.

**Fase 5 — Entrega MVP local (día 17-19):** instalación en la máquina de Juan Pablo/Santiago, capacitación breve, ajustes por feedback inicial.

**Post-MVP (fuera de este plan):** definir destino de despliegue compartido (F3) y ejecutarlo; mejoras de UI sugeridas por uso real; evaluar ChatBot/Agente (fases 2 y 3 del brief).

## Riesgos y supuestos identificados al planificar
- El plazo era ajustado (~3 semanas); si aparecían bloqueos, el primer candidato a recortar era la robustez del flujo FDP (el más simple: solo renombrar y trazar), no ODC/ODR/CDP.
- El brief no completaba "Restricciones" (técnicas/tiempo/presupuesto/regulatorias) ni FX2/FX3 — se asumió que no había restricciones adicionales más allá del plazo.
- MaestroDP/MaestroPMC seguirían siendo Excel actualizados manualmente — el refresh es manual, no automático.

## Verificación planeada
- Levantar la app localmente y recorrer los 4 flujos completos usando los archivos reales de `Ejemplos/`.
- Comparar cada `.prn` generado contra el archivo de ejemplo correspondiente para validar formato de ancho fijo.
- Verificar que el dashboard refleje correctamente cada cambio de estado y que la trazabilidad quede completa.
- Verificar login y permisos por rol.
