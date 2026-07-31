"""Contrato y prompt del Estadista."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from typing import Any

import pandas as pd

from backend.claude_client import ClaudeP
from backend.llm_client import llm_p
from backend.contracts import (
    EvidenciaTool,
    Metrica,
    PlanAnalisis,
    ResultadoEstadista,
    Severidad,
    ToolName,
    Ventana,
)
from backend.severity import clasificar_severidad, nivel_alerta_global

_METRICA_A_CSV_COLUMNA: dict[Metrica, tuple[str, str]] = {
    Metrica.NIVEL_PRESA: ("presas", "nivel_pct"),
    Metrica.PRECIPITACION_MENSUAL: ("precipitacion", "precipitacion_mm"),
    Metrica.DELTA_NIVEL_MENSUAL: ("presas", "nivel_pct"),
    Metrica.TEMPERATURA_MAXIMA: ("temperatura", "tmax_c"),
}


SYSTEM_PROMPT = """
Eres el Estadista del sistema HidroAlerta. Recibes un "plan_analisis" del Explorador y lo ejecutas usando ÚNICAMENTE las tools MCP reales disponibles. Nunca inventas ni estimas un número — todo valor que reportes debe venir de una tool ejecutada.

TOOLS DISPONIBLES (ejecutan pandas real; los nombres de argumento deben ser
EXACTAMENTE estos, son los nombres reales de la función Python):
- describe(csv_name) → resumen de columnas, tipos, nulos.
- filter_by_date(csv_name, desde, hasta) → subconjunto por fechas.
- calc_stats(csv_name, columna, agrupacion=None, desde=None, hasta=None) → media, mediana, desv, min, max.
- compare_periods(csv_name, columna, periodo_a, periodo_b, agrupacion=None) → % de cambio absoluto y relativo.
- plot_ascii(serie) → sparkline de texto.

``csv_name`` es una de estas tres claves exactas: "presas", "precipitacion", "temperatura".

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


def _resultado_json_seguro(resultado: Any) -> Any:
    if isinstance(resultado, pd.DataFrame):
        return resultado.to_dict(orient="records")
    return resultado


def _columna_fecha(df: pd.DataFrame) -> str:
    return next(c for c in df.columns if "fecha" in c or "semana" in c)


def _valor_real(tool: ToolName, resultado: Any) -> float:
    """Extrae el valor numérico real de la evidencia de la tool — nunca el
    que haya propuesto el modelo (regla 1). ``calc_stats``/``compare_periods``
    devuelven un dict plano, o un dict por grupo si el plan pidió agrupación
    (en ese caso, promedio simple entre grupos: ninguna tool implementa
    ponderación por capacidad u otro criterio)."""

    campo = "delta_absoluto" if tool is ToolName.COMPARE_PERIODS else "media"
    if isinstance(resultado, dict) and campo in resultado:
        return float(resultado[campo])
    if isinstance(resultado, dict):
        valores = [
            sub[campo] for sub in resultado.values() if isinstance(sub, dict) and campo in sub
        ]
        if valores:
            return round(sum(valores) / len(valores), 3)
    raise ValueError(f"No se pudo extraer un valor numérico de la evidencia de {tool.value}")


def _sparkline_real(
    tools: Mapping[str, Callable[..., Any]], metrica: Metrica, ventana: Ventana
) -> str:
    """Sparkline calculado con pandas real, nunca redactado por el modelo (regla 1)."""

    csv_name, columna = _METRICA_A_CSV_COLUMNA[metrica]
    subset = pd.DataFrame(
        tools["filter_by_date"](csv_name=csv_name, desde=str(ventana.desde), hasta=str(ventana.hasta))
    )
    if subset.empty:
        return tools["plot_ascii"](serie=[]) or " "
    fecha_col = _columna_fecha(subset)
    serie = subset.groupby(fecha_col)[columna].mean().tolist()
    return tools["plot_ascii"](serie=serie) or " "


def ejecutar_estadista(
    plan: PlanAnalisis,
    tools: Mapping[str, Callable[..., Any]],
    claude_fn: ClaudeP = llm_p,
) -> ResultadoEstadista:
    evidencias: dict[str, EvidenciaTool] = {}
    for pregunta in plan.preguntas:
        if pregunta.tool is ToolName.PLOT_ASCII:
            # "plot_ascii" no mapea 1:1 a un hallazgo: el Explorador la usa
            # para pedir sparklines de varias series a la vez, con argumentos
            # (series/desde/hasta) que no coinciden con la firma real de
            # tool_plot_ascii(serie, width). Generar esos sparklines reales
            # requeriría además una tabla columna->csv que hoy no está
            # definida en ningún contrato; se deja como TODO documentado y el
            # campo `sparkline` de cada hallazgo lo redacta el modelo por
            # ahora, no el código.
            continue
        tool_fn = tools[pregunta.tool.value]
        args_dict = pregunta.args.model_dump(exclude_none=True)
        resultado = tool_fn(**args_dict)
        evidencias[pregunta.id] = EvidenciaTool(
            tool=pregunta.tool,
            args=pregunta.args.model_dump(mode="json", exclude_none=True),
            resultado=_resultado_json_seguro(resultado),
        )

    prompt = json.dumps(
        {
            "plan": plan.model_dump(mode="json"),
            "evidencia_por_pregunta": {
                pregunta_id: evidencia.model_dump(mode="json")
                for pregunta_id, evidencia in evidencias.items()
            },
        },
        ensure_ascii=False,
    )

    bruto = claude_fn(prompt, system=SYSTEM_PROMPT, schema=ResultadoEstadista.model_json_schema())

    # Regla no negociable: la severidad y la evidencia nunca las decide el
    # modelo — se sustituyen aquí por los resultados reales de las tools y
    # por clasificar_severidad(), que lee únicamente umbrales.json.
    hallazgos_corregidos = []
    for hallazgo in bruto["hallazgos"]:
        metrica = Metrica(hallazgo["metrica"])
        evidencia = evidencias[hallazgo["pregunta_id"]]
        valor = _valor_real(evidencia.tool, evidencia.resultado)
        severidad = clasificar_severidad(metrica, valor)
        hallazgo = {
            **hallazgo,
            "valor": valor,
            "severidad": severidad.value,
            "sparkline": _sparkline_real(tools, metrica, plan.ventana),
            "evidencia": evidencia.model_dump(mode="json"),
        }
        hallazgos_corregidos.append(hallazgo)

    bruto["hallazgos"] = hallazgos_corregidos
    bruto["nivel_alerta_global"] = nivel_alerta_global(
        [Severidad(h["severidad"]) for h in hallazgos_corregidos]
    ).value

    return ResultadoEstadista.model_validate(bruto)

