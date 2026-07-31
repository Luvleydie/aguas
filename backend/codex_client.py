"""Adaptador mínimo de Codex CLI, para reemplazar a Claude CLI."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import os
from typing import Any


def codex_p(
    prompt: str,
    system: str | None = None,
    schema: dict[str, Any] | None = None,
    timeout: int = 120,
) -> Any:
    """Ejecuta `codex exec`; adapta los parámetros al nuevo CLI."""

    executable = shutil.which("codex")
    if executable is None:
        raise RuntimeError("No se encontró Codex CLI en PATH")

    # Si hay system prompt, se lo pegamos al principio del prompt de usuario.
    # (Ya que codex exec no parece tener --append-system-prompt como tal en sus argumentos)
    full_prompt = prompt
    if system:
        full_prompt = f"{system}\n\n{prompt}"

    command = [executable, "exec", "--ephemeral", "--color", "never"]
    
    schema_file = None
    if schema:
        # Codex CLI pide un archivo para --output-schema
        fd, schema_path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(schema, f, ensure_ascii=False)
        command.extend(["--output-schema", schema_path])
        schema_file = schema_path

    command.append(full_prompt)

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            stdin=subprocess.DEVNULL,
            check=False,
        )
    finally:
        if schema_file and os.path.exists(schema_file):
            os.remove(schema_file)

    if result.returncode != 0:
        raise RuntimeError(f"codex exec falló ({result.returncode}): {result.stderr[:500]}")

    output = result.stdout.strip()
    return json.loads(output) if schema else output
