"""Generador del PDF del Informe Ejecutivo de Gestión de Suministro.

Estructura: portada → contenido (índice) → secciones 1, 2, 3, 3.1, 4 y 4.1, cada una en página nueva.
Dentro de cada sección: encabezado → nota metodológica → tarjetas KPI → RESUMEN (texto de la IA) → figura (APA).

Todo color, fuente, tamaño y espaciado viene de pdf_generator/estilos.py.
"""
import os
import re
from datetime import datetime
from xml.sax.saxutils import escape

try:
    from reportlab.lib.colors import HexColor
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.platypus import (BaseDocTemplate, Flowable, Frame, HRFlowable, Image, NextPageTemplate,
                                    PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle)
    from reportlab.platypus.tableofcontents import TableOfContents
    REPORTLAB_INSTALLED = True
except ImportError:
    REPORTLAB_INSTALLED = False

try:
    from pdf_generator import estilos as E
except ImportError:   # ejecución directa desde la carpeta pdf_generator/
    import estilos as E


# ── Utilidades de texto ───────────────────────────────────────────────────────
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]


def _mes_anio(anio_mes):
    """'2026-10' -> 'octubre de 2026' (None si el formato no es AAAA-MM)."""
    try:
        anio, mes = str(anio_mes).strip()[:7].split("-")
        return f"{MESES[int(mes) - 1]} de {int(anio)}"
    except (ValueError, IndexError):
        return None


def texto_rango_meses(meses):
    """Rango legible de una lista de 'AAAA-MM': 'junio a octubre de 2026' o
    'noviembre de 2025 a marzo de 2026'. Retorna None si no hay meses válidos."""
    validos = sorted({str(m).strip()[:7] for m in meses if _mes_anio(m)})
    if not validos:
        return None
    ini, fin = validos[0], validos[-1]
    if ini == fin:
        return _mes_anio(fin)
    if ini[:4] == fin[:4]:
        return f"{MESES[int(ini[5:7]) - 1]} a {_mes_anio(fin)}"
    return f"{_mes_anio(ini)} a {_mes_anio(fin)}"


def markdown_to_html(text):
    """Convierte sintaxis básica de Markdown a etiquetas HTML compatibles con ReportLab."""
    text = escape(text)   # '&', '<', '>' del texto de la IA no rompen el párrafo
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'__(.*?)__', r'<b>\1</b>', text)
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    text = re.sub(r'_(.*?)_', r'<i>\1</i>', text)
    return text


def parse_simple_markdown(md_text, estilos):
    """Convierte el texto de la IA (negritas, cursivas, viñetas) en párrafos alineados a la izquierda."""
    flowables = []
    for line in md_text.split('\n'):
        linea = line.strip()
        if not linea:
            continue   # el aire entre párrafos lo da el estilo (spaceAfter)
        if linea.startswith(('- ', '* ', '• ')):
            contenido = linea[2:].strip() if linea[:2] in ('- ', '* ') else linea[1:].strip()
            flowables.append(Paragraph(f"&bull;&nbsp;&nbsp;{markdown_to_html(contenido)}", estilos['Viñeta']))
        else:
            flowables.append(Paragraph(markdown_to_html(linea), estilos['Texto']))
    if flowables:
        flowables[-1].style = flowables[-1].style.clone(flowables[-1].style.name + "Final", spaceAfter=0)
    return flowables


def _formato_pct(valor):
    """Porcentaje con 1 decimal; si el valor no es numérico se muestra tal cual."""
    try:
        return f"{float(valor):.1f}%"
    except (TypeError, ValueError):
        return f"{valor}%"


def _a_float(valor):
    """float o None (también None si es NaN)."""
    try:
        v = float(valor)
    except (TypeError, ValueError):
        return None
    return None if v != v else v


# ── Tarjetas KPI: datos ───────────────────────────────────────────────────────
# Cada tarjeta: {'titulo', 'valor', 'variacion_pp': float|None, 'mayor_es_mejor': bool, 'detalle': str}
#   - con variacion_pp: flecha ▲/▼ + "pp vs mes anterior", en verde si el cambio es favorable y rojo si no.
#   - sin variacion_pp: se muestra 'detalle' en gris.

def construir_kpis_resumen(df_historico):
    """Tarjetas de la sección 1 (cumplimiento, riesgo crítico y unidades defectuosas) desde datos_historicos.
    df_historico va del mes más reciente al más antiguo."""
    act, ant = df_historico.iloc[0], df_historico.iloc[1]
    return [
        {'titulo': 'Cumplimiento', 'valor': _formato_pct(act['tasa_cumpli_perfecto']),
         'variacion_pp': _a_float(act['tasa_cumpli_perfecto'] - ant['tasa_cumpli_perfecto']), 'mayor_es_mejor': True},
        {'titulo': 'Riesgo crítico', 'valor': _formato_pct(act['tasa_riesgo_critico']),
         'variacion_pp': _a_float(act['tasa_riesgo_critico'] - ant['tasa_riesgo_critico']), 'mayor_es_mejor': False},
        {'titulo': 'Unidades defectuosas',
         'valor': f"{int(act['cantidad_recibida_defectuosa']):,}".replace(",", "."),
         'detalle': 'Cantidad recibida defectuosa'},
    ]


def construir_kpis_cantidad(estado):
    """Tarjetas KPI de la sección 3 a partir del estado del agente de cantidad.
    Usa los mismos valores con los que el agente redacta el resumen, para que tarjetas y texto coincidan.
    Retorna None si faltan datos (la sección se omite sin romper el PDF)."""
    try:
        return [
            {'titulo': 'Cumplimiento de cantidad', 'valor': _formato_pct(estado['porcentajeCumpleCantidad']),
             'variacion_pp': _a_float(estado.get('variacion_pp_cumplimiento_cantidad')), 'mayor_es_mejor': True},
            {'titulo': 'Órdenes con faltantes', 'valor': f"{estado['noCumpleCantidad']}",
             'detalle': f"de {estado['total']} órdenes cerradas"},
            {'titulo': 'Promedio del período', 'valor': _formato_pct(estado['promedio_periodo']),
             'detalle': f"{estado['mes_nombre_inicio']} a {estado['mes_nombre']}"},
        ]
    except KeyError:
        return None


# ── Textos de las figuras (formato APA) ──────────────────────────────────────
def _con_rango(texto, rango):
    return f"{texto}, {rango}" if rango else texto


def _textos_figuras(rango, mes):
    """(título, nota) de cada figura. rango: 'junio a octubre de 2026'; mes: 'octubre de 2026'."""
    fuente = E.FUENTE_DATOS
    return {
        'entregas': (
            _con_rango("Distribución mensual del cumplimiento de plazos de entrega", rango),
            "Porcentaje del total de ingresos de materia prima de cada mes según la clasificación del semáforo "
            "de Logística. La zona gris corresponde a ingresos que el semáforo no evalúa. "
            f"{fuente}"),
        'criticos': (
            _con_rango("Proveedores con más unidades con retraso logístico y con defectos de calidad", mes),
            "Unidades (und) por proveedor y material en el mes evaluado; se muestran hasta los diez proveedores "
            f"con mayor volumen en cada caso. {fuente}"),
        'cantidad': (
            _con_rango("Evolución del cumplimiento de cantidad", rango),
            "Porcentaje de órdenes cerradas que completaron la cantidad pedida y número de órdenes con faltantes "
            f"de cada mes; la línea punteada marca el promedio del período. {fuente}"),
        'proveedores_cantidad': (
            "Proveedores con órdenes cerradas con faltantes en el mes evaluado y en el período",
            "Izquierda: órdenes con faltantes de cada proveedor en el mes evaluado sobre su total de órdenes cerradas. "
            "Derecha: los cinco proveedores con más faltantes acumulados en el período y los meses en que tuvieron "
            f"faltantes. En naranja, los proveedores con incumplimiento recurrente. {fuente}"),
        'primera_entrega': (
            _con_rango("Órdenes que requirieron entregas adicionales", rango),
            "Órdenes cuyo primer recibo no cubrió la cantidad pedida. "
            f"Etiqueta inferior: % de órdenes completas en el primer recibo. {fuente}"),
        'proveedores_primera': (
            "Proveedores con incumplimiento en primera entrega",
            f"Órdenes de cada proveedor que requirieron entregas adicionales. {fuente}"),
    }


# ── Flowables propios ─────────────────────────────────────────────────────────
if REPORTLAB_INSTALLED:

    class Subtitulo(Flowable):
        """Subtítulo H2: mayúsculas con espaciado de letras amplio (Paragraph no permite espaciado de letras)."""

        def __init__(self, texto):
            super().__init__()
            self.texto = texto.strip().upper()
            self.keepWithNext = True   # nunca queda solo al final de una página
            # El espacio hasta el texto va dentro del subtítulo, para que keepWithNext lo una al primer párrafo
            self.alto = E.TAM_H2 * 1.25 + E.ESPACIO_TRAS_H2

        def wrap(self, ancho_disp, alto_disp):
            return ancho_disp, self.alto

        def draw(self):
            t = self.canv.beginText(0, self.alto - E.TAM_H2)
            t.setFont(E.FUENTE_NEGRITA, E.TAM_H2)
            t.setFillColor(HexColor(E.AZUL_MEDIO))
            t.setCharSpace(E.ESPACIADO_LETRAS_H2)
            t.textOut(self.texto)
            self.canv.drawText(t)

    class BloqueFigura(Flowable):
        """Figura en formato APA como un solo bloque indivisible: "Figura N", título en cursiva,
        imagen al ancho útil y "Nota." debajo. Si no cabe en lo que queda de página, la imagen se
        encoge hasta E.REDUCCION_MAXIMA_FIGURA; si aun así no cabe, el bloque completo pasa a la
        página siguiente (nunca se separa la figura de su título o de su nota)."""

        def __init__(self, ruta, numero, titulo, nota, estilos):
            super().__init__()
            self.ruta = ruta
            self.img_w, self.img_h = ImageReader(ruta).getSize()
            self.p_numero = Paragraph(f"Figura {numero}", estilos['FiguraNumero'])
            self.p_titulo = Paragraph(titulo, estilos['FiguraTitulo'])
            self.p_nota = Paragraph(f"<i>Nota.</i> {nota}", estilos['FiguraNota'])

        def _alto_textos(self, ancho):
            self.h_numero = self.p_numero.wrap(ancho, 1e6)[1]
            self.h_titulo = self.p_titulo.wrap(ancho, 1e6)[1]
            self.h_nota = self.p_nota.wrap(ancho, 1e6)[1]
            return (self.h_numero + E.ESPACIO_ETIQUETA_FIGURA + self.h_titulo + E.ESPACIO_TITULO_FIGURA
                    + E.ESPACIO_FIGURA_NOTA + self.h_nota)

        def wrap(self, ancho_disp, alto_disp):
            self.ancho = ancho_disp
            textos = self._alto_textos(ancho_disp)
            w = ancho_disp
            h = w * self.img_h / self.img_w
            # Nunca más alta que una página completa
            max_h = E.ALTO_UTIL - textos - 2
            if h > max_h:
                w, h = w * max_h / h, max_h
            # Encoger un poco para aprovechar el espacio que queda en la página actual
            libre = alto_disp - textos
            if h > libre >= h * E.REDUCCION_MAXIMA_FIGURA:
                w, h = w * libre / h, libre
            self.w_img, self.h_img = w, h
            self.alto = textos + h
            return ancho_disp, self.alto

        def split(self, ancho_disp, alto_disp):
            return []   # indivisible

        def draw(self):
            y = self.alto
            y -= self.h_numero
            self.p_numero.drawOn(self.canv, 0, y)
            y -= E.ESPACIO_ETIQUETA_FIGURA + self.h_titulo
            self.p_titulo.drawOn(self.canv, 0, y)
            y -= E.ESPACIO_TITULO_FIGURA + self.h_img
            self.canv.drawImage(self.ruta, (self.ancho - self.w_img) / 2, y, self.w_img, self.h_img, mask='auto')
            y -= E.ESPACIO_FIGURA_NOTA + self.h_nota
            self.p_nota.drawOn(self.canv, 0, y)

    class LienzoNumerado(rl_canvas.Canvas):
        """Canvas que conoce el total de páginas al final, para escribir "Página X de Y"."""

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._estados = []
            self._numerar = False

        def showPage(self):
            self._estados.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            total = len(self._estados)
            for estado in self._estados:
                self.__dict__.update(estado)
                if estado.get('_numerar'):
                    self.saveState()
                    self.setFont(E.FUENTE, E.TAM_ENCABEZADO)
                    self.setFillColor(HexColor(E.TEXTO_SECUNDARIO))
                    self.drawRightString(E.ANCHO_PAGINA - E.MARGEN_LATERAL, E.Y_TEXTO_PIE,
                                         f"Página {self._pageNumber} de {total}")
                    self.restoreState()
                super().showPage()
            super().save()

    class DocumentoInforme(BaseDocTemplate):
        """Registra cada encabezado de sección en el índice y en los marcadores del PDF."""

        def afterFlowable(self, flowable):
            entrada = getattr(flowable, '_entrada_indice', None)
            if entrada:
                nivel, texto, clave = entrada
                self.canv.bookmarkPage(clave)
                self.canv.addOutlineEntry(texto, clave, level=nivel, closed=False)
                self.notify('TOCEntry', (nivel, texto, self.page, clave))


# ── Bloques de la página ──────────────────────────────────────────────────────
def _encabezado_seccion(numero, titulo, estilos, en_indice=True):
    """Número grande en azul medio a la izquierda, título H1 a la derecha y línea divisora debajo."""
    ancho_num = E.ANCHO_NUMERO_SECCION if numero else 0.01
    celdas = [[Paragraph(numero or "", estilos['NumeroSeccion']), Paragraph(titulo, estilos['H1'])]]
    tabla = Table(celdas, colWidths=[ancho_num, E.ANCHO_UTIL - ancho_num])
    tabla.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),   # número y (última línea del) título sobre la misma base
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    tabla.keepWithNext = True
    if en_indice and numero:
        etiqueta = numero.lstrip("0") if "." not in numero else numero
        nivel = 1 if "." in etiqueta else 0
        texto_indice = f"{etiqueta}. {titulo}" if nivel == 0 else f"{etiqueta} {titulo}"
        tabla._entrada_indice = (nivel, texto_indice, f"seccion_{etiqueta.replace('.', '_')}")
    linea = HRFlowable(width="100%", thickness=E.GROSOR_LINEA_FINA, color=HexColor(E.LINEA_DIVISORA),
                       spaceBefore=E.ESPACIO_TITULO_LINEA, spaceAfter=E.ESPACIO_TRAS_TITULO)
    linea.keepWithNext = True
    return [tabla, linea]


def _texto_variacion(k):
    """HTML de la línea de variación de una tarjeta (o su detalle en gris si no hay variación)."""
    v = k.get('variacion_pp')
    if v is None:
        detalle = k.get('detalle') or k.get('delta') or "&nbsp;"   # 'delta': formato anterior de tarjeta
        return detalle, E.TEXTO_SECUNDARIO
    v = round(v, 1)
    if v == 0:
        return f"{abs(v):.1f} pp vs mes anterior", E.TEXTO_SECUNDARIO
    favorable = (v > 0) == k.get('mayor_es_mejor', True)
    flecha = "▲" if v > 0 else "▼"
    color = E.VARIACION_FAVORABLE if favorable else E.VARIACION_DESFAVORABLE
    return (f'<font name="{E.FUENTE_SIMBOLOS}" size="{E.TAM_KPI_FLECHA}">{flecha}</font>'
            f'&nbsp;{v:+.1f} pp vs mes anterior'), color


def _tarjetas_kpi(lista_kpis, estilos):
    """Fila de tres tarjetas del mismo alto y ancho que ocupan todo el ancho útil.
    Columnas: [barra | contenido | hueco] × 3; al compartir fila, las tres miden lo mismo."""
    n = len(lista_kpis)
    sep = E.SEPARACION_TARJETAS
    ancho_tarjeta = (E.ANCHO_UTIL - sep * (n - 1)) / n
    barra = E.GROSOR_BARRA_ACENTO
    fila, anchos, estilo = [], [], [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]
    for i, k in enumerate(lista_kpis):
        texto_var, color_var = _texto_variacion(k)
        contenido = [
            Paragraph(escape(str(k['titulo'])).upper(), estilos['KpiEtiqueta']),
            Spacer(1, E.ESPACIO_KPI_ETIQUETA),
            Paragraph(str(k['valor']), estilos['KpiValor']),
            Spacer(1, E.ESPACIO_KPI_VALOR),
            Paragraph(texto_var, estilos['KpiVariacion'].clone(f"KpiVar{i}", textColor=HexColor(color_var))),
        ]
        c = len(fila)
        fila += ['', contenido]
        anchos += [barra, ancho_tarjeta - barra]
        estilo += [
            ('BACKGROUND', (c, 0), (c, 0), HexColor(E.AZUL_CORPORATIVO)),
            ('BOX', (c, 0), (c + 1, 0), E.GROSOR_LINEA_FINA, HexColor(E.LINEA_DIVISORA)),
            ('LEFTPADDING', (c + 1, 0), (c + 1, 0), E.RELLENO_TARJETA),
            ('RIGHTPADDING', (c + 1, 0), (c + 1, 0), E.RELLENO_TARJETA / 2),
            ('TOPPADDING', (c + 1, 0), (c + 1, 0), E.RELLENO_TARJETA),
            ('BOTTOMPADDING', (c + 1, 0), (c + 1, 0), E.RELLENO_TARJETA),
        ]
        if i < n - 1:
            fila.append('')
            anchos.append(sep)
    tabla = Table([fila], colWidths=anchos)
    tabla.setStyle(TableStyle(estilo))
    return tabla


# ── Páginas: portada, encabezado y pie ───────────────────────────────────────
def _dibujar_portada(canvas, doc, periodo, estilos):
    canvas.saveState()
    canvas._numerar = False
    W, H = E.ANCHO_PAGINA, E.ALTO_PAGINA
    x = E.MARGEN_LATERAL
    y_banda = H * (1 - E.PROPORCION_BANDA_PORTADA)

    # Banda azul en el tercio superior, con el logo (o la marca en texto) en blanco
    canvas.setFillColor(HexColor(E.AZUL_CORPORATIVO))
    canvas.rect(0, y_banda, W, H - y_banda, stroke=0, fill=1)
    centro_banda = y_banda + (H - y_banda) / 2
    if E.RUTA_LOGO.exists():
        alto_logo, ancho_max = E.PORTADA_ALTO_LOGO, E.PORTADA_ANCHO_MAX_LOGO
        lw, lh = ImageReader(str(E.RUTA_LOGO)).getSize()
        ancho_logo = min(ancho_max, alto_logo * lw / lh)
        alto_logo = ancho_logo * lh / lw
        canvas.drawImage(str(E.RUTA_LOGO), x, centro_banda - alto_logo / 2, ancho_logo, alto_logo, mask='auto')
    else:
        canvas.setFillColor(HexColor(E.TEXTO_SOBRE_AZUL))
        canvas.setFont(E.FUENTE_NEGRITA, E.TAM_PORTADA_MARCA)
        canvas.drawString(x, centro_banda - E.TAM_PORTADA_MARCA * 0.35, "CELSA")

    # Título y subtítulo
    titulo = Paragraph(E.TITULO_INFORME, estilos['Texto'].clone(
        'PortadaTitulo', fontName=E.FUENTE_NEGRITA, fontSize=E.TAM_PORTADA_TITULO,
        leading=E.TAM_PORTADA_TITULO * 1.2, textColor=HexColor(E.AZUL_CORPORATIVO), spaceAfter=0))
    subtitulo = Paragraph(E.SUBTITULO_INFORME, estilos['Texto'].clone(
        'PortadaSubtitulo', fontSize=E.TAM_PORTADA_SUBTITULO, leading=E.TAM_PORTADA_SUBTITULO * 1.3,
        textColor=HexColor(E.TEXTO_SECUNDARIO), spaceAfter=0))
    y = y_banda - E.PORTADA_ESPACIO_BANDA_TITULO
    _, h = titulo.wrapOn(canvas, E.ANCHO_UTIL * 0.9, H)
    titulo.drawOn(canvas, x, y - h)
    y -= h + E.PORTADA_ESPACIO_TITULO_SUBTITULO
    _, h = subtitulo.wrapOn(canvas, E.ANCHO_UTIL, H)
    subtitulo.drawOn(canvas, x, y - h)
    y -= h + E.PORTADA_ESPACIO_SUBTITULO_ACENTO
    canvas.setFillColor(HexColor(E.AZUL_MEDIO))
    canvas.rect(x, y, E.PORTADA_ANCHO_ACENTO, E.PORTADA_ALTO_ACENTO, stroke=0, fill=1)

    # Periodo evaluado y fecha de emisión
    hoy = datetime.now()
    datos = [("PERIODO EVALUADO", (_mes_anio(periodo) or str(periodo)).capitalize() if periodo else "—"),
             ("FECHA DE EMISIÓN", f"{hoy.day} de {MESES[hoy.month - 1]} de {hoy.year}")]
    y_dato = E.PORTADA_Y_DATOS
    for i, (etiqueta, valor) in enumerate(datos):
        xi = x + i * (E.ANCHO_UTIL / 2)
        canvas.saveState()   # el espaciado de letras de la etiqueta no debe pasar al valor
        t = canvas.beginText(xi, y_dato)
        t.setFont(E.FUENTE_NEGRITA, E.TAM_KPI_ETIQUETA)
        t.setFillColor(HexColor(E.TEXTO_SECUNDARIO))
        t.setCharSpace(E.ESPACIADO_LETRAS_H2)
        t.textOut(etiqueta)
        canvas.drawText(t)
        canvas.restoreState()
        canvas.setFont(E.FUENTE, E.TAM_PORTADA_DATO)
        canvas.setFillColor(HexColor(E.TEXTO_PRINCIPAL))
        canvas.drawString(xi, y_dato - E.PORTADA_ESPACIO_ETIQUETA_DATO, valor)

    # Leyenda de confidencialidad
    canvas.setStrokeColor(HexColor(E.LINEA_DIVISORA))
    canvas.setLineWidth(E.GROSOR_LINEA_FINA)
    canvas.line(x, E.PORTADA_Y_LINEA_LEYENDA, W - x, E.PORTADA_Y_LINEA_LEYENDA)
    canvas.setFont(E.FUENTE, E.TAM_NOTA)
    canvas.setFillColor(HexColor(E.TEXTO_SECUNDARIO))
    canvas.drawString(x, E.PORTADA_Y_LEYENDA, E.LEYENDA_CONFIDENCIAL)
    canvas.restoreState()


def _dibujar_interior(canvas, doc, periodo):
    canvas.saveState()
    canvas._numerar = True   # LienzoNumerado escribe "Página X de Y" al final
    x0, x1 = E.MARGEN_LATERAL, E.ANCHO_PAGINA - E.MARGEN_LATERAL

    # Encabezado
    canvas.setFont(E.FUENTE, E.TAM_ENCABEZADO)
    canvas.setFillColor(HexColor(E.TEXTO_SECUNDARIO))
    canvas.drawString(x0, E.Y_TEXTO_ENCABEZADO, E.TITULO_INFORME)
    if periodo:
        canvas.drawRightString(x1, E.Y_TEXTO_ENCABEZADO, f"Periodo {periodo}")
    canvas.setStrokeColor(HexColor(E.AZUL_CORPORATIVO))
    canvas.setLineWidth(E.GROSOR_LINEA_ENCABEZADO)
    canvas.line(x0, E.Y_LINEA_ENCABEZADO, x1, E.Y_LINEA_ENCABEZADO)

    # Pie
    canvas.setStrokeColor(HexColor(E.LINEA_DIVISORA))
    canvas.setLineWidth(E.GROSOR_LINEA_FINA)
    canvas.line(x0, E.Y_LINEA_PIE, x1, E.Y_LINEA_PIE)
    canvas.drawString(x0, E.Y_TEXTO_PIE, E.LEYENDA_CONFIDENCIAL)
    canvas.restoreState()


# ── Documento ─────────────────────────────────────────────────────────────────
def generar_pdf_reporte(texto_agente, ruta_pdf_salida, ruta_kpis=None, ruta_barras=None, kpis=None, periodo=None, grafica_tornado=None, texto_modulo_2=None, grafica_cantidad=None, texto_modulo_3=None,
                        kpis_cantidad=None, grafica_proveedores_cantidad=None, texto_proveedores_cantidad=None,
                        grafica_primera_evolucion=None, texto_primera_entrega=None,
                        rango_periodo=None, texto_proveedores_primera_entrega=None,
                        grafica_proveedores_primera_entrega=None):
    """Genera el Informe Ejecutivo en PDF.

    rango_periodo: texto del período de las gráficas (ej. 'junio a octubre de 2026'; ver texto_rango_meses).
    texto_/grafica_proveedores_primera_entrega: contenido futuro de la sección 4.1; mientras no exista,
    la 4.1 aparece en el índice y comparte página con la sección 4.
    """
    if not REPORTLAB_INSTALLED:
        print("\n" + "!" * 60)
        print("ERROR: La librería 'reportlab' no está instalada.")
        print("!" * 60 + "\n")
        return False

    estilos = E.estilos_parrafo()
    figuras = _textos_figuras(rango_periodo, _mes_anio(periodo) if periodo else None)
    contador = {'figura': 0}

    def existe(ruta):
        return bool(ruta) and os.path.exists(ruta)

    def figura(ruta, clave):
        contador['figura'] += 1
        titulo, nota = figuras[clave]
        try:
            return BloqueFigura(ruta, contador['figura'], titulo, nota, estilos)
        except Exception as e:
            contador['figura'] -= 1
            return Paragraph(f"Error cargando la figura: {escape(str(e))}", estilos['Aviso'])

    def bloque_resumen(texto):
        return [Subtitulo("Resumen")] + parse_simple_markdown(texto.strip(), estilos)

    def espacio():
        return Spacer(1, E.ESPACIO_ENTRE_BLOQUES)

    story = []

    # 1. Portada (dibujada en el canvas) → 2. Contenido
    story += [Spacer(1, 1), NextPageTemplate('interior'), PageBreak()]
    story += _encabezado_seccion(None, "Contenido", estilos, en_indice=False)
    indice = TableOfContents(dotsMinLevel=0)
    indice.levelStyles = [estilos['Indice0'], estilos['Indice1']]
    story.append(indice)

    # ── Sección 1: cumplimiento de entregas ──
    story.append(PageBreak())
    story += _encabezado_seccion("01", "Cumplimiento de Entregas", estilos)
    if kpis:
        story += [_tarjetas_kpi(kpis, estilos), espacio()]
    elif existe(ruta_kpis):
        try:
            iw, ih = ImageReader(ruta_kpis).getSize()
            ancho = E.ANCHO_UTIL * 0.6
            story += [Image(ruta_kpis, width=ancho, height=ancho * ih / iw), espacio()]
        except Exception as e:
            story.append(Paragraph(f"Error cargando KPIs: {escape(str(e))}", estilos['Aviso']))
    story += bloque_resumen(texto_agente or "")
    story.append(espacio())
    if existe(ruta_barras):
        story.append(figura(ruta_barras, 'entregas'))
    else:
        story.append(Paragraph("[Gráfica no encontrada]", estilos['Aviso']))

    # ── Sección 2: proveedores críticos ──
    if existe(grafica_tornado) or texto_modulo_2:
        story.append(PageBreak())
        story += _encabezado_seccion("02", "Análisis de Proveedores Críticos", estilos)
        if texto_modulo_2:
            story += bloque_resumen(texto_modulo_2)
        if existe(grafica_tornado):
            story += [espacio(), figura(grafica_tornado, 'criticos')]

    # ── Sección 3: cumplimiento de cantidad ──
    hay_kpis_cantidad = bool(kpis_cantidad) and len(kpis_cantidad) == 3
    if hay_kpis_cantidad or existe(grafica_cantidad) or texto_modulo_3:
        story.append(PageBreak())
        story += _encabezado_seccion("03", "Cumplimiento de Cantidad", estilos)
        if hay_kpis_cantidad:
            story += [_tarjetas_kpi(kpis_cantidad, estilos), espacio()]
        if texto_modulo_3:
            story += bloque_resumen(texto_modulo_3) + [espacio()]
        if existe(grafica_cantidad):
            story.append(figura(grafica_cantidad, 'cantidad'))

    # ── Sección 3.1: proveedores con incumplimiento de cantidad ──
    if existe(grafica_proveedores_cantidad) or texto_proveedores_cantidad:
        story.append(PageBreak())
        story += _encabezado_seccion("3.1", "Proveedores con Incumplimiento de Cantidad", estilos)
        if texto_proveedores_cantidad:
            story += bloque_resumen(texto_proveedores_cantidad) + [espacio()]
        if existe(grafica_proveedores_cantidad):
            story.append(figura(grafica_proveedores_cantidad, 'proveedores_cantidad'))

    # ── Sección 4: cumplimiento en primera entrega ──
    story.append(PageBreak())
    story += _encabezado_seccion("04", "Cumplimiento en Primera Entrega", estilos)
    story.append(Paragraph(
        "Mide las órdenes que llegaron completas en su primer recibo. Cada orden se asigna al mes de su "
        "primer recibo, por lo que su universo difiere del cumplimiento de cantidad.", estilos['NotaMetodologica']))
    story.append(espacio())
    if texto_primera_entrega:
        story += bloque_resumen(texto_primera_entrega) + [espacio()]
    if existe(grafica_primera_evolucion):
        story.append(figura(grafica_primera_evolucion, 'primera_entrega'))

    # ── Sección 4.1: proveedores con incumplimiento en primera entrega ──
    # Sin contenido todavía: va en la misma página que la 4 para no dejar una página casi vacía.
    hay_41 = existe(grafica_proveedores_primera_entrega) or texto_proveedores_primera_entrega
    story.append(PageBreak() if hay_41 else Spacer(1, E.ESPACIO_SECCION_COMPARTIDA))
    story += _encabezado_seccion("4.1", "Proveedores con Incumplimiento en Primera Entrega", estilos)
    if texto_proveedores_primera_entrega:
        story += bloque_resumen(texto_proveedores_primera_entrega) + [espacio()]
    if existe(grafica_proveedores_primera_entrega):
        story.append(figura(grafica_proveedores_primera_entrega, 'proveedores_primera'))
    # Quita espacios sueltos al final (no generan página en blanco, pero tampoco aportan)
    while story and isinstance(story[-1], Spacer):
        story.pop()

    # ── Plantillas de página ──
    marco = Frame(E.MARGEN_LATERAL, E.MARGEN_INFERIOR, E.ANCHO_UTIL, E.ALTO_UTIL,
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, id='contenido')
    doc = DocumentoInforme(
        ruta_pdf_salida, pagesize=letter,
        leftMargin=E.MARGEN_LATERAL, rightMargin=E.MARGEN_LATERAL,
        topMargin=E.MARGEN_SUPERIOR, bottomMargin=E.MARGEN_INFERIOR,
        title=E.TITULO_INFORME, subject=E.SUBTITULO_INFORME, author="CELSA",
    )
    doc.addPageTemplates([
        PageTemplate(id='portada', frames=[marco], onPage=lambda c, d: _dibujar_portada(c, d, periodo, estilos)),
        PageTemplate(id='interior', frames=[marco], onPage=lambda c, d: _dibujar_interior(c, d, periodo)),
    ])

    try:
        doc.multiBuild(story, canvasmaker=LienzoNumerado)
        print(f"Reporte PDF generado exitosamente en: {ruta_pdf_salida}")
        return True
    except Exception as e:
        print(f"Ocurrió un error al compilar el PDF: {e}")
        return False
