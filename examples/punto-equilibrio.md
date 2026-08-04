# Punto de equilibrio — ¿cuánto pueden caer las ventas antes de perder plata?

**El caso.** La distribuidora mueve ~16.500 cajas al mes. Precio promedio por caja $52.000 (0,052 MM), costo variable $37.000 (0,037 MM), costos fijos mensuales $180 MM (bodega, remuneraciones, flota).

**La pregunta al cliente MCP:**

> ¿Cuál es el punto de equilibrio con costos fijos de 180, precio 0,052 y costo variable 0,037? Vendemos 16.500 unidades al mes.

**Llamada:**

```json
punto_equilibrio(costos_fijos=180, precio_unitario=0.052, costo_variable_unitario=0.037, ventas_actuales_unidades=16500)
```

**Salida real:**

```json
{
  "punto_equilibrio_unidades": 12000.0,
  "punto_equilibrio_monto": 624.0,
  "margen_contribucion_unitario": 0.01,
  "razon_margen_contribucion_pct": 28.85,
  "margen_seguridad_pct": 27.27,
  "interpretacion": "Las ventas pueden caer 27.27% antes de entrar en pérdida."
}
```

**Cómo leerlo.** Necesita **12.000 cajas/mes** ($624 MM) para no perder plata; hoy vende 16.500, así que opera con un **margen de seguridad de 27%**. Cada caja aporta $15.000 de contribución (28,85% del precio) para pagar los fijos.

El uso real de esta tool no es el número estático sino las preguntas de comité que habilita: ¿qué pasa con el equilibrio si el arriendo sube $20 MM? ¿Si bajamos precio 5% para defender volumen? Cámbiale un parámetro y la respuesta sale sola — para eso está conectada a tu cliente MCP.
