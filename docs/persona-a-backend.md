# Brief — Persona A: Backend completo

> Preparación para la fase posterior al checkpoint de `CLAUDE.md`. **No
> implementes nada de esto hasta que el equipo apruebe explícitamente salir
> de la Fase 1 · Setup.**

## Por qué esto es un solo bloque de trabajo (y no se reparte)

`expert-backend` (`.claude/agents/expert-backend.md`) agrupa deliberadamente
tools MCP + los 4 agentes (`ejecutar_*`) + orquestador + API + RAG en un solo
subagente — porque el contrato entre esas piezas es interno y cambia junto
(un cambio de firma en una tool obliga a tocar el agente que la llama en el
mismo commit). Partirlo entre dos personas generaría handoffs constantes por
el mismo archivo. Por eso **Fase 2 (backend) la lleva una sola persona**;
Persona B empieza su parte (frontend) en paralelo, contra fixtures/mocks,
sin esperar a que el backend esté terminado.

## Objetivo

Todo lo que no es interfaz de usuario: severidad, tools MCP, los 4 agentes,
orquestador, Supabase (con `expert-bd`), API FastAPI, RAG.

## Contexto que ya existe

- `backend/contracts.py`: contratos Pydantic v2 de los 4 agentes — es la
  interfaz que Persona B también consume; no lo cambies sin avisarle.
- `backend/severity.py`, `backend/pipeline.py`, `backend/agents/*.py`:
  firmas y `SYSTEM_PROMPT` ya definidos, cuerpo en `NotImplementedError`
  (rojo esperado).
- `assets/umbrales.json`, `assets/cultivos_valle_guadiana.csv`: únicas
  fuentes de verdad para severidad y calendario de cultivos.
- `assets/starter.py`: firmas oficiales de las 5 tools MCP — úsalas tal
  cual, no inventes variantes.
- `backend/data/`: tu copia de trabajo de los CSV/JSON (assets/ es
  solo lectura, regla 8).

## Alcance por fase (roadmap completo en `arquitectura-hidroalerta.md` §12)

**Fase 2 · Backend con TDD**
1. `backend/severity.py` — `clasificar_severidad` contra `umbrales.json`.
2. Tools MCP reales (pandas) con las firmas EXACTAS de `assets/starter.py`
   (`tool_describe`, `tool_filter_by_date`, `tool_calc_stats`,
   `tool_compare_periods`, `tool_plot_ascii`) — cobertura ≥90%.
3. Los 4 agentes en `backend/agents/*.py` (`ejecutar_explorador`,
   `ejecutar_estadista`, `ejecutar_narrador`, `ejecutar_agronomo`), usando
   sus `SYSTEM_PROMPT` ya escritos y `AGENT_SCHEMAS` de `contracts.py`.
4. `backend/pipeline.py` — orquestador: Explorador → Estadista →
   {Narrador, Agrónomo} (estos dos en paralelo, ambos parten de los mismos
   `hallazgos`). Registra un evento por agente en `log_agentes.jsonl`
   (regla 7) y escribe `BOLETIN_SEMANA_{n}.md`.
5. API FastAPI + JWT validado contra Supabase Auth + RLS + sanitización de
   inputs (con `expert-seguridad`, en esta misma fase, no al final). Los 8
   endpoints exactos (rutas, rol requerido, función) están en
   `arquitectura-hidroalerta.md` §6 — impleméntalos tal cual, no inventes
   rutas nuevas.
6. Schema Supabase (`usuarios`, `boletines`, `agent_logs`,
   `acciones_ayuntamiento`, `alertas_enviadas`) con `expert-bd`. Ya hay un
   punto de partida en `backend/db/migrations/0001_init_schema.sql` (enums,
   tablas, FKs, trigger de opt-in WhatsApp, RLS básica) — corre la
   metodología TDD de `expert-bd.md` sobre eso: escribe los tests de
   insert/constraint/RLS por tabla antes de darla por "lista", no asumas
   que el DDL ya es suficiente.
7. **RAG (§5 de la arquitectura)** — sentence-transformers sobre 12
   boletines históricos sintéticos. ⚠️ Ese dataset **no existe todavía en
   ningún lado del repo** — nadie lo generó. Antes de poder implementar el
   RAG tienes que crear tú los 12 boletines sintéticos (mismo formato que
   `assets/boletin_referencia.md`, semanas/años distintos, severidades
   variadas para que la similitud coseno tenga con qué comparar) y
   guardarlos en `backend/data/boletines_historicos/` o directo en Supabase
   (tabla `boletines`) — decide cuál y documéntalo. Es Fase 2 tier Pro: si
   se te complica el tiempo, es lo primero que se puede recortar sin romper
   el resto del pipeline (el Narrador simplemente no recibe
   `contexto_historico`).
8. **`run.sh`** — el comando único que levanta todo (`arquitectura-hidroalerta.md`
   §6 y §12, "Demo local"): build del frontend + `uvicorn` sirviendo API +
   estáticos en un solo puerto. No está en ningún brief todavía; es tuyo
   porque es infraestructura de backend. Coordina con Persona B el comando
   de build exacto de `frontend/` (Next.js) antes de escribirlo.

**Fase 3 (tu parte)**
- Políticas RLS finas por rol con `expert-bd` + `expert-seguridad`.
- Dejar la API corriendo y documentada para que Persona B la consuma.

**Fase 4 · Entrega (junto con Persona B)**
- `validaciones` corre el checklist completo contra `boletin_referencia.md`.
- `expert-docs` + `expert-git` cierran README y commit final.

## Subagentes que usas (en este orden, por feature)

`expert-testing` (rojo) → `expert-bd` (si toca schema) → `expert-backend`
(verde) → `expert-seguridad` → `validaciones` → `expert-git` → `expert-docs`.
Si algo falla: `expert-bugs` diagnostica y corrige — nunca tú a mano, y
nunca editando el test para que pase.

## Interfaz con Persona B

Persona B no toca `backend/`. Le entregas la forma exacta de `Boletin` y
`RecomendacionAgricola` (`backend/contracts.py`, ya fijo) y, en cuanto
exista, la URL/contrato de cada endpoint FastAPI — avísale apenas un
endpoint quede verde para que deje de mockearlo en el frontend.

## Reglas no negociables que más te tocan

Regla 1 (pandas real, el modelo nunca calcula), regla 5 (severidad solo de
`umbrales.json`), regla 7 (`log_agentes.jsonl`), regla 8 (no tocar CSVs de
`assets/`).

## Rama de trabajo

Todo tu trabajo va en `persona-a-backend` (ya existe en `origin`) — **nunca
commitees ni hagas push directo a `main`**. El merge a `main` pasa por PR en
Fase 4, revisado antes de mergear (ver `## Merge a main` abajo).

## Comando para arrancar

Desde una terminal en la raíz del repo (`hidroalerta-limpio/`):

```powershell
git checkout persona-a-backend
git pull origin persona-a-backend
claude
```

Como primer mensaje:

```
Actúa como el subagente master (.claude/agents/master.md). Soy Persona A —
backend, trabajando en la rama persona-a-backend (nunca en main). Lee
docs/persona-a-backend.md y arquitectura-hidroalerta.md §3, §4, §6, §7.
Antes de escribir o ejecutar nada, arma un plan detallado de la Fase 2
(tareas 04-06: tools MCP, los 4 agentes, orquestador, schema Supabase, RAG,
run.sh) con el orden de subagentes por feature
(expert-testing → expert-backend → expert-seguridad → validaciones →
expert-git → expert-docs) y muéstramelo para que lo apruebe antes de
implementar. No toques frontend/ ni ningún archivo de Persona B. Cada
commit va a persona-a-backend, nunca a main. Antes de cada commit,
expert-git debe correr su escaneo de secretos.
```

## Merge a main

Al cerrar Fase 2 (checklist de `validaciones` en verde), `expert-git` abre
un Pull Request `persona-a-backend → main` en GitHub — no hace merge
directo. El usuario revisa y aprueba el PR antes de mergear. Si `main`
avanzó mientras tanto (Persona B ya mergeó su frontend), rebasa o mergea
`main` dentro de tu rama primero y vuelve a correr la suite completa antes
de abrir el PR.
