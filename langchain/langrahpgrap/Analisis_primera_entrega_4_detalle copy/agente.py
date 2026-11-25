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
from etl.datos_analisis_primera_entrega import ejecutar_detalle


from promt_template_entrega import template_proveedores_primera


class EstadoModelo_proveedores_primera_entrega_detalle(TypedDict, total=False):

    # --- Texto que devuelve variables_analisis_primera_entrega ---
    datos_proveedores_primera: str

    # --- Flujo escritor → auditor → corrector ---
    texto_proveedores_primera: str
    texto_final_proveedores_primera: list
    tiene_errores_proveedores_primera: bool
    notas_auditor_proveedores_primera: str

llm = obtener_llm()



def estado_cargas_datos(state: EstadoModelo_proveedores_primera_entrega_detalle) -> dict:
    print('cargando datos')

    datos_detalle_primera_entrega=ejecutar_detalle()
    return  {
        "datos_proveedores_primera": datos_detalle_primera_entrega["datos_proveedores_primera"]
    }



def redactar_analisis_proveedores_primera_entrega(state: EstadoModelo_proveedores_primera_entrega_detalle) -> dict:
    print('redactando analisis cantidad 3')

    datos_proveedores_primera = state.get("datos_proveedores_primera")



    promt= PromptTemplate(
        input_variables=[
            "datos_proveedores_primera"      
        ],
        template=template_proveedores_primera
    )

    cadena = promt | llm | StrOutputParser()

    resultado = cadena.invoke({
        "datos_proveedores_primera": datos_proveedores_primera
        
    })

    return {"texto_proveedores_primera": resultado}




# def nodo_revisar_analisis_proveedores_primera_entrega(state:EstadoModelo_proveedores_primera_entrega_detalle) -> dict:
#     print('realizando revision errores analisis cantidad ')

#     promt_template_revision_cantidad= PromptTemplate.from_template(prompt_revision_primera)

#     cadena_revision= promt_template_revision_cantidad|llm|StrOutputParser()

#     resultaldo_revision=cadena_revision.invoke({
#     "texto": state.get("texto_analisis_primera_entrega"),
#     "total_primera": state.get("total_primera"),
#     "cumple_primera": state.get("cumple_primera"),
#     "no_cumple_primera": state.get("no_cumple_primera"),
#     "porcentaje_primera": state.get("porcentaje_primera"),
#     "variacion_pp_primera": state.get("variacion_pp_primera"),
#     "promedio_periodo_primera": state.get("promedio_periodo_primera"),
#     "meses_consecutivos": state.get("meses_consecutivos")
#     })

#     if "PERFECTO" in resultaldo_revision:
#         return {"texto_final_analisis_primera_entrega": [state["texto_analisis_primera_entrega"]], "tiene_errores_analisis_primera_entrega": False, "notas_auditor_analisis_primera_entrega": ""}
    
#     else:
#         return {"tiene_errores_analisis_primera_entrega": True, "notas_auditor_analisis_primera_entrega": resultaldo_revision}






# def corregir_errores__analisis_primera_entrega(state:EstadoModelo_resumen_primera_entrega) -> dict:
#     print('corrigiendo errores')

#     promt_corregir_analisis_cantidad= PromptTemplate(
#         input_variables=[
#             "errores",
#             "texto_original"
#         ],
#         template=prompt_corregir_primera
#     )

#     cadena_corregir=promt_corregir_analisis_cantidad|llm|StrOutputParser()


#     nuevo_texto_analisis_entrega=cadena_corregir.invoke({
#     "texto_original": state.get("texto_analisis_primera_entrega"),
#     "errores": state.get("notas_auditor_analisis_primera_entrega")
#     })

#     return {"texto_final_analisis_primera_entrega": [nuevo_texto_analisis_entrega], "tiene_errores_analisis_primera_entrega": False, "notas_auditor_analisis_primera_entrega": ""} 

# ==============================================================================
# COMPILACIÓN DEL GRAFO
# ==============================================================================
builder = StateGraph(EstadoModelo_proveedores_primera_entrega_detalle)

builder.add_node("estado_cargas_datos", estado_cargas_datos)
builder.add_node("redactar_analisis_proveedores_primera_entrega", redactar_analisis_proveedores_primera_entrega)
# builder.add_node("nodo_revisar_analisis_primera_entrega", nodo_revisar_analisis_primera_entrega)
# builder.add_node("corregir_errores__analisis_primera_entrega", corregir_errores__analisis_primera_entrega)


# def nodo_desicion_analisis_primera_entrega(state:EstadoModelo_proveedores_primera_entrega_detalle) -> str:
#     """decide si corregir o no"""
#     if state["tiene_errores_analisis_primera_entrega"]:
#         return "corregir_errores__analisis_primera_entrega"
#     else:
#         return END

builder.add_edge(START, "estado_cargas_datos")
builder.add_edge("estado_cargas_datos", "redactar_analisis_proveedores_primera_entrega")
# builder.add_edge("redactar_analisis_primera_entrega", "nodo_revisar_analisis_primera_entrega")
# builder.add_conditional_edges("nodo_revisar_analisis_primera_entrega", nodo_desicion_analisis_primera_entrega)
# builder.add_edge("corregir_errores__analisis_primera_entrega", END)


grafo = builder.compile()


def ejecutar_reporte() -> EstadoModelo_proveedores_primera_entrega_detalle:
    return grafo.invoke({})




if __name__ == "__main__":
    print("ejecutando el agente...")
    estado_final = ejecutar_reporte()

    print("\n" + "="*100)
    print("ANÁLISIS 4 PRIMERA ENTREGA:")
    print("="*100)
    print(estado_final.get("texto_proveedores_primera", ""))
