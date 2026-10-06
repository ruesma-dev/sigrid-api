<!-- progress/review_F-009_T0a_quater.md -->
Revisión incremental desde 8e6e298 (pasada 2): `git show 7f350bb 2b7a85f`. Pasada 1: revisión completa,
`git diff abe70a3..8e6e298` (`aa599f0` y `8e6e298`). Lo aprobado de T0a, T0a-bis y T0a-ter (hasta `abe70a3`) se da
por bueno. `2631b1a` (contrato v7.1) se leyó como contexto, no se revisó.

# Review · F-009 T0a-quater (M14d, M16d y M19)

**Veredicto final: APPROVED** (pasada 2). La pasada 1 fue CHANGES_REQUESTED con cuatro cambios; los cuatro están
resueltos.

**Alcance**: `scripts/medir_f009_t0.py`, `tests/test_f009_t0_script.py` y `progress/impl_F-009_T0a_quater.md`. F-009
sigue en `spec_ready`. No se ha ejecutado nada contra la API, Azure ni el SQL Server.

**Fuera de la revisión**: C3 hexagonal (script suelto de `scripts/`), C3 bis (no entra documento de fuera), C4 ter
(sin rutas sensibles) y RM1-RM6 (sin campaña de mutación).

**Rigor `critico`**: exige fase RED con salida real, cobertura y la sección «Evidencias». **Mutación: N/A
justificado** por la decisión N3 del humano: el script y su test se retiran antes de T1.

## Pasada 1 (resumen)

Comprobado y correcto en `8e6e298`:
- **Diccionario** (`azure-apps/sigrid_tablas.md`): existen todas las columnas y tablas que usan las sentencias
  nuevas. M14d va por el índice `pfhi`, y ninguna sentencia lee `usu.cla`.
- **Sentencias**:
  - Todas los `?` cuadran con los parámetros de cada llamada.
  - No hay literales de negocio ni `ISNULL(…, -1)` sobre Byte, y no aparece el patrón del error 130.
  - Todas van envueltas.
  - Cada lectura distingue «SIN MEDICIÓN» de «cero filas».
  - Los umbrales llevan nombre.
- **M16d**: las candidatas fijan UNA caa. `regla_ampliada` coincide con la regla del contrato v7.1 (sin el prefijo
  `MOD.`) para las tres naturalezas del mapeo de H34.
- **Riesgo de tiempo**:
  - M14d: bajo. Son dos seeks por cada `mov`.
  - M16d: bajo-medio. Es lo que tardó M16c (9,8 s) más dos `LAG`.
  - M19 de `dncpro` y de `log`: bajo.
- **RED reproducida**: `57 failed, 84 passed`. `init.sh` en verde: 2363 passed.

| # | Cambio requerido (pasada 1) | Estado (pasada 2) |
|---|---|---|
| 1 | `CANDIDATAS_COD2` daba «REGLA escribible» a candidatas que solo prueban que el valor existe (`dnc_misma_obra`, `ctr_cualquier_linea`) o que no fijan UN valor (las de «mismo producto»), y el test lo esperaba | **Resuelto** (ver «Segunda pasada», punto 1) |
| 2 | `M19_vinculadas` no permitía confirmar ni refutar H35 para `dncide` y `dncproide` (solo medía presencias por separado) | **Resuelto** (punto 2) |
| 3 | `M19_cod2_origen`, la sentencia más cara de M19, iba la segunda: si el balanceador la cortaba, seguía viva en el servidor y competía con las siguientes | **Resuelto** (punto 3) |
| 4 | `lectura_m14d` concluía «NO arrastran» con base 0 | **Resuelto** (punto 4) |

## Segunda pasada (`7f350bb`, `2b7a85f`)

Leído en el diff, no en el informe.

1. **Candidatas de `cod2`**:
   - `tc` y `dp` agrupan por su clave, (`docide`, `proide`) y (`obride`, `proide`), con
     `COUNT(DISTINCT cod2) AS n_cod2` y `MIN(cod2)`. Se unen solo por la clave: una fila por clave, así que no
     multiplican filas.
   - El acierto exige `n_cod2 = 1` y que el `cod2` coincida. Los casos `n_cod2 > 1` salen como
     `*_ambiguo`/`*_ambigua`.
   - `dnc_misma_obra`, `ctr_cualquier_linea`, las ambiguas, `repetido_en_albaran` y `con_contrato` pasan a
     `PROPIEDADES_COD2`: se informan y no compiten.
   - El test anterior se invirtió: «existe en …» al 98 % ya no da «REGLA escribible». Hay un test nuevo que comprueba
     que identificativas y propiedades no se cruzan.
   - La nota final remite `con_dnc` a M19_dnc, que mide su `dncpro` por clave primaria.
   - El coste es el mismo recorrido que el `DISTINCT` anterior. Sin `?` nuevos.
2. **H35**:
   - `M19_vinculadas` suma `dncproide_igual` y `dncide_igual` (exigen valor distinto de 0 y que sea igual) y
     `*_ambos_cero` por separado. Sigue yendo por clave primaria.
   - `COPIA_H35` lee `cod2`, `dncide` y `dncproide` con `UMBRAL_HEREDA_DNC` y concluye «H35 CONFIRMADA» o «NO
     confirmada en: …». El límite 95/94 está probado.
   - Ahora la medición sí confirma o refuta la regla del contrato.
3. **Orden**: `M19_cod2_origen` va la última de `m19`. Hay un test que comprueba el orden de las claves.
4. **M14d**: con `otro <= 0` dice «sin mov siguiente de otro documento: no se mide el arrastre», y lo prueba un test.

**Observaciones de la pasada 1**, aplicadas también:
- (a) Aviso cuando un ítem tiene más de dos naturalezas. Tiene test.
- (b) `lectura_m19_api` ya no afirma que la API quede descartada. Ahora dice que eso se apoya en el código, no en la
  medición. Lo comprobé: los casos de uso de albarán no escriben `dbo.log`; solo lo escribe el de
  `partes-reclamacion`.
- (d) `dncide` entra en `HEREDA_M19`.

**Verificación propia (pasada 2)**:
- `bash harness/init.sh`, tal cual: **en verde** (exit 0).
  - 2369 passed, 1 skipped (75,5 s).
  - `PUERTA COBERTURA` [OK]: 98,9 % (1322/1337).
  - Tamaño OK y rama correcta.
- **RED del ciclo reproducida** en una copia del scratchpad (tests de `7f350bb` contra el script de `8e6e298`):
  `9 failed, 627 passed`. Cuadra con los 9 fallos que da el informe con su filtro.
- ruff: limpio en los dos ficheros.
- Informe del implementer: 219 líneas (tope 220), con «Ciclo 1 de revisión», RED y «Evidencias».
- Árbol: solo el fichero sin trackear de la raíz (previo y ajeno) y este informe.

## Checkpoints (estado final)

- **C1**: [x] `init.sh` termina con exit 0. [x] Los ficheros del arnés están presentes.
- **C2**: [x] Ninguna feature en `in_progress`. [x] Rama correcta. [x] `current.md` sin cambios de esta tarea.
  N/A «`done` sin historia»: no se cierra ninguna feature.
- **C3**:
  - N/A hexagonal: es un script de `scripts/`.
  - [x] Primera línea con la ruta.
  - [x] Sin secretos ni dependencias nuevas. Los `print` son la salida del script.
  - [x] SQL parametrizado, agregado en SQL y sin `ISNULL(…, -1)` sobre Byte.
  - [x] Lecturas fieles al dato (cambios 1 y 4).
- **C4**:
  - [x] Cada punto del encargo y cada cambio tiene test: 636 en la prueba de humo.
  - [x] Sin red ni BBDD.
  - [x] H35 se puede verificar (cambio 2).
- **C4 bis**: [x] RED con salida real, reproducida en las dos entregas. [x] Cobertura [OK]. [x] Mutación N/A (N3).
  [x] «Evidencias».
- **C5**:
  - [x] Commits `F-009 T0a-quater: …`.
  - [x] Sin temporales.
  - N/A «T0a-quater como tarea de `tasks.md`»: es el paso del implementer que precede a T0b-quater (MANUAL, humano).

## Trazabilidad (prefijo `test_f009_t0a_quater_`)

| Punto | Test |
|---|---|
| M14d (SQL, ventana, umbral, sin medición, arrastre sin base) | `m14d_va_por_el_producto…`, `lectura_m14d_*`, `c1_m14d_sin_siguiente…` |
| M16d (maestro, excepciones, sufijos, candidatas, elección) | `m16d_sql…`, `lecturas_m16d_*`, `lectura_m16d_*`, `c1_eleccion_avisa…` |
| M19 dnc y origen del cod2 (identificativas frente a propiedades) | `m19_sql`, `lectura_m19_dnc`, `c1_las_candidatas_de_existencia_no_compiten…` |
| M19 vinculadas (H35) | `lectura_m19_cod2_origen_y_vinculadas`, `c1_h35_en_el_limite_del_umbral` |
| Altas por usuario y API | `lectura_m19_usuarios_y_api`, `m19_pasa_los_parametros` |
| `?`, sin `cla`, un fallo ≠ vacío, orden, `--solo M14 M16 M19` | `cada_llamada…`, `sentencias_parametrizadas…`, `un_fallo…`, `c1_cod2_origen_va_la_ultima…`, `main_con_la_lista…` |

## Observaciones (no bloquean; para el spec-author al leer T0b-quater)

a. `n_cod2` cuenta solo los `cod2` no vacíos. Si en un mismo contrato hay líneas del producto con `cod2` y otras sin
   él, la clave cuenta como «única». Es irrelevante para F-009: en las sin vincular el `cod2` va vacío por decisión
   del humano (H35).
b. `M16d_maestro` busca por `con.emp` y `con.cod`, y el diccionario no da índice por `cod`. El `JOIN` con `pro`
   permite empezar por `pro`. Riesgo bajo.
c. Siguen en pie la observación (a) de T0a-bis (no relanzar justo después de un corte; timeout de `sql/read`) y las
   (e) y (f) de T0a-ter.

## Propuesta de automejora (no aplicada)

Es la tercera vez seguida (T0a-bis, T0a-ter y T0a-quater) que una candidata de existencia sale como «REGLA
escribible». Propongo añadir a C3, para los scripts de medición: «toda candidata que compita por "REGLA escribible"
fija UNA fila o UN valor por la clave con la que la buscaría la feature, con la unicidad medida; las existenciales van
a propiedades». Y añadir un test genérico que lo compruebe en cada tupla `CANDIDATAS_*`.
