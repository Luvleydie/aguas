from __future__ import annotations
import pytest
from backend.mcp_tools.plan_accion import generar_plan_accion

@pytest.mark.red
def test_generar_plan_accion_filtra_por_nivel_alerta():
    resultado = generar_plan_accion("naranja")
    assert all(accion["nivel_alerta"] == "naranja" for accion in resultado)
    assert len(resultado) > 0

@pytest.mark.red
def test_generar_plan_accion_ordenado_por_prioridad():
    resultado = generar_plan_accion("naranja")
    prioridades = [accion["prioridad"] for accion in resultado]
    assert prioridades == sorted(prioridades)
