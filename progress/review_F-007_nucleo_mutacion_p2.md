<!-- progress/review_F-007_nucleo_mutacion_p2.md -->
Revisión incremental desde fe85523 (pasada 2) · bloque **núcleo de F-009 y mutación** · HEAD revisado `765f273`

# F-007 · Pasada 2 · núcleo y mutación

**Veredicto del bloque: CHANGES_REQUESTED, solo por documentación.** `design.md` no recoge dos costuras nuevas del
núcleo (`_cargar_contrato`, `PerfilAlta.documentos`) y en la línea 105 dice lo contrario de lo que hace el código. El
núcleo y la mutación están bien: **no hay que tocar código ni repetir la campaña**.

**Rigor:** `critico`. Sin `init.sh` ni campaña (prohibidos en el árbol compartido): pruebas en el worktree desechable
`../sigrid-api-rev007-p2` (`765f273`), ya borrado; `git status` limpio. Tras `765f273` solo entraron informes ajenos.

## 1 · Costuras del núcleo: la conducta del albarán no cambia

| Comprobación | Resultado |
|---|---|
| R31: `git diff dev -- tests/test_f009_* tests/test_f015_* tests/fixtures/f009_caracterizacion.json tests/f009_dobles.py infrastructure/` | **vacío** |
| `python -m pytest tests/test_f009_*.py tests/test_f015_*.py -q -p no:cacheprovider` | **816 passed** |
| Diferencial `dev` ↔ `765f273` (grabador de la pasada 1 sobre `CreateAlbaranCompraUseCase.run`: respuesta o excepción, lecturas, sentencias, applocks y log) | **279/279 idénticas**, salvo el test de reloj real `r22_…utc_con_zona` (`fechor`, `hor`, `tiemod`), como en la pasada 1 |

- **`_cargar_contrato(request, ctride)`** es una extracción literal del código de antes: `ctr` por `_fila_completa`,
  `None` si falta, y `ctrpro` por `pos`. El albarán sigue localizando por `locate_contract`, con los mismos errores.
  Mi mutante N15 (`order_by="pos"` → `"ide"`) muere en F-009.
- **`PerfilAlta.documentos`** vale `"albaranes"` por defecto y `PERFIL_ALBARAN` no lo fija, así que el mensaje de la
  llave es idéntico. Lo fijan `test_f007_r31_el_mensaje_de_la_llave_del_albaran_es_el_de_hoy` y el diferencial. Mi
  mutante N12 (defecto `"proformas"`) muere, aunque solo en `test_f007_perfil`: F-009 no afirma ese texto.
- **`_comprobar_dentro(..., existente)` antes de la salida idempotente**: en la base el cuerpo sigue vacío y no toca el
  cursor. Las 42 transacciones del diferencial son iguales. Mi mutante N11 (devolver el gancho a después del `return`
  idempotente) muere con 8 fallos.
- **IVA del `ctrpro` sin plantilla.** `_de_la_plantilla_del_contrato` solo corre con `linea.del_contrato`, que exige
  que `_del_contrato` tenga el producto. En el albarán (`productos_del_contrato=False`) `_del_contrato` es `{}`, así
  que **un albarán sin histórico sigue con `ivaide` 0 y el mensaje «cuenta e IVA a 0»**. Lo confirman 12 casos del
  diferencial, idénticos, y `test_f007_r17_el_albaran_sin_historico_sigue_con_iva_0`. N14 (invertir la condición del
  mensaje) y N16 (llamarla siempre; 16 fallos en `test_f009_use_case`) mueren.
- **RM6** (de `if contexto is None: return` y el `and` a dos `assert`). El único camino al núcleo con un
  `_AltaDeProforma` es `CreateProformaUseCase.run`, que fija `alta._contexto` en `create_proforma_use_case.py:259`
  justo antes de `self._ejecutar(alta)` (`:264`). No se pierde ninguna defensa: antes un contexto ausente se saltaba
  R28 en silencio; ahora falla. [x]

## 2 · `design.md` frente a lo implementado

O1 de la pasada 1 está **resuelto**: §Costuras 1-2 nombran `cifras_serie`, `campo_max_lineas`, `error` y
`siguiente_cod(..., cifras=)`. Pero T33 y T35 llegaron después de la v3.1 y no constan (ver «Cambios requeridos»).

## 3 · Mutación

- **RM1** [x]: midió `4a94da0`; desde entonces, en el alcance, solo cambian las guardas de T32 (G1-G4, abajo).
- **RM2** [x]: base 79,5 s, media 12,3 s; 381 × 12,3 = 4686 s frente a 4674 s: cuadra (con `-x` y 376/381 muertos).
- **Campaña no reejecutada: 78 min según el informe** (y el encargo lo prohíbe). La sustituye RM4, abajo.

Cómo se midió: `python -m pytest tests/test_f007_*.py tests/test_f009_*.py tests/test_f015_*.py -q --tb=no -p
no:cacheprovider -rf` (la selección del implementer), con base **1328 passed**. Cada mutante es una sustitución exacta
de un texto único, restaurada con `git checkout`, mediante el script `mutar_rev007_p2.py` del scratchpad.

| Id | Original → mutado | Medido (fallos) | ¿Igual que el informe? |
|---|---|---|---|
| **N7** | `por_proide.setdefault(_entero(ctrpro.get("proide")), ctrpro)` → `por_proide[_entero(ctrpro.get("proide"))] = ctrpro` | **MUERE**, 1 (`…_iva_es_el_de_la_primera_por_pos`) | sí |
| A1 / A2 | añadir `"linea_ambigua",` a `CODIGOS_LINEA` / `"proforma_del_mes_existente",` a `CODIGOS_CABECERA` | MUERE, 2 / 1 | sí |
| A3 / A4 / A5 | `cls.codigos` → `CODIGOS_LINEA` / `type(self).codigos` → `CODIGOS_CABECERA` / `cls.codigos` → `CODIGOS_AVISO` | MUERE, 8 / 38 / 49 | sí |
| S1 / S2 / S3 | `Field(False,` → `True` / quitar `"sigrid_proforma_prefijos_referencia",` / quitar `"sigrid_proforma_naturaleza_por_producto",` | MUERE, 1 / 4 / 8 | sí |
| S4 / S5 | `Field(500,` → `Field(100,` / alias `SIGRID_PROFORMA_PRODUCTOS…` → `SIGRID_ALBARAN_PRODUCTOS…` | MUERE, 1 / 6 | sí |
| Sup. 3 | `leer_lineas_de_albaran(int(filas[0][0]))` → `filas[1][0]` | **MUERE**, 3 (`r23_…_es_idempotente[False/True]`, `t18_…`) | sí |
| Sup. 4 | `leer_lineas_de_proforma(proforma.ide), muchas=True)` → `muchas=False)` | **MUERE**, 1 (`t18_las_lecturas_de_muchas_filas…`) | sí |
| G1 / G2 | `_resolver_contrato`: `assert isinstance(…)` → `not isinstance` / `_contexto is not None` → `is None` | MUERE, 40 / 40 | sí |
| G3 / G4 | `_comprobar_dentro`: lo mismo | MUERE, 21 / 21 | sí |

Mis mutantes N11-N16 (§1) también mueren: en total, **23 de 23 muertos**.

- **A1-A5 y S1-S5 se pueden reproducir** con el texto de la tabla de T36. Detalle menor: A3 y A5 citan la línea del
  `def` (136, 330) y no la del `if` (+1), y S2 y S3 están en 168 y 254, no en 167 y 253. No bloquea.
- **Los 5 supervivientes, bien clasificados**: §1 equivalente (su fichero no cambia; reproducido en la pasada 1, RM5);
  §2 hueco real cerrado por T32; §3 y §4 falsos de la herramienta (medidos: mueren); §5 sustituido por G1-G4 (mueren).
- **RM3**: ningún equivalente declarado sale muerto. [x]
- **Aceptación del humano de `cifras: int = 0`**: consta en `mutacion_F-007.md:126` («lo aceptó por escrito el humano
  el 2026-10-26»). [x] Detalle menor: `mutacion_F-007.md:59` (§1) sigue diciendo «justificado para el humano».

## Hallazgos de la pasada 1 y su estado

| Hallazgo | Estado |
|---|---|
| Núcleo O1 · design sin `cifras_serie`, `campo_max_lineas`, `error` | **Resuelto** (design:60-68). Hay costuras nuevas sin documentar: cambio 1-2 |
| Núcleo O3 · `Settings` único: riesgo de despliegue | **Resuelto**: `azure-apps` `0072629` §8.10 y `verificacion_manual.md` D1-D3 |
| Mutación 1 · N7 sin test | **Resuelto** (T34): N7 muere |
| Mutación 2 · A1-A5 y S1-S5 irreproducibles | **Resuelto** (T36): los 10 reproducidos, con los mismos fallos |
| Mutación 3 · aceptación de `cifras` | **Resuelto** (`mutacion_F-007.md:126`) |
| Automejora «primera ↔ última» en `setdefault` | Pendiente de decisión del humano |

## Cambios requeridos (solo `specs/F-007-registrar-proforma/design.md`)

1. **`design.md:105`**: «Elegido el contrato, el núcleo lo vuelve a localizar con `cod_contrato` + obra +
   `ctr.entcif` (`locate_contract`)» es falso desde T33. La proforma carga el contrato resuelto por su `ide`
   (`_cargar_contrato`), y un `ctr.entcif` vacío da `proveedor_no_encontrado`.
2. **§Costuras (`design.md:58-78`) y tabla de ficheros (`:44`)** tienen que recoger: la costura
   `_cargar_contrato(request, ctride)`; `PerfilAlta.documentos` (`"albaranes"` por defecto, `"proformas"` en el
   perfil); la firma real `_comprobar_dentro(cursor, request, cabecera, existente)`, llamada antes de la salida
   idempotente (`:69` sigue con tres argumentos); y que la subclase sobrescribe también `_resolver_contrato` (`:77`).
   «Cinco costuras» (`:221`) debe contarlas. El fichero va por 248/250 líneas: compactar.
3. *(Opcional)*: la regla N7 («dos líneas del contrato con el producto: el IVA es el de la primera por `pos`») solo
   vive en un test y un docstring. Si es regla de negocio, añadir una frase en la costura 4 o en R17.
