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

from etl.datos_analisis_resumen_general import ( datos_historicos )
from datos.carga_datos import ( obtener_datos_completos )
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import FancyBboxPatch





def generar_imagen_tarjetas_kpi_desde_df(df_kpis: pd.DataFrame, ruta_salida: str = "tarjetas_ejecutivas.png") -> str:
    """
    Genera la imagen de tarjetas KPI ejecutivas directamente desde el DataFrame.
    """
    actual = df_kpis.iloc[0]
    anterior = df_kpis.iloc[1]

    # KPI 1: Cumplimiento
    val_cumplimiento = f"{actual['tasa_cumpli_perfecto']:.1f}%"
    delta_cumplimiento_val = actual['tasa_cumpli_perfecto'] - anterior['tasa_cumpli_perfecto']
    signo_c = "+" if delta_cumplimiento_val > 0 else ""
    delta_cumplimiento_txt = f"{signo_c}{delta_cumplimiento_val:.2f} pp vs mes anterior"
    #interp_cumplimiento = "Incremento en entregas a tiempo" if delta_cumplimiento_val >= 0 else "Deterioro en puntualidad"
    color_delta_c = '#2e7d32' if delta_cumplimiento_val >= 0 else '#c62828'

    # KPI 2: Riesgo Crítico
    val_riesgo = f"{actual['tasa_riesgo_critico']:.1f}%"
    delta_riesgo_val = actual['tasa_riesgo_critico'] - anterior['tasa_riesgo_critico']
    signo_r = "+" if delta_riesgo_val > 0 else ""
    delta_riesgo_txt = f"{signo_r}{delta_riesgo_val:.2f}  vs mes anterior"
    #interp_riesgo = "Reducción de riesgo critico" if delta_riesgo_val <= 0 else "Alerta: Incremento de riesgo"
    color_delta_r = '#2e7d32' if delta_riesgo_val <= 0 else '#c62828'


    unidades_defectuosa = "Unidades defectuosas"

    # KPI 3: Cantidad Ingresada (Solo la cantidad)
    val_cantidad = f"{int(actual['cantidad_recibida_defectuosa']):,}".replace(",", ".")

    # Crear la figura con un tamaño más cuadrado para acomodar 2 filas
    fig = plt.figure(figsize=(7.5, 5.5), facecolor='white')
    
    # Posicionar las 3 tarjetas: 2 arriba y 1 abajo al centro
    ax1 = fig.add_axes([0.05, 0.55, 0.42, 0.40]) # Arriba izquierda
    ax2 = fig.add_axes([0.53, 0.55, 0.42, 0.40]) # Arriba derecha
    ax3 = fig.add_axes([0.29, 0.05, 0.42, 0.40]) # Abajo centro

    def dibujar_tarjeta(ax, titulo, valor, delta_txt=None, interp=None, color_delta='#6c757d'):
        ax.axis('off')
        
        # Tarjeta con esquinas redondeadas usando FancyBboxPatch
        card = FancyBboxPatch(
            (0.02, 0.02), 0.96, 0.96,
            boxstyle="round,pad=0.03,rounding_size=0.08",
            transform=ax.transAxes,
            facecolor='white',
            edgecolor='none',
            linewidth=0
        )
        ax.add_patch(card)

        # Ajuste de fuentes para enfocarnos en el porcentaje de variación
        ax.text(0.5, 0.78, titulo, fontsize=12, fontweight='bold', color='#495057', ha='center', va='center')

        if delta_txt or interp:
            ax.text(0.5, 0.52, valor, fontsize=28, fontweight='heavy', color='#212529', ha='center', va='center')
            if delta_txt:
                # Variación super grande
                ax.text(0.5, 0.25, delta_txt, fontsize=16, fontweight='bold', color=color_delta, ha='center', va='center')
            if interp:
                ax.text(0.5, 0.10, interp, fontsize=10, color='#6c757d', ha='center', va='center', style='italic')
        else:
            ax.text(0.5, 0.40, valor, fontsize=32, fontweight='heavy', color='#212529', ha='center', va='center')

    dibujar_tarjeta(ax1, "CUMPLIMIENTO ", val_cumplimiento, delta_cumplimiento_txt, "", color_delta_c)
    dibujar_tarjeta(ax2, "RIESGO CRÍTICO", val_riesgo, delta_riesgo_txt, '', color_delta_r)
    dibujar_tarjeta(ax3, "CANTIDAD DEFECTUOSA", val_cantidad,unidades_defectuosa)  # Tarjeta mostrando solo la cantidad

    plt.tight_layout()
    plt.savefig(ruta_salida, dpi=300, bbox_inches='tight')
    plt.close()

    return ruta_salida


def generar_tarjetas_individuales(df_kpis: pd.DataFrame, dir_salida: str = ".") -> list:
    """
    Genera 3 imágenes individuales para cada tarjeta KPI.
    Retorna lista de rutas de los archivos PNG.
    """
    import os
    actual = df_kpis.iloc[0]
    anterior = df_kpis.iloc[1]

    rutas = []

    def dibujar_tarjeta_individual(titulo, valor, delta_txt=None, interp=None, color_delta='#6c757d', nombre_archivo="kpi.png"):
        fig, ax = plt.subplots(figsize=(3.5, 3.2), facecolor='white')
        ax.axis('off')
        
        card = FancyBboxPatch(
            (0.02, 0.02), 0.96, 0.96,
            boxstyle="round,pad=0.03,rounding_size=0.08",
            transform=ax.transAxes,
            facecolor='white',
            edgecolor='none',
            linewidth=0
        )
        ax.add_patch(card)

        ax.text(0.5, 0.78, titulo, fontsize=12, fontweight='bold', color='#495057', ha='center', va='center')

        if delta_txt or interp:
            ax.text(0.5, 0.48, valor, fontsize=32, fontweight='heavy', color='#212529', ha='center', va='center')
            if delta_txt:
                ax.text(0.5, 0.22, delta_txt, fontsize=10, fontweight='bold', color=color_delta, ha='center', va='center')
            if interp:
                ax.text(0.5, 0.10, interp, fontsize=8.5, color='#6c757d', ha='center', va='center', style='italic')
        else:
            ax.text(0.5, 0.40, valor, fontsize=36, fontweight='heavy', color='#212529', ha='center', va='center')

        plt.tight_layout()
        ruta = os.path.join(dir_salida, nombre_archivo)
        plt.savefig(ruta, dpi=300, bbox_inches='tight')
        plt.close()
        return ruta

    val_cumplimiento = f"{actual['tasa_cumpli_perfecto']:.1f}%"
    delta_cumplimiento_val = actual['tasa_cumpli_perfecto'] - anterior['tasa_cumpli_perfecto']
    signo_c = "+" if delta_cumplimiento_val > 0 else ""
    delta_cumplimiento_txt = f"{signo_c}{delta_cumplimiento_val:.2f} pp vs mes anterior"
    #interp_cumplimiento = "Incremento en entregas a tiempo" if delta_cumplimiento_val >= 0 else "Deterioro en puntualidad"
    color_delta_c = '#2e7d32' if delta_cumplimiento_val >= 0 else '#c62828'
    
    rutas.append(dibujar_tarjeta_individual("CUMPLIMIENTO", val_cumplimiento, delta_cumplimiento_txt, "", color_delta_c, "kpi_cumplimiento.png"))

    val_riesgo = f"{actual['tasa_riesgo_critico']:.1f}%"
    delta_riesgo_val = actual['tasa_riesgo_critico'] - anterior['tasa_riesgo_critico']
    signo_r = "+" if delta_riesgo_val > 0 else ""
    delta_riesgo_txt = f"{signo_r}{delta_riesgo_val:.2f} vs mes anterior"
    interp_riesgo = "Reducción de riesgo critico" if delta_riesgo_val <= 0 else "Alerta: Incremento de riesgo"
    color_delta_r = '#2e7d32' if delta_riesgo_val <= 0 else '#c62828'

    rutas.append(dibujar_tarjeta_individual("RIESGO CRÍTICO", val_riesgo, delta_riesgo_txt, interp_riesgo, color_delta_r, "kpi_riesgo.png"))

    val_cantidad = f"{int(actual['cantidad_recibida_defectuosa']):,}".replace(",", ".")
    unidades_defectuosa = "Unidades defectuosas"
    
    rutas.append(dibujar_tarjeta_individual("CANTIDAD DEFECTUOSA", val_cantidad, interp=unidades_defectuosa, nombre_archivo="kpi_defectos.png"))

    return rutas



def graficar_distribucion_volumen_mes(df_kpis,ruta_salida: str = "volumen_total_mes.png") -> str:
    """
    Genera un gráfico de barras apiladas al 100% que muestra la distribución mensual 
    de los estados de entrega (Óptimo, Riesgo, Retraso Severo, Incumplimiento) 
    a lo largo de los meses históricos evaluados.
    Retorna la ruta del archivo PNG generado.
    """

    df = df_kpis.sort_values(by="anio-mes", ascending=True).copy()


    optimo = (df['Cumplimiento_optimo'] / df['total']) * 100
    riesgo = (df['Riesgo_de_Retraso'] / df['total']) * 100
    severo = (df['Retraso_Severo'] / df['total']) * 100
    incumplimiento = (df['Incumplimiento_de_Plazo'] / df['total']) * 100

    meses = df['anio-mes'].astype(str).tolist()

    fig, ax = plt.subplots(figsize=(9, 4.8), facecolor="white")

    ancho_barra = 0.52
    color_optimo = "#2ecc71"       
    color_riesgo = "#f1c40f"       
    color_severo = "#e67e22"       
    color_incumplimiento = "#e74c3c" 

    b1 = optimo
    b2 = b1 + riesgo
    b3 = b2 + severo

    p1 = ax.bar(meses, optimo, width=ancho_barra, label="Óptimo", color=color_optimo, edgecolor="white")
    p2 = ax.bar(meses, riesgo, bottom=b1, width=ancho_barra, label="Riesgo Retraso", color=color_riesgo, edgecolor="white")
    p3 = ax.bar(meses, severo, bottom=b2, width=ancho_barra, label="Retraso Severo", color=color_severo, edgecolor="white")
    p4 = ax.bar(meses, incumplimiento, bottom=b3, width=ancho_barra, label="Incumplimiento", color=color_incumplimiento, edgecolor="white")

    for p in [p1, p2, p3, p4]:

        if p == p1 or p == p4 :
              
            labels = [f"{val:.1f}%" if val >= 3 else "" for val in p.datavalues]
            ax.bar_label(p, labels=labels, label_type="center", fontsize=8, color="black", fontweight="bold")

    ax.set_yticks([])  
    #ax.set_ylabel("Proporción del Volumen (%)", fontsize=10, fontweight="bold")
    ax.set_title("Distribución Tasa de Cumplimiento (%)", fontsize=12, fontweight="bold", pad=12)
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1.0), frameon=False)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)  
    ax.yaxis.grid(True, linestyle="--", alpha=0.3)

    plt.tight_layout()
    plt.savefig(ruta_salida, dpi=300, bbox_inches="tight")
    plt.close()

    return ruta_salida


if __name__ == "__main__":
    datos = obtener_datos_completos()
    datos_h = datos_historicos(datos)
  
    img_tarjetas = generar_imagen_tarjetas_kpi_desde_df(datos_h)
    img_volumen = graficar_distribucion_volumen_mes(datos_h)
  
    print("Tarjetas generadas en:", img_tarjetas)
    print("Gráfico de volumen generado en:", img_volumen)