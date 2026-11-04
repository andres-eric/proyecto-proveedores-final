import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from datos.carga_datos import obtener_datos_kpi_detalle

# -- Obtener datos -----------------------------------------------
df = obtener_datos_kpi_detalle()





if df is None:
    print("No se pudieron obtener los datos. Verifica que la API este disponible.")
    sys.exit(1)

print(f"Datos obtenidos: {len(df)} registros | {len(df.columns)} columnas")
print(f"Columnas: {df.columns.tolist()}")

