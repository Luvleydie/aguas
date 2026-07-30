"""Orquestación HidroAlerta: Explorador → Estadista → {Narrador, Agrónomo}."""

from __future__ import annotations

import json
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
from pydantic import BaseModel

from backend.agents.agronomo import ejecutar_agronomo
from backend.agents.estadista import ejecutar_estadista
from backend.agents.explorador import ejecutar_explorador
from backend.agents.narrador import ejecutar_narrador
from backend.claude_client import ClaudeP, claude_p
from backend.contracts import Boletin, RecomendacionAgricola, ResultadoEstadista
from backend.mcp_tools.tools import (
    tool_calc_stats,
    tool_compare_periods,
    tool_describe,
    tool_filter_by_date,
    tool_plot_ascii,
)

CSVS_DESCRIPCION = ("presas", "precipitacion", "temperatura")


def _cargar_calendario_cultivos(data_dir: Path) -> dict[str, object]:
    df = pd.read_csv(data_dir / "cultivos_valle_guadiana.csv")
    return {"cultivos": df.to_dict(orient="records")}


def _tools_para(data_dir: Path) -> dict[str, object]:
    return {
        "describe": lambda **kw: tool_describe(**kw, data_dir=data_dir),
        "filter_by_date": lambda **kw: tool_filter_by_date(**kw, data_dir=data_dir),
        "calc_stats": lambda **kw: tool_calc_stats(**kw, data_dir=data_dir),
        "compare_periods": lambda **kw: tool_compare_periods(**kw, data_dir=data_dir),
        "plot_ascii": lambda **kw: tool_plot_ascii(**kw),
    }


def _registrar(log_path: Path, agente: str, semana: int, mensaje: dict[str, object]) -> None:
    evento = {
        "agente": agente,
        "semana": semana,
        "timestamp": datetime.now(UTC).isoformat(),
        "mensaje": mensaje,
    }
    with log_path.open("a", encoding="utf-8") as archivo:
        archivo.write(json.dumps(evento, ensure_ascii=False) + "\n")


def _dump(modelo: BaseModel) -> dict[str, object]:
    return modelo.model_dump(mode="json")


def _texto_consulta_rag(hallazgos: ResultadoEstadista) -> str:
    return "\n".join(f"{h.metrica.value}: {h.valor} {h.unidad} — {h.contexto}" for h in hallazgos.hallazgos)


def orquestar(
    semana: int,
    data_dir: Path,
    output_dir: Path,
    log_path: Path,
    claude_fn: ClaudeP = claude_p,
    contexto_historico_fn: Callable[[str], list[dict[str, object]]] | None = None,
) -> tuple[Boletin, RecomendacionAgricola]:
    descripciones = {csv: tool_describe(csv, data_dir=data_dir) for csv in CSVS_DESCRIPCION}

    plan = ejecutar_explorador(descripciones, semana=semana, claude_fn=claude_fn)
    _registrar(log_path, "explorador", semana, _dump(plan))

    hallazgos = ejecutar_estadista(plan, tools=_tools_para(data_dir), claude_fn=claude_fn)
    _registrar(log_path, "estadista", semana, _dump(hallazgos))

    calendario_cultivos = _cargar_calendario_cultivos(data_dir)

    # RAG (tier Pro, opcional): si no se inyecta contexto_historico_fn — o si
    # falla (p. ej. el modelo de embeddings no está disponible) — el Narrador
    # simplemente no recibe contexto histórico; no bloquea el resto del pipeline.
    contexto_historico: list[dict[str, object]] = []
    if contexto_historico_fn is not None:
        try:
            contexto_historico = contexto_historico_fn(_texto_consulta_rag(hallazgos))
        except Exception:
            contexto_historico = []

    # Narrador y Agrónomo parten de los mismos hallazgos y no dependen entre
    # sí: se ejecutan en paralelo, pero se registran en orden fijo (narrador,
    # agronomo) para que el log de auditoría sea determinista.
    with ThreadPoolExecutor(max_workers=2) as executor:
        futuro_boletin = executor.submit(
            ejecutar_narrador, hallazgos, claude_fn=claude_fn, contexto_historico=contexto_historico
        )
        futuro_recomendacion = executor.submit(
            ejecutar_agronomo, hallazgos, calendario_cultivos, semana, claude_fn=claude_fn
        )
        boletin = futuro_boletin.result()
        recomendacion = futuro_recomendacion.result()

    _registrar(log_path, "narrador", semana, _dump(boletin))
    _registrar(log_path, "agronomo", semana, _dump(recomendacion))

    (output_dir / f"BOLETIN_SEMANA_{semana}.md").write_text(boletin.markdown, encoding="utf-8")

    return boletin, recomendacion
