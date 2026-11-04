import os
import re
from datetime import datetime

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, KeepTogether, HRFlowable, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.colors import HexColor
    from reportlab.lib.utils import ImageReader
    from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
    REPORTLAB_INSTALLED = True
except ImportError:
    REPORTLAB_INSTALLED = False

def markdown_to_html(text):
    """Convierte sintaxis básica de Markdown a etiquetas HTML compatibles con ReportLab."""
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'__(.*?)__', r'<b>\1</b>', text)
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    text = re.sub(r'_(.*?)_', r'<i>\1</i>', text)
    return text

def _escalar_imagen(img_w, img_h, max_ancho=460, max_alto=260):
    """Escala proporcionalmente una imagen para que nunca supere el bounding box indicado."""
    if img_w <= 0 or img_h <= 0:
        return max_ancho, max_alto
    escala = min(max_ancho / img_w, max_alto / img_h, 1.0)
    return img_w * escala, img_h * escala

def parse_simple_markdown(md_text, styles):
    """Convierte el texto puro (bold, cursivas) en una lista de Flowables (Párrafos, Listas)."""
    flowables = []
    lines = md_text.split('\n')
    in_list = False

    for line in lines:
        line_strip = line.strip()
        if not line_strip:
            if in_list:
                flowables.append(Spacer(1, 2))
            else:
                flowables.append(Spacer(1, 4))
            continue

        if line_strip.startswith('- ') or line_strip.startswith('* ') or line_strip.startswith('• '):
            in_list = True
            contenido_item = line_strip[2:].strip() if (line_strip.startswith('- ') or line_strip.startswith('* ')) else line_strip[1:].strip()
            flowables.append(Paragraph(f"&bull; {markdown_to_html(contenido_item)}", styles['CustomBullet']))
            flowables.append(Spacer(1, 2))
        else:
            in_list = False
            flowables.append(Paragraph(markdown_to_html(line_strip), styles['CustomBody']))
            flowables.append(Spacer(1, 4))
            
    return flowables

def _titulo_seccion(texto, ancho, color_barra, estilo):
    """Encabezado de sección con barra de acento lateral."""
    t = Table([['', Paragraph(texto, estilo)]], colWidths=[4, ancho - 4])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), color_barra),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('LEFTPADDING', (1, 0), (1, 0), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    return t

def generar_pdf_reporte(texto_agente, ruta_pdf_salida, ruta_kpis=None, ruta_barras=None, kpis=None, periodo=None, grafica_tornado=None, texto_modulo_2=None):
    """Genera un reporte PDF con layout tipo Dashboard Moderno."""
    if not REPORTLAB_INSTALLED:
        print("\n" + "!" * 60)
        print("ERROR: La librería 'reportlab' no está instalada.")
        print("!" * 60 + "\n")
        return False
        
    styles = getSampleStyleSheet()
    
    color_primario   = HexColor('#0F3D4C')   # Petróleo profundo
    color_secundario = HexColor('#14566B')   # Petróleo medio
    color_acento     = HexColor('#5E8FA0')   # Petróleo claro
    color_texto      = HexColor('#1E2B33')   # Carbón azulado
    color_suave      = HexColor('#5B6B75')   # Gris azulado
    
    styles['Normal'].textColor = color_texto
    styles['Normal'].fontSize = 9
    styles['Normal'].leading = 13
    
    custom_title = ParagraphStyle(
        'CustomTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=color_primario,
        spaceAfter=4,
        spaceBefore=0,
    )

    custom_subtitle = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=color_suave,
        spaceAfter=6,
    )
    
    custom_h2 = ParagraphStyle(
        'CustomH2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=12,
        textColor=color_secundario,
        spaceBefore=4,
        spaceAfter=3,
        keepWithNext=True,
    )
    
    custom_body = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        textColor=color_texto,
        alignment=TA_JUSTIFY,
        spaceAfter=2,
    )

    custom_caption = ParagraphStyle(
        'CustomCaption',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        leading=11,
        textColor=color_suave,
        alignment=TA_LEFT,
        spaceAfter=2,
    )
    
    custom_bullet = ParagraphStyle(
        'CustomBullet',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        leftIndent=14,
        firstLineIndent=-8,
        textColor=color_texto,
        alignment=TA_JUSTIFY,
        spaceAfter=1,
    )
    
    styles.add(custom_title)
    styles.add(custom_subtitle)
    styles.add(custom_h2)
    styles.add(custom_body)
    styles.add(custom_caption)
    styles.add(custom_bullet)
    
    margen_izq = 45
    margen_der = 45
    ancho_pagina = letter[0] - margen_izq - margen_der
    alto_banner = 64

    margen_sup = 30  # margen superior de todas las páginas; el banner solo existe en la página 1

    doc = SimpleDocTemplate(
        ruta_pdf_salida,
        pagesize=letter,
        leftMargin=margen_izq,
        rightMargin=margen_der,
        topMargin=margen_sup,
        bottomMargin=48,
    )

    # Espacio para el banner en la primera página (equivale al topMargin anterior)
    flowables = [Spacer(1, alto_banner + 18 - margen_sup)]
    color_fondo_card = HexColor('#F2F7F8')
    color_borde = HexColor('#D3E2E6')

    style_kpi_titulo = ParagraphStyle('KpiTitulo', parent=styles['Normal'], fontName='Helvetica-Bold',
                                      fontSize=7, leading=9, textColor=color_suave, alignment=1)
    style_kpi_valor = ParagraphStyle('KpiValor', parent=styles['Normal'], fontName='Helvetica-Bold',
                                     fontSize=15, leading=18, textColor=color_primario, alignment=1)
    style_kpi_delta = ParagraphStyle('KpiDelta', parent=styles['Normal'], fontName='Helvetica-Bold',
                                     fontSize=7, leading=9, alignment=1)

    # ── TARJETAS KPI (vectoriales) ────────────────────────────────────────────
    flowables.append(_titulo_seccion("INDICADORES CLAVE DEL PERIODO", ancho_pagina, color_secundario, custom_h2))
    flowables.append(Spacer(1, 14))

    if kpis:
        gap = 10
        ancho_card = (ancho_pagina * 0.84 - 2 * gap) / 3.0
        celdas = []
        for k in kpis:
            color_d = color_secundario
            contenido = [
                Paragraph(k['titulo'].upper(), style_kpi_titulo),
                Spacer(1, 4),
                Paragraph(k['valor'], style_kpi_valor),
                Spacer(1, 2),
                Paragraph(k.get('delta', '') or '&nbsp;', ParagraphStyle('d', parent=style_kpi_delta, textColor=color_d)),
            ]
            celdas.append(contenido)
        fila = [celdas[0], '', celdas[1], '', celdas[2]]
        tabla_kpi = Table([fila], colWidths=[ancho_card, gap, ancho_card, gap, ancho_card])
        estilo = [
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]
        for idx, k in enumerate(kpis):
            c = idx * 2
            estilo += [
                ('BACKGROUND', (c, 0), (c, 0), color_fondo_card),
                ('BOX', (c, 0), (c, 0), 0.6, color_borde),
                ('LINEABOVE', (c, 0), (c, 0), 1.5, color_acento),
            ]
        tabla_kpi.setStyle(TableStyle(estilo))
        flowables.append(tabla_kpi)
    elif ruta_kpis and os.path.exists(ruta_kpis):
        try:
            img_reader = ImageReader(ruta_kpis)
            img_w, img_h = img_reader.getSize()
            ancho_d, alto_d = _escalar_imagen(img_w, img_h, max_ancho=ancho_pagina * 0.6, max_alto=190)
            flowables.append(Image(ruta_kpis, width=ancho_d, height=alto_d))
        except Exception as e:
            flowables.append(Paragraph(f"<i>Error cargando KPIs: {str(e)}</i>", styles['CustomCaption']))
    flowables.append(Spacer(1, 16))

    # ── GRÁFICO HISTÓRICO ─────────────────────────────────────────────────────
    flowables.append(_titulo_seccion("EVOLUCIÓN DEL CUMPLIMIENTO DE ENTREGAS", ancho_pagina, color_secundario, custom_h2))
    flowables.append(Spacer(1, 14))

    if ruta_barras and os.path.exists(ruta_barras):
        try:
            img_reader = ImageReader(ruta_barras)
            img_w, img_h = img_reader.getSize()
            ancho_d, alto_d = _escalar_imagen(img_w, img_h, max_ancho=ancho_pagina, max_alto=235)
            img = Image(ruta_barras, width=ancho_d, height=alto_d)
            img.hAlign = 'CENTER'
            flowables.append(img)
        except Exception as e:
            flowables.append(Paragraph(f"<i>Error cargando barras: {str(e)}</i>", styles['CustomCaption']))
    else:
        flowables.append(Paragraph("<i>[Gráfica no encontrada]</i>", styles['CustomCaption']))
    flowables.append(Spacer(1, 6))

    # La leyenda de clasificación vive únicamente dentro del gráfico (esquina superior derecha).
    flowables.append(Spacer(1, 24))

    # ── RESUMEN EJECUTIVO ─────────────────────────────────────────────────────
    flowables.append(_titulo_seccion("RESUMEN EJECUTIVO", ancho_pagina, color_secundario, custom_h2))
    flowables.append(Spacer(1, 14))
    flowables.extend(parse_simple_markdown(texto_agente, styles))

    # ── MÓDULO 2 (página 2): título → síntesis del análisis (IA) → gráfico ──
    if grafica_tornado or texto_modulo_2:
        flowables.append(PageBreak())

        # a) Título
        flowables.append(_titulo_seccion("2. Análisis de Proveedores Críticos", ancho_pagina, color_secundario, custom_h2))
        flowables.append(Spacer(1, 12))

        # b) Síntesis ejecutiva generada por el agente LLM (analisis_2)
        if texto_modulo_2:
            flowables.extend(parse_simple_markdown(texto_modulo_2.strip(), styles))
            flowables.append(Spacer(1, 10))

        # c) Gráfico (Visualización)
        if grafica_tornado and os.path.exists(grafica_tornado):
            try:
                img_reader = ImageReader(grafica_tornado)
                img_w, img_h = img_reader.getSize()
                ancho_d, alto_d = _escalar_imagen(img_w, img_h, max_ancho=ancho_pagina, max_alto=520)
                img = Image(grafica_tornado, width=ancho_d, height=alto_d)
                img.hAlign = 'CENTER'
                flowables.append(img)
            except Exception as e:
                flowables.append(Paragraph(f"<i>Error cargando gráfica: {str(e)}</i>", styles['CustomCaption']))

    # ── PIE DE PÁGINA ─────────────────────────────────────────────────────────
    def dibujar_encabezado_pie(canvas, doc):
        canvas.saveState()
        page_w, page_h = letter
        margen = margen_izq

        # Banner superior (solo en la primera página)
        if doc.page == 1:
            canvas.setFillColor(HexColor('#0F3D4C'))
            canvas.rect(0, page_h - alto_banner, page_w, alto_banner, stroke=0, fill=1)
            canvas.setFillColor(HexColor('#5E8FA0'))
            canvas.rect(0, page_h - alto_banner - 1.5, page_w, 1.5, stroke=0, fill=1)

            canvas.setFillColor(HexColor('#FFFFFF'))
            canvas.setFont('Helvetica-Bold', 17)
            canvas.drawString(margen, page_h - 30, "Informe Ejecutivo de Gestión de Suministro")
            canvas.setFont('Helvetica', 9)
            canvas.setFillColor(HexColor('#BFD6DC'))
            sub = "Desempeño de proveedores y cumplimiento de entregas"
            canvas.drawString(margen, page_h - 46, sub)

            canvas.setFont('Helvetica-Bold', 8)
            canvas.setFillColor(HexColor('#FFFFFF'))
            if periodo:
                canvas.drawRightString(page_w - margen, page_h - 30, f"PERIODO: {periodo}")
            canvas.setFont('Helvetica', 8)
            canvas.setFillColor(HexColor('#BFD6DC'))
            canvas.drawRightString(page_w - margen, page_h - 46, f"Emitido: {datetime.now().strftime('%d/%m/%Y')}")

        # Pie de página
        canvas.setStrokeColor(HexColor('#D3E2E6'))
        canvas.setLineWidth(0.5)
        canvas.line(margen, 38, page_w - margen, 38)
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(HexColor('#6B7280'))
        canvas.drawString(margen, 26, "Confidencial — Uso exclusivo de la Mesa Directiva")
        canvas.setFont('Helvetica-Bold', 7)
        canvas.setFillColor(HexColor('#14566B'))
        canvas.drawRightString(page_w - margen, 26, f"Página {doc.page}")
        canvas.restoreState()
        
    try:
        doc.build(flowables, onFirstPage=dibujar_encabezado_pie, onLaterPages=dibujar_encabezado_pie)
        print(f"Reporte PDF generado exitosamente en: {ruta_pdf_salida}")
        return True
    except Exception as e:
        print(f"Ocurrió un error al compilar el PDF: {e}")
        return False
