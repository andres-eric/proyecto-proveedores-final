import sys
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from graficos.rutas_graficas import ruta_grafica, CARPETA_GRAFICAS

from graficos.tema import aplicar_tema, tamano_una_columna, leyenda_inferior, guardar
from pdf_generator import estilos as E

# Colores del informe (pdf_generator/estilos.py)
COLOR_TEXTO = E.TEXTO_PRINCIPAL
COLOR_LINEA = E.AZUL_MEDIO           # serie
COLOR_DESTACADO = E.AZUL_CORPORATIVO  # mes evaluado
COLOR_PROMEDIO = E.TEXTO_SECUNDARIO
COLOR_GRID = E.LINEA_DIVISORA

COL_MES = "anio-mes"
COL_PCT = "porcentaje_cumplimiento_cantidad"
COL_FALTANTES = "noCumpleCantidad"


def graficar_modulo_3(df: pd.DataFrame, ruta_salida: str = ruta_grafica("modulo3_cantidad.png")) -> str:
    """
    Línea con la evolución mensual del % de órdenes que completaron la cantidad pedida.
    Recibe el DataFrame de etl.datos_analisis_cantidad_entrega.datos_historicos
    (una fila por mes, de más reciente a más antiguo). Guarda un PNG y retorna la ruta.
    """
    datos = df[[COL_MES, COL_PCT, COL_FALTANTES]].copy()
    datos[COL_PCT] = pd.to_numeric(datos[COL_PCT], errors="coerce")
    datos = datos.dropna(subset=[COL_PCT])
    datos = datos.sort_values(COL_MES, ascending=True).reset_index(drop=True)

    aplicar_tema()
    fig, ax = plt.subplots(figsize=tamano_una_columna(), layout="constrained")

    if datos.empty:
        ax.text(0.5, 0.5, "Sin datos de cumplimiento de cantidad", ha="center", va="center",
                color=COLOR_TEXTO, transform=ax.transAxes)
        ax.axis("off")
        return guardar(fig, ruta_salida)

    meses = datos[COL_MES].astype(str).tolist()
    valores = datos[COL_PCT].astype(float).tolist()
    faltantes = datos[COL_FALTANTES].fillna(0).astype(int).tolist()
    x = list(range(len(meses)))

    # Eje Y acercado: piso(mínimo) - 2, nunca menor a 0; máximo 100
    y_min = max(0, math.floor(min(valores)) - 2)
    ax.set_ylim(y_min, 100)

    # Promedio del período
    promedio = round(sum(valores) / len(valores), 1)
    ax.axhline(promedio, color=COLOR_PROMEDIO, linestyle=(0, (4, 3)), linewidth=1.0,
               zorder=1, label=f"Promedio del período ({promedio:.1f}%)")

    # Línea principal + marcadores
    ax.plot(x, valores, color=COLOR_LINEA, linewidth=2.2, marker="o", markersize=6,
            markerfacecolor=COLOR_LINEA, markeredgecolor="white", markeredgewidth=1.2,
            zorder=3, label="% cumplimiento de cantidad")

    # Mes evaluado (último) resaltado
    ax.plot(x[-1], valores[-1], linestyle="none", marker="o", markersize=11,
            markerfacecolor=COLOR_DESTACADO, markeredgecolor="white", markeredgewidth=1.5,
            zorder=4, label=f"Mes evaluado ({meses[-1]})")

    # Etiquetas encima de cada punto. La base se eleva hasta la altura máxima de la línea
    # dentro del ancho de la etiqueta, para que un tramo ascendente no la atraviese.
    medio_ancho = 0.4  # mitad del ancho aproximado de la etiqueta, en unidades del eje X
    for i, (xi, v, f) in enumerate(zip(x, valores, faltantes)):
        es_ultimo = i == len(x) - 1
        color = COLOR_DESTACADO if es_ultimo else COLOR_TEXTO
        y_base = v
        if i > 0:
            y_base = max(y_base, v + (valores[i - 1] - v) * medio_ancho)
        if i < len(x) - 1:
            y_base = max(y_base, v + (valores[i + 1] - v) * medio_ancho)
        ax.annotate(f"{v:.1f}%\n{f} con faltantes", xy=(xi, y_base), xytext=(0, 12 if es_ultimo else 10),
                    textcoords="offset points", ha="center", va="bottom", fontsize=E.TAM_GRAFICA,
                    fontweight="bold" if es_ultimo else "normal", color=color, linespacing=1.2,
                    annotation_clip=False, zorder=5,
                    bbox=dict(boxstyle="round,pad=0.2", facecolor=E.BLANCO, edgecolor="none", alpha=0.9))

    # Ejes
    ax.set_xticks(x)
    ax.set_xticklabels(meses)
    ax.set_xlim(-0.5, len(x) - 0.5)
    ax.yaxis.set_major_locator(mticker.MaxNLocator(nbins=6, integer=True))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.tick_params(axis="x", length=0, pad=6)
    ax.set_ylabel("% de órdenes completas")

    ax.grid(axis="y")
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)

    # El título de la figura va en el PDF (formato APA). Las etiquetas cercanas a 100% sobresalen
    # por arriba del eje; constrained layout les reserva espacio.
    leyenda_inferior(fig, ncol=3, handlelength=2.2)

    return guardar(fig, ruta_salida)


def graficar_analisis_cantidad(ruta_salida: str = ruta_grafica("modulo3_cantidad.png")) -> tuple:
    """Carga los datos reales (datos_historicos) y genera la gráfica. Retorna (ruta, df)."""
    from datos.carga_datos import obtener_data_set_cantidad
    from etl.datos_analisis_cantidad_entrega import instanciar_datos_cantidad

    df = instanciar_datos_cantidad(obtener_data_set_cantidad())
    return graficar_modulo_3(df, ruta_salida), df


if __name__ == "__main__":
    ejemplo = pd.DataFrame({
        "anio-mes": ["2026-10", "2026-09", "2026-08", "2026-07", "2026-06"],
        "total": [427, 429, 405, 368, 431],
        "noCumpleCantidad": [7, 16, 22, 21, 25],
        "porcentaje_cumplimiento_cantidad": [98.4, 96.3, 94.6, 94.3, 94.2],
    })
    print("Gráfica generada:", graficar_modulo_3(ejemplo))
