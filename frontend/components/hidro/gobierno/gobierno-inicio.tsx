"use client"

import { useEffect, useState } from "react"
import { FilePlus2, FileText, TrendingUp, ArrowRight } from "lucide-react"
import { Semaforo } from "@/components/hidro/semaforo"
import { apiFetch, type BoletinReal } from "@/lib/api-client"
import { NivelBadge } from "@/components/hidro/nivel-badge"

const accesos = [
  { id: "generar", titulo: "Generar boletín", desc: "Crea el boletín de la semana", icon: FilePlus2 },
  { id: "boletin", titulo: "Ver boletín", desc: "Revisa y publica el más reciente", icon: FileText },
  { id: "tendencias", titulo: "Tendencias", desc: "Evolución del nivel de presas", icon: TrendingUp },
]

export function GobiernoInicio({ onNavigate, token }: { onNavigate: (id: string) => void; token: string }) {
  const [boletin, setBoletin] = useState<BoletinReal | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    apiFetch<BoletinReal[]>("/api/boletin/historico", { token })
      .then((lista) => { if (lista.length > 0) setBoletin(lista[0]) })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [token])

  return (
    <div className="space-y-6">
      <div className="grid gap-6 lg:grid-cols-[auto_1fr]">
        <div className="flex flex-col items-center justify-center rounded-3xl bg-card p-8 shadow-sm">
          <p className="mb-4 text-lg font-semibold text-muted-foreground">Nivel de alerta estatal</p>
          {loading ? (
            <p className="text-muted-foreground">Cargando...</p>
          ) : boletin ? (
            <Semaforo nivel={boletin.nivel} size="lg" />
          ) : (
            <p className="text-muted-foreground">Sin boletines</p>
          )}
        </div>

        <div className="flex flex-col justify-center rounded-3xl bg-card p-8 shadow-sm">
          <p className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
            Boletín más reciente {boletin ? `· Semana ${boletin.semana}` : ""}
          </p>
          {boletin && (
            <>
              <div className="mt-2">
                <NivelBadge nivel={boletin.nivel} />
              </div>
              <p className="mt-4 text-lg leading-relaxed text-foreground text-pretty line-clamp-3">
                {boletin.recomendacion}
              </p>
            </>
          )}
          <button
            type="button"
            onClick={() => onNavigate("boletin")}
            className="mt-6 inline-flex w-fit items-center gap-2 rounded-2xl bg-primary px-5 py-3 text-base font-semibold text-primary-foreground hover:bg-primary/90"
          >
            Ver boletín completo
            <ArrowRight size={20} aria-hidden />
          </button>
        </div>
      </div>

      <div className="grid gap-5 sm:grid-cols-3">
        {accesos.map((a) => {
          const Icon = a.icon
          return (
            <button
              key={a.id}
              type="button"
              onClick={() => onNavigate(a.id)}
              className="group flex flex-col items-start gap-3 rounded-3xl bg-card p-6 text-left shadow-sm transition-transform hover:-translate-y-1"
            >
              <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-secondary text-primary">
                <Icon size={24} aria-hidden />
              </span>
              <span className="text-xl font-bold text-foreground">{a.titulo}</span>
              <span className="text-base text-muted-foreground">{a.desc}</span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
