"""Tributario (Chile por defecto, parametrizable): IVA, impuesto empresa, corrección monetaria, escudo fiscal."""

from typing import Annotated

from pydantic import Field

from .app import READ_ONLY, mcp, pct


@mcp.tool(annotations=READ_ONLY)
def iva(
    monto: Annotated[float, Field(description="Monto sobre el que operar", gt=0)],
    operacion: Annotated[str, Field(description="'agregar' (neto → bruto) o 'extraer' (bruto → neto)")] = "agregar",
    tasa: Annotated[float, Field(description="Tasa de IVA, decimal (Chile: 0.19)", gt=0, le=1)] = 0.19,
) -> dict:
    """Agrega o extrae IVA de un monto (Chile 19% por defecto, tasa configurable)."""
    if operacion == "agregar":
        impuesto = monto * tasa
        return {"neto": round(monto, 2), "iva": round(impuesto, 2), "bruto": round(monto + impuesto, 2), "tasa_pct": pct(tasa)}
    if operacion == "extraer":
        neto = monto / (1 + tasa)
        return {"bruto": round(monto, 2), "neto": round(neto, 2), "iva": round(monto - neto, 2), "tasa_pct": pct(tasa)}
    raise ValueError(f"'operacion' debe ser 'agregar' o 'extraer', no '{operacion}'.")


@mcp.tool(annotations=READ_ONLY)
def impuesto_empresa(
    base_imponible: Annotated[float, Field(description="Base imponible (renta líquida imponible)")],
    regimen: Annotated[
        str,
        Field(description="'14A' (semi-integrado, 27%), '14D3' (pyme, 25%) u 'otro' (usar tasa_custom)"),
    ] = "14A",
    tasa_custom: Annotated[float, Field(description="Tasa a usar si regimen='otro', decimal", ge=0, le=1)] = 0,
    ppm_pagados: Annotated[float, Field(description="PPM ya pagados en el ejercicio, para el saldo (0 = omitir)", ge=0)] = 0,
) -> dict:
    """Impuesto de primera categoría (Chile): 14A 27%, 14 D N°3 pyme 25%, o tasa configurable; saldo contra PPM."""
    tasas = {"14A": 0.27, "14D3": 0.25}
    if regimen in tasas:
        tasa = tasas[regimen]
    elif regimen == "otro":
        if not tasa_custom:
            raise ValueError("Con regimen='otro' se debe entregar tasa_custom > 0.")
        tasa = tasa_custom
    else:
        raise ValueError(f"Régimen '{regimen}' no soportado. Usar: 14A, 14D3 u otro.")
    impuesto = max(base_imponible, 0) * tasa
    resultado = {
        "regimen": regimen,
        "tasa_pct": pct(tasa),
        "impuesto_determinado": round(impuesto, 2),
    }
    if base_imponible <= 0:
        resultado["nota"] = "Base imponible negativa o cero: sin impuesto; la pérdida tributaria se arrastra."
    if ppm_pagados:
        saldo = impuesto - ppm_pagados
        resultado["ppm_pagados"] = ppm_pagados
        resultado["saldo"] = round(saldo, 2)
        resultado["situacion"] = "por pagar en la declaración anual" if saldo > 0 else "devolución a favor"
    return resultado


@mcp.tool(annotations=READ_ONLY)
def correccion_monetaria(
    monto: Annotated[float, Field(description="Monto histórico a corregir")],
    indice_inicial: Annotated[float, Field(description="Índice del período de origen (IPC, UF u otro)", gt=0)],
    indice_final: Annotated[float, Field(description="Índice del período de cierre", gt=0)],
) -> dict:
    """Corrección monetaria de un monto por variación de un índice (IPC/UF): monto corregido y ajuste."""
    factor = indice_final / indice_inicial
    corregido = monto * factor
    return {
        "monto_historico": round(monto, 2),
        "factor_correccion": round(factor, 6),
        "variacion_indice_pct": pct(factor - 1),
        "monto_corregido": round(corregido, 2),
        "ajuste": round(corregido - monto, 2),
        "nota": "El usuario entrega los índices (ej: UF o IPC de cada fecha); la tool no consulta valores en línea.",
    }


@mcp.tool(annotations=READ_ONLY)
def escudo_fiscal(
    gasto_deducible: Annotated[float, Field(description="Gasto deducible del período (intereses, depreciación, etc.)", gt=0)],
    tasa_impuesto: Annotated[float, Field(description="Tasa de impuesto corporativo, decimal", gt=0, le=1)] = 0.27,
) -> dict:
    """Escudo fiscal: ahorro de impuesto que genera un gasto deducible (gasto × tasa)."""
    ahorro = gasto_deducible * tasa_impuesto
    return {
        "gasto_deducible": round(gasto_deducible, 2),
        "tasa_pct": pct(tasa_impuesto),
        "ahorro_impuesto": round(ahorro, 2),
        "costo_neto_del_gasto": round(gasto_deducible - ahorro, 2),
        "nota": "Solo aplica si la empresa tiene base imponible positiva contra la cual deducir.",
    }


@mcp.tool(annotations=READ_ONLY)
def ppm_calculo(
    ingresos_brutos_mes: Annotated[float, Field(description="Ingresos brutos del mes", gt=0)],
    tasa_ppm: Annotated[float, Field(description="Tasa PPM vigente, decimal (ej: 0.005 = 0,5%)", gt=0, le=1)] = 0.005,
) -> dict:
    """Pago provisional mensual (PPM) sobre ingresos brutos con tasa configurable."""
    return {
        "ingresos_brutos": round(ingresos_brutos_mes, 2),
        "tasa_ppm_pct": pct(tasa_ppm, 3),
        "ppm_del_mes": round(ingresos_brutos_mes * tasa_ppm, 2),
        "nota": "La tasa PPM se recalcula anualmente según la relación impuesto/ingresos del ejercicio anterior.",
    }
