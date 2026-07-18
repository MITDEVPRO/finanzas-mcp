"""Ratios financieros y modelos de diagnóstico (DuPont, Altman, Piotroski)."""

from typing import Annotated

from pydantic import Field

from .app import READ_ONLY, mcp, pct, safe_div


@mcp.tool(annotations=READ_ONLY)
def ratios_liquidez(
    activo_corriente: Annotated[float, Field(description="Activo corriente total")],
    pasivo_corriente: Annotated[float, Field(description="Pasivo corriente total")],
    inventario: Annotated[float, Field(description="Inventario (existencias)")] = 0,
    efectivo: Annotated[float, Field(description="Efectivo y equivalentes")] = 0,
) -> dict:
    """Ratios de liquidez: corriente, ácida (quick), de caja y capital de trabajo."""
    corriente = safe_div(activo_corriente, pasivo_corriente)
    acida = safe_div(activo_corriente - inventario, pasivo_corriente)
    caja = safe_div(efectivo, pasivo_corriente)
    wc = activo_corriente - pasivo_corriente
    if corriente is None:
        estado = "sin pasivo corriente: liquidez no medible (revisar datos)"
    elif corriente >= 2:
        estado = "liquidez holgada (posible exceso de activos ociosos si >3)"
    elif corriente >= 1:
        estado = "liquidez adecuada"
    else:
        estado = "riesgo de liquidez: activo corriente no cubre el pasivo corriente"
    return {
        "razon_corriente": round(corriente, 2) if corriente is not None else None,
        "razon_acida": round(acida, 2) if acida is not None else None,
        "razon_caja": round(caja, 2) if caja is not None else None,
        "capital_trabajo": round(wc, 2),
        "interpretacion": estado,
    }


@mcp.tool(annotations=READ_ONLY)
def ratios_rentabilidad(
    ventas: Annotated[float, Field(description="Ingresos por ventas del período")],
    utilidad_bruta: Annotated[float, Field(description="Utilidad bruta (ventas - costo de ventas)")],
    utilidad_operacional: Annotated[float, Field(description="Resultado operacional (EBIT)")],
    utilidad_neta: Annotated[float, Field(description="Utilidad neta del período")],
    activos_totales: Annotated[float, Field(description="Activos totales")],
    patrimonio: Annotated[float, Field(description="Patrimonio total")],
) -> dict:
    """Márgenes (bruto, operacional, neto) y retornos ROA / ROE, en porcentaje."""
    return {
        "margen_bruto_pct": pct(safe_div(utilidad_bruta, ventas) or 0),
        "margen_operacional_pct": pct(safe_div(utilidad_operacional, ventas) or 0),
        "margen_neto_pct": pct(safe_div(utilidad_neta, ventas) or 0),
        "roa_pct": pct(safe_div(utilidad_neta, activos_totales) or 0),
        "roe_pct": pct(safe_div(utilidad_neta, patrimonio) or 0),
        "nota": "Contribución=$ y Margen=% — comparar contra el benchmark del rubro, no un umbral universal.",
    }


@mcp.tool(annotations=READ_ONLY)
def ratios_eficiencia(
    ventas: Annotated[float, Field(description="Ventas del período (a precio de venta)")],
    costo_ventas: Annotated[float, Field(description="Costo de ventas del período")],
    inventario_promedio: Annotated[float, Field(description="Inventario promedio del período")],
    cxc_promedio: Annotated[float, Field(description="Cuentas por cobrar promedio")],
    cxp_promedio: Annotated[float, Field(description="Cuentas por pagar promedio")],
    dias_periodo: Annotated[int, Field(description="Días del período analizado", ge=1, le=366)] = 365,
) -> dict:
    """Rotaciones y ciclo de conversión de caja: DIO, DSO, DPO y CCC en días."""
    dio = safe_div(inventario_promedio * dias_periodo, costo_ventas)
    dso = safe_div(cxc_promedio * dias_periodo, ventas)
    dpo = safe_div(cxp_promedio * dias_periodo, costo_ventas)
    ccc = None
    if None not in (dio, dso, dpo):
        ccc = dio + dso - dpo
    return {
        "dio_dias_inventario": round(dio, 1) if dio is not None else None,
        "dso_dias_cobro": round(dso, 1) if dso is not None else None,
        "dpo_dias_pago": round(dpo, 1) if dpo is not None else None,
        "ccc_ciclo_conversion_caja": round(ccc, 1) if ccc is not None else None,
        "rotacion_inventario_veces": round(safe_div(costo_ventas, inventario_promedio) or 0, 2),
        "interpretacion": (
            "CCC alto = más días financiando la operación con caja propia; "
            "compararlo con el ciclo del rubro y con la evolución histórica."
        ),
    }


@mcp.tool(annotations=READ_ONLY)
def ratios_endeudamiento(
    pasivos_totales: Annotated[float, Field(description="Pasivos totales (deuda + otros)")],
    patrimonio: Annotated[float, Field(description="Patrimonio total")],
    activos_totales: Annotated[float, Field(description="Activos totales")],
    ebitda: Annotated[float, Field(description="EBITDA del período (0 si no aplica)")] = 0,
    deuda_financiera: Annotated[float, Field(description="Deuda financiera (bancos + bonos)")] = 0,
    gastos_financieros: Annotated[float, Field(description="Gastos financieros del período")] = 0,
    ebit: Annotated[float, Field(description="Resultado operacional para cobertura de intereses")] = 0,
) -> dict:
    """Apalancamiento: leverage, endeudamiento sobre activos, deuda/EBITDA y cobertura de intereses."""
    return {
        "leverage_pasivos_sobre_patrimonio": round(safe_div(pasivos_totales, patrimonio) or 0, 2),
        "endeudamiento_sobre_activos_pct": pct(safe_div(pasivos_totales, activos_totales) or 0),
        "deuda_financiera_sobre_ebitda": (
            round(safe_div(deuda_financiera, ebitda), 2) if ebitda else None
        ),
        "cobertura_intereses_veces": (
            round(safe_div(ebit, gastos_financieros), 2) if gastos_financieros else None
        ),
        "interpretacion": (
            "Referencias usuales: deuda/EBITDA > 3-4x exige plan de desapalancamiento; "
            "cobertura de intereses < 2x es señal de estrés."
        ),
    }


@mcp.tool(annotations=READ_ONLY)
def dupont(
    ventas: Annotated[float, Field(description="Ventas del período")],
    utilidad_neta: Annotated[float, Field(description="Utilidad neta")],
    activos_totales: Annotated[float, Field(description="Activos totales")],
    patrimonio: Annotated[float, Field(description="Patrimonio total")],
    ebit: Annotated[float, Field(description="EBIT — solo para DuPont de 5 factores (0 = omitir)")] = 0,
    utilidad_antes_impuesto: Annotated[float, Field(description="UAI — solo para 5 factores (0 = omitir)")] = 0,
) -> dict:
    """Descomposición DuPont del ROE en 3 factores (margen × rotación × apalancamiento); 5 factores si se entrega EBIT y UAI."""
    margen = safe_div(utilidad_neta, ventas) or 0
    rotacion = safe_div(ventas, activos_totales) or 0
    apalancamiento = safe_div(activos_totales, patrimonio) or 0
    resultado = {
        "roe_pct": pct(margen * rotacion * apalancamiento),
        "factores_3": {
            "margen_neto_pct": pct(margen),
            "rotacion_activos_veces": round(rotacion, 3),
            "multiplicador_apalancamiento": round(apalancamiento, 3),
        },
        "driver_dominante": max(
            [("margen", margen), ("rotacion", rotacion / 10), ("apalancamiento", apalancamiento / 10)],
            key=lambda x: x[1],
        )[0],
    }
    if ebit and utilidad_antes_impuesto:
        resultado["factores_5"] = {
            "carga_tributaria": round(safe_div(utilidad_neta, utilidad_antes_impuesto) or 0, 3),
            "carga_intereses": round(safe_div(utilidad_antes_impuesto, ebit) or 0, 3),
            "margen_operacional_pct": pct(safe_div(ebit, ventas) or 0),
            "rotacion_activos_veces": round(rotacion, 3),
            "multiplicador_apalancamiento": round(apalancamiento, 3),
        }
    return resultado


@mcp.tool(annotations=READ_ONLY)
def altman_z_score(
    activos_totales: Annotated[float, Field(description="Activos totales", gt=0)],
    pasivos_totales: Annotated[float, Field(description="Pasivos totales", gt=0)],
    capital_trabajo: Annotated[float, Field(description="Capital de trabajo (AC - PC)")],
    utilidades_retenidas: Annotated[float, Field(description="Utilidades retenidas acumuladas")],
    ebit: Annotated[float, Field(description="Resultado operacional (EBIT)")],
    patrimonio: Annotated[float, Field(description="Patrimonio contable (o capitalización bursátil si cotiza)")],
    ventas: Annotated[float, Field(description="Ventas del período (solo modelos con X5)")] = 0,
    modelo: Annotated[
        str,
        Field(description="'privada' (Z', manufactura no listada), 'publica' (Z original) o 'servicios' (Z'', no manufactura/emergentes)"),
    ] = "privada",
) -> dict:
    """Altman Z-Score de riesgo de insolvencia, en sus 3 variantes (pública, privada, servicios)."""
    x1 = capital_trabajo / activos_totales
    x2 = utilidades_retenidas / activos_totales
    x3 = ebit / activos_totales
    x4 = patrimonio / pasivos_totales
    x5 = ventas / activos_totales
    if modelo == "publica":
        z = 1.2 * x1 + 1.4 * x2 + 3.3 * x3 + 0.6 * x4 + 1.0 * x5
        z_seguro, z_gris = 2.99, 1.81
    elif modelo == "servicios":
        z = 6.56 * x1 + 3.26 * x2 + 6.72 * x3 + 1.05 * x4
        z_seguro, z_gris = 2.6, 1.1
    else:  # privada (Z')
        z = 0.717 * x1 + 0.847 * x2 + 3.107 * x3 + 0.420 * x4 + 0.998 * x5
        z_seguro, z_gris = 2.9, 1.23
    if z >= z_seguro:
        zona = "SEGURA — baja probabilidad de insolvencia"
    elif z >= z_gris:
        zona = "GRIS — monitorear liquidez y deuda"
    else:
        zona = "PELIGRO — probabilidad relevante de insolvencia a 2 años"
    return {
        "z_score": round(z, 2),
        "modelo": modelo,
        "zona": zona,
        "umbrales": {"zona_segura_desde": z_seguro, "zona_peligro_bajo": z_gris},
        "componentes": {"x1_wc_ta": round(x1, 3), "x2_re_ta": round(x2, 3), "x3_ebit_ta": round(x3, 3), "x4_eq_pas": round(x4, 3), "x5_ventas_ta": round(x5, 3)},
    }


@mcp.tool(annotations=READ_ONLY)
def piotroski_f_score(
    actual: Annotated[
        dict,
        Field(
            description=(
                "Año actual: {utilidad_neta, activos_totales, flujo_caja_operacional, "
                "deuda_largo_plazo, activo_corriente, pasivo_corriente, utilidad_bruta, ventas, acciones_emitidas}"
            )
        ),
    ],
    anterior: Annotated[dict, Field(description="Año anterior: mismas llaves que 'actual'")],
) -> dict:
    """Piotroski F-Score (0-9) de calidad/fortaleza financiera comparando dos ejercicios."""
    requeridas = [
        "utilidad_neta", "activos_totales", "flujo_caja_operacional", "deuda_largo_plazo",
        "activo_corriente", "pasivo_corriente", "utilidad_bruta", "ventas", "acciones_emitidas",
    ]
    for etiqueta, datos in (("actual", actual), ("anterior", anterior)):
        faltan = [k for k in requeridas if k not in datos]
        if faltan:
            raise ValueError(f"Faltan llaves en '{etiqueta}': {faltan}. Se requieren: {requeridas}")
    roa_a = safe_div(actual["utilidad_neta"], actual["activos_totales"]) or 0
    roa_p = safe_div(anterior["utilidad_neta"], anterior["activos_totales"]) or 0
    liq_a = safe_div(actual["activo_corriente"], actual["pasivo_corriente"]) or 0
    liq_p = safe_div(anterior["activo_corriente"], anterior["pasivo_corriente"]) or 0
    mb_a = safe_div(actual["utilidad_bruta"], actual["ventas"]) or 0
    mb_p = safe_div(anterior["utilidad_bruta"], anterior["ventas"]) or 0
    rot_a = safe_div(actual["ventas"], actual["activos_totales"]) or 0
    rot_p = safe_div(anterior["ventas"], anterior["activos_totales"]) or 0
    apal_a = safe_div(actual["deuda_largo_plazo"], actual["activos_totales"]) or 0
    apal_p = safe_div(anterior["deuda_largo_plazo"], anterior["activos_totales"]) or 0
    senales = {
        "1_roa_positivo": roa_a > 0,
        "2_fco_positivo": actual["flujo_caja_operacional"] > 0,
        "3_roa_mejora": roa_a > roa_p,
        "4_fco_mayor_que_utilidad": actual["flujo_caja_operacional"] > actual["utilidad_neta"],
        "5_apalancamiento_baja": apal_a < apal_p,
        "6_liquidez_mejora": liq_a > liq_p,
        "7_sin_dilucion": actual["acciones_emitidas"] <= anterior["acciones_emitidas"],
        "8_margen_bruto_mejora": mb_a > mb_p,
        "9_rotacion_mejora": rot_a > rot_p,
    }
    score = sum(senales.values())
    return {
        "f_score": score,
        "senales": senales,
        "interpretacion": "fuerte (7-9)" if score >= 7 else "media (4-6)" if score >= 4 else "débil (0-3)",
    }


@mcp.tool(annotations=READ_ONLY)
def working_capital(
    cxc: Annotated[float, Field(description="Cuentas por cobrar")],
    inventario: Annotated[float, Field(description="Inventario")],
    cxp: Annotated[float, Field(description="Cuentas por pagar")],
    activo_corriente: Annotated[float, Field(description="Activo corriente total (0 = usar solo componentes operativos)")] = 0,
    pasivo_corriente: Annotated[float, Field(description="Pasivo corriente total (0 = usar solo componentes operativos)")] = 0,
    ventas_anuales: Annotated[float, Field(description="Ventas anuales para expresar la necesidad como % (0 = omitir)")] = 0,
) -> dict:
    """Capital de trabajo contable y necesidad operativa de fondos (NOF = CxC + inventario - CxP)."""
    nof = cxc + inventario - cxp
    resultado = {
        "nof_necesidad_operativa": round(nof, 2),
        "componentes": {"cxc": cxc, "inventario": inventario, "cxp": cxp},
    }
    if activo_corriente or pasivo_corriente:
        resultado["capital_trabajo_contable"] = round(activo_corriente - pasivo_corriente, 2)
    if ventas_anuales:
        resultado["nof_sobre_ventas_pct"] = pct(nof / ventas_anuales)
        resultado["interpretacion"] = (
            "Cada punto de NOF/ventas es caja inmovilizada en el ciclo: "
            "reducir DSO/DIO o subir DPO libera caja sin tocar el negocio."
        )
    return resultado
