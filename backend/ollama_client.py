"""Adaptador de Ollama local como respaldo gratuito de Claude CLI."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from typing import Any


def ollama_p(
    prompt: str,
    system: str | None = None,
    schema: dict[str, Any] | None = None,
    model: str = "llama3.1",
    timeout: int = 120,
) -> Any:
    """Ejecuta `ollama run` con un modelo local; misma interfaz que `claude_p`."""

    executable = shutil.which("ollama")
    if executable is None:
        raise RuntimeError(
            "No se encontró Ollama en PATH. "
            "Instala desde https://ollama.com o ejecuta: winget install Ollama.Ollama"
        )

    full_prompt = prompt
    if schema:
        schema_hint = (
            "\n\nResponde EXCLUSIVAMENTE con JSON válido que cumpla este esquema. "
            "Sin texto adicional, sin bloques de código, solo JSON puro:\n"
            f"{json.dumps(schema, ensure_ascii=False, indent=2)}"
        )
        full_prompt = prompt + schema_hint

    command = [executable, "run", model]
    if system:
        command.extend(["--system", system])
    command.append(full_prompt)

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
        stdin=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"ollama run falló ({result.returncode}): {result.stderr[:500]}"
        )

    output = result.stdout.strip()
    if not output:
        raise RuntimeError("ollama devolvió salida vacía")

    if schema:
        parsed = _extraer_json(output)
        return parsed

    return output


def _extraer_json(texto: str) -> dict[str, Any]:
    """Extrae JSON de la respuesta de Ollama, manejando bloques de código."""
    # 1. Intentar parsear directamente
    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        pass

    # 2. Buscar bloque ```json ... ```
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", texto, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # 3. Buscar primer { ... } o [ ... ]
    match = re.search(r"(\{.*\}|\[.*\])", texto, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    raise RuntimeError(
        f"No se pudo extraer JSON válido de la respuesta de Ollama: "
        f"{texto[:300]}..."
    )
