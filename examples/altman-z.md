# Altman Z-Score — ¿qué tan cerca está de la insolvencia?

**El caso.** La misma distribuidora: activos totales $5.600 MM, pasivos $3.300 MM, capital de trabajo $750 MM, utilidades retenidas $980 MM, EBIT $430 MM, patrimonio $2.300 MM, ventas $7.800 MM. Empresa privada no listada → modelo Z' (`privada`).

**La pregunta al cliente MCP:**

> Calcula el Z-Score modelo privada: activos 5600, pasivos 3300, capital de trabajo 750, utilidades retenidas 980, EBIT 430, patrimonio 2300, ventas 7800.

**Llamada:**

```json
altman_z_score(activos_totales=5600, pasivos_totales=3300, capital_trabajo=750, utilidades_retenidas=980, ebit=430, patrimonio=2300, ventas=7800, modelo="privada")
```

**Salida real:**

```json
{
  "z_score": 2.17,
  "modelo": "privada",
  "zona": "GRIS — monitorear liquidez y deuda",
  "umbrales": {
    "zona_segura_desde": 2.9,
    "zona_peligro_bajo": 1.23
  },
  "componentes": {
    "x1_wc_ta": 0.134,
    "x2_re_ta": 0.175,
    "x3_ebit_ta": 0.077,
    "x4_eq_pas": 0.697,
    "x5_ventas_ta": 1.393
  }
}
```

**Cómo leerlo.** Z' = 2,17: **zona gris**. No es alarma de quiebra (eso es bajo 1,23) pero tampoco zona segura (sobre 2,9). Los componentes dicen dónde apretar: la rotación de activos (x5 = 1,39) es sana para una distribuidora; lo flaco es la rentabilidad operacional sobre activos (x3 = 7,7%) y el colchón de utilidades retenidas (x2). Traducción: el problema no es vender, es **margen** — y eso conecta directo con el [punto de equilibrio](punto-equilibrio.md).

Un solo número no diagnostica una empresa; el Z-Score sirve como alarma temprana y para seguir la **tendencia** trimestre a trimestre.
