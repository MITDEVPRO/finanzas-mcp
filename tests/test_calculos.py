"""Tests de la matemática financiera de las tools (se prueban las funciones registradas)."""

import pytest

from finanzas_mcp import tools_operaciones as ops
from finanzas_mcp import tools_ratios as ratios
from finanzas_mcp import tools_tributario as trib
from finanzas_mcp import tools_valoracion as val


# Las @mcp.tool exponen la función original en .fn
def fn(tool):
    return tool.fn if hasattr(tool, "fn") else tool


def test_ratios_liquidez():
    r = fn(ratios.ratios_liquidez)(activo_corriente=300, pasivo_corriente=100, inventario=50, efectivo=20)
    assert r["razon_corriente"] == 3.0
    assert r["razon_acida"] == 2.5
    assert r["capital_trabajo"] == 200


def test_liquidez_division_cero():
    r = fn(ratios.ratios_liquidez)(activo_corriente=300, pasivo_corriente=0)
    assert r["razon_corriente"] is None


def test_dupont_cierra_con_roe():
    r = fn(ratios.dupont)(ventas=1000, utilidad_neta=80, activos_totales=500, patrimonio=250)
    # ROE directo = 80/250 = 32%
    assert r["roe_pct"] == pytest.approx(32.0, abs=0.01)


def test_altman_publica_valores_conocidos():
    # Empresa con todos los X = 1 -> Z = 1.2+1.4+3.3+0.6+1.0 = 7.5
    r = fn(ratios.altman_z_score)(
        activos_totales=100, pasivos_totales=100, capital_trabajo=100,
        utilidades_retenidas=100, ebit=100, patrimonio=100, ventas=100, modelo="publica",
    )
    assert r["z_score"] == 7.5
    assert "SEGURA" in r["zona"]


def test_piotroski_maximo():
    base = dict(utilidad_neta=100, activos_totales=1000, flujo_caja_operacional=150,
                deuda_largo_plazo=200, activo_corriente=400, pasivo_corriente=200,
                utilidad_bruta=300, ventas=1000, acciones_emitidas=100)
    anterior = dict(base, utilidad_neta=50, flujo_caja_operacional=40, deuda_largo_plazo=300,
                    activo_corriente=300, utilidad_bruta=200, ventas=900)
    r = fn(ratios.piotroski_f_score)(actual=base, anterior=anterior)
    assert r["f_score"] == 9


def test_piotroski_llaves_faltantes():
    with pytest.raises(ValueError, match="Faltan llaves"):
        fn(ratios.piotroski_f_score)(actual={"ventas": 1}, anterior={"ventas": 1})


def test_wacc_clasico():
    # 60% equity al 12%, 40% deuda al 6% con t=25% -> 7.2% + 1.8% = 9.0%
    r = fn(val.wacc)(valor_equity=600, valor_deuda=400, costo_equity=0.12, costo_deuda=0.06, tasa_impuesto=0.25)
    assert r["wacc_pct"] == pytest.approx(9.0, abs=0.01)


def test_dcf_perpetuidad_simple():
    # FCF 100 constante, wacc 10%, g 0 -> EV = 100/1.1 + (100/0.1)/1.1 = 90.909 + 909.09 = 1000
    r = fn(val.dcf)(flujos_caja_libre=[100], tasa_descuento=0.10, crecimiento_perpetuo=0.0, sensibilidad=False)
    assert r["enterprise_value"] == pytest.approx(1000.0, abs=0.1)


def test_dcf_g_mayor_que_wacc():
    with pytest.raises(ValueError, match="diverge"):
        fn(val.dcf)(flujos_caja_libre=[100], tasa_descuento=0.05, crecimiento_perpetuo=0.08)


def test_van_tir():
    # -1000 + 500/(1+r) + 600/(1+r)^2 = 0 -> TIR ~ 6.394% ; VAN al 5%
    r = fn(val.van_tir)(inversion_inicial=1000, flujos=[500, 600], tasa_descuento=0.05)
    assert r["van"] == pytest.approx(-1000 + 500 / 1.05 + 600 / 1.05**2, abs=0.01)
    assert r["tir_pct"] == pytest.approx(6.39, abs=0.05)
    assert "ACEPTAR" in r["decision"]


def test_punto_equilibrio():
    r = fn(ops.punto_equilibrio)(costos_fijos=10000, precio_unitario=50, costo_variable_unitario=30)
    assert r["punto_equilibrio_unidades"] == 500.0
    assert r["punto_equilibrio_monto"] == 25000.0


def test_punto_equilibrio_margen_negativo():
    with pytest.raises(ValueError, match="punto de equilibrio"):
        fn(ops.punto_equilibrio)(costos_fijos=1000, precio_unitario=10, costo_variable_unitario=15)


def test_aging():
    docs = [
        {"monto": 100, "dias_vencido": -5, "cliente": "A"},
        {"monto": 200, "dias_vencido": 15, "cliente": "A"},
        {"monto": 300, "dias_vencido": 200, "cliente": "B"},
    ]
    r = fn(ops.aging_cartera)(documentos=docs)
    assert r["total_cartera"] == 600
    assert r["tramos"]["por_vencer"] == 100
    assert r["tramos"]["1_30"] == 200
    assert r["tramos"]["mas_180"] == 300
    assert r["pct_vencido"] == pytest.approx(83.33, abs=0.01)


def test_amortizacion_francesa_cuota_fija():
    r = fn(ops.amortizacion_credito)(principal=100000, tasa_periodo=0.01, num_cuotas=12, sistema="frances")
    assert r["cuota_inicial"] == r["cuota_final"]  # cuota fija
    assert r["tabla"][-1]["saldo"] == pytest.approx(0, abs=0.01)


def test_depreciacion_acelerada_chile():
    r = fn(ops.depreciacion)(valor_activo=9000, vida_util_anios=9, metodo="acelerada")
    assert len(r["tabla"]) == 3  # 9 // 3
    assert r["tabla"][0]["cuota"] == 3000.0


def test_iva_agregar_extraer_consistentes():
    bruto = fn(trib.iva)(monto=100000, operacion="agregar")["bruto"]
    neto = fn(trib.iva)(monto=bruto, operacion="extraer")["neto"]
    assert neto == pytest.approx(100000, abs=0.01)


def test_impuesto_14a_con_ppm():
    r = fn(trib.impuesto_empresa)(base_imponible=100_000_000, regimen="14A", ppm_pagados=20_000_000)
    assert r["impuesto_determinado"] == 27_000_000
    assert r["saldo"] == 7_000_000


def test_correccion_monetaria_uf():
    r = fn(trib.correccion_monetaria)(monto=1000, indice_inicial=36000, indice_final=37800)
    assert r["factor_correccion"] == pytest.approx(1.05, abs=1e-6)
    assert r["monto_corregido"] == 1050.0


def test_flujo_indirecto():
    r = fn(ops.flujo_caja_indirecto)(
        utilidad_neta=100, depreciacion_amortizacion=20, delta_cxc=30, delta_inventario=10, delta_cxp=15, capex=40,
    )
    assert r["flujo_operacional_fco"] == 95   # 100+20-30-10+15
    assert r["flujo_caja_libre_fcf"] == 55


def test_servidor_registra_todas_las_tools():
    import asyncio

    from finanzas_mcp import server  # noqa: F401  (importa y registra todo)
    from finanzas_mcp.app import mcp

    tools = asyncio.run(mcp.list_tools())
    assert len(tools) == 25
    assert all(t.annotations.readOnlyHint for t in tools)


# --- Cobertura de las tools que faltaban ---

def test_ratios_rentabilidad():
    r = fn(ratios.ratios_rentabilidad)(
        ventas=1000, utilidad_bruta=400, utilidad_operacional=200, utilidad_neta=100,
        activos_totales=2000, patrimonio=800,
    )
    assert r["margen_bruto_pct"] == 40.0
    assert r["margen_operacional_pct"] == 20.0
    assert r["margen_neto_pct"] == 10.0
    assert r["roa_pct"] == 5.0
    assert r["roe_pct"] == 12.5


def test_ratios_eficiencia_ccc():
    r = fn(ratios.ratios_eficiencia)(
        ventas=3650, costo_ventas=1825, inventario_promedio=500, cxc_promedio=300,
        cxp_promedio=250, dias_periodo=365,
    )
    assert r["dio_dias_inventario"] == 100.0
    assert r["dso_dias_cobro"] == 30.0
    assert r["dpo_dias_pago"] == 50.0
    assert r["ccc_ciclo_conversion_caja"] == 80.0   # DIO + DSO - DPO


def test_ratios_endeudamiento():
    r = fn(ratios.ratios_endeudamiento)(
        pasivos_totales=1200, patrimonio=800, activos_totales=2000,
        ebitda=300, deuda_financiera=900, gastos_financieros=60, ebit=240,
    )
    assert r["leverage_pasivos_sobre_patrimonio"] == 1.5
    assert r["endeudamiento_sobre_activos_pct"] == 60.0
    assert r["deuda_financiera_sobre_ebitda"] == 3.0
    assert r["cobertura_intereses_veces"] == 4.0


def test_endeudamiento_sin_ebit_no_reporta_cobertura_cero():
    r = fn(ratios.ratios_endeudamiento)(
        pasivos_totales=1200, patrimonio=800, activos_totales=2000, gastos_financieros=60,
    )
    assert r["cobertura_intereses_veces"] is None   # sin EBIT no hay cobertura, no "0.0x"


def test_working_capital_nof():
    r = fn(ratios.working_capital)(cxc=300, inventario=500, cxp=250, ventas_anuales=3650)
    assert r["nof_necesidad_operativa"] == 550
    assert r["nof_sobre_ventas_pct"] == 15.07


def test_capm_directo():
    r = fn(val.capm_costo_equity)(
        tasa_libre_riesgo=0.045, beta=1.2, premio_riesgo_mercado=0.05, riesgo_pais=0.01,
    )
    assert r["ke_costo_equity_pct"] == 11.5   # 4.5 + 1.2×5 + 1


def test_valoracion_multiplos_ev_ebitda():
    r = fn(val.valoracion_multiplos)(ebitda=100, multiplo_ev_ebitda=8)
    assert r["valor_equity_por_metodo"]["por_ev_ebitda"] == 800
    assert r["rango"] == {"min": 800, "max": 800}


def test_variacion_simple_y_cagr():
    r = fn(ops.variacion)(valor_actual=150, valor_anterior=100)
    assert r["variacion_absoluta"] == 50
    assert r["variacion_pct"] == 50.0
    r5 = fn(ops.variacion)(valor_actual=200, valor_anterior=100, periodos=5)
    assert r5["cagr_pct"] == 14.87   # 2^(1/5) - 1


def test_interes_compuesto_vf():
    r = fn(ops.interes_compuesto)(capital=1000, tasa_periodo=0.05, periodos=10)
    assert r["valor_futuro"] == 1628.89
    assert r["interes_ganado"] == 628.89


def test_escudo_fiscal():
    r = fn(trib.escudo_fiscal)(gasto_deducible=1000, tasa_impuesto=0.27)
    assert r["ahorro_impuesto"] == 270.0
    assert r["costo_neto_del_gasto"] == 730.0


def test_ppm():
    r = fn(trib.ppm_calculo)(ingresos_brutos_mes=10000, tasa_ppm=0.005)
    assert r["ppm_del_mes"] == 50.0
