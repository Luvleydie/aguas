"""Contrato y prompt del Explorador de datos."""

from __future__ import annotations

from typing import Any

from backend.claude_client import ClaudeP, claude_p
from backend.contracts import PlanAnalisis


SYSTEM_PROMPT = """
Eres el Explorador de datos de HidroAlerta.
Recibes únicamente descripciones estructurales de tres CSV y una semana ISO.
Decide preguntas específicas sobre últimas cuatro semanas, comparación mensual
y tendencias. No calcules estadísticas ni afirmes hallazgos. Cada pregunta debe
nombrar exactamente una tool MCP y argumentos verificables.
Devuelve solo JSON válido conforme al esquema PlanAnalisis.
""".strip()


def ejecutar_explorador(
    descripciones: dict[str, Any],
    semana: int,
    claude_fn: ClaudeP = claude_p,
) -> PlanAnalisis:
    del descripciones, semana, claude_fn
    raise NotImplementedError("ROJO esperado: agente Explorador pendiente")

