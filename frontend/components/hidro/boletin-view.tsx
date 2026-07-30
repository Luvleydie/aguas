"use client"

import { useState } from "react"
import { ChevronDown, Droplet, CloudRain, Thermometer, TriangleAlert, CheckCircle2, Send } from "lucide-react"
import type { Boletin } from "@/lib/hidro-data"
import { Semaforo } from "@/components/hidro/semaforo"
import { NivelBadge } from "@/components/hidro/nivel-badge"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

/** Renders **bold** segments from a simple markdown string. */
function RichText({ text, className }: { text: string; className?: string }) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g)
  return (
    <p className={cn("text-lg leading-relaxed text-foreground", className)}>
      {parts.map((p, i) =>
        p.startsWith("**") && p.endsWith("**") ? (
          <strong key={i} className="font-bold text-primary">
            {p.slice(2, -2)}
          </strong>
        ) : (
          <span key={i}>{p}</span>
        ),
      )}
    </p>
  )
}

const secciones = [
  { key: "presas", titulo: "Estado de presas", icon: Droplet },
  { key: "precipitacion", titulo: "Precipitación", icon: CloudRain },
  { key: "temperatura", titulo: "Temperatura", icon: Thermometer },
  { key: "alerta", titulo: "Alerta y recomendación", icon: TriangleAlert },
] as const

export function BoletinView({
  boletin,
  showPublish = false,
}: {
  boletin: Boletin
  showPublish?: boolean
}) {
  const [rawOpen, setRawOpen] = useState(false)
  const [publicado, setPublicado] = useState(boletin.publicado)

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-6 rounded-3xl bg-card p-6 shadow-sm sm:flex-row sm:items-center sm:justify-between">
        <div className="space-y-1">
          <p className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
            Boletín · Semana {boletin.semana}
          </p>
          <h2 className="text-2xl font-bold text-foreground sm:text-3xl">{boletin.fecha}</h2>
          <div className="pt-1">
            <NivelBadge nivel={boletin.nivel} />
          </div>
        </div>
        <Semaforo nivel={boletin.nivel} size="md" showLabel={false} showScale />
      </div>

      <div className="grid gap-5 md:grid-cols-2">
        {secciones.map((s) => {
          const Icon = s.icon
          return (
            <section key={s.key} className="rounded-3xl bg-card p-6 shadow-sm">
              <div className="mb-3 flex items-center gap-3">
                <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-secondary text-primary">
                  <Icon size={20} aria-hidden />
                </span>
                <h3 className="text-xl font-bold text-foreground">{s.titulo}</h3>
              </div>
              <RichText text={boletin.secciones[s.key]} />
            </section>
          )
        })}
      </div>

      <div className="overflow-hidden rounded-3xl bg-card shadow-sm">
        <button
          type="button"
          onClick={() => setRawOpen((o) => !o)}
          className="flex w-full items-center justify-between p-6 text-left text-lg font-semibold text-foreground hover:bg-muted/40"
          aria-expanded={rawOpen}
        >
          Ver datos crudos
          <ChevronDown size={22} className={cn("transition-transform", rawOpen && "rotate-180")} aria-hidden />
        </button>
        {rawOpen && (
          <div className="border-t border-border px-6 pb-6 pt-2">
            <dl className="divide-y divide-border">
              {boletin.datosCrudos.map((d) => (
                <div key={d.indicador} className="flex items-center justify-between py-3">
                  <dt className="text-base text-muted-foreground">{d.indicador}</dt>
                  <dd className="text-base font-semibold text-foreground">{d.valor}</dd>
                </div>
              ))}
            </dl>
          </div>
        )}
      </div>

      {showPublish && (
        <div className="flex flex-col items-start gap-3 rounded-3xl bg-card p-6 shadow-sm sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-lg font-semibold text-foreground">
              {publicado ? "Boletín publicado" : "Boletín en borrador"}
            </p>
            <p className="text-base text-muted-foreground">
              {publicado
                ? "Visible para ayuntamientos, medios y agricultores."
                : "Publícalo para notificar a todos los destinatarios."}
            </p>
          </div>
          <Button
            size="lg"
            onClick={() => setPublicado(true)}
            disabled={publicado}
            className="h-12 gap-2 px-6 text-base font-semibold text-white"
            style={{ backgroundColor: "var(--nivel-verde)" }}
          >
            {publicado ? <CheckCircle2 size={20} /> : <Send size={20} />}
            {publicado ? "Publicado" : "Publicar boletín"}
          </Button>
        </div>
      )}
    </div>
  )
}
