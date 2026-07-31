"use client"

import { usuarios as data } from "@/lib/hidro-data"
import { cn } from "@/lib/utils"

function Toggle({ on, label }: { on: boolean; label: string }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={on}
      aria-label={label}
      disabled
      title="Disponible en una fase futura"
      className={cn(
        "relative h-8 w-14 shrink-0 rounded-full transition-colors disabled:cursor-not-allowed disabled:opacity-50",
        on ? "" : "bg-muted",
      )}
      style={on ? { backgroundColor: "var(--nivel-verde)" } : undefined}
    >
      <span
        className={cn(
          "absolute top-1 h-6 w-6 rounded-full bg-white shadow transition-transform",
          on ? "translate-x-7" : "translate-x-1",
        )}
      />
    </button>
  )
}

export function GobiernoUsuarios() {
  return (
    <div className="overflow-hidden rounded-3xl bg-card shadow-sm">
      <div className="p-6 sm:p-8">
        <h2 className="text-xl font-bold text-foreground">Usuarios y notificaciones</h2>
        <p className="mt-1 text-base text-muted-foreground">
          Alertas por WhatsApp — disponibles en una fase futura.
        </p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-y border-border bg-secondary/40 text-left text-sm font-semibold uppercase tracking-wide text-muted-foreground">
              <th className="px-6 py-3 sm:px-8">Nombre</th>
              <th className="px-6 py-3">Rol</th>
              <th className="px-6 py-3 text-right sm:px-8">WhatsApp</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {data.map((u) => (
              <tr key={u.id}>
                <td className="px-6 py-4 text-lg font-medium text-foreground sm:px-8">{u.nombre}</td>
                <td className="px-6 py-4 text-base text-muted-foreground">{u.rol}</td>
                <td className="px-6 py-4 sm:px-8">
                  <div className="flex justify-end">
                    <Toggle on={u.whatsapp} label={`WhatsApp para ${u.nombre}`} />
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
