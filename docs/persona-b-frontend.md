# Brief — Persona B: Frontend (Next.js)

> Preparación para la fase posterior al checkpoint de `CLAUDE.md`. **No
> implementes nada de esto hasta que el equipo apruebe explícitamente salir
> de la Fase 1 · Setup.**

## Alcance real (corregido)

La implementación de los 4 agentes (`ejecutar_*`) vive dentro del bloque de
`expert-backend` — la lleva Persona A junto con las tools MCP, ver
`docs/persona-a-backend.md`. Tu trabajo es **frontend**: las pantallas por
rol sobre el dashboard Next.js que ya existe en `frontend/`, y su conexión a
la API que construye Persona A. Puedes empezar **en paralelo**, sin esperar
al backend, mockeando las respuestas con las fixtures que ya existen
(`tests/fixtures/boletin.json`, `recomendacion_agricola.json`).

## Contexto que ya existe

- `frontend/components/hidro/`: dashboard Next.js ya construido — login +
  4 roles (`gobierno/`, `ayuntamiento/`, `medios/`, `agricultor/`), más
  `boletin-view.tsx`, `semaforo.tsx`, `trend-chart.tsx`, `nivel-badge.tsx`.
  Hoy consume datos de ejemplo en `frontend/lib/hidro-data.ts`.
- `backend/contracts.py`: `Boletin` y `RecomendacionAgricola` son la forma
  exacta que vas a recibir de la API — úsalos como tipos de referencia al
  tipar las props en TypeScript.
- Diseño de referencia: `C:\Users\Lenovo\Documents\Curso\hidro-alerta` es la
  exportación original (hoy idéntica a `frontend/`) — solo consúltala si en
  algún momento se re-exporta el diseño y hay que comparar contra el
  original; si no tienes acceso a esa ruta, ignórala.

## Alcance por fase (roadmap completo en `arquitectura-hidroalerta.md` §8, §12)

**Fase 3 · Plataforma (tu fase principal)**
1. **Gobierno** (sidebar, 6 pantallas): Inicio · Generar boletín (selector
   semana 1-52 + botón que dispara el pipeline, progreso en vivo
   Explorador→Estadista→Narrador→Agrónomo) · Boletín detalle (markdown 4
   secciones reales + semáforo + panel plegable de hallazgos crudos +
   publicar) · Tendencias · Auditoría/Logs · Usuarios (toggle
   `recibir_whatsapp` deshabilitado — es fase extra).
2. **Ayuntamiento** (tabs, 3): Inicio (semáforo + "marcar acción tomada") ·
   Boletín (solo lectura) · Tendencias.
3. **Medios** (tabs, 3): Inicio (publicados) · Boletín narrativo + descargas
   PNG/PDF/md · Comparativa histórica.
4. **Agricultor** (tabs, 3): Inicio (semáforo + frase + audio) · **Siembra
   recomendada** (cultivo prioritario, acción, ventana de siembra desde
   `RecomendacionAgricola`) · Historial simple.
5. Componente compartido de gráfica (variantes: completa/simple/con
   anotaciones históricas) — no dupliques el componente de gráfica por rol.
6. Login con redirección por rol.

**Fase 4 · Entrega (junto con Persona A)**
- `validaciones` corre el checklist E2E contra `boletin_referencia.md`.
- `expert-docs` + `expert-git` cierran README y commit final.

## Subagentes que usas (en este orden, por componente)

`expert-testing` (test de render/interacción, rojo) → `expert-frontend-web`
(implementación mínima, verde) → `expert-seguridad` (validación de payloads
del lado cliente, RLS visible por rol) → `validaciones` → `expert-git` →
`expert-docs`. Si algo falla: `expert-bugs`.

## Interfaz con Persona A

No tocas `backend/`. Persona A te avisa cuándo cada endpoint FastAPI queda
verde — hasta entonces, mockea con las fixtures de `tests/fixtures/`. No
cambies la forma de `Boletin`/`RecomendacionAgricola` sin coordinarlo con
Persona A, son el contrato compartido.

## Reglas no negociables que más te tocan

Regla 4 (el boletín se renderiza con las 4 secciones reales tal cual las
produce el Narrador, sin inventar una quinta), regla 6 (cada serie con
sparkline ASCII visible).

## Definición de hecho

- Suite de componentes (Vitest + RTL) en verde.
- Las 4 vistas por rol renderizan `Boletin`/`RecomendacionAgricola` reales
  (no solo los mocks de `hidro-data.ts`) una vez la API esté disponible.

## Fuera de alcance

`backend/agents/*.py`, tools MCP, `severity.py`, `pipeline.py`, esquema de
Supabase.

## Comando para arrancar

Desde una terminal en la raíz del repo (`hidroalerta-limpio/`):

```powershell
claude
```

Como primer mensaje:

```
Actúa como el subagente master (.claude/agents/master.md). Soy Persona B —
frontend. Lee docs/persona-b-frontend.md y arquitectura-hidroalerta.md §8.
Antes de escribir o ejecutar nada, arma un plan detallado de la Fase 3
(las 4 pantallas por rol sobre frontend/, Next.js, NO Vite, usando las
fixtures de tests/fixtures/ como datos mock mientras el backend no esté
listo) con el orden de subagentes por componente
(expert-testing → expert-frontend-web → expert-seguridad → validaciones →
expert-git → expert-docs) y muéstramelo para que lo apruebe antes de
implementar. No toques backend/. Antes de cada commit, expert-git debe
correr su escaneo de secretos.
```
