from __future__ import annotations

import uuid

import psycopg
import pytest

from tests.db.conftest import como_rol, insertar_usuario, requiere_supabase


@requiere_supabase
def test_insertar_usuario_valido_existe(pg_conn, make_auth_user):
    auth_user = make_auth_user()
    usuario_id = insertar_usuario(pg_conn, auth_user.id, auth_user.email, "Prueba Válida", "ayuntamiento")

    with pg_conn.cursor() as cur:
        cur.execute("select nombre, rol, recibir_whatsapp from usuarios where id = %s", (usuario_id,))
        assert cur.fetchone() == ("Prueba Válida", "ayuntamiento", False)


@requiere_supabase
def test_insertar_usuario_con_auth_user_id_inexistente_viola_fk(pg_conn):
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        insertar_usuario(pg_conn, uuid.uuid4(), "fantasma@hidroalerta.test", "Fantasma", "gobierno")


@requiere_supabase
def test_insertar_usuario_con_email_duplicado_falla(pg_conn, make_auth_user):
    a = make_auth_user()
    b = make_auth_user()
    insertar_usuario(pg_conn, a.id, "duplicado@hidroalerta.test", "Uno", "agricultor")
    with pytest.raises(psycopg.errors.UniqueViolation):
        insertar_usuario(pg_conn, b.id, "duplicado@hidroalerta.test", "Dos", "agricultor")


@requiere_supabase
def test_insertar_usuario_con_rol_invalido_falla(pg_conn, make_auth_user):
    auth_user = make_auth_user()
    with pytest.raises(psycopg.errors.InvalidTextRepresentation):
        insertar_usuario(pg_conn, auth_user.id, auth_user.email, "Rol inventado", "superadmin")


@requiere_supabase
def test_rls_usuario_no_ve_fila_de_otro_usuario(pg_conn, make_auth_user):
    propio = make_auth_user()
    ajeno = make_auth_user()
    insertar_usuario(pg_conn, propio.id, propio.email, "Yo", "ayuntamiento")
    insertar_usuario(pg_conn, ajeno.id, ajeno.email, "Otro", "ayuntamiento")

    como_rol(pg_conn, "authenticated", propio.id)
    with pg_conn.cursor() as cur:
        cur.execute("select auth_user_id from usuarios")
        filas = {fila[0] for fila in cur.fetchall()}

    assert filas == {propio.id}


@requiere_supabase
def test_rls_gobierno_ve_todos_los_usuarios(pg_conn, make_auth_user):
    admin = make_auth_user()
    otro = make_auth_user()
    insertar_usuario(pg_conn, admin.id, admin.email, "Gobierno", "gobierno")
    insertar_usuario(pg_conn, otro.id, otro.email, "Cualquiera", "agricultor")

    como_rol(pg_conn, "authenticated", admin.id)
    with pg_conn.cursor() as cur:
        cur.execute("select auth_user_id from usuarios")
        filas = {fila[0] for fila in cur.fetchall()}

    assert {admin.id, otro.id} <= filas


@requiere_supabase
def test_rls_anonimo_no_ve_usuarios(pg_conn, make_auth_user):
    alguien = make_auth_user()
    insertar_usuario(pg_conn, alguien.id, alguien.email, "Alguien", "agricultor")

    como_rol(pg_conn, "anon")
    with pg_conn.cursor() as cur:
        cur.execute("select id from usuarios")
        assert cur.fetchall() == []
