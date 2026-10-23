# F-015 · Diseño (v2)

Medidas: [`progress/explore_F-015.md`](../../progress/explore_F-015.md) (Mn). Base: `specs/F-009-alta-albaran-compra/`
(design §Sentencias, §Filas, §Flujo) y su contrato [`contrato_albaranes.md`](../F-009-alta-albaran-compra/contrato_albaranes.md).

## La decisión de fondo

Dos correcciones del **modo extendido** y nada del clásico, en las tres piezas de F-009 (modelo, constructor puro, caso de
uso). Ni ruta nueva, ni App Setting nueva, ni cambios en `infrastructure/`.

- **O1 · Lista blanca.** `con` y `dca` dejan de clonarse de una plantilla: se construyen columna a columna, cada columna con
  un origen (§Lista blanca), y se insertan con columnas fijas, como `mov` o la `con` de F-006. Lo del proveedor sale, por
  este orden (humano, 2026-10-23), del **contrato**, del **proveedor** (`prv`) y del albarán anterior (**respaldo**), que
  es opcional: sin él no hay error. Se mide contra lo que deja el escritorio en 1.293 altas a mano (M18, M20, M26) y se
  corrige lo que hoy arrastra la API (M19: 60 de 68).
- **O2 · Retención.** Con contrato, una `dcarec` copiada de su único `ctrrec` y el total neto (M9-M13). Importa por dinero:
  **la factura hereda la retención del albarán** (M16) y el asiento del albarán no la usa (M15).
- **Límite de microservicio: cabe.** Copiar al albarán lo que el contrato y Sigrid ya dicen es construir bien el documento.
  **Interpretar el texto del contrato no cabe** (D1).

## Ficheros a crear

| Fichero | Qué contiene |
|---|---|
| `tests/test_f015_statements.py` | Lista blanca (R1, R2, R25 centinela), L5, L11, L16, E6b, `INSERT` de `con`/`dca`/`dcarec`, E12 carácter a carácter; `construir_con`, `construir_dca`, `resolver_retencion`, `calcular_retencion`, `construir_dcarec`, `numerar` con `dcarec`, applocks, control negativo |
| `tests/test_f015_use_case.py` | Flujo con el doble: cascada contrato → proveedor → respaldo (R3-R5), respaldo opcional (R6), proveedor por CIF (R7), falta de columna (R10), retención (R12-R16), respuesta (R17-R19), previa (R20), commit, reintento y relecturas (R21-R23) |

## Ficheros a modificar

| Fichero | Qué cambia |
|---|---|
| `application/use_cases/albaran_compra_statements.py` | §Lista blanca, §Sentencias, §Funciones puras y §Filas |
| `application/use_cases/create_albaran_compra_use_case.py` | §Flujo |
| `domain/models/albaran_compra_models.py` | `CODIGOS_CABECERA`: más `retencion_no_soportada`, `proveedor_no_encontrado` y `proveedor_ambiguo`, menos `proveedor_sin_albaran_previo`; `CODIGOS_AVISO`: más `retencion_del_contrato` y `cabecera_sin_dato` (D12) |
| `tests/f009_dobles.py` | Filas completas de respaldo (`DCA_COLUMNAS`), `ctr`, `prv` y `auxpag`; L17; respaldo ausente; sin lectura de la `con` de la plantilla; L16, E6b, `INSERT` y relectura de `dcarec`; `ctrrec` vacío por defecto |
| `tests/test_f009_statements.py`, `tests/test_f009_use_case.py`, `tests/test_f009_equivalencia.py` | Solo donde fijan L5, L11, `APPLOCKS`, `_TOTALES_DCA`, `construir_con`, `construir_dca`, `insertar_con`/`_dca` o `totales` (R26, R27) |
| `function_app.py` | Solo el docstring de `sigrid_albaran` |
| `specs/F-009-alta-albaran-compra/contrato_albaranes.md` | v8.3 (§Contrato), **antes** de implementar (R28) |
| `docs/ARCHITECTURE.md`; `azure-apps/sigrid_api.md` | Lista blanca, applock `SIGRID_IDE_dcarec`, `dcarec`, respaldo (R28; `azure-apps` en commit aparte) |

## Ficheros que NO se tocan

`create_purchase_albaran_use_case.py`, `create_direct_albaran_use_case.py`, `albaran_domain_models.py`,
`albaran_directo_models.py`, `tests/test_f009_caracterizacion.py` y **`tests/fixtures/f009_caracterizacion.json`** (R11),
`parte_reclamacion_statements.py` (se **importan** `CON_COLUMNAS` y `fecha_ole_utc`), `infrastructure/` entero,
`config/settings.py`, `infra/`. Sin ficheros `NN_nombre.sql`: SQL constante, como F-009.

## Lista blanca (R1-R9; constantes en `albaran_compra_statements.py`)

**`DCA_COLUMNAS`** (M17, orden físico, 145): `ide, cla, entide, entcod, entres, entref, entcif, ivareq, facper, fecdoc,
fecpag, hor, eioide, eiotex, eitide, eittra, pagide, pagtex, pagfor, efeide, cueide, impbru, impnet, impdes, imprec, totbas,
totiva, totdoc, tot, totpag, cenide, caaide, almide, ivaide, tex, bul, pes, volum, empide, ageide, ageimp, obride, ctride,
fecent, feclim, fecrec, diremp1, dircon1, dirdir1, diremp2, dircon2, dirdir2, diremp3, dircon3, dirdir3, estser, estfac,
antestser, antestfac, ivadif, docoritip, docoriide, comide, pasdeside, pasori, divcod, divcam, emppreide, empconide,
docrelide, cocide, paclis, tipsininv, prmide, estped, antestped, empcif, cveide, alqide, alqfec, pexide, divcamfec, ctdide,
totbasdiv, totivadiv, totdocdiv, totdiv, totpagdiv, cypnatide, refarc, emptex, horlim, pdpide, ano, mes, texent, refcom,
emnet, eg3w, dtumID, cptide, eleenvio, tipisp, delide, banide, banban, bansuc, bandig, bancue, ban, bantipide, entciftip,
entcifpai, aoside, PFID, cadcod1, caddir1, cadcod2, caddir2, cadcod3, caddir3, cadcod4, caddir4, cpapai, cpaban, cpasuc,
cpaswi, cpatip, cpadiv, cpacue1, cpacue2, ppoide, fecfac, horfac, idefac, clabieser, facoriide, duaide, numregcon, fas,
periodo, tipctr, tipgar, impavr, synckey`.

**`_DCA_TEXTO`** (varchar/text, M17): `entcod, entres, entref, entcif, eiotex, eittra, pagtex, pagfor, tex, diremp1-3,
dircon1-3, dirdir1-3, divcod, paclis, empcif, refarc, emptex, texent, refcom, dtumID, eleenvio, bandig, bancue, ban,
entciftip, entcifpai, PFID, cadcod1-4, cpapai, cpaban, cpasuc, cpaswi, cpatip, cpadiv, cpacue1, cpacue2, numregcon,
periodo, synckey` (48).

| Origen | Columnas de `dca` | Valor | Evidencia |
|---|---|---|---|
| **petición / obra / cálculo** (18) | `ide`; `entref`; `fecdoc`, `hor`; `obride`, `ctride`; `almide`, `cenide`; `empide`; `synckey`; `impbru`, `impnet`, `totbas`, `totiva`, `totdoc`; `tot`, `totpag`; `diremp1` | `numerar`; `su_referencia`; sellos; obra y contrato (0 sin él); almacén de cabecera de F-009; petición o `SIGRID_ALBARAN_EMPIDE`; `referencia_externa`; `sumar_importes`; `totdoc − cuo` (R13); la `entres` escrita | F-009; M20 (`diremp1` = `entres` 100 %, `cenide`/`almide` = contrato 99,9 %) |
| **identidad** (6) | `entide`, `entcod`, `entres`, `entcif`, `entciftip`, `entcifpai` | `ctr`; sin contrato, el `prv` de L17 (`ide`, `con.cod`, `raz`, `cif`, `tipcif`, `cifpai`) | M20, M27 |
| **cascada** (15): `ctr` → `prv` → respaldo, el primero con valor | pago: `pagide`, `pagtex`, `pagfor`, `efeide` (en grupo; del `prv`, `pagtex` = `auxpag.res` y `pagfor` = `auxpag.formul` de su `pagide`); banco: `banban`, `bansuc`, `bandig`, `bancue`, `ban`, `bantipide` (en grupo, del primero con `banban` ≠ 0 o `ban` no vacío); `cueide`; `eioide`; `dirdir1` (del `prv`, `dir`); `dircon1` y `ivadif` (sin columna en `prv`: `ctr` → respaldo; `ivadif` del `ctr` aunque sea 0) | si nadie la trae, 0 o `''` (R5) | M26 |
| **fijo** (106) | `tipgar` −1; `emptex` NULL; las demás de `_DCA_TEXTO` `''` y las demás numéricas 0 (`cla`, facturación, cadena, divisa, `fecent`, `feclim`, `cocide`, `estser`, `estfac`, `impdes`, `imprec`, `banide`…) | constante | M18 (0 o vacías en las 1.293), M19; D7 |

**`con`** (`CON_COLUMNAS` de F-006, todas fijas o calculadas, la fila que F-006 ya escribe): `ide` y `cod` de `numerar`,
`emp` de la obra, `tip` 14, `subtip` 0, `res` = `"<entres>. (<su_referencia>)"`[:128], `fec` de los sellos, `tex` NULL,
`cee` 0, `est` 1, `fecbaj` 0, `tiemod` = `sellos.tiemod`, `ico`/`delo`/`del`/`obr`/`doc` `''`, `serie` 0, `hor` 0 (M18).

Se declaran como `DCA_IDENTIDAD`, `DCA_CASCADA` (con los grupos `GRUPO_PAGO` y `GRUPO_BANCO` y el mapeo de nombres del `prv`),
`DCA_CALCULADAS` y `DCA_FIJAS` (dict columna → valor), y
`ORIGEN_DCA` (columna → origen) se **deriva** de ellas; un test exige que sus claves sean `DCA_COLUMNAS` sin huecos ni
repetidas (R25). Las bancarias siguen fuera de `cabecera` y `filas.dca` de la respuesta (H16).

## Sentencias (todas con `?`)

- **L5** (R6): `... WHERE c.tip = ? AND c.emp = ? AND d.entide = ? AND c.cod LIKE ? AND d.cla = ? AND ISNULL(d.entref, '')
  NOT LIKE ? ORDER BY c.ide DESC` con `[14, emp, entide, "AC__/%", 0, "PROF%"]` (`PATRON_SERIE_RESPALDO`, `CLA_ALBARAN`,
  `PATRON_PROFORMA`); la variante por `d.entcif = ?` solo desempata R7. Sin filas, no hay respaldo (ni error).
- **L17** (R7): `SELECT v.ide, c.cod FROM dbo.prv v JOIN dbo.con c ON c.ide = v.ide WHERE c.tip = ? AND c.emp = ? AND
  c.fecbaj = ? AND v.cif = ?` con `[5, emp, 0, cif]` (`TIP_PROVEEDOR`). El `prv` (por `entide`, siempre) y el `auxpag`
  (solo si el pago sale del `prv`) se leen con `read_full_row`, como el `ctr` y la `dca` del respaldo.
- Se **quita** la lectura de la `con` de la plantilla (`_fila_completa(..., "con", ...)`).
- **L11** (R18) añade `d.tot` al final. **L16** (R12, R14): `SELECT r.ide, r.recide, r.pos, r.valdef, r.valpor, r.valcan,
  r.valmod, r.valfij, r.reccla, r.cueide, r.ivaide, r.tex, r.resalt, r.item, x.cla, c.cod FROM dbo.ctrrec r LEFT JOIN
  dbo.rec x ON x.ide = r.recide LEFT JOIN dbo.con c ON c.ide = r.recide WHERE r.docide = ? ORDER BY r.pos, r.ide`.
- **E6b** (R21): `SELECT ISNULL(MAX(ide), 0) + 1 FROM dbo.dcarec WITH (UPDLOCK, HOLDLOCK)`.
- **E8**: `insertar_con` e `insertar_dca` pasan a `_insert_fijo("con", CON_COLUMNAS)` y `_insert_fijo("dca",
  DCA_COLUMNAS)`; `_TABLAS_CLONADAS` queda en `{"dcapro"}`. `insertar_dcarec`: `_insert_fijo("dcarec", DCAREC_COLUMNAS)`
  con `ide, docide, recide, pos, bas, valdef, valpor, valcan, valmod, valfij, cuo, tex, reccla, cueide, ivaide, ivacuo,
  reqcuo, refide, resalt, frasupide, item` (M14). **E12** (R23): `SELECT COUNT(*) FROM dbo.dcarec WHERE docide = ?`.
- **`APPLOCKS`**: `SIGRID_REFEXT_14`, `SIGRID_SERIE_14`, `SIGRID_IDE_con`, `_dcapro`, `_ctrprodes`, `_mov`,
  **`SIGRID_IDE_dcarec`**, `_log`. Nadie más toma el nuevo: sin orden inverso posible.

## Funciones puras (application, sin E/S)

```python
def construir_con(*, emp: int, fec: int, entres: str | None, su_referencia: str, tiemod: float) -> dict
def construir_dca(*, contrato: Mapping | None, proveedor: Mapping, pago_proveedor: Mapping | None,
                  respaldo: Mapping | None, fec: int, hor: int, su_referencia: str,
                  obride: int, ctride: int, almide: int, cenide: int, empide: int, totales: Mapping[str, float],
                  cuo: Decimal, referencia_externa: str) -> dict
    # Recorre DCA_COLUMNAS y aplica ORIGEN_DCA (cascada R3, R5). Columna ausente en su fila -> ValueError (R10).
    # Devuelve tambien las columnas sin fuente para el aviso de R5.
def resolver_retencion(filas_ctrrec: list[dict]) -> dict | None     # R14: ValueError con el motivo
def calcular_retencion(ctrrec: dict, totales: dict) -> tuple[Decimal, Decimal]   # R15
def construir_dcarec(ctrrec: dict, *, bas: Decimal, cuo: Decimal) -> dict        # R13
```

`SellosAlbaran` gana `tiemod: float` = `fecha_ole_utc(instante_utc)` (F-006). `_TOTALES_DCA` desaparece: los totales son
columnas calculadas de la lista. `CLASES_RETENCION_BASE = {5: "totbas", 3: "totbas", 4: "totdoc"}` (M12).

## Filas

- **`FilasAlbaran`** gana `dcarec: list[dict]` (0 o 1, por defecto `[]`) y `como_dict()` la devuelve en `filas.dcarec`.
  **`numerar`** gana `ide_dcarec: int | None`: `ide` = el reservado y `docide` = `ide_con`; con `dcarec` y `None` ⇒
  `ValueError`, como con `mov`.
- **`dcarec`** (R13): la del `ctrrec` resuelto con `bas`/`cuo` de R15; `cueide` del `ctrrec` (M11; D8).

## Flujo del modo extendido (cambios sobre F-009 design §Flujo)

1. Igual.
2. Obra → contrato (fila completa del `ctr`, como hoy) o, sin contrato, **L17** (R7) → `prv` → **L5 respaldo**
   (opcional) → L11 (idempotencia, con `tot`) → `conest`/`usu` → **con contrato, L16** y `resolver_retencion` (o
   `retencion_no_soportada`, R14) → `auxpag` si el pago sale del `prv`. Un albarán ya escrito sigue siendo
   `idempotente` aunque su contrato cambie después.
3. Igual (líneas).
4. `_construir`: `sumar_importes` → retención (`calcular_retencion`, `construir_dcarec`) → `construir_con` y
   `construir_dca` con `contrato` (o `None`), `proveedor`, `pago_proveedor`, `respaldo` (o `None`) y `cuo`; aviso R5.
   Previa: `numerar` con `peek_next_ide("dcarec")`.
5. Commit: como F-009 y, si hay `dcarec`, E6b y su `INSERT` tras los `mov` (R21); E12 de `dcarec` (R23); reentrante (R22).
6. Respuesta: `totales` + `tot`, `retenciones`, `n_retenciones`; avisos R5 y R16; traza con `n_retenciones` (R19).

## Contrato con albaranes v8.3 (lo pasa el líder a albaranes ANTES de implementar; R28)

| Cambio | § | Qué hace sv9 (recomendación) |
|---|---|---|
| Respaldo opcional (serie `AC`, `cla 0`, sin proformas); **`proveedor_sin_albaran_previo` se retira** | §4.1 paso 2; §3.3 | Quitar su mapeo: ya no llega |
| Sin contrato: **`proveedor_no_encontrado`** y **`proveedor_ambiguo`** (cab.) | §3.3 | Mapearlos a `no_admitido` (M27: 7 de 429 serían ambiguos) |
| Cabecera por lista blanca: identidad del contrato (o del `prv`); pago, efecto, banco, cuenta, condición de envío y dirección por contrato → proveedor → respaldo; facturación, fechas, divisa y Documentum a 0; `tiemod` del alta | §3.1 `cabecera`/`filas`, §4.2 | Nada (F-053 R16 no los guarda) |
| Aviso **`cabecera_sin_dato`** (cab., si D12 se aprueba) | §3.2 | Informativo; sv9 decide si lo bloquea |
| Error **`retencion_no_soportada`** (cab.) | §3.3 | Mapearlo a **`no_admitido`**; sin mapear, H25 lo lleva a `error` |
| Aviso **`retencion_del_contrato`** (cab.) | §3.2 | Informativo; **no** en `ALTA_SIGRID_AVISOS_BLOQUEANTES` (~89 % de los de contrato con `ctrrec`) |
| `totales.tot`, `retenciones`, `n_retenciones`; `filas.dcarec[]`; en `idempotente`, `tot` y `retenciones` | §3.1 | `totdoc` sigue sin retención; el neto es `tot`. La comparación de la previa es por línea: no cambia |
| Escribe además `dcarec` ×0-1 y el applock `SIGRID_IDE_dcarec` | §4.1 paso 4, §4.2 | Nada |
| No interpreta el texto del contrato; no deduce `empide` del `usu` (M24); sin retención sin contrato | §4.3 | `empide` sigue en la petición (`ALTA_SIGRID_EMPIDE` o `null`) |
| **Corrección**: `usu` = `ALTA_SIGRID_USUARIO_RESPALDO` o el `usu` de quien aprueba, no `ALTA_SIGRID_USUARIO` | §2.1 (l. 189), §2.4.9 (l. 254), H1 (l. 485); §7 (l. 1079), a confirmar | Lo confirma albaranes (columna suya) |

§2 (petición) sin cambios de forma. Versión v8.3 con su línea de cambios arriba.

## Equivalencia (R26) y dorado (R11)

- **Dorado**: no se toca; `git diff dev` vacío en el JSON, su test y los cuatro ficheros intocables de F-009 R4.
- **Equivalencia**: `_diferencias` compara `con` y `dca` en las columnas del clásico (que clona una plantilla del doble) y
  exige que el extendido tenga exactamente `CON_COLUMNAS`/`DCA_COLUMNAS`. El caso de equivalencia deja vacías en el `ctr` y
  el `prv` del doble las columnas de cascada, para que caigan al respaldo (= la plantilla del clásico) y deban **coincidir
  con el clon**; `DECLARADAS["dca"]` = las columnas de `ORIGEN_DCA` que no son de cascada (derivado, no a mano) y
  `DECLARADAS["con"]` = todas. `dcapro`, `ctrprodes` y `mov`, como hoy. Un caso con `ctrrec` declara `dcarec` y el aviso.

## Limpieza de las altas ya escritas (R30; MANUAL, solo con autorización expresa)

1. **Previa (lectura, `sql/read`)**: `SELECT c.ide, c.cod, d.idefac, d.fecfac, d.horfac, d.antestfac, d.fecent, d.feclim,
   d.cocide, d.totbasdiv, d.totivadiv, d.totdocdiv, d.totdiv, d.totpagdiv, d.dtumID, d.tipgar FROM dbo.con c JOIN dbo.dca d
   ON d.ide = c.ide WHERE c.tip = ? AND c.emp = ? AND d.empide = ? AND d.synckey LIKE ? AND d.estfac = ? AND (d.idefac <> 0
   OR d.fecfac <> 0 OR d.horfac <> 0 OR d.antestfac <> 0 OR d.fecent <> 0 OR d.feclim <> 0 OR d.cocide <> 0 OR d.totbasdiv
   <> 0 OR d.totivadiv <> 0 OR d.totdocdiv <> 0 OR d.totdiv <> 0 OR d.totpagdiv <> 0 OR d.dtumID <> '' OR d.tipgar <> ?) AND
   NOT EXISTS (SELECT 1 FROM dbo.dcapro p JOIN dbo.dcfpro f ON f.linoriide = p.ide WHERE p.docide = d.ide)` con
   `[14, 1, 2425207, "ALB-%", 0, -1]`. La lista (N filas, se espera ~60) va a `progress/` sin nombres; el humano la revisa.
   `sql/write` no tiene dry-run: esta lectura es la previa.
2. **Escritura (`sql/write`)**: `UPDATE dbo.dca SET idefac = ?, fecfac = ?, horfac = ?, antestfac = ?, fecent = ?, feclim =
   ?, cocide = ?, totbasdiv = ?, totivadiv = ?, totdocdiv = ?, totdiv = ?, totpagdiv = ?, dtumID = ?, tipgar = ? WHERE ide = ?
   AND empide = ? AND synckey LIKE ? AND estfac = ?`, `parameter_sets` = `[0×12, '', -1, ide, 2425207, "ALB-%", 0]` por
   cada `ide` de la previa, `max_affected_rows` = N. Una transacción. Requiere `UPDATE` en `ALLOWED_WRITE_PREFIXES`.
3. **Relectura**: la consulta 1 debe dar 0 filas; y `SELECT COUNT(*)` de las N por `ide` con los valores nuevos, N.
No se tocan `con`, `eioide` ni `tiemod`. Hacerla **después** de desplegar F-015 (hoy entra ~1 alta al día con el defecto).

## Decisiones

**Aprobadas por el humano (2026-10-23, «todo lo demás ok»)**: D1, D6, D7, D8, D9 y D11 tal como se recomendaban; D10
fuera de alcance. **Para validar**: D2-D5 tal como quedan con el orden del humano, y D12.

- **D1 · Forma de pago: campos del `ctr`, sin leer el documento** (aprobada). Está estructurada en `ctr.pagide` (548 de 548)
  y el texto del `.doc` casa con ella en 9 de 11 contratos (2 ambiguos) (M21). Interpretar el texto no cabe en este
  microservicio (sería otro servicio, o albaranes mandando un `pagide` resuelto).
- **D2 · Orden de fuentes** (*para validar*; orden y lectura «de no encontrarla» del humano). *Problema*: con
  contrato → proveedor → respaldo, columna a columna, el **banco empeora claramente** (`ban` 77,8 % frente a 96,2 % con el
  respaldo primero; `bantipide` 45,8 %): el `prv` tiene banco y el escritorio no lo pone en pagarés ni recibos (M22, M26).
  El resto queda igual o mejor (pago sin contrato 99,3 %; `dirdir1` 95,4 % frente a 99,2 %). *Se aplica el orden del
  humano*. *Alternativa a validar*: banco del primer origen solo si el efecto del pago es confirming o transferencia; si
  no, vacío (~96 %, M22).
- **D3 · Sin contrato** (*para validar*). Identidad del `prv` por CIF en la empresa de la obra (L17: uno en 422 de 429) y
  cascada `prv` → respaldo (pago 99,3 %, `cueide` 100 %); `ivadif` del respaldo (97,0 %; 0 fijo daría 100 %). Códigos
  nuevos `proveedor_no_encontrado` y `proveedor_ambiguo` (este, solo si el respaldo por CIF no desempata). *Alternativas*:
  `ivadif` 0 sin contrato; desempatar siempre con error.
- **D4 · Sin respaldo** (*para validar*; decidido por el humano que no es error). Se retira `proveedor_sin_albaran_previo`;
  todo sale del contrato o del proveedor (M26, columna «sin respaldo»: pago con contrato 83,9 %, sin él 96,5 %). Afecta a
  50 de 865 proveedores (M25).
- **D5 · Columnas sin columna en el `prv`** (*para validar*). `dircon1` e `ivadif` van del `ctr` al respaldo; `ivadif` se
  toma del `ctr` aunque sea 0 (es una marca, no un dato que falte). `eioide` sale de la cascada (98,3 %), no del 1 fijo de
  F-009; `cueide`, 99,9-100 %.
- **D6 · `INSERT` de columnas fijas y test centinela** (aprobada): una columna nueva de Sigrid queda NULL o hace fallar el
  alta, nunca se copia.
- **D7 · Fijos** (aprobada): `tipgar` −1, NULL solo en `emptex` y `con.tex`, `fecent`/`feclim`/`cocide` a 0.
- **D8 · Retención** (aprobada; v1 D5-D8, D10, D11): con contrato siempre; sin contrato ninguna; `ctrrec` no soportado ⇒
  error; aviso informativo; sin interruptor; `cueide` del `ctrrec`.
- **D9 · Clásico intacto** (aprobada); limitación documentada en `sigrid_api.md` §8.6-§8.7.
- **D10 · `empide` desde el `usu`**: fuera de alcance; lo resuelve albaranes en su F-069 (M24: no hay clave en Sigrid).
- **D11 · Limpieza por `sql/write`** (aprobada), §Limpieza, tras desplegar y con autorización expresa para esa escritura.
- **D12 · Columnas imprescindibles sin fuente** (*para validar*). *Problema*: si ninguna fuente trae el dato, R5 escribe lo
  que deja el alta a mano (0, `''`), pero el escritorio **nunca** deja el pago a 0 y el banco hace falta para confirming y
  transferencia. Medido (M26): pago sin fuente 0 con respaldo; **13 de 429** sin contrato si no hay respaldo; banco con
  efecto confirming o transferencia y sin fuente, **4 de 426** con contrato y **5 de 231** sin él (el escritorio deja sin
  banco 12 de 261 `CC`); `cueide` sin fuente 3 de 1.293 (también a 0 a mano). *Recomendada*: escribir el vacío y el aviso
  informativo `cabecera_sin_dato` (sv9 lo hace bloqueante si quiere). *Alternativas*: sin aviso; o error (descartado por
  el humano como regla general: «no para nada»).

## Riesgos

- **El escritorio no es uniforme**: toma la forma de pago del contrato en el 84 % y del proveedor en el resto (M23). La
  lista sigue la regla del humano, no la moda; V1 en la UI lo confirma.
- **Cambio de esquema** de Sigrid: R10 y el `INSERT` fijo lo hacen visible en vez de copiar a ciegas.
- **Redondeo, recálculo del escritorio y concurrencia de `dcarec`**: como en la v1 (empate 3.775,30 · 0,05 → 188,77;
  V1-V3; applock + `UPDLOCK` + reintento R22).
- **Respaldo antiguo** (M3: un `AC18/`): ahora es el último recurso, para lo que no traen contrato ni proveedor.
- **`prv` desactualizado**: el pago y el banco del maestro pueden haber cambiado desde el último albarán; es el orden del
  humano y la verificación manual (R29) lo revisa.
