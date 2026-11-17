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
    obtener_datos_completos,
    obtener_datos_kpi_detalle,
    obtener_datos_inspeccion_categoria,
    obtener_datos_kpi_detalle,
    obtener_data_set_cantidad

)
from etl.datos_analisis_resumen_general import datos_historicos
from etl.datos_detalles import datos_modulo_2
from etl.datos_detalles import convertir_df_a_contexto_llm
from etl.datos_analisis_cantidad_entrega import  instanciar_datos_cantidad,ejecucion_variables

from promt_template_cantidad_detalle import template_analisis_detalle_3,prompt_revision_analisis_3_detalle,prompt_corregir_analisis_3_detalle


class EstadoModelo_resumen_3_detalle(TypedDict, total=False):

    frase_mes: str
    proveedor_acumulado: str
    incumplidas_acumulado: str
    total_acumulado: str
    porcentaje_acumulado: str
    meses_acumulado: str
    mes_nombre: str
    mes_nombre_inicio: str
    frase_tasa: str
    frase_recurrencia: str


    texto_analisis_3: str
    notas_auditor_analisis_3_detalle: str
    tiene_errores_analisis_3_detalle: bool
    texto_final_analisis_3_detalle: list


llm = obtener_llm()


def estado_cargas_datos(state: EstadoModelo_resumen_3_detalle) -> dict:
    print('cargando datos')

    datos_cantidad_entrega=ejecucion_variables()
    

    return  {
        "frase_mes": datos_cantidad_entrega["frase_mes"],
        "proveedor_acumulado": datos_cantidad_entrega["proveedor_acumulado"],
        "incumplidas_acumulado": datos_cantidad_entrega["incumplidas_acumulado"],
        "total_acumulado": datos_cantidad_entrega["total_acumulado"],
        "porcentaje_acumulado": datos_cantidad_entrega["porcentaje_acumulado"],
        "meses_acumulado": datos_cantidad_entrega["meses_acumulado"],
        "mes_nombre": datos_cantidad_entrega["mes_nombre"],
        "mes_nombre_inicio": datos_cantidad_entrega["mes_nombre_inicio"],
        "frase_tasa": datos_cantidad_entrega["frase_tasa"],
        "frase_recurrencia": datos_cantidad_entrega["frase_recurrencia"]
    }

    

def redactar_analisis_cantidad(state: EstadoModelo_resumen_3_detalle) -> dict:
    print('redactando analisis cantidad 3 detalle')

    frase_mes = state["frase_mes"]
    proveedor_acumulado = state["proveedor_acumulado"]
    incumplidas_acumulado = state["incumplidas_acumulado"]
    total_acumulado = state["total_acumulado"]
    porcentaje_acumulado = state["porcentaje_acumulado"]
    meses_acumulado = state["meses_acumulado"]
    mes_nombre = state["mes_nombre"]
    mes_nombre_inicio = state["mes_nombre_inicio"]
    frase_tasa = state["frase_tasa"]
    frase_recurrencia = state["frase_recurrencia"]


    promt= PromptTemplate(
        input_variables=[
            "frase_mes",
            "proveedor_acumulado",
            "incumplidas_acumulado",
            "total_acumulado",
            "porcentaje_acumulado",
            "meses_acumulado",
            "mes_nombre",
            "mes_nombre_inicio",
            "frase_tasa",
            "frase_recurrencia"
        ],
        template=template_analisis_detalle_3
    )

    cadena = promt | llm | StrOutputParser()

    resultado = cadena.invoke({
        "frase_mes": frase_mes,
        "proveedor_acumulado": proveedor_acumulado,
        "incumplidas_acumulado": incumplidas_acumulado,
        "total_acumulado": total_acumulado,
        "porcentaje_acumulado": porcentaje_acumulado,
        "meses_acumulado": meses_acumulado,
        "mes_nombre": mes_nombre,
        "mes_nombre_inicio": mes_nombre_inicio,
        "frase_tasa": frase_tasa,
        "frase_recurrencia": frase_recurrencia,
    })

    return {"texto_analisis_3": resultado}


def nodo_revisar_analisis_3(state:EstadoModelo_resumen_3_detalle) -> dict:
    print('realizando revision errores analisis 3 ')


    promt_template_revision_3_detalle= PromptTemplate.from_template(prompt_revision_analisis_3_detalle)

    cadena_revision= promt_template_revision_3_detalle|llm|StrOutputParser()

    resultaldo_revision=cadena_revision.invoke({
    "texto": state.get("texto_analisis_3"),
    "frase_mes": state.get("frase_mes"),
    "proveedor_acumulado": state.get("proveedor_acumulado"),
    "incumplidas_acumulado": state.get("incumplidas_acumulado"),
    "total_acumulado": state.get("total_acumulado"),
    "porcentaje_acumulado": state.get("porcentaje_acumulado"),
    "meses_acumulado": state.get("meses_acumulado"),
    "frase_tasa": state.get("frase_tasa"),
    "frase_recurrencia": state.get("frase_recurrencia")
    })

    if "PERFECTO" in resultaldo_revision:
        return {"texto_final_analisis_3_detalle": [state["texto_analisis_3"]], "tiene_errores_analisis_3_detalle": False, "notas_auditor_analisis_3_detalle": ""}
    
    else:
        return {"tiene_errores_analisis_3_detalle": True, "notas_auditor_analisis_3_detalle": resultaldo_revision}


def corregir_errores__analisis_3(state:EstadoModelo_resumen_3_detalle) -> dict:
    print('corrigiendo errores analisis 3')

    promt_corregir_analisis_3_detalle= PromptTemplate(
        input_variables=[
            "errores",
            "texto"
        ],
        template=prompt_corregir_analisis_3_detalle
    )

    cadena_corregir= promt_corregir_analisis_3_detalle|llm|StrOutputParser()


    nuevo_texto_analisis_3_detalle=cadena_corregir.invoke({
    "texto": state.get("texto_analisis_3"),
    "errores": state.get("notas_auditor_analisis_3_detalle")
    })

    return {"texto_final_analisis_3_detalle": [nuevo_texto_analisis_3_detalle], "tiene_errores_analisis_3_detalle": False, "notas_auditor_analisis_3_detalle": ""} 

# ==============================================================================
# COMPILACIÓN DEL GRAFO
# ==============================================================================
builder = StateGraph(EstadoModelo_resumen_3_detalle)

builder.add_node("estado_cargas_datos", estado_cargas_datos)
builder.add_node("redactar_analisis_cantidad", redactar_analisis_cantidad)
builder.add_node("nodo_revisar_analisis_3", nodo_revisar_analisis_3)
builder.add_node("corregir_errores__analisis_3", corregir_errores__analisis_3)


def nodo_desicion_analisis_3_detalle(state:EstadoModelo_resumen_3_detalle) -> str:
    """decide si corregir o no"""
    if state["tiene_errores_analisis_3_detalle"]:
        return "corregir_errores__analisis_3"
    else:
        return END



builder.add_edge(START, "estado_cargas_datos")
builder.add_edge("estado_cargas_datos", "redactar_analisis_cantidad")
builder.add_edge("redactar_analisis_cantidad", "nodo_revisar_analisis_3")
builder.add_conditional_edges("nodo_revisar_analisis_3", nodo_desicion_analisis_3_detalle)
builder.add_edge("corregir_errores__analisis_3", END)


grafo = builder.compile()


def ejecutar_reporte() -> EstadoModelo_resumen_3_detalle:
    return grafo.invoke({})


if __name__ == "__main__":
    print("ejecutando el agente...")
    estado_final = ejecutar_reporte()

    print("\n" + "="*100)
    print("ANÁLISIS 3 - PROVEEDORES CON INCUMPLIMIENTO DE CANTIDAD:")
    print("="*100)
    finales = estado_final.get("texto_final_analisis_3_detalle")
    print(finales[-1] if finales else estado_final.get("texto_analisis_3", ""))
