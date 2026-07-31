from __future__ import annotations

import json

import psycopg
import pytest

from tests.db.conftest import como_rol, insertar_boletin, insertar_usuario, requiere_supabase


def _insertar_log(conn: psycopg.Connection, boletin_id, agente: str = "explorador"):
    with conn.cursor() as cur:
        cur.execute(
            "insert into agent_logs (boletin_id, agente, mensaje) values (%s, %s, %s) returning id",
            (boletin_id, agente, json.dumps({"ok": True})),
        )
        return cur.fetchone()[0]


@requiere_supabase
def test_insertar_agent_log_valido_existe(pg_conn, make_auth_user):
    autor = make_auth_user()
    autor_id = insertar_usuario(pg_conn, autor.id, autor.email, "Autora", "gobierno")
    boletin_id = insertar_boletin(pg_conn, autor_id, semana=20, anio=2024)

    log_id = _insertar_log(pg_conn, boletin_id, "estadista")

    with pg_conn.cursor() as cur:
        cur.execute("select agente, mensaje from agent_logs where id = %s", (log_id,))
        assert cur.fetchone() == ("estadista", {"ok": True})


@requiere_supabase
def test_agent_log_con_boletin_inexistente_falla(pg_conn):
    import uuid

    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        _insertar_log(pg_conn, uuid.uuid4())


@requiere_supabase
def test_agent_log_con_agente_invalido_falla(pg_conn, make_auth_user):
    autor = make_auth_user()
    autor_id = insertar_usuario(pg_conn, autor.id, autor.email, "Autora", "gobierno")
    boletin_id = insertar_boletin(pg_conn, autor_id, semana=21, anio=2024)

    with pytest.raises(psycopg.errors.CheckViolation):
        _insertar_log(pg_conn, boletin_id, agente="inventado")


@requiere_supabase
def test_rls_no_gobierno_no_ve_agent_logs(pg_conn, make_auth_user):
    autor = make_auth_user()
    autor_id = insertar_usuario(pg_conn, autor.id, autor.email, "Autora", "gobierno")
    boletin_id = insertar_boletin(pg_conn, autor_id, semana=22, anio=2024)
    _insertar_log(pg_conn, boletin_id)

    agricultor = make_auth_user()
    insertar_usuario(pg_conn, agricultor.id, agricultor.email, "Agricultor", "agricultor")

    como_rol(pg_conn, "authenticated", agricultor.id)
    with pg_conn.cursor() as cur:
        cur.execute("select id from agent_logs where boletin_id = %s", (boletin_id,))
        assert cur.fetchall() == []


@requiere_supabase
def test_rls_gobierno_ve_agent_logs(pg_conn, make_auth_user):
    admin = make_auth_user()
    admin_id = insertar_usuario(pg_conn, admin.id, admin.email, "Gobierno", "gobierno")
    boletin_id = insertar_boletin(pg_conn, admin_id, semana=23, anio=2024)
    _insertar_log(pg_conn, boletin_id)

    como_rol(pg_conn, "authenticated", admin.id)
    with pg_conn.cursor() as cur:
        cur.execute("select id from agent_logs where boletin_id = %s", (boletin_id,))
        assert len(cur.fetchall()) == 1


@requiere_supabase
def test_rls_gobierno_puede_insertar_agent_log(pg_conn, make_auth_user):
    """El backend inserta agent_logs con el token del gobierno que disparó el
    pipeline (backend/main.py::generar_boletin), no con la service key."""
    admin = make_auth_user()
    admin_id = insertar_usuario(pg_conn, admin.id, admin.email, "Gobierno", "gobierno")
    boletin_id = insertar_boletin(pg_conn, admin_id, semana=24, anio=2024)

    como_rol(pg_conn, "authenticated", admin.id)
    log_id = _insertar_log(pg_conn, boletin_id)

    assert log_id is not None
