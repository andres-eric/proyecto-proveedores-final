import sys
import pandas as pd
import matplotlib.pyplot as plt
import textwrap
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from datos.carga_datos import obtener_datos_kpi_detalle, obtener_datos_inspeccion_categoria
from etl.datos_detalles import datos_modulo_2

CATEGORIAS_NO_ESPECIFICADAS = {"SIN CATEGORIA", "SIN CATEGORÍA", "OTROS", "", "NONE", "NAN"}

# Paleta corporativa
COLOR_LOGISTICA = "#1F4E78"   # Azul Marino Corporativo
COLOR_CALIDAD = "#8B0000"     # Rojo Guinda / Carmesí
COLOR_TEXTO = "#1E2B33"

TOP_N = 10
ANCHO_WRAP = 26               # caracteres por línea en las etiquetas del eje Y
FUENTE_ETIQUETA = 7
ALTO_FIGURA = 8.6             # más alto => cada fila tiene espacio para etiquetas de varias líneas


def _etiqueta_categoria(valor) -> str:
    texto = "" if pd.isna(valor) else str(valor).strip()
    return "Material no especificado" if texto.upper() in CATEGORIAS_NO_ESPECIFICADAS else texto


def _etiqueta_eje(proveedor, categoria, ancho: int = ANCHO_WRAP) -> str:
    """Etiqueta 'Proveedor / Material' completa (sin puntos suspensivos) dividida en líneas con textwrap."""
    prov = textwrap.fill(str(proveedor).strip(), width=ancho)
    mat = textwrap.fill(_etiqueta_categoria(categoria), width=ancho)
    return f"{prov}\n{mat}"


def obtener_top_modulo_2(top_n: int = TOP_N) -> tuple:
    """Retorna (logistica, calidad): los Top N de retrasos logísticos y de defectos de calidad."""
    # datos_modulo_2 devuelve (calidad/inspección, logística/retrasos)
    inspeccion, logistica = datos_modulo_2(obtener_datos_kpi_detalle(), obtener_datos_inspeccion_categoria())
    return logistica.head(top_n).copy(), inspeccion.head(top_n).copy()


def _panel_tornado(ax, df, col_proveedor, col_categoria, col_cantidad, titulo, color, n_filas):
    """Dibuja un panel: etiquetas (Proveedor / Material) a la izquierda y barras creciendo hacia la derecha."""
    df = df.head(n_filas).sort_values(by=col_cantidad, ascending=True)  # el mayor queda arriba
    valores = df[col_cantidad].astype(float).tolist()
    etiquetas = [_etiqueta_eje(p, c) for p, c in zip(df[col_proveedor], df[col_categoria])]
    # Alineación superior: si hay menos de n_filas, los huecos quedan abajo
    posiciones = list(range(n_filas - len(valores), n_filas))

    # Sin bordes negros en las barras
    ax.barh(posiciones, valores, color=color, height=0.58, edgecolor="none", linewidth=0)

    vmax = max(valores) if valores else 1
    ax.set_yticks(posiciones)
    ax.set_yticklabels(etiquetas, fontsize=FUENTE_ETIQUETA, color=COLOR_TEXTO, linespacing=1.1)
    ax.tick_params(axis="y", length=0, pad=6)
    ax.set_xticks([])
    ax.set_ylim(-0.6, n_filas - 0.4)
    ax.set_xlim(0, vmax * 1.45)  # holgura para el texto "N und"

    # Valor al extremo de cada barra, con su unidad
    for y, v in zip(posiciones, valores):
        ax.annotate(f"{int(v):,} und".replace(",", "."), xy=(v, y), xytext=(4, 0), textcoords="offset points",
                    ha="left", va="center", fontsize=8, fontweight="bold", color=color)

    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title(titulo, fontsize=11, fontweight="bold", color=color, pad=12)


def graficar_tornado_modulo_2(logistica, calidad, ruta_salida: str = "modulo2_tornado.png") -> str:
    """
    Dos paneles lado a lado separados por una línea vertical:
    izquierda = Top Retrasos Logísticos (azul marino), derecha = Top Defectos de Calidad (rojo guinda).
    Cada panel lleva sus propias etiquetas, por lo que nunca se solapan en el centro.
    """
    from matplotlib.lines import Line2D

    n_filas = min(max(len(logistica), len(calidad), 1), TOP_N)

    fig = plt.figure(figsize=(9.5, ALTO_FIGURA), facecolor="white")

    # Coordenadas explícitas (fracción de la figura): [izq, abajo, ancho, alto]
    # [etiquetas L | barras L] | separador | [etiquetas R | barras R]
    ax_l = fig.add_axes([0.21, 0.02, 0.27, 0.90])
    ax_r = fig.add_axes([0.73, 0.02, 0.27, 0.90])

    _panel_tornado(ax_l, logistica, 'proveedor', 'categoria', 'suma_cantidades',
                   "Top Retrasos Logísticos", COLOR_LOGISTICA, n_filas)
    _panel_tornado(ax_r, calidad, 'Nombre_Proveedor', 'categoria', 'cantidad_recivida',
                   "Top Defectos de Calidad", COLOR_CALIDAD, n_filas)

    # Separador vertical central entre ambos gráficos
    fig.add_artist(Line2D([0.5, 0.5], [0.02, 0.95], transform=fig.transFigure,
                          color="#B8C7CE", linewidth=1.0, linestyle=(0, (4, 3))))

    plt.savefig(ruta_salida, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()
    return ruta_salida


def graficar_modulo_2(ruta_salida: str = "modulo2_tornado.png") -> tuple:
    """Genera el gráfico tornado del módulo 2. Retorna (ruta_salida, logistica, calidad)."""
    logistica, calidad = obtener_top_modulo_2()
    ruta = graficar_tornado_modulo_2(logistica, calidad, ruta_salida)
    return ruta, logistica, calidad


if __name__ == "__main__":
    print("Gráfica generada:", graficar_modulo_2()[0])
