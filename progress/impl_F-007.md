<!-- progress/impl_F-007.md -->
# F-007 · Informe del implementer (T1-T19; correcciones de la pasada 1: T25-T40)

Rama `feature/F-007-registrar-proforma`, rigor **critico**. Spec v3 (PARADA 1 del 2026-10-25) y enmienda 1
(2026-10-26, `spec_F-007_enmienda1.md`, aprobada por el humano). Nada contra Sigrid: ni lecturas ni escrituras; los
tests no tocan red ni base. T1-T17 `04f13ba`…`bbd562c`; T18-T19 `904a2ef`…`d9e97a8` (+ `azure-apps` `af81713`);
pasada 1 `6af8221`…T40 (+ `azure-apps` `0072629`). T20-T22 (MANUAL), T23 (revisión) y T24 van aparte.

## Qué cambió en T1-T19 (resumen; el detalle, en los commits)

- **T1** · red de R31: los ocho `test_f009_*.py`, los dos `test_f015_*.py`, el dorado
  `tests/fixtures/f009_caracterizacion.json` y el doble `tests/f009_dobles.py` no se tocan (`git diff dev` vacío).
- **T2-T5** · costuras en el núcleo de F-009 con los valores de hoy: `PerfilAlta`/`PERFIL_ALBARAN`,
  `prefijo_de_serie`/`sellos_del_alta`/`siguiente_cod(..., cifras=0)`, gancho `_comprobar_dentro`, `_Catalogo` con
  `productos_del_contrato`, `codigos` de clase en `FalloLinea`, `AlbaranCompraError` y `AvisoAlbaran`. Cinco App
  Settings `SIGRID_PROFORMA_*` cerradas por defecto (`config/settings.py`, `local.settings.sample.json`).
- **T6-T11** · `domain/models/proforma_models.py` (petición, línea, respuesta, `ProformaError` con `reparto`,
  `FalloLineaProforma` con `candidatos`) y `application/use_cases/proforma_statements.py` (LP1-LP6 con `?` y
  funciones puras de R7-R24). Fixture `tests/fixtures/f007_obra0719.json` (M29, proveedores y CIF ficticios).
- **T12-T17** · `CreateProformaUseCase(CreateAlbaranCompraUseCase)` con `PERFIL_PROFORMA`, traza R33, R28 bajo
  `SIGRID_REFEXT_14`; doble `tests/f007_dobles.py`; ruta `sigrid/proforma` (400 de F-012, llave R5 antes del caso
  de uso, `AlbaranCompraError` → 400 con `codigo`, `lineas` y `reparto`).
- **T18** · mutación en serie: ronda 1, 375 / 67 supervivientes; ronda 2, 374 / 2 (un equivalente y uno cazado en
  `8c92d52`). Detalle en [`mutacion_F-007.md`](mutacion_F-007.md) (ahora con la ronda de la pasada 1).
- **T19** · `docs/ARCHITECTURE.md`, mapa de `CLAUDE.md`, `contrato_proformas.md` v1 y `azure-apps/sigrid_api.md`
  (§4, §4.1, §7.2, §7.6, §8, §8.10, §10, §13) con «PENDIENTE DE DESPLIEGUE (F-007)».
- **Hojas con precios**: convertir a `docs/referencia/proforma_ejemplo_*.md` las cuatro hojas de proforma, que traen
  precios de subcontratista, lo **autorizó el humano el 2026-10-25** (consta en la cabecera de cada una).

**Fase ROJA de T2-T16** (comando `python -m pytest <fichero> -q`, salida real): T2 `test_f007_perfil.py` →
`ImportError: cannot import name 'PERFIL_ALBARAN'` (1 error); T3 `test_f007_settings.py` → `40 failed, 2 passed`
(`'Settings' object has no attribute 'sigrid_proforma_write_enabled'`); T6 `test_f007_models.py` y T8
`test_f007_statements_contrato.py` → `ModuleNotFoundError` del módulo nuevo; T10 `test_f007_statements_lineas.py` →
`cannot import name 'FalloIdentificacion'`; T12 `test_f007_use_case.py` → `ModuleNotFoundError`; T14
`test_f007_transaccion.py` → `6 failed, 9 passed` (`assert ('creado', ...) == ('existente', ...)`); T16
`test_f007_route.py` → `17 failed` (`has no attribute 'CreateProformaUseCase'`).

## Desviaciones de T1-T19 que siguen vivas (las superadas por la enmienda 1, al final)

1. **Costura 1 ampliada** con `cifras_serie` (5 cifras de `PROF26/01282`) y `error` (la clase de las guardas); en la
   pasada 1, además, `documentos` (T35). `PERFIL_ALBARAN` deja el albarán igual.
2. **`periodo` entero `AAAAMM`** estricto; el ejemplo del contrato v0.1 lo escribía como texto. Contrato v1.
4. **R8**: si viene `cif_proveedor`, se filtra solo por CIF (manda sobre el nombre).
5. **R9**: alguna línea de contrato fuera de todo candidato → `contrato_no_resuelto`; si se solapan, o varios
   candidatos sin líneas de contrato → `contrato_ambiguo`.
7. **R11 literal**: sin contrato no hay ninguna comprobación de R19, tampoco `linea_descuadrada`.
9. **`existente`**: `cabecera` `{fec, entref}`, `totales` `{totbas, n_lineas}` y los avisos de R20-R22.
11. **R28**: el contexto viaja en un `PrivateAttr` de una subclase de `AlbaranCompraRequest`; la `existente` hallada
    dentro sale por una excepción interna que revierte y se responde fuera con LP6.
12. **Ruta**: `ValueError` → 400 como en `sigrid/albaran`; lo demás, 500.
13. **Test de F-012 tocado**: cuenta 10 rutas con `validation_error_response` en vez de 9 (una línea, comentada).
14. `ahora` se lee dos veces; `con.fec` y `fecdoc` salen de la fecha de R18, no de la segunda lectura.

Superadas: **3** (fixture 0417 con `/25552`) la cierra el líder: T21 compara con `AC26/25552`; **6** (embudo de R14)
la sustituye R14 v1.1 (T25-T26); **8** (E1 bajo el applock) la sustituye D2 (T29-T30); **10** (IVA a 0 sin
plantilla) la sustituye D1 (T27-T28).

**Texto del aviso** (actualizado a la v1.1 en T40; lo manda el líder, no he avisado a nadie):

> **sigrid-api F-007 (`POST /api/sigrid/proforma`) implementada en su rama, pendiente de revisión y despliegue.**
> - **proformas (F-005)**: contrato **v1.1** en `sigrid-api/specs/F-007-registrar-proforma/contrato_proformas.md`
>   (§8, lo que cambió). Lo que os afecta: `periodo` y `fecha_proforma` son **enteros** (`202608`; el texto da 400);
>   `cif_proveedor` manda sobre el nombre; sin contrato no hay `existente` ni comprobación de la hoja; referencia
>   `PRF-`; vuestra lista de productos, contenida en la de la API. **Novedades de la v1.1**: una línea de contrato
>   sin `ctrpro_ide` (respaldo que no usáis) se vincula **solo por partida y precio unitario**; si casan varias,
>   `linea_ambigua` con sus `candidatos`: desempatáis por la descripción y reenviáis con `ctrpro_ide` (la misma regla
>   decide entre contratos); `otra_del_mes` registra aunque haya una del mismo importe; reenviar una ya grabada da
>   `idempotente` con `origen` nulo y `avisos` vacío; una referencia de otro contrato o que no es proforma da
>   `referencia_en_conflicto` también bajo el applock; el IVA de una nueva con producto del contrato sale de su línea
>   de contrato; un contrato sin CIF en Sigrid da `proveedor_no_encontrado`; con la llave cerrada, el 400 dice
>   «Escritura de proformas desactivada». Siguen abiertas las tres preguntas de design §Preguntas (CIF o nombre;
>   solo MES ≠ 0; qué avisos bloquean la aprobación).
> - **facturas**: las proformas que registre la API serán `tip 14` de la serie `PROF<aa>/` (`cla 141`) con
>   `dca.entref` = `PROF<MMAA>_<cod_obra>`, el mismo de las `AC` de hoy. Si buscáis proformas por `con.cod` `AC…`,
>   añadid la serie `PROF`. Ver `azure-apps/sigrid_api.md` §8.10 y §10.
> - **albaranes**: el núcleo del modo extendido de `sigrid/albaran` cambia por costuras **sin cambio de conducta**;
>   su dorado y sus tests de F-009 y F-015 pasan sin modificarse. Nada que cambiar en sv9. Al desplegar F-007 se
>   hará un dry-run de `sigrid/albaran` antes que nada (una App Setting mal formada tumbaría todas las rutas).

## Correcciones pasada 1 (T25-T40, 2026-10-26)

Origen: `review_F-007_*.md` (pasada 1) y enmienda 1 de la spec. RED antes que GREEN, un commit por paso.

| Tarea | Qué cambió | Ficheros |
|---|---|---|
| T25-T26 | **R14/R8 estrictos**: `_por_partida_y_precio` (partida por código **y** precio ±0,0001; sin partida no casa ninguna); una → esa, ninguna → `linea_no_es_del_contrato`, varias → `linea_ambigua` con `candidatos`; sin relajar filtros; medición, unidad y producto no cuentan. `_contiene` (R8) usa la misma regla. Quitado `_casa_medicion` | `proforma_statements.py`; tests `statements_lineas`, `statements_contrato`, `filas` |
| T27-T28 | **D1**: la sin vincular con producto del contrato y **sin plantilla** toma el IVA de su `ctrpro` (naturaleza y cuentas a 0); `producto_sin_historico` lo dice («cuenta a 0 e IVA de su linea de contrato»). El albarán sin histórico, igual que antes | `create_albaran_compra_use_case.py` (`_de_la_plantilla_del_contrato`); `test_f007_perfil.py`, `test_f007_use_case.py` |
| T29-T30 | **D2/D3**: el núcleo pasa la fila de E1 a `_comprobar_dentro(cursor, request, cabecera, existente)` **antes** de la salida idempotente (la base no hace nada); la proforma repite LP5 por el cursor: misma referencia, proforma `cla 141` del mismo contrato → `idempotente` con `origen` nulo y `avisos` `[]`; otro contrato, otra clase o varias filas → `referencia_en_conflicto` | núcleo (gancho), `create_proforma_use_case.py`; `test_f007_transaccion.py` |
| T31 | **D5/O3**: hora de Madrid en el borde del mes (22:30 y 21:30 UTC del 31-8), cambio de año (23:30 UTC del 31-12: `202612` → `PROF26/`, `20261231`; `202701` → `PROF27/`) y `otra_del_mes` con la del mismo total | `test_f007_use_case.py` (tests de fijación) |
| T33 | **O4**: costura `_cargar_contrato(request, ctride)` en el núcleo (el albarán sigue localizando por `cod` + obra + CIF); la proforma carga el contrato **ya resuelto por su `ide`** (`_resolver_contrato`), sin volver a buscarlo por un CIF normalizado; `traducir` normaliza `ctr.entcif` y, vacío, lanza `proveedor_no_encontrado` (antes, 400 sin `codigo` por `ValidationError`) | núcleo, `create_proforma_use_case.py`, `proforma_statements.py`; tests `use_case`, `statements_lineas` |
| T34 | **N7**: test de que el IVA de la sin vincular sale de la **primera** línea del contrato por `pos` (`setdefault`) | `test_f007_perfil.py` |
| T35 | **Llave**: `PerfilAlta.documentos` (`"albaranes"` por defecto, `"proformas"` en el perfil): «Escritura de proformas desactivada: hacen falta …». El mensaje de albaranes no cambia | núcleo, `create_proforma_use_case.py`; tests `use_case` |
| T32, T36 | Campaña en serie: 381 / 5 supervivientes, 0 no aceptados (abajo); **test nuevo** de las columnas de la sin plantilla (hueco real de D1) y la guarda de `_resolver_contrato` en dos `assert` (equivalente). Manuales N7, A1-A5, S1-S5 reproducibles | `progress/mutacion_F-007.md`, `test_f007_perfil.py`, `create_proforma_use_case.py` |
| T37 | `specs/F-007-registrar-proforma/verificacion_manual.md`: D1-D3 (App Settings en JSON validado, cerradas; publicar; dry-run de `sigrid/albaran`) y V0-V5 (llave, `existente` de las tres hojas, `otra_del_mes`, respaldo, una grabación y su anulación por la UI). Sin secretos: URL, clave y recursos por variable de entorno | spec |
| T38 | `progress/current.md` reescrito al estado real (H1), descripción de F-007 en `harness/features.json` (H2), `BACKLOG.md` regenerado con `harness/backlog.py` | arnés |
| T39 | `azure-apps/sigrid_api.md` §8.10: riesgo O3, R14 v1.1, `otra_del_mes`, idempotente bajo el applock, IVA del `ctrpro`, `proveedor_no_encontrado` (commit `0072629`, sin tocar `datamart_seg_anual.md`) | `azure-apps` |
| T40 | Texto del aviso a la v1.1 (arriba) | este informe |

**Fase ROJA de la pasada 1** (salida real; `-q -p no:cacheprovider --tb=line`):

- T25 `python -m pytest tests/test_f007_statements_lineas.py tests/test_f007_statements_contrato.py
  tests/test_f007_filas.py` → **26 failed, 161 passed**: `E AssertionError: assert 281001 == 281002`
  (`test_f007_statements_lineas.py:128`), `E Failed: DID NOT RAISE FalloIdentificacion`, `assert False is True`
  (`test_f007_statements_contrato.py:474`).
- T27 `python -m pytest tests/test_f007_perfil.py tests/test_f007_use_case.py` → **2 failed, 85 passed**:
  `E assert (0, 0.0) == (3, 1.58)` (`test_f007_perfil.py:419`) y `E assert (0, 0.0) == (3, 55.75)`.
- T29 `python -m pytest tests/test_f007_transaccion.py tests/test_f007_perfil.py` → **10 failed, 50 passed**:
  `E AssertionError: assert ['referencia'...el_existente'] == ['referencia'...el_existente']`
  (`test_f007_transaccion.py:146`) y `E Failed: DID NOT RAISE ProformaError`.
- T33 `python -m pytest tests/test_f007_use_case.py tests/test_f007_statements_lineas.py` → **7 failed, 154
  passed**: `E AssertionError: assert 'locate_contract' not in ['leer', ...]` (`test_f007_use_case.py:367`) y
  `E domain.models.albaran_compra_models.AlbaranCompraError: No hay un contrato 'CTSB26/0472' de la obra '0719' y
  ese proveedor.`
- T35 `python -m pytest tests/test_f007_use_case.py tests/test_f007_perfil.py` → **3 failed, 96 passed**:
  `E AttributeError: 'PerfilAlta' object has no attribute 'documentos'` (`test_f007_use_case.py:94`) y
  `E AssertionError: assert 'Escritura de...de escritura.' == 'Escritura de...de escritura.'`.
- T32 (superviviente §2 aplicado en el worktree `../sigrid-api-mut007-p1`) `python -m pytest
  tests/test_f007_perfil.py` → **1 failed, 41 passed**: `E AssertionError: assert {'envide': 1,...ride': 0, ...} ==
  {'envide': 0,...ride': 0, ...}` (`test_f007_perfil.py:501`).
- T31 y T34 son tests de **fijación** (la conducta ya era la pedida): verdes desde el principio. Su RED es el
  mutante: con `datetime.now(timezone.utc)` en vez de Madrid caen 2 de los 3 de T31; con `por_proide[...] = ctrpro`
  en vez de `setdefault` cae el de T34 (N7 de la tabla de manuales).

**Decisiones y puntos para el reviewer:**

- **`proveedor_no_encontrado` para `ctr.entcif` vacío** (O4): código ya existente de F-009, no está en la tabla §4
  del contrato; el mensaje nombra el contrato y `ctr.entcif`. A validar por el líder (alternativa: código nuevo).
- **design.md** dice que el núcleo relocaliza el contrato con `locate_contract`; desde T33 la proforma lo carga por
  `ide` (la costura nueva es de solo extracción: el albarán sigue igual, dorados intactos).
- **Guardas en vez de ramas muertas** (T32): en `_resolver_contrato` y `_comprobar_dentro` de la proforma, el
  contexto de R28 siempre existe; un `and` equivalente y un `if contexto is None: return` sin cubrir pasan a dos
  `assert` (tipo y contexto), cuyos mutantes mueren a mano. La base del núcleo sigue sin hacer nada en el gancho.
- **Residual fuera del applock** (no lo pide la enmienda): entre LP5 de fuera y L11 del núcleo, otra petición con la
  misma referencia puede grabar; dentro, D2 lo resuelve. Sin cambio.
- **R31**: `git diff dev -- tests/test_f009_* tests/test_f015_* tests/fixtures/f009_caracterizacion.json
  tests/f009_dobles.py infrastructure/` → vacío.

## Verificación (resultado real)

- `python -m pytest tests/test_f007_*.py tests/test_f009_*.py tests/test_f015_*.py -q` → **1328 passed** (F-007 sola,
  512 passed en 6,4 s).
- `bash harness/init.sh` → **ENTORNO LISTO** (salida al final).
- Las tres hojas de agosto de la 0719 dan `existente` sobre `AC26/25548`, `AC26/25552` y `AC26/25551` con sus líneas
  (`test_f007_r24_las_tres_hojas_de_la_0719_son_existentes`); en real, V2 de `verificacion_manual.md`.

## Qué queda (fuera de este encargo)

- **Avisos** (texto arriba, los manda el líder); **T23** pasada 2 de la revisión; merge.
- **T20-T22** MANUALES con `specs/F-007-registrar-proforma/verificacion_manual.md`; **T24** `init.sh` final.

## Evidencias

| Evidencia | Valor medido |
|---|---|
| Tests ejecutados | 3393 passed, 1 skipped (suite completa en `init.sh`); 512 de F-007; 1328 de F-007 + F-009 + F-015 |
| Cobertura de las líneas cambiadas | **100,0 %** (736/736, umbral 80 %, nivel critico) |
| Mutantes generados / supervivientes | Pasada 1 (`4a94da0`): **381 / 5** (376 muertos, 0 timeouts): 1 equivalente aceptado por el humano (`cifras`), 1 hueco cazado con test, 2 falsos de la herramienta (mueren a mano), 1 guarda reescrita; **0 no aceptados**. Manuales: 11 / 0 (N7, A1-A5, S1-S5). Rondas anteriores: 375 / 67 y 374 / 2 |
| Tiempo de la suite | 156,90 s con cobertura (`init.sh`); F-007 sola, 6,4 s; campaña de la pasada 1, 4674,3 s (media 12,3 s por mutante) |

Salida de `bash harness/init.sh` (última ejecución, sin las líneas de puntos):

```
[OK] Arnés v1.7.8 (2026-09-02) · [OK] features.json válido · [OK] BACKLOG.md al día
    15 features, 6 abiertas, en curso: ['F-007'], bloqueadas: ['F-015']
[AVISO] Hay features en estado blocked: revisa progress/current.md      (F-015, previa)
[AVISO] ruff: 79 avisos (deuda previa, no bloquea)
3393 passed, 1 skipped, 1 warning in 156.90s (0:02:36)
[OK] pytest en verde (con medición de cobertura)
[OK] PUERTA COBERTURA: 100.0% de 736 líneas cambiadas cubiertas (736/736, umbral 80%, nivel critico)
[OK] PUERTA TAMAÑO: F-007 dentro de los topes (requirements 150/150, design 248/250, impl 164/220)
[OK] Rama actual: feature/F-007-registrar-proforma
ENTORNO LISTO. Puedes trabajar.
```
