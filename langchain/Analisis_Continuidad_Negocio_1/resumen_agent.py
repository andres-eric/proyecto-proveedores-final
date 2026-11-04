import os
import sys
import pandas as pd

from pathlib import Path

# Asegurar que la raíz del proyecto está en sys.path
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from typing import List
from datetime import datetime
from dotenv import find_dotenv, load_dotenv
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

from datos.carga_datos import (obtener_datos_completos)
from etl.datos_analisis_resumen_general import datos_historicos




def analisis_1(datos) -> str:

    ultimo_mes_analisis=datos[0:1]
    llm=obtener_llm()

    mes=ultimo_mes_analisis['anio-mes'].values[0]
    var_optimo=ultimo_mes_analisis['var_optimo'].values[0]
    tasa_riesgo=format(ultimo_mes_analisis['tasa_riesgo_critico'].values[0], '.2f')
    var_incumplimiento=ultimo_mes_analisis['var_incumplimiento'].values[0]
    var_Severo=ultimo_mes_analisis['var_ Severo'].values[0]

    total_volumen = ultimo_mes_analisis['total'].values[0]
    variacion_volumen = ultimo_mes_analisis['variacion_mes'].values[0]
    cumplimiento_optimo = ultimo_mes_analisis['Cumplimiento_optimo'].values[0]


    template_resumen ="""
Eres el Director de Operaciones (COO) redactando el resumen mensual de abastecimiento para los accionistas correspondiente a {mes_evaluado}.

REGLAS ARQUITECTÓNICAS DEL PROMPT (CERO ALUCINACIÓN Y HECHOS PUROS):
1. PROHIBIDO INVENTAR ACCIONES: Limítate estrictamente a reportar los números y sus definiciones operativas. NO agregues frases sobre "acciones tomadas", "consumo de inventarios" o "gestiones del equipo". 
2. DEFINICIONES INTEGRADAS: Usa exactamente el texto que se te proporciona en el guion para explicar los indicadores.
3. INTERPRETACIÓN DE SIGNOS MATEMÁTICOS: Si el valor de la variación es positivo, omite el signo "+" y redacta "un aumento del X%". Si el valor es negativo, omite el signo "-" y redacta "una caída del X%" o "una disminución del X%".

EL ARCO NARRATIVO OBLIGATORIO (Sigue este guion exacto, redactando UN SOLO PÁRRAFO continuo):

1. EL ESCENARIO MATEMÁTICO:
   Inicia indicando que durante {mes_evaluado}, la operación registró {total_volumen} ingresos de materia prima. Usa la variable de {variacion_volumen}% para indicar si hubo un aumento o disminución frente al mes anterior.

2. EL CUMPLIMIENTO (Definición orgánica + Dato + Variación):
   Continúa exactamente con esta idea: "De este total, solo {cumplimiento_optimo} ingresos cumplieron con las cantidades y fechas pactadas originalmente (lo que medimos como cumplimiento óptimo)." 
   Inmediatamente después, usa la variable de {var_optimo}% para explicar si esto representa una caída o un incremento en la fiabilidad del servicio respecto al mes pasado.

3. EL RIESGO CRÍTICO (Dato + Definición orgánica):
   Finaliza explicando el nivel de riesgo con esta frase exacta: "En consecuencia, el {tasa_riesgo}% de la operación entró en riesgo crítico, es decir, despachos que presentaron retrasos graves o incumplimientos definitivos de entrega."
   (DETÉNTE AQUÍ. No agregues ninguna conclusión adicional).

Resumen Ejecutivo:
"""

    prompt_template = PromptTemplate(input_variables=["mes_evaluado", "total_volumen", "variacion_volumen", "cumplimiento_optimo", "var_optimo", "tasa_riesgo"],
    template=template_resumen)
    cadena = prompt_template | llm | StrOutputParser()
    resultado=cadena.invoke({"mes_evaluado": mes, "total_volumen": total_volumen, "variacion_volumen": variacion_volumen, "cumplimiento_optimo": cumplimiento_optimo, "var_optimo": var_optimo, "tasa_riesgo": tasa_riesgo})
    return resultado
    

   
if __name__ == "__main__":
    datos = datos_historicos(obtener_datos_completos())
    print(analisis_1(datos=ultimo_mes_analisis))
    #print(ultimo_mes_analisis)




