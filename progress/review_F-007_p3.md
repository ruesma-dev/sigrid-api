<!-- progress/review_F-007_p3.md -->
Revisión incremental desde `30ca6b0` (pasada 3) · delta `30ca6b0..0f053da` · solo documentación

# F-007 · Pasada 3 · enmienda 2 de documentación

**Veredicto de la pasada: APPROVED.** La enmienda 2 cierra los cinco cambios pendientes de la pasada 2 y cada
afirmación nueva casa con el código de `0f053da`. **Rigor:** `critico`. Nada contra Sigrid ni contra la API.

- **El diff no toca código ni tests**: `git diff --stat 30ca6b0..0f053da` → 6 ficheros, todos `.md`
  (`progress/{impl,mutacion,spec_..._enmienda2}`, `specs/F-007-*/{contrato_proformas,design,verificacion_manual}`).
  Lo aprobado en las pasadas 1 y 2 sigue valiendo: el código es el mismo.
- **`bash harness/init.sh`** (tal cual, exit 0): `3393 passed, 1 skipped` en 138 s; PUERTA COBERTURA `[OK]` 100,0 %
  de 736 líneas (umbral 80 %, critico); PUERTA TAMAÑO `[OK]` (requirements 150/150, design 249/250, impl 176/220);
  BACKLOG al día; avisos de siempre (F-015 `blocked`, ruff 79). `git status` limpio después.

## Lo que había que cerrar

| Origen | Estado | Comprobado contra el código |
|---|---|---|
| proforma_p2 **N1** (§4 del contrato) | **Cerrado** | Filas nuevas: `contrato_no_encontrado` (`proforma_statements.py:270`, `create_proforma_use_case.py:386`), `proveedor_no_encontrado` (`proforma_statements.py:689`; núcleo `:497`, solo sin contrato), `contrato_ambiguo` también por `cod` repetido (`:274`), `base_de_datos_no_permitida` (núcleo `:398`) y la fila de heredados. §2.1 `cod_contrato` y §8 al día |
| C_p2 **N1** (D2 con `!`) | **Cerrado** | D2 es `! func azure functionapp publish <app> --python`, sin `$env:`; la nota de PowerShell 5.1 exceptúa D2 |
| C_p2 **N2** (mensaje de V1) | **Cerrado** | Texto literal de `function_app.py:355-356` |
| C_p2 N3, N4 (opcionales) | Cerrados | `Lineas` con `dcapro_ide`, `linoriide`, `importe` (campos de `LineaProformaResultado`); `COUNT` de `dcarec` tras anular |
| nucleo_mutacion_p2 **1** (`design.md:105`) | **Cerrado** | Ahora: carga por `ide` con `_cargar_contrato` (`create_proforma_use_case.py:376-388`) y `entcif` vacío → `proveedor_no_encontrado` (O8) |
| nucleo_mutacion_p2 **2** (costuras) | **Cerrado** | `PerfilAlta.documentos` (núcleo `:142`, `"proformas"` en `:132` de la subclase); `_comprobar_dentro(cursor, request, cabecera, existente)` (`:859`), llamado en `:743` **antes** del `return` idempotente; `_cargar_contrato(request, ctride)` (`:629`), usado por `_resolver_contrato` de la base (`:620`). Las cuatro sobrescrituras citadas son las reales (`run`, `_resolver_contrato`, `_comprobar_dentro`, `_construir`; `_convertir` es propio, no sobrescribe). Siguen siendo cinco costuras |
| nucleo_mutacion_p2 **3** (N7, opcional) | Cerrado | Costura 4: «el de la primera por `pos`» = `setdefault` del núcleo `:1325` sobre `ctrpro` leído `order_by="pos"` |
| `mutacion_F-007.md` | Correcto | §1 «aceptado por el humano el 2026-10-26»; A3 `:137`, A5 `:331` (el `if`), S2 `:168`, S3 `:254`, comprobados con `sed -n` |
| Aviso a `proformas` (`impl_F-007.md`) | Correcto | «sin `partida` no casa ninguna» (`_por_partida_y_precio`, `if linea.partida is None: return []`), ninguna → `linea_no_es_del_contrato`, y los dos códigos nuevos de §4 |

## §4 frente al conjunto cerrado de la proforma

`CODIGOS_CABECERA_PROFORMA` tiene 28 códigos. §4 nombra 26. Los dos que faltan son justo los que la enmienda declara
que **no salen nunca**, y no salen:
- `peticion_mixta`: solo lo lanza el validador de `AlbaranCompraRequest` con `lineas_recibidas`, y `traducir` no
  lo rellena;
- `escritura_albaranes_deshabilitada`: `PERFIL_PROFORMA.codigo_llave` es `escritura_proformas_deshabilitada` y la
  ruta tiene su propia llave.

Cada heredado de la fila nueva tiene su `raise` en el núcleo, en el camino de la proforma: `obra_*` `:584-597`,
`usuario_no_valido` `:574`, `estado_inicial_no_encontrado` `:570`, `retencion_no_soportada` `:551`,
`proveedor_ambiguo` `:503` (solo `_proveedor_por_cif`, es decir, sin contrato), `filas_afectadas_inesperadas` `:826`,
`colision_de_clave` `:844` y `almacen_de_obra_no_resuelto` `:943`.

## D2 lanzado con `!` (Git Bash)

En Git Bash, `func` resuelve a `/c/Program Files/Microsoft/Azure Functions Core Tools/func` (v4.9.0). La misma orden,
con el nombre de la app en lugar de `<app>`, la lanzó el humano con `!` en F-010 y F-011 (`verificacion_F-010.md:11`:
exit 0, 9 funciones). Sin variables, no depende de la consola de PowerShell. **No he publicado nada.** Nota: si
alguien teclea `<app>` tal cual, bash lo toma como redirección y falla sin desplegar. El texto ya dice que hay que
sustituirlo.

## Cambios requeridos

Ninguno.
