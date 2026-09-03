<!-- progress/review_F-003.md -->
Revisión completa (pasada 1) · diff `f1946d9..b70a689` (commits `4892e36`, `b70a689`)

# F-003 · Informe de revisión

**Veredicto: RECHAZADO (CHANGES_REQUESTED).**

**Rigor `critico`** (declarado en `features.json`): exige C1–C5, fase RED,
cobertura, **campaña de mutación con cero supervivientes** y las verificaciones
`MANUAL` listadas con su comando.

**Lo que más pesa, primero: la condición del humano está bien verificada.** No
hay ninguna consulta legítima que empiece a fallar, y lo comprobé por mi cuenta.
Lo que se rechaza es el papeleo del rigor y el cierre de sesión, no la defensa:
el código es bueno y no hay que rehacerlo.

## 1 · La condición del humano, comprobada de forma independiente

1. **Reejecuté `scripts/verificar_sql_ecosistema.py`**: 13.635 ficheros, 256 que
   hablan con la API, **0 rechazos**, exit 0. Reproduce el §3 del impl.
2. **Auditoría de sus tres reglas de filtrado** (script propio en scratchpad,
   árbol limpio): desactivé cada una y miré qué esconde. *«Solo ficheros que
   hablan con la API»* → **1** (`datamart-seg-anual/.../mart.yaml`, diccionario
   de un proyecto PostgreSQL que no pasa por estos guardias). *«Empieza por verbo
   SQL»* → **4** (Python dentro de here-strings de PowerShell, docstrings en
   español). *«Literal sin cerrar es ruido»* → **4**, todos la concatenación
   partida `cif LIKE '%" + cif + "%'` de `diagnose_sigrid_contrato*.py`.
   **Ninguna esconde un caso real.** Punto ciego residual: un fragmento sin verbo
   (`"JOIN ruesma_rep.dbo.gra..."`) ni llega a ser candidato; lo cubre el
   inventario manual del §3a, no el script.
3. **Los tests no se engañan.** Neutralicé `DatabaseReferenceGuard.validate` en
   memoria (plugin de pytest, sin tocar el árbol): caen **26 tests** (6 del
   detector, 5 de lectura, 12 de escritura, 3 del verificador).
4. **Orden intacto**: en los dos guardias la llamada nueva va **al final**, tras
   prefijos, sentencia única, palabras prohibidas y WHERE obligatorio; ninguna
   defensa anterior se relajó y hay tres tests que lo fijan. Los endpoints
   `sigrid/*` y `documents/read` **no pasan** por estos guardias (solo los usan
   los dos casos de uso de `sql/read` y `sql/write`): R10 se sostiene.

## 2 · Falsos positivos encontrados (no bloquean; hay que anotarlos)

Probé 47 formas de T-SQL. Pasan bien CTEs, subconsultas, `CROSS APPLY` con
función, `dbo.fn_x(...)`, `OPENJSON`, `#tmp`, `@tabla`, decimales, `::`, `t.*`,
literales y comentarios con puntos. Rechazan `t.col.value(...)`/`c.doc.nodes(...)`
(XML/CLR) y `base.esq.tabla.columna`, **ambos previstos** en `design.md` y §7 del
impl. Y dos **no previstos**: `SELECT dbo.con.* FROM dbo.con`, y `SELECT
[Client's Name] FROM dbo.con`, que cae con «literal sin cerrar» porque un
apóstrofo dentro de un identificador entre corchetes arranca un literal falso en
`_neutralizar_literales_y_comentarios()`, que no conoce el corchete como
delimitador. Ninguno aparece en el ecosistema (§1): **no rompen nada hoy**.

## 3 · Checkpoints

**C1** — [x] `init.sh` en `ENTORNO LISTO`: 438 pasan, 1 skip, cobertura 97,8 % (225/230). [x] Existen todos los ficheros exigidos.

**C2** — [x] Una sola `in_progress`. [x] Rama correcta. [x] F-002 en `history.md`.
- [ ] **`progress/current.md` no describe la sesión activa**: sigue contando la
  instalación del arnés, dice que F-003 está en `spec_ready` y que «F-001 y F-002
  siguen en pending» (F-002 está `done`).

**C3** — [x] Hexagonal respetada: el detector vive en `infrastructure/security/`
y no importa `Settings` ni dominio. [x] Primera línea con la ruta en los seis
ficheros nuevos. [x] Sin `print()` de producción (los del script los permite
`CONVENTIONS.md`), sin secretos, sin dependencias nuevas. [x] Reglas Sigrid: la
feature **refuerza** «`ruesma_rep` solo se lee». `ruff`: **0 avisos** en lo nuevo;
los 3 de los guardias son previos (verificado contra `498963b`).

**C4** — [x] R1–R11 con test que pasa (§4). [x] Ningún test toca red ni BBDD:
`Settings` y petición doblados con dataclasses, el verificador usa `tmp_path`.
- [ ] **Las verificaciones `MANUAL` no están en `progress/current.md`.** T8 vive
  solo en el §6 del informe del implementer, sin comando exacto.
- [ ] **Nombres de test no trazables.** `docs/CONVENTIONS.md` §Tests y C4 piden
  `test_f003_rN_...`; la trazabilidad va en comentarios de sección.

**C4 bis** — [x] Declara `rigor`. [x] **Fase RED** con traza real (§2 del impl:
T1 `ModuleNotFoundError`, T3 `10 failed, 11 passed`, T5 `13 failed` con su
diagnóstico honesto). [x] **Cobertura** `[OK]` 97,8 % (el impl publica 98,2 % /
223: medición anterior al último commit).
- [ ] **MUTACIÓN: no existe `progress/mutacion_F-003.md`; la campaña no se ha
  ejecutado.** No es un caso de «0 mutantes»: recalculé el alcance con
  `harness.alcance` y generé los mutantes con `harness.mutacion.generar_mutantes`
  (cálculo puro): **102 mutantes**, 63 en `database_reference_guard.py` y 39 en
  `verificar_sql_ecosistema.py` (0 en los dos guardias). Hay campaña que hacer.
- [ ] Muertos comprobados, coherencia de tiempos, RM1, RM2, RM5, RM6 y análisis
  de supervivientes: **vacíos por la misma causa**; no los marco N/A.
- [ ] **«Evidencias» incompleta**: trae tests, cobertura y `ruff`, pero no
  mutantes, ni supervivientes, ni workers, ni tiempo de la suite.

**C3 bis y C4 ter** — **N/A justificados**: la feature no toca
`docs/referencia/` (no hay barrido de datos sensibles que hacer) y no existe
`harness/rutas_sensibles.json`, solo el `.ejemplo.json`.

**C5** — [x] Árbol limpio, sin artefactos sospechosos. [x] `features.json`
refleja `in_progress`.
- [ ] **`tasks.md`: 0 de 10 tareas marcadas `[x]`**, y los commits son
  `F-003: ...` en vez de `F-003 Tn: ...`. Dos commits para diez tareas: quien
  abra la spec no puede saber qué se hizo. Observación aparte:
  `azure-apps/sigrid_api.md` está modificado **sin commit** en su repositorio (lo
  commitea el humano, pero conviene no perderlo).

## 4 · Trazabilidad requisito → test

| Req | Test (`dbg`/`wg`/`qg` = `test_database_reference_guard` / `test_sql_write_guard_bases` / `test_sql_query_guard_bases`) |
|---|---|
| R1 / R2 | `wg::..._aunque_el_campo_database_este_permitido`, `wg::..._culpable_no_sea_la_primera`; `wg::test_sigue_aceptando_las_escrituras_normales` (8), `wg::test_acepta_la_documental_si_alguien_la_pone_en_la_lista` |
| R3 / R4 | `dbg::test_detecta_la_base_de_un_nombre_de_tres_partes`, `dbg::test_la_comparacion_no_distingue_mayusculas`, `wg::test_rechaza_cualquier_forma_de_nombrar_una_base_no_permitida`; `dbg::test_rechaza_siempre_los_nombres_de_cuatro_partes` y su par en los dos guardias |
| R5 | `dbg::test_sin_referencias_a_otra_base`, `qg::test_las_consultas_de_una_y_dos_partes_ni_se_tocan` |
| R6 / R7 | `wg::test_el_mensaje_nombra_la_base_y_la_lista_sin_filtrar_credenciales`; `qg::test_rechaza_una_base_fuera_de_allowed_databases` |
| R8 | `qg::TestConsultasRealesDelEcosistema::...siguen_pasando` (7 consultas reales) |
| R9 / R10 | Los 96 tests nuevos (ninguno toca red ni BBDD) + suite completa en verde (438) + los tres tests de «las comprobaciones anteriores siguen mandando» |
| R11 | `dbg::test_un_literal_sin_cerrar_no_deja_pasar_la_referencia_de_despues`, `dbg::..._comentario_de_bloque_sin_cerrar...` |

## 5 · Cambios requeridos

1. **Ejecutar la campaña**: `python -m harness.mutacion --feature F-003` →
   `progress/mutacion_F-003.md`. Rigor `critico` exige **cero supervivientes** o
   justificación escrita aceptada por el humano. ~102 mutantes; declara los
   **workers** con que se lanzó.
2. **Completar «Evidencias»** en `progress/impl_F-003.md`: tests, cobertura
   (97,8 % / 230, lo que mide hoy la puerta), mutantes, supervivientes, tiempo de
   la suite y workers.
3. **`tasks.md`**: marcar `[x]` T1–T7, T9 y T10; T8 se queda sin marcar por ser
   MANUAL. Los commits siguientes, con formato `F-003 Tn: ...`.
4. **Reescribir `progress/current.md`** para la sesión de F-003, **con T8 y su
   comando exacto** (ejecutar
   `albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs.py` tras
   desplegar y comparar la salida), como pide C4.
5. **Renombrar los tests** a `test_f003_rN_...` (`docs/CONVENTIONS.md` §Tests), o
   proponer al humano cambiar la convención; no saltársela en silencio.
6. **Anotar en el §7 del impl los dos falsos positivos** de §2. El del apóstrofo
   se cerraría haciendo que `_neutralizar_literales_y_comentarios()` salte los
   tramos entre `[` y `]` antes de mirar la comilla simple, pero **no lo toques
   sin decidirlo con el humano**: es seguridad y hoy no rompe nada.

## 6 · Automejora (propuesta, no aplicada)

`init.sh` valida cobertura y tamaño pero **no avisa de que falte
`progress/mutacion_F-XXX.md`** en rigor `critico` o `estandar`. Este rechazo se
habría evitado con un aviso de tres líneas: propongo añadirlo y portarlo a
`arnes-base`.
