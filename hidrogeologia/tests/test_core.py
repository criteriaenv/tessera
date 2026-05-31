"""Pruebas del núcleo científico.

Ejecutar con:  python -m pytest -q   (o)   python hidrogeologia/tests/test_core.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from hidrogeologia.core import Capa, ModeloHidrogeologico, SEG_POR_ANIO


def _aprox(a, b, rel=1e-6):
    return abs(a - b) <= rel * max(abs(a), abs(b), 1e-30)


def test_permeabilidad_intrinseca():
    c = Capa("test", espesor_m=1.0, K_m_s=1e-4)
    esperado = 1e-4 * 1.002e-3 / (998.2 * 9.81)
    assert _aprox(c.permeabilidad_intrinseca_m2, esperado)


def test_transmisividad_y_K_equivalente():
    capas = [
        Capa("A", espesor_m=10.0, K_m_s=1e-3),
        Capa("B", espesor_m=10.0, K_m_s=1e-5),
    ]
    m = ModeloHidrogeologico("caso", capas)
    assert _aprox(m.transmisividad_total_m2_s, 1e-3*10 + 1e-5*10)
    assert _aprox(m.K_horizontal_equivalente, (1e-3*10 + 1e-5*10) / 20.0)
    kv = 20.0 / (10.0/1e-3 + 10.0/1e-5)
    assert _aprox(m.K_vertical_equivalente, kv)
    # Kh siempre >= Kv en sistema estratificado
    assert m.K_horizontal_equivalente >= m.K_vertical_equivalente


def test_velocidades_darcy():
    c = Capa("ac", espesor_m=10.0, K_m_s=1e-4, porosidad_eficaz=0.25)
    m = ModeloHidrogeologico("g", [c], gradiente_hidraulico=0.01)
    q = m.velocidad_darcy(c)
    v = m.velocidad_real(c)
    assert _aprox(q, 1e-4 * 0.01)         # q = K*i
    assert _aprox(v, q / 0.25)            # v = q/n_e
    assert v > q                          # velocidad real > Darcy


def test_sin_gradiente_devuelve_none():
    c = Capa("ac", espesor_m=10.0, K_m_s=1e-4)
    m = ModeloHidrogeologico("g", [c])
    assert m.velocidad_darcy(c) is None
    assert m.velocidad_real(c) is None


def test_factor_retardo():
    c = Capa("r", espesor_m=1.0, K_m_s=1e-4, porosidad_eficaz=0.3,
             densidad_seca_kg_m3=1800.0, kd_m3_kg=0.001)
    R = 1.0 + 1800.0 * 0.001 / 0.3
    assert _aprox(c.factor_retardo, R)
    c2 = Capa("c", espesor_m=1.0, K_m_s=1e-4)
    assert _aprox(c2.factor_retardo, 1.0)


def test_desplazamiento_lateral():
    c = Capa("ac", espesor_m=10.0, K_m_s=1e-4, porosidad_eficaz=0.25)
    m = ModeloHidrogeologico("d", [c], gradiente_hidraulico=0.01)
    t = SEG_POR_ANIO  # 1 año
    L = m.desplazamiento_lateral_capa(c, t)
    v = m.velocidad_real(c)
    assert _aprox(float(L), v * t)        # L = v*t (R=1)


def test_ogata_banks_limites():
    import numpy as np
    v, DL = 1e-6, 1e-5
    c0 = ModeloHidrogeologico.ogata_banks(np.array([0.0]), 1e7, v, DL)
    clejos = ModeloHidrogeologico.ogata_banks(np.array([1e6]), 1e7, v, DL)
    assert c0[0] > 0.49
    assert clejos[0] < 0.01


def test_calcular_completo():
    capas = [
        Capa("Arena", espesor_m=10.0, K_m_s=1e-3, porosidad_eficaz=0.25,
             dispersividad_long_m=5.0),
        Capa("Arcilla", espesor_m=5.0, K_m_s=1e-8, porosidad_eficaz=0.45),
    ]
    m = ModeloHidrogeologico("completo", capas, gradiente_hidraulico=0.005,
                             concentracion_fuente=100.0, tiempo_max_anios=10.0)
    res = m.calcular()
    assert res.sistema["n_capas"] == 2
    assert res.desplazamiento_lateral is not None
    assert len(res.desplazamiento_lateral["por_capa"]) == 2
    assert res.transporte["perfiles"] is not None
    # capa de transporte = más transmisiva = Arena (idx 0)
    assert res.transporte["capa"] == "Arena"
    # penacho en planta y en perfil presentes
    assert res.transporte["penacho_2d"] is not None
    assert res.transporte["penacho_perfil"] is not None
    pp = res.transporte["penacho_perfil"]
    assert len(pp["capas"]) == 2
    assert pp["z_m"][-1] == 15.0  # espesor total 10+5


def test_alfa_vertical_por_defecto():
    # α_V por defecto = α_L/100 (Gelhar et al., 1992)
    c = Capa("t", espesor_m=1.0, K_m_s=1e-4, dispersividad_long_m=5.0)
    assert _aprox(c.alfa_V(), 0.05)
    assert _aprox(c.alfa_T(), 0.5)   # α_T por defecto = α_L/10
    c2 = Capa("t2", espesor_m=1.0, K_m_s=1e-4, dispersividad_long_m=5.0,
              dispersividad_vert_m=0.2)
    assert _aprox(c2.alfa_V(), 0.2)  # respeta el valor dado


def test_domenico_perfil_limites():
    import numpy as np
    # En la profundidad de la fuente y x pequeño, C alto; fuera de la fuente, bajo.
    v, aL, aV = 1e-6, 5.0, 0.05
    z = np.array([10.0])     # centro de fuente
    c_centro = ModeloHidrogeologico.domenico_perfil(
        np.array([1.0]), z, 1e8, v, aL, aV, alto_fuente=4.0, z_fuente=10.0)
    c_fuera = ModeloHidrogeologico.domenico_perfil(
        np.array([1.0]), np.array([100.0]), 1e8, v, aL, aV,
        alto_fuente=4.0, z_fuente=10.0)
    assert c_centro[0] > c_fuera[0]
    assert c_fuera[0] < 0.01


def test_calcular_sin_gradiente():
    capas = [Capa("Arena", espesor_m=10.0, K_m_s=1e-3, porosidad_eficaz=0.25)]
    m = ModeloHidrogeologico("sg", capas)  # sin gradiente
    res = m.calcular()
    assert res.desplazamiento_lateral is None
    assert res.transporte["perfiles"] is None
    assert res.sistema["n_capas"] == 1


def test_geo_conversion_wgs84_y_mercator():
    from hidrogeologia.geo import a_lonlat
    # 4326 passthrough
    lon, lat = a_lonlat(-3.7, 40.4, 4326)
    assert _aprox(lon, -3.7) and _aprox(lat, 40.4)
    # 3857 -> WGS84 (ida y vuelta aproximada)
    import math
    R = 6378137.0
    x = -3.7 * math.pi / 180 * R
    y = math.log(math.tan(math.pi/4 + (40.4*math.pi/180)/2)) * R
    lon2, lat2 = a_lonlat(x, y, 3857)
    assert abs(lon2 - (-3.7)) < 1e-4 and abs(lat2 - 40.4) < 1e-4


def test_geo_huella_y_info():
    from hidrogeologia.geo import info_geo
    g = info_geo({"x": -3.7, "y": 40.4, "wkid": 4326}, azimut_flujo_grados=90.0,
                 longitud_penacho_m=1000.0, semiancho_penacho_m=50.0)
    assert g is not None
    assert len(g["huella_penacho"]) == 4
    # rumbo 90° (este): la punta tiene mayor longitud y ~igual latitud
    assert g["punta_penacho"]["lon"] > g["lon"]
    assert abs(g["punta_penacho"]["lat"] - g["lat"]) < 0.01
    # sin penacho
    g2 = info_geo({"x": 0, "y": 0, "wkid": 4326}, 90.0, None, None)
    assert g2["huella_penacho"] is None


def test_extension_longitudinal_autofit():
    # La extensión (umbral 1%) debe superar el avance advectivo v·t y ser finita.
    import numpy as np
    v, D_L, t, R = 1e-6, 1e-5, 1e8, 1.0
    ext = ModeloHidrogeologico.extension_longitudinal(v, D_L, t, R, umbral=0.01)
    avance = v * t / R
    assert ext > avance            # incluye la cola dispersiva
    assert np.isfinite(ext)
    # C/C0 en la extensión debe rondar el umbral (frente del penacho)
    c = float(ModeloHidrogeologico.ogata_banks(np.array([ext]), t, v, D_L, R)[0])
    assert c < 0.05


def test_calcular_con_geo_y_extension():
    capas = [Capa("Arena", espesor_m=10.0, K_m_s=1e-4, porosidad_eficaz=0.25,
                  dispersividad_long_m=5.0)]
    m = ModeloHidrogeologico("geo", capas, gradiente_hidraulico=0.005,
                             tiempo_max_anios=10.0,
                             origen={"x": -3.7, "y": 40.4, "wkid": 4326},
                             azimut_flujo_grados=45.0, basemap="imagen")
    res = m.calcular()
    assert res.geo is not None
    assert res.geo["basemap"] == "imagen"
    assert _aprox(res.geo["lon"], -3.7) and _aprox(res.geo["lat"], 40.4)
    assert "extension_penacho_m" in res.transporte
    assert res.geo["huella_penacho"] is not None


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    fallos = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS  {fn.__name__}")
        except AssertionError as e:
            fallos += 1
            print(f"FAIL  {fn.__name__}: {e}")
    print(f"\n{len(fns)-fallos}/{len(fns)} pruebas superadas")
    sys.exit(1 if fallos else 0)
