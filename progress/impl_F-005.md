<!-- progress/impl_F-005.md -->
# F-005 · Informe de implementación

`sigrid/concepto-grafico` admite documentos **sin clase de gráfico**
(`gratipide = 0`), que es como Sigrid adjunta en contratos y albaranes de
compra. Rama `feature/F-005-grafico-sin-clase`, `sdd: false`, rigor `critico`.

**SHA final del código: `cfb8048`.** Los commits posteriores son papeleo.

## Qué cambió

Tres ficheros de producción, **7 líneas** de cambio efectivo. Nada más:
`ALLOWED_WRITE_DATABASES` no se toca, ningún otro fichero de
`infrastructure/security/` se toca, ni el repositorio, ni el constructor de
sentencias, ni la ruta.

| Fichero | Cambio |
|---|---|
| `infrastructure/security/document_write_guard.py` | `validar_clase_de_grafico`: tras la lista blanca, `if gratipide == 0: return`. El 0 no exige `existe` ni mira `fecbaj`. Para `gratipide > 0`, idéntico a F-004. |
| `application/use_cases/attach_concepto_grafico_use_case.py` | `_leer_clase`: la lectura **L2** de `dbo.auxgra` solo se ejecuta `if request.gratipide != 0`. `fila` se queda en `None`, y de ahí salen `existe` y `fecbaj`. |
| `domain/models/concepto_grafico_models.py` | `gratipide: Field(..., ge=0)` (era `ge=1`). Los negativos los sigue cortando el modelo. |

Consecuencias medidas por los tests:

- Con `0` en `SIGRID_DOCUMENT_ALLOWED_GRATIPIDE`, el dry-run hace **cinco**
  lecturas (`concepto, usuario, pos, idempotencia, huerfanas`) en vez de seis, y
  no añade el aviso de `tipaso` — que sin fila en `auxgra` saldría siempre.
- **Sin** el `0` en la lista, se rechaza con `clase_de_grafico_no_permitida`
  tras **una sola** lectura (la del concepto): ni siquiera se gasta la de
  `auxgra`. El defecto de la App Setting (lista vacía) sigue rechazándolo.
- Con `gratipide > 0` la L2 se sigue ejecutando **aunque el 0 esté permitido**,
  y una clase inexistente o dada de baja se sigue rechazando.
- Las filas escritas solo cambian en una columna: negocio con `gratipide = 0`;
  la documental ya escribía `0` y `res = ''` desde F-004 y **no se toca**.

## Decisión de diseño que vale la pena contar

En T4 `_leer_clase` tenía **dos** llamadas a `validar_clase_de_grafico`: una en
la rama del 0, con `existe=False, fecbaj=None` escritos a mano (que es lo que
decía la propuesta aprobada), y otra en la rama normal. La campaña de mutación
demostró que ese `existe=False` era **código muerto**. T5 lo quitó de raíz:
**un solo** punto de llamada, y lo único que cambia con el 0 es que `fila` se
queda en `None` por no haberse leído. Mismo comportamiento — el guardia recibe
exactamente `existe=False, fecbaj=None` —, un punto de decisión menos y ningún
literal muerto que mutar.

## Fase RED (obligatoria, nivel `critico`)

Comando exacto, con los 23 tests `f005` escritos **antes** de tocar producción,
sobre `602e079` (HEAD al empezar):

```
.venv/Scripts/python.exe -m pytest tests -q -k "f005" --tb=short
```

Salida real (resumen; traza completa en el commit `ca2b123`):

```
10 failed, 13 passed, 1481 deselected, 1 warning in 4.29s

________ test_f005_la_clase_0_permitida_pasa_sin_exigir_fila_en_auxgra ________
tests\test_f004_document_write_guard.py:270: in test_f005_...
    DocumentWriteGuard.validar_clase_de_grafico(
infrastructure\security\document_write_guard.py:152: in validar_clase_de_grafico
    raise ConceptoGraficoError(
E   domain.models.concepto_grafico_models.ConceptoGraficoError:
    La clase de grafico 0 no existe en dbo.auxgra.

___________________ test_f005_el_modelo_acepta_gratipide_0 ____________________
tests\test_f004_models.py:266: assert peticion(gratipide=0).gratipide == 0
E   pydantic_core._pydantic_core.ValidationError: 1 validation error for
    AttachConceptoGraficoRequest
E   gratipide
E     Input should be greater than or equal to 1
      [type=greater_than_equal, input_value=0, input_type=int]

____ test_f005_r3_un_gratipide_0_no_permitido_sale_como_400_con_su_codigo _____
tests\test_f004_route.py:249: in ...
    assert vistos == [0]
E   assert [] == [0]
------------------------------ Captured log call ------------------------------
WARNING  function_app:function_app.py:298 ValidationError en
sigrid/concepto-grafico: ... gratipide Input should be greater than or equal to 1

FAILED ...::test_f005_la_clase_0_permitida_pasa_sin_exigir_fila_en_auxgra
FAILED ...::test_f005_la_clase_0_permitida_pasa_aunque_lleguen_existe_falso_y_un_fecbaj
FAILED ...::test_f005_el_modelo_acepta_gratipide_0
FAILED ...::test_f005_r3_un_gratipide_0_no_permitido_sale_como_400_con_su_codigo
FAILED ...::test_f005_con_el_0_permitido_el_dry_run_hace_cinco_lecturas_sin_auxgra
FAILED ...::test_f005_con_el_0_permitido_no_se_avisa_de_tipaso
FAILED ...::test_f005_sin_el_0_en_la_lista_se_rechaza_y_no_se_lee_auxgra
FAILED ...::test_f005_el_defecto_de_la_app_setting_sigue_rechazando_el_0
FAILED ...::test_f005_las_dos_filas_del_preview_llevan_gratipide_0
FAILED ...::test_f005_el_commit_con_el_0_escribe_las_tres_filas_igual
```

Los **13 que ya pasaban** son los **controles negativos** a propósito: clase
`> 0` sigue exigiendo `auxgra`, `conide`/`contip` mantienen suelo 1, y las filas
de `statements` con `gratipide=0` (esa capa nunca validó nada). Tenían que pasar
antes y después: son la prueba de que no se relajó nada de más. Tras implementar,
los 23 en verde.

## Los 23 tests, por criterio de aceptación

| Criterio | Tests |
|---|---|
| (a) 0 permitido: acepta sin `auxgra`, sin aviso `tipaso`, sin L2 | `test_f005_la_clase_0_permitida_pasa_sin_exigir_fila_en_auxgra`, `..._pasa_aunque_lleguen_existe_falso_y_un_fecbaj`, `test_f005_con_el_0_permitido_el_dry_run_hace_cinco_lecturas_sin_auxgra`, `..._no_se_avisa_de_tipaso` |
| (b) 0 no permitido → `clase_de_grafico_no_permitida` | `test_f005_la_clase_0_fuera_de_la_lista_blanca_se_rechaza`, `test_f005_con_la_lista_blanca_vacia_el_0_tampoco_vale`, `test_f005_sin_el_0_en_la_lista_se_rechaza_y_no_se_lee_auxgra`, `test_f005_el_defecto_de_la_app_setting_sigue_rechazando_el_0` |
| (c) control negativo: clase > 0 sin relajar | `test_f005_una_clase_mayor_que_cero_sigue_exigiendo_auxgra_con_el_0_permitido` (×2), `..._viva_sigue_pasando_con_el_0_permitido`, `test_f005_una_clase_mayor_que_cero_sigue_leyendo_auxgra_con_el_0_permitido`, `..._con_tipaso_vacio_sigue_avisando`, `test_f005_conide_y_contip_siguen_exigiendo_al_menos_1` |
| (d) modelo acepta 0, rechaza −1 | `test_f005_el_modelo_acepta_gratipide_0`, `test_f005_el_modelo_sigue_rechazando_un_gratipide_negativo` (×2) |
| (e) filas E4/E5 con 0, resto igual | `test_f005_la_fila_de_negocio_sin_clase_solo_cambia_en_gratipide`, `test_f005_el_insert_de_negocio_sin_clase_manda_el_0_en_su_columna`, `test_f005_las_dos_filas_del_preview_llevan_gratipide_0`, `test_f005_el_commit_con_el_0_escribe_las_tres_filas_igual` |
| (f) la ruta devuelve 400 con `codigo` | `test_f005_r3_un_gratipide_0_no_permitido_sale_como_400_con_su_codigo`, `..._un_gratipide_negativo_lo_para_el_modelo_en_la_ruta` |

Ninguno toca red ni BBDD.

**Dos tests de F-004 se ajustaron** porque medían justo el suelo que cambia:
`test_f004_r1_los_identificadores_son_enteros_positivos` deja de parametrizar
`gratipide`, y la tabla del borde de abajo pasa de `("gratipide", 1)` a
`("gratipide", 0)` — si no, dejaría de probar el borde. Ambos lo dicen en su
docstring. Ningún otro test de F-004 cambió.

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados | **1.502 passed, 1 skipped** (eran 1.480 + 1; +22 netos) |
| Tests nuevos `f005` | 23, todos en verde |
| Cobertura de líneas cambiadas | **100,0 % (7/7)**, umbral 80 %, nivel `critico` |
| Mutantes generados / muertos / supervivientes | **6 / 6 / 0** sobre `cfb8048` |
| Tiempo de la suite | **50,52 s** (`init.sh` final); 60,32 s en la línea base al empezar |
| `bash harness/init.sh` | **ENTORNO LISTO** — pytest verde, puerta cobertura OK, puerta tamaño OK |

Salida literal de las dos puertas en el `init.sh` final:

```
1502 passed, 1 skipped, 1 warning in 50.52s
[OK] pytest en verde (con medición de cobertura)
[OK] PUERTA COBERTURA: 100.0% de 7 líneas cambiadas cubiertas (7/7, umbral 80%, nivel critico)
[OK] PUERTA TAMAÑO: F-005 dentro de los topes
```

`ruff` sigue con la deuda previa del repositorio (79 avisos, no bloquea); los
tres ficheros tocados están limpios.

### Mutación: 0 supervivientes, ninguno justificado como equivalente

Detalle completo y las tres campañas en **`progress/mutacion_F-005.md`**.
Resumen: la campaña sobre `f36a242` (T4) dejó **1 superviviente**, el
`existe=False` de la rama del 0. Se cerró **midiendo, no razonando**:

1. Reevaluado en serie en el árbol principal: seguía vivo (`1502 passed` con el
   mutante puesto) — no era un falso superviviente de la campaña paralela.
2. **Canario**: sustituido el argumento por un objeto cuyo `__bool__` lanza
   `AssertionError` → `108 passed`. Nadie lo lee.
3. **Control negativo** (que el canario no fuera vacuo): con el canario puesto,
   quitado el `if gratipide == 0: return` del guardia → `4 failed` con
   `AssertionError: CANARIO: se leyo 'existe'/'fecbaj' en la rama gratipide=0`.

Era equivalente. En vez de pedir que se aceptara un equivalente, T5 eliminó el
valor muerto y la campaña final ya no genera ese mutante: **6 de 6 muertos**.

## Documentación del ecosistema

`azure-apps/sigrid_api.md`, commit **`5e9a7bc`** en ese repositorio (solo ese
fichero; el `.env` sin versionar de la otra sesión no se tocó, y no hubo push):

- **§4**: la fila de `SIGRID_DOCUMENT_ALLOWED_GRATIPIDE` documenta el `0` =
  «sin clase» y que solo vale si se pone explícitamente; la de
  `_ALLOWED_CONTIP` anota que añadir `44` o `14` es lo único que hace falta
  para abrir contratos y albaranes de compra.
- **§8.8**: la fila del campo `gratipide` recoge el `0` y su regla, y un bloque
  nuevo explica qué significa, las mediciones del 2026-09-06 (99,98 % y 100 %),
  que con `0` no se consulta `auxgra`, que hay que ampliar **las dos** App
  Settings, y que las clases > 0 no se relajan.

## Lo que queda fuera y lo que falta

- **Pendiente del humano (MANUAL, criterio 8)**: ampliar las App Settings de
  `func-sigridapi-dev-huyke` a `SIGRID_DOCUMENT_ALLOWED_CONTIP=[708,44,14]` y
  `SIGRID_DOCUMENT_ALLOWED_GRATIPIDE=[35,0]`, y hacer el dry-run y el primer
  `commit:true` sobre un contrato o albarán de la obra **0404** (CUBIERTA NAVE
  14 - JOHN DEERE), con autorización expresa, comprobándolo desde la ficha de
  Sigrid. **Nada de esta sesión tocó la API desplegada ni el ERP.**
- **Fuera de alcance a propósito**: `ALLOWED_WRITE_DATABASES` (sin cambios),
  el resto de `infrastructure/security/`, el repositorio, el constructor de
  sentencias y la ruta. El defecto de las App Settings tampoco cambia: sin
  tocar configuración, el `0` se sigue rechazando exactamente como antes.
- **No se despliega nada** en esta feature: el código queda en la rama, sin
  push, a la espera del reviewer.

## Commits (rama `feature/F-005-grafico-sin-clase`)

| SHA | Tarea |
|---|---|
| `ca2b123` | T1: los 23 tests en fase RED |
| `cec651a` | T2: el guardia admite `gratipide=0` si la lista blanca lo incluye |
| `96500e4` | T3: el modelo baja el suelo a `ge=0` (+ 2 tests F-004 ajustados) |
| `f36a242` | T4: el caso de uso no lee `auxgra` cuando `gratipide=0` |
| `d561731` | T5: un solo punto de llamada al guardia, sin argumento muerto |
| `a072bec` | T6: informe de mutación con el análisis del superviviente |
| `cfb8048` | ajuste: el comentario, delante del `if` que explica |
| `e04d6b1` | campaña relanzada sobre el SHA final |
