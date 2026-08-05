# Ejemplos con salidas reales

Cinco casos de una misma empresa ficticia — una **distribuidora chilena mediana** (cifras en millones de CLP) — resueltos con las tools de finanzas-mcp. Cada ejemplo trae la pregunta como se la harías a tu cliente MCP (Claude Desktop, Claude Code u otro), los parámetros exactos y la **salida real** de la tool, sin editar.

| Ejemplo | Tool | Pregunta que responde |
|---|---|---|
| [WACC](wacc.md) | `wacc` | ¿A qué tasa descuento los flujos de esta empresa? |
| [Valoración DCF](dcf.md) | `dcf` | ¿Cuánto vale el negocio (con sensibilidad WACC × g)? |
| [Altman Z-Score](altman-z.md) | `altman_z_score` | ¿Qué tan cerca está de la insolvencia? |
| [Punto de equilibrio](punto-equilibrio.md) | `punto_equilibrio` | ¿Cuánto pueden caer las ventas antes de perder plata? |
| [Ciclo de caja valorizado](ciclo-caja.md) | `ciclo_caja` | ¿Cuánta plata vale cada día del ciclo (y cómo se consolida multipaís)? |

Los cinco se encadenan: el WACC alimenta el DCF, y el Z-Score más el punto de equilibrio le ponen contexto de riesgo a esa valoración.

## Reproducirlos

Con el servidor conectado a tu cliente MCP basta pegar la pregunta de cada ejemplo. Para verificar la matemática sin cliente:

```bash
uv run --with pytest pytest   # 33 tests sobre las mismas funciones
```

¿Falta un caso que te serviría? [Abre un issue](https://github.com/MITDEVPRO/finanzas-mcp/issues).
