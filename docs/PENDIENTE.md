# Pendiente — FileCenterDP

> Para retomar este proyecto desde otra sesión: leer primero [DOCUMENTACION.md](DOCUMENTACION.md) (qué es y cómo está armado), [PROGRESO.md](PROGRESO.md) (qué está hecho) y [PLAN_EJECUCION.md](PLAN_EJECUCION.md) (el plan original). Esto es la lista de lo que falta.

## Contexto rápido para quien retome esto
El MVP local de FileCenterDP (Streamlit + SQLite, en `C:\Users\dp887\Desktop\FileCenterDP\app\`) está **construido y probado de punta a punta** (los 4 flujos: ODC, ODR, CDP, FDP), pero **no fue entregado/usado en producción todavía**. Falta la puesta en marcha real con el equipo.

## Pendientes concretos

### 1. Entrega del MVP local (Fase 5 del plan, no ejecutada)
- [ ] Confirmar con Juan Pablo que la app corre bien en su máquina y en la de Santiago (o la que vayan a usar día a día).
- [ ] Capacitación breve a los analistas (cómo cargar una solicitud) y a los asistentes (cómo descargar y actualizar estado).
- [ ] Usarla con datos reales unos días y juntar feedback (qué molesta, qué falta, qué sobra).
- [ ] Ajustar según ese feedback antes de darla por cerrada.

### 2. Despliegue compartido (F3 del brief, sin definir)
El brief pide que en una fase 2 esto se suba "a un repositorio con todas las medidas de seguridad para que accedan todos los miembros del área". Al momento de planificar **no había destino decidido** (¿servidor interno? ¿nube privada? ¿carpeta compartida?). Cuando se decida:
- [ ] Elegir dónde se aloja (afecta si Streamlit alcanza o si conviene migrar a otro framework).
- [ ] Revisar el modelo de autenticación actual (login simple con SQLite) — puede necesitar reforzarse para acceso multiusuario por red.
- [ ] Definir estrategia de backup del `db/filecenterdp.db` (hoy es un solo archivo local, sin backup automático).

### 3. Mejoras identificadas pero no incluidas en el MVP
- [ ] **Actualización automática de maestros**: hoy `MaestroDP.xlsx` se recarga con un botón manual en Administración. Si se pudiera detectar la actualización semanal automáticamente, se evitaría que alguien cargue una solicitud con datos viejos.
- [ ] **Notificaciones a analistas**: hoy el único lugar donde se ve un cambio de estado es el Dashboard (hay que entrar a mirarlo). El brief menciona "informando a los analistas" — evaluar si hace falta algo más proactivo (mail, aviso).
- [ ] **Rubro en CDP/FDP**: siguiendo el brief al pie de la letra, esos dos tipos no piden Rubro al cargar (solo ODC/ODR lo piden). Confirmar con el usuario si esto es intencional o conviene agregarlo también ahí.
- [ ] **Recuperar contraseña / gestión de usuarios más robusta**: hoy no hay flujo de "olvidé mi contraseña"; el administrador tiene que recrear el usuario manualmente.

### 4. Fases 2 y 3 del brief (explícitamente fuera de alcance del MVP)
- [ ] Fase 2 del brief: "embellecimiento y nuevas funcionalidades que puedan ser recomendadas por el LLM" — mejoras de UI/UX basadas en uso real.
- [ ] Fase 3 del brief: evaluar un ChatBot o Agente sobre el sistema.

### 5. Mejoras de la revisión de usabilidad (2026-09-14)

Se hizo una revisión de punta a punta de la app y se armó un reporte de 17 hallazgos ordenados por gravedad (detalle completo en la bitácora del 2026-09-14 y en la conversación donde se generó). Ya resueltos: validación numérica de la plantilla, redondeo en vez de truncado en el `.prn`, confirmación al borrar un usuario, y anti-duplicado al cargar una solicitud — ver [bitacora.md](../bitacora.md).

Queda pendiente, en orden sugerido:

- [ ] **Anular/editar una solicitud ya cargada** (el hallazgo más grande, deliberadamente pospuesto). Hoy no existe ninguna forma de corregir un error de carga (SKU, cantidad, comitente) ni de anular una solicitud emitida por error. Antes de encararlo hay que definir con el usuario:
  - Quién puede anular (¿el mismo analista que la cargó? ¿solo administrador?) y desde qué estados (¿solo Cargado (pendiente)? ¿también Emitido/Aplicado?).
  - Si hace falta un estado nuevo (`Anulada`) y si debe quedar visible en el dashboard/historial o desaparecer de las vistas activas.
  - Cómo impacta al presupuesto PMC: si se anula una ODC que ya estaba Emitida y ya había descontado presupuesto, ¿el sistema debería devolver automáticamente ese monto al saldo del rubro, o se sigue corrigiendo a mano como hasta ahora?
- [ ] Sin previsualización de los ítems parseados antes de confirmar la carga (en los 4 tipos) — a diferencia de la pantalla del asistente, que sí muestra una tabla antes de actuar.
- [ ] Comitente/Rubro/Prioridad arrancan con un valor por default (el primero alfabético, o "alta" en Prioridad) en vez de un placeholder vacío — fácil pasar por alto y cargar con el valor equivocado.
- [ ] La columna "DIF vs Maestro" en la previsualización del asistente puede mostrar "-0,00" en rojo por redondeo de punto flotante, aunque la diferencia real sea cero (la tolerancia de $1 que ya tiene la alerta de carga no se aplicó a esta columna).
- [ ] El campo de presupuesto PMC (Administración → PMC) no muestra separador de miles mientras se tipea — en montos de 7-8 cifras es fácil equivocarse un cero.
- [ ] `fecha_vigencia` de CDP se pide al cargar pero no se muestra en ningún lado después (ni en la previsualización del asistente, ni en el Dashboard, ni en la trazabilidad).
- [ ] El Dashboard no muestra la columna Marca en la tabla principal de solicitudes, pese a que ahora define en qué solicitud separada quedó cada línea de una ODC.
- [ ] No hay forma de anticipar, antes de emitir una ODC, cuánto va a consumir del presupuesto PMC de su rubro ni cuál quedaría el saldo.
- [ ] Rubro en CDP/FDP (ya estaba anotado más arriba, sigue sin resolver).
- [ ] Sin tests automatizados (decisión consciente, pero unos tests unitarios de `solicitudes.py`/`generators.py`/`presupuestos.py` cubrirían la parte más frágil con poco esfuerzo).
- [ ] SQLite con una conexión por operación: si el despliegue compartido (F3) termina siendo varios analistas escribiendo a la vez, pueden aparecer errores de "database is locked".
- [ ] `resumen_pmc()` solo muestra los rubros que existen hoy en MaestroDP — si un rubro se renombra o desaparece del maestro, el presupuesto histórico cargado para ese rubro queda invisible en el Dashboard (sigue en la tabla, pero nadie lo ve).
- [ ] `views_admin.py` solo atrapa `FileNotFoundError` al actualizar MaestroDP — si el Excel cambia de layout, la actualización también va a crashear con un traceback crudo.

## Cosas a tener en cuenta si se retoma el desarrollo
- El entorno usa un venv propio en `FileCenterDP/.venv` — si se reinstalan dependencias, `pip install` puede fallar por SSL si hay un proxy corporativo interceptando; en ese caso agregar `--trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host pypi.python.org`.
- El formato `.prn` es muy sensible (ancho fijo, CRLF) — cualquier cambio en `app/generators.py` debería re-validarse byte a byte contra los archivos de `Ejemplos/`, no solo "a ojo".
- La base `db/filecenterdp.db` no está versionada ni tiene backups — antes de cualquier cambio de esquema, conviene guardar una copia.
