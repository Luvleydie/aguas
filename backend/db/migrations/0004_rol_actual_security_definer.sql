-- rol_actual() consultaba `usuarios` sin SECURITY DEFINER. Como esa misma
-- tabla tiene RLS que a su vez invoca rol_actual() (usuarios_select_propio:
-- "auth_user_id = auth.uid() or rol_actual() = 'gobierno'"), cualquier
-- evaluación de la rama OR disparaba recursión infinita
-- (Postgres: "statement too complex"). Con SECURITY DEFINER la consulta
-- interna corre como el dueño de la función (que es dueño de la tabla y por
-- tanto no está sujeto a su propio RLS), rompiendo la recursión — mismo
-- patrón que .agents/skills/supabase-postgres-best-practices/references/
-- security-rls-performance.md recomienda para estos helpers.
--
-- Encontrado por TDD: 8 de los tests de RLS en tests/db/ fallaban con
-- psycopg.errors.StatementTooComplex antes de esta migración.

create or replace function rol_actual() returns rol_usuario
language sql
stable
security definer
set search_path = public, pg_temp
as $$
    select rol from usuarios where auth_user_id = auth.uid();
$$;
