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
from langchain_core.prompts import PromptTemplate
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
from promt_template_riesgo  import template_resumen, prompt_revision, prompt_corregir


class EstadoModelo(TypedDict, total=False):
    datos_logistica: str
    datos_calidad: str
    borrador_riesgo: str
    texto_final_riesgo: list
    tiene_errores_riesgo: bool
    notas_auditor_riesgo: str


llm = obtener_llm()



def nodo_carga_datos(state: EstadoModelo) -> dict:
    print("---obteniendo datos...")
    datos_calidad, datos_logistica = datos_modulo_2(obtener_datos_kpi_detalle(), obtener_datos_inspeccion_categoria())

    datos_logistica = convertir_df_a_contexto_llm(datos_logistica)
    datos_calidad = convertir_df_a_contexto_llm(datos_calidad)
    
    return {
        "datos_logistica": str(datos_logistica),
        "datos_calidad": str(datos_calidad),
    }


def nodo_analisis(state: EstadoModelo) -> dict:
    print("---analizando datos...")

    datos_logistica = state.get("datos_logistica")
    datos_calidad = state.get("datos_calidad")
    # Si Studio le envió un input vacío {}, se conecta directamente a las APIs
    if not datos_logistica or not datos_calidad:
        print("--- Obteniendo datos en vivo desde las APIs de Celsa...")
        datos_kpi = obtener_datos_kpi_detalle()
        datos_insp = obtener_datos_inspeccion_categoria()
        calidad_df, logistica_df = datos_modulo_2(datos_kpi, datos_insp)
        datos_logistica = convertir_df_a_contexto_llm(logistica_df)
        datos_calidad = convertir_df_a_contexto_llm(calidad_df)

    prompt_template = PromptTemplate(
        input_variables=["datos_logistica", "datos_calidad"],
        template=template_resumen
    )
    cadena = prompt_template | llm | StrOutputParser()
    resultado = cadena.invoke({
        "datos_logistica": datos_logistica,
        "datos_calidad": datos_calidad
    })
    return {
        "datos_logistica": datos_logistica,
        "datos_calidad": datos_calidad,
        "borrador_riesgo": resultado
    }




def nodo_revisar(state: EstadoModelo) -> dict:
    print("---revisando borrador...")

    prompt_template_rev = PromptTemplate(input_variables=["texto"], template=prompt_revision)
    cadena = prompt_template_rev | llm | StrOutputParser()
    resultado = cadena.invoke({"texto": state["borrador_riesgo"]})
    if 'PERFECTO' in resultado:
        return {"texto_final_riesgo": [state["borrador_riesgo"]], "tiene_errores_riesgo": False, "notas_auditor_riesgo": ""}
    else:
        return {"tiene_errores_riesgo": True, "notas_auditor_riesgo": resultado}




def nodo_correccion(state: EstadoModelo) -> dict:
    print("---corrigiendo texto...")
    prompt_template_corr = PromptTemplate(
        input_variables=["errores", "texto_original"],
        template=prompt_corregir
    )
    cadena = prompt_template_corr | llm | StrOutputParser()
    nuevo_texto = cadena.invoke({
        "errores": state["notas_auditor_riesgo"],
        "texto_original": state["borrador_riesgo"]
    })

    return {"texto_final_riesgo": [nuevo_texto], "tiene_errores_riesgo": False, "notas_auditor_riesgo": ""}


# ==============================================================================
# COMPILACIÓN DEL GRAFO (Nivel de módulo para LangGraph CLI / Studio)
# ==============================================================================
builder = StateGraph(EstadoModelo)

builder.add_node("nodo_carga_datos", nodo_carga_datos)
builder.add_node("nodo_analisis", nodo_analisis)
builder.add_node("nodo_revisar", nodo_revisar)
builder.add_node("nodo_correccion", nodo_correccion)


def nodo_decision(state: EstadoModelo) -> Literal["nodo_correccion", END]:
    if state.get("tiene_errores_riesgo"):
        return "nodo_correccion"
    else:
        return END


builder.add_edge(START, "nodo_carga_datos")
builder.add_edge("nodo_carga_datos", "nodo_analisis")
builder.add_edge("nodo_analisis", "nodo_revisar")
builder.add_conditional_edges("nodo_revisar", nodo_decision)
builder.add_edge("nodo_correccion", END)

grafo = builder.compile()




def ejecutar_reporte(datos=None, datos_completos_inspeccion=None) -> EstadoModelo:
    print("---obteniendo datos de las apis...")
    return grafo.invoke({})


    
    
    
   
if __name__ == "__main__":
    print("ejecutando el agente....")

    estado_final = ejecutar_reporte()
    

    texto_final_riesgo = estado_final["texto_final_riesgo"][-1] if estado_final.get("texto_final_riesgo") else estado_final.get("borrador_riesgo", "")

    # Imprimir el texto final
    print("\n" + "="*80)
    print("TEXTO FINAL DEL ANÁLISIS:")
    print("="*80)
    print(texto_final_riesgo)
    print("="*80)

    




## langgraph dev
