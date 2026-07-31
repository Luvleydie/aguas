import type { Nivel } from "@/lib/hidro-data"

export type Severidad = "info" | "warn" | "alerta" | "critico"

/** Subconjunto de Hallazgo (backend/contracts.py) que consume la UI. */
export interface Hallazgo {
  id: string
  metrica: string
  valor: number
  unidad: string
  severidad: Severidad
  contexto: string
  sparkline: string
}

/**
 * Forma real de una fila de la tabla `boletines` (ver
 * backend/db/migrations/0001_init_schema.sql): el contrato Boletin del
 * Narrador (nivel_alerta_global -> nivel, markdown) más los campos que
 * agrega la fila de Supabase. No existe una columna `fecha` — la fecha se
 * deriva de `semana`+`anio` en la UI. `hallazgos` solo llega para el rol
 * gobierno (tabla `boletines` completa); el resto de roles lee la vista
 * `boletines_publico`, que no expone hallazgos_json/recomendacion_agricola_json.
 */
export interface BoletinReal {
  id: string
  semana: number
  anio: number
  publicado: boolean
  createdAt: string
  publishedAt: string | null
  nivel: Nivel
  markdown: string
  recomendacion: string
  hallazgos?: Hallazgo[]
  evaluacion_calidad_json?: {
    [key: string]: {
      audiencia: string
      scores: Record<string, number>
      promedio: number
      justificacion_breve: string
    }
  }
}

export interface SeccionesBoletin {
  presas: string
  precipitacion: string
  temperatura: string
  alerta: string
}

const TITULOS: { key: keyof SeccionesBoletin; titulo: string }[] = [
  { key: "presas", titulo: "Estado de presas" },
  { key: "precipitacion", titulo: "Precipitación" },
  { key: "temperatura", titulo: "Temperatura" },
  { key: "alerta", titulo: "Alerta y recomendación" },
]

/**
 * El Narrador entrega las 4 secciones fijas embebidas en un único markdown
 * (ver backend/contracts.py: Boletin.markdown). Este parser las separa para
 * las vistas del frontend, replicando el criterio de match del validador
 * Pydantic `exigir_secciones_fijas` (línea que empieza con "##", numeración
 * opcional, sin distinguir mayúsculas/minúsculas).
 */
export function parseSeccionesBoletin(markdown: string): SeccionesBoletin {
  const lineas = markdown.split("\n")
  const encabezados: { key: keyof SeccionesBoletin; inicio: number }[] = []

  lineas.forEach((linea, i) => {
    if (!/^##(?!#)/.test(linea)) return
    const match = TITULOS.find((t) => linea.toLowerCase().includes(t.titulo.toLowerCase()))
    if (match) encabezados.push({ key: match.key, inicio: i + 1 })
  })

  const faltantes = TITULOS.filter((t) => !encabezados.some((e) => e.key === t.key))
  if (faltantes.length > 0) {
    throw new Error(`faltan secciones fijas: ${faltantes.map((f) => f.titulo).join(", ")}`)
  }

  const secciones = {} as SeccionesBoletin
  encabezados.forEach((enc, i) => {
    const fin = i + 1 < encabezados.length ? encabezados[i + 1].inicio - 1 : lineas.length
    secciones[enc.key] = lineas.slice(enc.inicio, fin).join("\n").trim()
  })

  return secciones
}
