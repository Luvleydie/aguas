from __future__ import annotations

import json

from backend.agents.agronomo import SYSTEM_PROMPT as AGRONOMO_PROMPT
from backend.agents.agronomo import ejecutar_agronomo
from backend.agents.estadista import SYSTEM_PROMPT as ESTADISTA_PROMPT
from backend.agents.estadista import ejecutar_estadista
from backend.agents.explorador import SYSTEM_PROMPT as EXPLORADOR_PROMPT
from backend.agents.explorador import ejecutar_explorador
from backend.agents.narrador import SYSTEM_PROMPT as NARRADOR_PROMPT
from backend.agents.narrador import ejecutar_narrador
from backend.contracts import Boletin, PlanAnalisis, RecomendacionAgricola, ResultadoEstadista


def test_explorador_usa_prompt_y_schema_propios(load_fixture, mock_claude_p):
    resultado = ejecutar_explorador(
        load_fixture("descripciones.json"),
        semana=42,
        claude_fn=mock_claude_p,
    )

    assert isinstance(resultado, PlanAnalisis)
    assert mock_claude_p.calls[-1]["system"] == EXPLORADOR_PROMPT
    assert mock_claude_p.calls[-1]["schema"]["title"] == "PlanAnalisis"


def test_estadista_entrega_evidencia_de_tools(
    load_fixture, mock_claude_p, fake_tools
):
    plan = PlanAnalisis.model_validate(load_fixture("plan_analisis.json"))

    resultado = ejecutar_estadista(
        plan,
        tools=fake_tools,
        claude_fn=mock_claude_p,
    )

    assert isinstance(resultado, ResultadoEstadista)
    assert all(hallazgo.evidencia.resultado is not None for hallazgo in resultado.hallazgos)
    assert mock_claude_p.calls[-1]["system"] == ESTADISTA_PROMPT
    assert mock_claude_p.calls[-1]["schema"]["title"] == "ResultadoEstadista"


def test_estadista_calcula_sparkline_con_tools_no_con_el_modelo(
    load_fixture, mock_claude_p, fake_tools
):
    plan = PlanAnalisis.model_validate(load_fixture("plan_analisis.json"))

    resultado = ejecutar_estadista(
        plan,
        tools=fake_tools,
        claude_fn=mock_claude_p,
    )

    fabricado_por_el_modelo = {
        h["sparkline"] for h in load_fixture("hallazgos.json")["hallazgos"]
    }
    for hallazgo in resultado.hallazgos:
        assert hallazgo.sparkline == "▁▂▃"
        assert hallazgo.sparkline not in fabricado_por_el_modelo


def test_narrador_genera_secciones_sin_recibir_csv(load_fixture, mock_claude_p):
    hallazgos = ResultadoEstadista.model_validate(load_fixture("hallazgos.json"))

    resultado = ejecutar_narrador(hallazgos, claude_fn=mock_claude_p)

    assert isinstance(resultado, Boletin)
    assert mock_claude_p.calls[-1]["system"] == NARRADOR_PROMPT
    assert mock_claude_p.calls[-1]["schema"]["title"] == "Boletin"


def test_narrador_incluye_contexto_historico_en_el_prompt_cuando_se_pasa(load_fixture, mock_claude_p):
    hallazgos = ResultadoEstadista.model_validate(load_fixture("hallazgos.json"))
    contexto = [{"id": "2020-S48", "similitud": 0.87, "extracto": "..."}]

    ejecutar_narrador(hallazgos, claude_fn=mock_claude_p, contexto_historico=contexto)

    prompt_enviado = json.loads(mock_claude_p.calls[-1]["prompt"])
    assert prompt_enviado["contexto_historico"] == contexto


def test_agronomo_traduce_hallazgos_en_mensaje_simple(load_fixture, mock_claude_p):
    hallazgos = ResultadoEstadista.model_validate(load_fixture("hallazgos.json"))
    calendario = load_fixture("calendario_cultivos.json")

    resultado = ejecutar_agronomo(
        hallazgos,
        calendario_cultivos=calendario,
        semana=42,
        claude_fn=mock_claude_p,
    )

    assert isinstance(resultado, RecomendacionAgricola)
    assert mock_claude_p.calls[-1]["system"] == AGRONOMO_PROMPT
    assert mock_claude_p.calls[-1]["schema"]["title"] == "RecomendacionAgricola"

