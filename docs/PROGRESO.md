# Progreso — FileCenterDP

> Última actualización: 2026-09-14. Ver el plan original en [PLAN_EJECUCION.md](PLAN_EJECUCION.md) y el detalle técnico en [DOCUMENTACION.md](DOCUMENTACION.md). Lo que sigue abierto está en [PENDIENTE.md](PENDIENTE.md). El detalle cronológico de cada cambio está en [bitacora.md](../bitacora.md).

## Estado general: MVP local construido y probado ✅, con mejoras post-MVP incorporadas a partir del uso real (ver más abajo) — falta la entrega/capacitación real (Fase 5) y todo lo posterior al MVP

## Avance por fase del plan

| Fase | Descripción | Estado |
|---|---|---|
| Fase 0 | Setup del proyecto, esquema SQLite, calibración de anchos de `.prn` | ✅ Completa |
| Fase 1 | Cargador de maestros, numeración correlativa, validaciones, generadores de archivos | ✅ Completa |
| Fase 2 | Login/roles, formulario de carga de solicitud (Analista) | ✅ Completa |
| Fase 3 | Vista de pendientes/descarga y dashboard (Asistente) | ✅ Completa |
| Fase 4 | Pruebas end-to-end con archivos reales, manejo de errores, bitácora | ✅ Completa |
| Fase 5 | Instalación real en la máquina de Juan Pablo/Santiago, capacitación, feedback inicial | ⬜ Pendiente — requiere acción del usuario, ver [PENDIENTE.md](PENDIENTE.md) |
| Post-MVP | Definir y ejecutar despliegue compartido (F3), mejoras de UI, ChatBot/Agente | ⬜ Pendiente — fuera de alcance del MVP |

## Detalle de lo construido (2026-08-24)

- [x] Estructura de proyecto y entorno Python (venv + dependencias)
- [x] Formato exacto de los `.prn` calibrado byte a byte contra `Ejemplos/`
- [x] Esquema SQLite (usuarios, solicitudes, ítems, historial, cache de maestros)
- [x] Cargador de MaestroDP.xlsx (71.004 filas) y MaestroPMC.xlsx (2.156 filas) a SQLite
- [x] Generadores de `.prn` (ODC/ODR/CDP) y `PMC.xlsx`, empaquetados en `.zip` para descarga en un click
- [x] Login con roles (analista / asistente / administrador) y alta de usuarios
- [x] Formulario de carga de solicitud con autocompletado de Comitente/Rubro y alerta de diferencia de costo en ODC
- [x] Vista de pendientes, descarga de archivos y actualización de estado
- [x] Dashboard con filtros, indicadores y trazabilidad por solicitud
- [x] Pruebas end-to-end de los 4 tipos de solicitud (backend y navegador real)
- [x] Bitácora del proyecto (`bitacora.md`, punto 10 del brief)
- [x] Documentación completa (esta carpeta `docs/`)

## Cambios posteriores al MVP inicial (post 2026-08-24)

El MVP se usó y, a partir de ese uso real, se le agregaron mejoras que no estaban en el plan original. Detalle día a día en [bitacora.md](../bitacora.md); resumen:

**2026-08-27:**
- ODC dividida en una solicitud por marca (columna `Marca` agregada a la plantilla).
- Alerta de diferencia de costo pasó a no bloquear la carga.
- SKU sin separador de miles en las previsualizaciones.
- Se eliminó por completo la funcionalidad PMC original (archivo `PMC.xlsx` cruzando `MaestroPMC.xlsx` + MaestroDP) — decisión del usuario, ya no se usa `MaestroPMC.xlsx`.
- Botón de Descarga Masiva (un `.zip` con todas las pendientes).
- Orden por prioridad en la lista de pendientes.
- Detalle de ítems de ODC ampliado (costo/PVP en vivo contra MaestroDP, diferencia coloreada).

**2026-09-14:**
- La columna `Marca` de ODC pasó a ser opcional: los renglones sin marca se agrupan en una solicitud aparte a nombre del comitente.
- Nueva pestaña **PMC** en Administración: presupuesto mensual por rubro, cargado a mano, descontado en vivo con las ODC Emitidas del mes y visible en el Dashboard (saldo en rojo si es negativo). Sin relación con el PMC original eliminado en agosto — mismo nombre, concepto distinto.
- La alerta de diferencia de costo en ODC dejó de marcar diferencias menores a $1 (redondeo/centavos).

## Qué falta para considerar el proyecto "cerrado" según el brief

1. Instalar/probar la app en la máquina real de uso diario (no solo en esta sesión de desarrollo).
2. Capacitación breve a analistas y asistentes.
3. Una ronda de feedback real de uso y ajustes menores.
4. Definir dónde se aloja la versión compartida (F3) cuando haya destino decidido.

Ver el detalle accionable de cada punto en [PENDIENTE.md](PENDIENTE.md).
