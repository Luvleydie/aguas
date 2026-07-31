"""Doble mínimo de un cliente Supabase (postgrest) para probar backend/main.py
sin red. No simula RLS — eso se prueba aparte, directo contra Postgres, en el
punto 6 (TDD de expert-bd sobre el schema ya aplicado)."""

from __future__ import annotations

import uuid
from typing import Any

_COLUMNAS_PUBLICAS_BOLETIN = {
    "id",
    "semana",
    "anio",
    "markdown",
    "nivel_alerta_global",
    "recomendacion",
    "publicado",
    "generado_por",
    "created_at",
    "published_at",
}


class FakeResponse:
    def __init__(self, data: list[dict[str, Any]]) -> None:
        self.data = data


class FakeQuery:
    def __init__(self, store: dict[str, list[dict[str, Any]]], tabla: str) -> None:
        self._store = store
        self._tabla = tabla
        self._filtros: dict[str, Any] = {}
        self._orden: list[tuple[str, bool]] = []
        self._limite: int | None = None
        self._modo: str | None = None
        self._payload: Any = None

    def select(self, _columnas: str = "*") -> "FakeQuery":
        self._modo = "select"
        return self

    def insert(self, payload: Any) -> "FakeQuery":
        self._modo = "insert"
        self._payload = payload
        return self

    def update(self, payload: dict[str, Any]) -> "FakeQuery":
        self._modo = "update"
        self._payload = payload
        return self

    def eq(self, columna: str, valor: Any) -> "FakeQuery":
        self._filtros[columna] = valor
        return self

    def order(self, columna: str, desc: bool = False) -> "FakeQuery":
        self._orden.append((columna, desc))
        return self

    def limit(self, cantidad: int) -> "FakeQuery":
        self._limite = cantidad
        return self

    def _filas_base(self) -> list[dict[str, Any]]:
        if self._tabla == "boletines_publico":
            filas = [f for f in self._store.get("boletines", []) if f.get("publicado")]
            return [{k: v for k, v in f.items() if k in _COLUMNAS_PUBLICAS_BOLETIN} for f in filas]
        return self._store.setdefault(self._tabla, [])

    def execute(self) -> FakeResponse:
        if self._modo == "insert":
            filas = self._store.setdefault(self._tabla, [])
            payloads = self._payload if isinstance(self._payload, list) else [self._payload]
            creadas = []
            for payload in payloads:
                fila = {"id": str(uuid.uuid4()), **payload}
                filas.append(fila)
                creadas.append(fila)
            return FakeResponse(creadas)

        if self._modo == "update":
            filas = self._store.setdefault(self._tabla, [])
            actualizadas = []
            for fila in filas:
                if all(fila.get(k) == v for k, v in self._filtros.items()):
                    fila.update(self._payload)
                    actualizadas.append(fila)
            return FakeResponse(actualizadas)

        resultado = [
            fila for fila in self._filas_base() if all(fila.get(k) == v for k, v in self._filtros.items())
        ]
        for columna, desc in reversed(self._orden):
            resultado.sort(key=lambda f: f.get(columna), reverse=desc)
        if self._limite is not None:
            resultado = resultado[: self._limite]
        return FakeResponse(resultado)


class FakeSupabase:
    def __init__(self) -> None:
        self.store: dict[str, list[dict[str, Any]]] = {}

    def table(self, nombre: str) -> FakeQuery:
        return FakeQuery(self.store, nombre)
