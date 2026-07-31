"use client"

import { LogOut } from "lucide-react"
import { Logo } from "@/components/hidro/logo"
import { cn } from "@/lib/utils"

export interface TabItem {
  id: string
  label: string
}

export function TabsLayout({
  tabs,
  active,
  onSelect,
  roleName,
  onLogout,
  children,
}: {
  tabs: TabItem[]
  active: string
  onSelect: (id: string) => void
  roleName: string
  onLogout: () => void
  children: React.ReactNode
}) {
  return (
    <div className="min-h-svh bg-background">
      <div className="mx-auto max-w-5xl px-5 pt-5 md:px-8 md:pt-8 lg:max-w-6xl">
        <header className="overflow-hidden rounded-3xl bg-primary text-primary-foreground shadow-sm">
          <div className="flex items-center justify-between gap-3 px-5 py-4">
            <Logo size="sm" variant="light" />
            <div className="flex items-center gap-3">
              <span className="hidden text-sm text-primary-foreground/80 sm:inline">{roleName}</span>
              <button
                type="button"
                onClick={onLogout}
                className="flex items-center gap-2 rounded-xl bg-white/10 px-3 py-2 text-sm font-medium hover:bg-white/20"
              >
                <LogOut size={18} aria-hidden />
                <span className="hidden sm:inline">Salir</span>
              </button>
            </div>
          </div>
          <nav className="flex gap-1 overflow-x-auto px-5">
            {tabs.map((t) => {
              const isActive = t.id === active
              return (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => onSelect(t.id)}
                  aria-current={isActive ? "page" : undefined}
                  className={cn(
                    "shrink-0 border-b-4 px-4 py-3 text-base font-semibold transition-colors",
                    isActive
                      ? "border-white text-white"
                      : "border-transparent text-primary-foreground/70 hover:text-white",
                  )}
                >
                  {t.label}
                </button>
              )
            })}
          </nav>
        </header>
      </div>
      <main className="mx-auto max-w-5xl p-5 md:p-8 lg:max-w-6xl">{children}</main>
    </div>
  )
}
