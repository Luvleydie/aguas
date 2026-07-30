import { type Nivel, nivelConfig } from "@/lib/hidro-data"
import { cn } from "@/lib/utils"

export function NivelBadge({ nivel, className }: { nivel: Nivel; className?: string }) {
  const cfg = nivelConfig[nivel]
  return (
    <span
      className={cn("inline-flex items-center gap-2 rounded-full px-3 py-1 text-sm font-semibold", className)}
      style={{ backgroundColor: cfg.color, color: cfg.texto }}
    >
      <span className="h-2.5 w-2.5 rounded-full bg-current opacity-80" aria-hidden />
      {cfg.label}
    </span>
  )
}
