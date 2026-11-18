import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent  # raíz del proyecto (este script vive en ejecutar_reporte/)
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from exportar_excel.generar_todos_los_excels import exportar_todos_los_datasets

if __name__ == "__main__":
    exportar_todos_los_datasets()
