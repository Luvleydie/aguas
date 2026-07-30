"""
Reto 02 · HidroAlerta · Monitor de sequía y presas
Starter (esqueleto). NO incluye la solución — solo la estructura mínima.

Objetivo: pipeline de 3 agentes (explorador → estadista → narrador),
un servidor MCP con 5 tools ejecutables sobre los 3 CSVs, y salida en boletín
markdown validable contra umbrales.json.

Este archivo te da:
  - claude_p() con detección de CLI y stdin=DEVNULL
  - stub del servidor MCP mostrando la firma de las 5 tools
  - Contratos JSON de los 3 tipos de mensaje
  - main() con smoke test: cargar 3 CSVs + preguntar al estadista una stat sencilla

NO te da:
  - system prompts (los escribes tú)
  - la implementación real de las tools (mock incluido para arrancar)
  - la orquestación del pipeline
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).parent
PRESAS = ROOT / "presas_2024.csv"
PRECIP = ROOT / "precipitacion_estaciones.csv"
TEMP = ROOT / "temperatura_regional.csv"
UMBRALES = ROOT / "umbrales.json"
LOG_PATH = ROOT / "log_agentes.jsonl"


# ─────────────────────────────────────────────────────────────
# CLI helper
# ─────────────────────────────────────────────────────────────

def _find_claude() -> str:
    exe = shutil.which("claude")
    if exe:
        return exe
    for c in [
        Path.home() / ".local" / "bin" / "claude",
        Path("/opt/homebrew/bin/claude"),
        Path("/usr/local/bin/claude"),
        Path.home() / ".npm-global" / "bin" / "claude",
    ]:
        if c.exists() and os.access(c, os.X_OK):
            return str(c)
    raise RuntimeError("No encontré `claude`.")


CLAUDE_BIN = _find_claude()


def claude_p(prompt: str, system: str | None = None, schema: dict | None = None, timeout: int = 120) -> Any:
    cmd = [CLAUDE_BIN, "-p"]
    if system:
        cmd += ["--append-system-prompt", system]
    if schema:
        cmd += ["--json-schema", json.dumps(schema)]
    cmd.append(prompt)
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL)
    if r.returncode != 0:
        raise RuntimeError(f"claude -p falló ({r.returncode}): {r.stderr[:500]}")
    out = r.stdout.strip()
    return json.loads(out) if schema else out


# ─────────────────────────────────────────────────────────────
# TOOLS MCP (implementación de referencia — mueve a servidor MCP real)
# ─────────────────────────────────────────────────────────────

CSV_MAP = {"presas": PRESAS, "precipitacion": PRECIP, "temperatura": TEMP}


def tool_describe(csv_name: str) -> dict:
    """Summary de columnas + tipos + rango de fechas."""
    df = pd.read_csv(CSV_MAP[csv_name])
    date_col = next((c for c in df.columns if "fecha" in c or "semana" in c), None)
    return {
        "csv": csv_name,
        "n_filas": len(df),
        "columnas": {c: str(df[c].dtype) for c in df.columns},
        "fecha_min": str(df[date_col].min()) if date_col else None,
        "fecha_max": str(df[date_col].max()) if date_col else None,
    }


def tool_filter_by_date(csv_name: str, desde: str, hasta: str) -> pd.DataFrame:
    """Subset del CSV filtrado por rango de fechas."""
    df = pd.read_csv(CSV_MAP[csv_name])
    date_col = next(c for c in df.columns if "fecha" in c or "semana" in c)
    return df[(df[date_col] >= desde) & (df[date_col] <= hasta)]


def tool_calc_stats(csv_name: str, columna: str, agrupacion: str | None = None,
                    desde: str | None = None, hasta: str | None = None) -> dict:
    """Media, mediana, desv, min, max, tendencia (pendiente regresión lineal)."""
    df = pd.read_csv(CSV_MAP[csv_name])
    if desde or hasta:
        date_col = next(c for c in df.columns if "fecha" in c or "semana" in c)
        if desde:
            df = df[df[date_col] >= desde]
        if hasta:
            df = df[df[date_col] <= hasta]

    def _stats(sub: pd.DataFrame) -> dict:
        s = sub[columna]
        return {
            "n": int(len(s)),
            "media": round(float(s.mean()), 3),
            "mediana": round(float(s.median()), 3),
            "desv": round(float(s.std()), 3),
            "min": round(float(s.min()), 3),
            "max": round(float(s.max()), 3),
        }

    if agrupacion:
        return {g: _stats(sub) for g, sub in df.groupby(agrupacion)}
    return _stats(df)


def tool_compare_periods(csv_name: str, columna: str, periodo_a: tuple[str, str],
                          periodo_b: tuple[str, str], agrupacion: str | None = None) -> dict:
    """% cambio absoluto y relativo entre 2 periodos."""
    a = tool_calc_stats(csv_name, columna, agrupacion, *periodo_a)
    b = tool_calc_stats(csv_name, columna, agrupacion, *periodo_b)
    # TODO: si agrupacion, iterar por grupo. Aquí caso simple.
    if agrupacion:
        raise NotImplementedError("Extiende: compare_periods con agrupación")
    delta_abs = round(b["media"] - a["media"], 3)
    delta_pct = round(((b["media"] - a["media"]) / a["media"]) * 100.0, 2) if a["media"] else None
    return {"periodo_a": a, "periodo_b": b, "delta_absoluto": delta_abs, "delta_pct": delta_pct}


def tool_plot_ascii(serie: list[float], width: int = 20) -> str:
    """Sparkline ASCII para embeber en boletín."""
    blocks = " ▁▂▃▄▅▆▇█"
    if not serie:
        return ""
    lo, hi = min(serie), max(serie)
    rng = hi - lo or 1e-9
    step = max(1, len(serie) // width)
    reduced = [serie[i:i+step] for i in range(0, len(serie), step)][:width]
    return "".join(blocks[min(len(blocks)-1, int((sum(chunk)/len(chunk) - lo) / rng * (len(blocks)-1)))] for chunk in reduced)


# ─────────────────────────────────────────────────────────────
# Contratos JSON entre agentes
# ─────────────────────────────────────────────────────────────

PLAN_ANALISIS_SCHEMA = {
    "type": "object",
    "properties": {
        "ventana": {"type": "object", "properties": {"desde": {"type": "string"}, "hasta": {"type": "string"}}, "required": ["desde", "hasta"]},
        "preguntas": {"type": "array", "items": {
            "type": "object",
            "properties": {"id": {"type": "string"}, "tool": {"type": "string"}, "args": {"type": "object"}},
            "required": ["id", "tool", "args"],
        }},
    },
    "required": ["ventana", "preguntas"],
}

HALLAZGOS_SCHEMA = {
    "type": "object",
    "properties": {"hallazgos": {"type": "array", "items": {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "metrica": {"type": "string"},
            "valor": {"type": "number"},
            "unidad": {"type": "string"},
            "severidad": {"type": "string", "enum": ["info", "warn", "alerta", "critico"]},
            "contexto": {"type": "string"},
        },
        "required": ["id", "metrica", "valor", "severidad"],
    }}},
    "required": ["hallazgos"],
}

BOLETIN_SCHEMA = {
    "type": "object",
    "properties": {
        "semana": {"type": "integer"},
        "nivel_alerta_global": {"type": "string", "enum": ["verde", "amarillo", "naranja", "rojo"]},
        "markdown": {"type": "string"},
        "recomendacion": {"type": "string"},
    },
    "required": ["semana", "nivel_alerta_global", "markdown", "recomendacion"],
}


# ─────────────────────────────────────────────────────────────
# TODO: agentes (completar tú)
# ─────────────────────────────────────────────────────────────

SYS_EXPLORADOR = """TODO: escribe el system prompt del explorador.
Recibe descripciones de los 3 CSVs y la ventana de análisis.
Devuelve un plan_analisis con preguntas específicas para el estadista.
"""

SYS_ESTADISTA = """TODO: system prompt del estadista.
Debe invocar las tools MCP (describe, filter_by_date, calc_stats, compare_periods, plot_ascii).
Convierte resultados numéricos en hallazgos con severidad según umbrales.json.
"""

SYS_NARRADOR = """TODO: system prompt del narrador.
Recibe hallazgos + umbrales. NO ejecuta datos. Produce boletín markdown con 4 secciones fijas:
  1. Estado de presas · 2. Precipitación · 3. Temperatura · 4. Alerta y recomendación.
"""


def agente_explorador(descripciones: dict, semana: int) -> dict:
    raise NotImplementedError("Implementa el agente explorador")


def agente_estadista(plan: dict) -> dict:
    raise NotImplementedError("Implementa el agente estadista")


def agente_narrador(hallazgos: dict, semana: int) -> dict:
    raise NotImplementedError("Implementa el agente narrador")


# ─────────────────────────────────────────────────────────────
# Pipeline
# ─────────────────────────────────────────────────────────────

def orquestar(semana: int) -> dict:
    descripciones = {k: tool_describe(k) for k in ["presas", "precipitacion", "temperatura"]}
    plan = agente_explorador(descripciones, semana)
    hallazgos = agente_estadista(plan)
    boletin = agente_narrador(hallazgos, semana)
    return boletin


# ─────────────────────────────────────────────────────────────
# Smoke test
# ─────────────────────────────────────────────────────────────

def main() -> None:
    print("[+] Descripciones de los 3 CSVs:")
    for k in CSV_MAP:
        print(f"    {k}: {tool_describe(k)}")
    print()
    print("[+] Ejemplo: nivel promedio de La Tinaja en septiembre 2024:")
    stats = tool_calc_stats("presas", "nivel_pct",
                            agrupacion="presa",
                            desde="2024-09-01", hasta="2024-09-30")
    print(f"    {stats.get('La Tinaja')}")
    print()
    print("[+] Sparkline nivel La Tinaja 2024:")
    df = pd.read_csv(PRESAS)
    serie = df[df["presa"] == "La Tinaja"]["nivel_pct"].tolist()
    print(f"    {tool_plot_ascii(serie)}")
    print()
    print("[i] Ahora completa los stubs de los 3 agentes y ejecuta orquestar(semana=42).")


if __name__ == "__main__":
    main()
