<!-- progress/review_F-009_T0a.md -->
Revisión incremental desde 988e7c1 (pasada 2): `git show 2f68c41`. Pasada 1: completa, `a81b8e9..988e7c1`.

# Review · F-009 T0a (ampliación del script de mediciones de T0)

**Veredicto final: APPROVED** (pasada 2). Pasada 1: CHANGES_REQUESTED (tres cambios, resueltos).

Alcance: solo T0a (`scripts/medir_f009_t0.py`, `tests/test_f009_t0_script.py`,
`progress/impl_F-009_T0a.md`). F-009 sigue en `spec_ready`. No se ha ejecutado nada contra la API,
Azure ni el SQL Server.

## Nivel de rigor

F-009 declara `critico` en `harness/features.json`. Para T0a se exige lo pertinente a una
herramienta de medición desechable: fase RED con salida real, cobertura de lo cambiado y
«Evidencias». **Mutación: N/A justificado** por la decisión del humano N3 (`progress/spec_F-009.md`
§Preguntas de la v3): script y test se retiran con `git rm` antes de T1 y salen del alcance de
cobertura y mutación; no es código que F-009 entregue. RM1-RM6: N/A, no hay campaña.

## Pasada 1 (resumen)

| # | Comprobación pedida | Resultado |
|---|---|---|
| 1 | Solo lectura | OK: las 20 sentencias nuevas son un único `SELECT`; `ClienteLectura` solo hace `POST /api/sql/read` y rechaza en local lo que no sea `SELECT`/`WITH`; tests parametrizados sobre las 67 con `es_solo_lectura` y el `SqlQueryGuard` real |
| 2 | Parametrizado | OK: `MA9999`, empresa 1 e `ide` con `?`; los literales (14, 44, fechas) son constantes de la spec |
| 3 | Fidelidad | SQL OK (comparación automática spec ↔ script: idénticas, con el `GROUP BY` de los `CASE` que la spec describe en prosa; `M14_sv_valores` = spec + 8 columnas de la lista). Desviaciones 1-6 del informe justificadas. Lectura automática: dos defectos (cambios 1 y 2) |
| 4 | Error 130 | OK: ningún agregado sobre subconsulta ni `APPLY` escalar; detector sobre las 67 |
| 5 | `--solo` de T0b | OK: ejecuta exactamente esas nueve; salida en `%TEMP%`, nunca en el repo; datos de test ficticios |
| 6 | `M14_sv_valores` | OK: 16 de la spec + `fec_igual_albaran` + las 23 de `LISTA_DE_RESETEO`, un test por columna |
| 7 | Sin red; tiempos | OK. 200 s por llamada (< 230 s). Sin riesgo claro; vigilar `M18_propagacion` (recorre `dcfpro` sin filtro indexado) y `M17_existe_sin_emp` (sin `emp` no usa el índice `(emp, tip, cod)`) |
| 8 | `init.sh` | Verde (1998 passed) |

Cambios requeridos en la pasada 1:
1. «Dominante» (M16, R15) documentado como 0,95 (`:96` y el informe) pero aplicado como literal 0,5
   (`:1095`).
2. `lectura_sv_valores` clasificaba `tex` (fuera de la lista) como «reseteo confirmado» o «revisar
   §Reseteo (v6)», contra la regla de la spec («columnas **de la lista**»).
3. Regresión PEP8 `iv =c.leer(` en `:869`.

Observaciones de la pasada 1: (a) un fallo de una sentencia nueva de M11/M14 perdía el bloque
entero; (b) `isp1 != resto` demasiado laxo; (c) acierto de M11 sesgado en bruto contra L8b.

## Checkpoints (`CHECKPOINTS.md`, estado tras la pasada 2)

- C1: [x] init.sh exit 0. [x] ficheros del arnés presentes.
- C2: [x] ninguna feature `in_progress`. [x] rama `feature/F-009-alta-albaran-compra`.
  [x] `current.md` describe la sesión activa. N/A `done` sin historia: no hay feature cerrada.
- C3: N/A hexagonal: script suelto de `scripts/`, fuera de las capas. [x] primera línea con ruta.
  [x] sin `print` de debug (los `print` son la salida del script), sin secretos (clave ficticia en
  tests), sin dependencias nuevas. [x] PEP8: `ruff check --preview --select E2,W,F` limpio en los
  dos ficheros. Trampas Sigrid: [x] base `ruesma`; [x] `cod`/`fec`/`tip`/`est` de `con`;
  N/A «nada se recalcula» (no escribe); [x] estados contra `M2_conest`; [x] parametrizado y
  agregación en SQL.
- C3 bis: N/A (no toca `docs/referencia/`).
- C4: [x] cada sentencia y lectura de §T0 v5 con test (276 en el fichero). [x] sin red ni BBDD.
  [x] T0b listada en `current.md` y en el informe con su comando exacto.
- C4 bis: [x] RED con salida real (pasada 1: 11 y 8 fallos; ciclo 1: 10 fallos). [x] cobertura
  [OK] 97,9 %. [x] mutación N/A justificado (N3). [x] «Evidencias».
- C4 ter: N/A (init.sh no señala rutas sensibles).
- C5: [ ] T0a sin marcar en `tasks.md`: **esperado**, lo marca el líder o el spec-author al
  aprobar (F-009 no se cierra aquí). [x] sin temporales de T0a; el sin trackear de la raíz
  (`` `0`].{t ``) es previo y ajeno: conviene que el humano lo borre. [x] `features.json`
  coherente (`spec_ready`).

## Trazabilidad (§T0 v5 → test)

| Punto | Test |
|---|---|
| Existen M16-M18 y ampliaciones | `test_f009_t0a_existen_las_sentencias_nuevas_de_la_spec_v5`, `..._hay_una_medicion_por_cada_m...` |
| Solo lectura, guardia, error 130 | `..._toda_sentencia_es_select_o_with...`, `..._el_guardia_de_lectura...`, `..._ninguna_sentencia_agrega...` |
| `?` | `test_f009_t0a_las_sentencias_nuevas_con_valores_van_parametrizadas` |
| M11 por MA9999, `OVER`, L8b, fallos | `..._m11_ampliada_va_por_cada_ma9999...`, `..._m11_sigue_si_la_api_rechaza_over`, `..._l8b_*`, `..._m11_un_fallo...` |
| M14 lista entera, arrastre, fallos | `..._cuenta_toda_la_lista_de_reseteo[23]`, `..._r2_sv_valores...`, `..._sacan_su_conclusion`, `..._m14_un_fallo...` |
| M16 confirma / PARADA / dominante | `..._lectura_m16_para_si_no_se_cumple`, `..._r1_dominante_*` |
| M17, M18 | `..._lectura_m17_borra_marca_o_t23`, `..._m17_repite_el_join_sin_emp...`, `..._lectura_m18_y_sv_valores...` |
| `--solo` T0b y `main` | `..._solo_acepta_la_repeticion_unica_de_t0b`, `..._main_con_la_lista_de_t0b` |

## Segunda pasada (`2f68c41`)

**Cambios requeridos:**

| # | Estado | Comprobado |
|---|---|---|
| 1 | Resuelto | `UMBRAL_DOMINANTE = 0.5` con nombre; el comentario de `UMBRAL_CASI_TODO` ya no dice «dominante»; `dominante()` usa la constante; el bloque M16 imprime el criterio («≥ 50 % y no menos que la alternativa; ficha ≥ 95 %»), así T0c no lo puede leer como 95 %. Informe corregido. Tests en el límite (50/100 sí, 49/100 no; 60 frente a 61 no) |
| 2 | Resuelto | `vacias`/`llenas` solo sobre columnas de `LISTA_DE_RESETEO`; `tex` en la línea informativa con su porcentaje. Test con `tex` 300/1000 que no aparece en las dos líneas clasificadas (la comprobación por token evita la subcadena `texcom`) |
| 3 | Resuelto | `iv = c.leer(`; ruff E2/W/F y el ruff por defecto limpios en los dos ficheros |

**Observaciones aplicadas** (no cambian lo que decide cada medición):
- (a) `_leer_o_anotar` en `M11_iva_por_proveedor` y `M11_iva_y_isp`; M14 partida en tres partes
  (API, valores, arrastre), cada una con su `try` sobre `ErrorDeLectura`. Si `M11_iva_y_isp` falla,
  `lectura_l8b` recibe `[]` y no revienta. El fallo queda escrito en la conclusión del bloque, así
  que el humano lo ve y puede repetir con `--solo`. Las sentencias SQL no cambian.
- (b) `isp1 - resto` no vacío: más fiel a «IVA distinto con tipisp 1». Queda un caso residual
  (`resto` vacío: todo MA9999 con tipisp 1 ⇒ «justificada»), improbable e inocuo.
- (c) Tasas: `tasa_mismo_prv` sobre `lineas - sin_previa_del_prv` (con guarda de base 0) frente a
  `tasa_cualquiera` sobre `lineas`; la conclusión dice sobre qué base va cada porcentaje y la tabla
  conserva los recuentos brutos. Es una lectura distinta de la literal de la spec («>» en bruto),
  declarada en el informe. **No cambia la decisión**: según la spec, L8b se queda tanto si sale
  «justificada» como «inocua». El spec-author debe saberlo al volcar en T0c (está en el informe).

**Verificación propia:** `bash harness/init.sh` tal cual en verde: 2009 passed, 1 skipped (80,1 s);
`PUERTA COBERTURA` [OK] 97,9 % (651/665, umbral 80 %, critico); tamaño OK. Humo: 276 passed.
La cobertura difiere de la del informe (617/630) por el alcance medido en cada árbol; ambas [OK].
El informe del implementer tiene 220 líneas e init.sh no lo marca en la puerta de tamaño.

## Propuesta de automejora (no aplicada)

Que la puerta de ruff de `init.sh` muestre los avisos **nuevos en los ficheros del diff** con
`--select E2,W` además de la regla por defecto: la regresión del cambio 3 pasó con «All checks
passed!».
