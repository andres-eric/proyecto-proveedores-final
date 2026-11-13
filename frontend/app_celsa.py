"""
CELSA AI Suministros — Capa de presentación (Streamlit)
=======================================================

Este archivo es SOLO interfaz. No modifica ni duplica lógica de negocio: llama a las
funciones reales del backend (ETL en Pandas, agentes LangChain y generador de PDF).

Cómo ejecutarlo (desde la raíz del proyecto):

    pip install streamlit
    streamlit run frontend/app_celsa.py

Dónde conectar tus variables
----------------------------
Todo el acoplamiento con el backend está concentrado en TRES funciones, marcadas con
el encabezado  ">>> PUNTO DE CONEXIÓN <<<"  :

    1. ejecutar_etl()          -> Fase 1: datos + métricas + gráficas
    2. ejecutar_motor_ia()     -> Fase 2: analisis_1() y analisis_2()
    3. generar_informe_pdf()   -> Fase 3: ReportLab

El resto del archivo (CSS, layout, efecto máquina de escribir, descarga) no necesita cambios.
"""

import importlib.util
import os
import sys
import time
import traceback
from pathlib import Path

import streamlit as st

# ──────────────────────────────────────────────────────────────────────────────
# RUTAS DEL PROYECTO
# ──────────────────────────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
os.chdir(ROOT_DIR)  # el backend resuelve .env y rutas relativas desde la raíz del proyecto

RUTA_KPIS = str(ROOT_DIR / "tarjetas_ejecutivas.png")
RUTA_BARRAS = str(ROOT_DIR / "volumen_total_mes.png")
RUTA_M2_TORNADO = str(ROOT_DIR / "modulo2_tornado.png")
RUTA_M3_CANTIDAD = str(ROOT_DIR / "modulo3_cantidad.png")
RUTA_M3_PROVEEDORES = str(ROOT_DIR / "modulo3_proveedores.png")
RUTA_PDF = ROOT_DIR / "archivos_pdf" / "Reporte_Operativo_Pipeline.pdf"

VELOCIDAD_ESCRITURA = 0.05  # segundos por palabra en el efecto máquina de escribir


# ──────────────────────────────────────────────────────────────────────────────
# IMPORTACIONES DEL BACKEND (perezosas y cacheadas)
# ──────────────────────────────────────────────────────────────────────────────
def _cargar_modulo_desde_archivo(nombre: str, ruta: Path):
    """
    Los agentes viven en la carpeta `langchain/`, cuyo nombre choca con el paquete real
    `langchain`. Por eso se cargan por ruta de archivo (misma técnica que generar_reporte_completo.py).
    """
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = modulo
    spec.loader.exec_module(modulo)
    return modulo


@st.cache_resource(show_spinner=False)
def cargar_backend() -> dict:
    """
    >>> PUNTO DE CONEXIÓN (importaciones) <<<
    Importa las funciones reales del backend UNA sola vez por sesión del servidor.
    Se importa de forma perezosa para que la interfaz cargue aunque la BD/API esté caída
    (el error se mostrará en pantalla al ejecutar el pipeline, no al abrir la app).
    """
    from datos.carga_datos import (
        obtener_datos_completos,
        obtener_datos_kpi_detalle,
        obtener_datos_inspeccion_categoria,
    )
    from etl.datos_analisis_resumen_general import datos_historicos
    from graficos.graficas_resumen import generar_imagen_tarjetas_kpi_desde_df, graficar_distribucion_volumen_mes
    from graficos.graficas_modulo2 import graficar_modulo_2
    from graficos.graficas_analisis_cantidad import graficar_analisis_cantidad
    from graficos.graficas_modulo3 import graficar_modulo_3_desde_datos
    from pdf_generator.pdf_generator import generar_pdf_reporte, construir_kpis_cantidad

    resumen_agent = _cargar_modulo_desde_archivo(
        "resumen_agent", ROOT_DIR / "langchain" / "Analisis_Continuidad_Negocio_1" / "resumen_agent.py")
    analisis_2_agent = _cargar_modulo_desde_archivo(
        "analisis_2_agent", ROOT_DIR / "langchain" / "Analisis_evaluacion_Riesgo_2" / "Analisis_2.py")
    # Módulo 3: agentes LangGraph de cantidad (resumen) y de proveedores (detalle)
    agente_cantidad = _cargar_modulo_desde_archivo(
        "agente_cantidad", ROOT_DIR / "langchain" / "langrahpgrap" / "Analisis_evaluacion_cantidad_3" / "agente.py")
    agente_cantidad_detalle = _cargar_modulo_desde_archivo(
        "agente_cantidad_detalle", ROOT_DIR / "langchain" / "langrahpgrap" / "Analisis_evaluacion_cantidad_3 _detalle" / "agente.py")

    return {
        "obtener_datos_completos": obtener_datos_completos,
        "obtener_datos_kpi_detalle": obtener_datos_kpi_detalle,
        "obtener_datos_inspeccion_categoria": obtener_datos_inspeccion_categoria,
        "datos_historicos": datos_historicos,
        "generar_imagen_tarjetas_kpi_desde_df": generar_imagen_tarjetas_kpi_desde_df,
        "graficar_distribucion_volumen_mes": graficar_distribucion_volumen_mes,
        "graficar_modulo_2": graficar_modulo_2,
        "graficar_analisis_cantidad": graficar_analisis_cantidad,
        "graficar_modulo_3_desde_datos": graficar_modulo_3_desde_datos,
        "grafo_cantidad": agente_cantidad.grafo,
        "grafo_cantidad_detalle": agente_cantidad_detalle.grafo,
        "construir_kpis_cantidad": construir_kpis_cantidad,
        "analisis_1": resumen_agent.analisis_1,
        "analisis_2": analisis_2_agent.analisis_2,
        "generar_pdf_reporte": generar_pdf_reporte,
    }


# ──────────────────────────────────────────────────────────────────────────────
# >>> PUNTO DE CONEXIÓN 1 <<<  FASE 1: ETL Y PROCESAMIENTO
# ──────────────────────────────────────────────────────────────────────────────
def ejecutar_etl(status) -> dict:
    """
    Ejecuta el ETL real y genera las gráficas. Cada `status.write` se muestra con
    el desglose exacto de los pasos operativos del pipeline para máxima visibilidad.

    Retorna un dict con los DataFrames/rutas que consumen las fases siguientes.
    """
    backend = cargar_backend()

    status.write("🚀 **Iniciando pipeline de generación de reporte...**")
    time.sleep(0.2)

    status.write("📥 **[1/4] Obteniendo datos y calculando métricas históricas...**")
    status.write("&nbsp;&nbsp;&nbsp;&nbsp;↳ Conectando con la base de datos y extrayendo registros...")
    df_base = backend["obtener_datos_completos"]()

    status.write("&nbsp;&nbsp;&nbsp;&nbsp;↳ Calculando métricas históricas y aislando último mes evaluado...")
    df_historico = backend["datos_historicos"](df_base)
    ultimo_mes = df_historico.iloc[0:1]

    status.write("📊 **[2/4] Generando gráficas (Tarjetas KPI y Volumen Mensual)...**")
    status.write("&nbsp;&nbsp;&nbsp;&nbsp;↳ Renderizando tarjetas ejecutivas de KPI (cumplimiento, riesgo, calidad)...")
    backend["generar_imagen_tarjetas_kpi_desde_df"](df_historico, ruta_salida=RUTA_KPIS)

    status.write("&nbsp;&nbsp;&nbsp;&nbsp;↳ Generando gráfico de barras apiladas de volumen histórico...")
    backend["graficar_distribucion_volumen_mes"](df_historico, ruta_salida=RUTA_BARRAS)

    status.write("&nbsp;&nbsp;&nbsp;&nbsp;↳ Extrayendo detalle de proveedores críticos y graficando Tornado...")
    datos_kpi_detalle = backend["obtener_datos_kpi_detalle"]()
    datos_inspeccion = backend["obtener_datos_inspeccion_categoria"]()
    backend["graficar_modulo_2"](RUTA_M2_TORNADO)

    status.write("&nbsp;&nbsp;&nbsp;&nbsp;↳ Graficando cumplimiento de cantidad y proveedores con faltantes...")
    backend["graficar_analisis_cantidad"](RUTA_M3_CANTIDAD)
    backend["graficar_modulo_3_desde_datos"](RUTA_M3_PROVEEDORES)

    status.write("✨ **Gráficas creadas en la raíz del proyecto exitosamente.**")

    return {
        "df_historico": df_historico,
        "ultimo_mes": ultimo_mes,
        "datos_kpi_detalle": datos_kpi_detalle,
        "datos_inspeccion": datos_inspeccion,
    }


# ──────────────────────────────────────────────────────────────────────────────
# >>> PUNTO DE CONEXIÓN 2 <<<  FASE 2: MOTOR DE INFERENCIA IA
# ──────────────────────────────────────────────────────────────────────────────
def ejecutar_motor_ia(etl: dict) -> dict:
    """
    Llama a los agentes LangChain reales. Retorna:
      - texto_1: resumen ejecutivo de continuidad (analisis_1)
      - texto_2: análisis de proveedores críticos (analisis_2)
      - texto_3: resumen de cumplimiento de cantidad (agente de cantidad)
      - texto_3_proveedores: proveedores con incumplimiento de cantidad (agente de detalle)
      - kpis_cantidad: tarjetas de la sección 3, con los mismos valores que usa el agente
    """
    backend = cargar_backend()
    texto_1 = backend["analisis_1"](datos=etl["ultimo_mes"])
    texto_2 = backend["analisis_2"](etl["datos_kpi_detalle"], etl["datos_inspeccion"])

    estado_cantidad = backend["grafo_cantidad"].invoke({})
    finales = estado_cantidad.get("texto_final_cantidad")
    texto_3 = finales[-1] if finales else estado_cantidad.get("borrador_cantidad", "")
    estado_detalle = backend["grafo_cantidad_detalle"].invoke({})

    return {
        "texto_1": texto_1,
        "texto_2": texto_2,
        "texto_3": texto_3,
        "texto_3_proveedores": estado_detalle.get("texto_analisis_3"),
        "kpis_cantidad": backend["construir_kpis_cantidad"](estado_cantidad),
    }


# ──────────────────────────────────────────────────────────────────────────────
# >>> PUNTO DE CONEXIÓN 3 <<<  FASE 3: ENSAMBLAJE DEL PDF (ReportLab)
# ──────────────────────────────────────────────────────────────────────────────
def _construir_kpis(df_historico) -> tuple:
    """Arma la lista de KPIs y el periodo exactamente como lo hace generar_reporte_completo.py."""
    act, ant = df_historico.iloc[0], df_historico.iloc[1]
    d_c = act["tasa_cumpli_perfecto"] - ant["tasa_cumpli_perfecto"]
    d_r = act["tasa_riesgo_critico"] - ant["tasa_riesgo_critico"]
    verde, rojo = "#16A34A", "#B91C1C"
    kpis = [
        {"titulo": "Cumplimiento", "valor": f"{act['tasa_cumpli_perfecto']:.1f}%",
         "delta": f"{d_c:+.2f} pp vs mes anterior",
         "color": verde if d_c >= 0 else rojo, "acento": "#16A34A"},
        {"titulo": "Riesgo crítico", "valor": f"{act['tasa_riesgo_critico']:.1f}%",
         "delta": f"{d_r:+.2f} pp vs mes anterior",
         "color": verde if d_r <= 0 else rojo, "acento": "#B91C1C"},
        {"titulo": "Unidades defectuosas",
         "valor": f"{int(act['cantidad_recibida_defectuosa']):,}".replace(",", "."),
         "delta": "Cantidad recibida defectuosa", "color": "#6B7280", "acento": "#EA580C"},
    ]
    return kpis, str(act["anio-mes"])


def generar_informe_pdf(etl: dict, ia: dict) -> bytes:
    """Llama al generador real de ReportLab y devuelve los bytes del PDF para la descarga."""
    backend = cargar_backend()
    RUTA_PDF.parent.mkdir(exist_ok=True)
    kpis, periodo = _construir_kpis(etl["df_historico"])

    exito = backend["generar_pdf_reporte"](
        texto_agente=ia["texto_1"],
        ruta_pdf_salida=str(RUTA_PDF),
        ruta_kpis=RUTA_KPIS,
        ruta_barras=RUTA_BARRAS,
        kpis=kpis,
        periodo=periodo,
        grafica_tornado=RUTA_M2_TORNADO,
        texto_modulo_2=ia["texto_2"],
        grafica_cantidad=RUTA_M3_CANTIDAD,
        texto_modulo_3=ia.get("texto_3"),
        kpis_cantidad=ia.get("kpis_cantidad"),
        grafica_proveedores_cantidad=RUTA_M3_PROVEEDORES,
        texto_proveedores_cantidad=ia.get("texto_3_proveedores"),
    )
    if not exito or not RUTA_PDF.exists():
        raise RuntimeError("El generador de PDF no pudo crear el informe. Revisa la consola del servidor.")
    return RUTA_PDF.read_bytes()


# ══════════════════════════════════════════════════════════════════════════════
# A PARTIR DE AQUÍ: SOLO INTERFAZ (no requiere cambios)
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="CELSA AI",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="collapsed",
)

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* Reglas globales de texto y tipografía */
html, body, [class*="css"], .stMarkdown, p, span, label, li {
    font-family: 'Inter', sans-serif !important;
    color: #F1F5F9 !important;
}

.stApp {
    background:
        radial-gradient(1200px 500px at 85% -10%, rgba(20,86,107,0.35), transparent 65%),
        radial-gradient(900px 400px at -10% 10%, rgba(94,143,160,0.25), transparent 60%),
        #081419 !important;
}

header[data-testid="stHeader"] { background: transparent !important; }
.block-container { padding-top: 2.2rem; max-width: 860px; }

/* Hero */
.hero {
    padding: 2.2rem 2rem 1.8rem 2rem;
    border-radius: 20px;
    background: linear-gradient(135deg, rgba(15,61,76,0.95) 0%, rgba(20,86,107,0.85) 60%, rgba(94,143,160,0.65) 100%);
    border: 1px solid rgba(191,214,220,0.3);
    box-shadow: 0 18px 50px rgba(0,0,0,0.55), inset 0 1px 0 rgba(255,255,255,0.1);
    margin-bottom: 1.4rem;
}
.hero .chip {
    display: inline-block; font-size: 0.72rem; font-weight: 700; letter-spacing: .14em;
    color: #E2E8F0 !important; background: rgba(255,255,255,0.12); border: 1px solid rgba(191,214,220,0.4);
    padding: .25rem .75rem; border-radius: 999px; margin-bottom: .9rem;
}
.hero h1 { font-size: 2.3rem; font-weight: 800; color: #FFFFFF !important; margin: 0 0 .35rem 0; letter-spacing: -.02em; }
.hero h1 span { background: linear-gradient(90deg,#A5F3FC,#67E8F9); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.hero p { color: #E2E8F0 !important; font-size: 1rem; margin: 0; line-height: 1.5; }

/* Botón principal */
div.stButton > button[kind="primary"] {
    width: 100%; padding: 1rem 1.4rem; font-size: 1.05rem; font-weight: 700; border: 0; border-radius: 14px;
    color: #FFFFFF !important; background: linear-gradient(90deg, #14566B, #0284C7);
    box-shadow: 0 10px 30px rgba(2,132,199,0.35); transition: transform .15s ease, box-shadow .15s ease;
}
div.stButton > button[kind="primary"]:hover { transform: translateY(-2px); box-shadow: 0 14px 38px rgba(2,132,199,0.5); }
div.stButton > button[kind="primary"]:active { transform: translateY(0); }

/* Títulos de fase */
.fase { display:flex; align-items:center; gap:.75rem; margin: 1.8rem 0 .7rem 0; }
.fase .num {
    padding: 0 .65rem; height: 32px; border-radius: 999px; display:flex; align-items:center; justify-content:center;
    font-weight:800; font-size:.85rem; color:#0B1A21 !important; background: linear-gradient(135deg,#67E8F9,#38BDF8);
    box-shadow: 0 2px 8px rgba(56,189,248,0.4);
}
.fase .tit { font-size: 1.2rem; font-weight: 700; color: #F8FAFC !important; }
.ia-badge {
    display:inline-block; font-size:.72rem; font-weight:700; letter-spacing:.12em; color:#67E8F9 !important;
    border:1px solid rgba(103,232,249,.45); background: rgba(103,232,249,.08); padding:.2rem .65rem; border-radius:6px; margin-bottom:.5rem;
}

/* Chat messages (Contenedores IA) */
[data-testid="stChatMessage"] {
    background-color: rgba(15, 61, 76, 0.45) !important;
    border: 1px solid rgba(143, 227, 245, 0.28) !important;
    border-radius: 16px !important;
    padding: 1.2rem 1.4rem !important;
    margin-bottom: 1rem !important;
    box-shadow: 0 8px 24px rgba(0,0,0,0.3) !important;
}
[data-testid="stChatMessage"] * {
    color: #F8FAFC !important;
    font-size: 0.98rem !important;
    line-height: 1.65 !important;
}

/* Status widget */
[data-testid="stStatusWidget"] {
    background-color: rgba(15, 61, 76, 0.4) !important;
    border: 1px solid rgba(94, 143, 160, 0.4) !important;
    border-radius: 14px !important;
}
[data-testid="stStatusWidget"] * {
    color: #E2E8F0 !important;
}

/* Expander */
[data-testid="stExpander"] {
    background-color: rgba(15, 61, 76, 0.3) !important;
    border: 1px solid rgba(94, 143, 160, 0.3) !important;
    border-radius: 14px !important;
}
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary span, [data-testid="stExpander"] svg {
    color: #E2E8F0 !important;
    fill: #E2E8F0 !important;
    font-weight: 600 !important;
}

/* Métricas */
div[data-testid="stMetric"] {
    background: rgba(15, 61, 76, 0.35) !important; border: 1px solid rgba(191,214,220,0.22) !important;
    border-radius: 14px !important; padding: 1rem 1.1rem !important;
    box-shadow: 0 6px 16px rgba(0,0,0,0.25) !important;
}
div[data-testid="stMetricValue"] * { color: #FFFFFF !important; font-weight: 800 !important; font-size: 1.7rem !important; }
div[data-testid="stMetricLabel"] p { color: #94A3B8 !important; font-weight: 700 !important; letter-spacing: .06em; text-transform: uppercase; font-size:.75rem !important; }

/* Subtítulos y Captions */
.stCaption, [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * {
    color: #94A3B8 !important;
    font-size: 0.85rem !important;
}

/* Alertas informativas */
[data-testid="stAlert"] {
    background-color: rgba(15, 61, 76, 0.5) !important;
    border: 1px solid rgba(56, 189, 248, 0.35) !important;
    border-radius: 12px !important;
}
[data-testid="stAlert"] * {
    color: #F8FAFC !important;
}

hr { border-color: rgba(191,214,220,0.18) !important; }
footer { visibility: hidden; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def titulo_fase(badge: str, texto: str):
    st.markdown(f'<div class="fase"><div class="num">{badge}</div><div class="tit">{texto}</div></div>',
                unsafe_allow_html=True)


def _escapar_markdown(texto: str) -> str:
    """Evita que '$' se interprete como fórmula LaTeX en st.markdown."""
    return texto.replace("$", "\\$")


def maquina_de_escribir(texto: str, delay: float = VELOCIDAD_ESCRITURA):
    """Muestra `texto` palabra por palabra con cursor parpadeante (efecto de redacción en vivo)."""
    placeholder = st.empty()
    acumulado = ""
    for palabra in texto.split(" "):
        acumulado += palabra + " "
        placeholder.markdown(_escapar_markdown(acumulado) + " ▌")
        time.sleep(delay)
    placeholder.markdown(_escapar_markdown(texto))


def mostrar_kpis(df_historico):
    """Tarjetas con los KPIs reales del último periodo (calculados por el ETL)."""
    kpis, periodo = _construir_kpis(df_historico)
    st.caption(f"Periodo analizado: **{periodo}**")
    columnas = st.columns(len(kpis))
    for col, k in zip(columnas, kpis):
        col.metric(k["titulo"], k["valor"], k["delta"], delta_color="off")


def mostrar_resultados_ia(ia: dict, animar: bool):
    """Pinta los dos análisis de la IA con tipografía clara y de alto contraste."""
    secciones = [
        ("Resumen ejecutivo · Continuidad de negocio", ia["texto_1"]),
        ("Análisis de proveedores críticos", ia["texto_2"]),
        ("Cumplimiento de cantidad", ia.get("texto_3")),
        ("Proveedores con incumplimiento de cantidad", ia.get("texto_3_proveedores")),
    ]
    for titulo, texto in secciones:
        if not texto:
            continue
        with st.chat_message("ai", avatar="🧠"):
            st.markdown(f'<span class="ia-badge">{titulo.upper()}</span>', unsafe_allow_html=True)
            if animar:
                maquina_de_escribir(texto)
            else:
                st.markdown(_escapar_markdown(texto))


def mostrar_descarga(pdf_bytes: bytes):
    st.success("✅ **Reporte gerencial C-Level compilado exitosamente.** Listo para entrega a Mesa Directiva.", icon="📑")
    st.download_button(
        label="⬇️ Descargar Informe Gerencial (PDF Oficial)",
        data=pdf_bytes,
        file_name="Reporte_Operativo_CELSA.pdf",
        mime="application/pdf",
        use_container_width=True,
        key="descarga_pdf",
    )


def mostrar_error(etapa: str, exc: Exception):
    st.error(f"Ocurrió un error en {etapa}: {exc}", icon="🚨")
    with st.expander("Detalle técnico"):
        st.code(traceback.format_exc())


# ──────────────────────────────────────────────────────────────────────────────
# HEADER
# ──────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="hero">
        <div class="chip">INTELIGENCIA ARTIFICIAL · SUMINISTROS</div>
        <h1>CELSA <span>AI</span></h1>
        <p>Del dato crudo al informe de Mesa Directiva: ETL, análisis de riesgo con IA y entrega en PDF, en un solo flujo.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

ejecutar = st.button("🚀 Ejecutar Pipeline Analítico de Inteligencia Artificial", type="primary")

# ──────────────────────────────────────────────────────────────────────────────
# EJECUCIÓN DEL PIPELINE
# ──────────────────────────────────────────────────────────────────────────────
if ejecutar:
    st.session_state.pop("resultado", None)
    t0 = time.time()

    # ── FASE 1: ETL ───────────────────────────────────────────────────────────
    titulo_fase("FASE 1", "Extracción y Preparación de Datos (ETL)")
    with st.status("🔄 Ejecutando ETL y procesando registros operativos...", expanded=True) as status:
        try:
            etl = ejecutar_etl(status)
        except Exception as exc:
            status.update(label="❌ Falló el ETL", state="error", expanded=True)
            mostrar_error("la Fase 1 (ETL)", exc)
            st.stop()
        status.update(label="✅ Datos estructurados exitosamente", state="complete", expanded=False)
    mostrar_kpis(etl["df_historico"])

    with st.expander("📊 Ver visualizaciones generadas para el reporte"):
        st.image(RUTA_BARRAS, caption="Evolución del cumplimiento de entregas", use_container_width=True)
        st.image(RUTA_M2_TORNADO, caption="Proveedores críticos: retrasos logísticos vs. defectos de calidad",
                 use_container_width=True)
        st.image(RUTA_M3_CANTIDAD, caption="Evolución del cumplimiento de cantidad", use_container_width=True)
        st.image(RUTA_M3_PROVEEDORES, caption="Proveedores con órdenes con faltantes: mes evaluado vs. acumulado",
                 use_container_width=True)

    # ── FASE 2: MOTOR IA ──────────────────────────────────────────────────────
    st.divider()
    titulo_fase("FASE 2", "🧠 [3/4] Motor de Inferencia IA (LangChain)")
    try:
        with st.spinner("⚡ La Inteligencia Artificial está cruzando variables y detectando riesgos sistémicos... por favor espere."):
            ia = ejecutar_motor_ia(etl)
    except Exception as exc:
        mostrar_error("la Fase 2 (Motor IA)", exc)
        st.stop()
    mostrar_resultados_ia(ia, animar=True)

    # ── FASE 3: PDF ───────────────────────────────────────────────────────────
    st.divider()
    titulo_fase("FASE 3", "📄 [4/4] Construyendo el Documento PDF Final (ReportLab)")
    with st.status("📄 Renderizando Informe Gerencial C-Level...", expanded=True) as status:
        try:
            status.write("🧩 Integrando tarjetas ejecutivas, gráficos de volumen y tornado…")
            status.write("📝 Incrustando narrativa analítica generada por el LLM…")
            status.write("🖨️ Compilando documento PDF en alta resolución con ReportLab…")
            pdf_bytes = generar_informe_pdf(etl, ia)
        except Exception as exc:
            status.update(label="❌ Falló la generación del PDF", state="error", expanded=True)
            mostrar_error("la Fase 3 (PDF)", exc)
            st.stop()
        status.update(label="✅ Informe renderizado exitosamente", state="complete", expanded=False)

    # Guardar en sesión para persistir ante interacción
    st.session_state["resultado"] = {
        "etl_kpis": etl["df_historico"],
        "ia": ia,
        "pdf": pdf_bytes,
        "segundos": time.time() - t0,
    }
    mostrar_descarga(pdf_bytes)
    st.caption(f"⏱️ Pipeline completo ejecutado en {st.session_state['resultado']['segundos']:.1f} segundos.")

# ──────────────────────────────────────────────────────────────────────────────
# VISTA ESTÁTICA (tras un rerun, p. ej. al pulsar "Descargar")
# ──────────────────────────────────────────────────────────────────────────────
elif "resultado" in st.session_state:
    res = st.session_state["resultado"]
    titulo_fase("FASE 1", "Extracción y Preparación de Datos (ETL)")
    mostrar_kpis(res["etl_kpis"])
    st.divider()
    titulo_fase("FASE 2", "🧠 [3/4] Motor de Inferencia IA (LangChain)")
    mostrar_resultados_ia(res["ia"], animar=False)
    st.divider()
    titulo_fase("FASE 3", "📄 [4/4] Documento PDF Generado")
    mostrar_descarga(res["pdf"])
    st.caption(f"⏱️ Última ejecución completada en {res['segundos']:.1f} segundos.")
else:
    st.info("Presiona el botón para ejecutar el flujo completo con datos reales.", icon="ℹ️")

