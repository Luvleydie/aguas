"""Contrato y prompt del Estadista."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from backend.claude_client import ClaudeP, claude_p
from backend.contracts import PlanAnalisis, ResultadoEstadista


SYSTEM_PROMPT = """
Eres el Estadista de HidroAlerta.
Ejecuta cada pregunta del PlanAnalisis exclusivamente mediante las tools MCP
describe, filter_by_date, calc_stats, compare_periods y plot_ascii. Nunca hagas
aritmética ni estimes números con el modelo. Interpreta los resultados exactos,
adjunta evidencia de la tool y clasifica severidad sólo con umbrales.json.
Devuelve solo JSON válido conforme al esquema ResultadoEstadista.
""".strip()


def ejecutar_estadista(
    plan: PlanAnalisis,
    tools: Mapping[str, Callable[..., Any]],
    claude_fn: ClaudeP = claude_p,
) -> ResultadoEstadista:
    del plan, tools, claude_fn
    raise NotImplementedError("ROJO esperado: agente Estadista pendiente")

