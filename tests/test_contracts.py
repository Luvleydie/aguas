from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from backend.contracts import (
    AGENT_SCHEMAS,
    Boletin,
    PlanAnalisis,
    RecomendacionAgricola,
    ResultadoEstadista,
)


@pytest.mark.parametrize(
    ("fixture_name", "model"),
    [
        ("plan_analisis.json", PlanAnalisis),
        ("hallazgos.json", ResultadoEstadista),
        ("boletin.json", Boletin),
        ("recomendacion_agricola.json", RecomendacionAgricola),
    ],
)
def test_fixtures_cumplen_contratos(fixture_dir, fixture_name, model):
    contenido = (fixture_dir / fixture_name).read_text(encoding="utf-8")
    assert model.model_validate_json(contenido)


def test_contratos_rechazan_campos_desconocidos(load_fixture):
    plan = load_fixture("plan_analisis.json")
    plan["campo_inventado"] = True

    with pytest.raises(ValidationError, match="campo_inventado"):
        PlanAnalisis.model_validate(plan)


def test_ventana_rechaza_fechas_invertidas(load_fixture):
    plan = load_fixture("plan_analisis.json")
    plan["ventana"] = {"desde": "2024-10-20", "hasta": "2024-10-14"}

    with pytest.raises(ValidationError, match="ventana.desde"):
        PlanAnalisis.model_validate(plan)


def test_boletin_exige_las_cuatro_secciones(load_fixture):
    boletin = load_fixture("boletin.json")
    boletin["markdown"] = boletin["markdown"].replace(
        "## 4 · Alerta y recomendación", "### Cierre"
    )

    with pytest.raises(ValidationError, match="Alerta y recomendación"):
        Boletin.model_validate(boletin)


def test_cada_agente_tiene_esquema_json_propio():
    assert set(AGENT_SCHEMAS) == {"explorador", "estadista", "narrador", "agronomo"}
    assert {schema["title"] for schema in AGENT_SCHEMAS.values()} == {
        "PlanAnalisis",
        "ResultadoEstadista",
        "Boletin",
        "RecomendacionAgricola",
    }
    assert len({json.dumps(schema, sort_keys=True) for schema in AGENT_SCHEMAS.values()}) == 4

