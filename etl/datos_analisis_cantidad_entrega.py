import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

import pandas as pd 
from sqlalchemy import create_engine
from dotenv import load_dotenv 
from datos.carga_datos import (obtener_datos_completos)





def cambiar_nombre_head(df):

    datos_resumen_1 = df.rename(columns={

        "verde": "Cumplimiento_optimo",
        "negra": "Retraso_Severo",
        "amarilla": "Riesgo_de_Retraso",
        "roja": "Incumplimiento_de_Plazo"

    })[1:].reset_index(drop=True)
    return datos_resumen_1



# datos que se utilizan: datos obtenidos de obtener_datos_completos()
def datos_historicos(datos=None):

    datos_resumen=datos.groupby(['anio-mes'])[['negra','roja','amarilla','verde','total','cantidad_ingresada','cantidad_recibida_defectuosa']].sum()
    datos_resumen=datos_resumen.sort_values(['anio-mes','negra','verde'],ascending=False).reset_index()
    datos_resumen_1=cambiar_nombre_head(datos_resumen)
    datos_resumen_1['variacion_mes'] = datos_resumen_1['total'].pct_change(periods=-1) * 100
    datos_resumen_1['variacion_mes'] = datos_resumen_1['variacion_mes'].fillna(0).round(2)
    datos_resumen_1['var_optimo']=(datos_resumen_1['Cumplimiento_optimo'].pct_change(periods=-1) * 100).round(2).fillna(0)
    datos_resumen_1['tasa_cumpli_perfecto']=((1-(datos_resumen_1['Retraso_Severo']/datos_resumen_1['total']))*100).round(2).fillna(0)
    datos_resumen_1['var_incumplimiento']=(datos_resumen_1['Incumplimiento_de_Plazo'].pct_change(periods=-1) * 100).round(2).fillna(0)
    datos_resumen_1['var_retraso']=(datos_resumen_1['Riesgo_de_Retraso'].pct_change(periods=-1) * 100).round(2).fillna(0)
    datos_resumen_1['var_ Severo']=(datos_resumen_1['Retraso_Severo'].pct_change(periods=-1) * 100).round(2).fillna(0)
    datos_resumen_1['tasa_riesgo_critico']=(datos_resumen_1['Retraso_Severo']+datos_resumen_1['Incumplimiento_de_Plazo'])/datos_resumen_1['total']*100
    datos_resumen_1['cantidad_ingresada']=datos_resumen_1['cantidad_ingresada']
    datos_resumen_1=datos_resumen_1[['anio-mes','Cumplimiento_optimo','var_optimo','tasa_cumpli_perfecto','Retraso_Severo','var_ Severo','Riesgo_de_Retraso','var_retraso','tasa_riesgo_critico','Incumplimiento_de_Plazo','var_incumplimiento','total','variacion_mes','cantidad_ingresada','cantidad_recibida_defectuosa']]
    return datos_resumen_1




if __name__ == "__main__":
    datos = obtener_datos_completos()
    df_historicos = datos_historicos(datos)
    print(df_historicos)



