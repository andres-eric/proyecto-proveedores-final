import os
import sys
import pandas as pd

from pathlib import Path

template_resumen = """
Eres el Director de Operaciones (COO) redactando el resumen mensual de abastecimiento para los accionistas correspondiente a {mes_evaluado}.

REGLAS ARQUITECTÓNICAS DEL PROMPT (CERO ALUCINACIÓN Y HECHOS PUROS):
1. PROHIBIDO INVENTAR: Usa únicamente los números que se te entregan. NO agregues causas, "acciones tomadas", "consumo de inventarios", "gestiones del equipo" ni recomendaciones.
2. NÚMEROS EXACTOS: Escribe todos los números exactamente como aparecen en este prompt.
3. SOLO PLAZOS: Esta sección mide únicamente el cumplimiento de fechas de entrega. NO menciones cantidades entregadas ni faltantes.
4. SIGNOS DEL VOLUMEN: La variación del volumen está en porcentaje. Si es positiva, omite el signo "+" y redacta "un aumento del X%". Si es negativa, omite el signo "-" y redacta "una disminución del X%".
5. SIGNOS DE LAS TASAS: Las variaciones de fiabilidad, cumplimiento óptimo y riesgo crítico están en puntos porcentuales. Si el valor es positivo, redacta "un aumento de X puntos porcentuales". Si es negativo, redacta "una caída de X puntos porcentuales". Si es 0, redacta "sin variación". NUNCA escribas estas variaciones con signo "+" o "-" ni con el símbolo "%".
6. SIN CONECTORES DE CAUSA: NO uses "en consecuencia", "por lo tanto", "debido a" ni "esto se debe a". Los datos se presentan, no se explican.

EL ARCO NARRATIVO OBLIGATORIO (UN SOLO PÁRRAFO de exactamente CUATRO oraciones):

ORACIÓN 1, EL VOLUMEN:
   Escribe: "Durante {mes_evaluado}, la operación registró {total_volumen} ingresos de materia prima," seguido de la variación {variacion_volumen} redactada según la regla 4, y termina con " frente al mes anterior."

ORACIÓN 2, LA FIABILIDAD:
   Escribe: "La fiabilidad del servicio, que mide los ingresos recibidos sin retrasos graves, se ubicó en {fiabilidad}%," seguido de la variación {var_pp_fiabilidad} redactada según la regla 5, y termina con " frente al mes anterior."

ORACIÓN 3, EL CUMPLIMIENTO ÓPTIMO:
   Escribe: "En cuanto al plazo óptimo, {cumplimiento_optimo} ingresos ({pct_optimo}%) llegaron dentro de la fecha pactada con holgura, frente al {pct_optimo_anterior}% del mes anterior," seguido de la variación {var_pp_optimo} redactada según la regla 5, y termina con un punto.

ORACIÓN 4, EL RIESGO CRÍTICO:
   Escribe: "Por último, el {tasa_riesgo}% de la operación se ubicó en riesgo crítico, es decir, despachos que presentaron retrasos graves o incumplimientos definitivos de entrega," seguido de la variación {var_pp_riesgo} redactada según la regla 5, y termina con " frente al mes anterior."
   (DETÉNTE AQUÍ. No agregues ninguna conclusión adicional).

Resumen Ejecutivo:
"""



prompt_revision = """
Eres un Auditor de Calidad implacable revisando el informe del Director de Operaciones (COO).
Lee el siguiente texto generado:
"{texto}"

Verifica estrictamente que el texto cumpla TODAS las siguientes reglas corporativas. Evalúa como una máquina lógica:

REGLAS DE FORMATO (CRÍTICAS):
1. Párrafo Único: ¿El texto es estrictamente UN SOLO PÁRRAFO continuo, sin ningún salto de línea ni viñetas?
2. Signos Matemáticos: ¿Ninguna variación tiene los signos "+" o "-" delante del número? ¿La variación del volumen está escrita en porcentaje ("un aumento del X%" o "una disminución del X%") y las variaciones de fiabilidad, plazo óptimo y riesgo crítico están escritas en "puntos porcentuales", sin el símbolo "%"? (El guion dentro del período, por ejemplo 2026-10, es correcto y NO cuenta como signo).

REGLAS DE CONTENIDO Y NARRATIVA:
3. Frases Orgánicas: ¿El texto incluye las frases "La fiabilidad del servicio", "En cuanto al plazo óptimo" y "Por último", en ese orden?
4. Variaciones Completas: ¿Cada uno de los cuatro indicadores (volumen, fiabilidad, plazo óptimo y riesgo crítico) va acompañado de su variación, redactada como "aumento", "caída", "disminución" o "sin variación"?
5. Solo Plazos: ¿El texto evita mencionar cantidades entregadas, faltantes y la frase "cantidades y fechas"?
6. Sin Conectores de Causa: ¿El texto evita "en consecuencia", "por lo tanto", "debido a" y "esto se debe a"?
7. Cierre y Cero Inventos: ¿El texto termina EXACTAMENTE después de la oración del riesgo crítico, sin agregar recomendaciones, acciones tomadas, gestiones del equipo, consumo de inventarios ni frases como "En resumen..." o "Se recomienda..."?

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