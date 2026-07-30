# HidroAlerta — Flujo de pantallas y estrategia (para exponer al instructor)

## 1. El problema en una frase

Durango sufre sequía recurrente. Los datos existen (CONAGUA, SMN, INEGI) pero están fragmentados en CSVs distintos, y cruzarlos manualmente toma días — por eso la reacción ante sequías severas (2011, 2020, 2023) siempre llega tarde.

## 2. La solución en una frase

Un pipeline de 4 agentes que ejecuta pandas real (no simula cálculos), clasifica severidad con umbrales fijos, y entrega un boletín semanal accionable a 4 audiencias distintas — cada una con su propia interfaz, no un solo reporte genérico.

## 3. Por qué 4 agentes y no 1 solo prompt

| Agente | Por qué existe por separado |
|---|---|
| Explorador | Decide QUÉ preguntar antes de calcular — sin esto, el Estadista no sabe qué analizar y se dispersa. |
| Estadista | Es el único que toca datos — ejecuta tools MCP de pandas real, nunca "adivina" un número. Separarlo garantiza trazabilidad y verificación. |
| Narrador | Redacta para gobierno/ayuntamiento/medios. Separado del Estadista para que la redacción no contamine ni invente cifras. |
| Agrónomo | Traduce los mismos hallazgos a decisión de siembra para agricultores — audiencia y objetivo completamente distintos al Narrador, por eso es un agente aparte y no una variación de tono. |

**Contrato entre agentes**: JSON fijo (`plan_analisis` → `hallazgos` → `boletin` / `recomendacion_agricola`), validado con schema — así cada agente se puede probar de forma aislada (TDD).

## 4. Estrategia general (qué resuelve cada pieza del curso)

| Pieza del curso | Dónde vive en HidroAlerta |
|---|---|
| Prompts | System prompts de los 4 agentes, cada uno con una única responsabilidad |
| Orquestación multiagente | Pipeline secuencial/paralelo Explorador→Estadista→{Narrador, Agrónomo} |
| Tools ejecutables (MCP) | 5 tools de pandas real sobre los 3 CSVs |
| RAG | Embeddings de 12 boletines históricos sintéticos, para contextualizar al Narrador (tier Pro) |
| Frontend demo | Web (React) para jueces + móvil (Expo) + WhatsApp, todo contra la misma API |

## 5. Flujo de pantallas por rol

### 🏛️ Gobierno (flujo lineal: generar → revisar → publicar)

```
Login
  │
  ▼
Inicio ──────────────► Generar boletín
(resumen +                 │ selecciona semana
 accesos rápidos)          │ clic "Generar"
                           ▼
                    [Progreso en vivo:
                     Explorador → Estadista
                     → Narrador → Agrónomo]
                           │
                           ▼
                    Boletín detalle
                    (markdown + semáforo +
                     panel JSON crudo)
                           │
                           ▼
                    Publicar ──┬──► visible en Ayuntamiento/Medios/Agricultor
                                ├──► push a Ayuntamiento/Medios (si alerta ≥ amarillo)
                                └──► WhatsApp a agricultores con opt-in
                           │
                           ▼
                    (accesos secundarios en cualquier momento:
                     Tendencias · Auditoría/Logs · Usuarios)
```

**Punto clave para el instructor**: gobierno es el único rol con capacidad de generar/publicar — los demás son consumidores. Esto demuestra control de acceso real (RLS), no solo una UI distinta.

### 🏛️ Ayuntamiento (flujo de consulta + acción)

```
Login → Inicio (semáforo + recomendación)
              │
              ├─► Boletín (solo lectura)
              ├─► Tendencias (histórico simple)
              └─► "Marcar acción tomada" (racionamiento/campaña de ahorro)
                        → queda registrado en acciones_ayuntamiento
```

### 📰 Medios (flujo de consumo + exportación)

```
Login → Inicio (lista de boletines publicados)
              │
              ▼
        Boletín narrativo ──► Descargar (PDF / PNG / Markdown)
              │
              ▼
        Comparativa histórica (sequías 2011/2020/2023 anotadas)
```

### 🌾 Agricultor (flujo simplificado, doble canal)

```
Login (o acceso simplificado)
      │
      ├─► Inicio: semáforo grande + frase + 🔊 escuchar
      ├─► Siembra recomendada: cultivo + acción + ventana de siembra
      └─► Historial: últimas 4 semanas (solo semáforos)

Canal paralelo (opt-in, independiente de la app):
      WhatsApp ──► recibe mensaje corto automático cuando se publica el boletín
      (el usuario activa/desactiva esto en su perfil, no es forzado)
```

## 6. Decisiones de diseño que vale la pena explicar (y por qué)

1. **Severidad = tabla de umbrales fija, no criterio del LLM.** El modelo interpreta números, no decide qué es "grave" — esto hace el sistema auditable y reproducible.
2. **4 secciones fijas del boletín** (Estado de presas, Precipitación, Temperatura, Alerta y recomendación) — sin esto no hay comparabilidad semana a semana.
3. **Separación estricta entre quien calcula (Estadista) y quien redacta (Narrador/Agrónomo)** — evita que el LLM "invente" cifras al escribir de forma fluida.
4. **RAG no es un agente nuevo, es memoria para el Narrador** — se agrega sin romper la arquitectura de 4 agentes.
5. **WhatsApp es opt-in, no forzado** — decisión de accesibilidad real: no todos los adultos mayores quieren notificaciones por ese canal, y forzarlo sería una mala práctica de UX.
6. **Un mismo backend (FastAPI) sirve web, móvil y WhatsApp** — evita duplicar lógica de negocio en 3 lugares distintos.

## 7. Cómo se demuestra en vivo (para la exposición)

1. Mostrar el selector de semana + botón "Generar" → se ve correr Explorador → Estadista → Narrador → Agrónomo en tiempo real.
2. Abrir el panel de "hallazgos crudos" → demostrar que los números vienen de pandas real, no del modelo.
3. Publicar → mostrar cómo cambia la vista de Ayuntamiento/Medios/Agricultor al instante.
4. Mostrar el mensaje simplificado que recibiría un agricultor (semáforo + frase + opción de audio) vs. el boletín técnico de gobierno — mismo dato, dos audiencias.
5. (Si da tiempo) Mostrar `agent_logs` como evidencia de trazabilidad completa del pipeline.
