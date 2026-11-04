import os
import sys
from pathlib import Path
import numpy as np

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))


import pandas as pd 
from sqlalchemy import create_engine
from dotenv import load_dotenv 
from datos.carga_datos import (obtener_datos_kpi_detalle)
from datos.carga_datos import obtener_datos_kpi_detalle
from datos.carga_datos import obtener_datos_completos







def fecha_anterior(df):

    datos=pd.DataFrame(df)
    periodos=pd.to_datetime(datos['anio-mes']).dt.to_period('M')
    mes_anterior=periodos.max()-1
    return str(mes_anterior)  # Convierte Period('2026-09') → '2026-09' para comparar con str


if __name__ == "__main__":
    datos = obtener_datos_kpi_detalle()
    datos_completos=obtener_datos_completos()
    print(fecha_anterior(datos))