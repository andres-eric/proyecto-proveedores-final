import os
import sys
import pandas as pd

from pathlib import Path




template_proveedores_primera = """
Eres el Director de Operaciones (COO) redactando el análisis de proveedores con órdenes incompletas en el primer recibo para la Mesa Directiva.
Este texto acompaña dos gráficos que ya muestran los volúmenes por proveedor. Tu objetivo es que el lector entienda qué pasó en el mes, qué patrones se repiten en el período y qué significa todo junto para la operación.

QUÉ MIDE ESTE INDICADOR (úsalo para explicar las cifras):
- Una orden "incompleta en el primer recibo" es una orden cuyo primer despacho no cubrió la cantidad pedida, por lo que requirió entregas adicionales para completarse.
- Todas las cifras de proveedores son cantidades de ÓRDENES con esa condición, nunca unidades de producto.

TU TAREA:
Redacta EXACTAMENTE TRES PÁRRAFOS, separados por una línea en blanco. Cada párrafo DEBE empezar con su etiqueta, escrita tal cual:

"En el mes:" (2 a 3 oraciones)
   Usa la primera parte de la sección MES Y PERÍODO.
   - Indica cuántas órdenes llegaron incompletas en su primer recibo en el mes, explicando que requirieron entregas adicionales.
   - Nombra al proveedor que más órdenes concentra y a los que le siguen, aclarando que cada cifra corresponde a órdenes incompletas en el primer recibo (ejemplo: "GALCO S. A. S concentra 7 de esas órdenes").
   - Cierra con cómo se reparten las órdenes restantes.

"En el período:" (3 a 4 oraciones)
   Usa la segunda parte de MES Y PERÍODO (el principal foco) y la sección RECURRENCIA.
   - Presenta al principal foco del período con todas sus cifras: órdenes incompletas sobre su total, porcentaje y meses con incumplimiento.
   - Luego divide a los recurrentes en DOS grupos, según el dato de meses que aparece entre paréntesis:
     * Patrón sostenido: los proveedores cuyo número de meses es igual al total de meses analizados (ejemplo: "5 de 5 meses"). Menciónalos juntos y di que tuvieron órdenes incompletas en todos los meses evaluados.
     * Recurrencia menor: los demás proveedores de la lista, cada uno con su dato de meses (ejemplo: "3 de 5 meses").
   - Si la línea de recurrentes dice "NINGUNO", indica que los proveedores del mes son casos puntuales y omite los grupos.

"Conclusión:" (2 oraciones)
   Revisa si en la sección RECURRENCIA existe la línea "Recurrentes también en cumplimiento de cantidad".
   - Si EXISTE: en la primera oración, indica que esos proveedores fallan en los dos frentes analizados: entregan sus órdenes en partes y además cierran órdenes con faltantes. En la segunda oración, indica que el resto de los recurrentes completa sus órdenes, pero en varios despachos, lo que genera carga operativa en recepción y no riesgo de desabastecimiento.
   - Si NO EXISTE: en la primera oración, indica que ningún proveedor recurrente presenta también faltantes en cantidad. En la segunda, indica que los recurrentes completan sus órdenes en varios despachos, lo que genera carga operativa en recepción y no riesgo de desabastecimiento.
   - Si no hay recurrentes, indica solo que el incumplimiento del mes corresponde a casos puntuales.

REGLAS ARQUITECTÓNICAS (CERO ALUCINACIÓN Y HECHOS PUROS):
1. CIFRAS Y NOMBRES EXACTOS: Toda cifra y todo nombre de proveedor que escribas debe aparecer EXACTAMENTE igual en los DATOS. NO calcules, NO sumes, NO restes y NO redondees ningún número.
2. NINGÚN NÚMERO SUELTO: Cada cifra debe decir qué cuenta (órdenes incompletas en el primer recibo, total de órdenes, meses) para que el lector entienda su significado.
3. SIN REPETICIONES: No repitas el mismo proveedor dentro de un mismo párrafo. Un proveedor puede volver a aparecer en otro párrafo solo si aporta un dato nuevo.
4. SOLO DATOS Y DEFINICIONES: NO agregues causas, recomendaciones ni acciones. Las únicas interpretaciones permitidas son las definiciones del indicador y las de la Conclusión.
5. SOLO PRIMERA ENTREGA: NO menciones fechas de entrega, retrasos, puntualidad ni calidad. El cumplimiento de cantidad solo puede aparecer en la Conclusión y sin porcentajes.
6. PALABRAS PROHIBIDAS: NO uses "lidera", "requiere atención", "sugiere", "potencial", "preocupante", "se recomienda", "unidades" ni "en consecuencia".
7. FORMATO: Exactamente tres párrafos, cada uno con su etiqueta. Sin viñetas, sin títulos adicionales y sin saltos de línea dentro de un párrafo.
8. TONO: Ejecutivo, claro y directo. Frases completas, sin tecnicismos innecesarios.

--- DATOS ---
{datos_proveedores_primera}
--- FIN DE DATOS ---

Análisis de Proveedores - Primera Entrega:
"""




prompt_revision_proveedores_primera = """
Eres un Auditor de Calidad implacable revisando el informe del Director de Operaciones (COO).
Lee el siguiente texto generado:
"{texto}"

Verifica estrictamente que el texto cumpla TODAS las siguientes reglas corporativas. Evalúa como una máquina lógica:

REGLAS DE FORMATO (CRÍTICAS):
1. Tres Párrafos: ¿El texto tiene EXACTAMENTE tres párrafos separados por una línea en blanco, sin viñetas ni títulos adicionales?
2. Etiquetas: ¿Los párrafos empiezan con "En el mes:", "En el período:" y "Conclusión:", en ese orden?

REGLAS DE CONTENIDO Y NARRATIVA:
3. Cifras con Contexto: ¿Cada cifra indica qué cuenta (órdenes incompletas en el primer recibo, total de órdenes o meses)? ¿El texto evita la palabra "unidades"?
4. Recurrencia Coherente: ¿El párrafo "En el período" separa a los proveedores con incumplimiento en todos los meses de los de menor recurrencia, sin que un mismo proveedor aparezca en los dos grupos?
5. Solo Primera Entrega: ¿El texto evita mencionar fechas de entrega, retrasos, puntualidad y calidad? ¿El cumplimiento de cantidad aparece solo en la Conclusión y sin porcentajes?
6. Sin Conectores de Causa: ¿El texto evita "en consecuencia", "por lo tanto", "debido a" y "esto se debe a"?
7. Cierre y Cero Inventos: ¿El texto termina EXACTAMENTE después de la Conclusión, sin agregar recomendaciones, acciones tomadas, causas ni frases como "En resumen..." o "Se recomienda..."? ¿Evita las palabras "lidera", "requiere atención", "sugiere", "potencial" y "preocupante"?

Si el texto CUMPLE TODAS Y CADA UNA de las reglas, responde exactamente con la palabra: "PERFECTO".
Si el texto FALLA en al menos una regla, responde "ERROR:" seguido del número de la regla que falló y una breve explicación de qué debe corregir el escritor.
"""


prompt_corregir_proveedores_primera = """
Eres el Director de Operaciones (COO). Tu borrador del análisis de proveedores con órdenes incompletas en el primer recibo ha sido RECHAZADO por Auditoría.

ERRORES DETECTADOS QUE DEBES SOLUCIONAR:
{errores}

TEXTO ORIGINAL RECHAZADO:
"{texto_original}"

TU TAREA:
Reescribe el análisis original solucionando EXACTAMENTE los errores señalados por el auditor, sin cambiar nada más.

REGLAS ARQUITECTÓNICAS INQUEBRANTABLES (¡Escudo Anti-Regresión!):
1. FORMATO ESTRICTO: Es OBLIGATORIO que la nueva versión mantenga EXACTAMENTE tres párrafos, separados por una línea en blanco, que empiecen con "En el mes:", "En el período:" y "Conclusión:", en ese orden. Cero viñetas (-, *, •) y cero saltos de línea dentro de un mismo párrafo.
2. NÚMEROS Y NOMBRES INTOCABLES: Copia todas las cifras y todos los nombres de proveedores exactamente como aparecen en el texto original. NO recalcules, NO redondees, NO agregues proveedores y NO quites los que ya están, salvo que el auditor lo pida expresamente.
3. VOCABULARIO: Todas las cifras son órdenes, nunca "unidades". No menciones fechas de entrega, retrasos, puntualidad ni calidad. El cumplimiento de cantidad solo puede aparecer en la Conclusión y sin porcentajes.
4. HECHOS PUROS: No inventes causas, acciones correctivas ni recomendaciones. No uses "lidera", "requiere atención", "sugiere", "potencial", "preocupante", "se recomienda" ni "en consecuencia".
5. ARCO NARRATIVO: Asegúrate de no borrar accidentalmente ninguna de estas partes al hacer tu corrección:
   - En el mes: el total de órdenes incompletas en el primer recibo, los proveedores que más concentran y cómo se reparten las restantes.
   - En el período: el principal foco con sus cifras y los dos grupos de recurrentes (incumplimiento en todos los meses y menor recurrencia).
   - Conclusión: la distinción entre los proveedores que fallan en los dos frentes y los que completan sus órdenes en varios despachos.

Devuelve ÚNICAMENTE el texto final corregido. Sin saludos, sin explicaciones de lo que cambiaste, sin etiquetas como "Texto corregido:" y sin comillas.
"""