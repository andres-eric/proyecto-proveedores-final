"""Identidad visual única del informe (PDF y gráficas).

Todo color, fuente, tamaño y espaciado del reporte sale de este archivo:
- pdf_generator/pdf_generator.py arma el PDF con estas constantes.
- graficos/tema.py configura matplotlib con estas mismas constantes.

Los colores se guardan como texto HEX para que sirvan tanto en ReportLab como en matplotlib.
Si llegan los códigos oficiales de CELSA, se reemplazan solo aquí.
"""
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
CARPETA_ASSETS = ROOT_DIR / "assets"
RUTA_LOGO = CARPETA_ASSETS / "logo_celsa.png"       # si no existe, la portada muestra el texto "CELSA"
CARPETA_FUENTES = CARPETA_ASSETS / "fonts"

# ── Textos fijos del documento ────────────────────────────────────────────────
TITULO_INFORME = "Informe Ejecutivo de Gestión de Suministro"
SUBTITULO_INFORME = "Desempeño de proveedores y cumplimiento de entregas"
LEYENDA_CONFIDENCIAL = "Confidencial — Uso exclusivo de la Mesa Directiva"
FUENTE_DATOS = "Fuente: ERP MAX, proveedores nacionales."

# ── Paleta ────────────────────────────────────────────────────────────────────
# Regla: el azul domina, el blanco es el fondo; los colores fuertes solo cuando tienen significado.
AZUL_CORPORATIVO = "#0B3C6E"    # encabezados, portada, mes evaluado en gráficas
AZUL_MEDIO = "#2E6DA4"          # líneas y elementos secundarios
AZUL_CLARO = "#EAF1F8"          # fondos de tarjetas y bandas suaves
AZUL_GRIS = "#A9BFD6"           # meses anteriores y elementos neutros
TEXTO_PRINCIPAL = "#1F2933"
TEXTO_SECUNDARIO = "#5F6B7A"
LINEA_DIVISORA = "#D5DDE6"
BLANCO = "#FFFFFF"

ACENTO_RECURRENTE = "#C2560C"   # naranja: proveedor con incumplimiento recurrente (secciones 3.1 y 4.1)
ROJO_CALIDAD = "#8B0000"        # guinda: defectos de calidad (sección 2), distinto de los retrasos logísticos

# Semáforo de la sección 1 (los que Logística ya reconoce)
SEMAFORO_OPTIMO = "#2ecc71"
SEMAFORO_RIESGO = "#f1c40f"
SEMAFORO_SEVERO = "#e67e22"
SEMAFORO_INCUMPLIMIENTO = "#e74c3c"

# Variación de las tarjetas KPI (sobrios)
VARIACION_FAVORABLE = "#2E7D4F"
VARIACION_DESFAVORABLE = "#B23A3A"

# Texto sobre la banda azul de la portada
TEXTO_SOBRE_AZUL = BLANCO
TEXTO_SOBRE_AZUL_SUAVE = AZUL_GRIS

# ── Tipografía ────────────────────────────────────────────────────────────────
# Una sola familia. Si en assets/fonts/ hay TTF de alguna de estas familias, se registran;
# si no, el PDF usa Helvetica y las gráficas Arial (mismas métricas que Helvetica).
FAMILIAS_TTF = {
    # familia: (regular, negrita, cursiva, negrita cursiva)
    "SourceSans3": ("SourceSans3-Regular.ttf", "SourceSans3-Bold.ttf",
                    "SourceSans3-Italic.ttf", "SourceSans3-BoldItalic.ttf"),
    "Inter": ("Inter-Regular.ttf", "Inter-Bold.ttf", "Inter-Italic.ttf", "Inter-BoldItalic.ttf"),
    "OpenSans": ("OpenSans-Regular.ttf", "OpenSans-Bold.ttf", "OpenSans-Italic.ttf", "OpenSans-BoldItalic.ttf"),
}

FUENTE = "Helvetica"
FUENTE_NEGRITA = "Helvetica-Bold"
FUENTE_CURSIVA = "Helvetica-Oblique"
FUENTE_NEGRITA_CURSIVA = "Helvetica-BoldOblique"
FUENTE_SIMBOLOS = "ZapfDingbats"     # ▲ ▼ de las tarjetas (Helvetica no trae esos glifos)
RUTAS_TTF = []                       # archivos TTF registrados (tema.py los carga en matplotlib)
FAMILIA_GRAFICAS = ["Arial", "Helvetica", "DejaVu Sans"]


def _registrar_fuentes():
    """Registra la primera familia TTF completa que encuentre en assets/fonts/."""
    global FUENTE, FUENTE_NEGRITA, FUENTE_CURSIVA, FUENTE_NEGRITA_CURSIVA, RUTAS_TTF
    if not CARPETA_FUENTES.is_dir():
        return
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.lib.fonts import addMapping
    except ImportError:
        return
    for familia, archivos in FAMILIAS_TTF.items():
        rutas = [CARPETA_FUENTES / a for a in archivos]
        if not all(r.exists() for r in rutas):
            continue
        nombres = [familia, f"{familia}-Bold", f"{familia}-Italic", f"{familia}-BoldItalic"]
        try:
            for nombre, ruta in zip(nombres, rutas):
                pdfmetrics.registerFont(TTFont(nombre, str(ruta)))
            addMapping(familia, 0, 0, nombres[0])
            addMapping(familia, 1, 0, nombres[1])
            addMapping(familia, 0, 1, nombres[2])
            addMapping(familia, 1, 1, nombres[3])
        except Exception:
            continue
        FUENTE, FUENTE_NEGRITA, FUENTE_CURSIVA, FUENTE_NEGRITA_CURSIVA = nombres
        RUTAS_TTF = [str(r) for r in rutas]   # tema.py las agrega a matplotlib y las pone primero
        return


_registrar_fuentes()

# Tamaños (pt)
TAM_NUMERO_SECCION = 30
TAM_H1 = 18
LEADING_H1 = 22
TAM_H2 = 11
ESPACIADO_LETRAS_H2 = 1.2
TAM_TEXTO = 10
LEADING_TEXTO = 15
TAM_NOTA = 8.5
LEADING_NOTA = 12
TAM_ENCABEZADO = 8
TAM_KPI_ETIQUETA = 8
TAM_KPI_VALOR = 24
TAM_KPI_VARIACION = 9
TAM_INDICE = 11
TAM_PORTADA_MARCA = 30
TAM_PORTADA_TITULO = 28
TAM_PORTADA_SUBTITULO = 14
TAM_PORTADA_DATO = 13
TAM_GRAFICA = 9               # texto mínimo de las gráficas al tamaño impreso

# Grosores de línea (pt)
GROSOR_LINEA_FINA = 0.6
GROSOR_LINEA_ENCABEZADO = 0.8
GROSOR_BARRA_ACENTO = 4

# ── Retícula (carta) ──────────────────────────────────────────────────────────
CM = 72 / 2.54
ANCHO_PAGINA, ALTO_PAGINA = 612.0, 792.0          # carta en puntos
MARGEN_LATERAL = 2.2 * CM
MARGEN_SUPERIOR = 2.5 * CM
MARGEN_INFERIOR = 2.2 * CM
ANCHO_UTIL = ANCHO_PAGINA - 2 * MARGEN_LATERAL    # ≈ 487 pt: texto, tarjetas y gráficas
ALTO_UTIL = ALTO_PAGINA - MARGEN_SUPERIOR - MARGEN_INFERIOR

Y_TEXTO_ENCABEZADO = ALTO_PAGINA - 1.35 * CM      # línea base del encabezado
Y_LINEA_ENCABEZADO = ALTO_PAGINA - 1.55 * CM
Y_LINEA_PIE = 1.45 * CM
Y_TEXTO_PIE = 1.0 * CM
PROPORCION_BANDA_PORTADA = 1 / 3                  # alto de la banda azul de la portada

# ── Espaciado vertical (pt) ───────────────────────────────────────────────────
ESPACIO_TRAS_TITULO = 14       # título de sección → primer bloque
ESPACIO_ENTRE_BLOQUES = 22     # tarjetas, texto, figura
ESPACIO_FIGURA_NOTA = 6        # figura → nota
ESPACIO_TRAS_H2 = 8            # subtítulo → texto
ESPACIO_PARRAFOS = 6           # entre párrafos del texto de la IA
ESPACIO_ETIQUETA_FIGURA = 2    # "Figura N" → título de la figura
ESPACIO_TITULO_FIGURA = 8      # título de la figura → imagen
SEPARACION_TARJETAS = 12       # hueco horizontal entre tarjetas KPI
RELLENO_TARJETA = 12           # padding interior de las tarjetas
REDUCCION_MAXIMA_FIGURA = 0.85  # una figura puede encogerse hasta este factor para caber en la página
ESPACIO_TITULO_LINEA = 10      # título de sección → línea divisora
ANCHO_NUMERO_SECCION = 64      # columna del número grande ("03") del encabezado de sección
ESPACIO_KPI_ETIQUETA = 6       # etiqueta de la tarjeta → valor
ESPACIO_KPI_VALOR = 4          # valor de la tarjeta → variación
TAM_KPI_FLECHA = TAM_KPI_VARIACION - 2
ESPACIO_SECCION_COMPARTIDA = ESPACIO_ENTRE_BLOQUES * 1.5  # antes de una sección que comparte página (4.1)

# ── Portada (pt) ──────────────────────────────────────────────────────────────
PORTADA_ALTO_LOGO = 64
PORTADA_ANCHO_MAX_LOGO = 220
PORTADA_ESPACIO_BANDA_TITULO = 64
PORTADA_ESPACIO_TITULO_SUBTITULO = 12
PORTADA_ESPACIO_SUBTITULO_ACENTO = 22
PORTADA_ANCHO_ACENTO = 56
PORTADA_ALTO_ACENTO = 3
PORTADA_Y_DATOS = MARGEN_INFERIOR + 150
PORTADA_ESPACIO_ETIQUETA_DATO = 20
PORTADA_Y_LINEA_LEYENDA = MARGEN_INFERIOR + 24
PORTADA_Y_LEYENDA = MARGEN_INFERIOR + 8

# ── Gráficas (tamaño = tamaño impreso, para que 9 pt en matplotlib sean 9 pt en papel) ──
ANCHO_GRAFICA_PULG = ANCHO_UTIL / 72
PROPORCION_UNA_COLUMNA = 7 / 16
PROPORCION_DOS_PANELES = 10 / 16
DPI_GRAFICAS = 300


def estilos_parrafo():
    """Estilos de párrafo de ReportLab para el PDF."""
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.colors import HexColor
    from reportlab.lib.enums import TA_LEFT, TA_RIGHT

    texto = ParagraphStyle("Texto", fontName=FUENTE, fontSize=TAM_TEXTO, leading=LEADING_TEXTO,
                           textColor=HexColor(TEXTO_PRINCIPAL), alignment=TA_LEFT, spaceAfter=ESPACIO_PARRAFOS)
    return {
        "H1": ParagraphStyle("H1", parent=texto, fontName=FUENTE_NEGRITA, fontSize=TAM_H1, leading=LEADING_H1,
                             textColor=HexColor(AZUL_CORPORATIVO), spaceAfter=0),
        "NumeroSeccion": ParagraphStyle("NumeroSeccion", parent=texto, fontName=FUENTE_NEGRITA,
                                        fontSize=TAM_NUMERO_SECCION, leading=TAM_NUMERO_SECCION,
                                        textColor=HexColor(AZUL_MEDIO), spaceAfter=0),
        "Texto": texto,
        "Viñeta": ParagraphStyle("Viñeta", parent=texto, leftIndent=14, firstLineIndent=-10,
                                 spaceAfter=ESPACIO_PARRAFOS / 2),
        "NotaMetodologica": ParagraphStyle("NotaMetodologica", parent=texto, fontName=FUENTE_CURSIVA,
                                           fontSize=TAM_NOTA + 0.5, leading=LEADING_NOTA + 1,
                                           textColor=HexColor(TEXTO_SECUNDARIO), spaceAfter=0),
        "FiguraNumero": ParagraphStyle("FiguraNumero", parent=texto, fontName=FUENTE_NEGRITA,
                                       leading=LEADING_TEXTO - 2, spaceAfter=0),
        "FiguraTitulo": ParagraphStyle("FiguraTitulo", parent=texto, fontName=FUENTE_CURSIVA,
                                       leading=LEADING_TEXTO - 1, spaceAfter=0),
        "FiguraNota": ParagraphStyle("FiguraNota", parent=texto, fontSize=TAM_NOTA, leading=LEADING_NOTA,
                                     textColor=HexColor(TEXTO_SECUNDARIO), spaceAfter=0),
        "Aviso": ParagraphStyle("Aviso", parent=texto, fontName=FUENTE_CURSIVA, fontSize=TAM_NOTA,
                                leading=LEADING_NOTA, textColor=HexColor(TEXTO_SECUNDARIO)),
        "KpiEtiqueta": ParagraphStyle("KpiEtiqueta", parent=texto, fontName=FUENTE_NEGRITA,
                                      fontSize=TAM_KPI_ETIQUETA, leading=TAM_KPI_ETIQUETA + 2,
                                      textColor=HexColor(TEXTO_SECUNDARIO), spaceAfter=0),
        "KpiValor": ParagraphStyle("KpiValor", parent=texto, fontName=FUENTE_NEGRITA, fontSize=TAM_KPI_VALOR,
                                   leading=TAM_KPI_VALOR + 4, textColor=HexColor(AZUL_CORPORATIVO), spaceAfter=0),
        "KpiVariacion": ParagraphStyle("KpiVariacion", parent=texto, fontName=FUENTE_NEGRITA,
                                       fontSize=TAM_KPI_VARIACION, leading=TAM_KPI_VARIACION + 3,
                                       textColor=HexColor(TEXTO_SECUNDARIO), spaceAfter=0),
        "Indice0": ParagraphStyle("Indice0", parent=texto, fontName=FUENTE_NEGRITA, fontSize=TAM_INDICE,
                                  leading=TAM_INDICE + 6, textColor=HexColor(AZUL_CORPORATIVO),
                                  spaceBefore=10, spaceAfter=0),
        "Indice1": ParagraphStyle("Indice1", parent=texto, fontSize=TAM_TEXTO, leading=TAM_TEXTO + 6,
                                  leftIndent=22, textColor=HexColor(TEXTO_PRINCIPAL), spaceBefore=4, spaceAfter=0),
        "Derecha": ParagraphStyle("Derecha", parent=texto, alignment=TA_RIGHT),
    }
