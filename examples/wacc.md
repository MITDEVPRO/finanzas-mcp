# WACC — ¿a qué tasa descuento esta empresa?

**El caso.** Distribuidora chilena mediana: patrimonio a mercado de $3.200 MM, deuda financiera de $1.800 MM. El costo del equity (vía CAPM, ver tool `capm_costo_equity`) dio 14,5%; los bancos le prestan al 7,8% anual antes de impuesto. Impuesto de primera categoría: 27%.

**La pregunta al cliente MCP:**

> Calcula el WACC: equity 3200, deuda 1800, Ke 14,5%, Kd 7,8%, impuesto 27%.

**Llamada:**

```json
wacc(valor_equity=3200, valor_deuda=1800, costo_equity=0.145, costo_deuda=0.078, tasa_impuesto=0.27)
```

**Salida real:**

```json
{
  "wacc_pct": 11.33,
  "peso_equity_pct": 64.0,
  "peso_deuda_pct": 36.0,
  "kd_despues_impuesto_pct": 5.69,
  "formula": "WACC = E/(D+E)×Ke + D/(D+E)×Kd×(1-t)"
}
```

**Cómo leerlo.** Cada peso invertido en esta empresa tiene que rendir al menos **11,33% anual** para crear valor. Nota el efecto del escudo fiscal: la deuda cuesta 7,8% nominal pero solo 5,69% después de impuesto — por eso endeudarse "barato" baja el WACC… hasta que el riesgo financiero empieza a subir el Ke.

Siguiente paso natural: usar este 11,33% (redondeado a 11,8% si quieres castigo por tamaño) como tasa de descuento del [DCF](dcf.md).
