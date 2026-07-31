from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest


FIXTURES = Path(__file__).parent / "fixtures"


def _read_json(name: str) -> dict[str, Any]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class FakeClaudeP:
    """Doble secuencial de `claude_p` que nunca llama a la red ni a la CLI."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.responses = {
            "PlanAnalisis": _read_json("plan_analisis.json"),
            "ResultadoEstadista": _read_json("hallazgos.json"),
            "Boletin": _read_json("boletin.json"),
            "RecomendacionAgricola": _read_json("recomendacion_agricola.json"),
        }

    def __call__(
        self,
        prompt: str,
        system: str | None = None,
        schema: dict[str, Any] | None = None,
        timeout: int = 120,
    ) -> dict[str, Any]:
        if schema is None:
            raise AssertionError("cada agente debe enviar su esquema JSON propio")
        title = schema.get("title")
        if title not in self.responses:
            raise AssertionError(f"esquema inesperado en mock: {title!r}")
        self.calls.append(
            {
                "prompt": prompt,
                "system": system,
                "schema": copy.deepcopy(schema),
                "timeout": timeout,
            }
        )
        return copy.deepcopy(self.responses[title])


@pytest.fixture
def fixture_dir() -> Path:
    return FIXTURES


@pytest.fixture
def load_fixture():
    return _read_json


@pytest.fixture
def mock_claude_p() -> FakeClaudeP:
    return FakeClaudeP()


_SERIES_POR_CSV: dict[str, list[dict[str, Any]]] = {
    "presas": [
        {"fecha": "2024-10-14", "nivel_pct": 51.2},
        {"fecha": "2024-10-17", "nivel_pct": 50.6},
        {"fecha": "2024-10-20", "nivel_pct": 50.1},
    ],
    "precipitacion": [
        {"fecha": "2024-10-01", "precipitacion_mm": 12.0},
        {"fecha": "2024-10-08", "precipitacion_mm": 18.4},
        {"fecha": "2024-10-15", "precipitacion_mm": 23.3},
    ],
    "temperatura": [
        {"fecha": "2024-10-14", "tmax_c": 27.1},
        {"fecha": "2024-10-17", "tmax_c": 26.0},
        {"fecha": "2024-10-20", "tmax_c": 25.8},
    ],
}


_STATS_POR_CSV: dict[str, dict[str, float]] = {
    "presas": {"n": 3, "media": 50.8, "mediana": 50.8, "desv": 3.6, "min": 46.9, "max": 58.4},
    "precipitacion": {"n": 5, "media": 53.7, "mediana": 41.7, "desv": 34.9, "min": 22.1, "max": 118.9},
    "temperatura": {"n": 7, "media": 26.3, "mediana": 26.3, "desv": 0.7, "min": 24.8, "max": 27.4},
}


@pytest.fixture
def fake_tools() -> dict[str, Any]:
    return {
        "describe": lambda **_: {"n_filas": 1},
        "filter_by_date": lambda csv_name, **_: _SERIES_POR_CSV.get(csv_name, []),
        "calc_stats": lambda csv_name, **_: _STATS_POR_CSV.get(csv_name, {"media": 0.0}),
        "compare_periods": lambda **_: {"delta_absoluto": -2.4},
        "plot_ascii": lambda **_: "▁▂▃",
    }

