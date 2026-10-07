Revisión completa (pasada 1) de T17 y T18: `1da0c5e` y `ebb0ddc` (sigrid-api) y `51b29a6` (azure-apps)

# F-009 · Revisión del lote E, parte documental (T17, T18)

**Veredicto: APPROVED.** No hay cambios requeridos. Hay siete observaciones que no bloquean.
Reviewer, 2026-10-07. Spec v8.2. Rama `feature/F-009-alta-albaran-compra`, HEAD `3d681e6`. No he tocado Azure ni el SQL Server.
La campaña de mutación (T16) la revisa otro reviewer en paralelo y queda fuera de este informe.

## Nivel de rigor

`critico`, declarado en `harness/features.json`. T17 y T18 son documentación y se verifican con la «revisión
del reviewer». Por eso no tienen fase RED ni cobertura ni mutación propias: no añaden código ni requisitos de
comportamiento. Las puertas de la feature (cobertura, mutación) se juzgan en T16 y en la revisión final.

## `bash harness/init.sh` (tal cual, sobre HEAD `3d681e6`)

`2370 passed, 1 skipped`. `PUERTA COBERTURA` [OK] 100,0 % (1103/1103). `PUERTA TAMAÑO` [OK]. Rama correcta.
Resultado: `ENTORNO LISTO`, exit 0.
Los commits de T16 posteriores a los de la documentación (`92bf606`..`3d681e6`) solo cambian detalles internos de
`create_albaran_compra_use_case.py` y `albaran_compra_statements.py`: valores `None` por defecto en `_Linea`, fuera
`strict=` y `ide_log=None`. Nada de lo documentado cambia; lo comprobé con `git diff ebb0ddc..HEAD`.

## 1 · T17: `docs/ARCHITECTURE.md`, contrastado con el código

| Afirmación | Dónde lo comprobé | Resultado |
|---|---|---|
| Tupla de ocho; clásico en el 6 y extendido en el 7 | `function_app.py:58-81` y `:221` (`deps[6]`, `deps[7]`) | [x] (ver O1) |
| Selector por claves, `peticion_mixta`, función pura del dominio | `albaran_compra_models.py:159-178` | [x] |
| `AlbaranCompraError(ValueError)` con `codigo` y `lineas`; petición `extra="forbid"` | `albaran_compra_models.py:131`, `:259` | [x] |
| SQL constante L1-L15 y E1-E12, autovalidado con `DatabaseReferenceGuard` | `albaran_compra_statements.py:81-161`, `:805` | [x] |
| Applocks en orden fijo | `albaran_compra_statements.py:51-58` | [x] |
| La colisión sale del caso de uso y la ruta no captura `IntegrityError` | `create_albaran_compra_use_case.py:635-648`; la ruta no tiene ese `except` | [x] (O4 del lote D) |
| R8 tras validar y antes del caso de uso, en los dos modos y en el directo | `function_app.py:226`, `:272`, `:319`, `:276-285` | [x] |
| Traza R32 que emite el caso de uso; lo que la ruta corta solo deja su `warning` | `create_albaran_compra_use_case.py:246-248`; `function_app.py:263`, `:292` | [x] (O6 del lote D) |
| Clásico intocable, fijado por el dorado | `tests/test_f009_caracterizacion.py` y su fixture existen | [x] |
| Cada capa en su sitio; infrastructure no añade nada | Comprobado | [x] (ver O5) |

## 2 · T18: `azure-apps/sigrid_api.md`, contrastado con el código y la spec v8.2

| Punto pedido | Línea en `sigrid_api.md` | Comprobado contra | Resultado |
|---|---|---|---|
| §4: seis App Settings con defecto y efecto; listas y mapeo solo en JSON, el mapeo estricto al arrancar | 285-289, 322-327 | `config/settings.py:115-131`, `:232`; `local.settings.sample.json:49-54` | [x] |
| §4.1: valores de T19 al pie de la letra; `MAX_LINEAS` se queda en el defecto | 358-363 | `tasks.md` T19 | [x] |
| §4.1: `dev` escribe en la base real y la previa es el entorno de prueba | 365-368 | contrato §1.3 | [x] |
| §7.2, punto 8: llave R8 en los dos modos y en el directo; en el extendido también DOMAIN, credenciales y lista vacía que no abre, solo en commit | 635-644 | `create_albaran_compra_use_case.py:277-310` | [x] (ver O2) |
| §7.5, H32 corregido: el `cod` va fuera en el clásico y el directo, dentro en el extendido | 690-693, 709-721 | `create_purchase_albaran_use_case.py:110`, `:545-555`; `E2_COD` con `UPDLOCK, HOLDLOCK` | [x] |
| §7.5: se reintenta toda `IntegrityError`; el clásico agotado da 500 | 723-732 | `sql_server_repository.py:302-309`; la ruta clásica no tiene `except` para ella | [x] |
| §7.6: clásico corregido (solo `lineas_recibidas`, suma por `ctrpro`) y fila del extendido | 742-744 | `create_purchase_albaran_use_case.py:229-235`; contrato §4.2 | [x] |
| §8.6, H32 corregido: deja de decir «replica todas las líneas» | 869-872 | ídem | [x] |
| §8.6: clásico y directo obsoletos cuando F-053 esté en real (también en §8.7 y §13) | 872, 964, §13 | `tasks.md` T18; contrato §7 | [x] |
| §8.6: varias entradas por línea en `details.lineas`, con la confirmación de albaranes | 924-928 | `create_albaran_compra_use_case.py:681-700` (origen, partida, precio) | [x] |
| §8.6: `producto` a `null` en las vinculadas, con la confirmación de albaranes | 910-912 | `create_albaran_compra_use_case.py:1148` | [x] |
| §8.6: 400 de texto libre por un maestro incoherente (IVA o plantilla) | 937-941 | `create_albaran_compra_use_case.py:373`, `:1256` (nombra `indice` y `referencia_linea`) | [x] |
| §8.6: `idempotente` con `cabecera={"fec"}` y `totales`; 500 que reenvía la misma referencia; `ValidationError` interno; orden R8 frente a `demasiadas_lineas` | 913-948 | `:505-529`; observaciones O1-O3 del lote D y O6 del lote C_2 | [x] |
| §8.7: el directo hereda `paride` y el extendido nunca | 960-967 | `create_direct_albaran_use_case.py:178` | [x] |
| §10: consumidor albaranes sv9 (F-053) | 1294-1295 | contrato §7 y F-053 R33 | [x] |
| §13: estado de F-009, roadmap y punto nuevo para filtrar el reintento | 1360+ | O3 del lote C_2 | [x] |
| §1.1 y §1.2: árbol y tupla de ocho | 76, 88-89, 117-119 | código | [x] (ver O1) |

## 3 · Secretos, `.env` y enlace al contrato

- **Barrido propio** sobre `git show 51b29a6` y `git show 1da0c5e ebb0ddc`. Patrones: IPv4
  `[0-9]{1,3}(\.[0-9]{1,3}){3}`, GUID `[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-`, `Password=`, `Pwd=`, `AccountKey`,
  `SharedAccess`, `code=`, `vault.azure` y `secret`. Una sola coincidencia, la palabra «secretos» (línea 290 del diff),
  que es texto. Ningún valor de Key Vault, de secreto ni de clave de función.
- `azure-apps`: `.env` ignorado (`.gitignore:15`) y fuera de `git ls-files`. El árbol de trabajo está limpio.
  El commit `51b29a6` toca solo `sigrid_api.md`.
- **Enlace, no copia**: §8.6 y §10 apuntan a `contrato_albaranes.md` §2-§4 y §6 y dicen «no se copia aquí». Lo
  que se repite es un resumen de lo esencial más lo que el contrato no recoge (observaciones de los lotes C y D).

## 4 · Coherencia con §2-§4 del contrato (congelado para F-053)

No he encontrado contradicciones. Hay una divergencia **documentada a propósito**: con `commit:true` y R8 cerrada,
la ruta responde antes que `demasiadas_lineas` y `referencia_no_permitida`, que es lo contrario del contrato §4.1.
La manda R8, que va por encima del contrato; se aceptó en el lote D (O3) y T18 la escribe con su efecto en F-053
(`no_admitido` frente a `error`, sin impacto práctico). Es el código el que se aparta del contrato, no la
documentación, y el contrato no hace falta tocarlo. Lo mismo pasa con lo que T18 añade a §3.1 y §3.4 del contrato
(`producto` a `null`, `cabecera={"fec"}`, texto libre por un maestro incoherente): todo eso F-053 ya lo trata como
`error` o no lo lee (R16).

## Checkpoints (en lo que toca a este lote)

- C1 [x]: `init.sh` sale con exit 0 y los ficheros del arnés existen.
- C2 [x]: solo F-009 está `in_progress`; la rama es la correcta; `current.md` describe la sesión activa.
- C3 [x]: no hay código nuevo en T17 ni en T18 y no hay secretos (barrido de arriba). Arquitectura hexagonal: el
  diseño que se documenta es el real (ver O5).
- C3 bis: N/A. El lote no añade nada a `docs/referencia/`. El barrido de secretos se hizo igualmente (§3).
- C4: N/A para este lote. T17 y T18 no tienen requisitos de comportamiento propios, y la trazabilidad R→test la
  cubren las revisiones B-D y la final. R36: ARCHITECTURE y azure-apps hechos aquí; docstring en T13 y
  `local.settings.sample.json` en T2, ya revisados.
- C4 bis: N/A en este informe. La mutación es T16 y la revisa el otro reviewer. La sección «Evidencias» del informe
  `impl_F-009_loteE_docs.md` está presente, con mutación «no aplica» justificada.
- C5: parcial, porque la feature sigue abierta (T19-T25 pendientes). T17 y T18 están `[x]` con sus commits
  `F-009 T17:` y `F-009 T18:`. El fichero sin trackear `` `0`].{t `` sigue ahí (ver O7).

## Observaciones (no bloquean)

- **O1 · Posiciones de la tupla escritas como índice sin decirlo.** En `docs/ARCHITECTURE.md:34-35` y
  `sigrid_api.md:118-119`, «la 6 es el clásico y la 7 el extendido» es correcto en base 0 (`deps[6]`, `deps[7]`).
  Pero en una tupla «de ocho posiciones», quien cuente desde 1 leerá la sexta. Conviene escribir «índice 6
  (`deps[6]`)» la próxima vez que se toque.
- **O2 · §7.2, punto 2 (`ALLOWED_WRITE_PREFIXES` no vacío), anterior a F-009 e inexacto para dominio.** Ningún caso de
  uso de dominio lo mira, el extendido tampoco (`create_albaran_compra_use_case.py:293-299`), y solo afecta a
  `sql/write` (`settings.write_enabled`). F-009 no lo introduce. Queda para una corrección documental aparte.
- **O3 · `azure-apps/albaranes.md:31-32` dice «nada del pipeline escribe allí»** y todavía no menciona sv9 ni F-053.
  El documento es de albaranes, y por la regla de propiedad lo actualiza su F-053 cuando pase a real. Que el líder
  se lo diga a ese proyecto.
- **O4 · `sigrid_api.md:892` escribe `descripcion?`**, pero el campo es obligatorio en las sin vincular (R6). Es menor:
  la línea 935 remite a «las reglas de línea de R6» y el contrato enlazado lo dice.
- **O5 · `ARCHITECTURE.md` dice «dependencias apuntando siempre al dominio»**, pero `albaran_compra_statements.py:29-30`
  (application) importa guardias de `infrastructure.security`. Es el patrón previo de `concepto_grafico_statements` y
  `execute_sql_*`, así que no es una novedad de F-009. Es deuda del documento normativo, no de este lote.
- **O6 · El docstring «tupla de siete» de `tests/test_f004_route.py` (O7 del lote D) sigue igual.** Es razonable: está
  en un test de otra feature y R36 no lo pide. El implementer lo justifica en su informe.
- **O7 · `` `0`].{t `` sin trackear en la raíz** (O5 del lote D). Lo decide el humano antes del cierre (C5).

Para el otro reviewer, sin efecto sobre la documentación: `create_albaran_compra_use_case.py:1184` introduce un `assert`
en producción (T16, `8a85804`), que desaparece con `python -O`.

## Cambios requeridos

Ninguno.
