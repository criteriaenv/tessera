"""Genera el notebook de Google Colab (hidrogeologia_colab.ipynb).

Se escribe el .ipynb como JSON (sin depender de nbformat). El notebook reutiliza
el paquete ``hidrogeologia`` clonándolo desde GitHub, y ofrece una interfaz
interactiva con ipywidgets para cargar los insumos (añadir/quitar capas, más
campos de datos), calcular y generar las tres salidas (HTML, PDF, JSON).

Ejecutar:  python hidrogeologia/build_notebook.py
"""
import json
import os

REPO = "https://github.com/criteriaenv/tessera.git"
RAMA = "claude/hydrogeology-contaminant-analysis-J21BH"


def md(texto):
    return {"cell_type": "markdown", "metadata": {}, "source": _src(texto)}


def code(texto):
    return {"cell_type": "code", "metadata": {}, "execution_count": None,
            "outputs": [], "source": _src(texto)}


def _src(texto):
    lineas = texto.split("\n")
    return [l + "\n" for l in lineas[:-1]] + [lineas[-1]]


CELDAS = []

CELDAS.append(md(
"""# 🌊 Hidrogeología — Tránsito de contaminantes (Google Colab)

Análisis y visualización del **tránsito de contaminantes** en un sistema
acuífero **multicapa**: transporte advectivo-dispersivo, penacho en **planta**
y en **perfil vertical**, y **desplazamiento lateral** por gradiente hidráulico.

**Cómo usar este notebook:**
1. Ejecuta la celda **1 (Instalación)**.
2. Ejecuta la celda **2 (Interfaz)**: indica el **punto de origen** (con su
   **WKID**) y el mapa base, añade/quita capas y rellena los datos.
3. Ejecuta la celda **3 (Calcular y visualizar)** y la **3b (Mapa interactivo)**.
4. Ejecuta la celda **4 (Generar y descargar salidas)** para obtener el
   HTML interactivo, el informe PDF y el artefacto JSON.

> Modelo analítico de cribado (Ogata-Banks 1961 / Domenico 1987). No sustituye
> a una modelización numérica ni a la caracterización de campo."""))

CELDAS.append(md("## 1 · Instalación y carga del paquete"))

CELDAS.append(code(
f"""# Clona el repositorio (rama de desarrollo) e instala dependencias.
import os, sys, subprocess

REPO = "{REPO}"
RAMA = "{RAMA}"

if not os.path.isdir("tessera"):
    subprocess.run(["git", "clone", "--depth", "1", "--branch", RAMA, REPO, "tessera"], check=True)

# Dependencias científicas (ya suelen estar en Colab; se asegura su versión).
subprocess.run([sys.executable, "-m", "pip", "install", "-q",
                "numpy", "scipy", "matplotlib", "ipywidgets", "pyproj", "folium"], check=True)

# Hace importable el paquete `hidrogeologia`.
ruta = os.path.abspath("tessera")
if ruta not in sys.path:
    sys.path.insert(0, ruta)

import importlib
import hidrogeologia, hidrogeologia.core, hidrogeologia.pdf_report, hidrogeologia.html_report
importlib.reload(hidrogeologia.core)
print("✓ Paquete hidrogeologia cargado · versión", hidrogeologia.__version__)"""))

CELDAS.append(md(
"""## 2 · Interfaz de carga de insumos (interactiva)

Define los **parámetros globales** y la **lista de capas**. Usa **➕ Añadir capa**
para crear tantas capas como necesites y **✕** para eliminarlas. Cada capa
admite nombre, espesor, permeabilidad K, porosidad eficaz, dispersividades
(α_L, α_V) y, opcionalmente, densidad seca y K_d (retardo por sorción)."""))

CELDAS.append(code(
'''import ipywidgets as W
from IPython.display import display, clear_output

PALETA = ["#8d6e63","#ffb74d","#fff176","#aed581","#4fc3f7","#7986cb","#ba68c8","#f06292"]

# ---- Parámetros globales ----
w_nombre = W.Text(value="Caso de estudio — acuífero multicapa", description="Nombre:",
                  layout=W.Layout(width="98%"), style={"description_width":"110px"})
w_desc   = W.Textarea(value="Emplazamiento con vertido de contaminante hacia aguas abajo.",
                  description="Descripción:", layout=W.Layout(width="98%", height="56px"),
                  style={"description_width":"110px"})
w_grad   = W.FloatText(value=0.008, description="Gradiente i:", style={"description_width":"110px"})
w_c0     = W.FloatText(value=500.0, description="C₀ (mg/L):", style={"description_width":"110px"})
w_tmax   = W.FloatText(value=20.0, description="Tiempo (años):", style={"description_width":"110px"})
w_usargrad = W.Checkbox(value=True, description="Incluir gradiente (transporte + desplazamiento lateral)")

CAPAS_UI = []          # lista de dicts de widgets
caja_capas = W.VBox()  # contenedor dinámico

def _fila_capa(d=None):
    d = d or {}
    i = len(CAPAS_UI)
    color = d.get("color", PALETA[i % len(PALETA)])
    w = {
      "nombre": W.Text(value=d.get("nombre", f"Capa {i+1}"), layout=W.Layout(width="150px")),
      "espesor": W.FloatText(value=d.get("espesor_m", 5.0), layout=W.Layout(width="85px")),
      "K": W.FloatText(value=d.get("K_m_s", 1e-4), layout=W.Layout(width="95px")),
      "ne": W.FloatText(value=d.get("porosidad_eficaz", 0.25), layout=W.Layout(width="70px")),
      "alfaL": W.FloatText(value=d.get("dispersividad_long_m", 1.0), layout=W.Layout(width="70px")),
      "alfaV": W.FloatText(value=d.get("dispersividad_vert_m", 0.01), layout=W.Layout(width="70px")),
      "rho": W.FloatText(value=d.get("densidad_seca_kg_m3", 0.0) or 0.0, layout=W.Layout(width="80px")),
      "kd": W.FloatText(value=d.get("kd_m3_kg", 0.0) or 0.0, layout=W.Layout(width="85px")),
      "color": color,
    }
    btn = W.Button(description="✕", button_style="danger", layout=W.Layout(width="36px"))
    fila = W.HBox([w["nombre"], w["espesor"], w["K"], w["ne"], w["alfaL"],
                   w["alfaV"], w["rho"], w["kd"], btn])
    w["_fila"] = fila
    def quitar(_):
        if len(CAPAS_UI) <= 1: return
        CAPAS_UI.remove(w); _refrescar()
    btn.on_click(quitar)
    CAPAS_UI.append(w)
    return fila

def _refrescar():
    cab = W.HBox([W.HTML(v) for v in [
        "<b style='width:150px;display:inline-block'>Nombre</b>",
        "<b style='width:85px;display:inline-block'>Espesor m</b>",
        "<b style='width:95px;display:inline-block'>K m/s</b>",
        "<b style='width:70px;display:inline-block'>n_e</b>",
        "<b style='width:70px;display:inline-block'>α_L m</b>",
        "<b style='width:70px;display:inline-block'>α_V m</b>",
        "<b style='width:80px;display:inline-block'>ρ_b kg/m³</b>",
        "<b style='width:85px;display:inline-block'>K_d m³/kg</b>"]])
    caja_capas.children = [cab] + [w["_fila"] for w in CAPAS_UI]

def añadir_capa(_=None, d=None):
    _fila_capa(d); _refrescar()

btn_add = W.Button(description="➕ Añadir capa", button_style="success")
btn_add.on_click(lambda b: añadir_capa())

# Capas iniciales de ejemplo (acuífero detrítico multicapa).
for d in [
    {"nombre":"Relleno antrópico","espesor_m":3.0,"K_m_s":5e-5,"porosidad_eficaz":0.30,"dispersividad_long_m":2.0},
    {"nombre":"Arena fina limosa","espesor_m":6.0,"K_m_s":8e-5,"porosidad_eficaz":0.28,"dispersividad_long_m":3.0},
    {"nombre":"Grava arenosa (acuífero)","espesor_m":8.0,"K_m_s":2e-3,"porosidad_eficaz":0.22,
     "dispersividad_long_m":5.0,"densidad_seca_kg_m3":1700.0,"kd_m3_kg":0.00012},
    {"nombre":"Arcilla limosa (acuitardo)","espesor_m":5.0,"K_m_s":1e-8,"porosidad_eficaz":0.45,"dispersividad_long_m":1.0},
]:
    añadir_capa(d=d)

# ---- Ubicación / georreferenciación ----
from hidrogeologia.geo import WKID_CATALOGO, BASEMAPS
w_usargeo = W.Checkbox(value=True, description="Georreferenciar (punto de origen + mapa)")
w_ox = W.FloatText(value=441000.0, description="X / Este:", style={"description_width":"110px"})
w_oy = W.FloatText(value=4474000.0, description="Y / Norte:", style={"description_width":"110px"})
w_wkid = W.Dropdown(options=[(f"{w['wkid']} — {w['nombre']}", w["wkid"]) for w in WKID_CATALOGO],
                    value=25830, description="WKID:", style={"description_width":"110px"},
                    layout=W.Layout(width="360px"))
w_az = W.FloatText(value=115.0, description="Rumbo flujo (°):", style={"description_width":"110px"})
w_base = W.Dropdown(options=[(BASEMAPS[k]["etiqueta"], k) for k in BASEMAPS],
                    value="imagen", description="Mapa base:", style={"description_width":"110px"})

display(W.HTML("<h3>Parámetros globales</h3>"))
display(w_nombre, w_desc, W.HBox([w_grad, w_c0, w_tmax]), w_usargrad)
display(W.HTML("<h3>Ubicación (punto de origen y mapa)</h3>"))
display(w_usargeo, W.HBox([w_ox, w_oy]), W.HBox([w_wkid, w_az]), w_base)
display(W.HTML("<h3>Capas (de techo a muro)</h3>"))
display(caja_capas, btn_add)


def construir_config():
    """Lee los widgets y devuelve el dict de configuración del modelo."""
    capas = []
    for w in CAPAS_UI:
        c = {"nombre": w["nombre"].value, "espesor_m": w["espesor"].value,
             "K_m_s": w["K"].value, "porosidad_eficaz": w["ne"].value,
             "dispersividad_long_m": w["alfaL"].value,
             "dispersividad_vert_m": w["alfaV"].value, "color": w["color"]}
        if w["rho"].value > 0 and w["kd"].value > 0:
            c["densidad_seca_kg_m3"] = w["rho"].value
            c["kd_m3_kg"] = w["kd"].value
        capas.append(c)
    cfg = {
        "nombre": w_nombre.value, "descripcion": w_desc.value,
        "gradiente_hidraulico": (w_grad.value if w_usargrad.value else None),
        "concentracion_fuente": w_c0.value, "tiempo_max_anios": w_tmax.value,
        "capas": capas,
    }
    if w_usargeo.value:
        cfg["origen"] = {"x": w_ox.value, "y": w_oy.value, "wkid": int(w_wkid.value)}
        cfg["azimut_flujo_grados"] = w_az.value
        cfg["basemap"] = w_base.value
    return cfg
print("Interfaz lista. Tras editar, ejecuta la celda 3.")'''))

CELDAS.append(md("## 3 · Calcular y visualizar"))

CELDAS.append(code(
'''import numpy as np
import matplotlib.pyplot as plt
from hidrogeologia.core import ModeloHidrogeologico, SEG_POR_ANIO

cfg = construir_config()
modelo = ModeloHidrogeologico.desde_dict(cfg)
res = modelo.calcular()
s = res.sistema

print(f"Capas: {s['n_capas']}  ·  Espesor total: {s['espesor_total_m']:.1f} m")
print(f"Transmisividad: {s['transmisividad_total_m2_dia']:.2f} m²/día")
print(f"Kh / Kv equiv.: {s['K_horizontal_equivalente_m_s']:.2e} / {s['K_vertical_equivalente_m_s']:.2e} m/s")
print(f"Anisotropía Kh/Kv: {s['relacion_anisotropia']:.1f}")

t = res.transporte
PAL = [w["color"] for w in CAPAS_UI]

# --- Columna estratigráfica ---
fig, ax = plt.subplots(figsize=(3.2, 5))
prof = 0.0
for i, c in enumerate(res.capas):
    ax.add_patch(plt.Rectangle((0, prof), 1, c["espesor_m"], facecolor=PAL[i % len(PAL)], edgecolor="w"))
    ax.text(0.5, prof + c["espesor_m"]/2, c["nombre"], ha="center", va="center", fontsize=8)
    prof += c["espesor_m"]
ax.set_ylim(prof, 0); ax.set_xlim(0, 1); ax.set_xticks([]); ax.set_ylabel("Profundidad (m)")
ax.set_title("Columna hidrogeológica"); plt.tight_layout(); plt.show()

if t.get("perfiles"):
    # --- Perfiles C(x) ---
    fig, ax = plt.subplots(figsize=(9, 3.2))
    x = np.array(t["x_m"]); cmap = plt.cm.viridis
    for i, p in enumerate(t["perfiles"]):
        ax.plot(x, p["C_rel"], color=cmap(i/len(t["perfiles"])), label=f"{p['t_anios']:.1f} a")
    ax.axhline(0.5, color="orange", ls="--", lw=1)
    ax.set_xlabel("Distancia x (m)"); ax.set_ylabel("C/C₀"); ax.legend(fontsize=7, ncol=2)
    ax.set_title("Perfiles de concentración (Ogata-Banks, 1961)"); ax.grid(alpha=0.3)
    plt.tight_layout(); plt.show()

    # --- Penacho en PLANTA y en PERFIL, lado a lado ---
    pen = t["penacho_2d"]; per = t["penacho_perfil"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 3.6))
    im1 = a1.pcolormesh(pen["x_m"], pen["y_m"], np.array(pen["C_rel"]), cmap="turbo", vmin=0, vmax=1, shading="auto")
    a1.contour(pen["x_m"], pen["y_m"], np.array(pen["C_rel"]), levels=[0.05,0.1,0.5], colors="w", linewidths=0.7)
    a1.set_title("Penacho en planta (x–y)"); a1.set_xlabel("x (m)"); a1.set_ylabel("y (m)")
    fig.colorbar(im1, ax=a1, fraction=0.046, label="C/C₀")
    im2 = a2.pcolormesh(per["x_m"], per["z_m"], np.array(per["C_rel"]), cmap="turbo", vmin=0, vmax=1, shading="auto")
    a2.contour(per["x_m"], per["z_m"], np.array(per["C_rel"]), levels=[0.05,0.1,0.5], colors="w", linewidths=0.7)
    for c in per["capas"]:
        a2.axhline(c["muro_m"], color="w", lw=0.5, ls=":", alpha=0.6)
    a2.invert_yaxis(); a2.set_title("Pluma en perfil (x–z)"); a2.set_xlabel("x (m)"); a2.set_ylabel("Profundidad z (m)")
    fig.colorbar(im2, ax=a2, fraction=0.046, label="C/C₀")
    plt.tight_layout(); plt.show()

# --- Desplazamiento lateral por capa ---
if res.desplazamiento_lateral:
    fig, ax = plt.subplots(figsize=(9, 3.4))
    for i, c in enumerate(res.desplazamiento_lateral["por_capa"]):
        ax.plot(c["curva"]["t_anios"], c["curva"]["L_m"], color=PAL[i % len(PAL)], lw=2, label=c["nombre"])
    ax.set_xlabel("Tiempo (años)"); ax.set_ylabel("Desplazamiento lateral L (m)")
    ax.set_title("Desplazamiento lateral por capa  L(t) = (K·i/n_e)·t / R"); ax.legend(fontsize=7); ax.grid(alpha=0.3)
    plt.tight_layout(); plt.show()
    print("\\nDesplazamiento lateral a t_max:")
    for c in res.desplazamiento_lateral["por_capa"]:
        print(f"  · {c['nombre']:<30} {c['desplazamiento_tmax_m']:>10.1f} m")
else:
    print("Sin gradiente: no se calculan transporte ni desplazamiento lateral.")'''))

CELDAS.append(md(
"""## 3b · Mapa interactivo del emplazamiento

Mapa centrado en el **punto de origen** (convertido a WGS84 desde el WKID
indicado), con selector de **mapa base** (topografía, imagen/satélite, calles)
y la **huella del penacho** proyectada en planta según el rumbo del flujo."""))

CELDAS.append(code(
'''if res.geo:
    import folium
    g = res.geo
    centro = [g["lat"], g["lon"]]
    m_map = folium.Map(location=centro, zoom_start=15, tiles=None)
    # Mapas base estándar como capas conmutables.
    folium.TileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
                     attr="Esri", name="Topografía").add_to(m_map)
    folium.TileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                     attr="Esri", name="Imagen (satélite)").add_to(m_map)
    folium.TileLayer("OpenStreetMap", name="Mapa (calles)").add_to(m_map)
    folium.Marker(centro, tooltip="Origen de los datos",
                  popup=f"{g['lat']:.6f}, {g['lon']:.6f} · EPSG:{g['wkid']}",
                  icon=folium.Icon(color="darkblue", icon="tint")).add_to(m_map)
    if g.get("huella_penacho"):
        folium.Polygon(g["huella_penacho"], color="#ffb74d", weight=2,
                       fill=True, fill_color="#ff7043", fill_opacity=0.35,
                       tooltip="Huella del penacho").add_to(m_map)
        pt = g["punta_penacho"]
        folium.CircleMarker([pt["lat"], pt["lon"]], radius=5, color="#fff",
                            fill_color="#ff7043", fill_opacity=1,
                            tooltip=f"Frente del penacho · {pt['longitud_m']:.0f} m").add_to(m_map)
    folium.LayerControl().add_to(m_map)
    display(m_map)
else:
    print("Activa la georreferenciación en la celda 2 para ver el mapa.")'''))

CELDAS.append(md("## 4 · Generar y descargar las salidas (HTML · PDF · JSON)"))

CELDAS.append(code(
'''import json as _json
from hidrogeologia.html_report import generar_html
from hidrogeologia.pdf_report import generar_pdf

pref = "resultado_hidrogeologia"
generar_html(modelo, res, pref + ".html")
generar_pdf(modelo, res, pref + ".pdf")
with open(pref + ".json", "w", encoding="utf-8") as f:
    _json.dump(res.a_dict(), f, ensure_ascii=False, indent=2)

print("Salidas generadas:", pref + ".html /.pdf /.json")

# Descarga automática (solo en Google Colab).
try:
    from google.colab import files
    for ext in (".html", ".pdf", ".json"):
        files.download(pref + ext)
except Exception:
    print("Si no estás en Colab, descarga los archivos desde el panel lateral.")

# Vista previa del informe interactivo HTML dentro del notebook.
from IPython.display import IFrame, HTML
display(HTML(open(pref + ".html", encoding="utf-8").read()))'''))


nb = {
    "cells": CELDAS,
    "metadata": {
        "colab": {"name": "hidrogeologia_colab.ipynb", "provenance": []},
        "kernelspec": {"display_name": "Python 3", "name": "python3"},
        "language_info": {"name": "python"},
    },
    "nbformat": 4,
    "nbformat_minor": 0,
}

destino = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hidrogeologia_colab.ipynb")
with open(destino, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)
print("Notebook escrito en:", destino, "·", len(CELDAS), "celdas")
