import type { RecomendacionAgricolaReal } from "@/lib/recomendacion-adapter"

/**
 * Mock con la forma real del contrato del Agrónomo, espejo de
 * tests/fixtures/recomendacion_agricola.json. Reemplázalo por la respuesta
 * de la API una vez que Persona A publique el endpoint (ver Paso 8 del plan).
 */
export const recomendacionActualReal: RecomendacionAgricolaReal = {
  semana: 42,
  cultivo_prioritario: "frijol",
  accion: "retrasar_siembra",
  razon: "nivel de presa 12% bajo la media, precipitación insuficiente para la etapa crítica",
  mensaje_whatsapp: "🌾 Alerta: nivel bajo en las presas. Se recomienda posponer la siembra 2 semanas.",
  severidad: "alerta",
}
