export type Cultivo = "maiz" | "frijol" | "alfalfa"
export type AccionAgricola =
  | "sembrar_normal"
  | "retrasar_siembra"
  | "reducir_riego"
  | "cultivo_alternativo"
  | "sin_accion_urgente"
export type Severidad = "info" | "warn" | "alerta" | "critico"

export interface RecomendacionAgricolaReal {
  semana: number
  cultivo_prioritario: Cultivo
  accion: AccionAgricola
  razon: string
  mensaje_whatsapp: string
  severidad: Severidad
}

const MESES = [
  "Enero",
  "Febrero",
  "Marzo",
  "Abril",
  "Mayo",
  "Junio",
  "Julio",
  "Agosto",
  "Septiembre",
  "Octubre",
  "Noviembre",
  "Diciembre",
]

/** Espejo de assets/cultivos_valle_guadiana.csv (tabla de referencia, solo lectura). */
const CALENDARIO_CULTIVOS: Record<Cultivo, { nombre: string; mesInicioSiembra: number; mesFinSiembra: number }> = {
  maiz: { nombre: "Maíz", mesInicioSiembra: 4, mesFinSiembra: 6 },
  frijol: { nombre: "Frijol", mesInicioSiembra: 6, mesFinSiembra: 8 },
  alfalfa: { nombre: "Alfalfa", mesInicioSiembra: 9, mesFinSiembra: 11 },
}

export function nombreCultivo(cultivo: Cultivo): string {
  return CALENDARIO_CULTIVOS[cultivo].nombre
}

export function ventanaSiembra(cultivo: Cultivo): string {
  const { mesInicioSiembra, mesFinSiembra } = CALENDARIO_CULTIVOS[cultivo]
  return `${MESES[mesInicioSiembra - 1]} – ${MESES[mesFinSiembra - 1]}`
}

const ACCION_LABELS: Record<AccionAgricola, string> = {
  sembrar_normal: "Sembrar",
  retrasar_siembra: "Retrasar siembra",
  reducir_riego: "Reducir riego",
  cultivo_alternativo: "Cultivo alternativo",
  sin_accion_urgente: "Sin acción urgente",
}

export function accionLabel(accion: AccionAgricola): string {
  return ACCION_LABELS[accion]
}
