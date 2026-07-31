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
    except (RuntimeError, FileNotFoundError):
        try:
            return claude_p(prompt, system=system, schema=schema, timeout=timeout)
        except (RuntimeError, FileNotFoundError):
            ollama_fn = _get_ollama_p()
            return ollama_fn(
                prompt, system=system, schema=schema,
                model=_resolve_ollama_model(), timeout=timeout,
            )
