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
- `M14d_muestra`: los 15 `mov` de albarán más recientes con esos valores (solo va a `%TEMP%`).
- `lectura_m14d`: la mejor candidata (desempate por orden) «⇒ mov.prepma = …» si llega a `UMBRAL_REGLA_PREPMA`;
  si no, «no concluyente (la mejor: …)». Línea de **arrastre**: si el `mov` siguiente que NO es compra repite el
  prepma (≥ 95 %) ⇒ «precio medio de compra del PRODUCTO que solo cambia con las compras (el resultante)».
- El **PMP global resultante no es calculable barato** (Sigrid no guarda el stock global por `mov`): el prepma del
  `mov` siguiente es su sustituto, y la lectura lo dice.

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

Diccionario: `dncpro` tiene `proide`, `cod2`, `caaide`, `cenide`, `paride`, **`natide`**, `dncide`; `dnc.obride`;
`ctrpro` tiene `cod2`, `natide` y `dncproide`; `pro` **no** tiene `cod2`.

- `M19_dnc` (grupos, 6 `?`): sin vincular desde 2025 con `dncproide > 0` frente a su `dncpro`: cod2 igual / ambos
  vacíos, caaide, producto, natide (= la de `dncpro` y = la del producto de `dncpro`), partida, `dncide`, obra del
  `dnc`, centro. Lectura por grupo y TOTAL; «se heredan (≥ 95 %): …; no se heredan: …».
- `M19_cod2_origen` (sin `?`), por `con_dnc`/`sin_dnc`, solo líneas con cod2: línea del contrato de la cabecera
  con el mismo producto / cualquiera, **planificación de la misma obra y producto / de la misma obra** (para las que
  no enlazan `dncproide`), línea anterior del mismo proveedor y de la misma obra y producto (`LAG`), código de la
  partida, código del producto; propiedades: repetido en otra línea del albarán (`COUNT(*) OVER`), albarán con
  contrato. Fuentes externas en derivadas `DISTINCT` + `LEFT JOIN` (no multiplican filas).
- `M19_cod2_valores` (TOP 10 cod2 con nº de obras, productos y proveedores; sin nombres) y `M19_vinculadas`
  (cod2 de la línea frente a `ctrpro` por clave primaria y a la `dncpro` del contrato).
- `M19_altas_usuario` (5 `?`): líneas MA9999/QA9999/XA9999 desde `DESDE_ALTAS_LOG` por `log.usu` de la **última**
  ope 1 de su (emp, cod) en la ventana (`_ALTAS_LOG`; el cod se reutiliza tras borrar, M17b), y por producto.
  De `usu` solo el código y `tipdes` (`en_usu`, `desactivado`). `''` = **sin alta en log** (la API no escribe log).
  Lectura: TOP 10 usuarios, % sin alta, «posibles usuarios técnicos por su código» (heurística
  `MARCAS_USUARIO_TECNICO`: el diccionario no tiene esa marca) y usuarios del log que no están en `usu`.
- `M19_sin_alta` (TOP 10 albaranes recientes con esos genéricos y sin alta) y `M19_api` (productos de
  `AC26/15951`): «solo el albarán de prueba de la API» / «hay otros además del de prueba».

## Lecturas baratas añadidas (justificación)

`M16d_sufijos` y `obra_natcod` (la composición de la caa de XA9999 no se ve con una sola candidata);
`regla_ampliada` (es la regla que escribiría la spec si XA9999 sigue `<obra>.<caagascod entero>`); clase del `mov`
siguiente y `entre_anterior_y_pre` (distinguen «PMP de compra del producto» de «precio de la línea»);
`M19_cod2_valores`, `es_cod_partida`/`es_cod_producto` y `repetido_en_albaran` (forma y alcance del cod2);
`M19_sin_alta` y `M19_api` (cierran la duda 4 con nombres de albarán, no solo cifras). Todas por las mismas
tablas e índices que M16b/M16c/M17.

## Desviaciones (justificadas)

1. **Ventana de usuarios desde 2025-09-01**, no desde 2025: la ventana de `log` (`_VENTANA_LOG`, 1.000.000 `ide`)
   arranca el 2025-08-20 (M17 del 2026-10-05); antes de ella todo saldría «sin alta». El encargo lo permite.
2. **MA99 frente a MA1501 por la naturaleza de la ficha frente a «otra»**, no por literal: sin literales en el SQL;
   T0b-ter dice que esas dos son el 100 % de las líneas MA9999 (23.217 + 22.375 = 45.592), así que es equivalente.
3. **Las tres dimensiones de M16d en la misma ventana** (desde 2025-09-01) para que la pureza sea comparable.

## Riesgo de tiempo (balanceador 230 s; `sql/read` no corta la consulta en el servidor)

Todas las sentencias van envueltas (`_leer_tabla`, y M14d además en el `try` de las partes de `m14`): una que
falle se anota y el bloque sigue. Referencias de T0b-ter: M14c 0,5 s (mismo patrón que M14d, dos seeks por `mov`
en `pfhi`, ~8.300 `mov`); M16c_reglas 9,8 s (universo de `M16d_candidatas`, que añade dos `LAG` sobre ~190.000
filas); M16c_naturalezas_ma 2,9 s (universo de las tres de elección); M17 1-2 s (ventana de `log`). Lo más
pesado: `M16d_candidatas` y `M19_cod2_origen` (dos `LAG`, un `COUNT OVER` y cuatro derivadas `DISTINCT` sobre
`ctrpro` (245.566 filas) y `dncpro`). Estimación: decenas de segundos, no minutos. Por eso M16d va al final de
M16 y M19 es un bloque aparte.

## Fase RED (comando exacto, salida real)

Tests escritos antes que el código (más el ajuste de `test_f009_t0_hay_una_medicion_por_cada_m_de_la_spec` a
M1-M19):

```
$ .venv/Scripts/python.exe -m pytest tests/test_f009_t0_script.py -q -p no:cacheprovider -k "t0a_quater or medicion_por_cada"
__main__.py: error: medición desconocida: M19 (válidas: M1, M2, ..., M17, M18)
FAILED tests/test_f009_t0_script.py::test_f009_t0_hay_una_medicion_por_cada_m_de_la_spec
FAILED tests/test_f009_t0_script.py::test_f009_t0a_quater_existen_las_sentencias_nuevas
FAILED ...::test_f009_t0a_quater_sentencias_parametrizadas_sin_literales_ni_isnull_negativo[M14d_prepma_producto]  (y las otras 15)
FAILED ...::test_f009_t0a_quater_cada_llamada_lleva_tantos_parametros_como_marcadores[m19]
FAILED ...::test_f009_t0a_quater_m14d_va_por_el_producto_en_cualquier_almacen
FAILED ...::test_f009_t0a_quater_m14_pasa_la_ventana_de_un_mes_a_m14d
FAILED ...::test_f009_t0a_quater_lectura_m14d_arrastre_y_candidatas
FAILED ...::test_f009_t0a_quater_lectura_m14d_en_el_limite_del_umbral[95-True]  (y [94-False])
FAILED ...::test_f009_t0a_quater_lectura_m14d_sin_medicion_frente_a_cero_filas
FAILED ...::test_f009_t0a_quater_m16d_sql_de_excepciones_y_candidatas  (y m16d_eleccion…, m16_pasa_xa9999…)
FAILED ...::test_f009_t0a_quater_lecturas_m16d_maestro_excepciones_y_sufijos
FAILED ...::test_f009_t0a_quater_lectura_m16d_candidatas  (y …_en_el_limite[95-True], [94-False])
FAILED ...::test_f009_t0a_quater_lectura_m16d_eleccion_por_dimension
FAILED ...::test_f009_t0a_quater_lecturas_m16d_sin_medicion_frente_a_cero_filas
FAILED ...::test_f009_t0a_quater_m19_sql - KeyError:...  (y m19_pasa_los_parametros)
FAILED ...::test_f009_t0a_quater_lectura_m19_dnc - A...  (y …_cod2_origen_y_vinculadas, …_usuarios_y_api)
FAILED ...::test_f009_t0a_quater_lecturas_m19_sin_medicion_frente_a_cero_filas
FAILED ...::test_f009_t0a_quater_un_fallo_no_pierde_el_bloque[m14-M14d_prepma_producto]  (y las otras 15)
FAILED ...::test_f009_t0a_quater_main_con_la_lista_de_t0b_quater
57 failed, 84 passed, 425 deselected in 11.63s
```

Errores (`grep "^E " | sort | uniq -c`): `AttributeError: … no attribute 'm19'` (×9), `KeyError:
'M14d_prepma_producto'` (×4), `… no attribute 'lectura_m14d'` (×4), `KeyError: 'M16d_excepciones'` (×3), `… no
attribute 'lectura_m16d_candidatas'` (×3), `KeyError: 'M19_dnc'`, `'M16d_sufijos'`, `'M16d_por_*'`,
`'M16d_maestro'`, `'M16d_candidatas'`, `'M14d_muestra'` (×2 cada una), `SystemExit: 2` (main con `--solo … M19`).
Los 84 que pasaban son los parametrizados sobre todo `SQL` (aún sin las sentencias nuevas) y los de `m14`/`m16` que
cuentan marcadores. Tras el código: `630 passed, 1 warning in 2.08s` a la primera; ruff marcó un ISC004
(concatenación implícita en una lista) y se envolvió entre paréntesis: `630 passed`, ruff limpio (por defecto y
`--preview --select E2,W,E7,F`).

Ajuste de test: `test_f009_t0a_ter_un_fallo_de_m16c_no_pierde_el_bloque…` usa ahora `_datos_quater()` (con datos de
M16d): con la fixture anterior, M16d devolvía cero filas legítimas y su texto contenía «cero filas».

## Trazabilidad (encargo → test, prefijo `test_f009_t0a_quater_`)

| Punto | Test |
|---|---|
| M14d: producto en cualquier almacén por `pfhi`, ventana, banderas | `m14d_va_por_el_producto…`, `m14_pasa_la_ventana…` |
| M14d: lectura, arrastre, umbral 95/94, sin medición ≠ cero filas | `lectura_m14d_arrastre…`, `…_en_el_limite_del_umbral`, `lectura_m14d_sin_medicion…` |
| M16d: XA9999, excepciones y sufijos (XA9999 y MA9999) | `m16d_sql_de_excepciones…`, `m16_pasa_xa9999_y_ma9999…`, `lecturas_m16d_maestro…` |
| M16d: candidatas (regla ampliada, «anterior» por obra+naturaleza y obra+producto) | `m16d_sql…`, `lectura_m16d_candidatas`, `…_candidatas_en_el_limite` |
| M16d: MA99/MA1501 por obra, proveedor y usuario | `m16d_eleccion_por_obra_proveedor_y_usuario`, `lectura_m16d_eleccion_por_dimension` |
| M19: dnc/dncpro, origen del cod2, vinculadas | `m19_sql`, `lectura_m19_dnc`, `lectura_m19_cod2_origen_y_vinculadas` |
| M19: altas por usuario, técnicos, API | `lectura_m19_usuarios_y_api`, `m19_pasa_los_parametros` |
| `?` = parámetros en cada llamada real; sin literales; sin `ISNULL(…, -1)`; nunca `cla`/`pas` | `cada_llamada_lleva_tantos_parametros…` (m14, m16, m19), `sentencias_parametrizadas…` (×16), `ninguna_sentencia_lee_contrasenas` (todas) |
| Sin medición ≠ cero filas; un fallo no pierde el bloque | `lecturas_m16d/m19_sin_medicion…`, `un_fallo_no_pierde_el_bloque` (×16) |
| Guardia real de `sql/read`, error 130, solo SELECT | los parametrizados previos sobre todo `SQL` (ya incluyen las 16 nuevas) |
| `--solo M14 M16 M19` | `main_con_la_lista_de_t0b_quater` |

## Salida real de `bash harness/init.sh` (tras el commit `aa599f0`)

```
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 80 avisos (deuda previa, no bloquea).   (los dos ficheros tocados: «All checks passed!»)
2363 passed, 1 skipped, 1 warning in 74.48s (0:01:14)
[OK] pytest en verde (con medición de cobertura)
[OK] PUERTA COBERTURA: 98.9% de 1322 líneas cambiadas cubiertas (1307/1322, umbral 80%, nivel critico)
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
| Tests de la prueba de humo | 630 pasan (antes 426), 2,08 s |
| Suite completa | 2363 passed, 1 skipped, 74,48 s |
| Cobertura de líneas cambiadas | 98,9 % (1307/1322) tras el commit; antes de él, 98,4 % (867/881) |
| Mutación | No aplica: script de mediciones desechable que se retira antes de T1 (N3, decisión del humano), como en T0a-ter; no se lanzó campaña |
| ruff en los dos ficheros | sin avisos (también `--preview --select E2,W,E7,F`) |
