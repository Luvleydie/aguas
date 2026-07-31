"use client"

import { useEffect, useState } from "react"
import { Loader2 } from "lucide-react"
import { BoletinView } from "@/components/hidro/boletin-view"
import { apiFetch, type BoletinReal } from "@/lib/api-client"

export function GobiernoBoletin({ token }: { token: string }) {
  const [boletin, setBoletin] = useState<BoletinReal | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    apiFetch<BoletinReal[]>("/api/boletin/historico", { token })
      .then((lista) => { if (lista.length > 0) setBoletin(lista[0]) })
      .catch((err) => setError(err instanceof Error ? err.message : "Error al cargar boletín"))
      .finally(() => setLoading(false))
  }, [token])

  if (loading) {
    return (
      <div className="flex items-center justify-center rounded-3xl bg-card p-8 shadow-sm">
        <Loader2 size={24} className="animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-3xl bg-card p-8 shadow-sm">
        <p className="text-destructive">{error}</p>
      </div>
    )
  }

  if (!boletin) {
    return (
      <div className="rounded-3xl bg-card p-8 shadow-sm">
        <p className="text-muted-foreground">No hay boletines disponibles. Genera uno primero.</p>
      </div>
    )
  }

  return <BoletinView boletin={boletin} showPublish token={token} />
}
