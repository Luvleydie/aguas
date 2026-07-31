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
from backend.agents.supervisor import ejecutar_supervisor
from backend.agents.juez import agente_juez
from backend.contracts import Boletin, PlanAnalisis, RecomendacionAgricola, ResultadoEstadista, SupervisorMultiAudiencia


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


def test_estadista_ignora_el_valor_que_alucine_el_modelo_y_usa_el_de_la_tool(
    load_fixture, mock_claude_p, fake_tools
):
    plan = PlanAnalisis.model_validate(load_fixture("plan_analisis.json"))
    # El modelo "alucina" un valor que no coincide con lo que calculó la tool.
    mock_claude_p.responses["ResultadoEstadista"]["hallazgos"][0]["valor"] = 999.0

    resultado = ejecutar_estadista(plan, tools=fake_tools, claude_fn=mock_claude_p)

    hallazgo_nivel = next(h for h in resultado.hallazgos if h.pregunta_id == "nivel_actual")
    assert hallazgo_nivel.valor != 999.0
    assert hallazgo_nivel.valor == 50.8


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


# ── Tests tier EXTREMO: Supervisor + Juez ────────────────────────────────────


def test_supervisor_devuelve_tres_versiones(load_fixture, mock_claude_p):
    hallazgos = ResultadoEstadista.model_validate(load_fixture("hallazgos.json"))
    recomendacion = RecomendacionAgricola.model_validate(load_fixture("recomendacion_agricola.json"))
    boletin = Boletin.model_validate(load_fixture("boletin.json"))

    resultado = ejecutar_supervisor(
        hallazgos=hallazgos,
        recomendacion=recomendacion,
        boletin=boletin,
        claude_fn=mock_claude_p,
    )

    assert isinstance(resultado, SupervisorMultiAudiencia)
    assert resultado.tipo == "supervisor_multiaudiencia"
    assert hasattr(resultado.contenido, "version_gobierno")
    assert hasattr(resultado.contenido, "version_medios")
    assert hasattr(resultado.contenido, "version_agricultores")


def test_supervisor_cada_version_cumple_schema(load_fixture, mock_claude_p):
    hallazgos = ResultadoEstadista.model_validate(load_fixture("hallazgos.json"))
    recomendacion = RecomendacionAgricola.model_validate(load_fixture("recomendacion_agricola.json"))
    boletin = Boletin.model_validate(load_fixture("boletin.json"))

    resultado = ejecutar_supervisor(
        hallazgos=hallazgos,
        recomendacion=recomendacion,
        boletin=boletin,
        claude_fn=mock_claude_p,
    )

    gov = resultado.contenido.version_gobierno
    assert gov.texto
    assert gov.formato == "markdown"

    medios = resultado.contenido.version_medios
    assert medios.titular
    assert medios.texto
    assert medios.formato == "texto"

    agri = resultado.contenido.version_agricultores
    assert agri.texto
    assert agri.formato == "texto_corto"


def test_supervisor_usa_prompt_y_schema_propios(load_fixture, mock_claude_p):
    from backend.agents.supervisor import SYSTEM_PROMPT as SUPERVISOR_PROMPT

    hallazgos = ResultadoEstadista.model_validate(load_fixture("hallazgos.json"))
    recomendacion = RecomendacionAgricola.model_validate(load_fixture("recomendacion_agricola.json"))
    boletin = Boletin.model_validate(load_fixture("boletin.json"))

    ejecutar_supervisor(
        hallazgos=hallazgos,
        recomendacion=recomendacion,
        boletin=boletin,
        claude_fn=mock_claude_p,
    )

    assert mock_claude_p.calls[-1]["system"] == SUPERVISOR_PROMPT
    assert mock_claude_p.calls[-1]["schema"]["title"] == "SupervisorMultiAudiencia"


def test_juez_devuelve_score_por_version(load_fixture, mock_claude_p):
    texto = "Nivel de presas en 50.8%, tendencia descendente."

    resultado = agente_juez(
        texto=texto,
        audiencia="gobierno",
        claude_fn=mock_claude_p,
    )

    assert isinstance(resultado, dict)
    assert resultado["audiencia"] == "gobierno"
    assert set(resultado["scores"].keys()) == {"claridad", "tono_apropiado", "accionabilidad", "concision"}
    for score in resultado["scores"].values():
        assert 1 <= score <= 5
    assert isinstance(resultado["promedio"], float)


def test_juez_no_se_ejecuta_si_no_hay_versiones(load_fixture, mock_claude_p):
    from backend.agents.juez import evaluar_calidad

    resultado = evaluar_calidad(
        versiones=None,
        claude_fn=mock_claude_p,
    )

    assert resultado is None
    assert len(mock_claude_p.calls) == 0

