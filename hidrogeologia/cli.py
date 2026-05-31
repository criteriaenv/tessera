"""Interfaz de línea de comandos.

Uso:
    python -m hidrogeologia                       # usa el ejemplo incorporado
    python -m hidrogeologia caso.json             # carga un caso desde JSON
    python -m hidrogeologia caso.json -o salidas  # define carpeta de salida

Genera tres salidas:
    * informe HTML interactivo
    * informe técnico PDF
    * artefacto de resultados en JSON
"""
from __future__ import annotations

import argparse
import json
import os
import sys

from .core import ModeloHidrogeologico
from .html_report import generar_html
from .pdf_report import generar_pdf


EJEMPLO = {
    "nombre": "Emplazamiento industrial — vertido de tricloroetileno (TCE)",
    "descripcion": (
        "Acuífero detrítico multicapa bajo un antiguo emplazamiento industrial. "
        "Se evalúa el tránsito de un disolvente clorado desde una fuente "
        "continua hacia un pozo de abastecimiento situado aguas abajo."
    ),
    "gradiente_hidraulico": 0.008,
    "concentracion_fuente": 500.0,
    "tiempo_max_anios": 20.0,
    "capas": [
        {"nombre": "Relleno antrópico", "espesor_m": 3.0, "K_m_s": 5e-5,
         "porosidad_eficaz": 0.30, "dispersividad_long_m": 2.0, "color": "#8d6e63"},
        {"nombre": "Arena fina limosa", "espesor_m": 6.0, "K_m_s": 8e-5,
         "porosidad_eficaz": 0.28, "dispersividad_long_m": 3.0, "color": "#ffb74d"},
        {"nombre": "Grava arenosa (acuífero)", "espesor_m": 8.0, "K_m_s": 2e-3,
         "porosidad_eficaz": 0.22, "dispersividad_long_m": 5.0,
         "densidad_seca_kg_m3": 1700.0, "kd_m3_kg": 0.00012, "color": "#4fc3f7"},
        {"nombre": "Arcilla limosa (acuitardo)", "espesor_m": 5.0, "K_m_s": 1e-8,
         "porosidad_eficaz": 0.45, "dispersividad_long_m": 1.0, "color": "#7986cb"},
    ],
}


def main(argv=None):
    pa = argparse.ArgumentParser(
        prog="hidrogeologia",
        description="Análisis y visualización de tránsito de contaminantes en hidrogeología.",
    )
    pa.add_argument("config", nargs="?", help="Archivo JSON con la definición del caso.")
    pa.add_argument("-o", "--salida", default="salidas", help="Carpeta de salida.")
    pa.add_argument("--prefijo", default=None, help="Prefijo de los archivos de salida.")
    args = pa.parse_args(argv)

    if args.config:
        with open(args.config, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        print(f"· Caso cargado desde {args.config}")
    else:
        cfg = EJEMPLO
        print("· Usando el caso de ejemplo incorporado (TCE en acuífero multicapa)")

    modelo = ModeloHidrogeologico.desde_dict(cfg)
    res = modelo.calcular()

    os.makedirs(args.salida, exist_ok=True)
    pref = args.prefijo or _slug(modelo.nombre)
    ruta_html = os.path.join(args.salida, f"{pref}.html")
    ruta_pdf = os.path.join(args.salida, f"{pref}.pdf")
    ruta_json = os.path.join(args.salida, f"{pref}.json")

    generar_html(modelo, res, ruta_html)
    generar_pdf(modelo, res, ruta_pdf)
    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump(res.a_dict(), f, ensure_ascii=False, indent=2)

    print("\n  Resultados del sistema multicapa")
    s = res.sistema
    print(f"    · Capas:                {s['n_capas']}")
    print(f"    · Espesor total:        {s['espesor_total_m']:.1f} m")
    print(f"    · Transmisividad:       {s['transmisividad_total_m2_dia']:.2f} m²/día")
    print(f"    · Kh / Kv equivalente:  {s['K_horizontal_equivalente_m_s']:.2e} / "
          f"{s['K_vertical_equivalente_m_s']:.2e} m/s")
    print(f"    · Anisotropía Kh/Kv:    {s['relacion_anisotropia']:.1f}")
    if res.desplazamiento_lateral:
        print("\n  Desplazamiento lateral a t_max:")
        for c in res.desplazamiento_lateral["por_capa"]:
            print(f"    · {c['nombre']:<32} {c['desplazamiento_tmax_m']:>10.1f} m")

    print("\n  Salidas generadas:")
    print(f"    · HTML interactivo:  {ruta_html}")
    print(f"    · Informe PDF:       {ruta_pdf}")
    print(f"    · Artefacto JSON:    {ruta_json}")
    return 0


def _slug(texto: str) -> str:
    import re, unicodedata
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    t = re.sub(r"[^a-zA-Z0-9]+", "_", t).strip("_").lower()
    return t[:60] or "hidrogeologia"


if __name__ == "__main__":
    sys.exit(main())
