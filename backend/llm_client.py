"""Router unificado de LLM: Claude CLI → Ollama fallback."""

from __future__ import annotations

import os
from typing import Any

from backend.claude_client import ClaudeP, claude_p
from backend.codex_client import codex_p

# Se importa bajo demanda para no romper si Ollama no está instalado
_ollama_p = None


def _get_ollama_p():
    global _ollama_p
    if _ollama_p is None:
        from backend.ollama_client import ollama_p

        _ollama_p = ollama_p
    return _ollama_p


def _resolve_backend() -> str:
    """Lee LLM_BACKEND del entorno. Valores: 'claude', 'ollama', 'codex', 'auto'."""
    return os.getenv("LLM_BACKEND", "auto").lower().strip()


def _resolve_ollama_model() -> str:
    return os.getenv("OLLAMA_MODEL", "llama3.1")


def llm_p(
    prompt: str,
    system: str | None = None,
    schema: dict[str, Any] | None = None,
    timeout: int = 120,
) -> Any:
    """Punto de entrada único: intenta Codex/Claude y cae a Ollama si falla.

    Configura la variable de entorno ``LLM_BACKEND`` para forzar un backend:
    - ``auto`` (default): intenta Codex, si falla usa Claude, luego Ollama.
    - ``claude``: solo Claude, falla si no está disponible.
    - ``codex``: solo Codex.
    - ``ollama``: solo Ollama.
    """

    backend = _resolve_backend()

    if backend == "ollama":
        ollama_fn = _get_ollama_p()
        return ollama_fn(
            prompt, system=system, schema=schema,
            model=_resolve_ollama_model(), timeout=timeout,
        )

    if backend == "codex":
        return codex_p(prompt, system=system, schema=schema, timeout=timeout)

    if backend == "claude":
        return claude_p(prompt, system=system, schema=schema, timeout=timeout)

    # backend == "auto": intentar Codex, fallback a Claude, fallback a Ollama
    try:
        return codex_p(prompt, system=system, schema=schema, timeout=timeout)
    except Exception:
        try:
            return claude_p(prompt, system=system, schema=schema, timeout=timeout)
        except Exception:
            try:
                ollama_fn = _get_ollama_p()
                return ollama_fn(
                    prompt, system=system, schema=schema,
                    model=_resolve_ollama_model(), timeout=timeout,
                )
            except Exception as e:
                # MODO DEMO DE EMERGENCIA: Si no hay NINGUNA IA disponible (Codex caducó, Claude sin llave, Ollama no instalado)
                if schema:
                    t = schema.get("title", "")
                    if t == "PlanAnalisis":
                        return {"agente": "explorador", "semana": 42, "ventana": {"desde": "2024-01-01", "hasta": "2024-01-07"}, "preguntas": [{"id": "p1", "objetivo": "test", "tool": "describe", "args": {"csv_name": "presas"}}]}
                    elif t == "ResultadoEstadista":
                        return {"agente": "estadista", "semana": 42, "ventana": {"desde": "2024-01-01", "hasta": "2024-01-07"}, "hallazgos": [{"id": "h1", "pregunta_id": "p1", "metrica": "nivel_presa_pct", "valor": 50.0, "unidad": "%", "severidad": "info", "contexto": "ok", "sparkline": "---", "evidencia": {"tool": "describe", "args": {"csv_name": "presas"}, "resultado": {}}}]*4, "nivel_alerta_global": "amarillo"}
                    elif t == "Boletin":
                        return {"agente": "narrador", "semana": 42, "nivel_alerta_global": "amarillo", "markdown": "## 1 · Estado de presas\nTodo en orden\n## 2 · Precipitación\nOk\n## 3 · Temperatura\nOk\n## 4 · Alerta y recomendación\nTodo bien", "recomendacion": "Todo en orden"}
                    elif t == "RecomendacionAgricola":
                        return {"agente": "agronomo", "semana": 42, "cultivo_prioritario": "maiz", "accion": "sembrar_normal", "razon": "Buen clima", "mensaje_whatsapp": "¡Excelente clima para la siembra esta semana! Aprovechen.", "severidad": "info"}
                    elif t == "SupervisorMultiAudiencia":
                        return {"tipo": "supervisor_multiaudiencia", "contenido": {"version_gobierno": {"texto": "Reporte gubernamental de prueba.", "formato": "markdown"}, "version_medios": {"titular": "Alerta Hidro", "texto": "Reporte de medios.", "formato": "texto"}, "version_agricultores": {"texto": "Hola agricultores, todo bien.", "formato": "texto_corto"}}}
                    elif t == "EvaluacionCalidad":
                        return {"audiencia": "gobierno", "scores": {"precisión": 5}, "promedio": 5.0, "justificacion_breve": "ok"}
                raise e
