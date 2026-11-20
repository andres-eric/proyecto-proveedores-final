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
    datos_resumen['porcentaje_cumplimiento_1_entrega']=round((datos_resumen['cantidadCumple1Entrega']/datos_resumen['totalPrimerasEntregas'])*100,1)
    datos_resumen['variacion_pp_cumplimiento_1_entrega'] = round(datos_resumen['porcentaje_cumplimiento_1_entrega'].diff(periods=-1), 1)
    datos_resumen=datos_resumen[['anio-mes','totalPrimerasEntregas','cantidadCumple1Entrega','porcentaje_cumplimiento_1_entrega','variacion_pp_cumplimiento_1_entrega']].copy()
    datos_resumen['cantidad_no_cumple'] = datos_resumen['totalPrimerasEntregas'] - datos_resumen['cantidadCumple1Entrega']

    
    return datos_resumen


def variables_analisis_primera_entrega():

    df=obtener_data_set_primera_entrega()
    datos_resumen=datos_historicos(df)


    porcentaje_mes=datos_resumen['porcentaje_cumplimiento_1_entrega'].values[0]
    promedio_cumplimidatos_resumen= round(datos_resumen['porcentaje_cumplimiento_1_entrega'].mean(),1)

    if porcentaje_mes>promedio_cumplimidatos_resumen:
        posicion_promdio='por encima del promedio'
    elif porcentaje_mes< promedio_cumplimidatos_resumen:
        posicion_promdio='por debajo del promedio'
    else: posicion_promdio='igual al promedio'

    meses_consectivos=0

    for i in datos_resumen['variacion_pp_cumplimiento_1_entrega']:
        if pd.notna(i) and i>0:
            meses_consectivos+=1

     

        else:
            break


    return {
        "mes_evaluado": str(datos_resumen['anio-mes'].values[0]),
        "mes_nombre": pd.to_datetime(datos_resumen['anio-mes'].values[0]).month_name(locale="es_ES").lower(),
        "total_primera": str(datos_resumen['totalPrimerasEntregas'].values[0]),
        "cumple_primera": str(datos_resumen['cantidadCumple1Entrega'].values[0]),
        "no_cumple_primera": str(datos_resumen['cantidad_no_cumple'].values[0]),
        "porcentaje_primera": str(porcentaje_mes),
        "variacion_pp_primera": str(datos_resumen['variacion_pp_cumplimiento_1_entrega'].values[0]),
        # --- Contexto histórico ---
        "promedio_periodo_primera": str(promedio_cumplimidatos_resumen),
        "posicion_promedio": posicion_promdio,
        "mes_nombre_inicio": pd.to_datetime(datos_resumen['anio-mes'].values[-1]).month_name(locale="es_ES").lower(),
        "meses_consecutivos": str(meses_consectivos)

    }



def datos_detalle_primera_entrega(datos=None):

    datos_=datos.copy()
    datos_['no_cumple_primera'] = datos_['totalPrimerasEntregas'] - datos_['cantidadCumple1Entrega']
    entrega_agrupado= datos_.groupby(['anio-mes','proveedor'],as_index=False)[['totalPrimerasEntregas','cantidadCumple1Entrega','no_cumple_primera']].sum()
    mes=entrega_agrupado['anio-mes'].unique().tolist()
    mes_=mes[-2]

    entrega_agrupado=entrega_agrupado[entrega_agrupado['anio-mes']<=mes_]

    entrega_agrupado_filtrado= entrega_agrupado[entrega_agrupado['no_cumple_primera']>0]
    entrega_agrupado_filtrado=entrega_agrupado_filtrado.sort_values(['no_cumple_primera'],ascending=False)


    acumulado=entrega_agrupado_filtrado.groupby(['proveedor'],as_index=False)['no_cumple_primera'].sum().sort_values(['no_cumple_primera'],ascending=False)





    return acumulado





def ejecutar_resumen():

    porcentaje_mes=variables_analisis_primera_entrega()

    return porcentaje_mes




# if __name__ == "__main__":

    
#     df=obtener_data_set_primera_entrega()
#     datos_historico=datos_historicos(df)
#     print(datos_historico)



if __name__ == "__main__":
    #print(ejecutar_resumen())
    df=obtener_data_set_primera_entrega()
    detalle=datos_detalle_primera_entrega(df)

    print(detalle)





