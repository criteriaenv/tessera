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


def test_calcular_sin_gradiente():
    capas = [Capa("Arena", espesor_m=10.0, K_m_s=1e-3, porosidad_eficaz=0.25)]
    m = ModeloHidrogeologico("sg", capas)  # sin gradiente
    res = m.calcular()
    assert res.desplazamiento_lateral is None
    assert res.transporte["perfiles"] is None
    assert res.sistema["n_capas"] == 1


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
