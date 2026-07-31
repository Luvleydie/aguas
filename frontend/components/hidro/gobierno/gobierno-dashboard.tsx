"use client"

import { useState } from "react"
import { Home, FilePlus2, FileText, TrendingUp, History, Users } from "lucide-react"
import { SidebarLayout, type NavItem } from "@/components/hidro/sidebar-layout"
import { GobiernoInicio } from "@/components/hidro/gobierno/gobierno-inicio"
import { GobiernoGenerar } from "@/components/hidro/gobierno/gobierno-generar"
import { GobiernoBoletin } from "@/components/hidro/gobierno/gobierno-boletin"
import { GobiernoTendencias } from "@/components/hidro/gobierno/gobierno-tendencias"
import { GobiernoAuditoria } from "@/components/hidro/gobierno/gobierno-auditoria"
import { GobiernoUsuarios } from "@/components/hidro/gobierno/gobierno-usuarios"

const items: NavItem[] = [
  { id: "inicio", label: "Inicio", icon: Home },
  { id: "generar", label: "Generar boletín", icon: FilePlus2 },
  { id: "boletin", label: "Boletín", icon: FileText },
  { id: "tendencias", label: "Tendencias", icon: TrendingUp },
  { id: "auditoria", label: "Auditoría", icon: History },
  { id: "usuarios", label: "Usuarios", icon: Users },
]

const titulos: Record<string, string> = {
  inicio: "Inicio",
  generar: "Generar boletín",
  boletin: "Boletín semanal",
  tendencias: "Tendencias",
  auditoria: "Auditoría de agentes",
  usuarios: "Usuarios",
}

export function GobiernoDashboard({ onLogout, token }: { onLogout: () => void; token: string }) {
  const [active, setActive] = useState("inicio")

  return (
    <SidebarLayout
      items={items}
      active={active}
      onSelect={setActive}
      roleName="Gobierno del Estado"
      onLogout={onLogout}
      title={titulos[active]}
    >
      {active === "inicio" && <GobiernoInicio onNavigate={setActive} token={token} />}
      {active === "generar" && <GobiernoGenerar onDone={() => setActive("boletin")} token={token} />}
      {active === "boletin" && <GobiernoBoletin token={token} />}
      {active === "tendencias" && <GobiernoTendencias />}
      {active === "auditoria" && <GobiernoAuditoria token={token} />}
      {active === "usuarios" && <GobiernoUsuarios />}
    </SidebarLayout>
  )
}
