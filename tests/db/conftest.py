"""Fixtures para el TDD de expert-bd contra el proyecto Supabase real.

Sin mocks: abre una conexión Postgres real (``DATABASE_URL``) y crea usuarios
reales de Supabase Auth (vía Admin API) para poder ejercer RLS de verdad
(``0001_init_schema.sql``). Cada test corre en una transacción que siempre se
revierte, así que la base remota queda limpia al terminar.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
import uuid
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any, NamedTuple

import psycopg
import pytest

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

ROOT = Path(__file__).resolve().parents[2]

if load_dotenv is not None:
    load_dotenv(ROOT / ".env")

DATABASE_URL = os.environ.get("DATABASE_URL")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.environ.get("SUPABASE_SECRET_KEY")

requiere_supabase = pytest.mark.skipif(
    not (DATABASE_URL and SUPABASE_URL and SUPABASE_SECRET_KEY),
    reason="Faltan DATABASE_URL/SUPABASE_URL/SUPABASE_SECRET_KEY en el entorno (.env)",
)


@pytest.fixture
def pg_conn() -> Iterator[psycopg.Connection]:
    conn = psycopg.connect(DATABASE_URL, connect_timeout=10)
    try:
        yield conn
    finally:
        conn.rollback()
        conn.close()


class AuthUser(NamedTuple):
    id: uuid.UUID
    email: str


def _admin_request(method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    url = f"{SUPABASE_URL}/auth/v1/admin{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = urllib.request.Request(url, data=data, method=method)
    request.add_header("apikey", SUPABASE_SECRET_KEY)
    request.add_header("Authorization", f"Bearer {SUPABASE_SECRET_KEY}")
    request.add_header("Content-Type", "application/json")

    ultimo_error: Exception | None = None
    for _intento in range(3):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = response.read()
                return json.loads(payload) if payload else {}
        except urllib.error.HTTPError as exc:
            detalle = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Admin API {method} {path} -> {exc.code}: {detalle}") from exc
        except urllib.error.URLError as exc:
            ultimo_error = exc
    raise RuntimeError(f"Admin API {method} {path} agotó el tiempo tras 3 intentos") from ultimo_error


_TAMANO_POOL = 6


@pytest.fixture(scope="session")
def _pool_auth_users() -> Iterator[list[AuthUser]]:
    """Crea un puñado de usuarios reales de Supabase Auth UNA sola vez por
    sesión de pytest (la Admin API de este entorno tarda ~20-45s por
    llamada; crear/borrar un usuario por test haría la suite impracticable).

    Cada test toma prestados algunos de este pool; como cada test corre en
    una transacción de Postgres que siempre se revierte, reutilizar el mismo
    auth_user_id entre tests no deja residuos.
    """

    if not (DATABASE_URL and SUPABASE_URL and SUPABASE_SECRET_KEY):
        yield []
        return

    creados: list[AuthUser] = []
    for _ in range(_TAMANO_POOL):
        email = f"pool-{uuid.uuid4().hex}@hidroalerta.test"
        resultado = _admin_request(
            "POST",
            "/users",
            {"email": email, "password": uuid.uuid4().hex, "email_confirm": True},
        )
        creados.append(AuthUser(id=uuid.UUID(resultado["id"]), email=email))

    yield creados

    for usuario in creados:
        try:
            _admin_request("DELETE", f"/users/{usuario.id}")
        except RuntimeError:
            pass


@pytest.fixture
def make_auth_user(_pool_auth_users: list[AuthUser]) -> Callable[[], AuthUser]:
    """Entrega usuarios distintos del pool de sesión, sin llamar a la Admin
    API por test. Cada test recibe su propio contador (arranca en 0)."""

    disponibles = iter(_pool_auth_users)

    def _obtener() -> AuthUser:
        try:
            return next(disponibles)
        except StopIteration as exc:
            raise RuntimeError(
                f"Pool de usuarios de prueba ({_TAMANO_POOL}) agotado en un solo test; "
                "sube _TAMANO_POOL si un test necesita más usuarios distintos."
            ) from exc

    return _obtener


def insertar_usuario(
    conn: psycopg.Connection,
    auth_user_id: uuid.UUID,
    email: str,
    nombre: str,
    rol: str,
) -> uuid.UUID:
    with conn.cursor() as cur:
        cur.execute(
            "insert into usuarios (auth_user_id, email, nombre, rol) values (%s, %s, %s, %s) returning id",
            (auth_user_id, email, nombre, rol),
        )
        return cur.fetchone()[0]


def insertar_boletin(
    conn: psycopg.Connection,
    generado_por: uuid.UUID,
    *,
    semana: int = 42,
    anio: int = 2024,
    nivel_alerta_global: str = "amarillo",
    publicado: bool = False,
) -> uuid.UUID:
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into boletines
                (semana, anio, markdown, hallazgos_json, nivel_alerta_global, recomendacion, publicado, generado_por)
            values (%s, %s, %s, %s, %s, %s, %s, %s)
            returning id
            """,
            (
                semana,
                anio,
                "## Estado de presas\n## Precipitación\n## Temperatura\n## Alerta y recomendación\n",
                json.dumps({}),
                nivel_alerta_global,
                "Recomendación de prueba",
                publicado,
                generado_por,
            ),
        )
        return cur.fetchone()[0]


def como_rol(conn: psycopg.Connection, rol: str, auth_user_id: uuid.UUID | None = None) -> None:
    """Simula, dentro de la transacción actual, una petición autenticada como ``rol``."""

    with conn.cursor() as cur:
        cur.execute(psycopg.sql.SQL("set local role {}").format(psycopg.sql.Identifier(rol)))
        if auth_user_id is not None:
            cur.execute("select set_config('request.jwt.claim.sub', %s, true)", (str(auth_user_id),))
