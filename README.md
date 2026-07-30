# HidroAlerta

Monitor de sequía y presas de Durango — pipeline de 4 agentes de Claude
(Explorador, Estadista, Narrador, Agrónomo) que produce un boletín semanal
accionable a partir de datos reales de presas, precipitación y temperatura.
Capstone DuranIA · Metaphorce × Gobierno de Durango.

## Estado actual: Fase 1 · Setup (checkpoint)

Detenido deliberadamente antes de implementar pipeline, tools MCP o
severidad — ver `CLAUDE.md`. `pytest` debe salir en **8 passed / 6 failed**,
con los 6 fallos marcados `@pytest.mark.red` (esperados, por
`NotImplementedError`).

## Documentos del proyecto

| Documento | Para qué |
|---|---|
| `CLAUDE.md` | Reglas no negociables y estado del checkpoint |
| `arquitectura-hidroalerta.md` | Arquitectura completa: agentes, tools MCP, Supabase, API, pantallas, roadmap por fases |
| `flujo-y-estrategia-hidroalerta.md` | Flujo de pantallas por rol y guion de exposición para el instructor |
| `assets/boletin_referencia.md` | Oráculo de formato del boletín |
| `docs/persona-a-backend.md` | Brief de implementación — backend (Fase 2) |
| `docs/persona-b-frontend.md` | Brief de implementación — frontend (Fase 3) |
| `.claude/agents/` | Subagentes de Claude Code (`master` + 9 expertos + `validaciones`) |

## Cómo correrlo (setup actual)

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
.\.venv\Scripts\python -m pytest
cd frontend
pnpm install
pnpm dev
```

## Decisiones de diseño

- **Severidad por tabla de umbrales fija (`assets/umbrales.json`), nunca por
  criterio del modelo** — auditable y reproducible.
- **4 agentes separados**, no un solo prompt: Explorador decide qué
  preguntar, Estadista es el único que toca datos (tools MCP/pandas real),
  Narrador y Agrónomo redactan para audiencias distintas sin volver a tocar
  datos. Contrato JSON fijo entre cada par.
- **4 secciones fijas del boletín** — Estado de presas, Precipitación,
  Temperatura, Alerta y recomendación — según el oráculo real
  (`boletin_referencia.md`), no una versión inventada.
- **Frontend: se conservó el Next.js ya construido en `frontend/`** en vez
  de migrar a React+Vite como sugiere la arquitectura original — el
  dashboard por rol (gobierno/ayuntamiento/medios/agricultor) ya estaba
  hecho y funcional.
- **Dos ramas de trabajo** (`persona-a-backend`, `persona-b-frontend`) que
  mergean a `main` por Pull Request revisado, nunca push directo.

## Ramas y flujo de trabajo

`main` es la rama estable/entregable. Todo el desarrollo pasa por
`persona-a-backend` (backend, Fase 2) o `persona-b-frontend` (frontend,
Fase 3) — ver el brief correspondiente en `docs/` para el comando de
arranque exacto.
