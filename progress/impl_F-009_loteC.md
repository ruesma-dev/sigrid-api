<!-- progress/impl_F-009_loteC.md -->
# F-009 · Informe del implementer · Lote C (T7-T12)

Rama `feature/F-009-alta-albaran-compra`, 2026-10-06. Spec v8.2. Nivel `critico`. Sin red, sin Azure, sin SQL Server.
Commits locales, uno por tarea:

| Commit | Tarea |
|---|---|
| `c4fb55b` | T7: caso de uso, resolución de cabecera y de líneas, previa |
| `0ed5573` | T8: idempotencia por `synckey` (previa y E1 en la transacción) y prefijo |
| `d4e695d` | T9: tests de la previa (solo lecturas, preview completo, sin bancarias) |
| `65f4ae6` | T10: commit (guardas, E1-E12 reentrante, reintento, relecturas) |
| `f60d9a5` | T11: tests de devoluciones de punta a punta |
| `1c10f72` | T12: equivalencia con el modo clásico |

**Ficheros**: nuevo `application/use_cases/create_albaran_compra_use_case.py`; tests nuevos
`tests/test_f009_use_case.py` (155) y `tests/test_f009_equivalencia.py` (2); dobles y datos de mentira en
`tests/f009_dobles.py` (no es de tests: lo importan los dos). `tasks.md` (T7-T12 `[x]`) y `progress/current.md`.
**Sin tocar** (comprobado con `git log bee6716..HEAD -- …`, vacío): casos de uso y modelos del clásico y de
`albaran-directo`, `domain/`, `infrastructure/` (security incluida), `config/`, `function_app.py`, `.env` y el dorado
de T1. `contrato_albaranes.md` no cambia: el código no ha obligado a tocar forma, campos, códigos ni estados.

## Qué se hizo, por tarea

**T7** · `CreateAlbaranCompraUseCase(repository, settings, ahora_utc=...)`. Cabecera (R11): L1 filtrado por
`SIGRID_ALBARAN_EMPRESAS_OBRA`; `locate_contract` + solo los de esa obra, `read_full_row(ctr)`, `read_rows_by(ctrpro)`;
L5 por `entide` del contrato o, sin él, por CIF normalizado, ambos con `emp` de la obra; `con`/`dca` de la plantilla.
Líneas: un `_Catalogo` lee UNA vez cada lista (L6 partidas, L7 productos, L15a-c naturaleza, cuenta y analítica) y,
validadas todas, completa (L7b `tipmov`, L8b/L8 plantilla, L9 IVA). Construcción con las funciones del lote B; el
balance se encadena con el `pre` ESCRITO y `dcapro.prepma` = `mov.prepma` o 0.
**T8** · R29 antes de leer; L11 tras la plantilla y antes de `conest`/`usu`; E1 dentro, primera sentencia de `work`.
**T9** · Sin código nuevo: la previa salió en T7; los tests fijan R7 y R23.
**T10** · Guardas de R24 y `work` con E1 → E2-E7 → `numerar` → E8 → E9-E11 (solo con vinculadas) → E11b → E12.
**T11** · Sin código nuevo: devoluciones por el mismo camino (T7 y T10). **T12** · Test de equivalencia.

## Decisiones de interpretación (para el reviewer y el líder)

Ninguna cambia lo que se escribe en Sigrid más allá de la spec; las que tocan la respuesta no cambian el contrato §3.
1. **Obra y lista vacía** (R11): sin obra en ninguna empresa → `obra_no_encontrada`; si existe y la lista está vacía o
   no la incluye → `obra_de_empresa_no_permitida`. Contrato del localizador de otra obra: se descarta; ninguno de esta
   obra o `ctr` ilegible → `contrato_no_encontrado`.
2. **Proveedor sin contrato**: `entide` = el de la `dca` plantilla (hallada por CIF); `dca.ent*` de la plantilla
   (`construir_dca` con `None`). Ese `entide` es el de L8b, el `mov.oriide` y el de la comparación de R30.
3. **Almacén de las sin vincular** (R15, M16): contrato si `ctr.almide` ≠ 0; si no, ficha de obra si `obr.almide` ≠ 0;
   si no, el único `alm` de la obra. El `cenide` sale de la MISMA fuente. «Sin él» se lee como «sin almacén del
   contrato» (cubre contrato con `almide` 0). Solo se resuelve si hay sin vincular; `almacen_de_obra_no_resuelto` es de
   cabecera y corta antes de validar líneas. `dca.almide/cenide` = ese almacén si se resolvió (el del contrato cuando lo
   tiene) y, si no, el del contrato, como el clásico. La variante L10 `OR ide IN (…)` no se usa.
4. **Vinculada**: almacén/centro `ctrpro or ctr` (como el clásico); `producto_sin_historico` también si L8 no da
   plantilla (el clásico ya avisaba). `producto` de su `LineaResultado` va `None`: su código exigiría una lectura que
   L7b no trae y no se añade SQL.
5. **Fallos por línea** (R9): una línea puede dar VARIOS si son independientes, en este orden: origen (`ctrpro`, o la
   cadena producto → naturaleza → analítica, que corta en el primero), partida y precio. Errores de cabecera cortan antes.
6. **Avisos de seguimiento**: `supera_pendiente` con lo servido ACUMULADO por `ctrpro` en el albarán (líneas positivas)
   frente a `can − canser` (como el clásico, a 2 decimales); `servido_negativo` igual en devoluciones. Orden de avisos
   de una línea: partida, precio, seguimiento, IVA/histórico y `stock_negativo` (este, con el balance del intento que
   escribe: E7 en commit, L12 en previa).
7. **IVA**: `ivaide` 0 (sin histórico) → 0; un `ivaide` ≠ 0 que no esté en `dbo.iva` → `ValueError` (400 de texto,
   sin escribir; no invento código). Producto de un `ctrpro` ausente de L7b → sin `mov` (no tiene `tipmov` = 1).
8. **Comparación de códigos** (partida, producto, naturaleza, cuenta, analítica): recortados y sin mayúsculas, como
   F-006 (`Modern_Spanish_CI_AS`). Lista blanca, mapeo y prefijos: exactos (distinguen mayúsculas).
9. **Idempotencia**: L11 se lee también en commit fuera de la transacción (si aparece, sale sin abrirla); la
   autoritativa es E1. Sale antes de `conest`/`usu` y sin validar líneas. `fec` va en `cabecera = {"fec": …}`;
   `totales` = `{totbas, totdoc, n_lineas}`; `cod` y `refent` recortados; el resto vacío.
10. **`estados_contrato`**: `{}` sin vinculadas (también con contrato). Previa: sumas leídas + lo servido; commit: E10.
11. **Reservas**: E5/E6 solo si hay `ctrprodes`/`mov`; E11b al final (design): `numerar(..., ide_log=0)` y luego se
    pone el `ide` reservado. Previa: `peek` de las cinco tablas siempre (design L14).
12. **`colision_de_clave`** en el caso de uso, reconociendo `IntegrityError` por nombre (como F-006); cualquier otro
    error de la base sube tal cual (500). El `except` de `function_app.py` para esto (design) queda redundante.
13. **`reloj`** (design: constructor) no se añade aún: solo lo usaría la traza R32, que es T15 (lote D).
14. Orden de guardas: tope (`demasiadas_lineas`), prefijo y, con commit, llaves y base (vacía no abre).

## Fase RED (trazas reales; tests escritos antes que el código)

**T7 (R11, R13b, R14, R15)** · `.venv/Scripts/python.exe -m pytest tests/test_f009_use_case.py -q -p no:cacheprovider
-k "r9 or r11 or r12 or r13 or r14 or r15 or r16 or r17"`, sin el módulo:
```
tests\test_f009_use_case.py:16: in <module>
    from application.use_cases.create_albaran_compra_use_case import CreateAlbaranCompraUseCase
E   ModuleNotFoundError: No module named 'application.use_cases.create_albaran_compra_use_case'
1 error in 0.19s
```
Para tener el fallo test a test, con un esqueleto cuyo `run` lanza `NotImplementedError` (mismo comando y, después,
`-k "r11 or r13b or r14 or r15"`):
```
     85 E       NotImplementedError
85 failed, 1 deselected in 4.12s
FAILED tests/test_f009_use_case.py::test_f009_r11_obra_por_empresa[obras1-empresas1-obra_de_empresa_no_permitida]
FAILED tests/test_f009_use_case.py::test_f009_r15_analitica_no_resuelta[solo_prefijo]
58 failed, 28 deselected in 2.15s
```
**T8 (R30)** · con el código de T7 (sin idempotencia ni prefijo), `-k "r29 or r30"` y `-k r30`:
```
      6 E       Failed: DID NOT RAISE AlbaranCompraError
      6 E           NotImplementedError: El commit del modo extendido llega en T10.
      2 E       AssertionError: assert 'previsto' == 'idempotente'
      1 E         At index 2 diff: 'conest' != 'referencia'
16 failed, 1 passed, 88 deselected
FAILED tests/test_f009_use_case.py::test_f009_r30_previa_idempotente_sin_seguir_leyendo
FAILED tests/test_f009_use_case.py::test_f009_r30_commit_dentro_de_la_transaccion_antes_de_reservar_nada
FAILED tests/test_f009_use_case.py::test_f009_r30_commit_conflicto_dentro_de_la_transaccion
10 failed, 95 deselected in 1.26s
```
**T10 (R26-R28)** · con el código de T8 (`work` solo con E1), `-k "r20 or r24 or r25 or r26 or r27 or r28 or r19 or
r21 or r31"` y `-k "r26 or r27 or r28"`:
```
     27 E       NotImplementedError: Las reservas y los INSERT llegan en T10.
      1 E       Failed: DID NOT RAISE AlbaranCompraError
      1 E         Actual message: 'Las reservas y los INSERT llegan en T10.'
29 failed, 4 passed, 114 deselected
FAILED tests/test_f009_use_case.py::test_f009_r27_reintenta_la_transaccion_entera_recalculando
FAILED tests/test_f009_use_case.py::test_f009_r28_si_no_cuadran_rollback_con_codigo[releer_dcapro-1]
15 failed, 132 deselected in 2.64s
```
(Los 4 que pasaban: los de R19/R21 en previa —O3, ya cubiertos por T7— y `r24_en_el_tope_vale`.) T9, T11 y T12 no
piden RED (R34): sus tests pasaron al escribirlos, salvo tres expectativas de datos del propio test que corregí
(`almpma` sin redondear, 2,6749999…; y `stock_negativo` que sí tocaba en dos devoluciones).

## Verificación de cada tarea (salida real, tras el último commit)

| Tarea | Comando | Resultado |
|---|---|---|
| T7 | `pytest tests/test_f009_use_case.py -k "r9 or r11 or r12 or r13 or r14 or r15 or r16 or r17"` | `86 passed, 69 deselected` |
| T8 | `… -k "r29 or r30"` | `17 passed, 138 deselected` |
| T9 | `… -k "r7 or r23"` | `9 passed, 146 deselected` |
| T10 | `… -k "r20 or r24 or r25 or r26 or r27 or r28"` | `32 passed, 123 deselected` |
| T11 | `… -k "r18 or r20"` | `10 passed, 145 deselected` |
| T12 | `pytest tests/test_f009_equivalencia.py` | `2 passed` |
| R2-R4 | `pytest tests/test_f009_caracterizacion.py` (dorado intacto) | `17 passed` |
| F-009 | los seis ficheros `tests/test_f009_*.py` | `551 passed in 2.04s` |

Lo que fijan, además de lo obvio: el SQL de cada lectura y de cada sentencia de la transacción es el EXACTO del
constructor (el doble falla con cualquier otro) y sus parámetros; la secuencia completa de `work` y los siete applocks
en su orden; los `INSERT` llevan exactamente las filas devueltas (y la `dca` escrita, las bancarias); en la
transacción solo los dos `UPDATE` de R25 y ningún `DELETE`; sin vinculadas, ni un `UPDATE` aunque haya contrato (H31);
`mov` si y solo si `tipmov` = 1 con `dcapro.prepma` = `mov.prepma` o 0, encadenado (O3); `mov.pre` y el balance con el
`pre` escrito (condición b); el aviso de precio con `usa_precio_del_contrato` (condición a: δ = 0,00005 con 25.000 uds
avisa aunque `precio_coincide` diga sí); reintento que recalcula `cod`, `ide` y balance desde filas limpias; seis
relecturas que no cuadran → `filas_afectadas_inesperadas` sin reintentar.
**T12**: las filas construidas por los dos modos (espiadas en `_assign_ides` del clásico y en `numerar` del extendido,
con `monkeypatch`, sin tocar el clásico) tienen las mismas columnas en el mismo orden y difieren EXACTAMENTE en
`dca.synckey`; `dcapro` `prepma`, `refent`, `cod2`, `dncide`, `dncproide`; `mov` `fec`, `fechor`, `prepma`. Todas
declaradas en design §Equivalencia (v8.2); el test además rechaza cualquier diferencia fuera de esa lista. Con la fecha
de hoy, en el `mov` solo queda `prepma`.

## `bash harness/init.sh` (final)

Tal cual, tras el último commit de código (ruff: 80 avisos de deuda previa; los ficheros del lote, limpios):
```
2284 passed, 1 skipped, 1 warning in 74.80s (0:01:14)
[OK] pytest en verde (con medición de cobertura)
[OK] PUERTA COBERTURA: 100.0% de 1042 líneas cambiadas cubiertas (1042/1042, umbral 80%, nivel critico)
[OK] PUERTA TAMAÑO: F-009 dentro de los topes (requirements 150/150, design 250/250, impl 196/220, review 117/140)
[OK] Rama actual: feature/F-009-alta-albaran-compra
ENTORNO LISTO. Puedes trabajar.
```

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados (suite completa) | 2284 passed, 1 skipped (`bash harness/init.sh`) |
| Tests nuevos del lote | 157 (155 de `test_f009_use_case.py` + 2 de `test_f009_equivalencia.py`), todos en verde |
| Cobertura de las líneas cambiadas | **100,0 %** (1042/1042, umbral 80 %, `critico`), línea `PUERTA COBERTURA` |
| Mutantes generados y supervivientes | **No medido en este lote**: la campaña de rigor `critico` es T16 (lote E), sobre la feature entera, como fijó el plan aprobado en la PARADA 1 |
| Tiempo de la suite | 74,80 s la suite completa con cobertura; los seis ficheros de F-009, 2,04 s |

## Observaciones del lote B, atendidas

O3 (R19/R21 en el caso de uso): `test_f009_r19_mov_si_y_solo_si_tipmov_1_y_prepma_de_su_mov_o_0`,
`test_f009_r21_prepma_encadenado_…`, `test_f009_r19_el_mov_lleva_el_pre_escrito_en_la_fila`. O2: cubierta por T12 con
la v8.2. Condiciones (a) y (b) del reviewer: arriba. O3 del trozo 1 (`contrato` no es la fila `ctr`): la respuesta lleva
un resumen (`ctride`, `obride`, códigos, `entide`, `almide`, `template_ide`), fijado en `test_f009_r7_superconjunto_…`.

## Lo que queda para el lote D (T13-T15) y después

- **T13** `function_app.py`: elegir modo (R1); extendido → `CreateAlbaranCompraUseCase(repo, settings)`; el `except
  AlbaranCompraError` ANTES de los `except ValueError` (O4 del lote B, hereda de `ValueError`), con `details.codigo` y,
  si es `lineas_no_validas`, `details.lineas` (`model_dump` de `FalloLinea`); guarda R8 en las dos rutas. La colisión ya
  llega como `AlbaranCompraError(colision_de_clave)` (decisión 12).
- **T15** trazas R32: añadir `reloj` al constructor (decisión 13) y trazar en `run` sin textos, precios ni bancarias.
- **T14** comprobación de R2-R4 (hoy, `git diff dev` vacío en el clásico y `albaran-directo`; el dorado solo con T1).
- **T16** mutación sobre el lote B y C juntos; **T17-T18** documentación (la decisión 3 —almacén con contrato sin
  `almide`— y la 9 —`fec` del `idempotente` en `cabecera`— conviene reflejarlas en `azure-apps/sigrid_api.md`).
- Verificación manual (T21-T24) de lo que ningún doble puede probar: `prepma` real, analítica `0404.CDSB37` en el
  centro del contrato y la primera devolución.
