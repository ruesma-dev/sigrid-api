<!-- specs/F-007-registrar-proforma/design.md -->
# F-007 · Diseño (v2, pendiente de la PARADA 1)

Medición: [`progress/explore_F-007.md`](../../progress/explore_F-007.md) (**Mn**). Diccionario:
[`azure-apps/sigrid_tablas.md`](../../../azure-apps/sigrid_tablas.md). Núcleo: F-009
([`requirements`](../F-009-alta-albaran-compra/requirements.md), [`design`](../F-009-alta-albaran-compra/design.md))
tal como lo deje **F-015** (spec en curso). Llamante: app de facturas, F-063
([`facturas/progress/explore_alta_sigrid.md`](../../../facturas/progress/explore_alta_sigrid.md)).

## La decisión de fondo

Una proforma es un albarán de compra de la serie `PROF<aa>/` (`sercon` 230) con `dca.cla 141` (M1): mueve stock si
`tipmov` 1, sirve el contrato y nace en 1 `PDT`. La de la hoja de certificación es **a origen** (`docoritip 1`, M17)
y forma una **cadena lineal** por contrato (M19): cada una arrastra todas las líneas de la anterior, con la cantidad
del MES (o 0) y la acumulada en `canoriori` (M11, M23). Hoy las dan de alta a mano administrativos y jefes de obra;
en adelante, **todas por la app vía este endpoint**, que convive con las manuales: detecta la que ya existe (R11) y
encadena con la última, sea manual o suya (R12).

**El endpoint resuelve la cadena; el llamante identifica las líneas.** Ninguna clave de texto identifica la línea de
contrato (M20: partida + descripción es única solo en el 75 % de los contratos), así que la API **no casa por
texto**: devuelve en la previa la cadena con sus líneas (`cadena.lineas_anteriores`, R4) y el llamante, con su humano
de revisión, manda `linea_anterior_ide`, `ctrpro_ide` o `producto` (D9).

**Límite de microservicio: cabe.** Dar de alta un documento del ERP con sus efectos (cadena, stock, servido,
retención, totales) es de la pasarela, y Sigrid no tiene triggers. Leer la hoja, decidir qué línea es cuál y cuándo
se registra es de facturas. Fuera: facturación (F-008), asiento (`tip 20`, M1), provisiones `PREV`/`ANUL` (M16).

**Tamaño: cabe en una feature** (requisitos 133/150). Partirla (F-007a primera de cadena, F-007b encadenamiento)
no sirve al consumidor: 1.642 de las 1.963 a origen desde 2025 son encadenadas (M17). Se implementa **en lotes**
(tasks.md), como F-009.

## Dependencia de F-015

F-015 cambia el núcleo que esto reutiliza: plantilla de cabecera **solo de la serie `AC`** y `dcarec` **desde
`ctrrec`** (con su cálculo de `tot`/`totpag`). F-007 **se implementa después de F-015 cerrada**, sobre su rama
fusionada en `dev`, y usa su constructor de `dcarec` tal cual (R23). Si F-015 cambia de forma (nombres, firmas,
clases de retención admitidas), esta spec se revisa antes de `in_progress`.

## Ficheros a crear

| Fichero | Capa | Qué contiene |
|---|---|---|
| `domain/models/proforma_models.py` | domain | `LineaProformaIn`, `ProformaRequest` (R1-R2), `LineaAnterior` y `CadenaProforma` (R4), `ProformaResponse(AlbaranCompraResponse)` con `estado` ampliado y `cadena`; `ProformaError(AlbaranCompraError)` y `FalloLineaProforma` con sus conjuntos cerrados (§Códigos) |
| `application/use_cases/proforma_statements.py` | application | SQL constante LP1-LP8 (§Sentencias) y puras: `fecha_de_periodo`, `entref_por_defecto`, `buscar_existente`, `elegir_anterior`, `asignar_lineas`, `arrastrar_linea`, `ajustar_nueva_vinculada`, `ajustar_nueva_sin_vincular`, `ajustar_dca_proforma`, `es_proforma`. Sin E/S; se autovalida con `DatabaseReferenceGuard` |
| `application/use_cases/create_proforma_use_case.py` | application | `CreateProformaUseCase(CreateAlbaranCompraUseCase)`: `perfil = PERFIL_PROFORMA` y las sobrescrituras de §Costuras |
| `tests/test_f007_*.py` + `tests/fixtures/f007_*.json` | — | ver `tasks.md` |

## Ficheros a modificar

| Fichero | Qué cambia |
|---|---|
| `application/use_cases/create_albaran_compra_use_case.py` | §Costuras: los literales de hoy (`_ENDPOINT`, prefijo `AC`, `APPLOCKS`, nombres de los campos `sigrid_albaran_*`, código de la llave) pasan a un `PerfilAlta` de clase con **los mismos valores**; métodos sobrescribibles ya existentes (`_leer_cabecera`, `_resolver_lineas`, `_construir`, `_respuesta`) y un gancho nuevo `_resolver_dentro(cursor, construido)` que en la base devuelve `construido` sin leer nada |
| `application/use_cases/albaran_compra_statements.py` | `prefijo_de_serie(fecha, prefijo=PREFIJO_SERIE)`; ninguna constante SQL cambia |
| `domain/models/albaran_compra_models.py` | `AlbaranCompraError` y `FalloLinea` validan contra un atributo de clase (`CODIGOS`), por defecto los conjuntos de hoy; nada más |
| `config/settings.py`, `local.settings.sample.json` | las cinco claves de R3, con `parse_string_list`/`parse_string_dict` de F-009 |
| `function_app.py` | ruta `sigrid/proforma` (POST) con el esqueleto de `sigrid_albaran` extendido: validar, llave R6 solo con `commit`, `CreateProformaUseCase(repository, settings)` construido en la ruta (sin tocar la tupla de `build_dependencies`), `AlbaranCompraError` → 400 con `codigo`, `ValidationError` → `validation_error_response` (F-012) |
| `docs/ARCHITECTURE.md`, `CLAUDE.md`, `azure-apps/sigrid_api.md` | R35 (commit aparte en `azure-apps`) |

## Ficheros que NO se tocan

Los casos de uso y modelos del clásico y de `albaran-directo`; los tests y dorados de F-009 y F-015;
`infrastructure/security/*`; `sql_server_repository.py` (bastan `execute_read_query`, `read_full_row`,
`read_rows_by`, `locate_contract`, `peek_next_ide`, `run_in_write_transaction`); F-004, F-006; `infra/`;
`contrato_albaranes.md` (no cambia el contrato de albaranes). Sin ficheros `NN_nombre.sql`: SQL constante.

## Costuras (D6)

`PerfilAlta` (dataclass congelada) con `endpoint`, `prefijo_serie`, `applocks`, `llave`, `codigo_llave` y los
nombres de los campos de `Settings` (prefijos, productos, naturalezas, máximo de líneas); `PERFIL_ALBARAN` reproduce
los literales de hoy y `PERFIL_PROFORMA` los de R3. Un test comprueba que todos los nombres existen en `Settings`.

`CreateProformaUseCase` sobrescribe:
1. `_leer_cabecera`: obra y contrato (R7), proveedor de `ctr.entide`, fecha (R8), idempotencia (R29), cadena
   (LP1-LP2: R10-R14), plantilla (R9) y las columnas del contrato (LP7).
2. `_resolver_lineas`: líneas de la anterior (LP3-LP5), `asignar_lineas` (R15-R16), las nuevas con el `_Catalogo` de
   F-009 (lista y mapeo del perfil) y `anterior_no_casa` (R14); todos los fallos juntos.
3. `_construir`: `super()` para lo común y después, puras: `arrastrar_linea`, `ajustar_nueva_*`,
   `ajustar_dca_proforma`; la retención la pone ya el núcleo de F-015.
4. `_resolver_dentro`: repite LP1-LP2 en la transacción (R27); si la anterior o la existente cambian, vuelve a
   construir con lo leído (el `work` es reentrante en F-009).
5. `_respuesta`: añade `cadena` y el estado `existente`.

## Cadena (R10-R14)

- **LP1** da por cada a origen del contrato: `ide`, `cod`, `fec`, `docoriide`, `punta` (nadie la cita) y `ori` =
  Σ round(`canoriori`·`pre`, 2) de todas sus líneas. **LP2**, por documento y `ctrpro` de la petición, Σ`can` y
  Σ`canoriori`.
- `buscar_existente` (R11): documentos con |`ori` − (`importe_anterior` + `importe_mes`)| ≤ 0,05 y, por `ctrpro`
  pedido, `can` igual y, con `cantidad_anterior`, `canoriori` = esa + `cantidad` (±0,0001). Uno → `existente`;
  varios → `proforma_existente_ambigua`.
- `elegir_anterior` (R12-R13): con `importe_anterior` 0, ninguna; si no, puntas con |`ori` − `importe_anterior`| ≤
  0,05 y sin `cantidad_anterior` en contradicción. Medido sobre 773 encadenadas: 745 única y correcta, 1 varias, 27
  ninguna, 0 incorrectas (M25). Existente antes que anterior: si la hoja ya está en Sigrid, la punta es ella; por
  eso el total del MES va en cabecera (`importe_mes`) y la previa con `lineas` vacía ya la detecta.
- Una manual del mismo mes con otras cantidades **no** se duplica en silencio: su punta ya no casa con
  `importe_anterior` y sale `anterior_no_encontrada` (salvo cadenas paralelas de igual importe, M26).

## Filas que se escriben

- **`con`** (R21): F-009 con prefijo `PROF`; `log` como F-009.
- **`dca`** (R22): plantilla R9 (anterior → última `PROF` del proveedor (LP6) → plantilla `AC` de F-015; M24: 88/48/20
  de 156 primeras) con los overrides de F-009 y: `cla` 141, `docoritip` 1, `docoriide`, `ivadif` del contrato,
  `pagide`/`pagtex`/`pagfor` del contrato si `pagide` > 0, `entref`, `fecdoc`, y a 0 `idefac`, `fecfac`, `horfac`,
  `antestfac`, `antestser`, `antestped`, `estped`, `pasdeside`, `pasori`, `docrelide`, `facoriide` (M4, M15).
- **`dcapro`**: arrastradas = copia de la línea de la anterior (es su plantilla) con R17 y el seguimiento a 0 de
  F-009 (`_SEGUIMIENTO_A_CERO`); nuevas como F-009 con R18-R19. `pos` con `numerar` de F-009.
- **`ctrprodes`**, **`mov`**, **`ctrpro`**, **`ctr`**, **`dcarec`**: R23. `E9_SERVIDO` solo con `can` ≠ 0.

## Sentencias nuevas (`proforma_statements`; todas con `?`)

- **LP1** `SELECT d.ide, c.cod, c.fec, d.docoriide, CASE WHEN EXISTS (SELECT 1 FROM dbo.dca s WHERE s.docoriide =
  d.ide) THEN 0 ELSE 1 END AS punta, (SELECT ISNULL(SUM(ROUND(p.canoriori * p.pre, 2)), 0) FROM dbo.dcapro p WHERE
  p.docide = d.ide) AS ori FROM dbo.dca d JOIN dbo.con c ON c.ide = d.ide WHERE c.tip = ? AND d.ctride = ? AND
  d.docoritip = ?` (`[14, ctride, 1]`).
- **LP2** `SELECT p.docide, p.linoriide, SUM(p.can), SUM(p.canoriori) FROM dbo.dcapro p JOIN dbo.dca d ON d.ide =
  p.docide JOIN dbo.con c ON c.ide = d.ide WHERE c.tip = ? AND d.ctride = ? AND d.docoritip = ? AND p.docoritip = ?
  AND p.linoriide IN {marcadores} GROUP BY p.docide, p.linoriide` (`44` = contrato).
- **LP3** `SELECT * FROM dbo.dcapro WHERE docide = ? ORDER BY pos, ide`; **LP4** `SELECT ide, cod FROM
  dbo.obrparpar WHERE ide IN {marcadores}`; **LP5** `SELECT ide, cod FROM dbo.con WHERE ide IN {marcadores}`.
- **LP6** `SELECT TOP 1 c.ide FROM dbo.con c JOIN dbo.dca d ON d.ide = c.ide WHERE c.tip = ? AND c.emp = ? AND
  d.entide = ? AND d.cla = ? AND c.cod LIKE ? ORDER BY c.ide DESC` (`[14, emp, entide, 141, 'PROF%']`).
- **LP7** `SELECT entide, ivadif, pagide, pagtex, pagfor FROM dbo.ctr WHERE ide = ?`.
- **LP8** = L11 de F-009 con `d.cla` y `d.ctride` en la lista de columnas (la de F-009 no cambia).

## Applocks

Orden fijo: `SIGRID_REFEXT_14`, **`SIGRID_PROFORMA_CADENA`**, y después los de F-009/F-015 en su orden
(`SIGRID_SERIE_14`, `SIGRID_IDE_con`, `_dcapro`, `_ctrprodes`, `_mov`, `_dcarec`, `_log`). Solo este endpoint toma
el de cadena: dos altas de la API sobre el mismo contrato se serializan; ninguno se toma en orden inverso.

## Códigos (§R5)

Cabecera nuevos: `escritura_proformas_deshabilitada`, `periodo_no_valido`, `proveedor_sin_documento_previo`,
`proforma_existente_ambigua`, `anterior_no_encontrada`, `anterior_no_valida`, `cadena_ambigua`,
`lineas_obligatorias`, `importe_mes_no_cuadra` (precio efectivo: el pedido, o el de la anterior o del `ctrpro`). Línea nuevos: `linea_anterior_no_valida`, `linea_ambigua`, `linea_repetida`,
`anterior_no_casa`. Se heredan los de F-009/F-015 que aplican; `proveedor_sin_albaran_previo` no sale de aquí.

## Flujo

1. Guardas sin leer la base (R25, R6 en la ruta); `ahora` (Madrid) una vez; fecha (R8).
2. Obra, contrato y LP7; LP8 (R29 sale ya); LP1-LP2 → existente (R11 sale ya) → anterior (R12-R13); plantilla.
3. Líneas: LP3-LP5, asignación, nuevas con el catálogo de F-009 (todos los fallos juntos) y R20.
4. Construcción pura → en dry-run, `previsto` con `cadena`, `cod` e `ide` provisionales.
5. Con `commit`, `run_in_write_transaction(work)` con `perfil.applocks`; dentro, idempotencia y `_resolver_dentro`.
6. Traza R32 y respuesta.

## Decisiones (abiertas para el humano; recomendación en negrita)

- **D1 · Consumidor: resuelta** (humano, 2026-10-19): la app de facturas, F-063. Volumen: decenas al día, tope ~50.
- **D2 · Encadenamiento: dentro**, por **importe ANTERIOR total ±0,05 € + cantidades ANTERIOR por línea si vienen**
  (M25: 96,4 % única y correcta, 0 incorrectas); `cod_proforma_anterior` opcional para deshacer `cadena_ambigua` o
  `anterior_no_encontrada` con un humano. Descartado casar solo por cantidades de las líneas con MES (85 ambiguas).
- **D3 · Retención: la de F-015**, sin reglas propias.
- **D4 · Cabecera:** **`docoritip` 1 siempre** (cerrado por M17); **`ivadif` y forma de pago del contrato** (M22:
  94 %); **sin vencimiento**: la `dca` no lo tiene, es de la factura (F-008).
- **D5 · Plantilla: anterior → última `PROF` del proveedor → plantilla `AC` de F-015**; sin ninguna,
  `proveedor_sin_documento_previo` (13 % de las primeras, M24: la primera la da de alta un humano).
- **D6 · Reutilización: subclase del caso de uso de F-009 con costuras mínimas** y sus dorados intactos (R30).
  Descartado: los cinco ganchos de la v1 dentro del núcleo (ahora serían más y en producción) y copiar el caso de uso.
- **D7 · Configuración: listas propias** con `SB9999`/`SM9999` (M23: los nuevos más frecuentes con `tipmov` 1);
  `SM370001` (`tipmov` 0, 246 líneas) y `MA9999`/`XA9999`, **fuera hasta que negocio diga**; tope 500 líneas.
- **D8 · Fecha: último día del periodo si ya pasó, hoy si es el mes en curso**, o `fecha_proforma` dentro del
  periodo (M16: 97,7 % en el mes certificado, sin día fijo). Alternativa: siempre la de recepción.
- **D9 · Líneas: las identifica el llamante por `ide`** con la ayuda de la previa (`lineas` vacía → la cadena) y,
  para una primera de cadena, una consulta de `ctrpro` por `sql/read` documentada en `sigrid_api.md`. Descartado
  casar por texto en la API (M20) y un endpoint de lectura propio (si facturas lo pide, feature aparte).
- **D10 · Ya dada de alta: `existente` (200, sin escribir)** si casa por ORIGEN (M26: 2 pares en 913); con dos,
  `proforma_existente_ambigua`.
- **D11 · `entref`: `PROF<MMAA>_<cod_obra>` por defecto** (M16: la forma más usada).
- **D12 · Lotes:** una feature en lotes (A costuras y dorado, B primera y existente, C cadena y arrastre), no dos.

## Riesgos y decisiones

- **Tocar el núcleo de F-009 (crítico, en producción con la llave abierta).** Costuras de solo nombres, dorados de
  F-009 y F-015 intactos, campaña de mutación sobre todo lo cambiado; avisar a albaranes **antes** de fusionar.
- **Carrera con el escritorio**: el escritorio no toma applocks; si un humano da de alta la misma PROF en el mismo
  segundo, puede quedar duplicada (residual, como F-009). La API contra sí misma, serializada por contrato.
- **Transacción grande**: una encadenada de 500 líneas son ~1.500 `INSERT` (Sigrid hace lo mismo: `ctrprodes` y
  `mov` también con `can` 0, M6). Medir el tiempo en el dry-run real de T-manual frente al corte de 230 s.
- **TOTAL ANTERIOR de la hoja distinto del de Sigrid** (V4): sale `anterior_no_encontrada` con mensaje claro y
  `cod_proforma_anterior` como salida.
- **Para el líder (fuera de F-007):** hay 354 `AC` a origen desde 2025 (M19): la plantilla `AC` de F-015 puede ser
  una de ellas y clonar `docoritip`/`docoriide`; F-015 debería ponerlos a 0. La memoria del arnés sigue llamando al
  `tip 20` «documento de compra»: es el asiento (M1).
- **Descartado**: modo nuevo en `sigrid/albaran` (reabre el contrato con albaranes); `cif_proveedor` (la hoja no lo
  trae y el contrato lo fija); (contrato, mes) como clave de duplicada (M18: 18 cadenas con dos en un mes); escribir
  `med`/`canmed`; la regla de `canoriori` del albarán.
