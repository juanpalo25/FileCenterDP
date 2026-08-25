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
- [ ] **Actualización automática de maestros**: hoy `MaestroDP.xlsx`/`MaestroPMC.xlsx` se recargan con un botón manual en Administración. Si se pudiera detectar la actualización semanal automáticamente, se evitaría que alguien cargue una solicitud con datos viejos.
- [ ] **Notificaciones a analistas**: hoy el único lugar donde se ve un cambio de estado es el Dashboard (hay que entrar a mirarlo). El brief menciona "informando a los analistas" — evaluar si hace falta algo más proactivo (mail, aviso).
- [ ] **Rubro en CDP/FDP**: siguiendo el brief al pie de la letra, esos dos tipos no piden Rubro al cargar (solo ODC/ODR lo piden). Confirmar con el usuario si esto es intencional o conviene agregarlo también ahí.
- [ ] **Recuperar contraseña / gestión de usuarios más robusta**: hoy no hay flujo de "olvidé mi contraseña"; el administrador tiene que recrear el usuario manualmente.

### 4. Fases 2 y 3 del brief (explícitamente fuera de alcance del MVP)
- [ ] Fase 2 del brief: "embellecimiento y nuevas funcionalidades que puedan ser recomendadas por el LLM" — mejoras de UI/UX basadas en uso real.
- [ ] Fase 3 del brief: evaluar un ChatBot o Agente sobre el sistema.

## Cosas a tener en cuenta si se retoma el desarrollo
- El entorno usa un venv propio en `FileCenterDP/.venv` — si se reinstalan dependencias, `pip install` puede fallar por SSL si hay un proxy corporativo interceptando; en ese caso agregar `--trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host pypi.python.org`.
- El formato `.prn` es muy sensible (ancho fijo, CRLF) — cualquier cambio en `app/generators.py` debería re-validarse byte a byte contra los archivos de `Ejemplos/`, no solo "a ojo".
- La base `db/filecenterdp.db` no está versionada ni tiene backups — antes de cualquier cambio de esquema, conviene guardar una copia.
