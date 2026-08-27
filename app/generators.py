import io
import re
import zipfile
from datetime import date

_INVALID_FILENAME_CHARS = re.compile(r'[\\/:*?"<>|]')


def format_solicitud_id(solicitud_id: int) -> str:
    return f"#{solicitud_id:04d}"


def _sanitizar(texto: str) -> str:
    return _INVALID_FILENAME_CHARS.sub("", texto).strip()


def nombre_archivo(tipo: str, comitente: str, solicitud_id: int, extension: str, fecha: date = None) -> str:
    fecha = fecha or date.today()
    partes = [tipo, _sanitizar(comitente), format_solicitud_id(solicitud_id), fecha.strftime("%d-%m-%Y")]
    return " ".join(partes) + f".{extension.lstrip('.')}"


def _campo(valor, ancho: int, decimales: int = 0) -> str:
    """Formatea un valor numérico justificado a la derecha en un campo de ancho fijo.
    Si valor es None, devuelve el campo en blanco (mismo ancho)."""
    if valor is None:
        return " " * ancho
    if decimales:
        texto = f"{float(valor):.{decimales}f}"
    else:
        texto = str(int(valor))
    return texto.rjust(ancho)


def generar_odc_odr_prn(items: list[dict]) -> bytes:
    """items: [{'sku': int, 'cantidad': number}, ...]. Formato: SKU(10) + Cantidad(10), CRLF."""
    lineas = [_campo(it["sku"], 10) + _campo(it["cantidad"], 10) for it in items]
    contenido = "\r\n".join(lineas) + "\r\n"
    return contenido.encode("latin-1")


def generar_cdp_prn(items: list[dict]) -> bytes:
    """items: [{'sku': int, 'pvp': number, 'costo': number|None}, ...].
    Formato: SKU(10) + PVP(10, entero) + Costo(10, 2 decimales), CRLF."""
    lineas = [
        _campo(it["sku"], 10) + _campo(it["pvp"], 10) + _campo(it.get("costo"), 10, decimales=2)
        for it in items
    ]
    contenido = "\r\n".join(lineas) + "\r\n"
    return contenido.encode("latin-1")


def generar_fdp_output(archivo_original: bytes) -> bytes:
    """FDP se entrega tal cual lo subió el analista, solo se renombra al descargar."""
    return archivo_original


def _extension_original(nombre_archivo_original: str) -> str:
    return nombre_archivo_original.rsplit(".", 1)[-1] if "." in nombre_archivo_original else "xlsx"


def generar_archivos_solicitud(solicitud: dict) -> list[tuple[str, bytes]]:
    """Genera el/los archivo(s) de salida de una solicitud (nombre, contenido)."""
    tipo = solicitud["tipo"]
    comitente = solicitud["comitente"]
    solicitud_id = solicitud["id"]
    items = solicitud["items"]

    archivos: list[tuple[str, bytes]] = []

    if tipo == "ODC":
        odc_items = [{"sku": it["sku"], "cantidad": it["cantidad"]} for it in items]
        odc_bytes = generar_odc_odr_prn(odc_items)
        odc_nombre = nombre_archivo("ODC", comitente, solicitud_id, "prn")
        archivos.append((odc_nombre, odc_bytes))

    elif tipo == "ODR":
        odr_items = [{"sku": it["sku"], "cantidad": it["cantidad"]} for it in items]
        odr_bytes = generar_odc_odr_prn(odr_items)
        odr_nombre = nombre_archivo("ODR", comitente, solicitud_id, "prn")
        archivos.append((odr_nombre, odr_bytes))

    elif tipo == "CDP":
        cdp_items = [{"sku": it["sku"], "pvp": it["pvp"], "costo": it["costo"]} for it in items]
        cdp_bytes = generar_cdp_prn(cdp_items)
        cdp_nombre = nombre_archivo("CDP", comitente, solicitud_id, "prn")
        archivos.append((cdp_nombre, cdp_bytes))

    elif tipo == "FDP":
        ext = _extension_original(solicitud["archivo_origen_nombre"])
        fdp_bytes = generar_fdp_output(solicitud["archivo_origen_datos"])
        fdp_nombre = nombre_archivo("FDP", comitente, solicitud_id, ext)
        archivos.append((fdp_nombre, fdp_bytes))

    return archivos


def construir_paquete_descarga(solicitud: dict) -> tuple[bytes, str]:
    """Empaqueta el/los archivo(s) de salida de una solicitud en un .zip
    para que el asistente los descargue con un solo botón."""
    archivos = generar_archivos_solicitud(solicitud)

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for nombre, contenido in archivos:
            zf.writestr(nombre, contenido)

    zip_nombre = nombre_archivo(solicitud["tipo"], solicitud["comitente"], solicitud["id"], "zip")
    return buffer.getvalue(), zip_nombre


def construir_paquete_descarga_masiva(solicitudes: list[dict]) -> bytes:
    """Empaqueta en un solo .zip los archivos de salida de varias solicitudes
    (una entrada por cada archivo individual, con el mismo nombre que tendría
    si se descargara solicitud por solicitud)."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for solicitud in solicitudes:
            for nombre, contenido in generar_archivos_solicitud(solicitud):
                zf.writestr(nombre, contenido)
    return buffer.getvalue()
