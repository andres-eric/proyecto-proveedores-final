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

    datos_resumen_cantidad=datos_cantidad[['anio-mes','proveedor','cantidadIncumplimiento','cantidadCumpleCantidad','totalOrdenesCantidad']]
    cantiadad_provedores=datos_cantidad['proveedor'].nunique()


    return datos_resumen_cantidad






if __name__ == "__main__":
    datos = obtener_data_set_cantidad()
    df_historicos = datos_historicos(datos)
    print(df_historicos)



