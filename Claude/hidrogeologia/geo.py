"""Georreferenciación: punto de origen, sistema de referencia (WKID) y
geometría del penacho para su representación en mapa.

El usuario indica el **punto de origen** de los datos en el sistema de
coordenadas que elija mediante su **WKID** (Well-Known ID de ESRI/EPSG, p. ej.
4326 = WGS84 lon/lat, 3857 = Web Mercator, 25830 = ETRS89 UTM 30N…). Este
módulo convierte ese origen a longitud/latitud (WGS84) para poder centrar un
mapa interactivo (Leaflet) y proyectar sobre él la huella del penacho.

La conversión usa ``pyproj`` cuando está disponible (cualquier EPSG); si no lo
está, se resuelven en Python puro los casos más habituales (4326 y 3857).
"""
from __future__ import annotations

import math
from typing import Dict, Any, Optional, Tuple, List

# Catálogo curado de WKID frecuentes (el usuario puede introducir cualquier otro).
WKID_CATALOGO = [
    {"wkid": 4326, "nombre": "WGS 84 (longitud/latitud)", "unidad": "grados"},
    {"wkid": 3857, "nombre": "WGS 84 / Web Mercator", "unidad": "m"},
    {"wkid": 25829, "nombre": "ETRS89 / UTM 29N (Iberia O)", "unidad": "m"},
    {"wkid": 25830, "nombre": "ETRS89 / UTM 30N (Iberia C)", "unidad": "m"},
    {"wkid": 25831, "nombre": "ETRS89 / UTM 31N (Iberia E)", "unidad": "m"},
    {"wkid": 23030, "nombre": "ED50 / UTM 30N", "unidad": "m"},
    {"wkid": 32630, "nombre": "WGS 84 / UTM 30N", "unidad": "m"},
    {"wkid": 32631, "nombre": "WGS 84 / UTM 31N", "unidad": "m"},
    {"wkid": 32719, "nombre": "WGS 84 / UTM 19S (Chile/Perú)", "unidad": "m"},
    {"wkid": 32718, "nombre": "WGS 84 / UTM 18S", "unidad": "m"},
    {"wkid": 27700, "nombre": "OSGB36 / British National Grid", "unidad": "m"},
    {"wkid": 2154, "nombre": "RGF93 / Lambert-93 (Francia)", "unidad": "m"},
    {"wkid": 5070, "nombre": "NAD83 / Conus Albers (EE. UU.)", "unidad": "m"},
    {"wkid": 26910, "nombre": "NAD83 / UTM 10N (California)", "unidad": "m"},
]

# Mapas base estándar para el visor (capas de teselas XYZ).
BASEMAPS = {
    "topografia": {
        "etiqueta": "Topografía",
        "url": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
        "atribucion": "Esri — World Topographic Map",
    },
    "imagen": {
        "etiqueta": "Imagen (satélite)",
        "url": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        "atribucion": "Esri — World Imagery",
    },
    "mapa": {
        "etiqueta": "Mapa (calles)",
        "url": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        "atribucion": "© OpenStreetMap contributors",
    },
}

RADIO_TIERRA_M = 6378137.0


def nombre_wkid(wkid: int) -> str:
    for w in WKID_CATALOGO:
        if w["wkid"] == wkid:
            return w["nombre"]
    return f"EPSG:{wkid}"


def a_lonlat(x: float, y: float, wkid: int) -> Tuple[float, float]:
    """Convierte (x, y) en el sistema ``wkid`` a (longitud, latitud) WGS84.

    Devuelve (lon, lat) en grados. Usa pyproj si está disponible; en su
    defecto resuelve 4326 (passthrough) y 3857 (Web Mercator) en Python puro.
    """
    if wkid == 4326:
        return float(x), float(y)
    if wkid == 3857:
        lon = (x / RADIO_TIERRA_M) * 180.0 / math.pi
        lat = (2.0 * math.atan(math.exp(y / RADIO_TIERRA_M)) - math.pi / 2.0) * 180.0 / math.pi
        return lon, lat
    # Cualquier otro EPSG: requiere pyproj.
    try:
        from pyproj import Transformer
        tr = Transformer.from_crs(int(wkid), 4326, always_xy=True)
        lon, lat = tr.transform(x, y)
        return float(lon), float(lat)
    except Exception as e:  # pyproj ausente o WKID no resoluble
        raise ValueError(
            f"No se pudo convertir el origen desde EPSG:{wkid} a WGS84. "
            f"Instala pyproj o usa WKID 4326/3857. Detalle: {e}"
        )


def destino_geodesico(lon: float, lat: float, azimut_deg: float, dist_m: float) -> Tuple[float, float]:
    """Punto destino a ``dist_m`` y rumbo ``azimut_deg`` (0=N, 90=E) desde
    (lon, lat). Fórmula esférica directa (suficiente a escala de emplazamiento).
    """
    R = RADIO_TIERRA_M
    az = math.radians(azimut_deg)
    lat1 = math.radians(lat)
    lon1 = math.radians(lon)
    dr = dist_m / R
    lat2 = math.asin(math.sin(lat1) * math.cos(dr) +
                     math.cos(lat1) * math.sin(dr) * math.cos(az))
    lon2 = lon1 + math.atan2(math.sin(az) * math.sin(dr) * math.cos(lat1),
                             math.cos(dr) - math.sin(lat1) * math.sin(lat2))
    return math.degrees(lon2), math.degrees(lat2)


def huella_penacho(lon: float, lat: float, azimut_deg: float,
                   longitud_m: float, semiancho_m: float) -> List[List[float]]:
    """Polígono (lista de [lat, lon]) que aproxima la huella del penacho en
    planta: un rectángulo desde el origen a lo largo del azimut de flujo, de
    longitud ``longitud_m`` y semianchura ``semiancho_m``.
    """
    # Esquinas en el sistema local (a lo largo y perpendicular al flujo).
    perp = azimut_deg + 90.0
    # origen ± semiancho
    o_izq = destino_geodesico(lon, lat, perp, semiancho_m)
    o_der = destino_geodesico(lon, lat, perp - 180.0, semiancho_m)
    # punta del penacho ± semiancho
    punta_lon, punta_lat = destino_geodesico(lon, lat, azimut_deg, longitud_m)
    p_izq = destino_geodesico(punta_lon, punta_lat, perp, semiancho_m)
    p_der = destino_geodesico(punta_lon, punta_lat, perp - 180.0, semiancho_m)
    # Orden: o_izq -> p_izq -> p_der -> o_der  ([lat, lon] para Leaflet)
    return [[o_izq[1], o_izq[0]], [p_izq[1], p_izq[0]],
            [p_der[1], p_der[0]], [o_der[1], o_der[0]]]


def _deg2tile(lon: float, lat: float, z: int) -> Tuple[float, float]:
    """Coordenadas de tesela (fraccionarias) XYZ para (lon, lat) y zoom z."""
    lat_r = math.radians(lat)
    n = 2.0 ** z
    xt = (lon + 180.0) / 360.0 * n
    yt = (1.0 - math.asinh(math.tan(lat_r)) / math.pi) / 2.0 * n
    return xt, yt


def _tile2deg(xt: float, yt: float, z: int) -> Tuple[float, float]:
    n = 2.0 ** z
    lon = xt / n * 360.0 - 180.0
    lat = math.degrees(math.atan(math.sinh(math.pi * (1.0 - 2.0 * yt / n))))
    return lon, lat


def stitch_basemap(lon: float, lat: float, z: int, basemap: str = "topografia",
                   n_tiles: int = 3, timeout: float = 6.0):
    """Descarga y compone un mosaico de teselas (n_tiles × n_tiles) centrado en
    (lon, lat). Devuelve ``(imagen_PIL, extent)`` donde ``extent`` = (lon_min,
    lon_max, lat_min, lat_max), o ``None`` si no hay red/teselas disponibles.

    Pensado para incrustar un mapa estático en el informe PDF. Si no hay acceso
    a internet en el momento de generar el informe, el llamador debe ofrecer una
    alternativa esquemática.
    """
    try:
        import io
        import urllib.request
        from PIL import Image
    except Exception:
        return None
    bm = BASEMAPS.get(basemap, BASEMAPS["topografia"])
    plantilla = bm["url"]
    xt, yt = _deg2tile(lon, lat, z)
    xc, yc = int(math.floor(xt)), int(math.floor(yt))
    media = n_tiles // 2
    TS = 256
    mosaico = Image.new("RGB", (TS * n_tiles, TS * n_tiles), (230, 230, 230))
    exito = False
    for i in range(n_tiles):
        for j in range(n_tiles):
            tx, ty = xc - media + i, yc - media + j
            url = plantilla.format(z=z, x=tx, y=ty)
            try:
                req = urllib.request.Request(url, headers={
                    "User-Agent": "hidrogeologia/1.0 (informe PDF; investigación)"})
                datos = urllib.request.urlopen(req, timeout=timeout).read()
                tile = Image.open(io.BytesIO(datos)).convert("RGB")
                mosaico.paste(tile, (i * TS, j * TS))
                exito = True
            except Exception:
                continue
    if not exito:
        return None
    lon_min, lat_max = _tile2deg(xc - media, yc - media, z)
    lon_max, lat_min = _tile2deg(xc - media + n_tiles, yc - media + n_tiles, z)
    return mosaico, (lon_min, lon_max, lat_min, lat_max)


def zoom_para_extension(longitud_m: float) -> int:
    """Elige un nivel de zoom XYZ razonable para abarcar una huella de penacho
    de ``longitud_m`` metros (mosaico de ~3 teselas)."""
    if longitud_m <= 0:
        return 15
    # Ancho objetivo ≈ 2.5× la longitud; metros por tesela ≈ 156543·cos(lat)/2^z.
    objetivo = max(longitud_m * 2.5, 200.0)
    for z in range(19, 2, -1):
        metros_mosaico = 3 * 156543.03 / (2 ** z)  # aprox. a lat 0; conservador
        if metros_mosaico >= objetivo:
            return z
    # Penacho enorme: ni el zoom más bajo del bucle lo abarca → vista más amplia.
    return 3


def info_geo(origen: Optional[Dict[str, Any]], azimut_flujo_grados: float,
             longitud_penacho_m: Optional[float],
             semiancho_penacho_m: Optional[float],
             basemap: str = "topografia") -> Optional[Dict[str, Any]]:
    """Construye el bloque de georreferenciación para los resultados.

    ``origen`` = {"x": ..., "y": ..., "wkid": ...} o None (sin georreferencia).
    """
    if not origen:
        return None
    x = float(origen["x"]); y = float(origen["y"])
    wkid = int(origen.get("wkid", 4326))
    lon, lat = a_lonlat(x, y, wkid)
    info: Dict[str, Any] = {
        "origen_x": x, "origen_y": y, "wkid": wkid,
        "wkid_nombre": nombre_wkid(wkid),
        "lon": lon, "lat": lat,
        "azimut_flujo_grados": azimut_flujo_grados,
        "basemap": basemap if basemap in BASEMAPS else "topografia",
        "basemaps": BASEMAPS,
        "huella_penacho": None,
        "punta_penacho": None,
    }
    if longitud_penacho_m and longitud_penacho_m > 0:
        semi = semiancho_penacho_m or max(longitud_penacho_m * 0.05, 1.0)
        info["huella_penacho"] = huella_penacho(lon, lat, azimut_flujo_grados,
                                                longitud_penacho_m, semi)
        plon, plat = destino_geodesico(lon, lat, azimut_flujo_grados, longitud_penacho_m)
        info["punta_penacho"] = {"lon": plon, "lat": plat,
                                 "longitud_m": longitud_penacho_m}
    return info
