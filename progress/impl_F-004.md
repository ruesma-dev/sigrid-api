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
`run_in_write_transaction`), `ALLOWED_WRITE_DATABASES`. Sí `requirements.txt`: +`tzdata` (§8).

## 2 · Decisiones de diseño que no estaban escritas en la spec

1. **La hora de Madrid, sin `zoneinfo`** (regla europea a mano, fija desde 1996,
   siete casos). **SUPERADA en §8.1**: hoy la vía normal es `ZoneInfo` + `tzdata`.
2. **`SqlReadRequest.model_construct`** en vez de `model_validate`: sus
   validadores llaman a `get_settings()`, que leería el `.env` de la máquina
   dentro de un test. El SQL es constante y los parámetros los pone el caso de uso.
3. **El base64 se valida en dos sitios y a propósito.** El modelo comprueba la
   **forma** (alfabeto, múltiplo de 4) sin decodificar, para no materializar un
   fichero enorme antes del tope (R1 + R8); el guardia decodifica estricto. Uno
   mal formado sale como `ValueError` (400), no con `codigo`: R3 es lista cerrada.
4. **`committed` es honesto.** En el caso idempotente vale `false` con
   `filas_afectadas: 0` (no se escribió nada) y `dry_run` sigue siendo `not
   commit`. `EnlacePreview.pos` es `None` ahí: L5 no devuelve la posición.
5. **Se borró la propiedad `documental`** del constructor de sentencias: nadie
   la usaba y era la única línea sin cubrir de ese módulo.

## 3 · Fase RED (rigor `critico`)

Los pares test→código, con el comando y la **salida real** del fallo.

**T3** (`R4`, los siete ajustes) — `python -m pytest tests/test_f004_settings.py -q`

```
>       assert settings.sigrid_document_write_enabled is False
tests\test_f004_settings.py:62: AttributeError
item = 'sigrid_document_write_enabled'
...
24 failed in 1.27s
```

**T5** (contrato), **T7** (guardia), **T9** (sentencias) y **T11** (caso de uso)
— `pytest tests/test_f004_<models|document_write_guard|statements|use_case>.py -q`.
Los cuatro fallan igual, en la **colección**, porque el módulo aún no existía:

```
tests\test_f004_models.py:16: in <module>
    from domain.models.concepto_grafico_models import (
E   ModuleNotFoundError: No module named 'domain.models.concepto_grafico_models'
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
```

Idéntico para `document_write_guard`, `concepto_grafico_statements` y
`attach_concepto_grafico_use_case`. Evidencia válida pero **débil** (error de
colección, no aserción rota); las de §8.1, §8.2 y §8.7 sí lo son.

**T13** (`R3`, la ruta) — `python -m pytest tests/test_f004_route.py -q`

```
>       monkeypatch.setattr(function_app, "AttachConceptoGraficoUseCase", CasoDoble)
E       AttributeError: <module 'function_app' ...> has no attribute 'AttachConceptoGraficoUseCase'
7 failed, 1 warning in 1.25s
```

**Tres tests míos estaban mal escritos y se corrigieron tras ver el verde** (sin
tocar producción): el de R16 prohibía `cod = ?` en toda sentencia y **L3 lee
`usu.cod` legítimamente** (ahora prohíbe `COUNT(*)` + `cod = ?`, que es lo que dice
R16); el de R19 esperaba rechazo de `documental="msdb"`, imposible por construcción
(se sustituyó por un **espía** sobre `DatabaseReferenceGuard.validate`); y dos
constantes tenían la cuenta mal a mano.

## 4 · Lo que garantizan los tests (175, seis ficheros; ninguno toca red ni BBDD: repositorio, cursor y `Settings` son dobles, y la ruta se invoca con un `func.HttpRequest` construido a mano)

| Fichero | n | Qué fija |
|---|---|---|
| `test_f004_settings.py` | 26 | R4/R5: los siete defectos cerrados, `parse_int_list` (JSON y CSV) falla en vez de degradar a `[]`, `ALLOWED_WRITE_DATABASES` sigue en `["ruesma"]` y el `local.settings.sample.json` viene cerrado |
| `test_f004_models.py` | 33 | R1/R2/R3: obligatorios, 48/255/24, `sha256`, base64 mal formado, campos prohibidos ignorados, los 11 campos de la respuesta, los 12 códigos |
| `test_f004_document_write_guard.py` | 27 | R8 y las listas de R7: base64 estricto, vacío, tope antes y después de decodificar, firma al principio, `sha256`, listas vacías rechazan todo |
| `test_f004_statements.py` | 41 | R11-R20: SQL **carácter a carácter** de las 15 sentencias, las 29 columnas y sus constantes medidas, mismo objeto `cod`/`emp`, `(emp, cod)` y nunca `ide`, control negativo de verbos, el guardia de bases |
| `test_f004_use_case.py` | 41 | R6/R7/R9/R10/R12/R14/R15/R17/R21: guards antes de la red, dry-run sin transacción, orden E4→E5→E6, `ide` de E2 en `rcg.gra`, relectura ≠ 1, fallo que no llega al insert siguiente, idempotencia (fuera y dentro de la transacción), huérfanas, traza sin base64 |
| `test_f004_route.py` | 7 | R3: 400 con `codigo`, `colision_de_clave`, «Solicitud invalida.», 500 en lo inesperado, y que las siete rutas anteriores siguen registradas |

## 5 · Lo que NO se hizo (y por qué)

- **T15, la campaña de mutación**: fuera del encargo; la lanza el líder.
- **T18-T22**: manuales del humano (despliegue, App Settings, dry-run en producción,
  primer `commit:true` y su repetición). Hasta T20 **nadie ha escrito nunca** ahí.
- **Sin sondear el driver**: que `pyodbc` convierta `bytes` → `image` en E4 no se
  puede comprobar sin escribir. Si el motor lo rechazara: fallo en E4, `ROLLBACK`,
  nada escrito; el arreglo sería `CAST(? AS image)`. Riesgo vivo que T20 despeja.
- **Fuera de alcance de la spec**: borrar o sustituir adjuntos, reparar huérfanas,
  versionado (`graant`), `multipart`, `dbo.log`, abrir `sql/write` a la documental.

## 6 · Evidencias

**Las cifras vigentes están en §8.6**, remedidas tras las rondas. Primera entrega
(SHA `87098d6`): 1.437 tests, 175 de F-004, suite 51,35 s, cobertura 100,0 % de 455
líneas cambiadas, tamaño `[OK]`, 79 avisos de `ruff` (los previos), `ENTORNO LISTO`.

| Evidencia | Valor |
|---|---|
| **Mutantes generados y supervivientes** | **CERRADO (T15)**: 167 mutantes, **167 muertos, 0 supervivientes**, 0 timeouts, **8 workers**, 366 s, sobre `79c5520`. Los **36** supervivientes de la campaña anterior (`d4e8535`) se remidieron EN SERIE —ninguno falso— y se cerraron con **16 tests nuevos** en fase RED contra su mutante, cero producción tocada. Medición, ficha a ficha, y el aviso sobre los 5 falsos supervivientes que se coló el modo paralelo: [`mutacion_F-004.md`](mutacion_F-004.md) |
| **Verificaciones MANUAL** | T18 y T19 **hechas el 2026-09-06** contra producción, todo lectura: [`verificacion_F-004_t18_t19.md`](verificacion_F-004_t18_t19.md). Quedan T20-T21 (primer `commit:true`, autorización expresa) |

## 7 · Cierre

**Commits** (uno por tarea, ninguno en `dev` ni en `main`, sin `git push`):
T3 `d714964` · T4 `00f6140` · T5 `308fa2b` · T6 `d285e38` · T7 `4f21c73` ·
T8 `5a7edf6` · T9 `15ce980` · T10 `80fc7cb` · T11 `9e1aeac` · T12 `0d9e8d1` ·
T13 (ruta) · T14 `a39b075` + `a8b4c17` · T16 `4d3bcf1` · T17 `87098d6`; en
`azure-apps`, `a40684f`. Rondas §8: `bb92507`, `7f0bcfb`, `aed7ef8`, T14c (§8.7) y,
en `azure-apps`, `157b392`. `658b8fb` es **ajeno a F-004** (recoge
`progress/impl_albaranes_script_docs.md`, aparecido en el árbol y separado aparte).

## 8 · Ronda tras revisión (2026-09-05)

Las tres revisiones APROBARON; el humano incorporó cuatro mejoras antes de la
campaña de mutación y una quinta (§8.7) al arrancarla. **Nada más**: ni guardias,
ni repositorio, ni `ALLOWED_WRITE_DATABASES`, ni el resto del caso de uso.

**8.1 · `tzdata` + `ZoneInfo`, con la regla manual de respaldo** — `bb92507`.
`requirements.txt` +`tzdata==2026.3` (fijada, instalada en el venv).
`hora_local_de_madrid()` usa `ZoneInfo("Europe/Madrid")` y **solo** ante
`ZoneInfoNotFoundError` cae a `_hora_por_la_regla_de_respaldo()`, intacta. Motivo
(review del constructor §3): si la UE deroga el cambio de hora, la regla a mano se
pudre en silencio; con `tzdata` llega sola. Los siete casos corren por los **dos**
caminos (fixture `camino_horario`, que en `respaldo` hace lanzar a `ZoneInfo`) y uno
nuevo prueba que con `tzdata` **no** se pasa por la manual. Control propio: los dos
caminos comparados en **788.976 instantes** de 1996-2040 → **0 discrepancias**.
RED — `pytest tests/test_f004_statements.py -q -k "hora_de_madrid or sin_zona or tzdata"`:

```
>       assert statements.ZoneInfo(statements.ZONA_DE_MADRID) is not None
E       AttributeError: module 'application.use_cases.concepto_grafico_statements'
        has no attribute 'ZoneInfo'
1 failed, 8 passed, 33 deselected, 8 errors in 0.30s
```
(los 8 errores son el fixture del camino `respaldo`: tampoco halla qué sustituir)

**8.2 · `max_rows` explícito en L5 y L6** — `7f0bcfb`. `_leer(..., max_rows=None)`;
L5 y L6 pasan `MAX_ALLOWED_ROWS` (1.000). El tope real era `DEFAULT_MAX_ROWS` (200)
y `_truncado` se descartaba: más de 200 binarios del mismo tamaño en un concepto
dejarían fuera al candidato y R17 duplicaría el adjunto **en silencio**. **Ningún
código de R3 encaja** (describen fallos de la petición o de la escritura, y
`filas_afectadas_inesperadas` es la relectura de R14, filas *escritas*) y la lista
es cerrada a propósito: sube un `ValueError` que la ruta ya saca como 400, **sin
ampliar R3**, antes de abrir transacción (`repositorio.transacciones == []`).
RED — `pytest tests/test_f004_use_case.py -q -k "tope_maximo or truncada"`:

```
tests\test_f004_use_case.py:388: assert topes["idempotencia"] == SettingsDoble().max_allowed_rows
E   AssertionError: assert None == 1000
tests\test_f004_use_case.py:400: with pytest.raises(ValueError) as excinfo:
E   Failed: DID NOT RAISE ValueError
3 failed, 41 deselected in 1.84s
```

**8.3 · Constantes** — `aed7ef8`. `vin=3` → `VIN_REPOSITORIO` y el `64` de
respaldo de `_leer_posicion` → `POS_PASO`. Sin cambio de comportamiento.

**8.4 · `committed:false` documentado** — `azure-apps` `157b392`. §8.8 avisa de que
con `commit:true` sobre un documento ya adjunto la respuesta es `ok:true`,
`idempotente:true`, `committed:false`, `filas_afectadas:0`, y da la comprobación
correcta: **`ok && (committed || idempotente)`**. Commit aparte, sin remoto ni `push`.

**8.5 · Fuera de esta ronda.** La recomendación 2 de la review del caso de uso
(`ALLOWED_WRITE_DATABASES` vacía **falla abierto**, aquí y en otros tres casos
de uso) **no se toca**: es un cambio de seguridad que merece feature propia.

### 8.6 · Evidencias remedidas (sobre `aed7ef8`, último commit de código)

| Evidencia | Valor |
|---|---|
| **Tests ejecutados** | **1.449 pasan**, 1 se salta, 0 fallan (+12 sobre la entrega anterior); de F-004, **187** (`-k f004`) |
| **Tiempo de la suite** | **45,12 s** y **60,21 s** bajo `coverage`, en las dos ejecuciones de cierre de `init.sh` (misma máquina, sin cambios entre ambas) |
| **Cobertura de líneas cambiadas** | **100,0 %** — `PUERTA COBERTURA: 100.0% de 465 líneas cambiadas cubiertas (465/465, umbral 80%, nivel critico)` |
| **Puerta de tamaño** e **`init.sh`** | `[OK]` — requirements 150/150, design 250/250, impl dentro de 220 · **ENTORNO LISTO** |
| **`ruff`** | **79 avisos, los mismos que antes de esta ronda** (deuda previa en `harness/`, `scripts/`, `config/`…). En los cuatro ficheros tocados: `All checks passed!` |
| **Mutación** | **cerrada** en `79c5520`: 167/167 muertos, 0 supervivientes (ver §6) |
| **Contra el ERP o la API** | **nada** |

**8.7 · Los tests de settings se aíslan del entorno** — commit `F-004 T14c`. Al
arrancar T15 la campaña abortó con la **línea base en rojo**: en sus worktrees
fallaban 25 tests de `tests/test_f004_settings.py` que en el árbol principal pasan.
La campaña vuelca el `.env` al entorno (arnés ≥1.7.7) y `EnvSettingsSource` hace
`json.loads` de `ALLOWED_DATABASES=master,…` **antes** que `parse_string_list`: reventaba todo `Settings` real aunque el test no tocara esa clave. RED:

```
E   pydantic_settings.sources.SettingsError: error parsing value for field "allowed_databases" from source "EnvSettingsSource"
25 failed, 1 passed in 4.00s  →  exit 1
```

Arreglo: `_entorno_limpio` borra **toda** clave que `Settings` reconozca (alias de
`model_fields`, no a mano: así cubre los campos futuros, en sus tres grafías) y
`ajustes()` pasa `_env_file=None`. Solo ese fichero —único con un `Settings` real
(`grep "Settings("` en `tests/test_f004_*.py`)—; **cero producción**. Verde: `exit 0`, `26 passed`; y `26 passed` sin entorno exportado.
**Lección:** un test con `Settings` real debe aislar el entorno **entero**, no solo
las claves que toca, porque la campaña de mutación exporta el `.env` de la máquina.
