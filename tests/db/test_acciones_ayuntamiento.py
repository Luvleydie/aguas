from __future__ import annotations

import uuid

import psycopg
import pytest

from tests.db.conftest import como_rol, insertar_boletin, insertar_usuario, requiere_supabase


def _insertar_accion(conn: psycopg.Connection, boletin_id, usuario_id, accion: str = "campaña de ahorro"):
    with conn.cursor() as cur:
        cur.execute(
            "insert into acciones_ayuntamiento (boletin_id, usuario_id, accion) values (%s, %s, %s) returning id",
            (boletin_id, usuario_id, accion),
        )
        return cur.fetchone()[0]


@requiere_supabase
def test_insertar_accion_valida_existe(pg_conn, make_auth_user):
    gobierno = make_auth_user()
    gobierno_id = insertar_usuario(pg_conn, gobierno.id, gobierno.email, "Gobierno", "gobierno")
    boletin_id = insertar_boletin(pg_conn, gobierno_id, semana=30, anio=2024)

    ayuntamiento = make_auth_user()
    ayuntamiento_id = insertar_usuario(pg_conn, ayuntamiento.id, ayuntamiento.email, "Ayuntamiento", "ayuntamiento")

    accion_id = _insertar_accion(pg_conn, boletin_id, ayuntamiento_id)

    with pg_conn.cursor() as cur:
        cur.execute("select accion from acciones_ayuntamiento where id = %s", (accion_id,))
        assert cur.fetchone() == ("campaña de ahorro",)


@requiere_supabase
def test_insertar_accion_con_usuario_inexistente_falla(pg_conn, make_auth_user):
    gobierno = make_auth_user()
    gobierno_id = insertar_usuario(pg_conn, gobierno.id, gobierno.email, "Gobierno", "gobierno")
    boletin_id = insertar_boletin(pg_conn, gobierno_id, semana=31, anio=2024)

    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        _insertar_accion(pg_conn, boletin_id, uuid.uuid4())


@requiere_supabase
def test_rls_ayuntamiento_no_ve_acciones_de_otro(pg_conn, make_auth_user):
    gobierno = make_auth_user()
    gobierno_id = insertar_usuario(pg_conn, gobierno.id, gobierno.email, "Gobierno", "gobierno")
    boletin_id = insertar_boletin(pg_conn, gobierno_id, semana=33, anio=2024)

    propio = make_auth_user()
    propio_id = insertar_usuario(pg_conn, propio.id, propio.email, "Propio", "ayuntamiento")
    ajeno = make_auth_user()
    ajeno_id = insertar_usuario(pg_conn, ajeno.id, ajeno.email, "Ajeno", "ayuntamiento")

    mi_accion_id = _insertar_accion(pg_conn, boletin_id, propio_id)
    _insertar_accion(pg_conn, boletin_id, ajeno_id)

    como_rol(pg_conn, "authenticated", propio.id)
    with pg_conn.cursor() as cur:
        cur.execute("select id from acciones_ayuntamiento")
        assert {fila[0] for fila in cur.fetchall()} == {mi_accion_id}


@requiere_supabase
def test_rls_agricultor_no_puede_crear_accion(pg_conn, make_auth_user):
    gobierno = make_auth_user()
    gobierno_id = insertar_usuario(pg_conn, gobierno.id, gobierno.email, "Gobierno", "gobierno")
    boletin_id = insertar_boletin(pg_conn, gobierno_id, semana=34, anio=2024)

    agricultor = make_auth_user()
    agricultor_id = insertar_usuario(pg_conn, agricultor.id, agricultor.email, "Agricultor", "agricultor")

    como_rol(pg_conn, "authenticated", agricultor.id)
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        _insertar_accion(pg_conn, boletin_id, agricultor_id)


@requiere_supabase
def test_rls_ayuntamiento_no_puede_suplantar_a_otro_usuario_al_insertar(pg_conn, make_auth_user):
    """Hallazgo del punto 5 (API): la política original solo exigía
    rol_actual() = 'ayuntamiento', sin atar usuario_id al auth.uid() de quien
    inserta. Este test debe quedar en rojo hasta aplicar la migración que lo
    corrige."""
    gobierno = make_auth_user()
    gobierno_id = insertar_usuario(pg_conn, gobierno.id, gobierno.email, "Gobierno", "gobierno")
    boletin_id = insertar_boletin(pg_conn, gobierno_id, semana=35, anio=2024)

    atacante = make_auth_user()
    insertar_usuario(pg_conn, atacante.id, atacante.email, "Atacante", "ayuntamiento")
    victima = make_auth_user()
    victima_id = insertar_usuario(pg_conn, victima.id, victima.email, "Víctima", "ayuntamiento")

    como_rol(pg_conn, "authenticated", atacante.id)
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        _insertar_accion(pg_conn, boletin_id, victima_id)


@requiere_supabase
def test_rls_gobierno_ve_todas_las_acciones(pg_conn, make_auth_user):
    gobierno = make_auth_user()
    gobierno_id = insertar_usuario(pg_conn, gobierno.id, gobierno.email, "Gobierno", "gobierno")
    boletin_id = insertar_boletin(pg_conn, gobierno_id, semana=36, anio=2024)

    ayuntamiento = make_auth_user()
    ayuntamiento_id = insertar_usuario(pg_conn, ayuntamiento.id, ayuntamiento.email, "Ayuntamiento", "ayuntamiento")
    _insertar_accion(pg_conn, boletin_id, ayuntamiento_id)

    como_rol(pg_conn, "authenticated", gobierno.id)
    with pg_conn.cursor() as cur:
        cur.execute("select count(*) from acciones_ayuntamiento")
        assert cur.fetchone()[0] >= 1
