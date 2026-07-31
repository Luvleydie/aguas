"use client"

import { useEffect, useState } from "react"
import { Search, BarChart3, PenLine, Sprout, Loader2 } from "lucide-react"
import { apiFetch } from "@/lib/api-client"

interface AgentLog {
  id: string
  agente: string
  mensaje: unknown
  timestamp: string
}

const iconos: Record<string, typeof Search> = {
  explorador: Search,
  estadista: BarChart3,
  narrador: PenLine,
  agronomo: Sprout,
}

export function GobiernoAuditoria({ token }: { token: string }) {
  const [logs, setLogs] = useState<AgentLog[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    apiFetch<AgentLog[]>("/api/logs/52", { token })
      .then(setLogs)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [token])

  return (
    <div className="rounded-3xl bg-card p-6 shadow-sm sm:p-8">
      <h2 className="text-xl font-bold text-foreground">Registro de actividad — Semana 52</h2>
      <p className="mt-1 text-base text-muted-foreground">
        Cada agente registra su contribución al generar el boletín.
      </p>

      {loading ? (
        <div className="mt-6 flex items-center justify-center">
          <Loader2 size={24} className="animate-spin text-muted-foreground" />
        </div>
      ) : logs.length === 0 ? (
        <p className="mt-6 text-muted-foreground">No hay logs disponibles para esta semana.</p>
      ) : (
        <ol className="mt-6 space-y-6">
          {logs.map((paso, i) => {
            const Icon = iconos[paso.agente] ?? Search
            const isLast = i === logs.length - 1
            const msg = typeof paso.mensaje === "string" ? paso.mensaje : JSON.stringify(paso.mensaje)
            return (
              <li key={paso.id} className="relative flex gap-4">
                {!isLast && <span className="absolute left-6 top-14 h-full w-0.5 bg-border" aria-hidden />}
                <span className="z-10 flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-primary text-primary-foreground">
                  <Icon size={22} aria-hidden />
                </span>
                <div className="flex-1 rounded-2xl bg-secondary/40 p-4">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="text-lg font-bold text-foreground capitalize">{paso.agente}</p>
                    <span className="text-sm font-medium text-muted-foreground">
                      {new Date(paso.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  <p className="mt-1 text-base text-muted-foreground leading-relaxed line-clamp-3">{msg}</p>
                </div>
              </li>
            )
          })}
        </ol>
      )}
    </div>
  )
}
