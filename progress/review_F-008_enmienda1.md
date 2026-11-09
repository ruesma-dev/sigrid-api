<!-- progress/review_F-008_enmienda1.md -->
Revisión completa de la enmienda 1 (pasada 1): `09339e8..4f6bddd` (HEAD `4f6bddd`) + azure-apps `612d84b`

# Review F-008 · enmienda 1 (spec v3.2): naturaleza de la ficha o forzada por empresa, FR con cuenta

**Veredicto: CHANGES_REQUESTED (RECHAZADO).** El código, los tests y la mutación están bien y los apruebo tal cual. Bloquea
**un solo hallazgo, de documentación operativa** (B1): el guion manual del despliegue sigue con las App Settings viejas y
T34 no tiene comandos exactos. Se corrige sin tocar código ni tests; la pasada 2 será incremental.

**Nivel de rigor:** `critico` (`harness/features.json:166`): fase RED, cobertura, mutación con 0 supervivientes salvo
justificación aceptada por el humano, RM5 con muestra.

## Verificación ejecutada por el reviewer

- `bash harness/init.sh` → `ENTORNO LISTO`: **4364 passed, 1 skipped** (134 s); `PUERTA COBERTURA` [OK] 100 % (136/136);
  `PUERTA TAMAÑO` [OK].
- Recálculo puro (`alcance_de_feature` + `generar_mutantes`): **315 líneas, 6 ficheros, 104 mutantes** (26/26/22/5/16/9),
  igual que el informe. Los supervivientes 1, 2, 7 y 8 existen con el mismo operador y texto original→mutado.
- **Campaña no reejecutada: 2160,6 s según el informe** (> 60 s).
- RM4 en un worktree aparte del scratchpad (retirado; `git status` limpio): reapliqué al pie de la letra los supervivientes
  1 (`or 0`→`or 1`), 8 (`or not emp.isascii()`→`and`), 7 (`and`→`or`, facturas:738) y 6 (`muchas=True`→`False`). Cada
  uno lo caza **exactamente** su test nuevo (`natide_0_con_auxpronat`, `١`, `producto_no_permitido_no_lee_naturalezas`,
  `l15d_..._pide_el_tope`) y nada más.
- RM1: medido sobre `66c7570`; lo posterior (`71706f5`..`4f6bddd`) solo toca tests, docs y `progress/`, ninguno de los 6
  ficheros del alcance. RM2: base 130,8 s, media 20,8 s, 1 worker; 104 × 20,8 = 2163 s ≈ total; con 94 muertos y `-x`,
  media baja legítima.

## Lo que se pidió mirar con cuidado

1. **Naturaleza** (`albaran_compra_statements.py:635-671`, `create_albaran_compra_use_case.py:1467-1488`,
   `create_factura_use_case.py:722-768`): una sola regla pura, `naturalezas_elegidas`. El producto sale de L7 por
   `(emp, tip 3)` y L15D va por el `p.ide` ya resuelto. La clave es `clave_forzada(emp de la obra, producto)`: la de otra
   empresa no fuerza (probado con `31:` en los dos endpoints). `natide` 0/NULL, sin `auxpronat`, de baja, de otra empresa o
   sin `cuacomcod` → `naturaleza_no_valida` con el origen en el mensaje; `analitica_no_resuelta` intacta.
2. **P22/P23**: `albaran-directo` no está en el diff. `_naturalezas_del_mapa` es el bloque viejo movido tal cual, con el
   mensaje de siempre (`create_albaran_compra_use_case.py:1490-1497`); los tests r51 cubren mapa, L15D no lanzada y validez.
3. **FR con cuenta**: resolvedor por línea (`create_factura_use_case.py:673-688`); `resolver_linea_gg` sin cambios, con
   `proide`/`paride`/`natide` 0 (probado en la transacción). «Ambigua», juego incompleto, `partida`/`paride` sin producto
   y ninguno → 400 (`factura_models.py:202-218`). FRGG por `_linea_frgg`, tests de antes intactos. Sin claves que choquen
   al fundir `LecturasLineas`.
4. **`_FORZADA`**: `parse_naturaleza_forzada` (`config/settings.py:347-380`) cumple R54 (dígitos ASCII > 0, `01:`
   normalizado, producto 1-24 sin espacios ni `:`, repetidas tras normalizar). Las viejas se ignoran con `extra="ignore"`
   (`settings.py:190`; test `..._viejas_..._arranca`). Proformas siguen con `parse_string_dict`.
5. **Seguridad**: L15D constante con `IN {marcadores}` y `?`; tope de filas (`muchas=True` en albaranes; en facturas el
   `Lector` siempre pone `max_rows` y falla si trunca). `infrastructure/security/` intacto. Sin secretos, proveedores ni
   CIF reales (`B12345678` es ficticio y previo).
6. **Tests**: de comportamiento (filas escritas, parámetros de cada lectura, lecturas no lanzadas). Los ajustes de F-009,
   F-007 y F-018 son renombres, claves `1:` o ficha vacía donde el caso pedía «sin naturaleza»; `el_mapeo_es_exacto` gana
   una aserción; nada se borra.
7. **Documentación**: `ARCHITECTURE.md`, contrato v8.5 (§1.3, §2.2, §3.3, §4.3, H34) y `azure-apps` §4, §8.6 y §8.11
   coinciden con el código, salvo M1. El guion manual no: B1.

## Checkpoints

- **C1** [x] `init.sh` exit 0 · [x] ficheros del arnés presentes.
- **C2** [x] una sola `in_progress` (F-008) · [x] rama `feature/F-008-registrar-factura` · [x] `current.md` dice la verdad
  de la enmienda (las secciones de F-018/F-016/F-007 son pendientes vivos del humano, no la contradicen) · [x] `done` con
  resumen en `history.md`.
- **C3** [x] hexagonal (dominio solo valida forma; la regla en application; sin infraestructura nueva) · [x] primera línea
  con ruta (también `test_f008_naturaleza_albaran.py`) · [x] sin `print`, TODO ni secretos (ruff de producción: 16 avisos,
  todos en líneas previas) · [x] Sigrid: base `ruesma`, `con` no se toca, nada que recalcular (solo una lectura), sin
  estados nuevos, SQL con `?` y tope.
- **C3 bis** N/A: no entran documentos de fuera.
- **C4** [x] cada requisito con test (tabla abajo), en verde · [x] sin red ni BBDD (dobles de `SqlRepository`) ·
  [ ] MANUAL con comando exacto → **B1**.
- **C4 bis** [x] `rigor` `critico` · [x] fase RED con traza real de T26-T31 (`impl_F-008.md`, «Fase RED (enmienda 1)») ·
  [x] cobertura [OK] 100 % · [x] mutación recalculada (104 = 104) · [x] muertos: > 60 s, sin reejecutar; recálculo puro +
  RM4 con 4 mutantes · [x] coste por mutante 2160,6 × 1 / 104 = 20,8 s (≥ 1 s) · [x] sin «⚠ CAMPAÑA NO VÁLIDA», sin
  veredicto = 0 · [x] RM1 · [x] RM2 · N/A RM5: ningún superviviente declarado equivalente (los 10 se mataron con tests) ·
  N/A RM6: no se quitó ninguna guarda (solo casos nuevos; el fuente no cambió tras medir) · N/A campaña manual: la
  automática dio 104 · [x] 10 supervivientes con análisis completo y 0 tras T32 (reproducido en 4) · [x] «Evidencias» con
  los cuatro números y `--workers 1` · [x] ningún N/A sin motivo. RM3: ninguno de los muestreados es equivalente.
- **C4 ter** N/A: no existe `harness/rutas_sensibles.json`.
- **C5** [x] T26-T33 y T36 `[x]` con commit `F-008 Tn:` (T34 MANUAL, T35 esta revisión) · [x] sin temporales ni sin
  trackear · [x] `features.json` en `in_progress`, que es lo real.

## Cobertura requisito → test

| Req. | Tests |
|---|---|
| R23 | `test_f008_models.py`: `r23_linea_fr_con_cuenta_*`, `_ambigua_es_400`, `_juego_..._incompleto`, `_con_cuenta_y_partida`, `_sin_ningun_juego`, `_solo_con_partida` |
| R25 | `test_f008_use_case.py`: `r25_r53_producto_no_permitido_no_lee_naturalezas`, `r49_g1_*` |
| R26-R27, R52 | `test_f008_use_case.py`: `r52_fr_solo_con_cuenta_*`, `r52_fr_mixta_*`, `r26_r52_*`, `r26_fr_con_cuenta_y_prefijos_vacios`; `test_f008_transaccion.py`: `r27_r52_*`; `test_f008_models.py`: `r52_fr_mezcla_*` |
| R28 | `test_f008_lineas.py`: `r28_fr_y_frgg_salen_por_el_mismo_constructor` |
| R49 | `test_f008_lineas.py:630-674`, `test_f008_naturaleza_albaran.py:68-89`, `test_f008_statements.py:731-739` |
| R50 | `test_f008_naturaleza_albaran.py:101-136,183`, `test_f008_lineas.py:518-525,646-656`, `test_f008_use_case.py` `r50_*` |
| R51 | `test_f008_naturaleza_albaran.py` `r51_*` (perfil de proforma, mapa, L15D no lanzada) |
| R53 | `test_f008_naturaleza_albaran.py` `r53_*` (sin leer ficha, tope de L15D), `test_f008_lineas.py:669` |
| R54 | `test_f008_settings.py:167-267` (vacías, válidas, mal escritas en código y entorno, viejas ignoradas, proformas, muestra) |
| R47 | suites de F-007, F-009, F-015, F-016 y F-018 en verde, con los ajustes listados en `impl_F-008.md` |
| R48 | revisión documental (punto 7) + `test_documentos_del_arnes.py` |

## Cambios requeridos (bloqueantes)

1. **B1 · El guion de despliegue contradice la enmienda y T34 no tiene comandos exactos** (C4; punto 7 del encargo).
   - `specs/F-008-registrar-factura/verificacion_manual.md:52-66` (§D.1) sigue mandando cargar
     `SIGRID_FACTURA_NATURALEZA_POR_PRODUCTO` copiada de la de albaranes, y parar si falta algún producto. Esa variable ya
     no se lee: quien siga el guion carga una App Setting muerta y da por configurada una naturaleza que el código ignora.
     Hay que sustituir esa línea por la `_FORZADA` o marcarla como superada por la enmienda 1.
   - T34 (`tasks.md:43`) opera sobre producción con la llave de albaranes abierta, y ni el guion ni
     `progress/current.md:27` traen sus pasos. Hay que añadir una sección T34 a `verificacion_manual.md`, enlazada desde
     `current.md`, con: el aviso previo a `albaranes`; el `az functionapp config appsettings list` de las `_FORZADA` y las
     `_POR_PRODUCTO`; los cuerpos fijos de las tres previas con lo esperado (FR con `MA9999` en una obra de la empresa 1 →
     `MA1501` y `<obra>.CDMA15`; FR solo con cuenta y analítica; una de `sigrid/albaran`); el borrado de las dos viejas y
     la carga de las `_FORZADA`, cada paso con su autorización; y qué se anota en `verificacion_F-008.md`.
   - Según `progress/verificacion_F-008.md:14-18`, la vieja de facturas lleva hoy además `SM9999`→`SM99`,
     `SB9999`→`SB99` y `SM370001`→`SM37`. El guion debe decir que esas tres pasan a la ficha al desplegar salvo forzado
     por empresa; hoy solo se cuenta el caso de `MA9999`.

## Menores (no bloquean)

- **M1** · `azure-apps/sigrid_api.md:362`: `SIGRID_FACTURA_CUENTAS_GASTO_PREFIJOS` dice «líneas FRGG sin origen (vacía:
  ninguna línea propia FRGG es válida)». Desde R52 gobierna también la FR con cuenta (lo prueba
  `r26_fr_con_cuenta_y_prefijos_vacios_no_vale`): añadir «y FR con cuenta».
- **M2** · `tests/test_f018_use_case.py:367-370` quita L15D de la huella de las tres clases. Es correcto (solo lectura,
  ajena a F-018), pero deja ver que `ProformaStatements` también la lista: una línea en el informe evita leerlo como un
  cambio de proformas (P23).
- **M3** · Dos nombres de test se han quedado cortos aunque la aserción sigue valiendo con los mensajes nuevos:
  `test_f008_models.py:135` (`linea_fr_exige_producto`; ahora vale producto o cuenta) y `:142`
  (`_con_campo_de_frgg_es_400`; hoy es el caso «ambigua»). Renombrar cuando convenga.

## Automejora (propuesta, no aplicada)

- Añadir a C4 de `CHECKPOINTS.md`: «si la feature cambia App Settings ya desplegadas, el guion manual de despliegue se
  actualiza en el mismo trabajo». Ninguna puerta lo mira, y un guion viejo es el documento desactualizado que parece vigente.
