import os
import pandas as pd 
from sqlalchemy import create_engine
from dotenv import load_dotenv 
#import matplotlib.pyplot as plt
#import seaborn as sns
import sys
from pathlib import Path


#=======================#=======================#==================
def obtener_llm():

    from langchain_ollama import ChatOllama
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.prompts import ChatPromptTemplate
    try:
        llm_gemini_instance = ChatOllama(
            model="qwen2.5-coder:14b",
            #base_url="gemma2:27b",  # URL por defecto de Ollama
            temperature=0.0, 
            #repeat_penalty=1.15,
            #num_gpu=10  # <-- Se procesarán menos capas en la Tarjeta Gráfica para no saturar la VRAM y evitar el error CUDA
        )
        print("Modelos de Langchain para la pregunta incializado.")
        return llm_gemini_instance
    except Exception as e:
        print(f"El verdadero error al inicializar es: {type(e).__name__} - {e}")
        return None



#=======================#=======================#==================
# unir pipline de paso 1-2-3

