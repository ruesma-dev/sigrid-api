<!-- progress/impl_F-009_T0a.md -->
# Informe del implementer · F-009 T0a (ampliación del script de T0)

Fecha: 2026-10-05. Rama `feature/F-009-alta-albaran-compra`. F-009 sigue en `spec_ready`: T0a es
la tarea previa a `in_progress`, autorizada por el humano. **No se ha llamado a la API, ni a
Azure, ni al SQL Server**: el script lo lanza el humano en T0b.

## Qué cambió

| Fichero | Cambio |
|---|---|
| `scripts/medir_f009_t0.py` | M16, M17 y M18 nuevas; M11 y M14 ampliadas según `progress/spec_F-009.md` §T0 v5; `--solo` acepta M16-M18; docstring y ayuda dicen M1-M18 |
| `tests/test_f009_t0_script.py` | 79 tests más (163 → 242), todos sin red ni BBDD |

No se han tocado la spec (`specs/F-009-…/*`), `progress/spec_F-009.md`, `harness/features.json`,
`BACKLOG.md`, `progress/current.md`, `progress/para_albaranes_F-009.md`, `.env` ni el fichero sin
trackear de la raíz. **La casilla de T0a en `tasks.md` queda sin marcar** porque ese fichero lo
está editando el spec-author: la marca el líder o el spec-author.

### Sentencias nuevas (20; el script pasa de 47 a 67)

- **M16** (`m16`): `M16_caa_con_partida`, `M16_caa_almacen`, `M16_almacen_sin_vincular`,
  `M16_ficha_obra`, tal cual la spec. Las expresiones `CASE` del `SELECT` y del `GROUP BY` salen de
  los mismos fragmentos fijos (`_TIPO_LINEA`, `_PARTIDA_DISTINTA`, `_TIPO_PARTIDA`, `_CABECERA`),
  así que no pueden divergir.
- **M17** (`m17`): `M17_ope`, `M17_existe`, `M17_marcas` de la spec, más `M17_emp_log` y
  `M17_existe_sin_emp` (ver desviaciones). Además reutiliza `M2_conest` para saber qué `est` son
  estados válidos.
- **M18** (`m18`): `M18_refent`, `M18_valores`, `M18_propagacion`, tal cual.
- **M11 ampliada** (`_m11_iva_por_proveedor`, dentro del bucle que ya recorría cada MA9999 por
  empresa): `M11_iva_por_proveedor`, `M11_iva_y_isp`, `M11_acierto`, con el `ide` como parámetro
  `?`. Se mantiene `M11_iva_usado` (la comprobación de `ivacuo`).
- **M14 ampliada** (`_m14_sin_vincular`; lo que ya hacía M14 pasa sin cambios a
  `_m14_frente_a_la_api`): `M14_sv_valores` y el arrastre (`M14_sv_ma9999`, `M14_sv_ultimas`,
  `M14_sv_linea`, `M14_sv_plantilla`).

Todas son `SELECT` de una sentencia, con `?` para cualquier valor de fuera (los `ide`, `MA9999`,
la empresa 1) y respetan la regla del error 130: los recuentos por proveedor van en tabla derivada
y ningún agregado lleva subconsulta dentro (la prueba de humo lo comprueba con el detector).

### Conclusión automática de cada bloque («debe salir / decide» de la spec)

Cada medición escribe su «CONCLUSIÓN» con las cifras y una lectura automática, con funciones puras
probadas sin red:

- `lectura_m16`: ≥ 95 % en las tres proporciones de analítica ⇒ «Hipótesis de design §Analítica:
  CONFIRMADA», si no «NO confirmada ⇒ PARADA y v6». Orden de R15: almacén del contrato dominante en
  `con_contrato`, el de la ficha en `sin_contrato`, `con_almide` ≥ 95 % de `obras` y
  `almide_de_su_obra` ≥ 95 % de `con_almide` ⇒ «CONFIRMADO», si no «PARADA y v6».
- `lectura_m17`: alguna `ope` ≠ 1 con `con_existe` ≤ 5 % ⇒ «anular BORRA: R30 sin cambios»; todas
  con `con_existe` ≥ 95 % y hay marca (`fecbaj` > 0 o `est` fuera de `conest`) ⇒ «MARCA: L11 añade
  AND <no marcado> y F-053 usa ALB-{id}-{n}»; si no ⇒ «se decide con T23».
- `lectura_m18`: `con_refent` ≤ 0,1 % ⇒ «LIBRE: se escribe referencia_linea»; si no, «NO libre».
  `copiada` > 0 ⇒ «la referencia llegaría a la factura (N9)».
- `lectura_l8b` (M11): `acierta_mismo_prv` > `acierta_cualquiera` o IVA de `tipisp` 1 distinto del
  resto ⇒ «L8b JUSTIFICADA (motivo)»; si aciertan igual ⇒ «L8b inocua: se queda».
- `lectura_sv_valores` (M14): columnas con ≤ 0,1 % de valores ⇒ «reseteo confirmado»; las demás,
  con su porcentaje, ⇒ «revisar §Reseteo (v6)»; `fec_igual_albaran` ≥ 95 % ⇒ «§Reseteo debe
  escribir fec = con.fec (v6)». El arrastre lista, por línea, las columnas que difieren de su
  plantilla marcando «lista de reseteo» o «FUERA de la lista», y concluye con las de fuera.

Los umbrales son constantes con nombre (`UMBRAL_CASI_TODO` 0,95, `UMBRAL_CASI_NADA` 0,001,
`UMBRAL_BORRA` 0,05). **Son mi traducción de los «≈», «dominante» y «≈ 0» de la spec**: la lectura
automática orienta, pero las cifras van siempre al lado y decide el humano.

## Desviaciones respecto de la spec y por qué

1. **M17, `log.emp` nulo (alternativa de la spec).** El script lo resuelve solo: `M17_emp_log`
   cuenta las filas por `ISNULL(emp, -1)`; si alguna sale 0 o nula, lanza `M17_existe_sin_emp`
   (mismo `SELECT`, `JOIN` solo por `tip` y `cod`), lo anota en la conclusión y la lectura usa esa
   repetición. Aviso escrito en el resultado: un `cod` repetido entre empresas cuenta de más (con
   el 99,97 % de albaranes en `emp` 1, despreciable).
2. **M11, `OVER` rechazado (alternativa de la spec).** `SqlQueryGuard` **acepta** `LAG ... OVER`
   (lo comprueba la prueba de humo con el guardia real). Si aun así la llamada falla (p. ej. SQL
   Server la rechaza), `m11` captura el error, escribe «M11_acierto (LAG ... OVER) no se pudo leer
   (…); según la spec se queda con las dos primeras» y sigue: no se pierde el resto de M11.
3. **M14 arrastre: el `ide` del MA9999 de la empresa 1** lo busca una sentencia propia
   (`M14_sv_ma9999`, `cod = ?` y `emp = ?`) en vez de depender de M11, para que M14 funcione sola
   con `--solo M14`.
4. **M14 arrastre, columnas ignoradas**: las de `PROPIAS_DEL_DOCUMENTO` (las que cambian por
   construcción: `ide`, `docide`, `pos`, `can`, `pre`, `almide`…) **menos** las de la lista de
   reseteo, para que `fec` (que está en ambas) sí se compare.
5. **`M14_sv_valores` cuenta exactamente las columnas que nombra la spec.** Ocho columnas de
   `LISTA_DE_RESETEO` no están en esa lista (`dncide`, `dncproide`, `desesp`, `edilin`, `garfec`,
   `mesrevpre`, `ejerevpre`, `prepma`): no se cuentan ahí; sí salen en el arrastre si difieren de
   la plantilla, y `prepma` ya lo mide `M14_prepma`. Si el humano las quiere en el recuento, es
   añadir una tupla a `COLUMNAS_SV`. `tex` (que la spec sí pide) no está en la lista de reseteo y
   se marca como «solo informativa».
6. **Tipos de columna comprobados** contra `azure-apps/sigrid_tablas.md`: `med` binario ilimitado,
   `tex`/`texcom` texto ilimitado (por eso `DATALENGTH`), `cod2`/`pac`/`refent` texto de 24, el
   resto enteros, reales o fechas enteras; `alm.caaproide`/`caaseride`, `obr.almide`/`cenide`,
   `dca.ctride`/`tipisp`, `ctr.almide`/`cenide`, `log.emp`/`ope` y `dcfpro.refent`/`linoriide`
   existen. Lo que el diccionario no garantiza (versión 2024) se verá en T0b.

## Fase RED (con el comando exacto)

Tests escritos antes del código. Salida real (resumen de pytest):

```
$ .venv/Scripts/python.exe -m pytest tests/test_f009_t0_script.py -q -k "spec or t0a" -p no:cacheprovider
__main__.py: error: medición desconocida: M16, M17, M18 (válidas: M1, M2, M3, M4, M5, M6, M7, M8, M9, M10, M11, M12, M13, M14, M15)
FAILED tests/test_f009_t0_script.py::test_f009_t0_hay_una_medicion_por_cada_m_de_la_spec
FAILED tests/test_f009_t0_script.py::test_f009_t0a_existen_las_sentencias_nuevas_de_la_spec_v5
FAILED tests/test_f009_t0_script.py::test_f009_t0a_las_sentencias_nuevas_con_valores_van_parametrizadas[M11_iva_por_proveedor]
FAILED tests/test_f009_t0_script.py::test_f009_t0a_las_sentencias_nuevas_con_valores_van_parametrizadas[M11_iva_y_isp]
FAILED tests/test_f009_t0_script.py::test_f009_t0a_las_sentencias_nuevas_con_valores_van_parametrizadas[M11_acierto]
FAILED tests/test_f009_t0_script.py::test_f009_t0a_las_sentencias_nuevas_con_valores_van_parametrizadas[M14_sv_ma9999]
FAILED tests/test_f009_t0_script.py::test_f009_t0a_las_sentencias_nuevas_con_valores_van_parametrizadas[M14_sv_ultimas]
FAILED tests/test_f009_t0_script.py::test_f009_t0a_las_sentencias_nuevas_con_valores_van_parametrizadas[M14_sv_linea]
FAILED tests/test_f009_t0_script.py::test_f009_t0a_las_sentencias_nuevas_con_valores_van_parametrizadas[M14_sv_plantilla]
FAILED tests/test_f009_t0_script.py::test_f009_t0a_m14_sv_valores_cuenta_las_columnas_de_la_spec
FAILED tests/test_f009_t0_script.py::test_f009_t0a_solo_acepta_la_repeticion_unica_de_t0b
11 failed, 163 deselected in 1.26s
```

Después del código: `242 passed, 1 warning in 1.16s` (mismo fichero, sin `-k`). Durante la
segunda tanda un test falló de verdad: el arrastre esperaba ver `almide`, que es columna propia del
documento y se ignora a propósito; se corrigió el **dato del test** (se usa `dto`) y se añadió la
aserción de que `almide` no se señala.

## Qué prueba la prueba de humo nueva

- Existen las 20 sentencias nuevas y las que llevan valores van con `?` (sin `{`, sin `MA9999`
  dentro del texto). Las 67 sentencias pasan los tests ya parametrizados sobre `SQL`: solo
  `SELECT`/`WITH` de una sentencia, el `SqlQueryGuard` real de `sql/read` con los topes de `dev`
  (incluido `LAG ... OVER`) y el detector del error 130.
- `M14_sv_valores` cuenta las 16 columnas de la spec y `fec_igual_albaran`, con la condición de
  cada tipo.
- `--solo M3 M7 M9 M11 M13 M14 M16 M17 M18` se acepta, y `main` con esa lista escribe las nueve
  mediciones en el fichero sin ningún `ERROR` (cliente falso).
- M11 ampliada va por cada MA9999 (`[[31], [1]]` de parámetros en cada sentencia nueva) y sigue si
  `M11_acierto` falla.
- M17 solo lanza `M17_existe_sin_emp` cuando `log.emp` sale 0 o nulo, y entonces la lectura cambia.
- Las lecturas de M16, M17, M18, L8b y `sv_valores` en sus casos (confirma, PARADA, borra, marca,
  T23, libre/no libre en el límite de 0,1 %, muestra vacía).
- Las mediciones nuevas no revientan sin datos (test existente sobre todo `MEDICIONES`).

## Salida real de `bash harness/init.sh`

```
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 80 avisos (deuda previa, no bloquea).   (los dos ficheros tocados: «All checks passed!»)
1975 passed, 1 skipped, 1 warning in 71.59s (0:01:11)
[OK] pytest en verde (con medición de cobertura)
[OK] PUERTA COBERTURA: 97.7% de 355 líneas cambiadas cubiertas (347/355, umbral 80%, nivel critico)
[OK] PUERTA TAMAÑO: F-009 dentro de los topes (requirements 150/150, design 249/250)
[OK] Rama actual: feature/F-009-alta-albaran-compra
ENTORNO LISTO. Puedes trabajar.
```

## Comando para el humano (T0b, PowerShell 5.1)

```powershell
Set-Location C:\Users\pgris\PycharmProjects\sigrid-api
git switch feature/F-009-alta-albaran-compra
& .\.venv\Scripts\python.exe -m scripts.medir_f009_t0 --solo M3 M7 M9 M11 M13 M14 M16 M17 M18
```

- Solo lecturas por `POST /api/sql/read`; credenciales del entorno o del `.env`, nunca impresas.
- Tarda varios minutos: casi todas las sentencias nuevas piden hasta 200 s (corte del balanceador,
  230 s). Si una medición falla, el script la anota en su bloque y sigue; se repite con `--solo Mn`.
- Al final indica el fichero `%TEMP%\f009_t0_<fecha>.txt`: **se pega entero** de vuelta. Lleva
  datos de negocio: no se versiona (el script se niega a escribirlo dentro del repositorio).

## Qué queda fuera y qué falta

- Fuera: ejecutar el script (T0b, humano); volcar resultados en la spec (T0c, spec-author); retirar
  el script y su test antes de T1 (T0c, N3); marcar T0a en `tasks.md` (el fichero lo edita el
  spec-author en paralelo).
- Riesgo residual: el diccionario es de 2024; si alguna columna no existe en la base real, esa
  medición saldrá con `ERROR` en su bloque y se corrige antes de repetir con `--solo`.
- Las sentencias más pesadas nuevas son `M11_acierto` (ventana con `LAG` sobre todas las líneas de
  MA9999 de la empresa 1 desde 2025), `M17_*` (ventana de 1.000.000 `ide` de `log`, como M13) y
  `M18_propagacion` (`dcfpro` × `dcapro` desde 2025).

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests de la prueba de humo | 242 pasan (antes 163), 1,16 s |
| Suite completa | 1975 passed, 1 skipped, 71,59 s |
| Cobertura de líneas cambiadas | 97,7 % (347/355), `PUERTA COBERTURA` de init.sh |
| Mutación | No aplica: es un script de mediciones desechable que se retira en T0c (N3, decisión del humano en la v4 sobre el alcance del script de T0 en cobertura y mutación); no se lanzó campaña |
| ruff en los dos ficheros | sin avisos |
