<!-- specs/F-007-registrar-proforma/contrato_proformas.md -->
# Contrato proformas ↔ sigrid-api · registro de la proforma del jefe de obra

**F-007 de sigrid-api (`POST /api/sigrid/proforma`) ↔ F-005 del microservicio `proformas`.** **Borrador v0.1**
(2026-10-25), escrito con la spec v3 de F-007 y las decisiones del humano de ese día: pendiente de la PARADA 1 y de la
respuesta de `proformas` (§7). Traspaso de origen: `proformas/docs/referencia/01_traspaso_facturas.md`. Plantilla de
hoja propuesta para los jefes de obra: [`plantilla_hoja.md`](plantilla_hoja.md).

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

## 2. Petición

### 2.1. Cabecera

| Campo | Tipo | Oblig. | De la hoja | Qué hace la API |
|---|---|---|---|---|
| `database` | texto | sí | — | `ruesma` |
| `usu` | texto ≤24 | sí | — | `dbo.usu.cod` de **quien aprueba** en la bandeja (traza `log`) |
| `referencia_externa` | texto 1-128 | sí | — | `PRF-` + id de la proforma en `proformas`; clave de idempotencia (`dca.synckey`) |
| `cod_obra` | texto | sí | OBRA («719.…» → `0719`) | Obra de las empresas permitidas |
| `periodo` | `AAAAMM` | sí | MES («AGOSTO-26» → `202608`) | Mes de la proforma; fecha = último día si ya pasó |
| `importe_mes` | número | sí | TOTALES · IMPORTE MES | Debe ser Σ round(`cantidad`·`precio`, 2) ± 0,05 |
| `importe_anterior` | número | no | TOTALES · IMPORTE ANTERIOR | Se compara con lo registrado (aviso) |
| `importe_origen` | número | no | TOTALES · IMPORTE ORIGEN | Con el anterior: ORIGEN = ANTERIOR + MES (error si no) |
| `cod_contrato` | texto | no | Nº CONTRATO | Si viene, **manda** (así se cambia el resuelto) |
| `cif_proveedor` | texto | no¹ | — | Resuelve el contrato (`ctr.entcif`); obligatorio con `sin_contrato` |
| `nombre_proveedor` | texto ≤128 | no¹ | SUBCONTRATISTA | Resuelve el contrato por nombre normalizado en `ctr.entres` |
| `sin_contrato` | bool | no | Nº CONTRATO vacío | Alta sin contrato (todas las líneas sin vincular, sin retención) |
| `otra_del_mes` | bool | no | — | Permite una segunda proforma del mismo contrato y mes |
| `fecha_proforma` | `AAAAMMDD` | no | — | Debe caer en `periodo` |
| `su_referencia` | texto ≤128 | no | — | `dca.entref`; por defecto `PROF<MMAA>_<obra>` (§6) |
| `numero_orden` | entero | no | Nº ORDEN | Solo traza (es el ordinal mensual, no se valida) |
| `commit` | bool | no | — | `false` por defecto |

¹ Hace falta `cod_contrato`, `cif_proveedor` o `nombre_proveedor`.

### 2.2. Línea (solo las partidas con MES ≠ 0)

| Campo | Tipo | Oblig. | De la hoja | Qué hace la API |
|---|---|---|---|---|
| `referencia_linea` | texto 1-24 | sí | (la fila) | `dcapro.refent`; única en la petición |
| `cantidad` | número ≠ 0 | sí | MEDICIÓN · MES | Cantidad de la línea (con signo) |
| `precio` | número | sí | P. unit. | Si difiere del contrato, aviso y se escribe el de la hoja |
| `descripcion` | texto ≤128 | sí | Trabajos realizados | `dcapro.res` |
| `ctrpro_ide` | entero | **sí en las de contrato**² | (casada en la bandeja) | Solo se comprueba que es del contrato resuelto; si no, `linea_no_es_del_contrato` (también si es de otro contrato de la obra). No se corrige ni se sustituye |
| `producto` | texto | **sí en las nuevas**² | (elegido en la bandeja) | De la lista de §5 o de los productos del contrato; sin él, `producto_obligatorio` |
| `partida` | texto | no | Partida | Partida de la línea nueva (si no, la de imputación) |
| `medicion_contrato` | número | no | Medición de Contrato | Solo para el respaldo sin `ctrpro_ide` |
| `unidad` | texto ≤8 | no | UD. | `dcapro.unimed` |
| `cantidad_anterior`, `cantidad_origen` | número | no | MEDICIÓN · ANTERIOR / ORIGEN | ORIGEN = ANTERIOR + MES (error); ANTERIOR frente a Sigrid (aviso) |
| `partida_imputacion` | texto | no | — | Otra partida que la de la línea de contrato |

² `ctrpro_ide` y `producto` no van juntos. La API admite, como respaldo para otro llamante, una línea de contrato sin
`ctrpro_ide` (la identifica por partida, medición de contrato, unidad y precio); `proformas` no lo usa.

## 3. Respuesta

200 con la forma del modo extendido de `sigrid/albaran` (`estado`, `cod`, `con_ide`, `totales` con `tot`, `retenciones`,
`avisos[]`, `lineas[]`, `filas`) y además:

- `estado`: `previsto` (previa), `creado`, `idempotente` (misma `referencia_externa`) o **`existente`**: ya hay una
  proforma **de ese contrato** y mes con el mismo importe (también una `AC` con `entref` `PROF…`); la devuelve, **no
  escribe** y trae por línea `dcapro_ide`, `linoriide`, `producto`, `cantidad`, `precio` e `importe`, en previa y con
  `commit`, para enlazarla sin otra lectura.
- `contrato`: `cod`, `ide`, `resuelto_por` (`peticion`, `proveedor` o `lineas`) y `candidatos` (sus `cod`).
- `origen`: `importe_anterior_sigrid`, `importe_mes`, `importe_origen`, `importe_contrato`, `porcentaje_contrato`.
- Por línea: `de_contrato`, `ctrpro_ide`, `cantidad_anterior_sigrid`.

Ejemplo (hoja de agosto de `CTSB26/0472`, obra 0719, en `docs/referencia/proforma_ejemplo_bau_siglo_xxi.md`; dos de
sus seis líneas y BERENJENO): la proforma ya existe en Sigrid (`AC26/25548`, M29), así que la previa da `existente`.

```jsonc
// POST /api/sigrid/proforma
{"database": "ruesma", "usu": "<login de quien aprueba>", "referencia_externa": "PRF-<id en proformas>",
 "cod_obra": "0719", "periodo": "202608", "nombre_proveedor": "BAU SIGLO XXI", "numero_orden": 2,
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

## 4. Errores (400 con `details.codigo`) y avisos

| Código | Tipo | Cuándo | Qué hace `proformas` (propuesta) |
|---|---|---|---|
| `contrato_no_resuelto` | error | Ningún contrato de la obra y el proveedor a la fecha | Revisar proveedor; o `cod_contrato`, o `sin_contrato` |
| `contrato_ambiguo` | error | Varios candidatos que no deshacen las líneas (mensaje con sus `cod`) | La persona elige y reenvía con `cod_contrato` |
| `hoja_de_varios_contratos` | error | Las líneas se reparten entre contratos (`details.reparto`) | Una petición por contrato, mismo `periodo` |
| `contrato_de_otro_proveedor` | error | `cod_contrato` de otro CIF | Revisar |
| `periodo_no_valido` | error | Mes futuro o `fecha_proforma` fuera del mes | Revisar |
| `importe_mes_no_cuadra`, `hoja_descuadrada` | error | La hoja no suma (MES o ORIGEN ≠ ANTERIOR + MES) | Revisar la lectura |
| `proforma_del_mes_existente` | error | Ya hay una del contrato y mes con otro importe (mensaje con su `cod`) | La persona decide; `otra_del_mes` si es una segunda |
| `lineas_no_validas` | error | Fallos por línea: `linea_no_es_del_contrato`, `producto_obligatorio`, `producto_no_permitido`, `linea_descuadrada`, `linea_ambigua` (solo respaldo) y los de F-009 (`partida_*`…) | Recasar la línea o elegir el producto |
| `escritura_proformas_deshabilitada`, `referencia_no_permitida`, `demasiadas_lineas`, `referencia_en_conflicto` | error | Configuración o reintento con otra proforma | — |
| `anterior_distinto_de_sigrid` | aviso | ANTERIOR (cabecera o línea) ≠ lo registrado | Informativo (bis, anulaciones) |
| `supera_contrato` | aviso | El origen supera el importe del contrato | Avisar de preparar una ampliación |
| `supera_contrato_10` | aviso | Lo supera en más del 10 % | Frenar la aprobación; la factura no se podrá aprobar (`facturas` o F-008) |
| `contrato_a_origen` | aviso | El contrato ya tiene proformas a origen | Informativo; Administración decide |
| `otra_del_mes` | aviso | Segunda proforma del mes, pedida con `otra_del_mes` | Informativo |
| `precio_distinto_del_contrato`, `supera_pendiente`, `retencion_del_contrato`, `cabecera_sin_dato` | aviso | Los de `sigrid/albaran` | Informativos |

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

## 7. Lo que la API no hace y preguntas para `proformas`

No hace: leer el xlsx o el pdf; casar partidas ni elegir producto por defecto; decidir qué hoja se registra ni quién
la aprueba; avisar por correo; bloquear la aprobación o la factura; escribir observaciones, «Nº ORDEN» o «IMPORTE
TOTAL» en Sigrid; proformas a origen; varias proformas por petición; modificar o anular (se anula desde la UI).

Preguntas: las de `design.md` §Preguntas para `proformas` (CIF o nombre; solo MES ≠ 0; avisos que bloquean).
