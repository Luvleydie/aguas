"use client"

import type React from "react"
import { useState } from "react"
import { Mail, Lock, Loader2, UserPlus, Eye, EyeOff } from "lucide-react"
import { Logo } from "@/components/hidro/logo"
import { Button } from "@/components/ui/button"
import { type UserProfile, register } from "@/lib/api-client"

export function Login({ onLogin }: { onLogin: (email: string, password: string) => Promise<UserProfile> }) {
  const [mode, setMode] = useState<"login" | "register">("login")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setSuccess(null)
    setLoading(true)
    try {
      if (mode === "register") {
        await register(email, password)
        setSuccess("Usuario registrado. Ahora puedes iniciar sesión.")
        setMode("login")
      } else {
        await onLogin(email, password)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al procesar")
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
                type={showPassword ? "text" : "password"}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="h-14 w-full bg-transparent text-lg text-foreground outline-none placeholder:text-muted-foreground"
                placeholder="••••••••"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="shrink-0 rounded-lg p-1 text-muted-foreground hover:text-foreground"
                aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
              >
                {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
              </button>
            </div>
          </div>

          {mode === "register" && (
            <p className="text-sm text-muted-foreground text-center">
              Tu rol se asigna según tu correo: <strong>@durango.gob.mx</strong> (Gobierno), <strong>@ayuntamiento.com</strong> (Ayuntamiento), <strong>@prensa.com</strong> (Medios), <strong>@gmail.com</strong> (Agricultor)
            </p>
          )}

          {error && (
            <p className="text-sm font-medium text-destructive">{error}</p>
          )}

          {success && (
            <p className="text-sm font-medium text-green-600">{success}</p>
          )}

          <Button type="submit" disabled={loading} className="h-14 w-full text-lg font-semibold">
            {loading ? <Loader2 size={22} className="animate-spin" /> : mode === "register" ? <><UserPlus size={22} /> Registrarse</> : "Iniciar sesión"}
          </Button>
        </form>

        <div className="mt-4 text-center">
          <button
            type="button"
            onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(null); setSuccess(null) }}
            className="text-sm text-primary hover:underline"
          >
            {mode === "login" ? "¿No tienes cuenta? Regístrate" : "¿Ya tienes cuenta? Inicia sesión"}
          </button>
        </div>

        <p className="mt-6 text-center text-sm text-muted-foreground">
          Gobierno del Estado de Durango · Comisión Estatal del Agua
        </p>
      </div>
    </main>
  )
}
