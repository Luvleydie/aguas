# HidroAlerta · Documentación viva

Última actualización: **2026-07-30**

Este documento es la fuente canónica del estado técnico de HidroAlerta. Debe
actualizarse después de cada cambio validado por medio del agente
`documentacion-hidroalerta`.

## 1. Objetivo

HidroAlerta cruza datos de presas, precipitación y temperatura de Durango para
producir un boletín semanal que ayude a gobierno, ayuntamientos, agricultores y
medios a reaccionar antes ante condiciones de sequía.

Las presas principales del alcance inicial son:

- La Tinaja;
- Peña del Águila;
- Guadalupe Victoria.

## 2. Estado actual

Leyenda: ✅ completado · 🟡 en progreso · ⬜ pendiente.

| Componente | Estado | Evidencia |
|---|:---:|---|
| Ambiente Python y assets | ✅ | `.venv/`, `assets/`, `requirements*.txt` |
| Contratos de cuatro agentes | ✅ | `backend/contracts.py` (incluye Agrónomo) |
| Fixtures y doble de `claude_p` | ✅ | `tests/fixtures/`, `tests/conftest.py` |
| Clasificación de severidad | ✅ | `backend/severity.py`, `tests/test_severity.py` (93% cobertura) |
| Tools MCP con pandas | ✅ | `backend/mcp_tools/tools.py`, `tests/test_mcp_tools.py` (100% cobertura) |
| Explorador, Estadista, Narrador, Agrónomo | ✅ | `backend/agents/*.py`; sparkline de cada hallazgo calculado con `tool_plot_ascii` real, nunca redactado por el modelo |
| Orquestación y `log_agentes.jsonl` | ✅ | `backend/pipeline.py`: Explorador → Estadista → {Narrador, Agrónomo en paralelo}, 4 eventos por corrida |
| API FastAPI (8 endpoints) | ✅ | `backend/main.py`, `tests/test_main.py` (JWT vs. Supabase Auth, RLS vía token del usuario, 20 tests) |
| Schema Supabase y RLS | ✅ | `backend/db/migrations/0001-0004`, `tests/db/` — 32 tests contra el proyecto Supabase real (insert/constraint/RLS por rol y tabla) |
| RAG (12 boletines sintéticos) | ✅ | `backend/data/boletines_historicos/` (3 boletines por cada severidad), `backend/rag.py`, `tests/test_rag.py` (95% cobertura) |
| `run.sh` (demo en un solo puerto) | ✅ | Build de `frontend/` (`output: 'export'`) servido por FastAPI vía `montar_frontend_estatico()`; `tests/test_run_sh.py` |
| Dashboard integrado con backend | ⬜ | Persona B (frontend), fuera de este documento |

### Verificación estable más reciente

```powershell
.\.venv\Scripts\python -m pytest --ignore=tests\db -q      # 67 pruebas, sin red
.\.venv\Scripts\python -m pytest tests\db -q                # 32 pruebas, contra Supabase real (requiere .env)
```

Resultado comprobado: **99 pruebas aprobadas** (67 + 32), suite completa en
verde. Todo Fase 2 (backend) está implementado sobre `persona-a-backend`,
pendiente del PR a `main` que se abre al cerrar Fase 4 junto con Persona B.

## 3. Arquitectura objetivo

```text
assets/*.csv
    │
    ▼
Explorador ── plan JSON
    │
    ▼
Estadista ── tools MCP con pandas ──► resultados numéricos exactos
    │
    ▼
hallazgos JSON + severidad + sparklines
    │
    ▼
Narrador ──► BOLETIN_SEMANA_N.md
    │
    ├──► log_agentes.jsonl
    ├──► persistencia Supabase
    └──► dashboard Next.js
```

Regla central: el modelo interpreta resultados; no calcula estadísticas.

## 4. Estructura del repositorio

```text
assets/       CSV originales, umbrales, starter y boletín de referencia
backend/      Contratos, cliente Claude, agentes, severidad y pipeline
frontend/     Dashboard Next.js
supabase/     Configuración y migraciones de base de datos
tests/        Contratos, agentes, severidad, pipeline y pruebas de BD
docs/         Documentación técnica viva
.claude/      Agentes y skills locales de Claude Code
```

## 5. Datos de entrada

| Archivo | Frecuencia | Campos principales |
|---|---|---|
| `assets/presas_2024.csv` | diaria | fecha, presa, nivel, volumen, capacidad |
| `assets/precipitacion_estaciones.csv` | semanal | semana, estación, precipitación, días con lluvia |
| `assets/temperatura_regional.csv` | diaria | fecha, región, Tmax, Tmin, Tmedia |
| `assets/umbrales.json` | configuración | rangos por métrica y orden de alerta |

Los CSV originales son de solo lectura.

## 6. Contratos entre agentes

### Explorador

Devuelve `PlanAnalisis`: semana, ventana temporal y preguntas concretas, cada
una asociada con una tool MCP y argumentos verificables.

### Estadista

Devuelve `ResultadoEstadista`: hallazgos numéricos, evidencia de tools,
severidad, contexto y sparkline. No debe calcular estadísticas mediante el
modelo.

### Narrador

Devuelve `Boletin`: nivel global, Markdown y recomendación. No puede leer CSV ni
invocar tools.

El boletín debe conservar estas secciones:

1. Estado de presas;
2. Precipitación;
3. Alerta;
4. Recomendación.

## 7. Severidad

`backend/severity.py` carga los rangos desde `assets/umbrales.json`.

| Color configurado | Severidad del contrato |
|---|---|
| verde | `info` |
| amarillo | `warn` |
| naranja | `alerta` |
| rojo | `critico` |

Los rangos se evalúan como inclusivos. Cuando dos rangos comparten un extremo,
prevalece el primer color de `alerta_global.orden`. Valores no finitos, fuera de
dominio o situados en huecos de la configuración producen un error explícito.

## 8. Desarrollo local

### Backend

```powershell
python3 -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
.\.venv\Scripts\python -m pytest tests\test_contracts.py tests\test_severity.py -q
```

### Frontend

```powershell
cd frontend
pnpm install
pnpm dev
```

No se deben confirmar archivos `.env`, entornos virtuales, caches ni
`settings.local.json`.

## 9. Decisiones de diseño

| ID | Fecha | Decisión | Motivo |
|---|---|---|---|
| ADR-001 | 2026-07-30 | Las estadísticas se ejecutan con pandas mediante MCP. | Evitar cálculos inventados o imprecisos del modelo. |
| ADR-002 | 2026-07-30 | `assets/umbrales.json` es la fuente de severidad. | Mantener reglas verificables y configurables. |
| ADR-003 | 2026-07-30 | Cada agente tiene prompt y esquema JSON propio. | Separar responsabilidades y validar contratos. |
| ADR-004 | 2026-07-30 | El Narrador no recibe acceso directo a datos. | Impedir que altere o recalcule hallazgos. |
| ADR-005 | 2026-07-30 | La documentación distingue implementado, en progreso y pendiente. | Evitar que el roadmap se confunda con el estado real. |
| ADR-006 | 2026-07-30 | El sparkline de cada hallazgo lo calcula el Estadista con `tool_plot_ascii` sobre la serie real (agregada por fecha), nunca lo redacta el modelo. | El esquema `Hallazgo.sparkline` es obligatorio; dejar que el modelo lo rellenara violaba la regla 1 (pandas real, el modelo nunca calcula). |
| ADR-007 | 2026-07-30 | `frontend/next.config.mjs` usa `output: 'export'` para que `run.sh` sirva el build de Next.js como estáticos desde FastAPI en un solo puerto. | El frontend no tiene rutas API ni middleware, así que el export estático es viable sin perder funcionalidad; alternativa (proxy a `next start`) era más compleja sin beneficio real aquí. |

## 10. Riesgos y deuda técnica

- `CLAUDE.md` y el boletín de referencia presentan diferencias históricas sobre
  la distribución exacta de secciones; los contratos actuales son la referencia
  ejecutable.
- Los rangos de `delta_nivel_mensual_pp` se solapan en algunos extremos; el
  orden del JSON resuelve la precedencia.
- El selector de roles del frontend es demostrativo y no constituye
  autorización.
- `backend/agents/estadista.py` ignora explícitamente las preguntas del plan
  con `tool: "plot_ascii"` (el Explorador las pide con argumentos que no
  coinciden con la firma real de la tool) — no afecta el resultado porque el
  sparkline de cada hallazgo se calcula aparte, directo desde `_METRICA_A_CSV_COLUMNA`,
  pero es deuda técnica documentada en el propio archivo.
- Fase 2 (backend) está completa en `persona-a-backend` pero no mergeada a
  `main` — el PR se abre en Fase 4, junto con Persona B.

## 11. Próximos hitos

1. Persona B: conectar el dashboard Next.js a la API real (endpoints ya
   documentados y en verde).
2. Rebasar/mergear `main` dentro de `persona-a-backend` si Persona B ya
   mergeó su frontend, y volver a correr la suite completa antes del PR.
3. `validaciones`: correr el checklist E2E contra `boletin_referencia.md`.
4. Abrir el PR `persona-a-backend → main` (Fase 4) para revisión del usuario.

## 12. Protocolo de actualización

Después de cada feature:

1. ejecutar las pruebas relevantes;
2. cambiar el estado únicamente con evidencia;
3. actualizar arquitectura y comandos si cambiaron;
4. agregar o modificar una ADR cuando exista una decisión duradera;
5. registrar el cambio en la bitácora;
6. comprobar que no se incluyeron secretos.

## 13. Bitácora

| Fecha | Cambio | Evidencia |
|---|---|---|
| 2026-07-30 | Setup inicial, contratos y fixtures. | Siete pruebas de contratos aprobadas en el checkpoint. |
| 2026-07-30 | Clasificador de severidad implementado. | Commit local `5096840`; pruebas de contratos y severidad aprobadas. |
| 2026-07-30 | Agente documental y documento maestro creados. | `.claude/agents/documentacion.md` y este archivo. |
| 2026-07-30 | Verificación completa de Fase 2 (backend) contra el trabajo ya implementado: tools MCP, severidad, 4 agentes, pipeline, API (8 endpoints), schema Supabase/RLS, RAG. Se corrigió un gap real (sparkline redactado por el modelo en vez de calculado con pandas) y se completó `run.sh` (única pieza faltante). | 99 pruebas aprobadas (67 sin red + 32 contra Supabase real); ver ADR-006 y ADR-007. |
