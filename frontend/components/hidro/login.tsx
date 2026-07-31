"use client"

import type React from "react"
import { useState } from "react"
import { Mail, Lock, Loader2 } from "lucide-react"
import { Logo } from "@/components/hidro/logo"
import { Button } from "@/components/ui/button"
import { type UserProfile } from "@/lib/api-client"

export function Login({ onLogin }: { onLogin: (email: string, password: string) => Promise<UserProfile> }) {
  const [email, setEmail] = useState("demo@durango.gob.mx")
  const [password, setPassword] = useState("hidroalerta")
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await onLogin(email, password)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al iniciar sesión")
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="flex min-h-svh items-center justify-center bg-background p-6">
      <div className="w-full max-w-md">
        <div className="mb-8 flex flex-col items-center gap-3 text-center">
          <Logo size="lg" />
          <p className="text-lg leading-relaxed text-muted-foreground text-pretty">
            Monitoreo de sequía y presas del estado de Durango
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5 rounded-3xl bg-card p-8 shadow-sm">
          <div className="space-y-2">
            <label htmlFor="email" className="text-base font-semibold text-foreground">
              Correo electrónico
            </label>
            <div className="flex items-center gap-3 rounded-2xl border border-input bg-background px-4 focus-within:border-ring focus-within:ring-3 focus-within:ring-ring/40">
              <Mail size={20} className="text-muted-foreground" aria-hidden />
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="h-14 w-full bg-transparent text-lg text-foreground outline-none placeholder:text-muted-foreground"
                placeholder="tucorreo@ejemplo.com"
              />
            </div>
          </div>

          <div className="space-y-2">
            <label htmlFor="password" className="text-base font-semibold text-foreground">
              Contraseña
            </label>
            <div className="flex items-center gap-3 rounded-2xl border border-input bg-background px-4 focus-within:border-ring focus-within:ring-3 focus-within:ring-ring/40">
              <Lock size={20} className="text-muted-foreground" aria-hidden />
              <input
                id="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="h-14 w-full bg-transparent text-lg text-foreground outline-none placeholder:text-muted-foreground"
                placeholder="••••••••"
              />
            </div>
          </div>

          {error && (
            <p className="text-sm font-medium text-destructive">{error}</p>
          )}

          <Button type="submit" disabled={loading} className="h-14 w-full text-lg font-semibold">
            {loading ? <Loader2 size={22} className="animate-spin" /> : "Iniciar sesión"}
          </Button>
        </form>

        <p className="mt-6 text-center text-sm text-muted-foreground">
          Gobierno del Estado de Durango · Comisión Estatal del Agua
        </p>
      </div>
    </main>
  )
}
