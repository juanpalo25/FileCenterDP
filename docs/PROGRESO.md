# Progreso — FileCenterDP

> Última actualización: 2026-08-24. Ver el plan original en [PLAN_EJECUCION.md](PLAN_EJECUCION.md) y el detalle técnico en [DOCUMENTACION.md](DOCUMENTACION.md). Lo que sigue abierto está en [PENDIENTE.md](PENDIENTE.md).

## Estado general: MVP local construido y probado ✅ — falta la entrega/capacitación real (Fase 5) y todo lo posterior al MVP

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

## Qué falta para considerar el proyecto "cerrado" según el brief

1. Instalar/probar la app en la máquina real de uso diario (no solo en esta sesión de desarrollo).
2. Capacitación breve a analistas y asistentes.
3. Una ronda de feedback real de uso y ajustes menores.
4. Definir dónde se aloja la versión compartida (F3) cuando haya destino decidido.

Ver el detalle accionable de cada punto en [PENDIENTE.md](PENDIENTE.md).
