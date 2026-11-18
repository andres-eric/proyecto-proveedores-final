import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from graficos.rutas_graficas import ruta_grafica, CARPETA_GRAFICAS

from graficos.tema import aplicar_tema, tamano_una_columna, guardar
from pdf_generator import estilos as E

# Colores del informe (pdf_generator/estilos.py)
COLOR_DESTACADO = E.AZUL_CORPORATIVO   # mes evaluado
COLOR_COLUMNA = E.AZUL_GRIS            # meses anteriores
COLOR_ETIQUETA = E.AZUL_MEDIO          # número de los meses anteriores (se lee mejor que el azul gris)
COLOR_TEXTO = E.TEXTO_PRINCIPAL
COLOR_SECUNDARIO = E.TEXTO_SECUNDARIO  # % de completas
COLOR_EJE = E.LINEA_DIVISORA

COL_MES = "anio-mes"
COL_NO_CUMPLE = "cantidad_no_cumple"
COL_PCT = "porcentaje_cumplimiento_1_entrega"

RUTA_EVOLUCION = ruta_grafica("modulo4_primera_evolucion.png")
# El título ("Órdenes que requirieron entregas adicionales") y la nota de la figura van en el PDF
# (pdf_generator.FIGURAS), en formato APA; la imagen no lleva título.


def graficar_modulo_4_evolucion(df: pd.DataFrame, ruta_salida: str = RUTA_EVOLUCION) -> str:
    """
    Columnas con las órdenes que requirieron entregas adicionales por mes (sección 4 del PDF).
    Recibe el DataFrame de etl.datos_analisis_primera_entrega.datos_historicos
    (una fila por mes, de más reciente a más antiguo). Guarda un PNG y retorna la ruta.
    """
    datos = df[[COL_MES, COL_NO_CUMPLE, COL_PCT]].copy()
    datos[COL_NO_CUMPLE] = pd.to_numeric(datos[COL_NO_CUMPLE], errors="coerce")
    datos[COL_PCT] = pd.to_numeric(datos[COL_PCT], errors="coerce")
    datos = datos.dropna(subset=[COL_NO_CUMPLE])
    datos = datos.sort_values(COL_MES, ascending=True).reset_index(drop=True)

    # Mismo tamaño que la gráfica de evolución de la sección 3
    aplicar_tema()
    fig, ax = plt.subplots(figsize=tamano_una_columna(), layout="constrained")

    if datos.empty:
        ax.text(0.5, 0.5, "Sin datos de cumplimiento en primera entrega", ha="center", va="center",
                color=COLOR_TEXTO, transform=ax.transAxes)
        ax.axis("off")
        return guardar(fig, ruta_salida)

    meses = datos[COL_MES].astype(str).tolist()
    valores = datos[COL_NO_CUMPLE].astype(int).tolist()
    porcentajes = datos[COL_PCT].tolist()
    x = list(range(len(meses)))
    ultimo = len(x) - 1

    colores = [COLOR_DESTACADO if i == ultimo else COLOR_COLUMNA for i in x]
    ax.bar(x, valores, width=0.55, color=colores, edgecolor="none", zorder=2)

    # Eje Y siempre desde 0 (en columnas, acercar el eje exagera las diferencias).
    # Techo en máximo × 1.30 para que las etiquetas no se corten ni toquen el título.
    maximo = max(valores)
    ax.set_ylim(0, maximo * 1.30 if maximo > 0 else 1)

    # Etiqueta en dos líneas encima de cada columna: número (negrita) y % de completas (gris, más pequeña).
    # Si el valor es 0 no hay columna visible y la etiqueta queda sobre el eje.
    for i, (xi, v, pct) in enumerate(zip(x, valores, porcentajes)):
        es_ultimo = i == ultimo
        tiene_pct = pd.notna(pct)
        if tiene_pct:
            ax.annotate(f"{pct:.1f}% completas", xy=(xi, v), xytext=(0, 3), textcoords="offset points",
                        ha="center", va="bottom", fontsize=E.TAM_GRAFICA, color=COLOR_SECUNDARIO,
                        annotation_clip=False, zorder=5)
        ax.annotate(f"{v}", xy=(xi, v), xytext=(0, 15 if tiene_pct else 3), textcoords="offset points",
                    ha="center", va="bottom", fontsize=E.TAM_GRAFICA + 1, fontweight="bold",
                    color=COLOR_DESTACADO if es_ultimo else COLOR_ETIQUETA,
                    annotation_clip=False, zorder=5)

    # Eje X: del mes más antiguo al más reciente, formato YYYY-MM (igual que la sección 3)
    ax.set_xticks(x)
    ax.set_xticklabels(meses)
    ax.set_xlim(-0.5, len(x) - 0.5)
    ax.tick_params(axis="x", length=0, pad=6)

    # Eje Y sin ticks: cada columna ya tiene su valor escrito
    ax.set_yticks([])

    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color(COLOR_EJE)

    return guardar(fig, ruta_salida)


def graficar_primera_entrega(ruta_salida: str = RUTA_EVOLUCION) -> tuple:
    """Carga los datos reales (datos_historicos de primera entrega) y genera la gráfica. Retorna (ruta, df)."""
    from datos.carga_datos import obtener_data_set_primera_entrega
    from etl.datos_analisis_primera_entrega import datos_historicos

    df = datos_historicos(obtener_data_set_primera_entrega())
    return graficar_modulo_4_evolucion(df, ruta_salida), df


if __name__ == "__main__":
    ejemplo = pd.DataFrame({
        "anio-mes": ["2026-10", "2026-09", "2026-08", "2026-07", "2026-06"],
        "cantidad_no_cumple": [23, 23, 39, 46, 60],
        "porcentaje_cumplimiento_1_entrega": [94.7, 94.6, 90.2, 87.5, 86.5],
    })
    print("Gráfica generada:", graficar_modulo_4_evolucion(ejemplo))
