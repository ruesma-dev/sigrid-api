<!-- progress/impl_F-004.md -->
# F-004 · Informe de implementación — `POST /api/sigrid/concepto-grafico`

| | |
|---|---|
| **Fecha** | 2026-09-05 · rama `feature/F-004-endpoint-concepto-grafico` |
| **Alcance del encargo** | T3–T14, T16 y T17. **T15 (mutación) la lanza el líder**; T18–T22 son manuales |
| **Rigor** | `critico` (fase RED obligatoria, cobertura y mutación) |
| **Contra el ERP** | **nada**: ni una lectura, ni una escritura, ni una llamada a la API desplegada |
| **Cierre** | `bash harness/init.sh` → **ENTORNO LISTO** (§7) |

## 1 · Qué cambió

| Fichero | Qué es |
|---|---|
| `domain/models/concepto_grafico_models.py` | **nuevo** · petición, respuesta, previews y `ConceptoGraficoError` con su `codigo` (lista cerrada de 12) |
| `infrastructure/security/document_write_guard.py` | **nuevo** · guardia puro del fichero (base64 estricto, tamaño, firma, `sha256`) y de las listas blancas de `contip`/`gratipide` |
| `application/use_cases/concepto_grafico_statements.py` | **nuevo** · constructor puro de las 15 sentencias (L1-L6, E1-E7), las 29 columnas de `gra` y las 7 de `rcg`, el `cod` y la hora de Madrid |
| `application/use_cases/attach_concepto_grafico_use_case.py` | **nuevo** · guards → lecturas → idempotencia → dry-run o transacción de tres filas |
| `config/settings.py` | +7 App Settings (todas con defecto cerrado) y el validador `parse_int_list` |
| `function_app.py` | +ruta `sigrid/concepto-grafico`. `git diff` = **66 líneas añadidas, 0 borradas**: ninguna ruta existente se toca |
| `local.settings.sample.json` | las siete claves, cerradas |
| `CLAUDE.md`, `docs/ARCHITECTURE.md`, `CHECKPOINTS.md` (C3) | T16 · `ruesma_rep` se escribe **solo** por este endpoint, nunca por `sql/write` |
| `tests/test_f004_*.py` (6 ficheros, 175 tests) | R1-R22, sin red ni BBDD |
| `azure-apps/` (`sigrid_api.md`, `dedicacion.md`, `partes.md`, `remesas.md`) | T17 · commit **aparte**: `a40684f` (ese repositorio no tiene remoto) |

**No se tocó**: ningún guardia existente (`sql_write_guard`, `sql_query_guard`,
`identifier_guard`, `database_reference_guard` **se usan**, no se editan),
`sql_server_repository.py` (bastaron `execute_read_query`, `peek_next_ide` y
`run_in_write_transaction`), `ALLOWED_WRITE_DATABASES`, `requirements.txt`.

## 2 · Decisiones de diseño que no estaban escritas en la spec

1. **La hora de Madrid, sin `zoneinfo`.** `ZoneInfo("Europe/Madrid")` **falla
   en esta máquina**: Windows no trae base de datos de zonas y `tzdata` no está
   en `requirements.txt`; añadirlo sería una dependencia nueva que la spec no
   autoriza. `hora_local_de_madrid()` implementa la regla europea (CET, y CEST
   entre el último domingo de marzo y el de octubre, a las 01:00 UTC), fija por
   directiva desde 1996. Siete casos de test, incluidos los dos saltos de 2026
   y el cambio de año. Un solo camino de código: nada de «ZoneInfo si está».
2. **`SqlReadRequest.model_construct`** en vez de `model_validate`: los
   validadores del modelo llaman a `get_settings()`, que leería el `.env` de la
   máquina dentro de un test unitario. El SQL es constante y los parámetros los
   pone el caso de uso, así que no hay nada que validar.
3. **El base64 se valida en dos sitios y a propósito.** El modelo comprueba la
   **forma** (alfabeto y longitud múltiplo de 4) sin decodificar, para no
   materializar un fichero enorme antes de mirar el tope (R1 + R8); el guardia
   decodifica en modo estricto. Un base64 mal formado que llegara al guardia
   sale como `ValueError` (400 con su mensaje), no con `codigo`: la lista de R3
   es cerrada y ese caso es de R1.
4. **`committed` es honesto.** En el caso idempotente vale `false` con
   `filas_afectadas: 0`, porque no se escribió ninguna fila, y `dry_run` sigue
   siendo `not commit`. `EnlacePreview.pos` es `None` ahí: se conoce el enlace
   existente, no su posición (L5 no la devuelve).
5. **Se borró la propiedad `documental`** del constructor de sentencias: nadie
   la usaba y era la única línea sin cubrir de ese módulo.

## 3 · Fase RED (rigor `critico`)

Los cinco pares test→código, con el comando y la **salida real** del fallo.

**T3** (`R4`, los siete ajustes) — `python -m pytest tests/test_f004_settings.py -q`

```
>       assert settings.sigrid_document_write_enabled is False
tests\test_f004_settings.py:62: AttributeError
item = 'sigrid_document_write_enabled'
...
24 failed in 1.27s
```

**T5** (`R1`/`R2`, el contrato) — `python -m pytest tests/test_f004_models.py -q`

```
tests\test_f004_models.py:16: in <module>
    from domain.models.concepto_grafico_models import (
E   ModuleNotFoundError: No module named 'domain.models.concepto_grafico_models'
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
```

**T7** (`R8`, el guardia) — `python -m pytest tests/test_f004_document_write_guard.py -q`

```
tests\test_f004_document_write_guard.py:16: in <module>
    from infrastructure.security.document_write_guard import DocumentWriteGuard
E   ModuleNotFoundError: No module named 'infrastructure.security.document_write_guard'
```

**T9** (`R11`-`R20`, las sentencias) — `python -m pytest tests/test_f004_statements.py -q`

```
tests\test_f004_statements.py:20: in <module>
    from application.use_cases.concepto_grafico_statements import (
E   ModuleNotFoundError: No module named 'application.use_cases.concepto_grafico_statements'
```

**T11** (`R6`-`R21`, el caso de uso) — `python -m pytest tests/test_f004_use_case.py -q`

```
tests\test_f004_use_case.py:22: in <module>
    from application.use_cases.attach_concepto_grafico_use_case import (
E   ModuleNotFoundError: No module named 'application.use_cases.attach_concepto_grafico_use_case'
```

**T13** (`R3`, la ruta) — `python -m pytest tests/test_f004_route.py -q`

```
>       monkeypatch.setattr(function_app, "AttachConceptoGraficoUseCase", CasoDoble)
E       AttributeError: <module 'function_app' ...> has no attribute 'AttachConceptoGraficoUseCase'
7 failed, 1 warning in 1.25s
```

**Tres tests míos estaban mal escritos y se corrigieron después de ver el
verde** (no se cambió el código de producción por ellos, y se dice aquí para
que el reviewer no tenga que descubrirlo):

- `test_..._r16_ninguna_sentencia_cuenta_por_cod_antes_de_insertar` prohibía
  `cod = ?` en toda sentencia previa, y **L3 lee `usu.cod` legítimamente**.
  Ahora prohíbe la combinación `COUNT(*)` + `cod = ?`, que es lo que dice R16.
- `test_..._r19_el_constructor_se_autovalida` esperaba que
  `documental="msdb"` fuera rechazado: imposible, porque la documental está en
  la lista de permitidas por construcción. Se sustituyó por un **espía** sobre
  `DatabaseReferenceGuard.validate` que comprueba que las 15 sentencias pasan
  por el guardia con `allowed=[negocio, documental]` antes de abrir conexión.
- Dos constantes del test tenían el valor mal calculado a mano (`dddd` del
  `cod`, longitud del PDF gemelo). Se corrigieron con la cuenta real.

## 4 · Lo que garantizan los tests (175, seis ficheros)

| Fichero | n | Qué fija |
|---|---|---|
| `test_f004_settings.py` | 26 | R4/R5: los siete defectos cerrados, `parse_int_list` (JSON y CSV) falla en vez de degradar a `[]`, `ALLOWED_WRITE_DATABASES` sigue en `["ruesma"]` y el `local.settings.sample.json` viene cerrado |
| `test_f004_models.py` | 33 | R1/R2/R3: obligatorios, 48/255/24, `sha256`, base64 mal formado, campos prohibidos ignorados, los 11 campos de la respuesta, los 12 códigos |
| `test_f004_document_write_guard.py` | 27 | R8 y las listas de R7: base64 estricto, vacío, tope antes y después de decodificar, firma al principio, `sha256`, listas vacías rechazan todo |
| `test_f004_statements.py` | 41 | R11-R20: SQL **carácter a carácter** de las 15 sentencias, las 29 columnas y sus constantes medidas, mismo objeto `cod`/`emp`, `(emp, cod)` y nunca `ide`, control negativo de verbos, el guardia de bases |
| `test_f004_use_case.py` | 41 | R6/R7/R9/R10/R12/R14/R15/R17/R21: guards antes de la red, dry-run sin transacción, orden E4→E5→E6, `ide` de E2 en `rcg.gra`, relectura ≠ 1, fallo que no llega al insert siguiente, idempotencia (fuera y dentro de la transacción), huérfanas, traza sin base64 |
| `test_f004_route.py` | 7 | R3: 400 con `codigo`, `colision_de_clave`, «Solicitud invalida.», 500 en lo inesperado, y que las siete rutas anteriores siguen registradas |

Ninguno toca red ni BBDD: repositorio, cursor y `Settings` son dobles, y la
ruta se invoca con un `func.HttpRequest` construido a mano.

## 5 · Lo que NO se hizo (y por qué)

- **T15, la campaña de mutación**: fuera del encargo; la lanza el líder.
- **T18-T22**: manuales del humano (despliegue, App Settings, dry-run contra
  producción, primer `commit:true` autorizado y su repetición idempotente).
  Hasta T20 **nadie ha escrito nunca** en `ruesma_rep` por esta vía: lo que hay
  es código y tests.
- **Sin sondear el driver**: que `pyodbc` convierta `bytes` → `image` en E4 no
  se puede comprobar sin escribir. Si el motor lo rechazara, fallaría en E4 con
  `ROLLBACK` y nada escrito; el arreglo sería `CAST(? AS image)` en la constante.
  Es el riesgo vivo que T20 despeja.
- **Fuera de alcance de la spec**: borrar o sustituir adjuntos, reparar
  huérfanas, versionado (`graant`), `multipart`, `dbo.log`, abrir `sql/write`
  a la documental.

## 6 · Evidencias

Todas medidas sobre **`87098d6`** (`feature/F-004-endpoint-concepto-grafico`),
con `bash harness/init.sh` completo.

| Evidencia | Valor |
|---|---|
| **Tests ejecutados** | **1.437 pasan**, 1 se salta, 0 fallan (`python -m pytest tests -q`, bajo `coverage`) |
| **De ellos, de F-004** | **175** (`-k f004`), en 2,1 s |
| **Tiempo de la suite** | **51,35 s** en la ejecución de cierre de `init.sh` (43,99 s sin cobertura) |
| **Cobertura de las líneas cambiadas** | **100,0 %** — 455/455 líneas, umbral 80 %, nivel `critico`. Línea literal: `PUERTA COBERTURA: 100.0% de 455 líneas cambiadas cubiertas (455/455, umbral 80%, nivel critico)` |
| **Puerta de tamaño** | `[OK]` — requirements 150/150, design 250/250; este informe, dentro del tope de 220 |
| **ruff** | **79 avisos**, exactamente los mismos que antes de la feature (deuda previa). Los 21 que introdujo F-004 se corrigieron; no queda ninguno en código de F-004 |
| **Mutantes generados y supervivientes** | **PENDIENTE — T15, fuera de este encargo.** La lanza el líder con `python -m harness.mutacion --feature F-004` → `progress/mutacion_F-004.md`. Es la única evidencia del nivel `critico` que este informe no puede cerrar |
| **Verificaciones MANUAL pendientes** | T18-T22 (`tasks.md`), todas del humano. R23 (comprobar el `sha256` con `documents/read`) depende de T20 |
| **Escrituras contra el ERP** | **ninguna** |

## 7 · Cierre

```
[OK] pytest en verde (con medición de cobertura)      1437 passed, 1 skipped in 51.35s
[OK] PUERTA COBERTURA: 100.0% de 455 líneas cambiadas cubiertas (455/455, umbral 80%, nivel critico)
[OK] PUERTA TAMAÑO: F-004 dentro de los topes (requirements 150/150, design 250/250)
[OK] Rama actual: feature/F-004-endpoint-concepto-grafico
ENTORNO LISTO. Puedes trabajar.
```

**Commits** (uno por tarea, ninguno en `dev` ni en `main`, sin `git push`):
T3 `d714964` · T4 `00f6140` · T5 `308fa2b` · T6 `d285e38` · T7 `4f21c73` ·
T8 `5a7edf6` · T9 `15ce980` · T10 `80fc7cb` · T11 `9e1aeac` · T12 `0d9e8d1` ·
T13 (ruta) · T14 `a39b075` + `a8b4c17` · T16 `4d3bcf1` · T17 `87098d6` y, en
`azure-apps`, `a40684f`.

Un commit **ajeno a F-004** (`658b8fb`) recoge
`progress/impl_albaranes_script_docs.md`, que apareció en el árbol durante esta
implementación y se separó para no mezclarlo con la feature.
