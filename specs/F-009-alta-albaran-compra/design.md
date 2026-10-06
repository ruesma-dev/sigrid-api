<!-- specs/F-009-alta-albaran-compra/design.md -->
# F-009 · Diseño (v8.2)

Detalle campo a campo, casos de línea, códigos → estados de F-053 y ejemplos: [`contrato_albaranes.md`](contrato_albaranes.md).

## La decisión de fondo

**Se amplía `POST /api/sigrid/albaran` con un segundo modo** (humano, 2026-10-01). El modo se decide **antes de
validar nada** con la función pura `elegir_modo_albaran(cuerpo: object) -> Literal["clasico", "extendido"]`: si no
es un `dict`, `"clasico"` (Pydantic lo rechaza igual que hoy); si tiene `lineas` o `referencia_externa`, `"extendido"`,
salvo que también traiga `lineas_recibidas` ⇒ `AlbaranCompraError(codigo="peticion_mixta")`; si no, `"clasico"`.

- **Por claves, no por valores**: `{"lineas": []}` ya es extendido (y Pydantic lo rechaza ahí). El clásico
  **ignora** claves desconocidas: una petición mixta olvidaría `lineas`; rechazarla es su único cambio visible.
- **Modo clásico**: la ruta llama a `AddPurchaseAlbaranRequest` y `CreatePurchaseAlbaranUseCase` **sin
  modificarlos** (R2, R4), fijados por el test de caracterización (§Caracterización).
- **Modo extendido**: modelo, sentencias y caso de uso **nuevos**, con el núcleo probado en junio (`AC26/15950-15952`;
  R33). No va en `CreatePurchaseAlbaranUseCase`: reabriría 600 líneas sin test con SQL en línea incomparable.
- **Límite de microservicio: cabe.** Dar de alta un concepto con sus efectos (stock, medición) es de la
  pasarela; qué se registra y a qué precio lo decide el llamante (sv9). Ningún hueco H1-H35 lo cambia.

## Ficheros a crear

| Fichero | Capa | Qué contiene |
|---|---|---|
| `domain/models/albaran_compra_models.py` | domain | `elegir_modo_albaran`, `LineaAlbaranIn`, `AlbaranCompraRequest` (validadores de R5-R6), `AvisoAlbaran`, `LineaResultado(AlbaranLinePreview)`, `FalloLinea`, `AlbaranCompraResponse(AddPurchaseAlbaranResponse)`, `AlbaranCompraError(ValueError)` con `codigo` cerrado y `lineas` opcional, `COLUMNAS_BANCARIAS`. **Importa** los modelos clásicos; no los edita |
| `application/use_cases/albaran_compra_statements.py` | application | `AlbaranCompraStatements(database)`: SQL constante L1-L15 (con L7b y L15a-c) y E1-E12; puras `siguiente_cod`, `siguiente_balance`, `estados_contrato`, `importe_linea`, `sufijo_analitica`, `redondear_euros` y constructores de filas. Sin E/S; se autovalida con `DatabaseReferenceGuard` |
| `application/use_cases/create_albaran_compra_use_case.py` | application | `CreateAlbaranCompraUseCase(repository, settings, ahora_utc=..., reloj=...)` |
| `tests/test_f009_caracterizacion.py` + `tests/fixtures/f009_caracterizacion.json` | — | §Caracterización |
| `tests/test_f009_settings.py`, `_models.py`, `_statements.py`, `_use_case.py`, `_route.py`, `_equivalencia.py` | — | Ver `tasks.md` |

## Ficheros a modificar

| Fichero | Qué cambia |
|---|---|
| `config/settings.py` | Seis campos de R10; las listas de texto con `parse_string_list`, `SIGRID_ALBARAN_EMPRESAS_OBRA` con `parse_int_list`, y `SIGRID_ALBARAN_NATURALEZA_POR_PRODUCTO` (`dict[str, str]`) con un validador nuevo `parse_string_dict`: vacío/ausente ⇒ `{}`; objeto JSON de textos no vacíos (recortados) ⇒ ese; cualquier otra cosa (CSV, lista, valores no texto) ⇒ `ValueError` **al arrancar**, como `parse_int_list` |
| `function_app.py` | `sigrid_albaran`: `elegir_modo_albaran(body)`; clásico → el camino de hoy; extendido → `CreateAlbaranCompraUseCase`. Guarda R8 en `sigrid_albaran` y `sigrid_albaran_directo` **después** de validar el modelo y **antes** de `use_case.run`, solo si `commit`. `AlbaranCompraError` → 400 `details:{type, codigo[, lineas]}`; `IntegrityError` agotado → `colision_de_clave`. Docstring de `sigrid_albaran` corregido (no replica todas las líneas del contrato; H32). Los `except` existentes no cambian |
| `local.settings.sample.json`, `docs/ARCHITECTURE.md` | Claves nuevas; modos de la ruta, modelo y caso de uso nuevos |
| `azure-apps/sigrid_api.md` | R36 (commit aparte en `azure-apps`) |

## Ficheros que NO se tocan

`create_purchase_albaran_use_case.py`, `create_direct_albaran_use_case.py`, `albaran_domain_models.py`,
`albaran_directo_models.py` (se **importan**), `infrastructure/security/*`, `sql_server_repository.py` (bastan
`execute_read_query`, `read_full_row`, `read_rows_by`, `locate_contract`, `peek_next_ide` y `run_in_write_transaction`),
F-004 y F-006 (se importa `hora_local_de_madrid`), `infra/`, `CLAUDE.md`. Sin ficheros `NN_nombre.sql`: SQL constante.

## Caracterización (R2-R4)

En T1, **sobre `dev` y antes de cualquier cambio de producción**. Un doble del repositorio graba cada llamada (método,
argumentos, SQL y parámetros) y devuelve datos fijos; `datetime` con `monkeypatch`. Casos: clásico dry-run; commit con
dos `lineas_recibidas` al mismo `ctrpro` (suma) y una que supera lo pendiente; contrato inexistente y línea ajena;
directo dry-run y commit (llave R8 abierta). **El dorado no se regenera** (solo T1).

## Modelo de petición del modo extendido (R5, R6)

```python
class LineaAlbaranIn(BaseModel):                  # extra="forbid" en los dos; floats finitos
    referencia_linea: str = Field(..., min_length=1, max_length=24)          # → dcapro.refent (R30c)
    ctrpro_ide: int | None = Field(default=None, ge=1)                       # vinculada
    producto: str | None = Field(default=None, min_length=1, max_length=24)  # sin vincular
    descripcion: str | None = Field(default=None, max_length=128)            # dcapro.res
    unidad: str | None = Field(default=None, max_length=8)                   # dcapro.unimed
    cantidad: float                                       # != 0; < 0 = devolución (los dos tipos)
    precio: float                                         # < 0 → fallo de línea precio_negativo
    partida: str | None = Field(default=None, min_length=1, max_length=24)   # None ⇒ sin partida, paride 0
    paride: int | None = Field(default=None, ge=1)        # R14b (M3); exige partida (R6)

class AlbaranCompraRequest(BaseModel):
    database: str; cod_obra: str (≤24); usu: str (1-24); cif_proveedor: str (≤24; mayúsculas sin espacios, H21)
    referencia_externa: str = Field(..., min_length=1, max_length=128)       # dca.synckey
    cod_contrato: str | None = None (≤24); su_referencia: str = "" (≤128)   # dca.entref
    fecha_albaran: int | None (19000101-29991231); empide: int | None (≥1)
    lineas: list[LineaAlbaranIn] = Field(..., min_length=1); commit: bool = False
```

La lista conserva el orden (`pos`). Precio negativo y tope de líneas, en el caso de uso con código (v5.1). **Sin
campo `naturaleza`** (v8, H34): el de la v7 se retira; mandarlo da 400 sin código (`extra="forbid"`).

## Respuesta (R7, R30)

- **Cabecera**: los campos de `AddPurchaseAlbaranResponse` + `estado`, `referencia_externa`, `avisos[]` y `filas`
  (`con`, `dca`, `dcapro[]`, `ctrprodes[]`, `mov[]`, `log`). **Línea**: los de `AlbaranLinePreview` (`ctrpro_ide`/
  `linoriide` 0 en sin vincular) + `indice` (0..N-1), `referencia_linea`, `tipo` (`vinculada`|`sin_vincular`),
  `producto`, `paride`/`partida` (0/`null` sin partida), `cenide`, `avisos[]`.
- **Avisos** (H27): `AvisoAlbaran{codigo, mensaje}` en cabecera y línea; `warnings` = los `mensaje` de
  todos los avisos, en orden, y nada más (el texto de dry-run va en `cod_provisional`).
- **Columnas bancarias** (H16): `COLUMNAS_BANCARIAS` = `banide`, `banban`, `bansuc`, `bandig`, `bancue`,
  `ban`, `bantipide`, `cpapai`, `cpaban`, `cpasuc`, `cpaswi`, `cpatip`, `cpadiv`, `cpacue1`, `cpacue2`
  (diccionario, `dca`). Se quitan de `cabecera`, `filas.dca` y trazas; la fila escrita las lleva.
- **`idempotente`** (H18): `committed` `false`, `dry_run` = `not commit`, `con_ide`, `cod`, `fec`, totales de L11 y
  `lineas` leídas por `pos` (`indice` 0.., `pos`, `proide`, `cantidad`, `precio`, `total`, `paride`, `almide` y
  `referencia_linea` de `refent`, R30c); el resto de campos, vacíos (`{}`/`[]`).

## Filas que se escriben (cifras de T0: `progress/spec_F-009.md` §v6-§v8.1)

- **`con`**: clon de la plantilla (L5: mismo proveedor y empresa, H3) con `tip 14`, `emp` de la obra,
  `cod` ← E2, `res` ← `"<entres>. (<su_referencia>)"` recortado, `fec`, `est` 1 `PDT` en `conest` (M13).
- **`dca`**: clon de esa plantilla (forma de pago y efecto, M14b; dirección del proveedor) con los
  *overrides* de hoy (`fecdoc`, `hor`, `entref`, `eioide`, `ent*`, `obride`, `almide`, `cenide`, `empide`,
  totales, descuentos a 0, `estser/estfac` 0) más `ctride` (0 sin contrato) y `synckey`.
- **`dcapro` vinculada**: como hoy (plantilla = última `dcapro` del producto; `proide`, `ivaide`,
  `unimed`, `almide`, `cenide`, `caaide` y `docori*` del `ctrpro`, nunca `NULL` según M4; `canoriori`,
  `imporiori`) más `paride`, `pre`/`tar`/`dto` (R17), `res`/`unimed`, `refent` = `referencia_linea` y **`cod2`,
  `dncide` y `dncproide` del `ctrpro`** (`''`/0 si no los tiene; H35; M19: `cod2` 100 %, enlace 98,8 % y el resto con ambos a 0).
- **`dcapro` sin vincular**: plantilla = L8b (última del producto **del mismo proveedor**; M11) o, sin ella,
  L8 con aviso `iva_de_otro_proveedor` (H15): de ella `ivaide`; `natide`, `cueide` y `caaide` de §Analítica;
  `res`, `unimed`, `pre`, `tar` = `precio`, `dto` `''`, `paride`, `almide`/`cenide` (R15), `obride`, `refent` =
  `referencia_linea`; `docori*`, `can*`, `impori*` a 0/`''`; y §Reseteo.
- **`prepma`**: `dcapro.prepma` = `mov.prepma` de su `mov` (M14: 100 %) o 0 sin `mov` (M14c: 99,4 %); `mov.prepma`,
  §`prepma`. **`ctrprodes`** (vinculadas): una por línea, `can` con signo (M6). **`mov`**: como hoy, `emp` =
  `con.emp`, **si y solo si** `pro.tipmov` = 1 (M9; H20; `XA9999` también, 98,5 %).
- **`log`** (alta): la de F-006 (`tab 'con'`, `tip 14`, `ope 1`, `ori` 0, `est` 1; M13), `cod`/`res` del `con`,
  `fec`/`hor` del alta y `usu`. **`dcapropar`**: nunca (M7).

**Reseteo (sin vincular; H11, H35, M14)**: `med` NULL; `canmed`, `parcandes`, `anades`, `serdes`, `fecimp`,
`item`, `anexo`, `taride`, `fec`, `pla`, `dncide`, `dncproide`, `edilin`, `garfec`, `mesrevpre`,
`ejerevpre` a 0; `tex`, `texcom`, `desesp`, `cod2`, `pac` a `''`. M14: ninguna se arrastra de la plantilla y
las que el escritorio rellena cambian línea a línea con otra fuente. `cod2` vacío, decidido (H35; M19: sin regla).

**Analítica, naturaleza y cuenta (H10, H34; R13b, R15)**. **Vinculada**: `ctrpro.caaide` siempre (M16), como hoy
(R33). **Sin vincular**: naturaleza `nat` = la del producto en `SIGRID_ALBARAN_NATURALEZA_POR_PRODUCTO` (L15a: una
sola con ese `cod`, `fecbaj` 0 y `numemp` ∈ {0, empresa de la obra}, P2); sin entrada o sin esa fila ⇒
`naturaleza_no_valida`. `natide` = `nat.ide`; `cueide` = la `cua` de la empresa del albarán con `cod` =
`nat.cuacomcod` (L15c; ninguna o varias ⇒ `naturaleza_no_valida`); `caaide` = la `caa` con `cenide` = el de la
línea (L15b) y `cod` = `RTRIM(cod de la obra)` + `.` + `sufijo_analitica(nat.caagascod)`: el `caagascod` recortado
sin el prefijo `MOD.` si lo lleva, entero si no (`MOD.CDSB37`, obra `0678` ⇒ `0678.CDSB37`; `CDXA01` ⇒
`<obra>.CDXA01`); ninguna, varias o `caagascod` vacío ⇒ `analitica_no_resuelta`. **Consecuencia aceptada** (H34,
negocio: «códigos genéricos»): el escritorio imputa ~42 % de las MA9999 a `CDMA15` (`MA1501` del maestro); el alta
automática, **todas** a `MA99`/`CDSB37`. Descartadas: §v6-§v7 de `progress/spec_F-009.md`, `pro.natide` y el campo `naturaleza`.

## `prepma` (R19, R21)

`mov.prepma` = el **PMP de partida** de su línea: el `almpma` del último `mov` del mismo producto y almacén (L12/E7;
sin él, 0) o, si una línea anterior del albarán lleva ese par, el `almpma` resultante de esa línea (se encadenan como
el balance). Lo devuelve `siguiente_balance` junto a `almcan`/`almpma` (con el ε de R19); sin lectura ni función propias.
**Hipótesis coherente con los datos, no demostrada sobre el histórico** (M14e: `prepma(n)` = `almpma(n-1)` en 4 de 4
`mov`; el histórico da 9,7 % porque el escritorio reescribe el `almpma` de los `mov` posteriores, M10): verificación
manual en T22 y T24. Descartada la media ponderada global del producto (M14e; `progress/spec_F-009.md` §v8.1).

**Importes (R17; H14, H33)**: `redondear_euros(x)` = `Decimal(repr(x)).quantize(Decimal("0.01"), ROUND_HALF_UP)`;
`tot` = `redondear_euros(cantidad·pre)` siempre, `ivacuo` = `redondear_euros(tot·iva)`; test con el empate 2,675 → 2,68
(`round` da 2,67). **Opción C** (humano, v8.2): la vinculada toma `pre`, `tar` y `dto` del `ctrpro` solo si |`precio` −
`ctrpro.pre`| ≤ 0,0001 (M4) **y** `redondear_euros(cantidad·precio)` = `redondear_euros(cantidad·ctrpro.pre)`; si no,
`pre` = `tar` = `precio`, `dto` `''` y aviso `precio_distinto_del_contrato`. Así `tot` = `can·pre` de la fila y = el aprobado.

## Devoluciones (R18, R20) y fecha atrasada (R19)

**Regla A** (M5): entrada (`tip 1`, `oritip 5`, `destip 2`) con `canent` < 0, `cansal` 0 y PMP de alta; `canser` < 0
admitido (M6); T24 vigila la primera devolución real. **N1 (b)**: el escritorio recalcula los `mov` posteriores (M10);
aquí el `mov` se fecha en el alta y el albarán conserva su fecha; L12/E7 por `fechor DESC, ide DESC` (§v4).

## Sentencias (constructor puro; todas con `?`; lecturas con credenciales de lectura; `truncado` → `ValueError`, 400)

- **L1** obra: `SELECT ide, emp, cod FROM dbo.con WHERE tip = ? AND cod = ?` (`[42, cod]`); se filtra por
  `SIGRID_ALBARAN_EMPRESAS_OBRA` en Python (el índice único `(emp, tip, cod)` da una por empresa; H2).
- **L2-L4** contrato: `locate_contract` (+ `obride` = L1), `read_full_row(ctr)`, `read_rows_by`, como hoy.
- **L5** plantilla de cabecera: `SELECT TOP 1 c.ide FROM dbo.con c JOIN dbo.dca d ON d.ide = c.ide WHERE
  c.tip = ? AND c.emp = ? AND d.entide = ? ORDER BY c.ide DESC` (`emp` de la obra; `entide` del contrato
  o, sin él, `d.entcif = ?`); sin *fallback* a otro proveedor ni a otra empresa (H3).
- **L6** partidas: `SELECT ide, cod, tip, tipdes, tipvis FROM dbo.obrparpar WHERE obride = ? AND cod IN
  (?, …)`; imputable = `tip 1`, `tipdes 0`, `tipvis` 0/1 (M3); el `paride` de R14b se busca entre ellas.
- **L7** productos: `SELECT c.ide, c.cod, c.fecbaj, p.tipmov FROM dbo.con c JOIN dbo.pro p ON p.ide = c.ide
  WHERE c.emp = ? AND c.tip = ? AND c.cod IN (?, …)` (`tip 3`; sin `natide`, H34); **L7b** `SELECT ide, tipmov FROM
  dbo.pro WHERE ide IN (?, …)` (productos de los `ctrpro`; R19).
- **L8** plantilla de línea: `SELECT TOP 1 * FROM dbo.dcapro WHERE proide = ? ORDER BY ide DESC`. **L8b**
  (sin vincular): `SELECT TOP 1 p.* FROM dbo.dcapro p JOIN dbo.dca d ON d.ide = p.docide WHERE p.proide =
  ? AND d.entide = ? ORDER BY p.ide DESC` (`entide` de la plantilla de cabecera; H15; M11).
- **L9** tasas: `SELECT ide, iva FROM dbo.iva WHERE ide IN (?, …)` (fracción; M11).
- **L10** almacén: `SELECT almide, cenide FROM dbo.obr WHERE ide = ?` (H13) y `SELECT ide, obride, cenide
  FROM dbo.alm WHERE obride = ? OR ide IN (?, …)` (los de la obra y los resueltos; M8).
- **L11** idempotencia: `SELECT c.ide, c.cod, c.fec, d.entide, d.obride, d.totbas, d.totdoc FROM dbo.dca d
  JOIN dbo.con c ON c.ide = d.ide WHERE c.tip = ? AND d.synckey = ?` (M1; anular borra, M17b);
  si hay uno, `SELECT pos, proide, can, pre, tot, paride, almide, refent FROM dbo.dcapro WHERE docide = ?
  ORDER BY pos` (R30c).
- **L12** balance: `SELECT TOP 1 almcan, almpma FROM dbo.mov WHERE proide = ? AND almide = ? ORDER BY
  fechor DESC, ide DESC` (N1; sin fila, `(0, 0)`); de él salen `almcan`, `almpma` y `prepma` (§`prepma`).
- **L13** `SELECT est FROM dbo.conest WHERE tip = ? AND est = ?`; `SELECT TOP (1) cod FROM dbo.usu WHERE
  cod = ?`. **L14** (dry-run) `cod` provisional = E2 sin bloqueos y `peek_next_ide` de las 5 tablas.
- **L15a** `SELECT ide, cod, numemp, fecbaj, caagascod, cuacomcod FROM dbo.auxpronat WHERE cod IN (?, …)` (las del
  mapeo de los productos pedidos); **L15b** `SELECT c.ide, c.cod, a.cenide FROM dbo.con c JOIN dbo.caa a ON a.ide =
  c.ide WHERE c.cod IN (?, …)` (se casa por `cenide` y `cod`); **L15c** `SELECT c.ide, c.cod FROM dbo.con c JOIN
  dbo.cua a ON a.ide = c.ide WHERE c.emp = ? AND c.cod IN (?, …)` (P3). Códigos comparados recortados (`RTRIM`).

Dentro de `work(cursor)`, en orden: **E1** = L11 (sale sin escribir si aparece); **E2** `SELECT
MAX(TRY_CONVERT(int, SUBSTRING(cod, ?, 40))) FROM dbo.con WITH (UPDLOCK, HOLDLOCK) WHERE emp = ? AND tip
= ? AND cod LIKE ?` (`None` → 1); **E3-E6** `SELECT ISNULL(MAX(ide), 0) + 1 FROM
dbo.<con|dcapro|ctrprodes|mov> WITH (UPDLOCK, HOLDLOCK)`; **E7** = L12 con `WITH (UPDLOCK, HOLDLOCK)`; **E8** `INSERT INTO dbo.<tabla> (<columnas>) VALUES (?, …)`: `con` →
`dca` → `dcapro`×N → `ctrprodes`×M → `mov`×K; solo con vinculadas, **E9** `UPDATE dbo.ctrpro SET canser = canser
+ ? WHERE ide = ?`, **E10** `SELECT SUM(can), SUM(canser), SUM(canfac) FROM dbo.ctrpro WHERE docide = ?` y **E11**
`UPDATE dbo.ctr SET estser = ?, estfac = ? WHERE ide = ?` (H31); **E11b** `log`: `MAX(ide)+1 WITH (UPDLOCK,
HOLDLOCK)` e `INSERT`, al final (F-006); **E12** relecturas de R28 con `COUNT(*)` por clave.

**Applocks**, siempre en este orden: `SIGRID_REFEXT_14`, `SIGRID_SERIE_14`, `SIGRID_IDE_con`,
`SIGRID_IDE_dcapro`, `SIGRID_IDE_ctrprodes`, `SIGRID_IDE_mov`, `SIGRID_IDE_log`. Los cuatro del medio, como
el clásico y `albaran-directo`; F-006 toma `_con` y `_log` en el mismo orden: sin orden inverso posible.

## Flujo del modo extendido

1. Tope de líneas y prefijo (R24, R29). Con `commit`: llaves, credenciales y base (R24).
2. `ahora` (Madrid) una vez; L1-L5, L11 (R30 sale ya si aparece), L13.
3. Por línea, en orden: L6-L10 y L15 (con caché) y validación (R12-R17); **todos** los fallos → `lineas_no_validas`.
4. Construcción pura de filas con balances de L12 → si dry-run, `previsto` con L14.
5. Si commit, `run_in_write_transaction(work)`; `work` es **reentrante**: reconstruye las filas en cada
   intento con `cod`, `ide` y balances de E2-E7 (fechas fijas); reintentos agotados → `colision_de_clave`.
6. Traza (R32) y respuesta.

## Condicionales

**T0 cerrada**, ninguna medición pendiente (cifras en `progress/spec_F-009.md` §v6-§v8.1). **Solo verificación manual**:
`prepma` (hipótesis de §`prepma`) en T22 (frente a un albarán del escritorio del mismo día y almacén) y T24 (primera alta
real); la primera devolución real (regla A, M5) en T24; y en T22-T23, lo revisable en la UI.

## Códigos (R1, R8, R9)

Cabecera: `peticion_mixta`, `escritura_albaranes_deshabilitada`, `base_de_datos_no_permitida`, `demasiadas_lineas`,
`referencia_no_permitida`, `referencia_en_conflicto`, `obra_no_encontrada`, `obra_de_empresa_no_permitida`,
`obra_ambigua`, `contrato_no_encontrado`, `contrato_ambiguo`, `usuario_no_valido`, `proveedor_sin_albaran_previo`,
`estado_inicial_no_encontrado`, `almacen_de_obra_no_resuelto`, `colision_de_clave`, `filas_afectadas_inesperadas`,
`lineas_no_validas`. Línea: `linea_no_es_del_contrato`, `producto_no_permitido`, `producto_no_encontrado`,
`partida_no_encontrada`, `partida_ambigua`, `partida_no_imputable`, `precio_negativo`, `paride_no_valido` (R14b),
`naturaleza_no_valida` (R13b: configuración, H34), `analitica_no_resuelta` (R15). Avisos: `producto_sin_historico`,
`supera_pendiente`, `partida_distinta_del_contrato`, `sin_partida_en_linea_con_partida`, `precio_distinto_del_contrato`,
`iva_de_otro_proveedor`, `servido_negativo`, `stock_negativo`, `cod_provisional`.

## Equivalencia con el modo clásico (R33)

Mismo doble; el mismo albarán (solo vinculadas, positivas, sin `ctrpro` repetido, partida y precio del `ctrpro`, plantilla
de la misma empresa, `tipmov` 1) en dry-run por los dos modos; filas **construidas** columna a columna. Diferencias
**declaradas**, y ninguna más: `synckey`, `hor`/`fechor` (Madrid frente a UTC; y `mov.fec`/`fechor` del alta, N1),
`est`, `prepma` (`dcapro` y `mov`), `ivacuo` (`dbo.iva` frente al cociente del `ctrpro`), `tot`/`ivacuo` en empates
(H33; el dato fijo los evita), `dcapro.refent` (R30c), `cod2`/`dncide`/`dncproide` (del `ctrpro` frente a la
plantilla; H35), el `log`, el `mov` con `tipmov` 0 (R19), `con.res` (recortado a 128; el clásico, a 200) y `mov.almpma` con
stock final 0 (aquí se conserva el PMP, R19; el clásico pone `pre`). La opción C de R17 no añade ninguna: con `precio` =
`ctrpro.pre` escribe `pre`, `tar`, `dto` y `tot` como el clásico (salvo los empates ya declarados).

## Riesgos y decisiones

- **Retrocompatibilidad**: dorado de T1; lo único observable es R8 y `peticion_mixta`. **Doble alta**: `synckey`
  dentro bajo `SIGRID_REFEXT_14`. **Colisión**: índice único + reintento. **Bloqueos**: ms. **Empresa** (H2, H3):
  obra y plantilla en la de la lista; vacía cierra el modo; no se descartan obras de baja (N6).
- **Naturaleza por configuración** (H34): el mapeo vacío cierra las sin vincular (`naturaleza_no_valida`); lista
  blanca y mapeo deben cubrir los mismos productos (T19). Corregir el maestro de `MA9999` es de Administración.
- **`prepma`** (hipótesis, §`prepma`): si el escritorio usa otra regla, solo difiere ese campo (no toca stock,
  importes ni medición) y T22/T24 lo detectan. Sale del balance de E7, ya bajo `UPDLOCK`: sin lecturas nuevas.
- **Precio negativo** (H8): segunda barrera tras sv9, fallo de línea con código (no `ge=0`). **Stock negativo**: aviso.
- **Descartado**: ruta nueva; modo por valores; meter el modo en `CreatePurchaseAlbaranUseCase`;
  reutilizar `albaran-directo`; plantilla de otro proveedor o empresa; `dcapropar` (M7); recibir almacén,
  centro, analítica o naturaleza del llamante; campo `almacen` y `fecha_no_valida` (v5.1); las de §Analítica;
  la media ponderada global de `prepma` (M14e) con sus lecturas del stock global sin `UPDLOCK`.
