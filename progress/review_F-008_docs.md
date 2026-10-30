Revisión completa (pasada 1), trozo `docs`: `ccfb334..2879ddb` en sigrid-api y `a2127a6` en azure-apps
<!-- progress/review_F-008_docs.md -->
# F-008 · Revisión troceada (T21) · trozo `docs`

**Veredicto: CHANGES_REQUESTED**

**Nivel de rigor:** `critico` (declarado). Este trozo no evalúa puertas de RED, cobertura ni mutación (son de otros
trozos); aquí solo documentación y contratos, cotejados con el código real de HEAD `2879ddb`.

**Alcance mirado:** `docs/ARCHITECTURE.md`, `CLAUDE.md`, `local.settings.sample.json`,
`specs/F-008-registrar-factura/verificacion_manual.md`, `progress/impl_F-008.md` (desviación 1) y
`azure-apps/sigrid_api.md` en `a2127a6` (más el delta `a2127a6..HEAD` de ese repo, que solo toca Application Insights
—`9ff6ac6`— y la fila de `facturas` —F-078—; ninguno contradice F-008). Contrastado con `config/settings.py:158-180`,
`function_app.py:394-479`, `domain/models/factura_models.py` y `application/use_cases/create_factura_use_case.py`.

**FUERA (N/A con motivo):** C1-C5, C3 bis y C4 bis: los cubren los otros seis trozos por encargo del líder.
`bash harness/init.sh`, suite y mutación: prohibidos en este encargo por convivencia con revisores en paralelo.

## Lo que está bien (verificado contra el código)

- [x] `CLAUDE.md:82-83` y `docs/ARCHITECTURE.md:33-34, 45-46, 58-59, 69-70, 230-266`: ruta, `factura_models`,
  `factura_lineas`, `factura_statements`, `create_factura_use_case`, orden de applocks (= `APPLOCKS_FACTURA`,
  `factura_statements.py:323-333`), `UPDLOCK, HOLDLOCK`, `pag` con `ide` de su `con`, llave tras validar y antes del caso
  de uso (`function_app.py:423`), 400 sin `input` ni `ctx` (`function_app.py:440-454`). Coherente con design v3.1.
- [x] Siete ajustes `SIGRID_FACTURA_*`: nombres y defectos de `settings.py:165-180` = `local.settings.sample.json:62-68`
  = tabla §4 de `azure-apps/sigrid_api.md` (`false`, `[]`, `500`, `[]`, `{}`, `[]`, `[]`). Listas y mapeo en JSON
  (`parse_string_list`, `parse_string_dict`), como dice §4. Sin valores reales en el sample.
- [x] Códigos de §8.11: los 32 coinciden uno a uno con `CODIGOS_FACTURA` (`factura_models.py:25-58`).
- [x] Campos de §8.11 coinciden con `FacturaRequest` (`factura_models.py:135-152`): longitudes, `vencimientos` 1-12,
  números estrictos, campos por serie (`CAMPOS_FR`/`CAMPOS_FRGG`), tolerancias ±0,001/±0,01/±0,05 y 730 días
  (`factura_lineas.py:65,195`; `create_factura_use_case.py:97-98`).
- [x] §7.11: la doble puerta (ruta + `SIGRID_DOMAIN_WRITE_ENABLED`, credenciales y `ALLOWED_WRITE_DATABASES` no vacía)
  es real: `create_factura_use_case.py:327-345`.
- [x] Sin secretos: nada de hosts, claves ni IDs en lo añadido; la URL y la clave de `verificacion_manual.md:19-22` van en
  variables de entorno de la consola.
- [x] Desviación 1 (sin `.env.example`): aceptada. `git ls-files` confirma que no existe en el repo (el `.env` local no
  está versionado); design §4 lo nombraba por error y las siete viven en el sample y en §4 de azure-apps.
- [x] `verificacion_manual.md`: nunca `DELETE` (l.13, l.146), anulación en la UI (V4, l.144), una autorización expresa
  por llamada y previa repetida antes de cada grabación (l.107-108), `commit = $true` en G1 solo sobre el cuerpo ya
  previsto (l.112), obra 0404 para FR (l.111, = T24), lecturas por `sql/read` con `truncated` = parada (l.31-34),
  ningún SQL directo. Las filas de `sql/read` son listas (`sql_models.py:69`): columnas sin nombre no colisionan.

## Hallazgos que bloquean

1. **[ ] T23 no puede salir verde tal como está escrito.** `verificacion_manual.md:53-54` dice «**No** se tocan App
   Settings»; con eso `SIGRID_FACTURA_PREFIJOS_REFERENCIA` vale `[]` y **toda** previa acaba en `referencia_no_permitida`
   (`create_factura_use_case.py:321-326`, antes de mirar `commit`), y con `_IVAS`, `_PRODUCTOS_SIN_ORIGEN`,
   `_NATURALEZA_POR_PRODUCTO` y `_CUENTAS_GASTO_PREFIJOS` vacíos P3, P4, P5 y P7 caen en `lineas_no_validas`. Además
   contradice a `azure-apps/sigrid_api.md` §8.11 (aviso de cabecera: «Al desplegar: las siete App Settings
   `SIGRID_FACTURA_*` con la llave **cerrada**»). **Pido:** que D1 diga que se cargan las seis ajustes no-llave con los
   valores de design §4, en JSON y literales, p. ej.:
   `SIGRID_FACTURA_PREFIJOS_REFERENCIA=["FAC-"]`, `SIGRID_FACTURA_PRODUCTOS_SIN_ORIGEN=["MA9999","SM9999","SB9999","QA9999","XA9999","SM370001"]`,
   `SIGRID_FACTURA_NATURALEZA_POR_PRODUCTO={...}` (el mapeo concreto, o remitir al de `SIGRID_ALBARAN_NATURALEZA_POR_PRODUCTO`
   si es el mismo), `SIGRID_FACTURA_IVAS=["I21","I10","ISP21","i0","i4","I21NDED","I10NDED"]`,
   `SIGRID_FACTURA_CUENTAS_GASTO_PREFIJOS=["6"]`; y `SIGRID_FACTURA_WRITE_ENABLED` ausente o `false`. Que conste que
   `FAC-` sigue pendiente de confirmar con `facturas` (P15).
2. **[ ] La `referencia_externa` de las previas y grabaciones no tiene formato.** `verificacion_manual.md:84-85` solo
   dice «nueva por previa». Con el único prefijo `FAC-` compartido con la app `facturas`, una referencia de prueba mal
   elegida pisaría su idempotencia (design §8, «Varios llamantes»). **Pido:** fijar el formato, p. ej.
   `FAC-VERIF-F008-<previa>-<n>`, y anotarlo junto a `con.ide` en `progress/verificacion_F-008.md`.
3. **[ ] D2 y T24.5 son un `commit: true` a ciegas contra producción.** `verificacion_manual.md:55-56` («`Factura` con
   **cualquier** cuerpo válido y `commit = $true`») y l.115 («repetir D2») confían en que la llave está cerrada sin
   comprobarlo. Si alguien la hubiera dejado abierta, un cuerpo válido con prefijo admitido escribiría una factura.
   **Pido:** (a) antes de D2, una lectura de App Settings (`az functionapp config appsettings list`, solo lectura) que
   confirme `SIGRID_FACTURA_WRITE_ENABLED` ausente o `false`; (b) un cuerpo **fijo y escrito en el documento** cuya
   `referencia_externa` lleve un prefijo **no admitido** (p. ej. `NOADMITIDA-D2`), de modo que, abierta la llave, la
   respuesta fuera `referencia_no_permitida` sin escribir nada (`create_factura_use_case.py:321-326`, antes de cualquier
   escritura) y nunca `creado`.
4. **[ ] `azure-apps/sigrid_api.md:1524` y `:1526`: llaves dobles** `{{linea: dcapro.ide, canoriori, imporiori}}` y
   `{{fecha, importe}}`. Restos de un f-string: el contrato publicado dice otra cosa que el JSON real. **Pido:**
   `{linea: dcapro.ide, canoriori, imporiori}` y `{fecha, importe}`.
5. **[ ] §8.11 «Respuesta» incompleta.** Faltan `database`, `committed`, `dry_run` y `referencia_externa`, que sí devuelve
   `FacturaResultado` (`factura_models.py:223-239`); la propia `verificacion_manual.md:62` comprueba `committed = false`.
   **Pido:** «**Respuesta:** `database`, `estado` (…), `committed`, `dry_run`, `cod`, `con_ide`, `serie`, `modo`,
   `referencia_externa`, `totales`, …».
6. **[ ] §8.11 calla dos cosas que el consumidor necesita.** (a) Los 11 códigos de línea dentro de
   `lineas_no_validas` (`CODIGOS_LINEA_FACTURA`, `factura_models.py:61-73`: `iva_no_valido`, `producto_no_permitido`,
   `producto_no_encontrado`, `naturaleza_no_valida`, `analitica_no_resuelta`, `partida_no_encontrada`,
   `partida_no_imputable`, `partida_ambigua`, `paride_no_valido`, `cuenta_no_valida`, `analitica_no_valida`), con la forma
   `{indice, codigo, mensaje}`. (b) Que la obra se busca en `SIGRID_ALBARAN_EMPRESAS_OBRA`
   (`create_factura_use_case.py:404-406, 440`), igual que F-007 lo dice en §4 (l.411). **Pido:** una frase para cada uno
   en §8.11.

## Sugerencias (no bloquean)

- `verificacion_manual.md:66`: el comentario de C0 («último `con` de factura FR y FRGG») no describe la consulta. Y C0
  no mira `log`, `consii`, `dcf` ni `dcaprodes`: añadir sus `MAX(ide)` cerraría el «no se escribió nada».
- `verificacion_manual.md:74`: la consulta de albaranes no filtra por obra; G1 exige la 0404 (l.111). Una variante con
  `d.obride` de la 0404 evita elegir a ojo. G2 (l.114) no dice obra.
- `verificacion_manual.md:90` (P2): falta la lectura de donde salen `canoriori`/`imporiori` que se mandan en `a_origen`.
- `CLAUDE.md:89` habla de «las tres altas de dominio» en `application/use_cases/`; ya son más. Previo a F-008.

## Cobertura (trozo docs)

| Requisito / tarea | Dónde se cumple | Estado |
|---|---|---|
| R48 / T18 (docs en el mismo trabajo) | `CLAUDE.md`, `ARCHITECTURE.md`, azure-apps `a2127a6` | [x] con hallazgos 4-6 |
| R4 (llave propia) documentada | §4, §7.11, §8.11 de azure-apps; `ARCHITECTURE.md:259-261` | [x] |
| R1 (400 sin eco) documentado | §8.11; `ARCHITECTURE.md:69-70`; D3 | [x] |
| T22-T24 ejecutables y seguros | `verificacion_manual.md` | [ ] hallazgos 1-3 |
| Ajustes en sample / `.env.example` | `local.settings.sample.json:62-68`; desviación 1 | [x] |

## Automejora (propuesta, no aplicada)

Añadir a `CHECKPOINTS.md` (C5 o documental): «Toda `verificacion_manual.md` que lance un `commit: true` para comprobar
una llave cerrada usa un cuerpo que no podría escribir aunque la llave estuviera abierta, y lee antes las App Settings».
Vale para cualquier proyecto con llaves de escritura: candidata a `arnes-base`.
