"""Orquestación HidroAlerta: interfaz preparada, implementación pendiente."""

from __future__ import annotations

from pathlib import Path

from backend.claude_client import ClaudeP, claude_p
from backend.contracts import Boletin


def orquestar(
    semana: int,
    data_dir: Path,
    output_dir: Path,
    log_path: Path,
    claude_fn: ClaudeP = claude_p,
) -> Boletin:
    del semana, data_dir, output_dir, log_path, claude_fn
    raise NotImplementedError("ROJO esperado: pipeline pendiente")

