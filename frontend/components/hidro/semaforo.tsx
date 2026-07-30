import { type Nivel, nivelConfig } from "@/lib/hidro-data"
import { cn } from "@/lib/utils"

const niveles: Nivel[] = ["verde", "amarillo", "naranja", "rojo"]

const sizeMap = {
  sm: { circle: "h-20 w-20", label: "text-base", value: "text-sm", dot: "h-3 w-3" },
  md: { circle: "h-32 w-32", label: "text-xl", value: "text-base", dot: "h-4 w-4" },
  lg: { circle: "h-44 w-44", label: "text-2xl", value: "text-lg", dot: "h-5 w-5" },
  xl: { circle: "h-64 w-64", label: "text-4xl", value: "text-2xl", dot: "h-6 w-6" },
}

export function Semaforo({
  nivel,
  size = "md",
  showLabel = true,
  showScale = true,
  className,
}: {
  nivel: Nivel
  size?: keyof typeof sizeMap
  showLabel?: boolean
  showScale?: boolean
  className?: string
}) {
  const cfg = nivelConfig[nivel]
  const s = sizeMap[size]

  return (
    <div className={cn("flex flex-col items-center gap-4", className)}>
      <div
        className={cn("flex flex-col items-center justify-center rounded-full shadow-md ring-8 ring-white/60", s.circle)}
        style={{ backgroundColor: cfg.color, color: cfg.texto }}
        role="img"
        aria-label={`Nivel de alerta: ${cfg.label}`}
      >
        <span className={cn("font-bold leading-none", s.label)}>{cfg.label}</span>
      </div>
      {showScale && (
        <div className="flex items-center gap-2" aria-hidden>
          {niveles.map((n) => (
            <span
              key={n}
              className={cn("rounded-full transition-transform", s.dot, n === nivel && "scale-150 ring-2 ring-foreground/30")}
              style={{ backgroundColor: nivelConfig[n].color, opacity: n === nivel ? 1 : 0.45 }}
            />
          ))}
        </div>
      )}
      {showLabel && <p className={cn("max-w-xs text-center text-muted-foreground leading-relaxed", s.value)}>{cfg.descripcion}</p>}
    </div>
  )
}
