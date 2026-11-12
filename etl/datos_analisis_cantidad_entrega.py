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



def top_cantidad_provedores(datos=None):

    datos_=datos.copy()
    fecha_=sorted(datos_['anio-mes'].unique().tolist())
    fecha=fecha_[-2]
    datos_ = datos_[datos_['anio-mes'] <= fecha]
    datos_filtrados=datos_[datos_['anio-mes']==fecha].sort_values(['cumpleCantidad'],ascending=[False])
    datos_agrupados=datos_filtrados.groupby(['proveedor'], as_index=False)[['total','cumpleCantidad','noCumpleCantidad']].sum().sort_values(['noCumpleCantidad'],ascending=False).head(10)
    datos_agrupados=datos_agrupados[datos_agrupados['noCumpleCantidad']>0]
    datos_agrupados=datos_agrupados[['proveedor','total','noCumpleCantidad']]
    datos_agrupados['porcentaje_incumplimiento'] = round(datos_agrupados['noCumpleCantidad'] / datos_agrupados['total'] * 100, 1)


    datos_acumulados=datos_.groupby(['anio-mes','proveedor'], as_index=False).agg(faltantes_acumulados=('noCumpleCantidad','sum'))
    datos_acumulados=datos_acumulados[datos_acumulados['faltantes_acumulados']>0].reset_index(drop=True)#.sort_values(['faltantes_acumulados'],ascending=False)
    datos_acumulados_conteo=datos_acumulados[['anio-mes','proveedor']].drop_duplicates()
    conteo=datos_acumulados['proveedor'].value_counts().reset_index(name='meses_con_faltantes')

    acumulados_top=datos_acumulados.groupby('proveedor',as_index=False).agg(faltantes_acumulados_=('faltantes_acumulados','sum')).sort_values('faltantes_acumulados_', ascending=False)
    
    datos_total=datos_.groupby(['proveedor']).agg(total=('total','sum')).sort_values('total', ascending=False)


    acumulados=pd.merge(acumulados_top,conteo,on='proveedor',how='inner')
    acumulados = pd.merge(acumulados, datos_total, on='proveedor', how='left')
    acumulados['porcentaje_incumplimiento'] = round(acumulados['faltantes_acumulados_'] / acumulados['total'] * 100, 1)
    acumulados=acumulados.sort_values('faltantes_acumulados_', ascending=False).head(10)

    return datos_agrupados,acumulados,fecha_





def funcion_texto_cantidad(df_top_cantidad_provedo, datos_acmulados, fechas):

    mes_maximo = fechas[-2]
    mes_primero = fechas[0]
    n_meses = len(fechas) - 1                                    # CAMBIO: meses del período, sin el mes en curso
    mes_nombre_actual = pd.to_datetime(mes_maximo).month_name(locale="es_ES").lower()
    mes_nombre_primero = pd.to_datetime(mes_primero).month_name(locale="es_ES").lower()
    año_maximo = pd.to_datetime(mes_maximo).year
    año_minimo = pd.to_datetime(mes_primero).year

    proveedor_max_acumulado = datos_acmulados.loc[datos_acmulados['faltantes_acumulados_'].idxmax()]

    # CAMBIO: la mayor tasa solo entre proveedores con al menos 10 órdenes
    candidatos_tasa = datos_acmulados[datos_acmulados['total'] >= 10]
    proveedor_max_porcentaje = candidatos_tasa.loc[candidatos_tasa['porcentaje_incumplimiento'].idxmax()]

    # CAMBIO: recurrente = falló en el mes y en al menos 3 meses del período
    acumulados_recurrentes = datos_acmulados[datos_acmulados['meses_con_faltantes'] >= 3]
    recurrentes = sorted(set(df_top_cantidad_provedo['proveedor']) & set(acumulados_recurrentes['proveedor']))

    texto = []

    texto.append("")
    texto.append(f"MES EVALUADO: {mes_nombre_actual} del año {año_maximo}")

    if df_top_cantidad_provedo.empty:
        texto.append("Total de órdenes incumplidas en el mes: 0")   # CAMBIO
        texto.append("Ningún proveedor tuvo órdenes incumplidas en el mes.")

    else:
        df_top_cantidad = df_top_cantidad_provedo['proveedor'].iloc[0]   # CAMBIO: se movió aquí para que no falle si está vacío
        total_mes = int(df_top_cantidad_provedo['noCumpleCantidad'].sum())   # CAMBIO
        texto.append(f"Total de órdenes incumplidas en el mes: {total_mes}")   # CAMBIO
        texto.append(f"Proveedor con más órdenes incumplidas en el mes: {df_top_cantidad}")
        texto.append("")
        texto.append("PROVEEDORES CON ÓRDENES INCUMPLIDAS EN EL MES:")
        for _, r in df_top_cantidad_provedo.iterrows():
            texto.append(
                f"- Proveedor: {r['proveedor']} | "
                f"Órdenes incumplidas: {int(r['noCumpleCantidad'])} de {int(r['total'])} ({r['porcentaje_incumplimiento']}%)"
            )

    texto.append("")
    texto.append(f"PERÍODO ACUMULADO: {mes_nombre_primero} del {año_minimo} a {mes_nombre_actual} del {año_maximo}")
    texto.append(
        f"Proveedor con mayor volumen de incumplimiento acumulado: {proveedor_max_acumulado['proveedor']} | "
        f"Órdenes incumplidas: {int(proveedor_max_acumulado['faltantes_acumulados_'])} de {int(proveedor_max_acumulado['total'])} "   # CAMBIO: etiqueta
        f"({proveedor_max_acumulado['porcentaje_incumplimiento']}%) | "
        f"Meses con incumplimiento: {int(proveedor_max_acumulado['meses_con_faltantes'])} de {n_meses}"   # CAMBIO: formato
    )

    texto.append(
        f"Proveedor con mayor tasa de incumplimiento (mínimo 10 órdenes): {proveedor_max_porcentaje['proveedor']} | "   # CAMBIO
        f"Órdenes incumplidas: {int(proveedor_max_porcentaje['faltantes_acumulados_'])} de {int(proveedor_max_porcentaje['total'])} "   # CAMBIO: etiqueta
        f"({proveedor_max_porcentaje['porcentaje_incumplimiento']}%) | "
        f"Meses con incumplimiento: {int(proveedor_max_porcentaje['meses_con_faltantes'])} de {n_meses}"   # CAMBIO: formato
    )

    acumulados_recurrentes = datos_acmulados[datos_acmulados['meses_con_faltantes'] >= 2]
    recurrentes = acumulados_recurrentes[acumulados_recurrentes['proveedor'].isin(df_top_cantidad_provedo['proveedor'])]

    texto.append("PROVEEDORES QUE FALLARON EN EL MES Y TAMBIÉN EN MESES ANTERIORES:")
    if recurrentes.empty:
        texto.append("NINGUNO")
    else:
        for _, r in recurrentes.iterrows():
            texto.append(
                f"- {r['proveedor']} | Meses con incumplimiento: {int(r['meses_con_faltantes'])} de {n_meses} | "
                f"Órdenes incumplidas en el período: {int(r['faltantes_acumulados_'])} de {int(r['total'])} ({r['porcentaje_incumplimiento']}%)"
            )

    return "\n".join(texto)

def ejecucion_texto(datos=None):

    datos = obtener_data_set_cantidad()
    df_historicos_mes = datos_agrupados(datos)
    df_top_cantidad_provedo,acumuladores,fecha = top_cantidad_provedores(df_historicos_mes)
    texto=funcion_texto_cantidad(df_top_cantidad_provedo,acumuladores,fecha)

    return texto



# if __name__ == "__main__":
#     datos = obtener_data_set_cantidad()
#     df_historicos_mes = datos_historicos(datos_agrupados(datos))
#     print(df_historicos_mes)



if __name__ == "__main__":
    datos = obtener_data_set_cantidad()
    texto=ejecucion_texto(datos)

    print(texto)
    
 


