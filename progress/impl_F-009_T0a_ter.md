<!-- progress/impl_F-009_T0a_ter.md -->
# Informe del implementer · F-009 T0a-ter (M16c, M14c, XA9999 y numemp en el script de T0)

Fecha: 2026-10-05. Rama `feature/F-009-alta-albaran-compra`. F-009 sigue en `spec_ready`; T0 está
autorizada por el humano. **No se ha llamado a la API, ni a Azure, ni al SQL Server**: el script lo lanza
el humano. Origen: el bloque M16 de `%TEMP%\f009_t0_20261005_163206.txt` y `progress/spec_F-009.md` §v7.
Tres commits: `38d3571` (M16c), `ade7b47` (ciclo 1 de revisión) y el de la ampliación (M14c, XA9999, P2).

## Qué cambió

| Fichero | Cambio |
|---|---|
| `scripts/medir_f009_t0.py` | M16c (subbloque de M16), ciclo 1, M14c (parte de M14), XA9999 en los genéricos, `M16c_numemp` |
| `tests/test_f009_t0_script.py` | 374 → 426 tests, sin red ni BBDD |

No se han tocado la spec ni el contrato, `progress/spec_F-009.md`, `progress/current.md`,
`harness/features.json`, `BACKLOG.md`, `infrastructure/`, `.env` ni el fichero sin trackear de la raíz.
`MEDICIONES` sigue siendo M1-M18 (un test lo fija): **M16c es subbloque de M16 y M14c parte de M14**.
M16c va antes de `M16b_dcaproana` (la más expuesta por volumen). Diccionario (`sigrid_tablas.md`): `caa`,
`cua`, `obr`, `cen` son «Propiedades de con» (código en `con.cod`); `caa.cenide`, `auxpronat.caagascod/
caaexicod/cuacomcod/numemp`, `ctrpro.natide/cenide/caaide/obride`, `mov.prepma/almpma/fechor`
(índice `pafhi` = producto, almacén, fechor) y `pro.prepma` existen.

## M16c (primera entrega) · regla del código de la caa

Universo de M16b: sin vincular desde 2025, por grupo (genéricos de la empresa 1 y «resto», con `?`) ×
con/sin partida. `_regla_caa(nat, codigo)`, con `gas = RTRIM(LTRIM(<nat>.caagascod))`:

```
k.cenide = d.cenide AND CHARINDEX('.', gas) > 0
AND RTRIM(LTRIM(kc.cod)) = RTRIM(LTRIM(<obra|centro>.cod)) + '.' + SUBSTRING(gas, CHARINDEX('.', gas) + 1, 24)
AND u.cod IS NULL      -- u = (cenide, código) repetidos entre las caa: ahí la regla no fija UNA caa
```

| Sentencia | Qué devuelve |
|---|---|
| `M16c_reglas` | `regla_linea/producto_obra/centro`, `cueide_linea/producto` y avisos (sin `MOD.`, sin `.`, sin naturaleza, `caaexicod`, caa repetida, obra = centro) |
| `M16c_naturalezas_ma` | TOP 15 naturalezas de la línea en el MA9999 de la empresa 1 con sus aciertos |
| `M16c_vinculadas` | control: la regla sobre `ctrpro` por clave primaria (`t.ide = d.linoriide`), líneas de contrato distintas |

Lecturas con `UMBRAL_REGLA_ESCRIBIBLE = 0.95`: por grupo y TOTAL, «⇒ REGLA escribible «…»» o «sin regla
escribible (la mejor: …)», desempate línea > producto y obra > centro con empates nombrados; «Hipótesis
M16c … CONFIRMADA / NO confirmada» (la de la línea ≥ 95 % y no menor que la del producto). `None` ⇒
«`<sentencia>` SIN MEDICIÓN»; `[]` ⇒ «cero filas» (la de `M16c_reglas` nombra la sentencia: con «No hay
líneas sin vincular…» chocaba con un test de T0a-bis).

## Ciclo 1 de revisión (`progress/review_F-009_T0a_ter.md`, CHANGES_REQUESTED) · `ade7b47`

| Punto | Cambio |
|---|---|
| 1 Cuenta identificativa (P3) | `cueide_linea/producto` exigen `cf.emp = c.emp` y `w.cod IS NULL`, con `w` = (`emp`, código) repetidos entre las `cua` (`dbo.cua` ⨝ `dbo.con`, `HAVING COUNT(*) > 1`). Avisos `cua_repetida` y `cua_de_otra_empresa` (no pedida: explica el fallo si las `cua` se comparten); cierre «La de la cuenta exige …». Sin `?` nuevos |
| obs. a | `M16c_naturalezas_ma` trae `regla_linea_centro`; la lectura usa la mejor de obra y centro |
| obs. b, c | `caa_informada` en `M16c_reglas`; el control de vinculadas mide sobre las líneas de contrato **con** caaide y, si no hay, «no sirve de control (sin contraejemplos)» |

## Ampliación del líder (aprobada por el humano; T0b-ter = `--solo M9 M14 M16`)

1. **M14c (P1)**, parte nueva de M14, ventana `VENTANA_M9` (un mes, `?`) y `mov` por `doclin` como M9:
   - `M14c_mov_prepma`: por cada `mov` de albarán (`m.doctip = 14`), el `almpma` del `mov` **anterior** del
     mismo producto y almacén (`OUTER APPLY (SELECT TOP 1 … ORDER BY p.fechor DESC, p.ide DESC)`, por el
     índice `pafhi`; anterior = `fechor` menor, o igual con `ide` menor). Banderas: `igual_anterior` (a),
     `igual_resultante` (b, `m.almpma`), `igual_pro_prepma`, `anterior_igual_resultante` (no
     discriminan), `sin_anterior`, `prepma_cero`, `linea_igual_mov`. Tolerancia `0.0001` (la de
     `M14_prepma`). El APPLY es una tabla (TOP 1), no una subconsulta escalar, y va dentro de la derivada:
     fuera solo se suman banderas (no es el patrón del error 130, y el detector lo confirma).
   - `M14c_sin_mov`: líneas sin `mov` de la ventana por `tipmov` (`COALESCE(CAST … AS int), -1)`):
     `dcapro.prepma` = 0, = `pro.prepma` (≠ 0) y `pro.prepma` = 0.
   - `lectura_m14c` (`UMBRAL_REGLA_PREPMA = 0.95`): «PMP vigente ANTES de la entrada (hipótesis a)»
     (sobre los `mov` con anterior), «PMP RESULTANTE», «pro.prepma ⇒ PARADA (R25)», «no discrimina» si a
     y b llegan a la vez, o «no concluyente»; para la línea sin `mov`, «lleva prepma 0» / «lleva
     pro.prepma» / «no concluyente».
2. **XA9999 (P5)**: `PRODUCTOS_GENERICOS` + `XA9999`; `LISTA_BLANCA_GENERICOS = ("MA9999", "QA9999",
   "XA9999")`. M9 (`mov`, `tipmov`), M11 (IVA, L8b) y M16b/M16c lo miden y concluyen aparte; los `?` de
   las listas IN salen de la tupla (5 genéricos), los tests lo comprueban.
3. **P2 (`M16c_numemp`)**, informativa: líneas sin vincular desde 2025 de la empresa `?` (1) por clase de
   `auxpronat.numemp` de la naturaleza de la línea (`igual_empresa` = `c.emp`, `cero`, `otra_empresa`,
   `sin_naturaleza`), con naturalezas distintas y `numemp` = empresa de la obra. Lectura: «numemp =
   empresa: la validación por numemp es viable» / «numemp en {0, empresa}» / «la validación pasa a
   «existe y sin baja»».

Riesgo de tiempo: bajo. `M14c_mov_prepma` hace un TOP 1 por índice por cada `mov` del mes (~8.300 el
2026-09 según `M14_prepma`); `M14c_sin_mov` es el camino de `M9_sin_mov_por_producto`; `M16c_numemp`, el
de M16b sin `pro`. Todas envueltas (`_leer_tabla`): una que falle se anota y el bloque sigue.

Ajuste de test: `..._un_fallo_de_m16c_no_pierde_el_bloque...` usa ahora los datos con `M16c_numemp`; con
la fixture anterior esa sentencia nueva devolvía cero filas legítimas y su texto contenía «cero filas».

## Fase RED (comandos exactos, salidas reales)

Primera entrega (`-k "t0a_ter"`), tests antes que el código:

```
$ .venv/Scripts/python.exe -m pytest tests/test_f009_t0_script.py -q -p no:cacheprovider -k "t0a_ter"
FAILED ...::test_f009_t0a_ter_existen_las_sentencias_de_m16c
FAILED ...::test_f009_t0a_ter_m16c_va_parametrizada_y_sin_isnull_con_literal_negativo[M16c_reglas]  (y las otras 2)
FAILED ...::test_f009_t0a_ter_m16c_construye_el_codigo_con_la_naturaleza_de_la_linea_y_la_del_producto
FAILED ...::test_f009_t0a_ter_m16c_la_regla_exige_que_centro_y_codigo_identifiquen_una_sola_caa
FAILED ...::test_f009_t0a_ter_m16c_vinculadas_usa_la_linea_del_contrato
FAILED ...::test_f009_t0a_ter_m16_pasa_los_grupos_y_el_generico_de_las_naturalezas
FAILED ...::test_f009_t0a_ter_lectura_m16c_regla_escribible_y_manda_la_linea
FAILED ...::test_f009_t0a_ter_lectura_m16c_en_el_limite_del_umbral[95-True]  (y [94-False])
FAILED ...::test_f009_t0a_ter_lectura_m16c_manda_el_producto_si_acierta_mas
FAILED ...::test_f009_t0a_ter_lecturas_m16c_distinguen_sin_medicion_de_cero_filas
FAILED ...::test_f009_t0a_ter_lectura_de_las_naturalezas_de_ma9999
FAILED ...::test_f009_t0a_ter_lectura_del_control_con_las_vinculadas
FAILED ...::test_f009_t0a_ter_un_fallo_de_m16c_no_pierde_el_bloque_ni_se_lee_como_vacio[M16c_reglas]  (y las otras 2)
FAILED ...::test_f009_t0a_ter_main_solo_m16_con_m16c
19 failed, 374 deselected in 2.24s
E  KeyError: 'M16c_reglas' · AttributeError: ... no attribute 'UMBRAL_REGLA_ESCRIBIBLE' · ... 'lectura_m16c' (×4)
```

(«(y …)» agrupa casos que la salida listaba uno a uno.) Tras el código: `402 passed`.

Ciclo 1 (`-k "t0a_ter_c1"`):

```
E   assert "cf.emp = c.emp AND ISNULL(nl.cuacomcod, '') <> '' AND RTRIM(LTRIM(cf.cod)) = RTRIM(LTRIM(nl.cuacomcod)) AND w.cod IS NULL" in 'SELECT x.grupo, ...
E   AssertionError: assert ('AS regla_linea_centro,' in 'SELECT TOP 15 nl.cod AS nat_cod, ...
E   AssertionError: assert 'caaide informado 50 de 100 (50.0 %)' in 'Control con las vinculadas (100 líneas de contrato): ctrpro.caaide = ... 49 de 100 (49.0 %); ...
FAILED tests/test_f009_t0_script.py::test_f009_t0a_ter_c1_la_cuenta_exige_la_empresa_del_albaran_y_un_solo_codigo
FAILED tests/test_f009_t0_script.py::test_f009_t0a_ter_c1_naturalezas_miden_tambien_la_variante_centro
FAILED tests/test_f009_t0_script.py::test_f009_t0a_ter_c1_el_control_cuenta_solo_las_lineas_de_contrato_con_caa
3 failed, 402 deselected in 0.36s
```

Tras el código: `405 passed`. Ampliación (`-k "t0a_ter_amp"`):

```
$ .venv/Scripts/python.exe -m pytest tests/test_f009_t0_script.py -q -p no:cacheprovider -k "t0a_ter_amp"
FAILED ...::test_f009_t0a_ter_amp_sentencias_parametrizadas_sin_isnull_negativo[M14c_mov_prepma]  (y M14c_sin_mov, M16c_numemp)
FAILED ...::test_f009_t0a_ter_amp_xa9999_se_mide_y_concluye_como_ma9999_y_qa9999
FAILED ...::test_f009_t0a_ter_amp_m14c_compara_con_el_mov_anterior_por_indice
FAILED ...::test_f009_t0a_ter_amp_m14_pasa_la_ventana_de_un_mes_a_m14c
FAILED ...::test_f009_t0a_ter_amp_lectura_m14c_anterior_resultante_o_pro
FAILED ...::test_f009_t0a_ter_amp_lecturas_distinguen_sin_medicion_de_cero_filas
FAILED ...::test_f009_t0a_ter_amp_un_fallo_de_m14c_no_pierde_el_bloque[M14c_mov_prepma]  (y [M14c_sin_mov])
FAILED ...::test_f009_t0a_ter_amp_numemp_de_las_naturalezas_de_la_empresa_1
FAILED ...::test_f009_t0a_ter_amp_main_con_la_lista_de_t0b_ter
12 failed, 405 deselected in 3.63s
E  AssertionError: assert ('XA9999' in ('MA9999', 'SM9999', 'SB9999', 'QA9999'))
E  AttributeError: ... no attribute 'UMBRAL_REGLA_PREPMA' · ... 'lectura_m14c' · KeyError: 'M14c_mov_prepma' (×4)
E  KeyError: 'M14c_sin_mov' (×2) · KeyError: 'M16c_numemp' (×2) · AssertionError: (hipótesis a)
```

Tras el código: 3 fallos del ajuste de fixture de arriba; corregido, `426 passed, 1 warning in 2.61s`.
ruff limpio en los dos ficheros (por defecto y `--preview --select E2,W,E7,F`).

## Trazabilidad (encargo → test, prefijo `test_f009_t0a_ter_`)

| Punto | Test |
|---|---|
| Regla caa (composición, línea/producto × obra/centro, caa única) | `m16c_construye_el_codigo...`, `m16c_la_regla_exige_que_centro_y_codigo...` |
| Cuenta única por empresa (ciclo 1, P3) | `c1_la_cuenta_exige_la_empresa_del_albaran_y_un_solo_codigo` |
| Naturalezas MA9999 (con centro) y control vinculadas (con caaide) | `lectura_de_las_naturalezas...`, `c1_naturalezas_miden...`, `lectura_del_control...`, `c1_el_control_cuenta...` |
| Umbrales con nombre y límites | `lectura_m16c_en_el_limite_del_umbral[95/94]`, `amp_lectura_m14c_anterior_resultante_o_pro` (95 justo) |
| M14c: mov anterior por índice, ventana, sin mov | `amp_m14c_compara_con_el_mov_anterior_por_indice`, `amp_m14_pasa_la_ventana...` |
| XA9999 en M9, M11 y M16 | `amp_xa9999_se_mide_y_concluye_como_ma9999_y_qa9999` |
| numemp (P2) | `amp_numemp_de_las_naturalezas_de_la_empresa_1` |
| Sin medición ≠ cero filas; el bloque sigue | `lecturas_m16c_distinguen...`, `un_fallo_de_m16c...` (×3), `amp_lecturas_distinguen...`, `amp_un_fallo_de_m14c...` (×2) |
| `?`, sin literales, sin `ISNULL(…, -1)`, guardia real, error 130 | `m16c_va_parametrizada...` (×3), `amp_sentencias_parametrizadas...` (×3) y los parametrizados sobre todo `SQL` |
| `--solo M16` y `--solo M9 M14 M16` | `main_solo_m16_con_m16c`, `amp_main_con_la_lista_de_t0b_ter` |

## Salida real de `bash harness/init.sh` (tras la ampliación)

```
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 80 avisos (deuda previa, no bloquea).   (los dos ficheros tocados: «All checks passed!»)
2159 passed, 1 skipped, 1 warning in 72.14s (0:01:12)
[OK] pytest en verde (con medición de cobertura)
[OK] PUERTA COBERTURA: 98.5% de 951 líneas cambiadas cubiertas (937/951, umbral 80%, nivel critico)
[OK] PUERTA TAMAÑO: F-009 dentro de los topes (requirements 150/150, design 250/250)
[OK] Rama actual: feature/F-009-alta-albaran-compra
ENTORNO LISTO. Puedes trabajar.
```

## Comando para el humano (PowerShell 5.1) · T0b-ter

```powershell
Set-Location C:\Users\pgris\PycharmProjects\sigrid-api
git switch feature/F-009-alta-albaran-compra
& .\.venv\Scripts\python.exe -m scripts.medir_f009_t0 --solo M9 M14 M16
```

- Solo lecturas por `POST /api/sql/read`; credenciales del entorno o del `.env`, nunca impresas.
- Se mira en la CONCLUSIÓN: «XA9999 emp 1: …» (M9), «M14c mov.prepma …» y «M14c línea sin mov …» (M14),
  «M16c … / TOTAL / Hipótesis / Naturalezas / Control / numemp …» (M16), y XA9999 en M16b/M16c.
- **El IVA y L8b de XA9999 son de M11**, que esa lista no lanza: para medirlos, añadir `M11`
  (`--solo M9 M11 M14 M16`; M11 va por ventana corta desde T0a-bis).
- Si sale «SIN MEDICIÓN», se repite ese bloque con `--solo Mn`; no relanzar justo tras un corte.
- El fichero `%TEMP%\f009_t0_<fecha>.txt` lleva datos de negocio: **se pega entero** y no se versiona.

## Qué queda fuera y qué falta

- Fuera: ejecutar el script (humano); volcar el resultado en la spec (spec-author); retirar script y
  test antes de T1 (N3); el timeout de `sql/read` (obs. a de T0a-bis).
- MANUAL pendiente: T0b-ter (`--solo M9 M14 M16`, o con M11 si se quiere el IVA de XA9999).
- `pro.prepma` es el valor de hoy, no el del momento del `mov`: un acierto bajo frente a él no descarta
  del todo la hipótesis (b) en productos que cambiaron después; la lectura solo la proclama si llega al 95 %.

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests de la prueba de humo | 426 pasan (antes 374), 2,61 s |
| Suite completa | 2159 passed, 1 skipped, 72,14 s |
| Cobertura de líneas cambiadas | 98,5 % (937/951), `PUERTA COBERTURA` de init.sh |
| Mutación | No aplica: script de mediciones desechable que se retira antes de T1 (N3, decisión del humano); no se lanzó campaña |
| ruff en los dos ficheros | sin avisos (también `--preview --select E2,W,E7,F`) |
