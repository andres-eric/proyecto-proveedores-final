import os
import sys
import pandas as pd

from pathlib import Path




template_proveedores_cantidad = """
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