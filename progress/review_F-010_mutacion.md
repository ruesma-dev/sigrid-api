<!-- progress/review_F-010_mutacion.md -->
Revisión completa (pasada 1) · bloque MUTACIÓN de C4 bis, sobre `c3d4e45` (punta de `feature/F-010-documents-read-nombres-y-clave`)

# Review F-010 · Bloque mutación (C4 bis + RM1-RM6)

Reviewer, 2026-10-17. Encargo acotado: solo la mutación. Medido en un worktree aislado (detached en
`c3d4e45ad221f227517646e41db8ceb8b6bc9881`) y en una copia (`git archive`) en el scratchpad. Sin
tocar código de la rama, sin commits; worktree limpio al terminar.

## Veredicto del bloque: APROBADO

Nivel de rigor: **`critico`** (declarado en `harness/features.json`). Exige cero supervivientes sin
test nuevo o justificación aceptada por el humano. Se cumple: **23 generados, 23 muertos, 0
supervivientes**, medido por mí y no leído del informe.

## Cifras medidas

| Medición | Resultado |
|---|---|
| Recálculo puro (`alcance_de_feature` + `generar_mutantes`) en HEAD | 7 ficheros, **198 líneas**, **23 mutantes**: igual al informe, fichero a fichero y mutante a mutante (mismo operador, mismo texto original→mutado) |
| Campaña serie, ronda R2 (`--workers 1`, `--salida` en el scratchpad, sin nada más corriendo) | **23/23 muertos**, 0 supervivientes, 0 timeouts, 0 sin veredicto, **153,8 s**, línea base 45,8 s, media 6,7 s, SHA `c3d4e45…` |
| Informe del implementer (`progress/mutacion_F-010.md`) | 23/23, 155,4 s, base 50,2 s, media 6,8 s, SHA `bb4a612…` |
| Campaña serie, ronda R1 (mía, **contaminada**, descartada) | 22 muertos + 1 «superviviente» falso, 240,1 s. Ver «Hallazgo sobre el arnés» |

Las dos rondas válidas (la del implementer y mi R2) coinciden en mutantes, veredictos y tiempo.

## Checkpoints del bloque

- [x] **Mutación**: `progress/mutacion_F-010.md` existe, generado por la herramienta, con totales
      verificados de forma independiente (recálculo puro + reejecución entera).
- [x] **Muertos comprobados, no contados**: el «Tiempo total» declarado (155,4 s) pasa de 60 s, así
      que bastaba el recálculo; **aun así reejecuté la campaña entera** (encargo: medir). R2 = 23/23.
- [x] **Coste por mutante**: 155,4 × 1 ÷ 23 = 6,8 s (> 1 s). Mi R2: 6,7 s.
- [x] **Sin «⚠ CAMPAÑA NO VÁLIDA» ni «Sin veredicto (base rota)» ≠ 0**: ni en el informe ni en R2;
      la línea base corrió y salió verde (50,2 s en el informe; 45,8 s en R2).
- [x] **RM1 · SHA**: el informe midió `bb4a612`; HEAD es `c3d4e45`. `git diff --stat bb4a612..HEAD`
      solo toca `progress/current.md`, `progress/impl_F-010.md`, `progress/mutacion_F-010.md` y
      `tasks.md`: ningún fichero del alcance. Además mi R2 mide sobre HEAD exacto: mismo resultado.
- [x] **RM2 · Coherencia del tiempo**: 23 × 6,8 = 156,4 ≈ 155,4 s; media/base = 0,135 (> 0,1);
      media por debajo de la base, explicada por `-x` con 23 de 23 muertos. Sin salto de orden.
- [x] **RM3 · Ningún equivalente sale muerto** (criterio): repasados los 23; todos cambian
      comportamiento observable (p. ej. `rows[0]→rows[1]` con una fila da `IndexError`;
      `range(0x20,128)` deja pasar DEL 0x7F, que `test_f010_cabecera` vigila).
- [x] **RM4 · Tercera vía**: usada para el mutante cerrado con test nuevo y para 16 mutantes manuales
      complementarios, todo sobre la copia del scratchpad (detalle abajo).
- N/A **RM5 · demostración de equivalentes**: rigor `critico`, pero el implementer **no declara
      ningún equivalente** (el `zip(strict)` se resolvió quitando código, no pidiendo aceptarlo).
      No hay muestra que reproducir.
- [x] **RM6 · Quitar código defensivo**: ver «El `strict=True` era código muerto».

## El mutante que cerró el test nuevo (`sql_models.py:200`, `min_length=1 → 2`)

Aplicado a mano en la copia, `python -m pytest tests/test_f010_modelo.py -q`:
`FAILED tests/test_f010_modelo.py::test_f010_r8_id_column_de_un_caracter_se_acepta_como_hoy` —
**`1 failed, 54 passed`**, idéntico a lo declarado (`String should have at least 2 characters
[type=string_too_short, input_value='a']`). Sin el mutante: `55 passed`.
Contraprueba de que el hueco era real: con el mutante aplicado y **ese test deseleccionado**, la
suite entera queda en `1 failed, 2525 passed, 1 skipped`, y el único fallo es
`test_mutacion_alcance_por_ficheros.py`, que falla igual sin mutante porque la copia no es un repo
git (ambiental). Es decir: sin el test nuevo el mutante sobrevivía; con él, muere.

## El `strict=True` era código muerto (juicio + RM6)

En `bef6a25`, `build_document_query` hacía `safe_key_columns = [validate(c) for c in key]` y
`values = list(key.values())`, y luego `zip(safe_key_columns, values, strict=True)`. Las dos listas
salen **del mismo dict** y `IdentifierGuard.validate_identifier` (`identifier_guard.py:15-21`)
devuelve un `str` o lanza: nunca descarta un elemento. Las longitudes son iguales por construcción;
el `ValueError` de `strict` no podía dispararse con ninguna entrada. Inalcanzable: sí.
RM6: no se quitó una defensa ante un dato ajeno, se eliminó la posibilidad del desajuste. El
invariante se verifica en quien construye el dato (la propia función): ahora compone pares
`(nombre validado, valor)` en una sola pasada sobre `key.items()`, y `values`, `where` y
`condition` salen de esa única lista. Más fuerte que antes. Aceptado.

## ¿Cubre la campaña todo el código de producción cambiado?

El alcance incluye los 7 ficheros de producción del diff (`http_response_factory`, `sql_models`,
`document_models`, puerto, caso de uso, repositorio, `function_app`). Pero el generador solo muta
comparaciones, enteros, lógicos y `not`: **no genera ningún mutante** en `build_document_query`
(formato de SQL), en `filename_header_value` ni en `quote(safe="")`, `document_models` ni el puerto.
Para no dar por cubierto lo que la herramienta no mira, apliqué **16 mutantes manuales** en la
copia (suite entera con `-x`, sin bytecode, `__pycache__` purgado en cada uno). **16/16 muertos**:

| # | Fichero | Original → mutado | Primer test que cae |
|---|---|---|---|
| M1 | repositorio | `TOP (2)` → `TOP (1)` | `test_f010_r11_sql_con_dos_columnas_en_el_orden_de_key` |
| M2 | repositorio | `" AND ".join` → `" OR ".join` | ídem |
| M3 | repositorio | `(IdentifierGuard.validate_identifier(column, …), value)` → `(column, value)` | `test_f010_r11_los_identificadores_salen_validados_y_recortados` |
| M4 | repositorio | `values = [...]` → `[...][:1]` | `test_f010_r11_sql_con_dos_columnas_en_el_orden_de_key` |
| M16 | repositorio | `rows = cursor.fetchall()` → `fetchall()[:1]` | `test_f010_r13_dos_filas_por_key_es_ambiguo` |
| M5 | factory | `quote(file_name, safe="")` → `quote(file_name)` | `test_f010_r4_la_barra_viaja_como_2f` |
| M6 | factory | `"X-Document-Filename": filename_header_value(file_name)` → `file_name` | `test_f010_r1_la_cabecera_es_ascii_imprimible[Factura año señal.pdf]` |
| M7 | factory | `encoding="utf-8", errors="strict"` → `"latin-1", "replace"` | `test_f010_r1_el_primer_caracter_no_ascii_viaja_codificado` |
| M8 | ruta | `except DocumentoAmbiguoError` → `except KeyError` | `test_f010_r13_ambiguedad_da_409_documento_ambiguo` |
| M9 | caso de uso | `"_".join(` → `"-".join(` | `test_f010_r15_reserva_con_dos_columnas_une_los_valores_en_orden` |
| M10 | caso de uso | `key=localizacion` → solo la primera columna | `test_f010_r12_key_llega_tal_cual_y_en_su_orden` |
| M11 | modelo | `limpio.casefold()` → `limpio` | `test_f010_r9_nombres_duplicados_sin_distinguir_mayusculas_se_rechazan` |
| M12 | modelo | `normalizada[limpio]` → `normalizada[nombre]` | `test_f010_r6_los_nombres_se_recortan_y_el_orden_se_conserva` |
| M13 | modelo | `StrictInt \| StrictStr` → `Any` | `test_f010_r6_valor_de_tipo_no_admitido_se_rechaza[None]` |
| M14 | modelo | `"id_value" in model_fields_set` → `id_value is not None` | `test_f010_r15_reserva_con_id_value_null_como_hoy` |
| M15 | `document_models` | `DocumentoAmbiguoError(ValueError)` → `(Exception)` | `test_f010_r13_la_ambiguedad_es_un_valueerror_de_otro_tipo` |

Script y salida: `manuales.py` y `manuales.log` en el scratchpad del reviewer (fuera del repo).
Conclusión: la cobertura de mutación del código cambiado es real también donde el generador es ciego.

## Hallazgo sobre el arnés (no bloquea F-010)

Mi primera ronda (R1) dio **un superviviente falso**: `http_response_factory.py:39` `!= "%"` →
`== "%"`. No es un hueco de tests: ese mutante tumba **8 tests** de `test_f010_cabecera.py`
aplicado en la copia, y muere **3 de 3** veces reproducido en el worktree con la propia maquinaria
de `harness.mutacion` (`_escribir` + `EjecutorPytest().correr`, código 1, primer fallo
`test_f010_r2_unquote_devuelve_el_nombre_original[a%20b.pdf]`); en R2 sale muerto.
**Causa más probable**: el hook `PostToolUse` de `.claude/settings.json` (`Edit|Write` →
`python -m pytest -q`) lanza la suite **en el árbol de trabajo, con bytecode activo**, cada vez que
el agente escribe un fichero, esté donde esté. Mi `Write` de `manuales.py` (19:53:08) cayó en mitad
de R1: un pytest ajeno cargó y compiló módulos del árbol mientras la campaña restauraba y mutaba
`http_response_factory.py` en el mismo segundo y con el mismo tamaño (`!=`→`==`), el caso de `.pyc`
rancio que describe `_purgar_bytecode`. Lo apoyan los `__pycache__` con `.pyc` de pytest 9.1.1 que
aparecieron en el worktree a las 19:49 (hook del `Write` de mi script de recálculo) y que la
campaña no genera. R1 duró 240 s frente a 154 s: ese mutante corrió la suite entera en verde
(~85 s). R1 queda **descartada por escrito**; vale R2. El mismo hook puede fabricar también muertos
falsos (un `.pyc` mutado que sobrevive a la restauración), aunque la línea base final lo delataría.

## Automejora propuesta (no aplicada; la decide el humano)

1. `.claude/settings.json`, hook `PostToolUse`: no correr pytest si existe
   `.arnes_cache/mutacion_en_curso.json`, y lanzarlo con `PYTHONDONTWRITEBYTECODE=1`. Vale para
   cualquier proyecto: portarlo a `arnes-base`.
2. `.claude/agents/reviewer.md` e `implementer.md`: «durante una campaña en serie, ni `Edit` ni
   `Write` en ningún sitio» (el hook se dispara aunque el fichero esté fuera del repo).
3. `harness/mutacion.py`: re-evaluar cada superviviente una vez antes de declararlo; un veredicto
   que cambia entre dos ejecuciones se marca «inestable», no «superviviente».

## Cambios requeridos

Ninguno para F-010 en este bloque.
