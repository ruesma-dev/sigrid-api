<!-- specs/F-016-proforma-a-origen/design.md -->
# F-016 · Diseño (v1.1: enmienda 1 del 2026-10-28, P4-P6 respondidas por el humano)

Medición: [`explore_F-016.md`](../../progress/explore_F-016.md) (M41-M44) sobre lo ya medido en
[`explore_F-007.md`](../../progress/explore_F-007.md) (M11, M16-M26, M37). Base: F-007 tal como quedó cerrada (spec
v3.1, [`contrato_proformas.md`](../F-007-registrar-proforma/contrato_proformas.md) v1.1). Llamante: `proformas` (su F-005).

## La decisión de fondo

En Sigrid conviven las dos formas: la proforma **de mes** (lo que hace F-007: solo el MES, sin cadena) y la **a origen**
(«check» de documento origen, `dca.docoritip 1`): cuelga de la anterior del contrato (`docoriide`), copia todas sus
líneas (las sin MES a `can` 0) y lleva por línea la cantidad a origen (`canoriori`) y la línea anterior (`canorilin`).
El humano decidió (2026-10-28) que se registre como indique el jefe de obra, **por meses por defecto**. F-016 añade el
modo a origen **sin cambiar el de mes**: todo lo nuevo cuelga de `modo: "origen"`.

**Límite de microservicio: cabe.** Encadenar el documento a su anterior y escribir sus líneas es alta de dominio en el
ERP, lo mismo que F-007. Decidir el modo, enseñar la cadena a la persona y desempatar por descripción es de `proformas`.

**Tamaño: una feature.** No toca el núcleo de F-009 (D11). Si el humano pide además paridad completa de las arrastradas
(D6) o sembrar el origen (D7), hay que tocar el núcleo y conviene partirla.

## Ficheros a crear

| Fichero | Capa | Qué contiene |
|---|---|---|
| `domain/models/proforma_origen_models.py` | domain | Códigos ampliados (§Códigos); `ProformaOrigenError(ProformaError)` con `puntas` (solo en los tres errores de R9); `FalloLineaProformaOrigen(FalloLineaProforma)`; `AvisoProformaOrigen(AvisoProforma)`; `PuntaCadena`, `CadenaProforma`; `LineaProformaOrigenResultado(LineaProformaResultado)`, `ProformaOrigenResponse(ProformaResponse)` (R20, R21) |
| `application/use_cases/proforma_origen_statements.py` | application | LP7 y LP8 (§SQL), `ProformaOrigenStatements` autovalidado con `DatabaseReferenceGuard`, y puras (§Funciones). Sin E/S |
| `tests/test_f016_*.py`, `tests/fixtures/f016_*.json` | — | `tasks.md`; una cadena sintética con la forma de M44 (primera, encadenadas, dos puntas, una de mes en medio) |

## Ficheros a modificar

| Fichero | Qué cambia |
|---|---|
| `domain/models/proforma_models.py` | Solo `ProformaRequest` (`modo`, `proforma_anterior`, `primera_de_cadena` y las reglas de R3) y `LineaProformaIn` (`linea_anterior`). Ni códigos ni respuestas |
| `application/use_cases/create_proforma_use_case.py` | Ramas de `modo` (§Flujo); `_Contexto` con la cadena; `_construir`, `_comprobar_dentro` y `_convertir` con lo de origen; traza R22. En mes, cada rama es inerte |
| `config/settings.py`, `local.settings.sample.json` | `SIGRID_PROFORMA_ORIGEN_ENABLED` (R4) |
| `function_app.py` | En `sigrid_proforma`, la llave de R4 tras la de F-007; en `_respuesta_albaran_compra_error`, `details.puntas` si el error las trae (como `reparto`) |
| `specs/F-007-registrar-proforma/contrato_proformas.md` | v1.2 (§Contrato v1.2); es el contrato vivo con `proformas` y no se duplica |
| `docs/ARCHITECTURE.md`, `CLAUDE.md`, `azure-apps/sigrid_api.md` | R26 (`azure-apps`, commit aparte) |

## Ficheros que NO se tocan

El núcleo de F-009/F-015 (`create_albaran_compra_use_case.py`, `albaran_compra_statements.py`,
`albaran_compra_models.py`) y sus tests y dorados; `proforma_statements.py` (LP1-LP6 y sus funciones se reutilizan
tal cual); los tests de F-007; `infrastructure/` entero; el clásico, `albaran-directo` y el resto de rutas; `infra/`.
Sin ficheros `NN_nombre.sql`: SQL constante.

## Flujo (en `CreateProformaUseCase._proforma`)

1-4. Como F-007 (guardas, fecha, obra, referencia, contrato, etapa 1 de líneas). La llave de R4 va en la ruta.
5. Con contrato, `comprobar_hoja`, LP1, LP2 y `origen` como F-007. **Mes**: `buscar_del_mes` y avisos de F-007.
   **Origen**: `anteriores_de_la_hoja` (R5b), `buscar_del_mes_origen` (R5; `existente` sale aquí, como F-007), LP7 → `elegir_anterior` (R6-R10), LP8 de
   la anterior → `casar_con_anterior` (R11; sus fallos, en un `lineas_no_validas`), tope R15 y `avisos_de_cadena` (R16,
   R17). Lo elegido viaja en `_Contexto.cadena` (`CadenaElegida`: la anterior, sus filas y el casado).
6. Traducción y núcleo como F-007. Con `cadena`, `_construir` llama a `super()` y después `superponer_cadena` (R12,
   R14) y `filas_arrastradas` (R13): las arrastradas se añaden **al final** de `filas.dcapro`, así que `numerar`, la previa,
   el `INSERT` y la relectura E12 las cuentan sin cambiar el núcleo; no son `_Linea` y no generan `ctrprodes`, `mov` ni
   `UPDATE`. `_comprobar_dentro` hace lo de F-007 (con R5) y, con `cadena`, LP7 por el cursor (R18).
7. `_convertir`: en mes, la de F-007; a origen, `ProformaOrigenResponse` con `cadena` y las arrastradas leídas de
   `filas.dcapro` a partir del índice `len(request.lineas)` (R20).

## Funciones puras (`proforma_origen_statements.py`)

- `DocumentoCadena.de_fila` (LP7: `ide`, `cod`, `fec`, `docoriide`, `totbas`, `importe_cadena`) y
  `puntas(documentos)`: las que no son `docoriide` de otra.
- `anteriores_de_la_hoja(request) -> AnterioresHoja` (R5b): la ANTERIOR de cabecera y la de cada línea, dadas o
  deducidas (ORIGEN − MES en `Decimal`, a 2 decimales en el importe), con `anterior_de` `peticion` o `deducido`.
- `elegir_anterior(documentos, *, fecha, anterior_hoja, proforma_anterior, primera, lineas_peticion,
  lineas_por_documento) -> AnteriorElegida`: R6-R10. La contradicción (R10) necesita las líneas (LP8) de las puntas
  que casan por importe; con una, son las que hacen falta para casar, sin otra lectura. `None` = primera.
- `casar_con_anterior(lineas, identificadas, filas_anterior) -> (dict[indice, fila], list[FalloLineaProformaOrigen])`:
  R11, con la partida de cada fila de LP8 (`partida_anterior`).
- `superponer_cadena(dcapro, casado) -> list[dict]` (R12) y `filas_arrastradas(filas_anterior, usadas, primera_pos)`
  (R13); quitan `partida_anterior`, que no es columna. `cabecera_a_origen(dca, anterior)` (R14).
- `buscar_del_mes_origen(proformas, *, periodo, importe_mes, otra_del_mes)` (R5) e `importe_de_cadena(filas)`
  (Σ round(`canoriori`·`pre`, 2) en `Decimal`, el de `redondear_euros`).
- `avisos_de_cadena(...)` (R16) y `meses_fuera(proformas_lp1, anterior, primer_dia)` (R17).

## SQL nuevo (`proforma_origen_statements`; todo con `?`, de lectura)

- **LP7** (R6, R9, R18): `SELECT c.ide, c.cod, c.fec, d.docoriide, d.totbas, (SELECT SUM(ROUND(p.canoriori * p.pre, 2))
  FROM dbo.dcapro p WHERE p.docide = d.ide) AS importe_cadena FROM dbo.dca d JOIN dbo.con c ON c.ide = d.ide WHERE
  c.tip = ? AND d.ctride = ? AND d.docoritip = ?` con `[14, ctride, 1]`. Por contrato: medida en 3,8-4,1 s con 5-24
  documentos (M44). El `ROUND` en SQL basta con la tolerancia de 0,05 (M25 midió así).
- **LP8** (R10, R11, R13): `SELECT p.*, ISNULL(pp.cod, '') AS partida_anterior FROM dbo.dcapro p LEFT JOIN
  dbo.obrparpar pp ON pp.ide = p.paride WHERE p.docide = ? ORDER BY p.pos, p.ide` con `[ide_anterior]`. Fila completa:
  es la plantilla de la arrastrada (como `SELECT *` de L8). Lectura por `docide`, la de LP6.

LP1-LP6 no cambian. La sucesora fuera del contrato no se busca (M19: 9 casos; un `docoriide` sin índice conocido
obligaría a recorrer `dca`): riesgo residual anotado.

## Contrato v1.2 con `proformas` (compatible hacia atrás)

- **Petición**: `modo`, `proforma_anterior`, `primera_de_cadena`, `linea_anterior` (R3). Sin ellos, v1.1 tal cual.
  A origen es obligatorio `importe_origen`; `importe_anterior` y `cantidad_anterior` son opcionales y, sin ellos, la
  API los deduce de ORIGEN − MES (R5b) y lo dice en `cadena.anterior_de`.
- **Respuesta a origen**: `cadena` y los cuatro campos de línea (R20); las arrastradas al final con `arrastrada: true`,
  `referencia_linea` la de su fila y `indice` ≥ nº de líneas pedidas. En mes, la respuesta de v1.1 sin claves nuevas.
- **Códigos**: los de §Códigos, con qué hace `proformas` (§4 del contrato).
- **§6 Lo que lee `facturas`**: una proforma a origen trae líneas con `can` 0 (arrastradas) y su `entref` es el mismo
  `PROF<MMAA>_<obra>`; `totbas` sigue siendo el MES (M28). Solo pasan a factura las de `can` ≠ 0 (M15).

## Códigos

- **Cabecera nuevos**: `escritura_proformas_origen_deshabilitada`, `anterior_no_resuelta`, `anterior_ambigua`,
  `anterior_con_sucesora`, `anterior_no_valida` (los tres de R9, con `puntas`). Heredados: todos los de F-007.
- **Línea nuevos**: `linea_anterior_no_valida`, `linea_anterior_ambigua` (con `candidatos`: `dcapro.ide`).
- **Avisos nuevos**: `origen_distinto_de_sigrid`, `cadena_con_meses_fuera`. Se reutilizan `anterior_distinto_de_sigrid`
  y `otra_del_mes` con el sentido de R16 y R5.

## Decisiones (para el humano; recomendación en negrita)

- **D1 · Modo por petición, de mes por defecto** *(decidido, 2026-10-28)*. **`modo: "origen"`** en cada petición; sin
  él, F-007 exacta (R1). Lo elige el jefe de obra al cargar la hoja en `proformas`, por hoja y no por contrato (P4); la API no lo deduce.
- **D2 · Elegir la anterior.** Problema: cadenas paralelas (M18: 158 pares en el mismo mes; M44: dos puntas), serie
  mezclada (M19: 92 anteriores `AC`), la primera y dos certificaciones del mismo mes (M18: 18). **Puntas a origen del
  contrato, de cualquier serie, cuyo importe de cadena = ANTERIOR de la hoja (±0,05) sin contradicción de líneas**:
  M25, 96,4 % única y correcta, 0 incorrectas; lo que no casa va a la persona con `details.puntas` y vuelve con
  `proforma_anterior` o `primera_de_cadena`. ANTERIOR ≈ 0 es primera (M25: 139 de 140 primeras no casan con ninguna).
  Dos del mismo mes en la misma cadena salen solas: la segunda cuelga de la primera, que es la punta. Ramificar una
  cadena nunca (M19: lineal): una candidata con sucesora es `anterior_con_sucesora`. Alternativas: anterior obligatoria
  en la petición (`proformas` no ve las altas a mano ni las `AC`); la última por fecha (falla con paralelas).
  **Enmienda 1 (humano, P5)**: la hoja trae ORIGEN y MES como mínimo, así que la ANTERIOR se toma de la petición o se
  deduce (R5b), y «la anterior siempre estará en Sigrid»: `anterior_no_resuelta` se espera rara (alta mal hecha o
  cambio de modo, D7). La regla no cambia.
- **D3 · Casar la línea con la de la anterior**, con la regla del humano para el contrato (2026-10-28): por `ctrpro`
  (vinculadas) o por **partida y precio** (sin vincular), **el producto no cuenta**, y el desempate por descripción es
  de `proformas` (`linea_anterior_ambigua` con `candidatos` → reenvía con `linea_anterior`). M20: 2 % de pares con dos
  líneas del mismo `ctrpro` en una proforma.
- **D4 · Qué líneas lleva.** **Todas las de la anterior** (M23: 746 de 775 arrastran todas) **más las nuevas de la
  petición**; la primera, **solo las de la petición** (M42: 151 «solo las del mes» frente a 96 «todas las del
  contrato»). Alternativa: la primera con todas las líneas del contrato a 0 (más filas, sin ganancia en el origen).
- **D5 · Columnas a origen como Sigrid** (M41, M11, M23): `canoriori` acumulado por línea y `= can` en la primera y en
  las nuevas; `canorilin` a la línea anterior; `canoriant`/`imporiant` 0; `imporiori` del `ctrpro` o de la anterior.
- **D6 · Arrastradas: solo `dcapro`.** Sigrid escribe además una `ctrprodes` a 0 por vinculada (M6) y un `mov` a 0 si
  `tipmov` 1 (M6: 96,8 %). No cambian servido, stock ni PMP, y escribirlas obliga a reservar `ide` y balances para
  líneas que no son del núcleo (costura nueva en F-009, en producción). **Solo `dcapro`, y V9 en la UI** (ficha,
  impresión, factura y anulación). Alternativa: paridad completa (tocar el núcleo; partir la feature). Pregunta P1.
- **D7 · Cambio de modo.** M43: 64 contratos mezclan modos; de mes a origen, 22 de 29 retoman la cadena vieja y 5
  empiezan otra; Sigrid **no siembra** el origen (M41). **De origen a mes, F-007 tal cual** (aviso `contrato_a_origen`);
  la cadena queda con su punta. **De mes a origen, como Sigrid**: la ANTERIOR de la hoja incluye los meses de mes y no
  casa con la punta vieja, así que sale `anterior_no_resuelta` con las puntas y la persona elige `proforma_anterior`
  (retomar) o `primera_de_cadena`; en los dos casos, aviso `cadena_con_meses_fuera` y `anterior_distinto_de_sigrid`.
  Alternativa: sembrar `canoriori` con lo servido de mes (LP2): origen «real», pero distinto de lo que hace Sigrid y
  sin regla para las sin vincular. Pregunta P2.
- **D8 · Ya registrada a origen** (R5): `idempotente` y `existente` como F-007. Una a origen del mes con otro total
  es otra cadena o la certificación anterior del mismo mes: aviso, no error. Si es la de **esta** cadena con otro
  total, la anterior ya tiene sucesora y sale `anterior_con_sucesora` (D2). No se ha usado la regla de M26 (origen y
  líneas): R24 + D2 ya la cubren sin otra lectura.
- **D9 · Cuadre ORIGEN/ANTERIOR: aviso, no error**, como F-007 D7. La ANTERIOR elige la anterior (R9); con la anterior
  pedida o en primera, su diferencia es aviso; ORIGEN = ANTERIOR + MES de la hoja sigue siendo error (F-007 R19). El
  importe de cadena es Σ round(`canoriori`·`pre`, 2): M44, 34 de 35 encadenadas cuadran con Σ anterior + `totbas`.
- **D10 · Llave propia del modo**: `SIGRID_PROFORMA_ORIGEN_ENABLED=false`. Con la de proformas abierta para el mes, el
  modo a origen no graba hasta verificarlo (V9). Alternativa: solo la llave de F-007 (sin red de seguridad).
- **D11 · Sin tocar el núcleo ni F-007**: las arrastradas se añaden en `_construir` (costura de F-007) y los códigos y
  respuestas nuevos viven en subclases, como F-007 amplió los de F-009 (costura 5). Así R1 y R2 se cumplen por
  construcción. Descartado: un modo dentro del núcleo; una ruta nueva.
- **D12 · Orden de las líneas**: las de la petición en su orden y después las arrastradas en el de la anterior
  (`pos` de 64 en 64). Sigrid conserva `pos` en el 84 % (M23); aquí el orden impreso cambia cada mes. Pregunta P3.
- **D13 · `facturas`**: no cambia lo que la API expone para ella, pero lee líneas a 0 y, al facturar una a origen,
  Sigrid pone `canoriant`/`imporiant` en la `dcfpro` (M30): es de F-008. Aviso escrito a `facturas` y a `proformas`.

## Preguntas

Para el humano o Administración (V10):
1. **P1 (D6)**: ¿basta con las `dcapro` arrastradas o hay que escribir también `ctrprodes` y `mov` a 0? Recomendación:
   solo `dcapro`, y lo confirma V9 en la UI.
2. **P2 (D7)**: al pasar de mes a origen, ¿retomar la cadena vieja (lo de hoy) o empezar otra? ¿Sembrar el origen?
   Recomendación: la persona elige entre las dos; sin sembrar.
3. **P3 (D12)**: ¿importa el orden impreso de las líneas? Recomendación: no, salvo que V9 diga lo contrario.

Para `proformas`, **decididas por el humano el 2026-10-28** (enmienda 1):
4. **P4**: el jefe de obra indica el modo **al cargar la proforma**, **por hoja** y no por contrato: es `modo` por
   petición (D1).
5. **P5**: a origen mandarán **ORIGEN y MES como mínimo**; la ANTERIOR se deduce y la anterior siempre estará en
   Sigrid. Obligatorio `importe_origen`, no `importe_anterior` (R3, R5b; D2).
6. **P6**: `proformas` enseña `details.puntas` y los `candidatos` de `linea_anterior_ambigua` y la persona elige.

## Riesgos

- **Escritura en producción con la cadena**: una anterior mal elegida encadena mal la proforma. Mitigan R9 (solo con
  importe y líneas; con la ANTERIOR deducida, un ORIGEN mal leído desplaza la elección y suele dar `anterior_no_resuelta`), la previa con `cadena`, R18 dentro y la llave propia (D10). Se anula desde la UI.
- **Carrera con el escritorio**: si Administración encadena otra a la misma punta entre la previa y el commit, R18 lo
  ve dentro; contra un alta del escritorio en el mismo instante no hay applock común (residual, como F-007).
- **Lecturas**: LP7 y LP8 van por contrato y por documento (M44: ≤ 4,1 s); nada global sobre `ctrpro` ni `dcapro`.
- **Dorados**: un cambio involuntario en el modo de mes lo detectan los tests de F-007 sin tocar (R1), que son la red.
