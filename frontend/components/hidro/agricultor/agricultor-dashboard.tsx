"use client"

import { useEffect, useState } from "react"
import { Home, Sprout, CalendarClock, Volume2, LogOut, Sun, Loader2 } from "lucide-react"
import { Semaforo } from "@/components/hidro/semaforo"
import { historialSemanas, nivelConfig, boletinActual } from "@/lib/hidro-data"
import { accionLabel, nombreCultivo, ventanaSiembra, type RecomendacionAgricolaReal } from "@/lib/recomendacion-adapter"
import { apiFetch } from "@/lib/api-client"
import { cn } from "@/lib/utils"

const SEMANA = 52

function hablar(texto: string) {
  if (typeof window === "undefined" || !("speechSynthesis" in window)) return
  window.speechSynthesis.cancel()
  const u = new SpeechSynthesisUtterance(texto)
  u.lang = "es-MX"
  u.rate = 0.95
  window.speechSynthesis.speak(u)
}

const nav = [
  { id: "inicio", label: "Inicio", icon: Home },
  { id: "siembra", label: "Siembra", icon: Sprout },
  { id: "historial", label: "Historial", icon: CalendarClock },
]

export function AgricultorDashboard({ onLogout, token }: { onLogout: () => void; token: string }) {
  const [active, setActive] = useState("inicio")
  const [recomendacion, setRecomendacion] = useState<RecomendacionAgricolaReal | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    apiFetch<RecomendacionAgricolaReal>(`/api/siembra/${SEMANA}`, { token })
      .then(setRecomendacion)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [token])

  return (
    <div className="flex min-h-svh flex-col bg-background">
      <header className="flex items-center justify-between px-6 py-4">
        <p className="text-lg font-bold text-primary">AWAS</p>
        <button
          type="button"
          onClick={onLogout}
          className="flex items-center gap-2 rounded-xl px-3 py-2 text-base font-medium text-muted-foreground hover:bg-muted"
        >
          <LogOut size={20} aria-hidden />
          Salir
        </button>
      </header>

      <main className="flex flex-1 flex-col items-center justify-center px-4 pb-6 sm:px-6 md:max-w-lg md:mx-auto lg:max-w-xl">
        {active === "inicio" && (
          <div className="flex w-full max-w-sm flex-col items-center gap-8 text-center sm:max-w-md">
            <Semaforo nivel={boletinActual.nivel} size="xl" showScale showLabel={false} />
            {loading ? (
              <Loader2 size={28} className="animate-spin text-muted-foreground" />
            ) : recomendacion ? (
              <>
                <p className="text-3xl font-bold leading-snug text-foreground text-balance">
                  {recomendacion.mensaje_whatsapp}
                </p>
                <button
                  type="button"
                  onClick={() => hablar(recomendacion.mensaje_whatsapp)}
                  className="flex h-32 w-32 flex-col items-center justify-center gap-1 rounded-full bg-accent text-accent-foreground shadow-lg transition-transform active:scale-95"
                  aria-label="Escuchar la recomendación en voz alta"
                >
                  <Volume2 size={44} aria-hidden />
                  <span className="text-lg font-bold">Escuchar</span>
                </button>
              </>
            ) : (
              <p className="text-lg text-muted-foreground">Sin recomendación disponible.</p>
            )}
          </div>
        )}

        {active === "siembra" && (
          <div className="flex w-full max-w-sm flex-col gap-5 sm:max-w-md">
            <h2 className="text-center text-3xl font-bold text-foreground">Siembra recomendada</h2>
            {loading ? (
              <div className="flex justify-center">
                <Loader2 size={28} className="animate-spin text-muted-foreground" />
              </div>
            ) : !recomendacion ? (
              <p className="text-center text-lg text-muted-foreground">Sin recomendación disponible.</p>
            ) : (
              <>
            <div className="flex items-center gap-5 rounded-3xl bg-card p-6 shadow-sm">
              <span
                className="flex h-20 w-20 shrink-0 items-center justify-center rounded-full text-white"
                style={{ backgroundColor: "var(--nivel-naranja)" }}
              >
                <Sprout size={40} />
              </span>
              <div>
                <p className="text-2xl font-bold text-foreground">{nombreCultivo(recomendacion.cultivo_prioritario)}</p>
                <p className="text-xl font-bold uppercase" style={{ color: "var(--nivel-naranja)" }}>
                  {accionLabel(recomendacion.accion)}
                </p>
                <p className="mt-1 text-lg text-muted-foreground leading-relaxed">{recomendacion.razon}</p>
              </div>
            </div>
            <div className="flex items-center gap-4 rounded-3xl bg-card p-6 shadow-sm">
              <span className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-secondary text-primary">
                <Sun size={26} />
              </span>
              <div>
                <p className="text-base font-semibold text-muted-foreground">Ventana de siembra</p>
                <p className="text-xl font-bold text-foreground">{ventanaSiembra(recomendacion.cultivo_prioritario)}</p>
              </div>
            </div>
              </>
            )}
          </div>
        )}

        {active === "historial" && (
          <div className="flex w-full max-w-sm flex-col items-center gap-8 text-center sm:max-w-md">
            <h2 className="text-3xl font-bold text-foreground">Últimas 4 semanas</h2>
            <div className="flex flex-wrap items-end justify-center gap-5">
              {historialSemanas.map((nivel, i) => (
                <div key={i} className="flex flex-col items-center gap-2">
                  <span
                    className="h-20 w-20 rounded-full shadow-md ring-4 ring-white/60"
                    style={{ backgroundColor: nivelConfig[nivel].color }}
                    aria-label={`Semana ${49 + i}: ${nivelConfig[nivel].label}`}
                  />
                  <span className="text-lg font-semibold text-foreground">S{49 + i}</span>
                </div>
              ))}
            </div>
            <p className="text-xl leading-relaxed text-muted-foreground text-pretty">
              La alerta ha subido de precaución a alerta en el último mes. Siga cuidando el agua.
            </p>
          </div>
        )}
      </main>

      <nav className="grid grid-cols-3 gap-2 border-t border-border bg-card p-3">
        {nav.map((n) => {
          const Icon = n.icon
          const isActive = n.id === active
          return (
            <button
              key={n.id}
              type="button"
              onClick={() => setActive(n.id)}
              aria-current={isActive ? "page" : undefined}
              className={cn(
                "flex flex-col items-center gap-1 rounded-2xl py-3 text-lg font-bold transition-colors",
                isActive ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-muted",
              )}
            >
              <Icon size={30} aria-hidden />
              {n.label}
            </button>
          )
        })}
      </nav>
    </div>
  )
}
