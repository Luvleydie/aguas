"use client"

import type { Rol } from "@/lib/hidro-data"
import { useSession } from "@/lib/use-session"
import { Login } from "@/components/hidro/login"
import { GobiernoDashboard } from "@/components/hidro/gobierno/gobierno-dashboard"
import { AyuntamientoDashboard } from "@/components/hidro/ayuntamiento/ayuntamiento-dashboard"
import { MediosDashboard } from "@/components/hidro/medios/medios-dashboard"
import { AgricultorDashboard } from "@/components/hidro/agricultor/agricultor-dashboard"

export function AppRoot() {
  const { user, token, loading, login, logout } = useSession()

  if (loading) {
    return (
      <div className="flex min-h-svh items-center justify-center">
        <p className="text-muted-foreground">Cargando...</p>
      </div>
    )
  }

  if (!user || !token) return <Login onLogin={login} />

  const rol = user.rol as Rol

  switch (rol) {
    case "gobierno":
      return <GobiernoDashboard onLogout={logout} token={token} />
    case "ayuntamiento":
      return <AyuntamientoDashboard onLogout={logout} token={token} />
    case "medios":
      return <MediosDashboard onLogout={logout} token={token} />
    case "agricultor":
      return <AgricultorDashboard onLogout={logout} token={token} />
  }
}
