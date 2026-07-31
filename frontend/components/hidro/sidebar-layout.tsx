"use client"

import type { LucideIcon } from "lucide-react"
import { LogOut } from "lucide-react"
import { Logo } from "@/components/hidro/logo"
import { cn } from "@/lib/utils"

export interface NavItem {
  id: string
  label: string
  icon: LucideIcon
}

export function SidebarLayout({
  items,
  active,
  onSelect,
  roleName,
  onLogout,
  title,
  children,
}: {
  items: NavItem[]
  active: string
  onSelect: (id: string) => void
  roleName: string
  onLogout: () => void
  title: string
  children: React.ReactNode
}) {
  return (
    <div className="flex min-h-svh bg-background">
      <aside className="sticky top-0 hidden h-svh w-72 shrink-0 flex-col bg-sidebar p-5 text-sidebar-foreground md:flex">
        <Logo size="sm" variant="light" className="px-2 py-3" />
        <p className="px-2 pb-4 text-sm text-sidebar-foreground/70">{roleName}</p>
        <nav className="flex flex-1 flex-col gap-1">
          {items.map((item) => {
            const Icon = item.icon
            const isActive = item.id === active
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => onSelect(item.id)}
                aria-current={isActive ? "page" : undefined}
                className={cn(
                  "flex items-center gap-3 rounded-2xl px-4 py-3 text-left text-base font-medium transition-colors",
                  isActive
                    ? "bg-sidebar-primary text-sidebar-primary-foreground"
                    : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
                )}
              >
                <Icon size={22} aria-hidden />
                {item.label}
              </button>
            )
          })}
        </nav>
        <button
          type="button"
          onClick={onLogout}
          className="mt-4 flex items-center gap-3 rounded-2xl px-4 py-3 text-left text-base font-medium text-sidebar-foreground hover:bg-sidebar-accent"
        >
          <LogOut size={22} aria-hidden />
          Cerrar sesión
        </button>
      </aside>

      {/* Mobile top nav */}
      <div className="flex w-full flex-col">
        <header className="sticky top-0 z-10 flex items-center justify-between gap-3 bg-sidebar px-5 py-3 text-sidebar-foreground md:bg-card md:text-foreground md:px-8 md:py-5">
          <div className="md:hidden">
            <Logo size="sm" variant="light" />
          </div>
          <h1 className="hidden text-2xl font-bold text-foreground md:block">{title}</h1>
          <button
            type="button"
            onClick={onLogout}
            className="rounded-xl p-2 hover:bg-sidebar-accent md:hidden"
            aria-label="Cerrar sesión"
          >
            <LogOut size={22} aria-hidden />
          </button>
        </header>

        {/* Mobile nav scroller */}
        <nav className="flex gap-2 overflow-x-auto bg-sidebar px-4 pb-3 md:hidden">
          {items.map((item) => {
            const Icon = item.icon
            const isActive = item.id === active
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => onSelect(item.id)}
                className={cn(
                  "flex shrink-0 items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium",
                  isActive
                    ? "bg-sidebar-primary text-sidebar-primary-foreground"
                    : "bg-sidebar-accent/60 text-sidebar-foreground",
                )}
              >
                <Icon size={18} aria-hidden />
                {item.label}
              </button>
            )
          })}
        </nav>

        <main className="flex-1 p-5 md:p-8">
          <div className="mx-auto max-w-6xl lg:max-w-7xl">{children}</div>
        </main>
      </div>
    </div>
  )
}
