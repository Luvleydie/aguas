-- La política original de 0001_init_schema.sql solo exigía
-- rol_actual() = 'ayuntamiento' al insertar en acciones_ayuntamiento, sin
-- atar `usuario_id` al auth.uid() de quien hace la petición: cualquier
-- usuario con rol ayuntamiento podía registrar una acción a nombre de otro.
-- Encontrado por TDD: tests/db/test_acciones_ayuntamiento.py::
-- test_rls_ayuntamiento_no_puede_suplantar_a_otro_usuario_al_insertar
-- (ya señalado como riesgo conocido al implementar backend/main.py, que sí
-- fuerza usuario_id = usuario autenticado a nivel API, pero la base de datos
-- debía exigirlo también).

drop policy if exists acciones_insert_ayuntamiento on acciones_ayuntamiento;

create policy acciones_insert_ayuntamiento
    on acciones_ayuntamiento
    for insert
    with check (
        rol_actual() = 'ayuntamiento'
        and usuario_id in (select id from usuarios where auth_user_id = auth.uid())
    );
