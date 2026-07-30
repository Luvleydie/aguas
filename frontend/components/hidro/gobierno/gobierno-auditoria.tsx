import { Search, BarChart3, PenLine, Sprout } from "lucide-react"
import { pasosAgentes } from "@/lib/hidro-data"

const iconos = {
  Explorador: Search,
  Estadista: BarChart3,
  Narrador: PenLine,
  Agrónomo: Sprout,
} as const

export function GobiernoAuditoria() {
  return (
    <div className="rounded-3xl bg-card p-6 shadow-sm sm:p-8">
      <h2 className="text-xl font-bold text-foreground">Registro de actividad — Semana 52</h2>
      <p className="mt-1 text-base text-muted-foreground">
        Cada agente registra su contribución al generar el boletín.
      </p>

      <ol className="mt-6 space-y-6">
        {pasosAgentes.map((paso, i) => {
          const Icon = iconos[paso.agente]
          const isLast = i === pasosAgentes.length - 1
          return (
            <li key={paso.id} className="relative flex gap-4">
              {!isLast && <span className="absolute left-6 top-14 h-full w-0.5 bg-border" aria-hidden />}
              <span className="z-10 flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-primary text-primary-foreground">
                <Icon size={22} aria-hidden />
              </span>
              <div className="flex-1 rounded-2xl bg-secondary/40 p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="text-lg font-bold text-foreground">{paso.agente}</p>
                  <span className="text-sm font-medium text-muted-foreground">{paso.hora} h</span>
                </div>
                <p className="mt-1 text-base font-medium text-foreground">{paso.descripcion}</p>
                <p className="mt-1 text-base text-muted-foreground leading-relaxed">{paso.detalle}</p>
              </div>
            </li>
          )
        })}
      </ol>
    </div>
  )
}
