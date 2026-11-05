import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

import pandas as pd 
from sqlalchemy import create_engine
from dotenv import load_dotenv 
from datos.carga_datos import (obtener_data_set_primera_entrega)






# ===================================================================================================
# NOTA DE NEGOCIO: GRANULARIDAD DE LOS DENOMINADORES (KPIs LOGÍSTICOS)
# ===================================================================================================
# Este reporte maneja tres niveles distintos de evaluación, lo que genera diferencias matemáticas 
# esperadas entre los totales.

# 1. [Total] (Histórico / Nivel de Servicio General):
#    - Mide el  (Total de transacciones de recibo en almacén).
#    - Cuenta cada movimiento físico individualmente, incluyendo TODAS las entregas parciales.
#    - (Ejemplo: Si una orden llegó en 3 parciales distintos, suma 3 al total).

# 2. [TOTAL_ORDENES_CANTIDAD] (Cumplimiento Comercial por Volumen):
#    - Mide  (Total de Órdenes Únicas evaluadas).
#    - Agrupa los datos por Número de Orden (GROUP BY ), sumando todos los recibos 
#      parciales de esa orden en el mes para compararlos contra la cantidad original pedida.
#    - (Ejemplo: Suma los 3 camiones y cuenta como 1 sola orden evaluada).

# 3. [TOTAL_PRIMERAS_ENTREGAS] (Eficiencia de Tiempos):
#    - Mide la PUNTUALIDAD INICIAL (Total de Órdenes Únicas evaluadas por fecha).
#    -  Solo evalúa si el *primer* recibo 
#      de la orden llegó a tiempo y descartando el ruido temporal de las entregas rezagadas.






# datos que se utilizan: datos obtenidos de obtener_datos_completos()
def datos_historicos(datos=None):

    datos_cantidad=datos.copy()
    cantiadad_provedores=datos_cantidad['proveedor'].nunique()

    provedores_no_cumplen_cantidad=datos_cantidad[datos_cantidad['cantidadIncumplimiento']>0]['proveedor'].nunique()
    proveedores_no_cumplen_1_entrega = datos_cantidad.loc[datos_cantidad['cantidadCumple1Entrega'] < datos_cantidad['totalPrimerasEntregas']]
    proveedores_no_cumplen_1_entrega_unicos=proveedores_no_cumplen_1_entrega['proveedor'].nunique()

    datos_proveedores=datos_cantidad.groupby(['anio-mes','proveedor'])[['cantidadIncumplimiento','cantidadCumpleCantidad','totalOrdenesCantidad','cantidadCumple1Entrega','totalPrimerasEntregas']].sum().reset_index()
    datos_proveedores=datos_proveedores.sort_values(by=['anio-mes'],ascending=False)
    
    datos_resumen=datos_cantidad.groupby(['anio-mes'])[['cantidadIncumplimiento','cantidadCumpleCantidad','totalOrdenesCantidad','cantidadCumple1Entrega','totalPrimerasEntregas']].sum().reset_index()
    datos_resumen=datos_resumen.sort_values(by=['anio-mes'],ascending=False)
    datos_resumen=datos_resumen[1:]
    datos_resumen['porcentaje_cumplimiento_cantidad']=round((datos_resumen['cantidadCumpleCantidad']/datos_resumen['totalOrdenesCantidad'])*100,1).fillna(0)
    datos_resumen['variacion_porcentaje_cumplimiento_cantidad'] = round(datos_resumen['porcentaje_cumplimiento_cantidad'].pct_change(periods=-1) * 100,1).fillna(0)
    datos_resumen['porcentaje_cumplimiento_1_entrega']=round((datos_resumen['cantidadCumple1Entrega']/datos_resumen['totalPrimerasEntregas'])*100,1).fillna(0)
    datos_resumen['variacion_porcentaje_cumplimiento_1_entrega'] = round(datos_resumen['porcentaje_cumplimiento_1_entrega'].pct_change(periods=-1) * 100,1).fillna(0)
    

    return datos_resumen

    




if __name__ == "__main__":
    datos = obtener_data_set_primera_entrega()
    df_historicos = datos_historicos(datos)
    print(df_historicos)



