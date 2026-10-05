<!-- specs/F-009-alta-albaran-compra/contrato_albaranes.md -->
# Contrato albaranes ↔ sigrid-api · alta de albaranes de compra

**F-009 de sigrid-api (modo extendido de `POST /api/sigrid/albaran`) ↔ F-053 de albaranes (sv9).**
Escrito el 2026-10-05 a petición del humano: «lo que va a recibir sigrid-api y lo que debe devolver
a albaranes, con almacén, líneas, etc., sin dejarnos nada». **Refleja F-009 v5.1** (2026-10-05): los
huecos de §5 que tocaban a F-009 están resueltos en su spec o pendientes de una medición de T0; el
estado de cada uno, en la tabla de §5. **v5.1** (respuestas del humano a la v5): no hay campo
`almacen`, la línea **sin partida** es el «almacén» de Ruesma (§0, §2.2); y sigrid-api **no** rechaza
fechas futuras (desaparece `fecha_no_valida`; H19 entero en albaranes).

**Dueño**: sigrid-api (es quien expone el endpoint). albaranes lo consume y **no lo copia**: enlaza
aquí. Si este documento y la spec de F-009 discrepan, manda la spec de F-009; si la discrepancia es
un hueco de §5, se resuelve en la spec que toque y se actualiza este documento.

**Fuentes cruzadas** (todas leídas enteras, solo lectura; sin llamar a sigrid-api, Azure ni BBDD):

| Fuente | Versión |
|---|---|
| sigrid-api `specs/F-009-alta-albaran-compra/` y `progress/spec_F-009.md` | **v5.1** (2026-10-05: huecos de §5, decisiones del humano sobre H4, H8, H9, H17, H20, H28 y H31, y respuestas a N4-N12). Este documento se escribió contra la v4 (2026-10-02) y se actualizó a la v5 y a la v5.1 |
| sigrid-api código vivo: `create_purchase_albaran_use_case.py`, `create_direct_albaran_use_case.py`, sus modelos y `function_app.py` | rama `feature/F-009-alta-albaran-compra` |
| albaranes F-053 `specs/F-053-alta-sigrid/` y `progress/spec_F-053.md` (worktree `albaranes-F-053`) | v5 (2026-10-01, alineada con F-009 **v2**) |
| albaranes F-051 `specs/F-051-almacen-por-linea/` y `progress/spec_F-051.md` + decisiones del humano del 2026-10-05 (D1, D2, D3, D4, D5, D7) | v3 (2026-10-02) |
| albaranes F-049 `specs/F-049-partida-de-la-lista/` y `progress/spec_F-049.md` | v4 (2026-10-03) |
| `azure-apps/sigrid_api.md` y `azure-apps/sigrid_tablas.md` (`con`, `dca`, `dcapro`, `ctrpro`, `ctrprodes`, `obrparpar`, `alm`, `obr`) | `f7da7cd` |

---

## 0. Resumen y huecos

- **Qué es**: UNA llamada HTTP por albarán aprobado. sv9 manda cabecera + líneas (vinculadas a una
  línea de contrato o sin vincular, cada una con o sin partida, positivas o devoluciones) a
  `POST /api/sigrid/albaran` en modo extendido; sigrid-api valida, resuelve contra Sigrid y, si
  `commit=true`, escribe el albarán entero en una transacción. Siempre primero una **previa**
  (`commit=false`) y, solo en modo real y sin motivos, la **grabación** (`commit=true`) idéntica.
- **Qué devuelve**: 200 con `estado` `previsto` / `creado` / `idempotente` (superconjunto de la
  respuesta clásica, con `avisos[]` por código y, por línea, `referencia_linea`, `total`, `partida`,
  `almide`…), o 400 con `details.codigo` (cabecera) y `details.lineas[]` (por línea).
- **Sin partida** (decisión del humano, F-051 D1 y respuesta a la v5 del 2026-10-05): en Ruesma
  «almacén» es **dejar la línea sin partida**; no hay un concepto almacén aparte. sv9 **no manda**
  `partida` (o la manda `null`) y sigrid-api escribe `dcapro.paride = 0`, **nunca** la del `ctrpro` ni
  la de otra línea. No existe campo `almacen` (con `extra="forbid"`, mandarlo da 400 sin código).
  `almide`/`cenide` (el almacén físico del stock y del `mov`) se escriben en **toda** línea, como el
  escritorio (M8). Vale en vinculadas (siguen consumiendo su línea de contrato, D4) y sin vincular, de
  cualquier familia (D2). Pasar después la línea a partida (al desacopiar) se hace en Sigrid, fuera
  de la API.
- **Estado del contrato**: la forma está cerrada en F-009 v4, pero **F-053 v5 se alineó con F-009 v2**
  y hay huecos que, sin resolver, hacen fallar o escribir mal el alta. **33 huecos** en §5. Tras
  **F-009 v5** quedan abiertos los de albaranes y los que dependen de la repetición de T0 (M3, M9, M11,
  M14, M16, M17, M18); tabla de estado al principio de §5:

  | Gravedad | Huecos | Qué pasa si no se resuelven |
  |---|---|---|
  | **Bloqueantes** (el alta falla o escribe en la empresa/obra equivocada) | H1, H2, H3, H4, H5, H6, H7, H8, H9 | `usu` ausente ⇒ todas las altas a `error`; obras repetidas entre empresas ⇒ `obra_ambigua`; albarán clonado en otra empresa; partida validada en albaranes y rechazada en sigrid-api; líneas sin partida rechazadas aunque el humano decidió que son válidas; longitudes; unidad incoherente con la cantidad en vinculadas; descuentos convertidos en devoluciones; reintento tras anular |
  | **Importantes** (escribe, con datos dudosos) | H10-H21 | analítica/almacén/columnas heredadas de otra obra; aviso de vinculada sin partida; obras con dos almacenes; precio «distinto» por decimales; IVA de otro proveedor; cuentas bancarias guardadas en albaranes; partida ambigua sin salida; idempotencia sin casar líneas; fechas absurdas; servicios como material; CIF |
  | **Menores / a confirmar** | H22-H33 | topes, repartos con cantidad 0, mapeo de códigos en F-053, índices, avisos, mediciones T0 pendientes, decisiones a confirmar, documentación |

- **Quién mueve ficha** (un hueco puede tocar a varios):
  - **F-009** (spec v5/v5.1 de sigrid-api, ya incorporados): H2, H3, H10-H18, H21, H26, H27, H32, H33.
  - **F-053**: H1, H5-H8, H12-H14, H16, H18, H19, H21, H22, H24-H26.
  - **F-049**: H4, H17, H23. **F-051**: H5.
  - **Humano** (decisión o medición): H4, H8, H9, H17, H20, H28-H31.
  - Ninguno exige un servicio nuevo ni sale del límite de sigrid-api.

---

## 1. Para qué y quién

### 1.1. Flujo

```
sv4 (revisor aprueba)            ── MensajeFeedback{accion:"alta", document_id, approved_by} ──▶ q-feedback
sv9 albaranes-alta-sigrid        ── lee merge + valoración (PostgreSQL albaranes)
   │  validación local (F-053 R10) ── si falla: estado no_admitido, sin llamar a nadie
   │  sql/read: ¿alta a mano con mismo CIF + nº? (F-053 R14) ── si sí: ya_en_sigrid
   ├─▶ POST /api/sigrid/albaran  {…, commit:false}   ── PREVIA (siempre, en los dos modos)
   │      200 previsto | idempotente   /   400 details.codigo   /   5xx, timeout
   │  compara la previa con lo aprobado (F-053 R17) ── si difiere: revisar
   │  modo simulacion ⇒ simulado (fin)
   ├─▶ POST /api/sigrid/albaran  {…, commit:true}    ── GRABACIÓN (solo modo real, una vez, sin reintento)
   │      200 creado | idempotente  ⇒ registrado
   └─▶ POST /api/sigrid/concepto-grafico (PDF, contip 14) ── adjunto (fuera de este contrato, §7)
sv4 lee albaran_altas_sigrid y bloquea el documento mientras esté en_curso / incierto / registrado.
```

### 1.2. Dueños

| Pieza | Dueño | Notas |
|---|---|---|
| Endpoint, validación, resolución en Sigrid, escritura, idempotencia, códigos | **sigrid-api F-009** | Spec v5.1 en `specs/F-009-alta-albaran-compra/` |
| Qué albarán se registra, qué líneas, a qué precio, con qué partida o sin ella | **albaranes** (sv6 valora, sv4 aprueba, sv9 construye la petición) | F-053 (sv9), F-051 (almacén), F-049 (partida de la lista y obras) |
| Estado del alta (`albaran_altas_sigrid`) | **sv9** (escribe), sv4 (lee) | F-053 design §6 |
| Clave de función | sigrid-api | La de siempre (decisión del humano, F-053 design §11) |

### 1.3. Llaves de seguridad y modos

Para que una **grabación** llegue a Sigrid tienen que estar abiertas **todas**:

| Llave | Lado | Defecto | Qué cierra |
|---|---|---|---|
| `ALTA_SIGRID_DESDE_UTC` | sv9 y sv4 | vacía | Vacía = F-053 apagada: ni previa ni grabación (solo documentos aprobados desde esa fecha) |
| `ALTA_SIGRID_COMMIT` | sv9 | `false` | Solo el literal `true` = modo **real**; si no, modo **simulación**: sv9 nunca manda `commit=true` |
| `SIGRID_DOMAIN_WRITE_ENABLED` | sigrid-api | `false` (en `dev`: **`true`**) | Commit de todos los endpoints de dominio |
| `SIGRID_ALBARAN_WRITE_ENABLED` (**nueva**, F-009 R8) | sigrid-api | `false` | Commit de `sigrid/albaran` (los dos modos) y de `albaran-directo` |
| Credenciales `SQL_SERVER_WRITE_*` + `ALLOWED_WRITE_DATABASES=["ruesma"]` | sigrid-api | — | Sin ellas, `escritura_albaranes_deshabilitada` / `base_de_datos_no_permitida` (vacía **no** abre) |
| `SIGRID_ALBARAN_PREFIJOS_REFERENCIA` (**nueva**) | sigrid-api | `[]` (despliegue `["ALB-"]`) | Vacía ⇒ toda referencia rechazada, **también en previa** |
| `SIGRID_ALBARAN_PRODUCTOS_SIN_CONTRATO` (**nueva**) | sigrid-api | `[]` (despliegue `["MA9999"]`) | Productos admitidos en líneas sin vincular |
| `SIGRID_ALBARAN_MAX_LINEAS` (**nueva**) | sigrid-api | `100` | Tope de líneas, también en previa |
| `SIGRID_ALBARAN_EMPRESAS_OBRA` (**nueva**, v5, H2) | sigrid-api | `[]` (despliegue `[1]`) | Empresas en que se busca la obra. Vacía ⇒ `obra_de_empresa_no_permitida`, también en previa |

Matriz de modos:

| sv9 | sigrid-api | Resultado |
|---|---|---|
| Simulación | cualquiera | Solo previas (lecturas con credenciales de lectura). Estado final `simulado`, `no_admitido`, `revisar`, `error` o `ya_en_sigrid`. **Nunca** escribe |
| Real | `SIGRID_ALBARAN_WRITE_ENABLED=false` | La previa funciona; la grabación da 400 `escritura_albaranes_deshabilitada` → `error`. ERP intacto |
| Real | todas abiertas | Previa + grabación única → `registrado` |

La instancia de sigrid-api se llama `dev` pero **escribe en la base real** `ruesma`. Desde local,
`ALTA_SIGRID_COMMIT` no se pone nunca.

---

## 2. Petición

`POST /api/sigrid/albaran`, cabecera `x-functions-key`, cuerpo JSON. El modo se decide **por las
claves presentes** (F-009 R1): con `lineas` o `referencia_externa` ⇒ extendido. sv9 manda siempre
las dos y **nunca** `lineas_recibidas` (⇒ 400 `peticion_mixta`). `extra="forbid"`: una clave que
F-009 no conozca ⇒ 400 sin código. Textos recortados (strip). Números como números JSON, no texto.
La previa y la grabación llevan **el mismo cuerpo** salvo `commit`.

### 2.1. Cabecera

| Campo | Tipo | Oblig. | Long. / dominio | Origen en albaranes | Destino en Sigrid | Notas |
|---|---|---|---|---|---|---|
| `database` | str | sí | ≥1 | `SIGRID_API_DATABASE` de sv9 (`ruesma`) | base de negocio | En commit debe estar en `ALLOWED_WRITE_DATABASES` |
| `cod_obra` | str | sí | ≤24 | `albaran_documents_merge.obra_codigo` (VARCHAR 128), **canonizado** por F-049 A2 tal como figura en Sigrid (`0676-B`, `0695`, `900`) | `con` (`tip 42`) → `dca.obride`, `dcapro.obride` | F-053 R10: falta → `falta_obra`; >24 → `campo_demasiado_largo`. Solo obras de la empresa 1 (F-049 O1). **H2 (v5)**: sigrid-api busca la obra solo en las empresas de `SIGRID_ALBARAN_EMPRESAS_OBRA` (`[1]`) |
| `cif_proveedor` | str | sí | ≤24 | `albaran_documents_merge.proveedor_cif` (VARCHAR 64; corregido por F-052) | `dca.entcif` (sin vincular: plantilla por CIF); con contrato, `ctr.entcif` del localizador | Formato **H21**: sigrid-api pasa a mayúsculas y quita espacios (v5); sin prefijo de país ni guiones, lo garantiza albaranes |
| `cod_contrato` | str \| null | no | ≤24 | `albaran_valuations.contrato_codigo` **solo si hay ≥1 línea vinculada**; si no, `null` (F-053 R12) | `dca.ctride` (0 sin contrato), `dcapro.docoricod` | Obligatorio si alguna línea trae `ctrpro_ide` (F-009 R6). **H31**: F-009 v5 lo admite también **sin** vinculadas (enlaza `dca.ctride`, plantilla y almacén del contrato, ningún `UPDATE` de medición) |
| `referencia_externa` | str | sí | 1-128; prefijo `ALB-` | `"ALB-" + albaran_documents_merge.id` (document_id, 36) | `dca.synckey` (128) | Clave de idempotencia (F-009 R30). **H9** |
| `su_referencia` | str | no (defecto `""`) | ≤128 | `albaran_documents_merge.numero_albaran` (VARCHAR 128) | `dca.entref` (128); `con.res` = `"<entres>. (<su_referencia>)"` recortado a 128 | F-053 R10: falta → `falta_numero_albaran` |
| `usu` | str | **sí** (v3) | 1-24 | `ALTA_SIGRID_USUARIO` de sv9 (fijado en F-053 T0c, debe existir en `dbo.usu`) | `log.usu` de la fila de alta | **F-053 v5 no lo manda: H1** |
| `fecha_albaran` | int `AAAAMMDD` \| null | no (null = hoy, Madrid) | 19000101-29991231 | `albaran_documents_merge.fecha` (`AAAA-MM-DD`) → entero | `con.fec`, `dca.fecdoc`; prefijo de serie `AC<aa>/` | El `mov` se fecha en el alta, no aquí (N1). F-053 la manda siempre. Solo formato y rango: una fecha futura **no** se rechaza (v5.1: lo hace la app; **H19**) |
| `empide` | int \| null | no | ≥1 | `ALTA_SIGRID_EMPIDE` o `null` | `dca.empide` | `null` ⇒ `SIGRID_ALBARAN_EMPIDE` (2425207 por defecto del código) |
| `commit` | bool | no (`false`) | — | `false` en la previa; `true` en la grabación (solo modo real) | — | |
| `lineas` | lista | sí | 1..`SIGRID_ALBARAN_MAX_LINEAS` | una por línea a registrar (§2.2) | `dcapro` ×N, `ctrprodes`, `mov` | Orden = `dcapro.pos` (64, 128…). **H22, H26** |

### 2.2. Línea

| Campo | Tipo | Oblig. | Long. / dominio | Origen en albaranes (`albaran_line_valuations` salvo indicación) | Destino en Sigrid | Notas |
|---|---|---|---|---|---|---|
| `referencia_linea` | str | sí | 1-64 (1-24 si M18); única en la petición | `str(id)` de la línea valorada | respuesta y errores; si M18 deja libre `dcapro.refent`, también `dcapro.refent` (**H18**, F-009 R30b) | sv9 casa la respuesta por este campo, nunca por posición |
| `ctrpro_ide` | int ≥1 | uno de los dos | — | Vinculada: `albaran_contrato_lines_merge.sigrid_ide` de `matched_contrato_line_id`, con `sigrid_ide` no nulo y `derived_contrato_line_id` nulo | `dcapro.linoriide`, `docoritip 44`, `docoriide`; `ctrprodes.docproide`; `ctrpro.canser` | Debe ser del contrato (`linea_no_es_del_contrato`) |
| `producto` | str | uno de los dos | 1-24 | Sin vincular: `ALTA_SIGRID_PRODUCTO_POR_DEFECTO` (`MA9999`) | `dcapro.proide` resuelto por `(emp de la obra, cod)`, `tip 3` | Debe estar en `SIGRID_ALBARAN_PRODUCTOS_SIN_CONTRATO`. **H20** |
| `descripcion` | str \| null | sí en sin vincular | ≤128 | Sin vincular: `descripcion_linea` (TEXT) o la de `albaran_lines_merge`, **recortada a 128 (H6)**. Vinculada: **no se manda (H7)** | `dcapro.res` (128) | Vinculada sin ella ⇒ `ctrpro.res` |
| `unidad` | str \| null | no | ≤8 | Sin vincular: `unidad_albaran` (VARCHAR 32) recortada a 8. Vinculada: **no se manda o `unidad_contrato` (H7)** | `dcapro.unimed` (8) | Vinculada sin ella ⇒ `ctrpro.unimed` |
| `cantidad` | float ≠ 0 | sí | negativa = devolución | Vinculada: `cantidad_convertida` (unidad del contrato); sin vincular: `cantidad_albaran`. **Signo = el de `importe_calculado`** (F-053 R12). **H8** | `dcapro.can`; `mov.canent`; `ctrprodes.can`; `ctrpro.canser += cantidad` | 0 o nula ⇒ F-053 `cantidad_no_valida`; vinculada sin convertida ⇒ `cantidad_sin_convertir` |
| `precio` | float | **sí, también en vinculadas** | — | `abs(importe_calculado) / abs(cantidad)`: unitario **neto** (el importe ya lleva el descuento) | `dcapro.pre`; `tar` = `precio` y `dto = ''` si difiere del `ctrpro` (aviso), si no `tar`/`dto` del `ctrpro` | `tot = cantidad·precio` a 2 decimales con `ROUND_HALF_UP` (H33) = importe aprobado; igual al `ctrpro.pre` si difiere ≤ 0,0001 (H14); < 0 ⇒ fallo de línea `precio_negativo` (H8, v5) |
| `partida` | str \| null | no (ausente o `null` ⇒ **sin partida**) | 1-24 | `codigo_partida_final` (VARCHAR 64) si **no está vacío** (ya es el código tal como figura en la lista de la obra, F-049 R20); vacío ⇒ no se manda (**H5**) | `dcapro.paride` = `obrparpar.ide` de esa obra; sin partida, 0 | Nunca se hereda del `ctrpro` ni de otra línea (F-009 R14). **H4, H6, H17** |
| `paride` | int ≥1 | no; **solo si M3** | — | `ide` de la hoja que conserve F-049 (H17) | `dcapro.paride` | Solo existe si la repetición de M3 da códigos repetidos entre imputables (F-009 R14b): va con `partida` y debe ser de la obra, imputable y con ese código (`paride_no_valido`) |

### 2.3. Casos de línea

| Caso | Campos que manda sv9 | Qué escribe sigrid-api |
|---|---|---|
| **Vinculada con partida** | `ctrpro_ide`, `cantidad` (convertida), `precio`, `partida` | `dcapro` con plantilla = última `dcapro` del producto del `ctrpro`; `proide`, `ivaide`, `unimed`, `almide`, `cenide`, `caaide`, `docori*` y `res` del `ctrpro`; `paride` = la pedida (si ≠ la del `ctrpro`: aviso `partida_distinta_del_contrato`, el `ctrpro` no se toca); `ctrprodes` (1 por línea, `can` con signo); `canser += cantidad`; `mov` si el producto hace movimientos |
| **Vinculada sin partida** (D4) | `ctrpro_ide`, `cantidad`, `precio`, sin `partida` | Igual que la anterior (mismo contrato, precio y servido: **consume medición**) pero `paride = 0` (nunca la del `ctrpro`) y `almide` del `ctrpro` o del contrato. Aviso `sin_partida_en_linea_con_partida` si el `ctrpro` tiene partida (H12, v5.1) |
| **Sin vincular con partida** | `producto:"MA9999"`, `descripcion`, `unidad`, `cantidad`, `precio`, `partida` | `dcapro` con plantilla = última `dcapro` de MA9999 **de esa empresa**; `natide` del maestro; `cueide`, `ivaide` de la última `dcapro` de MA9999 **del mismo proveedor** o, si no hay, de la del producto con aviso `iva_de_otro_proveedor` (**H15**, v5); `pre` = `tar` = `precio`, `dto ''`; sin `docori*`, sin `ctrprodes`, sin tocar `canser`; almacén y centro del contrato o de la obra (H10); `caaide` de la partida [M16]; columnas ajenas de la plantilla a vacío (H11) |
| **Sin vincular sin partida** | ídem sin `partida` | `paride = 0`; almacén y centro del contrato o, sin él, de la ficha de obra (`obr.almide`/`cenide`) o de su único `alm`; si no sale uno ⇒ `almacen_de_obra_no_resuelto` (**H13**, v5); `caaide` del almacén [M16] |
| **Devolución** (cantidad < 0), vinculada o no | `cantidad` negativa, `precio` ≥0 | `can`, `tot`, `ivacuo` negativos; `mov` de **entrada** con `canent` < 0 y PMP `(stock·pma + can·pre)/(stock + can)` (regla A medida en M5); vinculada: `ctrprodes.can` negativa, `canser += cantidad` aunque quede < 0 (aviso `servido_negativo`); stock < 0 ⇒ aviso `stock_negativo`; `estser` puede volver a 0 |
| **Varias líneas al mismo `ctrpro`** (p. ej. una compuesta repartida por F-049, o la misma línea de contrato en dos partidas) | un `ctrpro_ide` repetido con distinta `referencia_linea` | Cada una su `dcapro`, su `ctrprodes` y su `mov`; **no se suman** (F-009 R12) |
| **Línea resultado de reparto de compuesta** (F-049 R23: `P4/P5.01.09` ⇒ N líneas con una parte cada una, cantidad e importe a partes iguales, la primera con el resto) | N líneas normales, una partida cada una | N `dcapro` normales; sigrid-api no sabe que vinieron de una compuesta. **H23** |
| **Complementos, portes, recargos, sintéticas** | Como cualquier línea: vinculada si casaron con una línea del contrato; si no, MA9999 con su descripción; partida = la de su base (F-051 R7, F-049 R24) o sin partida | Igual. Si MA9999 hace movimientos, un porte suma stock de material (**H20**: puerta dura, sin M9 cerrada no hay modo real) |
| **ALM impreso** en el papel | sv6 la deja sin match (derivada `alm_acopio`, partida vacía) ⇒ **sin vincular sin partida** | Igual que sin vincular sin partida. **H30** |
| **Línea sin importe** (`importe_calculado` nulo o 0) | **No se manda** (F-053 R13) | Nada: no consume medición ni mueve stock. **H29** |
| **Línea con partida que la lista no valida** (F-049 `validada=false`) | Se manda tal cual tras aprobarla el revisor | sigrid-api la resuelve o la rechaza (`partida_no_encontrada` / `_no_imputable` / `_ambigua`) |
| **Pasar a partida una línea sin partida** (al desacopiar el material) | **No se manda** | Nada: se hace en Sigrid, fuera de la API (v5.1). F-009 no modifica albaranes |

### 2.4. Reglas de construcción en sv9 (F-053 R10-R13, con las correcciones de §5)

1. **Solo documentos «valorados»** (`ruesma_comun.valoracion.esta_valorado`, F-053 R38) y aprobados
   desde `ALTA_SIGRID_DESDE_UTC`.
2. **Líneas a registrar**: `importe_calculado` no nulo y ≠ 0 (positivo o negativo). Las demás no se
   mandan. Casar con el contrato **no** es requisito (F-053 R11).
3. **Vinculada** = `matched_contrato_line_id` con `sigrid_ide` y sin `derived_contrato_line_id`.
   Todo lo demás es **sin vincular** con `ALTA_SIGRID_PRODUCTO_POR_DEFECTO`.
4. **Precio neto y signo**: `precio = |importe| / |cantidad|`, `cantidad` con el signo del importe,
   de modo que `cantidad·precio = importe`. Signos incoherentes: **H8**.
5. **Con o sin partida**: `codigo_partida_final` no vacío ⇒ `partida`; vacío ⇒ sin `partida` (H5,
   v5.1). Nunca el literal `ALM`: sv6 deja `codigo_partida_final = NULL` en ese caso.
6. **Longitudes** antes de llamar (F-053 R10 + H6): obra, CIF, contrato y partida ≤24; número ≤128;
   `descripcion` recortada a 128 y `unidad` a 8; sin vincular sin descripción ⇒ motivo local.
7. **Nada de `lineas_recibidas`**, `paride`, `almide`, `cenide` ni analítica en la petición: los
   resuelve sigrid-api (F-009 fuera de alcance: «almacén/centro/analítica en la petición»).
8. Las decisiones de F-051 D3 (el botón «Almacén a todas» pisa también las líneas con partida), D5
   (el almacén elegido se pierde al revalorar) y D7 (re-alcance de F-007) no cambian este contrato:
   sv9 manda lo que esté aprobado en el momento del alta.

---

## 3. Respuesta

### 3.1. Éxito: HTTP 200

Misma forma en previa, grabación e idempotente: **superconjunto** de la respuesta clásica
(`AddPurchaseAlbaranResponse`, F-009 R7).

Cabecera:

| Campo | Tipo | Significado | Qué hace sv9 |
|---|---|---|---|
| `ok` | bool | `true` | — |
| `estado` | `previsto` \| `creado` \| `idempotente` | previa / escrito ahora / ya existía con esta referencia (no se ha escrito nada) | `previsto` ⇒ comparar (F-053 R17); `creado` ⇒ `registrado`; `idempotente` ⇒ `registrado` sin comparar (R15). **H18** |
| `committed`, `dry_run` | bool | `true/false` en `creado`; `false/true` en `previsto`; en `idempotente`, `false` y `not commit` (H18, v5) | — |
| `con_ide` | int | `con.ide` = `dca.ide`. **Provisional** en `previsto` (aviso `cod_provisional`) | Se guarda en `sigrid_con_ide` solo si `creado`/`idempotente` |
| `cod` | str | `AC<aa>/<n>`. Provisional en `previsto` | `sigrid_cod`; en simulación, «se habría creado como…» |
| `referencia_externa` | str | eco de la petición | — |
| `avisos` | `[{codigo, mensaje}]` | avisos de cabecera (§3.2) | por **código**, nunca por texto |
| `warnings` | `[str]` | los `mensaje` de los avisos, en orden (cada texto tiene su código; **H27**, v5) | se ignoran |
| `contrato` | obj | `ctride`, `obride`, `entide`, `almide`, `template_ide`… | informativo |
| `cabecera` | obj | fila `dca` resultante **sin** columnas bancarias (`ban*`, `cpa*`; **H16**, v5) | no se guarda entera |
| `totales` | obj | `totbas`, `totiva`, `totdoc`, `n_lineas`… | panel de sv4 |
| `estados_contrato` | obj | `estser`/`estfac` antes y después, sumas | panel |
| `movimientos` | `[obj]` | filas `mov` | — |
| `filas` | obj | `con`, `dca` (sin bancarias), `dcapro[]`, `ctrprodes[]`, `mov[]`, `log` completas | auditoría; **H16** |

Cada elemento de `lineas[]`:

| Campo | Significado |
|---|---|
| `indice` | posición en `lineas` de la petición, **desde 0** (H26, v5) |
| `referencia_linea` | eco: **la clave con la que sv9 casa** |
| `tipo` | `vinculada` \| `sin_vincular` |
| `ctrpro_ide`, `linoriide` | los del `ctrpro`; 0 en sin vincular |
| `proide`, `producto` | `ide` y código del producto |
| `res`, `unimed` | descripción y unidad escritas |
| `cantidad`, `precio`, `total`, `iva_cuota` | `can`, `pre`, `tot = round(can·pre, 2)`, `ivacuo = round(tot·iva, 2)` con `iva` de `dbo.iva` |
| `paride`, `partida` | `obrparpar.ide` y código; `0` y `null` sin partida |
| `almide`, `cenide` | almacén físico y centro de coste escritos |
| `stock_anterior`, `stock_resultante`, `pmp_anterior`, `pmp_resultante` | balance del `mov` (si lo hay) |
| `avisos` | `[{codigo, mensaje}]` de esa línea (**H27**) |

En `idempotente` las líneas son las **leídas** de Sigrid (`pos`, `proide`, `can`, `pre`, `tot`,
`paride`, `almide`) por orden de `pos`, con `indice` desde 0 y sin avisos; `referencia_linea` solo si
M18 deja escribirla en `dcapro.refent` (**H18**, F-009 R30b).

**Comparación de la previa en sv9** (F-053 R17): por `referencia_linea`, `|total − importe_calculado|
≤ ALTA_SIGRID_TOLERANCIA_EUR` (0,05) o `importe_distinto`; faltan o sobran líneas ⇒
`lineas_distintas`; `partida` distinta de la pedida (también nula frente a no nula) ⇒ `partida_distinta`; aviso con
código en `ALTA_SIGRID_AVISOS_BLOQUEANTES` ⇒ `aviso_bloqueante`. Cualquiera ⇒ `revisar`.

### 3.2. Avisos (no impiden el alta; viajan en `avisos[]` de cabecera o de línea)

| Código | Nivel | Cuándo (F-009) | F-053 |
|---|---|---|---|
| `cod_provisional` | cabecera | siempre en `previsto`: `cod`/`con_ide` son `MAX+1` sin reservar | informativo |
| `supera_pendiente` | línea | vinculada con `cantidad` > `can − canser` del `ctrpro` | informativo |
| `partida_distinta_del_contrato` | línea | vinculada con partida ≠ la del `ctrpro` (M4: 5,3 % en el escritorio) | informativo |
| `precio_distinto_del_contrato` | línea | vinculada con `precio` a más de 0,0001 de `ctrpro.pre` (escribe `tar` = `precio`, `dto ''`) | informativo. **H14** (tolerancia, v5) |
| `servido_negativo` | línea | devolución que deja `canser` < 0 (se admite; M6: 750 `ctrpro` así) | informativo |
| `stock_negativo` | línea | el `mov` deja `almcan` < 0 (se admite; M15) | informativo |
| `producto_sin_historico` | línea | producto sin `dcapro` previa en la empresa: cuenta/IVA a 0 | **bloqueante** (defecto de F-053) |
| `sin_partida_en_linea_con_partida` | línea | vinculada sin `partida` cuyo `ctrpro` tiene partida (`paride` ≠ 0; v5.1) | informativo (**H12**) |
| `iva_de_otro_proveedor` | línea | sin vincular sin `dcapro` previa del producto con ese proveedor: cuenta e IVA de la última de otro (v5) | informativo (N8, aprobada; **H15**) |
| ~~`plantilla_de_otro_proveedor`~~ | — | **ya no existe** desde F-009 v3: es el error `proveedor_sin_albaran_previo` | **H25** |

### 3.3. Errores: HTTP 400 con código

Forma: `{ "ok": false, "error": "<texto>", "details": { "type": "AlbaranCompraError", "codigo":
"<código>", "lineas": [ {indice, referencia_linea, codigo, mensaje} ] } }`. `lineas` solo con
`lineas_no_validas`, y entonces trae **todas** las líneas que fallan (F-009 R9). Los errores de
cabecera cortan antes de mirar las líneas.

| `details.codigo` | Nivel | Cuándo (F-009) | Estado en F-053 (design §2) | Propuesta (§5) |
|---|---|---|---|---|
| `peticion_mixta` | cab. | `lineas_recibidas` junto a `lineas`/`referencia_externa` | `error` | — |
| `escritura_albaranes_deshabilitada` | cab. | `commit:true` con cualquiera de las llaves cerrada o sin credenciales de escritura | `error` | — |
| `base_de_datos_no_permitida` | cab. | `commit:true` y `database` fuera de `ALLOWED_WRITE_DATABASES` (vacía no abre) | `error` | — |
| `demasiadas_lineas` | cab. | más de `SIGRID_ALBARAN_MAX_LINEAS` (también en previa) | `error` | `no_admitido` (H22) |
| `referencia_no_permitida` | cab. | `referencia_externa` sin prefijo admitido (también en previa) | `error` | — |
| `referencia_en_conflicto` | cab. | hay >1 albarán `tip 14` con ese `synckey`, o uno de otro proveedor u obra | `revisar` | H9 |
| `obra_no_encontrada` | cab. | ninguna `con tip 42` con ese código | `no_admitido` | — |
| `obra_de_empresa_no_permitida` | cab. | la obra solo existe en empresas fuera de `SIGRID_ALBARAN_EMPRESAS_OBRA`, o la lista está vacía (v5) | **no está en la tabla** | `error` (configuración u obra ajena; H2) |
| `obra_ambigua` | cab. | >1 obra con ese código entre las empresas admitidas (con `[1]` no puede darse: índice único `(emp, tip, cod)`) | `no_admitido` | H2 resuelto |
| `contrato_no_encontrado`, `contrato_ambiguo` | cab. | localizador `con.tip 44 + cod + obra + entcif` sin fila o con varias, o de otra obra | `no_admitido` | — |
| `usuario_no_valido` | cab. | `usu` no está en `dbo.usu` | **no está en la tabla** | `error` (H1, H25) |
| `proveedor_sin_albaran_previo` | cab. | el proveedor no tiene ningún albarán previo del que copiar la cabecera (sin *fallback*) | `no_admitido` (alta a mano) | — |
| `estado_inicial_no_encontrado` | cab. | `conest` sin `tip 14, est 1` | `error` | — |
| `almacen_de_obra_no_resuelto` | cab. | línea sin vincular (con o sin partida), sin contrato, sin `obr.almide` y con 0 o 2 `alm` en la obra | `error` | `no_admitido` (H13) |
| `colision_de_clave` | cab. | alta simultánea del escritorio; reintentos agotados; ERP intacto | `error` (reintentable) | — |
| `filas_afectadas_inesperadas` | cab. | las relecturas antes del COMMIT no cuadran; ROLLBACK | `error` | — |
| `lineas_no_validas` | cab. | una o más líneas fallan; detalle en `details.lineas` | según los códigos de línea | — |
| ↳ `linea_no_es_del_contrato` | línea | el `ctrpro` no es del contrato | `no_admitido` | — |
| ↳ `producto_no_permitido` | línea | producto fuera de `SIGRID_ALBARAN_PRODUCTOS_SIN_CONTRATO` | `error` | — |
| ↳ `producto_no_encontrado` | línea | producto inexistente o de baja en la empresa de la obra | `no_admitido` | `error` (H24) |
| ↳ `partida_no_encontrada` | línea | ninguna partida de la obra con ese código | `no_admitido` | — |
| ↳ `partida_no_imputable` | línea | existe pero no es `tip 1`, `tipdes 0`, `tipvis` 0/1 (no se exige hoja) | `no_admitido` | H4 (decidido) |
| ↳ `partida_ambigua` | línea | el código se repite entre las imputables de la obra (N2) | `no_admitido` | H17 (M3) |
| ↳ `precio_negativo` | línea | `precio` < 0: segunda barrera tras sv9 (v5) | **no está en la tabla** | `revisar` (H8) |
| ↳ `paride_no_valido` | línea | solo si R14b (M3): `paride` no es de la obra, no es imputable o no tiene ese código (v5) | **no está en la tabla** | `no_admitido` (H17) |

### 3.4. Otros fallos

| Respuesta | Cuándo | F-053 |
|---|---|---|
| 400 **sin** `codigo` (`error: "Solicitud invalida."`, `details.validation` de Pydantic) | campo ausente, sobrante, longitud, dominio, o las reglas de R6 (dos o ninguno de `ctrpro_ide`/`producto`, `cantidad == 0`, sin vincular sin `descripcion`, `referencia_linea` repetida, vinculada sin `cod_contrato`; también una clave `almacen`, que no existe) | `error` («fallo del servicio»). sv9 debe evitarlas validando antes (H6) |
| 400 con texto libre | errores de lectura (`truncado`) | `error` |
| 401/403 | clave de función | `error` |
| 500 | inesperado | previa: `error`; grabación: `incierto` |
| timeout (cliente 240 s; el balanceador corta a 230 s), conexión | — | previa: `error`; grabación: `incierto`. Tras `ALTA_SIGRID_ESPERA_INCIERTO_MIN` se reenvía la **misma** petición: la idempotencia devuelve `idempotente` si la transacción llegó a hacer COMMIT |

---

## 4. Reglas de validación de sigrid-api y lo que NO hace

### 4.1. Orden de validación (F-009 design §Flujo)

1. **Sin leer la base**: modo por claves (`peticion_mixta`); Pydantic (400 sin código); tope de
   líneas (`demasiadas_lineas`); prefijo (`referencia_no_permitida`). Con `commit:true`: llaves,
   credenciales y base (`escritura_albaranes_deshabilitada`, `base_de_datos_no_permitida`).
2. **Cabecera** (lecturas): obra por `(tip 42, cod)` en las
   empresas admitidas → contrato (localizador + esa obra) → plantilla de cabecera (último albarán **del
   mismo proveedor en la empresa de la obra**) → idempotencia por `synckey` (sale ya con `idempotente`)
   → `conest` y `usu`.
3. **Líneas**, todas, acumulando fallos: `ctrpro` del contrato; producto por `(emp, cod)` y lista
   blanca; partida entre las imputables de la obra (o `paride` 0 sin partida); precio no negativo;
   almacén físico de toda sin vincular.
4. Construcción y, si `commit`, transacción única bajo applocks (`SIGRID_REFEXT_14`,
   `SIGRID_SERIE_14`, `SIGRID_IDE_con`, `_dcapro`, `_ctrprodes`, `_mov`, `_log`) con la idempotencia
   **re-comprobada dentro**, `cod` e `ide` reservados con `UPDLOCK, HOLDLOCK`, reintento ante clave
   duplicada y relecturas antes del COMMIT.

### 4.2. Qué escribe (y nada más; F-009 R25, R31)

`INSERT` de `con` (`tip 14`, `cod AC<aa>/n`, `est 1 PDT`, `res`, `fec`), `dca` (`synckey`, `entref`,
`obride`, `ctride`, `almide`, `cenide`, `empide`, totales, descuentos a 0, `estser/estfac` 0),
`dcapro` ×N, `ctrprodes` ×M (vinculadas), `mov` ×K (productos que hacen movimientos; fechados en el
alta, N1) y la fila de alta de `log` (`usu`). Solo si hay vinculadas (H31), `UPDATE` relativo de
`ctrpro.canser` por vinculada y de `ctr.estser/estfac`. Sin `DELETE`, `MERGE` ni DDL; nunca `dcapropar` (salvo que M7 lo exija, H28).

### 4.3. Qué NO hace sigrid-api (lo decide albaranes o no se hace)

- **No elige partida**: resuelve el código pedido entre las imputables de la obra o rechaza. No
  completa abreviaturas, no busca parecidos, no reparte compuestas (eso es F-049 en sv2).
- **No hereda partida** de la plantilla, del `ctrpro` (salvo que se pida la misma) ni de otra `dcapro`:
  `paride` es la resuelta o 0 (F-009 R14): una línea sin partida queda en 0 aunque el `ctrpro` la tenga.
  Lo contrario de lo que hacía `albaran-directo`. **No reasigna** partidas después: pasar a partida
  una línea sin partida (al desacopiar) se hace en Sigrid.
- **No casa líneas** con el contrato: el `ctrpro_ide` lo trae sv9 (lo eligió IA3 en sv5 y lo aprobó
  el revisor). No convierte unidades: la cantidad de una vinculada llega ya en la unidad del contrato.
- **No calcula importes desde el contrato**: `tot = round(cantidad·precio, 2)` con el precio pedido;
  no aplica descuentos (por eso sv9 manda el neto).
- **No suma** líneas repetidas del mismo `ctrpro` (el modo clásico sí).
- **No elige producto por familia**: el código lo trae sv9 y debe estar en la lista blanca.
- **No recibe** almacén, centro, cuenta analítica ni IVA en la petición: los deriva. `paride`, solo si M3
  obliga a R14b (H17).
- **No adjunta el PDF** (es `concepto-grafico`, §7), no modifica ni anula albaranes (anular es desde
  la UI de Sigrid), no registra varios albaranes por petición, no recalcula `mov` posteriores.
- **No busca altas a mano** con otra referencia: eso lo hace sv9 por `sql/read` (F-053 R14).
- **No** valida la plausibilidad de la fecha (solo formato y rango: una futura **no** se rechaza, v5.1)
  y **solo** normaliza mayúsculas y espacios del CIF; fechas plausibles y formato del CIF son de
  albaranes (H19, H21).

---

## 5. Huecos y contradicciones

Formato: **qué falta o choca** · fuentes · **propuesta** · quién. Numeración estable: F-053, F-009,
F-049 y F-051 pueden citarlos por número. Los textos de cada hueco son los del 2026-10-05 (contra
F-009 v4); **su estado tras F-009 v5.1 es el de esta tabla** («R» y «design §» son de la spec de F-009).
Donde un texto cite el campo `almacen`, «en almacén» o `fecha_no_valida`, léase la v5.1: línea sin
`partida` y ninguna validación de fecha futura en sigrid-api.

| H | Estado tras F-009 v5.1 | Dónde |
|---|---|---|
| H1 | De albaranes (F-053 añade `usu`); F-009 sin cambio | — |
| H2 | **Resuelto** en F-009: `SIGRID_ALBARAN_EMPRESAS_OBRA` y `obra_de_empresa_no_permitida`; obras de baja admitidas (N6, aprobada) | R10, R11, design L1 |
| H3 | **Resuelto** en F-009: plantilla y `con.emp` de la empresa de la obra | R11, design L5 y §Filas |
| H4 | **Decidido** (humano): F-009 conserva «imputable» y no exige hoja; F-049 alinea su lista (de albaranes) | R14 |
| H5 | **Resuelto en la forma** (v5.1): sin partida = `partida` ausente o `null`, sin campo `almacen`; `paride` 0, nunca heredada; `almide`/`cenide` en toda línea. Queda de albaranes: F-053 no manda `partida` si `codigo_partida_final` está vacío y retira `linea_sin_partida`; F-051 revisa su visor | R6, R14, R15 |
| H6 | De albaranes (F-053) | — |
| H7 | De albaranes (F-053); F-009 ya toma `ctrpro.unimed`/`res` si no vienen | R12 |
| H8 | **Decidido**: signos en F-053; F-009 añade `precio_negativo` (antes `ge=0` de Pydantic, 400 sin código); descuentos, a mano | R17, design §Riesgos |
| H9 | **Pendiente de M17**: si el escritorio marca en vez de borrar, R30 excluye anulados; F-053 usa `ALB-{id}-{n}` | R30b, design §Condicionales |
| H10 | **Resuelto** almacén y centro de toda sin vincular; `caaide` **pendiente de M16** (hipótesis escrita) | R15, design §Analítica |
| H11 | **Resuelto** con lista de reseteo; confirmación con M14 ampliada | R13, design §Reseteo |
| H12 | **Resuelto**: aviso informativo `sin_partida_en_linea_con_partida` (v5.1; en la v5 se llamaba `almacen_en_linea_con_partida`) | R16 |
| H13 | **Resuelto** en F-009 (`obr.almide`/`cenide` antes que `alm`; confirmación M16); mapeo a `no_admitido`, de F-053 | R15, design L10 |
| H14 | **Resuelto** en F-009 (tolerancia 0,0001 y `pre` del contrato); redondeo a 6 decimales, de F-053 | R17 |
| H15 | **Resuelto** en F-009 (plantilla del mismo proveedor, aviso `iva_de_otro_proveedor`); confirmación M11 ampliada | R13, design L8b |
| H16 | **Resuelto** en F-009 (sin bancarias en la respuesta); guardar solo lo usado, de F-053 | R7, design §Respuesta |
| H17 | **Pendiente de M3**: con repetidos entre imputables, `paride` opcional | R14b |
| H18 | **Resuelto** `committed`/`dry_run`/`indice`; `referencia_linea` en `refent` **pendiente de M18**; comparar totales, de F-053 | R30, R30b |
| H19 | **De albaranes entero** (humano, v5.1): sigrid-api no rechaza fechas futuras (solo formato y rango); futuras y ventana de 365 días, en F-053 | R6 |
| H20 | **Decidido**: puerta dura, sin M9 cerrada no hay modo real; si MA9999 mueve stock, PARADA | R35, tasks T22 |
| H21 | **Resuelto** en F-009 (mayúsculas sin espacios); formato, de albaranes | R5 |
| H22-H25 | De albaranes (F-053, F-049); H25 debe sumar además los códigos nuevos de v5 (§3.3) | — |
| H26 | **Resuelto** en F-009 (`indice` desde 0); orden de líneas, de F-053 | R7 |
| H27 | **Resuelto**: avisos `{codigo, mensaje}` y `warnings` derivados de ellos | R7, design §Respuesta |
| H28 | **Decidido**: una repetición `--solo M3 M7 M9 M11 M13 M14 M16 M17 M18` | tasks T0b |
| H29, H30 | De albaranes; no tocan F-009 | — |
| H31 | F-009 **ya lo admite** (`cod_contrato` sin vinculadas; sin `UPDATE`); F-053 lo manda siempre que la valoración tenga contrato (N4, aprobada) | R6, R20 |
| H32 | **Resuelto**: docstring y `sigrid_api.md` §4, §7.5, §7.6, §8.6 | R36, tasks T13 y T18 |
| H33 | **Resuelto**: `Decimal` con `ROUND_HALF_UP` | R17, design §Importes |

### Bloqueantes

**H1. `usu` obligatorio en F-009 y ausente en F-053.** F-009 v3 (R5, «Forma final») hizo `usu`
obligatorio para la fila de alta de `log`; F-053 v5 (R12, design §2) se alineó con la v2 y no lo
manda. Con `extra="forbid"` y campo obligatorio, **todas** las altas darían 400 sin código ⇒ `error`.
**Propuesta**: F-053 R12 añade `usu` = `ALTA_SIGRID_USUARIO` (el mismo del adjunto, ya fijado en su
T0c contra `dbo.usu`, ≤24) y su tabla mapea `usuario_no_valido` → `error`. *F-053.*

**H2. Obra por código sin empresa.** F-009 L1 resuelve `con WHERE tip = 42 AND cod = ?` sin
`emp`; F-049 midió (2026-10-03) que el código de obra **se repite entre empresas** (la emp 28 tiene
40 iguales a la emp 1, p. ej. `0517`, `0581`) y albaranes solo trabaja con la **emp 1** (O1). Esas
obras darían `obra_ambigua` siempre. El localizador de contrato (`locate_contract`) tampoco filtra la
empresa de la obra. **Propuesta**: F-009 filtra `con.emp = 1` en L1 (configurable,
`SIGRID_ALBARAN_EMPRESAS_OBRA=[1]`, defecto cerrado coherente con R10) y exige que el contrato sea de
esa obra (ya lo hace). Opcional: descartar obras de baja (`fecbaj`). *F-009.*

**H3. Empresa del albarán heredada de la plantilla.** La cabecera `con` se clona del último albarán
del proveedor (L5, sin filtro de empresa) y design §Filas no sobrescribe `con.emp`; con él van
`dca.empcif`/`emptex` y la serie (`cod` se reserva «por `emp`», R26). Si el último albarán del
proveedor fuera de otra empresa (M2: 0,03 % de albaranes fuera de la emp 1), el albarán nacería en
otra empresa que su obra. **Propuesta**: L5 añade `AND c.emp = ?` (emp de la obra) y `con.emp` =
emp de la obra siempre; `proveedor_sin_albaran_previo` si no hay plantilla en esa empresa; test. *F-009.*

**H4. «Imputable» (F-009) ≠ «hoja» (F-049).** F-049 valida la partida contra las **hojas** de la
obra (nodos sin hijos, sin mirar `tip`/`tipdes`/`tipvis`; SQL con `ide, padide, cod, res`); F-009
acepta solo **imputables** (`tip 1`, `tipdes 0`, `tipvis` 0/1, sin mirar si tiene hijos). Una hoja
desactivada (`tipdes` 1) o de venta (`tipvis` 2) saldría «Leída · en lista» en sv4 y
`partida_no_imputable` en sigrid-api ⇒ `no_admitido` tras aprobar. **Propuesta**: F-049 añade
`tip, tipdes, tipvis` a `SQL_PARTIDAS_POR_OBRA` y saca de la lista lo no imputable (lo que se ofrece a
IA2 y al combo de sv4 = lo que sigrid-api admite). F-009 conserva su regla; decidir si exige además
hoja (propuesta: no; M3 dice que el escritorio solo imputa a `tip 1`). *F-049 (+ humano).*

**H5. Línea sin partida sin marca: F-053 la rechaza, el humano decidió que es almacén.** F-053 R10
pone `no_admitido` (`linea_sin_partida`) a la línea con partida vacía **sin** marca de F-051, y F-051
R12 la pinta «Sin partida» con aviso. Decisión D1 del 2026-10-05: «en el visor, una línea sin
partida ES almacén (aunque en realidad sea partida vacía: el negocio ya funciona así a mano)».
**Propuesta**: F-053 manda `almacen: true` para todo `codigo_partida_final` vacío y retira
`linea_sin_partida`; F-051 revisa R10-R12 (`sin_partida` deja de ser un estado distinto en el visor)
en su PARADA 1. sigrid-api no cambia. **v5.1**: no hay campo `almacen`; F-053 simplemente no manda
`partida`. *F-053, F-051.*

**H6. Longitudes y vacíos que hoy acaban en `error` en vez de `no_admitido`.** `codigo_partida_final`
es VARCHAR(64) y `partida` ≤24 (`obrparpar.cod` 24); `descripcion_linea` es TEXT y `descripcion`
≤128; una sin vincular sin descripción incumple R6. Las tres dan 400 **sin código** (Pydantic) ⇒
F-053 «fallo del servicio», cuando son datos del albarán. **Propuesta**: F-053 R10 añade `partida`
>24 a `campo_demasiado_largo`, recorta `descripcion` a 128 (como `unidad` a 8) y, sin descripción,
usa la de la línea leída o un motivo local `falta_descripcion` (`no_admitido`). *F-053.*

**H7. Unidad y descripción de las vinculadas.** F-053 manda `cantidad_convertida` (unidad del
contrato) pero `unidad` = la del albarán recortada: `dcapro.unimed` no casaría con `dcapro.can`
(p. ej. 25 «m3» que en el albarán eran «Tn»). Con `descripcion`, la línea perdería el texto del
contrato. **Propuesta**: en vinculadas sv9 **no manda** `unidad` ni `descripcion` (F-009 toma
`ctrpro.unimed`/`res`, como el escritorio); en sin vincular, `unidad_albaran` recortada. Mejora
posterior: normalizar unidades a los códigos de Sigrid. *F-053.*

**H8. Signo: descuentos convertidos en devoluciones.** F-053 pone a la cantidad el signo del
importe. Un descuento o abono de precio (cantidad > 0, importe < 0) viajaría como **devolución**: en
vinculada resta `canser` (medición servida) y en las dos genera un `mov` que baja stock. Y una línea
con cantidad < 0 e importe > 0 (lectura incoherente) entraría como recepción. **Propuesta**: F-053
solo manda negativas si cantidad **e** importe del albarán son negativos; signos opuestos ⇒
`revisar` (motivo `signo_incoherente`). Cómo dar de alta un descuento comercial (línea MA9999 sin
`mov`, descuento de cabecera…) lo decide el humano; F-009 hoy no tiene descuento de cabecera (lo pone
a 0). *F-053 + humano.*

**H9. Reintento después de anular.** F-053 R28 da el alta por `anulado` si `con.ide` ya no existe y
permite «Solicitar alta» otra vez con la **misma** `referencia_externa` (`ALB-{document_id}`). Si
anular en la UI de Sigrid **no borra** el `con` (lo marca), R30 lo encontraría ⇒ `idempotente` ⇒
`registrado` sobre un albarán anulado; y R14 de F-053 lo vería como «alta a mano». Nadie ha medido
cómo anula el escritorio. **Propuesta**: medirlo en T23 de F-009 (anulación del albarán de prueba).
Si borra, nada que hacer. Si marca, F-009 R30 excluye los anulados y F-053 usa `ALB-{document_id}-{n}`
tras cada `anulado` (sigue con prefijo `ALB-`) y excluye anulados en R14. *Humano (medición), F-009, F-053.*

### Importantes

**H10. Almacén, centro y cuenta analítica de las sin vincular y de las líneas en almacén.** R15
define `almide`/`cenide` solo para `almacen:true`; para una **sin vincular con partida** design los
lista como sobrescritos pero no dice de dónde salen. `caaide` (cuenta analítica) no se sobrescribe en
sin vincular: queda la de la plantilla (última `dcapro` de MA9999 en **cualquier obra**). En una
vinculada con partida distinta o en almacén, el `caaide` del `ctrpro` corresponde a **otra** partida.
El diccionario tiene `obrparpar.caaide` (cuenta analítica de la partida) y `alm.caaproide`.
**Propuesta**: R15 para toda sin vincular; medición M16 de solo lectura (qué `caaide` pone el
escritorio frente a `obrparpar.caaide` de su `paride` y frente a `alm.caaproide` en las de almacén) y
regla según el resultado. *F-009.*

**H11. Columnas arrastradas de la plantilla en las sin vincular.** El hallazgo 5 de
`progress/spec_F-009.md` (la plantilla «arrastra medición, analítica, desglose y `prepma` ajenos»)
solo se resolvió para `prepma`; M14 comparó **vinculadas**. Quedan `med`, `canmed`, `parcandes`,
`tex`, `texcom`, `anades`, `serdes`, `fecimp`, `refent`, `cod2`, `item`, `pac`, `anexo`, `taride`,
`fec`, `pla`. **Propuesta**: lista explícita de reseteo para sin vincular (a 0/`''`), con test que
compare con una `dcapro` del escritorio sin contrato (ampliar M14). *F-009.*

**H12. Vinculada en almacén: sin aviso definido.** F-009 la admite (R6, R15; consume `canser` como
cualquier vinculada, coherente con D4), pero R16 solo habla de «partida distinta». **Propuesta**:
aviso informativo `sin_partida_en_linea_con_partida` (v5.1) cuando el `ctrpro` tiene `paride` ≠ 0,
informativo en F-053; test de F-009 con vinculada sin `partida` (`paride` 0, `almide` del `ctrpro`,
`ctrprodes`, `canser += cantidad`). *F-009, F-053.*

**H13. Obras con dos almacenes.** L10 lee `alm WHERE obride = ?` (M8: dos almacenes en 5 obras) y
falla con `almacen_de_obra_no_resuelto`, que F-053 trata como `error` («no es del revisor»): repetir
nunca lo arregla. El diccionario tiene `obr.almide` («Almacén» de la ficha de obra). **Propuesta**:
F-009 usa primero `obr.almide` (y `obr.cenide`) y solo si falta `alm WHERE obride`; F-053 mapea el
código a `no_admitido` («obra con dos almacenes: alta a mano»). *F-009, F-053.*

**H14. Precio «distinto del contrato» por decimales.** sv9 manda `|importe|/|cantidad|` sin
redondear (100 € / 3 ud = 33,3333…) y R17 compara con `ctrpro.pre` sin tolerancia: saldría
`precio_distinto_del_contrato` casi siempre y se perderían `tar`/`dto` del contrato. **Propuesta**:
F-009 compara con tolerancia (|precio − `ctrpro.pre`| ≤ 0,0001, la de M4) y, si es igual, escribe el
`pre` del contrato; F-053 redondea `precio` a 6 decimales. *F-009, F-053.*

**H15. IVA de las sin vincular.** `ivaide` sale de la última `dcapro` de MA9999 en la empresa, de
**cualquier proveedor**. Un proveedor con inversión del sujeto pasivo (`dca.tipisp`) o con otro tipo
recibiría el IVA de otro. **Propuesta**: `ivaide` de la última `dcapro` **del mismo proveedor** (la
plantilla de cabecera) y, si no hay, la del producto, con aviso si difieren; medir con M11. *F-009.*

**H16. Datos bancarios en la respuesta y en albaranes.** `cabecera` y `filas.dca` devuelven la fila
`dca` completa, que lleva la cuenta del proveedor (`ban`, `bancue`, `bandig`, `cpacue1`, `cpacue2`,
`cpaswi`…), y sv9 guarda la respuesta entera en `albaran_altas_sigrid.respuesta_json` (PostgreSQL
compartido, `psql-albaranes-rs9k2`). **Propuesta**: F-009 omite esas columnas de la **respuesta** (se
escriben igual) y F-053 guarda solo lo que usa (estado, `con_ide`, `cod`, avisos, líneas, totales). *F-009, F-053.*

**H17. Partida ambigua sin salida.** N2: código repetido entre las imputables ⇒ `partida_ambigua`
y «el revisor lo corrige en sv4»; pero los dos códigos son **iguales**: desde sv4 solo puede elegir
otra partida o almacén. **Propuesta**: campo opcional `paride` en la línea, junto a `partida` (F-009
comprueba que es de la obra, imputable y con ese código) y que F-049 conserve el `ide` de cada hoja.
Si la repetición de M3 da 0 casos entre imputables, se deja como está. *F-009, F-049, humano.*

**H18. Idempotente sin casar líneas.** R30 devuelve las líneas **leídas** (sin `referencia_linea` ni
avisos) y no comprueba que la petición actual coincida con el albarán existente; F-053 pasa a
`registrado` sin comparar. Inofensivo mientras el documento esté bloqueado en sv4 (F-053 R25), pero
un reenvío tras un cambio no se detectaría. **Propuesta**: en `idempotente`, `lineas[].indice` por
orden de `pos` y `referencia_linea` si se guarda (p. ej. en `dcapro.refent`, 24 caracteres, si el
escritorio no lo usa: medirlo); fijar `committed` (propuesta: `false`); F-053 compara totales
también en `idempotente` y, si difieren, `revisar`. *F-009, F-053.*

**H19. Fechas no plausibles.** F-009 admite 19000101-29991231 y F-053 solo comprueba el formato.
Una fecha mal leída (2062, 2016) crearía el albarán en otra serie (`AC62/…`) y con fecha absurda.
**Propuesta**: F-053 motivo `fecha_no_plausible` (posterior a hoy o anterior a hoy − 365 días) ⇒
`revisar`; F-009 rechaza fechas futuras con un código nuevo `fecha_no_valida`. **v5.1** (humano):
«la conexión no debe rechazar fechas futuras per se; eso se hará desde la app» ⇒ sin
`fecha_no_valida`; todo H19 en F-053. *F-053.*

**H20. Servicios dados de alta como material.** Toda sin vincular va como MA9999 («suministro de
materiales», decisión de F-053), también portes, bombeo, alquiler o residuos, que D2 permite en
almacén. Si MA9999 hace movimientos (M9 pendiente: `pro.tipmov`), un porte sube el stock de material.
**Propuesta**: cerrar M9 antes del modo real; si MA9999 mueve stock, decidir antes de abrir
(producto por familia —SM9999/QA9999…, ya previsto como mejora— o excluir servicios). *Humano.*

**H21. Formato del CIF.** F-009 compara `dca.entcif` / `ctr.entcif` exacto; Sigrid lo guarda sin
prefijo de país (`sigrid_api.md` §9.4). Un `ES` delante, guiones o minúsculas darían
`proveedor_sin_albaran_previo` o `contrato_no_encontrado`. **Propuesta**: fijar aquí el formato
(mayúsculas, sin prefijo de país, sin espacios ni guiones); lo garantiza albaranes (F-052 / sv9) y
F-009 normaliza mayúsculas y espacios. *F-053, F-009.*

### Menores y a confirmar

**H22. Tope de 100 líneas.** El reparto de compuestas (F-049) aumenta el número de líneas; F-053
trata `demasiadas_lineas` como `error`, pero es dato del albarán. **Propuesta**: `no_admitido` («más
de 100 líneas: alta a mano») y medir el máximo real en la medición de F-053. *F-053.*

**H23. Partes de cantidad 0 tras repartir.** `repartir` trunca: 0,002 / 3 ⇒ 0,002 + 0,000 + 0,000.
Una parte con cantidad 0 e importe ≠ 0 da `cantidad_no_valida` (F-053) o 400 (F-009 R6). Raro.
**Propuesta**: F-049 no reparte si alguna parte queda a 0 en cantidad o importe (queda la lectura,
`validada=false`, revisión). *F-049.*

**H24. `producto_no_encontrado` es configuración.** Si MA9999 no existe o está de baja en la
empresa, el revisor no puede arreglarlo; F-053 lo manda a `no_admitido`. **Propuesta**: `error`,
como `producto_no_permitido`. *F-053.*

**H25. Tabla de F-053 desfasada respecto de F-009 v4.** `ALTA_SIGRID_AVISOS_BLOQUEANTES` por defecto
incluye `plantilla_de_otro_proveedor`, que ya no existe; falta `usuario_no_valido`; no dice qué hacer
con un código desconocido. **Propuesta**: defecto `["producto_sin_historico"]`; `usuario_no_valido`
→ `error`; código desconocido → `error`. *F-053.*

**H26. Orden de las líneas e `indice`.** F-053 dice «en su orden» sin fijarlo; F-009 no dice si
`indice` empieza en 0 o en 1. **Propuesta**: sv9 ordena por `line_index` de la línea leída y las
manuales al final por `id`; `indice` empieza en 0 (posición en `lineas`); sv9 casa siempre por
`referencia_linea`. *F-053, F-009.*

**H27. Forma de los avisos.** R7 no fija que los avisos de línea sean `{codigo, mensaje}` ni que cada
`warning` tenga su aviso con código. **Propuesta**: fijarlo en F-009 (test de R7); sv9 ignora
`warnings`. *F-009.*

**H28. Mediciones de T0 sin cerrar.** M7 (¿el escritorio escribe `dcapropar` al imputar a
partida?), M9 (qué productos generan `mov`), M11 (cuenta e IVA de MA9999 por empresa), M13 (`est` y
`ori` de la fila de `log`) y M14 (cabecera del mismo proveedor y `prepma`). No cambian la forma del
contrato, sí lo que se escribe. **Propuesta**: cerrarlas antes de F-009 `in_progress`, como ya dice
su tasks T0. *Humano.*

**H29. Vinculadas sin importe.** Una línea con cantidad y sin importe (material «solo llevar», o con
precio 0 en el contrato) no se manda: no consume medición ni entra en stock. Decidido («solo
líneas con importe»); **confirmar** que también se quiere para las vinculadas. *Humano.*

**H30. ALM impreso.** sv6 deja la línea sin match (derivada `alm_acopio`) y va como sin vincular
MA9999, aunque casara con el contrato; el almacén elegido en sv4 conserva la línea de contrato (D4).
**Confirmar** si el ALM impreso debe vincular (sería cambio de sv6, no de F-009). *Humano.*

**H31. Contrato no enlazado si no hay vinculadas.** F-053 manda `cod_contrato` nulo cuando ninguna
línea es vinculada aunque la valoración tenga contrato ⇒ `dca.ctride` 0. **Confirmar**. *Humano.*

**H32. Documentación vieja contradictoria.** `sigrid_api.md` §8.6 y el docstring de `sigrid_albaran`
en `function_app.py` dicen que el modo clásico «replica TODAS las líneas del contrato (el resto con
cantidad 0)»; el código solo incluye las indicadas. §7.5 dice que los albaranes calculan el `cod`
fuera de la transacción (el modo extendido lo hará dentro). **Propuesta**: corregirlo en T18 de
F-009 (§4, §7.5, §7.6, §8.6). *F-009.*

**H33. Redondeo.** `round` de Python redondea la mitad al par (2,675 → 2,67); el escritorio
probablemente redondea la mitad hacia arriba. En `tot` e `ivacuo` puede haber 0,01 € de diferencia
con lo aprobado (dentro de la tolerancia de F-053, pero el total de Sigrid no cuadraría al céntimo).
**Propuesta**: `importe_linea` con `Decimal` y `ROUND_HALF_UP`, y un caso en el test de R17. *F-009.*

---

## 6. Ejemplos

Valores ficticios salvo el contrato y la obra de las pruebas de junio (`CTSU16/0206`, obra `0404`).
CIF, `ctrpro_ide`, `document_id`, `ide` y usuario son inventados. Las peticiones ya llevan `usu`
(H1) y las vinculadas van sin `unidad` ni `descripcion` (H7).

### 6.a. Líneas vinculadas con partida (previa)

Petición:

```json
{
  "database": "ruesma",
  "cod_obra": "0404",
  "cif_proveedor": "B00000000",
  "cod_contrato": "CTSU16/0206",
  "referencia_externa": "ALB-3f2b9c1e-0000-4000-8000-000000000001",
  "su_referencia": "ALB-58213",
  "usu": "USU_ALTA",
  "fecha_albaran": 20261002,
  "empide": null,
  "commit": false,
  "lineas": [
    { "referencia_linea": "90101", "ctrpro_ide": 700101, "cantidad": 12.5, "precio": 68.4, "partida": "03.02.01" },
    { "referencia_linea": "90102", "ctrpro_ide": 700102, "cantidad": 1, "precio": 45.0, "partida": "03.02.01" }
  ]
}
```

Respuesta 200 (`cabecera`, `filas` y `movimientos` resumidos):

```json
{
  "ok": true, "database": "ruesma", "committed": false, "dry_run": true,
  "estado": "previsto",
  "referencia_externa": "ALB-3f2b9c1e-0000-4000-8000-000000000001",
  "con_ide": 9123457, "cod": "AC26/16001",
  "avisos": [ { "codigo": "cod_provisional", "mensaje": "DRY-RUN: no se ha escrito nada; cod e ide provisionales (MAX+1 sin reservar)." } ],
  "warnings": [ "DRY-RUN: no se ha escrito nada; cod e ide provisionales (MAX+1 sin reservar)." ],
  "contrato": { "ctride": 1035535, "obride": 404404, "entide": 555001, "almide": 3001, "template_ide": 9120001 },
  "cabecera": { "entcif": "B00000000", "entref": "ALB-58213", "synckey": "ALB-3f2b9c1e-0000-4000-8000-000000000001", "totbas": 900.0, "totiva": 189.0, "totdoc": 1089.0 },
  "totales": { "totbas": 900.0, "totiva": 189.0, "totdoc": 1089.0, "n_lineas": 2 },
  "estados_contrato": { "estser_before": 0, "estser_after": 0, "estfac_before": 0, "estfac_after": 0 },
  "lineas": [
    { "indice": 0, "referencia_linea": "90101", "tipo": "vinculada", "ctrpro_ide": 700101, "linoriide": 700101,
      "proide": 41001, "producto": "HM2516", "res": "HORMIGON HA-25/B/20/IIa", "unimed": "M3",
      "cantidad": 12.5, "precio": 68.4, "total": 855.0, "iva_cuota": 179.55,
      "paride": 880301, "partida": "03.02.01", "almide": 3001, "cenide": 2101,
      "stock_anterior": 40.0, "stock_resultante": 52.5, "pmp_anterior": 66.0, "pmp_resultante": 66.57142857142857,
      "avisos": [] },
    { "indice": 1, "referencia_linea": "90102", "tipo": "vinculada", "ctrpro_ide": 700102, "linoriide": 700102,
      "proide": 41002, "producto": "BOMB01", "res": "BOMBEO", "unimed": "UD",
      "cantidad": 1.0, "precio": 45.0, "total": 45.0, "iva_cuota": 9.45,
      "paride": 880301, "partida": "03.02.01", "almide": 3001, "cenide": 2101,
      "stock_anterior": null, "stock_resultante": null, "pmp_anterior": null, "pmp_resultante": null,
      "avisos": [] }
  ],
  "movimientos": [ { "proide": 41001, "canent": 12.5, "almcan": 52.5, "almpma": 66.57142857142857 } ],
  "filas": { "con": {}, "dca": {}, "dcapro": [{}, {}], "ctrprodes": [{}, {}], "mov": [{}], "log": {} }
}
```

sv9: totales por `referencia_linea` = importes aprobados (855,00 y 45,00) ⇒ sin motivos ⇒
`simulado` (simulación) o grabación con `commit: true` (real). La segunda línea no tiene `mov`
porque, en el ejemplo, el producto no hace movimientos (M9).

### 6.b. Mezcla: vinculada con partida, vinculada sin partida, sin vincular con partida y sin vincular sin partida (grabación)

Petición (la previa fue idéntica con `commit: false`):

```json
{
  "database": "ruesma", "cod_obra": "0404", "cif_proveedor": "B00000000", "cod_contrato": "CTSU16/0206",
  "referencia_externa": "ALB-3f2b9c1e-0000-4000-8000-000000000002", "su_referencia": "ALB-58260",
  "usu": "USU_ALTA", "fecha_albaran": 20261003, "empide": null, "commit": true,
  "lineas": [
    { "referencia_linea": "90201", "ctrpro_ide": 700101, "cantidad": 6, "precio": 68.4, "partida": "03.02.01" },
    { "referencia_linea": "90202", "ctrpro_ide": 700101, "cantidad": 2, "precio": 68.4 },
    { "referencia_linea": "90203", "producto": "MA9999", "descripcion": "SACO CEMENTO CEM II 25 KG",
      "unidad": "UD", "cantidad": 10, "precio": 4.4, "partida": "03.04.02" },
    { "referencia_linea": "90204", "producto": "MA9999", "descripcion": "PORTES",
      "unidad": "UD", "cantidad": 1, "precio": 30.0 }
  ]
}
```

Respuesta 200 (solo lo que cambia frente a 6.a):

```json
{
  "ok": true, "committed": true, "dry_run": false, "estado": "creado",
  "referencia_externa": "ALB-3f2b9c1e-0000-4000-8000-000000000002",
  "con_ide": 9123461, "cod": "AC26/16004",
  "avisos": [],
  "totales": { "totbas": 621.2, "totiva": 130.45, "totdoc": 751.65, "n_lineas": 4 },
  "lineas": [
    { "indice": 0, "referencia_linea": "90201", "tipo": "vinculada", "ctrpro_ide": 700101, "cantidad": 6.0, "precio": 68.4, "total": 410.4,
      "paride": 880301, "partida": "03.02.01", "almide": 3001, "avisos": [] },
    { "indice": 1, "referencia_linea": "90202", "tipo": "vinculada", "ctrpro_ide": 700101, "cantidad": 2.0, "precio": 68.4, "total": 136.8,
      "paride": 0, "partida": null, "almide": 3001,
      "avisos": [ { "codigo": "sin_partida_en_linea_con_partida", "mensaje": "La línea de contrato tiene partida 03.02.01; se registra sin partida." } ] },
    { "indice": 2, "referencia_linea": "90203", "tipo": "sin_vincular", "ctrpro_ide": 0, "linoriide": 0, "producto": "MA9999",
      "cantidad": 10.0, "precio": 4.4, "total": 44.0, "paride": 880412, "partida": "03.04.02", "almide": 3001, "avisos": [] },
    { "indice": 3, "referencia_linea": "90204", "tipo": "sin_vincular", "ctrpro_ide": 0, "linoriide": 0, "producto": "MA9999",
      "cantidad": 1.0, "precio": 30.0, "total": 30.0, "paride": 0, "partida": null, "almide": 3001, "avisos": [] }
  ]
}
```

Las dos primeras líneas apuntan al mismo `ctrpro` y producen dos `dcapro`, dos `ctrprodes` y
`canser += 6` y `+= 2` por separado; la segunda va sin partida (`paride` 0) aunque el `ctrpro` la
tenga. El aviso `sin_partida_en_linea_con_partida` lo define F-009 v5.1 (R16, H12). sv9: `creado` ⇒ `registrado` con `con_ide` 9123461 y `cod`
`AC26/16004`; después, el adjunto.

### 6.c. Devolución (vinculada y sin vincular), grabación

Petición:

```json
{
  "database": "ruesma", "cod_obra": "0404", "cif_proveedor": "B00000000", "cod_contrato": "CTSU16/0206",
  "referencia_externa": "ALB-3f2b9c1e-0000-4000-8000-000000000003", "su_referencia": "DEV-1207",
  "usu": "USU_ALTA", "fecha_albaran": 20261004, "empide": null, "commit": true,
  "lineas": [
    { "referencia_linea": "90301", "ctrpro_ide": 700103, "cantidad": -3, "precio": 12.1, "partida": "03.02.01" },
    { "referencia_linea": "90302", "producto": "MA9999", "descripcion": "DEVOLUCION PALETS",
      "unidad": "UD", "cantidad": -2, "precio": 9.0 }
  ]
}
```

Respuesta 200 (extracto):

```json
{
  "ok": true, "committed": true, "estado": "creado", "con_ide": 9123470, "cod": "AC26/16010",
  "totales": { "totbas": -54.3, "totiva": -11.4, "totdoc": -65.7, "n_lineas": 2 },
  "estados_contrato": { "estser_before": 1, "estser_after": 0, "sum_can": 400.0, "sum_canser_before": 400.0, "sum_canser_after": 397.0 },
  "lineas": [
    { "indice": 0, "referencia_linea": "90301", "tipo": "vinculada", "cantidad": -3.0, "precio": 12.1, "total": -36.3, "iva_cuota": -7.62,
      "partida": "03.02.01",
      "stock_anterior": 2.0, "stock_resultante": -1.0, "pmp_anterior": 12.0, "pmp_resultante": 12.3,
      "avisos": [ { "codigo": "servido_negativo", "mensaje": "canser de la línea 700103 queda en -1." },
                  { "codigo": "stock_negativo", "mensaje": "El stock del producto en el almacén queda en -1." } ] },
    { "indice": 1, "referencia_linea": "90302", "tipo": "sin_vincular", "cantidad": -2.0, "precio": 9.0, "total": -18.0, "iva_cuota": -3.78,
      "partida": null, "avisos": [] }
  ]
}
```

Regla A: el `mov` es de **entrada** con `canent` = −3, `cansal` 0 y PMP
`(2·12 + (−3)·12,1)/(2 − 3) = 12,3` sin redondear (F-009 R19); si `stock + can` = 0, el PMP se
conserva. `servido_negativo` y `stock_negativo` son informativos en F-053. Una línea de
descuento (cantidad > 0, importe < 0) **no** debe llegar aquí como devolución (H8).

### 6.d. Reintento idempotente

sv9 reenvía la petición de 6.b (por ejemplo, tras un `incierto` por tiempo agotado, pasada la
Espera), aquí con `commit: true` (con `false`, `dry_run` sería `true`). Respuesta 200:

```json
{
  "ok": true, "database": "ruesma", "committed": false, "dry_run": false,
  "estado": "idempotente",
  "referencia_externa": "ALB-3f2b9c1e-0000-4000-8000-000000000002",
  "con_ide": 9123461, "cod": "AC26/16004",
  "avisos": [],
  "totales": { "totbas": 621.2, "totdoc": 751.65 },
  "lineas": [
    { "indice": 0, "pos": 64,  "proide": 41001, "cantidad": 6.0, "precio": 68.4, "total": 410.4, "paride": 880301, "almide": 3001 },
    { "indice": 1, "pos": 128, "proide": 41001, "cantidad": 2.0, "precio": 68.4, "total": 136.8, "paride": 0, "almide": 3001 },
    { "indice": 2, "pos": 192, "proide": 99990, "cantidad": 10.0, "precio": 4.4, "total": 44.0, "paride": 880412, "almide": 3001 },
    { "indice": 3, "pos": 256, "proide": 99990, "cantidad": 1.0, "precio": 30.0, "total": 30.0, "paride": 0, "almide": 3001 }
  ]
}
```

No escribe nada (ni en previa ni en grabación). `committed` `false` y `dry_run` = `not commit`
(F-009 v5 R30, H18). sv9 ⇒ `registrado` con ese `con_ide`/`cod`. Las líneas leídas van por `pos` con
`indice` desde 0 y traen `referencia_linea` solo si M18 lo permite (R30b). Si el `synckey` existiera
con otro proveedor u obra, o dos veces ⇒ 400 `referencia_en_conflicto` ⇒ `revisar`.

### 6.e. Error por línea

Petición (previa) con un `ctrpro` de otro contrato, una partida inexistente y un producto fuera de
la lista blanca:

```json
{
  "database": "ruesma", "cod_obra": "0404", "cif_proveedor": "B00000000", "cod_contrato": "CTSU16/0206",
  "referencia_externa": "ALB-3f2b9c1e-0000-4000-8000-000000000005", "su_referencia": "ALB-58400",
  "usu": "USU_ALTA", "fecha_albaran": 20261005, "empide": null, "commit": false,
  "lineas": [
    { "referencia_linea": "90501", "ctrpro_ide": 799999, "cantidad": 4, "precio": 20.0, "partida": "03.02.01" },
    { "referencia_linea": "90502", "producto": "MA9999", "descripcion": "TUBO PVC 110", "unidad": "ML",
      "cantidad": 30, "precio": 3.1, "partida": "99.99.99" },
    { "referencia_linea": "90503", "producto": "MA3413", "descripcion": "ARENA", "unidad": "TN",
      "cantidad": 5, "precio": 14.0 },
    { "referencia_linea": "90504", "producto": "MA9999", "descripcion": "GUANTES", "unidad": "UD",
      "cantidad": 12, "precio": 1.5 }
  ]
}
```

Respuesta **400**:

```json
{
  "ok": false,
  "error": "Hay líneas que no se pueden dar de alta.",
  "details": {
    "type": "AlbaranCompraError",
    "codigo": "lineas_no_validas",
    "lineas": [
      { "indice": 0, "referencia_linea": "90501", "codigo": "linea_no_es_del_contrato", "mensaje": "La línea 799999 no pertenece al contrato CTSU16/0206." },
      { "indice": 1, "referencia_linea": "90502", "codigo": "partida_no_encontrada", "mensaje": "La obra 0404 no tiene la partida 99.99.99." },
      { "indice": 2, "referencia_linea": "90503", "codigo": "producto_no_permitido", "mensaje": "El producto MA3413 no está admitido en líneas sin contrato." }
    ]
  }
}
```

La línea 90504 es válida y no aparece. sv9: con `producto_no_permitido` entre los códigos ⇒ `error`
(configuración); sin él ⇒ `no_admitido`, con cada línea y su mensaje en el panel de sv4 para
corregir y «Solicitar alta en Sigrid». (sv9 nunca manda un producto distinto de
`ALTA_SIGRID_PRODUCTO_POR_DEFECTO`: la tercera línea es solo para ilustrar el código.)

---

## 7. Otras llamadas de sv9 a sigrid-api (fuera de este endpoint, para completar el cuadro)

| Llamada | Para qué (F-053) | Forma |
|---|---|---|
| `POST /api/sql/read` | R14: ¿alta a mano del mismo albarán? | `SELECT c.ide, c.cod, c.fec FROM dbo.con c JOIN dbo.dca d ON d.ide = c.ide WHERE c.tip = 14 AND d.entcif = ? AND d.entref = ? AND ISNULL(d.synckey, '') <> ?` (`[cif, numero, "ALB-{document_id}"]`); comprobar `truncated`. H9 si anular no borra |
| `POST /api/sql/read` | R28: ¿se anuló en Sigrid? | `SELECT ide FROM dbo.con WHERE ide = ? AND tip = 14` |
| `POST /api/sigrid/concepto-grafico` | R22: adjuntar el PDF al albarán registrado | `contip` 14, `gratipide` 0, `usu` = `ALTA_SIGRID_USUARIO`, `sha256`. En `dev`, `SIGRID_DOCUMENT_ALLOWED_CONTIP` ya incluye 14 y `_GRATIPIDE` incluye 0 (`sigrid_api.md` §4.1) |

sv9 no llama a `sql/write`, ni a `sigrid/albaran` en modo clásico, ni a `albaran-directo`
(F-053 R33). Cuando F-053 esté en real, el modo clásico y `albaran-directo` quedan obsoletos
(F-009 T18).
