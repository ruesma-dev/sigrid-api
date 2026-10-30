<!-- progress/review_F-008.md -->
Revisión incremental desde `2879ddb` (pasada 2, consolidada): delta de la ronda `8ca7a4f..d0fc6e6` + `92067d9` en azure-apps

# F-008 · Review consolidada (T21)

**Veredicto: APPROVED**, con las condiciones para el humano de la sección final.

- **Nivel de rigor:** `critico`, declarado en `harness/features.json`. Exige tests trazables, fase RED con salida
  real, cobertura ≥ 80 % de lo cambiado, mutación con 0 supervivientes sin justificar y RM1-RM6 (RM5 con muestra).
- **Base:** lo aprobado o juzgado en los siete informes troceados de `2879ddb` (`review_F-008_{logica_lectura,
  logica_escritura,C3C4ter,C4red,mutacion,docs,C1C2C5}.md`) queda dado por bueno. Aquí se revisa solo el delta:
  `a837ab0`, `9cea72f`, `23207dd`, `215aff4` (código y tests), `4824027`, `7438910`, `d0fc6e6` (documentos). El delta
  no cambia firmas públicas salvo `construir_con_pago(..., est)`, que es interna y tiene un único llamante.
- **Árbol:** principal sin tocar ni cambiar de rama. Las mutaciones se hicieron en un worktree detached del
  scratchpad, borrado al acabar (`git worktree list` muestra solo el principal y `git status` está limpio).

## Medición propia en `d0fc6e6`

- `bash harness/init.sh`: exit 0, `4211 passed, 1 skipped, 1 warning in 70.09s`, `ENTORNO LISTO`.
- `PUERTA COBERTURA: 99.3% de 1201 líneas cambiadas cubiertas (1192/1201, umbral 80%, nivel critico)` `[OK]`.
- `PUERTA TAMAÑO: requirements 149/150, design 229/250, impl 176/220`. `python -m harness.tamano --feature F-008` da
  exit 0. Este informe tiene ≤ 140 líneas.
- `pytest tests -k f008 --collect-only`: **418**, es decir, 411 más los 7 de la ronda.

## Hallazgos bloqueantes de la pasada 1 → estado → evidencia

| # | Hallazgo (informe) | Estado | Evidencia |
|---|---|---|---|
| 1 | `con 25` con `est=1` literal (C3C4ter H1, escritura 1) | **Corregido** | `create_factura_use_case.py:381` añade `(TIP_PAGO, PDT)` a `necesarios`; `:180-182` `est_pago`; `:836` lo pasa a `construir_con_pago` (`factura_statements.py:136-145`, `est=est`). Tests `test_f008_r32_el_con_del_pago_nace_en_el_pdt_de_conest` (PDT=7 → `[7]`) y `..._sin_pdt_en_conest_no_se_da_de_alta`. Mutantes D y B abajo: muertos |
| 2 | `paride` sin `partida` descartado en silencio (lectura 1) | **Corregido** | `factura_models.py:188-190` → `ValueError` (400 sin `codigo`, como F-009 R14b). Test `test_f008_r25_paride_sin_partida_es_400` (también el caso válido con `partida`). Tres mutantes, los tres muertos |
| 3 | Orden de `retencion_no_soportada` (lectura 2) | **Corregido** | Se movió a `create_factura_use_case.py:301-302`, tras `_sin_origen` y antes de `_montar`; `_lineas_de_origen` y `_sin_origen` no usan `retencion`. Tests `test_f008_orden_lineas_de_origen_antes_que_retencion`, `..._sin_origen_antes_que_retencion` y `..._retencion_antes_que_totales`. Mutante C abajo: muerto |
| 4 | Justificación falsa de la D4 (escritura 2) | **Corregido (opción a)** | `impl_F-008.md:58-61` y `:86-87`: R40 lo sostiene `UPDLOCK, HOLDLOCK` y la relectura comprueba el estado final; reconoce que `@@ROWCOUNT` funcionaría |
| 5 | R16 sin test trazable (C4red 1) | **Corregido** | `test_f008_r16_solo_lineas_con_can_distinta_de_cero` (`tests/test_f008_transaccion.py:311-318`): 8002 fuera de `dcfpro` y de `dcaprodes`, `canfac` 0. Su RED, con la regla rota, está pegado en `impl:126` |
| 6 | MANUAL sin enlace en `current.md` (C4red 2) | **Corregido** | `current.md:11-17` enlaza `verificacion_manual.md` junto a T22-T24 |
| 7 | T23 imposible sin App Settings (docs 1) | **Corregido** | `verificacion_manual.md` D1: los valores JSON, `FAC-` pendiente de P15 y la llave sin cargar o en `false` |
| 8 | `referencia_externa` sin formato (docs 2) | **Corregido** | Formato fijo `FAC-VERIF-F008-<previa>-<n>`, anotado junto a `con.ide` |
| 9 | D2/T24.5 `commit:true` a ciegas (docs 3) | **Corregido** | D3 lee las App Settings y para si la llave sale `true`. D4 usa un cuerpo fijo `NOADMITIDA-D2`. Comprobado contra el código: con la llave cerrada, la ruta responde `escritura_facturas_deshabilitada` (`function_app.py:423, 457-465`) antes del caso de uso; con la llave abierta, el caso de uso responde `referencia_no_permitida` (`create_factura_use_case.py:330-335`) antes de leer o escribir. El cuerpo valida contra `FacturaRequest`: lo ejecuté con `model_validate_json` y salió `ok` |
| 10 | Llaves dobles en §8.11 (docs 4) | **Corregido** | azure-apps `92067d9`: `{linea: …}` y `{fecha, importe}` |
| 11 | Respuesta incompleta en §8.11 (docs 5) | **Corregido** | `92067d9` añade `database`, `committed`, `dry_run` y `referencia_externa` |
| 12 | Códigos de línea y `SIGRID_ALBARAN_EMPRESAS_OBRA` en §8.11 (docs 6) | **Sin corregir; lo rebajo a condición C3** | Motivo abajo |
| 13 | `current.md` contradictorio o caducado (C1C2C5 H2) | **Corregido** | Se quitaron la frase «en curso» y la sección «F-008 espera». F-008 está ya en el «Prompt para retomar» (`current.md:188-190`) |
| 14 | Commits agrupados (C1C2C5 H1) | **Declarado, sin historia reescrita** | `impl_F-008.md:26` y la desviación 7 (`:91-94`), con su motivo. Queda como **condición C1** |

**Por qué el 12 no bloquea.** R48 exige documentar «la ruta, los ajustes, los applocks y lo que no hace», y eso
está. §8.11 ya anuncia `lineas_no_validas` con `details.lineas`. Lo que falta es la lista de los 11 códigos de
`CODIGOS_LINEA_FACTURA` (`factura_models.py`) y la frase que dice que la obra se busca en
`SIGRID_ALBARAN_EMPRESAS_OBRA` (`create_factura_use_case.py:415, 450`). Las dos cosas las necesita el consumidor
`facturas`, pero ninguna cambia el comportamiento ni la seguridad. El implementer lo dejó fuera por encargo del líder
(`impl:151-153`), y §8.11 sigue marcada «pendiente de despliegue». Se exige **antes de T23** (condición C3).

## Lo que debía quedar fuera sigue fuera

- **Origen con todas sus líneas a `can` 0** (O1 de lectura): no hay ningún rechazo nuevo. `grep origen_sin_lineas`
  no da nada en `*.py`, y el filtro de `can` no cambió fuera del test de R16. Está anotado como pendiente en
  `current.md:13-14` y en `impl:151-152`. Queda como **condición C2**.
- `infrastructure/`, `.env` e `infra/` no aparecen en el delta. No hay `print` ni `breakpoint`. Los 7 commits de la ronda
  están en español y llevan `Co-Authored-By`.

## Código nuevo, mirado con ojo crítico

- **PDT siempre necesario.** Es correcto: el modelo exige 1-12 vencimientos (R32), así que toda factura crea algún
  `con 25`. Como efecto lateral, una petición idempotente con un `conest` sin PDT daría `estado_inicial_no_encontrado`.
  Ya pasaba igual con REC y RECH: es seguro y no bloquea.
- **Validador `paride`/`partida`.** Va en `_coherencia`, dentro del bucle que recorre las líneas de la serie. En FRGG
  las dos claves son `None` (otra serie es 400), así que el validador no puede saltar en falso. El mensaje cita el
  índice, no valores del llamante (R1).
- **Orden de la retención.** Ahora coincide con el texto de la decisión (`impl:50-51`). Sigue en pie la O2 de lectura:
  las guardas van `demasiadas` → prefijo → llaves, y design §7 dice llaves → prefijo. Es sin efecto, porque la llave
  propia la aplica antes la ruta. No bloquea.

## Mutantes de la ronda, reproducidos (worktree propio, `-x -k f008`, base 418 en verde)

| Mutante (texto original → mutado) | Resultado |
|---|---|
| A `paride is not None and partida is None` → `... or ...` (`factura_models.py:189`) | MUERTO, exit 1 (`test_f008_r1_el_cuerpo_minimo_vale_con_sus_defectos`) |
| `paride is not None` → `paride is None` (con `aplicar_mutante`) | MUERTO (`..._r1_el_cuerpo_minimo_vale...`) |
| `partida is None` → `partida is not None` (con `aplicar_mutante`) | MUERTO (`test_f008_r25_paride_sin_partida_es_400`) |
| B quitar `(TIP_PAGO, PDT)` de `necesarios` (`create_factura_use_case.py:381`) | MUERTO (`..._r32_sin_pdt_en_conest_no_se_da_de_alta`) |
| D `est=ctx.est_pago` → `est=1` (`:836`), mutante propio, no estaba en el informe | MUERTO (`..._r32_el_con_del_pago_nace_en_el_pdt_de_conest`) |
| C volver la retención al paso 5 | MUERTO, 2 fallos (`test_f008_orden_lineas_de_origen/sin_origen_antes_que_retencion`) |

- **Control del generador:** `generar_mutantes` sobre las líneas que cambió la ronda devuelve exactamente esos
  **3** mutantes en `factura_models.py` y **0** en `create_factura_use_case.py` y `factura_statements.py`. Coincide
  con lo que dice `impl:128-130`.
- **RM1:** la campaña es de `eba243e`. Su delta hasta T20 lo midió el trozo de mutación, y el de la ronda lo cubren
  las 6 filas de la tabla. No hace falta relanzarla.
- **RM3:** ningún mutante equivalente aparece como muerto.
- **RM6:** la ronda no quita ninguna guarda.

## Evidencias de `impl_F-008.md:157-170` frente a lo medido

| Informe | Medido | ¿Coincide? |
|---|---|---|
| 4211 passed, 1 skipped | 4211 passed, 1 skipped | sí |
| 418 de F-008 | 418 recogidos | sí |
| 99,3 % (1192/1201) | idéntico | sí |
| 4 mutantes manuales, 4 muertos | 6 reproducidos, 6 muertos | sí |
| 75,98 s | 70,09 s | sí (reloj) |
| tamaño impl 170/220 | 176/220 | se midió en `215aff4`, antes de que `d0fc6e6` tocara el informe. Menor |

`current.md` y `features.json` son coherentes: F-008 es la única `in_progress`, en su rama, con rigor `critico`.
`tasks.md` tiene T0-T20 `[x]`. T21 se marca con este informe. T22-T24 son MANUAL y T25 es el `init.sh` final.

## Checkpoints (delta; el resto, en los informes troceados)

- [x] C1 `init.sh` verde · [x] C2 estado coherente (H2 resuelto) · [x] C3 estados contra `conest`, también el pago
- [x] C3 bis N/A: el delta no toca `docs/referencia/`
- [x] C4 trazabilidad R1-R47 por nombre (R16 incluido). R48 es documental y queda con la condición C3
- [x] C4 bis: RED pegado en `impl:119-126`, cobertura `[OK]`, mutación 0 supervivientes, RM1-RM6
- [x] C4 ter N/A: no hay `harness/rutas_sensibles.json`. Verificaciones de la pasada 1 sin cambios
- [x] C5: un commit por tarea, salvo la desviación 7 declarada (condición C1). Sin temporales y árbol limpio

## Condiciones para el humano (no bloquean este veredicto)

- **C1.** Aceptar por escrito la desviación 7: `517ddd2` agrupa T9-T10 y `1da3d67` agrupa T12-T14.
- **C2.** Decidir si un origen cuyas líneas son todas `can` 0 se rechaza (`origen_sin_lineas`) o se admite. Hoy pasa,
  y el commit lo marcaría FAC sin `dcaprodes`. Sin decisión no se hace ninguna grabación con orígenes de ese tipo.
- **C3.** Antes de T23, completar `azure-apps/sigrid_api.md` §8.11 con los 11 códigos de línea (`{indice, codigo,
  mensaje}`) y con la obra buscada en `SIGRID_ALBARAN_EMPRESAS_OBRA` (hallazgo 6 de docs).
- **Menores, a criterio:**
  - D1 de `verificacion_manual.md` dice «seis App Settings», pero se cargan cinco: `MAX_LINEAS` va sin cargar.
  - `mutacion_F-008.md` llama «equivalentes» a #64 y #65, que no lo son (O1 del trozo de mutación).
  - Las observaciones O1-O6 de escritura. La O2, el índice de `dcapro.docide`, se comprueba solo leyendo en T22/T23.

## Pendiente para cerrar F-008

T22 (permisos de `user_rw`, el humano), T23 (despliegue con la llave cerrada, D1-D5 y previas P1-P7) y T24 (G1 FR en
la obra 0404 y G2 FRGG, cada una con su autorización expresa, y anularlas en el escritorio). Después, T25 (`init.sh`).

## Automejora (propuesta, no aplicada)

Cuando el líder saque un hallazgo bloqueante del encargo de correcciones, que lo escriba en `current.md` como
«rebajado por el líder, motivo X». Así el reviewer de la pasada 2 no tiene que reconstruirlo desde `impl`.
