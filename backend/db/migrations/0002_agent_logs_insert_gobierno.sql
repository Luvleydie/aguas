-- 0001_init_schema.sql solo definió SELECT para agent_logs (gobierno). El
-- backend (backend/main.py::generar_boletin) inserta el rastro de auditoría
-- con el token del propio usuario gobierno que disparó el pipeline, no con
-- la service key, así que necesita también INSERT.
-- Encontrado por TDD: tests/db/test_agent_logs.py::test_rls_gobierno_puede_insertar_agent_log
-- estaba en rojo contra el schema recién aplicado.

create policy agent_logs_insert_gobierno
    on agent_logs
    for insert
    with check (rol_actual() = 'gobierno');
