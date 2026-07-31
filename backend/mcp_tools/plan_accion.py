import pandas as pd
from pathlib import Path

# Path to the data file
DATA_DIR = Path(__file__).parent.parent / "data"
CSV_PATH = DATA_DIR / "planes_accion_municipal.csv"

def generar_plan_accion(nivel_alerta_global: str) -> list[dict]:
    """
    Lee el catálogo planes_accion_municipal.csv, filtra por nivel_alerta_global
    y ordena por prioridad ascendentemente.
    """
    if not CSV_PATH.exists():
        return []

    # Read the CSV
    df = pd.read_csv(CSV_PATH)
    
    # Clean up column names just in case
    df.columns = df.columns.str.strip().str.lower()
    
    # Filter by nivel_alerta_global
    df_filtrado = df[df['nivel_alerta'].str.lower() == nivel_alerta_global.lower()]
    
    # Sort by priority
    if 'prioridad' in df_filtrado.columns:
        df_ordenado = df_filtrado.sort_values(by='prioridad', ascending=True)
    else:
        df_ordenado = df_filtrado
        
    return df_ordenado.to_dict(orient='records')
