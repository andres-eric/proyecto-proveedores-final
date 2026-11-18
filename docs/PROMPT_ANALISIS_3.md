# Prompt: Crear el Análisis 3 — Cumplimiento de Cantidad y Primera Entrega

> Copia todo este documento y pégalo a Claude como contexto del proyecto.

---

## 1. Qué es este proyecto

Pipeline en Python que genera un **reporte operativo mensual de proveedores nacionales** (CELSA). Toma datos de APIs internas, calcula métricas con pandas, genera gráficas con matplotlib, redacta textos ejecutivos con un LLM local (Ollama `qwen2.5-coder:14b`, `temperature=0`) mediante LangChain/LangGraph, y arma un PDF con ReportLab. También tiene un frontend en Streamlit.

Ya existen dos análisis:
- **Análisis 1, Continuidad de Negocio**: volumen total, cumplimiento óptimo, tasa de riesgo crítico del último mes cerrado.
- **Análisis 2, Evaluación de Riesgo**: top proveedores con riesgo logístico (zona roja/negra) y top con defectos de calidad, cruce de doble afectación.

**Objetivo:** crear el **Análisis 3, Cantidad ingresada vs. cumplimiento de primera entrega**, siguiendo exactamente los mismos patrones.

---

## 2. Estructura del proyecto

```
.
├── .env                         # variables de entorno (cargado por los agentes y langgraph.json)
├── langgraph.json               # registra los grafos para `langgraph dev`
├── generar_reporte_completo.py  # ORQUESTADOR CLI: datos → gráficas → agentes → PDF
├── datos/
│   └── carga_datos.py           # EXTRACCIÓN: llamadas a APIs (requests + reintentos)
├── etl/
│   ├── datos_analisis_resumen_general.py  # datos_historicos()  → Análisis 1
│   ├── datos_detalles.py                  # datos_modulo_2(), convertir_df_a_contexto_llm() → Análisis 2
│   ├── datos_analisis_cantidad_entrega.py # ← NUEVO, Análisis 3 (hoy solo es una copia de datos_historicos, hay que reescribirlo)
│   └── exportar_kpi_detalle.py
├── herramientas/funciones.py    # fecha_anterior(df) → 'YYYY-MM' del último mes CERRADO (max - 1)
├── graficos/
│   ├── graficas_resumen.py      # tarjetas KPI + barras de volumen (Análisis 1)
│   └── graficas_modulo2.py      # gráfico tornado (Análisis 2)
├── langchain/                   # ⚠ el nombre choca con el paquete `langchain`; se importa por ruta
│   ├── Analisis_Continuidad_Negocio_1/resumen_agent.py   # LEGACY: analisis_1(datos) -> str (cadena simple)
│   ├── Analisis_evaluacion_Riesgo_2/Analisis_2.py         # LEGACY: analisis_2(kpi_det, insp) -> str
│   └── langrahpgrap/            # NUEVA arquitectura LangGraph (escritor → auditor → corrector)
│       ├── Analisis_Continuidad_Negocio_1_/agente.py + promt_template_continuidad.py
│       ├── Analisis_evaluacion_Riesgo_2/agente.py    + promt_template_riesgo.py
│       └── Nodo_Padre/agente.py # grafo padre: continuidad → riesgo (subgrafos en secuencia)
├── modelo_config/utiils_config_llm.py  # obtener_llm() → ChatOllama
├── pdf_generator/pdf_generator.py      # generar_pdf_reporte(...)
├── frontend/app_celsa.py               # Streamlit: cargar_backend / ejecutar_etl / ejecutar_motor_ia / generar_informe_pdf
└── exportar_excel/generar_todos_los_excels.py
```

### Flujo actual
```
APIs → datos/carga_datos.py → etl/* → graficos/* (PNG en raíz)
                                    → agentes LLM (texto)
                                    → pdf_generator → archivos_pdf/Reporte_Operativo_Pipeline.pdf
```

---

## 3. Fuente de datos del Análisis 3

Ya existe la función de extracción en `datos/carga_datos.py`:

```python
def obtener_data_set_cantidad():
    url_api = "http://192.168.6.105:9091/api/v1/extractor/consulta_cantidad"
    # devuelve pd.DataFrame crudo (sin limpiar), o None
```

Columnas reales que devuelve (una fila por **proveedor × anio × mes**, ~379 filas):

| Columna | Tipo | Ejemplo |
|---|---|---|
| proveedor | str | WEICON COLOMBIA SAS |
| mes, anio | int | 10, 2026 |
| total, verde, amarilla, roja, negra | int | conteo de órdenes por semáforo |
| porcentajeCumplimientoVerde | float | 25.00 |
| nivelServicioTotal | float | 100.00 |
| **cumplimientoCantidadEntregada** | float | 75.0 (%) |
| **porcentajeCumplimientoPrimeraEntrega** | float | 100.00 (%) |
| **porcentajeIncumplimientoCantidad** | float | 25.0 (%) |
| **cantidadCumpleCantidad** | int | 3 (órdenes que cumplen cantidad) |
| **cantidadIncumplimiento** | int | 1 (órdenes que no cumplen cantidad) |
| **totalOrdenesCantidad** | int | 4 |
| **cantidadCumple1Entrega** | int | 3 (órdenes completas en 1ª entrega) |
| **totalPrimerasEntregas** | int | 3 |
| **cantidadIngresada** | int | 98 (unidades) |

> ⚠ Confirma conmigo la semántica exacta antes de redactar el prompt del LLM: parece que `cantidadCumple*`, `cantidadIncumplimiento` y `total*` son **conteos de órdenes**, mientras que `cantidadIngresada` son **unidades**. No mezcles las dos cosas en un mismo porcentaje.

---

## 4. Convenciones que DEBES respetar

1. **Mes evaluado = último mes cerrado.** El mes actual está incompleto:
   - Análisis 1 lo descarta con `[1:]` en `cambiar_nombre_head()` tras ordenar descendente.
   - Análisis 2 usa `fecha_anterior(df)` de `herramientas/funciones.py` (`max - 1 mes`).
   - Para el Análisis 3 usa `fecha_anterior()`. Crea la columna `anio-mes` igual que en el resto: `pd.to_datetime(df["anio"].astype(str) + "-" + df["mes"].astype(str)).dt.strftime("%Y-%m")`.
2. **Normalizar proveedor:** `.astype(str).str.strip().str.upper()`.
3. **Imports de raíz:** cada módulo agrega `ROOT_DIR` a `sys.path` (ver cabecera de `etl/datos_detalles.py`).
4. **Carpeta `langchain/`:** choca con el paquete real, así que los agentes se cargan por ruta con `importlib.util.spec_from_file_location` (ver `generar_reporte_completo.py` y `Nodo_Padre/agente.py`).
5. **Nombres únicos para evitar choques en `sys.modules` y en el estado compartido del grafo padre:**
   - plantilla: `promt_template_cantidad.py` (no reutilices nombres)
   - claves del estado con sufijo `_cantidad`: `borrador_cantidad`, `texto_final_cantidad`, `tiene_errores_cantidad`, `notas_auditor_cantidad`.
6. **Estado de LangGraph serializable:** convierte todo a `str` antes de devolverlo desde los nodos (numpy no se serializa en `langgraph dev`).
7. **Datos hacia el LLM en texto compacto**, no como DataFrame crudo. Usa el patrón de `convertir_df_a_contexto_llm()` (líneas `- Proveedor: X | ... `) y formatea miles con punto: `f"{int(v):,}".replace(",", ".")`.
8. **Estilo de los prompts** (ver `promt_template_riesgo.py`): rol COO, “cero alucinación”, un solo párrafo, sin signos +/− (“un aumento del X %”, “una caída del X %”), separador de miles con punto, arco narrativo numerado, y un auditor que responde exactamente `PERFECTO` o `ERROR: <regla>`.

---

## 5. Lo que hay que construir

### 5.1 ETL: `etl/datos_analisis_cantidad_entrega.py` (reescribir)
Reemplaza el contenido actual (es una copia de `datos_historicos`) por algo como:
- `preparar_datos_cantidad(df_crudo)`: crea `anio-mes`, normaliza proveedor.
- `resumen_cantidad_mes(df)`: totales del **mes evaluado** y del anterior (para la variación): unidades ingresadas, % de cumplimiento de cantidad y % de cumplimiento en primera entrega, **recalculados como ratio de sumas** (`sum(cantidadCumple1Entrega)/sum(totalPrimerasEntregas)`), no como promedio de porcentajes.
- `top_proveedores_cantidad(df, n=7)`: proveedores del mes evaluado con más órdenes incumplidas en cantidad o en primera entrega, ponderados por `cantidadIngresada`.
- `convertir_cantidad_a_contexto_llm(df)`: texto compacto para el LLM.
- Bloque `if __name__ == "__main__":` para probarlo solo.

### 5.2 Gráfica: `graficos/graficas_modulo3.py`
`graficar_modulo_3(ruta_salida="modulo3_cantidad.png") -> str`. Sugerencia: barras horizontales por proveedor (top N) que comparen el % de primera entrega y el % de cumplimiento de cantidad, o la evolución mensual de ambas tasas. Sigue el estilo de `graficas_modulo2.py`.

### 5.3 Agente LangGraph: `langchain/langrahpgrap/Analisis_Cantidad_Entrega_3/`
- `promt_template_cantidad.py` con `template_resumen`, `prompt_revision` y `prompt_corregir`.
- `agente.py` con la misma estructura que `Analisis_evaluacion_Riesgo_2/agente.py`:
  `START → nodo_carga_datos → nodo_analisis → nodo_revisar → (condicional) nodo_correccion → END`, y la variable `grafo` a nivel de módulo.
- Arco narrativo propuesto: (1) volumen ingresado y su variación, (2) tasa de cumplimiento en primera entrega y su variación, (3) brecha de cantidad (órdenes que no llegaron completas), (4) proveedores que concentran el incumplimiento. Sin recomendaciones inventadas.

### 5.4 Integración
- `langgraph.json`: agregar `"cantidad_entrega_3": "./langchain/langrahpgrap/Analisis_Cantidad_Entrega_3/agente.py:grafo"`.
- `Nodo_Padre/agente.py`: `cargar_grafo("Analisis_Cantidad_Entrega_3")`, agregar las claves `_cantidad` a `EstadoFlujo` y encadenar `riesgo → cantidad → END`.
- `pdf_generator/pdf_generator.py`: agregar parámetros `grafica_modulo_3=None, texto_modulo_3=None` y una sección nueva tras la del Módulo 2 (`PageBreak()` + `_titulo_seccion("3. Cumplimiento de Cantidad y Primera Entrega", ...)`), siguiendo el bloque de `grafica_tornado` / `texto_modulo_2`.
- `generar_reporte_completo.py` y `frontend/app_celsa.py` (`cargar_backend`, `ejecutar_etl`, `ejecutar_motor_ia`, `generar_informe_pdf`): llamar al ETL, la gráfica y el agente del Módulo 3 y pasar el resultado al PDF.

---

## 6. Detalles conocidos del código (para no romper nada)

- Hay **dos implementaciones de agentes en paralelo**: las *legacy* (`langchain/Analisis_*`, funciones `analisis_1` / `analisis_2` que usan el orquestador y Streamlit) y las de **LangGraph** (`langchain/langrahpgrap/`, usadas por `langgraph dev`). Pregúntame a cuál conectar el orquestador y el frontend para el Módulo 3. Mi propuesta es usar LangGraph (`grafo.invoke({})["texto_final_cantidad"][-1]`).
- En los `agente.py`, `PROMPT_DIR` apunta a `.../Analisis_Continuidad_Negocio_1` (sin el `_` final), una carpeta que no existe. Funciona solo porque `CURRENT_DIR` también está en `sys.path`. En el agente nuevo usa `CURRENT_DIR`.
- `prompt_corregir` del Análisis 1 menciona “Cuello de Botella / Doble Afectación”, que vienen copiados del Análisis 2. No repitas ese error en el 3: el corrector debe proteger el arco narrativo del 3.
- `Analisis_2_state.py` (legacy) fue borrado en el árbol de trabajo.
- Las APIs están en `192.168.6.105` (puertos 9091 y 8086). `realizar_peticion` reintenta 6 veces.

---

## 7. Cómo quiero que trabajes

1. Lee primero estos archivos de referencia: `etl/datos_detalles.py`, `langchain/langrahpgrap/Analisis_evaluacion_Riesgo_2/agente.py`, `promt_template_riesgo.py`, `langchain/langrahpgrap/Nodo_Padre/agente.py`, `pdf_generator/pdf_generator.py`, `generar_reporte_completo.py`.
2. Confírmame la semántica de las columnas (sección 3) y qué métricas exactas quieres narrar antes de escribir el prompt del LLM.
3. Implementa en este orden: ETL (probarlo con `python etl/datos_analisis_cantidad_entrega.py`) → gráfica → agente (probarlo con `python langchain/langrahpgrap/Analisis_Cantidad_Entrega_3/agente.py`) → Nodo_Padre + langgraph.json → PDF → orquestador/frontend.
4. No modifiques el comportamiento de los Análisis 1 y 2.
