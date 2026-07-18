"""Operación y planificación: equilibrio, variaciones, aging, depreciación, crédito, flujo de caja."""

from typing import Annotated

from pydantic import Field

from .app import READ_ONLY, mcp, pct, safe_div


@mcp.tool(annotations=READ_ONLY)
def punto_equilibrio(
    costos_fijos: Annotated[float, Field(description="Costos fijos totales del período", ge=0)],
    precio_unitario: Annotated[float, Field(description="Precio de venta unitario", gt=0)],
    costo_variable_unitario: Annotated[float, Field(description="Costo variable unitario", ge=0)],
    ventas_actuales_unidades: Annotated[float, Field(description="Unidades vendidas hoy, para margen de seguridad (0 = omitir)")] = 0,
) -> dict:
    """Punto de equilibrio en unidades y en monto, con margen de contribución y margen de seguridad."""
    mc_unitario = precio_unitario - costo_variable_unitario
    if mc_unitario <= 0:
        raise ValueError(
            f"El margen de contribución unitario es {mc_unitario}: con precio <= costo variable "
            "no existe punto de equilibrio (cada unidad extra pierde plata)."
        )
    pe_unidades = costos_fijos / mc_unitario
    resultado = {
        "punto_equilibrio_unidades": round(pe_unidades, 1),
        "punto_equilibrio_monto": round(pe_unidades * precio_unitario, 2),
        "margen_contribucion_unitario": round(mc_unitario, 2),
        "razon_margen_contribucion_pct": pct(mc_unitario / precio_unitario),
    }
    if ventas_actuales_unidades:
        ms = (ventas_actuales_unidades - pe_unidades) / ventas_actuales_unidades
        resultado["margen_seguridad_pct"] = pct(ms)
        resultado["interpretacion"] = (
            f"Las ventas pueden caer {pct(ms)}% antes de entrar en pérdida."
            if ms > 0
            else "Se está vendiendo BAJO el punto de equilibrio: hoy la operación pierde plata."
        )
    return resultado


@mcp.tool(annotations=READ_ONLY)
def variacion(
    valor_actual: Annotated[float, Field(description="Valor del período actual")],
    valor_anterior: Annotated[float, Field(description="Valor del período de comparación")],
    periodos: Annotated[int, Field(description="Nº de períodos entre ambos valores, para CAGR (1 = variación simple)", ge=1)] = 1,
) -> dict:
    """Variación absoluta y porcentual entre dos valores; CAGR si hay más de un período."""
    absoluta = valor_actual - valor_anterior
    relativa = safe_div(absoluta, abs(valor_anterior))
    resultado = {
        "variacion_absoluta": round(absoluta, 2),
        "variacion_pct": pct(relativa) if relativa is not None else None,
    }
    if periodos > 1 and valor_anterior > 0 and valor_actual > 0:
        cagr = (valor_actual / valor_anterior) ** (1 / periodos) - 1
        resultado["cagr_pct"] = pct(cagr)
    return resultado


@mcp.tool(annotations=READ_ONLY)
def aging_cartera(
    documentos: Annotated[
        list[dict],
        Field(
            description=(
                "Lista de documentos: [{'monto': 1500000, 'dias_vencido': 45, 'cliente': 'opcional'}]. "
                "dias_vencido negativo = aún por vencer."
            ),
            min_length=1,
        ),
    ],
) -> dict:
    """Aging de cartera en tramos estándar (por vencer / 1-30 / 31-60 / 61-90 / 91-180 / +180) con concentración por cliente."""
    tramos = {"por_vencer": 0.0, "1_30": 0.0, "31_60": 0.0, "61_90": 0.0, "91_180": 0.0, "mas_180": 0.0}
    por_cliente: dict[str, float] = {}
    total = 0.0
    for i, d in enumerate(documentos):
        if "monto" not in d or "dias_vencido" not in d:
            raise ValueError(f"Documento {i}: se requieren llaves 'monto' y 'dias_vencido'. Recibido: {list(d.keys())}")
        monto, dias = float(d["monto"]), int(d["dias_vencido"])
        total += monto
        if dias <= 0:
            tramos["por_vencer"] += monto
        elif dias <= 30:
            tramos["1_30"] += monto
        elif dias <= 60:
            tramos["31_60"] += monto
        elif dias <= 90:
            tramos["61_90"] += monto
        elif dias <= 180:
            tramos["91_180"] += monto
        else:
            tramos["mas_180"] += monto
        cliente = str(d.get("cliente", "(sin cliente)"))
        por_cliente[cliente] = por_cliente.get(cliente, 0.0) + monto
    vencido = total - tramos["por_vencer"]
    top = sorted(por_cliente.items(), key=lambda x: -x[1])[:5]
    return {
        "total_cartera": round(total, 2),
        "total_vencido": round(vencido, 2),
        "pct_vencido": pct(safe_div(vencido, total) or 0),
        "tramos": {k: round(v, 2) for k, v in tramos.items()},
        "tramos_pct": {k: pct(safe_div(v, total) or 0) for k, v in tramos.items()},
        "top_5_clientes": [
            {"cliente": c, "monto": round(m, 2), "pct": pct(m / total)} for c, m in top
        ] if len(por_cliente) > 1 else None,
        "documentos": len(documentos),
    }


@mcp.tool(annotations=READ_ONLY)
def depreciacion(
    valor_activo: Annotated[float, Field(description="Valor de adquisición del activo", gt=0)],
    vida_util_anios: Annotated[int, Field(description="Vida útil normal en años", ge=1)],
    valor_residual: Annotated[float, Field(description="Valor residual al final de la vida útil", ge=0)] = 0,
    metodo: Annotated[
        str,
        Field(description="'lineal', 'acelerada' (vida/3, estilo Chile Art.31 N°5 bis) o 'suma_digitos'"),
    ] = "lineal",
) -> dict:
    """Tabla de depreciación anual por método lineal, acelerada (vida útil ÷ 3) o suma de dígitos."""
    base = valor_activo - valor_residual
    tabla = []
    if metodo == "acelerada":
        vida = max(1, vida_util_anios // 3)
        cuota = base / vida
        tabla = [{"anio": i + 1, "cuota": round(cuota, 2)} for i in range(vida)]
        nota = f"Vida acelerada = {vida_util_anios}//3 = {vida} años (mínimo 1). En Chile exige requisitos del Art. 31 N°5 bis LIR."
    elif metodo == "suma_digitos":
        suma = vida_util_anios * (vida_util_anios + 1) / 2
        tabla = [
            {"anio": i + 1, "cuota": round(base * (vida_util_anios - i) / suma, 2)}
            for i in range(vida_util_anios)
        ]
        nota = "Cuotas decrecientes: deprecia más al inicio."
    elif metodo == "lineal":
        cuota = base / vida_util_anios
        tabla = [{"anio": i + 1, "cuota": round(cuota, 2)} for i in range(vida_util_anios)]
        nota = "Cuota constante durante toda la vida útil."
    else:
        raise ValueError(f"Método '{metodo}' no soportado. Usar: lineal, acelerada o suma_digitos.")
    acumulado = 0.0
    for fila in tabla:
        acumulado += fila["cuota"]
        fila["acumulada"] = round(acumulado, 2)
        fila["valor_libro"] = round(valor_activo - acumulado, 2)
    return {"metodo": metodo, "base_depreciable": round(base, 2), "tabla": tabla, "nota": nota}


@mcp.tool(annotations=READ_ONLY)
def amortizacion_credito(
    principal: Annotated[float, Field(description="Monto del crédito", gt=0)],
    tasa_periodo: Annotated[float, Field(description="Tasa de interés POR PERÍODO, decimal (mensual si cuotas mensuales)", gt=0)],
    num_cuotas: Annotated[int, Field(description="Número de cuotas", ge=1)],
    sistema: Annotated[str, Field(description="'frances' (cuota fija) o 'aleman' (amortización fija)")] = "frances",
    detalle_maximo: Annotated[int, Field(description="Máx filas de tabla a devolver (resto se resume)", ge=1)] = 24,
) -> dict:
    """Tabla de amortización de un crédito en sistema francés (cuota fija) o alemán (amortización constante)."""
    tabla = []
    saldo = principal
    total_interes = 0.0
    if sistema == "frances":
        cuota = principal * tasa_periodo / (1 - (1 + tasa_periodo) ** -num_cuotas)
        for n in range(1, num_cuotas + 1):
            interes = saldo * tasa_periodo
            amort = cuota - interes
            saldo -= amort
            total_interes += interes
            tabla.append({"cuota_n": n, "cuota": round(cuota, 2), "interes": round(interes, 2), "amortizacion": round(amort, 2), "saldo": round(max(saldo, 0), 2)})
    elif sistema == "aleman":
        amort = principal / num_cuotas
        for n in range(1, num_cuotas + 1):
            interes = saldo * tasa_periodo
            cuota = amort + interes
            saldo -= amort
            total_interes += interes
            tabla.append({"cuota_n": n, "cuota": round(cuota, 2), "interes": round(interes, 2), "amortizacion": round(amort, 2), "saldo": round(max(saldo, 0), 2)})
    else:
        raise ValueError(f"Sistema '{sistema}' no soportado. Usar: frances o aleman.")
    resumen = {
        "sistema": sistema,
        "cuota_inicial": tabla[0]["cuota"],
        "cuota_final": tabla[-1]["cuota"],
        "total_intereses": round(total_interes, 2),
        "total_pagado": round(principal + total_interes, 2),
        "costo_total_sobre_principal_pct": pct(total_interes / principal),
    }
    if num_cuotas > detalle_maximo:
        resumen["tabla"] = tabla[:detalle_maximo]
        resumen["nota"] = f"Tabla truncada a {detalle_maximo} de {num_cuotas} cuotas (subir detalle_maximo para ver más)."
    else:
        resumen["tabla"] = tabla
    return resumen


@mcp.tool(annotations=READ_ONLY)
def interes_compuesto(
    capital: Annotated[float, Field(description="Capital inicial (VP) o meta final (VF) según 'calcular'", gt=0)],
    tasa_periodo: Annotated[float, Field(description="Tasa por período, decimal", gt=0)],
    periodos: Annotated[int, Field(description="Número de períodos", ge=1)],
    aporte_periodico: Annotated[float, Field(description="Aporte al final de cada período (anualidad ordinaria)", ge=0)] = 0,
    calcular: Annotated[str, Field(description="'vf' (valor futuro de capital+aportes) o 'vp' (valor presente de la meta)")] = "vf",
) -> dict:
    """Interés compuesto: valor futuro o presente, con aportes periódicos opcionales."""
    r, n = tasa_periodo, periodos
    if calcular == "vf":
        vf_capital = capital * (1 + r) ** n
        vf_aportes = aporte_periodico * (((1 + r) ** n - 1) / r) if aporte_periodico else 0
        total = vf_capital + vf_aportes
        aportado = capital + aporte_periodico * n
        return {
            "valor_futuro": round(total, 2),
            "vf_del_capital": round(vf_capital, 2),
            "vf_de_los_aportes": round(vf_aportes, 2),
            "total_aportado": round(aportado, 2),
            "interes_ganado": round(total - aportado, 2),
        }
    if calcular == "vp":
        return {
            "valor_presente": round(capital / (1 + r) ** n, 2),
            "nota": f"Cuánto vale hoy recibir {capital} dentro de {n} períodos al {pct(r)}% por período.",
        }
    raise ValueError(f"'calcular' debe ser 'vf' o 'vp', no '{calcular}'.")


@mcp.tool(annotations=READ_ONLY)
def flujo_caja_indirecto(
    utilidad_neta: Annotated[float, Field(description="Utilidad neta del período")],
    depreciacion_amortizacion: Annotated[float, Field(description="Depreciación + amortización del período", ge=0)],
    delta_cxc: Annotated[float, Field(description="Variación CxC (final - inicial); aumento = consume caja")],
    delta_inventario: Annotated[float, Field(description="Variación inventario (final - inicial)")],
    delta_cxp: Annotated[float, Field(description="Variación CxP (final - inicial); aumento = libera caja")],
    capex: Annotated[float, Field(description="Inversión en activo fijo del período, en positivo", ge=0)] = 0,
    nueva_deuda: Annotated[float, Field(description="Deuda tomada en el período", ge=0)] = 0,
    pago_deuda: Annotated[float, Field(description="Amortizaciones de deuda pagadas", ge=0)] = 0,
    dividendos: Annotated[float, Field(description="Dividendos pagados", ge=0)] = 0,
    otros_ajustes: Annotated[float, Field(description="Otros ajustes no-caja o partidas (+aporta / -consume)")] = 0,
) -> dict:
    """Flujo de caja por método indirecto: FCO, FCI, FCF (flujo libre) y flujo neto del período."""
    fco = utilidad_neta + depreciacion_amortizacion - delta_cxc - delta_inventario + delta_cxp + otros_ajustes
    fci = -capex
    fcf = fco + fci
    f_fin = nueva_deuda - pago_deuda - dividendos
    neto = fcf + f_fin
    return {
        "flujo_operacional_fco": round(fco, 2),
        "flujo_inversion_fci": round(fci, 2),
        "flujo_caja_libre_fcf": round(fcf, 2),
        "flujo_financiamiento": round(f_fin, 2),
        "flujo_neto_periodo": round(neto, 2),
        "interpretacion": (
            "FCO positivo con FCF negativo = la operación genera caja pero el capex la consume. "
            "FCO negativo sostenido = el negocio se financia con deuda o capital, no con su operación."
        ),
    }
