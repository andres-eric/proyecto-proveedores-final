import requests
import pandas as pd
import time



def realizar_peticion(url_api,max_intento=6,diley=5, timeout_sec=60):

    intentos=0
    #bandera=True
    while intentos < max_intento:
        intentos+=1
        try:
            respuesta=requests.get(url_api, timeout=timeout_sec)
            if respuesta.status_code == 200:
                print(f"intento numero {intentos}")
                return respuesta.json(),intentos
            else:
                print(f"intento fallido {intentos} de {max_intento}: respuesta {respuesta.status_code} ")
        except Exception as e:
            print(f"intento fallido {intentos} de {max_intento}: fallo por excepcion {e} ")

        time.sleep(diley)
        
    print("Se alcanzaron los intentos maximos.")
    return None, intentos
        



def obtener_datos_kpi():
    """Extrae los datos de KPI de la API y realiza la limpieza inicial."""
    #url_api = "http://localhost:8085/api/v1/extractor/consulta"
    #url_api = "http://host.docker.internal:8080/api/v1/extractor/consulta"
    #url_api="http://localhost:8085/api/v1/extractor/consulta"
    url_api="http://192.168.6.105:9091/api/v1/extractor/consulta"

    datos_proveedores,i_tentos=realizar_peticion(url_api)
    if datos_proveedores is not None:
        print(f"Datos de KPI cargados correctamente. {len(datos_proveedores)} registros.")
        #print(f"Intentos realizados para obtener datos de KPI: {intentos}")
        df = pd.DataFrame(datos_proveedores)
            # Limpieza y formateo
        df["anio-mes"] = pd.to_datetime(df["anio"].astype(str) + "-" + df["mes"].astype(str)).dt.strftime("%Y-%m")
        df = df[["proveedor","verde","amarilla","roja","negra","total","porcentajeCumplimientoVerde",
                     "nivelServicioTotal","cumplimientoCantidadEntregada","porcentajeCumplimientoPrimeraEntrega",
                     "anio-mes","cantidadIngresada"]]
        return df
    return None



def obtener_datos_kpi_detalle():
    """Extrae los datos de KPI de la API y realiza la limpieza inicial."""
    #url_api = "http://localhost:8085/api/v1/extractor/consulta"
    #url_api = "http://host.docker.internal:8080/api/v1/extractor/consulta"
    #url_api="http://localhost:8085/api/v1/extractor/consulta_det"
    url_api="http://192.168.6.105:9091/api/v1/extractor/consulta_det"



    datos_proveedores,i_tentos=realizar_peticion(url_api)
    if datos_proveedores is not None:
        print(f"Datos de KPI cargados correctamente. {len(datos_proveedores)} registros.")
        #print(f"Intentos realizados para obtener datos de KPI: {intentos}")
    
        df = pd.DataFrame(datos_proveedores)

        df["anio-mes"] = pd.to_datetime(df["anio"].astype(str) + "-" + df["mes"].astype(str)).dt.strftime("%Y-%m")
        #df=df[["proveedor","anio-mes","ORDNUM_10","PRTNUM_10"]]
            
        return df
    return None



def obtener_datos_inspeccion():
    """Extrae los datos de inspección de la API y realiza la limpieza inicial."""
    #url_api = "http://localhost:8086/api/consultainspeccion/transformardata_table_f"
    #url_api = "http://192.168.6.105:8081/api/consultainspeccion/transformardata_table_f"
    url_api= "http://192.168.6.105:8086/api/consultainspeccion/transformardata_table_f"

    datos_proveedores, intentos = realizar_peticion(url_api)

    if datos_proveedores is not None:
        print(f"Datos de inspección cargados correctamente. {len(datos_proveedores)} registros.")          
        df = pd.DataFrame(datos_proveedores)
            
            # se filtra inspeccion nacional
        df = df[df["Nacion_importado"] == "nacional"]
        df["anio-mes"] = pd.to_datetime(df["Fecha_ingreso"]).dt.strftime("%Y-%m")
        df = df[["Nombre_Proveedor", "Nombre_Producto", "Cantidad_recivida", "anio-mes"]]
        return df
    return None




def obtener_datos_inspeccion_categoria():
    """Extrae los datos de inspección de la API y realiza la limpieza inicial."""
    #url_api = "http://localhost:8086/api/consultainspeccion/transformardata_table_f"
    #url_api = "http://192.168.6.105:8081/api/consultainspeccion/transformardata_table_f"
    url_api= "http://192.168.6.105:8086/api/consultainspeccion/transformardata_table_f"
    #url_api_categoria="http://localhost:8085/api/v1/extractor/consulta_categorias"
    url_api_categoria="http://192.168.6.105:9091/api/v1/extractor/consulta_categorias"


    datos_proveedores, intentos = realizar_peticion(url_api)
    datos_categoria, intentos_categoria = realizar_peticion(url_api_categoria)

    if datos_proveedores is not None:
        print(f"Datos de inspección cargados correctamente. {len(datos_proveedores)} registros.")          
        df = pd.DataFrame(datos_proveedores)
        df_categoria = pd.DataFrame(datos_categoria)
            
            # Limpieza y formateo
        df = df[df["Nacion_importado"] == "nacional"]
        df["anio-mes"] = pd.to_datetime(df["Fecha_ingreso"]).dt.strftime("%Y-%m")
        df = df[["Nombre_Proveedor", "ID_Producto","Nombre_Producto", "Cantidad_recivida", "anio-mes"]]

        df_f=df.merge(df_categoria, left_on="ID_Producto", right_on="PRTNUM_01", how="left")

        df_f=df_f[["Nombre_Proveedor","anio-mes", "ID_Producto","Nombre_Producto","categoria", "Cantidad_recivida"]]

    

        return df_f
    return None



def obtener_datos_completos():
    """Une los datos de KPI y los datos de inspección en un solo DataFrame."""
    df_inspeccion = obtener_datos_inspeccion()
    df_kpi = obtener_datos_kpi()

    if df_inspeccion is None or df_kpi is None:
        print("No se pudieron obtener los datos base. Verifica las APIs.")
        return None

    df_resumen = (
        df_inspeccion.groupby(["Nombre_Proveedor", "anio-mes"])["Cantidad_recivida"]
        .sum().reset_index()
    )

    df_total = pd.merge(
        df_kpi,
        df_resumen,
        left_on=["proveedor", "anio-mes"],
        right_on=["Nombre_Proveedor", "anio-mes"],
        how="left"
    )

    columnas_finales = [
        'proveedor', 'anio-mes', 'verde', 'amarilla', 'roja', 'negra', 'total', 
        'porcentajeCumplimientoVerde', 'cumplimientoCantidadEntregada', 
        'porcentajeCumplimientoPrimeraEntrega', 'Cantidad_recivida', 
        'nivelServicioTotal', 'cantidadIngresada'
    ]
    df_total_ = df_total[columnas_finales].copy()
    
    df_total_["Cantidad_recivida"] = df_total_["Cantidad_recivida"].fillna(0)
    
    df_total_ = df_total_.rename(
        columns={
            "Cantidad_recivida": "cantidad_recibida_defectuosa",
            "cantidadIngresada": "cantidad_ingresada",
        }
    )

    df_total_= df_total_.sort_values(by=['proveedor','anio-mes'], ascending=[True, True])
    return df_total_



def dataframe_a_markdown(df):
    """Convierte el DataFrame final a un formato Markdown para dárselo al LLM."""
    if df is not None and not df.empty:
        return df.to_markdown(index=False)
    return "No hay datos disponibles."



def obtener_data_set_categoria():
    #url_api="http://localhost:8085/api/v1/extractor/consulta_categorias"
    url_api="http://192.168.6.105:9091/api/v1/extractor/consulta_categorias"
    
    datos_proveedores,intentos=realizar_peticion(url_api)
    if datos_proveedores is not None:
        print(f"Datos de categoria cargados correctamente. {len(datos_proveedores)} registros.")
        df=pd.DataFrame(datos_proveedores)
        return df
    return None


def obtener_data_set_cantidad():
    #url_api="http://localhost:8085/api/v1/extractor/consulta_categorias"
    url_api="http://192.168.6.105:9091/api/v1/extractor/consulta_cantidad"
    
    datos_proveedores,intentos=realizar_peticion(url_api)
    if datos_proveedores is not None:
        print(f"Datos de cantidad cargados correctamente. {len(datos_proveedores)} registros.")
        df=pd.DataFrame(datos_proveedores)
        return df
    return None



if __name__ == "__main__":
    # Prueba rápida
    datos = obtener_data_set_cantidad()
    if datos is not None:
        print("\nMuestra de los datos obtenidos:")
   # print(datos.head())
    print("cantidad", datos.columns)

