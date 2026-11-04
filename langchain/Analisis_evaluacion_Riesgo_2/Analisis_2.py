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

from datos.carga_datos import (
    obtener_datos_completos,
    obtener_datos_kpi_detalle,
    obtener_datos_inspeccion_categoria,
)
from etl.datos_analisis_resumen_general import datos_historicos
from etl.datos_detalles import datos_modulo_2
from etl.datos_detalles import convertir_df_a_contexto_llm


# datos_modulo_2 devuelve (inspeccion_frecuente, categoria_mas_frecuente) -> (calidad, logistica)



def analisis_2(datos=None, datos_completos_inspeccion=None) -> str:

    llm=obtener_llm()

    datos_calidad, datos_logistica = datos_modulo_2(datos, datos_completos_inspeccion)

    datos_logistica = convertir_df_a_contexto_llm(datos_logistica)
    datos_calidad = convertir_df_a_contexto_llm(datos_calidad)

    

    template_resumen ="""
Eres el Director de Operaciones (COO) redactando el análisis mensual de proveedores críticos para la Mesa Directiva.
Este texto se ubicará justo encima de un gráfico que ya detalla todos los volúmenes, por lo que tu objetivo es interpretar el riesgo estructural, no listar datos.

REGLAS ARQUITECTÓNICAS DEL PROMPT (CERO ALUCINACIÓN Y HECHOS PUROS):
1. PROHIBIDO INVENTAR ACCIONES: Limítate estrictamente a diagnosticar el riesgo en base a los datos.
2. PROHIBICIÓN DE LECTURA LITERAL: No enumeres a los proveedores ni repitas todas sus cifras exactas.
3. FORMATO ESTRICTO: Redacta UN SOLO PÁRRAFO continuo. Sin viñetas y sin saltos de línea.
4. FORMATO NUMÉRICO DE SALIDA: Cuando menciones las unidades en tu redacción final, asegúrate de agregar un punto como separador de miles (ejemplo: 25.200 o 1.012).

EL ARCO NARRATIVO OBLIGATORIO (Sigue este guion exacto, redactando de forma fluida):

1. EL CUELLO DE BOTELLA LOGÍSTICO:
   Inicia indicando si el riesgo de retrasos presenta una concentración masiva (mencionando al proveedor con el mayor volumen) o si está distribuido. 

2. EL RIESGO DE DESABASTECIMIENTO POR CATEGORÍA:
   Si notas que una misma familia de material (ej. TORNILLERIA) falla en varios proveedores a la vez, alerta sobre la vulnerabilidad para esa categoría.

3. EL FOCO DE CALIDAD (MÁXIMA ATENCIÓN):
   Aborda las desviaciones de calidad indicando EXACTAMENTE cuál es el proveedor que tiene la MAYOR CANTIDAD numérica de unidades defectuosas para señalarlo como líder del impacto de calidad.

4. EL RIESGO SISTÉMICO (DOBLE AFECTACIÓN):
   Finaliza cruzando ambas tablas. Identifica a los proveedores que aparecen en AMBOS listados e indica: "A nivel estructural, [Proveedores] representan un riesgo sistémico de doble impacto operativo al presentar simultáneamente retrasos críticos y defectos de calidad."

--- DATOS DE CONTEXTO ---
TOP LOGÍSTICO:
{datos_logistica}

TOP CALIDAD:
{datos_calidad}
--- FIN DE DATOS ---

Análisis Ejecutivo:
"""

    prompt_template = PromptTemplate(input_variables=["datos_logistica", "datos_calidad"],
    template=template_resumen)
    cadena = prompt_template | llm | StrOutputParser()
    resultado=cadena.invoke({"datos_logistica": datos_logistica, "datos_calidad": datos_calidad})
    return resultado
    

   
# if __name__ == "__main__":
#     print(analisis_2(obtener_datos_kpi_detalle(), obtener_datos_inspeccion_categoria()))
    
    




