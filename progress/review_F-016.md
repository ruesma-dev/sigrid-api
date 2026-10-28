<!-- progress/review_F-016.md -->
Revisión incremental desde `c08461f` (pasada 2, consolidación): delta `30a3d83` + `f0a870c`, solo texto, sobre HEAD `f0a870c`

# F-016 · Proforma a origen · veredicto consolidado de la revisión troceada

- **Veredicto: APROBADO** (para merge a `dev`). El `done` sigue bloqueado por T17-T18 (MANUAL) y T20 (ver C5).
- **Nivel de rigor:** `critico`, declarado en `harness/features.json`. Exige fase RED con salida real, cobertura
  ≥ 80 % de lo cambiado, campaña de mutación sin supervivientes no aceptados, RM1-RM6 (RM5 sobre un equivalente) y
  la sección «Evidencias». Todas cubiertas en los parciales (abajo).
- **Alcance de esta pasada:** lo aprobado en los seis parciales sobre `c08461f` queda dado por bueno. Desde ahí, el
  delta toca solo `BACKLOG.md`, `features.json`, `current.md`, `impl_F-016.md`, `contrato_proformas.md`, `tasks.md`,
  `verificacion_manual.md` y los propios informes: **ningún `.py`** (`git diff --stat c08461f..HEAD`). No invalida
  nada de lo aprobado: ni firmas, ni ficheros movidos, ni alcance de la campaña.

## Informes parciales

| Bloque | Informe | Veredicto |
|---|---|---|
| Cumplimiento funcional R1-R19 | [`review_F-016_origen.md`](review_F-016_origen.md) | APROBADO (3 observaciones) |
| C3, C3 bis, C4 ter | [`review_F-016_C3C4ter.md`](review_F-016_C3C4ter.md) | APROBADO (C3 bis y C4 ter N/A justificados) |
| C4 y C4 bis: fase RED y cobertura | [`review_F-016_C4red.md`](review_F-016_C4red.md) | APROBADO |
| C4 bis: campaña de mutación, RM1-RM6 | [`review_F-016_mutacion.md`](review_F-016_mutacion.md) | APROBADO (3 observaciones) |
| Documentación y verificación manual (R24, R25) | [`review_F-016_docs.md`](review_F-016_docs.md) | CHANGES_REQUESTED → **resuelto** |
| C1, C2, C5, topes, «Evidencias», barrido | [`review_F-016_C1C2C5.md`](review_F-016_C1C2C5.md) | CHANGES_REQUESTED → **resuelto** |

## Verificación de los cambios pedidos (leídos en los ficheros reales)

| Pedido | Dónde | Resuelto en | Comprobación |
|---|---|---|---|
| docs 1 · §2.3 sin «medidas así» | `contrato_proformas.md:106-112` | `f0a870c` | Dice que la 1 deriva de M44 (~4 s) medida **sin** el `NOT EXISTS`, que la 2 no se ha medido y que las dos se prueban en T17 (V0/V2) antes del despliegue. Es lo que pedía el parcial |
| docs 2 · cierre ante fallo en §G | `verificacion_manual.md:220-227` | `f0a870c` | «Regla de parada en G1-G3» **antes** de G1: ante cualquier resultado distinto de «Se mira», cerrar las dos llaves con `f016_cerrar.json` (comando completo, sin clave ni URL: `$env:`), parar y avisar. El registro en `progress/verificacion_F-016.md` ya lo manda la cabecera del fichero (l. 6) |
| C1C2C5 H1 · `current.md` | `current.md:21-23`, `:31-35`, `:195-214` | `30a3d83` | P1/P3 pasadas a «Decisiones del humano»; bloque de la revisión T19 con lo que sigue y quién lo lanza; «Lo siguiente» con F-018 (prioridad 9) y F-008 después; «Prompt para retomar» con F-016 `in_progress`, revisión en curso, merge, despliegue con la llave cerrada y T17-T18. Nada falso hoy |
| C1C2C5 H2 · `features.json` | F-016 `acceptance[3]` y `description` | `30a3d83` | La llave `SIGRID_PROFORMA_ORIGEN_ENABLED` en el criterio y en la descripción; frase de la spec v2 (el llamante elige). `BACKLOG.md` regenerado: `init.sh` → «BACKLOG.md al día» |
| C1C2C5 H3 · T15 | `tasks.md:21` | `f0a870c` | Nota: la prueba en lectura de §2.3 se hace en T17 (V0/V2). También en `impl_F-016.md:157` |
| origen obs. 1 · orden de errores a origen | `contrato_proformas.md` §4, l. 272-277 | `f0a870c` | Ver la tabla siguiente |

**Orden de §4 frente a `application/use_cases/create_proforma_use_case.py`** (`execute`, l. 246-304, y `_cadena`, l.
334-379). En mes, `lineas_no_validas` sale en el paso 4 (l. 256-261). A origen, `fallos` se guarda y el orden es:

1. `comprobar_hoja` (l. 271) → `importe_mes_no_cuadra` / `hoja_descuadrada` (`proforma_statements.py:503`, `:511`).
2. `buscar_del_mes_origen` (l. 285) → con alguna de mes u `otra_del_mes`, `buscar_del_mes` de F-007 →
   `proforma_del_mes_existente` (`proforma_statements.py:649`); `anterior_y_origen` solo produce avisos.
3. `existente` (l. 296-299), 200 sin escribir, antes de `_cadena`.
4. En `_cadena`: `validar_anterior` → `anterior_no_valida` (l. 353); `comprobar_sucesoras` → `anterior_con_sucesora`
   (l. 357).
5. `lineas_no_validas` con los fallos de la etapa 1 y los de `linea_anterior` juntos (l. 362-369); `demasiadas_lineas`
   después (l. 374-379).

El párrafo de §4 dice exactamente 1-4 y que todo eso sale antes que `lineas_no_validas`; el ejemplo («una línea que
no es del contrato y el mismo total que una del mes ya registrada recibe `existente`») es el escenario del parcial
`origen` y lo confirma el paso 3. `contrato_no_resuelto` y el conflicto de referencia van antes en los dos modos (no
cambian), así que §4 no tenía que nombrarlos. **Correcto.**

## C1-C5 (resumen; el detalle, en cada parcial)

- [x] **C1 · arnés completo y en verde.** `bash harness/init.sh` tal cual sobre `f0a870c`, una vez: exit 0, «ENTORNO
  LISTO»; **3549 passed, 1 skipped**, 260,62 s; PUERTA COBERTURA `[OK]` **100,0 %** de 270 líneas (umbral 80 %,
  critico); PUERTA TAMAÑO `[OK]` (requirements 118/150, design 186/250, impl 173/220); BACKLOG al día; rama correcta.
  Avisos esperados: F-015 `blocked` y ruff 158 (79 propios = `dev`, los otros 79 son la copia de `.claude/worktrees/`
  de F-018; medido en `C1C2C5`).
- [x] **C2 · estado coherente.** Una sola `in_progress` (F-016); rama de `features.json`; `current.md` al día tras H1;
  `history.md` con todas las `done`; `features.json`/`BACKLOG.md` coherentes tras H2.
- [x] **C3 · código** (`C3C4ter`): hexagonal respetada, solo los ficheros previstos en design, primera línea con ruta,
  sin prints ni secretos, SQL con `?`; núcleo de F-007 y `infrastructure/` intactos (`git diff dev` vacío, R1/R2).
- N/A **C3 bis**: la feature no trae documentos de fuera (justificado en `C3C4ter`).
- [x] **C4 · trazabilidad y RED** (`C4red`, `origen`): cada Rn con su test (116 funciones de test F-016); salida real del
  rojo de los requisitos centrales en `impl_F-016.md`; cobertura 100 % de lo cambiado.
- [x] **C4 bis · mutación** (`mutacion`): 116 mutantes, 102 muertos, 14 vivos de la campaña, **0 no aceptados** tras
  T14 (5 de los 14 reproducidos a mano por el parcial); alcance y nº de mutantes recalculados; «Tiempo total» 4937,2 s
  > 60 s → **campaña no reejecutada** (82 min según el informe), con muestra de 4 muertos verificados; sin «⚠ CAMPAÑA
  NO VÁLIDA», base medida (129,4 s). RM1: SHA `06ffcb6` ≠ HEAD, pero desde entonces solo cambian
  `tests/test_f016_{statements,use_case}.py` (+84/−1), ningún fichero de producción del alcance (comprobado de nuevo
  aquí). RM2 coherente (media 42,6 s con `-x`, 102/116 muertos). RM3: ningún equivalente. RM5: N/A justificado (no
  se declaró ningún equivalente). RM6: ninguna guarda quitada.
- N/A **C4 ter**: no toca `infrastructure/security/` ni rutas sensibles (justificado en `C3C4ter`).
- [x] **C5 · cierre de sesión.** Un commit `F-016 Tn:` por tarea (T1-T16, en `C1C2C5`); los commits del delta en
  español con `Co-Authored-By` y `Claude-Session`; árbol limpio salvo `.claude/worktrees/` (F-018, ajeno).
  **T17 y T18 (MANUAL, del humano: despliegue con `SIGRID_PROFORMA_ORIGEN_ENABLED=false`, previas en producción, un
  `commit:true` autorizado en la 0404 y V9 en la UI) y T20 (`init.sh` de cierre) siguen abiertas: no bloquean este
  veredicto ni el merge, pero sí el `done`.** Mismo criterio que F-007, F-010, F-011 y F-015. T19 se marca `[x]` con
  este informe.
- [x] **Sin secretos, personas ni CIF** en el delta: el bloque nuevo de §G usa `$env:SIGRID_API_RG`/`_APP` y
  `$env:TEMP`; ni clave, ni URL, ni GUID (revisado a ojo; el barrido completo es de `C1C2C5` y `docs`).

## Cobertura (requisito → evidencia)

| Requisitos | Tests / evidencia | Parcial |
|---|---|---|
| R1-R2 (mes intacto) | `git diff dev` vacío en tests y dorados de F-007/F-009/F-015 | `origen`, `C1C2C5` |
| R3-R4 (petición y llave) | `tests/test_f016_models.py`, `tests/test_f016_route.py`, `tests/test_f016_settings.py` | `origen`, `C4red` |
| R5-R19 (cadena, continuadas, arrastradas, respuesta) | `tests/test_f016_statements.py`, `tests/test_f016_use_case.py`, `tests/test_f016_transaccion.py` | `origen`, `C4red` |
| R24 (MANUAL) | `verificacion_manual.md` con regla de parada; ejecución en T17-T18 | `docs` |
| R25 (contrato v1.2, ARCHITECTURE, CLAUDE.md, sample, `azure-apps`, avisos) | `contrato_proformas.md`, `azure-apps` `3744877`/`7afe9e9`, `impl_F-016.md` §T15 | `docs` |

## Observaciones heredadas (no bloquean; para el líder y el humano)

1. **`;` en el comentario de la consulta 2** (`contrato_proformas.md:148`, «`max_rows ≥ nº de líneas; ver
   truncated`»): si `proformas` copia el bloque tal cual, el guardia de `sql/read` lo rechaza como dos sentencias.
   `$SQL_LINEAS` de V0 no lleva el comentario, así que **V2 no lo cazará**. Conviene quitar el `;` (o sacar la nota del
   bloque `sql`) antes de enviar el aviso a `proformas`: es una línea de texto.
2. `totales.n_lineas` cuenta las arrastradas a origen y el contrato no lo dice; `_vinculo` no mira `docoritip`
   (riesgo residual) (`origen`, obs. 2 y 3).
3. Avisos de `docs` sin aplicar: precisar de dónde sale `<ctride>` y «o sin vincular» en el aviso a `proformas`; G1
   abre la llave de mes de F-007 en producción mientras dura G (el humano elige la hora).
4. La campaña dio un superviviente falso (n.º 4) sin causa conocida: posible `.pyc` retenido en Windows
   (`mutacion`, obs. 1). Va a `arnes-base`, no a F-016.
5. Al mergear: `1733c2f` (alta de F-018) vive en esta rama; el worktree de F-018 salió de `dev` sin ella (`C1C2C5`).

## Cambios requeridos

Ninguno.

## Automejora (propuesta, no aplicada)

- Recojo las de los parciales para `arnes-base`: excluir `.claude/` del recuento de ruff en `init.sh`; en revisiones
  troceadas, mutar y verificar sobre una copia en el scratchpad, nunca en el árbol compartido; en verificaciones
  manuales con escritura, exigir una «regla de parada» con el cierre de llaves ante fallo (F-016 la trae ya); y prohibir
  anotaciones dentro de un bloque `sql` documentado para otro equipo que el guardia rechazaría si se copia.
- `reviewer.md`: añadir el formato de esta pasada de **consolidación** (tabla de parciales + tabla «pedido → commit →
  comprobación») como caso de revisión incremental, que hoy solo describe la pasada sobre código.
