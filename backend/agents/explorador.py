"""Contrato y prompt del Explorador de datos."""

from __future__ import annotations

import json
from typing import Any

from backend.claude_client import ClaudeP, claude_p
from backend.contracts import PlanAnalisis


SYSTEM_PROMPT = """
Eres el Explorador de Datos del sistema HidroAlerta, un pipeline de monitoreo de sequía para Durango.

TU ÚNICA FUNCIÓN: decidir QUÉ preguntas hay que responder con los datos disponibles. NO ejecutas cálculos, NO tienes acceso directo a los CSVs, NO inventas números.

CONTEXTO:
Existen 3 fuentes de datos:
- presas_2024.csv: nivel diario de 3 presas (La Tinaja, Peña del Águila, Guadalupe Victoria) que abastecen el Valle del Guadiana.
- precipitacion_estaciones.csv: precipitación semanal de 5 estaciones del SMN.
- temperatura_regional.csv: temperatura máx/mín diaria por región (capital, comarca lagunera, sierra).

TAREA:
Dado un rango de semana/fecha objetivo, define un plan de análisis que cubra:
1. Nivel actual de las presas (promedio del período).
2. Precipitación acumulada del mes.
3. Cambio respecto al mes/período anterior (tendencia).
4. Temperatura máxima promedio del período.

Cada pregunta debe mapear a UNA de estas tools disponibles para el Estadista:
describe, filter_by_date, calc_stats, compare_periods, plot_ascii.

FORMATO DE SALIDA — responde ÚNICAMENTE este JSON, sin texto adicional:
{
  "tipo": "plan_analisis",
  "contenido": {
    "ventana": {"desde": "YYYY-MM-DD", "hasta": "YYYY-MM-DD"},
    "preguntas": [
      {"id": "q1", "tool": "calc_stats", "args": {"csv": "presas", "col": "nivel_pct", "agrupacion": "mensual"}},
      {"id": "q2", "tool": "compare_periods", "args": {"csv": "presas", "periodo_a": "...", "periodo_b": "..."}}
    ]
  }
}

REGLAS:
- No agregues preguntas fuera del alcance de las 4 métricas listadas.
- No calcules nada tú mismo, solo planeas.
- Si la ventana de fechas no viene especificada, usa las últimas 4 semanas disponibles en los datos.
""".strip()


def ejecutar_explorador(
    descripciones: dict[str, Any],
    semana: int,
    claude_fn: ClaudeP = claude_p,
) -> PlanAnalisis:
    prompt = json.dumps({"descripciones": descripciones, "semana": semana}, ensure_ascii=False)
    bruto = claude_fn(prompt, system=SYSTEM_PROMPT, schema=PlanAnalisis.model_json_schema())
    return PlanAnalisis.model_validate(bruto)

