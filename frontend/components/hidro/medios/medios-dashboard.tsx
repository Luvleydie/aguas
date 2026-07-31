"use client"

import { useState } from "react"
import { FileDown, ImageDown, FileText, Calendar } from "lucide-react"
import { TabsLayout, type TabItem } from "@/components/hidro/tabs-layout"
import { Semaforo } from "@/components/hidro/semaforo"
import { NivelBadge } from "@/components/hidro/nivel-badge"
import { TrendChart } from "@/components/hidro/trend-chart"
import { boletines, boletinActual, presas, sequiasHistoricas } from "@/lib/hidro-data"

const tabs: TabItem[] = [
  { id: "inicio", label: "Inicio" },
  { id: "narrativo", label: "Boletín narrativo" },
  { id: "comparativa", label: "Comparativa" },
]

function descargar(nombre: string, contenido: string, tipo: string) {
  const blob = new Blob([contenido], { type: tipo })
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = nombre
  a.click()
  URL.revokeObjectURL(url)
}

export function MediosDashboard({ onLogout }: { onLogout: () => void }) {
  const [active, setActive] = useState("inicio")

  const markdown = `# Boletín AWAS — Semana ${boletinActual.semana}\n\n${boletinActual.fecha}\n\nNivel de alerta: ${boletinActual.nivel.toUpperCase()}\n\n${boletinActual.narrativo}`

  return (
    <TabsLayout tabs={tabs} active={active} onSelect={setActive} roleName="Medios de comunicación" onLogout={onLogout}>
      {active === "inicio" && (
        <div className="space-y-4">
          <h2 className="text-xl font-bold text-foreground">Boletines publicados</h2>
          {boletines.map((b) => (
            <article key={b.id} className="flex items-center gap-5 rounded-3xl bg-card p-5 shadow-sm sm:p-6">
              <Semaforo nivel={b.nivel} size="sm" showLabel={false} showScale={false} />
              <div className="flex-1">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Calendar size={16} aria-hidden />
                  Semana {b.semana} · {b.fecha}
                </div>
                <h3 className="mt-1 text-lg font-bold text-foreground">Boletín semanal de sequía</h3>
                <p className="mt-1 text-base text-muted-foreground leading-relaxed line-clamp-2">{b.resumen}</p>
                <div className="mt-2">
                  <NivelBadge nivel={b.nivel} />
                </div>
              </div>
            </article>
          ))}
        </div>
      )}

      {active === "narrativo" && (
        <div className="space-y-6">
          <article className="rounded-3xl bg-card p-6 shadow-sm sm:p-8">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-2xl font-bold text-foreground">Boletín narrativo</h2>
                <p className="text-base text-muted-foreground">Semana {boletinActual.semana} · {boletinActual.fecha}</p>
              </div>
              <NivelBadge nivel={boletinActual.nivel} />
            </div>
            <p className="text-xl leading-relaxed text-foreground text-pretty">{boletinActual.narrativo}</p>
          </article>

          <div className="rounded-3xl bg-card p-6 shadow-sm sm:p-8">
            <h3 className="mb-4 text-lg font-bold text-foreground">Descargar boletín</h3>
            <div className="flex flex-wrap gap-4">
              <button
                type="button"
                onClick={() => window.print()}
                className="flex items-center gap-2 rounded-2xl bg-primary px-6 py-4 text-base font-semibold text-primary-foreground hover:bg-primary/90"
              >
                <FileDown size={22} aria-hidden />
                Descargar PDF
              </button>
              <button
                type="button"
                onClick={() => descargar(`awas-s${boletinActual.semana}.svg`, `<svg xmlns='http://www.w3.org/2000/svg' width='800' height='400'><rect width='100%' height='100%' fill='#03695e'/><text x='40' y='120' fill='white' font-size='40' font-family='sans-serif'>AWAS — Semana ${boletinActual.semana}</text><text x='40' y='190' fill='white' font-size='28' font-family='sans-serif'>Nivel: ${boletinActual.nivel}</text></svg>`, "image/svg+xml")}
                className="flex items-center gap-2 rounded-2xl bg-accent px-6 py-4 text-base font-semibold text-accent-foreground hover:bg-accent/90"
              >
                <ImageDown size={22} aria-hidden />
                Descargar imagen
              </button>
              <button
                type="button"
                onClick={() => descargar(`awas-s${boletinActual.semana}.md`, markdown, "text/markdown")}
                className="flex items-center gap-2 rounded-2xl border-2 border-primary px-6 py-4 text-base font-semibold text-primary hover:bg-secondary/50"
              >
                <FileText size={22} aria-hidden />
                Descargar Markdown
              </button>
            </div>
          </div>
        </div>
      )}

      {active === "comparativa" && (
        <div className="rounded-3xl bg-card p-6 shadow-sm sm:p-8">
          <h2 className="mb-1 text-xl font-bold text-foreground">Comparativa histórica</h2>
          <p className="mb-5 text-base text-muted-foreground">
            Nivel de almacenamiento actual frente a sequías históricas.
          </p>
          <TrendChart
            data={presas[0].historial}
            height={320}
            references={sequiasHistoricas.map((s) => ({ y: s.nivel, label: s.etiqueta }))}
          />
          <div className="mt-5 grid gap-3 sm:grid-cols-3">
            {sequiasHistoricas.map((s) => (
              <div key={s.anio} className="rounded-2xl bg-secondary/40 p-4">
                <p className="text-2xl font-bold text-foreground">{s.anio}</p>
                <p className="text-base text-muted-foreground">Mínimo del {s.nivel}% de capacidad</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </TabsLayout>
  )
}
