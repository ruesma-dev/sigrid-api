<!-- specs/F-009-alta-albaran-compra/design.md -->
# F-009 · Diseño

## La decisión de fondo

**Ruta nueva `sigrid/albaran-compra`, no ampliación de `sigrid/albaran`** (pregunta 1). Lo que
F-053 necesita cambia la semántica, no solo añade campos: una línea de la petición = una
`dcapro` (hoy se agregan por `ctrpro`), partida o almacén obligatorio por línea (hoy se copia
del `ctrpro` o de la plantilla), negativas, idempotencia obligatoria, errores con código y el
`cod` dentro de la transacción. Meterlo en la ruta actual obligaría a un «modo» implícito
según qué campos vengan, y a re-verificar entero un núcleo de 600 líneas **sin un solo test**
(`tests/` no tiene ninguno de albaranes). Con ruta nueva, los dos endpoints actuales quedan
**byte a byte** (R6) y su contrato no puede romperse.

**Ampliar, no reescribir:** las reglas del núcleo probado en junio (`AC26/15950-15952`) se
conservan —plantilla de cabecera y de línea, `mov` con PMP sin redondear, `ctrprodes`,
`canser` relativo, `estser/estfac` por sumas— y R31 lo demuestra con un **test de
equivalencia** contra `CreatePurchaseAlbaranUseCase` sobre el mismo doble del repositorio.
Lo nuevo sigue el esqueleto de F-006: modelo Pydantic → **constructor puro de sentencias** →
caso de uso con dry-run por defecto → `run_in_write_transaction()`.

**Límite de microservicio: cabe.** Dar de alta un concepto del ERP con sus efectos (stock,
medición del contrato) es la responsabilidad de la pasarela. Qué albarán se registra, con qué
partida y a qué precio lo decide el llamante (albaranes sv9).

## Ficheros a crear

| Fichero | Capa | Qué contiene |
|---|---|---|
| `domain/models/albaran_compra_models.py` | domain | `LineaAlbaranIn`, `AlbaranCompraRequest` (validadores de R2), `AvisoAlbaran`, `LineaResultado`, `FalloLinea`, `AlbaranCompraResponse`, `AlbaranCompraError(ValueError)` con `codigo` del conjunto cerrado y `lineas` opcional |
| `application/use_cases/albaran_compra_statements.py` | application | `AlbaranCompraStatements(database)`: SQL constante de L1-L14 y E1-E12; funciones puras `siguiente_cod`, `siguiente_balance`, `estados_contrato`, `importe_linea` y constructores de filas. Sin E/S. Se autovalida con `DatabaseReferenceGuard` |
| `application/use_cases/create_albaran_compra_use_case.py` | application | `CreateAlbaranCompraUseCase(repository, settings, ahora_utc=..., reloj=...)` |
| `tests/test_f009_settings.py`, `_models.py`, `_statements.py`, `_use_case.py`, `_route.py`, `_equivalencia.py` | — | Ver `tasks.md` |

## Ficheros a modificar

| Fichero | Qué cambia |
|---|---|
| `config/settings.py` | Cuatro campos de R5; las dos listas de texto reutilizan `parse_string_list` |
| `function_app.py` | Ruta `sigrid/albaran-compra` con el esqueleto de `sigrid_partes_reclamacion`: `AlbaranCompraError` → 400 con `details.codigo` (y `details.lineas`); `IntegrityError` agotado → 400 `colision_de_clave`; `ValidationError`/`ValueError` → 400; resto → 500. Con R7, además, la guarda de la llave antes de `use_case.run` en las dos rutas de albarán **solo si `commit` es true** |
| `local.settings.sample.json`, `docs/ARCHITECTURE.md`, `CLAUDE.md` | Claves nuevas; ruta, modelo y caso de uso; lista de rutas |
| `azure-apps/sigrid_api.md` | R34 (commit aparte en `azure-apps`) |

## Ficheros que NO se tocan

`create_purchase_albaran_use_case.py`, `create_direct_albaran_use_case.py`,
`albaran_domain_models.py`, `albaran_directo_models.py` (el caso de uso nuevo **importa** sus
constantes `_ALBARAN_TIP`, `_MOV_*`, `_POS_STEP`, `_SERIE_PREFIX` y `_r2`; no hereda de la
clase, cuyo SQL vive en línea y no se puede comparar carácter a carácter);
`infrastructure/security/*`; `sql_server_repository.py` (bastan `execute_read_query`,
`read_full_row`, `read_rows_by`, `locate_contract`, `peek_next_ide` y
`run_in_write_transaction`); F-004 y F-006 (se importa `hora_local_de_madrid`); `infra/`.
Sin ficheros `NN_nombre.sql`: el SQL vive como constante en el constructor, como en F-006.

## Modelo de petición (R1, R2)

```python
class LineaAlbaranIn(BaseModel):                  # extra="forbid" en los dos
    referencia_linea: str = Field(..., min_length=1, max_length=64)
    ctrpro_ide: int | None = Field(default=None, ge=1)          # vinculada
    producto: str | None = Field(default=None, min_length=1, max_length=24)  # sin vincular
    descripcion: str | None = Field(default=None, max_length=128)   # dcapro.res
    unidad: str | None = Field(default=None, max_length=8)          # dcapro.unimed
    cantidad: float                                                 # != 0; < 0 = devolución
    precio: float = Field(..., ge=0)
    partida: str | None = Field(default=None, min_length=1, max_length=24)  # obrparpar.cod
    almacen: bool = False                                           # paride 0

class AlbaranCompraRequest(BaseModel):
    database: str; cod_obra: str (≤24); cif_proveedor: str (≤24)
    referencia_externa: str = Field(..., min_length=1, max_length=128)   # dca.synckey
    cod_contrato: str | None = None (≤24); su_referencia: str = "" (≤128)  # dca.entref
    fecha_albaran: int | None (19000101-29991231); empide: int | None (≥1)
    lineas: list[LineaAlbaranIn] = Field(..., min_length=1); commit: bool = False
```

**Una sola lista** con discriminador por línea, no dos (`lineas_recibidas` +
`lineas_sin_contrato` de F-053 §2): conserva el orden del albarán (`pos`). F-053 se alinea
(informe, pregunta 18). El tope de líneas es configuración: se comprueba en el caso de uso.

## Filas que se escriben — origen de cada columna

- **`con`**: clon de la plantilla (como hoy) con `tip 14`, `cod` ← E2, `res` ←
  `"<entres>. (<su_referencia>)"` recortado a la columna, `fec`, `est` ← [M2] validado en
  `conest`.
- **`dca`**: clon de la plantilla con los *overrides* de hoy (`fecdoc`, `hor`, `entref`,
  `eioide`, `ent*`, `obride`, `almide`, `cenide`, `empide`, totales, descuentos a 0,
  `estser/estfac` 0) más `ctride` (0 sin contrato) y **`synckey` ← `referencia_externa`**.
- **`dcapro` vinculada**: como hoy (plantilla = última `dcapro` del producto; `proide`,
  `ivaide`, `unimed`, `almide`, `cenide`, `caaide` y `docori*` del `ctrpro`; `canoriori`,
  `imporiori`) más `paride` (R12-R14), `pre`/`tar`/`dto` (R15), `res`/`unimed` de la petición
  si vienen.
- **`dcapro` sin vincular**: plantilla del producto; `cueide`/`natide`/`ivaide` del maestro
  si ≠ 0 (R11) [M11]; `res`, `unimed`, `pre`, `tar` = `precio`, `dto` `''`, `paride`,
  `almide`, `cenide`, `obride`; `docori*`, `can*`, `impori*` a 0/`''`.
- **Lista de reseteo** (las dos): columnas de la plantilla que describen *otra* línea, a su
  valor inicial. Hipótesis a confirmar con M14 (diff de un albarán del escritorio contra
  `AC26/15951`): `fec`, `pla`, `refent`, `cod2`, `dncide`, `dncproide`, `anades`, `serdes`,
  `parcandes`, `med`, `canmed`, `item`, `pac`, `desesp`, `edilin`, `texcom`, `anexo`,
  `fecimp`, `garfec`, `mesrevpre`, `ejerevpre`, `taride`, `prepma` [M14]. Columna que M14
  no confirme se queda como hoy.
- **`ctrprodes`** (solo vinculadas): como hoy, una por línea, `can` con signo.
- **`mov`**: como hoy (`emp` ← [M2] en vez del `1` literal); una fila por línea [M9].

## Devoluciones (R16) [M5, M6]

Hipótesis **A** (por defecto): la fila de `mov` tiene la forma de una entrada con `canent` =
cantidad (< 0), `cansal` 0, y el PMP se calcula con la misma fórmula; si `stock + can` = 0
el PMP se conserva. Alternativa **B**: `canent` 0, `cansal` = |cantidad|, PMP vigente sin
cambio (y quizá otro `tip`/`oritip`/`destip`). M5 decide entre A y B leyendo devoluciones
reales y el `mov` anterior del mismo (producto, almacén); `siguiente_balance` implementa la
que salga, con su test. Si M5 no encuentra devoluciones reales, pregunta 8. En vinculadas,
M6 confirma que `ctrprodes.can` va con signo y que `canser = Σ ctrprodes.can`.

## Sentencias (constructor puro; todas con `?`)

Lecturas (credenciales de lectura; una vez por petición salvo L8 y L12, una por producto o
por (producto, almacén)). Toda lectura con `truncado` → `ValueError` (400).

- **L1** obra: `SELECT ide, emp, cod FROM dbo.con WHERE tip = ? AND cod = ?` (`[42, cod]`).
- **L2-L4** contrato: `locate_contract` (+ `obride` = L1), `read_full_row(ctr)`,
  `read_rows_by(ctrpro, docide)`, como hoy.
- **L5** plantilla de cabecera: las tres consultas de `_find_template_ide` (con contrato) o la
  de `_find_template_by_cif` (sin él), copiadas literales; `read_full_row` de `con` y `dca`.
- **L6** partidas: `SELECT ide, cod, tip, tipdes FROM dbo.obrparpar WHERE obride = ? AND cod
  IN (?, …)` con los códigos distintos de la petición.
- **L7** productos: `SELECT c.ide, c.cod, c.fecbaj, p.comide, p.ivacomide, p.natide FROM
  dbo.con c JOIN dbo.pro p ON p.ide = c.ide WHERE c.cod IN (?, …)` [M11: `tip`/`emp`].
- **L8** plantilla de línea: `SELECT TOP 1 * FROM dbo.dcapro WHERE proide = ? ORDER BY ide DESC`.
- **L9** tasas: `SELECT ide, iva FROM dbo.iva WHERE ide IN (?, …)` [M11].
- **L10** almacén de la obra: `SELECT ide, cenide FROM dbo.alm WHERE obride = ?` [M8].
- **L11** idempotencia: `SELECT c.ide, c.cod, c.fec, d.entide, d.obride, d.totbas, d.totdoc
  FROM dbo.dca d JOIN dbo.con c ON c.ide = d.ide WHERE c.tip = ? AND d.synckey = ?`; si hay
  uno, sus líneas: `SELECT pos, proide, can, pre, tot, paride, almide FROM dbo.dcapro WHERE
  docide = ? ORDER BY pos`. `synckey` no tiene índice: recorre `dca` [M1 mide el coste].
- **L12** balance: `SELECT TOP 1 almcan, almpma FROM dbo.mov WHERE proide = ? AND almide = ?
  ORDER BY ide DESC` (como hoy).
- **L13** estado: `SELECT est FROM dbo.conest WHERE tip = ? AND est = ?`.
- **L14** (dry-run) `cod` provisional = E2 sin bloqueos, y `peek_next_ide` de las 4 tablas.

Dentro de `work(cursor)`, en este orden: **E1** = L11 (sale sin escribir si aparece);
**E2** `SELECT MAX(TRY_CONVERT(int, SUBSTRING(cod, ?, 40))) FROM dbo.con WITH (UPDLOCK,
HOLDLOCK) WHERE emp = ? AND tip = ? AND cod LIKE ?` (`None` → 1); **E3-E6** `SELECT
ISNULL(MAX(ide), 0) + 1 FROM dbo.<con|dcapro|ctrprodes|mov> WITH (UPDLOCK, HOLDLOCK)`;
**E7** = L12 con `WITH (UPDLOCK, HOLDLOCK)` por (producto, almacén); **E8** `INSERT INTO
dbo.<tabla> (<columnas>) VALUES (?, …)`: `con` → `dca` → `dcapro`×N → `ctrprodes`×M →
`mov`×N; **E9** `UPDATE dbo.ctrpro SET canser = canser + ? WHERE ide = ?`; **E10** `SELECT
SUM(can), SUM(canser), SUM(canfac) FROM dbo.ctrpro WHERE docide = ?`; **E11** `UPDATE
dbo.ctr SET estser = ?, estfac = ? WHERE ide = ?`; **E12** relecturas de R26 (`COUNT(*)`
por clave y `SELECT MIN(canser)` de los `ctrpro` tocados; con `NOCOUNT ON` el `rowcount` no
es fiable).

**Applocks**, siempre en este orden: `SIGRID_REFEXT_14`, `SIGRID_SERIE_14`, `SIGRID_IDE_con`,
`SIGRID_IDE_dcapro`, `SIGRID_IDE_ctrprodes`, `SIGRID_IDE_mov`. Los cuatro últimos son los
nombres y el orden de `sigrid/albaran` y `albaran-directo` (este sin `ctrprodes`), y F-006
comparte solo `SIGRID_IDE_con` tras los suyos propios: no hay orden inverso posible.

## Flujo del caso de uso

1. Tope de líneas; prefijo de la referencia (R27). Con `commit`: llaves, credenciales y base
   (R22). Errores → `AlbaranCompraError` → 400.
2. `ahora` (Madrid) una vez; L1-L5, L11 (en dry-run y en commit: R28 sale ya si aparece), L13.
3. Por línea, en orden: L6-L10 (con caché) y validación (R10-R16); se acumulan **todos** los
   fallos de línea → `lineas_no_validas` con `details.lineas`.
4. Construcción pura de filas con balances leídos (L12) → si dry-run, `previsto` con L14.
5. Si commit, `run_in_write_transaction(work)`; `work` es **reentrante**: las filas se
   reconstruyen en cada intento con `cod`, `ide` y balances leídos dentro (E2-E7); `fec`,
   `hor` y `fechor` no cambian entre intentos. `IntegrityError` agotado → `colision_de_clave`.
6. Traza (R30) y respuesta.

## Códigos (R4)

Cabecera: `escritura_albaranes_deshabilitada`, `base_de_datos_no_permitida`,
`demasiadas_lineas`, `referencia_no_permitida`, `referencia_en_conflicto`,
`obra_no_encontrada`, `obra_ambigua`, `contrato_no_encontrado`, `contrato_ambiguo`,
`proveedor_sin_albaran_previo`, `estado_inicial_no_encontrado`,
`almacen_de_obra_no_resuelto`, `colision_de_clave`, `filas_afectadas_inesperadas`,
`lineas_no_validas`. Línea: `linea_no_es_del_contrato`, `producto_no_permitido`,
`producto_no_encontrado`, `partida_no_encontrada`, `partida_ambigua`,
`partida_no_imputable`, `devolucion_supera_lo_servido`. Avisos: `plantilla_de_otro_proveedor`,
`producto_sin_historico`, `supera_pendiente`, `partida_distinta_del_contrato`,
`precio_distinto_del_contrato`, `stock_negativo`, `cod_provisional`.

## Equivalencia con el núcleo actual (R31)

El test arma un doble del repositorio con un contrato, su plantilla y sus balances, lanza el
mismo albarán por `CreatePurchaseAlbaranUseCase` y por el nuevo (dry-run los dos) y compara
`con`, `dca`, `dcapro`, `ctrprodes` y `mov` columna a columna. Diferencias **declaradas**, y
ninguna más: `synckey`, `hor`/`fechor` (Madrid frente a hora del servidor, que en Azure es
UTC), `est` y `mov.emp` [M2], las columnas de la lista de reseteo [M14], `ivacuo` (tasa de
`dbo.iva` frente al cociente `ivacuo/tot` del `ctrpro`, que no sirve con `tot` 0) y el
`paride` cuando el `ctrpro` lo trae `NULL` (hoy se queda el de la plantilla) [M4].

## Riesgos y decisiones

- **Doble alta**: cerrada por `synckey` comprobado dentro de la transacción bajo
  `SIGRID_REFEXT_14`. El escritorio no escribe `synckey` [M1]: no hay carrera con él.
- **Colisión con el escritorio**: si da de alta el mismo `cod`, el índice único `(emp, tip,
  cod)` de `con` [M2] hace fallar el segundo `INSERT`; nosotros reintentamos (R25). Hoy los
  albaranes calculan el `cod` fuera de la transacción: carrera que aquí se cierra.
- **Bloqueos**: el `HOLDLOCK` del prefijo `AC<aa>/` y del último `ide` de cada tabla dura
  milisegundos; la transacción no lee catálogos (todo se lee antes, salvo E1, E2-E7).
- **Fecha atrasada**: el `mov` se encadena con el último por `ide`, como hoy; si el escritorio
  recalcula los movimientos posteriores al insertar con fecha anterior (M10), aquí no se hace
  (fuera de alcance, pregunta 11).
- **`synckey` sin índice**: L11/E1 recorren `dca`; M1 mide cuánto. Si es caro, se acota por
  `entide` (sí indexable vía `con`) sin cambiar el contrato.
- **Descartado**: ampliar `sigrid/albaran` (ver arriba); reutilizar `albaran-directo` (exige
  `proide` y hereda la partida de la última `dcapro`); clonar la línea entera sin lista de
  reseteo (arrastra medición, analítica y desglose de otra obra); un albarán por partida
  (F-053 lo descartó); escribir `dcapropar` y `log` sin que M7/M13 lo pidan.
