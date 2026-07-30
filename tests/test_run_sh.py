"""run.sh no es Python, así que no se ejecuta en la suite (necesitaría pnpm +
red + un build real). Este test es un chequeo estructural: confirma que el
script sigue conteniendo los pasos que arquitectura-hidroalerta.md §6/§12
exige para la demo local (build del frontend + uvicorn en un solo puerto),
para que un cambio futuro no los borre por accidente."""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN_SH = ROOT / "run.sh"


def test_run_sh_existe_y_es_ejecutable():
    """NTFS no tiene bit POSIX de ejecución, así que ``Path.stat()`` no sirve
    en Windows (core.filemode=false es la config recomendada ahí, y no la
    tocamos — regla del proyecto de no editar git config). Lo que importa es
    el modo que git va a checkoutear en Linux/Mac: 100755."""

    assert RUN_SH.is_file()
    resultado = subprocess.run(
        ["git", "ls-files", "--stage", "run.sh"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert resultado.stdout.startswith("100755"), (
        f"run.sh no está marcado ejecutable en el índice de git: {resultado.stdout!r}. "
        "Corre: git update-index --chmod=+x run.sh"
    )


def test_run_sh_construye_el_frontend_antes_de_levantar_la_api():
    contenido = RUN_SH.read_text(encoding="utf-8")
    assert "pnpm build" in contenido
    assert "uvicorn backend.main:app" in contenido
    assert contenido.index("pnpm build") < contenido.index("uvicorn backend.main:app")


def test_run_sh_sirve_todo_en_un_solo_puerto():
    contenido = RUN_SH.read_text(encoding="utf-8")
    assert "--port 8000" in contenido
    assert "HIDROALERTA_FRONTEND_DIR" in contenido


def test_run_sh_falla_rapido_si_falta_el_venv_o_pnpm():
    contenido = RUN_SH.read_text(encoding="utf-8")
    assert "set -euo pipefail" in contenido
    assert "command -v pnpm" in contenido
