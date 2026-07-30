"use client"

import { useState } from "react"
import { Check, CheckCircle2 } from "lucide-react"
import { TabsLayout, type TabItem } from "@/components/hidro/tabs-layout"
import { Semaforo } from "@/components/hidro/semaforo"
import { BoletinView } from "@/components/hidro/boletin-view"
import { TrendChart } from "@/components/hidro/trend-chart"
import { Button } from "@/components/ui/button"
import { boletinActual, presas } from "@/lib/hidro-data"

const tabs: TabItem[] = [
  { id: "inicio", label: "Inicio" },
  { id: "boletin", label: "Boletín" },
  { id: "tendencias", label: "Tendencias" },
]

export function AyuntamientoDashboard({ onLogout }: { onLogout: () => void }) {
  const [active, setActive] = useState("inicio")
  const [accion, setAccion] = useState(false)

  return (
    <TabsLayout tabs={tabs} active={active} onSelect={setActive} roleName="Ayuntamiento de Durango" onLogout={onLogout}>
      {active === "inicio" && (
        <div className="flex flex-col items-center gap-8 rounded-3xl bg-card p-8 text-center shadow-sm">
          <div>
            <p className="text-lg font-semibold text-muted-foreground">Nivel de alerta · Semana {boletinActual.semana}</p>
          </div>
          <Semaforo nivel={boletinActual.nivel} size="xl" showScale showLabel={false} />
          <p className="max-w-xl text-2xl font-semibold leading-relaxed text-foreground text-balance">
            Restricción parcial del riego agrícola. Priorizar el consumo humano y reforzar el ahorro de agua.
          </p>
          <Button
            onClick={() => setAccion(true)}
            disabled={accion}
            className="h-16 gap-3 px-8 text-lg font-bold text-white"
            style={{ backgroundColor: accion ? "var(--nivel-verde)" : "var(--primary)" }}
          >
            {accion ? <CheckCircle2 size={26} /> : <Check size={26} />}
            {accion ? "Acción registrada" : "Marcar acción tomada"}
          </Button>
        </div>
      )}

      {active === "boletin" && <BoletinView boletin={boletinActual} />}

      {active === "tendencias" && (
        <div className="rounded-3xl bg-card p-6 shadow-sm sm:p-8">
          <h2 className="mb-1 text-xl font-bold text-foreground">Nivel de presas locales</h2>
          <p className="mb-5 text-base text-muted-foreground">Últimas 12 semanas · % de capacidad</p>
          <TrendChart data={presas[0].historial} simple height={280} />
        </div>
      )}
    </TabsLayout>
  )
}
