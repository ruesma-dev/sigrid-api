<!-- specs/F-007-registrar-proforma/contrato_facturas.md -->
# Contrato facturas ↔ sigrid-api · registro de la proforma del jefe de obra

**F-007 de sigrid-api (`POST /api/sigrid/proforma`) ↔ F-063 de facturas.** **Borrador v0** (2026-10-25), escrito con la
spec v3 de F-007: pendiente de la PARADA 1 del humano y de la respuesta de facturas (§6). Plantilla de hoja propuesta
para los jefes de obra: [`plantilla_hoja.md`](plantilla_hoja.md).

**Dueño**: sigrid-api (expone el endpoint). Facturas lo consume y **no lo copia**: enlaza aquí. Si este documento y la
spec de F-007 discrepan, manda la spec. Como con albaranes: las reglas, la validación y los códigos los cambia
sigrid-api; facturas edita solo lo que consume (de dónde saca cada campo y cómo mapea cada código).

## 1. Flujo

1. El administrativo recibe la hoja del jefe de obra (xlsx o pdf) y la lanza a la app. **La app la lee** (eso es suyo)
   y arma la petición de §2: una por hoja y mes, y una por contrato si la hoja abarca dos (§4, `hoja_de_varios_contratos`).
2. **Previa** (`commit:false`): la API resuelve contrato y líneas, valida y devuelve lo que escribiría, sin escribir.
3. El humano de la app revisa el **contrato resuelto** (`contrato.resuelto_por`, `candidatos`), las líneas (`de_contrato`,
   `ctrpro_ide`) y los **avisos**. Si el contrato o una línea no es el bueno, reenvía con `cod_contrato` o `ctrpro_ide`.
4. **Grabación** (`commit:true`): la misma petición. Repetirla da `idempotente`.

Una proforma de mes se escribe como un albarán de compra de la serie `PROF<aa>/` (`cla 141`) con solo las partidas de
MES ≠ 0; las de contrato, vinculadas a su línea de contrato («documento origen»). El origen no se escribe: lo calcula
la API sumando las proformas del contrato.

## 2. Petición

### 2.1. Cabecera

| Campo | Tipo | Oblig. | De la hoja | Qué hace la API |
|---|---|---|---|---|
| `database` | texto | sí | — | `ruesma` |
| `usu` | texto ≤24 | sí | — | `dbo.usu.cod` de quien registra (traza `log`) |
| `referencia_externa` | texto 1-128 | sí | — | Clave de idempotencia (`dca.synckey`); prefijo propuesto `PRF-` |
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
| `su_referencia` | texto ≤128 | no | — | `dca.entref`; por defecto `PROF<MMAA>_<obra>` |
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
| `partida` | texto | no² | Partida | Identifica la línea de contrato y es la partida por defecto |
| `medicion_contrato` | número | no² | Medición de Contrato | > 0 ⇒ **de contrato**; vacía o 0 ⇒ sin contrato |
| `unidad` | texto ≤8 | no | UD. | Desempate y `dcapro.unimed` |
| `cantidad_anterior`, `cantidad_origen` | número | no | MEDICIÓN · ANTERIOR / ORIGEN | ORIGEN = ANTERIOR + MES (error); ANTERIOR frente a Sigrid (aviso) |
| `ctrpro_ide` | entero | no | — | Fija la línea de contrato (salta el embudo) |
| `producto` | texto | no | — | Sin contrato: de la lista de la API o del contrato; por defecto, el único del contrato |
| `partida_imputacion` | texto | no | — | Otra partida que la de la línea de contrato |

² Una línea de contrato necesita `ctrpro_ide` o `partida` + `medicion_contrato`.

**Cómo identifica la API la línea de contrato** (sin `ctrpro_ide`): entre las del contrato, las de esa partida; si hay
varias, las de esa medición de contrato; después la unidad; y el precio como desempate (96,8 % única y correcta en las
proformas de 2026).

## 3. Respuesta

200 con la forma del modo extendido de `sigrid/albaran` (`estado`, `cod`, `con_ide`, `totales` con `tot`, `retenciones`,
`avisos[]`, `lineas[]`, `filas`) y además:

- `estado`: `previsto` (previa), `creado`, `idempotente` (misma `referencia_externa`) o **`existente`** (ya hay una
  proforma de ese contrato y mes con el mismo importe: la devuelve y **no escribe**).
- `contrato`: `cod`, `ide`, `resuelto_por` (`peticion`, `proveedor` o `lineas`) y `candidatos` (sus `cod`).
- `origen`: `importe_anterior_sigrid`, `importe_mes`, `importe_origen`, `importe_contrato`, `porcentaje_contrato`.
- Por línea: `de_contrato`, `ctrpro_ide`, `cantidad_anterior_sigrid`.

Ejemplo (hoja de agosto de `CTSB26/0472`, obra 0719, en `docs/referencia/proforma_ejemplo_bau_siglo_xxi.md`; dos de
sus seis líneas y BERENJENO): la proforma ya existe en Sigrid (`AC26/25548`, M29), así que la previa da `existente`.

```jsonc
// POST /api/sigrid/proforma
{"database": "ruesma", "usu": "<login>", "referencia_externa": "PRF-<id de la app>", "cod_obra": "0719",
 "periodo": "202608", "nombre_proveedor": "BAU SIGLO XXI", "numero_orden": 2,
 "importe_mes": 17024.28, "importe_anterior": 2651.00, "importe_origen": 19675.28,
 "lineas": [
  {"referencia_linea": "F09", "partida": "02.03.02.01", "medicion_contrato": 403.058, "unidad": "M3",
   "descripcion": "VERTIDO HORMIGON CIMENTACION LIMPIEZA", "cantidad": 620, "cantidad_anterior": 241,
   "cantidad_origen": 861, "precio": 11},
  {"referencia_linea": "F15", "partida": "02.03.03.06", "medicion_contrato": 37.22, "unidad": "M3",
   "descripcion": "VERTIDO HORMIGON MUROS", "cantidad": 38.57, "cantidad_origen": 38.57, "precio": 10},
  {"referencia_linea": "F23", "partida": "02.20.02.02.11", "medicion_contrato": 0, "unidad": "M2",
   "descripcion": "BERENJENO", "cantidad": 75.85, "precio": 3.5}],
 "commit": false}
// 200
{"estado": "existente", "cod": "AC26/25548", "con_ide": 2831541, "committed": false,
 "contrato": {"cod": "CTSB26/0472", "ide": 2793879, "resuelto_por": "proveedor", "candidatos": ["CTSB26/0472"]},
 "origen": {"importe_anterior_sigrid": 2651.0, "importe_mes": 17024.28, "importe_origen": 19675.28,
            "importe_contrato": 64897.38, "porcentaje_contrato": 30.3}, "avisos": []}
```

Con `otra_del_mes: true` la previa daría `previsto`: F09 y F15 vinculadas a los `ctrpro` 262990 y 262996 (F15 con
el aviso `supera_pendiente`: 38,57 frente a 37,22 de contrato), BERENJENO sin vincular con el único producto del
contrato, y la retención del contrato.

## 4. Errores (400 con `details.codigo`) y avisos

| Código | Tipo | Cuándo | Qué hace la app (propuesta) |
|---|---|---|---|
| `contrato_no_resuelto` | error | Ningún contrato de la obra y el proveedor a la fecha | Revisar proveedor; o `cod_contrato`, o `sin_contrato` |
| `contrato_ambiguo` | error | Varios candidatos que no deshacen las líneas (mensaje con sus `cod`) | El humano elige y reenvía con `cod_contrato` |
| `hoja_de_varios_contratos` | error | Las líneas se reparten entre contratos (`details.reparto`) | Una petición por contrato |
| `contrato_de_otro_proveedor` | error | `cod_contrato` de otro CIF | Revisar |
| `periodo_no_valido` | error | Mes futuro o `fecha_proforma` fuera del mes | Revisar |
| `importe_mes_no_cuadra`, `hoja_descuadrada` | error | La hoja no suma (MES o ORIGEN ≠ ANTERIOR + MES) | `LECTURA_DESCUADRADA` |
| `proforma_del_mes_existente` | error | Ya hay una del mes con otro importe (mensaje con su `cod`) | El humano decide; `otra_del_mes` si es una segunda |
| `lineas_no_validas` | error | Fallos por línea: `linea_ambigua` (con `candidatos`), `linea_no_es_del_contrato`, `producto_obligatorio`, `linea_descuadrada` y los de F-009 (`partida_*`, `producto_no_permitido`…) | Corregir la línea o fijar `ctrpro_ide`/`producto` |
| `escritura_proformas_deshabilitada`, `referencia_no_permitida`, `demasiadas_lineas`, `referencia_en_conflicto` | error | Configuración o reintento con otra proforma | — |
| `anterior_distinto_de_sigrid` | aviso | ANTERIOR (cabecera o línea) ≠ lo registrado | Informativo (bis, anulaciones) |
| `supera_contrato` | aviso | El origen supera el importe del contrato | Avisar de preparar una ampliación |
| `supera_contrato_10` | aviso | Lo supera en más del 10 % | **La factura no se podrá aprobar** (lo bloquea facturas o F-008) |
| `contrato_a_origen` | aviso | El contrato ya tiene proformas a origen | Informativo; Administración decide |
| `otra_del_mes` | aviso | Segunda proforma del mes, pedida con `otra_del_mes` | Informativo |
| `precio_distinto_del_contrato`, `supera_pendiente`, `retencion_del_contrato`, `cabecera_sin_dato` | aviso | Los de `sigrid/albaran` | Informativos |

## 5. Lo que la API no hace

Leer el xlsx o el pdf; decidir qué hoja se registra ni quién la aprueba; avisar por correo; bloquear la factura;
escribir observaciones, «Nº ORDEN» o «IMPORTE TOTAL» en Sigrid; proformas a origen; varias proformas por petición;
modificar o anular (se anula desde la UI de Sigrid).

## 6. Preguntas para facturas

Las de `design.md` §Preguntas para facturas: CIF o nombre; medición de contrato; solo MES ≠ 0; una petición por
contrato; `usu`, prefijo y avisos bloqueantes; producto de las partidas sin contrato.
