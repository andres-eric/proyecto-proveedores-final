import os
import sys
import importlib.util
import pandas as pd
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
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



BASE = Path(__file__).resolve().parent.parent  # carpeta langrahpgrap, donde viven los dos agentes

def cargar_grafo(carpeta: str):
    # Se carga por ruta para evitar choques de nombres entre los dos agente.py
    ruta = BASE / carpeta / "agente.py"
    spec = importlib.util.spec_from_file_location(f"ag_{carpeta}", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.grafo

grafo_continuidad = cargar_grafo("Analisis_Continuidad_Negocio_1_")
grafo_riesgo = cargar_grafo("Analisis_evaluacion_Riesgo_2")
grafo_cantidad = cargar_grafo("Analisis_evaluacion_cantidad_3")
grafo_cantidad_detalle = cargar_grafo("Analisis_evaluacion_cantidad_3 _detalle")


class EstadoFlujo(TypedDict, total=False):
    

    mes_evaluado: str
    total_volumen: str
    variacion_volumen: str
    cumplimiento_optimo: str
    var_optimo: str
    tasa_riesgo: str
    texto_final_continuidad: list
    tiene_errores_continuidad: bool
    notas_auditor_continuidad: str
    borrador_continuidad: str
    

    datos_logistica: str
    datos_calidad: str
    borrador_riesgo: list
    texto_final_riesgo: list
    tiene_errores_riesgo: bool
    notas_auditor_riesgo: str



    mes_nombre: str
    total: str
    cumpleCantidad: str
    noCumpleCantidad: str
    porcentajeCumpleCantidad: str
    variacion_pp_cumplimiento_cantidad: str

    
    promedio_periodo: str
    meses_consecutivos_mejora: str
    posicion_promedio: str
    mes_nombre_inicio: str
    borrador_cantidad: str
    texto_final_cantidad: list
    tiene_errores_cantidad: bool
    notas_auditor_cantidad: str

    # analisis 3 detalle (proveedores con incumplimiento de cantidad)
    texto_analisis_3: str


builder = StateGraph(EstadoFlujo)

builder.add_node("continuidad_negocio", grafo_continuidad)
builder.add_node("riesgo", grafo_riesgo)
builder.add_node("cantidad", grafo_cantidad)
builder.add_node("cantidad_detalle", grafo_cantidad_detalle)


builder.add_edge(START, "continuidad_negocio")
builder.add_edge("continuidad_negocio", "riesgo")
builder.add_edge("riesgo", "cantidad")
builder.add_edge("cantidad", "cantidad_detalle")
builder.add_edge("cantidad_detalle", END)

grafo = builder.compile()


def ejecutar_reporte() -> EstadoFlujo:  
    print("---obteniendo datos de las apis...")


    return grafo.invoke({})



if __name__ == "__main__":
    print("ejecutando el agente....")
    estado_final = ejecutar_reporte()
    print(estado_final)


## langgraph dev
