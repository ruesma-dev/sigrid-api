# F-015 · Diseño (v2)

Medidas: [`progress/explore_F-015.md`](../../progress/explore_F-015.md) (Mn). Base: `specs/F-009-alta-albaran-compra/`
(design §Sentencias, §Filas, §Flujo) y su contrato [`contrato_albaranes.md`](../F-009-alta-albaran-compra/contrato_albaranes.md).

## La decisión de fondo

Dos correcciones del **modo extendido** y nada del clásico, en las tres piezas de F-009 (modelo, constructor puro, caso de
uso). Ni ruta nueva, ni App Setting nueva, ni cambios en `infrastructure/`.

- **O1 · Lista blanca.** `con` y `dca` dejan de clonarse de una plantilla: se construyen columna a columna, cada columna con
  un origen (§Lista blanca), y se insertan con columnas fijas, como `mov` o la `con` de F-006. La forma de pago sale del
  **contrato**; el albarán anterior del proveedor (**respaldo**) solo aporta lo que el contrato no trae. Se mide contra lo
  que deja el escritorio en 1.293 altas a mano (M18, M20) y se corrige lo que hoy arrastra la API (M19: 60 de 68).
- **O2 · Retención.** Con contrato, una `dcarec` copiada de su único `ctrrec` y el total neto (M9-M13). Importa por dinero:
  **la factura hereda la retención del albarán** (M16) y el asiento del albarán no la usa (M15).
- **Límite de microservicio: cabe.** Copiar al albarán lo que el contrato y Sigrid ya dicen es construir bien el documento.
  **Interpretar el texto del contrato no cabe** (D1).

## Ficheros a crear

| Fichero | Qué contiene |
|---|---|
| `tests/test_f015_statements.py` | Lista blanca (R1, R2, R25 centinela), L5, L11, L16, E6b, `INSERT` de `con`/`dca`/`dcarec`, E12 carácter a carácter; `construir_con`, `construir_dca`, `resolver_retencion`, `calcular_retencion`, `construir_dcarec`, `numerar` con `dcarec`, applocks, control negativo |
| `tests/test_f015_use_case.py` | Flujo con el doble: respaldo (R6, R7), contrato y sin contrato (R3-R5), falta de columna (R10), retención (R12-R16), respuesta (R17-R19), previa (R20), commit, reintento y relecturas (R21-R23) |

## Ficheros a modificar

| Fichero | Qué cambia |
|---|---|
| `application/use_cases/albaran_compra_statements.py` | §Lista blanca, §Sentencias, §Funciones puras y §Filas |
| `application/use_cases/create_albaran_compra_use_case.py` | §Flujo |
| `domain/models/albaran_compra_models.py` | `retencion_no_soportada` en `CODIGOS_CABECERA`; `retencion_del_contrato` en `CODIGOS_AVISO` |
| `tests/f009_dobles.py` | Filas completas de respaldo (`DCA_COLUMNAS`) y de `ctr` (las 13 de contrato); sin lectura de la `con` de la plantilla; L16, E6b, `INSERT` y relectura de `dcarec`; `ctrrec` vacío por defecto |
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
| **contrato** (13; sin contrato, respaldo) | `entide`, `entcod`, `entres`, `entcif`, `entciftip`, `entcifpai`, `pagide`, `pagtex`, `pagfor`, `efeide`, `eioide`, `ivadif`, `cueide` | la del `ctr` (`cueide` del respaldo si la del `ctr` es 0/`None`) | M20, M21, M23; D1, D3, D5 |
| **respaldo** (8) | `banban`, `bansuc`, `bandig`, `bancue`, `ban`, `bantipide`, `dirdir1`, `dircon1` | la del respaldo | M20 (96,2 / 99,2 / 99,5 %), M22; D5 |
| **fijo** (106) | `tipgar` −1; `emptex` NULL; las demás de `_DCA_TEXTO` `''` y las demás numéricas 0 (`cla`, facturación, cadena, divisa, `fecent`, `feclim`, `cocide`, `estser`, `estfac`, `impdes`, `imprec`, `banide`…) | constante | M18 (0 o vacías en las 1.293), M19; D7 |

**`con`** (`CON_COLUMNAS` de F-006, todas fijas o calculadas, la fila que F-006 ya escribe): `ide` y `cod` de `numerar`,
`emp` de la obra, `tip` 14, `subtip` 0, `res` = `"<entres>. (<su_referencia>)"`[:128], `fec` de los sellos, `tex` NULL,
`cee` 0, `est` 1, `fecbaj` 0, `tiemod` = `sellos.tiemod`, `ico`/`delo`/`del`/`obr`/`doc` `''`, `serie` 0, `hor` 0 (M18).

Se declaran como `DCA_DE_CONTRATO`, `DCA_DE_RESPALDO`, `DCA_CALCULADAS` y `DCA_FIJAS` (dict columna → valor), y
`ORIGEN_DCA` (columna → origen) se **deriva** de ellas; un test exige que sus claves sean `DCA_COLUMNAS` sin huecos ni
repetidas (R25). Las bancarias siguen fuera de `cabecera` y `filas.dca` de la respuesta (H16).

## Sentencias (todas con `?`)

- **L5** (R6), las dos variantes: `... WHERE c.tip = ? AND c.emp = ? AND d.entide = ? AND c.cod LIKE ? AND d.cla = ? AND
  ISNULL(d.entref, '') NOT LIKE ? ORDER BY c.ide DESC` (`d.entcif = ?` en la otra), con `[14, emp, entide|cif, "AC__/%",
  0, "PROF%"]` (`PATRON_SERIE_RESPALDO`, `CLA_ALBARAN`, `PATRON_PROFORMA`). M3: 0,9-5,2 s en frío, como hoy.
- Se **quita** la lectura de la `con` de la plantilla (`_fila_completa(..., "con", ...)`): ya no se usa. La `dca` del
  respaldo y el `ctr` se siguen leyendo con `read_full_row`, como hoy.
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
def construir_dca(*, contrato: Mapping | None, respaldo: Mapping, fec: int, hor: int, su_referencia: str,
                  obride: int, ctride: int, almide: int, cenide: int, empide: int, totales: Mapping[str, float],
                  cuo: Decimal, referencia_externa: str) -> dict
    # Recorre DCA_COLUMNAS y aplica ORIGEN_DCA. Columna de contrato o respaldo ausente en su fila -> ValueError (R10).
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
2. Obra → contrato (fila completa del `ctr`, como hoy) → **L5 respaldo** (sin filas ⇒ `proveedor_sin_albaran_previo`,
   R7) → `dca` del respaldo (ya no la `con`) → L11 (idempotencia, con `tot`) → `conest`/`usu` → **con contrato, L16** y
   `resolver_retencion` (o `retencion_no_soportada`, R14). Un albarán ya escrito sigue siendo `idempotente` aunque su
   contrato cambie después.
3. Igual (líneas).
4. `_construir`: `sumar_importes` → retención (`calcular_retencion`, `construir_dcarec`) → `construir_con` y
   `construir_dca` con `contrato` (o `None`), `respaldo` y `cuo`. Previa: `numerar` con `peek_next_ide("dcarec")`.
5. Commit: como F-009 y, si hay `dcarec`, E6b y su `INSERT` tras los `mov` (R21); E12 de `dcarec` (R23); reentrante (R22).
6. Respuesta: `totales` + `tot`, `retenciones`, `n_retenciones`; aviso R16; traza con `n_retenciones` (R19).

## Contrato con albaranes v8.3 (lo pasa el líder a albaranes ANTES de implementar; R28)

| Cambio | § | Qué hace sv9 (recomendación) |
|---|---|---|
| Respaldo solo de la serie `AC`, `cla 0` y sin proformas (`entref` `PROF%`) | §4.1 paso 2; §3.3 `proveedor_sin_albaran_previo` | Nada: mismo código en `no_admitido`. Afecta a 50 de 865 proveedores (antes 6) |
| Cabecera por lista blanca: pago, efecto, condición de envío, IVA diferido y cuenta del **contrato**; banco y dirección del respaldo; facturación, fechas, divisa y Documentum a 0; `tiemod` del alta | §3.1 `cabecera`/`filas`, §4.2 | Nada (F-053 R16 no los guarda) |
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
  exige que el extendido tenga exactamente `CON_COLUMNAS`/`DCA_COLUMNAS`. `DECLARADAS["dca"]` = columnas de `ORIGEN_DCA`
  que no son de respaldo (derivado, no a mano); `DECLARADAS["con"]` = todas. Las de respaldo deben coincidir con el clon.
  `dcapro`, `ctrprodes` y `mov`, como hoy. Un caso con `ctrrec` declara además `dcarec` y el aviso.

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

## Decisiones (abiertas: las valida el humano; recomendación primero)

- **D1 · Fuente de la forma de pago.** *Problema*: el humano la sitúa en el texto del documento del contrato. Medido: está
  **estructurada** en `ctr.pagide` (100 % de 548 contratos), `pagtex`/`pagfor` salen de su `auxpag`, y en 11 contratos
  muestreados el texto del `.doc` casa con ella en 9 (2 ambiguos) (M21). *Recomendada*: `pagide`, `pagtex`, `pagfor` y
  `efeide` del `ctr`, sin leer el documento. *Alternativas*: (b) interpretar el `.doc`/`.pdf` (87 % con documento): texto
  libre de plantilla que a veces enumera opciones sin elegir y no distingue confirming TR/CH ni «+ ret»; si no se reconoce
  habría que caer al estructurado o dar error; y **no cabe aquí** (leer y entender ofimática no es de la pasarela a Sigrid):
  sería otro servicio, o albaranes, mandando un `pagide` resuelto en un campo nuevo. (c) `prv.pagide` (85,9 %).
- **D2 · Respaldo.** *Interpretación del líder, anotada*: «solo en caso de encontrar la info» se lee como «**de no**
  encontrarla en el contrato». *Recomendada*: respaldo solo para las 8 columnas que el contrato no trae (o trae peor) y,
  sin contrato, para las 13 de contrato; filtrado como R6. *Alternativas*: el `prv` como respaldo (igual en pago, peor en
  banco: 79,9 % frente a 96,2 %); sin respaldo (banco y dirección vacíos).
- **D3 · Altas sin contrato.** El modo extendido las admite (9 de 68). *Recomendada*: seguir admitiéndolas, con las 13 de
  contrato del respaldo (96-99 %, M20). *Alternativas*: del `prv` (96,5 % el pago); rechazarlas (código nuevo; cambia F-053).
- **D4 · Sin respaldo.** *Recomendada*: `proveedor_sin_albaran_previo`, con y sin contrato (50 de 865 proveedores, casi
  todos de proformas). *Alternativa*: con contrato, alta sin respaldo con banco del `prv` solo si el efecto es confirming o
  transferencia (M22, ~96 %) y dirección del `prv`, más un aviso nuevo.
- **D5 · Excepciones a «primero el contrato».** *Recomendada*: `dirdir1`/`dircon1` del respaldo (contrato 88,5/97,3 %,
  respaldo 99,2/99,5 %); `cueide` del respaldo cuando el contrato la tiene a 0 (11 %); `eioide` del contrato (97,7 %) en vez
  del 1 fijo de F-009; `ivadif` del contrato (89,0 %; respaldo 91,3 %), por la regla. *Alternativas*: todo del contrato;
  dirección del `prv` (99,1 %).
- **D6 · Mecánica.** *Recomendada*: `INSERT` de columnas fijas y test centinela: una columna nueva de Sigrid queda NULL o
  hace fallar el alta, nunca se copia. *Alternativa*: `SELECT *` del respaldo pisando lo no listado según su tipo (tolera
  columnas nuevas, pero las copia hasta que alguien las liste).
- **D7 · Fijos.** *Recomendada*: `tipgar` −1 (100 %), NULL solo en `emptex` y `con.tex`; `fecent`, `feclim` y `cocide` a 0
  aunque el contrato los traiga (el alta a mano coincide con él en el 21-58 %). *Alternativa*: copiarlos del contrato.
- **D8 · Retención** (v1 D5-D8, D10, D11, sin cambios): con contrato siempre (también sin vinculadas y en devoluciones);
  sin contrato ninguna; `ctrrec` no soportado ⇒ error; aviso informativo; sin interruptor; `cueide` del `ctrrec`.
- **D9 · Clásico**: no se toca (v1 D4); limitación documentada en `sigrid_api.md` §8.6-§8.7.
- **D10 · `empide` desde el `usu`** (pregunta de albaranes). *Recomendada*: fuera de alcance: no hay clave (`dni` y `ele`
  vacíos, `codemp` = `tarseg` en 6 de 24 usuarios) y el `empide` no es función del usuario (M24). *Alternativas*: `tarseg`
  con *fallback* al de la petición; el `empide` habitual del usuario en sus altas (heurística, 20 de 34).
- **D11 · Limpieza.** *Recomendada*: §Limpieza por `sql/write`, tras desplegar, con autorización expresa. *Alternativas*:
  Administración desde la UI (~60 a mano); dejarlas (32 apuntan con `idefac` a facturas de otros albaranes; no se ha medido
  qué hace el escritorio al facturarlas); añadir `eioide`.

## Riesgos

- **El escritorio no es uniforme**: toma la forma de pago del contrato en el 84 % y del proveedor en el resto (M23). La
  lista sigue la regla del humano, no la moda; V1 en la UI lo confirma.
- **Cambio de esquema** de Sigrid: R10 y el `INSERT` fijo lo hacen visible en vez de copiar a ciegas.
- **Redondeo, recálculo del escritorio y concurrencia de `dcarec`**: como en la v1 (empate 3.775,30 · 0,05 → 188,77;
  V1-V3; applock + `UPDLOCK` + reintento R22).
- **Respaldo antiguo** (M3: un `AC18/`): ahora solo aporta banco y dirección, o el pago sin contrato.
