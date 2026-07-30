# HidroAlerta

## Propósito

HidroAlerta cruza datos de presas, precipitación y temperatura de Durango para
producir un boletín semanal accionable. El flujo objetivo tiene tres agentes:
Explorador de datos, Estadista y Narrador de boletín.

## Estado actual

Este repositorio está detenido deliberadamente en **1 · Setup**:

- ambiente y assets preparados;
- estructura `backend/`, `frontend/` y `tests/`;
- contratos Pydantic v2, fixtures y doble de prueba de `claude_p`;
- pruebas de contratos verdes y pruebas funcionales en rojo por
  `NotImplementedError`.

No implementes el pipeline, las herramientas MCP ni el cálculo de severidad
hasta recibir aprobación explícita para continuar después del checkpoint.

## Reglas no negociables

1. Las estadísticas se calculan con pandas mediante tools MCP; el modelo nunca
   inventa ni calcula resultados.
2. Cada agente tiene un system prompt y un esquema JSON de salida propio.
3. El Narrador no lee CSV ni ejecuta tools.
4. El boletín conserva estas cuatro secciones comparables:
   `Estado de presas`, `Precipitación`, `Alerta` y `Recomendación`.
5. La severidad se deriva únicamente de `assets/umbrales.json`.
6. Cada serie relevante lleva un sparkline ASCII.
7. Las ejecuciones se auditan en `log_agentes.jsonl`.
8. No se modifican los CSV originales dentro de `assets/`.

## Estructura

```text
backend/     Contratos y stubs del pipeline Python
frontend/    Dashboard Next.js existente
tests/       Fixtures, dobles de prueba y especificación ejecutable
assets/      CSV, umbrales, starter y boletín de referencia
```

## Comandos de setup

```powershell
python3 -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
.\.venv\Scripts\python -m pytest
cd frontend
pnpm install
pnpm dev
```

En este checkpoint, `pytest` debe terminar con pruebas funcionales en rojo.
Los fallos esperados están marcados con `@pytest.mark.red` y deben deberse
exclusivamente a stubs aún no implementados.
