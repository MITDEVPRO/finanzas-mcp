"""Valoración: WACC, CAPM, DCF, múltiplos y evaluación de proyectos (VAN/TIR)."""

from typing import Annotated

from pydantic import Field

from .app import READ_ONLY, mcp, pct, safe_div


@mcp.tool(annotations=READ_ONLY)
def capm_costo_equity(
    tasa_libre_riesgo: Annotated[float, Field(description="Tasa libre de riesgo, decimal (0.045 = 4.5%)")],
    beta: Annotated[float, Field(description="Beta apalancada de la empresa/comparable")],
    premio_riesgo_mercado: Annotated[float, Field(description="Premio por riesgo de mercado (ERP), decimal")],
    riesgo_pais: Annotated[float, Field(description="Premio por riesgo país, decimal (0 = mercado desarrollado)")] = 0,
    beta_desapalancada: Annotated[float, Field(description="Beta desapalancada del rubro; si se entrega junto a deuda_patrimonio, se reapalanca")] = 0,
    deuda_patrimonio: Annotated[float, Field(description="Razón D/E objetivo para reapalancar la beta")] = 0,
    tasa_impuesto: Annotated[float, Field(description="Tasa de impuesto corporativo, decimal (para reapalancar)")] = 0.27,
) -> dict:
    """Costo del patrimonio (Ke) vía CAPM, con opción de reapalancar una beta de industria (Hamada)."""
    beta_usada = beta
    detalle_beta = "beta entregada directamente"
    if beta_desapalancada and deuda_patrimonio:
        beta_usada = beta_desapalancada * (1 + (1 - tasa_impuesto) * deuda_patrimonio)
        detalle_beta = f"beta reapalancada desde βu={beta_desapalancada} con D/E={deuda_patrimonio} (Hamada)"
    ke = tasa_libre_riesgo + beta_usada * premio_riesgo_mercado + riesgo_pais
    return {
        "ke_costo_equity_pct": pct(ke),
        "beta_utilizada": round(beta_usada, 3),
        "detalle_beta": detalle_beta,
        "formula": "Ke = Rf + β×ERP + riesgo_país",
    }


@mcp.tool(annotations=READ_ONLY)
def wacc(
    valor_equity: Annotated[float, Field(description="Valor del patrimonio (E), a mercado si es posible", gt=0)],
    valor_deuda: Annotated[float, Field(description="Valor de la deuda financiera (D)", ge=0)],
    costo_equity: Annotated[float, Field(description="Costo del patrimonio Ke, decimal")],
    costo_deuda: Annotated[float, Field(description="Costo de la deuda Kd antes de impuesto, decimal")],
    tasa_impuesto: Annotated[float, Field(description="Tasa de impuesto corporativo, decimal", ge=0, le=1)] = 0.27,
) -> dict:
    """WACC — costo promedio ponderado de capital, con escudo fiscal de la deuda."""
    total = valor_equity + valor_deuda
    we, wd = valor_equity / total, valor_deuda / total
    tasa = we * costo_equity + wd * costo_deuda * (1 - tasa_impuesto)
    return {
        "wacc_pct": pct(tasa),
        "peso_equity_pct": pct(we),
        "peso_deuda_pct": pct(wd),
        "kd_despues_impuesto_pct": pct(costo_deuda * (1 - tasa_impuesto)),
        "formula": "WACC = E/(D+E)×Ke + D/(D+E)×Kd×(1-t)",
    }


@mcp.tool(annotations=READ_ONLY)
def dcf(
    flujos_caja_libre: Annotated[
        list[float],
        Field(description="FCF proyectados por año, del año 1 en adelante (ej: [1200, 1350, 1500])", min_length=1),
    ],
    tasa_descuento: Annotated[float, Field(description="Tasa de descuento (WACC), decimal", gt=0)],
    crecimiento_perpetuo: Annotated[float, Field(description="Crecimiento g a perpetuidad, decimal; debe ser < tasa de descuento")] = 0.02,
    deuda_neta: Annotated[float, Field(description="Deuda financiera neta (deuda - caja) para pasar de EV a equity")] = 0,
    sensibilidad: Annotated[bool, Field(description="Incluir matriz de sensibilidad WACC ±1% × g ±1%")] = True,
) -> dict:
    """Valoración por flujos de caja descontados: valor presente de FCFs + valor terminal (Gordon), EV y valor del equity."""
    if crecimiento_perpetuo >= tasa_descuento:
        raise ValueError(
            f"g ({crecimiento_perpetuo}) debe ser menor que la tasa de descuento ({tasa_descuento}); "
            "de lo contrario el valor terminal diverge."
        )

    def _ev(wacc_: float, g_: float) -> float:
        pv = sum(f / (1 + wacc_) ** (i + 1) for i, f in enumerate(flujos_caja_libre))
        tv = flujos_caja_libre[-1] * (1 + g_) / (wacc_ - g_)
        return pv + tv / (1 + wacc_) ** len(flujos_caja_libre)

    ev = _ev(tasa_descuento, crecimiento_perpetuo)
    pv_explicito = sum(f / (1 + tasa_descuento) ** (i + 1) for i, f in enumerate(flujos_caja_libre))
    resultado = {
        "enterprise_value": round(ev, 2),
        "valor_equity": round(ev - deuda_neta, 2),
        "vp_periodo_explicito": round(pv_explicito, 2),
        "vp_valor_terminal": round(ev - pv_explicito, 2),
        "peso_valor_terminal_pct": pct((ev - pv_explicito) / ev) if ev else None,
        "supuestos": {"wacc_pct": pct(tasa_descuento), "g_pct": pct(crecimiento_perpetuo), "anios_explicitos": len(flujos_caja_libre)},
    }
    if sensibilidad:
        filas = {}
        for dw in (-0.01, 0, 0.01):
            w = tasa_descuento + dw
            fila = {}
            for dg in (-0.01, 0, 0.01):
                g = crecimiento_perpetuo + dg
                fila[f"g={pct(g)}%"] = round(_ev(w, g) - deuda_neta, 2) if g < w else "n/a (g>=wacc)"
            filas[f"wacc={pct(w)}%"] = fila
        resultado["sensibilidad_valor_equity"] = filas
    if resultado["peso_valor_terminal_pct"] and resultado["peso_valor_terminal_pct"] > 75:
        resultado["advertencia"] = (
            "El valor terminal pesa más del 75% del EV: la valoración depende casi por completo "
            "de los supuestos de perpetuidad — alargar el período explícito o revisar g."
        )
    return resultado


@mcp.tool(annotations=READ_ONLY)
def valoracion_multiplos(
    ebitda: Annotated[float, Field(description="EBITDA de la empresa a valorar (0 = omitir múltiplo EV/EBITDA)")] = 0,
    utilidad_neta: Annotated[float, Field(description="Utilidad neta (0 = omitir P/E)")] = 0,
    ventas: Annotated[float, Field(description="Ventas (0 = omitir EV/Ventas)")] = 0,
    multiplo_ev_ebitda: Annotated[float, Field(description="Múltiplo EV/EBITDA de comparables")] = 0,
    multiplo_pe: Annotated[float, Field(description="Múltiplo precio/utilidad de comparables")] = 0,
    multiplo_ev_ventas: Annotated[float, Field(description="Múltiplo EV/Ventas de comparables")] = 0,
    deuda_neta: Annotated[float, Field(description="Deuda neta para convertir EV en valor del equity")] = 0,
) -> dict:
    """Valoración por múltiplos de comparables (EV/EBITDA, P/E, EV/Ventas) con rango y promedio."""
    valores = {}
    if ebitda and multiplo_ev_ebitda:
        valores["por_ev_ebitda"] = round(ebitda * multiplo_ev_ebitda - deuda_neta, 2)
    if utilidad_neta and multiplo_pe:
        valores["por_pe"] = round(utilidad_neta * multiplo_pe, 2)
    if ventas and multiplo_ev_ventas:
        valores["por_ev_ventas"] = round(ventas * multiplo_ev_ventas - deuda_neta, 2)
    if not valores:
        raise ValueError(
            "Entregar al menos un par métrica+múltiplo: (ebitda, multiplo_ev_ebitda), "
            "(utilidad_neta, multiplo_pe) o (ventas, multiplo_ev_ventas)."
        )
    lista = list(valores.values())
    return {
        "valor_equity_por_metodo": valores,
        "rango": {"min": min(lista), "max": max(lista)},
        "promedio_simple": round(sum(lista) / len(lista), 2),
        "nota": "P/E ya es valor de equity; EV/EBITDA y EV/Ventas se ajustan por deuda neta.",
    }


@mcp.tool(annotations=READ_ONLY)
def van_tir(
    inversion_inicial: Annotated[float, Field(description="Inversión inicial en t=0, en positivo (ej: 50000)", gt=0)],
    flujos: Annotated[list[float], Field(description="Flujos netos por período, del período 1 en adelante", min_length=1)],
    tasa_descuento: Annotated[float, Field(description="Tasa de descuento por período, decimal", gt=0)],
) -> dict:
    """Evaluación de proyecto: VAN, TIR, payback simple y descontado, e índice de rentabilidad."""
    van = -inversion_inicial + sum(f / (1 + tasa_descuento) ** (i + 1) for i, f in enumerate(flujos))

    def _van(r: float) -> float:
        return -inversion_inicial + sum(f / (1 + r) ** (i + 1) for i, f in enumerate(flujos))

    # TIR por bisección en [-0.99, 10]
    tir = None
    lo, hi = -0.99, 10.0
    if _van(lo) * _van(hi) < 0:
        for _ in range(200):
            mid = (lo + hi) / 2
            if _van(lo) * _van(mid) <= 0:
                hi = mid
            else:
                lo = mid
        tir = (lo + hi) / 2

    payback = payback_desc = None
    acum = acum_d = -inversion_inicial
    for i, f in enumerate(flujos, start=1):
        prev, prev_d = acum, acum_d
        acum += f
        acum_d += f / (1 + tasa_descuento) ** i
        if payback is None and acum >= 0:
            payback = round(i - 1 + (-prev / f), 2) if f else i
        if payback_desc is None and acum_d >= 0:
            fd = f / (1 + tasa_descuento) ** i
            payback_desc = round(i - 1 + (-prev_d / fd), 2) if fd else i

    vp_flujos = van + inversion_inicial
    return {
        "van": round(van, 2),
        "tir_pct": pct(tir) if tir is not None else None,
        "payback_simple_anios": payback,
        "payback_descontado_anios": payback_desc,
        "indice_rentabilidad": round(safe_div(vp_flujos, inversion_inicial) or 0, 3),
        "decision": "ACEPTAR (VAN > 0)" if van > 0 else "RECHAZAR (VAN <= 0)",
    }
