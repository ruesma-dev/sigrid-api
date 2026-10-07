<!-- progress/review_F-009_T0a_quinquies.md -->
Revisión incremental desde 5262a74 (pasada 2): `git show fb04d9a 832b9c5`. Pasada 1: revisión completa de
`git show 5e9975f 5262a74`, y lo aprobado hasta `9672216` (T0a a T0a-quater) quedó dado por bueno. La spec v8
(`8a6ecab`) no entra en esta revisión, por encargo.

# Review · F-009 T0a-quinquies (M14e: ¿`mov.prepma` = media ponderada global?)

**Veredicto final: APPROVED** (pasada 2). La pasada 1 fue CHANGES_REQUESTED con tres cambios, y los tres están
resueltos.

**Alcance**: `scripts/medir_f009_t0.py`, `tests/test_f009_t0_script.py` y `progress/impl_F-009_T0a_quinquies.md`. No
se ha ejecutado nada contra la API, Azure ni el SQL Server.

**Fuera de la revisión**: C3 hexagonal (es un script de `scripts/`), C3 bis, C4 ter y RM1-RM6 (no hay campaña de
mutación).

**Rigor `critico`**: exige RED con salida real, cobertura y la sección «Evidencias». **Mutación N/A, justificada**
por N3: el script y su test se retiran antes de T1.

## Pasada 1 (resumen)

Comprobado y correcto en `5262a74`:

- **Columnas**: las de `mov` y `proalm` existen en el diccionario. Los índices usados son `pfhi` y `pafhi`.
- **Construcción de la fórmula**:
  - `prepma_ant` sale del `mov` anterior del producto, en cualquier almacén.
  - `stock_otros` es el `TOP 1 almcan` anterior de cada almacén de `proalm` distinto del propio.
  - El orden es `fechor DESC, ide DESC`, con un desempate en forma de rango que excluye el propio `mov`.
  - El stock propio se calcula como `almcan - canent + cansal`, con un control contra el `almcan` anterior.
- **Muestra**: `TOP 50` determinista (por `m.ide`), metida en una derivada para que los `APPLY` solo se hagan
  sobre ella. Los 4 `?` cuadran.
- **Seguridad de la sentencia**:
  - No aparece el patrón del error 130 ni `ISNULL(…, -1)`.
  - Va envuelta.
  - `--solo M14` la lanza.
  - Distingue «SIN MEDICIÓN» de «cero filas».
  - Las devoluciones van aparte.
- **Riesgo de tiempo: bajo-medio, aceptable**:
  - Son seeks por `pafhi` por cada otro almacén del producto.
  - Hay dos barridos de `proalm`.
- **RED reproducida**: `10 failed`.

| # | Cambio requerido (pasada 1) | Estado (pasada 2) |
|---|---|---|
| 1 | El acierto solo admitía 1e-6 relativo. Con el prepma redondeado a 4 decimales, el propio código daba «NO confirmada (0 de 20)» con la holgada al 100 %, es decir, concluía lo contrario de lo que dice el dato | **Resuelto** (ver «Segunda pasada», punto 1) |
| 2 | Con base 0, la lectura concluía «NO confirmada (0 de 0)» | **Resuelto** (punto 2) |
| 3 | `init.sh` en rojo por la edición de `design.md` del spec-author, aún sin commit | **Resuelto** fuera de esta tarea: la v8 está cerrada en `8a6ecab` y la puerta de tamaño queda dentro (requirements 150/150, design 249/250) |

## Segunda pasada (`fb04d9a`, `832b9c5`)

He leído el diff, no el informe.

1. **Tolerancia del acierto**:
   - Nueva función `acierta_m14e`, que admite `|a - b| ≤ max(TOL_RELATIVA_M14E · max(1, |a|, |b|),
     TOL_ABSOLUTA_M14E)`.
   - `TOL_ABSOLUTA_M14E` vale `float(_TOL_PRECIO)`, es decir 0,0001: la misma que usan M14c y M14d. La constante
     tiene nombre y comentario.
   - El acierto de las variantes y el de «sin cambio» usan esa función.
   - La cifra con 1e-6 queda solo como informativa («exacta»).
   - La holgada de 1e-3 desaparece. Era demasiado ancha para decidir entre variantes.
   - La línea «Hipótesis» declara la regla de acierto que aplica.
   - **Reproducido con mis dos casos de la pasada 1**:
     - Con el prepma redondeado a 4 decimales: «Hipótesis M14e … CONFIRMADA (20 de 20)».
     - Con una fórmula errónea, el mismo caso redondeado da «NO confirmada (0 de 20)».
     - La tolerancia nueva no deja pasar lo que no es.
2. **Base 0**:
   - Si un tipo de `mov` tiene base 0, su línea dice «ningún mov con anterior del producto ⇒ no se contrasta» y
     devuelve base 0.
   - La hipótesis distingue tres casos: «ninguna entrada en la muestra» y «ninguna entrada con mov anterior del
     producto», que acaban los dos en «no se concluye», y el veredicto normal.
   - **Reproducido** con mi caso de la pasada 1.
3. **Observaciones aplicadas**:
   - (a) Nueva cifra «no discriminan» (principal = (a) = (b), con la misma tolerancia). Es informativa y no compite.
   - (b) `m.docide` pasa a la muestra y la sentencia exterior. La lectura cuenta albaranes y productos distintos.
     Añade una columna y ningún `?` nuevo, así que el riesgo de tiempo no cambia.
   - (c) y (d) siguen como límites declarados en el informe.

**Verificación propia (pasada 2)**:

- `bash harness/init.sh` tal cual: **en verde** (exit 0).
  - 2386 passed, 1 skipped (81,7 s).
  - `PUERTA COBERTURA` [OK]: 98,9 % (1402/1417).
  - `PUERTA TAMAÑO` [OK].
  - Rama correcta.
- **RED del ciclo reproducida** en una copia del scratchpad (tests de `fb04d9a` contra el script de `5262a74`):
  `3 failed, 650 passed`. Cuadra con los 3 fallos del informe.
- ruff: limpio en los dos ficheros.
- Informe del implementer: 203 líneas (tope 220), con «Ciclo 1 de revisión», RED y «Evidencias».
- Árbol: solo el fichero sin trackear de la raíz (previo y ajeno) y este informe.

## Checkpoints (estado final)

- **C1**:
  - [x] `init.sh` exit 0.
  - [x] Ficheros del arnés presentes.
- **C2**:
  - [x] Ninguna feature en `in_progress`.
  - [x] Rama correcta.
  - N/A «`done` sin historia»: no se cierra ninguna feature.
- **C3**:
  - N/A hexagonal: es un script de `scripts/`.
  - [x] Primera línea con la ruta, sin secretos ni dependencias nuevas.
  - [x] SQL parametrizado, sin error 130 y sin `ISNULL(…, -1)`.
  - [x] Lecturas fieles al dato (cambios 1 y 2).
- **C4**:
  - [x] Cada punto del encargo y cada cambio tiene test (653 en la prueba de humo).
  - [x] Sin red ni BBDD.
  - [x] T0b-quinquies queda como MANUAL del humano (`--solo M14`).
- **C4 bis**:
  - [x] RED con salida real, reproducida en las dos entregas.
  - [x] Cobertura [OK].
  - [x] Mutación N/A (N3).
  - [x] «Evidencias».
- **C5**:
  - [x] Commits `F-009 T0a-quinquies: …`.
  - [x] Sin temporales.
  - N/A «tarea de `tasks.md`»: es el paso del implementer previo a T0b-quinquies.

## Trazabilidad (prefijo `test_f009_t0a_quinquies_`)

| Punto | Test |
|---|---|
| Muestra pequeña por índices, suma en derivada, `?` | `m14e_sql_muestra_pequena_por_indices`, `m14_pasa_la_ventana_dos_veces` |
| Fórmula, variantes a-c, «solo almacén», tipos | `formula_y_variantes` |
| Veredicto, umbral, tolerancia de precio (cambio 1) | `lectura_regla_y_variante_ganadora`, `lectura_en_el_limite_del_umbral`, `c1_prepma_redondeado_a_4_decimales_confirma` |
| Base 0, sin anterior, denominador 0 (cambio 2) | `sin_anterior_y_denominador_cero`, `c1_base_cero_no_se_contrasta_ni_concluye` |
| Devoluciones aparte, coherencia, `proalm`, no discriminan | `devoluciones_aparte_y_coherencia`, `c1_filas_que_no_discriminan_y_representatividad` |
| Sin medición frente a cero filas; un fallo no pierde M14 | `sin_medicion_frente_a_cero_filas`, `un_fallo_no_pierde_el_bloque_y_main` |

## Observaciones (no bloquean; para el spec-author al leer T0b-quinquies)

a. Con la tolerancia absoluta de 0,0001, dos variantes que se separen menos que eso empatan. La lectura nombra el
   empate, y la cifra «no discriminan» dice cuántas filas no deciden nada. Si la mayoría de la muestra no
   discrimina, un «REGLA escribible» vale poco: hay que leerlo junto a esa cifra.
b. `proalm`: la sonda solo comprueba el almacén propio. Si `proalm` omite almacenes que tienen stock, `stock_otros`
   sale corto. Es un límite declarado.
c. La muestra es de 50 filas, así que el 95 % son 48. Si sale REGLA, conviene ampliar `MUESTRA_M14E` y mirar cuántos
   albaranes y productos distintos hay en ella.
