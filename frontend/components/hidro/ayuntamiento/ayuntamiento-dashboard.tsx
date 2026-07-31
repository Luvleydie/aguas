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

interface PlanAccionItem {
  id: string | number
  accion: string
  descripcion: string
  plazo: string
  costo: string
  area_responsable: string
  prioridad: number
}

export function AyuntamientoDashboard({ onLogout, token }: { onLogout: () => void; token: string }) {
  const [active, setActive] = useState("inicio")
  const [boletin, setBoletin] = useState<BoletinReal | null>(null)
  const [plan, setPlan] = useState<PlanAccionItem[]>([])
  const [loading, setLoading] = useState(true)
  const [registeringId, setRegisteringId] = useState<string | null>(null)
  const [accionesRegistradas, setAccionesRegistradas] = useState<Record<string, boolean>>({})

  useEffect(() => {
    apiFetch<BoletinReal[]>("/api/boletin/historico", { token })
      .then(async (lista) => { 
        if (lista.length > 0) {
          const b = lista[0]
          setBoletin(b)
          try {
            const planData = await apiFetch<PlanAccionItem[]>(`/api/plan-accion/${b.semana}`, { token })
            setPlan(planData)
          } catch(e) {}
        } 
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [token])

  async function handleMarcarAccion(item: PlanAccionItem) {
    if (!boletin) return
    const sid = item.id.toString()
    setRegisteringId(sid)
    try {
      await apiFetch("/api/acciones/ayuntamiento", {
        method: "POST",
        token,
        body: { boletin_id: boletin.id, accion: item.accion, notas: `Ref ID: ${item.id}` },
      })
      setAccionesRegistradas(prev => ({ ...prev, [sid]: true }))
    } catch {
      // silenciar
    } finally {
      setRegisteringId(null)
    }
  }

  return (
    <TabsLayout tabs={tabs} active={active} onSelect={setActive} roleName="Ayuntamiento de Durango" onLogout={onLogout}>
      {active === "inicio" && (
        <div className="flex flex-col gap-8">
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
              </>
            ) : (
              <p className="text-muted-foreground">No hay boletines disponibles</p>
            )}
          </div>
          
          {plan.length > 0 && (
            <div className="rounded-3xl bg-card p-8 shadow-sm">
              <h2 className="mb-6 text-2xl font-bold text-foreground">Plan de acción recomendado</h2>
              <div className="flex flex-col gap-4">
                {plan.map(item => {
                  const sid = item.id.toString()
                  const isRegistered = accionesRegistradas[sid]
                  const isRegistering = registeringId === sid
                  
                  return (
                    <div key={sid} className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 p-5 rounded-2xl border bg-background">
                      <div className="flex-1">
                        <div className="flex flex-wrap items-center gap-3 mb-2">
                          <h3 className="font-semibold text-lg">{item.accion}</h3>
                          <span className="px-2 py-1 text-xs font-medium bg-secondary text-secondary-foreground rounded-full">
                            Prioridad: {item.prioridad}
                          </span>
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                            item.costo.toLowerCase() === 'alto' ? 'bg-destructive/10 text-destructive' :
                            item.costo.toLowerCase() === 'medio' ? 'bg-orange-500/10 text-orange-600' :
                            'bg-green-500/10 text-green-600'
                          }`}>
                            Costo: {item.costo}
                          </span>
                          <span className="px-2 py-1 text-xs font-medium bg-blue-500/10 text-blue-600 rounded-full">
                            {item.area_responsable}
                          </span>
                        </div>
                        <p className="text-muted-foreground text-sm">{item.descripcion}</p>
                        <p className="text-xs text-muted-foreground mt-2 font-medium">Plazo: {item.plazo}</p>
                      </div>
                      
                      <Button
                        onClick={() => handleMarcarAccion(item)}
                        disabled={isRegistered || isRegistering || registeringId !== null}
                        variant={isRegistered ? "outline" : "default"}
                        className="w-full sm:w-auto flex-shrink-0"
                      >
                        {isRegistering ? <Loader2 size={16} className="animate-spin mr-2" /> : 
                         isRegistered ? <CheckCircle2 size={16} className="mr-2 text-green-600" /> : 
                         <Check size={16} className="mr-2" />}
                        {isRegistering ? "Registrando..." : isRegistered ? "Iniciada" : "Marcar como iniciada"}
                      </Button>
                    </div>
                  )
                })}
              </div>
            </div>
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
