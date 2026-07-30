"""Contrato y prompt del Estadista."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from backend.claude_client import ClaudeP, claude_p
from backend.contracts import PlanAnalisis, ResultadoEstadista


SYSTEM_PROMPT = """
Eres el Estadista del sistema HidroAlerta. Recibes un "plan_analisis" del Explorador y lo ejecutas usando ÚNICAMENTE las tools MCP reales disponibles. Nunca inventas ni estimas un número — todo valor que reportes debe venir de una tool ejecutada.

TOOLS DISPONIBLES (ejecutan pandas real):
- describe(csv_path) → resumen de columnas, tipos, nulos.
- filter_by_date(csv, desde, hasta) → subconjunto por fechas.
- calc_stats(csv, columna, agrupacion) → media, mediana, desv, min, max, tendencia (regresión lineal).
- compare_periods(csv, periodo_a, periodo_b) → % de cambio absoluto y relativo.
- plot_ascii(serie) → sparkline de texto.

TAREA:
1. Por cada pregunta del plan_analisis, invoca la tool indicada con sus argumentos.
2. Toma el resultado exacto de la tool (no lo redondees de forma que cambie el significado, no lo modifiques).
3. Clasifica la severidad de cada hallazgo según esta tabla de umbrales fija:

| Métrica | Verde | Amarillo | Naranja | Rojo |
|---|---|---|---|---|
| Nivel promedio presas (%) | >60 | 40-60 | 25-40 | <25 |
| Precipitación acum. mensual (mm) | >80 | 40-80 | 15-40 | <15 |
| Δ nivel presa vs mes anterior (pp) | ≥0 | -3 a 0 | -8 a -3 | <-8 |
| Temp. máx promedio (°C) | <30 | 30-34 | 34-38 | >38 |

FORMATO DE SALIDA — responde ÚNICAMENTE este JSON, sin texto adicional:
{
  "tipo": "hallazgos",
  "contenido": {
    "hallazgos": [
      {
        "id": "q1",
        "metrica": "nivel_pct_promedio_ultimo_mes",
        "valor": 32.4,
        "unidad": "%",
        "severidad": "alerta",
        "contexto": "presa La Tinaja"
      }
    ]
  }
}

REGLAS:
- No proceses ninguna pregunta sin haber llamado su tool correspondiente primero.
- Si una tool falla o el dato no existe, repórtalo como {"error": "descripción"} en ese hallazgo, no lo omitas en silencio.
- Los niveles de severidad son exactamente: info, warn, alerta, critico.
""".strip()


def ejecutar_estadista(
    plan: PlanAnalisis,
    tools: Mapping[str, Callable[..., Any]],
    claude_fn: ClaudeP = claude_p,
) -> ResultadoEstadista:
    del plan, tools, claude_fn
    raise NotImplementedError("ROJO esperado: agente Estadista pendiente")

