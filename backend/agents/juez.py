"""Evaluación de calidad narrativa con LLM-as-judge (tier EXTREMO)."""

from __future__ import annotations

import json
from typing import Any

from backend.claude_client import ClaudeP, claude_p


SYSTEM_PROMPT_JUEZ = """
Eres un evaluador de calidad narrativa. Recibes un texto y la audiencia para la que fue escrito. Evalúa en escala 1-5 estos 4 criterios:

1. claridad: ¿se entiende sin conocimiento técnico previo?
2. tono_apropiado: ¿coincide con la audiencia: formal/divulgativo/accionable?
3. accionabilidad: ¿queda claro qué hacer con esta información?
4. concision: ¿respeta la extensión esperada para su formato?

FORMATO DE SALIDA — responde ÚNICAMENTE este JSON, sin texto adicional:
{
  "audiencia": "gobierno|medios|agricultores",
  "scores": {"claridad": 0, "tono_apropiado": 0, "accionabilidad": 0, "concision": 0},
  "promedio": 0.0,
  "justificacion_breve": "una frase por criterio que puntuó menos de 4"
}

REGLAS:
- Usa la escala 1-5 (1=muy malo, 5=excelente).
- El promedio es el promedio aritmético de los 4 scores.
- Si todos los scores son ≥4, justificacion_breve puede ser una cadena vacía.
- Si algún score es <4, explica brevemente por qué en justificacion_breve.
""".strip()


def agente_juez(
    texto: str,
    audiencia: str,
    claude_fn: ClaudeP = claude_p,
) -> dict[str, Any]:
    prompt = json.dumps(
        {"texto": texto, "audiencia": audiencia},
        ensure_ascii=False,
    )
    resultado = claude_fn(
        prompt,
        system=SYSTEM_PROMPT_JUEZ,
        schema={
            "title": "EvaluacionCalidad",
            "type": "object",
            "properties": {
                "audiencia": {"type": "string", "enum": ["gobierno", "medios", "agricultores"]},
                "scores": {
                    "type": "object",
                    "properties": {
                        "claridad": {"type": "integer", "minimum": 1, "maximum": 5},
                        "tono_apropiado": {"type": "integer", "minimum": 1, "maximum": 5},
                        "accionabilidad": {"type": "integer", "minimum": 1, "maximum": 5},
                        "concision": {"type": "integer", "minimum": 1, "maximum": 5},
                    },
                    "required": ["claridad", "tono_apropiado", "accionabilidad", "concision"],
                },
                "promedio": {"type": "number"},
                "justificacion_breve": {"type": "string"},
            },
            "required": ["audiencia", "scores", "promedio", "justificacion_breve"],
        },
    )
    return resultado


def evaluar_calidad(
    versiones: dict[str, Any] | None,
    claude_fn: ClaudeP = claude_p,
) -> dict[str, Any] | None:
    if versiones is None:
        return None

    audiencias = {
        "version_gobierno": "gobierno",
        "version_medios": "medios",
        "version_agricultores": "agricultores",
    }

    resultados = {}
    for clave, audiencia in audiencias.items():
        version = versiones.get(clave)
        if version is None:
            continue
        texto = version.get("texto", "")
        resultados[clave] = agente_juez(texto=texto, audiencia=audiencia, claude_fn=claude_fn)

    return resultados if resultados else None
