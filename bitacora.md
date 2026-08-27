# Bitácora del proyecto FileCenterDP

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
