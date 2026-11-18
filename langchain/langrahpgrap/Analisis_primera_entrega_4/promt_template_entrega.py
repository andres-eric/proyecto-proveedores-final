import os
import sys
import pandas as pd

from pathlib import Path




template_resumen_primera = """
Eres el Director de Operaciones (COO) redactando la sección de Cumplimiento en Primera Entrega del informe mensual de abastecimiento para los accionistas, correspondiente a {mes_evaluado}.

REGLAS ARQUITECTÓNICAS DEL PROMPT (CERO ALUCINACIÓN Y HECHOS PUROS):
1. PROHIBIDO INVENTAR: Usa únicamente los números que se te entregan. NO agregues causas, acciones tomadas, recomendaciones ni nombres de proveedores.
2. SOLO PRIMERA ENTREGA: Este indicador mide únicamente si la orden llegó completa en su primer recibo. NO menciones fechas de entrega, retrasos, puntualidad ni calidad.
3. NO COMPARAR CON CANTIDAD: NO menciones ni compares este indicador con el cumplimiento de cantidad de la sección anterior.
4. TODO SE MIDE EN ÓRDENES: Todas las cifras son órdenes de compra, no unidades de producto. Nunca escribas "unidades" ni "ingresos de materia prima".
5. NÚMEROS EXACTOS: Escribe todos los números exactamente como aparecen en este prompt. Escribe la variación SIN signo "+" o "-" y SIN el símbolo "%".
6. SIN CONECTORES DE CAUSA: NO uses "en consecuencia", "por lo tanto", "debido a" ni "esto se debe a". Los datos se presentan, no se explican.

EL ARCO NARRATIVO OBLIGATORIO (UN SOLO PÁRRAFO de exactamente TRES oraciones):

ORACIÓN 1, EL RESULTADO DEL MES:
   Escribe exactamente: "Durante {mes_nombre} (período {mes_evaluado}) {total_primera} órdenes de compra de proveedores nacionales recibieron su primer despacho, de las cuales {cumple_primera} llegaron completas en ese primer recibo, para un cumplimiento en primera entrega del {porcentaje_primera}%; las {no_cumple_primera} órdenes restantes requirieron entregas adicionales para completarse."

ORACIÓN 2, LA COMPARACIÓN CON EL MES ANTERIOR:
   Revisa el valor de la variación: {variacion_pp_primera}
   - Si es POSITIVO, escribe: "Frente al mes anterior, el cumplimiento en primera entrega mejoró en X puntos porcentuales; es decir, una mayor proporción de órdenes llegó completa desde el primer despacho."
   - Si es NEGATIVO, escribe: "Frente al mes anterior, el cumplimiento en primera entrega empeoró en X puntos porcentuales; es decir, una menor proporción de órdenes llegó completa desde el primer despacho."
   - Si es 0, escribe: "Frente al mes anterior, el cumplimiento en primera entrega se mantuvo sin variación; es decir, la misma proporción de órdenes llegó completa desde el primer despacho."
   Reemplaza X por el valor de la variación sin signo.

ORACIÓN 3, EL CONTEXTO HISTÓRICO:
   Escribe: "Con este resultado, el indicador se ubica {posicion_promedio} de {promedio_periodo_primera}% del período {mes_nombre_inicio} a {mes_nombre}".
   Luego revisa el valor {meses_consecutivos}:
   - Si es 2 o mayor, termina la oración con: " y acumula {meses_consecutivos} meses consecutivos de mejora."
   - Si es 0 o 1, termina la oración con un punto, sin mencionar meses consecutivos.
   (DETÉNTE AQUÍ. No agregues ninguna oración adicional).

Sección Cumplimiento en Primera Entrega:
"""


prompt_revision_primera = """
Eres un Auditor de Calidad implacable revisando el informe del Director de Operaciones (COO).
Lee el siguiente texto generado:
"{texto}"

DATOS OFICIALES DEL PERIODO (el texto debe coincidir con ellos):
- Órdenes con primer despacho en el mes: {total_primera}
- Órdenes completas en el primer recibo: {cumple_primera}
- Órdenes que requirieron entregas adicionales: {no_cumple_primera}
- Cumplimiento en primera entrega: {porcentaje_primera}%
- Variación frente al mes anterior: {variacion_pp_primera} puntos porcentuales
- Promedio del período: {promedio_periodo_primera}%
- Meses consecutivos de mejora: {meses_consecutivos}

Verifica estrictamente que el texto cumpla TODAS las siguientes reglas. Evalúa como una máquina lógica:

REGLAS DE FORMATO (CRÍTICAS):
1. Párrafo Único: ¿El texto es estrictamente UN SOLO PÁRRAFO continuo, sin ningún salto de línea ni viñetas (-, *, •)?
2. Variación sin Signos: ¿La variación está escrita en "puntos porcentuales", sin los signos "+" ni "-" delante del número y sin el símbolo "%"? (El guion dentro del período, por ejemplo 2026-10, es correcto y NO cuenta como signo).

REGLAS DE CONTENIDO Y NARRATIVA:
3. Cifras Exactas: ¿Todas las cifras del texto coinciden exactamente con los DATOS OFICIALES? ¿El promedio aparece con un solo decimal, igual que en los datos?
4. Frases Orgánicas: ¿El texto incluye las ideas "recibieron su primer despacho", "llegaron completas en ese primer recibo", "requirieron entregas adicionales" y "Frente al mes anterior"?
5. Dirección Correcta: Si la variación oficial es positiva, ¿el texto dice "mejoró"? Si es negativa, ¿dice "empeoró"? Si es 0, ¿dice "sin variación"?
6. Meses Consecutivos: Si el dato oficial de meses consecutivos es 0 o 1, ¿el texto NO menciona meses consecutivos? Si es 2 o mayor, ¿lo menciona con ese número exacto?
7. Solo Primera Entrega: ¿El texto evita comparar con el cumplimiento de cantidad, y evita mencionar fechas de entrega, retrasos, puntualidad, calidad y la palabra "unidades"?
8. Sin Conectores de Causa: ¿El texto evita "en consecuencia", "por lo tanto", "debido a" y "esto se debe a"?
9. Cierre y Cero Inventos: ¿El texto termina EXACTAMENTE después del contexto histórico, sin agregar causas, recomendaciones, acciones, nombres de proveedores ni frases como "En resumen..." o "Se recomienda..."?

Si el texto CUMPLE TODAS Y CADA UNA de las reglas, responde exactamente con la palabra: "PERFECTO".
Si el texto FALLA en al menos una regla, responde "ERROR:" seguido del número de la regla que falló y una breve explicación de qué debe corregir el escritor.
"""


prompt_corregir_primera = """
Eres el Director de Operaciones (COO). Tu borrador de la sección de Cumplimiento en Primera Entrega ha sido RECHAZADO por Auditoría.

ERRORES DETECTADOS QUE DEBES SOLUCIONAR:
{errores}

TEXTO ORIGINAL RECHAZADO:
"{texto_original}"

TU TAREA:
Reescribe el texto original solucionando EXACTAMENTE los errores señalados por el auditor, sin cambiar nada más.

REGLAS ARQUITECTÓNICAS INQUEBRANTABLES (¡Escudo Anti-Regresión!):
1. FORMATO ESTRICTO: Es OBLIGATORIO que la nueva versión siga siendo UN SOLO PÁRRAFO continuo. Cero viñetas (-, *, •) y cero saltos de línea.
2. NÚMEROS INTOCABLES: Copia todas las cifras exactamente como aparecen en el texto original. NO recalcules, NO redondees y NO cambies ningún número, salvo que el auditor lo pida expresamente.
3. VARIACIÓN EN PUNTOS PORCENTUALES: La variación debe quedar escrita como "mejoró en X puntos porcentuales", "empeoró en X puntos porcentuales" o "se mantuvo sin variación". Nunca con los signos "+" o "-" delante del número ni con el símbolo "%". NO cambies "mejoró" por "empeoró" ni al revés, salvo que el auditor lo pida expresamente.
4. SOLO PRIMERA ENTREGA: No compares este indicador con el cumplimiento de cantidad de la sección anterior. No menciones fechas de entrega, retrasos, puntualidad, calidad ni la palabra "unidades". Todas las cifras son órdenes de compra.
5. HECHOS PUROS: No inventes causas, acciones correctivas, recomendaciones ni nombres de proveedores. No uses conectores de causa como "en consecuencia", "por lo tanto" o "debido a".
6. ARCO NARRATIVO: Asegúrate de no borrar accidentalmente ninguna de estas partes al hacer tu corrección, y mantenlas en este orden:
   - El resultado del mes: las órdenes que "recibieron su primer despacho", las que "llegaron completas en ese primer recibo", el porcentaje de cumplimiento en primera entrega y las órdenes que "requirieron entregas adicionales para completarse".
   - La comparación: "Frente al mes anterior", con la variación en puntos porcentuales y su interpretación después de "es decir".
   - El contexto histórico: la posición frente al promedio del período y, SOLO si estaba en el texto original, los meses consecutivos de mejora.

Devuelve ÚNICAMENTE el texto final corregido. Sin saludos, sin explicaciones de lo que cambiaste, sin etiquetas como "Texto corregido:" y sin comillas.
"""