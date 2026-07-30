# HidroAlerta

## Propósito

HidroAlerta cruza datos de presas, precipitación y temperatura de Durango para
producir un boletín semanal accionable y una recomendación agrícola en
lenguaje simple. El flujo objetivo tiene cuatro agentes: Explorador de datos,
Estadista, Narrador de boletín y Agrónomo (recomendación agrícola).

## Estado actual

Este repositorio está detenido deliberadamente en **1 · Setup**:

- ambiente y assets preparados;
- estructura `backend/`, `frontend/` y `tests/`;
- contratos Pydantic v2 para los 4 agentes, fixtures y doble de prueba de
  `claude_p`;
- pruebas de contratos verdes y pruebas funcionales en rojo por
  `NotImplementedError`.

**Checkpoint aprobado (2026-07-30):** el usuario dio luz verde explícita para
salir de Fase 1 y arrancar Fase 2 (backend) y Fase 3 (frontend). `master` y
los subagentes de implementación (`expert-backend`, `expert-frontend-web`,
`expert-bd`, etc.) ya pueden implementar pipeline, tools MCP, severidad y
pantallas — siguiendo TDD estricto y el reparto de `docs/persona-a-backend.md`
/ `docs/persona-b-frontend.md`, cada quien en su rama
(`persona-a-backend` / `persona-b-frontend`), nunca directo en `main`.

## Reglas no negociables

1. Las estadísticas se calculan con pandas mediante tools MCP; el modelo nunca
   inventa ni calcula resultados.
2. Cada agente tiene un system prompt y un esquema JSON de salida propio.
3. El Narrador no lee CSV ni ejecuta tools.
4. El boletín conserva estas cuatro secciones comparables (oráculo:
   `assets/boletin_referencia.md`): `Estado de presas`, `Precipitación`,
   `Temperatura` y `Alerta y recomendación` (combinada — NO existe una
   sección "Recomendación" separada).
5. La severidad se deriva únicamente de `assets/umbrales.json`.
6. Cada serie relevante lleva un sparkline ASCII.
7. Las ejecuciones se auditan en `log_agentes.jsonl`.
8. No se modifican los CSV originales dentro de `assets/`.

## Estructura

```text
backend/     Contratos y stubs del pipeline Python
backend/data/ Copia de trabajo de CSVs + umbrales.json + cultivos_valle_guadiana.csv
frontend/    Dashboard Next.js existente (ver desviación abajo)
tests/       Fixtures, dobles de prueba y especificación ejecutable
assets/      CSV, umbrales, cultivos, starter y boletín de referencia (solo lectura)
docs/        Briefs de implementación para la siguiente fase
```

## Documentos de referencia

- `arquitectura-hidroalerta.md` — arquitectura completa v2 (agentes, tools MCP,
  Supabase, API, pantallas por rol, roadmap de fases). **Fuente de verdad**
  por encima de este archivo para cualquier detalle no cubierto aquí.
- `flujo-y-estrategia-hidroalerta.md` — flujo de pantallas por rol y
  justificación de decisiones de diseño (para exponer al instructor).
- `assets/boletin_referencia.md` — oráculo de formato del boletín.
- `assets/umbrales.json` — única fuente de verdad de severidad.
- `assets/cultivos_valle_guadiana.csv` — tabla de referencia del Agrónomo.

**Desviación deliberada respecto a `arquitectura-hidroalerta.md`:** esa
arquitectura especifica frontend en React+Vite (`frontend-web/`) servido por
FastAPI. Este repo ya tenía un dashboard Next.js completo y funcional en
`frontend/` (login + 4 roles) — se decidió conservarlo. Los subagentes en
`.claude/agents/` traen una nota de adaptación para no intentar migrar a
Vite. Reparto de trabajo entre las dos personas del equipo:
`docs/persona-a-backend.md` (backend completo: tools MCP, 4 agentes,
orquestador, API, Supabase) y `docs/persona-b-frontend.md` (Next.js sobre
`frontend/`, en paralelo con mocks).

## Subagentes de Claude Code

`.claude/agents/` — `master` (orquestador) + 9 expertos
(`expert-backend`, `expert-bd`, `expert-bugs`, `expert-docs`,
`expert-frontend-web`, `expert-frontend-mobile`, `expert-git`,
`expert-seguridad`, `expert-testing`) + `validaciones`. TDD estricto: todo
código pasa primero por `expert-testing` (rojo) antes de implementarse.
Roadmap completo de fases en `arquitectura-hidroalerta.md` §12.

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
