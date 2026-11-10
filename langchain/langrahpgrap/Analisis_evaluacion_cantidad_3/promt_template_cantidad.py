import os
import sys
import pandas as pd

from pathlib import Path


template_resumen_cantidad = """
Eres el Director de Operaciones (COO) redactando la sección de Cumplimiento de Cantidad del informe mensual de abastecimiento para los accionistas, correspondiente a {mes_evaluado}.

REGLAS ARQUITECTÓNICAS DEL PROMPT (CERO ALUCINACIÓN Y HECHOS PUROS):
1. PROHIBIDO INVENTAR: Usa únicamente los números que se te entregan. NO agregues causas, acciones tomadas, recomendaciones ni nombres de proveedores.
2. SOLO CANTIDAD: Este indicador mide únicamente si la orden completó la cantidad pedida. NO menciones fechas, retrasos, puntualidad ni calidad.
3. TODO SE MIDE EN ÓRDENES: Todas las cifras son órdenes de compra, no unidades de producto. Nunca escribas "unidades" ni "ingresos de materia prima".
4. NÚMEROS EXACTOS: Escribe todos los números exactamente como aparecen en este prompt. Escribe la variación SIN signo "+" o "-" y SIN el símbolo "%".
5. SIN CONECTORES DE CAUSA: NO uses "en consecuencia", "por lo tanto", "debido a" ni "esto se debe a". Los datos se presentan, no se explican.

EL ARCO NARRATIVO OBLIGATORIO (UN SOLO PÁRRAFO de exactamente TRES oraciones):

ORACIÓN 1, EL RESULTADO DEL MES:
   Escribe exactamente: "Durante {mes_nombre} (período {mes_evaluado}) se cerraron {total} órdenes de compra de proveedores nacionales, de las cuales {cumpleCantidad} completaron la cantidad pedida sumando todas sus entregas, para un cumplimiento de cantidad del {porcentajeCumpleCantidad}%; las {noCumpleCantidad} órdenes restantes cerraron con faltantes."

ORACIÓN 2, LA COMPARACIÓN CON EL MES ANTERIOR:
   Revisa el valor de la variación: {variacion_pp_cumplimiento_cantidad}
   - Si es POSITIVO, escribe: "Frente al mes anterior, el cumplimiento de cantidad mejoró en X puntos porcentuales; es decir, los proveedores entregaron completa una mayor proporción de las órdenes."
   - Si es NEGATIVO, escribe: "Frente al mes anterior, el cumplimiento de cantidad empeoró en X puntos porcentuales; es decir, los proveedores entregaron completa una menor proporción de las órdenes."
   - Si es 0, escribe: "Frente al mes anterior, el cumplimiento de cantidad se mantuvo sin variación; es decir, los proveedores entregaron completa la misma proporción de las órdenes."
   Reemplaza X por el valor de la variación sin signo.

ORACIÓN 3, EL CONTEXTO HISTÓRICO:
   Escribe: "Con este resultado, el indicador se ubica {posicion_promedio} de {promedio_periodo}% del período {mes_nombre_inicio} a {mes_nombre}".
   Luego revisa el valor {meses_consecutivos_mejora}:
   - Si es 2 o mayor, termina la oración con: " y acumula {meses_consecutivos_mejora} meses consecutivos de mejora."
   - Si es 0 o 1, termina la oración con un punto, sin mencionar meses consecutivos.
   (DETÉNTE AQUÍ. No agregues ninguna oración adicional).

Sección Cumplimiento de Cantidad:
"""


prompt_revision_cantidad = """
Eres un Auditor de Calidad implacable revisando el informe del Director de Operaciones (COO).
Lee el siguiente texto generado:
"{texto}"

DATOS OFICIALES DEL PERIODO (el texto debe coincidir con ellos):
- Órdenes cerradas: {total}
- Órdenes que completaron la cantidad: {cumpleCantidad}
- Órdenes con faltantes: {noCumpleCantidad}
- Cumplimiento de cantidad: {porcentajeCumpleCantidad}%
- Variación frente al mes anterior: {variacion_pp_cumplimiento_cantidad} puntos porcentuales
- Promedio del período: {promedio_periodo}%
- Meses consecutivos de mejora: {meses_consecutivos_mejora}

Verifica estrictamente que el texto cumpla TODAS las siguientes reglas corporativas. Evalúa como una máquina lógica:

REGLAS DE FORMATO (CRÍTICAS):
1. Párrafo Único: ¿El texto es estrictamente UN SOLO PÁRRAFO continuo, sin saltos de línea ni viñetas?
2. Signos Matemáticos: ¿La variación está escrita como "un aumento de X puntos porcentuales", "una caída de X puntos porcentuales" o "sin variación", sin los signos "+" ni "-" delante del número y sin el símbolo "%"? (El guion dentro del período, por ejemplo 2026-10, es correcto y NO cuenta como signo).

REGLAS DE CONTENIDO Y NARRATIVA:
3. Números Exactos: ¿Todas las cifras del texto coinciden exactamente con los DATOS OFICIALES? ¿El promedio aparece con un solo decimal, igual que en los datos?
4. Frases Orgánicas Exactas: ¿El texto incluye exactamente las frases "de las cuales", "cerraron con faltantes" y "Frente al mes anterior"?
5. Meses Consecutivos: Si el dato de meses consecutivos de mejora es 0 o 1, ¿el texto NO menciona meses consecutivos? Si es 2 o mayor, ¿lo menciona con ese número exacto?
6. Solo Cantidad: ¿El texto evita mencionar fechas de entrega, retrasos, puntualidad, calidad y la palabra "unidades"?
7. Sin Conectores de Causa: ¿El texto evita "en consecuencia", "por lo tanto", "debido a" y "esto se debe a"?
8. Cierre Abrupto: ¿El texto termina EXACTAMENTE después de la comparación con el promedio o los meses consecutivos de mejora? (Verifica que NO haya recomendaciones, acciones tomadas, nombres de proveedores ni frases como "En resumen..." o "Se recomienda...").

Si el texto CUMPLE TODAS Y CADA UNA de las reglas, responde exactamente con la palabra: "PERFECTO".
Si el texto FALLA en al menos una regla, responde "ERROR:" seguido del número de la regla que falló y una breve explicación de qué debe corregir el escritor.
"""


prompt_corregir_cantidad = """
Eres el Director de Operaciones (COO). Tu borrador de la sección de Cumplimiento de Cantidad ha sido RECHAZADO por Auditoría.

ERRORES DETECTADOS QUE DEBES SOLUCIONAR:
{errores}

TEXTO ORIGINAL RECHAZADO:
"{texto_original}"

TU TAREA:
Reescribe el texto original solucionando EXACTAMENTE los errores señalados por el auditor, sin cambiar nada más.

REGLAS ARQUITECTÓNICAS INQUEBRANTABLES (¡Escudo Anti-Regresión!):
1. FORMATO ESTRICTO: Es OBLIGATORIO que la nueva versión siga siendo UN SOLO PÁRRAFO continuo. Cero viñetas (-, *, •) y cero saltos de línea.
2. NÚMEROS INTOCABLES: Copia todas las cifras exactamente como aparecen en el texto original. NO recalcules, NO redondees y NO cambies ningún número, salvo que el auditor lo pida expresamente.
3. VARIACIÓN EN PUNTOS PORCENTUALES: La variación debe quedar escrita como "un aumento de X puntos porcentuales", "una caída de X puntos porcentuales" o "sin variación". Nunca con los signos "+" o "-" delante del número ni con el símbolo "%".
4. SOLO CANTIDAD: No menciones fechas de entrega, retrasos, puntualidad, calidad ni la palabra "unidades". Todas las cifras son órdenes de compra.
5. HECHOS PUROS: No inventes causas, acciones correctivas, recomendaciones ni nombres de proveedores. No uses conectores de causa como "en consecuencia", "por lo tanto" o "debido a".
6. ARCO NARRATIVO: Asegúrate de no borrar accidentalmente ninguna de estas dos partes al hacer tu corrección:
   - El resultado del mes: órdenes cerradas, órdenes que completaron la cantidad ("de las cuales"), el porcentaje de cumplimiento y las órdenes restantes que "cerraron con faltantes".
   - La evolución: la comparación "Frente al mes anterior", la posición frente al promedio del período y, si estaba en el texto original, los meses consecutivos de mejora.

Devuelve ÚNICAMENTE el texto final corregido. Sin saludos, sin explicaciones de lo que cambiaste, sin etiquetas como "Texto corregido:" y sin comillas.
"""