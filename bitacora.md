# Bitácora del proyecto FileCenterDP

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
