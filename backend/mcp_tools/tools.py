"""Tools MCP reales de HidroAlerta: ejecutan pandas, el modelo nunca calcula.

Firmas oficiales tomadas de ``assets/starter.py``. El único añadido es el
parámetro ``data_dir`` (keyword-only) para poder apuntar a distintos
directorios de datos (fixtures de prueba vs. ``backend/data`` en producción)
sin cambiar el comportamiento documentado de cada tool.
"""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[2] / "backend" / "data"

_ARCHIVOS = {
    "presas": "presas_2024.csv",
    "precipitacion": "precipitacion_estaciones.csv",
    "temperatura": "temperatura_regional.csv",
}


def _resolver_data_dir(data_dir: Path | str | None) -> Path:
    if data_dir is not None:
        return Path(data_dir)
    return Path(os.environ.get("HIDROALERTA_DATA_DIR", DEFAULT_DATA_DIR))


def _ruta_csv(csv_name: str, data_dir: Path | str | None) -> Path:
    return _resolver_data_dir(data_dir) / _ARCHIVOS[csv_name]


def _columna_fecha(df: pd.DataFrame) -> str:
    return next(c for c in df.columns if "fecha" in c or "semana" in c)


def tool_describe(csv_name: str, *, data_dir: Path | str | None = None) -> dict:
    """Summary de columnas + tipos + rango de fechas."""
    df = pd.read_csv(_ruta_csv(csv_name, data_dir))
    date_col = next((c for c in df.columns if "fecha" in c or "semana" in c), None)
    return {
        "csv": csv_name,
        "n_filas": len(df),
        "columnas": {c: str(df[c].dtype) for c in df.columns},
        "fecha_min": str(df[date_col].min()) if date_col else None,
        "fecha_max": str(df[date_col].max()) if date_col else None,
    }


def tool_filter_by_date(
    csv_name: str, desde: str, hasta: str, *, data_dir: Path | str | None = None
) -> pd.DataFrame:
    """Subset del CSV filtrado por rango de fechas."""
    df = pd.read_csv(_ruta_csv(csv_name, data_dir))
    date_col = _columna_fecha(df)
    return df[(df[date_col] >= desde) & (df[date_col] <= hasta)]


def tool_calc_stats(
    csv_name: str,
    columna: str,
    agrupacion: str | None = None,
    desde: str | None = None,
    hasta: str | None = None,
    *,
    data_dir: Path | str | None = None,
) -> dict:
    """Media, mediana, desv, min, max por CSV/columna, con filtro y agrupación opcionales."""
    df = pd.read_csv(_ruta_csv(csv_name, data_dir))
    if desde or hasta:
        date_col = _columna_fecha(df)
        if desde:
            df = df[df[date_col] >= desde]
        if hasta:
            df = df[df[date_col] <= hasta]

    def _stats(sub: pd.DataFrame) -> dict:
        s = sub[columna]
        return {
            "n": int(len(s)),
            "media": round(float(s.mean()), 3),
            "mediana": round(float(s.median()), 3),
            "desv": round(float(s.std()), 3),
            "min": round(float(s.min()), 3),
            "max": round(float(s.max()), 3),
        }

    if agrupacion:
        return {g: _stats(sub) for g, sub in df.groupby(agrupacion)}
    return _stats(df)


def tool_compare_periods(
    csv_name: str,
    columna: str,
    periodo_a: tuple[str, str],
    periodo_b: tuple[str, str],
    agrupacion: str | None = None,
    *,
    data_dir: Path | str | None = None,
) -> dict:
    """% de cambio absoluto y relativo entre 2 periodos, por grupo si se pide."""
    a = tool_calc_stats(csv_name, columna, agrupacion, *periodo_a, data_dir=data_dir)
    b = tool_calc_stats(csv_name, columna, agrupacion, *periodo_b, data_dir=data_dir)

    def _delta(stats_a: dict | None, stats_b: dict | None) -> dict:
        if stats_a is None or stats_b is None:
            return {"periodo_a": stats_a, "periodo_b": stats_b, "delta_absoluto": None, "delta_pct": None}
        delta_abs = round(stats_b["media"] - stats_a["media"], 3)
        delta_pct = round((delta_abs / stats_a["media"]) * 100.0, 2) if stats_a["media"] else None
        return {"periodo_a": stats_a, "periodo_b": stats_b, "delta_absoluto": delta_abs, "delta_pct": delta_pct}

    if agrupacion:
        return {grupo: _delta(a.get(grupo), b.get(grupo)) for grupo in sorted(set(a) | set(b))}
    return _delta(a, b)


def tool_plot_ascii(serie: list[float], width: int = 20) -> str:
    """Sparkline ASCII para embeber en boletín."""
    blocks = " ▁▂▃▄▅▆▇█"
    if not serie:
        return ""
    lo, hi = min(serie), max(serie)
    rng = hi - lo or 1e-9
    step = max(1, len(serie) // width)
    reduced = [serie[i : i + step] for i in range(0, len(serie), step)][:width]
    return "".join(
        blocks[min(len(blocks) - 1, int((sum(chunk) / len(chunk) - lo) / rng * (len(blocks) - 1)))]
        for chunk in reduced
    )
