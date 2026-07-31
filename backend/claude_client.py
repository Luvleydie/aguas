"""Adaptador mínimo de Claude CLI, sustituible por un doble en pruebas."""

from __future__ import annotations

import json
import shutil
import subprocess
from typing import Any, Protocol


class ClaudeP(Protocol):
    def __call__(
        self,
        prompt: str,
        system: str | None = None,
        schema: dict[str, Any] | None = None,
        timeout: int = 120,
    ) -> Any: ...


def claude_p(
    prompt: str,
    system: str | None = None,
    schema: dict[str, Any] | None = None,
    timeout: int = 120,
) -> Any:
    """Ejecuta `claude -p`; no realiza cálculos estadísticos."""

    executable = shutil.which("claude")
    if executable is None:
        raise RuntimeError("No se encontró Claude CLI en PATH")

    command = [executable, "-p"]
    if system:
        command.extend(["--append-system-prompt", system])
    if schema:
        command.extend(["--json-schema", json.dumps(schema, ensure_ascii=False)])
    command.append(prompt)

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
    if result.returncode != 0:
        raise RuntimeError(f"claude -p falló ({result.returncode}): {result.stderr[:500]}")

    output = result.stdout.strip()
    return json.loads(output) if schema else output

