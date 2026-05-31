"""Núcleo científico del análisis de tránsito de contaminantes.

Implementa el modelo conceptual de un acuífero multicapa y las ecuaciones
de flujo y transporte usadas habitualmente en hidrogeología de contaminantes.

Referencias clave (ver ``referencias.py`` para la lista completa):
  * Darcy, H. (1856) — Ley de Darcy.
  * Ogata, A. & Banks, R.B. (1961) — Solución analítica de la ecuación de
    advección-dispersión (ADE) para fuente continua en medio semi-infinito.
  * Freeze, R.A. & Cherry, J.A. (1979) — *Groundwater*.
  * Domenico, P.A. (1987) — Solución analítica para penacho 2D/3D.
  * Bear, J. (1972, 1979) — Hidráulica de medios porosos / dispersión.
  * Fetter, C.W. (2001) — *Applied Hydrogeology* / *Contaminant Hydrogeology*.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any

import numpy as np
from scipy.special import erfc

# ---------------------------------------------------------------------------
# Constantes físicas (agua a 20 °C)
# ---------------------------------------------------------------------------
G_GRAVEDAD = 9.81            # aceleración de la gravedad [m/s²]
RHO_AGUA = 998.2             # densidad del agua a 20 °C [kg/m³]
MU_AGUA = 1.002e-3           # viscosidad dinámica del agua a 20 °C [Pa·s]
DARCY_A_M2 = 9.869233e-13    # 1 darcy en m²
SEG_POR_ANIO = 365.25 * 24 * 3600.0


# ---------------------------------------------------------------------------
# Capa hidrogeológica
# ---------------------------------------------------------------------------
@dataclass
class Capa:
    """Una capa (estrato) del modelo hidrogeológico.

    Parámetros
    ----------
    nombre : str
        Nombre identificativo de la capa.
    espesor_m : float
        Espesor (potencia) de la capa [m].
    K_m_s : float
        Conductividad hidráulica (permeabilidad) [m/s].
    porosidad_eficaz : float
        Porosidad eficaz / efectiva n_e [-] (fracción, 0-1).
    densidad_seca_kg_m3 : float, opcional
        Densidad aparente seca ρ_b del sólido [kg/m³]. Para el factor de retardo.
    kd_m3_kg : float, opcional
        Coeficiente de distribución (sorción lineal) K_d [m³/kg].
    dispersividad_long_m : float, opcional
        Dispersividad longitudinal α_L [m]. Por defecto 1.0 m.
    dispersividad_trans_m : float, opcional
        Dispersividad transversal α_T [m]. Por defecto α_L/10.
    color : str, opcional
        Color HEX para la representación gráfica.
    """

    nombre: str
    espesor_m: float
    K_m_s: float
    porosidad_eficaz: float = 0.25
    densidad_seca_kg_m3: Optional[float] = None
    kd_m3_kg: Optional[float] = None
    dispersividad_long_m: Optional[float] = None
    dispersividad_trans_m: Optional[float] = None
    dispersividad_vert_m: Optional[float] = None
    color: Optional[str] = None

    # -- Propiedades derivadas --------------------------------------------
    @property
    def permeabilidad_intrinseca_m2(self) -> float:
        """Permeabilidad intrínseca k = K·μ/(ρ·g) [m²]."""
        return self.K_m_s * MU_AGUA / (RHO_AGUA * G_GRAVEDAD)

    @property
    def permeabilidad_darcy(self) -> float:
        """Permeabilidad intrínseca expresada en darcy."""
        return self.permeabilidad_intrinseca_m2 / DARCY_A_M2

    @property
    def transmisividad_m2_s(self) -> float:
        """Transmisividad de la capa T = K·b [m²/s]."""
        return self.K_m_s * self.espesor_m

    @property
    def factor_retardo(self) -> float:
        """Factor de retardo R = 1 + ρ_b·K_d/n_e [-].

        Si no se aportan ρ_b y K_d, R = 1 (transporte conservativo).
        """
        if self.densidad_seca_kg_m3 and self.kd_m3_kg:
            return 1.0 + (self.densidad_seca_kg_m3 * self.kd_m3_kg) / self.porosidad_eficaz
        return 1.0

    def alfa_L(self) -> float:
        """Dispersividad longitudinal efectiva [m]."""
        if self.dispersividad_long_m is not None:
            return self.dispersividad_long_m
        return 1.0

    def alfa_T(self) -> float:
        """Dispersividad transversal (horizontal) efectiva [m]."""
        if self.dispersividad_trans_m is not None:
            return self.dispersividad_trans_m
        return self.alfa_L() / 10.0

    def alfa_V(self) -> float:
        """Dispersividad vertical efectiva [m].

        Por defecto α_V ≈ α_L/100 (Gelhar et al., 1992): la dispersión
        vertical es típicamente uno o dos órdenes menor que la longitudinal.
        """
        if self.dispersividad_vert_m is not None:
            return self.dispersividad_vert_m
        return self.alfa_L() / 100.0

    def clasificacion(self) -> str:
        """Clasifica el material por su conductividad hidráulica.

        Rangos según Freeze & Cherry (1979), Tabla 2.2.
        """
        k = self.K_m_s
        if k >= 1e-2:
            return "Muy permeable (grava limpia)"
        if k >= 1e-3:
            return "Permeable (arena gruesa)"
        if k >= 1e-5:
            return "Permeable (arena fina / arena limosa)"
        if k >= 1e-7:
            return "Poco permeable (limo, loess)"
        if k >= 1e-9:
            return "Muy poco permeable (arcilla limosa)"
        return "Impermeable / acuicludo (arcilla)"

    def a_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d.update(
            permeabilidad_intrinseca_m2=self.permeabilidad_intrinseca_m2,
            permeabilidad_darcy=self.permeabilidad_darcy,
            transmisividad_m2_s=self.transmisividad_m2_s,
            factor_retardo=self.factor_retardo,
            alfa_L=self.alfa_L(),
            alfa_T=self.alfa_T(),
            alfa_V=self.alfa_V(),
            clasificacion=self.clasificacion(),
        )
        return d


# ---------------------------------------------------------------------------
# Resultados
# ---------------------------------------------------------------------------
@dataclass
class ResultadosModelo:
    """Contenedor de los resultados calculados del modelo."""

    sistema: Dict[str, Any]
    capas: List[Dict[str, Any]]
    transporte: Dict[str, Any]
    desplazamiento_lateral: Optional[Dict[str, Any]]
    metadatos: Dict[str, Any]
    geo: Optional[Dict[str, Any]] = None

    def a_dict(self) -> Dict[str, Any]:
        return {
            "metadatos": self.metadatos,
            "sistema": self.sistema,
            "capas": self.capas,
            "transporte": self.transporte,
            "desplazamiento_lateral": self.desplazamiento_lateral,
            "geo": self.geo,
        }


# ---------------------------------------------------------------------------
# Modelo hidrogeológico
# ---------------------------------------------------------------------------
class ModeloHidrogeologico:
    """Modelo de un sistema acuífero multicapa con transporte de contaminante.

    Parámetros
    ----------
    nombre : str
        Nombre del caso / emplazamiento.
    capas : list[Capa]
        Lista ordenada de capas, de techo (somera) a muro (profunda).
    gradiente_hidraulico : float, opcional
        Gradiente hidráulico i [-]. Si se aporta, se calcula el flujo de
        Darcy, la velocidad real y el desplazamiento lateral del contaminante.
    concentracion_fuente : float
        Concentración de la fuente C0 [mg/L].
    capa_transporte_idx : int, opcional
        Índice (0-based) de la capa donde se simula el transporte. Si es None,
        se usa la capa más transmisiva.
    tiempo_max_anios : float
        Horizonte temporal de la simulación [años].
    distancia_max_m : float, opcional
        Distancia máxima considerada para los perfiles [m].
    descripcion : str
        Texto descriptivo del emplazamiento/caso.
    """

    def __init__(
        self,
        nombre: str,
        capas: List[Capa],
        gradiente_hidraulico: Optional[float] = None,
        concentracion_fuente: float = 100.0,
        capa_transporte_idx: Optional[int] = None,
        tiempo_max_anios: float = 10.0,
        distancia_max_m: Optional[float] = None,
        descripcion: str = "",
        origen: Optional[Dict[str, Any]] = None,
        azimut_flujo_grados: float = 90.0,
        basemap: str = "topografia",
    ):
        if not capas:
            raise ValueError("El modelo debe tener al menos una capa.")
        self.nombre = nombre
        self.capas = capas
        self.gradiente_hidraulico = gradiente_hidraulico
        self.concentracion_fuente = concentracion_fuente
        self.tiempo_max_anios = tiempo_max_anios
        self.descripcion = descripcion
        # Georreferenciación: punto de origen {x, y, wkid}, rumbo del flujo y
        # mapa base por defecto del visor.
        self.origen = origen
        self.azimut_flujo_grados = azimut_flujo_grados
        self.basemap = basemap

        # Capa de transporte: por defecto la más transmisiva (la más rápida).
        if capa_transporte_idx is None:
            capa_transporte_idx = int(
                np.argmax([c.transmisividad_m2_s for c in capas])
            )
        self.capa_transporte_idx = capa_transporte_idx
        self.distancia_max_m = distancia_max_m

    # -- Propiedades del sistema multicapa --------------------------------
    @property
    def espesor_total_m(self) -> float:
        return sum(c.espesor_m for c in self.capas)

    @property
    def transmisividad_total_m2_s(self) -> float:
        """Transmisividad total del sistema T = Σ K_i·b_i."""
        return sum(c.transmisividad_m2_s for c in self.capas)

    @property
    def K_horizontal_equivalente(self) -> float:
        """K equivalente para flujo paralelo a la estratificación (media
        aritmética ponderada por espesor). Freeze & Cherry (1979)."""
        return self.transmisividad_total_m2_s / self.espesor_total_m

    @property
    def K_vertical_equivalente(self) -> float:
        """K equivalente para flujo perpendicular a la estratificación
        (media armónica ponderada). Freeze & Cherry (1979)."""
        suma = sum(c.espesor_m / c.K_m_s for c in self.capas)
        return self.espesor_total_m / suma

    @property
    def relacion_anisotropia(self) -> float:
        """Relación de anisotropía Kh/Kv del sistema multicapa."""
        return self.K_horizontal_equivalente / self.K_vertical_equivalente

    @property
    def porosidad_media(self) -> float:
        """Porosidad eficaz media ponderada por espesor."""
        return sum(c.porosidad_eficaz * c.espesor_m for c in self.capas) / self.espesor_total_m

    # -- Flujo (Darcy) ----------------------------------------------------
    def velocidad_darcy(self, capa: Capa) -> Optional[float]:
        """Flujo de Darcy q = K·i [m/s]. Requiere gradiente."""
        if self.gradiente_hidraulico is None:
            return None
        return capa.K_m_s * self.gradiente_hidraulico

    def velocidad_real(self, capa: Capa) -> Optional[float]:
        """Velocidad real / lineal media v = K·i/n_e [m/s]."""
        q = self.velocidad_darcy(capa)
        if q is None:
            return None
        return q / capa.porosidad_eficaz

    def velocidad_contaminante(self, capa: Capa) -> Optional[float]:
        """Velocidad del contaminante v_c = v/R (con retardo) [m/s]."""
        v = self.velocidad_real(capa)
        if v is None:
            return None
        return v / capa.factor_retardo

    # -- Transporte: ecuación de advección-dispersión ---------------------
    @staticmethod
    def ogata_banks(x, t, v, D_L, R=1.0):
        """Solución de Ogata & Banks (1961) para fuente continua.

        C/C0 = 0.5·[ erfc((x - v·t/R)/(2·√(D_L·t/R)))
                     + exp(v·x/D_L)·erfc((x + v·t/R)/(2·√(D_L·t/R))) ]

        Parámetros en unidades coherentes (m, s). Devuelve C/C0 [-].
        """
        x = np.asarray(x, dtype=float)
        if t <= 0:
            return np.zeros_like(x)
        vt = v * t / R
        denom = 2.0 * np.sqrt(D_L * t / R)
        term1 = erfc((x - vt) / denom)
        # El segundo término puede desbordar; se controla el exponente.
        arg_exp = np.clip(v * x / D_L, -700, 700)
        term2 = np.exp(arg_exp) * erfc((x + vt) / denom)
        term2 = np.where(np.isfinite(term2), term2, 0.0)
        c = 0.5 * (term1 + term2)
        return np.clip(c, 0.0, 1.0)

    @staticmethod
    def domenico_2d(x, y, t, v, alpha_L, alpha_T, ancho_fuente, R=1.0):
        """Penacho 2D en planta (Domenico, 1987; Domenico & Robbins, 1985).

        Fuente vertical de ancho Y a lo largo del eje y. Devuelve C/C0.
        """
        x = np.asarray(x, dtype=float)
        y = np.asarray(y, dtype=float)
        if t <= 0:
            return np.zeros_like(x)
        vt = v * t / R
        # Término longitudinal (frente de avance) — forma estable habitual.
        long_term = 0.5 * erfc((x - vt) / (2.0 * np.sqrt(alpha_L * np.maximum(x, 1e-9))))
        # Término transversal (ensanchamiento lateral del penacho).
        sigma = np.sqrt(np.maximum(alpha_T * x, 1e-12))
        trans_term = 0.5 * (
            erfc((y - ancho_fuente / 2.0) / (2.0 * sigma))
            - erfc((y + ancho_fuente / 2.0) / (2.0 * sigma))
        )
        return np.clip(long_term * trans_term, 0.0, 1.0)

    @staticmethod
    def domenico_perfil(x, z, t, v, alpha_L, alpha_V, alto_fuente, z_fuente, R=1.0):
        """Penacho en perfil — corte vertical x–z (Domenico, 1987).

        Análoga a ``domenico_2d`` pero en el plano vertical: el penacho avanza
        por advección a lo largo de x y se dispersa verticalmente según α_V.
        La fuente tiene una altura ``alto_fuente`` centrada en ``z_fuente`` (la
        profundidad del centro de la fuente, positiva hacia abajo).

        Devuelve C/C0 [-].
        """
        x = np.asarray(x, dtype=float)
        z = np.asarray(z, dtype=float)
        if t <= 0:
            return np.zeros_like(x)
        vt = v * t / R
        long_term = 0.5 * erfc((x - vt) / (2.0 * np.sqrt(alpha_L * np.maximum(x, 1e-9))))
        sigma = np.sqrt(np.maximum(alpha_V * x, 1e-12))
        vert_term = 0.5 * (
            erfc((z - (z_fuente + alto_fuente / 2.0)) / (2.0 * sigma))
            - erfc((z - (z_fuente - alto_fuente / 2.0)) / (2.0 * sigma))
        )
        return np.clip(long_term * vert_term, 0.0, 1.0)

    @staticmethod
    def extension_longitudinal(v, D_L, t, R, umbral=0.01, dist_tope=None):
        """Distancia a la que el frente del penacho cae por debajo de ``umbral``
        (C/C0) al tiempo ``t``. Sirve para **autoajustar** la longitud de los
        gráficos del penacho a la prolongación real del resultado.

        Se busca el x donde la solución de Ogata-Banks en el eje = umbral,
        partiendo del avance advectivo y añadiendo la cola dispersiva.
        """
        if v <= 0 or t <= 0:
            return 50.0
        vt = v * t / R
        # Punto de partida: avance advectivo. La cola dispersiva añade ~ varias
        # veces sqrt(D_L*t/R). Se busca con bisección sobre el eje longitudinal.
        sigma = math.sqrt(max(D_L * t / R, 1e-12))
        x_hi = vt + 6.0 * sigma + 10.0
        if dist_tope:
            x_hi = min(x_hi, dist_tope)
        # Si en x_hi aún hay concentración por encima del umbral, devuélvelo.
        f = lambda xx: float(ModeloHidrogeologico.ogata_banks(
            np.array([xx]), t, v, D_L, R)[0]) - umbral
        lo, hi = 0.0, x_hi
        if f(hi) > 0:
            return hi * 1.05
        for _ in range(40):
            mid = 0.5 * (lo + hi)
            if f(mid) > 0:
                lo = mid
            else:
                hi = mid
        return max(50.0, hi * 1.08)  # pequeño margen visual

    # -- Desplazamiento lateral -------------------------------------------
    def desplazamiento_lateral_capa(self, capa: Capa, tiempos_s):
        """Desplazamiento (avance) del contaminante por advección [m].

        El avance horizontal del centro de masa del penacho impulsado por el
        gradiente hidráulico:  L(t) = v_c · t = (K·i/n_e)·t / R
        """
        vc = self.velocidad_contaminante(capa)
        if vc is None:
            return None
        return vc * np.asarray(tiempos_s, dtype=float)

    # -- Cálculo integral -------------------------------------------------
    def calcular(self) -> ResultadosModelo:
        capa_t = self.capas[self.capa_transporte_idx]

        tmax_s = self.tiempo_max_anios * SEG_POR_ANIO
        vc = self.velocidad_contaminante(capa_t)
        if self.distancia_max_m is None:
            if vc is not None and vc > 0:
                self.distancia_max_m = max(50.0, vc * tmax_s * 1.3)
            else:
                self.distancia_max_m = 500.0

        n_x = 240
        x = np.linspace(0.0, self.distancia_max_m, n_x)
        n_t = 60
        tiempos_anios = np.linspace(0.0, self.tiempo_max_anios, n_t + 1)[1:]
        tiempos_s = tiempos_anios * SEG_POR_ANIO

        alpha_L = capa_t.alfa_L()
        R = capa_t.factor_retardo

        transporte: Dict[str, Any] = {
            "capa": capa_t.nombre,
            "capa_idx": self.capa_transporte_idx,
            "concentracion_fuente_mg_l": self.concentracion_fuente,
            "x_m": x.tolist(),
            "tiempos_anios": tiempos_anios.tolist(),
            "dispersividad_long_m": alpha_L,
            "factor_retardo": R,
            "perfiles": None,
            "curva_llegada": None,
            "penacho_2d": None,
            "penacho_perfil": None,
        }

        if vc is not None and vc > 0:
            v = self.velocidad_real(capa_t)
            D_L = alpha_L * v  # dispersión longitudinal (dominada por advección)
            transporte["velocidad_real_m_s"] = v
            transporte["velocidad_contaminante_m_s"] = vc
            transporte["dispersion_long_m2_s"] = D_L

            idxs = np.linspace(0, len(tiempos_s) - 1, 6).astype(int)
            perfiles = []
            for i in idxs:
                c = self.ogata_banks(x, tiempos_s[i], v, D_L, R)
                perfiles.append({
                    "t_anios": float(tiempos_anios[i]),
                    "C_rel": c.tolist(),
                    "C_mg_l": (c * self.concentracion_fuente).tolist(),
                })
            transporte["perfiles"] = perfiles

            x_obs = min(self.distancia_max_m * 0.5, 100.0)
            t_fino_anios = np.linspace(0.01, self.tiempo_max_anios, 120)
            t_fino_s = t_fino_anios * SEG_POR_ANIO
            c_obs = np.array([
                float(self.ogata_banks(np.array([x_obs]), ts, v, D_L, R)[0])
                for ts in t_fino_s
            ])
            transporte["curva_llegada"] = {
                "x_obs_m": float(x_obs),
                "t_anios": t_fino_anios.tolist(),
                "C_rel": c_obs.tolist(),
                "C_mg_l": (c_obs * self.concentracion_fuente).tolist(),
            }

            # Autoajuste de la longitud del penacho a la prolongación real del
            # resultado (hasta donde C/C0 cae por debajo del 1 %), en lugar de
            # usar siempre la distancia máxima de los perfiles.
            ext_pen = self.extension_longitudinal(
                v, D_L, tmax_s, R, umbral=0.01, dist_tope=self.distancia_max_m * 3.0)
            transporte["extension_penacho_m"] = ext_pen
            ancho_fuente = max(ext_pen * 0.04, 2.0)
            ny = 80
            y_ext = max(ext_pen * 0.18, 10.0)
            xg = np.linspace(0.1, ext_pen, 120)
            yg = np.linspace(-y_ext, y_ext, ny)
            XX, YY = np.meshgrid(xg, yg)
            CC = self.domenico_2d(
                XX, YY, tmax_s, v, alpha_L, capa_t.alfa_T(), ancho_fuente, R
            )
            transporte["penacho_2d"] = {
                "t_anios": self.tiempo_max_anios,
                "x_m": xg.tolist(),
                "y_m": yg.tolist(),
                "C_rel": CC.tolist(),
                "ancho_fuente_m": ancho_fuente,
            }

            # Penacho en perfil (corte vertical x–z). La fuente se sitúa en la
            # capa de transporte; z se mide en profundidad (positiva hacia abajo).
            z_techo = sum(self.capas[i].espesor_m for i in range(self.capa_transporte_idx))
            z_centro = z_techo + capa_t.espesor_m / 2.0
            alto_fuente = capa_t.espesor_m
            nz = 80
            zg = np.linspace(0.0, self.espesor_total_m, nz)
            XXp, ZZp = np.meshgrid(xg, zg)
            CCp = self.domenico_perfil(
                XXp, ZZp, tmax_s, v, alpha_L, capa_t.alfa_V(),
                alto_fuente, z_centro, R
            )
            # Límites de cada capa para dibujar la estratigrafía en el perfil.
            limites = []
            prof = 0.0
            for c in self.capas:
                limites.append({"nombre": c.nombre, "techo_m": prof,
                                "muro_m": prof + c.espesor_m})
                prof += c.espesor_m
            transporte["penacho_perfil"] = {
                "t_anios": self.tiempo_max_anios,
                "x_m": xg.tolist(),
                "z_m": zg.tolist(),
                "C_rel": CCp.tolist(),
                "z_centro_fuente_m": z_centro,
                "alto_fuente_m": alto_fuente,
                "alfa_V_m": capa_t.alfa_V(),
                "capas": limites,
            }

        desplazamiento = None
        if self.gradiente_hidraulico is not None:
            por_capa = []
            for c in self.capas:
                q = self.velocidad_darcy(c)
                v = self.velocidad_real(c)
                vc_c = self.velocidad_contaminante(c)
                L = vc_c * tmax_s
                por_capa.append({
                    "nombre": c.nombre,
                    "q_darcy_m_s": q,
                    "q_darcy_m_anio": q * SEG_POR_ANIO,
                    "v_real_m_s": v,
                    "v_real_m_anio": v * SEG_POR_ANIO,
                    "v_contaminante_m_anio": vc_c * SEG_POR_ANIO,
                    "factor_retardo": c.factor_retardo,
                    "desplazamiento_tmax_m": L,
                    "curva": {
                        "t_anios": tiempos_anios.tolist(),
                        "L_m": (vc_c * tiempos_s).tolist(),
                    },
                })
            desplazamiento = {
                "gradiente_hidraulico": self.gradiente_hidraulico,
                "tiempo_max_anios": self.tiempo_max_anios,
                "por_capa": por_capa,
            }

        sistema = {
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "n_capas": len(self.capas),
            "espesor_total_m": self.espesor_total_m,
            "transmisividad_total_m2_s": self.transmisividad_total_m2_s,
            "transmisividad_total_m2_dia": self.transmisividad_total_m2_s * 86400.0,
            "K_horizontal_equivalente_m_s": self.K_horizontal_equivalente,
            "K_vertical_equivalente_m_s": self.K_vertical_equivalente,
            "relacion_anisotropia": self.relacion_anisotropia,
            "porosidad_media": self.porosidad_media,
            "gradiente_hidraulico": self.gradiente_hidraulico,
            "capa_transporte": capa_t.nombre,
            "distancia_max_m": self.distancia_max_m,
            "tiempo_max_anios": self.tiempo_max_anios,
        }

        capas_dict = []
        prof = 0.0
        for c in self.capas:
            d = c.a_dict()
            d["profundidad_techo_m"] = prof
            d["profundidad_muro_m"] = prof + c.espesor_m
            prof += c.espesor_m
            capas_dict.append(d)

        import datetime as _dt
        metadatos = {
            "generado": _dt.datetime.now().isoformat(timespec="seconds"),
            "version": "1.0.0",
            "modelo": "Acuífero multicapa · ADE (Ogata-Banks) · Domenico 2D",
        }

        # Bloque de georreferenciación (origen + huella del penacho en planta).
        geo = None
        if self.origen:
            from .geo import info_geo
            long_pen = transporte.get("extension_penacho_m")
            semi = None
            if transporte.get("penacho_2d"):
                semi = transporte["penacho_2d"]["y_m"][-1] * 0.6
            geo = info_geo(self.origen, self.azimut_flujo_grados,
                           long_pen, semi, self.basemap)

        return ResultadosModelo(
            sistema=sistema,
            capas=capas_dict,
            transporte=transporte,
            desplazamiento_lateral=desplazamiento,
            metadatos=metadatos,
            geo=geo,
        )

    # -- Construcción desde diccionario -----------------------------------
    @classmethod
    def desde_dict(cls, d: Dict[str, Any]) -> "ModeloHidrogeologico":
        capas = [Capa(**c) for c in d["capas"]]
        return cls(
            nombre=d.get("nombre", "Caso sin nombre"),
            capas=capas,
            gradiente_hidraulico=d.get("gradiente_hidraulico"),
            concentracion_fuente=d.get("concentracion_fuente", 100.0),
            capa_transporte_idx=d.get("capa_transporte_idx"),
            tiempo_max_anios=d.get("tiempo_max_anios", 10.0),
            distancia_max_m=d.get("distancia_max_m"),
            descripcion=d.get("descripcion", ""),
            origen=d.get("origen"),
            azimut_flujo_grados=d.get("azimut_flujo_grados", 90.0),
            basemap=d.get("basemap", "topografia"),
        )
