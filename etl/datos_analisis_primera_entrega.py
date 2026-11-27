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
from etl.datos_analisis_cantidad_entrega import ejecucion_variables_cantidad






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


def variables_resumen_primera_entrega():

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

    fechas = sorted(datos_['anio-mes'].unique(), reverse=False)
    datos_['no_cumple_primera'] = datos_['totalPrimerasEntregas'] - datos_['cantidadCumple1Entrega']
    entrega_agrupado= datos_.groupby(['anio-mes','proveedor'],as_index=False)[['totalPrimerasEntregas','cantidadCumple1Entrega','no_cumple_primera']].sum()
    mes=entrega_agrupado['anio-mes'].unique().tolist()
    mes_=mes[-2]

    entrega_agrupado=entrega_agrupado[entrega_agrupado['anio-mes']<=mes_]

    entrega_agrupado_filtrado= entrega_agrupado[entrega_agrupado['no_cumple_primera']>0]
    entrega_agrupado_filtrado=entrega_agrupado_filtrado.sort_values(['no_cumple_primera'],ascending=False)
    meses_agrupados = (entrega_agrupado_filtrado.groupby('proveedor', as_index=False).agg(meses_con_incumplimiento=('anio-mes', 'nunique'))).sort_values(['meses_con_incumplimiento'],ascending=False).reset_index(drop=True)
    meses_agrupados=meses_agrupados[meses_agrupados['meses_con_incumplimiento']>=2]

    acumulado=entrega_agrupado_filtrado.groupby(['proveedor'],as_index=False)[['no_cumple_primera','totalPrimerasEntregas']].sum().sort_values(['no_cumple_primera'],ascending=False)
    acumulado=acumulado.reset_index(drop=True).head(10)
    acumulado['porcentaje']=round(acumulado['no_cumple_primera']/acumulado['totalPrimerasEntregas'],2)*100


    acumulado = pd.merge(acumulado, meses_agrupados, on='proveedor', how='inner')

    datos_mes= datos_[datos_['anio-mes']==mes_]
    datos_mes= datos_mes[datos_mes['no_cumple_primera']>0]
    agrupado_mes=datos_mes.groupby(['anio-mes','proveedor'], as_index=False)[['totalPrimerasEntregas','cantidadCumple1Entrega','no_cumple_primera']].sum()
    agrupado_mes=agrupado_mes.sort_values(by=['no_cumple_primera'],ascending=False)

    return agrupado_mes,acumulado,fechas,meses_agrupados






def _unir_con_y(items):
  
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " y " + items[-1]




def variables_analisis_primera_entrega(df_mes, df_acum, fechas, meses_agrupados, datos_cantidad):

    mes_maximo = fechas[-2]
    mes_primero = fechas[0]
    n_meses = len(fechas) - 1
    mes_nombre = pd.to_datetime(mes_maximo).month_name(locale="es_ES").lower()
    mes_nombre_inicio = pd.to_datetime(mes_primero).month_name(locale="es_ES").lower()

    proveedor_mes = df_mes['proveedor'].tolist()

   
    if df_mes.empty:
        texto = (f"MES Y PERÍODO:\nDurante {mes_nombre} ningún proveedor registró órdenes "
                 f"que requirieran entregas adicionales.\n\n"
                 f"RECURRENCIA:\n- Recurrentes: NINGUNO.")
        return {"datos_proveedores_primera": texto}

    # ---- Mes ----
    total_mes = int(df_mes['no_cumple_primera'].sum())
    top_5 = df_mes.head(4)
    resto = df_mes.iloc[4:]

    primero = top_5.iloc[0]
    frase = (f"De las {total_mes} órdenes que requirieron entregas adicionales en {mes_nombre}, "
             f"{primero['proveedor']} concentra {int(primero['no_cumple_primera'])}")

    siguientes = [f"{r['proveedor']} con {int(r['no_cumple_primera'])}" for _, r in top_5.iloc[1:].iterrows()]
    if siguientes:
        frase += f", seguido de {_unir_con_y(siguientes)}"
    if not resto.empty:
        frase += (f"; las {int(resto['no_cumple_primera'].sum())} restantes se distribuyen "
                  f"entre {len(resto)} proveedores")


    acumulado = df_acum.loc[df_acum['no_cumple_primera'].idxmax()]
    incumplida = (                                                     
        f"El principal foco del período ({mes_nombre_inicio} a {mes_nombre}) es {acumulado['proveedor']}, "
        f"con {int(acumulado['no_cumple_primera'])} de sus {int(acumulado['totalPrimerasEntregas'])} órdenes "
        f"incompletas en el primer recibo ({acumulado['porcentaje']}%) e incumplimiento en "
        f"{int(acumulado['meses_con_incumplimiento'])} de los {n_meses} meses analizados."
    )
    frase_mes = frase + ". " + incumplida                               

   
    meses_rec = meses_agrupados.loc[
        (meses_agrupados['proveedor'].isin(proveedor_mes)) &
        (meses_agrupados['meses_con_incumplimiento'] >= 2),              
        ['proveedor', 'meses_con_incumplimiento']
    ].sort_values('meses_con_incumplimiento', ascending=False)

    if meses_rec.empty:
        recurrentes_ = "- Recurrentes: NINGUNO. Los proveedores del mes son casos puntuales."
    else:
        partes = [f"{r['proveedor']} ({int(r['meses_con_incumplimiento'])} de {n_meses} meses)"
                  for _, r in meses_rec.iterrows()]
        recurrentes_ = f"- Recurrentes (fallaron en {mes_nombre} y en meses anteriores): {_unir_con_y(partes)}."

    # ---- Cruce con cantidad ----                                       # CAMBIO: nuevo
    recurrentes_cantidad = set(datos_cantidad['proveedor'].astype(str).str.strip())
    cruce = sorted(set(meses_rec['proveedor']) & recurrentes_cantidad)
    if cruce:
        recurrentes_ += f"\n- Recurrentes también en cumplimiento de cantidad: {_unir_con_y(cruce)}."

    # ---- Un solo texto ----                                            # CAMBIO
    texto = (
        "MES Y PERÍODO:\n" + frase_mes + "\n\n"
        "RECURRENCIA:\n" + recurrentes_
    )
    return {"datos_proveedores_primera": texto}






def ejecutar_resumen():

    porcentaje_mes=variables_resumen_primera_entrega()

    return porcentaje_mes


def ejecutar_detalle():

    df=obtener_data_set_primera_entrega()
    detalle,agrupado,fechas,meses=datos_detalle_primera_entrega(df)
    df_mes, df_acum, fechas=ejecucion_variables_cantidad()
    analisis=variables_analisis_primera_entrega(detalle,agrupado,fechas,meses,df_acum)

    return analisis

# if __name__ == "__main__":

#     df=obtener_data_set_primera_entrega()
#     datos_historico=datos_historicos(df)
#     print(datos_historico)



# if __name__ == "__main__":
#     #print(ejecutar_resumen())
#     df=obtener_data_set_primera_entrega()
#     detalle,agrupado,fechas,meses=datos_detalle_primera_entrega(df)

#     print(meses) 


if __name__ == "__main__":

    df=obtener_data_set_primera_entrega()
    detalle,agrupado,fechas,meses=datos_detalle_primera_entrega(df)
    df_mes, df_acum, fechas=ejecucion_variables_cantidad()
    analisis=variables_analisis_primera_entrega(detalle,agrupado,fechas,meses,df_acum)
    

    print(analisis)

