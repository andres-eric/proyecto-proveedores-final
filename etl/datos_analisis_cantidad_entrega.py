import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

import pandas as pd 
from sqlalchemy import create_engine
from dotenv import load_dotenv 
from datos.carga_datos import (obtener_data_set_cantidad)




def datos_agrupados(datos=None):

    datos_cantidad=datos.copy()
    datos_cantidad=datos_cantidad[['anio-mes','proveedor','sumaAcumulada','cantidadPedido','cumpleCantidad','noCumpleCantidad']]
    datos_cantidad['total']=datos_cantidad['cumpleCantidad']+datos_cantidad['noCumpleCantidad']
    datos_agrupados=datos_cantidad.groupby(['anio-mes','proveedor'],as_index=False)[['sumaAcumulada','cantidadPedido','cumpleCantidad','noCumpleCantidad','total']].sum()
    return datos_agrupados


def datos_historicos(datos=None):

    datos_h_cantidad=datos.copy()
    datos_h_cantidad=datos_h_cantidad[['anio-mes','proveedor','sumaAcumulada','cantidadPedido','cumpleCantidad','noCumpleCantidad','total']]
    datos_h_cantidad=datos_h_cantidad.groupby(['anio-mes'],as_index=False)[['total','cumpleCantidad','noCumpleCantidad']].sum().sort_values(['anio-mes'],ascending=[False])
    datos_h_cantidad['porcentaje_cumplimiento_cantidad']=round(datos_h_cantidad['cumpleCantidad']/datos_h_cantidad['total']*100,1)
    datos_h_cantidad['porcentaje_no_cumplimiento_cantidad']=round(datos_h_cantidad['noCumpleCantidad']/datos_h_cantidad['total']*100,1)
    datos_h_cantidad['variacion_pp_cumplimiento_cantidad'] = round(datos_h_cantidad['porcentaje_cumplimiento_cantidad'].diff(periods=-1), 1)

    return datos_h_cantidad[1:]


def instanciar_datos_cantidad(datos=None):
    datos_agrupados_=datos_agrupados(datos)
    datos_historicos_=datos_historicos(datos_agrupados_)
    return datos_historicos_





if __name__ == "__main__":
    datos = obtener_data_set_cantidad()
    df_historicos_mes = datos_historicos(datos_agrupados(datos))
    print(df_historicos_mes)



