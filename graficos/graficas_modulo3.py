import sys
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from graficos.rutas_graficas import ruta_grafica, CARPETA_GRAFICAS
from graficos.tema import aplicar_tema, tamano_dos_paneles, titulo_panel, ajustar_eje_a_etiquetas, leyenda_inferior, guardar
from pdf_generator import estilos as E

# Colores del informe (pdf_generator/estilos.py). El naranja marca al proveedor recurrente.
COLOR_RECURRENTE = E.ACENTO_RECURRENTE   # mismo tono en ambos paneles
COLOR_RESTO = E.AZUL_GRIS                # resto de proveedores (neutro)
COLOR_ETIQUETA_RESTO = E.TEXTO_SECUNDARIO
COLOR_TITULO = E.AZUL_CORPORATIVO
COLOR_TEXTO = E.TEXTO_PRINCIPAL
COLOR_SEPARADOR = E.LINEA_DIVISORA

TOP_ACUMULADO = 5
ANCHO_WRAP = 22                     # caracteres por línea en los nombres del eje Y (máx. 2 líneas)
FUENTE_ETIQUETA = E.TAM_GRAFICA
PROPORCION_PANEL_DERECHO = 0.56     # fracción del ancho para el panel del acumulado


def _nombre_eje(proveedor, ancho: int = ANCHO_WRAP) -> str:
    """Nombre del proveedor sin espacios sobrantes, partido en máximo dos líneas."""
    lineas = textwrap.wrap(str(proveedor).strip(), width=ancho)
    if len(lineas) > 2:
        lineas = [lineas[0], textwrap.shorten(" ".join(lineas[1:]), width=ancho, placeholder="…")]
    return "\n".join(lineas)


def _panel(ax, nombres, valores, etiquetas, colores, colores_etiqueta, n_filas, holgura):
    """Barras horizontales con el mayor arriba; si hay menos de n_filas, los huecos quedan abajo."""
    posiciones = list(range(n_filas - len(valores), n_filas))

    ax.barh(posiciones, valores, color=colores, height=0.58, edgecolor="none", linewidth=0)

    vmax = max(valores) if valores else 1
    ax.set_yticks(posiciones)
    ax.set_yticklabels([_nombre_eje(n) for n in nombres], fontsize=FUENTE_ETIQUETA,
                       color=COLOR_TEXTO, linespacing=1.1)
    ax.tick_params(axis="y", length=0, pad=6)
    ax.set_xticks([])
    ax.set_ylim(-0.6, n_filas - 0.4)
    ax.set_xlim(0, vmax * holgura)       # cada panel con su propia escala (ajustar_eje_a_etiquetas la amplía si hace falta)

    anotaciones = [ax.annotate(txt, xy=(v, y), xytext=(4, 0), textcoords="offset points",
                               ha="left", va="center", fontsize=E.TAM_GRAFICA, fontweight="bold", color=c)
                   for y, v, txt, c in zip(posiciones, valores, etiquetas, colores_etiqueta)]

    for s in ax.spines.values():
        s.set_visible(False)
    ax.grid(False)
    return valores, anotaciones


def graficar_modulo_3_proveedores(top_mes, acumulados, recurrentes, n_meses, mes_nombre, periodo_texto,
                                  ruta_salida: str = ruta_grafica("modulo3_proveedores.png")) -> str:
    """
    Dos paneles lado a lado separados por una línea vertical punteada (mismo layout que graficas_modulo2.py):
    izquierda = órdenes con faltantes en el mes evaluado; derecha = top 5 del acumulado del período.
    Los proveedores recurrentes van en naranja en los dos paneles; el resto en gris.
    """
    recurrentes = {str(p).strip() for p in (recurrentes or [])}

    def _color(p, c_si, c_no):
        return c_si if str(p).strip() in recurrentes else c_no

    # Datos de cada panel, el mayor primero (se dibuja arriba)
    mes = (top_mes.sort_values("noCumpleCantidad", ascending=False)
           if top_mes is not None and not top_mes.empty else pd.DataFrame())
    acum = (acumulados.sort_values("faltantes_acumulados_", ascending=False).head(TOP_ACUMULADO)
            if acumulados is not None and not acumulados.empty else pd.DataFrame())

    n_filas = max(len(mes), len(acum), 1)

    aplicar_tema()
    fig = plt.figure(figsize=tamano_dos_paneles(), layout="constrained")
    # [etiquetas L | barras L] | separador | [etiquetas R | barras R]: una subfigura por mitad
    # El panel derecho lleva el texto de valor más largo ("45 de 128 · 5/5 meses"): recibe más ancho
    sub_l, sub_r = fig.subfigures(1, 2, wspace=0.04, width_ratios=[1 - PROPORCION_PANEL_DERECHO, PROPORCION_PANEL_DERECHO])
    ax_l = sub_l.subplots()
    ax_r = sub_r.subplots()

    # ── Panel izquierdo: mes evaluado ──
    titulo_l = f"Órdenes con faltantes · {mes_nombre}"
    paneles = []   # (ax, valores, anotaciones) para que el texto al final de cada barra quepa en su panel
    if mes.empty:
        ax_l.text(0.5, 0.5, "Sin órdenes con faltantes en el mes", ha="center", va="center",
                  color=COLOR_ETIQUETA_RESTO, transform=ax_l.transAxes)
        ax_l.set_xticks([])
        ax_l.set_yticks([])
        for s in ax_l.spines.values():
            s.set_visible(False)
    else:
        filas = mes.iloc[::-1]   # barh dibuja de abajo hacia arriba: se invierte para dejar el mayor arriba
        paneles.append((ax_l, *_panel(
            ax_l,
            nombres=filas["proveedor"].tolist(),
            valores=filas["noCumpleCantidad"].astype(float).tolist(),
            etiquetas=[f"{int(r.noCumpleCantidad)} de {int(r.total)} órdenes" for r in filas.itertuples()],
            colores=[_color(p, COLOR_RECURRENTE, COLOR_RESTO) for p in filas["proveedor"]],
            colores_etiqueta=[_color(p, COLOR_RECURRENTE, COLOR_ETIQUETA_RESTO) for p in filas["proveedor"]],
            n_filas=n_filas, holgura=1.9,
        )))

    # ── Panel derecho: acumulado del período ──
    titulo_r = f"Acumulado · {periodo_texto}"
    if acum.empty:
        ax_r.text(0.5, 0.5, "Sin órdenes con faltantes en el período", ha="center", va="center",
                  color=COLOR_ETIQUETA_RESTO, transform=ax_r.transAxes)
        ax_r.set_xticks([])
        ax_r.set_yticks([])
        for s in ax_r.spines.values():
            s.set_visible(False)
    else:
        filas = acum.iloc[::-1]
        paneles.append((ax_r, *_panel(
            ax_r,
            nombres=filas["proveedor"].tolist(),
            valores=filas["faltantes_acumulados_"].astype(float).tolist(),
            etiquetas=[f"{int(r.faltantes_acumulados_)} de {int(r.total)} · {int(r.meses_con_faltantes)}/{n_meses} meses"
                       for r in filas.itertuples()],
            colores=[_color(p, COLOR_RECURRENTE, COLOR_RESTO) for p in filas["proveedor"]],
            colores_etiqueta=[_color(p, COLOR_RECURRENTE, COLOR_ETIQUETA_RESTO) for p in filas["proveedor"]],
            n_filas=n_filas, holgura=2.3,
        )))

    # Etiquetas de panel (el título de la figura va en el PDF), centradas sobre cada mitad
    for sub, titulo in ((sub_l, titulo_l), (sub_r, titulo_r)):
        titulo_panel(sub, titulo, COLOR_TITULO)

    # Separador vertical central (igual que la página 2)
    x_sep = 1 - PROPORCION_PANEL_DERECHO
    fig.add_artist(Line2D([x_sep, x_sep], [0.12, 0.95], transform=fig.transFigure,
                          color=COLOR_SEPARADOR, linewidth=1.0, linestyle=(0, (4, 3))))

    # Leyenda debajo de la figura, centrada y sin marco
    leyenda_inferior(fig, handles=[Patch(facecolor=COLOR_RECURRENTE, edgecolor="none",
                                         label="Incumplimiento recurrente (mes evaluado y meses anteriores)")], ncol=1)

    ajustar_eje_a_etiquetas(fig, paneles)

    return guardar(fig, ruta_salida)


def graficar_modulo_3_desde_datos(ruta_salida: str = ruta_grafica("modulo3_proveedores.png")) -> str:
    """Carga los datos reales desde el ETL de cantidad y genera el gráfico de proveedores."""
    from etl.datos_analisis_cantidad_entrega import datos_grafico_proveedores

    return graficar_modulo_3_proveedores(**datos_grafico_proveedores(), ruta_salida=ruta_salida)


if __name__ == "__main__":
    top_mes = pd.DataFrame({
        "proveedor": ["GALCO S. A. S", "CAJONERIA RANCHO MOJADO S.A.S.", "IPROCOM S.A.S."],
        "total": [12, 21, 2],
        "noCumpleCantidad": [4, 2, 1],
    })
    acumulados = pd.DataFrame({
        "proveedor": ["GALCO S. A. S", "PROELECTRA DE COLOMBIA S.A.S", "CORRUMED S.A.S.",
                      "C.I. COBRES DE COLOMBIA S.A.S", "RESTREPO JIMENEZ JAIME DARIO"],
        "faltantes_acumulados_": [45, 16, 5, 4, 3],
        "total": [128, 29, 38, 21, 27],
        "meses_con_faltantes": [5, 3, 3, 2, 3],
        "porcentaje_incumplimiento": [35.2, 55.2, 13.2, 19.0, 11.1],
    })
    ruta = graficar_modulo_3_proveedores(
        top_mes, acumulados, recurrentes=["GALCO S. A. S"], n_meses=5,
        mes_nombre="Octubre 2026", periodo_texto="Junio a Octubre 2026",
    )
    print("Gráfica generada:", ruta)
