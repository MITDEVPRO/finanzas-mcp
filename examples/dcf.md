# DCF — ¿cuánto vale el negocio?

**El caso.** La misma distribuidora del [ejemplo WACC](wacc.md). Flujos de caja libre proyectados a 5 años: $420 → $590 MM (crecimiento moderado). Tasa de descuento 11,8% (el WACC más un castigo por tamaño), crecimiento a perpetuidad 3%, deuda neta $900 MM.

**La pregunta al cliente MCP:**

> Valoriza por DCF con FCF [420, 460, 505, 550, 590], WACC 11,8%, g 3% y deuda neta 900. Incluye sensibilidad.

**Llamada:**

```json
dcf(flujos_caja_libre=[420, 460, 505, 550, 590], tasa_descuento=0.118, crecimiento_perpetuo=0.03, deuda_neta=900, sensibilidad=true)
```

**Salida real:**

```json
{
  "enterprise_value": 5748.55,
  "valor_equity": 4848.55,
  "vp_periodo_explicito": 1794.9,
  "vp_valor_terminal": 3953.64,
  "peso_valor_terminal_pct": 68.78,
  "supuestos": {
    "wacc_pct": 11.8,
    "g_pct": 3.0,
    "anios_explicitos": 5
  },
  "sensibilidad_valor_equity": {
    "wacc=10.8%": { "g=2.0%": 5038.4, "g=3.0%": 5608.72, "g=4.0%": 6346.78 },
    "wacc=11.8%": { "g=2.0%": 4410.65, "g=3.0%": 4848.55, "g=4.0%": 5398.73 },
    "wacc=12.8%": { "g=2.0%": 3899.81, "g=3.0%": 4244.13, "g=4.0%": 4666.71 }
  }
}
```

**Cómo leerlo.** El equity vale ~$4.850 MM… bajo ESOS supuestos. Los dos números que debieran incomodarte:

- **68,78% del valor está en el valor terminal** — más de dos tercios de la valoración depende de lo que pase después del año 5. Típico, pero hay que decirlo en el comité.
- La sensibilidad muestra el rango honesto: mover WACC y g apenas ±1 punto lleva el equity de **$3.900 a $6.350 MM**. Quien te entregue un DCF con un solo número te está vendiendo precisión que no existe.
