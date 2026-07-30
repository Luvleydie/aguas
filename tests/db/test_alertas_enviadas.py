from __future__ import annotations

import uuid

import psycopg
import pytest

from tests.db.conftest import como_rol, insertar_boletin, insertar_usuario, requiere_supabase


def _insertar_alerta(conn: psycopg.Connection, boletin_id, usuario_id, canal: str = "web"):
    with conn.cursor() as cur:
        cur.execute(
            "insert into alertas_enviadas (boletin_id, usuario_id, canal) values (%s, %s, %s) returning id",
            (boletin_id, usuario_id, canal),
        )
        return cur.fetchone()[0]


@requiere_supabase
def test_insertar_alerta_valida_existe(pg_conn, make_auth_user):
    gobierno = make_auth_user()
    gobierno_id = insertar_usuario(pg_conn, gobierno.id, gobierno.email, "Gobierno", "gobierno")
    boletin_id = insertar_boletin(pg_conn, gobierno_id, semana=40, anio=2024)

    destinatario = make_auth_user()
    destinatario_id = insertar_usuario(pg_conn, destinatario.id, destinatario.email, "Destinatario", "agricultor")

    alerta_id = _insertar_alerta(pg_conn, boletin_id, destinatario_id)

    with pg_conn.cursor() as cur:
        cur.execute("select canal, estado from alertas_enviadas where id = %s", (alerta_id,))
        assert cur.fetchone() == ("web", "pendiente")


@requiere_supabase
def test_insertar_alerta_con_usuario_inexistente_falla(pg_conn, make_auth_user):
    gobierno = make_auth_user()
    gobierno_id = insertar_usuario(pg_conn, gobierno.id, gobierno.email, "Gobierno", "gobierno")
    boletin_id = insertar_boletin(pg_conn, gobierno_id, semana=41, anio=2024)

    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        _insertar_alerta(pg_conn, boletin_id, uuid.uuid4())


@requiere_supabase
def test_insertar_alerta_whatsapp_sin_opt_in_falla(pg_conn, make_auth_user):
    gobierno = make_auth_user()
    gobierno_id = insertar_usuario(pg_conn, gobierno.id, gobierno.email, "Gobierno", "gobierno")
    boletin_id = insertar_boletin(pg_conn, gobierno_id, semana=42, anio=2024)

    destinatario = make_auth_user()
    destinatario_id = insertar_usuario(pg_conn, destinatario.id, destinatario.email, "Sin opt-in", "agricultor")

    with pytest.raises(psycopg.Error, match="whatsapp"):
        _insertar_alerta(pg_conn, boletin_id, destinatario_id, canal="whatsapp")


@requiere_supabase
def test_insertar_alerta_whatsapp_con_opt_in_funciona(pg_conn, make_auth_user):
    gobierno = make_auth_user()
    gobierno_id = insertar_usuario(pg_conn, gobierno.id, gobierno.email, "Gobierno", "gobierno")
    boletin_id = insertar_boletin(pg_conn, gobierno_id, semana=43, anio=2024)

    destinatario = make_auth_user()
    destinatario_id = insertar_usuario(pg_conn, destinatario.id, destinatario.email, "Con opt-in", "agricultor")
    with pg_conn.cursor() as cur:
        cur.execute("update usuarios set recibir_whatsapp = true where id = %s", (destinatario_id,))

    alerta_id = _insertar_alerta(pg_conn, boletin_id, destinatario_id, canal="whatsapp")

    assert alerta_id is not None


@requiere_supabase
def test_rls_usuario_solo_ve_sus_alertas(pg_conn, make_auth_user):
    gobierno = make_auth_user()
    gobierno_id = insertar_usuario(pg_conn, gobierno.id, gobierno.email, "Gobierno", "gobierno")
    boletin_id = insertar_boletin(pg_conn, gobierno_id, semana=44, anio=2024)

    propio = make_auth_user()
    propio_id = insertar_usuario(pg_conn, propio.id, propio.email, "Propio", "agricultor")
    ajeno = make_auth_user()
    ajeno_id = insertar_usuario(pg_conn, ajeno.id, ajeno.email, "Ajeno", "agricultor")

    mi_alerta_id = _insertar_alerta(pg_conn, boletin_id, propio_id)
    _insertar_alerta(pg_conn, boletin_id, ajeno_id)

    como_rol(pg_conn, "authenticated", propio.id)
    with pg_conn.cursor() as cur:
        cur.execute("select id from alertas_enviadas")
        assert {fila[0] for fila in cur.fetchall()} == {mi_alerta_id}


@requiere_supabase
def test_rls_usuario_normal_no_puede_insertar_alerta(pg_conn, make_auth_user):
    gobierno = make_auth_user()
    gobierno_id = insertar_usuario(pg_conn, gobierno.id, gobierno.email, "Gobierno", "gobierno")
    boletin_id = insertar_boletin(pg_conn, gobierno_id, semana=45, anio=2024)

    usuario = make_auth_user()
    usuario_id = insertar_usuario(pg_conn, usuario.id, usuario.email, "Agricultor", "agricultor")

    como_rol(pg_conn, "authenticated", usuario.id)
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        _insertar_alerta(pg_conn, boletin_id, usuario_id)
