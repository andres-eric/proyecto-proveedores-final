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





def proveedores_recurrentes(df_mes, df_acum):
    """Proveedores que fallaron en el mes evaluado y también en meses anteriores (al menos 2 meses con faltantes).
    La usan el texto del análisis 3 y el gráfico del módulo 3, para que ambos marquen a los mismos proveedores."""
    rec = df_acum[(df_acum['meses_con_faltantes'] >= 2) & (df_acum['proveedor'].isin(df_mes['proveedor']))]
    return rec['proveedor'].tolist()


def variables_analisis_cantidad(df_mes, df_acum, fechas):

    mes_maximo = fechas[-2]
    mes_primero = fechas[0]
    n_meses = len(fechas) - 1
    mes_nombre = pd.to_datetime(mes_maximo).month_name(locale="es_ES").lower()
    mes_nombre_inicio = pd.to_datetime(mes_primero).month_name(locale="es_ES").lower()

    v = {}

    # ---- Paso 1: el mes (Python decide cuál frase va) ----
    if df_mes.empty:
        v["frase_mes"] = f"Durante {mes_nombre} ningún proveedor registró órdenes cerradas con faltantes."
    else:
        primero = df_mes.iloc[0]
        resto = df_mes.iloc[1:]
        total_mes = int(df_mes['noCumpleCantidad'].sum())
        frase = (f"De las {total_mes} órdenes que cerraron con faltantes en {mes_nombre}, "
                 f"{primero['proveedor']} concentra {int(primero['noCumpleCantidad'])}")
        if not resto.empty:
            otros = ", ".join(f"{r['proveedor']} con {int(r['noCumpleCantidad'])}" for _, r in resto.iterrows())
            frase += f", mientras que el resto corresponde a {otros}"
        v["frase_mes"] = frase + "."

    # ---- Paso 2: el acumulado (siempre va, cada dato en su variable) ----
    acum = df_acum.loc[df_acum['faltantes_acumulados_'].idxmax()]
    v["proveedor_acumulado"] = acum['proveedor']
    v["incumplidas_acumulado"] = str(int(acum['faltantes_acumulados_']))
    v["total_acumulado"] = str(int(acum['total']))
    v["porcentaje_acumulado"] = str(acum['porcentaje_incumplimiento'])
    v["meses_acumulado"] = f"{int(acum['meses_con_faltantes'])} de {n_meses}"
    v["mes_nombre"] = mes_nombre
    v["mes_nombre_inicio"] = mes_nombre_inicio

    # ---- Paso 3: mayor tasa (solo si existe y es otro proveedor) ----
    candidatos = df_acum[df_acum['total'] >= 10]
    v["frase_tasa"] = ""
    if not candidatos.empty:
        tasa = candidatos.loc[candidatos['porcentaje_incumplimiento'].idxmax()]
        if tasa['proveedor'] != acum['proveedor']:
            v["frase_tasa"] = (f"Por su parte, {tasa['proveedor']} presenta la mayor tasa de incumplimiento del período, "
                               f"con {int(tasa['faltantes_acumulados_'])} de sus {int(tasa['total'])} órdenes "
                               f"cerradas con faltantes ({tasa['porcentaje_incumplimiento']}%).")

    # ---- Paso 4: recurrencia ----
    rec = df_acum[df_acum['proveedor'].isin(proveedores_recurrentes(df_mes, df_acum))]
    if rec.empty:
        v["frase_recurrencia"] = ("Ninguno de los proveedores con faltantes en el mes registra incumplimiento "
                                  "en meses anteriores, por lo que se trata de casos puntuales.")
    else:
        partes = [f"{r['proveedor']} ({int(r['meses_con_faltantes'])} de {n_meses} meses)" for _, r in rec.iterrows()]
        v["frase_recurrencia"] = (f"{', '.join(partes)} presenta un incumplimiento recurrente, al registrar "
                                  f"órdenes con faltantes en el mes evaluado y en meses anteriores del período.")

    return v


def ejecucion_variables():
    datos = obtener_data_set_cantidad()
    df_mes, df_acum, fechas = top_cantidad_provedores(datos_agrupados(datos))
    return variables_analisis_cantidad(df_mes, df_acum, fechas)


def datos_grafico_proveedores():
    """Datos para graficos.graficas_modulo3.graficar_modulo_3_proveedores (gráfico de la página 3.1 del PDF)."""
    datos = obtener_data_set_cantidad()
    df_mes, df_acum, fechas = top_cantidad_provedores(datos_agrupados(datos))

    fecha_fin = pd.to_datetime(fechas[-2])     # mes evaluado (el último mes es el que está en curso)
    fecha_ini = pd.to_datetime(fechas[0])
    mes_fin = fecha_fin.month_name(locale="es_ES").capitalize()
    mes_ini = fecha_ini.month_name(locale="es_ES").capitalize()

    if fecha_ini.year == fecha_fin.year:
        periodo_texto = f"{mes_ini} a {mes_fin} {fecha_fin.year}"
    else:
        periodo_texto = f"{mes_ini} {fecha_ini.year} a {mes_fin} {fecha_fin.year}"

    return {
        "top_mes": df_mes,
        "acumulados": df_acum,
        "recurrentes": proveedores_recurrentes(df_mes, df_acum),
        "n_meses": len(fechas) - 1,
        "mes_nombre": f"{mes_fin} {fecha_fin.year}",
        "periodo_texto": periodo_texto,
    }




# if __name__ == "__main__":
#     datos = obtener_data_set_cantidad()
#     df_historicos_mes = datos_historicos(datos_agrupados(datos))
#     print(df_historicos_mes)



if __name__ == "__main__":
    variables = ejecucion_variables()
    for clave, valor in variables.items():
        print(f"{clave}: {valor}")

    


