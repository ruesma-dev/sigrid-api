<!-- progress/impl_F-009_T0a_quater.md -->
# Informe del implementer · F-009 T0a-quater (M14d, M16d y M19 en el script de T0)

Fecha: 2026-10-06. Rama `feature/F-009-alta-albaran-compra`. F-009 sigue en `spec_ready`; T0 autorizada por el
humano («más mediciones si es necesario»). **No se ha llamado a la API, ni a Azure, ni al SQL Server**: el script
lo lanza el humano. Origen: `%TEMP%\f009_t0_20261006_005622.txt` (T0b-ter) y el diccionario
`azure-apps/sigrid_tablas.md` (`mov`, `dcapro`, `dnc`, `dncpro`, `ctrpro`, `pro`, `auxpronat`, `caa`, `log`, `usu`).

## Qué cambió

| Fichero | Cambio |
|---|---|
| `scripts/medir_f009_t0.py` | M14d (parte de M14), M16d (subbloque de M16, al final), **M19 nuevo** en `MEDICIONES` |
| `tests/test_f009_t0_script.py` | 426 → 630 tests, sin red ni BBDD; `MEDICIONES` = M1-M19 |

No se han tocado la spec, `progress/spec_F-009.md`, `progress/current.md`, `harness/features.json`,
`BACKLOG.md`, `infrastructure/`, `.env` ni el fichero sin trackear de la raíz. Constantes nuevas con nombre:
`DESDE_ALTAS_LOG = 20250901`, `GENERICO_XA`, `GENERICOS_EXCEPCIONES_M16D = (XA9999, MA9999)`,
`UMBRAL_PUREZA_M16D = 0.95`, `TOP_ELECCION_M16D = 300`, `UMBRAL_HEREDA_DNC = 0.95`, `MARCAS_USUARIO_TECNICO`.
Se reutilizan `UMBRAL_REGLA_PREPMA` (M14d) y `UMBRAL_REGLA_ESCRIBIBLE` (M16d, M19 cod2).

## M14d · `mov.prepma` mirado por PRODUCTO (duda 1)

Diccionario: `mov.prepma` = «Precio Medio Compra»; `almpma` = «Almacén Precio Medio Compra»; `pro` no tiene
stock global (solo `proalm.canact`, el de hoy). Ventana `VENTANA_M9` (un mes, `?`), `mov` por `doclin`, `m.doctip = 14`.

- `M14d_prepma_producto`: por cada `mov` de albarán, `OUTER APPLY TOP 1` del `mov` **anterior** y del **siguiente**
  del mismo `proide` en **cualquier almacén**, por el índice `pfhi` (producto, fechor), con el desempate ya escrito
  como rango (`p.fechor <= m.fechor AND (p.fechor < m.fechor OR p.ide < m.ide)`, obs. d de T0a-ter). Banderas:
  `igual_anterior_producto`, `igual_siguiente_producto`, `igual_pre`, `igual_prc`, `igual_dcapro_pre`, y
  propiedades `entre_anterior_y_pre` (compatible con media ponderada), `anterior_igual_pre`,
  `anterior_igual_siguiente`, `anterior_es_albaran`. **Agrupada por la clase del `mov` siguiente**
  (`otro_documento` / `albaran_compra` / `sin_siguiente`).
- `M14d_muestra`: los 15 `mov` de albarán más recientes (solo va a `%TEMP%`). `lectura_m14d`: la mejor candidata (desempate por orden) «⇒ mov.prepma = …» si llega a `UMBRAL_REGLA_PREPMA`;
  si no, «no concluyente (la mejor: …)». Línea de **arrastre**: si el `mov` siguiente que NO es compra repite el
  prepma (≥ 95 %) ⇒ «precio medio de compra del PRODUCTO que solo cambia con las compras (el resultante)».
  El **PMP global resultante no es calculable barato** (no hay stock global por `mov`): lo sustituye el siguiente.

## M16d · XA9999, excepciones de MA9999 y MA99 frente a MA1501 (duda 2)

- `M16d_maestro` (`?` empresa, código): `con.res`, naturaleza de la ficha (`cod`, `res`, `caagascod`,
  `cuacomcod`, `caaexicod`, `cuafaccod`). Lectura: «caagascod sin '.': la regla de M16c no se puede aplicar».
- `M16d_excepciones` (TOP 20 de `caa.cod`, naturaleza de la línea, `caagascod`, obra, con/sin partida, líneas) y
  `M16d_sufijos` (**añadida**: lo mismo sin la obra, agrupado por el sufijo de la caa tras el primer '.', con nº
  de obras y cuántas caa empiezan por `<obra>.`). Solo las líneas que **no** cumplen M16c (obra o centro),
  `CASE … END = 0`. Se lanzan dos veces: **XA9999** (todas fallan) y **MA9999**. Lecturas: % de caa que empiezan por
  `<obra>.`, = `<obra>.<caagascod entero>`, = `<obra>.<código de la naturaleza>`; sufijo = caagascod entero / =
  código de la naturaleza / = caagascod tras el '.'.
- `M16d_candidatas` (grupos de M16b, 6 `?`): `regla_actual` (M16c), `caagascod_entero`, `obra_natcod`,
  **`regla_ampliada`** (M16c, o `<obra>.<caagascod entero>` si la naturaleza no tiene '.') y «la cuenta de la
  línea anterior»: `LAG(caaide)` sobre las sin vincular por (obra, naturaleza de la línea) y por (obra,
  producto), con `sin_anterior_*` aparte. Todas fijan UNA caa (las de código exigen `k.cenide = d.cenide` y
  `u.cod IS NULL`). Lectura por grupo × partida y TOTAL con `_veredicto_m16c` (desempate por orden, empates
  nombrados) + acierto condicionado de las «anterior»; «Hipótesis M16d … CONFIRMADA / NO confirmada».
- `M16d_por_obra` / `_por_proveedor` (por `dca.entide`, sin nombres) / `_por_usuario` (alta en `log`): TOP 300,
  la tabla enseña 15; columnas `nat_producto` (la de la ficha, MA1501), `otra_nat`, `naturalezas`,
  `cumple_regla`. `lectura_m16d_eleccion`: «pureza» = líneas que siguen la naturaleza mayoritaria de su ítem;
  «la fija la obra / el proveedor / el usuario del alta» si ≥ `UMBRAL_PUREZA_M16D`, si no «mixta», con aviso de
  que muchos ítems pequeños suben la pureza por azar.

## M19 (nuevo) · planificación de compras y `cod2`; altas por usuario (dudas 3 y 4)

- `M19_dnc` (grupos, 6 `?`): sin vincular desde 2025 con `dncproide > 0` frente a su `dncpro`: cod2 igual / ambos
  vacíos, caaide, producto, natide (= la de `dncpro` y = la del producto de `dncpro`), partida, `dncide`, obra del
  `dnc`, centro. Lectura por grupo y TOTAL; «se heredan (≥ 95 %): …; no se heredan: …».
- `M19_cod2_origen` (sin `?`, **la última de M19** desde el ciclo 1), por `con_dnc`/`sin_dnc`, solo líneas con
  cod2. Fijan UN valor (compiten): planificación de la misma obra y producto y línea del contrato con el mismo
  producto, **si su clave tiene un único cod2**; línea anterior del mismo proveedor y de la misma obra y producto
  (`LAG`); código de la partida y del producto. Propiedades (no compiten): existe en alguna planificación de la obra
  / línea del contrato, claves con varios cod2, repetido en el albarán, albarán con contrato.
- `M19_cod2_valores` (TOP 10 cod2 con nº de obras, productos y proveedores; sin nombres) y `M19_vinculadas`
  (cod2, `dncide` y `dncproide` de la línea frente a su `ctrpro` por clave primaria: H35 del contrato v7.1).
- `M19_altas_usuario` (5 `?`): líneas MA9999/QA9999/XA9999 desde `DESDE_ALTAS_LOG` por `log.usu` de la **última**
  ope 1 de su (emp, cod) en la ventana (`_ALTAS_LOG`; el cod se reutiliza tras borrar, M17b), y por producto.
  De `usu` solo el código y `tipdes` (`en_usu`, `desactivado`). `''` = **sin alta en log** (la API no escribe log).
  Lectura: TOP 10 usuarios, % sin alta, «posibles usuarios técnicos por su código» (heurística
  `MARCAS_USUARIO_TECNICO`: el diccionario no tiene esa marca) y usuarios del log que no están en `usu`.
- `M19_sin_alta` (TOP 10 albaranes recientes con esos genéricos y sin alta) y `M19_api` (productos de
  `AC26/15951`): «solo el albarán de prueba de la API» / «hay otros además del de prueba».

**Lecturas baratas añadidas**: `M16d_sufijos`, `obra_natcod` y `regla_ampliada` (composición de la caa de XA9999);
clase del `mov` siguiente y `entre_anterior_y_pre` (PMP de compra del producto frente a precio de la línea);
`M19_cod2_valores`, `es_cod_*`, `repetido_en_albaran`, `M19_sin_alta` y `M19_api`. Mismas tablas e índices que M16b-M17.

## Desviaciones (justificadas)

1. **Ventana de usuarios desde 2025-09-01**, no desde 2025: la ventana de `log` (`_VENTANA_LOG`, 1.000.000 `ide`)
   arranca el 2025-08-20 (M17 del 2026-10-05); antes de ella todo saldría «sin alta». El encargo lo permite.
2. **MA99 frente a MA1501 por la naturaleza de la ficha frente a «otra»**, no por literal: sin literales en el SQL;
   T0b-ter dice que esas dos son el 100 % de las líneas MA9999 (23.217 + 22.375 = 45.592), así que es equivalente.
3. **Las tres dimensiones de M16d en la misma ventana** (desde 2025-09-01) para que la pureza sea comparable.

## Riesgo de tiempo (balanceador 230 s; `sql/read` no corta la consulta en el servidor)

Todo envuelto (`_leer_tabla`; M14d además en el `try` de `m14`). Referencias de T0b-ter: M14c 0,5 s (patrón de
M14d), M16c_reglas 9,8 s (universo de `M16d_candidatas`, + dos `LAG`), M16c_naturalezas_ma 2,9 s, M17 1-2 s. Lo
más pesado, `M16d_candidatas` y `M19_cod2_origen`, va al final de su bloque. Estimación: decenas de segundos.

## Fase RED (comando exacto, salida real)

Tests escritos antes que el código (más el ajuste de `test_f009_t0_hay_una_medicion_por_cada_m_de_la_spec` a
M1-M19):

```
$ .venv/Scripts/python.exe -m pytest tests/test_f009_t0_script.py -q -p no:cacheprovider -k "t0a_quater or medicion_por_cada"
__main__.py: error: medición desconocida: M19 (válidas: M1, M2, ..., M17, M18)
FAILED tests/test_f009_t0_script.py::test_f009_t0_hay_una_medicion_por_cada_m_de_la_spec
FAILED tests/test_f009_t0_script.py::test_f009_t0a_quater_existen_las_sentencias_nuevas
FAILED ...::test_f009_t0a_quater_sentencias_parametrizadas_sin_literales_ni_isnull_negativo[M14d_prepma_producto]  (y las otras 15)
FAILED ...::test_f009_t0a_quater_lectura_m14d_arrastre_y_candidatas  (y el resto de m14d, m16d y m19: 20 tests)
FAILED ...::test_f009_t0a_quater_un_fallo_no_pierde_el_bloque[m14-M14d_prepma_producto]  (y las otras 15)
FAILED ...::test_f009_t0a_quater_main_con_la_lista_de_t0b_quater
57 failed, 84 passed, 425 deselected in 11.63s
```

Errores: `AttributeError: … no attribute 'm19'` (×9), `… 'lectura_m14d'` (×4), `KeyError: 'M14d_prepma_producto'`
(×4) y demás `KeyError` de las sentencias nuevas, `SystemExit: 2` (`--solo … M19`). Tras el código: `630 passed`;
ruff marcó un ISC004 (envuelto entre paréntesis) y quedó limpio.

Ajuste de test: `test_f009_t0a_ter_un_fallo_de_m16c_no_pierde_el_bloque…` usa ahora `_datos_quater()` (con datos de
M16d): con la fixture anterior, M16d devolvía cero filas legítimas y su texto contenía «cero filas».

## Trazabilidad (encargo → test, prefijo `test_f009_t0a_quater_`)

| Punto | Test |
|---|---|
| M14d: producto en cualquier almacén por `pfhi`, ventana, banderas | `m14d_va_por_el_producto…`, `m14_pasa_la_ventana…` |
| M14d: lectura, arrastre, umbral 95/94, sin medición ≠ cero filas | `lectura_m14d_arrastre…`, `…_en_el_limite_del_umbral`, `lectura_m14d_sin_medicion…` |
| M16d: XA9999, excepciones y sufijos (XA9999 y MA9999) | `m16d_sql_de_excepciones…`, `m16_pasa_xa9999_y_ma9999…`, `lecturas_m16d_maestro…` |
| M16d: candidatas y MA99/MA1501 por obra, proveedor y usuario | `lectura_m16d_candidatas`, `…_en_el_limite`, `m16d_eleccion_…`, `lectura_m16d_eleccion_…` |
| M19: dnc/dncpro, origen del cod2, vinculadas | `m19_sql`, `lectura_m19_dnc`, `lectura_m19_cod2_origen_y_vinculadas` |
| M19: altas por usuario, técnicos, API | `lectura_m19_usuarios_y_api`, `m19_pasa_los_parametros` |
| `?` = parámetros en cada llamada real; sin literales; sin `ISNULL(…, -1)`; nunca `cla`/`pas` | `cada_llamada_lleva_tantos_parametros…` (m14, m16, m19), `sentencias_parametrizadas…` (×16), `ninguna_sentencia_lee_contrasenas` (todas) |
| Sin medición ≠ cero filas; un fallo no pierde el bloque | `lecturas_m16d/m19_sin_medicion…`, `un_fallo_no_pierde_el_bloque` (×16) |
| Guardia real, error 130, solo SELECT; `--solo M14 M16 M19` | parametrizados sobre todo `SQL`; `main_con_la_lista_de_t0b_quater` |

## Ciclo 1 de revisión (`progress/review_F-009_T0a_quater.md`, CHANGES_REQUESTED) · `7f350bb`

| Punto | Cambio |
|---|---|
| 1 cod2: candidatas que no fijan UN valor | `dnc_misma_obra` y `ctr_cualquier_linea` pasan a `PROPIEDADES_COD2` (se informan, no compiten). Las dos «mismo producto» van por una derivada con UNA fila por clave, `COUNT(DISTINCT cod2) AS n_cod2` y `MIN(cod2)`, y aciertan solo con `n_cod2 = 1` y cod2 igual: equivale al `HAVING … = 1` pedido y además da `ctr_producto_ambiguo` / `dnc_obra_producto_ambigua` (claves con varios cod2) como propiedades. El cierre dice que `con_dnc` se lee en M19_dnc (su fuente directa) |
| 2 H35 en las vinculadas | `M19_vinculadas` suma `dncproide_igual`/`dncide_igual` (iguales y ≠ 0) y `*_ambos_cero`. `COPIA_H35` (cod2, dncide, dncproide) se lee con `UMBRAL_HEREDA_DNC`: «⇒ se copia / NO se copia siempre de ctrpro» por campo y «H35 CONFIRMADA / NO confirmada en: …» |
| 3 Orden de M19 | `M19_cod2_origen` se lanza la última, tras `M19_api` |
| 4 Arrastre sin base | `lectura_m14d` con 0 mov siguientes de otro documento: «sin mov siguiente de otro documento: no se mide el arrastre» |
| obs. a | `_eleccion_de` avisa de los ítems con más de dos naturalezas (pureza sobrestimada ahí) |
| obs. b | Con `M19_sin_alta` vacío, la lectura dice que descartar la API se apoya en el código de sus endpoints de albarán (no escriben `dbo.log`) y que no se mide |
| obs. d | `dncide` entra en `HEREDA_M19` (conclusión de M19_dnc) |

No aplicada la obs. c (`M16d_maestro` por `con.emp`/`cod`): riesgo bajo y no cambia lo que se decide.
Tests: los de cod2, vinculadas y dnc ajustados; cinco nuevos (`test_f009_t0a_quater_c1_*`): existencia ≠ regla
(una propiedad al 98 % no da «REGLA escribible»), H35 en el límite (950/949 de 1000), `M19_cod2_origen` la última,
arrastre sin base y aviso de más de dos naturalezas. **RED**: los tests nuevos contra el script de `8e6e298`
(copia en el scratchpad, `PYTHONPATH` a la copia):

```
$ python -m pytest tests/test_f009_t0_script.py -q -p no:cacheprovider --rootdir . -k "t0a_quater"
E  assert "SELECT docide, proide, COUNT(DISTINCT RTRIM(LTRIM(cod2))) AS n_cod2, ..." in "SELECT x.origen_dnc, ...
E  AssertionError: assert '... natide, dncide; no se heredan: partida.' in '... natide; no se heredan: partida.'
E  AttributeError: module 'scripts.medir_f009_t0' has no attribute 'PROPIEDADES_COD2'
E  AssertionError: assert ('M19_api' == 'M19_cod2_origen'
E  AssertionError: assert 'sin mov siguiente de otro documento: no se mide el arrastre' in 'M14d mov.prepma (60 mov ...
FAILED ...::test_f009_t0a_quater_m19_sql · ..._lectura_m19_dnc · ..._lectura_m19_cod2_origen_y_vinculadas
FAILED ...::test_f009_t0a_quater_c1_las_candidatas_de_existencia_no_compiten_por_la_regla
FAILED ...::test_f009_t0a_quater_c1_h35_en_el_limite_del_umbral[850-True]  (y [849-False])
FAILED ...::test_f009_t0a_quater_c1_cod2_origen_va_la_ultima_de_m19
FAILED ...::test_f009_t0a_quater_c1_m14d_sin_siguiente_de_otro_documento_no_concluye_el_arrastre
FAILED ...::test_f009_t0a_quater_c1_eleccion_avisa_si_un_item_tiene_mas_de_dos_naturalezas
9 failed, 153 passed, 474 deselected in 2.59s
```

Con el código: `636 passed`; ruff limpio en los dos ficheros (por defecto y `--preview --select E2,W,E7,F`).

## Salida real de `bash harness/init.sh` (tras el commit `7f350bb` del ciclo 1)

```
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 80 avisos (deuda previa, no bloquea).   (los dos ficheros tocados: «All checks passed!»)
2369 passed, 1 skipped, 1 warning in 75.15s (0:01:15)
[OK] pytest en verde (con medición de cobertura)
[OK] PUERTA COBERTURA: 98.9% de 1337 líneas cambiadas cubiertas (1322/1337, umbral 80%, nivel critico)
[OK] PUERTA TAMAÑO: F-009 dentro de los topes (requirements 150/150, design 250/250)
[OK] Rama actual: feature/F-009-alta-albaran-compra
ENTORNO LISTO. Puedes trabajar.
```

## Comando para el humano (PowerShell 5.1) · T0b-quater

```powershell
Set-Location C:\Users\pgris\PycharmProjects\sigrid-api
git switch feature/F-009-alta-albaran-compra
& .\.venv\Scripts\python.exe -m scripts.medir_f009_t0 --solo M14 M16 M19
```

- Solo lecturas por `POST /api/sql/read`; credenciales del entorno o del `.env`, nunca impresas.
- Mirar en la CONCLUSIÓN: «M14d …» (M14); «M16d Maestro de XA9999», «Excepciones / Sufijos de …», «Hipótesis
  M16d», «Lectura M16d» (M16); «Lectura M19 (total)», «cod2 de las sin vincular …», «Vinculadas …», «Sin fila de
  alta en log», «AC26/15951 (API)» (M19).
- Si sale «SIN MEDICIÓN», repetir ese bloque con `--solo Mn`; no relanzar justo tras un corte.
- El fichero `%TEMP%\f009_t0_<fecha>.txt` lleva datos de negocio (códigos de usuario, cod2, precios de la muestra):
  **se pega entero** y no se versiona.

## Qué queda fuera y qué falta

- Fuera: ejecutar el script (humano); volcar el resultado en la spec (spec-author); retirar script y test antes de
  T1 (N3); el timeout de `sql/read` (obs. a de T0a-bis).
- MANUAL pendiente: T0b-quater (`--solo M14 M16 M19`).
- Límites conocidos: «técnico» es heurística por el código; «sin alta en log» mezcla la API con albaranes cuya
  alta quedó fuera de la ventana (por eso `M19_sin_alta` da los códigos); la «anterior» de M16d no aplica a la
  primera línea de su obra (se informa aparte).

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests de la prueba de humo | 636 pasan tras el ciclo 1 (630 en la entrega; antes 426), 2,02 s |
| Suite completa | 2369 passed, 1 skipped, 75,15 s |
| Cobertura de líneas cambiadas | 98,9 % (1322/1337) tras el ciclo 1 (`PUERTA COBERTURA`) |
| Mutación | No aplica: script de mediciones desechable que se retira antes de T1 (N3, decisión del humano), como en T0a-ter; no se lanzó campaña |
| ruff en los dos ficheros | sin avisos (también `--preview --select E2,W,E7,F`) |
