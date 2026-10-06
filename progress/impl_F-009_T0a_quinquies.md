<!-- progress/impl_F-009_T0a_quinquies.md -->
# Informe del implementer · F-009 T0a-quinquies (M14e: ¿`mov.prepma` = media ponderada GLOBAL?)

Fecha: 2026-10-06. Rama `feature/F-009-alta-albaran-compra`. F-009 sigue en `spec_ready`; T0a-quinquies autorizada
por el humano. **No se ha llamado a la API, ni a Azure, ni al SQL Server**: el script lo lanza el humano.
Commits: `5e9975f` (código y tests), `fb04d9a` (ciclo 1 de revisión). No se han tocado la spec, el contrato, `progress/spec_F-009.md`,
`progress/current.md`, `harness/features.json`, `BACKLOG.md`, `.env` ni el fichero sin trackear de la raíz.

## Qué cambió

| Fichero | Cambio |
|---|---|
| `scripts/medir_f009_t0.py` | M14e, nueva parte de M14 (`--solo M14`), tras M14d |
| `tests/test_f009_t0_script.py` | 636 → 650 tests, sin red ni BBDD |

Hipótesis: `prepma_nuevo = (prepma_ant × stock_global_ant + can × pre) / (stock_global_ant + can)`, con `prepma_ant`
el `prepma` del `mov` anterior del **producto** (cualquier almacén, `fechor DESC, ide DESC`) y `stock_global_ant` =
Σ del último `almcan` anterior de cada **otro** almacén + el stock del propio antes de la entrada
(`almcan - canent + cansal`).

## Diseño

**Una sentencia, `M14e_muestra`** (4 `?`: la ventana `VENTANA_M9` dos veces), que devuelve los componentes por fila;
**la fórmula se evalúa en Python** (función pura, probada sin red). Diccionario: `mov` (`prepma`, `almcan`, `canent`,
`cansal`, `pre`, `prc`, `fechor`; índices `pfhi` = producto, fechor y `pafhi` = producto, almacén, fechor) y
`proalm` (producto × almacén, sin índice declarado por `proide`).

- **Muestra**: derivada `SELECT TOP MUESTRA_M14E (50) … ORDER BY m.ide DESC` de los `mov` de albarán (`doctip 14`)
  de la ventana, guiada desde `con` (`tip`, `fec`) y `mov` por `doclin`. Va en una derivada para que los `APPLY` se
  hagan solo sobre las 50 filas.
- `prepma_ant`: `OUTER APPLY TOP 1` del `mov` anterior del producto por `pfhi` (desempate como rango, igual que M14d).
- `almcan_ant_alm`: `OUTER APPLY TOP 1` del `mov` anterior del mismo producto y almacén por `pafhi` (control de
  coherencia con `almcan - canent + cansal`).
- `stock_otros`: derivada agrupada por `mov` de la muestra: almacenes del producto en `(SELECT DISTINCT proide,
  almide FROM dbo.proalm)` distintos del suyo, y en cada uno un `TOP 1 x.almcan` anterior por `pafhi`;
  `SUM(w.almcan)` sobre la columna del `APPLY` dentro de la derivada (no es el patrón del error 130; el detector y
  el guardia real lo aceptan). También `almacenes_otros` y `almacenes_con_mov`. `proalm` va unida por `JOIN` a la
  muestra (un hash, no un barrido por fila).
- `alm_propio_en_proalm`: si el almacén del propio `mov` está en `proalm` (sonda de que `proalm` lista los
  almacenes del producto: si no, `stock_otros` se quedaría corto).

**Lectura** (`lectura_m14e`), por tipo de `mov` (`clasifica_m14e`, punto d): `entrada` (`canent > 0`), `devolucion`
(`canent < 0`, o salida del albarán: la regla B de M5) y `otro`. Variantes (`variantes_m14e`), en orden de desempate:

| Variante | Cambio respecto a la principal |
|---|---|
| `global_anterior` (principal) | stock global anterior, `canent`, `pre` |
| `global_posterior` (a) | stock global con el `almcan` posterior del propio almacén |
| `can_neta` (b) | `canent - cansal` |
| `precio_prc` (c) | `prc` en vez de `pre` |
| `solo_almacen` | solo el stock anterior del almacén del `mov` (control frente a la versión por almacén) |

- Acierto (desde el ciclo 1): `acierta_m14e`, diferencia ≤ max(**`TOL_RELATIVA_M14E` = 1e-6** relativo,
  **`TOL_ABSOLUTA_M14E` = `float(_TOL_PRECIO)` = 0,0001** absoluto, la tolerancia de precio de M14c y M14d).
  Informativa: «la principal exacta» (solo 1e-6 relativo).
- Base: los `mov` con `mov` anterior del producto. `prepma_ponderado` devuelve `None` sin anterior o con
  denominador 0 (cuenta como fallo y se informa aparte), y se cuenta el stock global anterior < 0 (M15: hay stock
  negativo).
- Veredicto por tipo con `_veredicto_m16c` (≥ **`UMBRAL_REGLA_ESCRIBIBLE` = 95 %** ⇒ «REGLA escribible «…»», empates
  nombrados; si no, «sin regla escribible (la mejor: …)»), más todas las variantes, la exacta, las que no discriminan y «prepma = el del
  `mov` anterior (sin cambio)».
- Comprobaciones: almacén del `mov` en `proalm`, coherencia de `almcan`, nº de otros almacenes y con `mov` anterior.
- «Hipótesis M14e (… en las entradas): CONFIRMADA / NO confirmada»; sin entradas, «ninguna entrada en la muestra ⇒ no
  se concluye». `None` ⇒ «`M14e_muestra` SIN MEDICIÓN»; `[]` ⇒ «cero filas».

## Riesgo de tiempo

Bajo: 50 filas; por fila dos seeks (`pfhi`, `pafhi`) y uno por `pafhi` por cada otro almacén del producto
(decenas como mucho: unos miles de seeks en total), dos lecturas `DISTINCT` de `proalm` y la muestra dos veces (es
la de M14d, 0,5 s en T0b-ter). Va envuelta en `_leer_tabla` y en el `try` de las partes de `m14`: si falla, se anota
y el resto de M14 sigue. La sentencia, en su forma final, está en el script (`SQL["M14e_muestra"]`).

## Límites conocidos (no cambian lo que se decide)

- Si `proalm` no lista algún almacén del producto, `stock_otros` sale corto: lo vigila `alm_propio_en_proalm`.
- `mov` con el mismo `fechor` en otro almacén se ordenan por `ide` (el mismo desempate que M14d).
- 50 `mov` son una muestra: si sale «REGLA», se puede ampliar con `MUESTRA_M14E` sin tocar nada más.

## Fase RED (comando exacto, salida real)

Tests escritos antes que el código:

```
$ .venv/Scripts/python.exe -m pytest tests/test_f009_t0_script.py -q -p no:cacheprovider -k "t0a_quinquies"
E           AttributeError: module 'scripts.medir_f009_t0' has no attribute 'prepma_ponderado'
E       AttributeError: module 'scripts.medir_f009_t0' has no attribute 'lectura_m14e'. Did you mean: 'lectura_m14b'?
E       KeyError: 'M14e_muestra'
FAILED tests/test_f009_t0_script.py::test_f009_t0a_quinquies_devoluciones_aparte_y_coherencia
FAILED tests/test_f009_t0_script.py::test_f009_t0a_quinquies_formula_y_variantes
FAILED tests/test_f009_t0_script.py::test_f009_t0a_quinquies_lectura_en_el_limite_del_umbral[94-False]
FAILED tests/test_f009_t0_script.py::test_f009_t0a_quinquies_lectura_en_el_limite_del_umbral[95-True]
FAILED tests/test_f009_t0_script.py::test_f009_t0a_quinquies_lectura_regla_y_variante_ganadora
FAILED tests/test_f009_t0_script.py::test_f009_t0a_quinquies_m14_pasa_la_ventana_dos_veces
FAILED tests/test_f009_t0_script.py::test_f009_t0a_quinquies_m14e_sql_muestra_pequena_por_indices
FAILED tests/test_f009_t0_script.py::test_f009_t0a_quinquies_sin_anterior_y_denominador_cero
FAILED tests/test_f009_t0_script.py::test_f009_t0a_quinquies_sin_medicion_frente_a_cero_filas
FAILED tests/test_f009_t0_script.py::test_f009_t0a_quinquies_un_fallo_no_pierde_el_bloque_y_main
10 failed, 636 deselected in 2.89s
```

Con el código, el primer intento dio `NameError: name 'MUESTRA_M14E' is not defined` (la derivada de la muestra se
compone antes del bloque de constantes): la constante se movió junto a `MUESTRA_DEVOLUCIONES`. Después:
`650 passed, 1 warning in 5.62s`; ruff limpio en los dos ficheros (por defecto y `--preview --select E2,W,E7,F`).

## Trazabilidad (encargo → test, prefijo `test_f009_t0a_quinquies_`)

| Punto | Test |
|---|---|
| Muestra pequeña por índices (`TOP 50`, `pfhi`, `pafhi`, `proalm DISTINCT`), suma en derivada, sin error 130 | `m14e_sql_muestra_pequena_por_indices` |
| `?` = parámetros (ventana dos veces) | `m14_pasa_la_ventana_dos_veces` |
| Fórmula, denominador 0, sin anterior, variantes a-c y «solo almacén», tipos (d), tolerancia con nombre | `formula_y_variantes` |
| Lectura: regla principal / gana la variante (a); hipótesis | `lectura_regla_y_variante_ganadora` |
| Devoluciones aparte; coherencia de `almcan` y `proalm` | `devoluciones_aparte_y_coherencia` |
| Umbral con nombre en el límite (95 / 94 de 100) | `lectura_en_el_limite_del_umbral` |
| Denominador 0 y stock negativo informados | `sin_anterior_y_denominador_cero` |
| Sin medición ≠ cero filas ≠ sin entradas | `sin_medicion_frente_a_cero_filas` |
| Un fallo no pierde M14; la parte sale en `m14` | `un_fallo_no_pierde_el_bloque_y_main` |
| Solo SELECT, guardia real, sin `cla`/`pas`, sin `ISNULL(…, -1)` | los parametrizados previos sobre todo `SQL` (incluyen `M14e_muestra`) |

## Ciclo 1 de revisión (`progress/review_F-009_T0a_quinquies.md`, CHANGES_REQUESTED) · `fb04d9a`

| Punto | Cambio |
|---|---|
| 1 Tolerancia | El acierto usa `acierta_m14e`: max(1e-6 relativo, `TOL_ABSOLUTA_M14E` = `float(_TOL_PRECIO)` = 0,0001). Un prepma guardado con 4 decimales (hasta 5e-5) ya no refuta la hipótesis. 1e-6 queda como «la principal exacta», informativa; se quita `TOL_HOLGADA_M14E` (1e-3 era demasiado ancha para decidir entre variantes) |
| 2 Base 0 | Un tipo sin ningún `mov` con anterior del producto dice «ningún mov con anterior del producto ⇒ no se contrasta» (sin veredicto ni «0 de 0»); la hipótesis, «ninguna entrada con mov anterior del producto ⇒ no se concluye» |
| 3 `init.sh` | No es de esta tarea: ver «Salida real de `bash harness/init.sh`» |
| obs. a | Se cuentan las filas que **no discriminan** (principal = (a) = (b) dentro de la tolerancia) |
| obs. b | `docide` en la muestra; las comprobaciones dicen en cuántos albaranes y productos están los 50 `mov` |

Obs. c (sonda de `proalm`) y d (ampliar la muestra si sale REGLA) quedan como límites declarados.

Tests nuevos (`test_f009_t0a_quinquies_c1_*`): prepma redondeado a 4 decimales (exacto 12,04545…, guardado 12,0455:
3,8e-6 relativo) ⇒ CONFIRMADA y «exacta 0 de 20», y con la fórmula desviada 0,01 ⇒ NO confirmada; base 0 ⇒ «no se
contrasta» y «no se concluye», sin «0 de 0»; filas que no discriminan y albaranes/productos de la muestra.
**RED** (tests antes que el código, contra el script de `5262a74`):

```
$ .venv/Scripts/python.exe -m pytest tests/test_f009_t0_script.py -q -p no:cacheprovider -k "t0a_quinquies_c1"
E       AttributeError: module 'scripts.medir_f009_t0' has no attribute 'TOL_ABSOLUTA_M14E'. Did you mean: 'TOL_HOLGADA_M14E'?
E       AssertionError: assert 'ningún mov con anterior del producto ⇒ no se contrasta' in 'M14e entrada (3 mov; con mov anterior del producto 0; denominador 0: 0; stock global anterior < 0: 0): sin regla escr...con el stock anterior, en las entradas): NO confirmada (0 de 0; REGLA escribible = ≥ 95 %, tolerancia relativa 1e-06).'
E       AssertionError: assert ('s.docide,' in 'SELECT s.ide, s.proide, s.almide, s.canent, ...')
FAILED tests/test_f009_t0_script.py::test_f009_t0a_quinquies_c1_prepma_redondeado_a_4_decimales_confirma
FAILED tests/test_f009_t0_script.py::test_f009_t0a_quinquies_c1_base_cero_no_se_contrasta_ni_concluye
FAILED tests/test_f009_t0_script.py::test_f009_t0a_quinquies_c1_filas_que_no_discriminan_y_representatividad
3 failed, 650 deselected in 1.26s
```

Con el código: `653 passed, 1 warning in 4.37s`; ruff limpio en los dos ficheros (por defecto y
`--preview --select E2,W,E7,F`).

## Salida real de `bash harness/init.sh` (tras el commit `fb04d9a` del ciclo 1)

```
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 80 avisos (deuda previa, no bloquea).   (los dos ficheros tocados: «All checks passed!»)
2386 passed, 1 skipped, 1 warning in 110.53s (0:01:50)
[OK] pytest en verde (con medición de cobertura)
[OK] PUERTA COBERTURA: 98.9% de 1417 líneas cambiadas cubiertas (1402/1417, umbral 80%, nivel critico)
[KO] PUERTA TAMAÑO: F-009 se pasa de los topes:
    specs/F-009-alta-albaran-compra/design.md: 252 líneas > tope 250
[OK] Rama actual: feature/F-009-alta-albaran-compra
1 comprobaciones fallidas. NO empieces a trabajar.
```

**init.sh sale en rojo SOLO por la puerta de tamaño de la spec**: `design.md` (y `requirements.md`) están
modificados y sin commit (`git status`: ` M specs/F-009-alta-albaran-compra/design.md`, ` M …/requirements.md`): es
la edición en curso de la spec v8 por el spec-author, que el encargo me prohíbe tocar. Lo mío, verificado: compileall
[OK], la suite completa dentro de init.sh `2386 passed, 1 skipped`, la prueba de humo `653 passed` y `PUERTA
COBERTURA` [OK]. En la primera entrega el rojo era el mismo (entonces `requirements.md` 151 > 150 y luego
`design.md` 278 > 250).

## Comando para el humano (PowerShell 5.1) · T0b-quinquies

```powershell
Set-Location C:\Users\pgris\PycharmProjects\sigrid-api
git switch feature/F-009-alta-albaran-compra
& .\.venv\Scripts\python.exe -m scripts.medir_f009_t0 --solo M14
```

- Solo lecturas por `POST /api/sql/read`; credenciales del entorno o del `.env`, nunca impresas.
- Mirar en la CONCLUSIÓN de M14: «M14e entrada (…)», «M14e devolucion (…)», «M14e comprobaciones» e «Hipótesis M14e».
  Si se lanza junto con lo de T0b-quater: `--solo M14 M16 M19`.
- Si sale «SIN MEDICIÓN», repetir con `--solo M14`; no relanzar justo tras un corte.
- El fichero `%TEMP%\f009_t0_<fecha>.txt` lleva datos de negocio (precios y stocks de la muestra): **se pega entero**
  y no se versiona.

## Qué queda fuera y qué falta

- Fuera: ejecutar el script (humano); volcar el resultado en la spec (spec-author); retirar script y test antes de
  T1 (N3).
- MANUAL pendiente: T0b-quinquies (`--solo M14`).
- Pendiente ajeno: que el spec-author deje la spec v8 (`design.md`, `requirements.md`) dentro de los topes para que
  `init.sh` vuelva a verde.

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests de la prueba de humo | 653 pasan tras el ciclo 1 (650 en la entrega; antes 636), 4,37 s |
| Suite completa | 2386 passed, 1 skipped, 110,53 s |
| Cobertura de líneas cambiadas | 98,9 % (1402/1417), `PUERTA COBERTURA` de init.sh |
| Mutación | No aplica: script de mediciones desechable que se retira antes de T1 (N3, decisión del humano), como en T0a-ter y T0a-quater; no se lanzó campaña |
| ruff en los dos ficheros | sin avisos (también `--preview --select E2,W,E7,F`) |
