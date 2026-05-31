# Hidrogeología — Tránsito de contaminantes

**Análisis y visualización del tránsito de contaminantes en hidrogeología.**

Módulo independiente (dentro de este repositorio) que modela un sistema
acuífero **multicapa** y simula el **transporte advectivo-dispersivo** de un
contaminante. Cuando se conoce el **gradiente hidráulico**, calcula además el
**desplazamiento lateral** (avance horizontal) del contaminante. Todos los
resultados se presentan gráficamente y se exportan en tres formatos:

- 🌐 **Informe HTML interactivo** (autónomo, funciona sin conexión)
- 📄 **Informe técnico PDF** (multipágina, con figuras y tablas)
- 📦 **Artefacto de resultados JSON** (datos reutilizables)

Cada salida incluye las **referencias bibliográficas** y un **capítulo
hidrogeológico** que interpreta el modelo.

> Nota: este módulo no tiene relación con el modelo de teledetección TESSERA
> del resto del repositorio; comparte únicamente el contenedor del proyecto.

---

## Características

- **Número de capas configurable**, cada una con **nombre**, **espesor** y
  **permeabilidad** (conductividad hidráulica `K`).
- Datos opcionales por capa: porosidad eficaz, dispersividad, densidad seca y
  coeficiente de reparto `K_d` (factor de retardo por sorción).
- **Propiedades equivalentes** del sistema estratificado: transmisividad total,
  `K` horizontal/vertical equivalente y anisotropía.
- **Transporte de contaminantes** mediante la solución analítica de
  **Ogata & Banks (1961)**: perfiles `C(x)`, curvas de llegada `C(t)` y
  **penacho 2D en planta** (**Domenico, 1987**).
- **Desplazamiento lateral** opcional `L(t) = (K·i/n_e)·t / R` por capa cuando
  se aporta el gradiente hidráulico.
- HTML **interactivo**: edición en vivo de capas, control de tiempo, selección
  de capa de transporte y recálculo instantáneo (matemática reimplementada en
  JavaScript, sin librerías externas).

---

## Instalación

Requiere Python 3.9+ y tres dependencias científicas habituales:

```bash
pip install -r hidrogeologia/requirements.txt   # numpy, scipy, matplotlib
```

## Uso

Desde la raíz del repositorio:

```bash
# Caso de ejemplo incorporado (TCE en acuífero multicapa)
python -m hidrogeologia

# Caso propio definido en JSON
python -m hidrogeologia hidrogeologia/examples/ejemplo_acuifero.json -o salidas

# Con prefijo de archivos personalizado
python -m hidrogeologia hidrogeologia/examples/ejemplo_acuifero.json -o salidas --prefijo mi_caso
```

Genera `mi_caso.html`, `mi_caso.pdf` y `mi_caso.json` en la carpeta de salida.

### Definición de un caso (JSON)

```json
{
  "nombre": "Mi emplazamiento",
  "descripcion": "Acuífero detrítico multicapa...",
  "gradiente_hidraulico": 0.008,
  "concentracion_fuente": 500.0,
  "tiempo_max_anios": 20.0,
  "capas": [
    {"nombre": "Arena",   "espesor_m": 8.0, "K_m_s": 2e-3, "porosidad_eficaz": 0.22,
     "dispersividad_long_m": 5.0, "densidad_seca_kg_m3": 1700, "kd_m3_kg": 0.00012},
    {"nombre": "Arcilla", "espesor_m": 5.0, "K_m_s": 1e-8, "porosidad_eficaz": 0.45}
  ]
}
```

| Campo | Obligatorio | Descripción | Unidad |
|---|---|---|---|
| `nombre` | sí | Nombre de la capa | — |
| `espesor_m` | sí | Espesor (potencia) | m |
| `K_m_s` | sí | Conductividad hidráulica (permeabilidad) | m/s |
| `porosidad_eficaz` | no (0,25) | Porosidad eficaz `n_e` | — |
| `dispersividad_long_m` | no | Dispersividad longitudinal `α_L` | m |
| `densidad_seca_kg_m3` | no | Densidad aparente seca `ρ_b` | kg/m³ |
| `kd_m3_kg` | no | Coeficiente de reparto `K_d` | m³/kg |

A nivel de caso, `gradiente_hidraulico` es **opcional**: si se omite, se
calculan las propiedades del sistema y la columna, pero **no** el transporte ni
el desplazamiento lateral (que dependen del flujo).

### Uso como librería

```python
from hidrogeologia import ModeloHidrogeologico, Capa
from hidrogeologia.html_report import generar_html
from hidrogeologia.pdf_report import generar_pdf

modelo = ModeloHidrogeologico(
    nombre="Caso",
    capas=[Capa("Arena", 8.0, 2e-3, 0.22, dispersividad_long_m=5.0)],
    gradiente_hidraulico=0.008,
    concentracion_fuente=500.0,
)
res = modelo.calcular()
generar_html(modelo, res, "caso.html")
generar_pdf(modelo, res, "caso.pdf")
```

---

## Fundamento científico

| Proceso | Ecuación | Referencia |
|---|---|---|
| Flujo (Darcy) | `q = K·i` | Darcy (1856) |
| Velocidad real | `v = K·i / n_e` | Bear (1972) |
| Permeabilidad intrínseca | `k = K·μ / (ρ·g)` | — |
| `K` horiz. equivalente | `Kh = Σ(K_i·b_i) / Σ(b_i)` | Freeze & Cherry (1979) |
| `K` vert. equivalente | `Kv = Σ(b_i) / Σ(b_i/K_i)` | Freeze & Cherry (1979) |
| Factor de retardo | `R = 1 + ρ_b·K_d / n_e` | Fetter (2001) |
| Transporte 1D (ADE) | solución de fuente continua | Ogata & Banks (1961) |
| Penacho 2D | dispersión transversal | Domenico (1987) |

> ⚠️ Modelo **analítico** de cribado preliminar. Asume medio homogéneo por
> capa, flujo permanente y uniforme y fuente constante. No sustituye a una
> modelización numérica (p. ej. MODFLOW/MT3D) ni a la caracterización de campo.

La lista completa de referencias y el capítulo hidrogeológico se incluyen en
cada informe (HTML y PDF) y en `hidrogeologia/referencias.py`.

---

## Salidas de ejemplo

En [`ejemplo_salidas/`](ejemplo_salidas/) se incluyen los tres artefactos
generados a partir de `examples/ejemplo_acuifero.json`:

- `ejemplo_tce.html` — informe interactivo (ábrelo en el navegador)
- `ejemplo_tce.pdf` — informe técnico
- `ejemplo_tce.json` — datos de resultados

## Estructura del módulo

```
hidrogeologia/
├── core.py           # modelo, capas y ecuaciones de flujo/transporte
├── referencias.py    # bibliografía + capítulo hidrogeológico
├── html_report.py    # informe HTML interactivo (SVG/Canvas + JS)
├── pdf_report.py     # informe PDF (matplotlib)
├── cli.py            # interfaz de línea de comandos
├── examples/ejemplo_acuifero.json
├── ejemplo_salidas/  # artefactos de ejemplo
├── tests/test_core.py
└── requirements.txt
```

## Pruebas

```bash
python hidrogeologia/tests/test_core.py     # o:  python -m pytest hidrogeologia -q
```
