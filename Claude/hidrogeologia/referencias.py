"""Bibliografía científica y capítulo hidrogeológico final.

Reúne las referencias en las que se fundamentan las ecuaciones del modelo y
el texto del capítulo hidrogeológico que se incorpora a las salidas.
"""

REFERENCIAS = [
    {
        "clave": "Darcy1856",
        "cita": "Darcy, H. (1856). Les fontaines publiques de la ville de Dijon. "
                "Victor Dalmont, Paris.",
        "aporta": "Ley de Darcy: q = -K·i. Base del flujo en medios porosos.",
    },
    {
        "clave": "OgataBanks1961",
        "cita": "Ogata, A. & Banks, R.B. (1961). A solution of the differential "
                "equation of longitudinal dispersion in porous media. "
                "U.S. Geological Survey Professional Paper 411-A.",
        "aporta": "Solución analítica de la ADE para fuente continua usada en "
                  "los perfiles y curvas de llegada.",
    },
    {
        "clave": "Bear1972",
        "cita": "Bear, J. (1972). Dynamics of Fluids in Porous Media. "
                "American Elsevier, New York.",
        "aporta": "Teoría de la dispersión hidrodinámica y la velocidad real.",
    },
    {
        "clave": "Bear1979",
        "cita": "Bear, J. (1979). Hydraulics of Groundwater. McGraw-Hill, New York.",
        "aporta": "Formulación del transporte y de los parámetros hidráulicos.",
    },
    {
        "clave": "FreezeCherry1979",
        "cita": "Freeze, R.A. & Cherry, J.A. (1979). Groundwater. "
                "Prentice-Hall, Englewood Cliffs, 604 pp.",
        "aporta": "Conductividades típicas (Tabla 2.2), K equivalente "
                  "horizontal/vertical en sistemas estratificados, anisotropía.",
    },
    {
        "clave": "DomenicoRobbins1985",
        "cita": "Domenico, P.A. & Robbins, G.A. (1985). A new method of "
                "contaminant plume analysis. Ground Water, 23(4), 476-485.",
        "aporta": "Modelo analítico del penacho con dispersión transversal.",
    },
    {
        "clave": "Domenico1987",
        "cita": "Domenico, P.A. (1987). An analytical model for multidimensional "
                "transport of a decaying contaminant species. "
                "Journal of Hydrology, 91(1-2), 49-58.",
        "aporta": "Solución 2D/3D usada para la representación del penacho en "
                  "planta.",
    },
    {
        "clave": "GelharEtAl1992",
        "cita": "Gelhar, L.W., Welty, C. & Rehfeldt, K.R. (1992). A critical "
                "review of data on field-scale dispersion in aquifers. "
                "Water Resources Research, 28(7), 1955-1974.",
        "aporta": "Dependencia de la dispersividad con la escala de medida.",
    },
    {
        "clave": "XuEckstein1995",
        "cita": "Xu, M. & Eckstein, Y. (1995). Use of weighted least-squares "
                "method in evaluation of the relationship between dispersivity "
                "and field scale. Ground Water, 33(6), 905-908.",
        "aporta": "Relación empírica dispersividad-escala para estimar α_L.",
    },
    {
        "clave": "DomenicoSchwartz1998",
        "cita": "Domenico, P.A. & Schwartz, F.W. (1998). Physical and Chemical "
                "Hydrogeology, 2nd ed. John Wiley & Sons, New York.",
        "aporta": "Marco general de hidrogeología física y química.",
    },
    {
        "clave": "Fetter2001",
        "cita": "Fetter, C.W. (2001). Applied Hydrogeology, 4th ed. "
                "Prentice-Hall, Upper Saddle River.",
        "aporta": "Transmisividad y factor de retardo R = 1 + ρ_b·K_d/n_e.",
    },
    {
        "clave": "FetterContaminant2008",
        "cita": "Fetter, C.W. (2008). Contaminant Hydrogeology, 2nd ed. "
                "Waveland Press, Long Grove.",
        "aporta": "Procesos de sorción, retardo y transporte de solutos.",
    },
    {
        "clave": "Zheng2002",
        "cita": "Zheng, C. & Bennett, G.D. (2002). Applied Contaminant "
                "Transport Modeling, 2nd ed. Wiley-Interscience, New York.",
        "aporta": "Modelización numérica del transporte (contexto MT3D).",
    },
    {
        "clave": "USEPA1989",
        "cita": "U.S. EPA (1989). Risk Assessment Guidance for Superfund "
                "(RAGS), Vol. I. EPA/540/1-89/002, Washington D.C.",
        "aporta": "Marco de evaluación de riesgos por contaminación de aguas "
                  "subterráneas.",
    },
]


CAPITULO_HIDROGEOLOGICO = {
    "titulo": "Capítulo hidrogeológico: interpretación del modelo de tránsito de contaminantes",
    "secciones": [
        {
            "titulo": "1. Marco conceptual del flujo subterráneo",
            "parrafos": [
                "El movimiento del agua subterránea a través de un medio poroso "
                "saturado se describe mediante la ley de Darcy (1856), que "
                "establece que el flujo específico (descarga de Darcy) es "
                "proporcional al gradiente hidráulico: q = -K·i, donde K es la "
                "conductividad hidráulica del material. La conductividad "
                "hidráulica integra las propiedades del medio (permeabilidad "
                "intrínseca k) y del fluido (densidad y viscosidad), de modo "
                "que k = K·μ/(ρ·g).",
                "La velocidad real o lineal media del agua en los poros, "
                "responsable del transporte advectivo del contaminante, se "
                "obtiene dividiendo el flujo de Darcy entre la porosidad eficaz: "
                "v = q/n_e = K·i/n_e. Esta velocidad es siempre mayor que la "
                "de Darcy porque el agua circula únicamente por la fracción "
                "interconectada de poros.",
            ],
        },
        {
            "titulo": "2. Sistema acuífero multicapa y propiedades equivalentes",
            "parrafos": [
                "En un sistema estratificado, el comportamiento hidráulico "
                "depende de la dirección del flujo respecto a la estratificación. "
                "Para flujo paralelo a las capas, la conductividad equivalente es "
                "la media aritmética ponderada por el espesor (dominada por las "
                "capas más permeables): K_h = Σ(K_i·b_i)/Σ(b_i). Para flujo "
                "perpendicular, es la media armónica ponderada (dominada por las "
                "capas menos permeables): K_v = Σ(b_i)/Σ(b_i/K_i).",
                "La diferencia entre ambas define la anisotropía del sistema "
                "(K_h/K_v ≥ 1), un parámetro determinante en la geometría del "
                "penacho: cuanto mayor es la anisotropía, más se favorece el "
                "transporte horizontal frente al vertical (Freeze & Cherry, "
                "1979). La transmisividad total T = Σ(K_i·b_i) cuantifica la "
                "capacidad global del acuífero para transmitir agua.",
            ],
        },
        {
            "titulo": "3. Transporte de contaminantes: advección y dispersión",
            "parrafos": [
                "El transporte de solutos en el acuífero se rige por la ecuación "
                "de advección-dispersión (ADE). La advección desplaza el "
                "contaminante a la velocidad del agua, mientras que la dispersión "
                "hidrodinámica (mezcla mecánica más difusión molecular) lo "
                "ensancha. La dispersión longitudinal se cuantifica con la "
                "dispersividad α_L, que crece con la escala del problema "
                "(Gelhar et al., 1992; Xu & Eckstein, 1995).",
                "Para una fuente continua en un medio semi-infinito, Ogata & "
                "Banks (1961) proporcionaron la solución analítica empleada en "
                "los perfiles de concentración C(x) y en las curvas de llegada "
                "C(t). El frente del 50 % de la concentración (C/C0 = 0,5) avanza "
                "aproximadamente a la velocidad del contaminante.",
                "La extensión lateral (transversal) del penacho se modela con la "
                "dispersividad transversal α_T (típicamente α_L/10 a α_L/100) "
                "siguiendo el modelo de Domenico (1987), que permite representar "
                "el penacho en planta.",
            ],
        },
        {
            "titulo": "4. Retardo por sorción",
            "parrafos": [
                "Los contaminantes reactivos interaccionan con la matriz sólida "
                "(sorción). Bajo la hipótesis de sorción lineal en equilibrio, "
                "el factor de retardo R = 1 + ρ_b·K_d/n_e (Fetter, 2001) reduce "
                "la velocidad efectiva del contaminante a v_c = v/R. Un valor "
                "R = 1 corresponde a un trazador conservativo (no reactivo); "
                "valores elevados implican una migración mucho más lenta que la "
                "del agua.",
            ],
        },
        {
            "titulo": "5. Desplazamiento lateral inducido por el gradiente hidráulico",
            "parrafos": [
                "Cuando se conoce el gradiente hidráulico, el desplazamiento "
                "lateral (avance horizontal) del contaminante por advección se "
                "estima como L(t) = v_c·t = (K·i/n_e)·t/R. Este desplazamiento "
                "es el principal indicador de la distancia recorrida por el "
                "núcleo del penacho y resulta crítico para evaluar el tiempo de "
                "llegada a un punto de interés (pozo de abastecimiento, masa de "
                "agua superficial, límite del emplazamiento).",
                "Dado que cada capa puede tener distinta K y porosidad, el "
                "desplazamiento se calcula por capa: las capas más transmisivas "
                "actúan como vías preferentes de migración, donde el contaminante "
                "avanza más rápido.",
            ],
        },
        {
            "titulo": "6. Limitaciones e implicaciones para la gestión",
            "parrafos": [
                "El modelo es analítico y asume condiciones idealizadas: medio "
                "homogéneo por capa, flujo permanente y uniforme, fuente "
                "constante y propiedades invariables en el tiempo. No sustituye a "
                "una modelización numérica (p. ej. MODFLOW/MT3D; Zheng & "
                "Bennett, 2002) ni a la caracterización de campo, pero ofrece una "
                "estimación de primer orden útil para el cribado, el diseño de "
                "redes de control y la evaluación preliminar de riesgos "
                "(US EPA, 1989).",
                "Los resultados deben interpretarse junto con datos "
                "piezométricos, ensayos de bombeo y análisis químicos reales. "
                "La incertidumbre en la dispersividad y en K_d puede modificar "
                "sustancialmente las predicciones de llegada.",
            ],
        },
    ],
}
