<!-- progress/impl_F-009_T0a_ter.md -->
# Informe del implementer · F-009 T0a-ter (M16c en el script de T0)

Fecha: 2026-10-05. Rama `feature/F-009-alta-albaran-compra`. F-009 sigue en `spec_ready`; T0 está
autorizada por el humano. **No se ha llamado a la API, ni a Azure, ni al SQL Server**: el script lo lanza
el humano. Origen: el bloque M16 de `%TEMP%\f009_t0_20261005_163206.txt` (M16b y su muestra TOP 20).

## Qué cambió

| Fichero | Cambio |
|---|---|
| `scripts/medir_f009_t0.py` | M16c como **subbloque de M16** (se lanza con `--solo M16`): 3 sentencias, 3 lecturas, umbral con nombre |
| `tests/test_f009_t0_script.py` | 374 → 402 tests, sin red ni BBDD |

No se han tocado la spec, `progress/spec_F-009.md`, `progress/current.md`, `harness/features.json`,
`BACKLOG.md`, `infrastructure/`, `.env` ni el fichero sin trackear de la raíz. El cambio sin commit de
`specs/F-009-…/requirements.md` que hay en el árbol es del spec-author: no entra en mi commit.

**Elección: subbloque de M16, no bloque nuevo.** `MEDICIONES` sigue siendo M1-M18 (la spec numera así
y hay un test que lo fija); M16c comparte universo, grupos y joins con M16b, y el humano la lanza con
`--solo M16` (unos 20 s en total si M16c tarda como M16b). Va **antes** de `M16b_dcaproana`, que es la
sentencia más expuesta por volumen de M16: si esa se corta, M16c ya está medida.

## M16c: qué mide

Universo de M16b: líneas de albarán **sin vincular desde 2025**, por grupo (`MA9999`, `QA9999`,
`SM9999`, `SB9999` de la empresa 1 y «resto», como `?`) × con/sin partida. Alias de M16b: `k` (caa de
la línea), `kc`/`cf`/`oc`/`ec` (con de la caa, de la cuenta, de la obra y del centro), `nl` (naturaleza
de la línea, `dcapro.natide`) y `nt` (la del producto, `pro.natide`). Diccionario: `caa`, `cua`, `obr`
y `cen` son «Propiedades de con» (su código está en `con.cod`, texto de 24); `caa.cenide` existe;
`auxpronat.caagascod/caaexicod/cuacomcod` son texto de 24; `ctrpro` tiene `natide`, `cenide`,
`caaide` y `obride`.

**Regla de la caa** (`_regla_caa(nat, codigo)`), con `gas = RTRIM(LTRIM(<nat>.caagascod))`:

```
k.cenide = d.cenide AND CHARINDEX('.', gas) > 0
AND RTRIM(LTRIM(kc.cod)) = RTRIM(LTRIM(<obra|centro>.cod)) + '.' + SUBSTRING(gas, CHARINDEX('.', gas) + 1, 24)
AND u.cod IS NULL
```

- Sin `.` en `caagascod` (o nulo) no casa. Códigos recortados por si son `CHAR`.
- `u` = pares (`cenide`, código) **repetidos** entre las caa (`caa` ⨝ `con`, `GROUP BY … HAVING
  COUNT(*) > 1`). Una regla escribible busca LA caa por centro y código: si el par se repite, no fija
  una y la línea **no cuenta como acierto**. Es lo que separa «caaide = la caa con …» de «el código de
  su caa tiene esa forma» (criterio identificativa/propiedad de la revisión de T0a-bis).
- Cuatro variantes: naturaleza de la **línea**/del **producto** × código de la **obra**/del **centro**.

**Sentencias** (todas `SELECT` de una sentencia, valores de fuera con `?`, agregados sobre banderas de
una tabla derivada, sin `ISNULL(…, -1)`):

| Sentencia | Qué devuelve | Parámetros |
|---|---|---|
| `M16c_reglas` | por grupo × partida: `n`, `regla_linea_obra/centro`, `regla_producto_obra/centro`, `cueide_linea/producto` (`cf.cod` = `cuacomcod` recortado, no vacío), `linea_sin_mod`, `linea_sin_punto`, `linea_sin_naturaleza`, `producto_sin_mod`, `linea_caaexicod`, `producto_caaexicod`, `caa_repetida`, `obra_igual_centro` | empresa + 4 genéricos |
| `M16c_naturalezas_ma` | TOP 15 naturalezas de la línea en el MA9999 de la empresa 1: código, resumen, `caagascod`, líneas, aciertos de la regla línea/producto (obra), líneas con naturaleza = la del producto | empresa, `GENERICO_NATURALEZAS_M16C` |
| `M16c_vinculadas` | control: la misma regla sobre `ctrpro` (su `natide`, `obride`, `cenide`, `caaide`), por grupo; cuenta **líneas de contrato distintas** (`COUNT(DISTINCT CASE …)`) | empresa + 4 genéricos |

El control de las vinculadas **sí es barato**: entra por `ctrpro` con su clave primaria
(`t.ide = d.linoriide`, `d.docoritip = 44`), el mismo camino que `M16_caa_con_partida` (1,0 s el
2026-10-05). No se omite.

**Lecturas automáticas** (umbral con nombre `UMBRAL_REGLA_ESCRIBIBLE = 0.95`):

- `lectura_m16c`: por grupo × partida y en **TOTAL**: «caa ⇒ REGLA escribible «…» x de n» si la mejor
  candidata llega al 95 %, o «sin regla escribible (la mejor: …)»; lo mismo para `cueide`. Desempate
  en orden: línea antes que producto, obra antes que centro; las empatadas se nombran. Una segunda
  línea por grupo con «dónde no aplica o puede fallar» (sin `MOD.`, sin `.`, sin naturaleza,
  `caaexicod`, caa repetida, obra = centro). Cierra con «Hipótesis M16c … CONFIRMADA / NO confirmada
  en el total» (la de la línea ≥ 95 % y no menor que la del producto).
- `lectura_m16c_naturalezas`: las tres más usadas y en cuáles la regla de la línea no llega al 95 %.
- `lectura_m16c_vinculadas`: % de `ctrpro` que cumple la regla ⇒ «también explica las del contrato» o
  «NO sigue la regla (no sirve de control)».
- **`None` (falló la lectura) ⇒ «`<sentencia>` SIN MEDICIÓN»; `[]` ⇒ texto con «cero filas»**. Nunca
  se confunden: hay test de las tres lecturas y del bloque con cada sentencia rota.

## Decisiones y desviaciones

1. Subbloque de M16 (arriba). 2. La variante «centro» usa el código del centro de la **línea**
(`ec` = `con` de `dcapro.cenide`), como pide el encargo. 3. `caa_repetida` y el filtro `u.cod IS NULL`
no estaban pedidos: sin ellos la regla mediría una propiedad del código y no que identifique UNA caa.
Coste: agrupar `caa` ⨝ `con` (tabla de cuentas, no de movimientos). 4. Sin medir, también, la naturaleza
del producto en el control de las vinculadas: el encargo pide «la naturaleza de la línea del contrato».
5. Texto de cero filas de `M16c_reglas` nombra la sentencia: con «No hay líneas sin vincular…» chocaba
con el test de T0a-bis que prohíbe esa frase cuando falla `M16b_fuentes` (un falso positivo de redacción,
no de lógica; se vio en verde→rojo al ejecutar el fichero entero).

## Riesgo de tiempo

Bajo. `M16c_reglas` y `M16c_naturalezas_ma` hacen los mismos joins que `M16b_codigos` (6,1 s) más el
`LEFT JOIN` a `u`; `M16c_vinculadas`, los de `M16_caa_con_partida` (1,0 s) más `auxpronat` y tres `con`
por clave primaria. Todas con `TIMEOUT_PESADO_S` y envueltas: una que falle se anota y el bloque sigue.

## Fase RED (comando exacto, salida real)

Tests nuevos escritos antes que el código:

```
$ .venv/Scripts/python.exe -m pytest tests/test_f009_t0_script.py -q -p no:cacheprovider -k "t0a_ter"
FAILED tests/test_f009_t0_script.py::test_f009_t0a_ter_existen_las_sentencias_de_m16c
FAILED tests/test_f009_t0_script.py::test_f009_t0a_ter_m16c_va_parametrizada_y_sin_isnull_con_literal_negativo[M16c_reglas]
FAILED tests/test_f009_t0_script.py::test_f009_t0a_ter_m16c_va_parametrizada_y_sin_isnull_con_literal_negativo[M16c_naturalezas_ma]
FAILED tests/test_f009_t0_script.py::test_f009_t0a_ter_m16c_va_parametrizada_y_sin_isnull_con_literal_negativo[M16c_vinculadas]
FAILED tests/test_f009_t0_script.py::test_f009_t0a_ter_m16c_construye_el_codigo_con_la_naturaleza_de_la_linea_y_la_del_producto
FAILED tests/test_f009_t0_script.py::test_f009_t0a_ter_m16c_la_regla_exige_que_centro_y_codigo_identifiquen_una_sola_caa
FAILED tests/test_f009_t0_script.py::test_f009_t0a_ter_m16c_vinculadas_usa_la_linea_del_contrato
FAILED tests/test_f009_t0_script.py::test_f009_t0a_ter_m16_pasa_los_grupos_y_el_generico_de_las_naturalezas
FAILED tests/test_f009_t0_script.py::test_f009_t0a_ter_lectura_m16c_regla_escribible_y_manda_la_linea
FAILED tests/test_f009_t0_script.py::test_f009_t0a_ter_lectura_m16c_en_el_limite_del_umbral[95-True]
FAILED tests/test_f009_t0_script.py::test_f009_t0a_ter_lectura_m16c_en_el_limite_del_umbral[94-False]
FAILED tests/test_f009_t0_script.py::test_f009_t0a_ter_lectura_m16c_manda_el_producto_si_acierta_mas
FAILED tests/test_f009_t0_script.py::test_f009_t0a_ter_lecturas_m16c_distinguen_sin_medicion_de_cero_filas
FAILED tests/test_f009_t0_script.py::test_f009_t0a_ter_lectura_de_las_naturalezas_de_ma9999
FAILED tests/test_f009_t0_script.py::test_f009_t0a_ter_lectura_del_control_con_las_vinculadas
FAILED tests/test_f009_t0_script.py::test_f009_t0a_ter_un_fallo_de_m16c_no_pierde_el_bloque_ni_se_lee_como_vacio[M16c_reglas]
FAILED tests/test_f009_t0_script.py::test_f009_t0a_ter_un_fallo_de_m16c_no_pierde_el_bloque_ni_se_lee_como_vacio[M16c_naturalezas_ma]
FAILED tests/test_f009_t0_script.py::test_f009_t0a_ter_un_fallo_de_m16c_no_pierde_el_bloque_ni_se_lee_como_vacio[M16c_vinculadas]
FAILED tests/test_f009_t0_script.py::test_f009_t0a_ter_main_solo_m16_con_m16c
19 failed, 374 deselected in 2.24s
```

Errores distintos (agrupados con `grep "^E " | sort | uniq -c`): `KeyError: 'M16c_reglas'`;
`AttributeError: … no attribute 'UMBRAL_REGLA_ESCRIBIBLE'`; `… 'lectura_m16c'` (×4);
`… 'lectura_m16c_naturalezas'`; `… 'lectura_m16c_vinculadas'`; `assert ['M16c_reglas...c_vinculadas'] == []`;
y el de `main`: `'M16c' in '=== M16 · analítica, almacén y centro de las líneas (H10, H13) y origen de
caaide (M16b) ==='` falso.

Tras el código, fichero entero: `1 failed, 401 passed` (la colisión de redacción de la decisión 5); tras
corregirla, `402 passed, 1 warning in 2.19s`. ruff limpio en los dos ficheros (por defecto y con
`--preview --select E2,W,E7,F`; un `ISC004` intermedio se corrigió).

## Trazabilidad (encargo → test)

| Punto del encargo | Test |
|---|---|
| `regla_linea` / `regla_producto`, obra y centro, `SUBSTRING`/`CHARINDEX`, sin `.` no casa, `RTRIM`/`LTRIM` | `..._m16c_construye_el_codigo_con_la_naturaleza_de_la_linea_y_la_del_producto` |
| (centro, código) identifica una sola caa | `..._m16c_la_regla_exige_que_centro_y_codigo_identifiquen_una_sola_caa` |
| `cueide_linea` / `cueide_producto` | el de construcción (`cf.cod` = `cuacomcod`) y `..._lectura_m16c_regla_escribible...` |
| sin `MOD.`, `caaexicod` | el de construcción (columnas) y la lectura (`naturaleza de la línea sin «MOD.»`) |
| naturalezas del MA9999 | `..._lectura_de_las_naturalezas_de_ma9999`, `..._m16_pasa_los_grupos_y_el_generico...` |
| control vinculadas | `..._m16c_vinculadas_usa_la_linea_del_contrato`, `..._lectura_del_control_con_las_vinculadas` |
| umbral con nombre, límite 95/94 | `..._lectura_m16c_en_el_limite_del_umbral[95-True/94-False]`, `..._manda_el_producto_si_acierta_mas` |
| sin medición ≠ cero filas | `..._lecturas_m16c_distinguen_sin_medicion_de_cero_filas`, `..._un_fallo_de_m16c_no_pierde_el_bloque...` (×3) |
| `?`, sin genéricos literales, sin `ISNULL(…, -1)` | `..._m16c_va_parametrizada_y_sin_isnull_con_literal_negativo` (×3) |
| solo lectura, guardia real, error 130 | los parametrizados sobre todo `SQL` (`..._toda_sentencia_es_select...`, `..._el_guardia_de_lectura...`, `..._ninguna_sentencia_agrega_sobre_una_subconsulta`) |
| `--solo M16` | `..._main_solo_m16_con_m16c` |

## Salida real de `bash harness/init.sh`

```
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 80 avisos (deuda previa, no bloquea).   (los dos ficheros tocados: «All checks passed!»)
2135 passed, 1 skipped, 1 warning in 94.18s (0:01:34)
[OK] pytest en verde (con medición de cobertura)
[OK] PUERTA COBERTURA: 98.4% de 830 líneas cambiadas cubiertas (817/830, umbral 80%, nivel critico)
[OK] PUERTA TAMAÑO: F-009 dentro de los topes (requirements 150/150, design 250/250)
[OK] Rama actual: feature/F-009-alta-albaran-compra
ENTORNO LISTO. Puedes trabajar.
```

## Comando para el humano (PowerShell 5.1)

```powershell
Set-Location C:\Users\pgris\PycharmProjects\sigrid-api
git switch feature/F-009-alta-albaran-compra
& .\.venv\Scripts\python.exe -m scripts.medir_f009_t0 --solo M16
```

- Solo lecturas por `POST /api/sql/read`; credenciales del entorno o del `.env`, nunca impresas.
- Repite M16 y M16b (unos segundos) y añade M16c. Se mira en la CONCLUSIÓN: las líneas «M16c MA9999 /
  …», «M16c TOTAL …», «M16c Hipótesis M16c …», «M16c Naturalezas …» y «M16c Control …».
- Si sale «SIN MEDICIÓN», se repite `--solo M16`. No relanzar justo después de un corte (observación a
  de la revisión de T0a-bis).
- El fichero `%TEMP%\f009_t0_<fecha>.txt` lleva datos de negocio (códigos y resúmenes de naturalezas,
  muestra de M16b): **se pega entero** en la conversación y **no se versiona**.

## Qué queda fuera y qué falta

- Fuera: ejecutar el script (humano); volcar el resultado en la spec (spec-author); retirar script y
  test antes de T1 (N3); el timeout de `sql/read` (observación a de T0a-bis).
- MANUAL pendiente: la ejecución de `--solo M16` por el humano.
- Límite conocido: «cueide» compara el código de la cuenta con `cuacomcod` sin filtrar por empresa, como
  `cuenta_es_cuacomcod` de M16b. Si la regla sale escribible, la consulta de F-009 que la aplique tendrá
  que fijar la empresa al buscar la `cua` por código (lo decide el spec-author con el dato).

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests de la prueba de humo | 402 pasan (antes 374), 2,19 s |
| Suite completa | 2135 passed, 1 skipped, 94,18 s |
| Cobertura de líneas cambiadas | 98,4 % (817/830), `PUERTA COBERTURA` de init.sh |
| Mutación | No aplica: script de mediciones desechable que se retira antes de T1 (N3, decisión del humano); no se lanzó campaña |
| ruff en los dos ficheros | sin avisos (también `--preview --select E2,W,E7,F`) |
