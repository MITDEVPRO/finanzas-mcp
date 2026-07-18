"""Instancia compartida del servidor FastMCP."""

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

mcp = FastMCP(
    "finanzas",
    instructions=(
        "Calculadoras financieras genéricas: ratios, diagnóstico (DuPont, Z-Score, "
        "F-Score), valoración (WACC, CAPM, DCF, múltiplos, VAN/TIR), operación "
        "(punto de equilibrio, aging, depreciación, amortización) y tributario Chile "
        "(IVA, impuesto empresa, corrección monetaria). Todas las tools son cálculo "
        "puro sobre datos que entrega el usuario: no consultan sistemas externos ni "
        "guardan estado. Montos en la moneda que entregue el usuario; tasas en "
        "decimales (0.10 = 10%) salvo que el parámetro indique otra cosa. "
        "Los resultados son referenciales y no constituyen asesoría financiera."
    ),
)

# Todas las tools de este servidor son cálculo puro.
READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)


def pct(value: float, decimals: int = 2) -> float:
    """Redondea un decimal expresado como porcentaje (0.1234 -> 12.34)."""
    return round(value * 100, decimals)


def safe_div(num: float, den: float) -> float | None:
    """División que devuelve None en vez de reventar con denominador 0."""
    return None if den == 0 else num / den
