import os
import sys
from pathlib import Path
import warnings
import logging
warnings.filterwarnings("ignore")
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("matplotlib").setLevel(logging.WARNING)

ROOT_DIR = Path(__file__).resolve().parent.parent  # raíz del proyecto (este script vive en ejecutar_reporte/)
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
from graficos.graficas_modulo3 import graficar_modulo_3_desde_datos
from graficos.rutas_graficas import ruta_grafica
from graficos.graficas_modulo4 import graficar_primera_entrega, RUTA_EVOLUCION as RUTA_M4_EVOLUCION


from pdf_generator.pdf_generator import (generar_pdf_reporte, construir_kpis_cantidad, construir_kpis_resumen,
                                         texto_rango_meses)


def extraer_texto(estado, clave_final, clave_borrador):
    # Saca el texto final del resultado del grafo; si no existe, usa el borrador
    texto_final = estado.get(clave_final)
    if texto_final:
        return texto_final[-1]
    return estado.get(clave_borrador, "")


def ejecutar_pipeline():
    print("Iniciando pipeline de generación de reporte...")


    print("\n[1/4] Obteniendo datos y calculando métricas históricas...")
    df_base = obtener_datos_completos()
    df_historico = datos_historicos(df_base)
    ultimo_mes = df_historico.iloc[0:1]


    print("\n[2/4] Generando gráficas (Tarjetas KPI y Volumen Mensual)...")
    ruta_kpis = ruta_grafica("tarjetas_ejecutivas.png")
    ruta_barras = ruta_grafica("volumen_total_mes.png")
    
    generar_imagen_tarjetas_kpi_desde_df(df_historico, ruta_salida=ruta_kpis)
    graficar_distribucion_volumen_mes(df_historico, ruta_salida=ruta_barras)
    
    print(f"  -> Gráficas creadas en la carpeta archivos_graficas/.")

    ruta_m2_tornado = ruta_grafica("modulo2_tornado.png")
    graficar_modulo_2(ruta_m2_tornado)

    ruta_m3_cantidad = ruta_grafica("modulo3_cantidad.png")
    graficar_analisis_cantidad(ruta_m3_cantidad)

    ruta_m3_proveedores = ruta_grafica("modulo3_proveedores.png")
    graficar_modulo_3_desde_datos(ruta_m3_proveedores)

    graficar_primera_entrega(RUTA_M4_EVOLUCION)


    print("\n[3/4] Ejecutando grafo LangGraph (Generación de texto analítico)...")
    estado_final = grafo_padre.invoke({})
    texto_agente = extraer_texto(estado_final, "texto_final_continuidad", "borrador_continuidad")
    texto_modulo_2 = extraer_texto(estado_final, "texto_final_riesgo", "borrador_riesgo")
    texto_modulo_3 = extraer_texto(estado_final, "texto_final_cantidad", "borrador_cantidad")
    texto_proveedores_cantidad = extraer_texto(estado_final, "texto_final_analisis_3_detalle", "texto_analisis_3")
    texto_primera_entrega = extraer_texto(estado_final, "texto_final_analisis_primera_entrega", "texto_analisis_primera_entrega")
    texto_proveedores_primera = extraer_texto(estado_final, "texto_final_proveedores_primera", "texto_proveedores_primera")
    kpis_cantidad = construir_kpis_cantidad(estado_final)
    print("  -> Textos generados por el LLM exitosamente.")


    print("\n[4/4] Construyendo el documento PDF final...")
   
    ruta_pdfs = ROOT_DIR / "archivos_pdf"
    ruta_pdfs.mkdir(exist_ok=True)
    ruta_pdf_salida = str(ruta_pdfs / "Reporte_Operativo_Pipeline.pdf")

    kpis = construir_kpis_resumen(df_historico)
    periodo = str(df_historico.iloc[0]['anio-mes'])
    rango_periodo = texto_rango_meses(df_historico['anio-mes'])

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
        kpis_cantidad=kpis_cantidad,
        grafica_proveedores_cantidad=ruta_m3_proveedores,
        texto_proveedores_cantidad=texto_proveedores_cantidad,
        grafica_primera_evolucion=RUTA_M4_EVOLUCION,
        texto_primera_entrega=texto_primera_entrega,
        texto_proveedores_primera_entrega=texto_proveedores_primera,
        rango_periodo=rango_periodo,
    )

    if exito:
        print(f"\n ¡PROCESO EXITOSO! El reporte final se encuentra en: {ruta_pdf_salida}")
    else:
        print("\n Error al generar el PDF.")

if __name__ == "__main__":
    ejecutar_pipeline()
