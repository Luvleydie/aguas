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


@pytest.fixture
def fake_tools() -> dict[str, Any]:
    return {
        "describe": lambda **_: {"n_filas": 1},
        "filter_by_date": lambda **_: [{"fecha": "2024-10-14"}],
        "calc_stats": lambda **_: {"media": 50.8},
        "compare_periods": lambda **_: {"delta_absoluto": -2.4},
        "plot_ascii": lambda **_: "▁▂▃",
    }

