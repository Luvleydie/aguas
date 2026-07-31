import { describe, expect, it, vi, beforeEach } from "vitest"

vi.mock("@/lib/api-client", () => ({
  login: vi.fn(),
  getProfile: vi.fn(),
  apiFetch: vi.fn().mockResolvedValue([]),
}))

import { login, getProfile, apiFetch } from "@/lib/api-client"
import { render, screen, waitFor } from "@testing-library/react"
import { AppRoot } from "./app-root"

const mockLogin = vi.mocked(login)
const mockGetProfile = vi.mocked(getProfile)
const mockApiFetch = vi.mocked(apiFetch)

beforeEach(() => {
  localStorage.clear()
  vi.clearAllMocks()
  mockApiFetch.mockResolvedValue([])
})

function renderConSesion(rol: "gobierno" | "ayuntamiento" | "medios" | "agricultor") {
  localStorage.setItem("awas_token", "tok_saved")
  mockGetProfile.mockResolvedValue({ id: "1", email: "test@test.com", rol })
  render(<AppRoot />)
}

describe("AppRoot", () => {
  it("muestra el login antes de autenticarse", () => {
    render(<AppRoot />)
    expect(screen.getByRole("button", { name: /iniciar sesión/i })).toBeInTheDocument()
  })

  it("redirige a Gobierno si rol=gobierno", async () => {
    renderConSesion("gobierno")
    await waitFor(() => {
      expect(screen.getByText("Gobierno del Estado")).toBeInTheDocument()
    })
  })

  it("redirige a Ayuntamiento si rol=ayuntamiento", async () => {
    renderConSesion("ayuntamiento")
    await waitFor(() => {
      expect(screen.getByText("Ayuntamiento de Durango")).toBeInTheDocument()
    })
  })

  it("redirige a Medios si rol=medios", async () => {
    renderConSesion("medios")
    await waitFor(() => {
      expect(screen.getByText("Boletín narrativo")).toBeInTheDocument()
    })
  })

  it("redirige a Agricultor si rol=agricultor", async () => {
    renderConSesion("agricultor")
    await waitFor(() => {
      expect(screen.getByText("Siembra")).toBeInTheDocument()
    })
  })
})
