<!-- specs/F-003-guardia-bases-cruzadas/tasks.md -->
# F-003 · Tareas

- [ ] T1: Escribir `tests/test_database_reference_guard.py` con los casos de R3, R4, R5 y R11 (1-2 partes se ignoran; 3 partes devuelven la base; 4 partes rechazan; corchetes, comillas, `base..tabla`, capitalización mezclada; literales y comentarios que no deben confundir). Todos en ROJO.  |  Verificación: `python -m pytest tests/test_database_reference_guard.py` falla por módulo inexistente
- [ ] T2: Crear `infrastructure/security/database_reference_guard.py` con `DatabaseReferenceError`, `extract_database_references()` y `validate()`, incluida la neutralización de literales y comentarios.  |  Verificación: `python -m pytest tests/test_database_reference_guard.py` en verde
- [ ] T3: Escribir `tests/test_sql_write_guard_bases.py` (R1, R2, R6): rechazo de `INSERT INTO ruesma_rep.dbo.gra ...` con `database: "ruesma"`; aceptación de `INSERT INTO ruesma.dbo.gra ...` y de `INSERT INTO dbo.gra ...`; el mensaje nombra la base y la lista. En ROJO.  |  Verificación: `python -m pytest tests/test_sql_write_guard_bases.py` falla
- [ ] T4: Enganchar el detector en `SqlWriteGuard._validate_statement()`.  |  Verificación: `python -m pytest tests/test_sql_write_guard_bases.py` en verde
- [ ] T5: Escribir `tests/test_sql_query_guard_bases.py` (R7, R8) en ROJO y enganchar el detector en `SqlQueryGuard.validate()`.  |  Verificación: `python -m pytest tests/test_sql_query_guard_bases.py` en verde
- [ ] T6: Comprobar que no hay regresión en la suite completa (R10).  |  Verificación: `python -m pytest -q` en verde, con los 341 tests previos incluidos
- [ ] T7: Revisar `scripts/` en busca de consultas con nombres de tres partes que hoy funcionen y quedarían rechazadas; si alguna aparece, anotarla en `progress/impl_F-003.md` y decidir antes de cerrar.  |  Verificación: `grep -rniE "(ruesma|ruesma_rep|master)\.[a-z_]*\." scripts/` revisado uno a uno
- [ ] T8: **MANUAL** — con el humano: ejecutar una consulta real de un script contra la API desplegada y comprobar que sigue respondiendo igual.  |  Verificación: salida del script comparada con la anterior
- [ ] T9: Documentar la defensa en `docs/ARCHITECTURE.md` (sección de acceso a datos) y en `azure-apps/sigrid_api.md` §5, donde hoy se afirma que la lista blanca de bases protege la documental.  |  Verificación: el reviewer comprueba que lo escrito coincide con el código
- [ ] T10: Ejecutar `bash harness/init.sh` en verde.  |  Verificación: termina en ENTORNO LISTO
