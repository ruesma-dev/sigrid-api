<!-- progress/impl_F-016.md -->
# F-016 · Informe del implementer (T1-T16)

Spec v2 aprobada (2026-10-28, D6 y D12). Rama `feature/F-016-proforma-a-origen`. Rigor `critico`.

## T1 · La red de R1 y R2

`python -m pytest tests/test_f007_*.py tests/test_f009_*.py tests/test_f015_*.py -q` en la rama, antes de tocar
nada: **1328 passed** en 15,5 s. Ficheros (sin modificar en todo el trabajo):
`test_f007_{filas,models,perfil,route,settings,statements_contrato,statements_lineas,transaccion,use_case}.py`,
`test_f009_{caracterizacion,equivalencia,models,mutacion,route,settings,statements,use_case}.py`,
`test_f015_{statements,use_case}.py`, los dobles `f007_dobles.py` y `f009_dobles.py` y los dorados
`fixtures/f007_obra0719.json` y `fixtures/f009_caracterizacion.json`.

## Fase RED (salidas reales, recortadas a lo que falla)

**T2** `python -m pytest tests/test_f016_models.py -q`:
```
tests/test_f016_models.py:31: in <module>
    from domain.models.proforma_origen_models import (
E   ModuleNotFoundError: No module named 'domain.models.proforma_origen_models'
ERROR tests/test_f016_models.py
1 error in 1.47s
```

**T4** `python -m pytest tests/test_f016_settings.py -q`:
```
E   AttributeError: 'Settings' object has no attribute 'sigrid_proforma_origen_enabled'. Did you mean: 'sigrid_proforma_write_enabled'?
E   Failed: DID NOT RAISE ValidationError
E   AssertionError: assert None == 'false'
FAILED tests/test_f016_settings.py::test_f016_r4_la_llave_de_origen_arranca_cerrada
FAILED tests/test_f016_settings.py::test_f016_r4_se_lee_de_su_alias_como_booleano[true-True]
FAILED tests/test_f016_settings.py::test_f016_r4_un_valor_que_no_es_booleano_no_arranca[quizas]
10 failed, 1 passed in 2.01s (la que pasa: ninguna existente cambia)
```

**T6** `python -m pytest tests/test_f016_statements.py -q`:
```
tests/f016_dobles.py:26: in <module>
    from application.use_cases.proforma_origen_statements import ProformaOrigenStatements
E   ModuleNotFoundError: No module named 'application.use_cases.proforma_origen_statements'
ERROR tests/test_f016_statements.py
1 error in 2.57s
```

**T8** `python -m pytest tests/test_f016_use_case.py -q` (motivos agrupados con `grep "^E  " | sort | uniq -c`):
```
FAILED tests/test_f016_use_case.py::test_f016_r8_r13_previa_de_una_primera
FAILED tests/test_f016_use_case.py::test_f016_r11_r12_previa_encadenada_lee_y_escribe_la_cadena
FAILED tests/test_f016_use_case.py::test_f016_r5_existente_antes_de_validar_la_anterior
FAILED tests/test_f016_use_case.py::test_f016_r7_anterior_con_sucesora - Fail...
FAILED tests/test_f016_use_case.py::test_f016_r9_los_fallos_de_r9_y_de_la_etapa_1_juntos
FAILED tests/test_f016_use_case.py::test_f016_r14_tope_con_las_arrastradas_aun_en_previa
20 failed, 9 passed, 1 warning in 1.66s
      6 E       Failed: DID NOT RAISE AlbaranCompraError
      3 E       AssertionError: assert <class '...ProformaResponse'> is ProformaOrigenResponse
      2 E       KeyError: 'modo'
      1 E       domain.models.proforma_models.ProformaError: El contrato ya tiene proforma de este mes con otro importe: PROF26/00401. ...
      1 E       AssertionError: assert ['cod_provisi...ato_a_origen'] == ['cod_provisi...to_de_sigrid']
```
Las 9 que pasan son las de R1 (mes) y las que solo miran errores de F-007 (`importe_mes_no_cuadra`, `proforma_del_mes_existente`).

**T10** `python -m pytest tests/test_f016_transaccion.py -q` (T9 ya hecha: la parte de fuera pasa):
```
E       AssertionError: assert ['referencia'...rprodes', ...] == ['referencia'..._dcapro', ...]
E         At index 2 diff: 'reservar_cod' != 'lp8_sucesoras'
E       assert [] == [[14, 2793879, 2850201]]
E       Failed: DID NOT RAISE ProformaOrigenError
E       domain.models.proforma_models.ProformaError: El contrato ya tiene proforma de este mes con otro importe: PROF26/00401. Si es una segunda, otra_del_mes.
FAILED tests/test_f016_transaccion.py::test_f016_r18_orden_de_las_sentencias_y_applocks_de_f015
FAILED tests/test_f016_transaccion.py::test_f016_r17_lp8_por_el_cursor_tras_lp1
FAILED tests/test_f016_transaccion.py::test_f016_r17_sucesora_aparecida_dentro_no_escribe
FAILED tests/test_f016_transaccion.py::test_f016_r17_a_origen_del_mes_con_otro_total_aparecida_dentro_sigue
FAILED tests/test_f016_transaccion.py::test_f016_r18_reintento_reentrante_con_las_mismas_filas
5 failed, 7 passed, 1 warning in 2.25s
```

**T12** `python -m pytest tests/test_f016_route.py -q` (R3 y los códigos ya pasan por T2/T5; falta la llave):
```
>       assert estado == 400
E       assert 200 == 400
tests\test_f016_route.py:90: AssertionError
FAILED tests/test_f016_route.py::test_f016_r4_commit_a_origen_con_la_llave_cerrada_antes_del_caso_de_uso
1 failed, 15 passed, 1 warning in 1.82s
```

## T13-T14 (resumen; detalle en los commits y en `mutacion_F-016.md`)

- **T13** (`93bbce3`, `06ffcb6`): llave `SIGRID_PROFORMA_ORIGEN_ENABLED` en `function_app.py` tras la de F-007 y antes
  del caso de uso; imports de los tests nuevos ordenados con ruff. `git diff dev` de los tests de F-007/F-009/F-015 y
  de `fixtures/f009_caracterizacion.json`: vacío.
- **T14** (`eca4629`): campaña completa, **116 mutantes, 102 muertos, 14 supervivientes**; 13 eran huecos reales y
  tienen test nuevo (`test_f016_t14_*`), medidos muertos con él; el 4 era un falso superviviente de la campaña
  (aplicado a mano: `1 failed`). **0 supervivientes no aceptados**, ningún equivalente. Ver
  [`mutacion_F-016.md`](mutacion_F-016.md).

## T15 · Documentación (R25)

- `specs/F-007-registrar-proforma/contrato_proformas.md` → **v1.2**: campos nuevos (§2.1 con la nota ³ de las
  combinaciones que dan 400 sin `codigo`, §2.2 `linea_anterior`), **§2.3** con las dos consultas `sql/read` completas
  (puntas a origen del contrato con su importe de cadena, la de M44 con `NOT EXISTS` de sucesora; líneas de la punta
  con partida y producto) y lo que comprueba la API, §3.1 respuesta a origen, §4 códigos nuevos con qué hace
  `proformas`, §6 `facturas`, §7 y §8. Compatible hacia atrás.
- `docs/ARCHITECTURE.md`: capas (`proforma_origen_models`, `proforma_origen_statements`) y sección propia del modo.
- `CLAUDE.md`: solo la línea del mapa de `function_app.py` (`sigrid/proforma` de mes o a origen).
- `azure-apps/sigrid_api.md`: `3744877` (de la sesión anterior) revisado contra R25: App Setting en §4.1, punto 10 de
  §7, tabla de escrituras, §8.10.1 (remite a §2.3 del contrato, que ya existe), consumidores `proformas` y `facturas`
  y §13. Faltaba una cosa: el riesgo de despliegue de §8.10 seguía diciendo «cinco» App Settings; corregido en
  **`7afe9e9`** (seis; la booleana tampoco arranca con un valor malo; enlace a la verificación manual de F-016).
- `local.settings.sample.json`: hecho en T5.
- **PENDIENTE (humano/líder; no se ha llamado a la red)**: probar en lectura las dos consultas de §2.3 sobre una cadena
  real (T15 «Verificación»). Están en `verificacion_manual.md` V2 listas para lanzar.

### Aviso a `proformas` (lo envía el líder)

> sigrid-api F-016 (implementada, pendiente de revisión y de despliegue): `POST /api/sigrid/proforma` registra también
> proformas **a origen**. El contrato pasa a **v1.2** (`sigrid-api/specs/F-007-registrar-proforma/contrato_proformas.md`)
> y es **compatible hacia atrás**: sin `modo` todo sigue como la v1.1 y la respuesta no trae claves nuevas, así que no
> tenéis que cambiar nada para seguir registrando de mes.
> Para registrar a origen (cuando el jefe de obra lo indique al cargar la proforma): mandad `modo: "origen"` y
> **exactamente uno** de `proforma_anterior` (`con.cod` de la anterior) o `primera_de_cadena: true`, y en cada línea que
> continúe una de la anterior su `linea_anterior` (`dcapro.ide`). **Elegirlos es vuestro**: la API no busca ni deduce,
> solo valida que la anterior es del contrato, a origen, no posterior y la punta, y que cada `linea_anterior` es de ella
> y del mismo `ctrpro`. Las dos lecturas `sql/read` para enseñar a la persona las puntas (con la sugerencia por el
> ANTERIOR de la hoja) y las líneas de la elegida están escritas en §2.3. Las líneas de la anterior que no continuéis
> las arrastra la API a 0. Respuesta a origen: `cadena` e importes de cadena para cotejar con la hoja (§3.1). Códigos
> nuevos (§4): `anterior_no_valida`, `anterior_con_sucesora`, `linea_anterior_no_valida`,
> `escritura_proformas_origen_deshabilitada` (la grabación a origen tiene llave propia, que se despliega cerrada) y el
> aviso `linea_nueva_ya_en_la_anterior`. `contrato_a_origen` ya solo sale en las de mes. Ni a origen sin contrato ni
> con la anterior en otro contrato. Os avisamos cuando esté desplegada.

### Aviso a `facturas` (lo envía el líder)

> sigrid-api F-016 (implementada, pendiente de despliegue): `sigrid/proforma` podrá registrar proformas **a origen**
> (`dca.docoritip` 1). No cambia nada de lo que la API expone para vosotros ni el contrato de lectura (`dca.entref`
> `PROF<MMAA>_<cod_obra>`, serie `PROF<aa>/` o `AC<aa>/`), pero una proforma a origen trae **todas** las líneas de la
> cadena: las arrastradas de la anterior con `can` 0 y `tot` 0, y `dca.totbas` sigue siendo **el MES**. Al leer sus
> `dcapro` por `docide`, **solo pasan a factura las de `can` ≠ 0**; las columnas a origen (`canoriori`, `canorilin`) no
> son el importe del mes. Al facturar una a origen, el escritorio pone `canoriant`/`imporiant` en la `dcfpro`: si
> llegáis a registrar facturas por la API (F-008 de sigrid-api), se tratará allí. Detalle: §6 de
> `sigrid-api/specs/F-007-registrar-proforma/contrato_proformas.md` v1.2 y §8.10.1 de `azure-apps/sigrid_api.md`.

## T16 · Verificación manual

[`verificacion_manual.md`](../specs/F-016-proforma-a-origen/verificacion_manual.md), con el modelo de F-007: V0 (las
dos consultas de §2.3 copiadas tal cual, `truncated` = parar), D1-D3 (App Setting `false` validada con `Settings`,
publish con `!`, dry-run de `sigrid/albaran` primero), V1-V6 (llaves, puntas y líneas con tiempos, `existente`, la del
mes siguiente encadenada, aviso R10, sin `modo` = F-007, `anterior_con_sucesora`/`anterior_no_valida`/
`linea_anterior_no_valida`) y G1-G3 en la 0404 (la llave de origen se mira tras la de F-007; primera y encadenada con
una arrastrada; lecturas de `ctrprodes`, `mov` y `canser`; V9 en la UI y anulación en orden inverso). Sin URL ni clave
(variables de entorno; comprobado con `grep`). **No ejecutado**: es MANUAL (T17-T18, humano/líder).

## Qué queda fuera y qué falta

- **Fuera (spec §Fuera de alcance)**: elegir modo, anterior y continuaciones (del llamante, contrato §2.3); a origen sin
  contrato o con la anterior en otro contrato; sembrar el origen; `ctrprodes`/`mov` de las arrastradas (D6); F-017.
- **MANUAL pendiente (humano/líder)**: las dos consultas de §2.3 en lectura sobre una cadena real (verificación de T15,
  V2); T17 (despliegue con la llave `false` y previas V1-V6) y T18 (G1-G3 y V9 en la UI, con autorización expresa).
- **Líder**: enviar los dos avisos de arriba; T19 (reviewer) y marcar T20 al cierre.
- Ronda de correcciones de la revisión (solo texto): §2.3 sin «medidas así», orden de errores a origen en §4, regla de parada en G, nota en T15.

## Evidencias (T20, 2026-10-28, `bash harness/init.sh` tal cual)

| Evidencia | Valor real |
|---|---|
| Resultado de `bash harness/init.sh` | **ENTORNO LISTO** (avisos previos: F-015 `blocked`, 158 de ruff de deuda previa) |
| Tests de la suite | **3549 passed, 1 skipped**, 1 warning (el de `DocumentReadRequest.schema`, previo) |
| Tests de F-016 | 116 funciones en `tests/test_f016_{models 23, route 8, settings 6, statements 39, transaccion 12, use_case 28}.py` |
| Cobertura de líneas cambiadas | **PUERTA COBERTURA: 100.0 % de 270 líneas (270/270, umbral 80 %, nivel critico)** |
| Mutación | **116 generados, 102 muertos, 14 supervivientes → 13 con test nuevo y medidos muertos, 1 falso de la campaña; 0 no aceptados** ([`mutacion_F-016.md`](mutacion_F-016.md)) |
| Tiempo de la suite | 199,23 s (3 min 19 s) |
| Tamaño | PUERTA TAMAÑO: requirements 118/150, design 186/250, impl 151/220 (antes de esta sección) |
| R1/R2 | `git diff dev` de los tests y dorados de F-007/F-009/F-015, del núcleo de F-009, de `proforma_statements.py` y de `infrastructure/`: **vacío** |
