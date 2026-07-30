"use client"

import { useState } from "react"
import { ArrowDownRight, ArrowUpRight } from "lucide-react"
import { TrendChart } from "@/components/hidro/trend-chart"
import { NivelBadge } from "@/components/hidro/nivel-badge"
import { presas } from "@/lib/hidro-data"
import { cn } from "@/lib/utils"

export function GobiernoTendencias() {
  const [presaId, setPresaId] = useState(presas[0].id)
  const presa = presas.find((p) => p.id === presaId) ?? presas[0]
  const primera = presa.historial[0].nivel
  const ultima = presa.historial[presa.historial.length - 1].nivel
  const delta = ultima - primera

  return (
    <div className="space-y-6">
      <div className="rounded-3xl bg-card p-6 shadow-sm sm:p-8">
        <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-xl font-bold text-foreground">Nivel de almacenamiento</h2>
            <p className="text-base text-muted-foreground">Últimas 12 semanas · % de capacidad</p>
          </div>
          <select
            value={presaId}
            onChange={(e) => setPresaId(e.target.value)}
            className="h-12 rounded-2xl border border-input bg-background px-4 text-base text-foreground outline-none focus:border-ring focus:ring-3 focus:ring-ring/40"
            aria-label="Seleccionar presa"
          >
            {presas.map((p) => (
              <option key={p.id} value={p.id}>
                {p.nombre}
              </option>
            ))}
          </select>
        </div>
        <TrendChart data={presa.historial} references={[{ y: 25, label: "Nivel crítico" }]} />
      </div>

      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {presas.map((p) => {
          const d = p.historial[p.historial.length - 1].nivel - p.historial[0].nivel
          return (
            <div key={p.id} className="rounded-3xl bg-card p-5 shadow-sm">
              <p className="text-base font-semibold text-foreground">{p.nombre}</p>
              <p className="text-sm text-muted-foreground">{p.municipio}</p>
              <p className="mt-3 text-3xl font-bold text-foreground">{p.capacidadPct}%</p>
              <div className="mt-2 flex items-center justify-between">
                <NivelBadge nivel={p.nivel} />
                <span
                  className={cn("inline-flex items-center gap-1 text-sm font-semibold")}
                  style={{ color: d < 0 ? "var(--nivel-rojo)" : "var(--nivel-verde)" }}
                >
                  {d < 0 ? <ArrowDownRight size={16} /> : <ArrowUpRight size={16} />}
                  {Math.abs(d)} pts
                </span>
              </div>
            </div>
          )
        })}
      </div>

      <p className="text-base text-muted-foreground">
        {presa.nombre} {delta < 0 ? "ha descendido" : "ha aumentado"} {Math.abs(delta)} puntos porcentuales en las últimas
        12 semanas.
      </p>
    </div>
  )
}
