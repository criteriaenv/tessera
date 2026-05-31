"""Generación del informe técnico en PDF (matplotlib · PdfPages).

Produce un informe multipágina con: portada y resumen, columna
hidrogeológica, resultados de transporte, penacho, desplazamiento lateral,
capítulo hidrogeológico y referencias bibliográficas. No requiere librerías
externas más allá de matplotlib.
"""
from __future__ import annotations

import textwrap

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle

from .core import ModeloHidrogeologico, ResultadosModelo, SEG_POR_ANIO
from .referencias import REFERENCIAS, CAPITULO_HIDROGEOLOGICO

PALETA = [
    "#8d6e63", "#ffb74d", "#fff176", "#aed581", "#4fc3f7",
    "#7986cb", "#ba68c8", "#f06292", "#a1887f", "#90a4ae",
]
AZUL = "#1a3349"
ACC = "#1f6f8b"


def _fmt(x, d=2):
    if x is None or not np.isfinite(x):
        return "—"
    if x != 0 and (abs(x) < 1e-3 or abs(x) >= 1e5):
        return f"{x:.{d}e}"
    return f"{x:,.{d}f}".replace(",", " ")


def generar_pdf(modelo: ModeloHidrogeologico, res: ResultadosModelo, ruta: str) -> str:
    _PAG["n"] = 0
    with PdfPages(ruta) as pdf:
        _portada(pdf, modelo, res)
        if res.geo:
            _pagina_mapa(pdf, modelo, res)
        _pagina_columna(pdf, modelo, res)
        if res.transporte.get("perfiles"):
            _pagina_transporte(pdf, modelo, res)
            _pagina_penacho(pdf, modelo, res)
            _pagina_penacho_perfil(pdf, modelo, res)
        if res.desplazamiento_lateral:
            _pagina_desplazamiento(pdf, modelo, res)
        _paginas_capitulo(pdf)
        _pagina_referencias(pdf)

        d = pdf.infodict()
        d["Title"] = f"Informe hidrogeológico — {modelo.nombre}"
        d["Author"] = "Hidrogeología v1.0"
        d["Subject"] = "Análisis de tránsito de contaminantes"
    return ruta


def _encabezado(fig, titulo, subtitulo=""):
    fig.text(0.06, 0.95, "HIDROGEOLOGÍA", fontsize=11, color=ACC, fontweight="bold")
    fig.text(0.94, 0.95, "Tránsito de contaminantes", fontsize=8, color="#888", ha="right")
    fig.text(0.06, 0.905, titulo, fontsize=17, color=AZUL, fontweight="bold")
    if subtitulo:
        fig.text(0.06, 0.875, subtitulo, fontsize=10, color="#555")
    fig.add_artist(plt.Line2D([0.06, 0.94], [0.86, 0.86], color=ACC, lw=1.2,
                              transform=fig.transFigure))


# Contador de páginas físicas (se reinicia en cada generación de PDF).
_PAG = {"n": 0}


def _pie(fig, n=None):
    """Pie de página. La numeración física es automática (incremental) para que
    insertar páginas condicionales no descuadre los números."""
    _PAG["n"] += 1
    fig.text(0.94, 0.03, f"Pág. {_PAG['n']}", fontsize=8, color="#999", ha="right")
    fig.text(0.06, 0.03,
             "Modelo analítico Ogata-Banks (1961) / Domenico (1987) · cribado preliminar",
             fontsize=7, color="#999")


# ---------------------------------------------------------------------------
def _portada(pdf, modelo, res):
    fig = plt.figure(figsize=(8.27, 11.69))  # A4
    fig.patch.set_facecolor("white")
    s = res.sistema
    fig.text(0.06, 0.92, "HIDROGEOLOGÍA", fontsize=14, color=ACC, fontweight="bold")
    fig.text(0.06, 0.86, "Informe de análisis de tránsito\nde contaminantes en hidrogeología",
             fontsize=23, color=AZUL, fontweight="bold", va="top")
    fig.add_artist(plt.Line2D([0.06, 0.94], [0.80, 0.80], color=ACC, lw=2,
                              transform=fig.transFigure))
    fig.text(0.06, 0.76, modelo.nombre, fontsize=15, color="#222", fontweight="bold")
    if modelo.descripcion:
        for i, ln in enumerate(textwrap.wrap(modelo.descripcion, 80)):
            fig.text(0.06, 0.73 - i*0.022, ln, fontsize=10, color="#555")

    filas = [
        ("Número de capas", f"{s['n_capas']}"),
        ("Espesor total", f"{_fmt(s['espesor_total_m'],1)} m"),
        ("Transmisividad total", f"{_fmt(s['transmisividad_total_m2_dia'],2)} m²/día"),
        ("K horizontal equivalente", f"{_fmt(s['K_horizontal_equivalente_m_s'])} m/s"),
        ("K vertical equivalente", f"{_fmt(s['K_vertical_equivalente_m_s'])} m/s"),
        ("Anisotropía Kh/Kv", f"{_fmt(s['relacion_anisotropia'],1)}"),
        ("Porosidad eficaz media", f"{_fmt(s['porosidad_media'],3)}"),
        ("Gradiente hidráulico",
         f"{_fmt(s['gradiente_hidraulico'],4)}" if s['gradiente_hidraulico'] is not None else "no definido"),
        ("Capa de transporte", s['capa_transporte']),
        ("Concentración fuente C0", f"{_fmt(res.transporte['concentracion_fuente_mg_l'],1)} mg/L"),
        ("Horizonte temporal", f"{_fmt(s['tiempo_max_anios'],1)} años"),
    ]
    y = 0.60
    fig.text(0.06, y+0.03, "Parámetros del modelo", fontsize=12,
             color=AZUL, fontweight="bold")
    for idx, (k, v) in enumerate(filas):
        if idx % 2 == 0:
            fig.add_artist(Rectangle((0.06, y-0.012), 0.88, 0.026,
                           transform=fig.transFigure, facecolor="#f2f6f8",
                           edgecolor="none", zorder=0))
        fig.text(0.08, y, k, fontsize=10, color="#333", va="center")
        fig.text(0.92, y, v, fontsize=10, color="#111", va="center", ha="right",
                 fontweight="bold")
        y -= 0.028

    fig.text(0.06, 0.10, f"Generado: {res.metadatos['generado']}", fontsize=9, color="#777")
    fig.text(0.06, 0.075, f"Hidrogeología v{res.metadatos['version']}", fontsize=9, color="#777")
    _pie(fig, 1)
    pdf.savefig(fig)
    plt.close(fig)


def _pagina_mapa(pdf, modelo, res):
    """Página de ubicación con mapa estático del emplazamiento y huella del
    penacho. Descarga teselas del mapa base elegido (WKID/selector); si no hay
    red, dibuja una vista esquemática equivalente.
    """
    from .geo import (stitch_basemap, zoom_para_extension, destino_geodesico,
                      BASEMAPS)
    g = res.geo
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.patch.set_facecolor("white")
    bm_lbl = BASEMAPS.get(g["basemap"], BASEMAPS["topografia"])["etiqueta"]
    _encabezado(fig, "1 · Ubicación del emplazamiento",
                f"Origen EPSG:{g['wkid']} · mapa base «{bm_lbl}»")
    ax = fig.add_axes([0.10, 0.42, 0.84, 0.40])
    lon, lat = g["lon"], g["lat"]

    long_pen = 0.0
    if g.get("punta_penacho"):
        long_pen = g["punta_penacho"]["longitud_m"]

    z = zoom_para_extension(long_pen if long_pen else 400.0)
    mosaico = stitch_basemap(lon, lat, z, g["basemap"], n_tiles=3)

    if mosaico is not None:
        img, (lon_min, lon_max, lat_min, lat_max) = mosaico
        ax.imshow(img, extent=[lon_min, lon_max, lat_min, lat_max], aspect="auto")
        fuente_nota = f"Mapa base «{bm_lbl}» (teselas descargadas)."
    else:
        ax.set_facecolor("#eef3f6")
        fuente_nota = ("Sin acceso a teselas en el momento de generar el informe: "
                       "se muestra una vista esquemática (norte arriba).")

    # Huella del penacho (si la hay).
    if g.get("huella_penacho"):
        poly = g["huella_penacho"]  # [[lat, lon], ...]
        xs = [p[1] for p in poly] + [poly[0][1]]
        ys = [p[0] for p in poly] + [poly[0][0]]
        ax.fill(xs, ys, facecolor="#ff7043", alpha=0.35, edgecolor="#ffb74d", lw=1.5,
                zorder=5, label="Huella del penacho")
        pt = g["punta_penacho"]
        ax.plot([pt["lon"]], [pt["lat"]], "o", color="#fff",
                markeredgecolor="#ff7043", markersize=7, zorder=6)
    ax.plot([lon], [lat], "^", color="#1a3349", markersize=12, zorder=7,
            markeredgecolor="white", label="Origen de los datos")

    if mosaico is None and not g.get("huella_penacho"):
        # Vista esquemática sin penacho: indica el rumbo del flujo.
        az = g["azimut_flujo_grados"]
        ax.annotate("", xy=(0.7, 0.3), xytext=(0.3, 0.7),
                    xycoords="axes fraction",
                    arrowprops=dict(arrowstyle="->", color="#1f6f8b", lw=2))
        ax.text(0.5, 0.5, f"Flujo {az:.0f}°", transform=ax.transAxes,
                fontsize=9, color="#1f6f8b")

    ax.set_xlabel("Longitud (°)")
    ax.set_ylabel("Latitud (°)")
    ax.set_title("Emplazamiento y huella del penacho en planta", fontsize=10)
    ax.legend(fontsize=7, loc="upper right")

    # Ficha de coordenadas.
    txt = (
        f"Origen (entrada): X = {_fmt(g['origen_x'],2)} · Y = {_fmt(g['origen_y'],2)}  "
        f"[EPSG:{g['wkid']} — {g['wkid_nombre']}]\n"
        f"Origen (WGS84): lat = {_fmt(g['lat'],6)}° · lon = {_fmt(g['lon'],6)}°  ·  "
        f"rumbo del flujo = {_fmt(g['azimut_flujo_grados'],0)}° desde el N\n"
        + (f"Huella del penacho ≈ {_fmt(long_pen,0)} m de longitud (hasta C/C0 ≈ 0,01)."
           if long_pen else "Sin penacho georreferenciado (define gradiente).")
    )
    fig.text(0.10, 0.30, txt, fontsize=9, color="#333")
    fig.text(0.10, 0.20, fuente_nota, fontsize=8, color="#888")
    _pie(fig, 2)
    pdf.savefig(fig)
    plt.close(fig)


def _pagina_columna(pdf, modelo, res):
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.patch.set_facecolor("white")
    _encabezado(fig, "2 · Columna hidrogeológica y capas",
                "Espesores, permeabilidad y propiedades de cada estrato")

    ax = fig.add_axes([0.08, 0.40, 0.34, 0.40])
    prof = 0.0
    for i, c in enumerate(res.capas):
        col = modelo.capas[i].color or PALETA[i % len(PALETA)]
        ax.add_patch(Rectangle((0, prof), 1, c["espesor_m"], facecolor=col,
                               edgecolor="white"))
        ax.text(0.5, prof + c["espesor_m"]/2, c["nombre"], ha="center",
                va="center", fontsize=8, color="#102132")
        ax.text(1.05, prof + c["espesor_m"]/2, f"{_fmt(c['K_m_s'],1)} m/s",
                fontsize=7, va="center", color="#555")
        prof += c["espesor_m"]
    ax.set_ylim(prof, 0)
    ax.set_xlim(0, 1)
    ax.set_xticks([])
    ax.set_ylabel("Profundidad (m)")
    ax.set_title("Columna", fontsize=10)

    ax2 = fig.add_axes([0.56, 0.40, 0.38, 0.40])
    nombres = [c["nombre"] for c in res.capas]
    Ks = [c["K_m_s"] for c in res.capas]
    colores = [modelo.capas[i].color or PALETA[i % len(PALETA)] for i in range(len(res.capas))]
    ax2.barh(range(len(Ks)), Ks, color=colores)
    ax2.set_yticks(range(len(Ks)))
    ax2.set_yticklabels(nombres, fontsize=8)
    ax2.set_xscale("log")
    ax2.invert_yaxis()
    ax2.set_xlabel("K (m/s, escala log)")
    ax2.set_title("Conductividad hidráulica", fontsize=10)
    ax2.grid(True, axis="x", alpha=0.3)

    encabez = ["Capa", "b (m)", "K (m/s)", "n_e", "k (darcy)", "T (m²/día)", "R", "Clasificación"]
    cell = []
    for c in res.capas:
        cell.append([
            c["nombre"], _fmt(c["espesor_m"], 1), _fmt(c["K_m_s"], 1),
            _fmt(c["porosidad_eficaz"], 2), _fmt(c["permeabilidad_darcy"], 2),
            _fmt(c["transmisividad_m2_s"]*86400, 2), _fmt(c["factor_retardo"], 1),
            textwrap.fill(c["clasificacion"], 20),
        ])
    axt = fig.add_axes([0.06, 0.08, 0.88, 0.26])
    axt.axis("off")
    tab = axt.table(cellText=cell, colLabels=encabez, loc="center", cellLoc="center")
    tab.auto_set_font_size(False)
    tab.set_fontsize(7)
    tab.scale(1, 1.5)
    for (r, cc), cell_obj in tab.get_celld().items():
        if r == 0:
            cell_obj.set_facecolor(AZUL)
            cell_obj.set_text_props(color="white", fontweight="bold")
        elif r % 2 == 0:
            cell_obj.set_facecolor("#f2f6f8")
    _pie(fig, 2)
    pdf.savefig(fig)
    plt.close(fig)


def _pagina_transporte(pdf, modelo, res):
    t = res.transporte
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.patch.set_facecolor("white")
    _encabezado(fig, "3 · Transporte advectivo-dispersivo",
                f"Capa «{t['capa']}» · solución de Ogata-Banks (1961)")
    x = np.array(t["x_m"])

    ax = fig.add_axes([0.10, 0.50, 0.84, 0.30])
    cmap = plt.cm.viridis
    perf = t["perfiles"]
    for i, p in enumerate(perf):
        ax.plot(x, p["C_rel"], color=cmap(i/len(perf)),
                label=f"{_fmt(p['t_anios'],1)} años")
    ax.axhline(0.5, color="#ffb74d", ls="--", lw=1, label="C/C0 = 0,5 (frente)")
    ax.set_xlabel("Distancia x (m)")
    ax.set_ylabel("C/C0 (-)")
    ax.set_title("Perfiles de concentración a distintos tiempos", fontsize=10)
    ax.legend(fontsize=7, ncol=2)
    ax.grid(True, alpha=0.3)

    bt = t["curva_llegada"]
    ax2 = fig.add_axes([0.10, 0.13, 0.84, 0.27])
    ax2.plot(bt["t_anios"], bt["C_rel"], color="#2e7d32", lw=2)
    ax2.fill_between(bt["t_anios"], bt["C_rel"], color="#2e7d32", alpha=0.15)
    ax2.set_xlabel("Tiempo (años)")
    ax2.set_ylabel("C/C0 (-)")
    ax2.set_title(f"Curva de llegada en x = {_fmt(bt['x_obs_m'],0)} m", fontsize=10)
    ax2.grid(True, alpha=0.3)

    txt = (f"v real = {_fmt(t['velocidad_real_m_s']*SEG_POR_ANIO,2)} m/año   ·   "
           f"v contaminante = {_fmt(t['velocidad_contaminante_m_s']*SEG_POR_ANIO,2)} m/año   ·   "
           f"D_L = {_fmt(t['dispersion_long_m2_s'])} m²/s   ·   "
           f"R = {_fmt(t['factor_retardo'],2)}   ·   alfa_L = {_fmt(t['dispersividad_long_m'],2)} m")
    fig.text(0.10, 0.83, txt, fontsize=8.5, color="#333")
    _pie(fig, 3)
    pdf.savefig(fig)
    plt.close(fig)


def _pagina_penacho(pdf, modelo, res):
    pen = res.transporte.get("penacho_2d")
    if not pen:
        return
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.patch.set_facecolor("white")
    _encabezado(fig, "4 · Penacho de contaminación en planta",
                f"Modelo de Domenico (1987) · t = {_fmt(pen['t_anios'],1)} años")
    ax = fig.add_axes([0.10, 0.45, 0.84, 0.35])
    xg = np.array(pen["x_m"]); yg = np.array(pen["y_m"])
    CC = np.array(pen["C_rel"])
    im = ax.pcolormesh(xg, yg, CC, cmap="turbo", shading="auto", vmin=0, vmax=1)
    cs = ax.contour(xg, yg, CC, levels=[0.05, 0.1, 0.5], colors="white", linewidths=0.8)
    ax.clabel(cs, fmt="%.2f", fontsize=7)
    ax.set_xlabel("Distancia longitudinal x (m)")
    ax.set_ylabel("Distancia transversal y (m)")
    ax.set_title("Concentración relativa C/C0 del penacho", fontsize=10)
    fig.colorbar(im, ax=ax, label="C/C0", fraction=0.04, pad=0.02)

    fig.text(0.10, 0.36,
             "El penacho se ensancha lateralmente por dispersión transversal "
             "(alfa_T) mientras avanza por advección.\nLas isolíneas marcan C/C0 = "
             "0,50 (núcleo), 0,10 y 0,05 (borde del penacho).",
             fontsize=9, color="#444")
    _pie(fig, 4)
    pdf.savefig(fig)
    plt.close(fig)


def _pagina_penacho_perfil(pdf, modelo, res):
    pen = res.transporte.get("penacho_perfil")
    if not pen:
        return
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.patch.set_facecolor("white")
    _encabezado(fig, "4b · Pluma de transporte en perfil (corte vertical)",
                f"Modelo de Domenico (1987) · gradiente · t = {_fmt(pen['t_anios'],1)} años")
    ax = fig.add_axes([0.10, 0.45, 0.84, 0.35])
    xg = np.array(pen["x_m"]); zg = np.array(pen["z_m"])
    CC = np.array(pen["C_rel"])
    im = ax.pcolormesh(xg, zg, CC, cmap="turbo", shading="auto", vmin=0, vmax=1)
    cs = ax.contour(xg, zg, CC, levels=[0.05, 0.1, 0.5], colors="white", linewidths=0.8)
    ax.clabel(cs, fmt="%.2f", fontsize=7)
    # Límites entre capas (líneas horizontales) y etiquetas.
    for c in pen["capas"]:
        ax.axhline(c["muro_m"], color="white", lw=0.5, ls=":", alpha=0.6)
        ax.text(xg[-1]*0.99, (c["techo_m"]+c["muro_m"])/2, c["nombre"],
                fontsize=6.5, color="white", ha="right", va="center", alpha=0.9)
    ax.invert_yaxis()  # profundidad creciente hacia abajo
    ax.set_xlabel("Distancia longitudinal x (m)")
    ax.set_ylabel("Profundidad z (m)")
    ax.set_title("Concentración relativa C/C0 — perfil vertical", fontsize=10)
    fig.colorbar(im, ax=ax, label="C/C0", fraction=0.04, pad=0.02)

    fig.text(0.10, 0.36,
             "Pluma de transporte impulsada por el gradiente hidráulico, vista en "
             "corte vertical (x–z). La fuente se sitúa en la capa de transporte; el "
             "penacho\nse dispersa verticalmente según alfa_V "
             f"(= {_fmt(pen['alfa_V_m'],3)} m). Las líneas punteadas marcan los "
             "contactos entre capas.",
             fontsize=9, color="#444")
    _pie(fig, 5)
    pdf.savefig(fig)
    plt.close(fig)


def _pagina_desplazamiento(pdf, modelo, res):
    d = res.desplazamiento_lateral
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.patch.set_facecolor("white")
    _encabezado(fig, "5 · Desplazamiento lateral del contaminante",
                f"Gradiente hidráulico i = {_fmt(d['gradiente_hidraulico'],4)}")
    ax = fig.add_axes([0.10, 0.48, 0.84, 0.32])
    for i, c in enumerate(d["por_capa"]):
        col = modelo.capas[i].color or PALETA[i % len(PALETA)]
        ax.plot(c["curva"]["t_anios"], c["curva"]["L_m"], color=col, lw=2, label=c["nombre"])
    ax.set_xlabel("Tiempo (años)")
    ax.set_ylabel("Desplazamiento lateral L (m)")
    ax.set_title("L(t) = (K·i/n_e)·t / R por capa", fontsize=10)
    ax.legend(fontsize=7)
    ax.grid(True, alpha=0.3)

    encabez = ["Capa", "q (m/año)", "v real (m/año)", "R", "v cont. (m/año)",
               f"L a {_fmt(d['tiempo_max_anios'],0)} a (m)"]
    cell = []
    for c in d["por_capa"]:
        cell.append([
            c["nombre"], _fmt(c["q_darcy_m_anio"], 2), _fmt(c["v_real_m_anio"], 2),
            _fmt(c["factor_retardo"], 1), _fmt(c["v_contaminante_m_anio"], 2),
            _fmt(c["desplazamiento_tmax_m"], 1),
        ])
    axt = fig.add_axes([0.06, 0.14, 0.88, 0.26])
    axt.axis("off")
    tab = axt.table(cellText=cell, colLabels=encabez, loc="center", cellLoc="center")
    tab.auto_set_font_size(False)
    tab.set_fontsize(8)
    tab.scale(1, 1.5)
    for (r, cc), cell_obj in tab.get_celld().items():
        if r == 0:
            cell_obj.set_facecolor(AZUL)
            cell_obj.set_text_props(color="white", fontweight="bold")
        elif r % 2 == 0:
            cell_obj.set_facecolor("#f2f6f8")
    _pie(fig, 6)
    pdf.savefig(fig)
    plt.close(fig)


def _paginas_capitulo(pdf):
    cap = CAPITULO_HIDROGEOLOGICO
    bloques = []
    for sec in cap["secciones"]:
        bloques.append(("h", sec["titulo"]))
        for p in sec["parrafos"]:
            bloques.append(("p", p))

    estado = {"n_pag": 7, "primera": True, "fig": None, "y": 0.0}

    def nueva_pagina():
        fig = plt.figure(figsize=(8.27, 11.69))
        fig.patch.set_facecolor("white")
        _encabezado(fig, "7 · Capítulo hidrogeológico",
                    cap["titulo"] if estado["primera"] else "(continuación)")
        estado["fig"] = fig
        estado["y"] = 0.82
        estado["primera"] = False

    def cerrar():
        _pie(estado["fig"], estado["n_pag"])
        pdf.savefig(estado["fig"])
        plt.close(estado["fig"])
        estado["n_pag"] += 1

    nueva_pagina()
    for tipo, txt in bloques:
        if tipo == "h":
            if estado["y"] < 0.16:
                cerrar(); nueva_pagina()
            estado["y"] -= 0.01
            estado["fig"].text(0.06, estado["y"], txt, fontsize=11.5,
                               color=ACC, fontweight="bold")
            estado["y"] -= 0.030
        else:
            lineas = textwrap.wrap(txt, 95)
            if estado["y"] - len(lineas)*0.020 < 0.10:
                cerrar(); nueva_pagina()
            for ln in lineas:
                estado["fig"].text(0.06, estado["y"], ln, fontsize=9.5, color="#222")
                estado["y"] -= 0.020
            estado["y"] -= 0.012
    cerrar()


def _pagina_referencias(pdf):
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.patch.set_facecolor("white")
    _encabezado(fig, "8 · Referencias bibliográficas", "Fundamento científico del modelo")
    y = 0.82
    n = 1
    for r in REFERENCIAS:
        lineas = textwrap.wrap(f"[{n}] {r['cita']}", 92)
        if y - (len(lineas)+1)*0.018 < 0.06:
            pdf.savefig(fig); plt.close(fig)
            fig = plt.figure(figsize=(8.27, 11.69))
            fig.patch.set_facecolor("white")
            _encabezado(fig, "8 · Referencias bibliográficas", "(continuación)")
            y = 0.82
        for ln in lineas:
            fig.text(0.06, y, ln, fontsize=9, color="#222")
            y -= 0.018
        fig.text(0.08, y, r["aporta"], fontsize=8, color="#1f6f8b", style="italic")
        y -= 0.026
        n += 1
    _pie(fig, 8)
    pdf.savefig(fig)
    plt.close(fig)
