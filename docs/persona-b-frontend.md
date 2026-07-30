# Brief — Persona B: Frontend (Next.js)

> **Checkpoint de Fase 1 aprobado (2026-07-30, ver `CLAUDE.md`).** Ya puedes
> implementar siguiendo TDD estricto — arranca armando el plan de la fase
> (ver "Comando para arrancar" abajo) y preséntalo antes de escribir código,
> pero el gate de arquitectura ya no bloquea.

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

## Plan detallado de Fase 3 (orden real de ejecución)

Este es el plan que `master` debería presentarte al arrancar — te lo doy ya
armado para que lo revises antes de que nadie escriba código.

0. **⚠️ Infraestructura de testing primero.** `frontend/` hoy no tiene
   ningún test ni Vitest instalado (`package.json` solo tiene
   `dev`/`build`/`start`/`lint`) — antes del punto 1, instala Vitest +
   React Testing Library y agrega el script `test`. Sin esto
   `expert-testing` no tiene con qué escribir el rojo.
1. **Componente compartido de gráfica** (variantes completa/simple/con
   anotaciones) — constrúyelo primero porque el punto 3 y 4 lo reutilizan;
   evita que cada pantalla termine con su propia versión.
2. **Login + redirección por rol** — ya existe `login.tsx`; el trabajo aquí
   es el test de "redirige a Gobierno si rol=gobierno", etc., y conectar el
   mock de sesión (real cuando Persona A tenga el endpoint de auth).
3. **Gobierno** (la más grande, 6 pantallas) — en este orden porque
   "Generar boletín" es la única que dispara el pipeline en vivo, las demás
   son de lectura: Inicio → Boletín detalle (mockea con
   `tests/fixtures/boletin.json`) → Generar boletín (selector semana +
   progreso en vivo, mock del pipeline) → Tendencias → Auditoría/Logs →
   Usuarios (toggle WhatsApp deshabilitado).
4. **Agricultor** — antes que Ayuntamiento/Medios porque introduce la
   pantalla nueva "Siembra recomendada" (mockea con
   `tests/fixtures/recomendacion_agricola.json`), que vale la pena validar
   temprano por ser la que menos se parece a lo ya construido.
5. **Ayuntamiento** — Inicio (semáforo + "marcar acción") → Boletín
   (solo lectura, reutiliza lo del punto 3) → Tendencias.
6. **Medios** — Inicio (publicados) → Boletín narrativo + descargas
   PNG/PDF/md → Comparativa histórica.
7. **Reconectar mocks → API real**, endpoint por endpoint, conforme
   Persona A te avise que cada uno quedó verde (no esperes a que estén
   todos).

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

Todo tu trabajo va en la rama `persona-b-frontend` (ya existe en `origin`)
— **nunca commitees ni hagas push directo a `main`**. El merge a `main` pasa
por PR en Fase 4, revisado antes de mergear (ver `## Merge a main` abajo).

Desde una terminal en la raíz del repo (`hidroalerta-limpio/`):

```powershell
git checkout persona-b-frontend
git pull origin persona-b-frontend
claude
```

Como primer mensaje:

```
Actúa como el subagente master (.claude/agents/master.md). Soy Persona B —
frontend, trabajando en la rama persona-b-frontend (nunca en main). Lee
docs/persona-b-frontend.md y arquitectura-hidroalerta.md §8. Antes de
escribir o ejecutar nada, arma un plan detallado de la Fase 3 (las 4
pantallas por rol sobre frontend/, Next.js, NO Vite, usando las fixtures de
tests/fixtures/ como datos mock mientras el backend no esté listo) con el
orden de subagentes por componente
(expert-testing → expert-frontend-web → expert-seguridad → validaciones →
expert-git → expert-docs) y muéstramelo para que lo apruebe antes de
implementar. No toques backend/. Cada commit va a persona-b-frontend, nunca
a main. Antes de cada commit, expert-git debe correr su escaneo de
secretos.
```

## Merge a main

Al cerrar Fase 3 (checklist de `validaciones` en verde), `expert-git` abre
un Pull Request `persona-b-frontend → main` en GitHub — no hace merge
directo. El usuario revisa y aprueba el PR antes de mergear. Si `main`
avanzó mientras tanto (Persona A ya mergeó su backend), rebasa o mergea
`main` dentro de tu rama primero y vuelve a correr la suite completa antes
de abrir el PR.
