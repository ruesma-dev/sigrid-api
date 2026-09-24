<!-- progress/review_F-006_verificacion.md -->
Revisión completa (pasada 1), acotada a C4 y C4 ter, sobre HEAD `22ba2a5` (base `dev` = `210fac1`)

# F-006 · Revisión de verificación (C4 y C4 ter)

- **Alcance:** solo C4 y C4 ter de `CHECKPOINTS.md`. Sin `init.sh` ni suite completa (hay otros
  revisores en paralelo): solo `python -m pytest -q -k f006` y recuentos con `--co`.
- **Nivel de rigor:** `critico` (declarado en `harness/features.json`; estado `in_progress`).
  Exige además las verificaciones `MANUAL (humano)` con su comando exacto y su resultado real.

## C4 — La verificación es real

| Casilla | Estado | Evidencia |
|---|---|---|
| Cada requisito tiene ≥1 test trazable `test_f006_rN_*` y todos pasan | OK | Tabla de abajo; `-k f006` → **229 passed**, 1503 deselected, 5,5 s |
| Los tests no tocan red ni BBDD | OK | `grep requests\|urllib\|pyodbc\|socket\|httpx` en los cinco ficheros: una sola coincidencia, un docstring (`test_f006_use_case.py:136`). Repositorio, cursor, reloj y ajustes son dobles; la ruta dobla `build_dependencies`; `Settings` con `_env_file=None` y entorno vaciado |
| Verificaciones `MANUAL (humano)` listadas con su comando exacto, pendientes | **KO** | Listadas y pendientes (`tasks.md` T15-T18 en `[ ]`, `impl_F-006.md` §7, `current.md` l. 9 remite al guion), pero **T16 y T17 no son exactas** y T17 induce a un error en producción: ver Cambios 1 y 2 |

### Trazabilidad requisito → test (recuento de funciones `def test_f006_rN`)

| R | Nº | Tests representativos (todos en verde) |
|---|---|---|
| R1 | 22 | `models`: obligatorios, longitudes 24/80/128/48, `extra="forbid"` con `ide/cod/emp/est/pos`, `forma_comunicacion` 0/1, ≤10 intervinientes; `route::r1_un_cuerpo_invalido_sale_como_400_solicitud_invalida` |
| R2 | 6 | `models::r2_la_respuesta_tiene_la_forma_de_la_spec`, estado y motivo cerrados; `route::r2_un_lote_con_partes_rechazados_responde_200` |
| R3 | 14 | `use_case::r3_*` (base fuera, **lista vacía**, tope, serie, estado, obra, usu) sin leer; `route::r3_*` 400 con `details.codigo` y 500 con `exception` |
| R4 | 4 | `settings::r4_los_cuatro_ajustes_nuevos_arrancan_con_defecto_seguro` (+ JSON/CSV, alias, entorno) |
| R5 | 2 | `settings::r5_*` (defectos existentes intactos y `local.settings.sample.json`) — ver nota 1 |
| R6 | 10 | `statements::r6_l1..l7` (SQL literal); `use_case::r6_las_lecturas_comunes_se_hacen_una_vez_y_en_orden`, lectura truncada, `emp` de la serie |
| R7 | 12 | `use_case::r7_*`: cada código con el parte siguiente `previsto` y sin gastar número |
| R8 | 12 | `use_case::r8_*`: no está, ambiguo, idénticas por menor `pos` (NULL=0, desempate por `ide`), repetido, solo aviso |
| R9 | 5 | `use_case::r9_el_dry_run_no_abre_transacciones_y_numera_en_provisional`, cinco filas completas |
| R10 | 3 | `use_case::r10_el_commit_exige_las_llaves_antes_de_leer` (4 variantes: 2 llaves y 2 credenciales) |
| R11 | 15 | `statements::r11_fila_*` y `insert_con_literal`; `use_case::r11_work_ejecuta_e1_a_e14_en_orden`, una transacción por parte |
| R12 | 8 | `statements::r12_e2_cod_bajo_bloqueo`, `e3_a_e7`, `siguiente_cod`, `pasado_9999`; `use_case::r12_*` agotada en dry-run y commit |
| R13 | 3 | `use_case::r13_una_colision_repite_la_transaccion_entera_con_numeros_nuevos`, colisión persistente |
| R14 | 5 | `use_case::r14_*` (relectura de las 5 tablas, que falta, revalidación antes de insertar) |
| R15 | 5 | `statements::r15_l8`; `use_case::r15_*` dry-run, conflicto (otra UPV, sin UPV, varios), commit dentro de la transacción |
| R16 | 7 | `statements::r16_*` (OLE UTC verano/invierno, cambio de mes en Madrid, sellos inmutables); `use_case::r13_...` comprueba `ahora.llamadas == 1` en el reintento |
| R17 | 3 | `use_case::r17_*` (presupuesto, configurable, `error_de_escritura` sin reintento) |
| R18 | 5 | `statements::r18_*`: 30 sentencias sin verbos prohibidos ni literales, guardia real sin rechazo, constructor autovalidado |
| R19 | 1 (+1) | `use_case::r19_ninguna_sentencia_ejecutada_toca_tar_ni_pasa_a_pte`; `statements::r18_ninguna_sentencia_toca_tar_ni_graficos` |
| R20 | 3 | `use_case::r20_*`: traza por lote y por parte sin descripciones, también en fallo y excepción |
| R21 | N/A | Es el requisito de los propios tests: se cumple con las 20 filas anteriores, el SQL literal y la fase RED de R11-R15 (`impl_F-006.md` §5, salida real contra esqueleto `NotImplementedError`, 22 fallos). No lleva test propio porque sería autorreferente |
| R22 | MANUAL | T15-T18, pendientes del humano (ver C4, casilla 3) |
| R23 | N/A | Documental; lo coteja el revisor de documentación, fuera de este encargo |

**Calidad de los tests (lo pedido explícitamente):**

- **SQL carácter a carácter:** L1-L10, E2-E8, E14 e `INSERT` de `con` comparados contra literales
  escritos en el test (`test_f006_statements.py:48-191, 360-366`). Los `INSERT` de `rcp`, `rcpint`,
  `conext` y `log` se comparan con una plantilla del test sobre las tuplas de columnas, que a su vez
  están fijadas literalmente (`:197-217`): equivale a literal, no es SQL contra sí mismo.
- **Sin tautologías relevantes:** los dobles no se verifican a sí mismos. El cursor doble contesta
  las relecturas con lo que se insertó en ese intento, y el bucle de reintentos del repositorio doble
  reproduce el real (`sql_server_repository.py`, `attempt > max_retries: raise`), comprobado.
  `_NOMBRES` usa el constructor solo para poner nombre a las sentencias; su SQL lo fija el otro fichero.
- **Nota 1 (no bloquea):** la primera aserción de `test_f006_r5_allowed_write_databases_sigue_siendo_solo_ruesma`
  pasa `ALLOWED_WRITE_DATABASES="ruesma"` y comprueba que vuelve `["ruesma"]`: solo prueba el
  parseo. R5 queda demostrado por el resto del test (defectos existentes y fichero de ejemplo) y por
  el diff (C4 ter), no por esa línea.

## Evidencias del informe del implementer

| Evidencia | Estado | Comprobación independiente |
|---|---|---|
| 229 tests de F-006 (85/76/45/13/10) | OK | `-k f006` → 229 passed; `--co` por fichero: use_case 85, models 76, statements 45, settings 13, route 10. Coincide exacto |
| Del commit final | OK | `git diff --stat 22e23f7..HEAD`: solo `progress/*` y `tasks.md`. El código y los tests medidos por la mutación (`22e23f7`) son los de HEAD |
| Mutación 217/217, SHA `22e23f7e9a…`, 1.355,1 s | OK (cabecera) | `mutacion_F-006.md` l. 23-31 coincide con `impl` §6. Reejecución y RM1-RM6 son de C4 bis, fuera de este encargo |
| 1.731 tests, cobertura 100 % de 560 líneas, `ENTORNO LISTO` | No verificado aquí | Exige `init.sh`, que este encargo prohíbe: lo verifica el revisor de C1/C4 bis |

## C4 ter — Rutas sensibles

**`harness/rutas_sensibles.json` no existe** (solo `rutas_sensibles.ejemplo.json` y el módulo). Por
el texto del checkpoint el bloque es **N/A formal**: sin declaración no hay informe que exigir. Se
aplica el criterio a mano, como pide el encargo, sobre `config/settings.py`, `function_app.py` y la
escritura en producción:

| Verificación extra | Estado | Evidencia |
|---|---|---|
| Defectos cerrados de las cuatro App Settings | OK | `git diff dev...HEAD -- config/settings.py`: `WRITE_ENABLED=False`, `MAX_PARTES=50`, `PREFIJOS=default_factory=list`, `PRESUPUESTO=150`. Probado por `r4_los_cuatro_ajustes...` y, en uso, `r7_sin_prefijos_configurados_toda_referencia_se_rechaza` y `r10_*`. Sample: `false/50/""/150` |
| `ALLOWED_WRITE_DATABASES` intacta | OK | Diff de `settings.py` solo añade (+16/−0); la única línea tocada fuera del bloque nuevo añade el campo al validador `parse_string_list` existente, sin alterar los demás. Sample sigue en `"ruesma"`. `azure-apps/sigrid_api.md` no la cambia |
| `infrastructure/security/` sin tocar | OK | `git diff dev..HEAD --stat -- infrastructure/security/` → vacío. Tampoco `infrastructure/`, `domain/ports/` ni `infra/` |
| `function_app.py` solo añade | OK | 0 líneas `-`; +57: imports y la ruta nueva. `ValidationError` se captura antes que `ValueError` (es subclase) |
| Doble llave y credenciales antes de leer | OK | `create_partes_reclamacion_use_case.py:264-267` exige `sigrid_domain_write_enabled` **y** `sigrid_reclamacion_write_enabled` **y** usuario y contraseña de escritura; `:277` base en lista (vacía → rechazo) |
| Escritura en producción | Pendiente (humano) | Nada escrito contra Sigrid (`impl` §4 y §9: 2 `sql/read`). Las escrituras son T17-T18, manuales; ver Cambio 1 |

## Cambios requeridos

1. **`specs/F-006-alta-parte-reclamacion/tasks.md:22` (T17) — el guion puede cortar el commit de otros
   endpoints en producción.** Dice «con `SIGRID_RECLAMACION_WRITE_ENABLED=true` y
   `SIGRID_DOMAIN_WRITE_ENABLED=true` solo durante la ventana». `SIGRID_DOMAIN_WRITE_ENABLED` **ya está
   en `true`** en la instancia (`azure-apps/sigrid_api.md:330`) y de ella depende el commit de los
   demás endpoints de dominio (albaranes, `concepto-grafico`, abierto por orden del humano). Cerrar esa
   ventana tal como está escrita los apagaría. Reescribir T17 con:
   a) que `SIGRID_DOMAIN_WRITE_ENABLED` **no se toca**;
   b) el comando exacto para abrir **solo** `SIGRID_RECLAMACION_WRITE_ENABLED=true`, con el mismo
      patrón `az functionapp config appsettings set ... --settings "@fichero.json"` de T15;
   c) el comando exacto para cerrarla (`false`) **después de T18**, porque la idempotencia en
      `commit:true` también exige la llave (R10). Verificarlo con el `appsettings list` de T15.
2. **`tasks.md:21` (T16) — los dos negativos no tienen cuerpo literal, y el obvio falla por otro
   motivo.** El orden de validación (`create_partes_reclamacion_use_case.py:434-460`) es prefijo →
   referencia duplicada → UPV → … → oficio → intervinientes. Si el humano copia el parte válido y solo
   cambia la UPV, sale `referencia_duplicada_en_lote`, no `unidad_postventa_no_encontrada`. Si en el
   segundo negativo cambia también el `oficio` del parte, sale `oficio_no_esta_en_la_obra`. Escribir el
   JSON completo del lote de tres partes con:
   - referencias distintas con prefijo `PVI-` (p. ej. `PVI-PRUEBA-0002` y `PVI-PRUEBA-0003`);
   - en el tercero, `oficio` `0039` y un interviniente con un oficio **existente en `auxofc` pero sin
     `obrofc` en la obra 0626**, elegido y citado con su lectura por `sql/read`.

   Dar además el parámetro literal del `LIKE` (`RS<aa>.<mm>/[0-9][0-9][0-9][0-9]` del mes de la
   prueba). Trasladar los dos arreglos a `impl_F-006.md` §7.

## Propuesta de automejora (no aplicada)

- `CHECKPOINTS.md` C4, casilla 3: dice «listadas en `progress/current.md` con su comando exacto».
  Este arnés prohíbe duplicar y aquí `current.md` remite a `tasks.md`. Proponer: «listadas en
  `tasks.md` (o `current.md`) con su comando exacto **y revisado contra el estado desplegado**
  (`azure-apps/`)». Lo segundo es lo que habría cazado el Cambio 1.

VEREDICTO PARCIAL: CAMBIOS
