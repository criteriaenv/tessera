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
        "segPorAnio": SEG_POR_ANIO,
        "capas": capas,
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
</style>
</head>
<body>
<header>
  <h1>Hidrogeología — Tránsito de contaminantes</h1>
  <div class="sub" id="hdrSub"></div>
</header>
<nav id="nav"></nav>
<main>
  <section id="sec-resumen" class="activa">
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
      <h3 style="margin-top:0">Penacho en planta (modelo de Domenico, 1987)</h3>
      <canvas id="canvasPenacho" style="width:100%;border-radius:8px"></canvas>
      <div class="legend" id="leyendaPenacho"></div>
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
const SECCIONES=[['resumen','Resumen'],['columna','Columna y capas'],
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
      <td>${{fmt(k_darcy,2)}}</td><td>${{fmt(T,2)}}</td>
      <td><button class="btn sec" onclick="delCapa(${{i}})">✕</button></td>`;
    tb.appendChild(tr);
  }});
  document.getElementById('nCapasTag').textContent=CAPAS.length+' capas';
}}
function upd(i,campo,val){{CAPAS[i][campo]=val;recalcular();}}
function addCapa(){{CAPAS.push({{nombre:'Capa '+(CAPAS.length+1),espesor:5,K:1e-5,ne:0.25,alfaL:1,alfaT:0.1,R:1,color:PALETA[CAPAS.length%10]}});recalcular();}}
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
  ['panelTransporte','panelBreak','panelPenacho'].forEach(id=>document.getElementById(id).style.display=hayGrad?'block':'none');
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

/* ---------- Init ---------- */
initNav();dibujarResumen();dibujarColumna();
</script>
</body>
</html>
"""
