"use client"

import { useState } from "react"
import type { Rol } from "@/lib/hidro-data"
import { Login } from "@/components/hidro/login"
import { GobiernoDashboard } from "@/components/hidro/gobierno/gobierno-dashboard"
import { AyuntamientoDashboard } from "@/components/hidro/ayuntamiento/ayuntamiento-dashboard"
import { MediosDashboard } from "@/components/hidro/medios/medios-dashboard"
import { AgricultorDashboard } from "@/components/hidro/agricultor/agricultor-dashboard"

export function AppRoot() {
  const [session, setSession] = useState<Rol | null>(null)

  if (!session) return <Login onLogin={setSession} />

  const logout = () => setSession(null)

  switch (session) {
    case "gobierno":
      return <GobiernoDashboard onLogout={logout} />
    case "ayuntamiento":
      return <AyuntamientoDashboard onLogout={logout} />
    case "medios":
      return <MediosDashboard onLogout={logout} />
    case "agricultor":
      return <AgricultorDashboard onLogout={logout} />
  }
}
