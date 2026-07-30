export type Nivel = "verde" | "amarillo" | "naranja" | "rojo"

export const nivelConfig: Record<
  Nivel,
  { label: string; color: string; texto: string; descripcion: string }
> = {
  verde: {
    label: "Normal",
    color: "var(--nivel-verde)",
    texto: "#1f2a28",
    descripcion: "Niveles adecuados. Sin restricciones.",
  },
  amarillo: {
    label: "Precaución",
    color: "var(--nivel-amarillo)",
    texto: "#1f2a28",
    descripcion: "Vigilancia. Uso responsable del agua.",
  },
  naranja: {
    label: "Alerta",
    color: "var(--nivel-naranja)",
    texto: "#ffffff",
    descripcion: "Sequía moderada. Restricciones parciales.",
  },
  rojo: {
    label: "Emergencia",
    color: "var(--nivel-rojo)",
    texto: "#ffffff",
    descripcion: "Sequía severa. Restricciones estrictas.",
  },
}

export type Rol = "gobierno" | "ayuntamiento" | "medios" | "agricultor"

export const roles: { id: Rol; nombre: string; descripcion: string }[] = [
  { id: "gobierno", nombre: "Gobierno del Estado", descripcion: "Genera y publica boletines" },
  { id: "ayuntamiento", nombre: "Ayuntamiento", descripcion: "Consulta y actúa localmente" },
  { id: "medios", nombre: "Medios de comunicación", descripcion: "Difunde boletines narrativos" },
  { id: "agricultor", nombre: "Agricultor", descripcion: "Recomendaciones de siembra" },
]

export interface Presa {
  id: string
  nombre: string
  municipio: string
  capacidadPct: number
  nivel: Nivel
  historial: { semana: string; nivel: number }[]
}

function serie(base: number, drop: number): { semana: string; nivel: number }[] {
  return Array.from({ length: 12 }, (_, i) => ({
    semana: `S${i + 41}`,
    nivel: Math.max(6, Math.round(base - drop * i + (i % 2 === 0 ? 2 : -1))),
  }))
}

export const presas: Presa[] = [
  {
    id: "guadalupe-victoria",
    nombre: "Guadalupe Victoria",
    municipio: "Pánuco de Coronado",
    capacidadPct: 34,
    nivel: "naranja",
    historial: serie(58, 2.1),
  },
  {
    id: "santiago-bayacora",
    nombre: "Santiago Bayacora",
    municipio: "Durango",
    capacidadPct: 21,
    nivel: "rojo",
    historial: serie(48, 2.6),
  },
  {
    id: "el-tunal",
    nombre: "Presa El Tunal",
    municipio: "Durango",
    capacidadPct: 52,
    nivel: "amarillo",
    historial: serie(70, 1.6),
  },
  {
    id: "caboraca",
    nombre: "Peña del Águila",
    municipio: "Durango",
    capacidadPct: 63,
    nivel: "verde",
    historial: serie(78, 1.2),
  },
]

export interface Boletin {
  id: string
  semana: number
  fecha: string
  nivel: Nivel
  resumen: string
  publicado: boolean
  secciones: {
    presas: string
    precipitacion: string
    temperatura: string
    alerta: string
  }
  narrativo: string
  datosCrudos: { indicador: string; valor: string }[]
}

export const boletines: Boletin[] = [
  {
    id: "bol-52",
    semana: 52,
    fecha: "22 – 28 dic 2025",
    nivel: "naranja",
    publicado: false,
    resumen:
      "El almacenamiento estatal cae al 42%. La presa Santiago Bayacora entra en nivel crítico. Se recomienda restricción parcial del riego.",
    secciones: {
      presas:
        "El almacenamiento promedio de las presas de Durango se ubica en **42%**, una caída de 3 puntos respecto a la semana anterior. Santiago Bayacora es la más afectada con **21%** de su capacidad.",
      precipitacion:
        "La precipitación acumulada de la semana fue de **1.2 mm**, muy por debajo del promedio histórico de 8 mm para estas fechas. El déficit acumulado del año asciende al **34%**.",
      temperatura:
        "La temperatura media semanal fue de **17.4 °C**, con máximas de hasta 26 °C. La evaporación en embalses se mantiene elevada para la temporada.",
      alerta:
        "**Nivel Alerta (naranja).** Se recomienda restricción parcial del riego agrícola, priorizar el consumo humano y reforzar campañas de ahorro de agua en zonas urbanas.",
    },
    narrativo:
      "Durango enfrenta una semana de presión hídrica creciente. Con las presas al 42% de su capacidad y una precipitación casi nula, las autoridades activan el nivel de alerta naranja. La presa Santiago Bayacora, al 21%, encabeza la preocupación de las comunidades cercanas. Se pide a la ciudadanía y al campo un uso responsable del agua mientras se monitorea la evolución del temporal.",
    datosCrudos: [
      { indicador: "Almacenamiento estatal", valor: "42 %" },
      { indicador: "Precipitación semanal", valor: "1.2 mm" },
      { indicador: "Déficit anual", valor: "34 %" },
      { indicador: "Temperatura media", valor: "17.4 °C" },
      { indicador: "Presa más baja", valor: "Santiago Bayacora 21 %" },
    ],
  },
  {
    id: "bol-51",
    semana: 51,
    fecha: "15 – 21 dic 2025",
    nivel: "amarillo",
    publicado: true,
    resumen:
      "Almacenamiento estatal en 45%. Precipitación por debajo de la media. Vigilancia y uso responsable del agua.",
    secciones: {
      presas:
        "El almacenamiento promedio se ubica en **45%**. Las presas del norte muestran estabilidad, mientras las del sur continúan descendiendo lentamente.",
      precipitacion:
        "Precipitación semanal de **3.4 mm**, aún por debajo del promedio histórico. El suelo mantiene humedad moderada en zonas de riego.",
      temperatura:
        "Temperatura media de **16.1 °C**. Descenso nocturno favorable para reducir la evaporación en embalses.",
      alerta:
        "**Nivel Precaución (amarillo).** Se recomienda vigilancia y uso responsable del agua. Sin restricciones obligatorias por el momento.",
    },
    narrativo:
      "La semana cierra con las presas de Durango al 45% de su capacidad. Aunque la lluvia sigue siendo escasa, el descenso de las temperaturas nocturnas ayuda a contener la evaporación. Las autoridades mantienen el nivel amarillo y llaman a un consumo responsable.",
    datosCrudos: [
      { indicador: "Almacenamiento estatal", valor: "45 %" },
      { indicador: "Precipitación semanal", valor: "3.4 mm" },
      { indicador: "Déficit anual", valor: "31 %" },
      { indicador: "Temperatura media", valor: "16.1 °C" },
      { indicador: "Presa más baja", valor: "Santiago Bayacora 24 %" },
    ],
  },
]

export const boletinActual = boletines[0]

export interface PasoAgente {
  id: string
  agente: "Explorador" | "Estadista" | "Narrador" | "Agrónomo"
  descripcion: string
  detalle: string
  hora: string
}

export const pasosAgentes: PasoAgente[] = [
  {
    id: "explorador",
    agente: "Explorador",
    descripcion: "Recopiló datos de CONAGUA y estaciones locales",
    detalle:
      "Se consultaron 4 presas y 6 estaciones meteorológicas. Se obtuvieron niveles de almacenamiento, precipitación y temperatura de la semana 52.",
    hora: "08:02",
  },
  {
    id: "estadista",
    agente: "Estadista",
    descripcion: "Analizó tendencias y calculó el nivel de alerta",
    detalle:
      "Comparó los datos con promedios históricos. Determinó un déficit del 34% y asignó nivel de alerta naranja al estado.",
    hora: "08:05",
  },
  {
    id: "narrador",
    agente: "Narrador",
    descripcion: "Redactó el boletín en lenguaje claro",
    detalle:
      "Generó las 4 secciones del boletín y una versión narrativa para medios de comunicación.",
    hora: "08:07",
  },
  {
    id: "agronomo",
    agente: "Agrónomo",
    descripcion: "Emitió recomendaciones agrícolas",
    detalle:
      "Recomendó posponer la siembra de maíz y priorizar cultivos de bajo consumo hídrico como el frijol y el sorgo.",
    hora: "08:09",
  },
]

export interface Usuario {
  id: string
  nombre: string
  rol: string
  whatsapp: boolean
}

export const usuarios: Usuario[] = [
  { id: "u1", nombre: "María Elena Ríos", rol: "Gobierno del Estado", whatsapp: true },
  { id: "u2", nombre: "Jorge Alanís", rol: "Ayuntamiento de Durango", whatsapp: true },
  { id: "u3", nombre: "Prensa Estatal", rol: "Medios", whatsapp: false },
  { id: "u4", nombre: "Coop. Agrícola El Tunal", rol: "Agricultor", whatsapp: true },
  { id: "u5", nombre: "Comité de Cuenca Norte", rol: "Ayuntamiento de Pánuco", whatsapp: false },
]


export const sequiasHistoricas = [
  { anio: "2011", nivel: 28, etiqueta: "Sequía severa 2011" },
  { anio: "2020", nivel: 35, etiqueta: "Sequía 2020" },
  { anio: "2023", nivel: 31, etiqueta: "Sequía 2023" },
]

export const historialSemanas: Nivel[] = ["amarillo", "amarillo", "naranja", "naranja"]
