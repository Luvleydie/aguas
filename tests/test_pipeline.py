from __future__ import annotations

import json
import shutil

from backend.contracts import Boletin, RecomendacionAgricola
from backend.pipeline import orquestar


def test_pipeline_genera_boletin_y_recomendacion_con_cuatro_eventos_de_agente(
    tmp_path, fixture_dir, mock_claude_p, monkeypatch
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
        "umbrales.json",
        "cultivos_valle_guadiana.csv",
    ):
        shutil.copy2(fixture_dir / nombre, data_dir / nombre)

    monkeypatch.setenv("HIDROALERTA_DATA_DIR", str(data_dir))

    boletin, recomendacion = orquestar(
        semana=42,
        data_dir=data_dir,
        output_dir=output_dir,
        log_path=log_path,
        claude_fn=mock_claude_p,
    )

    assert isinstance(boletin, Boletin)
    assert isinstance(recomendacion, RecomendacionAgricola)
    assert (output_dir / "BOLETIN_SEMANA_42.md").read_text(encoding="utf-8") == boletin.markdown

    eventos = [
        json.loads(linea)
        for linea in log_path.read_text(encoding="utf-8").splitlines()
    ]
    assert [evento["agente"] for evento in eventos] == [
        "explorador",
        "estadista",
        "narrador",
        "agronomo",
    ]
    assert all("timestamp" in evento for evento in eventos)


def test_pipeline_usa_contexto_historico_cuando_se_inyecta(
    tmp_path, fixture_dir, mock_claude_p, monkeypatch
):
    """RAG (punto 7) es opcional: solo se usa si el llamador inyecta
    contexto_historico_fn (ver backend/main.py)."""
    data_dir = tmp_path / "assets"
    output_dir = tmp_path / "boletines"
    log_path = tmp_path / "log_agentes.jsonl"
    data_dir.mkdir()
    output_dir.mkdir()

    for nombre in (
        "presas_2024.csv",
        "precipitacion_estaciones.csv",
        "temperatura_regional.csv",
        "umbrales.json",
        "cultivos_valle_guadiana.csv",
    ):
        shutil.copy2(fixture_dir / nombre, data_dir / nombre)
    monkeypatch.setenv("HIDROALERTA_DATA_DIR", str(data_dir))

    contexto_falso = [{"id": "2020-S48", "similitud": 0.9, "extracto": "..."}]
    llamadas: list[str] = []

    def contexto_historico_fn(texto_consulta: str):
        llamadas.append(texto_consulta)
        return contexto_falso

    from backend.pipeline import orquestar

    orquestar(
        semana=42,
        data_dir=data_dir,
        output_dir=output_dir,
        log_path=log_path,
        claude_fn=mock_claude_p,
        contexto_historico_fn=contexto_historico_fn,
    )

    assert len(llamadas) == 1
    llamada_narrador = next(c for c in mock_claude_p.calls if c["schema"]["title"] == "Boletin")
    assert json.loads(llamada_narrador["prompt"])["contexto_historico"] == contexto_falso


def test_pipeline_ignora_fallas_de_rag_sin_romper_el_pipeline(
    tmp_path, fixture_dir, mock_claude_p, monkeypatch
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
        "umbrales.json",
        "cultivos_valle_guadiana.csv",
    ):
        shutil.copy2(fixture_dir / nombre, data_dir / nombre)
    monkeypatch.setenv("HIDROALERTA_DATA_DIR", str(data_dir))

    def contexto_historico_fn(_texto_consulta: str):
        raise RuntimeError("modelo de embeddings no disponible")

    from backend.pipeline import orquestar

    boletin, recomendacion = orquestar(
        semana=42,
        data_dir=data_dir,
        output_dir=output_dir,
        log_path=log_path,
        claude_fn=mock_claude_p,
        contexto_historico_fn=contexto_historico_fn,
    )

    assert isinstance(boletin, Boletin)
    assert isinstance(recomendacion, RecomendacionAgricola)
