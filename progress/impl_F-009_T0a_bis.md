<!-- progress/impl_F-009_T0a_bis.md -->
# Informe del implementer · F-009 T0a-bis (segunda pasada del script de T0)

Fecha: 2026-10-05. Rama `feature/F-009-alta-albaran-compra`. F-009 sigue en `spec_ready`; T0 está
autorizada por el humano. **No se ha llamado a la API, ni a Azure, ni al SQL Server**: el script lo
lanza el humano. Origen: la ejecución del 2026-10-05 (`%TEMP%\f009_t0_20261005_132453.txt`).
Commits: `00179a2`, `0037c72` (QA9999) y el del ciclo 1 de revisión.

## Qué cambió

| Fichero | Cambio |
|---|---|
| `scripts/medir_f009_t0.py` | M9 y M11 por ventanas cortas y cada sentencia protegida; M14b, M16b y M17b nuevas; reintento ante el 1205; M11 también para QA9999; ciclo 1 (ver abajo) |
| `tests/test_f009_t0_script.py` | 276 → 374 tests, sin red ni BBDD |

No se han tocado la spec, `progress/spec_F-009.md`, `progress/current.md`, `harness/features.json`,
`BACKLOG.md`, `infrastructure/`, `.env` ni el fichero sin trackear de la raíz. Sentencias: 67 → 76,
todas `SELECT` de una sentencia con `?` para los valores de fuera, aceptadas por el `SqlQueryGuard`
real y sin el patrón del error 130 (los tests de humo lo comprueban sobre las 76).

### Resumen de la primera entrega

1. **M9 y M11 sin cortes** (230 s del balanceador): ventanas cerradas como `?` (`VENTANA_M9`
   2026-09; `VENTANA_M11` 2026-07..09); se entra por `con` (`tip`, `fec`), `dcapro` por `docide` y
   `mov` por su índice `doclin` (`docide`, `linide`); fuera los `IN (SELECT …)`; líneas contadas con
   `COUNT(DISTINCT)`. Cada sentencia envuelta (`_leer_tabla` → `_leer_o_anotar`): un fallo se anota y
   el bloque sigue. `M9_por_banderas` (`pro.tipmov`, `pro.tipinv`, `auxfam.tipinv`) y `M9_genericos`
   (por código y empresa); `lectura_m9`: un campo **DECIDE** si con 1 hay mov en ≥ 95 % y con otro
   valor en ≤ 5 % (`UMBRAL_CASI_NINGUNA`); por genérico, «SÍ / NO genera mov», «a veces», «sin líneas».
2. **M16b** (origen de `dcapro.caaide` en las sin vincular desde 2025, por MA9999/QA9999/SM9999/SB9999
   de la empresa 1 y «resto», × con/sin partida): `M16b_fuentes` (campos: 0, `pro.gaside`,
   `cen.gaside`, `dca.caaide`, `ctr.caaide`, `obrparpar.caaide`, caa del centro), `M16b_codigos`
   (códigos vía `con.cod`: `auxpronat.caagascod/caaexicod/cuafaccod`, cuenta financiera, obra, centro
   y sus combinaciones con el centro, pista del director de Administración) y `M16b_muestra` (TOP 20
   con caa, naturaleza, obra, centro y cuenta). `obr` no ofrece una analítica de gasto candidata.
3. **M17b**: `log` no guarda el `ide` del registro; `M17b_reutiliza` clasifica cada `ope 2` en
   `no_existe` / `existe_con_alta_posterior` (cod reutilizado) / `existe_sin_alta_posterior`;
   `lectura_m17b` ⇒ BORRA / MARCA / no concluyente. `M17b_perfil` y `M17b_res` + `lectura_ope`.
4. **M14b**: `pagide`/`efeide` del albarán anterior del mismo proveedor y empresa (`LAG … PARTITION BY
   c.emp, a.entide ORDER BY c.ide`) frente al maestro, sobre los mismos albaranes.
5. **Reintento 1205** en el cliente: hasta 2 veces (5 s, 10 s), solo `(1205)`/`40001`. `M14_prv` y
   `M14_prepma` ya no se llevan la comparación con el albarán de la API.
6. **QA9999** (spec v6, lista blanca): M11 recorre `LISTA_BLANCA_GENERICOS` = (MA9999, QA9999) de cada
   empresa y etiqueta cada conclusión con su código; M9 ya separaba por código y empresa.

Desviaciones de la primera entrega: reintento en el cliente (vale para toda sentencia; CONVENTIONS pide
backoff); `M11_total_producto` también por ventana (dejaba de usar `dcapro` sin índice por `proide`);
M14b no separa los albaranes de la API (un puñado frente a ~2.600); sin `WITH (NOLOCK)` (propuesta
para el líder si M9/M11 vuelven a cortarse).

## Ciclo 1 de revisión (`progress/review_F-009_T0a_bis.md`, CHANGES_REQUESTED)

| Punto | Cambio |
|---|---|
| 1 Byte | `_TIPMOV`/`_TIPINV` = `COALESCE(CAST(r.tipmov AS int), -1)` (y `tipinv`); también `auxfam.tipinv` por uniformidad. Test que recorre las 76 sentencias y rechaza `ISNULL(<alias>.tipmov/tipinv` |
| 2 Fallo ≠ vacío | `_leer_tabla` devuelve `None` si falla (`[]` = cero filas). Helper `sin_medicion(nombre, clave)` ⇒ «`<sentencia>` SIN MEDICIÓN (falló la lectura; repetir con --solo Mn)». Lo distinguen `lectura_m9`, `lectura_m16` (analítica y R15 por separado), `lectura_m16b` (si cae una de las dos, sus candidatas no compiten y se dice), `lectura_muestra_m16b`, `lectura_m17` (`M17_existe`, `M17_marcas`, `M2_conest`), `lectura_m17b` (`[]` ⇒ «sin ope 2 en la ventana»), `lectura_ope` y `lectura_l8b` (`M11_iva_y_isp` caído ⇒ el motivo ISP «no se evaluó», nunca «inocua»); M11 no concluye `ivacuo` si cae `M11_iva_usado`. `lectura_m9` recorta `cod` (`strip().upper()`) |
| 3 Identificativas | `FUENTES_M16B` se parte en `IDENTIFICATIVAS_M16B` (fijan UNA caa: compiten por «domina» y «⇒ REGLA») y `PROPIEDADES_M16B` (caa del centro, centro y cuenta, empieza por cuenta, contiene obra, contiene centro: línea informativa «propiedades (no fijan la caa)»). Se nombra siempre la mejor identificativa («ninguna identificativa domina (la mejor: …)») y las empatadas («empata con: …») |
| 4 Naturaleza de la línea | `LEFT JOIN auxpronat nl ON nl.ide = d.natide` además de `nt` (producto). Nuevas: `lin_caa_cod_caagascod`, `lin_caa_cod_caaexicod`, `lin_centro_y_caagascod`, `lin_centro_y_caaexicod` y, por simetría, `centro_y_caaexicod` (producto); informativa `nat_linea_igual_producto`. La muestra añade `caagascod_linea` |
| obs. b | `M9_genericos` con `VENTANA_M11` (tres meses): QA9999 con líneas suficientes para H20 |
| obs. d | `M16b_dcaproana` (informativa, envuelta): líneas sin vincular con filas en `dcaproana`, con caa distinta de `dcapro.caaide` y con varias filas. El reparto se agrega antes por `docproide` en tabla derivada (sin error 130); `dcaproana` no tiene índice por `docproide` en el diccionario: un recorrido agrupado, como el `dcapropar` de M7 (0,5 s) |
| obs. e | `lectura_ope` compara sin tildes (`unicodedata`): «Envío» casa con `envi` |

Tests corregidos que fijaban el comportamiento erróneo: `lectura_m9([], [])` (ahora «sin líneas»,
nunca SIN MEDICIÓN), `lectura_m16b_dice_que_fuente_domina` (domina «caa del centro con código =
caagascod de la naturaleza del producto» 960/1000 ⇒ REGLA; «caa del centro» 980 va en propiedades),
`lectura_m16b_sin_dominante_y_desempate` y `lectura_m17b(...[])` (ahora «sin ope 2»); `m9_pasa_la_
ventana_y_los_genericos` espera `VENTANA_M11` en `M9_genericos`.

Orden de desempate entre identificativas: las de la naturaleza **de la línea** antes que las del
producto (F-009 escribe `dcapro.natide`); si empatan, la lectura nombra ambas.

## Fase RED (comandos exactos, salidas reales)

Primera entrega, tests nuevos antes del código:

```
$ .venv/Scripts/python.exe -m pytest tests/test_f009_t0_script.py -q -p no:cacheprovider -k "t0a_bis"
FAILED tests/test_f009_t0_script.py::test_f009_t0a_bis_existen_las_sentencias_nuevas
FAILED ...::test_f009_t0a_bis_las_sentencias_nuevas_van_parametrizadas_o_sin_valores_de_fuera[M9_genericos]  (y las 7 restantes)
FAILED ...::test_f009_t0a_bis_m9_va_por_ventana_corta_sin_subconsultas_in[M9_por_tipsininv]  (y las otras 4 de M9)
FAILED ...::test_f009_t0a_bis_m11_va_por_ventana_corta[M11_total_producto]  (y las otras 5 de M11)
FAILED ...::test_f009_t0a_bis_m11_pasa_la_ventana_y_el_ide_de_cada_ma9999
FAILED ...::test_f009_t0a_bis_m9_pasa_la_ventana_y_los_genericos
FAILED ...::test_f009_t0a_bis_m9_un_fallo_no_pierde_el_bloque[M9_por_tipsininv]  (×5)
FAILED ...::test_f009_t0a_bis_m11_un_fallo_no_pierde_el_bloque[M11_productos]  (y 3 más)
FAILED ...::test_f009_t0a_bis_m16_un_fallo_no_pierde_el_bloque[M16_caa_con_partida]  (y 3 más)
FAILED ...::test_f009_t0a_bis_m17_un_fallo_no_pierde_el_bloque[M17_ope]  (y 3 más)
FAILED ...::test_f009_t0a_bis_m14_un_fallo_no_pierde_la_comparacion[M14_prepma]  (y 2 más)
FAILED ...::test_f009_t0a_bis_lectura_m9_tipmov_decide_y_genericos   (y las 7 de lecturas m9/m16b/muestra/m17b/ope/m14b)
FAILED ...::test_f009_t0a_bis_el_cliente_reintenta_ante_el_interbloqueo_1205
FAILED ...::test_f009_t0a_bis_el_cliente_se_rinde_tras_los_reintentos_y_no_reintenta_otros_errores
FAILED ...::test_f009_t0a_bis_main_con_la_lista_de_la_segunda_pasada
53 failed, 1 passed, 276 deselected in 7.16s
```

(«(y …)» agrupa casos que la salida listaba uno a uno; el que pasó, `m11_un_fallo…[M11_acierto]`,
ya estaba protegido desde T0a.) Tras el código: `354 passed`. RED de QA9999:

```
$ .venv/Scripts/python.exe -m pytest tests/test_f009_t0_script.py -q -p no:cacheprovider -k "qa9999"
E           AssertionError: M11_total_producto
E           assert [1] == [1, 5]
FAILED tests/test_f009_t0_script.py::test_f009_t0a_bis_m11_mide_y_concluye_qa9999_aparte_de_ma9999
1 failed, 354 deselected in 0.39s
```

Ciclo 1, tests nuevos y corregidos antes del código (fichero entero):

```
$ .venv/Scripts/python.exe -m pytest tests/test_f009_t0_script.py -q -p no:cacheprovider
FAILED tests/test_f009_t0_script.py::test_f009_t0a_bis_m9_pasa_la_ventana_y_los_genericos
FAILED tests/test_f009_t0_script.py::test_f009_t0a_bis_lectura_m16b_dice_que_fuente_domina
FAILED tests/test_f009_t0_script.py::test_f009_t0a_bis_lectura_m16b_sin_dominante_y_desempate
FAILED ...::test_f009_t0a_bis_c1_las_propiedades_no_compiten_por_la_regla[caa_del_centro]  (y las otras 4 propiedades)
FAILED tests/test_f009_t0_script.py::test_f009_t0a_bis_c1_m16b_mide_tambien_la_naturaleza_de_la_linea
FAILED tests/test_f009_t0_script.py::test_f009_t0a_bis_c1_tipmov_y_tipinv_son_byte_sin_isnull_con_literal
FAILED tests/test_f009_t0_script.py::test_f009_t0a_bis_c1_lecturas_distinguen_no_se_pudo_leer_de_cero_filas
FAILED ...::test_f009_t0a_bis_c1_un_fallo_no_se_lee_como_dato_vacio[m9-M9_genericos-sin líneas en la ventana-…]
FAILED ...::test_f009_t0a_bis_c1_un_fallo_no_se_lee_como_dato_vacio[m9-M9_por_banderas-lo explican solos-…]
FAILED ...::test_f009_t0a_bis_c1_un_fallo_no_se_lee_como_dato_vacio[m16-M16b_fuentes-No hay líneas sin vincular-…]
FAILED ...::test_f009_t0a_bis_c1_un_fallo_no_se_lee_como_dato_vacio[m17-M17b_reutiliza-Lectura automática M17b: no concluyente-…]
FAILED ...::test_f009_t0a_bis_c1_un_fallo_no_se_lee_como_dato_vacio[m11-M11_iva_y_isp-L8b inocua (aciertan igual o menos): se queda.-…]
FAILED tests/test_f009_t0_script.py::test_f009_t0a_bis_c1_lectura_m9_compara_el_codigo_sin_espacios
FAILED tests/test_f009_t0_script.py::test_f009_t0a_bis_c1_dcaproana_informativa_y_envuelta
FAILED tests/test_f009_t0_script.py::test_f009_t0a_bis_c1_ope_envio_con_tilde
FAILED tests/test_f009_t0_script.py::test_f009_t0a_bis_lectura_muestra_m16b_ve_el_patron_del_codigo
FAILED tests/test_f009_t0_script.py::test_f009_t0a_bis_lectura_m17b_borra_marca_o_no_concluyente
21 failed, 350 passed, 1 warning in 3.87s
```

Tras el código, 3 fallos reales: dos tests de T0a-bis contaban una sola vez «no se pudo leer» y el texto
de SIN MEDICIÓN lo repetía (se cambió la redacción a «falló la lectura»), y el test del patrón Byte
detectó `ISNULL(f.tipinv, -1)` de `auxfam` (se pasó a `COALESCE(CAST(… AS int), -1)`). Final:
`374 passed, 1 warning in 2.07s`.

## Salida real de `bash harness/init.sh` (tras el ciclo 1)

```
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 80 avisos (deuda previa, no bloquea).   (los dos ficheros tocados: «All checks passed!»)
2107 passed, 1 skipped, 1 warning in 101.50s (0:01:41)
[OK] pytest en verde (con medición de cobertura)
[OK] PUERTA COBERTURA: 98.3% de 780 líneas cambiadas cubiertas (767/780, umbral 80%, nivel critico)
[OK] PUERTA TAMAÑO: F-009 dentro de los topes (requirements 150/150, design 250/250)
[OK] Rama actual: feature/F-009-alta-albaran-compra
ENTORNO LISTO. Puedes trabajar.
```

## Comando para el humano (PowerShell 5.1)

```powershell
Set-Location C:\Users\pgris\PycharmProjects\sigrid-api
git switch feature/F-009-alta-albaran-compra
& .\.venv\Scripts\python.exe -m scripts.medir_f009_t0 --solo M9 M11 M14 M16 M17
```

- Solo lecturas por `POST /api/sql/read`; credenciales del entorno o del `.env`, nunca impresas.
- Una sentencia que falle se anota («no se pudo leer») y su lectura sale «SIN MEDICIÓN»: se repite ese
  bloque con `--solo Mn`. Un interbloqueo se reintenta solo. No relanzar justo después de un corte
  (observación a de la revisión: la consulta cortada puede seguir viva en el servidor).
- Al final indica `%TEMP%\f009_t0_<fecha>.txt`: **se pega entero**. Lleva datos de negocio (códigos de
  la muestra de M16b, resúmenes de `log.res`): no se versiona.

## Qué queda fuera y qué falta

- Fuera: ejecutar el script (humano); volcar resultados en la spec (spec-author); retirar script y
  test antes de T1 (N3); el timeout de `sql/read` (observación a, feature aparte en `infrastructure/`);
  el margen de `lectura_m14b` (observación c) y `NOLOCK` (f), para el líder y el spec-author.
- Riesgo: diccionario de 2024 (una columna inexistente se anota, no tumba el bloque); las más pesadas
  son `M17b_reutiliza` (dos recorridos de la ventana de `log`), `M16b_codigos` (ahora dos `auxpronat`
  y cuatro `con`) y `M16b_dcaproana` (agrupa `dcaproana` entera).

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests de la prueba de humo | 374 pasan (antes 276), 2,07 s |
| Suite completa | 2107 passed, 1 skipped, 101,50 s |
| Cobertura de líneas cambiadas | 98,3 % (767/780), `PUERTA COBERTURA` de init.sh |
| Mutación | No aplica: script de mediciones desechable que se retira en T0c (N3, decisión del humano); no se lanzó campaña |
| ruff en los dos ficheros | sin avisos (también `--preview --select E2,W,E7,F`) |
