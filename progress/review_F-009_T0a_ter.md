<!-- progress/review_F-009_T0a_ter.md -->
Revisión incremental desde 38d3571 (pasada 2): `git show ade7b47 bda26b1`. Pasada 1: `git show 38d3571`, desde
844ebc8; lo aprobado de T0a y T0a-bis (hasta `a7517af`) quedó dado por bueno. `98aa512` (spec v7) no toca el script.

# Review · F-009 T0a-ter (M16c y ampliación para T0b-ter)

**Veredicto final: APPROVED** (pasada 2). Pasada 1: CHANGES_REQUESTED (un cambio, resuelto).

Alcance: `scripts/medir_f009_t0.py`, `tests/test_f009_t0_script.py`, `progress/impl_F-009_T0a_ter.md`. F-009
sigue en `spec_ready`. No se ha ejecutado nada contra la API, Azure ni el SQL Server. Fuera de la revisión:
C3 hexagonal (script suelto), C3 bis (no entra documento de fuera), C4 ter (sin rutas sensibles), RM1-RM6
(sin campaña). **Rigor `critico`**: RED con salida real, cobertura y «Evidencias». **Mutación N/A
justificada** por N3 (script y test se retiran antes de T1).

## Pasada 1 (resumen)

Correcto en `38d3571`:
- **Composición del código**: `RTRIM(LTRIM())`, `CHARINDEX('.') > 0` y sufijo tras el PRIMER `.`; sin
  `.` (o nulo) no casa.
- **Contra la caa correcta**: la de la línea, con `k.cenide = d.cenide`; `u` descarta los pares
  (`cenide`, código) repetidos, que es lo que hará L15b.
- Avisos completos; TOP 15 de MA9999 y control sobre `ctrpro` por clave primaria.
- Umbral con nombre; «SIN MEDICIÓN» ≠ «cero filas»; `?` cuadrados; sin `ISNULL(…, -1)` ni error 130.
- Sentencias envueltas; `--solo M16`; riesgo de tiempo bajo.
- RED reproducida: 19 failed.

| # | Cambio requerido (pasada 1) | Estado (pasada 2) |
|---|---|---|
| 1 | `cueide` «⇒ REGLA escribible» por igualdad de código, sin fijar UNA `cua` (`_cuenta_es_cuacomcod`) | **Resuelto** (`ade7b47`): exige `cf.emp = c.emp` y `w.cod IS NULL`, con `w` = (`emp`, código) repetidos entre `cua` ⨝ `con`, como `u`. Avisos `cua_repetida` y `cua_de_otra_empresa`. Frase de cierre «La de la cuenta exige …». Sin `?` nuevos (test que cuenta `1 + len(PRODUCTOS_GENERICOS)`) |

Observaciones de la pasada 1, atendidas en `ade7b47`:
- (a) `M16c_naturalezas_ma` trae `regla_linea_centro` y la lectura usa la mejor de obra y centro.
- (b) `caa_informada` en `M16c_reglas`.
- (c) El control de las vinculadas mide sobre las líneas de contrato con `caaide`; sin ninguna, dice «no
  sirve de control (sin contraejemplos)» en vez de «NO sigue la regla».

Cada una tiene su test.

## Segunda pasada: ampliación (`bda26b1`, aprobada por el humano)

**M14c (P1)**, parte nueva de M14, envuelta por `_leer_tabla` y además por el `try` de las partes de `m14`:
- `M14c_mov_prepma`: un mes (`VENTANA_M9`, 2 `?`) por `tipfec`; `mov` por `doclin` (`m.docide/linide`) con
  `m.doctip = 14`. El `mov` anterior va en un `OUTER APPLY (SELECT TOP 1 p.almpma … WHERE p.proide = m.proide
  AND p.almide = m.almide AND (fechor menor, o igual con ide menor) ORDER BY p.fechor DESC, p.ide DESC)`.
  - Columnas verificadas en `sigrid_tablas.md` (`mov`: `proide`, `almide`, `fechor` Real, `almpma`,
    `prepma`, `doctip`; índices `doclin` y `pafhi`). `pafhi` = producto, almacén, fechor: casa con la
    igualdad y con el orden del TOP 1.
  - Agregados solo sobre banderas de la derivada: no es el patrón del error 130. Tolerancia `0.0001` = la
    de `M14_prepma`.
- `M14c_sin_mov`: camino de `M9_sin_mov_por_producto`. `tipmov` por `COALESCE(CAST … AS int), -1)`, sin
  `ISNULL(…, -1)` sobre Byte.
- `lectura_m14c` (`UMBRAL_REGLA_PREPMA = 0.95`):
  - (a) se mide sobre los `mov` con anterior.
  - «no discrimina» cuando a y b llegan a la vez, «PARADA» para `pro.prepma` (R25), «no concluyente» en el
    resto.
  - `None` ⇒ SIN MEDICIÓN, cada sentencia por separado. `n = 0` o `[]` ⇒ cero filas.
  - Límite del 95 % probado.
  - T0b-bis dio un 2,6 % de igualdad con el resultante: la discriminación entre a y b está garantizada.
- **Riesgo de tiempo: bajo-medio, aceptable.**
  - Unos 8.300 `mov` en el mes, con un TOP 1 por índice cada uno.
  - El `OR` de desempate puede impedir el rango sobre `fechor`. En ese caso el motor busca por (`proide`,
    `almide`) y recorre hacia atrás desde el `mov` más reciente hasta el primero que cumple: lee los `mov`
    de ese producto y almacén posteriores a `m`, unas semanas de datos.
  - Solo es caro si un producto concentra miles de `mov` en un almacén. Los genéricos no los generan (H20:
    `tipmov` 0).
  - Va envuelto y el resto de M14 sigue. Ver obs. (d).

**XA9999 (P5)**:
- Está en `PRODUCTOS_GENERICOS` y en `LISTA_BLANCA_GENERICOS` (spec v7).
- Los `?` salen de la tupla: `M9_genericos` 7, `M16c_reglas`/`vinculadas` 6 (renderizado y test).
- Ningún literal en el SQL. M9 y M11 lo concluyen aparte (test con `ide 9`).

**`M16c_numemp` (P2)**, informativa:
- Un `?` (empresa); `c.emp = ?` entra por `emptipfec`; camino de M16b sin `pro`.
- `numemp` es Entero en el diccionario, así que su `ISNULL(…, 0)` es legítimo.
- La lectura usa el umbral con nombre y distingue SIN MEDICIÓN de cero filas.

**`--solo M9 M14 M16`** ejecuta todo: `..._amp_main_con_la_lista_de_t0b_ter` comprueba los tres bloques, sin
«SIN MEDICIÓN», y las conclusiones de M14c, numemp y XA9999.

## Verificación propia (pasada 2)

- `bash harness/init.sh` tal cual, en verde: 2159 passed, 1 skipped. `PUERTA COBERTURA` [OK] 98,6 %
  (1038/1053). Tamaño OK. Rama correcta.
- Humo: 426 passed. ruff limpio en los dos ficheros.
- **RED reproducida** en copias del scratchpad:
  - tests de `ade7b47` contra el script de `38d3571`: `3 failed, 402 passed`;
  - tests de `bda26b1` contra el script de `ade7b47`: `12 failed, 405 passed`.
  Las dos cuadran con el informe.
- Informe del implementer: 207 líneas (tope 220), con «Ciclo 1», ampliación, RED y «Evidencias».
- Árbol: solo el sin trackear de la raíz (previo y ajeno) y este informe.

## Checkpoints (estado final)

- C1: [x] init.sh exit 0. [x] ficheros del arnés.
- C2: [x] ninguna `in_progress` (F-009 `spec_ready`). [x] rama correcta. [x] `current.md` coherente
  (v7 en `98aa512`). N/A `done` sin historia: no se cierra ninguna feature.
- C3: N/A hexagonal (script de `scripts/`). [x] primera línea con ruta. [x] sin secretos ni dependencias
  nuevas; los `print` son la salida del script. Trampas Sigrid: [x] parametrizado, agregado en SQL, sin
  `ISNULL(…, -1)` sobre Byte. [x] lecturas fieles al dato (cambio 1 resuelto).
- C4: [x] cada punto del encargo, del ciclo y de la ampliación con test (426). [x] sin red ni BBDD.
  [x] T0b-ter como MANUAL (humano) en `tasks.md`.
- C4 bis: [x] RED con salida real (reproducida en las tres entregas). [x] cobertura [OK]. [x] mutación N/A
  (N3). [x] «Evidencias».
- C5: [x] commits `F-009 T0a-ter: …`. [x] sin temporales. N/A T0a-ter como tarea de `tasks.md`: es el
  paso del implementer que precede a T0b-ter.

## Trazabilidad (prefijo `test_f009_t0a_ter_`)

| Punto | Test |
|---|---|
| Composición y caa única | `m16c_construye_el_codigo...`, `m16c_la_regla_exige_que_centro_y_codigo...` |
| Cuenta única por empresa (cambio 1) | `c1_la_cuenta_exige_la_empresa_del_albaran_y_un_solo_codigo` |
| Obs. a/b/c | `c1_naturalezas_miden_tambien_la_variante_centro`, `c1_el_control_cuenta_solo...` |
| Umbrales, sin medición ≠ cero filas, bloque sigue | `lectura_m16c_en_el_limite...`, `..._distinguen_sin_medicion...` (×2), `..._un_fallo_de_m16c/m14c...` |
| M14c | `amp_m14c_compara_con_el_mov_anterior_por_indice`, `amp_m14_pasa_la_ventana...`, `amp_lectura_m14c...` |
| XA9999 / numemp | `amp_xa9999_se_mide_y_concluye...`, `amp_numemp_de_las_naturalezas_de_la_empresa_1` |
| `?`, sin literales ni `ISNULL(…, -1)` | `m16c_va_parametrizada...` (×3), `amp_sentencias_parametrizadas...` (×3) |
| `--solo M16` / `--solo M9 M14 M16` | `main_solo_m16_con_m16c`, `amp_main_con_la_lista_de_t0b_ter` |

## Observaciones (no bloquean; para el spec-author al leer T0b-ter)

d. `M14c_mov_prepma`: reescribir el desempate como `p.fechor <= m.fechor AND (p.fechor < m.fechor OR p.ide
   < m.ide)` haría explícito el rango sobre `pafhi`. Es equivalente y no cambia ningún número. Solo merece
   la pena si la sentencia se acerca a los 200 s.
e. `igual_pro_prepma` compara con el `pro.prepma` de HOY, no con el de septiembre. Un acierto alto confirma
   la hipótesis (b); uno bajo no la refuta del todo si el PMP del producto se ha movido desde entonces.
f. `lectura_m16c_numemp` cuenta en el denominador las líneas sin naturaleza. La cifra sale aparte: que el
   spec-author la descuente si pesa.
g. Siguen en pie las observaciones b y c de T0a-bis y la (a) de no relanzar justo después de un corte.

## Propuesta de automejora (no aplicada)

En C3, para scripts de medición: «toda candidata que una lectura proclame "REGLA escribible" debe identificar
UNA fila por la clave con la que la buscará la feature (unicidad medida, no supuesta)». T0a-bis lo cazó en la
caa y T0a-ter lo repitió en la cuenta.
