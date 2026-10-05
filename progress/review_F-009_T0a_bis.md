<!-- progress/review_F-009_T0a_bis.md -->
Revisión incremental desde 0037c72 (pasada 2): `git show c42bb2b`. Pasada 1: `git diff 18a2b77..0037c72` (lo aprobado de T0a hasta `2f68c41` quedó dado por bueno).

# Review · F-009 T0a-bis (segunda pasada del script de mediciones de T0)

**Veredicto final: APPROVED** (pasada 2). Pasada 1: CHANGES_REQUESTED (cuatro cambios, resueltos).

Alcance: `scripts/medir_f009_t0.py`, `tests/test_f009_t0_script.py`, `progress/impl_F-009_T0a_bis.md`.
F-009 sigue en `spec_ready`. No se ha ejecutado nada contra la API, Azure ni el SQL Server.
Fuera de la revisión: C3 hexagonal (script suelto), C3 bis (no hay documentos de fuera), C4 ter
(init.sh no señala rutas sensibles), RM1-RM6 (no hay campaña de mutación).

## Nivel de rigor

F-009 declara `critico`. Para T0a-bis se exige lo mismo que en T0a: fase RED con salida real,
cobertura de lo cambiado y «Evidencias». **Mutación: N/A justificado** por la decisión N3 del humano:
script y test se retiran antes de T1 y no son código que F-009 entregue.

## Pasada 1 (resumen)

Comprobado y correcto: solo lectura (un `SELECT` por sentencia, `SqlQueryGuard` real, detector del
error 130); `?` en todo valor de fuera, con el orden de parámetros cuadrado en M9, M11, M14b y M16b;
columnas y tablas existentes en `sigrid_tablas.md`; `text` solo dentro de `DATALENGTH`; QA9999 aparte
de MA9999 en M9 y M11; M14b fiel a la L5 de design (`LAG … PARTITION BY c.emp, a.entide ORDER BY
c.ide`); reintento solo ante el 1205; `--solo M9 M11 M14 M16 M17`; salida en `%TEMP%`. **RED
reproducida** en una copia del scratchpad (test de `00179a2` contra el script de `18a2b77`): `53
failed, 1 passed`.

Riesgo de tiempo: **por volumen**, ninguna sentencia apunta a 200 s. M9 lee un mes por `tipfec`,
`docide` y `doclin`; M11, tres meses por producto; M16b, ~189.000 líneas con uniones por clave
primaria; M14b, ~23.000 albaranes. La más expuesta es `M17b_reutiliza`, con dos recorridos de la
ventana de 1.000.000 de `log`: riesgo medio. **El riesgo real es la contención** (`M14_prv` tardó
121 s para 2.608 filas), agravada por la observación (a).

| # | Cambio requerido (pasada 1) | Estado (pasada 2) |
|---|---|---|
| 1 | `ISNULL(r.tipmov/tipinv, -1)` sobre columnas Byte: error 220 con `tinyint`, o -1 → 1 con `bit` | **Resuelto**: `COALESCE(CAST(… AS int), -1)`, también en `auxfam.tipinv`; test que barre las 76 sentencias contra el patrón |
| 2 | Una sentencia caída se leía como dato vacío (M9 «sin líneas en la ventana» sobre H20; M16b «no hay líneas»; M17b «⇒ T23»); `cod` sin `strip` en `lectura_m9` | **Resuelto**: `_leer_tabla` devuelve `None` si falla y `[]` si hay cero filas. `sin_medicion()` lo usan `lectura_m9`, `m16`, `m16b`, `muestra_m16b`, `m17`, `m17b`, `ope` y `l8b`. `cod` sale recortado. Tests de lectura y de bloque completo con la sentencia rota |
| 3 | «⇒ REGLA» para propiedades que no fijan UNA caa; «caa del centro» tapaba la regla útil | **Resuelto**: `IDENTIFICATIVAS_M16B` compiten y `PROPIEDADES_M16B` informan. Los datos del test dan ahora «caa del centro con código = caagascod … 960/1000 ⇒ REGLA» y «caa del centro» 980 entre las propiedades. Se nombran los empates |
| 4 | M16b solo con la naturaleza del producto | **Resuelto**: `nl` = `auxpronat` por `dcapro.natide`, con 4 candidatas de línea, `centro_y_caaexicod` por simetría, `nat_linea_igual_producto` informativa y `caagascod_linea` en la muestra |

## Segunda pasada (`c42bb2b`)

**Cambios requeridos:** los cuatro, resueltos (tabla de arriba). Lo leí en el diff, no en el informe.
Además lo reproduje con el cliente falso: con `M9_genericos` caída sale «M9_genericos SIN MEDICIÓN»,
no «sin líneas»; con `M16b_fuentes` y `M16b_codigos` caídas, «no se concluye»; con `M17b_reutiliza`
caída, sin T23.
Sin medición parcial en M16b: si cae una de las dos sentencias, compiten solo las de la otra y la
lectura lo dice («sus candidatas no compiten»). Es correcto: `caa_cero` o `cab_caaide` siguen siendo
hechos medidos.

**Lo añadido (observaciones b, d y e de la pasada 1):**
- `M9_genericos` con `VENTANA_M11` (tres meses): el mismo camino que M11 (`con` por `tipfec` →
  `dcapro` por `docide` → `mov` por `doclin`), filtrado por `k.cod` en un `JOIN` interno. Son unas
  40.000 líneas como mucho: **riesgo bajo**. El título del bloque declara las dos ventanas.
- `M16b_dcaproana`: columnas `docproide` y `caaide` existentes en el diccionario. Agrega **toda**
  `dcaproana` por `docproide`, sin índice declarado y sin ventana: es la sentencia nueva más
  expuesta. Su tamaño no se conoce. El patrón es el mismo que el `dcapropar` de M7, que terminó. Va
  envuelta, es la última de M16 y es informativa: si se corta, solo se pierde ella. **Riesgo
  bajo-medio, aceptable.** Sin error 130: los agregados van en la derivada.
- `lectura_ope` sin tildes (`unicodedata`): «Envío» casa con `envi`. Test.

**Verificación propia:**
- `bash harness/init.sh` tal cual, en verde: 2107 passed, 1 skipped (95,9 s); `PUERTA COBERTURA` [OK]
  98,4 % (880/894); tamaño OK.
- Humo: 374 passed. ruff, por defecto y con E2/W/E7/F, limpio en los dos ficheros.
- **RED del ciclo reproducida**: los tests de `c42bb2b` contra el script de `0037c72` dan `21 failed,
  350 passed`, igual que el informe.
- Informe del implementer: 181 líneas (tope 220), con la sección «Ciclo 1» y las «Evidencias» al día.

## Checkpoints (`CHECKPOINTS.md`, estado tras la pasada 2)

- C1: [x] init.sh exit 0. [x] ficheros del arnés presentes.
- C2: [x] ninguna `in_progress`. [x] rama `feature/F-009-alta-albaran-compra`. [x] `current.md` con
  T0b-bis abierta. Tiene un cambio sin commit que no es de esta tarea: es del líder. N/A `done` sin
  historia: no se cierra ninguna feature.
- C3: N/A hexagonal (script de `scripts/`). [x] primera línea con ruta. [x] sin `print` de debug
  (son la salida), sin secretos, sin dependencias nuevas (`unicodedata` es de la biblioteca
  estándar). Trampas Sigrid: [x] base `ruesma`, parametrizado, agregación en SQL; [x] lecturas
  automáticas fieles al dato (cambios 2 y 3).
- C4: [x] cada punto del encargo y cada cambio con test (374). [x] sin red ni BBDD. [x] T0b-bis como
  MANUAL (humano) en `tasks.md`, con su comando.
- C4 bis: [x] RED con salida real (reproducida en las dos entregas). [x] cobertura [OK].
  [x] mutación N/A (N3). [x] «Evidencias».
- C5: [ ] T0b-bis sin marcar en `tasks.md`: **es lo esperado**, la marca quien vuelque la ejecución.
  [x] sin temporales de T0a-bis; el sin trackear de la raíz `` `0`].{t `` es previo y ajeno (que lo
  borre el humano). [x] `features.json` coherente (`spec_ready`).

## Observaciones (no bloquean)

a. **Timeout de `sql/read`** (fuera de T0a-bis; para el líder):
   - `infrastructure/repositories/sql_server_repository.py:43` pasa `timeout_seconds` a
     `pyodbc.connect(timeout=…)`, que es el tiempo de *login*, no el tope de la consulta. Los casos
     de uso de dominio sí fijan `cursor.connection.timeout` (`attach_concepto_grafico_use_case.py:478`).
   - Consecuencia: una consulta que el balanceador corta a los 230 s sigue viva en el SQL Server. Es
     una explicación verosímil de los 121 s y del 1205 del 2026-10-05.
   - Propuesta: una feature aparte que fije `connection.timeout` en `execute_read_query` y actualice
     `azure-apps/sigrid_api.md`.
   - Mientras tanto, el humano no debe relanzar T0 justo después de un corte.
b. `lectura_dcaproana` (`:1617-1624` aprox.): con `con_ana` > 0 dice «dcapro.caaide no cuenta toda la
   analítica». Solo es cierto si hay `ana_caa_distinta` o `ana_varias_filas`, y las dos cifras
   salen al lado. Es informativa y no alimenta ninguna decisión de la spec: que el spec-author la
   lea con esas cifras.
c. `lectura_m14b` decide por diferencia estricta, sin margen. Es el texto literal de la spec («si
   acierta menos»), pero una diferencia de un solo albarán invierte la regla: que el spec-author lo
   mire con las cifras.
d. La propuesta de `NOLOCK` (Desviación 5) sigue siendo razonable como plan B: lo decide el líder.

## Trazabilidad (encargo y cambios → test)

| Punto | Test |
|---|---|
| M9/M11 por ventana, sin `IN (SELECT`, fallos protegidos | `..._m9_va_por_ventana_corta...`, `..._m11_va_por_ventana_corta`, `..._m9/m11_un_fallo...`, `..._m9_pasa_la_ventana_y_los_genericos` |
| M16b (identificativas, propiedades, naturaleza de la línea, dcaproana) | `..._lectura_m16b_*`, `..._c1_las_propiedades_no_compiten...`, `..._c1_m16b_mide_tambien_la_naturaleza...`, `..._c1_dcaproana...` |
| M17b y ope | `..._lectura_m17b...`, `..._significado_de_ope...`, `..._c1_ope_envio_con_tilde` |
| M14b | `..._lectura_m14b_anterior_frente_a_maestro`, `..._m14_un_fallo...` |
| 1205 | `..._el_cliente_reintenta...`, `..._se_rinde_tras_los_reintentos...` |
| Byte / fallo ≠ vacío / `cod` con espacios | `..._c1_tipmov_y_tipinv_son_byte...`, `..._c1_lecturas_distinguen...`, `..._c1_un_fallo_no_se_lee_como_dato_vacio[5]`, `..._c1_lectura_m9_compara_el_codigo...` |
| `--solo` y QA9999 | `..._main_con_la_lista_de_la_segunda_pasada`, `..._m11_mide_y_concluye_qa9999...` |

## Propuesta de automejora (no aplicada)

- Añadir a C3, trampas de Sigrid: «`ISNULL(col, literal)` con columnas Byte o bit: el literal toma
  el tipo de la columna; usar `COALESCE` o `CAST`».
- Añadir a cualquier script de medición: «un fallo de lectura nunca alimenta una conclusión como
  dato vacío».
