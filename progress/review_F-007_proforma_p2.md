<!-- progress/review_F-007_proforma_p2.md -->
Revisión incremental desde fe85523 (pasada 2), bloque proforma (conducta funcional), sobre HEAD `765f273`

# F-007 · Revisión funcional acotada (proforma), pasada 2

- **Veredicto del bloque:** CHANGES_REQUESTED, **solo por documentación** (N1: la tabla §4 del contrato v1.1 no recoge
  dos códigos que la API devuelve a `proformas`). El código corrige D1-D5 y O4 y cumple R8, R14, R17 y R28 de la v3.1.
  La pasada 3 de este bloque puede limitarse al diff de `contrato_proformas.md`. El veredicto de la feature lo da el
  informe consolidado del líder.
- **Nivel de rigor:** `critico` (el declarado). Delta revisado: `32ad8b4..765f273` (código: núcleo, caso de uso,
  `proforma_statements.py` y tests `test_f007_*`), contra requirements/design v3.1, contrato v1.1 y la enmienda 1.
- **Ejecutado:** `python -m pytest tests/test_f007_*.py -q -p no:cacheprovider` → **512 passed** en 8,46 s. Ni
  `init.sh` ni `harness.mutacion` (encargo). Sondas sobre los dobles en
  el scratchpad (`p2/sonda_*.py`) y las cuatro de la pasada 1 repetidas, sin escribir en el árbol y sin tocar Sigrid.

## Hallazgos de la pasada 1

| # | Hallazgo | Estado | Evidencia |
|---|---|---|---|
| D1 | R17: sin plantilla, IVA 0 | **Corregido** | `_de_la_plantilla_del_contrato` (núcleo `:1589-1592`) deja natide/cueide/caaide a 0 y lleva el `ivaide` del `ctrpro` a la fila. Sonda de la hoja 0472 por `sigrid/proforma` sin L8b ni L8: BERENJENO `(610004, 0, 0, 0, ivaide 3, ivacuo 55.75)`, `dca` totbas/totiva/totdoc 17024.28/3575.1/20599.38, **idénticos** a la variante con plantilla. Aviso: «cuenta a 0 e IVA de su linea de contrato». El albarán sigue con IVA 0 y su texto de siempre (`test_f007_perfil.py:191`, `:474-480`) |
| D2 | R28 sin R23 bajo el applock | **Corregido** | El gancho recibe la fila de E1 **antes** de la salida idempotente (núcleo `:740-743`); la proforma relee LP5 por el cursor y solo deja pasar UNA fila `cla 141` del contrato resuelto (`create_proforma_use_case.py:409-415`). Otro contrato, otra clase, dos filas o ninguna → `referencia_en_conflicto` sin escribir (`test_f007_transaccion.py:151-169`, 4 casos). L11 y LP5 tienen el mismo `WHERE` (`tip` + `synckey`) |
| D3 | Idempotente de dentro con `origen` y avisos | **Corregido** | Sonda: `estado idempotente`, `origen` `null`, `avisos` `[]` aunque la hoja dé `anterior_distinto_de_sigrid` fuera; el JSON coincide clave a clave con el de la idempotente de fuera (solo difiere `dry_run`) |
| D4 | Línea con `producto` + `medicion_contrato` vinculada en silencio | **Corregido** (por la enmienda) | Sonda de la pasada 1 repetida: `linea_no_es_del_contrato`, en una línea (`revisar_lineas`) y en R8 (`_contiene` → `False`) |
| D5 | Hora de Madrid sin test | **Corregido** | `test_f007_use_case.py:554-583`: 22:30 y 21:30 UTC del 31-08 y cambio de año (`202612` → `PROF26/`, `20261231`; `202701` → `PROF27/`). Sondas de la pasada 1, mismos resultados |
| O3 | `otra_del_mes` y la del mismo total | **Cerrada por la spec** | R24 v3.1 lo dice; `test_f007_use_case.py:586` |
| O4 | `entcif` con espacios o vacío | **Corregido** | La proforma carga el contrato resuelto por su `ide` (`_cargar_contrato`, sin relocalizar por CIF); `traducir` normaliza `ctr.entcif` y, vacío, `proveedor_no_encontrado` antes de la transacción (`proforma_statements.py:682-691`; tests `test_f007_use_case.py:393-418`) |
| O1, O2, O5, O6 | Observaciones | Sin cambio | No las tocó la enmienda; siguen siendo decisión del humano |

## Los puntos del encargo

1. **D1-D5 y O4:** ver tabla. La sonda D4 da ahora `linea_no_es_del_contrato`.
2. **R8 y R14:** `_por_partida_y_precio` (`proforma_statements.py:285-297`) filtra por código de partida **y**
   |pre − precio| ≤ 0,0001 en `Decimal`, sin vuelta atrás. Sondas: dos de la misma partida y precio → `linea_ambigua`
   `[1, 4]`; partida que casa y precio 11 frente a 10/12 → `linea_no_es_del_contrato`; precio que casa y partida
   ausente → ídem; sin `partida` → ídem; 12,0001 casa y 12,00011 no; medición 55 y unidad `KG` distintas no impiden
   casar; `producto` con `medicion_contrato` > 0 no cuenta. `_contiene` usa la misma función. R8 con dos contratos:
   precio solo de A → A (`lineas`); dos líneas de B que casan → B (y después `linea_ambigua` dentro de B); ninguno →
   `contrato_no_resuelto`; reparto → `hoja_de_varios_contratos` `{F1: A, F2: B}`. Todo conforme a R8, R9 y R14.
3. **R17:** conforme (D1). Además, N7: con el producto en dos `ctrpro`, manda el primero por `pos` (`test_f007_perfil.py:412`).
4. **R28:** conforme (D2, D3). Sin contrato, `es_proforma` exige `cla 141` y `ctride` 0
   (`test_f007_transaccion.py:172`). Si E1 encuentra una fila de otro proveedor u obra, el núcleo responde
   `referencia_en_conflicto` antes del gancho, como antes.
5. **Llave cerrada:** el caso de uso dice «Escritura de proformas desactivada: hacen falta SIGRID_DOMAIN_WRITE_ENABLED,
   SIGRID_PROFORMA_WRITE_ENABLED y credenciales de escritura.» (`test_f007_use_case.py:536`). El del albarán no cambia.
   La ruta (`function_app.py:349-357`, R5) ya hablaba de proformas.
6. **Forma §3/§4:** `idempotente` cumple §3 («viene el contrato y `origen` es nulo»). `existente` y `previsto`, sin
   cambios desde la pasada 1. **`proveedor_no_encontrado` para `entcif` vacío:** el código es coherente con su sentido
   (ya lo da `sin_contrato` sin `prv` por CIF, F-015 R7) y está en el conjunto heredado que permite design §Códigos.
   Pero **no está en la tabla §4**, que es lo que `proformas` mapea, y ya lo anuncian el aviso y `azure-apps`
   §8.10: hay que añadirlo (N1).
7. **Aviso a `proformas`** (`impl_F-007.md:58-76`): describe bien los cambios de la v1.1: R14 por partida y precio,
   `linea_ambigua` con `candidatos` y desempate por descripción, la misma regla entre contratos, `otra_del_mes`,
   idempotente con `origen` nulo, conflicto bajo el applock, IVA del `ctrpro`, `proveedor_no_encontrado` y el mensaje
   de la llave. Le falta decir que **sin `partida` no casa ninguna** y que **ninguna → `linea_no_es_del_contrato`**
   (nota ² de §2.2). No obliga a cambiar nada, porque `proformas` no usa el respaldo. Al cerrar N1, el aviso y §4 quedan
   de acuerdo.

## Defectos nuevos (cambios requeridos)

1. **N1 · `contrato_proformas.md` §4 (líneas 131-149) no recoge `proveedor_no_encontrado` ni `contrato_no_encontrado`**
   (baja; solo documentación). Escenarios: (a) contrato resuelto con `ctr.entcif` vacío → 400
   `proveedor_no_encontrado` (`proforma_statements.py:685-691`); también `sin_contrato` con un CIF sin `prv` vivo
   (F-015 R7). (b) `cod_contrato` que no está en la obra → `contrato_no_encontrado` (R7; falta desde la v1, y la fila
   `cod_contrato` de §2.1, línea 44, tampoco lo dice). La spec manda sobre el contrato. Aun así, §4 es la tabla de
   códigos que `proformas` traduce, y un código fuera de ella le llega sin acción definida. Arreglo: una fila por
   cada uno, con su «Cuándo» y la acción («revisar el CIF del contrato en Sigrid o alta a mano»; «revisar
   `cod_contrato`»), o una fila de heredados de `sigrid/albaran` que los nombre (`obra_*`, `usuario_no_valido`,
   `proveedor_*`, `contrato_no_encontrado`…), y su línea en §8.

## Observaciones (sin cambio obligatorio)

- **O7.** Si E1 encuentra la referencia en un documento de otro proveedor u obra, el mensaje de la proforma sigue
  diciendo «albaran(es) de otro proveedor u obra» (`create_albaran_compra_use_case.py:660-664`). El código es el
  correcto. Es el mismo caso que el mensaje de la llave que se corrigió en T35.
- **O8.** `proveedor_no_encontrado` con contrato es una regla nueva que la spec no recoge: con contrato, el núcleo
  toma `entide` del `ctr` y solo usa el CIF en la traza. Es la decisión del líder y mejora el 400 sin `codigo`
  anterior. Si se quiere dejar escrita, basta una frase en R7 o en design §Códigos.

## Propuesta de automejora

Ninguna para el protocolo. Para la spec: cuando una corrección introduzca un código que `proformas` puede recibir, la
tarea que la implementa debería tocar a la vez §4 del contrato. Aquí se tocaron el aviso y `azure-apps`, pero no §4.
