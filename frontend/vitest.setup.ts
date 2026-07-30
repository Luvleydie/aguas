import "@testing-library/jest-dom/vitest"

// Recharts (usado por TrendChart en gobierno/ayuntamiento/medios) mide su
// contenedor con ResizeObserver; jsdom no lo implementa y ResponsiveContainer
// no renderiza hijos con tamaño 0x0.
class ResizeObserverMock implements ResizeObserver {
  callback: ResizeObserverCallback
  constructor(callback: ResizeObserverCallback) {
    this.callback = callback
  }
  observe(target: Element) {
    this.callback([{ target, contentRect: { width: 600, height: 320 } } as ResizeObserverEntry], this)
  }
  unobserve() {}
  disconnect() {}
}
globalThis.ResizeObserver = ResizeObserverMock

Object.defineProperty(HTMLElement.prototype, "offsetWidth", { configurable: true, value: 600 })
Object.defineProperty(HTMLElement.prototype, "offsetHeight", { configurable: true, value: 320 })
HTMLElement.prototype.getBoundingClientRect = () =>
  ({ width: 600, height: 320, top: 0, left: 0, bottom: 320, right: 600, x: 0, y: 0, toJSON() {} }) as DOMRect
