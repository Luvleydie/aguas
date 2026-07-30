"""Contrato y prompt del Narrador de boletín."""

from __future__ import annotations

from backend.claude_client import ClaudeP, claude_p
from backend.contracts import Boletin, ResultadoEstadista


SYSTEM_PROMPT = """
Eres el Narrador de HidroAlerta.
Recibes hallazgos ya calculados y no puedes abrir CSV, invocar tools ni cambiar
valores o severidades. Redacta una página clara para gobierno, ayuntamiento,
agricultores y medios. Conserva exactamente las secciones Estado de presas,
Precipitación, Alerta y Recomendación, e incluye los sparklines recibidos.
Devuelve solo JSON válido conforme al esquema Boletin.
""".strip()


def ejecutar_narrador(
    resultado: ResultadoEstadista,
    claude_fn: ClaudeP = claude_p,
) -> Boletin:
    del resultado, claude_fn
    raise NotImplementedError("ROJO esperado: agente Narrador pendiente")

