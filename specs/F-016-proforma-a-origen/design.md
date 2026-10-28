<!-- specs/F-016-proforma-a-origen/design.md -->
# F-016 · Diseño (v2: cambio de alcance del humano, 2026-10-28)

Medición: [`explore_F-016.md`](../../progress/explore_F-016.md) (M41-M44) sobre lo ya medido en
[`explore_F-007.md`](../../progress/explore_F-007.md) (M11, M16-M26, M37). Base: F-007 tal como quedó cerrada (spec
v3.1, [`contrato_proformas.md`](../F-007-registrar-proforma/contrato_proformas.md) v1.1). Llamante: `proformas` (su F-005,
el «portal» en palabras del humano). La v1 de esta spec elegía la anterior y casaba las líneas en la API; la v2 lo deja
en el llamante.

## La decisión de fondo

En Sigrid conviven las dos formas: la proforma **de mes** (lo que hace F-007: solo el MES, sin cadena) y la **a origen**
(«check» de documento origen, `dca.docoritip 1`): cuelga de la anterior del contrato (`docoriide`), copia todas sus
líneas (las sin MES a `can` 0) y lleva por línea la cantidad a origen (`canoriori`) y la línea anterior (`canorilin`).
El humano decidió (2026-10-28) que se registre como indique el jefe de obra, **por meses por defecto**, y que la API
sea **solo el registro**: «marcar si es a origen, importes a buscar en Sigrid, etc., deberá hacerlo el portal».

Así que F-016 añade el modo a origen **sin cambiar el de mes**, y en él la API **registra lo que le mandan y valida su
integridad**: que la anterior existe, es del contrato, es a origen y es la punta; que cada `linea_anterior` es de esa
anterior y del mismo tipo; y lo escribe como lo deja Sigrid, arrastrando lo que nadie continúa. No elige, no busca
importes y no deduce.

**Límite de microservicio: cabe, y más estrecho que en la v1.** Validar y escribir es de la pasarela. Elegir el modo,
la anterior y las continuaciones, leer las puntas y enseñárselas a la persona es de `proformas` (§Contrato v1.2).

**Tamaño: una feature.** No toca el núcleo de F-009 (D11). Si el humano pide paridad completa de las arrastradas (D6),
hay que tocar el núcleo y conviene partirla.

## Ficheros a crear

| Fichero | Capa | Qué contiene |
|---|---|---|
| `domain/models/proforma_origen_models.py` | domain | Códigos ampliados (§Códigos); `ProformaOrigenError(ProformaError)`, `FalloLineaProformaOrigen(FalloLineaProforma)`, `AvisoProformaOrigen(AvisoProforma)`; `CadenaProforma`; `LineaProformaOrigenResultado(LineaProformaResultado)` y `ProformaOrigenResponse(ProformaResponse)` (R19, R20) |
| `application/use_cases/proforma_origen_statements.py` | application | LP7-LP9 (§SQL), `ProformaOrigenStatements` autovalidado con `DatabaseReferenceGuard`, y puras (§Funciones). Sin E/S |
| `tests/test_f016_*.py`, `tests/fixtures/f016_*.json` | — | `tasks.md`; una cadena sintética con la forma de M44 (primera, encadenadas, dos puntas, una de mes en medio) |

## Ficheros a modificar

| Fichero | Qué cambia |
|---|---|
| `domain/models/proforma_models.py` | Solo `ProformaRequest` (`modo`, `proforma_anterior`, `primera_de_cadena` y las reglas de R3) y `LineaProformaIn` (`linea_anterior`). Ni códigos ni respuestas |
| `application/use_cases/create_proforma_use_case.py` | Ramas de `modo` (§Flujo); `_Contexto` con la cadena; `_construir`, `_comprobar_dentro` y `_convertir` con lo de origen; traza R21. En mes, cada rama es inerte |
| `config/settings.py`, `local.settings.sample.json` | `SIGRID_PROFORMA_ORIGEN_ENABLED` (R4) |
| `function_app.py` | En `sigrid_proforma`, la llave de R4 tras la de F-007. `_respuesta_albaran_compra_error` no cambia |
| `specs/F-007-registrar-proforma/contrato_proformas.md` | v1.2 (§Contrato v1.2); es el contrato vivo con `proformas` y no se duplica |
| `docs/ARCHITECTURE.md`, `CLAUDE.md`, `azure-apps/sigrid_api.md` | R25 (`azure-apps`, commit aparte) |

## Ficheros que NO se tocan

El núcleo de F-009/F-015 (`create_albaran_compra_use_case.py`, `albaran_compra_statements.py`,
`albaran_compra_models.py`) y sus tests y dorados; `proforma_statements.py` (LP1-LP6 y sus funciones se reutilizan
tal cual); los tests de F-007; `infrastructure/` entero; el clásico, `albaran-directo` y el resto de rutas; `infra/`.
Sin ficheros `NN_nombre.sql`: SQL constante.

## Flujo (en `CreateProformaUseCase._proforma`)

1-4. Como F-007 (guardas, fecha, obra, referencia, contrato, etapa 1 de líneas). La llave de R4 va en la ruta.
5. Con contrato, `comprobar_hoja`, LP1, LP2, `origen` y avisos como F-007 (R15; sin `contrato_a_origen` a origen, R16).
   **Mes**: `buscar_del_mes`. **Origen**: `buscar_del_mes_origen` (R5; `existente` sale aquí, como en F-007); con
   `proforma_anterior`, LP7 → `validar_anterior` (R6), LP8 → sucesoras (R7) y LP9 de la anterior → `validar_continuadas`
   (R9; sus fallos, junto a los de la etapa 1 en un `lineas_no_validas`), `avisos_de_nuevas` (R10) y tope R14. Lo
   validado viaja en `_Contexto.cadena` (`CadenaValidada`: la anterior o `None`, sus filas y las continuaciones).
6. Traducción y núcleo como F-007. Con `cadena`, `_construir` llama a `super()` y después `superponer_cadena` (R11,
   R13) y `filas_arrastradas` (R12): las arrastradas se añaden **al final** de `filas.dcapro`, así que `numerar`, la previa,
   el `INSERT` y la relectura E12 las cuentan sin cambiar el núcleo; no son `_Linea` y no generan `ctrprodes`, `mov` ni
   `UPDATE`. `_comprobar_dentro` hace lo de F-007 (con R5) y, con anterior, LP8 por el cursor (R17).
7. `_convertir`: en mes, la de F-007; a origen, `ProformaOrigenResponse` con `cadena` y las arrastradas leídas de
   `filas.dcapro` a partir del índice `len(request.lineas)` (R19).

## Funciones puras (`proforma_origen_statements.py`)

- `validar_anterior(filas_lp7, *, cod, fecha) -> DocumentoCadena` (R6) y `comprobar_sucesoras(filas_lp8)` (R7, R17).
- `validar_continuadas(lineas, identificadas, filas_anterior) -> (dict[indice, fila], list[FalloLineaProformaOrigen])`
  (R9) y `avisos_de_nuevas(lineas, identificadas, filas_anterior, continuadas)` (R10).
- `superponer_cadena(dcapro, continuadas) -> list[dict]` (R11) y `filas_arrastradas(filas_anterior, usadas,
  primera_pos)` (R12). `cabecera_a_origen(dca, anterior)` (R13).
- `buscar_del_mes_origen(proformas, *, periodo, importe_mes, otra_del_mes)` (R5) e `importe_de_cadena(filas)`
  (Σ round(`canoriori`·`pre`, 2) en `Decimal`, el de `redondear_euros`; solo para la respuesta, R19).

## SQL nuevo (`proforma_origen_statements`; todo con `?`, de lectura y por contrato o documento)

- **LP7** (R6): `SELECT c.ide, c.cod, c.fec, d.docoritip FROM dbo.dca d JOIN dbo.con c ON c.ide = d.ide WHERE c.tip = ?
  AND d.ctride = ? AND c.cod = ?` con `[14, ctride, proforma_anterior]`.
- **LP8** (R7, R17): `SELECT c.ide, c.cod FROM dbo.dca d JOIN dbo.con c ON c.ide = d.ide WHERE c.tip = ? AND d.ctride
  = ? AND d.docoriide = ?` con `[14, ctride, ide_anterior]`. Por contrato, como LP1 y la LP7 medida en M44 (≤ 4,1 s).
- **LP9** (R9-R12, R19): `SELECT * FROM dbo.dcapro WHERE docide = ? ORDER BY pos, ide` con `[ide_anterior]`. Fila
  completa: es la plantilla de la arrastrada (como `SELECT *` de L8). Lectura por `docide`, la de LP6.

LP1-LP6 no cambian. Una sucesora en otro contrato no se busca (M19: 9 casos; `dca.docoriide` sin índice conocido
obligaría a recorrer `dca`): riesgo residual anotado.

## Contrato v1.2 con `proformas` (compatible hacia atrás)

- **Petición**: `modo`, `proforma_anterior` o `primera_de_cadena` (uno de los dos, obligatorio a origen) y por línea
  `linea_anterior` (R3). Sin ellos, v1.1 tal cual. Importes y cantidades, opcionales como en v1.1.
- **Respuesta a origen**: `cadena` y los cuatro campos de línea (R19); las arrastradas al final con `arrastrada: true`,
  `referencia_linea` la de su fila e `indice` ≥ nº de líneas pedidas. En mes, la respuesta de v1.1 sin claves nuevas.
- **Códigos**: los de §Códigos, con qué hace `proformas` (§4 del contrato).
- **Lo que lee el llamante de Sigrid** (por `sql/read`, con `?`, comprobando `truncated`; consultas orientativas que
  el contrato escribe enteras, y que el llamante adapta):
  1. **Puntas a origen del contrato**: `tip 14`, `dca.ctride` = el contrato, `docoritip 1`, de cualquier serie (`PROF` o
     `AC`, M19), que no son `docoriide` de otro `tip 14` del contrato; con su `cod`, `fec`, `totbas` y su importe de
     cadena (subconsulta Σ `ROUND(canoriori · pre, 2)` por `docide`, la de M44). Sugerencia medida (M25: 96,4 % única y
     correcta): la punta cuyo importe de cadena = ANTERIOR de la hoja (± 0,05; ANTERIOR = ORIGEN − MES si la hoja solo
     trae esos); ninguna o varias, que elija la persona; ANTERIOR 0, `primera_de_cadena`.
  2. **Líneas de la punta elegida**: `dcapro` por `docide` con `ide`, `linoriide`, `docoritip`, código de partida
     (`obrparpar.cod` del `paride`), producto, `res`, `pre`, `can` y `canoriori`, por `pos`. Cada línea de la hoja que
     continúa una de ellas manda su `ide` en `linea_anterior` (por `ctrpro`, y entre varias o sin vincular por partida,
     precio y descripción; la persona desempata). Las que no se continúen las arrastra la API a 0.
- **§6 Lo que lee `facturas`**: una proforma a origen trae líneas con `can` 0 (arrastradas) y su `entref` es el mismo
  `PROF<MMAA>_<obra>`; `totbas` sigue siendo el MES (M28). Solo pasan a factura las de `can` ≠ 0 (M15).

## Códigos

- **Cabecera nuevos**: `escritura_proformas_origen_deshabilitada`, `anterior_no_valida`, `anterior_con_sucesora`.
  Heredados: todos los de F-007.
- **Línea nuevo**: `linea_anterior_no_valida`.
- **Aviso nuevo**: `linea_nueva_ya_en_la_anterior` (R10, D3). Se reutiliza `otra_del_mes` con el sentido de R5.

## Decisiones (para el humano; recomendación en negrita)

- **D1 · Modo por petición, de mes por defecto** *(decidido, 2026-10-28)*. **`modo: "origen"`** en cada petición; sin
  él, F-007 exacta (R1). Lo indica el jefe de obra **al cargar cada proforma** en `proformas`, por hoja y no por
  contrato (humano, respuesta a P4); la API no lo deduce.
- **D2 · La anterior la manda el llamante; la API valida** *(decidido, 2026-10-28: alcance)*. Obligatorio
  `proforma_anterior` o `primera_de_cadena` (R3). La API comprueba lo que hace íntegro el registro: que exista en el
  contrato, sea a origen y no sea posterior (R6), y que sea la **punta** (R7, R17), porque la cadena es lineal (M19:
  ningún documento con dos sucesoras) y una segunda sucesora la ramificaría. No elige por importe: la regla de M25
  pasa al llamante como sugerencia (§Contrato v1.2). El humano: mandarán al menos ORIGEN y MES (respuesta a P5), y la
  anterior siempre estará en Sigrid. Las cadenas paralelas (M18), la serie mezclada (M19) y dos certificaciones del
  mismo mes (la segunda cuelga de la primera, que es la punta) las resuelve el llamante con la lista de puntas.
- **D3 · Las continuaciones las manda el llamante con `linea_anterior`; sin ella, la línea es nueva**. La API no casa
  ni siquiera por `ctrpro` único: sería una segunda regla, implícita, que deja de valer en cuanto hay dos líneas del
  mismo `ctrpro` (M20: 2 % de pares) y que el llamante ya aplica al elegir. A cambio, **un aviso de integridad**:
  una línea de contrato nueva cuyo `ctrpro` ya está en la anterior (R10) parte su origen en dos líneas (la nueva
  empieza en su MES y la vieja se arrastra a 0), que casi siempre es un olvido; no es error porque Sigrid lo admite.
  Se lee de LP9, que hace falta igual: no es buscar en Sigrid. Alternativa: casar por `ctrpro` único (comodidad, D3 v1).
- **D4 · Qué líneas lleva.** **Todas las de la anterior** (M23: 746 de 775 arrastran todas) **más las nuevas de la
  petición**; la primera, **solo las de la petición** (M42: 151 «solo las del mes» frente a 96 «todas las del
  contrato»). El arrastre es mecánica del registro: lo hace la API.
- **D5 · Columnas a origen como Sigrid** (M41, M11, M23): `canoriori` acumulado por línea y `= can` en la primera y en
  las nuevas; `canorilin` a la línea anterior; `canoriant`/`imporiant` 0; `imporiori` del `ctrpro` o de la anterior.
- **D6 · Arrastradas: solo `dcapro`** *(aprobado por el humano, 2026-10-28)*. Sigrid escribe además una `ctrprodes` a 0 por vinculada (M6) y un `mov` a 0 si
  `tipmov` 1 (M6: 96,8 %). No cambian servido, stock ni PMP, y escribirlas obliga a reservar `ide` y balances para
  líneas que no son del núcleo (costura nueva en F-009, en producción). **Solo `dcapro`, y V9 en la UI** (ficha,
  impresión, factura y anulación). Alternativa: paridad completa (tocar el núcleo; partir la feature). Pregunta P1.
- **D7 · Cambio de modo: lo decide el llamante** *(decidido, 2026-10-28: alcance; antes P2)*. M43: 64 contratos
  mezclan modos; de mes a origen, 22 de 29 retoman la cadena vieja y 5 empiezan otra. El llamante elige
  `proforma_anterior` (retomar) o `primera_de_cadena`; de origen a mes, F-007 tal cual (aviso `contrato_a_origen`). La
  API **no siembra** el origen: Sigrid tampoco (M41, `canoriori` = `can` en la primera en el 99,9 %).
- **D8 · Ya registrada a origen** (R5): `idempotente` y `existente` como F-007. Una a origen del mes con otro total
  es otra cadena o la certificación anterior del mismo mes: aviso, no error. Si es la sucesora de la anterior pedida,
  sale `anterior_con_sucesora` (R7).
- **D9 · Sin avisos nuevos de comparación con Sigrid** (alcance). Se quedan, sin cambios, los de F-007 que valen en
  los dos modos: cuadre de la hoja (R19, error), `origen` y `anterior_distinto_de_sigrid` frente a lo registrado del
  contrato (R20) y `supera_contrato*` (R21). Comparar la hoja con la cadena es del llamante, que la lee. Se calla
  `contrato_a_origen` a origen (R16) porque su texto sería falso. La respuesta da `importe_anterior_cadena` e
  `importe_origen_cadena` de las filas ya leídas y escritas, sin otra lectura, para que el llamante coteje.
- **D10 · Llave propia del modo**: `SIGRID_PROFORMA_ORIGEN_ENABLED=false`. Con la de proformas abierta para el mes, el
  modo a origen no graba hasta verificarlo (V9). Alternativa: solo la llave de F-007 (sin red de seguridad).
- **D11 · Sin tocar el núcleo ni F-007**: las arrastradas se añaden en `_construir` (costura de F-007) y los códigos y
  respuestas nuevos viven en subclases, como F-007 amplió los de F-009 (costura 5). Así R1 y R2 se cumplen por
  construcción. Descartado: un modo dentro del núcleo; una ruta nueva.
- **D12 · Orden de las líneas** *(aprobado por el humano, 2026-10-28)*: las de la petición en su orden y después las arrastradas en el de la anterior
  (`pos` de 64 en 64). Sigrid conserva `pos` en el 84 % (M23); aquí el orden impreso cambia cada mes. Pregunta P3.
- **D13 · `facturas`**: no cambia lo que la API expone para ella, pero lee líneas a 0 y, al facturar una a origen,
  Sigrid pone `canoriant`/`imporiant` en la `dcfpro` (M30): es de F-008. Aviso escrito a `facturas` y a `proformas`.
- **D14 · Respuestas del humano para `proformas`** *(decidido, 2026-10-28; cierran las antiguas P4-P6)*: el modo lo
  indica el jefe de obra al cargar cada proforma; mandarán al menos ORIGEN y MES; el portal enseña a la persona las
  puntas y las líneas candidatas y ella elige.

## Preguntas (para el humano o Administración)

1. **P1 (D6), aprobada: solo `dcapro`.** ¿Basta con las `dcapro` arrastradas o hay que escribir también `ctrprodes` y `mov` a 0? Recomendación:
   solo `dcapro`, y lo confirma V9 en la UI.
2. **P3 (D12), aprobada: el orden propuesto.** ¿Importa el orden impreso de las líneas? Recomendación: no, salvo que V9 diga lo contrario.

## Riesgos

- **Escritura en producción con la cadena**: una anterior o una continuación mal elegidas por el llamante encadenan mal
  la proforma. Mitigan R6, R7 y R9 (solo pasa lo íntegro), R10, la previa con `cadena`, R17 dentro y la llave propia
  (D10). Lo que la API no puede saber (que la persona eligió otra punta válida) es del llamante; se anula desde la UI.
- **Carrera con el escritorio**: si Administración encadena otra a la misma punta entre la previa y el commit, R17 lo
  ve dentro; contra un alta del escritorio en el mismo instante no hay applock común (residual, como F-007).
- **Lecturas**: LP7-LP9 van por contrato y por documento; nada global sobre `ctrpro`, `dca` ni `dcapro`.
- **Dorados**: un cambio involuntario en el modo de mes lo detectan los tests de F-007 sin tocar (R1), que son la red.
