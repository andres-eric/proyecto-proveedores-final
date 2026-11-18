"""Tema visual común de todas las gráficas del informe.

Los colores, la fuente y los tamaños vienen de pdf_generator/estilos.py (no se repiten aquí).
Las figuras se crean al tamaño en que se imprimen en el PDF (ancho útil de la página),
así un texto de 9 pt en matplotlib mide 9 pt en el papel.
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
from matplotlib import font_manager
from cycler import cycler

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from pdf_generator import estilos as E


def _familias():
    """Familia del PDF primero (si hay TTF en assets/fonts/), luego Arial/Helvetica como respaldo."""
    familias = []
    for ruta in E.RUTAS_TTF:
        try:
            font_manager.fontManager.addfont(ruta)
            nombre = font_manager.FontProperties(fname=ruta).get_name()
            if nombre not in familias:
                familias.append(nombre)
        except Exception:
            pass
    return familias + E.FAMILIA_GRAFICAS


def aplicar_tema():
    """Configura matplotlib (rcParams) con la identidad del informe. Llamar al inicio de cada gráfica."""
    matplotlib.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": _familias(),
        "font.size": E.TAM_GRAFICA,
        "text.color": E.TEXTO_PRINCIPAL,
        "axes.titlesize": E.TAM_GRAFICA,
        "axes.titleweight": "bold",
        "axes.titlecolor": E.AZUL_CORPORATIVO,
        "axes.labelsize": E.TAM_GRAFICA,
        "axes.labelcolor": E.TEXTO_SECUNDARIO,
        "axes.edgecolor": E.LINEA_DIVISORA,
        "axes.linewidth": 0.8,
        "axes.facecolor": E.BLANCO,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": False,
        "axes.axisbelow": True,
        "axes.prop_cycle": cycler(color=[E.AZUL_CORPORATIVO, E.AZUL_MEDIO, E.AZUL_GRIS]),
        "grid.color": E.LINEA_DIVISORA,
        "grid.linewidth": 0.6,
        "grid.alpha": 0.6,
        "xtick.labelsize": E.TAM_GRAFICA,
        "ytick.labelsize": E.TAM_GRAFICA,
        "xtick.color": E.TEXTO_SECUNDARIO,
        "ytick.color": E.TEXTO_SECUNDARIO,
        "xtick.labelcolor": E.TEXTO_PRINCIPAL,
        "ytick.labelcolor": E.TEXTO_PRINCIPAL,
        "legend.fontsize": E.TAM_GRAFICA,
        "legend.frameon": False,
        "legend.labelcolor": E.TEXTO_PRINCIPAL,
        "figure.facecolor": E.BLANCO,
        "figure.dpi": 100,
        "savefig.facecolor": E.BLANCO,
        "savefig.dpi": E.DPI_GRAFICAS,
        "figure.constrained_layout.h_pad": 0.04,
        "figure.constrained_layout.w_pad": 0.04,
    })


def tamano_una_columna():
    """(ancho, alto) en pulgadas de una gráfica de una sola columna (16:7)."""
    return E.ANCHO_GRAFICA_PULG, E.ANCHO_GRAFICA_PULG * E.PROPORCION_UNA_COLUMNA


def tamano_dos_paneles():
    """(ancho, alto) en pulgadas de una gráfica de dos paneles (16:10)."""
    return E.ANCHO_GRAFICA_PULG, E.ANCHO_GRAFICA_PULG * E.PROPORCION_DOS_PANELES


def titulo_panel(subfigura, texto, color):
    """Etiqueta de un panel (no es el título de la figura, que va en el PDF), centrada sobre su mitad.
    Se alinea por la línea base para que los dos paneles queden a la misma altura aunque uno lleve tildes."""
    tam = E.TAM_GRAFICA + 1
    alto_fig_pt = subfigura.get_figure(root=True).get_figheight() * 72
    y_base = 1 - (tam * 1.15) / alto_fig_pt          # deja sitio para las mayúsculas y tildes sobre la línea base
    subfigura.suptitle(texto, y=y_base, va="baseline", fontsize=tam, fontweight="bold", color=color)


def ajustar_eje_a_etiquetas(fig, ejes_y_etiquetas, separacion_pt=4):
    """Amplía el eje X de cada panel de barras horizontales para que el texto que va al final
    de cada barra quepa dentro del panel (sin cortarse ni cruzar el separador).
    ejes_y_etiquetas: lista de (ax, valores, anotaciones). Llamar después de dibujar todo."""
    # El texto al final de la barra no participa del layout: si participara, el layout encogería el eje
    # para hacerle sitio y al ampliar el eje después las barras quedarían diminutas.
    for _, _, anotaciones in ejes_y_etiquetas:
        for ann in anotaciones:
            ann.set_in_layout(False)
    fig.canvas.draw()   # resuelve el layout para medir anchos reales
    renderer = fig.canvas.get_renderer()
    sep_px = separacion_pt * fig.dpi / 72
    for ax, valores, anotaciones in ejes_y_etiquetas:
        if not valores:
            continue
        ancho_eje = ax.get_window_extent(renderer).width
        vmax = max(valores) or 1
        xmax = vmax * 1.05
        for v, ann in zip(valores, anotaciones):
            libre = ancho_eje - sep_px - ann.get_window_extent(renderer).width
            xmax = max(xmax, v * ancho_eje / libre if libre > ancho_eje * 0.05 else vmax * 20)
        ax.set_xlim(0, xmax)


def leyenda_inferior(fig, handles=None, labels=None, ncol=4, handlelength=1.0):
    """Leyenda debajo de la figura, centrada y sin marco (requiere layout='constrained')."""
    kwargs = {"loc": "outside lower center", "ncol": ncol, "frameon": False,
              "handlelength": handlelength, "handleheight": 1.0, "columnspacing": 1.6}
    if handles is not None:
        return fig.legend(handles=handles, labels=labels, **kwargs) if labels else fig.legend(handles=handles, **kwargs)
    return fig.legend(**kwargs)


def guardar(fig, ruta_salida):
    """Guarda al tamaño exacto de la figura (sin recortar), para que el PDF no la reescale."""
    import matplotlib.pyplot as plt
    fig.savefig(ruta_salida, dpi=E.DPI_GRAFICAS, facecolor=E.BLANCO)
    plt.close(fig)
    return ruta_salida
