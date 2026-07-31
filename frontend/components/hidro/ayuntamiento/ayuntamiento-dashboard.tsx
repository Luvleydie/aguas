"use client"

import { useState } from "react"
import { Check, CheckCircle2, Loader2 } from "lucide-react"
import { TabsLayout, type TabItem } from "@/components/hidro/tabs-layout"
import { Semaforo } from "@/components/hidro/semaforo"
import { BoletinView } from "@/components/hidro/boletin-view"
import { TrendChart } from "@/components/hidro/trend-chart"
import { Button } from "@/components/ui/button"
import { presas } from "@/lib/hidro-data"
import { apiFetch, type BoletinReal } from "@/lib/api-client"
import { useEffect } from "react"

const tabs: TabItem[] = [
  { id: "inicio", label: "Inicio" },
  { id: "boletin", label: "Boletín" },
  { id: "tendencias", label: "Tendencias" },
]

export function AyuntamientoDashboard({ onLogout, token }: { onLogout: () => void; token: string }) {
  const [active, setActive] = useState("inicio")
  const [accion, setAccion] = useState(false)
  const [boletin, setBoletin] = useState<BoletinReal | null>(null)
  const [loading, setLoading] = useState(true)
  const [registering, setRegistering] = useState(false)

  useEffect(() => {
    apiFetch<BoletinReal[]>("/api/boletin/historico", { token })
      .then((lista) => { if (lista.length > 0) setBoletin(lista[0]) })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [token])

  async function handleMarcarAccion() {
    if (!boletin) return
    setRegistering(true)
    try {
      await apiFetch("/api/acciones/ayuntamiento", {
        method: "POST",
        token,
        body: { boletin_id: boletin.id, accion: "marcado_por_ayuntamiento" },
      })
      setAccion(true)
    } catch {
      // silenciar
    } finally {
      setRegistering(false)
    }
  }

  return (
    <TabsLayout tabs={tabs} active={active} onSelect={setActive} roleName="Ayuntamiento de Durango" onLogout={onLogout}>
      {active === "inicio" && (
        <div className="flex flex-col items-center gap-8 rounded-3xl bg-card p-8 text-center shadow-sm">
          {loading ? (
            <Loader2 size={24} className="animate-spin text-muted-foreground" />
          ) : boletin ? (
            <>
              <div>
                <p className="text-lg font-semibold text-muted-foreground">Nivel de alerta · Semana {boletin.semana}</p>
              </div>
              <Semaforo nivel={boletin.nivel} size="xl" showScale showLabel={false} />
              <p className="max-w-xl text-2xl font-semibold leading-relaxed text-foreground text-balance">
                {boletin.recomendacion}
              </p>
              <Button
                onClick={handleMarcarAccion}
                disabled={accion || registering}
                className="h-16 gap-3 px-8 text-lg font-bold text-white"
                style={{ backgroundColor: accion ? "var(--nivel-verde)" : "var(--primary)" }}
              >
                {registering ? <Loader2 size={26} className="animate-spin" /> : accion ? <CheckCircle2 size={26} /> : <Check size={26} />}
                {registering ? "Registrando..." : accion ? "Acción registrada" : "Marcar acción tomada"}
              </Button>
            </>
          ) : (
            <p className="text-muted-foreground">No hay boletines disponibles</p>
          )}
        </div>
      )}

      {active === "boletin" && boletin && <BoletinView boletin={boletin} />}

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
