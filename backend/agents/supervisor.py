"""Contrato y prompt del Supervisor multiaudiencia (tier EXTREMO)."""

from __future__ import annotations

import json

from backend.claude_client import ClaudeP, claude_p
from backend.contracts import Boletin, RecomendacionAgricola, ResultadoEstadista, SupervisorMultiAudiencia


SYSTEM_PROMPT = """
Eres el Supervisor de HidroAlerta. Recibes 'hallazgos' (del Estadista), 'boletin' (del Narrador) y 'recomendacion_agricola' (del Agrónomo) y produces 3 versiones del mismo boletín, cada una optimizada para su audiencia. No inventas datos nuevos — solo adaptas tono, extensión y énfasis de lo ya calculado.

ENTRADAS:
- hallazgos: JSON con métricas y severidad ya calculadas.
- boletin: el boletín markdown generado por el Narrador (4 secciones fijas).
- recomendacion_agricola: la recomendación del Agrónomo (mensaje_whatsapp, acción, etc.).

TAREA:
Genera 3 versiones del boletín:

1. version_gobierno: formal, técnica, institucional. Reutiliza el boletín ya generado por el Narrador (4 secciones fijas: Estado de presas, Precipitación, Temperatura, Alerta y recomendación). Máximo 1 página.

2. version_medios: divulgación periodística. Lenguaje accesible, con un titular sugerido, 2-3 párrafos, cita los datos más noticiosos primero (ej. comparación histórica si hay RAG). Máximo 200 palabras.

3. version_agricultores: acción práctica. Reutiliza 'mensaje_whatsapp' del Agrónomo como base, expandido a 3-4 líneas máximo, sin tecnicismos, con la acción de siembra como primera línea.

FORMATO DE SALIDA — responde ÚNICAMENTE este JSON, sin texto adicional:
{
  "tipo": "supervisor_multiaudiencia",
  "contenido": {
    "version_gobierno": {"texto": "...", "formato": "markdown"},
    "version_medios": {"titular": "...", "texto": "...", "formato": "texto"},
    "version_agricultores": {"texto": "...", "formato": "texto_corto"}
  }
}

REGLAS:
- Nunca inventes datos numéricos nuevos — todo número debe existir en los hallazgos o el boletín original.
- La versión de gobierno debe conservar las 4 secciones fijas del boletín del Narrador.
- La versión de medios debe incluir un titular llamativo y datos clave en los primeros 2 párrafos.
- La versión de agricultores debe empezar con la acción de siembra y no debe superar 4 líneas.
- Si hay contexto histórico (RAG), menciona comparaciones en la versión de medios.
""".strip()


def ejecutar_supervisor(
    hallazgos: ResultadoEstadista,
    recomendacion: RecomendacionAgricola,
    boletin: Boletin,
    claude_fn: ClaudeP = claude_p,
) -> SupervisorMultiAudiencia:
    prompt = json.dumps(
        {
            "hallazgos": hallazgos.model_dump(mode="json"),
            "boletin": {"markdown": boletin.markdown, "recomendacion": boletin.recomendacion},
            "recomendacion_agricola": recomendacion.model_dump(mode="json"),
        },
        ensure_ascii=False,
    )
    bruto = claude_fn(
        prompt,
        system=SYSTEM_PROMPT,
        schema=SupervisorMultiAudiencia.model_json_schema(),
    )
    return SupervisorMultiAudiencia.model_validate(bruto)
