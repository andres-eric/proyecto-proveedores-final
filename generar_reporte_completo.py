import os
import sys
from pathlib import Path
import warnings
import logging
warnings.filterwarnings("ignore")
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("matplotlib").setLevel(logging.WARNING)

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


from datos.carga_datos import obtener_datos_completos, obtener_datos_kpi_detalle, obtener_datos_inspeccion_categoria
from etl.datos_analisis_resumen_general import datos_historicos

import importlib.util


ruta_agent = ROOT_DIR / "langchain" / "Analisis_Continuidad_Negocio_1" / "resumen_agent.py"
spec = importlib.util.spec_from_file_location("resumen_agent", ruta_agent)
resumen_agent = importlib.util.module_from_spec(spec)
sys.modules["resumen_agent"] = resumen_agent
spec.loader.exec_module(resumen_agent)
analisis_1 = resumen_agent.analisis_1

ruta_agent_2 = ROOT_DIR / "langchain" / "Analisis_evaluacion_Riesgo_2" / "Analisis_2.py"
spec_2 = importlib.util.spec_from_file_location("analisis_2_agent", ruta_agent_2)
analisis_2_agent = importlib.util.module_from_spec(spec_2)
sys.modules["analisis_2_agent"] = analisis_2_agent
spec_2.loader.exec_module(analisis_2_agent)
analisis_2 = analisis_2_agent.analisis_2


from graficos.graficas_resumen import generar_imagen_tarjetas_kpi_desde_df, graficar_distribucion_volumen_mes
from graficos.graficas_modulo2 import graficar_modulo_2


from pdf_generator.pdf_generator import generar_pdf_reporte

def ejecutar_pipeline():
    print("Iniciando pipeline de generación de reporte...")


    print("\n[1/4] Obteniendo datos y calculando métricas históricas...")
    df_base = obtener_datos_completos()
    df_historico = datos_historicos(df_base)
    ultimo_mes = df_historico.iloc[0:1]


    print("\n[2/4] Generando gráficas (Tarjetas KPI y Volumen Mensual)...")
    ruta_kpis = str(ROOT_DIR / "tarjetas_ejecutivas.png")
    ruta_barras = str(ROOT_DIR / "volumen_total_mes.png")
    
    generar_imagen_tarjetas_kpi_desde_df(df_historico, ruta_salida=ruta_kpis)
    graficar_distribucion_volumen_mes(df_historico, ruta_salida=ruta_barras)
    
    print(f"  -> Gráficas creadas en la raíz del proyecto.")

    ruta_m2_tornado = str(ROOT_DIR / "modulo2_tornado.png")
    graficar_modulo_2(ruta_m2_tornado)


    print("\n[3/4] Ejecutando agentes LangChain (Generación de texto analítico)...")
    texto_agente = analisis_1(datos=ultimo_mes)
    texto_modulo_2 = analisis_2(obtener_datos_kpi_detalle(), obtener_datos_inspeccion_categoria())
    print("  -> Textos generados por el LLM exitosamente.")


    print("\n[4/4] Construyendo el documento PDF final...")
   
    ruta_pdfs = ROOT_DIR / "archivos_pdf"
    ruta_pdfs.mkdir(exist_ok=True)
    ruta_pdf_salida = str(ruta_pdfs / "Reporte_Operativo_Pipeline.pdf")

    act, ant = df_historico.iloc[0], df_historico.iloc[1]
    d_c = act['tasa_cumpli_perfecto'] - ant['tasa_cumpli_perfecto']
    d_r = act['tasa_riesgo_critico'] - ant['tasa_riesgo_critico']
    verde, rojo = '#16A34A', '#B91C1C'
    kpis = [
        {'titulo': 'Cumplimiento', 'valor': f"{act['tasa_cumpli_perfecto']:.1f}%",
         'delta': f"{d_c:+.2f} pp vs mes anterior",
         'color': verde if d_c >= 0 else rojo, 'acento': '#16A34A'},
        {'titulo': 'Riesgo crítico', 'valor': f"{act['tasa_riesgo_critico']:.1f}%",
         'delta': f"{d_r:+.2f} pp vs mes anterior",
         'color': verde if d_r <= 0 else rojo, 'acento': '#B91C1C'},
        {'titulo': 'Unidades defectuosas',
         'valor': f"{int(act['cantidad_recibida_defectuosa']):,}".replace(",", "."),
         'delta': 'Cantidad recibida defectuosa', 'color': '#6B7280', 'acento': '#EA580C'},
    ]
    periodo = str(act['anio-mes'])

    exito = generar_pdf_reporte(
        texto_agente=texto_agente,
        ruta_pdf_salida=ruta_pdf_salida,
        ruta_kpis=ruta_kpis,
        ruta_barras=ruta_barras,
        kpis=kpis,
        periodo=periodo,
        grafica_tornado=ruta_m2_tornado,
        texto_modulo_2=texto_modulo_2,
    )

    if exito:
        print(f"\n ¡PROCESO EXITOSO! El reporte final se encuentra en: {ruta_pdf_salida}")
    else:
        print("\n Error al generar el PDF.")

if __name__ == "__main__":
    ejecutar_pipeline()
