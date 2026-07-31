"""TDD de las 5 tools MCP. Firmas exactas de assets/starter.py.

Cada test recalcula el valor esperado con `statistics` (no con pandas) para
verificar la tool de forma independiente de su propia implementación.
"""

from __future__ import annotations

import statistics

import pandas as pd
import pytest

from backend.mcp_tools.tools import (
    tool_calc_stats,
    tool_compare_periods,
    tool_describe,
    tool_filter_by_date,
    tool_plot_ascii,
)


# ── tool_describe ──────────────────────────────────────────────────────────


def test_describe_reporta_columnas_y_rango_de_fechas(fixture_dir):
    resultado = tool_describe("presas", data_dir=fixture_dir)

    assert resultado["csv"] == "presas"
    assert resultado["n_filas"] == 9
    assert set(resultado["columnas"]) == {"fecha", "presa", "nivel_pct", "volumen_hm3", "capacidad_hm3"}
    assert resultado["fecha_min"] == "2024-09-14"
    assert resultado["fecha_max"] == "2024-10-20"


def test_describe_detecta_columna_semana_en_precipitacion(fixture_dir):
    resultado = tool_describe("precipitacion", data_dir=fixture_dir)

    assert resultado["fecha_min"] == "2024-10-07"
    assert resultado["fecha_max"] == "2024-10-14"


def test_describe_csv_desconocido_falla(fixture_dir):
    with pytest.raises(KeyError):
        tool_describe("inexistente", data_dir=fixture_dir)


def test_describe_usa_hidroalerta_data_dir_cuando_no_se_pasa_data_dir(fixture_dir, monkeypatch):
    monkeypatch.setenv("HIDROALERTA_DATA_DIR", str(fixture_dir))

    resultado = tool_describe("presas")

    assert resultado["n_filas"] == 9


# ── tool_filter_by_date ─────────────────────────────────────────────────────


def test_filter_by_date_devuelve_solo_el_rango_pedido(fixture_dir):
    resultado = tool_filter_by_date("presas", "2024-10-14", "2024-10-20", data_dir=fixture_dir)

    assert isinstance(resultado, pd.DataFrame)
    assert len(resultado) == 6
    assert set(resultado["fecha"]) == {"2024-10-14", "2024-10-20"}


def test_filter_by_date_rango_sin_filas_devuelve_vacio(fixture_dir):
    resultado = tool_filter_by_date("presas", "2024-01-01", "2024-01-31", data_dir=fixture_dir)

    assert len(resultado) == 0


# ── tool_calc_stats ─────────────────────────────────────────────────────────


def test_calc_stats_sin_agrupacion(fixture_dir):
    valores = [45.5, 42.4, 42.1, 60.2, 58.7, 58.4, 49.5, 47.2, 46.9]

    resultado = tool_calc_stats("presas", "nivel_pct", data_dir=fixture_dir)

    assert resultado["n"] == 9
    assert resultado["media"] == pytest.approx(statistics.mean(valores), abs=1e-3)
    assert resultado["mediana"] == pytest.approx(statistics.median(valores), abs=1e-3)
    assert resultado["desv"] == pytest.approx(statistics.stdev(valores), abs=1e-3)
    assert resultado["min"] == min(valores)
    assert resultado["max"] == max(valores)


def test_calc_stats_con_agrupacion_devuelve_una_entrada_por_grupo(fixture_dir):
    resultado = tool_calc_stats("presas", "nivel_pct", agrupacion="presa", data_dir=fixture_dir)

    assert set(resultado) == {"La Tinaja", "Peña del Águila", "Guadalupe Victoria"}
    valores_la_tinaja = [45.5, 42.4, 42.1]
    assert resultado["La Tinaja"]["n"] == 3
    assert resultado["La Tinaja"]["media"] == pytest.approx(statistics.mean(valores_la_tinaja), abs=1e-3)


def test_calc_stats_con_desde_hasta_filtra_antes_de_calcular(fixture_dir):
    resultado = tool_calc_stats(
        "presas", "nivel_pct", desde="2024-10-14", hasta="2024-10-20", data_dir=fixture_dir
    )

    assert resultado["n"] == 6


# ── tool_compare_periods ─────────────────────────────────────────────────────


def test_compare_periods_calcula_delta_absoluto_y_relativo(fixture_dir):
    periodo_a = ("2024-09-14", "2024-09-14")
    periodo_b = ("2024-10-20", "2024-10-20")

    resultado = tool_compare_periods(
        "presas", "nivel_pct", periodo_a, periodo_b, data_dir=fixture_dir
    )

    media_a = statistics.mean([45.5, 60.2, 49.5])
    media_b = statistics.mean([42.1, 58.4, 46.9])
    assert resultado["delta_absoluto"] == pytest.approx(media_b - media_a, abs=1e-3)
    assert resultado["delta_pct"] == pytest.approx((media_b - media_a) / media_a * 100.0, abs=1e-2)


def test_compare_periods_con_agrupacion_devuelve_delta_por_grupo(fixture_dir):
    resultado = tool_compare_periods(
        "presas",
        "nivel_pct",
        ("2024-09-14", "2024-09-14"),
        ("2024-10-20", "2024-10-20"),
        agrupacion="presa",
        data_dir=fixture_dir,
    )

    assert set(resultado) == {"La Tinaja", "Peña del Águila", "Guadalupe Victoria"}
    assert resultado["La Tinaja"]["delta_absoluto"] == pytest.approx(42.1 - 45.5, abs=1e-3)
    assert resultado["Peña del Águila"]["delta_absoluto"] == pytest.approx(58.4 - 60.2, abs=1e-3)
    assert resultado["Guadalupe Victoria"]["delta_absoluto"] == pytest.approx(46.9 - 49.5, abs=1e-3)


def test_compare_periods_con_agrupacion_y_grupo_ausente_en_un_periodo(fixture_dir):
    resultado = tool_compare_periods(
        "presas",
        "nivel_pct",
        ("2024-09-14", "2024-09-14"),
        ("2024-01-01", "2024-01-01"),  # sin filas -> ningún grupo en periodo_b
        agrupacion="presa",
        data_dir=fixture_dir,
    )

    for grupo in ("La Tinaja", "Peña del Águila", "Guadalupe Victoria"):
        assert resultado[grupo]["periodo_b"] is None
        assert resultado[grupo]["delta_absoluto"] is None


# ── tool_plot_ascii ──────────────────────────────────────────────────────────


def test_plot_ascii_serie_vacia_devuelve_cadena_vacia():
    assert tool_plot_ascii([]) == ""


def test_plot_ascii_serie_normal_mapea_min_y_max_a_extremos_de_paleta():
    resultado = tool_plot_ascii([1, 2, 3, 4, 5], width=20)

    assert len(resultado) == 5
    assert resultado[0] == " "  # valor mínimo -> primer bloque de la paleta
    assert resultado[-1] == "█"  # valor máximo -> último bloque de la paleta
