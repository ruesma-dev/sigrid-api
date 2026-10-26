<!-- progress/review_F-007_nucleo_mutacion_p2.md -->
Revisión incremental desde fe85523 (pasada 2) · bloque **núcleo de F-009 y mutación** · HEAD revisado `765f273`

# F-007 · Pasada 2 · núcleo y mutación

**Veredicto del bloque: CHANGES_REQUESTED, solo por documentación.** `design.md` no describe dos costuras nuevas del
núcleo (`_cargar_contrato`, `PerfilAlta.documentos`) y en un punto (línea 105) dice lo contrario de lo que hace el
código. El código del núcleo y la mutación están bien: **no hay que tocar código ni repetir la campaña**.

**Rigor:** `critico` (declarado). En este bloque no ejecuté `init.sh` ni la campaña: el encargo lo prohíbe en el árbol
compartido. Las pruebas se hicieron en el worktree desechable `../sigrid-api-rev007-p2` (HEAD separado en
`765f273`), que ya está borrado. `git status` limpio. Después de `765f273` solo entraron informes de otros revisores
(`2faeea4`, `722995c`, `28b9620`), ningún código.

## 1 · Costuras del núcleo: la conducta del albarán no cambia

| Comprobación | Resultado |
|---|---|
| R31: `git diff dev -- tests/test_f009_* tests/test_f015_* tests/fixtures/f009_caracterizacion.json tests/f009_dobles.py infrastructure/` | **vacío** (0 líneas) |
| `python -m pytest tests/test_f009_*.py tests/test_f015_*.py -q -p no:cacheprovider` (worktree) | **816 passed** |
| Diferencial `dev` ↔ `765f273`: el grabador de la pasada 1 envuelve `CreateAlbaranCompraUseCase.run` y graba respuesta o excepción, lecturas, sentencias, applocks y log; 816 tests en cada árbol | **279/279 idénticas** salvo `r22_el_instante_por_defecto_es_utc_con_zona` (reloj real: solo cambian `fechor`, `hor` y `tiemod`), igual que en la pasada 1 |

- **`_cargar_contrato(request, ctride)`**: es una extracción literal del código de antes (`_fila_completa` del `ctr`,
  `None` si no está, y `ctrpro` por `pos`). `_resolver_contrato` del albarán sigue localizando por `locate_contract` y
  mantiene los mismos errores (`contrato_ambiguo`, `contrato_no_encontrado`). Mi mutante N15 (`order_by="pos"` →
  `"ide"`) lo mata F-009.
- **`PerfilAlta.documentos`**: vale `"albaranes"` por defecto y `PERFIL_ALBARAN` no lo fija. El mensaje de la llave
  queda idéntico: lo afirma `test_f007_r31_el_mensaje_de_la_llave_del_albaran_es_el_de_hoy` y el diferencial lo
  confirma. Mi mutante N12 (defecto `"proformas"`) lo mata, pero solo en `test_f007_perfil`, porque F-009 no afirma
  ese texto.
- **`_comprobar_dentro(..., existente)` antes de la salida idempotente**: en la base, el cuerpo sigue vacío y no toca
  el cursor, así que el orden de las sentencias de E1 y de la idempotente es el mismo (diferencial: 42 transacciones
  iguales). Mi mutante N11 (devolver el gancho a después del `return` idempotente) muere con 8 fallos (2 de perfil y 6
  de transacción).
- **IVA del `ctrpro` sin plantilla**: `_de_la_plantilla_del_contrato` solo se llama con `linea.del_contrato`, y eso
  solo es `True` si `_del_contrato` tiene el producto. Con `productos_del_contrato=False` (el albarán), `_del_contrato`
  es `{}`, así que **un albarán sin histórico sigue con `ivaide` 0 y el mensaje «cuenta e IVA a 0»**. El diferencial
  tiene 12 de esos casos y son idénticos en `dev` y en HEAD. Lo fija además
  `test_f007_r17_el_albaran_sin_historico_sigue_con_iva_0`. Mis mutantes:
  - N14 (invertir la condición del mensaje): muere en ese test;
  - N16 (llamar a `_de_la_plantilla_del_contrato` siempre): muere con 19 fallos, 16 de ellos en `test_f009_use_case`.
- **RM6** (las guardas `if contexto is None: return` y el `and` pasan a dos `assert`): verifiqué el invariante en
  quien construye el dato. Solo hay un camino al núcleo con un `_AltaDeProforma`: `CreateProformaUseCase.run`, que
  fija `alta._contexto` en `create_proforma_use_case.py:259` justo antes de `self._ejecutar(alta)` (`:264`). Además,
  `run` sobrescribe el de la base. No se pierde ninguna defensa: antes, un contexto ausente se saltaba R28 en
  silencio, y ahora falla. [x]

## 2 · `design.md` frente a lo implementado

O1 de la pasada 1 está **resuelto**: §Costuras 1-2 ya nombran `cifras_serie`, `campo_max_lineas`, `error` y
`siguiente_cod(..., cifras=)`. Pero T33 y T35 llegaron después de la v3.1 y el diseño no los recoge (ver
«Cambios requeridos»).

## 3 · Mutación

**RM1.** El informe midió `4a94da0`. Entre ese commit y `765f273` solo cambian `create_proforma_use_case.py` (la guarda
en dos `assert`, T32) y `tests/test_f007_perfil.py`. Las líneas del alcance que cambian son las de las guardas, y sus
mutantes los medí a mano (G1-G4, abajo). La campaña sigue valiendo. [x]

**RM2.** Línea base 79,5 s; media 12,3 s; 381 × 12,3 = 4686 s, frente a 4674 s declarados: cuadra. Con `-x` y 376 de
381 muertos, es lo esperable. **Campaña no reejecutada: 78 min según el informe** (y el encargo lo prohíbe). En su
lugar, RM4 con estos mutantes manuales.

Todos se midieron con `python -m pytest tests/test_f007_*.py tests/test_f009_*.py tests/test_f015_*.py -q --tb=no
-p no:cacheprovider -rf` (la selección del implementer), con una base de **1328 passed**. Cada mutante es una
sustitución exacta de un texto que aparece una sola vez, y se restaura con `git checkout`. El script es
`mutar_rev007_p2.py`, en el scratchpad de la sesión.

| Id | Original → mutado | Medido | ¿Cuadra con el informe? |
|---|---|---|---|
| **N7** | `por_proide.setdefault(_entero(ctrpro.get("proide")), ctrpro)` → `por_proide[_entero(ctrpro.get("proide"))] = ctrpro` | **MUERE**, 1 fallo (`test_f007_r17_dos_lineas_del_contrato…primera_por_pos`) | sí |
| A1 / A2 | añadir `"linea_ambigua",` a `CODIGOS_LINEA` / `"proforma_del_mes_existente",` a `CODIGOS_CABECERA` | MUERE, 2 / 1 | sí / sí |
| A3 / A4 / A5 | `cls.codigos` → `CODIGOS_LINEA` / `type(self).codigos` → `CODIGOS_CABECERA` / `cls.codigos` → `CODIGOS_AVISO` | MUERE, 8 / 38 / 49 | sí |
| S1 / S2 / S3 | `Field(False,` → `Field(True,` / quitar `"sigrid_proforma_prefijos_referencia",` / quitar `"sigrid_proforma_naturaleza_por_producto",` | MUERE, 1 / 4 / 8 | sí |
| S4 / S5 | `Field(500,` → `Field(100,` / alias `SIGRID_PROFORMA_PRODUCTOS…` → `SIGRID_ALBARAN_PRODUCTOS…` | MUERE, 1 / 6 | sí |
| Sup. 3 | `leer_lineas_de_albaran(int(filas[0][0]))` → `filas[1][0]` | **MUERE**, 3 (`r23_…_es_idempotente[False/True]`, `t18_…tope_de_filas`) | sí |
| Sup. 4 | `leer_lineas_de_proforma(proforma.ide), muchas=True)` → `muchas=False)` | **MUERE**, 1 (`t18_las_lecturas_de_muchas_filas…`) | sí |
| G1 / G2 | `_resolver_contrato`: `assert isinstance(…)` → `not isinstance` / `_contexto is not None` → `is None` | MUERE, 40 / 40 | sí (40) |
| G3 / G4 | `_comprobar_dentro`: lo mismo | MUERE, 21 / 21 | sí (21) |

Mis mutantes del núcleo, N11-N16 (§1), **mueren los seis**. En total, 23 de 23 mueren.

- **A1-A5 y S1-S5 se pueden reproducir** a partir de la tabla de T36. Hay un detalle menor: A3 y A5 citan la línea
  del `def` (136, 330) y no la del `if` (137, 331), y S2 y S3 están una línea por debajo (168 y 254). El texto exacto
  basta para reproducirlos. No bloquea.
- **Los 5 supervivientes están bien clasificados.** §1 es equivalente: `albaran_compra_statements.py` no cambia en el
  delta y lo reproduje en la pasada 1 (RM5). §2 es un hueco real cerrado por el test de T32. §3 y §4 son falsos de la
  herramienta y mueren, medido arriba. §5 era una guarda equivalente y ya no existe: sus sucesores G1-G4 mueren.
- **RM3**: ningún mutante declarado equivalente sale muerto. [x]
- **Aceptación del humano del equivalente `cifras: int = 0`**: consta en `mutacion_F-007.md:126` («lo aceptó por
  escrito el humano el 2026-10-26»). [x] Pero hay una incoherencia menor: el §1 del mismo fichero
  (`mutacion_F-007.md:59`) sigue diciendo «Decisión: … justificado para el humano». No bloquea.

## Hallazgos de la pasada 1 y su estado

| Hallazgo | Estado |
|---|---|
| Núcleo O1 · `design.md` sin `cifras_serie`, `campo_max_lineas`, `error` | **Resuelto** (design:60-68), pero hay costuras nuevas sin documentar (abajo) |
| Núcleo O2 · `PERFIL_ALBARAN.cla` es dato muerto | Sin cambio; no se pedía |
| Núcleo O3 · `Settings` único: riesgo de despliegue | **Resuelto**: `azure-apps` `0072629` §8.10 y `verificacion_manual.md` D1-D3 |
| Mutación 1 · N7 sin test | **Resuelto**: T34; N7 muere |
| Mutación 2 · A1-A5 y S1-S5 irreproducibles | **Resuelto**: tabla T36; los 10 reproducidos y con los mismos fallos |
| Mutación 3 · aceptación de `cifras` | **Resuelto** (`mutacion_F-007.md:126`) |
| Automejora `setdefault` / primera↔última | Sigue pendiente de decisión del humano (sin cambio) |

## Cambios requeridos

1. **`specs/F-007-registrar-proforma/design.md:105`** dice: «Elegido el contrato, el núcleo lo vuelve a localizar con
   `cod_contrato` + obra + `ctr.entcif` (`locate_contract`)». Desde T33 es falso para la proforma: carga el contrato
   ya resuelto por su `ide` con `_cargar_contrato`, y `ctr.entcif` vacío da `proveedor_no_encontrado`. Hay que
   reescribirlo.
2. **`design.md:58-78` (§Costuras) y `:44` (tabla de ficheros)** tienen que recoger:
   - `_cargar_contrato(request, ctride)`, la costura extraída de `_resolver_contrato`;
   - `PerfilAlta.documentos` (`"albaranes"` por defecto, `"proformas"` en el perfil), que cambia el texto de la llave;
   - la firma real `_comprobar_dentro(cursor, request, cabecera, existente)`, llamada **antes** de la salida
     idempotente (en `:69` sigue la de tres argumentos);
   - que `CreateProformaUseCase` sobrescribe también `_resolver_contrato` (`:77`).

   «Cinco costuras» (`:221`) debería contar la nueva. El fichero va por 248/250 líneas: compactar.
3. *(Opcional; la pasada 1 lo dejó a decisión del líder)*: la regla «si el producto está en dos líneas del contrato,
   el IVA es el de la primera por `pos`» (N7) solo vive en un test y en un docstring. Si es regla de negocio, una
   frase en la costura 4 o en R17.
