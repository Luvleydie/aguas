import { Droplets } from "lucide-react"
import { cn } from "@/lib/utils"

export function Logo({
  className,
  size = "md",
  variant = "dark",
}: {
  className?: string
  size?: "sm" | "md" | "lg"
  variant?: "dark" | "light"
}) {
  const iconSize = size === "lg" ? 40 : size === "md" ? 28 : 22
  const textSize = size === "lg" ? "text-4xl" : size === "md" ? "text-2xl" : "text-xl"
  const box = size === "lg" ? "h-16 w-16" : size === "md" ? "h-11 w-11" : "h-9 w-9"

  return (
    <div className={cn("flex items-center gap-3", className)}>
      <span
        className={cn(
          "flex items-center justify-center rounded-2xl shrink-0",
          box,
          variant === "dark" ? "bg-primary text-primary-foreground" : "bg-white text-primary",
        )}
      >
        <Droplets size={iconSize} strokeWidth={2.4} aria-hidden />
      </span>
      <span className={cn("font-bold tracking-tight leading-none", textSize, variant === "dark" ? "text-primary" : "text-white")}>
        Hidro<span className="text-accent">Alerta</span>
      </span>
    </div>
  )
}
