import os
import sys
from pathlib import Path
import pandas as pd

# Definir la ruta raíz del proyecto
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from datos.carga_datos import (
    obtener_datos_kpi,
    obtener_datos_kpi_detalle,
    obtener_datos_inspeccion,
    obtener_datos_completos,
    obtener_datos_inspeccion_categoria,
    
    

)
from etl.datos_analisis_resumen_general import datos_historicos
from etl.datos_detalles import (
    datos_detalles,
    cantidad_con_riesgo,
    porcentaje_retrasos,
    datos_modulo_2
    
)

# Directorio de salida para todos los archivos Excel
CARPETA_SALIDA = ROOT_DIR / "archivos_excel"


def exportar_todos_los_datasets():
  

    # Crear carpeta de destino si no existe
    CARPETA_SALIDA.mkdir(parents=True, exist_ok=True)


    archivos_generados = []
    dict_consolidado = {}

    # 1. Obtener Datos Completos (Base Principal)

    df_completos = obtener_datos_completos()
    if df_completos is not None and not df_completos.empty:
        ruta = CARPETA_SALIDA / "datos_completos.xlsx"
        df_completos.to_excel(ruta, index=False)
   
        archivos_generados.append(ruta)
        dict_consolidado["Datos Completos"] = df_completos
    else:
        print("   └─ [!] No se pudieron obtener los datos completos.")

    # 2. Datos Históricos
    
    if df_completos is not None and not df_completos.empty:
        df_historicos = datos_historicos(df_completos)
        ruta = CARPETA_SALIDA / "datos_historicos.xlsx"
        df_historicos.to_excel(ruta, index=False)

        archivos_generados.append(ruta)
        dict_consolidado["Datos Históricos"] = df_historicos
    else:
        print("   └─ [!] Omitido datos históricos por falta de datos base.")

    # 3. KPI Detalle
  
    df_kpi_det = obtener_datos_kpi_detalle()
    if df_kpi_det is not None and not df_kpi_det.empty:
        ruta = CARPETA_SALIDA / "datos_kpi_detalle.xlsx"
        df_kpi_det.to_excel(ruta, index=False)

        archivos_generados.append(ruta)
        dict_consolidado["KPI Detalle"] = df_kpi_det
    else:
        print("   └─ [!] No se pudieron obtener los datos de KPI detalle.")

    # 4. Datos Resumen KPI Base
  
    df_kpi = obtener_datos_kpi()
    if df_kpi is not None and not df_kpi.empty:
        ruta = CARPETA_SALIDA / "datos_kpi_resumen.xlsx"
        df_kpi.to_excel(ruta, index=False)
        archivos_generados.append(ruta)
        dict_consolidado["KPI Resumen"] = df_kpi

    # 5. Datos de Inspección
    
    df_insp = obtener_datos_inspeccion()
    if df_insp is not None and not df_insp.empty:
        ruta = CARPETA_SALIDA / "datos_inspeccion.xlsx"
        df_insp.to_excel(ruta, index=False)
        
        archivos_generados.append(ruta)
        dict_consolidado["Inspección"] = df_insp



    

    # 6. Fallas y Riesgos por Proveedor (Calidad y Logística)

    if df_completos is not None and not df_completos.empty:
        try:
            df_cantidades_riesgo = cantidad_con_riesgo(df_completos)
            if df_cantidades_riesgo is not None and not df_cantidades_riesgo.empty:
                ruta_cant = CARPETA_SALIDA / "datos_fallas_proveedores_mes.xlsx"
                df_cantidades_riesgo.to_excel(ruta_cant, index=False)
              
                archivos_generados.append(ruta_cant)
                dict_consolidado["Fallas Proveedor Mes"] = df_cantidades_riesgo

                df_pct_retrasos = porcentaje_retrasos(df_cantidades_riesgo)
                ruta_retrasos = CARPETA_SALIDA / "resumen_acumulado_fallas.xlsx"
                df_pct_retrasos.to_excel(ruta_retrasos)
  
                archivos_generados.append(ruta_retrasos)
                dict_consolidado["Acumulado Fallas"] = df_pct_retrasos
        except Exception as e:
            print(f"   └─ [!] Error al calcular datos de riesgo/fallas: {e}")


    
    df_inspeccion_categoria=obtener_datos_inspeccion_categoria()
    if df_inspeccion_categoria is not None and not df_inspeccion_categoria.empty:
        ruta = CARPETA_SALIDA / "datos_inspeccion_categoria.xlsx"
        df_inspeccion_categoria.to_excel(ruta, index=False)
        
        archivos_generados.append(ruta)
        dict_consolidado["Inspección Categoria"] = df_inspeccion_categoria




    # 7. Datos Detalles por Proveedor
    if df_kpi_det is not None and not df_kpi_det.empty:
        try:
            datos_2 = datos_detalles(df_kpi_det)
            ruta = CARPETA_SALIDA / "datos_detalles.xlsx"
            datos_2.to_excel(ruta, index=False)
            archivos_generados.append(ruta)
            dict_consolidado["datos_detalles"] = datos_2
        except Exception as e:
            print(f"   └─ [!] Error al calcular datos detalles: {e}")

    # 8. Crear Libro Consolidado (Todas las pestañas en un solo libro Excel)
    if dict_consolidado:
        ruta_consolidado = CARPETA_SALIDA / "reporte_consolidado_proveedores.xlsx"
    
        with pd.ExcelWriter(ruta_consolidado, engine="openpyxl") as writer:
            for nombre_hoja, df in dict_consolidado.items():
                # Nombre de pestaña limpio (máximo 31 caracteres)
                nombre_limpio = nombre_hoja[:31]
                df.to_excel(writer, sheet_name=nombre_limpio, index=(nombre_hoja == "Acumulado Fallas"))
       
        archivos_generados.append(ruta_consolidado)


    df_datos_modulo_2=datos_modulo_2(obtener_datos_kpi_detalle(),obtener_datos_inspeccion_categoria())    
    if df_datos_modulo_2 is not None and not df_datos_modulo_2.empty:
        ruta = CARPETA_SALIDA / "datos_modulo_2.xlsx"
        df_datos_modulo_2.to_excel(ruta, index=False)
        
        archivos_generados.append(ruta)
        dict_consolidado["datos_modulo_2"] = df_datos_modulo_2



    print("\n" + "=" * 60)
    print(f"PROCESO FINALIZADO. Se generaron {len(archivos_generados)} archivos en:")
    print(f"{CARPETA_SALIDA}")
    print("=" * 60)


if __name__ == "__main__":
    exportar_todos_los_datasets()
