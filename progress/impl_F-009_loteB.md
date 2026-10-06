<!-- progress/impl_F-009_loteB.md -->
# F-009 · Informe del implementer · Lote B (T2-T6)

Rama `feature/F-009-alta-albaran-compra`, 2026-10-06. Spec v8.1. Nivel `critico`. Sin red, sin Azure, sin SQL Server.
Commits (uno por tarea y un ajuste de cobertura), todos locales:

| Commit | Tarea |
|---|---|
| `c7c0b95` | T2: seis App Settings `SIGRID_ALBARAN_*` con defecto cerrado |
| `91f80f6` | T3: modelos del modo extendido |
| `e2d52fb` | T4: SQL constante L1-L15, E1-E12 y R31 |
| `f0130ed` | T5: funciones puras |
| `d936ced` | T6: constructores de filas |
| `43eae24` | Ajuste: dos tests para las dos únicas líneas cambiadas sin cubrir |

**Sin tocar** (comprobado con `git diff`): los casos de uso y modelos del clásico y de `albaran-directo`,
`infrastructure/security/`, `function_app.py`, `.env` y `tests/fixtures/f009_caracterizacion.json` (su diff con
`dev` es el de T1; desde `055a7e1` este lote no lo toca).

## Qué se hizo, por tarea

**T2** · `config/settings.py`: `SIGRID_ALBARAN_WRITE_ENABLED=false`, `_PREFIJOS_REFERENCIA=[]` y
`_PRODUCTOS_SIN_CONTRATO=[]` (`parse_string_list`), `_EMPRESAS_OBRA=[]` (`parse_int_list`), `_MAX_LINEAS=100` y
`_NATURALEZA_POR_PRODUCTO={}` con el validador nuevo `parse_string_dict`: vacío/ausente ⇒ `{}`; objeto JSON de textos no
vacíos (recortados) ⇒ ese; CSV, lista (también `[]`), texto suelto, valores no texto o vacíos y **claves repetidas** (también
tras recortar) ⇒ `ValueError` al arrancar. `local.settings.sample.json` con las seis en JSON (`"[]"`, `"{}"`). Tests
`tests/test_f009_settings.py` (57) con el entorno aislado (lección de F-004: se borran del entorno todas las claves que
`Settings` reconoce y `_env_file=None`), incluido un test que lee el fichero de ejemplo **por el entorno**.

**T3** · `domain/models/albaran_compra_models.py` (nuevo; importa los clásicos, no los edita): `elegir_modo_albaran` (R1),
`LineaAlbaranIn`, `AlbaranCompraRequest`, `AvisoAlbaran`, `LineaResultado(AlbaranLinePreview)`, `FalloLinea`,
`AlbaranCompraResponse(AddPurchaseAlbaranResponse)`, `AlbaranCompraError`, los tres conjuntos cerrados de códigos de design
§Códigos, `COLUMNAS_BANCARIAS` y `sin_columnas_bancarias`. Tests `tests/test_f009_models.py` (145).

**T4** · `application/use_cases/albaran_compra_statements.py` (nuevo): L1, L5 (por `entide` y, sin contrato, por `entcif`),
L6, L7 (sin `natide`), L7b, L8, L8b, L9, L10 (`obr` y `alm`), L11 (con `refent`), L12, L13, L14, L15a-c; E2-E7, E9-E11,
E11b, E12; `APPLOCKS` en el orden de design. Sin L12b, L12c ni E7b. El constructor valida las 40 constantes con
`DatabaseReferenceGuard`; las generadas (listas `IN` y los `INSERT` de tablas clonadas) se validan al generarse. Tests
carácter a carácter y control negativo en `tests/test_f009_statements.py`.

**T5** · en el mismo módulo: `prefijo_de_serie`, `siguiente_cod`, `redondear_euros`, `importe_linea`, `sumar_importes`,
`precio_coincide`, `Balance`, `siguiente_balance`, `encadenar_balances`, `sufijo_analitica`, `codigo_analitica`,
`estados_contrato`.

**T6** · en el mismo módulo: `SellosAlbaran`/`sellos_del_alta` (R22), `construir_con`, `construir_dca`,
`construir_dcapro_vinculada`, `construir_dcapro_sin_vincular`, `construir_ctrprodes`, `construir_mov`, `construir_log`,
`FilasAlbaran` (con `como_dict()` para `filas`) y `numerar` (reentrante: copia, no toca las filas de partida).

## Decisiones de interpretación (para el reviewer y el líder)

1. **`tot` de la vinculada con precio dentro de la tolerancia: `cantidad·precio` pedido.** R17 dice «`tot` =
   `cantidad·precio`» y el contrato §2.2 «= importe aprobado»; design §Importes escribe `redondear_euros(cantidad·pre)`, y
   con precio ≤ 0,0001 del `ctrpro` el `pre` escrito es el del `ctrpro`. Solo difieren en ese caso, en ≤ 0,0001·|cantidad|
   antes de redondear. He seguido R17 y el contrato (manda la spec, y sv9 compara `total` con su importe a 0,05 €); el
   `pre` escrito, el del `mov` y el balance usan el `pre` del `ctrpro` (H14). **A confirmar**: si debe ser `cantidad·pre`,
   es una línea en `construir_dcapro_vinculada` y un test.
2. **E8 de `con`, `dca` y `dcapro`**: se clonan con `SELECT *` (como el clásico y como exige R33), así que sus columnas
   son las de la plantilla. Interpretación de «SQL constante» para el `<columnas>` de E8: texto fijo, tabla de un conjunto
   cerrado, cada columna validada con `IdentifierGuard` (y rechazada si el guardia tuvo que recortarla), entre corchetes, y
   el `INSERT` validado con `DatabaseReferenceGuard` al generarse; los valores siempre `?`. `mov`, `ctrprodes` y `log`
   con columnas fijas y fila **exacta** (ni de más ni de menos).
3. **L10 sin almacenes resueltos**: `ide IN ()` no es SQL; se emite la primera mitad (`WHERE obride = ?`).
4. **E12**: design solo dice «`COUNT(*)` por clave». Claves elegidas: `con` por `(emp, tip, cod)` (índice único, como
   F-006), `dca` por `ide`, `dcapro` por `docide`, `ctrprodes` por `(docdeside, docdestip 14)`, `mov` por `(docide,
   doctip 14)`, `log` por `ide`.
5. **Números estrictos** (`strict=True`) en `cantidad`, `precio`, `ctrpro_ide`, `paride`, `fecha_albaran` y `empide`:
   el contrato §2 dice «números como números JSON, no texto». Un `"2"` o un `true` son 400 sin código; un entero JSON en
   `cantidad` sigue valiendo (`3` → `3.0`).
6. `descripcion` y `unidad` vacías tras recortar = ausentes (la vinculada las toma del `ctrpro`; la sin vincular sin
   `descripcion` falla R6). Sin `unidad`, la sin vincular escribe `unimed` `''` (nada de la plantilla, H11).
7. `AlbaranCompraResponse` **deriva** `warnings` (cabecera primero, luego cada línea en orden; lo que llegue se ignora) y
   **quita** las bancarias de `cabecera` y `filas["dca"]` en su propio validador: ningún camino del caso de uso puede
   saltárselo. La fila que se escribe las lleva (H16).
8. `AlbaranCompraError` solo admite códigos de cabecera; `lineas` va si y solo si el código es `lineas_no_validas` (y
   entonces no vacía). Los códigos de línea solo existen dentro de `FalloLinea`.
9. `LineaResultado`: `tipo`, `pos` y `cenide` opcionales (en `idempotente` no se leen). Los obligatorios del clásico
   (`ctrpro_ide`, `linoriide`, `iva_cuota`) los rellenará el lote C con 0 en `idempotente`.
10. Vinculada «como hoy» donde la spec no dice otra cosa: sin plantilla, el mínimo del clásico; `unimed` de la plantilla
    si ni la petición ni el `ctrpro` la traen; `tex` del `ctrpro`; seguimiento a 0 solo si la columna existe. `caaide`
    del `ctrpro` siempre (0 si fuera `NULL`, nunca de la plantilla). `dca`: overrides del clásico solo si la plantilla
    trae la columna; `ctride` y `synckey` siempre. `con.res` a 128 (el clásico, 200).
11. `estados_contrato` compara a 2 decimales, como el clásico; un `SUM` `NULL` cuenta como 0. `siguiente_balance`
    conserva el PMP solo con `stock + can` **exactamente** 0, como el clásico y R19 (un residuo binario daría un PMP
    enorme; no lo he visto en los datos de prueba, lo dejo anotado como riesgo para T11/T22).
12. `ctrprodes.docdescod` lo pone `numerar` (el `cod` se reserva en E2, después de construir las filas).

## Fase RED (trazas reales, test escrito antes que el código)

**R10 (T2)** · `.venv/Scripts/python.exe -m pytest tests/test_f009_settings.py -q -p no:cacheprovider` antes de tocar
`config/settings.py`:
```
E                   AttributeError: 'Settings' object has no attribute 'sigrid_albaran_write_enabled'. Did you mean: 'sigrid_domain_write_enabled'?
E       Failed: DID NOT RAISE ValidationError
E       AssertionError: assert {'SIGRID_ALBA...A': None, ...} == {'SIGRID_ALBA...A': '[]', ...}
E         {'SIGRID_ALBARAN_PREFIJOS_REFERENCIA': None} != {'SIGRID_ALBARAN_PREFIJOS_REFERENCIA': '[]'}
FAILED tests/test_f009_settings.py::test_f009_r10_los_seis_ajustes_nuevos_arrancan_con_defecto_cerrado
FAILED tests/test_f009_settings.py::test_f009_r10_naturaleza_mal_escrita_no_arranca[42]
FAILED tests/test_f009_settings.py::test_f009_r10_el_fichero_de_ejemplo_declara_las_seis_claves_cerradas
54 failed, 1 passed in 6.23s
```
(El que pasaba: el de «ninguna existente cambia». Después se añadieron `[]` y `[[...]]` a los rechazos al ver que
`object_pairs_hook=list` aceptaba `[]`; por eso el validador usa una clase centinela y `NoDecode`.)

**R1 (T3)** · `.venv/Scripts/python.exe -m pytest tests/test_f009_models.py -q -p no:cacheprovider -k r1`, sin el módulo:
```
tests\test_f009_models.py:19: in <module>
    from domain.models.albaran_compra_models import (
E   ModuleNotFoundError: No module named 'domain.models.albaran_compra_models'
ERROR tests/test_f009_models.py
1 error in 1.31s
```

**R15, R17, R18, R19 (T5)** · `.venv/Scripts/python.exe -m pytest tests/test_f009_statements.py -q -p no:cacheprovider
-k "r15 or r17 or r18 or r19 or r20 or r26 or r22"`, con el módulo de T4 y sin las funciones:
```
>       balance = modulo.siguiente_balance((10.0, 2.0), -4.0, 3.0)
E       AttributeError: module 'application.use_cases.albaran_compra_statements' has no attribute 'siguiente_balance'
>       assert modulo.redondear_euros(2.675) == Decimal("2.68")
E       AttributeError: module 'application.use_cases.albaran_compra_statements' has no attribute 'redondear_euros'
E       AttributeError: module 'application.use_cases.albaran_compra_statements' has no attribute 'sufijo_analitica'
E       AttributeError: module 'application.use_cases.albaran_compra_statements' has no attribute 'encadenar_balances'
65 failed, 4 passed, 49 deselected in 8.71s
```
(Los 4 que pasaban son las sentencias E2-E7 de T4, que también llevan `r26` en el nombre.) Los tests de T5 y T6 usan
`modulo.<nombre>` para que la fase RED falle test a test sin tumbar la recogida de los de T4. T6 también se escribió
antes: `32 failed, 38 passed, 85 deselected` con su filtro.

## Verificación de cada tarea (salida real, al final del lote)

| Tarea | Comando | Resultado |
|---|---|---|
| T2 | `pytest tests/test_f009_settings.py` | `57 passed in 4.09s` |
| T3 | `pytest tests/test_f009_models.py` (todos son `r1/r5/r6/r7/r9`) | `145 passed in 1.52s` |
| T4 | `pytest tests/test_f009_statements.py -k "r31 or sql"` | `56 passed, 102 deselected in 2.33s` |
| T5 | `pytest tests/test_f009_statements.py -k "r15 or r17 or r18 or r19 or r20 or r26"` | `72 passed, 86 deselected in 1.20s` |
| T6 | `pytest tests/test_f009_statements.py -k "r11 or r12 or r13 or r14 or r15 or r16 or r19 or r21 or r22 or r25"` | `69 passed, 89 deselected in 1.27s` |
| R2-R4 | `pytest tests/test_f009_caracterizacion.py` (dorado intacto) | `17 passed, 1 warning in 1.66s` |

Lo que fijan, además de lo obvio: 2,675 → 2,68 y 3·0,895 → 2,69 (`Decimal`, no `round`); `prepma` = PMP de **partida**
encadenado por (producto, almacén) y `(0, 0)` sin `mov`; devolución con la regla A (también con stock final negativo);
`sufijo_analitica` sin `MOD.` (y `CD.SB37` entero: la regla de la v7 no vuelve); H35 en vinculadas (y `''`/0 si el `ctrpro`
no los trae); §Reseteo completo en sin vincular; `paride` nunca del `ctrpro`; el `ctrpro` y las plantillas no se mutan;
`numerar` reentrante y las filas numeradas pasan por los `INSERT` sin error; R31 con 40 sentencias, solo los dos `UPDATE`
de R25, sin `DELETE`/`MERGE`/DDL/`;`/literales, y el control negativo (una constante con `ruesma_rep.dbo.` impide
construir; una generada con `msdb.dbo.` se rechaza; una columna inyectada, también).

## `bash harness/init.sh` (final)

Tal cual, tras el último commit de código y con este informe escrito: todas las comprobaciones en `[OK]` (ruff:
80 avisos de deuda previa, ninguno en los ficheros del lote, que pasan `ruff check` limpios), y:
```
2110 passed, 1 skipped, 1 warning in 104.31s (0:01:44)
[OK] pytest en verde (con medición de cobertura)
[OK] PUERTA COBERTURA: 100.0% de 517 líneas cambiadas cubiertas (517/517, umbral 80%, nivel critico)
[OK] PUERTA TAMAÑO: F-009 dentro de los topes (requirements 150/150, design 249/250, impl 196/220, review 117/140)
[OK] Rama actual: feature/F-009-alta-albaran-compra
ENTORNO LISTO. Puedes trabajar.
```
(Antes del ajuste `43eae24` la puerta daba 99,6 %, 515/517: la rama de columna con espacios de `insertar_clonada` y la
de CIF que no es texto.)

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados (suite completa) | 2110 passed, 1 skipped (`bash harness/init.sh`) |
| Tests nuevos del lote | 360 (57 + 145 + 158), todos en verde |
| Cobertura de las líneas cambiadas | **100,0 %** (517/517, umbral 80 %, `critico`), línea `PUERTA COBERTURA` |
| Mutantes generados y supervivientes | **No medido en este lote**: la campaña de rigor `critico` es T16 (lote E), sobre la feature entera, como fijó el plan aprobado; lanzarla ahora mediría un caso de uso que aún no existe |
| Tiempo de la suite | 104,31 s la suite completa con cobertura; los tres ficheros del lote, 2,36 s |

Cobertura de los tres módulos tocados con los tests del lote (`coverage run --include=...`): `albaran_compra_statements.py`
y `albaran_compra_models.py` 100 %; `config/settings.py` 92 %, con las líneas sin cubrir **todas previas** (rama CSV de
`parse_string_list`, ramas de `parse_int_list`, `write_enabled` y `get_settings`), ninguna de este lote.

## Lo que queda para el lote C (T7-T12)

- El caso de uso `create_albaran_compra_use_case.py`: orquestar L1-L15 con los métodos de `AlbaranCompraStatements`, la
  resolución de R11-R17 con todos los fallos acumulados (`AlbaranCompraError(codigo="lineas_no_validas", lineas=[...])`),
  los avisos (`precio_distinto_del_contrato` con `precio_coincide`, `supera_pendiente`, `servido_negativo`,
  `stock_negativo` con `Balance.almcan`, `iva_de_otro_proveedor`, `producto_sin_historico`, `cod_provisional`), y elegir la
  plantilla de línea (L8b o L8) que recibe `construir_dcapro_sin_vincular`.
- Cuántos `mov` hay y con qué balances: `encadenar_balances` con los `(proide, almide, can, pre)` de las líneas con
  `tipmov` 1, y `prepma` 0 en las `dcapro` sin `mov` (R21).
- `work(cursor)` reentrante: E1 → E2 (`siguiente_cod`) → E3-E7 → `numerar` → E8 → E9-E11 (solo con vinculadas, una E9
  **por línea**) → E11b → E12; applocks `APPLOCKS`; `estados_contrato` con E10.
- `idempotente`: líneas de L11 con `LineaResultado(..., pos=, ctrpro_ide=0, linoriide=0, iva_cuota=0.0)` (decisión 9).
- Confirmar la decisión 1 (`tot` con `precio` o con `pre`) antes de T12 (equivalencia).
