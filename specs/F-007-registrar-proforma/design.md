<!-- specs/F-007-registrar-proforma/design.md -->
# F-007 · Diseño (v3, pendiente de la PARADA 1)

Medición: [`progress/explore_F-007.md`](../../progress/explore_F-007.md) §v3 (**M27-M40**; M1-M15 siguen como hechos
de Sigrid). Núcleo: F-009 tal como lo dejó **F-015** (fusionada en `dev` y desplegada). Llamante: el microservicio
`proformas`, su F-005 ([`contrato_proformas.md`](contrato_proformas.md); traspaso en
`proformas/docs/referencia/01_traspaso_facturas.md`). Plantilla de hoja para los jefes de obra:
[`plantilla_hoja.md`](plantilla_hoja.md). La v2 (a origen, cadena, arrastre) queda superada.

## La decisión de fondo

Dos procesos (humano, 2026-10-25): **(a) cotejar** la proforma firmada del proveedor con Sigrid es lectura de
`facturas` (no es F-007); **(b) registrar en Sigrid la proforma del jefe de obra** es esto, y lo llama el microservicio
`proformas`: lee la hoja (xlsx o pdf), una persona casa en su bandeja las partidas con las líneas del contrato y elige
el producto de las nuevas, aprueba y entonces llama a la API con datos estructurados. La API resuelve el contrato,
valida contra Sigrid y escribe. `facturas` solo lee lo registrado por `sql/read`, por el `entref` de R12.

Se registra **por mes** (humano, 2026-10-24): la proforma lleva solo las partidas con MES ≠ 0 y el origen se calcula
sumando las del contrato. Es la forma que ya tienen 2.868 + 88 proformas de 2026 (M27) y, línea a línea, **es lo que
escribe hoy la vinculada de F-009** (M28: `canoriori` = `ctrpro.can`, `imporiori` = `ctrpro.tot`, sin anterior, sin
arrastre). Su factura es 1:1 y sin «hojitas» (M30), así que F-008 la facturará como factura las de mes de hoy. La
diferencia con un albarán es de cabecera: serie `PROF`, `cla 141` y `entref` `PROF<MMAA>_<obra>` (M31).

**Límite de microservicio: cabe.** Validar el contrato y las líneas contra Sigrid y dar de alta el documento con sus
efectos es de la pasarela. **No cabe** y es de `proformas`: leer el xlsx o el pdf, casar las partidas, elegir el
producto, el flujo de aprobación y bloquear la aprobación por exceso (con los avisos de F-007). Fuera también: facturación (F-008), asiento, provisiones `PREV`.

**Tamaño: una feature** (requisitos 150/150, en el tope), implementada en lotes (tasks.md). Si el humano pide además el modo sin
contrato completo o las hojas de varios contratos en una llamada, hay que partirla.

## Ficheros a crear

| Fichero | Capa | Qué contiene |
|---|---|---|
| `domain/models/proforma_models.py` | domain | `LineaProformaIn`, `ProformaRequest` (R1-R3), `ContratoResuelto`, `OrigenProforma`, `LineaProformaResultado`, `ProformaResponse(AlbaranCompraResponse)` (R10, R30) y `ProformaError(AlbaranCompraError)` / `FalloLineaProforma(FalloLinea)` con sus conjuntos (§Códigos), `reparto` y `candidatos` |
| `application/use_cases/proforma_statements.py` | application | SQL constante LP1-LP6 (§Sentencias) y puras: `normalizar_nombre`, `fecha_de_periodo`, `entref_por_defecto`, `candidatos_de_contrato`, `resolver_contrato`, `identificar_linea`, `comprobar_hoja`, `anterior_y_origen`, `buscar_del_mes`, `lineas_del_existente`, `es_proforma`, `traducir` (§Traducción). Sin E/S; autovalidado con `DatabaseReferenceGuard` |
| `application/use_cases/create_proforma_use_case.py` | application | `CreateProformaUseCase(CreateAlbaranCompraUseCase)` con `perfil = PERFIL_PROFORMA` (§Flujo) |
| `tests/test_f007_*.py`, `tests/fixtures/f007_*.json` | — | ver `tasks.md`; fixtures con las hojas de la obra 0719 (M29) |

## Ficheros a modificar

| Fichero | Qué cambia |
|---|---|
| `application/use_cases/create_albaran_compra_use_case.py` | §Costuras 1, 3 y 4: literales a `PerfilAlta` **con los mismos valores**; gancho `_comprobar_dentro`; `_Catalogo` con productos del contrato si el perfil lo pide |
| `application/use_cases/albaran_compra_statements.py` | §Costuras 2: `prefijo_de_serie(fecha, prefijo=PREFIJO_SERIE)` y `sellos_del_alta(..., prefijo=PREFIJO_SERIE)`; ninguna constante SQL cambia |
| `domain/models/albaran_compra_models.py` | §Costuras 5: `AlbaranCompraError` y `FalloLinea` validan contra atributos de clase (por defecto los conjuntos de hoy) |
| `config/settings.py`, `local.settings.sample.json` | las cinco claves de R4, con `parse_string_list`/`parse_string_dict` de F-009 |
| `function_app.py` | ruta `sigrid/proforma` (POST): validar, llave R5 solo con `commit`, `CreateProformaUseCase(repository, settings)` construido en la ruta (sin tocar la tupla de `build_dependencies`), `AlbaranCompraError` → 400 con `codigo` (y `reparto` si lo trae), `ValidationError` → F-012 |
| `docs/ARCHITECTURE.md`, `CLAUDE.md`, `azure-apps/sigrid_api.md` | R36 (`azure-apps` en commit aparte) |

## Ficheros que NO se tocan

Los casos de uso y modelos del clásico y de `albaran-directo`; **los tests y dorados de F-009 y F-015**
(`tests/fixtures/f009_caracterizacion.json` incluido); `infrastructure/` entero (bastan `execute_read_query`,
`read_full_row`, `read_rows_by`, `locate_contract`, `peek_next_ide`, `run_in_write_transaction`); `contrato_albaranes.md`
(no cambia lo que recibe albaranes); F-004, F-006; `infra/`. Sin ficheros `NN_nombre.sql`: SQL constante.

## Costuras en el núcleo (D12; sin cambio de conducta)

1. `PerfilAlta` (dataclass congelada): `endpoint`, `prefijo_serie`, `codigo_llave`, `cla` y los nombres de los campos
   de `Settings` (llave, prefijos de referencia, máximo de líneas, productos, naturalezas), y `productos_del_contrato:
   bool`. `PERFIL_ALBARAN` reproduce los literales de hoy; `CreateAlbaranCompraUseCase.perfil = PERFIL_ALBARAN`. Un test
   comprueba que todos los nombres existen en `Settings`.
2. Prefijo de serie como parámetro con el defecto de hoy (`AC`).
3. `_comprobar_dentro(cursor, request, cabecera)`: se llama en `work` justo después de E1 (idempotencia bajo
   `SIGRID_REFEXT_14`); en la base no lee nada.
4. `_Catalogo`: si `perfil.productos_del_contrato`, una sin vincular cuyo producto es el de alguna línea del contrato
   se admite fuera de la lista y toma naturaleza, cuenta y analítica de su plantilla de línea (L8b, L8) y el IVA de esa
   línea del contrato (R17); con `False` (albarán), igual que hoy.
5. Códigos: conjuntos cerrados como atributo de clase, para que `ProformaError` y `FalloLineaProforma` los amplíen.

`CreateProformaUseCase` sobrescribe `run` (su flujo y su traza R33), `_construir` (`super()` y después `dca.cla` =
`perfil.cla`) y `_comprobar_dentro` (R28). Todo lo demás es el núcleo, llamado con la petición traducida.

## Flujo

1. **Guardas** sin leer la base: prefijo de referencia, máximo de líneas y llave con `commit` (R26; R5 en la ruta).
   `ahora` (Madrid) una vez; fecha (R18).
2. **Obra** con el `_resolver_obra` del núcleo. **Idempotencia** (LP5, R23): si es una proforma del mismo contrato,
   se delega en el núcleo, que la devuelve `idempotente`; si no, `referencia_en_conflicto`.
3. **Contrato** (salvo `sin_contrato`): LP3 → R7 o R8 → LP4 de los candidatos → R8-R9 (§Contrato).
4. **Etapa 1 de líneas** (`identificar_linea`, `producto` presente, R13-R16, R19 de línea): todos sus fallos
   juntos en un `lineas_no_validas`.
5. **Comprobaciones** (R19 de cabecera) → LP1, LP2 → **ya registrada** (R24: `existente` sale ya con sus líneas de LP6, sin escribir) →
   avisos R20-R22.
6. **Traducción** a `AlbaranCompraRequest` (§Traducción) y **núcleo** (`_ejecutar`): etapa 2 de líneas (los fallos de
   F-009: partida, producto, naturaleza…), construcción, previa o transacción con R28 dentro.
7. **Respuesta** (R30): la del núcleo más `contrato`, `origen`, avisos de F-007 y los campos de línea; traza R33.

## Contrato (R7-R11; D4, D5)

- `candidatos_de_contrato(filas_lp3, fin_periodo, cif, nombre)`: `fec` ≤ `fin_periodo`, `nlin` > 0 y, por este orden,
  `entcif` = `cif` o `normalizar_nombre(nombre)` ⊆ `normalizar_nombre(entres)`. Con `cod_contrato` (R7) no se filtra
  por fecha ni proveedor: se busca por `cod` y se compara el CIF si viene.
- `resolver_contrato(candidatos, lineas_lp4, lineas_de_contrato)`: uno → `proveedor`; varios → los que contienen todas
  las (partida, `medicion_contrato`) de las líneas de contrato → uno → `lineas`. Si ninguno las contiene todas pero
  cada una está en exactamente un candidato → `hoja_de_varios_contratos` con `reparto` (referencia de línea → `cod`);
  si no, `contrato_ambiguo` o `contrato_no_resuelto`. Medido: 94,6 % único y correcto, 0,5 % incorrecto (M32).
- Elegido el contrato, el núcleo lo vuelve a localizar con `cod_contrato` + obra + `ctr.entcif` (`locate_contract`).

## Líneas (R13-R17; D6)

- `identificar_linea(linea, lineas_del_contrato)`: con `ctrpro_ide` (lo que manda `proformas`, casado por una
  persona), **solo** se comprueba que es una línea del contrato resuelto; si no (también si es de otro contrato de la
  obra), `linea_no_es_del_contrato`, sin buscar otra ni corregirla en silencio. Sin él (respaldo para otro llamante),
  el embudo de R14 (partida → medición → unidad → precio), quedándose en cada paso con las que casan si queda alguna.
  Varias → `linea_ambigua` + `candidatos`; ninguna → `linea_no_es_del_contrato`.
- Línea sin contrato: `producto` obligatorio (`producto_obligatorio`), de la lista de R4 o de los del contrato; R17
  pone naturaleza, cuenta, analítica e IVA del producto del contrato. M40: así son las extras de hoy.
- La partida que se escribe: vinculada, `partida_imputacion` o la del `ctrpro` (código y `paride`, F-009 R14b); sin
  contrato, `partida_imputacion` o `partida`. Las resuelve y valida el núcleo (F-009 R14-R16).

## Traducción (`traducir`, pura)

`AlbaranCompraRequest` con `database`, `cod_obra`, `usu`, `referencia_externa`, `commit`; `cod_contrato` = el
resuelto (o `None` sin contrato); `cif_proveedor` = `ctr.entcif` (o el de la petición sin contrato); `su_referencia`
= `su_referencia` o `entref_por_defecto(periodo, cod_obra)`; `fecha_albaran` = la de R18; `empide` `None`; y por
línea `LineaAlbaranIn` con `referencia_linea`, `ctrpro_ide` (de contrato) o `producto` (sin contrato), `descripcion`,
`unidad`, `cantidad`, `precio`, `partida` y `paride`. El orden de las líneas es el de la petición (`dcapro.pos`).

## Filas que se escriben

Las del modo extendido de F-009 con F-015 (`con`, `dca`, `dcapro` × N, `ctrprodes` por vinculada, `mov` si `tipmov`
1, `log`, `dcarec` 0-1, `UPDATE` de `ctrpro.canser` y de los estados del `ctr`), con la serie `PROF<aa>/` y `dca.cla`
141. Ni cadena (`docoritip`, `docoriide`, `canorilin` 0) ni nada de facturación.

## Sentencias nuevas (`proforma_statements`; todas con `?`)

- **LP1** (R20-R22, R24, R28): `SELECT c.ide, c.cod, c.fec, d.entref, d.totbas, d.docoritip FROM dbo.dca d JOIN dbo.con
  c ON c.ide = d.ide WHERE c.tip = ? AND d.ctride = ? AND (c.cod LIKE ? OR d.entref LIKE ?) AND ISNULL(d.entref, '')
  NOT LIKE ?` con `[14, ctride, 'PROF%', 'PROF%', 'PREV%']`.
- **LP2** (R20): `SELECT p.linoriide, SUM(p.can) FROM dbo.dcapro p JOIN dbo.dca d ON d.ide = p.docide JOIN dbo.con c ON
  c.ide = d.ide WHERE c.tip = ? AND d.ctride = ? AND p.docoritip = ? AND c.fec < ? AND (c.cod LIKE ? OR d.entref LIKE
  ?) AND ISNULL(d.entref, '') NOT LIKE ? GROUP BY p.linoriide` con `[14, ctride, 44, primer_dia, 'PROF%', 'PROF%',
  'PREV%']`.
- **LP3** (R7, R8): `SELECT t.ide, c.cod, c.fec, t.entcif, t.entres, (SELECT COUNT(*) FROM dbo.ctrpro p WHERE p.docide
  = t.ide) AS nlin FROM dbo.ctr t JOIN dbo.con c ON c.ide = t.ide WHERE c.tip = ? AND t.obride = ?` con `[44, obride]`.
- **LP4** (R8, R14, R16, R21): `SELECT p.ide, p.docide, p.paride, ISNULL(pp.cod, '') AS partida, p.can, p.pre, p.tot,
  p.unimed, p.proide, ISNULL(pc.cod, '') AS producto FROM dbo.ctrpro p LEFT JOIN dbo.obrparpar pp ON pp.ide = p.paride
  LEFT JOIN dbo.con pc ON pc.ide = p.proide WHERE p.docide IN {marcadores} ORDER BY p.docide, p.pos, p.ide`.
- **LP5** (R23): `SELECT c.ide, c.cod, d.cla, d.ctride FROM dbo.dca d JOIN dbo.con c ON c.ide = d.ide WHERE c.tip = ?
  AND d.synckey = ?` con `[14, referencia_externa]`.
- **LP6** (R24, solo con `existente`): `SELECT p.ide, p.linoriide, ISNULL(pc.cod, '') AS producto, p.can, p.pre, p.tot
  FROM dbo.dcapro p LEFT JOIN dbo.con pc ON pc.ide = p.proide WHERE p.docide = ? ORDER BY p.pos, p.ide` con
  `[con_ide]`. Probada en lectura sobre `AC26/25548` (M40): 6 líneas, 5 vinculadas.

Todas de lectura; LP1 se repite dentro de la transacción (R28) por el `cursor` del `work`. Ningún `UPDATE` nuevo.

## Applocks

Los de F-015, en su orden (`SIGRID_REFEXT_14`, `SIGRID_SERIE_14`, `SIGRID_IDE_con`, `_dcapro`, `_ctrprodes`, `_mov`,
`_dcarec`, `_log`). La repetición de R24 va bajo `SIGRID_REFEXT_14`, que ya serializa toda alta de la API de `tip 14`:
no hace falta uno nuevo. El escritorio no toma applocks (riesgo residual, §Riesgos).

## Códigos

- **Cabecera nuevos**: `escritura_proformas_deshabilitada`, `periodo_no_valido`, `contrato_no_resuelto`,
  `contrato_de_otro_proveedor`, `hoja_de_varios_contratos` (con `reparto`), `importe_mes_no_cuadra`,
  `hoja_descuadrada`, `proforma_del_mes_existente`. Se heredan los de F-009/F-015 que aplican (`contrato_ambiguo` y
  `contrato_no_encontrado` con el sentido de R7-R9).
- **Línea nuevos**: `linea_ambigua` (con `candidatos`), `producto_obligatorio`, `linea_descuadrada`; heredados
  `linea_no_es_del_contrato`, `producto_no_permitido`, `partida_*`, `naturaleza_no_valida`, `analitica_no_resuelta`.
- **Avisos nuevos** (informativos): `anterior_distinto_de_sigrid`, `supera_contrato`, `supera_contrato_10`,
  `contrato_a_origen`, `otra_del_mes`; más los de F-009/F-015 (`precio_distinto_del_contrato`, `supera_pendiente`,
  `retencion_del_contrato`, `cabecera_sin_dato`…).

## Decisiones (para el humano; recomendación en negrita)

- **D1 · Qué es F-007** *(decidido, 2026-10-24/25)*. El registro de la proforma del jefe de obra (b), llamado por
  `proformas` F-005 tras aprobar; el cotejo (a) es lectura de `facturas`. **La API recibe datos estructurados.**
- **D2 · Por mes** *(decidido)*. Problema: ¿qué escribir para que la de mes sea correcta y la factura cuadre?
  **`docoritip 0`, solo las partidas con MES ≠ 0 y vinculadas como F-009** (M28: así están el 100 % de las 2.956 de
  mes de 2026; M30: se facturan 1:1). Descartado: marcar el «check» (`docoritip 1`), que exige cadena y arrastre (v2).
- **D3 · Serie `PROF`** *(decidido, 2026-10-25)*. **`PROF<aa>/`, `cla 141`, `entref` `PROF<MMAA>_<obra>`**: el humano la
  mantiene sabiendo que hoy lo habitual es `AC` (2.868 `AC` de mes frente a 88 `PROF`, M27). La cabecera de una `PROF`
  de mes solo difiere de una `AC` de mes en `cla` (M31); LP1 encuentra también las `AC` con `entref` `PROF%`. El
  `entref` es el contrato de lectura entre `proformas` y `facturas`. V6 confirma en la UI que se ve y factura igual.
- **D4 · Contrato: lo resuelve la API y el llamante lo cambia.** *Interpretación del líder*, anotada como tal: «el
  humano» es la persona de la bandeja de `proformas`, que ve la previa y, si no está de acuerdo, reenvía con
  `cod_contrato`. Propuesta: **`cod_contrato` manda; si no viene, obra + proveedor (CIF o nombre normalizado) y, si
  quedan varios, las líneas de contrato** (94,6 %, 0,5 % mal, 4,9 % a la persona; M32), devolviendo
  `contrato.resuelto_por` y `candidatos`. Un `ctrpro_ide` de otro contrato es error (D6), nunca cambia el resuelto.
  Alternativas: contrato obligatorio (la hoja lo trae a veces); nombre solo en el llamante (frágil, M32).
- **D5 · Hoja de dos contratos** (1,7 %, M32). **Error `hoja_de_varios_contratos` con el reparto línea → contrato**, y
  `proformas` manda una petición por contrato con el mismo `periodo` (dos proformas, dos referencias); R24 va por
  contrato, así que la segunda no salta por la primera. Alternativa: dos documentos en una llamada (rompe «una proforma
  por petición», la idempotencia y la previa).
- **D6 · Casado en `proformas`** *(decidido, 2026-10-25)*. `proformas` manda **siempre `ctrpro_ide`** en las líneas de
  contrato y **siempre `producto`** en las nuevas, que elige una persona. La API **solo valida** que el `ctrpro_ide` es
  del contrato resuelto (`linea_no_es_del_contrato` si no, también si es de otro contrato de la obra); no re-identifica
  ni sustituye. El embudo de R14 queda de respaldo para quien no lo mande; **no hay producto por defecto**. Medido
  (M40): en las de mes de la 0719 todas las de contrato van vinculadas y lo sin vincular son las extras, con el
  producto del contrato (`/25548`: 5 de 6; BERENJENO con `SM1004`).
- **D7 · ANTERIOR frente a Sigrid: aviso, no error.** Σ de las proformas previas del contrato casa en 3 de 3 hojas de
  la 0719 (M29), pero facturas vio diferencias por «bis» y anulaciones (1 de 4 exacta). Alternativa: error con
  `forzar`. ORIGEN = ANTERIOR + MES de la propia hoja sí es error (R19).
- **D8 · Avisos de Administración** (correo del 2026-10-21). **En F-007, avisos informativos `supera_contrato`
  (> 100 %) y `supera_contrato_10` (> 110 %)** sobre Σ `ctrpro.tot` (= «IMPORTE TOTAL» de la hoja; `ctr.tot` es neto
  de retención o con IVA, M29); medido 2,2 % y 3,5 % de los contratos (M35). **Avisar al administrativo o al jefe de
  obra y frenar la aprobación es de `proformas` (en su bandeja) y bloquear la factura, de `facturas` o F-008**, que
  deciden con estos avisos.
- **D9 · Fecha y cabecera**: la de la v2 (M36: 96,4 % en el mes) y la lista blanca de F-015 sin más cambios que D3.
- **D10 · Ya registrada**: **`existente` (200, sin escribir) si hay una del mismo contrato y mes con el mismo total**
  (±0,05), con sus líneas (LP6: `dcapro.ide`, `linoriide`, producto, cantidad, precio, importe) para que `proformas`
  enlace sin otra lectura; con otro total, error salvo `otra_del_mes` (3,9 % de los meses llevan dos, M36). Por
  contrato, nunca por obra ni subcontratista (D5). Alternativa: confiar en la idempotencia (duplicaría las que
  Administración dé de alta a mano en la transición).
- **D11 · Configuración**: llave propia y listas propias; despliegue propuesto `SM9999`, `SB9999`, `SM370001` (los tres
  más usados sin contrato, M34; `SM370001` sin `mov`, `tipmov` 0), **pendiente de Administración (V8)**; tope 500.
  **Sin endpoint de lista de productos** (como albaranes): `proformas` tiene su App Setting, contenida en
  `SIGRID_PROFORMA_PRODUCTOS_SIN_CONTRATO`, y lee descripciones y productos del contrato por `sql/read`.
- **D12 · Reutilización: subclase del caso de uso de F-009 con cinco costuras** y sus dorados intactos (R31). La
  petición se traduce a la de F-009 (§Traducción). Descartado: copiar el núcleo; un modo nuevo de `sigrid/albaran`.
- **D13 · Contratos que van a origen** (24,7 % de los contratos con proformas desde julio, M37). **Aviso
  `contrato_a_origen`**; que Administración decida (V8) si se bloquean. Alternativa: error.
- **D14 · Sin contrato** (15,3 % de las de mes, M27). **Dentro, solo con `sin_contrato` explícito y `cif_proveedor`**
  (camino de F-015); sin él, una hoja sin contrato resuelto es `contrato_no_resuelto`. Alternativa: fuera (alta a mano).

## Preguntas para `proformas` (con su humano)

Decidido el 2026-10-25 y ya no se pregunta: `ctrpro_ide` y `producto` siempre (D6), `usu` = quien aprueba en la
bandeja, `referencia_externa` = `PRF-` + id de `proformas`, una petición por contrato (D5), previa desde la bandeja.

1. ¿Mandan el **CIF** del subcontratista o solo el nombre de la hoja? (R8 admite los dos; el CIF es más seguro.)
2. ¿Mandan solo las partidas con **MES ≠ 0** y el MES por línea (en xlsx, ORIGEN − ANTERIOR)?
3. ¿Qué avisos (`supera_contrato_10`, `anterior_distinto_de_sigrid`, `contrato_a_origen`) bloquean la aprobación?

## Riesgos

- **Tocar el núcleo de F-009 (crítico, en producción con la llave abierta).** Costuras de solo nombres y ganchos
  vacíos; dorados de F-009 y F-015 intactos; mutación sobre todo lo cambiado; avisar a albaranes antes de fusionar.
- **Carrera con el escritorio**: si Administración da de alta a mano la misma proforma en el mismo segundo, puede
  quedar duplicada (residual, como F-009). Mitiga R24 dentro de la transacción.
- **Contrato mal resuelto** (0,5 %, M32): la previa enseña el contrato y `resuelto_por`; la persona de la bandeja de `proformas` lo corrige.
- **Contratos a origen** (M37): una de mes deja su cadena sin ese mes; aviso D13 y V8.
- **Carga**: la previa se llama desde la bandeja antes de aprobar, una por proforma y sin ráfagas; tope de 500 líneas
  (R4) y balanceador a 230 s. Si una previa se corta, no se relanza en el acto (F-013).
- **Lecturas pesadas**: LP1-LP4 y LP6 van por contrato, obra o documento, nunca por toda la base (en la medición v3, dos consultas
  globales con subconsultas sobre `ctrpro` se cortaron a los 240 s).
