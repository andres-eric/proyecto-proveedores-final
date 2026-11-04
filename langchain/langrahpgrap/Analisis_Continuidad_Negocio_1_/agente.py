import os
import sys
import pandas as pd
from typing import TypedDict

from pathlib import Path

# Asegurar que la raíz del proyecto, el directorio actual y el directorio de prompts están en sys.path
ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

PROMPT_DIR = ROOT_DIR / "langchain" / "langrahpgrap" / "Analisis_Continuidad_Negocio_1"
if str(PROMPT_DIR) not in sys.path:
    sys.path.insert(0, str(PROMPT_DIR))

from dotenv import find_dotenv, load_dotenv
load_dotenv(ROOT_DIR / ".env")

from typing import List, Literal, TypedDict
from pydantic import BaseModel, Field
from langchain_core.documents import Document
from langchain_ollama import ChatOllama
from langchain_cohere import CohereEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.exceptions import OutputParserException
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from ollama._types import ResponseError
from modelo_config.utiils_config_llm import obtener_llm
from langgraph.graph import StateGraph, START, END


from datos.carga_datos import (
    obtener_datos_completos,
    obtener_datos_kpi_detalle,
    obtener_datos_inspeccion_categoria,
)
from etl.datos_analisis_resumen_general import datos_historicos
from etl.datos_detalles import datos_modulo_2
from etl.datos_detalles import convertir_df_a_contexto_llm
from promt_template_continuidad  import template_resumen, prompt_revision, prompt_corregir


class EstadoModelo_resumen_1(TypedDict, total=False):
    mes_evaluado: str
    total_volumen: str
    variacion_volumen: str
    cumplimiento_optimo: str
    var_optimo: str
    tasa_riesgo: str

    # variables de control

    texto_final_continuidad: list
    tiene_errores_continuidad: bool
    notas_auditor_continuidad: list[str]
    borrador_continuidad: str


llm = obtener_llm()


def nodo_carga_datos(state: EstadoModelo_resumen_1) -> dict:
    print("---obteniendo datos...")

    datos = datos_historicos(obtener_datos_completos())
    ultimo_mes_analisis=datos[0:1]

    # str(): el estado se serializa a JSON en langgraph dev y los tipos de numpy no
    return {
        "mes_evaluado": str(ultimo_mes_analisis['anio-mes'].values[0]),
        "var_optimo": str(ultimo_mes_analisis['var_optimo'].values[0]),
        "tasa_riesgo": format(ultimo_mes_analisis['tasa_riesgo_critico'].values[0], '.2f'),
        "total_volumen": str(ultimo_mes_analisis['total'].values[0]),
        "variacion_volumen": str(ultimo_mes_analisis['variacion_mes'].values[0]),
        "cumplimiento_optimo": str(ultimo_mes_analisis['Cumplimiento_optimo'].values[0]),
    }


def nodo_analisis(state: EstadoModelo_resumen_1) -> dict:
    print("---analizando datos...")

    mes_evaluado = state.get("mes_evaluado")
    total_volumen = state.get("total_volumen")
    variacion_volumen = state.get("variacion_volumen")
    cumplimiento_optimo = state.get("cumplimiento_optimo")
    var_optimo = state.get("var_optimo")
    tasa_riesgo = state.get("tasa_riesgo")



    prompt_template = PromptTemplate(
        input_variables=["mes_evaluado", "total_volumen", "variacion_volumen", "cumplimiento_optimo", "var_optimo", "tasa_riesgo"],
        template=template_resumen
    )

    cadena = prompt_template | llm | StrOutputParser()
    resultado = cadena.invoke({
        "mes_evaluado": mes_evaluado,
        "total_volumen": total_volumen,
        "variacion_volumen": variacion_volumen,
        "cumplimiento_optimo": cumplimiento_optimo,
        "var_optimo": var_optimo,
        "tasa_riesgo": tasa_riesgo
    })
    
    return {
        "borrador_continuidad": resultado,
        "mes_evaluado": mes_evaluado,
        "total_volumen": total_volumen,
        "variacion_volumen": variacion_volumen,
        "cumplimiento_optimo": cumplimiento_optimo,
        "var_optimo": var_optimo,
        "tasa_riesgo": tasa_riesgo, 
    }




def nodo_revisar_resumen_1 (state: EstadoModelo_resumen_1)-> dict:

    print("---revisando borrador...")

    promt_template_rev_resumen_1=PromptTemplate(input_variables=["texto"],template=prompt_revision)
    cadena=promt_template_rev_resumen_1 | llm | StrOutputParser()
    resultado=cadena.invoke({"texto":state["borrador_continuidad"]})
    if "PERFECTO" in resultado:
        return {"texto_final_continuidad": [state["borrador_continuidad"]], "tiene_errores_continuidad": False, "notas_auditor_continuidad": ""}
    else:
        return {"tiene_errores_continuidad": True, "notas_auditor_continuidad": resultado}

    


def nodo_correccion_resumen_1(state: EstadoModelo_resumen_1) -> dict:
    print("---corrigiendo texto...")
    PromptTemplate_corr=PromptTemplate(input_variables=["errores","texto_original"],template=prompt_corregir)
    cadena=PromptTemplate_corr | llm | StrOutputParser()

    nuevo_texto=cadena.invoke({"errores":state["notas_auditor_continuidad"],"texto_original":state["borrador_continuidad"]})
    return {"texto_final_continuidad": [nuevo_texto], "tiene_errores_continuidad": False, "notas_auditor_continuidad": ""}


# ==============================================================================
# COMPILACIÓN DEL GRAFO (Nivel de módulo para LangGraph CLI / Studio)
# ==============================================================================
builder = StateGraph(EstadoModelo_resumen_1)


builder.add_node("nodo_carga_datos", nodo_carga_datos)
builder.add_node("nodo_analisis", nodo_analisis)
builder.add_node("nodo_revisar_resumen_1", nodo_revisar_resumen_1)
builder.add_node("nodo_correccion_resumen_1", nodo_correccion_resumen_1)


def nodo_decision_1(state: EstadoModelo_resumen_1) -> Literal["nodo_correccion_resumen_1", END]:
    if state["tiene_errores_continuidad"]:
        return "nodo_correccion_resumen_1"
    else:
        return END  


builder.add_edge(START, "nodo_carga_datos")
builder.add_edge("nodo_carga_datos", "nodo_analisis")
builder.add_edge("nodo_analisis", "nodo_revisar_resumen_1")
builder.add_conditional_edges("nodo_revisar_resumen_1", nodo_decision_1)
builder.add_edge("nodo_correccion_resumen_1", END)

grafo = builder.compile()


def ejecutar_reporte() -> EstadoModelo_resumen_1:
    print("---obteniendo datos de las apis...")


    return grafo.invoke({})


    
    
    
   
if __name__ == "__main__":
    print("ejecutando el agente...")
    estado_final = ejecutar_reporte()

    texto_final_continuidad = estado_final["texto_final_continuidad"][-1] if estado_final.get("texto_final_continuidad") else estado_final.get("borrador_continuidad", "")

    # Imprimir el texto final
    print("\n" + "="*80)
    print("TEXTO FINAL DEL ANÁLISIS:")
    print("="*80)
    print(texto_final_continuidad)
    print("="*80)




## langgraph dev
