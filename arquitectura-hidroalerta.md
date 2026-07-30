# HidroAlerta — Arquitectura completa (v2)

Monitor de sequía y presas de Durango. Pipeline multiagente con tools MCP reales (pandas) que produce un boletín semanal con alerta temprana accionable, distribuido por rol (gobierno, ayuntamiento, medios, agricultores) vía web.

> 📌 **Alcance del entregable**: primero se queda **100% local** (web). Móvil (Expo) y WhatsApp quedan como **extra/post-entregable** — ver [sección 13](#13-extra-post-entregable-móvil-y-whatsapp). No bloquean ninguna fase del roadmap principal.

---

## 1. Visión general del sistema

```
                         ┌───────────────────────────────┐
                         │   3 CSVs + 1 CSV de cultivos    │
                         │   (presas, precipitación,       │
                         │   temperatura, cultivos_valle)  │
                         └───────────────┬───────────────┘
                                         ▼
              ┌─────────────────────────────────────────────┐
              │           PIPELINE DE 4 AGENTES               │
              │                                               │
              │  1. Explorador de datos                       │
              │       ▼ plan_analisis (JSON)                  │
              │  2. Estadista ──── MCP (5 tools pandas) ────┐ │
              │       ▼ hallazgos (JSON)                    │ │
              │  3. Narrador de boletín  4. Agrónomo         │ │
              │       ▼ boletin (JSON)     ▼ recomendacion   │ │
              └──────────────┬────────────────┬─────────────┘ │
                              ▼                ▼               │
                    ┌───────────────────────────────┐          │
                    │      RAG (sentence-           │◀─────────┘
                    │  transformers sobre 12 meses  │
                    │  de boletines históricos)      │
                    │  → contexto para el Narrador   │
                    └───────────────┬───────────────┘
                                     ▼
                    ┌───────────────────────────────┐
                    │         BACKEND (FastAPI)      │
                    │  - Orquesta el pipeline         │
                    │  - Expone API REST              │
                    │  - (extra) Webhook WhatsApp      │
                    └───────────────┬───────────────┘
                                     ▼
                    ┌───────────────────────────────┐
                    │      SUPABASE (DB + Auth)      │
                    │  usuarios · boletines ·         │
                    │  agent_logs · acciones_ayto ·   │
                    │  alertas_enviadas               │
                    └───────────────┬───────────────┘
                                     ▼
                    ┌───────────────────────────────┐
                    │          Web (React)           │
                    │        Vite + Tailwind         │
                    └───────────────────────────────┘

   (extra/post-entregable, no local aún: Móvil Expo · WhatsApp Business API)
```

---

## 2. Los 4 agentes (cómo se comunican)

No son servicios en red separados — son **4 llamadas secuenciales/paralelas a la API de Claude**, cada una con su propio system prompt. La salida JSON de una es la entrada de la siguiente.

```
Explorador ──▶ Estadista ──┬──▶ Narrador ──────▶ boletin.md
 (decide qué      (ejecuta   │    (redacta 4       (gobierno/
  preguntar)        tools     │     secciones,       ayuntamiento/
                    MCP)      │     usa RAG)          medios)
                              │
                              └──▶ Agrónomo ────▶ recomendacion_agricola
                                   (traduce a       (+ mensaje_whatsapp
                                    acción de         opcional)
                                    cultivo)
```

| Agente | Entrada | Salida | Toca datos? |
|---|---|---|---|
| Explorador | 3 CSVs (metadatos) | `plan_analisis` | No |
| Estadista | `plan_analisis` | `hallazgos` (con severidad, según `umbrales.json`) | Sí — vía tools MCP (firmas de `starter.py`) |
| Narrador | `hallazgos` + contexto RAG | `boletin` (markdown, **4 secciones reales**: Estado de presas, Precipitación, Temperatura, Alerta y recomendación) | No |
| Agrónomo | `hallazgos` + `cultivos_valle_guadiana.csv` | `recomendacion_agricola` (siembra + `mensaje_whatsapp` opcional, *extra*) | No |

> ⚠️ Corrección clave: el oráculo real (`boletin_referencia.md`) NO tiene "Recomendación" como sección aparte — Temperatura es su propia sección y la recomendación va dentro de "Alerta y recomendación". Todo prompt/test debe validar contra estas 4 exactas.

System prompts en `backend/agents/prompts/`.

---

## 3. Servidor MCP — 5 tools ejecutables (firmas oficiales de `starter.py`)

| Tool | Firma | Función |
|---|---|---|
| `tool_describe(csv_name)` | — | Resumen de columnas, tipos, rango de fechas |
| `tool_filter_by_date(csv_name, desde, hasta)` | — | Subconjunto por rango de fechas |
| `tool_calc_stats(csv_name, columna, agrupacion=None, desde=None, hasta=None)` | admite filtro de fecha opcional | Media, mediana, desv, min, max |
| `tool_compare_periods(csv_name, columna, periodo_a, periodo_b, agrupacion=None)` | periodos como tuplas `(desde, hasta)` | % de cambio absoluto y relativo |
| `tool_plot_ascii(serie, width=20)` | — | Sparkline ASCII |

Clave: ejecutan **pandas real** sobre `CSV_MAP = {"presas", "precipitacion", "temperatura"}`. El modelo nunca calcula — solo interpreta resultados numéricos exactos. Cualquier test debe usar estas firmas tal cual, no versiones inventadas.

---

## 4. Umbrales oficiales (`umbrales.json`)

4 métricas, cada una con rangos verde/amarillo/naranja/rojo:

| Métrica | Verde | Amarillo | Naranja | Rojo |
|---|---|---|---|---|
| `nivel_presa_pct` (%) | >60 | 40–60 | 25–40 | ≤25 |
| `precipitacion_mensual_mm` | >80 | 40–80 | 15–40 | ≤15 |
| `delta_nivel_mensual_pp` | ≥0 | -3 a 0 | -8 a -3 | <-8 |
| `temp_max_promedio_c` | <30 | 30–34 | 34–38 | >38 |

**Alerta global = severidad MÁXIMA de las 4 métricas.** Fuente única de verdad: el archivo `umbrales.json` provisto, no una tabla escrita a mano.

---

## 5. RAG (tier Pro)

- `sentence-transformers` genera embeddings de 12 boletines históricos sintéticos (una vez, al arrancar).
- Al generar hallazgos nuevos, se vectorizan y se comparan por similitud coseno contra el histórico.
- Los 2-3 más parecidos se inyectan como contexto extra al Narrador → frases como *"el nivel actual está 12% por debajo de la media 2020-2023"* y detección de cambio de régimen.
- Local, en memoria, sin API key.

---

## 6. Backend — API (FastAPI)

| Endpoint | Rol requerido | Función |
|---|---|---|
| `POST /api/auth/login` | — | Login vía Supabase Auth |
| `POST /api/boletin/generar` | gobierno | Dispara pipeline (selector de semana 1-52) |
| `GET /api/boletin/{semana}` | todos (según publicado) | Consulta boletín |
| `GET /api/boletin/historico` | todos | Lista de boletines pasados |
| `POST /api/boletin/{id}/publicar` | gobierno | Marca `publicado = true`, dispara notificaciones |
| `GET /api/logs/{semana}` | gobierno | `agent_logs` completo (auditoría) |
| `POST /api/acciones/ayuntamiento` | ayuntamiento | Registra acción tomada |
| `GET /api/siembra/{semana}` | agricultor | Recomendación de siembra del Agrónomo |

**Modo local (entregable)**: FastAPI sirve API + build de React desde el mismo proceso — un puerto, un comando (`./run.sh`).
**Modo producción (después)**: backend en Render/Railway, frontend en Vercel, unidos por `API_URL`.

> Endpoints de WhatsApp (`PATCH /api/usuarios/{id}/whatsapp`, `POST /api/whatsapp/webhook`) quedan fuera del entregable local — ver [sección 13](#13-extra-post-entregable-móvil-y-whatsapp).

---

## 7. Base de datos (Supabase)

```
usuarios ──┬──< boletines (generado_por)
           ├──< acciones_ayuntamiento (usuario_id)
           └──< alertas_enviadas (usuario_id)

boletines ──┬──< agent_logs (boletin_id)
            ├──< acciones_ayuntamiento (boletin_id)
            └──< alertas_enviadas (boletin_id)
```

| Tabla | Registra |
|---|---|
| `usuarios` | id, nombre, rol, telefono, email, municipio, **recibir_whatsapp (bool, opt-in, campo reservado para fase extra)** |
| `boletines` | markdown (4 secciones reales), recomendacion_agricola_json, hallazgos_json, nivel_alerta_global, recomendacion, publicado, generado_por |
| `agent_logs` | boletin_id, agente, mensaje (JSON), tool_llamada, tool_resultado, timestamp |
| `acciones_ayuntamiento` | boletin_id, usuario_id, accion, fecha, notas |
| `alertas_enviadas` | boletin_id, usuario_id, canal (`web` para el entregable local; `whatsapp`/`push` son *extra*), fecha_envio, estado |

RLS por rol: agricultor no ve `hallazgos_json` ni `agent_logs`. El canal `whatsapp` en `alertas_enviadas` no se usa en el entregable local — queda listo en el schema para la fase extra.

---

## 8. Pantallas por rol (actualizado)

### 🏛️ Gobierno — sidebar, 6 pantallas
1. Inicio (resumen + accesos rápidos)
2. **Generar boletín**: selector de semana (1-52, 2024) + botón "Generar boletín" que dispara Explorador → Estadista → Narrador (+ Agrónomo) en vivo
3. Boletín detalle: markdown renderizado (4 secciones reales) + semáforo 🟢🟡🟠🔴 + **panel plegable "hallazgos crudos" (JSON del estadista)** + botón publicar
4. Tendencias e histórico: gráfica real de nivel de presas en el tiempo (matplotlib/plotly o sparkline `plot_ascii`), comparativa, anotaciones RAG
5. Auditoría/Logs
6. Usuarios (rol + toggle `recibir_whatsapp`, *deshabilitado/oculto hasta la fase extra*)

### 🏛️ Ayuntamiento — tabs, 3 pantallas
1. Inicio (semáforo + botón "marcar acción tomada" — racionamiento/campaña de ahorro)
2. Boletín (solo lectura)
3. Tendencias (gráfica simple + historial de acciones)

### 📰 Medios — tabs, 3 pantallas
1. Inicio (lista de publicados)
2. Boletín narrativo + descargas PNG/PDF/md
3. Comparativa histórica (sequías 2011/2020/2023 anotadas)

### 🌾 Agricultor — tabs, **3 pantallas** (antes 2)
1. Inicio: semáforo grande + frase + botón audio
2. **Siembra recomendada** *(nueva)*: cultivo prioritario, acción (sembrar/retrasar/alternativo) desde `cultivos_valle_guadiana.csv`, ventana de siembra, comparación simple agua-disponible vs. agua-necesaria
3. Historial simple (últimas 4 semanas, solo semáforos)

**WhatsApp (opt-in vía toggle en perfil) es extra/post-entregable** — no forma parte del alcance local; ver [sección 13](#13-extra-post-entregable-móvil-y-whatsapp).

**Componente compartido**: `<GraphCard serie variante presa />` (variantes: `completa`, `simple`, `con_anotaciones_historicas`).

---

## 9. Stack tecnológico

| Capa | Tecnología |
|---|---|
| Agentes | Python + API de Claude (tool calling) |
| Backend/API | FastAPI + uvicorn |
| RAG | sentence-transformers |
| DB/Auth | Supabase (RLS por rol) |
| Web | React + Vite + Tailwind |
| Audio | Web Speech API |
| Deploy | Vercel (web) + Render/Railway (backend) |

**Extra/post-entregable** (no forma parte del stack local):

| Capa | Tecnología |
|---|---|
| Móvil | Expo / React Native (agente separado de web) |
| WhatsApp | WhatsApp Business Cloud API (opt-in) |

---

## 10. Estructura de carpetas

```
hidroalerta/
├── backend/
│   ├── main.py
│   ├── agents/
│   │   ├── orquestador.py      # 4 agentes, contratos de starter.py
│   │   └── prompts/
│   ├── mcp_tools/                # firmas exactas de starter.py
│   ├── rag/
│   ├── data/                     # 3 CSVs + cultivos_valle_guadiana.csv + umbrales.json
│   └── requirements.txt
├── frontend-web/                 # React (Vite) — expert-frontend-web
├── run.sh
└── README.md

# mobile/ — Expo, extra/post-entregable, no se crea en la fase local
```

---

## 11. Agentes de Claude Code (`.agents/`)

| Archivo | Rol |
|---|---|
| `expert_backend.MD` | Pipeline 4 agentes + tools MCP (TDD, firmas de `starter.py`) |
| `expert_frontend_web.MD` | Pantallas web por rol, GraphCard |
| `expert_frontend_mobile.MD` | App Expo, mismas pantallas + push (*extra/post-entregable, no arranca en fase local*) |
| `expert_seguridad.MD` | RLS, validación de payloads, opt-in WhatsApp (WhatsApp es *extra*) |
| `expert_bd.MD` | Schema Supabase, migraciones, RLS |
| `expert_testing.MD` | Escribe y mantiene pytest/vitest/jest — materializa el "rojo" del ciclo TDD |
| `expert_bugs.MD` | Diagnostica causa raíz de tests fallidos, corrige, retroalimenta a `master` |
| `expert_git.MD` | Commits atómicos siguiendo el ciclo TDD (red-green-refactor visible en el historial) |
| `expert_docs.MD` | Mantiene `README.md`, diagrama de arquitectura y decisiones de diseño al día |
| `validaciones.MD` | Valida contratos JSON + `boletin_referencia.md` como oráculo |
| `master.MD` | Orquesta el orden de delegación y el roadmap |

---

## 12. Roadmap de construcción

La estructura de fases adaptada a tu stack:

### Fase 1 · Setup

| # | Tarea | Agente |
|---|---|---|
| 01 | Python 3.11+, CLI de Claude Code, Node, entorno virtual. CSVs + `umbrales.json` + `cultivos_valle_guadiana.csv` en `backend/data/` | — (manual) |
| 02 | `CLAUDE.md` + estructura de carpetas (`backend/`, `frontend-web/`, `.gitignore`, `.env.example`) | `expert-docs` |
| 03 | Contratos JSON (los 4 schemas) + fixtures de prueba, tests en ROJO (esperado) | `expert-testing` |
| **Checkpoint** | Plan resumen → esperas tu OK antes de seguir | `master` |

### Fase 2 · Backend con TDD (rojo → verde)

| # | Tarea | Agente |
|---|---|---|
| 04 | Tools MCP ejecutables sobre los CSVs reales, firmas de `starter.py`, cobertura ≥90% | `expert-backend` + `expert-testing` |
| 05 | Los 4 agentes (Explorador, Estadista, Narrador, Agrónomo) — `claude_p()` vía CLI, salidas con `--json-schema` | `expert-backend` + `expert-testing` |
| 06 | Orquestador — pipeline secuencial Explorador→Estadista→{Narrador, Agrónomo} en paralelo | `expert-backend` |
| 07 | API FastAPI + JWT (validado contra Supabase Auth) + RLS + sanitización de inputs | `expert-backend` + `expert-seguridad` |
| **Checkpoint** | Tests verdes + commit por fase | `expert-git` |
| **Transversal** | `log_agentes.jsonl` — trazabilidad completa del flujo entre agentes | `expert-backend` |
| **Si falla algo** | Diagnóstico y fix | `expert-bugs` |

### Fase 3 · Plataforma (local, un solo comando)

| # | Tarea | Agente |
|---|---|---|
| 08 | Frontend React + Vite, build servido por FastAPI en el mismo puerto | `expert-frontend-web` |
| 09 | Políticas RLS en Supabase (aislamiento por rol, no por UID simple como Firestore — aquí sí necesitas reglas más finas) | `expert-bd` + `expert-seguridad` |
| **Demo local** | `./run.sh` → build + uvicorn → `localhost:8000` con las 4 vistas de rol funcionando | `master` verifica |

### Fase 4 · Entrega

| # | Tarea | Agente |
|---|---|---|
| 10 | E2E contra el oráculo `boletin_referencia.md` — coincidencia de las 4 secciones y severidad | `validaciones` |
| 11 | README con diagrama, decisiones de diseño, instrucciones, commit final | `expert-docs` + `expert-git` |
| **Entrega a jueces** | Repo + `run.sh` + `log_agentes.jsonl` + `boletin_referencia.md` como oráculo + README | — |

### Qué se agrega respecto a lo que ya tenías

- **Checkpoints explícitos** entre fases donde `master` debe esperar tu aprobación antes de seguir (nuevo — antes no lo teníamos formalizado).
- **Cobertura mínima 90%** en las tools MCP como criterio objetivo de "listo" (agregado a `expert-testing`).
- `expert-seguridad` se mueve a **fase 2**, no al final — el JWT y RLS se validan junto con la API, no después.

---

## 13. Extra (post-entregable): Móvil y WhatsApp

El entregable principal se queda **100% local y web** (Fases 1-4). Móvil y WhatsApp **no** son parte del roadmap principal ni bloquean ningún checkpoint — se abordan después, solo si hay tiempo/alcance extra.

| Qué | Detalle | Agente |
|---|---|---|
| Móvil (Expo/React Native) | Mismas 4 pantallas por rol que la web + notificaciones push | `expert-frontend-mobile` |
| WhatsApp Business Cloud API | Webhook (`POST /api/whatsapp/webhook`), toggle opt-in (`PATCH /api/usuarios/{id}/whatsapp`), envío de `mensaje_whatsapp` del Agrónomo | `expert-backend` + `expert-seguridad` |

**Ya preparado en el diseño base** (para no tener que rediseñar cuando se retome):
- Campo `recibir_whatsapp` en `usuarios` y canal `whatsapp` en `alertas_enviadas` (schema listo, sin usarse).
- `recomendacion_agricola` del Agrónomo ya contempla un `mensaje_whatsapp` opcional en su JSON.

**Antes de retomar esta fase**: correr de nuevo por `expert-testing` → `expert-bugs` como cualquier otra feature, y actualizar esta sección + el roadmap principal con `expert-docs` una vez priorizada.
