<!-- progress/spec_F-007_enmienda2.md -->
# F-007 · Enmienda 2 de documentación (tras la pasada 2 de revisión), 2026-10-26

Solo documentación: ni código ni tests. Origen: `review_F-007_proforma_p2.md` (N1, O8), `review_F-007_C_p2.md`
(N1-N4) y `review_F-007_nucleo_mutacion_p2.md` (cambios 1-3). Todo comprobado contra el código de HEAD `30ca6b0`.

## Qué cambió

1. **`contrato_proformas.md`** (sigue en v1.1): §2.1 `cod_contrato` dice `contrato_no_encontrado`. §4 gana tres filas:
   `contrato_no_encontrado` (`contrato_pedido`, `proforma_statements.py:270`; y el contrato que desaparece antes de
   grabar, `create_proforma_use_case.py:386`), `proveedor_no_encontrado` (`traducir`, `proforma_statements.py:685-690`;
   y `sin_contrato` sin respaldo ni `prv` vivo, núcleo `:494-498`) y una de heredados de `sigrid/albaran` que la ruta
   puede devolver (`obra_*`, `usuario_no_valido`, `proveedor_ambiguo`, `retencion_no_soportada`,
   `almacen_de_obra_no_resuelto`, `estado_inicial_no_encontrado`, `colision_de_clave`, `filas_afectadas_inesperadas`).
   `base_de_datos_no_permitida` va con los de configuración y `contrato_ambiguo` cubre también dos contratos con el
   mismo `cod_contrato` (`proforma_statements.py:272-275`). No salen nunca: `peticion_mixta` y
   `escritura_albaranes_deshabilitada`. §8: línea fechada el 2026-10-26.
2. **`design.md`** (249/250): la línea de `locate_contract` dice ahora que la subclase carga el contrato por su `ide`
   con `_cargar_contrato` y recoge O8 (con contrato, `entcif` vacío → `proveedor_no_encontrado`). Costura 1 con
   `PerfilAlta.documentos`; costura 3 con los dos ganchos (`_comprobar_dentro(cursor, request, cabecera, existente)`
   antes de la salida idempotente y `_cargar_contrato(request, ctride)`), así que siguen siendo cinco y cuadra D12;
   costura 4 con el IVA de la primera línea por `pos` (N7, `setdefault` en el núcleo `:1325`); la subclase sobrescribe
   también `_resolver_contrato`; tabla de ficheros al día. Compactados D5, D8 y D10 sin quitar contenido.
3. **`verificacion_manual.md`**: N1, D2 es una orden literal con `<app>` que teclea el humano tras `!` (bash), sin
   variables de PowerShell; la nota de PowerShell 5.1 exceptúa D2. N2, V1 espera el texto de `function_app.py:355-356`.
   También los opcionales N3 (`Lineas` con `dcapro_ide`, `linoriide`, `importe`) y N4 (`COUNT` de `dcarec` tras anular).
4. **`progress/mutacion_F-007.md`**: §1 «aceptado por el humano el 2026-10-26»; A3 `:137`, A5 `:331` (el `if`),
   S2 `:168` y S3 `:254`, comprobados con `grep -n`.
5. **Aviso a `proformas`** (`impl_F-007.md`, 176/220): sin `partida` no casa ninguna, y ninguna da
   `linea_no_es_del_contrato`; los dos códigos nuevos de §4 y la fila de heredados.

## Verificación

`bash harness/init.sh` en verde al empezar y al terminar (topes: requirements 150/150 sin tocar, design 249/250).

## Para el humano

- El aviso a `proformas` sigue sin enviarse: lo manda el líder.
- `azure-apps/sigrid_api.md` §8.10 ya nombraba `proveedor_no_encontrado`; no lo he tocado.
