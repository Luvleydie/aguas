from __future__ import annotations

import json
import shutil

import pytest

from backend.contracts import Boletin
from backend.pipeline import orquestar


@pytest.mark.red
def test_pipeline_genera_boletin_y_tres_eventos_de_agente(
    tmp_path, fixture_dir, mock_claude_p
):
    data_dir = tmp_path / "assets"
    output_dir = tmp_path / "boletines"
    log_path = tmp_path / "log_agentes.jsonl"
    data_dir.mkdir()
    output_dir.mkdir()

    for nombre in (
        "presas_2024.csv",
        "precipitacion_estaciones.csv",
        "temperatura_regional.csv",
    ):
        shutil.copy2(fixture_dir / nombre, data_dir / nombre)

    resultado = orquestar(
        semana=42,
        data_dir=data_dir,
        output_dir=output_dir,
        log_path=log_path,
        claude_fn=mock_claude_p,
    )

    assert isinstance(resultado, Boletin)
    assert (output_dir / "BOLETIN_SEMANA_42.md").read_text(encoding="utf-8")
    eventos = [
        json.loads(linea)
        for linea in log_path.read_text(encoding="utf-8").splitlines()
    ]
    assert [evento["agente"] for evento in eventos] == [
        "explorador",
        "estadista",
        "narrador",
    ]

