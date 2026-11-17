import os
import sys
import pandas as pd

from pathlib import Path




template_analisis_detalle_3= """
Eres el Director de Operaciones (COO) redactando el análisis de proveedores con incumplimiento de cantidad para la Mesa Directiva.
Este texto acompaña dos gráficos que ya muestran los volúmenes, por lo que tu objetivo es explicar qué significan los datos para el negocio.

REGLAS ARQUITECTÓNICAS DEL PROMPT (CERO ALUCINACIÓN Y HECHOS PUROS):
1. CIFRAS EXACTAS: Copia todos los nombres de proveedores y todas las cifras EXACTAMENTE como aparecen en este prompt. NO calcules, NO redondees y NO cambies ningún número.
2. PROHIBIDO INVENTAR: NO agregues causas, recomendaciones, acciones ni conclusiones propias.
3. TODO SE MIDE EN ÓRDENES: Las cifras son órdenes de compra, no unidades de producto. Nunca escribas "unidades".
4. SOLO CANTIDAD: NO menciones fechas de entrega, retrasos, puntualidad ni calidad.
5. PALABRAS PROHIBIDAS: NO uses "lidera", "requiere atención", "sugiere", "potencial", "preocupante" ni "se recomienda".
6. FORMATO ESTRICTO: Redacta UN SOLO PÁRRAFO continuo. Sin viñetas, sin títulos y sin saltos de línea.
7. CONECTORES: Puedes ajustar el inicio de las frases que se te entregan para que el texto fluya (por ejemplo "Por su parte," o "Además,"), pero NO cambies su contenido.

EL ARCO NARRATIVO OBLIGATORIO (Sigue este orden exacto):

1. EL MES EVALUADO:
   Inicia el párrafo con esta frase: {frase_mes}

2. EL PATRÓN DEL PERÍODO:
   Continúa con esta idea: "En el período de {mes_nombre_inicio} a {mes_nombre}, {proveedor_acumulado} se consolida como el principal foco de incumplimiento en cantidad, con {incumplidas_acumulado} de sus {total_acumulado} órdenes cerradas con faltantes ({porcentaje_acumulado}%) e incumplimiento en {meses_acumulado} meses del período."

3. EL SEGUNDO FOCO:
   Si la siguiente frase no está vacía, agrégala a continuación: {frase_tasa}
   Si está vacía, omite este punto.

4. LA RECURRENCIA:
   Finaliza con esta frase: {frase_recurrencia}
   (DETÉNTE AQUÍ. No agregues ninguna oración adicional).

Análisis de Proveedores - Cumplimiento de Cantidad:
"""


prompt_revision_analisis_3_detalle = """
Eres un Auditor de Calidad implacable revisando el informe del Director de Operaciones (COO).
Lee el siguiente texto generado:
"{texto}"

DATOS OFICIALES (el texto debe coincidir con ellos):
- Frase del mes evaluado: {frase_mes}
- Proveedor principal del período: {proveedor_acumulado} | Órdenes con faltantes: {incumplidas_acumulado} de {total_acumulado} ({porcentaje_acumulado}%) | Meses con incumplimiento: {meses_acumulado}
- Frase del segundo foco (puede estar vacía): {frase_tasa}
- Frase de recurrencia: {frase_recurrencia}

Verifica estrictamente que el texto cumpla TODAS las siguientes reglas. Evalúa como una máquina lógica:

REGLAS DE FORMATO (CRÍTICAS):
1. Párrafo Único: ¿El texto es estrictamente UN SOLO PÁRRAFO continuo, sin ningún salto de línea ni viñetas (-, *, •)?
2. Medido en Órdenes: ¿El texto evita la palabra "unidades" y habla siempre de órdenes?

REGLAS DE CONTENIDO Y NARRATIVA:
3. Mes Evaluado: ¿El texto inicia con el contenido de la frase del mes evaluado, con los mismos proveedores y las mismas cifras?
4. Patrón del Período: ¿El texto menciona a {proveedor_acumulado} como principal foco de incumplimiento en cantidad, con exactamente {incumplidas_acumulado} de {total_acumulado} órdenes, {porcentaje_acumulado}% y {meses_acumulado} meses?
5. Segundo Foco: Si la frase del segundo foco NO está vacía, ¿el texto la incluye con el mismo proveedor y las mismas cifras? Si está vacía, ¿el texto evita mencionar un proveedor con "mayor tasa de incumplimiento"?
6. Recurrencia: ¿El texto incluye el contenido de la frase de recurrencia, con los mismos proveedores, y termina inmediatamente después de ella?
7. Solo Cantidad: ¿El texto evita mencionar fechas de entrega, retrasos, puntualidad y calidad?
8. Cero Alucinación: ¿El texto evita agregar causas, recomendaciones, acciones o conclusiones propias, y no usa "lidera", "requiere atención", "sugiere", "potencial", "preocupante" ni "se recomienda"?

Si el texto CUMPLE TODAS Y CADA UNA de las reglas, responde exactamente con la palabra: "PERFECTO".
Si el texto FALLA en al menos una regla, responde "ERROR:" seguido del número de la regla que falló y una breve explicación de qué debe corregir el escritor.
"""


prompt_corregir_analisis_3_detalle = """
Eres el Director de Operaciones (COO). Tu borrador del análisis de proveedores con incumplimiento de cantidad ha sido RECHAZADO por Auditoría.

ERRORES DETECTADOS QUE DEBES SOLUCIONAR:
{errores}

TEXTO ORIGINAL RECHAZADO:
"{texto_original}"

TU TAREA:
Reescribe el texto original solucionando EXACTAMENTE los errores señalados por el auditor, sin cambiar nada más.

REGLAS ARQUITECTÓNICAS INQUEBRANTABLES (¡Escudo Anti-Regresión!):
1. FORMATO ESTRICTO: Es OBLIGATORIO que la nueva versión siga siendo UN SOLO PÁRRAFO continuo. Cero viñetas (-, *, •) y cero saltos de línea.
2. NÚMEROS INTOCABLES: Copia todas las cifras exactamente como aparecen en el texto original. NO recalcules, NO redondees y NO cambies ningún número, salvo que el auditor lo pida expresamente.
3. NOMBRES INTOCABLES: Copia todos los nombres de proveedores exactamente como aparecen en el texto original. NO agregues proveedores nuevos ni quites los que ya están, salvo que el auditor lo pida expresamente.
4. TODO SE MIDE EN ÓRDENES: No uses la palabra "unidades". Todas las cifras son órdenes de compra.
5. SOLO CANTIDAD: No menciones fechas de entrega, retrasos, puntualidad ni calidad.
6. HECHOS PUROS: No inventes causas, acciones correctivas ni recomendaciones. No uses "lidera", "requiere atención", "sugiere", "potencial", "preocupante" ni "se recomienda".
7. ARCO NARRATIVO: Asegúrate de no borrar accidentalmente ninguna de estas partes al hacer tu corrección, y mantenlas en este orden:
   - El mes evaluado: las órdenes que cerraron con faltantes en el mes y el proveedor que las concentra.
   - El patrón del período: el proveedor que "se consolida como el principal foco de incumplimiento en cantidad", con sus órdenes, su porcentaje y sus meses con incumplimiento.
   - El segundo foco: el proveedor con "la mayor tasa de incumplimiento del período", SOLO si estaba en el texto original.
   - La recurrencia: los proveedores con incumplimiento recurrente o los casos puntuales, como cierre del párrafo.

Devuelve ÚNICAMENTE el texto final corregido. Sin saludos, sin explicaciones de lo que cambiaste, sin etiquetas como "Texto corregido:" y sin comillas.
"""