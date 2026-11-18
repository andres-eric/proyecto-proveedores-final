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
    
    obtener_data_set_primera_entrega

)
from etl.datos_analisis_primera_entrega import datos_historicos, ejecutar_resumen


from promt_template_entrega import template_resumen_primera,prompt_corregir_primera,prompt_revision_primera


class EstadoModelo_resumen_primera_entrega(TypedDict, total=False):

   

    mes_evaluado: str
    mes_nombre: str
    total_primera: str
    cumple_primera: str
    no_cumple_primera: str
    porcentaje_primera: str
    variacion_pp_primera: str
    promedio_periodo_primera: str
    posicion_promedio: str
    mes_nombre_inicio: str
    meses_consecutivos: str

    texto_analisis_primera_entrega: str
    texto_final_analisis_primera_entrega: list
    tiene_errores_analisis_primera_entrega: bool
    notas_auditor_analisis_primera_entrega: str

llm = obtener_llm()


def estado_cargas_datos(state: EstadoModelo_resumen_primera_entrega) -> dict:
    print('cargando datos')

    datos_cantidad_entrega=ejecutar_resumen()
    

    return  {
        "mes_evaluado": datos_cantidad_entrega["mes_evaluado"],
        "mes_nombre": datos_cantidad_entrega["mes_nombre"],
        "total_primera": datos_cantidad_entrega["total_primera"],
        "cumple_primera": datos_cantidad_entrega["cumple_primera"],
        "no_cumple_primera": datos_cantidad_entrega["no_cumple_primera"],
        "porcentaje_primera": datos_cantidad_entrega["porcentaje_primera"],
        "variacion_pp_primera": datos_cantidad_entrega["variacion_pp_primera"],
        "promedio_periodo_primera": datos_cantidad_entrega["promedio_periodo_primera"],
        "posicion_promedio": datos_cantidad_entrega["posicion_promedio"],
        "mes_nombre_inicio": datos_cantidad_entrega["mes_nombre_inicio"],
        "meses_consecutivos": datos_cantidad_entrega["meses_consecutivos"],
    }



def redactar_analisis_primera_entrega(state: EstadoModelo_resumen_primera_entrega) -> dict:
    print('redactando analisis cantidad 3')

    mes_evaluado = state.get("mes_evaluado")
    mes_nombre = state.get("mes_nombre")
    total_primera = state.get("total_primera")
    cumple_primera = state.get("cumple_primera")
    no_cumple_primera = state.get("no_cumple_primera")
    porcentaje_primera = state.get("porcentaje_primera")
    variacion_pp_primera = state.get("variacion_pp_primera")
    promedio_periodo_primera = state.get("promedio_periodo_primera")
    posicion_promedio = state.get("posicion_promedio")
    mes_nombre_inicio = state.get("mes_nombre_inicio")
    meses_consecutivos = state.get("meses_consecutivos")


    promt= PromptTemplate(
        input_variables=[
            "mes_evaluado",
            "mes_nombre",
            "total_primera",
            "cumple_primera",
            "no_cumple_primera",
            "porcentaje_primera",
            "variacion_pp_primera",
            "promedio_periodo_primera",
            "posicion_promedio",
            "mes_nombre_inicio",
            "meses_consecutivos"
        ],
        template=template_resumen_primera
    )

    cadena = promt | llm | StrOutputParser()

    resultado = cadena.invoke({
        "mes_evaluado": mes_evaluado,
        "mes_nombre": mes_nombre,
        "total_primera": total_primera,
        "cumple_primera": cumple_primera,
        "no_cumple_primera": no_cumple_primera,
        "porcentaje_primera": porcentaje_primera,
        "variacion_pp_primera": variacion_pp_primera,
        "promedio_periodo_primera": promedio_periodo_primera,
        "posicion_promedio": posicion_promedio,
        "mes_nombre_inicio": mes_nombre_inicio,
        "meses_consecutivos":meses_consecutivos
    })

    return {"texto_analisis_primera_entrega": resultado}




def nodo_revisar_analisis_primera_entrega(state:EstadoModelo_resumen_primera_entrega) -> dict:
    print('realizando revision errores analisis cantidad ')

    promt_template_revision_cantidad= PromptTemplate.from_template(prompt_revision_primera)

    cadena_revision= promt_template_revision_cantidad|llm|StrOutputParser()

    resultaldo_revision=cadena_revision.invoke({
    "texto": state.get("texto_analisis_primera_entrega"),
    "total_primera": state.get("total_primera"),
    "cumple_primera": state.get("cumple_primera"),
    "no_cumple_primera": state.get("no_cumple_primera"),
    "porcentaje_primera": state.get("porcentaje_primera"),
    "variacion_pp_primera": state.get("variacion_pp_primera"),
    "promedio_periodo_primera": state.get("promedio_periodo_primera"),
    "meses_consecutivos": state.get("meses_consecutivos")
    })

    if "PERFECTO" in resultaldo_revision:
        return {"texto_final_analisis_primera_entrega": [state["texto_analisis_primera_entrega"]], "tiene_errores_analisis_primera_entrega": False, "notas_auditor_analisis_primera_entrega": ""}
    
    else:
        return {"tiene_errores_analisis_primera_entrega": True, "notas_auditor_analisis_primera_entrega": resultaldo_revision}






def corregir_errores__analisis_primera_entrega(state:EstadoModelo_resumen_primera_entrega) -> dict:
    print('corrigiendo errores')

    promt_corregir_analisis_cantidad= PromptTemplate(
        input_variables=[
            "errores",
            "texto_original"
        ],
        template=prompt_corregir_primera
    )

    cadena_corregir=promt_corregir_analisis_cantidad|llm|StrOutputParser()


    nuevo_texto_analisis_entrega=cadena_corregir.invoke({
    "texto_original": state.get("texto_analisis_primera_entrega"),
    "errores": state.get("notas_auditor_analisis_primera_entrega")
    })

    return {"texto_final_analisis_primera_entrega": [nuevo_texto_analisis_entrega], "tiene_errores_analisis_primera_entrega": False, "notas_auditor_analisis_primera_entrega": ""} 

# ==============================================================================
# COMPILACIÓN DEL GRAFO
# ==============================================================================
builder = StateGraph(EstadoModelo_resumen_primera_entrega)

builder.add_node("estado_cargas_datos", estado_cargas_datos)
builder.add_node("redactar_analisis_primera_entrega", redactar_analisis_primera_entrega)
builder.add_node("nodo_revisar_analisis_primera_entrega", nodo_revisar_analisis_primera_entrega)
builder.add_node("corregir_errores__analisis_primera_entrega", corregir_errores__analisis_primera_entrega)


def nodo_desicion_analisis_primera_entrega(state:EstadoModelo_resumen_primera_entrega) -> str:
    """decide si corregir o no"""
    if state["tiene_errores_analisis_primera_entrega"]:
        return "corregir_errores__analisis_primera_entrega"
    else:
        return END

builder.add_edge(START, "estado_cargas_datos")
builder.add_edge("estado_cargas_datos", "redactar_analisis_primera_entrega")
builder.add_edge("redactar_analisis_primera_entrega", "nodo_revisar_analisis_primera_entrega")
builder.add_conditional_edges("nodo_revisar_analisis_primera_entrega", nodo_desicion_analisis_primera_entrega)
builder.add_edge("corregir_errores__analisis_primera_entrega", END)


grafo = builder.compile()


def ejecutar_reporte() -> EstadoModelo_resumen_primera_entrega:
    return grafo.invoke({})




if __name__ == "__main__":
    print("ejecutando el agente...")
    estado_final = ejecutar_reporte()

    print("\n" + "="*100)
    print("ANÁLISIS 4 PRIMERA ENTREGA:")
    print("="*100)
    finales = estado_final.get("texto_final_analisis_primera_entrega")
    print(finales[-1] if finales else estado_final.get("texto_analisis_primera_entrega", ""))
