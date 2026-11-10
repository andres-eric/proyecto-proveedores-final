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


# Cargar el grafo padre de LangGraph (une continuidad + riesgo)
ruta_padre = ROOT_DIR / "langchain" / "langrahpgrap" / "Nodo_Padre" / "agente.py"
spec = importlib.util.spec_from_file_location("nodo_padre", ruta_padre)
nodo_padre = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nodo_padre)
grafo_padre = nodo_padre.grafo


from graficos.graficas_resumen import generar_imagen_tarjetas_kpi_desde_df, graficar_distribucion_volumen_mes
from graficos.graficas_modulo2 import graficar_modulo_2
from graficos.graficas_analisis_cantidad import graficar_analisis_cantidad


from pdf_generator.pdf_generator import generar_pdf_reporte


def extraer_texto(estado, clave_final, clave_borrador):
    # Saca el texto final del resultado del grafo; si no existe, usa el borrador
    texto_final = estado.get(clave_final)
    if texto_final:
        return texto_final[0]
    return estado.get(clave_borrador, "")


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

    ruta_m3_cantidad = str(ROOT_DIR / "modulo3_cantidad.png")
    graficar_analisis_cantidad(ruta_m3_cantidad)


    print("\n[3/4] Ejecutando grafo LangGraph (Generación de texto analítico)...")
    estado_final = grafo_padre.invoke({})
    texto_agente = extraer_texto(estado_final, "texto_final_continuidad", "borrador_continuidad")
    texto_modulo_2 = extraer_texto(estado_final, "texto_final_riesgo", "borrador_riesgo")
    texto_modulo_3 = extraer_texto(estado_final, "texto_final_cantidad", "borrador_cantidad")
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
        grafica_cantidad=ruta_m3_cantidad,
        texto_modulo_3=texto_modulo_3,
    )

    if exito:
        print(f"\n ¡PROCESO EXITOSO! El reporte final se encuentra en: {ruta_pdf_salida}")
    else:
        print("\n Error al generar el PDF.")

if __name__ == "__main__":
    ejecutar_pipeline()
