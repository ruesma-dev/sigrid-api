<!-- progress/review_F-008.md -->
Revisión incremental de la enmienda 1, desde `09339e8` (pasadas 1-2: `09339e8..fa0bfcf` + azure-apps `612d84b`, `8fca6a3`); antes, pasada 3 desde `591d9ab`

# F-008 · Review consolidada (T21 y T35)

**Veredicto: APPROVED.**
- **v3.1 (T21):** aprobada en la pasada 3 (`8313ba0`).
- **Enmienda 1, spec v3.2 (T35):** aprobada en su pasada 2 (`fa0bfcf`).
- Pendientes, solo manuales: T22-T24 (v3.1), T34 (despliegue de la enmienda) y el `init.sh` final (T25).

**Nivel de rigor:** `critico`, declarado en `harness/features.json:166`. Exige tests trazables, fase RED con salida real,
cobertura ≥ 80 % de lo cambiado, mutación con 0 supervivientes sin justificar y RM1-RM6 (RM5 con muestra).

**Árbol:** el principal no se tocó ni cambió de rama. Las mutaciones a mano se hicieron siempre en un worktree detached
del scratchpad, borrado al acabar; `git worktree list` solo muestra el principal.

## Enmienda 1 (spec v3.2): naturaleza de la ficha o forzada por empresa, FR con cuenta

Detalle completo en [`review_F-008_enmienda1.md`](review_F-008_enmienda1.md). El de la pasada 1 está en
`git show 84ee690:progress/review_F-008_enmienda1.md`.

- **Pasada 1 (`09339e8..4f6bddd`): CHANGES_REQUESTED, solo por documentación (B1).** Código, tests y mutación, correctos:
  - `init.sh` verde: 4364 passed, 1 skipped; cobertura 100 % (136/136).
  - Recálculo puro: 315 líneas y 104 mutantes, igual que el informe.
  - Campaña no reejecutada: 2160,6 s (más de 60 s). RM1 y RM2, coherentes.
  - RM4 en un worktree: reapliqué a mano 4 de los 10 supervivientes (1, 6, 7 y 8). Cada uno lo caza solo su test nuevo.
  - Comprobado:
    - el forzado `<emp>:<producto>` solo aplica en la empresa de la obra; si no, manda la ficha (`pro.natide`);
    - las fichas con `natide` 0 o NULL, de baja o de otra empresa dan `naturaleza_no_valida`;
    - `analitica_no_resuelta` no cambia;
    - proformas y `albaran-directo` no cambian (P22, P23);
    - la FR con cuenta valida como FRGG y escribe `proide`/`paride`/`natide` a 0, y con producto y cuenta a la vez da
      «ambigua»;
    - las `_FORZADA` mal formadas no arrancan y las viejas se ignoran (`extra="ignore"`);
    - L15D va con `?` y tope de filas;
    - `infrastructure/security/` no se toca.
  - **B1:** `verificacion_manual.md` §D.1 seguía mandando cargar la `_POR_PRODUCTO` de facturas y T34 no tenía guion.
- **Pasada 2 (`4f6bddd..fa0bfcf` + azure-apps `8fca6a3`): APPROVED.** El delta no toca código de producción (solo
  `progress/`, `specs/` y dos renombres de test); RM1 sigue valiendo. `init.sh` verde: 4364 passed, 1 skipped
  (111,85 s), cobertura 100 %. La §T34 nueva cumple:
  - órdenes `az` exactas, con `MSYS_NO_PATHCONV=1` y `@json` validado con `Settings` antes de subir;
  - la previa de albaranes, solo con `commit:false`;
  - publicar, `set` y `delete`, cada uno con su autorización expresa del humano, y el aviso previo a `albaranes`;
  - lo que cambia por empresa: en la 1 solo `MA9999` (`MA99` → `MA1501`); en la 34, `SM370001` tiene `SM08` y hoy no
    entra.

  M1 (`sigrid_api.md:362`), M2 y M3, corregidos.

## v3.1, pasada 3 (`591d9ab..8313ba0`), en resumen

Texto completo: `git show 84ee690:progress/review_F-008.md`.

- **Delta:**
  - `45e9707` (informe);
  - `e2bc1f4` (código y 6 tests de R16b);
  - `1b9f266` (R16b en `requirements.md`);
  - `8313ba0` (informe y `current.md`).
- **Alcance del delta:** sin cambios de firma ni de `infrastructure/`, `.env` o `infra/`. `CODIGOS_FACTURA` gana
  `origen_sin_lineas`.
- **Medido:** `init.sh` verde con 4217 passed, 1 skipped, y cobertura 99,3 % (1194/1203).
- **`origen_sin_lineas`** (`create_factura_use_case.py:621-656`):
  - filtra `can` ≠ 0 al agrupar y rechaza el origen que se queda vacío;
  - se aplica en la previa y otra vez bajo `UPDLOCK`;
  - va antes de `origen_ya_facturado`, como pide design §7;
  - no escribe nada: en la previa no se abre transacción, y bajo bloqueo hay ROLLBACK con el mundo intacto;
  - R16 y los orígenes mixtos no cambian.
- **Mutantes reproducidos de R16b:** 3 del informe y 1 propio (`if vacios:` → `if False:`, con 6 fallos), todos
  muertos.
  - RM3: ningún equivalente.
  - RM6: la guarda del bucle pasa a la agrupación, que es quien construye el dato.
- **Documentación:** coincide con el código R16b (`requirements.md:50`) y azure-apps `f3f6474` (§8.11) y `654e7fd` (los
  11 códigos de `lineas_no_validas` y la búsqueda de `cod_obra`).
- **Decisiones del humano del 2026-10-31**, ya en el informe:
  - commits agrupados T9-T10 y T12-T14 (`impl:91-94`);
  - R16b (`impl:133-145`).

## Pasada 2 de la v3.1 (`591d9ab`), en resumen

Los 14 bloqueantes de la pasada 1 quedaron corregidos. El 6 de docs se rebajó a condición C3 y quedó resuelto en
`654e7fd`. Se reprodujeron 6 mutantes, todos muertos. C1 y C2 eran decisiones del humano y las tomó el 2026-10-31.
Detalle: `git show 591d9ab:progress/review_F-008.md`.

## Checkpoints (estado consolidado en `fa0bfcf`)

- [x] **C1:** `init.sh` verde (4364 passed, 1 skipped) y el arnés completo.
- [x] **C2:** una sola `in_progress` y la rama de la feature. `current.md` recoge las decisiones y enlaza §T34.
- [x] **C3:**
  - arquitectura hexagonal;
  - primera línea con la ruta;
  - sin `print` ni secretos;
  - reglas de Sigrid: base `ruesma`, SQL con `?` y tope de filas, estados sin hardcodear, y `origen_sin_lineas` antes de
    tocar `con.est`.
- **C3 bis:** N/A, no entran documentos de fuera.
- [x] **C4:**
  - cada requisito (R1-R54) tiene su test `test_f008_rN_*`;
  - los tests no tocan red ni base;
  - las manuales T22-T24 y T34 tienen guion con comandos exactos en `verificacion_manual.md`.
- [x] **C4 bis:** RED pegado (v3.1 y enmienda), cobertura `[OK]`, mutación con 0 supervivientes sin justificar
  (`mutacion_F-008.md` y `mutacion_F-008_enmienda1.md`) y RM1-RM6.
- **C4 ter:** N/A, no hay `harness/rutas_sensibles.json`.
- [x] **C5:** las tareas de código están en `[x]` con su commit. Las manuales (T22-T24, T34) y las de revisión y cierre
  (T21, T25, T35) quedan para el líder y el humano. Árbol limpio, sin temporales.

## Observaciones menores (no bloquean, a criterio)

- `requirements.md` y `design.md` están en 150/150 y 250/250: cualquier línea más rompe la puerta de tamaño.
- `impl_F-008.md` está en 217/220.
- Siguen en pie, de la v3.1:
  - «seis App Settings» en D1 de `verificacion_manual.md` (son cinco);
  - los «equivalentes» #64 y #65 en `mutacion_F-008.md`;
  - las O1-O6 de escritura (la O2 se comprueba en T22/T23).
- La fila «Tamaños» de Evidencias de la enmienda dice `review 133/140`: es una cifra vieja.

## Pendiente para cerrar F-008

- **T22:** permisos de `user_rw` (V1), con quien administra Sigrid.
- **T23:** desplegar con la llave cerrada, D1-D5 y previas P1-P7, sin `commit`.
- **T24:** G1 (FR en la obra 0404) y G2 (FRGG), cada una con su autorización expresa; después, «Comprobar»,
  «Contabilizar» y anular en el escritorio (V2-V4, V6, V7).
- **T34:** despliegue de la enmienda según §T34: aviso a `albaranes`, previas PA/PB/PC y decisión de los `_FORZADA`, con
  cada escritura autorizada.
- **T21, T35** (marcar con estos APROBADOS) y **T25** (`bash harness/init.sh` final). Abrir
  `SIGRID_FACTURA_WRITE_ENABLED` es decisión del humano.

## Automejora (propuesta, no aplicada)

- Que `init.sh` imprima la fila «tamaño» de Evidencias junto a los tests, para que no se quede con una cifra vieja.
- Añadir a C4 de `CHECKPOINTS.md`: si la feature cambia App Settings ya desplegadas, el guion manual de despliegue se
  actualiza en el mismo trabajo. Es la lección de B1 de la enmienda.
