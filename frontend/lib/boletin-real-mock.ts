import type { BoletinReal } from "@/lib/boletin-adapter"

/**
 * Mock con la forma real del contrato (Narrador + hallazgos del Estadista),
 * espejo de tests/fixtures/boletin.json y tests/fixtures/hallazgos.json.
 * Reemplaza este mock por la respuesta de `GET /api/boletin/{semana}` una
 * vez que Persona A publique el endpoint (ver Paso 8 del plan).
 */
export const boletinActualReal: BoletinReal = {
  id: "bol-mock-42",
  semana: 42,
  anio: 2024,
  publicado: false,
  createdAt: "2024-10-20T08:00:00Z",
  publishedAt: null,
  nivel: "amarillo",
  markdown:
    "# Boletín HidroAlerta · Semana 42\n\n## 1 · Estado de presas\n\nPromedio ponderado: **50.8 %**. Tendencia: `▃▃▂▂▂▁▁`.\n\n## 2 · Precipitación\n\nAcumulado medio mensual: **53.7 mm**. Tendencia: `▁▂▅█▆▃▂`.\n\n## 3 · Temperatura\n\nTemperatura máxima promedio: **26.3 °C** (`▅▆▃▂▂▁▃`).\n\n## 4 · Alerta y recomendación\n\nNivel global **AMARILLO**. Recomendación: activar vigilancia y campaña preventiva de ahorro.",
  recomendacion: "Activar vigilancia y campaña preventiva de ahorro.",
  hallazgos: [
    {
      id: "h_nivel",
      metrica: "nivel_presa_pct",
      valor: 50.8,
      unidad: "%",
      severidad: "warn",
      contexto: "El promedio ponderado se encuentra entre 40 y 60 por ciento.",
      sparkline: "▃▃▂▂▂▁▁",
    },
    {
      id: "h_delta",
      metrica: "delta_nivel_mensual_pp",
      valor: -2.4,
      unidad: "pp",
      severidad: "warn",
      contexto: "El nivel descendió frente al mes anterior.",
      sparkline: "▅▄▃▂▂▁▁",
    },
    {
      id: "h_precipitacion",
      metrica: "precipitacion_mensual_mm",
      valor: 53.7,
      unidad: "mm",
      severidad: "warn",
      contexto: "La media estatal se encuentra entre 40 y 80 milímetros.",
      sparkline: "▁▂▅█▆▃▂",
    },
    {
      id: "h_temperatura",
      metrica: "temp_max_promedio_c",
      valor: 26.3,
      unidad: "°C",
      severidad: "info",
      contexto: "La temperatura máxima promedio permanece debajo de 30 grados.",
      sparkline: "▅▆▃▂▂▁▃",
    },
  ],
}
