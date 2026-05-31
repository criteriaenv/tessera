"""Generación del informe HTML interactivo (autónomo, sin conexión).

El HTML incrusta los datos del modelo en formato JSON y reimplementa en
JavaScript las ecuaciones de flujo y transporte, de modo que el usuario puede:
  * editar el número de capas, sus nombres, espesores y permeabilidades,
  * recalcular en vivo las propiedades equivalentes del sistema,
  * desplazar un control de tiempo para ver el avance del penacho,
  * inspeccionar el desplazamiento lateral por capa.

Los gráficos se dibujan con SVG/Canvas nativos (sin librerías externas), por
lo que el archivo funciona sin acceso a internet.
"""
from __future__ import annotations

import json
from typing import Dict, Any

from .core import ModeloHidrogeologico, ResultadosModelo, SEG_POR_ANIO
from .referencias import REFERENCIAS, CAPITULO_HIDROGEOLOGICO
from .geo import WKID_CATALOGO, BASEMAPS

PALETA = [
    "#8d6e63", "#ffb74d", "#fff176", "#aed581", "#4fc3f7",
    "#7986cb", "#ba68c8", "#f06292", "#a1887f", "#90a4ae",
]


def _config_js(modelo: ModeloHidrogeologico, res: ResultadosModelo) -> Dict[str, Any]:
    capas = []
    for i, c in enumerate(modelo.capas):
        capas.append({
            "nombre": c.nombre,
            "espesor": c.espesor_m,
            "K": c.K_m_s,
            "ne": c.porosidad_eficaz,
            "alfaL": c.alfa_L(),
            "alfaT": c.alfa_T(),
            "alfaV": c.alfa_V(),
            "R": c.factor_retardo,
            "color": c.color or PALETA[i % len(PALETA)],
        })
    return {
        "nombre": modelo.nombre,
        "descripcion": modelo.descripcion,
        "gradiente": modelo.gradiente_hidraulico,
        "C0": modelo.concentracion_fuente,
        "capaTransporte": modelo.capa_transporte_idx,
        "tiempoMax": modelo.tiempo_max_anios,
        "distanciaMax": modelo.distancia_max_m,
        "azimutFlujo": modelo.azimut_flujo_grados,
        "segPorAnio": SEG_POR_ANIO,
        "capas": capas,
        "geo": res.geo,
        "wkidCatalogo": WKID_CATALOGO,
        "basemaps": BASEMAPS,
    }


def generar_html(modelo: ModeloHidrogeologico, res: ResultadosModelo, ruta: str) -> str:
    cfg = _config_js(modelo, res)
    datos = res.a_dict()
    cap_html = _capitulo_html()
    ref_html = _referencias_html()

    html = _PLANTILLA.format(
        titulo=_esc(modelo.nombre),
        config_json=json.dumps(cfg, ensure_ascii=False),
        datos_json=json.dumps(datos, ensure_ascii=False),
        capitulo=cap_html,
        referencias=ref_html,
        fecha=res.metadatos["generado"],
    )
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(html)
    return ruta


def _esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _capitulo_html() -> str:
    out = [f"<h2>{_esc(CAPITULO_HIDROGEOLOGICO['titulo'])}</h2>"]
    for sec in CAPITULO_HIDROGEOLOGICO["secciones"]:
        out.append(f"<h3>{_esc(sec['titulo'])}</h3>")
        for p in sec["parrafos"]:
            out.append(f"<p>{_esc(p)}</p>")
    return "\n".join(out)


def _referencias_html() -> str:
    out = ["<ol class='refs'>"]
    for r in REFERENCIAS:
        out.append(
            f"<li><span class='cita'>{_esc(r['cita'])}</span>"
            f"<br><em>{_esc(r['aporta'])}</em></li>"
        )
    out.append("</ol>")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Plantilla HTML. Las llaves de CSS/JS van duplicadas ({{ }}) por str.format.
# ---------------------------------------------------------------------------
_PLANTILLA = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Hidrogeología · {titulo}</title>
<style>
:root {{
  --bg:#0f1720; --panel:#16212e; --panel2:#1c2a3a; --txt:#e6edf3;
  --muted:#9fb3c8; --acc:#4fc3f7; --acc2:#ffb74d; --line:#2b3a4d; --ok:#81c784;
}}
*{{box-sizing:border-box}}
body{{margin:0;font-family:'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
  background:var(--bg);color:var(--txt);line-height:1.5}}
header{{padding:24px 28px;background:linear-gradient(135deg,#102132,#1a3349);
  border-bottom:1px solid var(--line)}}
header h1{{margin:0 0 4px;font-size:1.6rem}}
header .sub{{color:var(--muted);font-size:.95rem}}
nav{{position:sticky;top:0;z-index:20;display:flex;flex-wrap:wrap;gap:4px;
  background:var(--panel);padding:8px 16px;border-bottom:1px solid var(--line)}}
nav button{{background:transparent;color:var(--muted);border:none;padding:8px 14px;
  cursor:pointer;border-radius:8px;font-size:.92rem}}
nav button:hover{{color:var(--txt);background:var(--panel2)}}
nav button.activo{{color:#06222f;background:var(--acc);font-weight:600}}
main{{max-width:1180px;margin:0 auto;padding:22px 18px 60px}}
section{{display:none;animation:fade .25s}}
section.activa{{display:block}}
@keyframes fade{{from{{opacity:0;transform:translateY(6px)}}to{{opacity:1}}}}
h2{{font-size:1.3rem;border-left:4px solid var(--acc);padding-left:10px;margin-top:4px}}
h3{{color:var(--acc2);font-size:1.05rem;margin:18px 0 6px}}
.grid{{display:grid;gap:14px}}
.cards{{grid-template-columns:repeat(auto-fit,minmax(200px,1fr))}}
.card{{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 16px}}
.card .k{{color:var(--muted);font-size:.8rem;text-transform:uppercase;letter-spacing:.04em}}
.card .v{{font-size:1.5rem;font-weight:600;margin-top:4px}}
.card .u{{color:var(--muted);font-size:.85rem}}
.panel{{background:var(--panel);border:1px solid var(--line);border-radius:12px;
  padding:16px 18px;margin:14px 0}}
table{{width:100%;border-collapse:collapse;font-size:.9rem}}
th,td{{padding:7px 9px;text-align:right;border-bottom:1px solid var(--line)}}
th:first-child,td:first-child{{text-align:left}}
th{{color:var(--muted);font-weight:600;font-size:.8rem;text-transform:uppercase}}
input,select{{background:var(--panel2);color:var(--txt);border:1px solid var(--line);
  border-radius:6px;padding:5px 7px;font-size:.88rem;width:100%}}
input[type=range]{{padding:0}}
.btn{{background:var(--acc);color:#06222f;border:none;border-radius:8px;padding:8px 14px;
  cursor:pointer;font-weight:600;font-size:.9rem}}
.btn.sec{{background:var(--panel2);color:var(--txt);border:1px solid var(--line)}}
.toolbar{{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-bottom:10px}}
.muted{{color:var(--muted)}}
.refs li{{margin-bottom:10px}}
.refs .cita{{color:var(--txt)}}
.flex{{display:flex;gap:18px;flex-wrap:wrap;align-items:flex-start}}
.flex>*{{flex:1;min-width:280px}}
svg{{width:100%;height:auto;display:block}}
.slider-wrap{{display:flex;align-items:center;gap:12px;margin:8px 0}}
.slider-wrap input{{flex:1}}
.tag{{display:inline-block;padding:2px 8px;border-radius:20px;font-size:.78rem;
  background:var(--panel2);border:1px solid var(--line);color:var(--muted)}}
.legend{{display:flex;gap:14px;flex-wrap:wrap;font-size:.82rem;margin-top:6px}}
.legend span{{display:flex;align-items:center;gap:5px}}
.sw{{width:14px;height:14px;border-radius:3px;display:inline-block}}
footer{{text-align:center;color:var(--muted);font-size:.82rem;padding:24px}}
.note{{background:#10283a;border-left:3px solid var(--acc);padding:10px 14px;
  border-radius:6px;font-size:.88rem;margin:10px 0}}
#mapa{{height:460px;border-radius:10px;border:1px solid var(--line)}}
.basemap-sw{{display:flex;gap:6px;flex-wrap:wrap;margin:8px 0}}
.basemap-sw button{{background:var(--panel2);color:var(--txt);border:1px solid var(--line);
  border-radius:8px;padding:6px 12px;cursor:pointer;font-size:.85rem}}
.basemap-sw button.activo{{background:var(--acc);color:#06222f;font-weight:600}}
.coordbox{{display:flex;gap:10px;flex-wrap:wrap;align-items:end}}
.coordbox>div{{flex:1;min-width:120px}}
.leaflet-popup-content{{color:#102132}}
</style>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/proj4js/2.11.0/proj4.js"></script>
</head>
<body>
<header>
  <h1>Hidrogeología — Tránsito de contaminantes</h1>
  <div class="sub" id="hdrSub"></div>
</header>
<nav id="nav"></nav>
<main>
  <section id="sec-ubicacion" class="activa">
    <h2>Ubicación · punto de origen y mapa interactivo</h2>
    <p class="muted">Indica el <strong>punto de origen</strong> de los datos en
       el sistema de coordenadas que elijas (por su <strong>WKID</strong>). El
       mapa se centra en ese punto y, si hay penacho calculado, dibuja su huella
       en planta según el rumbo del flujo.</p>
    <div class="panel">
      <div class="coordbox">
        <div><label class="muted">X / Este (o longitud)</label>
          <input id="inpOX" type="number" step="any"></div>
        <div><label class="muted">Y / Norte (o latitud)</label>
          <input id="inpOY" type="number" step="any"></div>
        <div><label class="muted">WKID (sistema de referencia)</label>
          <select id="selWkid"></select></div>
        <div><label class="muted">Rumbo del flujo (° desde N)</label>
          <input id="inpAz" type="number" step="1" value="90"></div>
        <div><button class="btn" onclick="recentrarMapa()">Actualizar mapa</button></div>
      </div>
      <div class="basemap-sw" id="basemapSw"></div>
    </div>
    <div id="mapa"></div>
    <div class="panel note" id="notaMapa"></div>
  </section>

  <section id="sec-resumen">
    <h2>Resumen del modelo</h2>
    <p class="muted" id="descripcion"></p>
    <div class="grid cards" id="tarjetas"></div>
    <div class="panel note" id="notaGradiente"></div>
  </section>

  <section id="sec-columna">
    <h2>Columna hidrogeológica · capas</h2>
    <p class="muted">Edita el número de capas, sus nombres, espesores y permeabilidades.
       Las propiedades equivalentes y la columna se recalculan en vivo.</p>
    <div class="toolbar">
      <button class="btn" onclick="addCapa()">+ Añadir capa</button>
      <button class="btn sec" onclick="resetCapas()">Restablecer</button>
      <span class="tag" id="nCapasTag"></span>
    </div>
    <div class="flex">
      <div class="panel" style="flex:2">
        <table id="tablaCapas"><thead><tr>
          <th>Capa</th><th>Espesor (m)</th><th>K (m/s)</th><th>n<sub>e</sub></th>
          <th>&alpha;<sub>L</sub> (m)</th><th>&alpha;<sub>V</sub> (m)</th>
          <th>k (darcy)</th><th>T (m&sup2;/d&iacute;a)</th><th></th>
        </tr></thead><tbody></tbody></table>
      </div>
      <div class="panel" style="flex:1">
        <h3 style="margin-top:0">Columna</h3>
        <div id="columnaSVG"></div>
        <div class="legend" id="leyendaK"></div>
      </div>
    </div>
    <div class="grid cards" id="tarjetasSistema" style="margin-top:8px"></div>
  </section>

  <section id="sec-transporte">
    <h2>Transporte del contaminante (advección-dispersión)</h2>
    <div class="panel" id="panelSinGrad" style="display:none">
      <p>El transporte advectivo y el desplazamiento lateral requieren el
      <strong>gradiente hidráulico</strong>. Introdúcelo abajo para activarlos.</p>
    </div>
    <div class="panel">
      <div class="flex">
        <div>
          <label class="muted">Gradiente hidráulico i (-)</label>
          <input id="inpGrad" type="number" step="0.0001">
        </div>
        <div>
          <label class="muted">Concentración fuente C&#8320; (mg/L)</label>
          <input id="inpC0" type="number" step="1">
        </div>
        <div>
          <label class="muted">Capa de transporte</label>
          <select id="selCapa"></select>
        </div>
      </div>
    </div>
    <div class="panel" id="panelTransporte">
      <h3 style="margin-top:0">Perfil de concentración C(x) — frente del penacho</h3>
      <div class="slider-wrap">
        <span class="muted">t =</span>
        <input id="sliderT" type="range" min="0.05" max="1" step="0.01" value="1">
        <span id="lblT" class="tag"></span>
      </div>
      <div id="perfilSVG"></div>
      <div class="legend"><span><span class="sw" style="background:#4fc3f7"></span>C/C&#8320; (perfil al tiempo seleccionado)</span>
        <span><span class="sw" style="background:#ffb74d"></span>C/C&#8320; = 0,5 (frente)</span></div>
      <div class="grid cards" id="tarjetasTrans" style="margin-top:12px"></div>
    </div>
    <div class="panel" id="panelBreak">
      <h3 style="margin-top:0">Curva de llegada C(t) en punto de observación</h3>
      <div id="breakSVG"></div>
    </div>
    <div class="panel" id="panelPenacho">
      <h3 style="margin-top:0">Penacho en planta — vista en planta x–y (Domenico, 1987)</h3>
      <canvas id="canvasPenacho" style="width:100%;border-radius:8px"></canvas>
      <div class="legend" id="leyendaPenacho"></div>
    </div>
    <div class="panel" id="panelPerfil">
      <h3 style="margin-top:0">Pluma de transporte en perfil — corte vertical x–z</h3>
      <p class="muted">Penacho impulsado por el gradiente hidráulico visto en
         corte vertical; la fuente se sitúa en la capa de transporte y se
         dispersa verticalmente seg&uacute;n &alpha;<sub>V</sub>. Las l&iacute;neas
         marcan los contactos entre capas.</p>
      <canvas id="canvasPerfil" style="width:100%;border-radius:8px"></canvas>
      <div class="legend" id="leyendaPerfil"></div>
    </div>
  </section>

  <section id="sec-desplazamiento">
    <h2>Desplazamiento lateral del contaminante</h2>
    <p class="muted">Avance horizontal del núcleo del penacho impulsado por el
       gradiente hidráulico: L(t) = (K·i/n<sub>e</sub>)·t / R.</p>
    <div class="panel" id="panelDespVacio" style="display:none">
      <p>Introduce un gradiente hidráulico en la pestaña «Transporte» para
      calcular el desplazamiento lateral.</p>
    </div>
    <div class="panel" id="panelDesp">
      <div id="despSVG"></div>
      <div class="legend" id="leyendaDesp"></div>
      <table id="tablaDesp" style="margin-top:14px"><thead><tr>
        <th>Capa</th><th>q Darcy (m/a&ntilde;o)</th><th>v real (m/a&ntilde;o)</th>
        <th>R</th><th>v contaminante (m/a&ntilde;o)</th><th>L a t<sub>max</sub> (m)</th>
      </tr></thead><tbody></tbody></table>
    </div>
  </section>

  <section id="sec-capitulo">
    {capitulo}
  </section>

  <section id="sec-referencias">
    <h2>Referencias bibliográficas</h2>
    {referencias}
  </section>
</main>
<footer>
  Generado por <strong>Hidrogeolog&iacute;a v1.0</strong> · {fecha} ·
  Modelo anal&iacute;tico Ogata-Banks (1961) / Domenico (1987) · Solo para cribado preliminar.
</footer>

<script id="config" type="application/json">{config_json}</script>
<script id="datos" type="application/json">{datos_json}</script>
<script>
const CFG = JSON.parse(document.getElementById('config').textContent);
const DATOS = JSON.parse(document.getElementById('datos').textContent);
let CAPAS = JSON.parse(JSON.stringify(CFG.capas));
const PALETA = ["#8d6e63","#ffb74d","#fff176","#aed581","#4fc3f7","#7986cb","#ba68c8","#f06292","#a1887f","#90a4ae"];

/* ---------- Matemáticas: erf / erfc y Ogata-Banks ---------- */
function erf(x){{
  const s=x<0?-1:1; x=Math.abs(x);
  const a1=0.254829592,a2=-0.284496736,a3=1.421413741,a4=-1.453152027,a5=1.061405429,p=0.3275911;
  const t=1/(1+p*x);
  const y=1-(((((a5*t+a4)*t)+a3)*t+a2)*t+a1)*t*Math.exp(-x*x);
  return s*y;
}}
function erfc(x){{return 1-erf(x);}}
function ogataBanks(x,t,v,DL,R){{
  if(t<=0) return 0;
  const vt=v*t/R, den=2*Math.sqrt(DL*t/R);
  let t1=erfc((x-vt)/den);
  let ex=v*x/DL; ex=Math.max(-700,Math.min(700,ex));
  let t2=Math.exp(ex)*erfc((x+vt)/den);
  if(!isFinite(t2)) t2=0;
  let c=0.5*(t1+t2);
  return Math.max(0,Math.min(1,c));
}}
const G=9.81,RHO=998.2,MU=1.002e-3,DARCY=9.869233e-13;
const fmt=(x,d=2)=>{{if(x===null||x===undefined||!isFinite(x))return '—';
  if(x!==0&&(Math.abs(x)<1e-3||Math.abs(x)>=1e5))return x.toExponential(d);
  return x.toLocaleString('es-ES',{{maximumFractionDigits:d}});}};

/* ---------- Estado del modelo (editable) ---------- */
let GRAD=CFG.gradiente, C0=CFG.C0, CAPA_T=CFG.capaTransporte;
let TMAX=CFG.tiempoMax, DMAX=CFG.distanciaMax;

function sistemaEquivalente(){{
  let B=0,T=0,sumHK=0,sumNe=0;
  CAPAS.forEach(c=>{{B+=c.espesor;T+=c.K*c.espesor;sumHK+=c.espesor/c.K;sumNe+=c.ne*c.espesor;}});
  return {{B,T,Kh:T/B,Kv:B/sumHK,aniso:(T/B)/(B/sumHK),ne:sumNe/B}};
}}
function distanciaMax(){{
  const c=CAPAS[CAPA_T];
  if(GRAD){{const vc=GRAD*c.K/c.ne/c.R*TMAX*CFG.segPorAnio; return Math.max(50,vc*1.3);}}
  return DMAX||500;
}}

/* ---------- Navegación ---------- */
const SECCIONES=[['ubicacion','Ubicación / Mapa'],['resumen','Resumen'],['columna','Columna y capas'],
  ['transporte','Transporte'],['desplazamiento','Desplazamiento lateral'],
  ['capitulo','Capítulo hidrogeológico'],['referencias','Referencias']];
function initNav(){{
  const nav=document.getElementById('nav');
  SECCIONES.forEach(([id,txt],i)=>{{
    const b=document.createElement('button');b.textContent=txt;
    if(i===0)b.classList.add('activo');
    b.onclick=()=>{{
      document.querySelectorAll('nav button').forEach(x=>x.classList.remove('activo'));
      document.querySelectorAll('section').forEach(x=>x.classList.remove('activa'));
      b.classList.add('activo');
      document.getElementById('sec-'+id).classList.add('activa');
      if(id==='transporte')dibujarTransporte();
      if(id==='desplazamiento')dibujarDesplazamiento();
      if(id==='columna')dibujarColumna();
      if(id==='ubicacion'&&MAPA)setTimeout(()=>MAPA.invalidateSize(),100);
    }};
    nav.appendChild(b);
  }});
}}

/* ---------- SVG helpers ---------- */
function svgPlot(w,h,pad){{return {{w,h,pad,
  X:(v,xmin,xmax)=>pad.l+(v-xmin)/(xmax-xmin)*(w-pad.l-pad.r),
  Y:(v,ymin,ymax)=>h-pad.b-(v-ymin)/(ymax-ymin)*(h-pad.t-pad.b)}};}}
function ejes(p,xmin,xmax,ymin,ymax,xlab,ylab,nx=5,ny=5){{
  let s=`<rect x="${{p.pad.l}}" y="${{p.pad.t}}" width="${{p.w-p.pad.l-p.pad.r}}" height="${{p.h-p.pad.t-p.pad.b}}" fill="#0c1825" stroke="#2b3a4d"/>`;
  for(let i=0;i<=nx;i++){{const v=xmin+(xmax-xmin)*i/nx,x=p.X(v,xmin,xmax);
    s+=`<line x1="${{x}}" y1="${{p.pad.t}}" x2="${{x}}" y2="${{p.h-p.pad.b}}" stroke="#1c2a3a"/>`;
    s+=`<text x="${{x}}" y="${{p.h-p.pad.b+16}}" font-size="11" text-anchor="middle" fill="#9fb3c8">${{fmt(v,1)}}</text>`;}}
  for(let i=0;i<=ny;i++){{const v=ymin+(ymax-ymin)*i/ny,y=p.Y(v,ymin,ymax);
    s+=`<line x1="${{p.pad.l}}" y1="${{y}}" x2="${{p.w-p.pad.r}}" y2="${{y}}" stroke="#1c2a3a"/>`;
    s+=`<text x="${{p.pad.l-6}}" y="${{y+4}}" font-size="11" text-anchor="end" fill="#9fb3c8">${{fmt(v,2)}}</text>`;}}
  s+=`<text x="${{(p.w+p.pad.l-p.pad.r)/2}}" y="${{p.h-2}}" font-size="12" text-anchor="middle" fill="#e6edf3">${{xlab}}</text>`;
  s+=`<text x="14" y="${{p.h/2}}" font-size="12" text-anchor="middle" fill="#e6edf3" transform="rotate(-90,14,${{p.h/2}})">${{ylab}}</text>`;
  return s;
}}
function linea(p,xs,ys,xmin,xmax,ymin,ymax,color,w=2){{
  let d='';xs.forEach((x,i)=>{{d+=(i?'L':'M')+p.X(x,xmin,xmax).toFixed(1)+' '+p.Y(ys[i],ymin,ymax).toFixed(1)+' ';}});
  return `<path d="${{d}}" fill="none" stroke="${{color}}" stroke-width="${{w}}"/>`;
}}

/* ---------- Resumen ---------- */
function dibujarResumen(){{
  document.getElementById('hdrSub').textContent=CFG.nombre+(CFG.descripcion?' · '+CFG.descripcion:'');
  document.getElementById('descripcion').textContent=CFG.descripcion||'';
  const s=sistemaEquivalente();
  const tj=[
    ['Nº de capas',CAPAS.length,''],
    ['Espesor total',fmt(s.B,1),'m'],
    ['Transmisividad total',fmt(s.T*86400,2),'m²/día'],
    ['K horizontal equiv.',fmt(s.Kh,2),'m/s'],
    ['K vertical equiv.',fmt(s.Kv,2),'m/s'],
    ['Anisotropía Kh/Kv',fmt(s.aniso,1),''],
    ['Porosidad media',fmt(s.ne,2),'-'],
    ['Gradiente hidráulico',GRAD!=null?fmt(GRAD,4):'no definido',''],
  ];
  document.getElementById('tarjetas').innerHTML=tj.map(([k,v,u])=>
    `<div class="card"><div class="k">${{k}}</div><div class="v">${{v}}</div><div class="u">${{u}}</div></div>`).join('');
  const ng=document.getElementById('notaGradiente');
  if(GRAD!=null){{
    const c=CAPAS[CAPA_T];const vc=GRAD*c.K/c.ne/c.R*CFG.segPorAnio;
    ng.innerHTML=`Con gradiente i=${{fmt(GRAD,4)}}, el contaminante avanza en la capa de transporte («${{c.nombre}}») a ≈ <strong>${{fmt(vc,2)}} m/año</strong> (v contaminante). Tiempo de simulación: ${{TMAX}} años.`;
    ng.style.display='block';
  }} else {{ng.style.display='none';}}
}}

/* ---------- Columna / capas ---------- */
function dibujarTablaCapas(){{
  const tb=document.querySelector('#tablaCapas tbody');tb.innerHTML='';
  CAPAS.forEach((c,i)=>{{
    const k_darcy=c.K*MU/(RHO*G)/DARCY;
    const T=c.K*c.espesor*86400;
    const tr=document.createElement('tr');
    tr.innerHTML=`
      <td><input value="${{c.nombre}}" onchange="upd(${{i}},'nombre',this.value)"></td>
      <td><input type="number" step="0.1" value="${{c.espesor}}" onchange="upd(${{i}},'espesor',+this.value)"></td>
      <td><input type="number" step="1e-7" value="${{c.K}}" onchange="upd(${{i}},'K',+this.value)"></td>
      <td><input type="number" step="0.01" value="${{c.ne}}" onchange="upd(${{i}},'ne',+this.value)"></td>
      <td><input type="number" step="0.1" value="${{c.alfaL}}" onchange="upd(${{i}},'alfaL',+this.value)"></td>
      <td><input type="number" step="0.001" value="${{c.alfaV}}" onchange="upd(${{i}},'alfaV',+this.value)"></td>
      <td>${{fmt(k_darcy,2)}}</td><td>${{fmt(T,2)}}</td>
      <td><button class="btn sec" onclick="delCapa(${{i}})">✕</button></td>`;
    tb.appendChild(tr);
  }});
  document.getElementById('nCapasTag').textContent=CAPAS.length+' capas';
}}
function upd(i,campo,val){{CAPAS[i][campo]=val;recalcular();}}
function addCapa(){{CAPAS.push({{nombre:'Capa '+(CAPAS.length+1),espesor:5,K:1e-5,ne:0.25,alfaL:1,alfaT:0.1,alfaV:0.01,R:1,color:PALETA[CAPAS.length%10]}});recalcular();}}
function delCapa(i){{if(CAPAS.length<=1)return;CAPAS.splice(i,1);if(CAPA_T>=CAPAS.length)CAPA_T=0;recalcular();}}
function resetCapas(){{CAPAS=JSON.parse(JSON.stringify(CFG.capas));CAPA_T=CFG.capaTransporte;recalcular();}}

function dibujarColumna(){{
  dibujarTablaCapas();
  const s=sistemaEquivalente();
  const H=420,W=240,x0=70,bw=120;
  let svg=`<svg viewBox="0 0 ${{W}} ${{H}}">`;
  let y=20;const esc=(H-40)/s.B;
  CAPAS.forEach((c,i)=>{{
    const h=c.espesor*esc;const col=c.color||PALETA[i%10];
    svg+=`<rect x="${{x0}}" y="${{y}}" width="${{bw}}" height="${{h}}" fill="${{col}}" stroke="#0c1825"/>`;
    svg+=`<text x="${{x0+bw/2}}" y="${{y+h/2+4}}" font-size="11" text-anchor="middle" fill="#102132">${{c.nombre}}</text>`;
    svg+=`<text x="${{x0-6}}" y="${{y+4}}" font-size="9" text-anchor="end" fill="#9fb3c8">${{fmt(yProf(i),1)}} m</text>`;
    svg+=`<text x="${{x0+bw+6}}" y="${{y+h/2+3}}" font-size="9" fill="#9fb3c8">${{fmt(c.K,1)}} m/s</text>`;
    y+=h;
  }});
  svg+=`<text x="${{x0-6}}" y="${{y+4}}" font-size="9" text-anchor="end" fill="#9fb3c8">${{fmt(s.B,1)}} m</text>`;
  svg+='</svg>';
  document.getElementById('columnaSVG').innerHTML=svg;
  document.getElementById('leyendaK').innerHTML=CAPAS.map((c,i)=>
    `<span><span class="sw" style="background:${{c.color||PALETA[i%10]}}"></span>${{c.nombre}}</span>`).join('');
  const tj=[
    ['Espesor total',fmt(s.B,1),'m'],['Kh equiv.',fmt(s.Kh,2),'m/s'],
    ['Kv equiv.',fmt(s.Kv,2),'m/s'],['Anisotropía',fmt(s.aniso,1),'Kh/Kv'],
    ['Transmisividad',fmt(s.T*86400,2),'m²/día'],['Porosidad media',fmt(s.ne,2),'-'],
  ];
  document.getElementById('tarjetasSistema').innerHTML=tj.map(([k,v,u])=>
    `<div class="card"><div class="k">${{k}}</div><div class="v">${{v}}</div><div class="u">${{u}}</div></div>`).join('');
}}
function yProf(i){{let p=0;for(let j=0;j<i;j++)p+=CAPAS[j].espesor;return p;}}

/* ---------- Transporte ---------- */
function dibujarTransporte(){{
  document.getElementById('inpGrad').value=GRAD!=null?GRAD:'';
  document.getElementById('inpC0').value=C0;
  const sel=document.getElementById('selCapa');
  sel.innerHTML=CAPAS.map((c,i)=>`<option value="${{i}}" ${{i===CAPA_T?'selected':''}}>${{c.nombre}}</option>`).join('');
  const hayGrad=GRAD!=null&&GRAD>0;
  document.getElementById('panelSinGrad').style.display=hayGrad?'none':'block';
  ['panelTransporte','panelBreak','panelPenacho','panelPerfil'].forEach(id=>document.getElementById(id).style.display=hayGrad?'block':'none');
  if(!hayGrad)return;
  const c=CAPAS[CAPA_T];
  const v=GRAD*c.K/c.ne, DL=c.alfaL*v, R=c.R;
  DMAX=distanciaMax();
  const frac=+document.getElementById('sliderT').value;
  const t=frac*TMAX*CFG.segPorAnio;
  document.getElementById('lblT').textContent=fmt(frac*TMAX,2)+' años';
  const N=200,xs=[],ys=[];
  for(let i=0;i<=N;i++){{const x=DMAX*i/N;xs.push(x);ys.push(ogataBanks(x,t,v,DL,R));}}
  const p=svgPlot(720,300,{{l:55,r:20,t:14,b:40}});
  let svg=`<svg viewBox="0 0 720 300">`+ejes(p,0,DMAX,0,1,'Distancia x (m)','C/C&#8320;');
  svg+=`<line x1="${{p.pad.l}}" y1="${{p.Y(0.5,0,1)}}" x2="${{p.w-p.pad.r}}" y2="${{p.Y(0.5,0,1)}}" stroke="#ffb74d" stroke-dasharray="4 4"/>`;
  let d='M'+p.X(0,0,DMAX)+' '+p.Y(0,0,1)+' ';xs.forEach((x,i)=>d+='L'+p.X(x,0,DMAX).toFixed(1)+' '+p.Y(ys[i],0,1).toFixed(1)+' ');
  d+='L'+p.X(DMAX,0,DMAX)+' '+p.Y(0,0,1)+' Z';
  svg+=`<path d="${{d}}" fill="#4fc3f733"/>`;
  svg+=linea(p,xs,ys,0,DMAX,0,1,'#4fc3f7',2.5);
  svg+='</svg>';
  document.getElementById('perfilSVG').innerHTML=svg;
  const vc=v/R;
  const xFrente=interpFrente(xs,ys);
  const tj=[
    ['v real',fmt(v*CFG.segPorAnio,2),'m/año'],
    ['v contaminante',fmt(vc*CFG.segPorAnio,2),'m/año'],
    ['Dispersión D_L',fmt(DL,2),'m²/s'],
    ['Factor retardo R',fmt(R,2),'-'],
    ['Frente 50% (t sel.)',fmt(xFrente,1),'m'],
    ['Dispersividad α_L',fmt(c.alfaL,2),'m'],
  ];
  document.getElementById('tarjetasTrans').innerHTML=tj.map(([k,v,u])=>
    `<div class="card"><div class="k">${{k}}</div><div class="v">${{v}}</div><div class="u">${{u}}</div></div>`).join('');
  dibujarBreakthrough(v,DL,R);
  dibujarPenacho(v,c,R);
  dibujarPerfil(v,R);
}}
function interpFrente(xs,ys){{for(let i=1;i<ys.length;i++){{if(ys[i]<=0.5){{const f=(0.5-ys[i-1])/(ys[i]-ys[i-1]);return xs[i-1]+f*(xs[i]-xs[i-1]);}}}}return 0;}}

function dibujarBreakthrough(v,DL,R){{
  const xobs=Math.min(DMAX*0.5,100);
  const N=120,ts=[],ys=[];
  for(let i=1;i<=N;i++){{const ta=TMAX*i/N;ts.push(ta);ys.push(ogataBanks(xobs,ta*CFG.segPorAnio,v,DL,R));}}
  const p=svgPlot(720,260,{{l:55,r:20,t:14,b:40}});
  let svg=`<svg viewBox="0 0 720 260">`+ejes(p,0,TMAX,0,1,'Tiempo (años)','C/C&#8320; en x='+fmt(xobs,0)+' m');
  svg+=linea(p,ts,ys,0,TMAX,0,1,'#81c784',2.5);
  svg+='</svg>';
  document.getElementById('breakSVG').innerHTML=svg;
}}

function dibujarPenacho(v,c,R){{
  const cv=document.getElementById('canvasPenacho');
  const Wpx=720,Hpx=260;cv.width=Wpx;cv.height=Hpx;
  const ctx=cv.getContext('2d');
  const t=TMAX*CFG.segPorAnio,vt=v*t/R;
  const aL=c.alfaL,aT=c.alfaT;
  const ancho=Math.max(DMAX*0.04,2);
  const yExt=Math.max(DMAX*0.18,10);
  const img=ctx.createImageData(Wpx,Hpx);
  for(let px=0;px<Wpx;px++){{
    const x=0.1+DMAX*px/Wpx;
    const longT=0.5*erfc((x-vt)/(2*Math.sqrt(aL*Math.max(x,1e-9))));
    const sig=Math.sqrt(Math.max(aT*x,1e-12));
    for(let py=0;py<Hpx;py++){{
      const y=-yExt+2*yExt*py/Hpx;
      const tr=0.5*(erfc((y-ancho/2)/(2*sig))-erfc((y+ancho/2)/(2*sig)));
      let C=Math.max(0,Math.min(1,longT*tr));
      const col=colormap(C);
      const o=(py*Wpx+px)*4;
      img.data[o]=col[0];img.data[o+1]=col[1];img.data[o+2]=col[2];img.data[o+3]=255;
    }}
  }}
  ctx.putImageData(img,0,0);
  ctx.fillStyle='#fff';ctx.font='12px sans-serif';
  ctx.fillText('Fuente',4,Hpx/2-4);ctx.fillText('Flujo →',Wpx-70,18);
  document.getElementById('leyendaPenacho').innerHTML=
    `<span class="muted">Penacho a t=${{TMAX}} años · eje X: 0–${{fmt(DMAX,0)}} m · eje Y: ±${{fmt(yExt,0)}} m</span>`+
    [0,0.25,0.5,0.75,1].map(cc=>{{const k=colormap(cc);return `<span><span class="sw" style="background:rgb(${{k[0]}},${{k[1]}},${{k[2]}})"></span>${{cc}}</span>`;}}).join('');
}}

function dibujarPerfil(v,R){{
  const cv=document.getElementById('canvasPerfil');
  const Wpx=720,Hpx=260;cv.width=Wpx;cv.height=Hpx;
  const ctx=cv.getContext('2d');
  const t=TMAX*CFG.segPorAnio,vt=v*t/R;
  const c=CAPAS[CAPA_T];
  const aL=c.alfaL,aV=c.alfaV;
  // Espesor total y profundidad del centro de la fuente (capa de transporte).
  let B=0;CAPAS.forEach(cc=>B+=cc.espesor);
  let zTecho=0;for(let i=0;i<CAPA_T;i++)zTecho+=CAPAS[i].espesor;
  const zCentro=zTecho+c.espesor/2, alto=c.espesor;
  const img=ctx.createImageData(Wpx,Hpx);
  for(let px=0;px<Wpx;px++){{
    const x=0.1+DMAX*px/Wpx;
    const longT=0.5*erfc((x-vt)/(2*Math.sqrt(aL*Math.max(x,1e-9))));
    const sig=Math.sqrt(Math.max(aV*x,1e-12));
    for(let py=0;py<Hpx;py++){{
      const z=B*py/Hpx;  // profundidad creciente hacia abajo
      const vert=0.5*(erfc((z-(zCentro+alto/2))/(2*sig))-erfc((z-(zCentro-alto/2))/(2*sig)));
      let C=Math.max(0,Math.min(1,longT*vert));
      const col=colormap(C);
      const o=(py*Wpx+px)*4;
      img.data[o]=col[0];img.data[o+1]=col[1];img.data[o+2]=col[2];img.data[o+3]=255;
    }}
  }}
  ctx.putImageData(img,0,0);
  // Contactos entre capas (líneas) y etiquetas.
  ctx.strokeStyle='rgba(255,255,255,0.55)';ctx.fillStyle='#fff';ctx.font='10px sans-serif';
  let zAcum=0;
  CAPAS.forEach((cc,i)=>{{
    zAcum+=cc.espesor;const py=zAcum/B*Hpx;
    ctx.setLineDash([4,3]);ctx.beginPath();ctx.moveTo(0,py);ctx.lineTo(Wpx,py);ctx.stroke();
    ctx.fillText(cc.nombre,6,(zAcum-cc.espesor/2)/B*Hpx+3);
  }});
  ctx.setLineDash([]);
  ctx.fillText('Flujo →',Wpx-70,14);
  document.getElementById('leyendaPerfil').innerHTML=
    `<span class="muted">Perfil x–z a t=${{TMAX}} años · X: 0–${{fmt(DMAX,0)}} m · profundidad: 0–${{fmt(B,1)}} m · α_V=${{fmt(aV,3)}} m</span>`+
    [0,0.25,0.5,0.75,1].map(cc=>{{const k=colormap(cc);return `<span><span class="sw" style="background:rgb(${{k[0]}},${{k[1]}},${{k[2]}})"></span>${{cc}}</span>`;}}).join('');
}}
function colormap(t){{
  t=Math.max(0,Math.min(1,t));
  const stops=[[12,24,37],[33,102,172],[79,195,247],[255,235,59],[244,67,54]];
  const f=t*(stops.length-1),i=Math.floor(f),fr=f-i;
  if(i>=stops.length-1)return stops[stops.length-1];
  return [0,1,2].map(j=>Math.round(stops[i][j]+(stops[i+1][j]-stops[i][j])*fr));
}}

/* ---------- Desplazamiento lateral ---------- */
function dibujarDesplazamiento(){{
  const hayGrad=GRAD!=null&&GRAD>0;
  document.getElementById('panelDespVacio').style.display=hayGrad?'none':'block';
  document.getElementById('panelDesp').style.display=hayGrad?'block':'none';
  if(!hayGrad)return;
  let Lmax=0;const curvas=CAPAS.map((c,i)=>{{
    const vc=GRAD*c.K/c.ne/c.R;const ys=[],ts=[];
    for(let k=0;k<=50;k++){{const ta=TMAX*k/50;ts.push(ta);const L=vc*ta*CFG.segPorAnio;ys.push(L);Lmax=Math.max(Lmax,L);}}
    return {{nombre:c.nombre,color:c.color||PALETA[i%10],ts,ys,vc}};
  }});
  const p=svgPlot(720,320,{{l:65,r:20,t:14,b:40}});
  let svg=`<svg viewBox="0 0 720 320">`+ejes(p,0,TMAX,0,Lmax*1.05||1,'Tiempo (años)','Desplazamiento lateral L (m)');
  curvas.forEach(cu=>{{svg+=linea(p,cu.ts,cu.ys,0,TMAX,0,Lmax*1.05||1,cu.color,2.5);}});
  svg+='</svg>';
  document.getElementById('despSVG').innerHTML=svg;
  document.getElementById('leyendaDesp').innerHTML=curvas.map(cu=>
    `<span><span class="sw" style="background:${{cu.color}}"></span>${{cu.nombre}}</span>`).join('');
  const tb=document.querySelector('#tablaDesp tbody');tb.innerHTML='';
  CAPAS.forEach(c=>{{
    const q=GRAD*c.K, v=q/c.ne, vc=v/c.R, L=vc*TMAX*CFG.segPorAnio;
    const tr=document.createElement('tr');
    tr.innerHTML=`<td>${{c.nombre}}</td><td>${{fmt(q*CFG.segPorAnio,2)}}</td>
      <td>${{fmt(v*CFG.segPorAnio,2)}}</td><td>${{fmt(c.R,2)}}</td>
      <td>${{fmt(vc*CFG.segPorAnio,2)}}</td><td>${{fmt(L,1)}}</td>`;
    tb.appendChild(tr);
  }});
}}

/* ---------- Recalcular global ---------- */
function recalcular(){{
  DMAX=distanciaMax();
  dibujarResumen();dibujarColumna();
  if(document.getElementById('sec-transporte').classList.contains('activa'))dibujarTransporte();
  if(document.getElementById('sec-desplazamiento').classList.contains('activa'))dibujarDesplazamiento();
}}

/* ---------- Eventos ---------- */
document.getElementById('sliderT').addEventListener('input',dibujarTransporte);
document.getElementById('inpGrad').addEventListener('change',e=>{{GRAD=e.target.value===''?null:+e.target.value;recalcular();dibujarTransporte();}});
document.getElementById('inpC0').addEventListener('change',e=>{{C0=+e.target.value;recalcular();}});
document.getElementById('selCapa').addEventListener('change',e=>{{CAPA_T=+e.target.value;dibujarTransporte();}});

/* ---------- Mapa interactivo (Leaflet) ---------- */
let MAPA=null, CAPA_BASE=null, CAPA_PENACHO=null, MARCADOR=null;
let BASEMAP_ACT=(CFG.geo&&CFG.geo.basemap)||'topografia';

function defWkid(){{
  // origen por defecto: el del modelo, o WGS84 en (0,0) si no hay geo.
  if(CFG.geo) return {{x:CFG.geo.origen_x,y:CFG.geo.origen_y,wkid:CFG.geo.wkid,az:CFG.geo.azimut_flujo_grados}};
  return {{x:-3.7038,y:40.4168,wkid:4326,az:CFG.azimutFlujo||90}};
}}

function aLonLat(x,y,wkid){{
  if(wkid===4326) return [x,y];
  if(wkid===3857){{const R=6378137;return [x/R*180/Math.PI,(2*Math.atan(Math.exp(y/R))-Math.PI/2)*180/Math.PI];}}
  // Cualquier EPSG vía proj4 (usa la BD pública epsg.io si está disponible).
  if(window.proj4){{
    try{{
      if(!proj4.defs('EPSG:'+wkid)){{
        // proj4 trae 4326/3857; para otros se requiere la definición. Se intenta
        // una def UTM genérica si el WKID es de la familia 326xx/327xx/258xx.
      }}
      return proj4('EPSG:'+wkid,'EPSG:4326',[x,y]);
    }}catch(e){{}}
  }}
  return null;
}}

// Definiciones proj4 para los WKID del catálogo (para no depender de la red).
function registrarProj(){{
  if(!window.proj4) return;
  const defs={{
    25829:"+proj=utm +zone=29 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs",
    25830:"+proj=utm +zone=30 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs",
    25831:"+proj=utm +zone=31 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs",
    23030:"+proj=utm +zone=30 +ellps=intl +towgs84=-87,-98,-121,0,0,0,0 +units=m +no_defs",
    32630:"+proj=utm +zone=30 +datum=WGS84 +units=m +no_defs",
    32631:"+proj=utm +zone=31 +datum=WGS84 +units=m +no_defs",
    32719:"+proj=utm +zone=19 +south +datum=WGS84 +units=m +no_defs",
    32718:"+proj=utm +zone=18 +south +datum=WGS84 +units=m +no_defs",
    27700:"+proj=tmerc +lat_0=49 +lon_0=-2 +k=0.9996012717 +x_0=400000 +y_0=-100000 +ellps=airy +towgs84=446.448,-125.157,542.06,0.15,0.247,0.842,-20.489 +units=m +no_defs",
    2154:"+proj=lcc +lat_1=49 +lat_2=44 +lat_0=46.5 +lon_0=3 +x_0=700000 +y_0=6600000 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs",
    5070:"+proj=aea +lat_1=29.5 +lat_2=45.5 +lat_0=23 +lon_0=-96 +x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs",
    26910:"+proj=utm +zone=10 +datum=NAD83 +units=m +no_defs"
  }};
  for(const k in defs){{ if(!proj4.defs('EPSG:'+k)) proj4.defs('EPSG:'+k, defs[k]); }}
}}

function destinoGeo(lon,lat,az,d){{
  const R=6378137,a=az*Math.PI/180,la=lat*Math.PI/180,lo=lon*Math.PI/180,dr=d/R;
  const la2=Math.asin(Math.sin(la)*Math.cos(dr)+Math.cos(la)*Math.sin(dr)*Math.cos(a));
  const lo2=lo+Math.atan2(Math.sin(a)*Math.sin(dr)*Math.cos(la),Math.cos(dr)-Math.sin(la)*Math.sin(la2));
  return [lo2*180/Math.PI,la2*180/Math.PI];
}}
function huellaPenacho(lon,lat,az,L,semi){{
  const perp=az+90;
  const oi=destinoGeo(lon,lat,perp,semi), od=destinoGeo(lon,lat,perp-180,semi);
  const pt=destinoGeo(lon,lat,az,L);
  const pi=destinoGeo(pt[0],pt[1],perp,semi), pd=destinoGeo(pt[0],pt[1],perp-180,semi);
  return [[oi[1],oi[0]],[pi[1],pi[0]],[pd[1],pd[0]],[od[1],od[0]]];
}}

function capaBase(clave){{
  const bm=CFG.basemaps[clave]||CFG.basemaps.topografia;
  return L.tileLayer(bm.url,{{maxZoom:19,attribution:bm.atribucion}});
}}

function initBasemapSwitcher(){{
  const cont=document.getElementById('basemapSw');
  cont.innerHTML='';
  Object.keys(CFG.basemaps).forEach(clave=>{{
    const b=document.createElement('button');b.textContent=CFG.basemaps[clave].etiqueta;
    if(clave===BASEMAP_ACT)b.classList.add('activo');
    b.onclick=()=>{{
      BASEMAP_ACT=clave;
      document.querySelectorAll('#basemapSw button').forEach(x=>x.classList.remove('activo'));
      b.classList.add('activo');
      if(CAPA_BASE)MAPA.removeLayer(CAPA_BASE);
      CAPA_BASE=capaBase(clave).addTo(MAPA);
    }};
    cont.appendChild(b);
  }});
}}

function initWkidSelect(){{
  const sel=document.getElementById('selWkid');
  sel.innerHTML=CFG.wkidCatalogo.map(w=>`<option value="${{w.wkid}}">${{w.wkid}} — ${{w.nombre}}</option>`).join('');
  const d=defWkid();
  document.getElementById('inpOX').value=d.x;
  document.getElementById('inpOY').value=d.y;
  document.getElementById('inpAz').value=d.az;
  sel.value=String(d.wkid);
}}

function longitudPenacho(){{
  // longitud para la huella: extensión autoajustada si existe, si no avance advectivo.
  if(DATOS.transporte&&DATOS.transporte.extension_penacho_m) return DATOS.transporte.extension_penacho_m;
  const c=CAPAS[CAPA_T];
  if(GRAD) return GRAD*c.K/c.ne/c.R*TMAX*CFG.segPorAnio;
  return 0;
}}

function recentrarMapa(){{
  registrarProj();
  const x=+document.getElementById('inpOX').value;
  const y=+document.getElementById('inpOY').value;
  const wkid=+document.getElementById('selWkid').value;
  const az=+document.getElementById('inpAz').value;
  const ll=aLonLat(x,y,wkid);
  const nota=document.getElementById('notaMapa');
  if(!ll||!isFinite(ll[0])||!isFinite(ll[1])){{
    nota.innerHTML=`No se pudo convertir el origen desde EPSG:${{wkid}} a longitud/latitud. `+
      `Prueba con WKID 4326 (lon/lat) o 3857, o comprueba las coordenadas.`;
    return;
  }}
  const [lon,lat]=ll;
  if(!MAPA){{
    MAPA=L.map('mapa').setView([lat,lon],14);
    CAPA_BASE=capaBase(BASEMAP_ACT).addTo(MAPA);
  }} else {{ MAPA.setView([lat,lon],MAPA.getZoom()||14); }}
  if(MARCADOR)MAPA.removeLayer(MARCADOR);
  MARCADOR=L.marker([lat,lon]).addTo(MAPA)
    .bindPopup(`<b>Origen de los datos</b><br>${{lat.toFixed(6)}}, ${{lon.toFixed(6)}}<br>EPSG:${{wkid}}`);
  if(CAPA_PENACHO)MAPA.removeLayer(CAPA_PENACHO);
  const L_pen=longitudPenacho();
  if(L_pen>0){{
    const semi=Math.max(L_pen*0.06,1);
    const poly=huellaPenacho(lon,lat,az,L_pen,semi);
    CAPA_PENACHO=L.polygon(poly,{{color:'#ffb74d',weight:2,fillColor:'#ff7043',fillOpacity:0.35}})
      .addTo(MAPA).bindPopup(`Huella del penacho · ${{(L_pen).toFixed(0)}} m · rumbo ${{az}}°`);
    const pt=destinoGeo(lon,lat,az,L_pen);
    L.circleMarker([pt[1],pt[0]],{{radius:5,color:'#fff',fillColor:'#ff7043',fillOpacity:1}})
      .addTo(MAPA).bindPopup('Frente del penacho (C/C₀ ≈ 0,01)');
    MARCADOR._penachoCapa=CAPA_PENACHO;
    MAPA.fitBounds(L.polygon(poly).getBounds().pad(0.5));
  }}
  nota.innerHTML=`Origen: <strong>${{lat.toFixed(6)}}, ${{lon.toFixed(6)}}</strong> `+
    `(EPSG:${{wkid}}) · mapa base «${{CFG.basemaps[BASEMAP_ACT].etiqueta}}»`+
    (L_pen>0?` · huella del penacho ${{L_pen.toFixed(0)}} m hacia ${{az}}°.`:` · sin penacho (define gradiente).`);
  setTimeout(()=>MAPA.invalidateSize(),50);
}}

function initMapa(){{
  if(!window.L){{document.getElementById('mapa').innerHTML=
    '<p class="muted" style="padding:20px">El mapa requiere conexión a internet (Leaflet).</p>';return;}}
  initWkidSelect();initBasemapSwitcher();recentrarMapa();
}}

/* ---------- Init ---------- */
initNav();initMapa();dibujarResumen();dibujarColumna();
</script>
</body>
</html>
"""
