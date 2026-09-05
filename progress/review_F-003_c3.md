# progress/review_F-003_c3.md

# F-003 · Revisión acotada C3 / C3 bis

Revisión completa del diff `dev...HEAD` (20 ficheros), **acotada por encargo**
a los checkpoints C3 y C3 bis. No se ejecuta `init.sh` ni la suite (campaña de
mutación en curso en paralelo); revisión de solo lectura.

**Veredicto (C3/C3 bis): APROBADO.**

## C3 — Arquitectura y convenciones

- [x] **Arquitectura hexagonal.** `DatabaseReferenceGuard`
  (`infrastructure/security/database_reference_guard.py`) es un módulo puro:
  sin `Settings`, sin I/O, recibe la lista blanca por argumento — tal como
  fija `design.md` ("módulo puro y trivial de testear"). Sus dos consumidores
  (`sql_query_guard.py`, `sql_write_guard.py`) siguen en `infrastructure/`.
  Dominio no tocado. `scripts/verificar_sql_ecosistema.py` es un script suelto
  de diagnóstico contra ficheros locales (no contra la API desplegada ni la
  BBDD), coherente con el resto de `scripts/`.
- [x] **Primera línea con ruta relativa.** Comprobado en los 4 ficheros de
  producción/script (`database_reference_guard.py`,
  `sql_query_guard.py`, `sql_write_guard.py`,
  `scripts/verificar_sql_ecosistema.py`) y en los 4 ficheros de test nuevos.
  Todos correctos.
- [x] **Sin `print()` de debug, sin TODO sin contexto, sin secretos.**
  Grep en los tres ficheros de `infrastructure/security/` tocados: cero
  coincidencias de `print(`, `TODO`, `FIXME`, `password`, `secret`. El único
  `print()` del diff vive en `scripts/verificar_sql_ecosistema.py`, que es
  script puntual (permitido por `CONVENTIONS.md`), no código de producción.
  Sin dependencias nuevas: los únicos imports añadidos son `re` y
  `types.MappingProxyType` (stdlib) — coincide con `design.md`, que descarta
  explícitamente `sqlglot`.
- [x] **Diff de los dos guardias exactamente el previsto.** `git diff
  dev...HEAD -- sql_query_guard.py sql_write_guard.py` muestra solo el import
  de `DatabaseReferenceGuard`/`DatabaseReferenceError` y una llamada a
  `.validate(...)` al final de la validación existente, en cada guardia. Nada
  más se toca — tal como exige `design.md` ("No se toca nada más de la
  clase").
- [x] **Reglas de dominio Sigrid — trampas vigiladas:**
  - **Base correcta (`ruesma` vs `ruesma_rep`).** Es el objeto mismo de la
    feature: cierra exactamente el agujero de escribir en `ruesma_rep` con
    `database: "ruesma"` citando el nombre dentro del SQL. `ruesma_rep` sigue
    fuera de `ALLOWED_WRITE_DATABASES` (no se toca `config/settings.py`, y el
    diseño lo deja escrito a propósito: "no se añade ninguna variable de
    entorno").
  - `cod`/`res`/`fec`/`tip`/`est` en `con`, no en extensión: **N/A** — el
    guardia no construye SQL, solo analiza el que llega; no inserta columnas.
  - Recalcular totales/`canser`/PMP: **N/A** — la feature no escribe datos,
    es una validación previa a la ejecución.
  - Estados no hardcodeados: **N/A** — no hay lógica de estados aquí.
  - SQL parametrizado con `?`: **N/A** — el guardia no emite SQL, lo recibe y
    lo analiza como texto.

## C3 bis — Documentos que entran de fuera

**N/A, justificado.** El diff no toca `docs/referencia/` (ver `git diff
dev...HEAD --stat`): no hay documento nuevo, no hay PDF/ofimática, nada que
barrer por datos sensibles. `docs/ARCHITECTURE.md` sí se modifica (+8 líneas),
pero es documentación normativa del propio repo, no un documento externo — no
es objeto de C3 bis. Comprobado también que `docs/ARCHITECTURE.md` describe
correctamente el comportamiento implementado (doble aplicación de listas
blancas, rechazo de 4+ partes, lectura cruzada permitida): coincide con el
código.

## Sobre la familia de fallos ya corregida (neutralizador vs. reconocedor)

Se leyó `database_reference_guard.py` completo buscando un séptimo caso de esa
familia (delimitador leído con reglas distintas en `_neutralizar_literales_y_
comentarios` vs. `_IDENT`/`_partir`). Los dos puntos de entrada para
identificadores delimitados (`[`→`]` y `"`→`"`, con sus escapes `]]`/`""`)
están unificados en `_APERTURA_DE_DELIMITADO` y se usan literalmente igual en
el reconocedor (`_IDENT`) y en `_partir`. No encontré un séptimo caso ni SQL
que lo demuestre; no lo afirmo como ausencia probada, solo que la lectura no
lo encontró. Fuera de mi ámbito profundizar más (no es objeto de C3).

## Nota fuera de ámbito (no bloquea C3)

`scripts/verificar_sql_ecosistema.py` hardcodea `ALLOWED_DATABASES`/
`ALLOWED_WRITE_DATABASES` como copia de la configuración desplegada en vez de
leerlas de `config/settings.py`. Es deliberado (compara contra lo
desplegado, no contra el `.env` local) y está documentado en el propio
fichero, pero es una lista que se puede desincronizar de la real con el
tiempo. No es un incumplimiento de C3; queda anotado para quien revise C4/C5.
