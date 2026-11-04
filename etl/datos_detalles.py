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
from herramientas.funciones import fecha_anterior
from datos.carga_datos import obtener_datos_inspeccion
from datos.carga_datos import obtener_datos_inspeccion_categoria
from datos.carga_datos import obtener_data_set_categoria


# datos = obtener_datos_kpi_detalle()
# datos_completos=obtener_datos_completos()
# datos_inspeccion=obtener_datos_inspeccion()
# datos_completos_inspeccion=obtener_datos_inspeccion_categoria()




# if datos_completos is None:
#     raise RuntimeError("No se pudieron cargar los datos. Verifica que la API en 192.168.6.105:8090 esté disponible.")


def cambiar_nombre_head(df):

    datos_resumen_1 = df.rename(columns={
        "verde": "Cumplimiento_optimo",
        "negra": "Retraso_Severo",
        "amarilla": "Riesgo_de_Retraso",
        "roja": "Incumplimiento_de_Plazo"

    })[1:].reset_index(drop=True)
    return datos_resumen_1



# aca se utiliza datos obtenidos de obtener_datos_kpi_detalle()
def datos_detalles(datos=None):

    datos_resumen=pd.DataFrame(datos)
    datos_resumen=datos_resumen[['anio-mes','proveedor','CANTIDAD_INGRESADA','ZONA_NEGRA','ZONA_ROJA','categoria']]
    datos_resumen['cantidad_Riesgo'] = np.where((datos_resumen['ZONA_ROJA']== 1) | (datos_resumen['ZONA_NEGRA']==1), datos_resumen['CANTIDAD_INGRESADA'], 0)
    datos_resumen['categoria']= np.where (datos_resumen['cantidad_Riesgo']>0, datos_resumen['categoria'], None)
    conteo_categorias = (
        datos_resumen.dropna(subset=['categoria'])
        .groupby(['anio-mes', 'proveedor', 'categoria'])
        .agg(conteo=('categoria', 'count'),
        suma_cantidades=('cantidad_Riesgo', 'sum'))
    ).reset_index()
    categoria_mas_frecuente= conteo_categorias.sort_values(by=['conteo','suma_cantidades'],ascending=[False,False]).drop_duplicates(subset=['anio-mes','proveedor'], keep='first').reset_index(drop=True)
   
    return categoria_mas_frecuente





def datos_modulo_2(datos_detalle=None, datos_inspeccion=None):

    fecha_anterior_val=fecha_anterior(datos_detalle)

    datos_detalle=pd.DataFrame(datos_detalle)
    datos_detalle=datos_detalle[datos_detalle['anio-mes']==fecha_anterior_val].reset_index(drop=True)
    datos_inspeccion=pd.DataFrame(datos_inspeccion)
    datos_detalle['proveedor'] = datos_detalle['proveedor'].astype(str).str.strip().str.upper()
    
    datos_detalle=datos_detalle[['anio-mes','proveedor','CANTIDAD_INGRESADA','ZONA_NEGRA','ZONA_ROJA','categoria']]
    datos_detalle['cantidad_Riesgo'] = np.where((datos_detalle['ZONA_ROJA']== 1) | (datos_detalle['ZONA_NEGRA']==1), datos_detalle['CANTIDAD_INGRESADA'], 0)
    datos_detalle['categoria']= np.where (datos_detalle['cantidad_Riesgo']>0, datos_detalle['categoria'], None)
    conteo_categorias = (
        datos_detalle.dropna(subset=['categoria'])
        .groupby(['anio-mes', 'proveedor', 'categoria'])
        .agg(conteo=('categoria', 'count'),
        suma_cantidades=('cantidad_Riesgo', 'sum'))
    ).reset_index()

    categoria_mas_frecuente= conteo_categorias.sort_values(by=['conteo','suma_cantidades'],ascending=[False,False]).drop_duplicates(subset=['anio-mes','proveedor'], keep='first').reset_index(drop=True)
    categoria_mas_frecuente=categoria_mas_frecuente.sort_values(by=['proveedor'],ascending=[True]).reset_index(drop=True)
    categoria_mas_frecuente=categoria_mas_frecuente[['anio-mes','proveedor','categoria','suma_cantidades']]
    categoria_mas_frecuente=categoria_mas_frecuente.nlargest(7, 'suma_cantidades').reset_index(drop=True)

    datos_inspeccion=datos_inspeccion[datos_inspeccion['anio-mes']==fecha_anterior_val].reset_index(drop=True)
    datos_inspeccion['Nombre_Proveedor'] = datos_inspeccion['Nombre_Proveedor'].astype(str).str.strip().str.upper()
    datos_inspeccion= datos_inspeccion[['Nombre_Proveedor','anio-mes','categoria','Cantidad_recivida']]
    datos_inspeccion_1 = datos_inspeccion.groupby(['anio-mes', 'Nombre_Proveedor','categoria']).agg(cantidad_recivida=('Cantidad_recivida', 'sum')).reset_index()
    inspeccion_frecuente= datos_inspeccion_1.sort_values(by=['cantidad_recivida'],ascending=[False]).drop_duplicates(subset=['anio-mes','Nombre_Proveedor'], keep='first').reset_index(drop=True)
    inspeccion_frecuente=inspeccion_frecuente.nlargest(7, 'cantidad_recivida').reset_index(drop=True)

    data_set_total = categoria_mas_frecuente.merge(
    inspeccion_frecuente,
    left_on=['anio-mes', 'proveedor'],
    right_on=['anio-mes', 'Nombre_Proveedor'],
    how='left'
)
    data_set_total=data_set_total[['anio-mes','proveedor','categoria_x','suma_cantidades','cantidad_recivida']]
    data_set_total.fillna(value={"cantidad_recivida": 0}, inplace=True)
    data_set_total['impacto_total']=data_set_total['suma_cantidades']+data_set_total['cantidad_recivida']
    data_set_total=data_set_total[data_set_total['impacto_total']>0]
    data_set_total=data_set_total.sort_values(by=['cantidad_recivida'],ascending=[False]).reset_index(drop=True)

    return inspeccion_frecuente,categoria_mas_frecuente





def convertir_df_a_contexto_llm(datos_mod2_detalles) -> str:
    """
    Función auxiliar: Convierte el DataFrame de Pandas en un texto estructurado
    para que el LLM lo entienda sin gastar tokens innecesarios ni alucinar.
    Soporta tanto el DataFrame de logística ('suma_cantidades' / 'proveedor')
    como el de calidad ('cantidad_recivida' / 'Nombre_Proveedor').
    """
    if datos_mod2_detalles is None or datos_mod2_detalles.empty:
        return "No hay datos críticos registrados."
    col_prov = 'proveedor' if 'proveedor' in datos_mod2_detalles.columns else 'Nombre_Proveedor'
    col_unidades = None
    for cand in ['suma_cantidades', 'cantidad_recivida', 'Cantidad_recivida', 'cantidad']:
        if cand in datos_mod2_detalles.columns:
            col_unidades = cand
            break

    texto = ""
    for _, row in datos_mod2_detalles.iterrows():
        prov = str(row[col_prov]).strip() if col_prov in row else "Proveedor no especificado"
        cat_cruda = str(row['categoria']).strip() if 'categoria' in row else ""
        if pd.isna(row.get('categoria')) or cat_cruda.upper() in ["SIN CATEGORIA", "SIN CATEGORÍA", "OTROS", "", "NAN", "NONE"]:
            cat = "Material no especificado"
        else:
            cat = cat_cruda
        val_unidades = row[col_unidades] if col_unidades and pd.notna(row[col_unidades]) else 0
        unidades = f"{int(val_unidades):,}".replace(",", ".") 
        texto += f"- Proveedor: {prov} | Unidades: {unidades} | Categoría: {cat}\n"     
    return texto



def cantidad_con_riesgo(datos=None):

    datos_resumen=pd.DataFrame(datos)
    fecha_anterior_val=fecha_anterior(datos_resumen)
    datos_resumen=datos_resumen[datos_resumen['anio-mes']==fecha_anterior_val]
    datos_resumen=datos_resumen[['anio-mes','proveedor','cantidad_ingresada','cantidad_recibida_defectuosa','verde','amarilla','roja','negra','total','nivelServicioTotal']]
    datos_resumen['cantidad_Riesgo_logistico'] = np.where((datos_resumen['roja']== 1) | (datos_resumen['negra']==1), datos_resumen['cantidad_ingresada'], 0)
    datos_resumen['flag_falla_logistica'] = np.where(datos_resumen['cantidad_Riesgo_logistico'] > datos_resumen['cantidad_recibida_defectuosa'], 1, 0)
    datos_resumen['flag_falla_calidad'] = np.where(datos_resumen['cantidad_recibida_defectuosa'] > datos_resumen['cantidad_Riesgo_logistico'], 1, 0)

    cantidades=datos_resumen.groupby(['anio-mes','proveedor']).agg({
        'cantidad_ingresada': 'sum',
        'cantidad_recibida_defectuosa': 'sum',
        'cantidad_Riesgo_logistico': 'sum',
        'flag_falla_logistica': 'sum',
        'flag_falla_calidad': 'sum'

    }).reset_index()
    return datos_resumen



def porcentaje_retrasos(datos):
    datos_resumen=pd.DataFrame(datos)
    conteo= datos_resumen['proveedor'].count()
    agrupar= datos_resumen.groupby(['proveedor']).agg({
        'flag_falla_logistica':'sum',
        'flag_falla_calidad':'sum'}
    )

    return agrupar




# inspeccion,categoria = datos_modulo_2(datos, datos_completos_inspeccion)



# print(convertir_df_a_contexto_llm(inspeccion))
# print(convertir_df_a_contexto_llm(categoria))



