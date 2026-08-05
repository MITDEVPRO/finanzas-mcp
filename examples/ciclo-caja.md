# Ciclo de caja valorizado — ¿cuánta plata vale cada día del ciclo?

> Tool nacida de una sugerencia en LinkedIn: "Ciclo de Caja con días y valor de día unitario de cada uno… y el condimento del multipaís".

**El caso.** La distribuidora vende $7.300 MM al año con un costo de ventas de $5.475 MM. En el balance promedio: inventario $1.800 MM, cuentas por cobrar $1.200 MM, cuentas por pagar $900 MM.

**La pregunta al cliente MCP:**

> ¿Cuál es mi ciclo de caja y cuánto vale cada día? Ventas 7.300, costo 5.475, inventario 1.800, CxC 1.200, CxP 900 (MM CLP).

**Llamada:**

```json
ciclo_caja(ventas=7300, costo_ventas=5475, inventario_promedio=1800, cxc_promedio=1200, cxp_promedio=900, moneda="MM CLP")
```

**Salida real:**

```json
{
  "dias": {
    "dio_inventario": 120.0,
    "dso_cobro": 60.0,
    "dpo_pago": 60.0,
    "ccc_ciclo_caja": 120.0
  },
  "valor_dia_unitario": {
    "dia_de_inventario": 15.0,
    "dia_de_cobro": 20.0,
    "dia_de_pago": 15.0,
    "nota": "1 día de inventario o de pago se valoriza a costo; 1 día de cobro, a venta."
  },
  "caja_atrapada_en_el_ciclo": 2100,
  "efecto_de_mover_1_dia": {
    "bajar_1_dia_inventario_libera": 15.0,
    "cobrar_1_dia_antes_libera": 20.0,
    "pagar_1_dia_despues_libera": 15.0
  },
  "interpretacion": "El ciclo es de 120.0 días y mantiene 2100 MM CLP atrapados en la operación. Decir 'cada día de cobro cuesta 20.0 MM CLP' mueve más decisiones que reportar los días a secas.",
  "nota_multipais": "Consolidación multipaís: calcule por entidad en su moneda y pondere los DÍAS por ventas; convierta a una moneda común solo si necesita sumar los montos."
}
```

**Cómo leerlo.** El ciclo son **120 días**: la empresa compra, fabrica inventario por 120 días, cobra a 60 y paga a 60 — y eso mantiene **$2.100 MM atrapados** financiando la operación. La gracia no son los días sino el precio de cada palanca: bajar **1 día de inventario libera $15 MM**; cobrar **1 día antes libera $20 MM**; estirar el pago 1 día, otros $15 MM. Un plan realista de −10 días de inventario y −5 de cobranza vale **$250 MM de caja** — así se le habla a un comité.

**El condimento multipaís.** Los días son comparables entre países; los pesos, no. Corre la tool por entidad en su moneda local, compara los DÍAS (¿por qué México cobra a 45 y Perú a 90?), y pondera por ventas para el consolidado. Convierte a moneda común solo si necesitas sumar la caja atrapada del grupo.
