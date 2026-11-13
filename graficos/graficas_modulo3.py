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

# Paleta: el acento es distinto al azul de logística (#1F4E78) y al rojo de calidad (#8B0000) de la página 2
COLOR_RECURRENTE = "#C2560C"        # naranja oscuro: proveedor recurrente (mismo tono en ambos paneles)
COLOR_RESTO = "#B8C2C8"             # gris claro: resto de proveedores
COLOR_ETIQUETA_RESTO = "#6B7780"    # gris oscuro para que la etiqueta de las barras grises se lea
COLOR_TITULO = "#0F3D4C"            # petróleo del reporte
COLOR_TEXTO = "#1E2B33"
COLOR_SEPARADOR = "#B8C7CE"

TOP_ACUMULADO = 5
ANCHO_WRAP = 26                     # caracteres por línea en los nombres del eje Y
FUENTE_ETIQUETA = 7
ANCHO_FIGURA = 9.5                  # igual que graficas_modulo2.py
ALTO_FIGURA = 4.5                   # menor que el módulo 2 (8.6): aquí hay máximo 5 filas por panel


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
    ax.set_xlim(0, vmax * holgura)       # cada panel con su propia escala

    for y, v, txt, c in zip(posiciones, valores, etiquetas, colores_etiqueta):
        ax.annotate(txt, xy=(v, y), xytext=(4, 0), textcoords="offset points",
                    ha="left", va="center", fontsize=8, fontweight="bold", color=c)

    for s in ax.spines.values():
        s.set_visible(False)
    ax.grid(False)


def graficar_modulo_3_proveedores(top_mes, acumulados, recurrentes, n_meses, mes_nombre, periodo_texto,
                                  ruta_salida: str = "modulo3_proveedores.png") -> str:
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

    fig = plt.figure(figsize=(ANCHO_FIGURA, ALTO_FIGURA), facecolor="white")
    # [izq, abajo, ancho, alto] en fracción de la figura: [etiquetas L | barras L] | separador | [etiquetas R | barras R]
    ax_l = fig.add_axes([0.21, 0.10, 0.27, 0.80])
    ax_r = fig.add_axes([0.73, 0.10, 0.27, 0.80])

    # ── Panel izquierdo: mes evaluado ──
    titulo_l = f"Órdenes con faltantes · {mes_nombre}"
    if mes.empty:
        ax_l.text(0.5, 0.5, "Sin órdenes con faltantes en el mes", ha="center", va="center",
                  fontsize=9, color=COLOR_ETIQUETA_RESTO, transform=ax_l.transAxes)
        ax_l.set_xticks([])
        ax_l.set_yticks([])
        for s in ax_l.spines.values():
            s.set_visible(False)
    else:
        filas = mes.iloc[::-1]   # barh dibuja de abajo hacia arriba: se invierte para dejar el mayor arriba
        _panel(
            ax_l,
            nombres=filas["proveedor"].tolist(),
            valores=filas["noCumpleCantidad"].astype(float).tolist(),
            etiquetas=[f"{int(r.noCumpleCantidad)} de {int(r.total)} órdenes" for r in filas.itertuples()],
            colores=[_color(p, COLOR_RECURRENTE, COLOR_RESTO) for p in filas["proveedor"]],
            colores_etiqueta=[_color(p, COLOR_RECURRENTE, COLOR_ETIQUETA_RESTO) for p in filas["proveedor"]],
            n_filas=n_filas, holgura=1.9,
        )

    # ── Panel derecho: acumulado del período ──
    titulo_r = f"Acumulado · {periodo_texto}"
    if acum.empty:
        ax_r.text(0.5, 0.5, "Sin órdenes con faltantes en el período", ha="center", va="center",
                  fontsize=9, color=COLOR_ETIQUETA_RESTO, transform=ax_r.transAxes)
        ax_r.set_xticks([])
        ax_r.set_yticks([])
        for s in ax_r.spines.values():
            s.set_visible(False)
    else:
        filas = acum.iloc[::-1]
        _panel(
            ax_r,
            nombres=filas["proveedor"].tolist(),
            valores=filas["faltantes_acumulados_"].astype(float).tolist(),
            etiquetas=[f"{int(r.faltantes_acumulados_)} de {int(r.total)} · {int(r.meses_con_faltantes)}/{n_meses} meses"
                       for r in filas.itertuples()],
            colores=[_color(p, COLOR_RECURRENTE, COLOR_RESTO) for p in filas["proveedor"]],
            colores_etiqueta=[_color(p, COLOR_RECURRENTE, COLOR_ETIQUETA_RESTO) for p in filas["proveedor"]],
            n_filas=n_filas, holgura=2.3,
        )

    # Títulos centrados sobre cada mitad de la figura (nombres + barras), para que no crucen el separador
    for x, titulo in ((0.24, titulo_l), (0.76, titulo_r)):
        fig.text(x, 0.97, titulo, ha="center", va="bottom", fontsize=11, fontweight="bold", color=COLOR_TITULO)

    # Separador vertical central (igual que la página 2)
    fig.add_artist(Line2D([0.5, 0.5], [0.08, 0.95], transform=fig.transFigure,
                          color=COLOR_SEPARADOR, linewidth=1.0, linestyle=(0, (4, 3))))

    # Leyenda pequeña debajo de la figura
    fig.legend(handles=[Patch(facecolor=COLOR_RECURRENTE, edgecolor="none",
                              label="Incumplimiento recurrente (mes evaluado y meses anteriores)")],
               loc="upper center", bbox_to_anchor=(0.5, 0.04), frameon=False, fontsize=8,
               handlelength=1.0, handleheight=1.0, labelcolor=COLOR_TEXTO)

    fig.savefig(ruta_salida, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return ruta_salida


def graficar_modulo_3_desde_datos(ruta_salida: str = "modulo3_proveedores.png") -> str:
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
