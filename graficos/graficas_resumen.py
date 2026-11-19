import os
import sys
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.colors import ListedColormap, BoundaryNorm
from adjustText import adjust_text
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from graficos.rutas_graficas import ruta_grafica, CARPETA_GRAFICAS
from graficos.tema import aplicar_tema, tamano_una_columna, leyenda_inferior, guardar
from pdf_generator import estilos as E

from etl.datos_analisis_resumen_general import ( datos_historicos )
from datos.carga_datos import ( obtener_datos_completos )
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import FancyBboxPatch





def generar_imagen_tarjetas_kpi_desde_df(df_kpis: pd.DataFrame, ruta_salida: str = ruta_grafica("tarjetas_ejecutivas.png")) -> str:
    """
    Genera la imagen de tarjetas KPI ejecutivas directamente desde el DataFrame.
    """
    aplicar_tema()
    actual = df_kpis.iloc[0]
    anterior = df_kpis.iloc[1]

    # KPI 1: Cumplimiento
    val_cumplimiento = f"{actual['tasa_cumpli_perfecto']:.1f}%"
    delta_cumplimiento_val = actual['tasa_cumpli_perfecto'] - anterior['tasa_cumpli_perfecto']
    signo_c = "+" if delta_cumplimiento_val > 0 else ""
    delta_cumplimiento_txt = f"{signo_c}{delta_cumplimiento_val:.1f} pp vs mes anterior"
    #interp_cumplimiento = "Incremento en entregas a tiempo" if delta_cumplimiento_val >= 0 else "Deterioro en puntualidad"
    color_delta_c = E.VARIACION_FAVORABLE if delta_cumplimiento_val >= 0 else E.VARIACION_DESFAVORABLE

    # KPI 2: Riesgo Crítico
    val_riesgo = f"{actual['tasa_riesgo_critico']:.1f}%"
    delta_riesgo_val = actual['tasa_riesgo_critico'] - anterior['tasa_riesgo_critico']
    signo_r = "+" if delta_riesgo_val > 0 else ""
    delta_riesgo_txt = f"{signo_r}{delta_riesgo_val:.1f}  vs mes anterior"
    #interp_riesgo = "Reducción de riesgo critico" if delta_riesgo_val <= 0 else "Alerta: Incremento de riesgo"
    color_delta_r = E.VARIACION_FAVORABLE if delta_riesgo_val <= 0 else E.VARIACION_DESFAVORABLE


    unidades_defectuosa = "Unidades defectuosas"

    # KPI 3: Cantidad Ingresada (Solo la cantidad)
    val_cantidad = f"{int(actual['cantidad_recibida_defectuosa']):,}".replace(",", ".")

    # Crear la figura con un tamaño más cuadrado para acomodar 2 filas
    fig = plt.figure(figsize=(7.5, 5.5), facecolor=E.BLANCO)
    
    # Posicionar las 3 tarjetas: 2 arriba y 1 abajo al centro
    ax1 = fig.add_axes([0.05, 0.55, 0.42, 0.40]) # Arriba izquierda
    ax2 = fig.add_axes([0.53, 0.55, 0.42, 0.40]) # Arriba derecha
    ax3 = fig.add_axes([0.29, 0.05, 0.42, 0.40]) # Abajo centro

    def dibujar_tarjeta(ax, titulo, valor, delta_txt=None, interp=None, color_delta=E.TEXTO_SECUNDARIO):
        ax.axis('off')
        
        # Tarjeta con esquinas redondeadas usando FancyBboxPatch
        card = FancyBboxPatch(
            (0.02, 0.02), 0.96, 0.96,
            boxstyle="round,pad=0.03,rounding_size=0.08",
            transform=ax.transAxes,
            facecolor=E.BLANCO,
            edgecolor='none',
            linewidth=0
        )
        ax.add_patch(card)

        # Ajuste de fuentes para enfocarnos en el porcentaje de variación
        ax.text(0.5, 0.78, titulo, fontsize=12, fontweight='bold', color=E.TEXTO_SECUNDARIO, ha='center', va='center')

        if delta_txt or interp:
            ax.text(0.5, 0.52, valor, fontsize=28, fontweight='heavy', color=E.AZUL_CORPORATIVO, ha='center', va='center')
            if delta_txt:
                # Variación super grande
                ax.text(0.5, 0.25, delta_txt, fontsize=16, fontweight='bold', color=color_delta, ha='center', va='center')
            if interp:
                ax.text(0.5, 0.10, interp, fontsize=10, color=E.TEXTO_SECUNDARIO, ha='center', va='center', style='italic')
        else:
            ax.text(0.5, 0.40, valor, fontsize=32, fontweight='heavy', color=E.AZUL_CORPORATIVO, ha='center', va='center')

    dibujar_tarjeta(ax1, "CUMPLIMIENTO ", val_cumplimiento, delta_cumplimiento_txt, "", color_delta_c)
    dibujar_tarjeta(ax2, "RIESGO CRÍTICO", val_riesgo, delta_riesgo_txt, '', color_delta_r)
    dibujar_tarjeta(ax3, "CANTIDAD DEFECTUOSA", val_cantidad,unidades_defectuosa)  # Tarjeta mostrando solo la cantidad

    plt.tight_layout()
    plt.savefig(ruta_salida, dpi=300, bbox_inches='tight')
    plt.close()

    return ruta_salida


def generar_tarjetas_individuales(df_kpis: pd.DataFrame, dir_salida: str = str(CARPETA_GRAFICAS)) -> list:
    """
    Genera 3 imágenes individuales para cada tarjeta KPI.
    Retorna lista de rutas de los archivos PNG.
    """
    import os
    aplicar_tema()
    actual = df_kpis.iloc[0]
    anterior = df_kpis.iloc[1]

    rutas = []

    def dibujar_tarjeta_individual(titulo, valor, delta_txt=None, interp=None, color_delta=E.TEXTO_SECUNDARIO, nombre_archivo="kpi.png"):
        fig, ax = plt.subplots(figsize=(3.5, 3.2), facecolor=E.BLANCO)
        ax.axis('off')
        
        card = FancyBboxPatch(
            (0.02, 0.02), 0.96, 0.96,
            boxstyle="round,pad=0.03,rounding_size=0.08",
            transform=ax.transAxes,
            facecolor=E.BLANCO,
            edgecolor='none',
            linewidth=0
        )
        ax.add_patch(card)

        ax.text(0.5, 0.78, titulo, fontsize=12, fontweight='bold', color=E.TEXTO_SECUNDARIO, ha='center', va='center')

        if delta_txt or interp:
            ax.text(0.5, 0.48, valor, fontsize=32, fontweight='heavy', color=E.AZUL_CORPORATIVO, ha='center', va='center')
            if delta_txt:
                ax.text(0.5, 0.22, delta_txt, fontsize=10, fontweight='bold', color=color_delta, ha='center', va='center')
            if interp:
                ax.text(0.5, 0.10, interp, fontsize=8.5, color=E.TEXTO_SECUNDARIO, ha='center', va='center', style='italic')
        else:
            ax.text(0.5, 0.40, valor, fontsize=36, fontweight='heavy', color=E.AZUL_CORPORATIVO, ha='center', va='center')

        plt.tight_layout()
        ruta = os.path.join(dir_salida, nombre_archivo)
        plt.savefig(ruta, dpi=300, bbox_inches='tight')
        plt.close()
        return ruta

    val_cumplimiento = f"{actual['tasa_cumpli_perfecto']:.1f}%"
    delta_cumplimiento_val = actual['tasa_cumpli_perfecto'] - anterior['tasa_cumpli_perfecto']
    signo_c = "+" if delta_cumplimiento_val > 0 else ""
    delta_cumplimiento_txt = f"{signo_c}{delta_cumplimiento_val:.1f} pp vs mes anterior"
    #interp_cumplimiento = "Incremento en entregas a tiempo" if delta_cumplimiento_val >= 0 else "Deterioro en puntualidad"
    color_delta_c = E.VARIACION_FAVORABLE if delta_cumplimiento_val >= 0 else E.VARIACION_DESFAVORABLE
    
    rutas.append(dibujar_tarjeta_individual("CUMPLIMIENTO", val_cumplimiento, delta_cumplimiento_txt, "", color_delta_c, "kpi_cumplimiento.png"))

    val_riesgo = f"{actual['tasa_riesgo_critico']:.1f}%"
    delta_riesgo_val = actual['tasa_riesgo_critico'] - anterior['tasa_riesgo_critico']
    signo_r = "+" if delta_riesgo_val > 0 else ""
    delta_riesgo_txt = f"{signo_r}{delta_riesgo_val:.1f} vs mes anterior"
    interp_riesgo = "Reducción de riesgo critico" if delta_riesgo_val <= 0 else "Alerta: Incremento de riesgo"
    color_delta_r = E.VARIACION_FAVORABLE if delta_riesgo_val <= 0 else E.VARIACION_DESFAVORABLE

    rutas.append(dibujar_tarjeta_individual("RIESGO CRÍTICO", val_riesgo, delta_riesgo_txt, interp_riesgo, color_delta_r, "kpi_riesgo.png"))

    val_cantidad = f"{int(actual['cantidad_recibida_defectuosa']):,}".replace(",", ".")
    unidades_defectuosa = "Unidades defectuosas"
    
    rutas.append(dibujar_tarjeta_individual("CANTIDAD DEFECTUOSA", val_cantidad, interp=unidades_defectuosa, nombre_archivo="kpi_defectos.png"))

    return rutas



def graficar_distribucion_volumen_mes(df_kpis,ruta_salida: str = ruta_grafica("volumen_total_mes.png")) -> str:
    """
    Genera un gráfico de barras apiladas al 100% que muestra la distribución mensual 
    de los estados de entrega (Óptimo, Riesgo, Retraso Severo, Incumplimiento) 
    a lo largo de los meses históricos evaluados.
    Retorna la ruta del archivo PNG generado.
    """

    aplicar_tema()
    df = df_kpis.sort_values(by="anio-mes", ascending=True).copy()


    meses = df['anio-mes'].astype(str).tolist()

    fig, ax = plt.subplots(figsize=tamano_una_columna(), layout="constrained")

    ancho_barra = 0.52
    # (columna, leyenda, color del segmento, color del texto o None si no lleva etiqueta), de abajo hacia arriba
    segmentos = [
        ('Cumplimiento_optimo', "Óptimo", E.SEMAFORO_OPTIMO, E.BLANCO),
        ('Riesgo_de_Retraso', "Riesgo de retraso", E.SEMAFORO_RIESGO, E.AZUL_CORPORATIVO),
        ('Incumplimiento_de_Plazo', "Incumplimiento de plazo", E.SEMAFORO_INCUMPLIMIENTO, E.BLANCO),
        ('Retraso_Severo', "Retraso severo", E.SEMAFORO_SEVERO, E.BLANCO),
        ('sin_clasificar', "Sin clasificar", E.SIN_CLASIFICAR, None),
    ]

    base = pd.Series(0.0, index=df.index)
    handles, nombres = [], []
    for columna, etiqueta, color, color_texto in segmentos:
        pct = (df[columna] / df['total']) * 100
        barras = ax.bar(meses, pct, bottom=base, width=ancho_barra, label=etiqueta,
                        color=color, edgecolor="white", linewidth=0.6)
        if color_texto is not None:
            etiquetas = [f"{v:.1f}%" if v >= 4 else "" for v in pct]
            ax.bar_label(barras, labels=etiquetas, label_type="center", fontsize=E.TAM_GRAFICA - 1,
                         color=color_texto, fontweight="bold")
            handles.append(barras)      # "Sin clasificar" queda fuera de la leyenda
            nombres.append(etiqueta)
        base = base + pct

    ax.set_ylim(0, 100)
    ax.set_yticks([])
    # El título de la figura va en el PDF (formato APA), no dentro de la imagen.
    ax.tick_params(axis="x", length=0, pad=4)
    ax.spines["left"].set_visible(False)
    leyenda_inferior(fig, handles=handles, labels=nombres, ncol=4)

    return guardar(fig, ruta_salida)


if __name__ == "__main__":
    datos = obtener_datos_completos()
    datos_h = datos_historicos(datos)
  
    img_tarjetas = generar_imagen_tarjetas_kpi_desde_df(datos_h)
    img_volumen = graficar_distribucion_volumen_mes(datos_h)
  
    print("Tarjetas generadas en:", img_tarjetas)
    print("Gráfico de volumen generado en:", img_volumen)