<!-- specs/F-007-registrar-proforma/contrato_proformas.md -->
# Contrato proformas ↔ sigrid-api · registro de la proforma del jefe de obra

**F-007 de sigrid-api (`POST /api/sigrid/proforma`) ↔ F-005 del microservicio `proformas`.** **v1.2**
(2026-10-28): la v1.1 (2026-10-26, F-007 desplegada el 2026-10-26 y cerrada el 2026-10-28) más el **modo a origen** de
**F-016** ([spec](../F-016-proforma-a-origen/requirements.md)), **revisado y desplegado el 2026-10-28**. Es compatible hacia atrás: sin `modo` (o con `"mes"`) todo es la v1.1 tal
cual, sin ninguna clave nueva en la respuesta. Lo nuevo de la v1.2: §2.1 y §2.2 (campos de cadena), **§2.3** (a origen:
lo que el llamante lee de Sigrid, con sus dos consultas), §3.1 (respuesta a origen), §4 (códigos nuevos), §6 y §8.
**v1.3** (2026-10-29, **F-018 v1.2** de sigrid-api, [spec](../F-018-descuento-por-linea/requirements.md), aprobada
por el humano; acusada por `proformas` el 2026-10-29; **pendiente de despliegue** de sigrid-api: hasta entonces la
API escribe esas líneas como la v1.2): las líneas de contrato cuyo `ctrpro` tiene descuento se
escriben como Sigrid, de mes y a origen. Compatible hacia atrás salvo esas líneas; la petición no cambia. Qué tiene que
hacer `proformas` (detalle en §8):

1. **Nada en la petición**: sigue sin `dto` (mandarlo da 400 sin código, §2.2) y el `precio` de una línea de
   contrato sigue siendo el de la hoja (el `ctrpro.pre`, neto).
2. **Esperar diferencias en las líneas con descuento del contrato** entre la hoja y lo registrado. De mes, hasta un
   céntimo por línea entre `importe_mes` y `totales.totbas` (con `cantidad` ≤ `ctrpro.can` y un `ctrpro` con `pre` =
   `tot`/`can`; §3). A origen, entre el ORIGEN de la hoja y `cadena.importe_origen_cadena`, **más de un céntimo**:
   crece con `canoriori`/`cantidad` (§3.1). La comprobación de la hoja (`importe_mes_no_cuadra`) no cambia.
3. **Admitir dos claves nuevas en la línea de respuesta**, `dto` y `precio_bruto`, solo en esas líneas, también de
   mes (§3.1).
4. **Reenviar siempre con la misma `referencia_externa`** (sale `idempotente`): con otra, una proforma con más de unas
   cinco de esas líneas puede no reconocerse como `existente` (§3, §4).
5. **Mapear el aviso `dto_distinto_del_contrato`** si vuestro conjunto de avisos es cerrado: lo hereda la proforma,
   aunque hoy no puede salir (§4).

Lo de `facturas` (§6) se le avisa aparte.

Traspaso de origen: `proformas/docs/referencia/01_traspaso_facturas.md`. Plantilla de hoja propuesta para los jefes de
obra: [`plantilla_hoja.md`](plantilla_hoja.md).

**Dueño**: sigrid-api (expone el endpoint). `proformas` lo consume y **no lo copia**: enlaza aquí. Si este documento y
la spec de F-007 discrepan, manda la spec. Como con albaranes: las reglas, la validación y los códigos los cambia
sigrid-api; `proformas` edita solo lo que consume (de dónde saca cada campo y cómo mapea cada código).

## 1. Flujo

1. `proformas` recibe la hoja del jefe de obra (xlsx o pdf) y **la lee** (eso es suyo). En su bandeja, una persona
   **casa cada partida de contrato con su línea del contrato** (`ctrpro_ide`) y **elige el producto** de cada línea
   nueva (§5). Arma la petición de §2: una por hoja, mes y contrato (si la hoja abarca dos, dos peticiones con el
   mismo `periodo`: cada una ve solo su contrato).
2. **Previa** (`commit:false`), desde la bandeja y antes de aprobar: valida contra Sigrid y devuelve lo que escribiría,
   sin escribir. **Una por proforma, sin ráfagas**; el balanceador corta a los 230 s y el tope es de 500 líneas.
3. La persona revisa el **contrato resuelto** (`contrato.resuelto_por`, `candidatos`), las líneas y los **avisos**. Si
   el contrato no es el bueno, reenvía con `cod_contrato`.
4. **Grabación** (`commit:true`) al aprobar: la misma petición. Repetirla da `idempotente`.

Una proforma de mes se escribe como un albarán de compra de la serie `PROF<aa>/` (`cla 141`; el humano la mantiene
aunque hoy lo habitual sea `AC`) con solo las partidas de MES ≠ 0; las de contrato, vinculadas a su línea de contrato
(«documento origen»). El origen no se escribe: la API lo calcula sumando las proformas del contrato.

**A origen (v1.2, F-016).** Si el jefe de obra indica que esa proforma va **a origen** (lo indica él al cargar cada
proforma, por hoja y no por contrato; por defecto, de mes), `proformas` manda `modo: "origen"` y además **elige** la
proforma anterior de la cadena (o dice que es la primera) y **qué línea de la anterior continúa** cada línea de la hoja,
leyendo Sigrid con las consultas de §2.3 y enseñándoselas a la persona en la bandeja. La API **no busca ni deduce**:
registra lo que le mandan, valida su integridad (§2.3, «Lo que comprueba la API») y lo escribe como lo deja Sigrid
(`dca.docoritip` 1, `docoriide` = la anterior; por línea, la cantidad a origen acumulada), **arrastrando a 0** las
líneas de la anterior que nadie continúa. Mismo flujo de previa y grabación; la grabación a origen tiene su propia
llave (`escritura_proformas_origen_deshabilitada`, §4).

## 2. Petición

### 2.1. Cabecera

| Campo | Tipo | Oblig. | De la hoja | Qué hace la API |
|---|---|---|---|---|
| `database` | texto | sí | — | `ruesma` |
| `usu` | texto ≤24 | sí | — | `dbo.usu.cod` de **quien aprueba** en la bandeja (traza `log`) |
| `referencia_externa` | texto 1-128 | sí | — | `PRF-` + id de la proforma en `proformas`; clave de idempotencia (`dca.synckey`) |
| `cod_obra` | texto | sí | OBRA («719.…» → `0719`) | Obra de las empresas permitidas |
| `periodo` | entero `AAAAMM` | sí | MES («AGOSTO-26» → `202608`) | Mes de la proforma; fecha = último día si ya pasó. **Número, no texto**: `"202608"` da 400 |
| `importe_mes` | número | sí | TOTALES · IMPORTE MES | Debe ser Σ round(`cantidad`·`precio`, 2) ± 0,05 |
| `importe_anterior` | número | no | TOTALES · IMPORTE ANTERIOR | Se compara con lo registrado (aviso) |
| `importe_origen` | número | no | TOTALES · IMPORTE ORIGEN | Con el anterior: ORIGEN = ANTERIOR + MES (error si no) |
| `cod_contrato` | texto | no | Nº CONTRATO | Si viene, **manda** (así se cambia el resuelto); si no está en la obra, `contrato_no_encontrado` |
| `cif_proveedor` | texto | no¹ | — | Resuelve el contrato (`ctr.entcif`); si viene, **manda sobre el nombre** (solo se filtra por CIF); obligatorio con `sin_contrato` |
| `nombre_proveedor` | texto ≤128 | no¹ | SUBCONTRATISTA | Resuelve el contrato por nombre normalizado en `ctr.entres` |
| `sin_contrato` | bool | no | Nº CONTRATO vacío | Alta sin contrato (todas las líneas sin vincular, sin retención). Sin contrato **no** se comprueba la hoja (`importe_mes_no_cuadra`, `hoja_descuadrada`, `linea_descuadrada`), ni se calcula el origen ni se busca la del mes (`existente`) |
| `otra_del_mes` | bool | no | — | Permite una segunda proforma del mismo contrato y mes, tenga la del mes el mismo importe o no (con él no se devuelve `existente`) |
| `fecha_proforma` | entero `AAAAMMDD` | no | — | Debe caer en `periodo` |
| `su_referencia` | texto ≤128 | no | — | `dca.entref`; por defecto `PROF<MMAA>_<obra>` (§6) |
| `numero_orden` | entero | no | Nº ORDEN | Solo traza (es el ordinal mensual, no se valida) |
| `commit` | bool | no | — | `false` por defecto |
| `modo` | `"mes"` \| `"origen"` | no | (lo indica el jefe de obra) | **v1.2.** `"mes"` por defecto: la v1.1 exacta. `"origen"`: proforma a origen (§2.3). A origen no admite `sin_contrato` |
| `proforma_anterior` | texto 1-24 | a origen³ | (elegida en la bandeja, §2.3) | **v1.2.** `con.cod` de la proforma anterior de la cadena (`PROF…` o `AC…`), del contrato resuelto |
| `primera_de_cadena` | bool | a origen³ | (elegida en la bandeja) | **v1.2.** `false` por defecto. `true`: primera proforma a origen del contrato, sin anterior |

¹ Hace falta `cod_contrato`, `cif_proveedor` o `nombre_proveedor`.

³ Con `modo: "origen"` va **exactamente uno** de `proforma_anterior` y `primera_de_cadena`. Dan 400 `Solicitud
invalida.` **sin `codigo`** (F-012): a origen sin ninguno de los dos o con los dos; `proforma_anterior`,
`primera_de_cadena` o una `linea_anterior` sin `modo: "origen"`; `linea_anterior` con `primera_de_cadena`; dos líneas
con el mismo `linea_anterior`; `modo: "origen"` con `sin_contrato`. Los importes y cantidades de la hoja siguen siendo
opcionales como en la v1.1 (`importe_mes` es obligatorio en los dos modos).

### 2.2. Línea (solo las partidas con MES ≠ 0)

| Campo | Tipo | Oblig. | De la hoja | Qué hace la API |
|---|---|---|---|---|
| `referencia_linea` | texto 1-24 | sí | (la fila) | `dcapro.refent`; única en la petición |
| `cantidad` | número ≠ 0 | sí | MEDICIÓN · MES | Cantidad de la línea (con signo) |
| `precio` | número | sí | P. unit. | Si difiere del contrato, aviso y se escribe el de la hoja. **v1.3**: si casa con un `ctrpro` con descuento, la línea se escribe como Sigrid (§3) |
| `descripcion` | texto ≤128 | sí | Trabajos realizados | `dcapro.res` |
| `ctrpro_ide` | entero | **sí en las de contrato**² | (casada en la bandeja) | Solo se comprueba que es del contrato resuelto; si no, `linea_no_es_del_contrato` (también si es de otro contrato de la obra). No se corrige ni se sustituye |
| `producto` | texto | **sí en las nuevas**² | (elegido en la bandeja) | De la lista de §5 o de los productos del contrato; sin él, `producto_obligatorio` |
| `partida` | texto | no | Partida | Partida de la línea nueva (si no, la de imputación); en el respaldo sin `ctrpro_ide`², filtro de la línea de contrato |
| `medicion_contrato` | número | no | Medición de Contrato | Sin `ctrpro_ide`, > 0 hace la línea de contrato²; no sirve para identificarla |
| `unidad` | texto ≤8 | no | UD. | `dcapro.unimed` |
| `cantidad_anterior`, `cantidad_origen` | número | no | MEDICIÓN · ANTERIOR / ORIGEN | ORIGEN = ANTERIOR + MES (error); ANTERIOR frente a Sigrid (aviso) |
| `partida_imputacion` | texto | no | — | Otra partida que la de la línea de contrato |
| `linea_anterior` | entero ≥ 1 | no (solo a origen) | (elegida en la bandeja, §2.3) | **v1.2.** `dcapro.ide` de la línea de la proforma anterior que esta continúa. Sin él, la línea es **nueva** en la cadena (su origen empieza en su MES). La API comprueba que es de la anterior y del mismo tipo (§2.3); no casa por su cuenta |

**v1.3**: la línea **no tiene campo `dto`** (a diferencia de `sigrid/albaran`); mandarlo da 400 `Solicitud invalida.`
sin `codigo`, como cualquier clave desconocida. El descuento de una línea de contrato sale de su `ctrpro` (§3).

² `ctrpro_ide` y `producto` no van juntos. La API admite, como respaldo para otro llamante, una línea de contrato sin
`ctrpro_ide`; `proformas` no lo usa. En Sigrid una partida de la proforma se vincula a una línea del contrato por
partida y precio unitario, y el desempate entre varias es semántico (la descripción significa lo mismo). Así que la API
se queda con las líneas del contrato de esa `partida` (código; sin `partida` no casa ninguna) **y** ese precio
(±0,0001), los dos filtros estrictos: una, esa; ninguna, `linea_no_es_del_contrato`; varias, `linea_ambigua` con sus
`ctrpro_ide`, y `proformas` desempata por la descripción y reenvía con `ctrpro_ide`. Ni la medición, ni la unidad, ni
el `producto` cuentan para vincularla. Con varios contratos candidatos, la misma regla dice en cuál «está» la línea.

### 2.3. A origen: lo que lee `proformas` de Sigrid y lo que comprueba la API (v1.2)

En Sigrid una proforma a origen cuelga de la anterior del contrato (`dca.docoriide`), copia **todas** sus líneas (las
que no tienen MES, a `can` 0) y lleva por línea la cantidad a origen (`dcapro.canoriori`) y la línea de la anterior que
continúa (`dcapro.canorilin`). La cadena es lineal: cada proforma tiene como mucho una sucesora. Elegir la anterior y
las continuaciones es de `proformas`; para eso lee Sigrid por **`sql/read`**, con marcadores `?`, `database` `ruesma`
y **comprobando `truncated`** (si viene `true`, la lectura no vale). Las dos consultas son orientativas (`proformas`
las adapta). La 1 deriva de la lectura de la cadena medida en M44 de `progress/explore_F-016.md` (~4 s por contrato),
que se midió **sin** el `NOT EXISTS` de sucesora; la 2 no se ha medido. Las dos se prueban en lectura sobre cadenas
reales en la verificación de F-016 (T17, V0/V2 de `specs/F-016-proforma-a-origen/verificacion_manual.md`), antes del
despliegue.
`<ctride>` es el `contrato.ide` que devuelve la previa (o el del `cod_contrato` que la persona eligió).

**1. Puntas a origen del contrato** (candidatas a `proforma_anterior`): los `tip 14` del contrato con `docoritip` 1, de
cualquier serie (`PROF` o `AC`: la cadena mezcla series), que **no** son la anterior de otro `tip 14` del contrato,
con su importe a origen de cadena (Σ `ROUND(canoriori · pre, 2)` de sus líneas):

```sql
SELECT c.ide, c.cod, c.fec, d.totbas, d.docoriide,
       (SELECT ISNULL(SUM(ROUND(p.canoriori * p.pre, 2)), 0)
          FROM dbo.dcapro p WHERE p.docide = d.ide) AS importe_cadena
  FROM dbo.dca d JOIN dbo.con c ON c.ide = d.ide
 WHERE c.tip = ? AND d.ctride = ? AND d.docoritip = ?
   AND NOT EXISTS (SELECT 1 FROM dbo.dca s JOIN dbo.con cs ON cs.ide = s.ide
                    WHERE cs.tip = ? AND s.ctride = d.ctride AND s.docoriide = d.ide)
 ORDER BY c.fec DESC, c.ide DESC
-- parameters: [14, <ctride>, 1, 14]
```

Sugerencia para la bandeja (regla medida en M25: única y correcta en el 96,4 % de 773 proformas encadenadas): la punta
cuyo `importe_cadena` es el ANTERIOR de la hoja ± 0,05 € (si la hoja solo trae ORIGEN y MES, ANTERIOR = ORIGEN − MES).
Ninguna o varias (dos cadenas paralelas en el mismo contrato pasan): **elige la persona**. ANTERIOR 0, o el contrato
sin puntas: `primera_de_cadena: true`. Una punta con `fec` posterior a la fecha de la proforma no vale (la API da
`anterior_no_valida`). Si el contrato pasó de mes a origen, retomar la cadena vieja (su punta) o empezar otra
(`primera_de_cadena`) lo decide la persona: la API no siembra el origen con los meses registrados de mes.

**2. Líneas de la punta elegida** (candidatas a `linea_anterior`), en su orden:

```sql
SELECT p.ide, p.pos, p.linoriide, p.docoritip, ISNULL(pp.cod, '') AS partida,
       ISNULL(pc.cod, '') AS producto, p.res, p.unimed, p.pre, p.can, p.canoriori
  FROM dbo.dcapro p
  LEFT JOIN dbo.obrparpar pp ON pp.ide = p.paride
  LEFT JOIN dbo.con pc ON pc.ide = p.proide
 WHERE p.docide = ?
 ORDER BY p.pos, p.ide
-- parameters: [<ide de la punta elegida>]   (max_rows ≥ nº de líneas; ver truncated)
```

Cada línea de la hoja que continúa una de ellas manda su `ide` en `linea_anterior`: una línea de contrato, la de
`linoriide` = su `ctrpro_ide` (si hay varias con el mismo, por partida, precio y descripción; desempata la persona);
una línea nueva sin vincular, una de `linoriide` 0, por partida, precio y descripción. Las líneas de la punta que
ninguna continúa **las arrastra la API** (§3.1): no hay que mandarlas.

**Lo que comprueba la API** (y nada más; no elige por importe ni casa por su cuenta):

- **La anterior** (`proforma_anterior`): un único `tip 14` con ese `con.cod` en el contrato resuelto, a origen
  (`docoritip` 1) y con `con.fec` no posterior a la fecha de la proforma; si no, `anterior_no_valida`. Y que es la
  **punta**: si ya tiene sucesora en el contrato, `anterior_con_sucesora` (con su `cod`); se relee bajo el applock antes
  de grabar. Una sucesora en **otro** contrato no se busca (riesgo residual). Con `primera_de_cadena`, nada de esto.
- **Cada `linea_anterior`**: es una línea de la anterior, del mismo `ctrpro` (`linoriide`) si la línea es de contrato,
  o sin vincular (`linoriide` 0) si es nueva sin vincular; si no, `linea_anterior_no_valida` en `lineas_no_validas`,
  junto con los demás fallos de línea de la v1.1.
- **Integridad**: una línea de contrato que va como nueva y cuyo `ctrpro` ya está en la anterior parte su origen en dos
  líneas (la nueva empieza en su MES y la vieja se arrastra a 0). Sigrid lo admite, así que no es error: aviso
  `linea_nueva_ya_en_la_anterior` con los `dcapro.ide` de la anterior (`lineas_anterior`), casi siempre un olvido.
- El tope `SIGRID_PROFORMA_MAX_LINEAS` cuenta las líneas de la petición **más las arrastradas** (`demasiadas_lineas`,
  también en la previa). Las comprobaciones de la hoja de la v1.1 (cuadre, `origen`, `anterior_distinto_de_sigrid`,
  `supera_contrato*`) se aplican igual; comparar la hoja con la cadena es de `proformas`, con la consulta 1 y la
  `cadena` de la respuesta.

## 3. Respuesta

200 con la forma del modo extendido de `sigrid/albaran` (`estado`, `cod`, `con_ide`, `totales` con `tot`, `retenciones`,
`avisos[]`, `lineas[]`, `filas`) y además:

- `estado`: `previsto` (previa), `creado`, `idempotente` (misma `referencia_externa`) o **`existente`**: ya hay una
  proforma **de ese contrato** y mes con el mismo importe (también una `AC` con `entref` `PROF…`); la devuelve, **no
  escribe** y trae por línea `dcapro_ide`, `linoriide`, `producto`, `cantidad`, `precio` e `importe`, en previa y con
  `commit`, para enlazarla sin otra lectura.
  En `existente`, `cabecera` trae `fec` y `entref`, `totales` trae `totbas` y `n_lineas`, y `avisos` los de la hoja
  (`anterior_distinto_de_sigrid`, `supera_contrato`, `supera_contrato_10`, `contrato_a_origen`).
- `contrato`: `cod`, `ide`, `resuelto_por` (`peticion`, `proveedor` o `lineas`) y `candidatos` (sus `cod`). Nulo con
  `sin_contrato`. En `idempotente` viene el contrato y `origen` es nulo.
- `origen`: `importe_anterior_sigrid`, `importe_mes`, `importe_origen`, `importe_contrato`, `porcentaje_contrato`;
  nulo sin contrato.
- Por línea: `de_contrato`, `ctrpro_ide`, `cantidad_anterior_sigrid`.
- **v1.3, línea de contrato cuyo `ctrpro` tiene descuento** (`ctrpro.dto` en el formato de Sigrid, `N%` o `N,N%`,
  mayor que 0, y `tar` ≠ 0) y que casa con él por precio (la regla de `sigrid/albaran`), de mes y a origen: se copian
  `tar` (bruto) y `dto` del contrato, como hasta ahora, y se escribe como Sigrid: `tot` = ROUND_HALF_UP(`cantidad` ·
  `tar` · (1 − d/100), 2) sobre el producto exacto, `pre` = `tot`/`cantidad` sin redondear, `ivacuo` sobre ese `tot`
  y, si la línea mueve stock, el `mov` con ese `pre`. La cabecera suma esos `tot`: `totales` y `dca.totbas` pueden
  diferir de `importe_mes` hasta **un céntimo por línea así** (más si el propio `ctrpro` no cumple `pre` =
  `tot`/`can`), y `dca.impbru` es el bruto (Σ `round(can·tar, 2)` en esas líneas y `tot` en las demás). Su línea de
  respuesta trae `precio` = el `pre` neto, `total` = ese `tot` y dos claves más: `dto` (el porcentaje, número) y
  `precio_bruto` (`tar`). Un `ctrpro.dto` en otra forma (cascada, sin `%`) o `tar` 0: la línea es la de la v1.2.
  Ejemplo: `tar` 4,278 al 40 % en un contrato de 36 uds (`tot` 92,40), proforma de 12,5 uds → `tot` 32,09 (con la v1.2,
  32,08).

Ejemplo (hoja de agosto de `CTSB26/0472`, obra 0719, en `docs/referencia/proforma_ejemplo_bau_siglo_xxi.md`; dos de
sus seis líneas y BERENJENO): la proforma ya existe en Sigrid (`AC26/25548`, M29), así que la previa da `existente`.

```jsonc
// POST /api/sigrid/proforma
{"database": "ruesma", "usu": "<login de quien aprueba>", "referencia_externa": "PRF-<id en proformas>",
 "cod_obra": "0719", "periodo": 202608, "nombre_proveedor": "BAU SIGLO XXI", "numero_orden": 2,
 "importe_mes": 17024.28, "importe_anterior": 2651.00, "importe_origen": 19675.28,
 "lineas": [
  {"referencia_linea": "F09", "ctrpro_ide": 262990, "unidad": "M3", "descripcion": "VERTIDO HORMIGON CIMENTACION LIMPIEZA",
   "cantidad": 620, "cantidad_anterior": 241, "cantidad_origen": 861, "precio": 11},
  {"referencia_linea": "F15", "ctrpro_ide": 262996, "unidad": "M3", "descripcion": "VERTIDO HORMIGON MUROS",
   "cantidad": 38.57, "cantidad_origen": 38.57, "precio": 10},
  {"referencia_linea": "F23", "producto": "SM1004", "partida": "02.20.02.02.11", "unidad": "M2",
   "descripcion": "BERENJENO", "cantidad": 75.85, "precio": 3.5}],
 "commit": false}
// 200 (líneas abreviadas a tres de seis)
{"estado": "existente", "cod": "AC26/25548", "con_ide": 2831541, "committed": false,
 "contrato": {"cod": "CTSB26/0472", "ide": 2793879, "resuelto_por": "proveedor", "candidatos": ["CTSB26/0472"]},
 "origen": {"importe_anterior_sigrid": 2651.0, "importe_mes": 17024.28, "importe_origen": 19675.28,
            "importe_contrato": 64897.38, "porcentaje_contrato": 30.3},
 "lineas": [
  {"dcapro_ide": 1352729, "linoriide": 262990, "producto": "SM1004", "cantidad": 620.0, "precio": 11.0, "importe": 6820.0},
  {"dcapro_ide": 1352733, "linoriide": 262996, "producto": "SM1004", "cantidad": 38.57, "precio": 10.0, "importe": 385.7},
  {"dcapro_ide": 1352739, "linoriide": 0, "producto": "SM1004", "cantidad": 75.85, "precio": 3.5, "importe": 265.48}],
 "avisos": []}
```

Con `otra_del_mes: true` la previa daría `previsto`: F09 y F15 vinculadas a los `ctrpro` 262990 y 262996 (F15 con
el aviso `supera_pendiente`: 38,57 frente a 37,22 de contrato), BERENJENO sin vincular con `SM1004` (producto del
contrato: naturaleza, cuenta e IVA de su línea de contrato) y la retención del contrato.

### 3.1. Respuesta a origen (v1.2)

Sin `modo` o con `"mes"`, la respuesta de §3 **sin ninguna clave nueva**, con una excepción de la v1.3: las líneas de
contrato con descuento del `ctrpro` traen `dto` y `precio_bruto` (§3). Las demás líneas, las de `existente` e
`idempotente` (leídas) y las arrastradas no las traen nunca. Con `modo: "origen"`, la misma más:

- `cadena` (objeto; **`null` en `existente` e `idempotente`**): `anterior` (`{cod, ide}` de la anterior, o `null` en
  la primera), `primera_de_cadena`, `importe_anterior_cadena` (Σ round(`canoriori`·`pre`, 2) de las líneas de la
  anterior), `importe_origen_cadena` (lo mismo de las líneas que se escriben, arrastradas incluidas) y `n_arrastradas`.
  `proformas` puede cotejar `importe_anterior_cadena` con el ANTERIOR de la hoja y `importe_origen_cadena` con el ORIGEN.
  **v1.3**: `importe_origen_cadena` usa el `pre` neto de las líneas con descuento del contrato (§3). A origen la
  diferencia **no** está acotada a un céntimo: `importe_origen_cadena` = Σ round(`canoriori`·`pre`, 2) y el `pre`
  neto sale de la cantidad del MES, así que la desviación de esa línea se multiplica por `canoriori`/`cantidad`. Es
  la forma de Sigrid, que escribe `pre` = `tot`/`can` (M46, 99,99 % de las líneas), no un error de la API. Medido
  con un `ctrpro` de 36 uds a `tar` 4,278 al 40 % (el `tot` del MES es el de la v1.2): MES 1 y `canoriori` 30, 77,10
  frente a 77,00 (10 céntimos); MES 0,5 y 30, 76,80 frente a 77,00 (20); MES 2 y 36, 92,34 frente a 92,40 (6). El
  `importe_anterior_cadena` de la proforma siguiente lo hereda, porque lee esos `pre`.
  En esta proforma, `importe_anterior_cadena`, `cantidad_anterior_cadena` y `cantidad_origen_cadena` no cambian.
- Por línea, además: `linea_anterior` (el `dcapro.ide` que continúa; `null` en las nuevas), `arrastrada` (`false`),
  `cantidad_anterior_cadena` (el `canoriori` de la línea continuada; 0 en las nuevas) y `cantidad_origen_cadena`
  (anterior + `cantidad`). En `existente` e `idempotente` (líneas leídas) estos cuatro van a `null`.
- **Las arrastradas, detrás** de las de la petición y en el orden de la anterior: `arrastrada: true`, `indice` ≥ nº de
  líneas pedidas, `referencia_linea` = la `refent` de su fila en la anterior, `cantidad` 0, `linea_anterior` = su `ide`
  en la anterior y `cantidad_anterior_cadena` = `cantidad_origen_cadena` = su `canoriori`. En `filas.dcapro` van
  también al final.
- `totales` (y `dca.totbas`) son los **del MES**, como en la v1.1: las arrastradas suman 0.
- `estado`: como en la v1.1. **`existente`** (la del contrato y mes con el mismo importe ± 0,05) sale antes de validar
  la anterior. Una proforma **a origen** del mismo contrato y mes con **otro** importe no da
  `proforma_del_mes_existente` sino el aviso `otra_del_mes` y sigue (otra cadena, o la certificación anterior del mismo
  mes); una **de mes** con otro importe, como en la v1.1 (error).
- A origen no se emite `contrato_a_origen` (su texto sería falso).

Forma abreviada (valores ilustrativos, no de una obra real):

```jsonc
// petición: la de §3 más
{"modo": "origen", "proforma_anterior": "PROF26/0xxxx",
 "lineas": [{"referencia_linea": "F09", "ctrpro_ide": 262990, "linea_anterior": 1350001, "cantidad": 620, "...": "..."},
            {"referencia_linea": "F23", "producto": "SM1004", "cantidad": 75.85, "...": "..."}]}
// 200 previsto
{"estado": "previsto", "...": "...",
 "cadena": {"anterior": {"cod": "PROF26/0xxxx", "ide": 2850001}, "primera_de_cadena": false,
            "importe_anterior_cadena": 2651.0, "importe_origen_cadena": 19675.28, "n_arrastradas": 3},
 "lineas": [
  {"indice": 0, "referencia_linea": "F09", "linea_anterior": 1350001, "arrastrada": false,
   "cantidad": 620.0, "cantidad_anterior_cadena": 241.0, "cantidad_origen_cadena": 861.0, "...": "..."},
  {"indice": 1, "referencia_linea": "F23", "linea_anterior": null, "arrastrada": false,
   "cantidad": 75.85, "cantidad_anterior_cadena": 0.0, "cantidad_origen_cadena": 75.85, "...": "..."},
  {"indice": 2, "referencia_linea": "F11", "linea_anterior": 1350002, "arrastrada": true,
   "cantidad": 0.0, "cantidad_anterior_cadena": 117.5, "cantidad_origen_cadena": 117.5, "...": "..."}]}
```

En Sigrid quedan: `dca.docoritip` 1 y `docoriide` = la anterior (0 en la primera); por línea continuada, `canorilin` =
su `linea_anterior` y `canoriori` = el de esa línea + `cantidad`; por línea nueva, `canorilin` 0 y `canoriori` =
`cantidad`; `canoriant` e `imporiant` 0. Las arrastradas son copia de su fila con `can`, `tot`, `ivacuo` y `prepma` 0 y
**solo como `dcapro`**: sin la `ctrprodes` ni el `mov` a 0 que pone el escritorio (no cambian servido, stock ni PMP;
decisión D6 de F-016, se comprueba en la UI).

## 4. Errores (400 con `details.codigo`) y avisos

**Orden a origen (v1.2).** En mes, los fallos de línea (`lineas_no_validas`) salen antes que las comprobaciones de la
hoja y de lo registrado. A origen se aplazan para darlos junto con los de `linea_anterior` en un solo
`lineas_no_validas`, así que antes salen, por este orden: `importe_mes_no_cuadra`/`hoja_descuadrada`,
`proforma_del_mes_existente`, `existente` (200, sin escribir), `anterior_no_valida` y `anterior_con_sucesora`. Por
ejemplo, una hoja a origen con una línea que no es del contrato y el mismo total que una proforma del mes ya registrada
recibe `existente`, no 400.

| Código | Tipo | Cuándo | Qué hace `proformas` (propuesta) |
|---|---|---|---|
| `contrato_no_resuelto` | error | Ningún contrato de la obra y el proveedor a la fecha, o una línea de contrato que no está en ninguno de los candidatos | Revisar proveedor; o `cod_contrato`, o `sin_contrato` |
| `contrato_no_encontrado` | error | `cod_contrato` que no está en la obra (o el contrato resuelto desaparece de Sigrid antes de grabar) | Revisar `cod_contrato`, o reenviar sin él para que la API lo resuelva |
| `contrato_ambiguo` | error | Varios candidatos que no deshacen las líneas: ninguna línea de contrato, o líneas que están en más de uno (mensaje con sus `cod`); o dos contratos de la obra con ese `cod_contrato` | La persona elige y reenvía con `cod_contrato` |
| `proveedor_no_encontrado` | error | Con contrato, su `ctr.entcif` está vacío en Sigrid; con `sin_contrato`, el CIF no tiene albarán anterior ni un `prv` vivo en la empresa de la obra | Revisar el CIF del contrato o del proveedor en Sigrid, o alta a mano |
| `hoja_de_varios_contratos` | error | Las líneas se reparten entre contratos (`details.reparto`) | Una petición por contrato, mismo `periodo` |
| `contrato_de_otro_proveedor` | error | `cod_contrato` de otro CIF | Revisar |
| `periodo_no_valido` | error | Mes futuro o `fecha_proforma` fuera del mes | Revisar |
| `importe_mes_no_cuadra`, `hoja_descuadrada` | error | La hoja no suma (MES o ORIGEN ≠ ANTERIOR + MES) | Revisar la lectura |
| `proforma_del_mes_existente` | error | Ya hay una del contrato y mes con otro importe (mensaje con su `cod`). A origen, solo si esa es **de mes** (una a origen da el aviso `otra_del_mes`) | La persona decide; `otra_del_mes` si es una segunda |
| `anterior_no_valida` | error | **v1.2**, a origen: `proforma_anterior` no es un único `tip 14` del contrato, no es a origen o es posterior a la fecha de la proforma (el mensaje dice cuál) | Releer las puntas (§2.3, consulta 1) y elegir otra, o `primera_de_cadena` |
| `anterior_con_sucesora` | error | **v1.2**, a origen: la anterior ya tiene sucesora en el contrato (mensaje con su `cod`), también si aparece entre la previa y la grabación | Releer las puntas y encadenar a la última; si la sucesora es otra hoja del mismo mes, la persona decide |
| `escritura_proformas_origen_deshabilitada` | error | **v1.2**: `commit:true` con `modo: "origen"` y `SIGRID_PROFORMA_ORIGEN_ENABLED` cerrada (se mira después de `escritura_proformas_deshabilitada`); la previa y la proforma de mes no la miran | No grabar a origen hasta que sigrid-api la abra; no reintentar en bucle |
| `lineas_no_validas` | error | Fallos por línea: `linea_no_es_del_contrato`, `producto_obligatorio`, `producto_no_permitido`, `linea_descuadrada`, `linea_ambigua` (solo respaldo), los de F-009 (`partida_*`…) y, a origen (**v1.2**), `linea_anterior_no_valida` (no es de la anterior, o es de otro `ctrpro`, o de contrato frente a sin vincular) | Recasar la línea o elegir el producto; `linea_anterior_no_valida`: releer las líneas de la anterior (§2.3, consulta 2) y recasar |
| `escritura_proformas_deshabilitada`, `referencia_no_permitida`, `demasiadas_lineas`, `base_de_datos_no_permitida`, `referencia_en_conflicto` | error | Configuración o reintento con otra proforma. A origen, `demasiadas_lineas` cuenta también las arrastradas | — (`demasiadas_lineas`: alta a mano) |
| Heredados de `sigrid/albaran`: `obra_no_encontrada`, `obra_de_empresa_no_permitida`, `obra_ambigua`, `usuario_no_valido`, `proveedor_ambiguo`, `retencion_no_soportada`, `almacen_de_obra_no_resuelto`, `estado_inicial_no_encontrado`, `colision_de_clave`, `filas_afectadas_inesperadas` | error | Con el sentido de F-009 y F-015 (`proveedor_ambiguo`, solo con `sin_contrato`) | Revisar `cod_obra` o `usu`; `colision_de_clave`, reenviar la misma petición; los demás, alta a mano |
| (sin `codigo`) | error | Cuerpo que no valida (también las combinaciones de la nota ³ de §2.1): 400 `Solicitud invalida.` con `details.validation` (F-012); cuerpo que no es JSON o lectura truncada: 400 con `details.type` `ValueError` | Revisar la petición |
| (500) | error | Inesperado | Reenviar la **misma** `referencia_externa`: la idempotencia dice si llegó a escribirse |
| `anterior_distinto_de_sigrid` | aviso | ANTERIOR (cabecera o línea) ≠ lo registrado | Informativo (bis, anulaciones) |
| `supera_contrato` | aviso | El origen supera el importe del contrato | Avisar de preparar una ampliación |
| `supera_contrato_10` | aviso | Lo supera en más del 10 % | Frenar la aprobación; la factura no se podrá aprobar (`facturas` o F-008) |
| `contrato_a_origen` | aviso | Proforma **de mes** en un contrato que ya tiene proformas a origen (a origen no sale) | Informativo; si el jefe de obra quería a origen, reenviar con `modo: "origen"` |
| `otra_del_mes` | aviso | Segunda proforma del mes, pedida con `otra_del_mes`; a origen (**v1.2**), también sin pedirla si la otra del mes es a origen con otro importe | Informativo; a origen, comprobar que la anterior elegida es la buena |
| `linea_nueva_ya_en_la_anterior` | aviso | **v1.2**, a origen: una línea de contrato va como nueva y su `ctrpro` ya está en la anterior (`lineas_anterior` con sus `dcapro.ide`) | Casi siempre un olvido: reenviar con su `linea_anterior`, o confirmar que va nueva |
| `precio_distinto_del_contrato`, `supera_pendiente`, `retencion_del_contrato`, `cabecera_sin_dato` | aviso | Los de `sigrid/albaran` | Informativos |
| `dto_distinto_del_contrato` | aviso | **v1.3**, heredado de `sigrid/albaran` (línea con un `dto` pedido distinto del del `ctrpro`). En la proforma **hoy no sale**: la petición no admite `dto` (§2.2) | Mapearlo como informativo si el conjunto de avisos es cerrado |

**v1.3 · `existente` y lo registrado.** `existente` (±0,05 sobre el total del documento) y `anterior_distinto_de_sigrid`
comparan con el `totbas` **registrado**, que en las líneas con descuento del contrato sigue la regla de Sigrid (§3).
Con más de unas cinco de esas líneas, una hoja **reenviada con otra `referencia_externa`** puede no reconocerse: de mes
daría `proforma_del_mes_existente` (sin escribir) y a origen el aviso `otra_del_mes` y un alta en una cadena paralela.
Con la misma referencia sale `idempotente`: reenviad siempre con ella. La tolerancia no cambia.

## 5. Productos y líneas del contrato: sin endpoint nuevo (como albaranes)

- La API lee `SIGRID_PROFORMA_PRODUCTOS_SIN_CONTRATO` (productos admitidos en líneas nuevas además de los del
  contrato). `proformas` tiene **su propia App Setting** con la lista que ofrece en la bandeja, que **debe estar
  contenida** en la de la API (si no, `producto_no_permitido`).
- Las líneas del contrato (`ctrpro`: `ide`, partida, medición, unidad, precio, producto) y las descripciones de los
  productos las lee `proformas` por `sql/read`, con `?` y comprobando `truncated`.

## 6. Lo que lee `facturas`

`facturas` no llama a este endpoint: solo **lee** lo registrado por `sql/read`. El contrato de lectura entre
`proformas` y `facturas` es el `dca.entref` `PROF<MMAA>_<cod_obra>` (R12) del albarán `tip 14` del contrato; la serie
puede ser `PROF<aa>/` (lo que escribe F-007) o `AC<aa>/` (las de hoy). Se declara en `azure-apps/` (R36).

**A origen (v1.2, F-016).** Lo que la API expone para `facturas` no cambia, pero una proforma a origen
(`dca.docoritip` 1) lee distinto: trae **todas** las líneas de la cadena, y las arrastradas llevan `can` 0 (también
`tot` 0); su `entref` es el mismo `PROF<MMAA>_<obra>` y `dca.totbas` sigue siendo **el MES**. Solo pasan a factura las
líneas con `can` ≠ 0. Las columnas a origen (`canoriori`, `canorilin`) no hay que sumarlas al facturar el mes. Al
facturar una proforma a origen, el escritorio pone `canoriant`/`imporiant` en la `dcfpro`: si `facturas` llega a
registrar facturas (F-008 de sigrid-api), eso es de esa feature, no de esta.

**Líneas con descuento del contrato (v1.3, F-018).** Las líneas de contrato cuyo `ctrpro` tiene descuento se leen como
las que deja el escritorio: `tar` es el unitario **bruto**, `dto` el porcentaje en texto (`"1%"`, `"1,5%"`), `pre` el
unitario **neto** (`tot`/`can`) y `tot` el importe neto de la línea; `dca.impbru` es el bruto y `dca.totbas` el neto.
El importe de la línea es `tot`; `can`·`tar` es el bruto, no el importe.

## 7. Lo que la API no hace y preguntas para `proformas`

No hace: leer el xlsx o el pdf; casar partidas ni elegir producto por defecto; decidir qué hoja se registra ni quién
la aprueba; avisar por correo; bloquear la aprobación o la factura; escribir observaciones, «Nº ORDEN» o «IMPORTE
TOTAL» en Sigrid; varias proformas por petición; modificar o anular (se anula desde la UI).

A origen (v1.2) tampoco: elegir el modo, la anterior ni qué línea continúa cada una, ni leer para ello los importes de
Sigrid (§2.3, es de `proformas`); deducir la anterior de la hoja; comparar la hoja con la cadena (más allá de lo de la
v1.1); proformas a origen sin contrato o con la anterior en otro contrato; sembrar el origen con los meses que se
registraron de mes; escribir la `ctrprodes` y el `mov` a 0 de las arrastradas.

Preguntas: las de `design.md` §Preguntas para `proformas` (CIF o nombre; solo MES ≠ 0; avisos que bloquean).

## 8. Cambios desde el borrador v0.1

Lo que la implementación fijó y el borrador no decía (detalle en `progress/impl_F-007.md`, §Desviaciones):

- `periodo` y `fecha_proforma` son **enteros** (como `fecha_albaran` de `sigrid/albaran`); el ejemplo de §3 lo
  escribía como texto, que da 400.
- El CIF manda sobre el nombre al resolver el contrato (§2.1).
- Cuándo es `contrato_no_resuelto` y cuándo `contrato_ambiguo` con varios candidatos (§4); el respaldo sin
  `ctrpro_ide` (nota ² de §2.2).
- Sin contrato no hay comprobaciones de la hoja ni `existente` (§2.1).
- Forma de `existente` y de `idempotente` (§3), y los 400 sin `codigo` y el 500 (§4).

**v1.1 (2026-10-26)**, enmienda 1 de la spec tras la primera revisión: respaldo sin `ctrpro_ide` estricto por partida
y precio (nota ² de §2.2; antes, partida → medición → unidad → precio relajando filtros), y la misma regla al decidir
entre contratos; `otra_del_mes` se salta también la `existente` del mismo importe (§2.1); bajo el applock, una fila con
la misma `referencia_externa` de otro contrato o que no es proforma da `referencia_en_conflicto` (§4); el IVA de una
línea nueva con producto del contrato sale de su `ctrpro` también si ese producto nunca ha salido en un albarán (§3).
Tras la segunda revisión (2026-10-26), §4 recoge `contrato_no_encontrado` (también en §2.1), `proveedor_no_encontrado`
(con contrato, un `ctr.entcif` vacío) y los heredados de `sigrid/albaran` que la ruta puede devolver.

**v1.2 (2026-10-28), F-016 (proforma a origen), compatible hacia atrás**: sin `modo` o con `"mes"`, la v1.1 sin
cambios y sin ninguna clave nueva en la respuesta. Nuevo: `modo`, `proforma_anterior` y `primera_de_cadena` en la
cabecera y `linea_anterior` en la línea (§2.1, §2.2 y su nota ³); §2.3 con las dos consultas `sql/read` que hace
`proformas` (puntas del contrato y líneas de la punta) y lo que comprueba la API; §3.1, la respuesta a origen (`cadena`,
cuatro campos por línea, las arrastradas detrás, `totales` del MES) y el sentido de `otra_del_mes` a origen; §4, los
códigos `anterior_no_valida`, `anterior_con_sucesora`, `escritura_proformas_origen_deshabilitada` (App Setting nueva
`SIGRID_PROFORMA_ORIGEN_ENABLED`, desplegada `false`), `linea_anterior_no_valida` y el aviso
`linea_nueva_ya_en_la_anterior`, y `demasiadas_lineas` contando las arrastradas; §6, lo que lee `facturas` de una
proforma a origen. `contrato_a_origen` sale solo en la proforma de mes. Desplegada el 2026-10-28 (antes decía
«pendiente de revisión y de despliegue»; corregido el 2026-10-29).

**v1.3 (2026-10-29), F-018 (descuento por línea), compatible hacia atrás salvo las líneas de contrato cuyo `ctrpro`
tiene descuento**: la petición no cambia y sigue sin `dto` (§2.2). Esas líneas, de mes y a origen, se escriben como
Sigrid: `tar` y `dto` del contrato, `tot` = ROUND_HALF_UP(`cantidad`·`tar`·(1 − d/100), 2), `pre` = `tot`/`cantidad`,
`impbru` bruto y `totales` sobre esos `tot`, con hasta un céntimo por línea frente a `importe_mes` (§3); su línea de
respuesta trae `dto` y `precio_bruto`, también en la de mes (§3.1); a origen, `importe_origen_cadena` con ese `pre`,
con una diferencia que crece con `canoriori`/`cantidad` (§3.1). **Pendiente de despliegue**; acusada por `proformas` el
2026-10-29. **Corrección de texto** (2026-10-29, tras la revisión de F-018; sin cambio de versión ni de lo que hace la
API): el estado y la cota a origen, que antes decía «hasta un céntimo».
`existente`, `idempotente` y las arrastradas, sin las claves nuevas. §4: el aviso heredado
`dto_distinto_del_contrato` (hoy no sale en la proforma) y el efecto en `existente` de reenviar con otra referencia.
§6: cómo lee `facturas` esas líneas.
