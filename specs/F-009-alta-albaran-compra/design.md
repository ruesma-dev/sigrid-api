<!-- specs/F-009-alta-albaran-compra/design.md -->
# F-009 · Diseño (v4)

## La decisión de fondo

**Se amplía `POST /api/sigrid/albaran` con un segundo modo** (decisión del humano, 2026-10-01,
pregunta 1). El endpoint tiene dos modos, decididos **antes de validar nada** por una función
pura sobre el cuerpo ya parseado:

```python
def elegir_modo_albaran(cuerpo: object) -> Literal["clasico", "extendido"]:
    if not isinstance(cuerpo, dict):            # lo que hoy rechaza Pydantic, igual que hoy
        return "clasico"
    nuevas = {"lineas", "referencia_externa"} & cuerpo.keys()
    if nuevas and "lineas_recibidas" in cuerpo:
        raise AlbaranCompraError("...", codigo="peticion_mixta")
    return "extendido" if nuevas else "clasico"
```

- **Por claves, no por valores**: `{"lineas": []}` o `"referencia_externa": null` ya son modo
  extendido (y Pydantic los rechaza ahí con 400). Así ningún valor vacío cambia de modo en
  silencio. Las claves del modo clásico (`cod_contrato`, `cod_obra`, `cif_proveedor`,
  `su_referencia`, `fecha_albaran`, `empide`, `commit`, `database`) existen en los dos modos y
  no deciden nada; `lineas_recibidas` solo existe en el clásico, `lineas` y
  `referencia_externa` solo en el extendido.
- **Peticiones mixtas** (`lineas_recibidas` con `lineas` o con `referencia_externa`): 400
  `peticion_mixta` sin leer la base. Hoy el modelo clásico **ignora** las claves que no conoce,
  así que esa misma petición se procesaría como clásica olvidando `lineas`: rechazarla es el
  único cambio de comportamiento visible, y solo afecta a cuerpos que mezclan los dos contratos.
- **Modo clásico**: la ruta llama a `AddPurchaseAlbaranRequest` y a `CreatePurchaseAlbaranUseCase`
  **sin modificarlos** (R2, R4). Su salida la fija un test de caracterización escrito antes de
  tocar nada (§Caracterización), incluida la suma de `lineas_recibidas` del mismo `ctrpro`.
- **Modo extendido**: modelo, constructor puro de sentencias y caso de uso **nuevos**, llamados
  desde la misma ruta. Conservan las reglas del núcleo probado en junio (`AC26/15950-15952`):
  plantillas de cabecera y de línea, `mov` con PMP sin redondear, `ctrprodes`, `canser`
  relativo y `estser/estfac` por sumas; R33 lo demuestra con un test de equivalencia contra el
  modo clásico. No se mete en `CreatePurchaseAlbaranUseCase` porque eso obligaría a reabrir sus
  600 líneas (sin un test hoy) y el SQL en línea no se puede comparar carácter a carácter.
- **Límite de microservicio: cabe.** Dar de alta un concepto con sus efectos (stock, medición
  del contrato) es de la pasarela; qué se registra y a qué precio lo decide el llamante (sv9).

## Ficheros a crear

| Fichero | Capa | Qué contiene |
|---|---|---|
| `domain/models/albaran_compra_models.py` | domain | `elegir_modo_albaran`, `LineaAlbaranIn`, `AlbaranCompraRequest` (validadores de R6), `AvisoAlbaran`, `LineaResultado(AlbaranLinePreview)`, `FalloLinea`, `AlbaranCompraResponse(AddPurchaseAlbaranResponse)`, `AlbaranCompraError(ValueError)` con `codigo` cerrado y `lineas` opcional. **Importa** los modelos clásicos; no los edita |
| `application/use_cases/albaran_compra_statements.py` | application | `AlbaranCompraStatements(database)`: SQL constante L1-L14 y E1-E12; puras `siguiente_cod`, `siguiente_balance`, `estados_contrato`, `importe_linea` y constructores de filas. Sin E/S; se autovalida con `DatabaseReferenceGuard` |
| `application/use_cases/create_albaran_compra_use_case.py` | application | `CreateAlbaranCompraUseCase(repository, settings, ahora_utc=..., reloj=...)` |
| `tests/test_f009_caracterizacion.py` + `tests/fixtures/f009_caracterizacion.json` | — | §Caracterización |
| `tests/test_f009_settings.py`, `_models.py`, `_statements.py`, `_use_case.py`, `_route.py`, `_equivalencia.py` | — | Ver `tasks.md` |

## Ficheros a modificar

| Fichero | Qué cambia |
|---|---|
| `config/settings.py` | Cuatro campos de R10; las dos listas de texto reutilizan `parse_string_list` |
| `function_app.py` | `sigrid_albaran`: `elegir_modo_albaran(body)`; clásico → el camino de hoy; extendido → `CreateAlbaranCompraUseCase`. `sigrid_albaran` y `sigrid_albaran_directo`: guarda R8 **después** de validar el modelo y **antes** de `use_case.run`, solo si `request_model.commit`. `AlbaranCompraError` → 400 `details:{type, codigo[, lineas]}`; `IntegrityError` agotado → 400 `colision_de_clave`. Los `except` existentes no cambian |
| `local.settings.sample.json`, `docs/ARCHITECTURE.md` | Claves nuevas; modos de la ruta, modelo y caso de uso nuevos |
| `azure-apps/sigrid_api.md` | R36 (commit aparte en `azure-apps`) |

## Ficheros que NO se tocan

`create_purchase_albaran_use_case.py`, `create_direct_albaran_use_case.py`,
`albaran_domain_models.py`, `albaran_directo_models.py` (se **importan** sus constantes y
modelos), `infrastructure/security/*`, `sql_server_repository.py` (bastan `execute_read_query`,
`read_full_row`, `read_rows_by`, `locate_contract`, `peek_next_ide` y
`run_in_write_transaction`), F-004 y F-006 (se importa `hora_local_de_madrid`), `infra/`,
`CLAUDE.md` (la lista de rutas no cambia). Sin ficheros `NN_nombre.sql`: SQL constante.

## Caracterización (R2-R4)

Se escribe **en T1, sobre el código de `dev` y antes de cualquier cambio de producción**, y se
commitea junto con su fichero dorado. Un doble del repositorio graba cada llamada (método,
argumentos, SQL y parámetros del cursor de `run_in_write_transaction`) y devuelve datos fijos
(un contrato con tres `ctrpro`, plantillas, balances); `datetime` del módulo clásico se fija
con `monkeypatch`. Casos: clásico dry-run; clásico commit con dos `lineas_recibidas` al mismo
`ctrpro` (suma) y una que supera lo pendiente (aviso); clásico con contrato inexistente y con
línea ajena (400 y su texto); directo dry-run y commit. Compara la respuesta JSON y la secuencia
de llamadas con el dorado. Tras T1 **el dorado no se regenera**: el reviewer comprueba con
`git log -- tests/fixtures/f009_caracterizacion.json` que solo lo toca el commit de T1. Los
casos de commit corren con la llave R8 abierta en el doble de `Settings`.

## Modelo de petición del modo extendido (R5, R6)

```python
class LineaAlbaranIn(BaseModel):                  # extra="forbid" en los dos
    referencia_linea: str = Field(..., min_length=1, max_length=64)
    ctrpro_ide: int | None = Field(default=None, ge=1)                       # vinculada
    producto: str | None = Field(default=None, min_length=1, max_length=24)  # sin vincular
    descripcion: str | None = Field(default=None, max_length=128)            # dcapro.res
    unidad: str | None = Field(default=None, max_length=8)                   # dcapro.unimed
    cantidad: float                                       # != 0; < 0 = devolución (los dos tipos)
    precio: float = Field(..., ge=0)
    partida: str | None = Field(default=None, min_length=1, max_length=24)   # obrparpar.cod
    almacen: bool = False                                                    # paride 0

class AlbaranCompraRequest(BaseModel):
    database: str; cod_obra: str (≤24); cif_proveedor: str (≤24); usu: str (1-24)  # log.usu
    referencia_externa: str = Field(..., min_length=1, max_length=128)       # dca.synckey
    cod_contrato: str | None = None (≤24); su_referencia: str = "" (≤128)   # dca.entref
    fecha_albaran: int | None (19000101-29991231); empide: int | None (≥1)
    lineas: list[LineaAlbaranIn] = Field(..., min_length=1); commit: bool = False
```

Una sola lista con discriminador por línea: conserva el orden del albarán (`pos`). El tope de
líneas es configuración y lo comprueba el caso de uso.

## Filas que se escriben — origen de cada columna (T0 en `progress/spec_F-009.md` §Resultados)

- **`con`**: clon de la plantilla (como hoy) con `tip 14`, `cod` ← E2, `res` ←
  `"<entres>. (<su_referencia>)"` recortado a la columna, `fec`, `est` = 1 `PDT` validado en
  `conest` (M2: estados 1 PDT, 2 COM, 3 CON, 10 FAC; `sercon.estini` 0 no es un estado) [M13].
- **`dca`**: clon de la plantilla **del mismo proveedor** (M14: la cabecera lleva forma de pago,
  efecto y dirección del proveedor) con los *overrides* de hoy (`fecdoc`, `hor`, `entref`,
  `eioide`, `ent*`, `obride`, `almide`, `cenide`, `empide`, totales, descuentos a 0,
  `estser/estfac` 0) más `ctride` (0 sin contrato) y **`synckey` ← `referencia_externa`**.
- **`dcapro` vinculada**: como hoy (plantilla = última `dcapro` del producto; `proide`, `ivaide`,
  `unimed`, `almide`, `cenide`, `caaide` y `docori*` del `ctrpro`, que nunca los trae `NULL`
  según M4; `canoriori`, `imporiori`) más `paride`, `pre`/`tar`/`dto` y `res`/`unimed`.
- **`dcapro` sin vincular**: plantilla = última `dcapro` del producto **de esa empresa**
  (`cueide`, `ivaide`); `natide` del maestro; `res`, `unimed`, `pre`, `tar` = `precio`, `dto`
  `''`, `paride`, `almide`, `cenide`, `obride`; `docori*`, `can*`, `impori*` a 0/`''`.
- **`prepma`** (las dos): el PMP resultante de su `mov` (M14: el de la API arrastraba el de la
  plantilla) [M14]. El resto de columnas de la plantilla, como hoy: M14 no encontró diferencias.
- **`ctrprodes`** (vinculadas): como hoy, una por línea, `can` con signo (M6: 20 de 20).
- **`mov`**: como hoy, con `emp` = `con.emp` (M2: siempre 1); solo si el producto hace
  movimientos [M9: en M5 las 6 devoluciones sin `mov` eran todas de un mismo producto].
- **`log`** (alta, M13: el escritorio la escribe): la fila de F-006 con `tab 'con'`, `tip 14`,
  `ope 1`, `ori` [M13], `cod`, `res` y `est` del `con`, `fec`/`hor` del alta y `usu` de la petición.

## Devoluciones (R18, R20) — cerrado con M5 y M6

**Regla A medida** (13 de las 13 devoluciones de la muestra que tienen `mov`): fila de entrada
(`tip 1`, `oritip 5`, `destip 2`) con `canent` = cantidad (< 0), `cansal` 0 y el PMP de la
fórmula de alta; si `stock + can` = 0 el PMP se conserva. La única «?» de la muestra era un
albarán con fecha atrasada (comparado con el `mov` anterior por `ide`, no por fecha: ver M10).
Vinculadas: `ctrprodes.can` con signo, `canser += cantidad` aunque quede < 0 (M6: hay 750
`ctrpro` así), aviso `servido_negativo`, y `estser` con la regla de hoy. T24 sigue vigilando la
primera devolución real del pipeline.

## Fecha atrasada (R19) — decidido: N1 (b)

M10: Sigrid mantiene `almcan`/`almpma` en orden de **`fechor`** (0 roturas en las 3 series; por
`ide`, 1 rotura en 2): al dar de alta con fecha anterior, el escritorio **recalcula los `mov`
posteriores**. Hoy la API encadena con el último por `ide` y pone `fechor` = fecha del albarán:
rompe la cadena. Los albaranes del pipeline llegan siempre con fecha atrasada. **Decisión del
humano (2026-10-02), opción (b):** el `mov` se fecha en el momento del alta (`mov.fec`, `hor` y
`fechor` = ahora, hora de Madrid, los mismos de R22); el albarán conserva su fecha (`con.fec`,
`dca.fecdoc` = `fecha_albaran`). La cadena queda bien sin tocar otras filas y **no** se
recalculan `mov` posteriores; el stock por fechas sitúa la entrada el día del alta (aceptado).
L12/E7 leen el último `mov` del (producto, almacén) por `fechor DESC, ide DESC`. Descartadas:
(a) recalcular los posteriores (`UPDATE` de decenas a cientos de `mov`) y (c) como hoy.

## Sentencias (constructor puro; todas con `?`)

Lecturas con credenciales de lectura; toda lectura con `truncado` → `ValueError` (400).

- **L1** obra: `SELECT ide, emp, cod FROM dbo.con WHERE tip = ? AND cod = ?` (`[42, cod]`).
- **L2-L4** contrato: `locate_contract` (+ `obride` = L1), `read_full_row(ctr)`,
  `read_rows_by(ctrpro, docide)`, como hoy.
- **L5** plantilla de cabecera: `SELECT TOP 1 c.ide FROM dbo.con c JOIN dbo.dca d ON d.ide =
  c.ide WHERE c.tip = ? AND d.entide = ? ORDER BY c.ide DESC` con el `entide` del contrato o,
  sin él, la consulta por `entcif` de hoy; sin los *fallbacks* a otro proveedor.
- **L6** partidas: `SELECT ide, cod, tip, tipdes, tipvis FROM dbo.obrparpar WHERE obride = ? AND
  cod IN (?, …)` con los códigos distintos de la petición; imputable = `tip 1`, `tipdes 0`,
  `tipvis` 0/1 (M3: el 100 % de las usadas) [M3: repetidos entre imputables].
- **L7** productos: `SELECT c.ide, c.cod, c.fecbaj, p.natide, p.tipmov FROM dbo.con c JOIN dbo.pro
  p ON p.ide = c.ide WHERE c.emp = ? AND c.tip = ? AND c.cod IN (?, …)` (`tip 3`) [M9: `tipmov`].
- **L8** plantilla de línea: `SELECT TOP 1 * FROM dbo.dcapro WHERE proide = ? ORDER BY ide DESC`.
- **L9** tasas: `SELECT ide, iva FROM dbo.iva WHERE ide IN (?, …)` (fracción) [M11].
- **L10** almacén de la obra: `SELECT ide, cenide FROM dbo.alm WHERE obride = ?` (M8: uno en 649
  obras, dos en 5).
- **L11** idempotencia: `SELECT c.ide, c.cod, c.fec, d.entide, d.obride, d.totbas, d.totdoc
  FROM dbo.dca d JOIN dbo.con c ON c.ide = d.ide WHERE c.tip = ? AND d.synckey = ?` (M1: libre,
  0,1 s sin índice); si hay uno, `SELECT pos, proide, can, pre, tot, paride, almide FROM
  dbo.dcapro WHERE docide = ? ORDER BY pos`.
- **L12** balance: `SELECT TOP 1 almcan, almpma FROM dbo.mov WHERE proide = ? AND almide = ?
  ORDER BY fechor DESC, ide DESC` (N1).
- **L13** estado y usuario: `SELECT est FROM dbo.conest WHERE tip = ? AND est = ?`;
  `SELECT TOP (1) cod FROM dbo.usu WHERE cod = ?`.
- **L14** (dry-run) `cod` provisional = E2 sin bloqueos, y `peek_next_ide` de las 5 tablas.

Dentro de `work(cursor)`, en orden: **E1** = L11 (sale sin escribir si aparece); **E2**
`SELECT MAX(TRY_CONVERT(int, SUBSTRING(cod, ?, 40))) FROM dbo.con WITH (UPDLOCK, HOLDLOCK)
WHERE emp = ? AND tip = ? AND cod LIKE ?` (`None` → 1); **E3-E6** `SELECT ISNULL(MAX(ide), 0)
+ 1 FROM dbo.<con|dcapro|ctrprodes|mov> WITH (UPDLOCK, HOLDLOCK)`; **E7** = L12 con `WITH
(UPDLOCK, HOLDLOCK)`; **E8** `INSERT INTO dbo.<tabla> (<columnas>) VALUES (?, …)`: `con` →
`dca` → `dcapro`×N → `ctrprodes`×M → `mov`×K; **E9** `UPDATE dbo.ctrpro SET canser = canser +
? WHERE ide = ?`; **E10** `SELECT SUM(can), SUM(canser), SUM(canfac) FROM dbo.ctrpro WHERE
docide = ?`; **E11** `UPDATE dbo.ctr SET estser = ?, estfac = ? WHERE ide = ?`; **E11b**
`log`: `MAX(ide)+1 WITH (UPDLOCK, HOLDLOCK)` e `INSERT`, al final (F-006: la cola de `log` la
comparte todo el ERP); **E12** relecturas de R28 con `COUNT(*)` por clave.

**Applocks**, siempre en este orden: `SIGRID_REFEXT_14`, `SIGRID_SERIE_14`, `SIGRID_IDE_con`,
`SIGRID_IDE_dcapro`, `SIGRID_IDE_ctrprodes`, `SIGRID_IDE_mov`, `SIGRID_IDE_log`. Los cuatro
del medio son los del modo clásico y `albaran-directo`, en su orden; F-006 toma `SIGRID_IDE_con`
y `SIGRID_IDE_log` en el mismo orden relativo: no hay orden inverso posible.

## Flujo del modo extendido

1. Tope de líneas y prefijo de la referencia (R24, R29). Con `commit`: llaves, credenciales y
   base (R24). Errores → `AlbaranCompraError` → 400.
2. `ahora` (Madrid) una vez; L1-L5, L11 (R30 sale ya si aparece), L13.
3. Por línea, en orden: L6-L10 (con caché) y validación (R12-R18); se acumulan **todos** los
   fallos → `lineas_no_validas` con `details.lineas`.
4. Construcción pura de filas con balances de L12 → si dry-run, `previsto` con L14.
5. Si commit, `run_in_write_transaction(work)`; `work` es **reentrante**: reconstruye las filas
   en cada intento con `cod`, `ide` y balances de E2-E7; las fechas no cambian.
   `IntegrityError` agotado → `colision_de_clave`.
6. Traza (R32) y respuesta.

## Códigos (R1, R8, R9)

Cabecera: `peticion_mixta`, `escritura_albaranes_deshabilitada`, `base_de_datos_no_permitida`,
`demasiadas_lineas`, `referencia_no_permitida`, `referencia_en_conflicto`, `obra_no_encontrada`,
`obra_ambigua`, `contrato_no_encontrado`, `contrato_ambiguo`, `usuario_no_valido`,
`proveedor_sin_albaran_previo`, `estado_inicial_no_encontrado`, `almacen_de_obra_no_resuelto`,
`colision_de_clave`, `filas_afectadas_inesperadas`, `lineas_no_validas`. Línea:
`linea_no_es_del_contrato`, `producto_no_permitido`, `producto_no_encontrado`,
`partida_no_encontrada`, `partida_ambigua`, `partida_no_imputable`. Avisos:
`producto_sin_historico`, `supera_pendiente`, `partida_distinta_del_contrato`,
`precio_distinto_del_contrato`, `servido_negativo`, `stock_negativo`, `cod_provisional`.

## Equivalencia con el modo clásico (R33)

Mismo doble del repositorio; el mismo albarán (solo vinculadas, positivas, sin `ctrpro`
repetido, partida y precio del `ctrpro`, proveedor con albarán previo) en dry-run por los dos
modos; se comparan `con`, `dca`, `dcapro`, `ctrprodes` y `mov` columna a columna. Diferencias
**declaradas**, y ninguna más: `synckey`, `hor`/`fechor` (Madrid frente a la hora del servidor,
UTC en Azure; y `mov.fec`/`fechor` del alta, N1), `est`, `prepma`, `ivacuo` (`dbo.iva` frente al cociente `ivacuo/tot` del
`ctrpro`) y la fila de `log`, que el clásico no escribe.

## Riesgos y decisiones

- **Retrocompatibilidad**: la garantiza el dorado de T1. El único cambio observable del modo
  clásico y de `albaran-directo` es R8 y `peticion_mixta`; los dos se despliegan con la llave
  en `false`, que deja cerrado su `commit` hasta que el humano la abra.
- **Doble alta**: `synckey` comprobado dentro de la transacción bajo `SIGRID_REFEXT_14` (M1:
  nadie más lo usa). **Colisión con el escritorio**: índice único `(emp, tip, cod)` + reintento.
- **Bloqueos**: `HOLDLOCK` del prefijo y del último `ide` de cada tabla, milisegundos; `log`, al
  final.
- **Stock negativo** (M15: 748 `mov` desde 2025): solo aviso, como el escritorio.
- **Descartado**: ruta nueva; modo por valores; meter el modo en `CreatePurchaseAlbaranUseCase`;
  reutilizar `albaran-directo`; la plantilla de otro proveedor (M14); `dcapropar` sin M7.
