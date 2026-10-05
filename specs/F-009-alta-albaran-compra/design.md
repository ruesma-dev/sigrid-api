<!-- specs/F-009-alta-albaran-compra/design.md -->
# F-009 · Diseño (v5.1)

Detalle campo a campo, casos de línea, mapa de códigos a estados de F-053 y ejemplos:
[`contrato_albaranes.md`](contrato_albaranes.md) (refleja esta v5.1; si discrepa, manda esta spec).

## La decisión de fondo

**Se amplía `POST /api/sigrid/albaran` con un segundo modo** (humano, 2026-10-01). El modo se decide
**antes de validar nada** por una función pura sobre el cuerpo ya parseado:

```python
def elegir_modo_albaran(cuerpo: object) -> Literal["clasico", "extendido"]:
    if not isinstance(cuerpo, dict):            # lo que hoy rechaza Pydantic, igual que hoy
        return "clasico"
    nuevas = {"lineas", "referencia_externa"} & cuerpo.keys()
    if nuevas and "lineas_recibidas" in cuerpo:
        raise AlbaranCompraError("...", codigo="peticion_mixta")
    return "extendido" if nuevas else "clasico"
```

- **Por claves, no por valores**: `{"lineas": []}` ya es extendido (y Pydantic lo rechaza ahí); las claves
  comunes no deciden nada. El clásico **ignora** claves desconocidas: una petición mixta se procesaría
  olvidando `lineas`; rechazarla (`peticion_mixta`) es el único cambio visible del clásico.
- **Modo clásico**: la ruta llama a `AddPurchaseAlbaranRequest` y `CreatePurchaseAlbaranUseCase` **sin
  modificarlos** (R2, R4), fijados por el test de caracterización (§Caracterización).
- **Modo extendido**: modelo, constructor de sentencias y caso de uso **nuevos**, con el núcleo probado en
  junio (`AC26/15950-15952`; R33 lo demuestra). No va dentro de `CreatePurchaseAlbaranUseCase`: obligaría
  a reabrir 600 líneas sin test y su SQL en línea no se puede comparar.
- **Límite de microservicio: cabe.** Dar de alta un concepto con sus efectos (stock, medición) es de la
  pasarela; qué se registra y a qué precio lo decide el llamante (sv9). Ningún hueco H1-H33 lo cambia.

## Ficheros a crear

| Fichero | Capa | Qué contiene |
|---|---|---|
| `domain/models/albaran_compra_models.py` | domain | `elegir_modo_albaran`, `LineaAlbaranIn`, `AlbaranCompraRequest` (validadores de R5-R6), `AvisoAlbaran`, `LineaResultado(AlbaranLinePreview)`, `FalloLinea`, `AlbaranCompraResponse(AddPurchaseAlbaranResponse)`, `AlbaranCompraError(ValueError)` con `codigo` cerrado y `lineas` opcional, `COLUMNAS_BANCARIAS`. **Importa** los modelos clásicos; no los edita |
| `application/use_cases/albaran_compra_statements.py` | application | `AlbaranCompraStatements(database)`: SQL constante L1-L14 y E1-E12; puras `siguiente_cod`, `siguiente_balance`, `estados_contrato`, `importe_linea`, `redondear_euros` y constructores de filas. Sin E/S; se autovalida con `DatabaseReferenceGuard` |
| `application/use_cases/create_albaran_compra_use_case.py` | application | `CreateAlbaranCompraUseCase(repository, settings, ahora_utc=..., reloj=...)` |
| `tests/test_f009_caracterizacion.py` + `tests/fixtures/f009_caracterizacion.json` | — | §Caracterización |
| `tests/test_f009_settings.py`, `_models.py`, `_statements.py`, `_use_case.py`, `_route.py`, `_equivalencia.py` | — | Ver `tasks.md` |

## Ficheros a modificar

| Fichero | Qué cambia |
|---|---|
| `config/settings.py` | Cinco campos de R10; las listas de texto con `parse_string_list`, `SIGRID_ALBARAN_EMPRESAS_OBRA` con `parse_int_list` |
| `function_app.py` | `sigrid_albaran`: `elegir_modo_albaran(body)`; clásico → el camino de hoy; extendido → `CreateAlbaranCompraUseCase`. Guarda R8 en `sigrid_albaran` y `sigrid_albaran_directo` **después** de validar el modelo y **antes** de `use_case.run`, solo si `commit`. `AlbaranCompraError` → 400 `details:{type, codigo[, lineas]}`; `IntegrityError` agotado → `colision_de_clave`. Docstring de `sigrid_albaran` corregido (no replica todas las líneas del contrato; H32). Los `except` existentes no cambian |
| `local.settings.sample.json`, `docs/ARCHITECTURE.md` | Claves nuevas; modos de la ruta, modelo y caso de uso nuevos |
| `azure-apps/sigrid_api.md` | R36 (commit aparte en `azure-apps`) |

## Ficheros que NO se tocan

`create_purchase_albaran_use_case.py`, `create_direct_albaran_use_case.py`, `albaran_domain_models.py`,
`albaran_directo_models.py` (se **importan**), `infrastructure/security/*`, `sql_server_repository.py`
(bastan `execute_read_query`, `read_full_row`, `read_rows_by`, `locate_contract`, `peek_next_ide` y
`run_in_write_transaction`), F-004 y F-006 (se importa `hora_local_de_madrid`), `infra/`, `CLAUDE.md`.
Sin ficheros `NN_nombre.sql`: SQL constante.

## Caracterización (R2-R4)

En T1, **sobre `dev` y antes de cualquier cambio de producción**, con su dorado. Un doble del repositorio
graba cada llamada (método, argumentos, SQL y parámetros) y devuelve datos fijos; `datetime` se fija con
`monkeypatch`. Casos: clásico dry-run; commit con dos `lineas_recibidas` al mismo `ctrpro` (suma) y una
que supera lo pendiente; contrato inexistente y línea ajena; directo dry-run y commit (llave R8 abierta en
el doble). **El dorado no se regenera**: `git log -- tests/fixtures/f009_caracterizacion.json` = solo T1.

## Modelo de petición del modo extendido (R5, R6)

```python
class LineaAlbaranIn(BaseModel):                  # extra="forbid" en los dos; floats finitos
    referencia_linea: str = Field(..., min_length=1, max_length=64)          # 24 si M18 (R30b)
    ctrpro_ide: int | None = Field(default=None, ge=1)                       # vinculada
    producto: str | None = Field(default=None, min_length=1, max_length=24)  # sin vincular
    descripcion: str | None = Field(default=None, max_length=128)            # dcapro.res
    unidad: str | None = Field(default=None, max_length=8)                   # dcapro.unimed
    cantidad: float                                       # != 0; < 0 = devolución (los dos tipos)
    precio: float                                         # < 0 → fallo de línea precio_negativo
    partida: str | None = Field(default=None, min_length=1, max_length=24)   # None ⇒ sin partida, paride 0
    paride: int | None = Field(default=None, ge=1)        # SOLO si M3 (R14b); exige partida

class AlbaranCompraRequest(BaseModel):
    database: str; cod_obra: str (≤24); usu: str (1-24)                      # log.usu
    cif_proveedor: str (≤24; validador: mayúsculas y sin espacios, H21)
    referencia_externa: str = Field(..., min_length=1, max_length=128)       # dca.synckey
    cod_contrato: str | None = None (≤24); su_referencia: str = "" (≤128)   # dca.entref
    fecha_albaran: int | None (19000101-29991231); empide: int | None (≥1)
    lineas: list[LineaAlbaranIn] = Field(..., min_length=1); commit: bool = False
```

Una lista con discriminador por línea conserva el orden (`pos`). Precio negativo y tope de líneas, en el
caso de uso con código. v5.1: sin campo `almacen` y sin rechazo de fechas futuras (solo el rango de arriba).

## Respuesta (R7, R30)

- **Cabecera**: todos los campos de `AddPurchaseAlbaranResponse` + `estado`, `referencia_externa`,
  `avisos[]` y `filas` (`con`, `dca`, `dcapro[]`, `ctrprodes[]`, `mov[]`, `log`). **Línea**: todos los de
  `AlbaranLinePreview` (`ctrpro_ide`/`linoriide` 0 en sin vincular) + `indice` (0..N-1), `referencia_linea`,
  `tipo` (`vinculada`|`sin_vincular`), `producto`, `paride`/`partida` (0/`null` sin partida), `cenide`, `avisos[]`.
- **Avisos** (H27): `AvisoAlbaran{codigo, mensaje}` en cabecera y línea; `warnings` = los `mensaje` de
  todos los avisos, en orden, y nada más (el texto de dry-run va en `cod_provisional`).
- **Columnas bancarias** (H16): `COLUMNAS_BANCARIAS` = `banide`, `banban`, `bansuc`, `bandig`, `bancue`,
  `ban`, `bantipide`, `cpapai`, `cpaban`, `cpasuc`, `cpaswi`, `cpatip`, `cpadiv`, `cpacue1`, `cpacue2`
  (diccionario, `dca`). Se quitan de `cabecera`, `filas.dca` y trazas; la fila escrita las lleva.
- **`idempotente`** (H18): `committed` `false`, `dry_run` = `not commit`, `con_ide`, `cod`, `fec`, totales
  de L11 y `lineas` leídas por `pos` (`indice` 0.., `pos`, `proide`, `cantidad`, `precio`, `total`,
  `paride`, `almide`, y `referencia_linea` si R30b/M18); el resto de campos, vacíos (`{}`/`[]`).

## Filas que se escriben (T0 en `progress/spec_F-009.md` §Resultados)

- **`con`**: clon de la plantilla (L5: mismo proveedor y empresa, H3) con `tip 14`, `emp` de la obra,
  `cod` ← E2, `res` ← `"<entres>. (<su_referencia>)"` recortado, `fec`, `est` 1 `PDT` en `conest` [M13].
- **`dca`**: clon de esa plantilla (M14: forma de pago, efecto y dirección del proveedor) con los
  *overrides* de hoy (`fecdoc`, `hor`, `entref`, `eioide`, `ent*`, `obride`, `almide`, `cenide`, `empide`,
  totales, descuentos a 0, `estser/estfac` 0) más `ctride` (0 sin contrato) y `synckey`.
- **`dcapro` vinculada**: como hoy (plantilla = última `dcapro` del producto; `proide`, `ivaide`,
  `unimed`, `almide`, `cenide`, `caaide` y `docori*` del `ctrpro`, nunca `NULL` según M4; `canoriori`,
  `imporiori`) más `paride`, `pre`/`tar`/`dto` (R17), `res`/`unimed` y `caaide` de §Analítica.
- **`dcapro` sin vincular**: plantilla = L8b (última del producto **del mismo proveedor**) o, sin ella,
  L8 con aviso `iva_de_otro_proveedor` (H15): de ella `cueide`, `ivaide`; `natide` del maestro; `res`,
  `unimed`, `pre`, `tar` = `precio`, `dto` `''`, `paride`, `almide`/`cenide` (R15), `caaide`, `obride`;
  `docori*`, `can*`, `impori*` a 0/`''`; y §Reseteo.
- **`prepma`** (las dos): PMP resultante de su `mov` [M14]. **`ctrprodes`** (vinculadas): una por línea,
  `can` con signo (M6). **`mov`**: como hoy, `emp` = `con.emp`, solo si el producto hace movimientos [M9].
- **`log`** (alta): la de F-006 (`tab 'con'`, `tip 14`, `ope 1`, `ori` [M13]), `cod`/`res`/`est` del
  `con`, `fec`/`hor` del alta y `usu`.

**Reseteo (sin vincular; H11) [M14]**: `med` NULL; `canmed`, `parcandes`, `anades`, `serdes`, `fecimp`,
`item`, `anexo`, `taride`, `fec`, `pla` a 0; `tex`, `texcom`, `cod2`, `pac`, `refent` a `''` (`refent`,
salvo R30b). Lista cerrada: si M14 ampliada muestra que el escritorio rellena alguna, se corrige la spec.

**Analítica (`caaide`; H10) [M16]**. Hipótesis: línea con partida → `obrparpar.caaide` de la partida
resuelta (L6) si ≠ 0; sin partida → `alm.caaproide` de su almacén (L10); vinculada con la misma partida
del `ctrpro` → `ctrpro.caaide`, como hoy (R33); si no, el de la plantilla. Si M16 la contradice, PARADA.

**Importes (R17; H14, H33)**: `redondear_euros(x)` = `Decimal(repr(x)).quantize(Decimal("0.01"),
ROUND_HALF_UP)`; `tot` = `redondear_euros(cantidad·pre)` e `ivacuo` = `redondear_euros(tot·iva)`; test con
el empate 2,675 → 2,68 (`round` da 2,67). Vinculada con |`precio` − `ctrpro.pre`| ≤ 0,0001 (la de M4):
`pre` = `ctrpro.pre` y `tar`/`dto` del `ctrpro`.

## Devoluciones (R18, R20) y fecha atrasada (R19)

**Regla A** (M5): entrada (`tip 1`, `oritip 5`, `destip 2`) con `canent` < 0, `cansal` 0 y PMP de alta;
`canser` < 0 admitido (M6); T24 vigila la primera devolución real. **N1 (b)**: el escritorio recalcula los
`mov` posteriores (M10); aquí el `mov` se fecha en el alta y el albarán conserva su fecha; L12/E7 por
`fechor DESC, ide DESC`. Razonamiento completo: `progress/spec_F-009.md` §Resultados y §v4.

## Sentencias (constructor puro; todas con `?`)

Lecturas con credenciales de lectura; toda lectura con `truncado` → `ValueError` (400).

- **L1** obra: `SELECT ide, emp, cod FROM dbo.con WHERE tip = ? AND cod = ?` (`[42, cod]`); se filtra por
  `SIGRID_ALBARAN_EMPRESAS_OBRA` en Python (el índice único `(emp, tip, cod)` da una por empresa; H2).
- **L2-L4** contrato: `locate_contract` (+ `obride` = L1), `read_full_row(ctr)`, `read_rows_by`, como hoy.
- **L5** plantilla de cabecera: `SELECT TOP 1 c.ide FROM dbo.con c JOIN dbo.dca d ON d.ide = c.ide WHERE
  c.tip = ? AND c.emp = ? AND d.entide = ? ORDER BY c.ide DESC` (`emp` de la obra; `entide` del contrato
  o, sin él, `d.entcif = ?`); sin *fallback* a otro proveedor ni a otra empresa (H3).
- **L6** partidas: `SELECT ide, cod, tip, tipdes, tipvis, caaide FROM dbo.obrparpar WHERE obride = ? AND
  cod IN (?, …)`; imputable = `tip 1`, `tipdes 0`, `tipvis` 0/1 (M3) [M3].
- **L7** productos: `SELECT c.ide, c.cod, c.fecbaj, p.natide, p.tipmov FROM dbo.con c JOIN dbo.pro p ON
  p.ide = c.ide WHERE c.emp = ? AND c.tip = ? AND c.cod IN (?, …)` (`tip 3`) [M9].
- **L8** plantilla de línea: `SELECT TOP 1 * FROM dbo.dcapro WHERE proide = ? ORDER BY ide DESC`. **L8b**
  (sin vincular): `SELECT TOP 1 p.* FROM dbo.dcapro p JOIN dbo.dca d ON d.ide = p.docide WHERE p.proide =
  ? AND d.entide = ? ORDER BY p.ide DESC` (`entide` de la plantilla de cabecera; H15) [M11].
- **L9** tasas: `SELECT ide, iva FROM dbo.iva WHERE ide IN (?, …)` (fracción) [M11].
- **L10** almacén: `SELECT almide, cenide FROM dbo.obr WHERE ide = ?` (H13) y `SELECT ide, obride, cenide,
  caaproide FROM dbo.alm WHERE obride = ? OR ide IN (?, …)` (los de la obra y los ya resueltos; M8).
- **L11** idempotencia: `SELECT c.ide, c.cod, c.fec, d.entide, d.obride, d.totbas, d.totdoc FROM dbo.dca d
  JOIN dbo.con c ON c.ide = d.ide WHERE c.tip = ? AND d.synckey = ?` (M1) [+ filtro de anulados si M17];
  si hay uno, `SELECT pos, proide, can, pre, tot, paride, almide FROM dbo.dcapro WHERE docide = ? ORDER
  BY pos` [+ `refent` si M18].
- **L12** balance: `SELECT TOP 1 almcan, almpma FROM dbo.mov WHERE proide = ? AND almide = ? ORDER BY
  fechor DESC, ide DESC` (N1).
- **L13** `SELECT est FROM dbo.conest WHERE tip = ? AND est = ?`; `SELECT TOP (1) cod FROM dbo.usu WHERE
  cod = ?`. **L14** (dry-run) `cod` provisional = E2 sin bloqueos y `peek_next_ide` de las 5 tablas.

Dentro de `work(cursor)`, en orden: **E1** = L11 (sale sin escribir si aparece); **E2** `SELECT
MAX(TRY_CONVERT(int, SUBSTRING(cod, ?, 40))) FROM dbo.con WITH (UPDLOCK, HOLDLOCK) WHERE emp = ? AND tip
= ? AND cod LIKE ?` (`None` → 1); **E3-E6** `SELECT ISNULL(MAX(ide), 0) + 1 FROM
dbo.<con|dcapro|ctrprodes|mov> WITH (UPDLOCK, HOLDLOCK)`; **E7** = L12 con `WITH (UPDLOCK, HOLDLOCK)`;
**E8** `INSERT INTO dbo.<tabla> (<columnas>) VALUES (?, …)`: `con` → `dca` → `dcapro`×N → `ctrprodes`×M →
`mov`×K; solo con vinculadas, **E9** `UPDATE dbo.ctrpro SET canser = canser + ? WHERE ide = ?`, **E10**
`SELECT SUM(can), SUM(canser), SUM(canfac) FROM dbo.ctrpro WHERE docide = ?` y **E11** `UPDATE dbo.ctr
SET estser = ?, estfac = ? WHERE ide = ?` (H31); **E11b** `log`: `MAX(ide)+1 WITH (UPDLOCK, HOLDLOCK)` e
`INSERT`, al final (F-006); **E12** relecturas de R28 con `COUNT(*)` por clave.

**Applocks**, siempre en este orden: `SIGRID_REFEXT_14`, `SIGRID_SERIE_14`, `SIGRID_IDE_con`,
`SIGRID_IDE_dcapro`, `SIGRID_IDE_ctrprodes`, `SIGRID_IDE_mov`, `SIGRID_IDE_log`. Los cuatro del medio, como
el clásico y `albaran-directo`; F-006 toma `_con` y `_log` en el mismo orden: sin orden inverso posible.

## Flujo del modo extendido

1. Tope de líneas y prefijo (R24, R29). Con `commit`: llaves, credenciales y base (R24).
2. `ahora` (Madrid) una vez; L1-L5, L11 (R30 sale ya si aparece), L13.
3. Por línea, en orden: L6-L10 (con caché) y validación (R12-R17); se acumulan **todos** los fallos →
   `lineas_no_validas` con `details.lineas`.
4. Construcción pura de filas con balances de L12 → si dry-run, `previsto` con L14.
5. Si commit, `run_in_write_transaction(work)`; `work` es **reentrante**: reconstruye las filas en cada
   intento con `cod`, `ide` y balances de E2-E7 (fechas fijas); reintentos agotados → `colision_de_clave`.
6. Traza (R32) y respuesta.

## Condicionales: qué decide cada medición de T0 (definiciones en `progress/spec_F-009.md` §T0 v5)

| M | Regla que fija | Si sale… | …entonces |
|---|---|---|---|
| M3 | R14b (H17) | 0 repetidos entre imputables | sin campo `paride`; si >0, `paride` opcional (R14b) |
| M7 | fuera de alcance | el escritorio escribe `dcapropar` al imputar | PARADA (hoy no se escribe) |
| M9 | R19, puerta H20 | `pro.tipmov` explica la falta de `mov` | `mov` solo si `tipmov`; si MA9999 mueve stock, PARADA antes del modo real |
| M11 | R13 (H15) | el IVA de MA9999 varía entre proveedores | L8b se queda (si no varía, es inocua) |
| M13 | R22, `log` | `est`/`ori` de la fila de alta | se fijan esos valores |
| M14 | R21, §Reseteo (H11) | columnas de la sin vincular del escritorio | `prepma` y lista de reseteo confirmadas o corregidas |
| M16 | §Analítica, R15 (H10, H13) | `caaide` = partida / `alm.caaproide`; `obr.almide` relleno | hipótesis confirmada; si no, PARADA |
| M17 | R30b (H9) | anular **borra** el `con` | nada; si **marca** (`fecbaj`, `est`…), L11 excluye esa marca |
| M18 | R30b (H18) | `refent` vacío en ≥ 99,9 % de líneas | se escribe `referencia_linea` (≤24); si no, no se escribe |

## Códigos (R1, R8, R9)

Cabecera: `peticion_mixta`, `escritura_albaranes_deshabilitada`, `base_de_datos_no_permitida`,
`demasiadas_lineas`, `referencia_no_permitida`, `referencia_en_conflicto`, `obra_no_encontrada`,
`obra_de_empresa_no_permitida`, `obra_ambigua`, `contrato_no_encontrado`, `contrato_ambiguo`,
`usuario_no_valido`, `proveedor_sin_albaran_previo`, `estado_inicial_no_encontrado`,
`almacen_de_obra_no_resuelto`, `colision_de_clave`, `filas_afectadas_inesperadas`, `lineas_no_validas`.
Línea: `linea_no_es_del_contrato`, `producto_no_permitido`, `producto_no_encontrado`,
`partida_no_encontrada`, `partida_ambigua`, `partida_no_imputable`, `precio_negativo`, `paride_no_valido`
(solo R14b). Avisos: `producto_sin_historico`, `supera_pendiente`, `partida_distinta_del_contrato`,
`sin_partida_en_linea_con_partida`, `precio_distinto_del_contrato`, `iva_de_otro_proveedor`,
`servido_negativo`, `stock_negativo`, `cod_provisional`.

## Equivalencia con el modo clásico (R33)

Mismo doble; el mismo albarán (solo vinculadas, positivas, sin `ctrpro` repetido, partida y precio del
`ctrpro`, plantilla de la misma empresa) en dry-run por los dos modos; se comparan las filas **construidas**
(no la respuesta, que omite las bancarias) de `con`, `dca`, `dcapro`, `ctrprodes` y `mov` columna a
columna. Diferencias **declaradas**, y ninguna más: `synckey`, `hor`/`fechor` (Madrid frente a UTC; y
`mov.fec`/`fechor` del alta, N1), `est`, `prepma`, `ivacuo` (`dbo.iva` frente al cociente del `ctrpro`),
`tot`/`ivacuo` en empates de redondeo (H33; el dato fijo evita empates) y la fila de `log`.

## Riesgos y decisiones

- **Retrocompatibilidad**: dorado de T1; lo único observable es R8 y `peticion_mixta`. **Doble alta**:
  `synckey` dentro bajo `SIGRID_REFEXT_14`. **Colisión**: índice único + reintento. **Bloqueos**: ms.
- **Empresa** (H2, H3): obra y plantilla en la empresa de la lista; `SIGRID_ALBARAN_EMPRESAS_OBRA` vacía
  cierra el modo. No se descartan obras de baja (H2; N6, aprobada).
- **Precio negativo** (H8): segunda barrera tras sv9; el `ge=0` de Pydantic (400 sin código) pasa a fallo
  de línea `precio_negativo` para que F-053 lo mapee. **Stock negativo** (M15): solo aviso.
- **Descartado**: ruta nueva; modo por valores; meter el modo en `CreatePurchaseAlbaranUseCase`;
  reutilizar `albaran-directo`; plantilla de otro proveedor o empresa; `dcapropar` sin M7; `paride` en la
  petición sin M3 (N2); recibir almacén, centro o analítica del llamante; campo `almacen` en la línea y
  `fecha_no_valida` (v5.1: la línea sin partida es el «almacén» de Ruesma; las fechas, la app).
