import sys
import pandas as pd
import matplotlib.pyplot as plt
import textwrap
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from graficos.rutas_graficas import ruta_grafica, CARPETA_GRAFICAS
from graficos.tema import aplicar_tema, tamano_dos_paneles, titulo_panel, ajustar_eje_a_etiquetas, guardar
from pdf_generator import estilos as E

from datos.carga_datos import obtener_datos_kpi_detalle, obtener_datos_inspeccion_categoria
from etl.datos_detalles import datos_modulo_2

CATEGORIAS_NO_ESPECIFICADAS = {"SIN CATEGORIA", "SIN CATEGORÍA", "OTROS", "", "NONE", "NAN"}

# Colores del informe (pdf_generator/estilos.py)
COLOR_LOGISTICA = E.AZUL_CORPORATIVO   # retrasos logísticos
COLOR_CALIDAD = E.ROJO_CALIDAD         # defectos de calidad (color con significado)
COLOR_TEXTO = E.TEXTO_PRINCIPAL

TOP_N = 10
ANCHO_WRAP = 26               # caracteres por línea en las etiquetas del eje Y
FUENTE_ETIQUETA = E.TAM_GRAFICA


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


ALTO_LINEA = 1.2               # interlineado de las etiquetas (en tamaños de fuente)
HUECO_FILA = 1.0              # aire entre filas, en líneas de texto
ALTO_BARRA = 1.6              # grosor de la barra, en líneas de texto
MARGEN_SUPERIOR = 0.6         # aire entre la etiqueta del panel y la primera fila, en líneas de texto


def _filas_panel(df, col_proveedor, col_categoria, col_cantidad, n_filas):
    """(valores, etiquetas, alturas) del panel, el mayor primero. Cada fila mide lo que ocupa su etiqueta
    (en líneas de texto), así las etiquetas largas de material nunca se montan sobre la fila vecina."""
    if df is None or df.empty:
        return [], [], []
    df = df.head(n_filas).sort_values(by=col_cantidad, ascending=False)
    valores = df[col_cantidad].astype(float).tolist()
    etiquetas = [_etiqueta_eje(p, c) for p, c in zip(df[col_proveedor], df[col_categoria])]
    alturas = [max(e.count("\n") + 1, 2) + HUECO_FILA for e in etiquetas]
    return valores, etiquetas, alturas


def _panel_tornado(ax, valores, etiquetas, alturas, total, color):
    """Dibuja un panel: etiquetas (Proveedor / Material) a la izquierda y barras creciendo hacia la derecha.
    Las filas se apilan desde arriba; si el panel tiene menos filas que el otro, el hueco queda abajo.
    Retorna las anotaciones de valor (para ajustar el eje a su ancho)."""
    posiciones, acumulado = [], 0.0
    for h in alturas:
        posiciones.append(total - acumulado - h / 2)
        acumulado += h

    # Sin bordes negros en las barras
    ax.barh(posiciones, valores, color=color, height=ALTO_BARRA, edgecolor="none", linewidth=0)

    ax.set_yticks(posiciones)
    ax.set_yticklabels(etiquetas, fontsize=FUENTE_ETIQUETA, color=COLOR_TEXTO, linespacing=ALTO_LINEA)
    ax.tick_params(axis="y", length=0, pad=6)
    ax.set_xticks([])
    ax.set_ylim(0, total + MARGEN_SUPERIOR)

    # Valor al extremo de cada barra, con su unidad
    anotaciones = [ax.annotate(f"{int(v):,} und".replace(",", "."), xy=(v, y), xytext=(4, 0),
                               textcoords="offset points", ha="left", va="center",
                               fontsize=E.TAM_GRAFICA, fontweight="bold", color=color)
                   for y, v in zip(posiciones, valores)]

    for s in ax.spines.values():
        s.set_visible(False)
    return anotaciones


def graficar_tornado_modulo_2(logistica, calidad, ruta_salida: str = ruta_grafica("modulo2_tornado.png")) -> str:
    """
    Dos paneles lado a lado separados por una línea vertical:
    izquierda = Top Retrasos Logísticos (azul), derecha = Top Defectos de Calidad (rojo guinda).
    Cada panel lleva sus propias etiquetas, por lo que nunca se solapan en el centro.
    """
    from matplotlib.lines import Line2D

    n_filas = min(max(len(logistica), len(calidad), 1), TOP_N)
    filas_l = _filas_panel(logistica, 'proveedor', 'categoria', 'suma_cantidades', n_filas)
    filas_r = _filas_panel(calidad, 'Nombre_Proveedor', 'categoria', 'cantidad_recivida', n_filas)
    total = max(sum(filas_l[2]), sum(filas_r[2]), 2 + HUECO_FILA)   # misma escala vertical en ambos paneles

    # Proporción común de dos paneles (16:10); solo crece si las etiquetas no caben a 9 pt
    aplicar_tema()
    ancho, alto = tamano_dos_paneles()
    alto_necesario = (total + MARGEN_SUPERIOR) * E.TAM_GRAFICA * ALTO_LINEA / 72 + 0.55   # + etiqueta del panel y márgenes
    fig = plt.figure(figsize=(ancho, max(alto, alto_necesario)), layout="constrained")

    # [etiquetas L | barras L] | separador | [etiquetas R | barras R]: una subfigura por mitad
    sub_l, sub_r = fig.subfigures(1, 2, wspace=0.06)
    ax_l = sub_l.subplots()
    ax_r = sub_r.subplots()

    ann_l = _panel_tornado(ax_l, *filas_l, total, COLOR_LOGISTICA)
    ann_r = _panel_tornado(ax_r, *filas_r, total, COLOR_CALIDAD)
    titulo_panel(sub_l, "Top Retrasos Logísticos", COLOR_LOGISTICA)
    titulo_panel(sub_r, "Top Defectos de Calidad", COLOR_CALIDAD)

    # Separador vertical central entre ambos gráficos
    fig.add_artist(Line2D([0.5, 0.5], [0.02, 0.95], transform=fig.transFigure,
                          color=E.LINEA_DIVISORA, linewidth=1.0, linestyle=(0, (4, 3))))

    ajustar_eje_a_etiquetas(fig, [(ax_l, filas_l[0], ann_l), (ax_r, filas_r[0], ann_r)])
    return guardar(fig, ruta_salida)


def graficar_modulo_2(ruta_salida: str = ruta_grafica("modulo2_tornado.png")) -> tuple:
    """Genera el gráfico tornado del módulo 2. Retorna (ruta_salida, logistica, calidad)."""
    logistica, calidad = obtener_top_modulo_2()
    ruta = graficar_tornado_modulo_2(logistica, calidad, ruta_salida)
    return ruta, logistica, calidad


if __name__ == "__main__":
    print("Gráfica generada:", graficar_modulo_2()[0])
