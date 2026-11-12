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

PROMPT_DIR = ROOT_DIR / "langchain" / "langrahpgrap" / "Analisis_evaluacion_cantidad_3"
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
    obtener_datos_kpi_detalle,
    obtener_data_set_cantidad

)
from etl.datos_analisis_resumen_general import datos_historicos
from etl.datos_detalles import datos_modulo_2
from etl.datos_detalles import convertir_df_a_contexto_llm
from etl.datos_analisis_cantidad_entrega import  instanciar_datos_cantidad

from promt_template_cantidad  import template_resumen_cantidad,prompt_revision_cantidad,prompt_corregir_cantidad


class EstadoModelo_resumen_3(TypedDict, total=False):
    # datos que llena estado_cargas_datos
    mes_evaluado: str
    mes_nombre: str
    total: str
    cumpleCantidad: str
    noCumpleCantidad: str
    porcentajeCumpleCantidad: str
    variacion_pp_cumplimiento_cantidad: str

    # calculos historicos (si no se declaran aqui, LangGraph los descarta y llegan como None)
    promedio_periodo: str
    meses_consecutivos_mejora: str
    posicion_promedio: str
    mes_nombre_inicio: str

    # texto que escribe modulo_analisis
    borrador_cantidad: str

    # control de la revision (lo que escribe nodo_revisar_resumen_3)
    texto_final_cantidad: list
    tiene_errores_cantidad: bool
    notas_auditor_cantidad: str

llm = obtener_llm()


def estado_cargas_datos(state: EstadoModelo_resumen_3) -> dict:
    print('cargando datos')

    datos_cantidad_entrega=instanciar_datos_cantidad(obtener_data_set_cantidad())

    pct_mes=datos_cantidad_entrega['porcentaje_cumplimiento_cantidad'].values[0]
    promedio_periodo= round(datos_cantidad_entrega['porcentaje_cumplimiento_cantidad'].mean(),2)

    if pct_mes>promedio_periodo:
        posicion_promedio ="por encima del promedio"
    elif pct_mes<promedio_periodo:
        posicion_promedio ="por debajo del promedio"
    else:
        posicion_promedio ="igual al promedio"


    meses_consecutivos_mejora=0

    for i in datos_cantidad_entrega['variacion_pp_cumplimiento_cantidad']:
        if pd.notna(i) and i>0:
            meses_consecutivos_mejora+=1 
        else:
            break


    return {
        "mes_evaluado": str(datos_cantidad_entrega['anio-mes'].values[0]),
        "mes_nombre": pd.to_datetime(datos_cantidad_entrega['anio-mes'].values[0]).month_name(locale="es_ES").lower(),
        "total": str(datos_cantidad_entrega['total'].values[0]),
        "cumpleCantidad": str(datos_cantidad_entrega['cumpleCantidad'].values[0]),
        "noCumpleCantidad": str(datos_cantidad_entrega['noCumpleCantidad'].values[0]),
        "porcentajeCumpleCantidad": str(datos_cantidad_entrega['porcentaje_cumplimiento_cantidad'].values[0]),
        "variacion_pp_cumplimiento_cantidad": str(datos_cantidad_entrega['variacion_pp_cumplimiento_cantidad'].values[0]),

        ####### calculos ######
        "promedio_periodo": str(promedio_periodo),
        "meses_consecutivos_mejora": str(meses_consecutivos_mejora),
        "posicion_promedio": posicion_promedio,
        "mes_nombre_inicio": pd.to_datetime(datos_cantidad_entrega['anio-mes'].values[-1]).month_name(locale="es_ES").lower(),
    }





def modulo_analisis(state: EstadoModelo_resumen_3) -> dict:
    print('ejecutando modulo de analisis')
    
    mes_evaluado = state.get('mes_evaluado')
    mes_nombre = state.get('mes_nombre')    
    total = state.get('total')
    cumpleCantidad = state.get('cumpleCantidad')
    noCumpleCantidad = state.get('noCumpleCantidad')
    porcentajeCumpleCantidad = state.get('porcentajeCumpleCantidad')
    variacion_pp_cumplimiento_cantidad = state.get('variacion_pp_cumplimiento_cantidad')

    promedio_periodo=state.get('promedio_periodo')
    meses_consecutivos_mejora=state.get('meses_consecutivos_mejora')
    posicion_promedio=state.get('posicion_promedio')
    mes_nombre_inicio=state.get('mes_nombre_inicio')

    prompt = PromptTemplate(
        input_variables=[
            "mes_evaluado",
            "mes_nombre",  
            "total",
            "cumpleCantidad",
            "noCumpleCantidad",
            "porcentajeCumpleCantidad",
            "variacion_pp_cumplimiento_cantidad",
            "promedio_periodo",
            "meses_consecutivos_mejora",
            "posicion_promedio",
            "mes_nombre_inicio"
        ],
        template=template_resumen_cantidad
    )

    cadena=prompt | llm | StrOutputParser()

    resultado= cadena.invoke({
        "mes_evaluado": mes_evaluado,
        "mes_nombre": mes_nombre,  
        "total": total,
        "cumpleCantidad": cumpleCantidad,
        "noCumpleCantidad": noCumpleCantidad,
        "porcentajeCumpleCantidad": porcentajeCumpleCantidad,
        "variacion_pp_cumplimiento_cantidad": variacion_pp_cumplimiento_cantidad,
        "promedio_periodo": promedio_periodo,
        "meses_consecutivos_mejora": meses_consecutivos_mejora,
        "posicion_promedio": posicion_promedio,
        "mes_nombre_inicio": mes_nombre_inicio
    })


    return {
        "borrador_cantidad": resultado,
        "mes_evaluado": mes_evaluado,
        "total": total,
        "cumpleCantidad": cumpleCantidad,
        "noCumpleCantidad": noCumpleCantidad,
        "porcentajeCumpleCantidad": porcentajeCumpleCantidad,
        "variacion_pp_cumplimiento_cantidad": variacion_pp_cumplimiento_cantidad,


        "promedio_periodo": promedio_periodo,
        "meses_consecutivos_mejora": meses_consecutivos_mejora,
        "posicion_promedio": posicion_promedio,
        "mes_nombre_inicio": mes_nombre_inicio
    }


def nodo_revisar_resumen_3(state: EstadoModelo_resumen_3) -> dict:
    print('revisando el resumen...')
    
    promt_template_resumen_3=PromptTemplate.from_template(prompt_revision_cantidad)

    cadena_revision=promt_template_resumen_3 | llm | StrOutputParser()
    
    # el auditor compara el texto contra los datos oficiales, por eso se los pasamos
    resultado=cadena_revision.invoke({
        "texto": state["borrador_cantidad"],
        "total": state.get("total"),
        "cumpleCantidad": state.get("cumpleCantidad"),
        "noCumpleCantidad": state.get("noCumpleCantidad"),
        "porcentajeCumpleCantidad": state.get("porcentajeCumpleCantidad"),
        "variacion_pp_cumplimiento_cantidad": state.get("variacion_pp_cumplimiento_cantidad"),
        "promedio_periodo": state.get("promedio_periodo"),
        "meses_consecutivos_mejora": state.get("meses_consecutivos_mejora"),
    })
    if "PERFECTO" in resultado:
        return {"texto_final_cantidad": [state["borrador_cantidad"]], "tiene_errores_cantidad": False, "notas_auditor_cantidad": ""}
    else:
        return {"tiene_errores_cantidad": True, "notas_auditor_cantidad": resultado}


def nodo_correcion_3( state:EstadoModelo_resumen_3 ) -> dict: 

    print("corrigiendo el resumen...")
    promt_correccion_3=PromptTemplate(input_variables=["errores","texto_original"], template=prompt_corregir_cantidad)
    cadena=promt_correccion_3 | llm | StrOutputParser()

    # aca devuelve un nuevo texto corregido
    nuevo_texto=cadena.invoke({"errores":state["notas_auditor_cantidad"],"texto_orginal":state["borrador_cantidad"]})
    return {"texto_final_cantidad": [nuevo_texto], "tiene_errores_cantidad": False, "notas_auditor_cantidad": ""} 

# ==============================================================================
# COMPILACIÓN DEL GRAFO (va SIN indentar: a nivel del archivo, fuera de las funciones)
# ==============================================================================
builder = StateGraph(EstadoModelo_resumen_3)

builder.add_node("estado_cargas_datos", estado_cargas_datos)
builder.add_node("modulo_analisis", modulo_analisis)
builder.add_node("nodo_revisar_resumen_3", nodo_revisar_resumen_3)
builder.add_node("nodo_correcion_3", nodo_correcion_3)


def nodo_desicion_cantidad(state: EstadoModelo_resumen_3 ) ->  Literal["nodo_correcion_3", END]:

    if state["tiene_errores_cantidad"]:
        return "nodo_correcion_3"
    else:
        return END

builder.add_edge(START, "estado_cargas_datos")
builder.add_edge("estado_cargas_datos", "modulo_analisis")
builder.add_edge("modulo_analisis", "nodo_revisar_resumen_3")
builder.add_conditional_edges("nodo_revisar_resumen_3", nodo_desicion_cantidad)
builder.add_edge("nodo_correcion_3", END)

grafo = builder.compile()   



def ejecutar_reporte() -> EstadoModelo_resumen_3:
    print("---obteniendo datos de las apis...")
    return grafo.invoke({})



    
# if __name__ == "__main__":
#     print("ejecutando el agente...")
#     estado_final = ejecutar_reporte()
#     texto_final_cantidad = estado_final.get("borrador_cantidad", "no hay datos")
#     tiene_errores = estado_final.get("tiene_errores_cantidad", False)
#     texto_final_cantidad_ = estado_final["texto_final_cantidad"][-1] if estado_final.get("texto_final_cantidad") else estado_final.get("borrador_cantidad", "")
#     # Imprimir el texto final
#     print("\n" + "="*100)
#     print("TEXTO FINAL DEL ANÁLISIS:")
#     print("="*100)
#     print(texto_final_cantidad_)
#     print(tiene_errores)
#     print("="*100)



## langgraph dev
