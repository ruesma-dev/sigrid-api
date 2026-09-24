# F-006 · Revisión acotada: C3 y corrección funcional del código

Revisión completa (pasada 1) de `dev..22ba2a5` (HEAD `22ba2a5474890a3e5e2c8a0a0d778c0f52480c2f`), acotada a
C3 y a la corrección del código frente a `design.md` y `explore_F-006_modelo_parte.md`. Reviewer, 2026-09-25.
Sin `init.sh` ni la suite completa (hay otros revisores en paralelo): `pytest -k f006` → **229 passed**.
Contra el ERP solo dos `sql/read` (columnas/índices de las cinco tablas y semántica del `LIKE`).
Pruebas propias del reviewer: `scratchpad/test_revision_f006.py`, **12 de 12 en verde** (la 13.ª, fallida a propósito, era una sonda del log).

## Veredicto parcial

**APROBADO.** Ningún hallazgo bloqueante. Hay 2 menores y 6 observaciones, que se pueden cerrar después (abajo).

## 1 · Filas (R11): conformes con design §Filas y con la exploración

Los números de línea son de `application/use_cases/parte_reclamacion_statements.py` (PRS) y de `create_partes_reclamacion_use_case.py` (UC).

| Punto | Evidencia | ✓ |
|---|---|---|
| Columnas 19/20/5/11/14, en su orden físico | PRS:57-74; se cruzan con `INFORMATION_SCHEMA` (tipos y longitudes: `res` 128, `valt` 80, `resubi` 48, `log.usu` 48, `rcp.tex` `text`) | [x] |
| Constantes de `con`, `rcp`, `rcpint`, `conext`, `log` | PRS:321-402, una a una contra la tabla del design | [x] |
| `tiemod` es una fecha OLE en UTC | PRS:77, 112-120; prueba propia: 2026-08-04 08:41:29 UTC → 46238.362141, **igual a lo medido en 2811304**, y `hor` 104129 | [x] |
| `rcp.pos` = MAX+64 global, bajo UPDLOCK/HOLDLOCK | PRS:183 (E4), UC:608 | [x] |
| `rcpint.pos` vale 0 | PRS:368 | [x] |
| `cliide`/`recide` salen de la UPV con `ISNULL(...,0)` | PRS:156 (L5), UC:354-358, 501-502 | [x] |
| `rcptip` 1 por defecto y tipo `0002` por defecto | modelo:104, 108; UC:459, 504 | [x] |
| `emp` y `est` salen de `sercon` y se validan en `conest`, sin escribirlos a mano | UC:319-336; `est` = `estini`, comprobado contra `conest` | [x] |
| En `log`, `fec`/`hor`/`cod`/`res`/`est` son los del parte | PRS:387-402 y `numerar` PRS:421, 428 | [x] |

## 2 · Transacción por parte (R11-R13, R16)

- **Orden E1→E14**: UC:596-655. Hace E1, luego E2-E7 (E5 solo si hay intervinientes), E8, los INSERT `con`→`rcp`→`rcpint`×N→`conext`→`log` y las cinco relecturas. [x]
- **Applocks**: siguen el orden del design al pie de la letra (UC:57-65). El repositorio los toma todos **antes** de `work` (`sql_server_repository.py:283-297`). Albaranes y concepto-grafico solo comparten `SIGRID_IDE_con`, y ninguno toma después un applock que aquí vaya antes, así que no hay orden inverso. [x]
- **`cod` e `ide` se reservan dentro de la transacción** con `UPDLOCK, HOLDLOCK` (PRS:178-186). Leídos los índices en `sys.indexes`: `con_indide`, `rcp_posupvide`, `rcpint_indide`, `conext_indide` y `log_indide` existen todos, así que cada `MAX` es un seek y no un barrido: no hay escalado de bloqueos en `log`, que es un HEAP de 8,5 M filas. [x]
- **Patrón `LIKE`**: `RS26.09/[0-9][0-9][0-9][0-9]` (prueba propia). Ni `.` ni `/` son comodines en T-SQL, y el prefijo no lleva `%`, `_` ni `[`. [x] (ver M2)
- **Números**: 9998 da 9999, 9999 da `numeracion_agotada`, y `None` da `0001` (prueba propia; PRS:100-109). [x]
- **Reentrada y reintento**: `numerar` copia las filas y no toca `plan.filas` (PRS:420-429). Prueba propia: con un `IntegrityError` en el primer intento, `cod` y `ide` se recalculan (0773 y 2900003), y `ahora_utc` se llama **una sola vez** aunque en el intento 2 el reloj esté en el mes siguiente (R16). [x]
- **Cruce de fin de mes**: probado. Dos partes a las 23:59:59 y a las 00:00:01 de Madrid bloquean `RS26.09/` y `RS26.10/` respectivamente, con `fec` 20260930 y 20261001. [x]

## 3 · Idempotencia (R15)

- E1 es la **misma** sentencia L8, se ejecuta dentro de `work` y con todos los applocks tomados (UC:599-602). En dry-run, L8 va con credenciales de lectura (UC:403-408). [x]
- Otra UPV, o varias filas, dan `referencia_en_conflicto` sin llegar a ningún INSERT (prueba propia). Un parte sin `rcp` (`upvide` NULL) también da conflicto (UC:570). [x]
- Prefijo `PVI-`: `startswith`, que distingue mayúsculas y es por tanto más estricto (desviación 6). Las referencias duplicadas se comparan con `casefold`. L8 usa `=` (no `LIKE`) bajo la colación CI, así que los comodines no importan y los espacios de cola los quita el modelo. [x]

## 4 · Guardias del lote (R3, R10)

- Las llaves se comprueban **antes** de leer nada: `SIGRID_DOMAIN_WRITE_ENABLED`, `SIGRID_RECLAMACION_WRITE_ENABLED` y las dos credenciales (UC:196-197, 262-273). [x]
- Con `ALLOWED_WRITE_DATABASES` vacía, `database not in []` rechaza (UC:277). El defecto en código sigue siendo `[]` (settings:36). [x]
- El tope es `len > max`, y se comprueba antes de leer (UC:199-204). [x]
- El dry-run vuelve en UC:402-418 **antes** de `_escribir`. Solo usa `execute_read_query` y `peek_next_ide`, las dos con `_read_credentials` (repositorio:67, 203), y no llama a `run_in_write_transaction`. Lo confirma la prueba propia: `repo.transacciones == []`. [x]

## 5 · Reglas duras

- El SQL es constante y va con `?`. Las dos únicas f-strings son `POS_PASO` (64, una constante) y `_insert`, que se construye con tuplas de columnas constantes. El guardia `DatabaseReferenceGuard` valida las 30 sentencias en `__init__` (PRS:207-210). [x]
- No hay `UPDATE`, `DELETE`, `MERGE` ni DDL: `grep` sobre el diff sin tests da 0. [x]
- `infrastructure/security/` y el repositorio no aparecen en el diff. `function_app.py` y `settings.py` suman 0 líneas `-`, y en `local.settings.sample.json` solo cambia una coma. [x]

## 6 · Presupuesto, trazas y códigos

- El presupuesto se mide desde el arranque de `run`, así que incluye las lecturas comunes, y se comprueba antes de cada parte (UC:218-233). [x] (ver O5)
- Hay una traza por lote (obra, `usu`, `commit`, resumen, duración) y una por parte (referencia, estado, código, `ide`, `cod`). Ninguna lleva textos (UC:166-190). [x] (ver M1)
- Los códigos son conjuntos cerrados, validados en `ParteReclamacionError` y en `MotivoParte` (modelo:21-72, 154-159). [x]

## 7 · Desviaciones de `impl_F-006.md` §3

Ninguna contradice la spec ni cambia lo que se escribe en commit:

- La 2 (numeración del dry-run leída una vez) solo afecta al preview.
- La 3 (E5 solo con intervinientes) no reserva un `ide` que no se va a usar, y mantiene el orden de los applocks.
- La 5 detecta `IntegrityError` por su nombre de clase. Todas las columnas que reciben NULL son nullable, así que un 23000 solo puede ser de clave.
- La 6 y la 8 son más estrictas que la spec.
- La 7 (`committed`) sigue a F-004.
- La 9 (RM6) está verificada en el origen: L5 lleva `ISNULL(..., 0)` (PRS:156) y L6 conserva `pos or 0` (UC:361).

## 8 · Hallazgos

**Bloqueantes: ninguno.**

**M1 · Menor: el 400 de validación deja fragmentos de la descripción en el log.** Está en `function_app.py:355`, que hace `logger.warning("ValidationError ...: %s", exc)`. Con pydantic 2.11, `str(exc)` incluye `input_value`: probado con un parte sin `oficio` (sale el dict truncado con la descripción) y con otro de más de 128 caracteres. R20 acota «nunca descripciones» a las trazas del lote y de cada parte, y el design manda copiar el esqueleto de `concepto-grafico`, que hace lo mismo. Por eso no bloquea. Propuesta: en esta ruta, loguear `exc.errors(include_input=False)`. En las demás rutas sería una feature aparte.

**M2 · Menor: `[0-9]` también acepta superíndices con `Modern_Spanish_CI_AS`.** Medido por `sql/read`: `'RS26.09/000²' LIKE 'RS26.09/[0-9][0-9][0-9][0-9]'` da 1. Si alguien tecleara a mano un `cod` así, `int()` en `siguiente_cod` (PRS:102) lanzaría `ValueError`, y todo parte de ese mes saldría `error_de_escritura`, con rollback y sin daño. Hoy no hay ningún código mal formado: 0 filas `RS` que no casen en binario o con `DATALENGTH ≠ 12`. Se deja anotado; no pide cambio.

**Observaciones (ninguna pide cambio):**

- **O1.** La primera aparición de una referencia se la queda aunque ese parte se rechace por otro motivo, y el segundo parte, aunque sea válido, sale `referencia_duplicada_en_lote` (prueba propia). Es coherente con la desviación 6.
- **O2.** En commit, R7-R8 se validan antes de E1. Por eso, un reenvío después de que cambie la obra (por ejemplo, un oficio retirado) sale con el código de validación y no como `idempotente` (prueba propia). Es el orden de design §Flujo, y conviene que `postventa-incidencias` lo sepa.
- **O3.** `log.usu` guarda el `usu` tal como llega en la petición, no el `usu.cod` leído en L4. Con la colación CI no rompe nada; como mucho cambian las mayúsculas en el log.
- **O4.** El mensaje de `error_de_escritura` («se revirtió y no se ha escrito nada», UC:679) puede no ser cierto si lo que falla es el propio `commit()`, porque entonces el resultado es incierto. Reenviar es seguro gracias a la idempotencia, pero convendría suavizar el texto.
- **O5.** El presupuesto solo impide **empezar** partes. Un solo parte en contención puede pasar del margen de 80 s hasta el corte de 230 s: 7 applocks de hasta 10 s cada uno, más sentencias de 30 s, por 4 intentos. La idempotencia lo cubre.
- **O6.** Un deadlock (1205) no se reintenta: sale `error_de_escritura`, con rollback, y se puede reenviar. Los textos fuera de cp1252 (emojis, por ejemplo) llegan como `?` a columnas `varchar`/`text`. `forma_comunicacion: true` se acepta como 1 (pydantic en modo lax).

## 9 · C3 (`CHECKPOINTS.md`)

- [x] **Hexagonal.** El dominio solo importa pydantic. `application` importa `DatabaseReferenceGuard`, igual que el precedente `concepto_grafico_statements.py:23`, y el design lo pide así.
- [x] **Primera línea con la ruta**: en los 10 `.py` del diff.
- [x] **Sin `print`, TODO, secretos ni dependencias nuevas**: comprobado con `grep` sobre el diff.
- [x] **Reglas de Sigrid:**
  - [x] Base correcta: solo la de `ALLOWED_WRITE_DATABASES`, y nada en `ruesma_rep`.
  - [x] `cod`/`res`/`fec`/`tip`/`est` en `con`.
  - [x] Nada que recalcular: el parte no tiene totales, stock ni `mov`, y la fila de `log` se escribe como lo hace la UI (Q3).
  - [x] Estado sacado de `sercon.estini` y validado en `conest`.
  - [x] SQL con `?`, y el `MAX` se agrega en SQL.

VEREDICTO PARCIAL: APROBADO
