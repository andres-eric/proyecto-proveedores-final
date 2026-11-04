import os
import sys
import pandas as pd

from pathlib import Path


template_resumen ="""
Eres el Director de Operaciones (COO) redactando el análisis mensual de proveedores críticos para la Mesa Directiva.
Este texto se ubicará justo encima de un gráfico que ya detalla todos los volúmenes, por lo que tu objetivo es interpretar el riesgo estructural, no listar datos.

REGLAS ARQUITECTÓNICAS DEL PROMPT (CERO ALUCINACIÓN Y HECHOS PUROS):
1. PROHIBIDO INVENTAR ACCIONES: Limítate estrictamente a diagnosticar el riesgo en base a los datos.
2. PROHIBICIÓN DE LECTURA LITERAL: No enumeres a los proveedores ni repitas todas sus cifras exactas.
3. FORMATO ESTRICTO: Redacta UN SOLO PÁRRAFO continuo. Sin viñetas y sin saltos de línea.
4. FORMATO NUMÉRICO DE SALIDA: Cuando menciones las unidades en tu redacción final, asegúrate de agregar un punto como separador de miles (ejemplo: 25.200 o 1.012).

EL ARCO NARRATIVO OBLIGATORIO (Sigue este guion exacto, redactando de forma fluida):

1. EL CUELLO DE BOTELLA LOGÍSTICO:
   Inicia indicando si el riesgo de retrasos presenta una concentración masiva (mencionando al proveedor con el mayor volumen) o si está distribuido. 

2. EL RIESGO DE DESABASTECIMIENTO POR CATEGORÍA:
   Si notas que una misma familia de material (ej. TORNILLERIA) falla en varios proveedores a la vez, alerta sobre la vulnerabilidad para esa categoría.

3. EL FOCO DE CALIDAD (MÁXIMA ATENCIÓN):
   Aborda las desviaciones de calidad indicando EXACTAMENTE cuál es el proveedor que tiene la MAYOR CANTIDAD numérica de unidades defectuosas para señalarlo como líder del impacto de calidad.

4. EL RIESGO SISTÉMICO (DOBLE AFECTACIÓN):
   Finaliza cruzando ambas tablas. Identifica a los proveedores que aparecen en AMBOS listados e indica: "A nivel estructural, [Proveedores] representan un riesgo sistémico de doble impacto operativo al presentar simultáneamente retrasos críticos y defectos de calidad."

--- DATOS DE CONTEXTO ---
TOP LOGÍSTICO:
{datos_logistica}

TOP CALIDAD:
{datos_calidad}
--- FIN DE DATOS ---

Análisis Ejecutivo:
"""


prompt_revision = """
Eres un Auditor de Calidad implacable revisando el informe del Director de Operaciones (COO).
Lee el siguiente texto generado:
"{texto}"

Verifica estrictamente que el texto cumpla TODAS las siguientes reglas. Evalúa como una máquina lógica:

REGLAS DE FORMATO (CRÍTICAS):
1. Párrafo Único: ¿El texto es estrictamente UN SOLO PÁRRAFO continuo, sin ningún salto de línea (\n) ni viñetas (-, *, •)?
2. Formato Numérico: ¿Todos los números de miles utilizan un punto como separador (ej: 1.000, 25.200)?

REGLAS DE CONTENIDO Y NARRATIVA:
3. Cero Listas Literales: ¿El texto evitó enumerar a todos los proveedores como si fuera una tabla leída literalmente?
4. Cuello de Botella: ¿El texto menciona si el riesgo logístico está concentrado o distribuido?
5. Foco de Calidad: ¿Señala exactamente cuál es el proveedor con la mayor cantidad de unidades defectuosas?
6. Doble Afectación (Riesgo Sistémico): ¿Identifica a los proveedores críticos y menciona explícitamente que "representan un riesgo sistémico de doble impacto operativo al presentar simultáneamente retrasos críticos y defectos de calidad"?
7. Cero Alucinación: ¿Se limitó a diagnosticar el riesgo en base a los datos sin inventar acciones correctivas o recomendaciones?

Si el texto CUMPLE TODAS Y CADA UNA de las reglas, responde exactamente con la palabra: "PERFECTO".
Si el texto FALLA en al menos una regla, responde "ERROR:" seguido del número de la regla que falló y una breve explicación de qué debe corregir el escritor.
"""

 
    
prompt_corregir = """
Eres el Director de Operaciones (COO). Tu borrador del análisis mensual de proveedores ha sido RECHAZADO por Auditoría.

ERRORES DETECTADOS QUE DEBES SOLUCIONAR:
{errores}

TEXTO ORIGINAL RECHAZADO:
"{texto_original}"

TU TAREA:
Reescribe el análisis original solucionando EXACTAMENTE los errores señalados por el auditor, integrándolos de forma fluida en la narrativa.

REGLAS ARQUITECTÓNICAS INQUEBRANTABLES (¡Escudo Anti-Regresión!):
1. FORMATO ESTRICTO: Es OBLIGATORIO que la nueva versión siga siendo UN SOLO PÁRRAFO continuo. Cero viñetas (-, *, •) y cero saltos de línea (\n).
2. FORMATO NUMÉRICO: Todos los miles deben mantener el punto como separador (ej: 1.000, 25.200).
3. HECHOS PUROS: No inventes acciones correctivas, recomendaciones, ni leas literalmente las tablas. Mantén el diagnóstico puro.
4. ARCO NARRATIVO: Asegúrate de no borrar accidentalmente las menciones al Cuello de Botella, Foco de Calidad y la Doble Afectación (Riesgo Sistémico) al hacer tu corrección.

Devuelve ÚNICAMENTE el texto final corregido. Sin saludos, sin explicaciones de lo que cambiaste, sin etiquetas como "Texto corregido:" y sin comillas.
"""
