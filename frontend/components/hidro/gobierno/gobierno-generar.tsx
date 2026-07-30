"use client"

import { useEffect, useState } from "react"
import { Search, BarChart3, PenLine, Sprout, Check, Loader2, Sparkles } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

const pasos = [
  { id: "explorador", nombre: "Explorador", desc: "Recopila datos de presas y clima", icon: Search },
  { id: "estadista", nombre: "Estadista", desc: "Analiza tendencias y calcula el nivel", icon: BarChart3 },
  { id: "narrador", nombre: "Narrador", desc: "Redacta el boletín en lenguaje claro", icon: PenLine },
  { id: "agronomo", nombre: "Agrónomo", desc: "Emite recomendaciones agrícolas", icon: Sprout },
]

export function GobiernoGenerar({ onDone }: { onDone: () => void }) {
  const [semana, setSemana] = useState(52)
  const [running, setRunning] = useState(false)
  const [step, setStep] = useState(-1)
  const [finished, setFinished] = useState(false)

  useEffect(() => {
    if (!running) return
    if (step >= pasos.length) {
      setFinished(true)
      setRunning(false)
      return
    }
    const t = setTimeout(() => setStep((s) => s + 1), 1100)
    return () => clearTimeout(t)
  }, [running, step])

  function start() {
    setFinished(false)
    setStep(0)
    setRunning(true)
  }

  return (
    <div className="space-y-6">
      <div className="rounded-3xl bg-card p-6 shadow-sm sm:p-8">
        <label htmlFor="semana" className="text-lg font-semibold text-foreground">
          Semana del boletín
        </label>
        <div className="mt-3 flex flex-col gap-4 sm:flex-row sm:items-center">
          <select
            id="semana"
            value={semana}
            onChange={(e) => setSemana(Number(e.target.value))}
            disabled={running}
            className="h-14 w-full rounded-2xl border border-input bg-background px-4 text-lg text-foreground outline-none focus:border-ring focus:ring-3 focus:ring-ring/40 sm:max-w-xs disabled:opacity-60"
          >
            {Array.from({ length: 52 }, (_, i) => 52 - i).map((n) => (
              <option key={n} value={n}>
                Semana {n}
              </option>
            ))}
          </select>
          <Button
            onClick={start}
            disabled={running}
            className="h-14 gap-2 px-8 text-lg font-semibold sm:w-auto"
          >
            {running ? <Loader2 size={22} className="animate-spin" /> : <Sparkles size={22} />}
            {running ? "Generando..." : "Generar boletín"}
          </Button>
        </div>
      </div>

      <div className="rounded-3xl bg-card p-6 shadow-sm sm:p-8">
        <h2 className="mb-5 text-xl font-bold text-foreground">Progreso de generación</h2>
        <ol className="space-y-4">
          {pasos.map((p, i) => {
            const Icon = p.icon
            const done = step > i
            const activeStep = running && step === i
            return (
              <li
                key={p.id}
                className={cn(
                  "flex items-center gap-4 rounded-2xl border p-4 transition-colors",
                  done
                    ? "border-transparent bg-secondary/50"
                    : activeStep
                      ? "border-accent bg-accent/5"
                      : "border-border bg-background",
                )}
              >
                <span
                  className={cn(
                    "flex h-12 w-12 items-center justify-center rounded-2xl",
                    done ? "text-white" : activeStep ? "bg-accent text-white" : "bg-muted text-muted-foreground",
                  )}
                  style={done ? { backgroundColor: "var(--nivel-verde)" } : undefined}
                >
                  {done ? <Check size={24} /> : activeStep ? <Loader2 size={22} className="animate-spin" /> : <Icon size={22} />}
                </span>
                <div className="flex-1">
                  <p className="text-lg font-bold text-foreground">{p.nombre}</p>
                  <p className="text-base text-muted-foreground">{p.desc}</p>
                </div>
                {done && <span className="text-base font-semibold" style={{ color: "var(--nivel-verde)" }}>Listo</span>}
              </li>
            )
          })}
        </ol>

        {finished && (
          <div className="mt-6 flex flex-col items-start gap-3 rounded-2xl bg-secondary/50 p-5 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-lg font-semibold text-foreground">
              Boletín de la semana {semana} generado correctamente.
            </p>
            <Button onClick={onDone} className="h-12 px-6 text-base font-semibold">
              Ver boletín
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}
