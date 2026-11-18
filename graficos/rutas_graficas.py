"""Carpeta única donde se guardan todas las gráficas (PNG) que genera el reporte.
Si cambias la carpeta, cámbiala solo aquí: los módulos de gráficas, generar_reporte_completo.py
y frontend/app_celsa.py toman la ruta de este archivo."""
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
CARPETA_GRAFICAS = ROOT_DIR / "archivos_graficas"
CARPETA_GRAFICAS.mkdir(exist_ok=True)


def ruta_grafica(nombre_archivo: str) -> str:
    """Ruta completa de una gráfica dentro de CARPETA_GRAFICAS."""
    return str(CARPETA_GRAFICAS / nombre_archivo)
