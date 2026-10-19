<!-- specs/F-015-albaran-plantilla-y-retencion/design.md -->
# F-015 · Diseño (v1)

Medidas: [`progress/explore_F-015.md`](../../progress/explore_F-015.md) (Mn). Base: `specs/F-009-alta-albaran-compra/`
(design §Sentencias, §Filas, §Flujo) y su contrato [`contrato_albaranes.md`](../F-009-alta-albaran-compra/contrato_albaranes.md).

## La decisión de fondo

Dos correcciones del **modo extendido** y nada del clásico, en las mismas tres piezas de F-009 (modelo, constructor puro,
caso de uso). Ni ruta nueva, ni App Setting nueva, ni cambios en `infrastructure/`.

- **O1**: la L5 filtra por serie y clase, y `construir_dca` deja de arrastrar de la plantilla la facturación, la cadena y
  los totales en divisa, que el escritorio no pone en un alta (M5, M6).
- **O2**: con contrato, una `dcarec` copiada de su único `ctrrec` y el total neto, como el escritorio (M9-M13). Importa
  por dinero, no por estética: **la factura hereda la retención del albarán** (M16: 95,9 % con ella frente a 14,3 % sin
  ella), y el asiento del albarán no la usa (M15: solo la base), así que escribirla no cambia nada de lo ya contabilizado.
- **Límite de microservicio: cabe.** Copiar al albarán lo que el contrato ya dice es construir bien el documento; no
  decide ninguna retención.

## Ficheros a crear

| Fichero | Qué contiene |
|---|---|
| `tests/test_f015_statements.py` | L5, L11, L16, E6b, `insertar_dcarec`, E12 carácter a carácter; `resolver_retencion`, `calcular_retencion`, `construir_dcarec`, `construir_dca` (R3, R4, R10), `numerar` con `dcarec`, applocks (R16), control negativo (R19) |
| `tests/test_f015_use_case.py` | Flujo con el doble: plantilla (R1, R2), retención soportada y no (R6-R11), respuesta (R12, R13), traza (R14), previa (R15), commit, reintento y relecturas (R16-R18) |

## Ficheros a modificar

| Fichero | Qué cambia |
|---|---|
| `application/use_cases/albaran_compra_statements.py` | §Sentencias, §Funciones puras y §Filas de este diseño |
| `application/use_cases/create_albaran_compra_use_case.py` | §Flujo |
| `domain/models/albaran_compra_models.py` | `retencion_no_soportada` en `CODIGOS_CABECERA`; `retencion_del_contrato` en `CODIGOS_AVISO` |
| `tests/f009_dobles.py` | Nombres de L16, E6b, el `INSERT` de `dcarec` y su relectura; `ctrrec` en `lecturas_base` vacío por defecto (los casos de F-009 no cambian); el cursor contesta E12 de `dcarec` con lo insertado |
| `tests/test_f009_statements.py`, `tests/test_f009_use_case.py`, `tests/test_f009_equivalencia.py` | Solo donde fijan L5, L11, `APPLOCKS`, `_TOTALES_DCA`, la `dca` o las diferencias declaradas (R20, R21); cada cambio cita su R |
| `function_app.py` | Solo el docstring de `sigrid_albaran` (plantilla AC y retención) |
| `specs/F-009-alta-albaran-compra/contrato_albaranes.md` | v8.3, §Contrato de este diseño (**antes** de implementar, R22) |
| `docs/ARCHITECTURE.md`; `azure-apps/sigrid_api.md` | Applock `SIGRID_IDE_dcarec`, `dcarec`, plantilla AC (R22; `azure-apps` en commit aparte) |

## Ficheros que NO se tocan

`create_purchase_albaran_use_case.py`, `create_direct_albaran_use_case.py`, `albaran_domain_models.py`,
`albaran_directo_models.py`, `tests/test_f009_caracterizacion.py` y **`tests/fixtures/f009_caracterizacion.json`** (R5,
D4), `infrastructure/` entero (el repositorio ya tiene `peek_next_ide` y `run_in_write_transaction`), `config/settings.py`,
`infra/`, F-004, F-006. Sin ficheros `NN_nombre.sql`: SQL constante, como F-009.

## Sentencias (constantes en `albaran_compra_statements.py`; todas con `?`)

- **L5** (R1), las dos variantes, añaden `AND c.cod LIKE ? AND d.cla = ?` antes del `ORDER BY`, con
  `PATRON_SERIE_PLANTILLA = "AC__/%"` y `CLA_ALBARAN = 0` como parámetros: `[14, emp, entide|cif, "AC__/%", 0]`. El `_`
  de `LIKE` es un carácter: `AC26/`, `AC18/`; no `ACX/` ni `NTC`. M3: 0,9-5,2 s en frío, como la de hoy.
- **L11** (R13) añade `d.tot` al final: `SELECT c.ide, c.cod, c.fec, d.entide, d.obride, d.totbas, d.totdoc, d.tot ...`.
- **L16** (R6, R8): `SELECT r.ide, r.recide, r.pos, r.valdef, r.valpor, r.valcan, r.valmod, r.valfij, r.reccla,
  r.cueide, r.ivaide, r.tex, r.resalt, r.item, x.cla, c.cod FROM dbo.ctrrec r LEFT JOIN dbo.rec x ON x.ide = r.recide
  LEFT JOIN dbo.con c ON c.ide = r.recide WHERE r.docide = ? ORDER BY r.pos, r.ide` (`[ctride]`; los `LEFT` dejan ver el
  `recide` 0 o sin catálogo de M11).
- **E6b** (R16): `SELECT ISNULL(MAX(ide), 0) + 1 FROM dbo.dcarec WITH (UPDLOCK, HOLDLOCK)`, como E3-E6.
- **E8 `dcarec`**: `INSERT INTO dbo.dcarec (<DCAREC_COLUMNAS>) VALUES (?, …)` con columnas fijas, como `mov`:
  `DCAREC_COLUMNAS` = `ide, docide, recide, pos, bas, valdef, valpor, valcan, valmod, valfij, cuo, tex, reccla, cueide,
  ivaide, ivacuo, reqcuo, refide, resalt, frasupide, item` (orden de `sys.columns`, M14).
- **E12** (R18): `SELECT COUNT(*) FROM dbo.dcarec WHERE docide = ?`.
- **`APPLOCKS`**: `SIGRID_REFEXT_14`, `SIGRID_SERIE_14`, `SIGRID_IDE_con`, `_dcapro`, `_ctrprodes`, `_mov`,
  **`SIGRID_IDE_dcarec`**, `_log`. Nadie más toma el nuevo; F-006 (`_con`, `_log`), el clásico y el directo siguen en el
  mismo orden relativo: sin orden inverso posible.

## Funciones puras (application, sin E/S)

```python
CLASES_RETENCION_BASE = {5: "totbas", 3: "totbas", 4: "totdoc"}   # garantía, IRPF, «sobre total» (M12)

def resolver_retencion(filas_ctrrec: list[dict]) -> dict | None
    # [] -> None (sin retención). Si no, la única fila; ValueError con el motivo legible (el caso de uso lo
    # convierte en retencion_no_soportada) si hay > 1, `recide` 0/None o sin `cla` (sin fila en rec), `cla`
    # fuera de CLASES_RETENCION_BASE, `valfij` != 0 o `ivaide` != 0 (None cuenta como 0). R8.
def calcular_retencion(ctrrec: dict, totales: dict) -> tuple[Decimal, Decimal]
    # bas = totales[CLASES_RETENCION_BASE[cla]] pasado a Decimal con _decimal (repr: exacto, sale de una suma
    # en Decimal); cuo = redondear_euros(bas · _decimal(valpor)). R9.
def construir_dcarec(ctrrec: dict, *, bas: Decimal, cuo: Decimal) -> dict
    # R7: ide/docide None (los pone numerar); copia de R7; ivacuo, reqcuo, refide, frasupide 0. bas/cuo como float.
```

`sumar_importes` sigue igual; `construir_dca` recibe además `cuo: Decimal` (0 sin retención) y `_TOTALES_DCA` cambia: `tot`
y `totpag` ← `totdoc − cuo` (R10); `totbasdiv`, `totivadiv`, `totdocdiv`, `totdiv` y `totpagdiv` ← 0 (R4); y se pisan a 0
las de `_RESETEO_CABECERA` = `fecfac, horfac, idefac, antestfac, docoritip, docoriide, pasdeside, pasori, docrelide,
fecpag` (R3). Las tres, **solo si la plantilla trae la columna**, como hoy.

## Filas

- **`FilasAlbaran`** gana `dcarec: list[dict]` (0 o 1; con valor por defecto `[]` para no romper a quien la construye) y
  `como_dict()` la devuelve en `filas.dcarec`. **`numerar`** gana `ide_dcarec: int | None`: `ide` y `docide` = `ide_con`;
  hay `dcarec` y `None` ⇒ `ValueError`, como con `mov`.
- **`dcarec`** (R7): la del `ctrrec` resuelto con `bas`/`cuo` de R9. `cueide` del `ctrrec` también en el 4 % en que el
  escritorio deja otro (M11; D11): no entra en el asiento del albarán (M15) y la factura lo toma de esta fila (M16; V3).
- **`dca`**: la de F-009 con R3, R4 y R10. **Sin `ctrrec` y con una plantilla PDT, sale idéntica a la de `dev`** (R20).

## Flujo del modo extendido (cambios sobre F-009 design §Flujo)

1. Igual.
2. L1-L5 (L5 con R1; sin filas ⇒ `proveedor_sin_albaran_previo`, mensaje «… ningún albarán de la serie AC …»), L11 (R30
   sale ya, ahora con `tot`, R13), L13 y, **con contrato, L16** + `resolver_retencion` ⇒ `cabecera.retencion` (o
   `retencion_no_soportada`, R8). Así un albarán ya escrito sigue siendo `idempotente` aunque su contrato cambie después.
3. Igual (líneas, todos los fallos).
4. `_construir`: `sumar_importes` → si `cabecera.retencion`, `calcular_retencion` y `construir_dcarec` → `construir_dca`
   con `cuo`. Previa: `numerar` con `peek_next_ide("dcarec")` (R15).
5. Commit, en `work`: E1-E7 como hoy; E8 `con`, `dca`, `dcapro`×N, `ctrprodes`×M, `mov`×K y, si hay `dcarec`, **E6b** y
   su `INSERT` (R16); E9-E11, E11b y E12 con la relectura de `dcarec` (R18). Reentrante: cada intento reserva su `ide` (R17).
6. Respuesta: `totales` + `tot`, `retenciones`, `n_retenciones` (R12); aviso `retencion_del_contrato` en `avisos` de
   cabecera en previa y en `creado` (R11); traza con `n_retenciones` (R14).

## Contrato con albaranes (lo que el líder pasa a albaranes ANTES de implementar; R22)

| Cambio | § del contrato | Qué hace sv9 (recomendación) |
|---|---|---|
| Plantilla solo de la serie `AC` y clase 0 | §4.1 paso 2; §3.3 `proveedor_sin_albaran_previo` («Cuándo») | Nada: mismo código, sigue en `no_admitido`. Lo dan de más 6 proveedores solo de proformas (M4) |
| Error nuevo **`retencion_no_soportada`** (cab.) | §3.3 | Mapearlo a **`no_admitido`** («la retención del contrato no se puede calcular: alta a mano»). Sin mapear, H25 lo lleva a `error`. 15 de 651 contratos (M11) |
| Aviso nuevo **`retencion_del_contrato`** (cab.) | §3.2 | Informativo. **No** debe ir a `ALTA_SIGRID_AVISOS_BLOQUEANTES`: saldrá en ~89 % de los albaranes con contrato con `ctrrec` (M9) |
| `totales.tot`, `totales.retenciones`, `totales.n_retenciones` | §3.1 | `totdoc` sigue siendo el total **sin** retención; el neto a pagar es `tot`. La comparación de la previa (F-053 R17) es por línea: no cambia |
| `filas.dcarec[]`; `cabecera.tot`/`totpag` netos; facturación y divisa a 0 | §3.1 | Nada (no se guarda, F-053 v6 R16) |
| `idempotente`: `totales.tot` y `retenciones` | §3.1 | Opcional: mostrarlos |
| Escribe además `dcarec` ×0-1; applock `SIGRID_IDE_dcarec` | §4.1 paso 4, §4.2 | Nada |
| Qué NO hace: retención sin contrato, `ctrrec` con base o importe fijo, con IVA o varios | §4.3 | Alta a mano |

Ningún campo de la petición cambia (§2 intacto). Versión: v8.3 del contrato, con su línea de cambios arriba.

## Equivalencia (R20) y dorado (R5)

- **Dorado** `f009_caracterizacion.json`: no se toca; `test_f009_caracterizacion.py` pasa sin cambios (T: `git diff dev`
  vacío en los dos y en los cuatro ficheros intocables de F-009 R4).
- **Equivalencia** (`test_f009_equivalencia.py`): el dato fijo no tiene `ctrrec` (el doble lo da vacío) ⇒ sin `dcarec` y
  `tot` = `totdoc`. Diferencias **nuevas** declaradas: las columnas de R3 y R4 en `dca` (el clásico las clona o pone los
  euros; el extendido, 0). Un caso nuevo con `ctrrec` declara además `dcarec`, `tot`/`totpag` y el aviso.
- **Caso a caso** en los tests de F-009 que cambian: L5 (dos parámetros más), L11 (`d.tot`), `APPLOCKS` (uno más), la
  `dca` de la plantilla de prueba (R3 y R4) y `totales` (tres claves más). Nada más: si otro test cambia, es un defecto.

## Decisiones (abiertas: las valida el humano; recomendación en negrita)

| D | Pregunta | Recomendación y por qué | Descartadas |
|---|---|---|---|
| D1 | ¿Cómo se reconoce la serie AC? | **Prefijo `AC__/%` y `cla 0`**: ni `con` ni `dca` guardan la serie (M1); los dos juntos excluyen PROF, NTC y los 18 AC de clase 141 | Solo prefijo (entran los AC 141); solo `cla 0` (entran NTC y 8 PROF26) |
| D1b | ¿Sin ningún AC? | **Error `proveedor_sin_albaran_previo`, como hoy**: 6 proveedores de proformas (M4) | Plantilla PROF «limpiada» (arrastraría `cla`, cadena y `ivadif`) |
| D2 | ¿Limpiar facturación y cadena? | **Sí (R3)**: el alta del escritorio las deja a 0 (M5, fila PDT) y la plantilla está facturada el 80 %. Cambia también albaranes sin retención: justificado | Dejarlo para otra ficha |
| D3 | ¿Totales en divisa a 0? | **Sí (R4)**: el escritorio, 0 en 29.486 de 29.487 (M6); misma función | Ficha aparte |
| D4 | ¿Y el clásico, que tiene el mismo fallo y peor (L5 sin empresa ni serie, *fallbacks*)? | **No se toca**: R2/R4 de F-009 lo congelan, sv9 nunca lo llama y queda obsoleto con F-053; se documenta la limitación en `sigrid_api.md` §8.6-§8.7 | Corregirlo (rompe el dorado sin consumidor que lo pida) |
| D5 | ¿Retención también sin vinculadas y en devoluciones? | **Sí, siempre que haya contrato**: 99,1 % con vinculadas, 82,7 % solo sin vincular, 80,6 % devoluciones (M10); la base es el `totbas` entero | Solo con vinculadas |
| D6 | ¿Sin contrato? | **Ninguna**: es manual (M9: 3,8 %; `entrec` no es la fuente) | `entrec` del proveedor |
| D7 | ¿`ctrrec` no soportado? | **Error `retencion_no_soportada`** (alta a mano, 2,3 %): sin retención, la factura saldría sin ella (M16) | Aviso y albarán sin retención; calcular `valfij` (base tecleada, M12) |
| D8 | ¿Aviso `retencion_del_contrato`? | **Sí, informativo y no bloqueante**: deja ver en sv4 por qué el neto no es la valoración | Sin aviso (solo `totales`) |
| D9 | ¿Avisar de una plantilla vieja (M3: un `AC18/`)? | **No**: pago y efecto coinciden con el AC anterior en el 93-97 % (M7); afecta a 18 proveedores | Aviso `plantilla_antigua` |
| D10 | ¿Interruptor para la retención? | **No**: la grabación real de albaranes está apagada; volver atrás es redesplegar | App Setting `SIGRID_ALBARAN_RETENCION_ENABLED` |
| D11 | ¿`cueide` del `ctrrec`? | **Sí** (96,0 %, M11); el resto, V3 | `rec.cuecomide` (casa solo cuando los dos son 0) |

## Riesgos

- **Redondeo**: `totbas` sale de `Decimal` exacto (F-009 `sumar_importes`), así que `bas · valpor` no tiene el residuo
  binario de M12; test con el empate 3.775,30 · 0,05 → 188,77 y su negativo → −188,77.
- **El escritorio recalcula al editar** (V1): si al grabar en la UI cambia `cuo` o `cueide`, solo difiere esa fila. Se ve
  en la verificación manual (R23) antes de F-053 en real.
- **Concurrencia**: el `ide` de `dcarec` sigue la regla de las demás tablas (applock + `UPDLOCK` + reintento R27); el
  escritorio no toma applocks, igual que hoy con `mov`.
- **Retenciones fuera del contrato** (M9: 57 con contrato sin `ctrrec` y 249 sin contrato): siguen siendo manuales.
- **Equivalencia**: el clásico sigue escribiendo facturación y divisa de la plantilla; el test lo declara (D4).
