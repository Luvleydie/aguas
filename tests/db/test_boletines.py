from __future__ import annotations

import json

import psycopg
import pytest

from tests.db.conftest import como_rol, insertar_boletin, insertar_usuario, requiere_supabase


@requiere_supabase
def test_insertar_boletin_valido_existe(pg_conn, make_auth_user):
    autor = make_auth_user()
    autor_id = insertar_usuario(pg_conn, autor.id, autor.email, "Autora", "gobierno")

    boletin_id = insertar_boletin(pg_conn, autor_id, semana=42, anio=2024)

    with pg_conn.cursor() as cur:
        cur.execute("select semana, anio, publicado from boletines where id = %s", (boletin_id,))
        assert cur.fetchone() == (42, 2024, False)


@requiere_supabase
def test_boletin_semana_fuera_de_rango_falla(pg_conn, make_auth_user):
    autor = make_auth_user()
    autor_id = insertar_usuario(pg_conn, autor.id, autor.email, "Autora", "gobierno")
    with pytest.raises(psycopg.errors.CheckViolation):
        insertar_boletin(pg_conn, autor_id, semana=99)


@requiere_supabase
def test_boletin_duplicado_semana_anio_falla(pg_conn, make_auth_user):
    autor = make_auth_user()
    autor_id = insertar_usuario(pg_conn, autor.id, autor.email, "Autora", "gobierno")
    insertar_boletin(pg_conn, autor_id, semana=10, anio=2024)
    with pytest.raises(psycopg.errors.UniqueViolation):
        insertar_boletin(pg_conn, autor_id, semana=10, anio=2024)


@requiere_supabase
def test_boletin_sin_generado_por_falla(pg_conn):
    with pg_conn.cursor() as cur:
        with pytest.raises(psycopg.errors.NotNullViolation):
            cur.execute(
                """
                insert into boletines (semana, anio, markdown, hallazgos_json, nivel_alerta_global, recomendacion)
                values (1, 2024, 'x', %s, 'verde', 'x')
                """,
                (json.dumps({}),),
            )


@requiere_supabase
def test_rls_publico_solo_ve_boletines_publicados(pg_conn, make_auth_user):
    autor = make_auth_user()
    autor_id = insertar_usuario(pg_conn, autor.id, autor.email, "Autora", "gobierno")
    publicado_id = insertar_boletin(pg_conn, autor_id, semana=1, anio=2024, publicado=True)
    insertar_boletin(pg_conn, autor_id, semana=2, anio=2024, publicado=False)

    como_rol(pg_conn, "anon")
    with pg_conn.cursor() as cur:
        cur.execute("select id from boletines")
        filas = {fila[0] for fila in cur.fetchall()}

    assert filas == {publicado_id}


@requiere_supabase
def test_rls_gobierno_ve_boletines_no_publicados(pg_conn, make_auth_user):
    admin = make_auth_user()
    admin_id = insertar_usuario(pg_conn, admin.id, admin.email, "Gobierno", "gobierno")
    borrador_id = insertar_boletin(pg_conn, admin_id, semana=3, anio=2024, publicado=False)

    como_rol(pg_conn, "authenticated", admin.id)
    with pg_conn.cursor() as cur:
        cur.execute("select id from boletines where id = %s", (borrador_id,))
        assert cur.fetchone() is not None


@requiere_supabase
def test_rls_solo_gobierno_puede_insertar_boletin(pg_conn, make_auth_user):
    ayuntamiento = make_auth_user()
    insertar_usuario(pg_conn, ayuntamiento.id, ayuntamiento.email, "Ayuntamiento", "ayuntamiento")

    como_rol(pg_conn, "authenticated", ayuntamiento.id)
    with pg_conn.cursor() as cur:
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            cur.execute(
                """
                insert into boletines (semana, anio, markdown, hallazgos_json, nivel_alerta_global, recomendacion, generado_por)
                values (5, 2024, 'x', %s, 'verde', 'x', (select id from usuarios where auth_user_id = %s))
                """,
                (json.dumps({}), ayuntamiento.id),
            )
