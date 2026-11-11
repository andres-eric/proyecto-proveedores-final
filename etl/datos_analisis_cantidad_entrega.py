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




def funcion_texto_cantidad(df_top_cantidad_provedo,datos_acmulados,fechas):

    mes_maximo=fechas[-2]
    mes_primero=fechas[0]
    df_top_cantidad=df_top_cantidad_provedo['proveedor'].head(1)

    texto=[]

    texto.append(f"MES EVALUADO: {mes_maximo}")

    if df_top_cantidad_provedo.empty:
        texto.append("Ningún proveedor tuvo órdenes incumplidas en el mes.")
    else:
        texto.append(f"Proveedor con más órdenes incumplidas en el mes: {df_top_cantidad}")
        texto.append("PROVEEDORES CON ÓRDENES INCUMPLIDAS EN EL MES:")
        for _, r in df_top_cantidad_provedo.iterrows():
            texto.append(
                f"- Proveedor: {r['proveedor']} | "
                f"Órdenes incumplidas: {int(r['noCumpleCantidad'])} de {int(r['total'])} ({r['porcentaje_incumplimiento']}%)"
            )
  

    texto.append("")
    texto.append(f"PERÍODO ACUMULADO: {mes_inicio} a {mes_nombre} ({n_meses} meses)")
    texto.append(f"Total de órdenes incumplidas en el período: {total_incumplidas_periodo}")
    texto.append(f"Proveedor con mayor volumen de incumplimiento acumulado: {acum.iloc[0]['proveedor']}")


    return "\n".join(texto)


# if __name__ == "__main__":
#     datos = obtener_data_set_cantidad()
#     df_historicos_mes = datos_historicos(datos_agrupados(datos))
#     print(df_historicos_mes)



if __name__ == "__main__":
    datos = obtener_data_set_cantidad()
    df_historicos_mes = datos_agrupados(datos)
    df_top_cantidad_provedo,acumuladores,fecha = top_cantidad_provedores(df_historicos_mes)
    mex_1=funcion_texto_cantidad(df_top_cantidad_provedo,fecha)
    print(mex_1)  
    
 


