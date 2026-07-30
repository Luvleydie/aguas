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
