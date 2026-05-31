"""Hidrogeología — Análisis y visualización de tránsito de contaminantes.

Paquete para modelar un sistema acuífero multicapa, calcular el transporte
advectivo-dispersivo de contaminantes y, opcionalmente, el desplazamiento
lateral inducido por un gradiente hidráulico. Genera informe interactivo
(HTML), informe técnico (PDF) y exportación de resultados (JSON, artefacto).

Base científica: Darcy (1856), Ogata & Banks (1961), Freeze & Cherry (1979),
Domenico (1987), Bear (1972, 1979), Fetter (2001), Domenico & Schwartz (1998).
"""

from .core import Capa, ModeloHidrogeologico, ResultadosModelo

__all__ = ["Capa", "ModeloHidrogeologico", "ResultadosModelo"]
__version__ = "1.0.0"
