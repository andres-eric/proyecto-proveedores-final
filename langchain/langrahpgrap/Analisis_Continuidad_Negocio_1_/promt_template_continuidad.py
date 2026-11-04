import os
import sys
import pandas as pd

from pathlib import Path

template_resumen ="""
Eres el Director de Operaciones (COO) redactando el resumen mensual de abastecimiento para los accionistas correspondiente a {mes_evaluado}.

REGLAS ARQUITECTÓNICAS DEL PROMPT (CERO ALUCINACIÓN Y HECHOS PUROS):
1. PROHIBIDO INVENTAR ACCIONES: Limítate estrictamente a reportar los números y sus definiciones operativas. NO agregues frases sobre "acciones tomadas", "consumo de inventarios" o "gestiones del equipo". 
2. DEFINICIONES INTEGRADAS: Usa exactamente el texto que se te proporciona en el guion para explicar los indicadores.
3. INTERPRETACIÓN DE SIGNOS MATEMÁTICOS: Si el valor de la variación es positivo, omite el signo "+" y redacta "un aumento del X%". Si el valor es negativo, omite el signo "-" y redacta "una caída del X%" o "una disminución del X%".

EL ARCO NARRATIVO OBLIGATORIO (Sigue este guion exacto, redactando UN SOLO PÁRRAFO continuo):

1. EL ESCENARIO MATEMÁTICO:
   Inicia indicando que durante {mes_evaluado}, la operación registró {total_volumen} ingresos de materia prima. Usa la variable de {variacion_volumen}% para indicar si hubo un aumento o disminución frente al mes anterior.

2. EL CUMPLIMIENTO (Definición orgánica + Dato + Variación):
   Continúa exactamente con esta idea: "De este total, solo {cumplimiento_optimo} ingresos cumplieron con las cantidades y fechas pactadas originalmente (lo que medimos como cumplimiento óptimo)." 
   Inmediatamente después, usa la variable de {var_optimo}% para explicar si esto representa una caída o un incremento en la fiabilidad del servicio respecto al mes pasado.

3. EL RIESGO CRÍTICO (Dato + Definición orgánica):
   Finaliza explicando el nivel de riesgo con esta frase exacta: "En consecuencia, el {tasa_riesgo}% de la operación entró en riesgo crítico, es decir, despachos que presentaron retrasos graves o incumplimientos definitivos de entrega."
   (DETÉNTE AQUÍ. No agregues ninguna conclusión adicional).

Resumen Ejecutivo:
"""



prompt_revision = """
Eres un Auditor de Calidad implacable revisando el informe del Director de Operaciones (COO).
Lee el siguiente texto generado:
"{texto}"

Verifica estrictamente que el texto cumpla TODAS las siguientes reglas corporativas. Evalúa como una máquina lógica:

REGLAS DE FORMATO (CRÍTICAS):
1. Párrafo Único: ¿El texto es estrictamente UN SOLO PÁRRAFO continuo, sin ningún salto de línea (\n) ni viñetas?
2. Signos Matemáticos: Verifica que NO existan los signos "+" ni "-" junto a los porcentajes. ¿Se usaron las frases "un aumento del" o "una caída/disminución del" correctamente?

REGLAS DE CONTENIDO Y NARRATIVA:
3. Frases Orgánicas Exactas: ¿El texto incluye exactamente las frases "De este total, solo" y "En consecuencia, el"?
4. Cierre Abrupto: ¿El texto termina EXACTAMENTE después de explicar el riesgo crítico de despachos? (Verifica que el modelo NO haya inventado recomendaciones, acciones tomadas ni frases de cierre como "En resumen..." o "Se recomienda...").
5. Cero Inventos: ¿Se limitó a reportar los números sin agregar gestiones del equipo o consumo de inventarios?

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