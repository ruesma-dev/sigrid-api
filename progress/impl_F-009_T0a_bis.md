<!-- progress/impl_F-009_T0a_bis.md -->
# Informe del implementer · F-009 T0a-bis (segunda pasada del script de T0)

Fecha: 2026-10-05. Rama `feature/F-009-alta-albaran-compra`. F-009 sigue en `spec_ready`; T0 está
autorizada por el humano. **No se ha llamado a la API, ni a Azure, ni al SQL Server**: el script lo
lanza el humano. Origen: la ejecución del 2026-10-05 (`%TEMP%\f009_t0_20261005_132453.txt`).

## Qué cambió

| Fichero | Cambio |
|---|---|
| `scripts/medir_f009_t0.py` | M9 y M11 reescritas por ventanas cortas y cada sentencia protegida; M14b, M16b y M17b nuevas; reintento ante el 1205 en el cliente; M16, M17 y la parte «API» de M14 ya no pierden el bloque por una sentencia |
| `tests/test_f009_t0_script.py` | 79 tests más (276 → 355), sin red ni BBDD; dos tests antiguos de M11 adaptados (ver Desviaciones 2) |

No se han tocado la spec, `progress/spec_F-009.md`, `progress/current.md`, `harness/features.json`,
`BACKLOG.md`, `.env` ni el fichero sin trackear de la raíz. Sentencias: 67 → 75. Todas `SELECT` de
una sentencia, con `?` para los valores de fuera, aceptadas por el `SqlQueryGuard` real y sin el
patrón del error 130 (los tests de humo lo comprueban sobre las 75).

### 1. M9 y M11 sin cortes (el balanceador corta a 230 s)

- **Ventanas cortas y cerradas**, como parámetros `?`: `VENTANA_M9` = 2026-09-01..30 y `VENTANA_M11`
  = 2026-07-01..09-30. Un mes cerrado toca menos filas y menos de las que el escritorio está editando
  hoy (el `M14_prv` del 2026-10-05 tardó 121 s para 2.608 filas y M14 cayó por interbloqueo: hay
  contención de bloqueos, no solo volumen).
- **Índices según el diccionario**: se entra por `con` (`tip`, `fec`: índices `emptipfec`/`tipfec`),
  `dcapro` por `docide`, y `mov` **por su índice `doclin` (`docide`, `linide`)**. Se eliminan los
  `docide IN (SELECT …)` sobre `mov`. `dcapro` no tiene índice por `proide` en el diccionario: por
  eso `M11_total_producto` (que lo recorría por `proide` sin ventana) ahora va por la ventana.
- Una línea puede tener más de un `mov`: se cuentan **líneas distintas** (`COUNT(DISTINCT …)`).
- **Cada sentencia envuelta** (`_leer_tabla` → `_leer_o_anotar`): un fallo se anota en el bloque
  («`<nombre>` no se pudo leer (…); el resto del bloque sigue») y lo demás se ejecuta.
- M9 responde: `M9_por_banderas` (`pro.tipmov`, `pro.tipinv`, `auxfam.tipinv`) y la nueva
  **`M9_genericos`** (MA9999, QA9999, SM9999, SB9999 por código y empresa, con sus banderas).
  `lectura_m9`: `pro.<campo>` **DECIDE** si con valor 1 hay mov en ≥ 95 % (`UMBRAL_CASI_TODO`) y con
  otro valor en ≤ 5 % (`UMBRAL_CASI_NINGUNA`, nueva); por genérico, en la empresa 1 y en todas:
  «SÍ genera mov» / «NO genera mov» / «a veces» / «sin líneas en la ventana».
  (Dato previo: en la M10 del 2026-10-02 ya salían `mov` de 1444469 MA9999, 1444470 QA9999 y
  1444472 SM9999 de la empresa 1; M9 lo cuantifica.)

### 2. M16b: origen de `dcapro.caaide` en las sin vincular (desde 2025)

Grupos: MA9999, QA9999, SM9999 y SB9999 **de la empresa 1** por separado y «resto», × con/sin
partida. Dos sentencias de banderas 0/1 por línea en tabla derivada (el grupo lleva `?`: agrupar
por la expresión repetida con otros `?` no lo acepta SQL Server) y una muestra:

- `M16b_fuentes`: `caaide = 0`; = `pro.gaside`; = `cen.gaside` del centro de la línea; = `dca.caaide`
  (cabecera); = `ctr.caaide` (contrato); = `obrparpar.caaide` (partida); **caa del centro de la línea**
  (`caa.cenide = dcapro.cenide`, pista del director de Administración y Control de Costes).
- `M16b_codigos` (`caa`, `cua`, `obr`, `cen` son «Propiedades de con»: su código está en `con.cod`):
  código de caa = `auxpronat.caagascod` / `caaexicod` / `cuafaccod` («Cód cta Financiera - Analítica
  compras») de la naturaleza del producto (`pro.natide`); = la cuenta financiera de la línea
  (`dcapro.cueide` → `cua`); empieza por ella; contiene el código de la obra; contiene el del centro;
  y las combinaciones con el centro (pista del director): **caa del centro con código caagascod** y
  **caa del centro cuyo código empieza por la cuenta financiera**. Informativas: cuenta 6XX y cuenta =
  `auxpronat.cuacomcod`.
- `M16b_muestra`: TOP 20 por frecuencia de (código de caa, `caagascod`, `caaexicod`, código de obra,
  **código de centro**, **código de la cuenta financiera**, con/sin partida). Se lanza siempre
  (barata); `lectura_muestra_m16b` mide, ponderado por líneas, si el código de caa = caagascod,
  contiene el de obra o el de centro, o empieza por la cuenta.
- `lectura_m16b`: por grupo y partida, **domina** la fuente de mayor proporción si llega a
  `UMBRAL_DOMINANTE` (50 %); con ≥ 95 % añade «⇒ REGLA»; si no, «ninguna fuente domina (la mejor:
  …)». A igual proporción gana la más específica (orden de `FUENTES_M16B`).
- `obr` no ofrece una analítica de gasto candidata (sus `caaejecer`, `caaejepen`, `caacerant`,
  `caacomava` son de obra ejecutada, certificación y avales): se sustituye por «código de caa contiene
  el de la obra».

### 3. M17b: ¿anular borra y el código se reutiliza?

`log` no guarda el `ide` del registro (diccionario: `ide, emp, ori, ope, fec, hor, usu, tab, tip,
cod, res, tex, est, err`). `M17b_reutiliza` clasifica cada `ope 2` (misma ventana de 1.000.000 `ide`
que M13/M17) en `no_existe`, `existe_con_alta_posterior` (hay un `ope 1` del mismo `(emp, cod)` con
`ide` mayor: el código se reutilizó) y `existe_sin_alta_posterior`; añade si hubo alta previa en la
ventana y si `con.fec` es posterior a la ope. `lectura_m17b`: no existe + reutilizado ≥ 95 % ⇒
«anular BORRA (el cod se reutiliza en N)»; sigue ≥ 95 % ⇒ «MARCA o no es anulación»; si no, «no
concluyente ⇒ T23». `M17b_perfil` (filas, documentos, usuarios y `est` por ope) y `M17b_res` (TOP 40
de `LEFT(res, 40)` por ope); `lectura_ope` deduce el significado de cada ope ≠ 1 por palabras de su
resumen más frecuente (modificación, impresión, anulación, baja, borrado, cambio de estado,
contabilización, facturación, consulta, envío, exportación) o dice «no deducible».

### 4. M14b: pago del albarán anterior frente al maestro

`M14b_pago_previo`: albaranes desde 2026-09; el anterior es el de `ide` inmediatamente menor del mismo
proveedor en la misma empresa (`LAG … OVER (PARTITION BY c.emp, a.entide ORDER BY c.ide)`, buscado
desde 2026-01). Cuenta `pagide`/`efeide` iguales al anterior y al maestro **sobre los mismos
albaranes** (los que tienen anterior); el maestro sobre todos va aparte (repite M14_prv). `lectura_m14b`
por campo: «acierta más el ALBARÁN ANTERIOR ⇒ la regla de la spec se sostiene» / «el MAESTRO ⇒
revisar la regla de cabecera (v6)» / «empate».

### 5. Reintento ante el 1205

`ClienteLectura.leer` repite hasta `REINTENTOS_INTERBLOQUEO` (2) veces, con espera creciente
(`ESPERA_INTERBLOQUEO_S` 5 s, 10 s), **solo** si el error es el interbloqueo (`(1205)` o `40001`);
cualquier otro (incluido un `ReadTimeout`) sale a la primera, para no gastar 230 s más. Vale para
todas las sentencias; la comparación de M14 con el albarán de la API se repite así. Además,
`M14_prv` y `M14_prepma` (la del interbloqueo) ya no se llevan la comparación columna a columna.

### 6. QA9999 junto a MA9999 (spec v6, lista blanca; aviso del líder durante la tarea)

M9 ya concluía por separado por código y empresa («MA9999 emp 1: …», «QA9999 emp 1: …»). M11
recorría solo los MA9999: ahora recorre `LISTA_BLANCA_GENERICOS` = (`MA9999`, `QA9999`) de cada
empresa, con las mismas seis sentencias por producto, y todas sus conclusiones (líneas, combinación,
IVA por proveedor, ISP, acierto y L8b) llevan el código delante («QA9999 emp 1: L8b …»). Cuesta seis
sentencias más por cada QA9999 (hay tres: empresas 1, 31 y 34), todas por la ventana de M11.

## Desviaciones y por qué

1. **El reintento está en el cliente**, no solo en M14: el 1205 es transitorio en cualquier sentencia
   y `docs/CONVENTIONS.md` pide reintentos con backoff ante errores transitorios.
2. **M11 por ventana (jul-sep 2026), también `M11_total_producto`**: deja de dar «desde siempre» (era
   la sentencia sin ventana que recorría `dcapro` por `proide`). Los tests antiguos que esperaban
   `[ide]` como único parámetro se adaptaron a `[desde, hasta, ide]`.
3. **M16b, «naturaleza del producto» = `pro.natide`** (literal del encargo), no `dcapro.natide`.
4. **M14b no distingue los albaranes de la API** de los del escritorio: son un puñado frente a ~2.600.
5. **No se añade `WITH (NOLOCK)`** (no pedido). Si M9/M11 vuelven a cortarse, propuesta para el
   líder: leer sin bloqueos compartidos evitaría esperar a las filas que edita el escritorio (y que
   nuestras lecturas le estorben); son agregados de medición, una lectura sucia no los altera.

## Fase RED (comando exacto, salida real)

Tests nuevos escritos antes del código:

```
$ .venv/Scripts/python.exe -m pytest tests/test_f009_t0_script.py -q -p no:cacheprovider -k "t0a_bis"
FAILED tests/test_f009_t0_script.py::test_f009_t0a_bis_existen_las_sentencias_nuevas
FAILED ...::test_f009_t0a_bis_las_sentencias_nuevas_van_parametrizadas_o_sin_valores_de_fuera[M9_genericos]  (y las 7 restantes)
FAILED ...::test_f009_t0a_bis_m9_va_por_ventana_corta_sin_subconsultas_in[M9_por_tipsininv]  (y M9_por_partida, M9_por_banderas, M9_genericos, M9_sin_mov_por_producto)
FAILED ...::test_f009_t0a_bis_m11_va_por_ventana_corta[M11_total_producto]  (y las otras 5 de M11)
FAILED ...::test_f009_t0a_bis_m11_pasa_la_ventana_y_el_ide_de_cada_ma9999
FAILED ...::test_f009_t0a_bis_m9_pasa_la_ventana_y_los_genericos
FAILED ...::test_f009_t0a_bis_m9_un_fallo_no_pierde_el_bloque[M9_por_tipsininv]  (×5)
FAILED ...::test_f009_t0a_bis_m11_un_fallo_no_pierde_el_bloque[M11_productos]  (y M11_total_producto, M11_lineas_producto, M11_iva_usado)
FAILED ...::test_f009_t0a_bis_m16_un_fallo_no_pierde_el_bloque[M16_caa_con_partida]  (y M16b_fuentes, M16b_codigos, M16b_muestra)
FAILED ...::test_f009_t0a_bis_m17_un_fallo_no_pierde_el_bloque[M17_ope]  (y M17_existe, M17b_reutiliza, M17b_res)
FAILED ...::test_f009_t0a_bis_m14_un_fallo_no_pierde_la_comparacion[M14_prepma]  (y M14_prv, M14b_pago_previo)
FAILED ...::test_f009_t0a_bis_lectura_m9_tipmov_decide_y_genericos
FAILED ...::test_f009_t0a_bis_lectura_m9_ninguna_bandera_y_a_veces
FAILED ...::test_f009_t0a_bis_lectura_m16b_dice_que_fuente_domina
FAILED ...::test_f009_t0a_bis_lectura_m16b_sin_dominante_y_desempate
FAILED ...::test_f009_t0a_bis_lectura_muestra_m16b_ve_el_patron_del_codigo
FAILED ...::test_f009_t0a_bis_lectura_m17b_borra_marca_o_no_concluyente
FAILED ...::test_f009_t0a_bis_significado_de_ope_por_su_resumen
FAILED ...::test_f009_t0a_bis_lectura_m14b_anterior_frente_a_maestro
FAILED ...::test_f009_t0a_bis_el_cliente_reintenta_ante_el_interbloqueo_1205
FAILED ...::test_f009_t0a_bis_el_cliente_se_rinde_tras_los_reintentos_y_no_reintenta_otros_errores
FAILED ...::test_f009_t0a_bis_main_con_la_lista_de_la_segunda_pasada
53 failed, 1 passed, 276 deselected in 7.16s
```

(Las líneas con «(y …)» agrupan casos parametrizados que la salida listaba uno a uno. El que pasó
es `m11_un_fallo…[M11_acierto]`, que ya estaba protegido desde el ciclo 1 de T0a.)

Tras el código: `2 failed, 352 passed` — los dos tests antiguos de M11 que esperaban `[ide]` como
único parámetro (Desviación 2); adaptados: `354 passed, 1 warning in 4.08s`.

RED del ajuste QA9999 (test escrito antes del cambio):

```
$ .venv/Scripts/python.exe -m pytest tests/test_f009_t0_script.py -q -p no:cacheprovider -k "qa9999"
E           AssertionError: M11_total_producto
E           assert [1] == [1, 5]
E             Right contains one more item: 5
FAILED tests/test_f009_t0_script.py::test_f009_t0a_bis_m11_mide_y_concluye_qa9999_aparte_de_ma9999
1 failed, 354 deselected in 0.39s
```

Con el cambio: `355 passed, 1 warning in 3.82s`.

## Qué prueba la prueba de humo nueva

Lo que listan los tests de la fase RED: sentencias nuevas con `?`; M9/M11 por ventana y sin `IN (SELECT`;
un fallo de cualquier sentencia no tumba su bloque; cada lectura en sus casos y límites; reintento 1205;
`main --solo M9 M11 M14 M16 M17` sin `ERROR`; M11 concluye QA9999 aparte de MA9999.

## Salida real de `bash harness/init.sh`

```
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 80 avisos (deuda previa, no bloquea).   (los dos ficheros tocados: «All checks passed!»)
2088 passed, 1 skipped, 1 warning in 101.37s (0:01:41)
[OK] pytest en verde (con medición de cobertura)
[OK] PUERTA COBERTURA: 98.4% de 817 líneas cambiadas cubiertas (804/817, umbral 80%, nivel critico)
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
- Tarda unos minutos. Una sentencia que falle se anota en su bloque («no se pudo leer») y el resto
  sigue; un interbloqueo se reintenta solo (hasta 2 veces, 5 s y 10 s).
- Al final indica `%TEMP%\f009_t0_<fecha>.txt`: **se pega entero**. Lleva datos de negocio (códigos de
  caa, obra, centro y cuenta en la muestra de M16b; resúmenes de `log.res` en M17b): no se versiona.

## Qué queda fuera y qué falta

- Fuera: ejecutar el script (humano); volcar los resultados en la spec (spec-author); retirar script
  y test antes de T1 (N3).
- Riesgo residual: diccionario de 2024 (una columna inexistente sale anotada en su bloque, no lo
  tumba); si M9/M11 vuelven a cortarse, ver la propuesta de `NOLOCK` (Desviación 5); `M16b_codigos`
  une cuatro veces `con` sobre ~190.000 líneas (las M16 sobre el mismo volumen tardaron 1-3 s).
- Las sentencias más pesadas: `M16b_codigos`, `M17b_reutiliza` (derivada de altas sobre la ventana
  de `log`) y `M14b_pago_previo` (`LAG` sobre los albaranes de 2026).

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests de la prueba de humo | 355 pasan (antes 276), 3,82 s |
| Suite completa | 2088 passed, 1 skipped, 101,37 s |
| Cobertura de líneas cambiadas | 98,4 % (804/817), `PUERTA COBERTURA` de init.sh (tras el ajuste QA9999) |
| Mutación | No aplica: script de mediciones desechable que se retira en T0c (N3, decisión del humano); no se lanzó campaña |
| ruff en los dos ficheros | sin avisos (también `--preview --select E2,W,E7,F`) |
