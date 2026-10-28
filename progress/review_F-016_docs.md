<!-- progress/review_F-016_docs.md -->
Revisión completa (pasada 1) del bloque de documentación y verificación manual (R24, R25), sobre HEAD `c08461f`

# F-016 · Revisión troceada: documentación y verificación manual (R24, R25)

- **Veredicto:** CHANGES_REQUESTED (dos cambios pequeños, solo de texto; el código no se toca)
- **Nivel de rigor:** `critico` (declarado en `harness/features.json`). Este encargo no cubre puertas de tests,
  cobertura ni mutación: van en otros trozos de la revisión. Aquí, por encargo, ni `init.sh` ni tests ni red.
- **Alcance:** `contrato_proformas.md` v1.2, `docs/ARCHITECTURE.md`, el mapa de `CLAUDE.md`,
  `local.settings.sample.json`, `azure-apps/sigrid_api.md` (`3744877`, `7afe9e9`; solo lectura),
  `verificacion_manual.md` (T16) y los avisos a `proformas` y `facturas` de `impl_F-016.md` (T15).
  Ajenos y no revisados: `1733c2f` (backlog F-018) y `.claude/worktrees/`.

## Checkpoints de este bloque

- [x] **Contrato v1.2 frente a design §Contrato v1.2.** Campos (`modo`, `proforma_anterior` 1-24,
  `primera_de_cadena`, `linea_anterior` entero ≥ 1 estricto) coinciden con `ProformaRequest`/`LineaProformaIn`; la
  nota ³ recoge las seis combinaciones de `_reglas_de_origen` (400 sin `codigo`). Respuesta §3.1 coincide con
  `CadenaProforma`, `LineaProformaOrigenResultado` y `_a_origen`/`_linea_arrastrada` (`cadena` nula en `existente` e
  `idempotente`; `cantidad_anterior_cadena` 0.0 en las nuevas; arrastradas detrás con `refent`, `can`/`tot`/`ivacuo`/
  `prepma` 0, `canorilin` = su `ide`). Códigos de §4 = `CODIGOS_*_PROFORMA_ORIGEN` (3 de cabecera, 1 de línea, 1 aviso),
  con qué hace `proformas`; orden de llaves = `function_app.py`; `demasiadas_lineas` con arrastradas y en previa =
  `_cadena`; `otra_del_mes` a origen = `buscar_del_mes_origen`; `contrato_a_origen` filtrado a origen = R16.
- [ ] **Las dos consultas de §2.3.** SQL correcto y coherente (ver «Consultas»), pero el texto afirma una medición
  que no existe → cambio 1.
- [x] **§6 `facturas` y §8 cambios.** Correctos frente a D13 y al código; §7 quita «proformas a origen» de lo que no hace
  y lista lo que sigue fuera (D6, D7, otro contrato).
- [x] **`docs/ARCHITECTURE.md`.** Capas, subclases, LP7-LP9, arrastradas al final de `filas.dcapro`, LP8 bajo el
  applock, llave en la ruta y traza (`modo`, `primera_de_cadena`, `anterior`, `n_continuadas`, `n_arrastradas`) =
  código.
- [x] **Mapa de `CLAUDE.md`** (`sigrid/proforma` de mes o a origen) y **`local.settings.sample.json`**
  (`SIGRID_PROFORMA_ORIGEN_ENABLED` `"false"`, = `Field(False)` de `settings.py`).
- [x] **`azure-apps/sigrid_api.md`** (`3744877` + `7afe9e9`): §4.1 App Setting, §7 punto 10 (`details.type`
  `ProformaOrigenError` = `type(exc).__name__` en `_respuesta_albaran_compra_error`), tabla de escrituras, tabla de
  rutas, §8.10.1, consumidores `proformas` y `facturas`, §13 y el riesgo de despliegue con **seis** App Settings.
  Todo coincide con el código y no duplica el contrato (enlaza a §2.3).
- [ ] **`verificacion_manual.md` (T16).** Sin clave ni URL (variables de entorno; la clave sale de `az ... keys list`
  a una variable), anulación desde la UI en orden inverso, nunca `DELETE`, autorización por cada `commit:true`,
  `otra_del_mes` en G para no caer en `existente`. Falta el cierre de llaves si algo se tuerce → cambio 2.
- [x] **Avisos a `proformas` y `facturas`.** Claros, correctos frente al código y sin secretos (una precisión
  opcional en «Observaciones»).
- [x] **Sin secretos, nombres de personas ni CIF.** Búsqueda en las líneas añadidas de todos los ficheros del bloque y
  de los dos commits de `azure-apps` (patrones de CIF/NIF, URL, `azurewebsites`, `code=`, GUID, IP privada,
  contraseñas): cero coincidencias reales (solo «8.10.1.»). El CIF de D3 se lee a una variable y no se escribe. Los
  códigos de la 0404 (`CTSU16/0206`, `ctrpro` 258782/258783) y el usuario `prueba` son los de la obra de pruebas, como en
  F-007.

## Consultas de §2.3 (contra LP7/LP8/LP9 y `azure-apps/sigrid_tablas.md`)

| Comprobación | Resultado |
|---|---|
| Marcadores `?` y orden de parámetros | Consulta 1: 4 `?` en el orden `c.tip`, `d.ctride`, `d.docoritip`, `cs.tip` = `[14, <ctride>, 1, 14]`. Consulta 2: 1 `?` = `[<ide>]`. Sin concatenación |
| Coherencia con LP8 | La «punta» de la consulta 1 (`NOT EXISTS` de un `tip 14` del mismo `ctride` con `docoriide` = su `ide`, sin filtrar el `docoritip` de la sucesora) es exactamente la negación de LP8: lo que `proformas` ofrece como punta no da `anterior_con_sucesora` |
| Coherencia con LP7/R6 | La consulta 1 filtra `docoritip 1` y el contrato, como R6; el `fec` lo deja a la persona y el texto lo avisa |
| Coherencia con LP9/R9 | La consulta 2 lee `dcapro` por `docide` en `ORDER BY pos, ide`, como LP9; casar por `linoriide` = `ctrpro_ide` (o 0 sin vincular) es la regla de `validar_continuadas` |
| Columnas en `sigrid_tablas.md` | `dca`: `ctride`, `totbas`, `docoritip`, `docoriide`. `dcapro`: `ide`, `docide`, `pos`, `linoriide`, `docoritip`, `paride`→`obrparpar`, `proide`, `res`, `unimed`, `pre`, `can`, `canoriori`. `obrparpar.cod`. Producto por `con` como LP1/LP6 |
| Guardia de `sql/read` | `SELECT` inicial, sin palabras prohibidas (`EXISTS`, `ISNULL`, `ROUND` pasan), sin `;` en el SQL, bases permitidas |
| Copia en V0 | `$SQL_PUNTAS` y `$SQL_LINEAS` = las del contrato, carácter a carácter salvo los saltos de línea |

## Cambios requeridos

1. **`specs/F-007-registrar-proforma/contrato_proformas.md`, §2.3, primer párrafo** («Las dos consultas son
   orientativas (`proformas` las adapta), pero están medidas así sobre cadenas reales (M44 …: ~4 s por contrato)»).
   No es cierto tal cual: M44 de `progress/explore_F-016.md` midió la lectura de la cadena **sin** el `NOT EXISTS` de
   sucesora, y la consulta 2 no se ha medido; la propia `impl_F-016.md` (T15) dice que probarlas en lectura está
   **PENDIENTE** (V2 de la verificación manual). Es el contrato vivo que lee otro equipo: que diga lo que hay, por
   ejemplo «la 1 deriva de la medida en M44 (~4 s por contrato, sin el `NOT EXISTS`); las dos se prueban en lectura en
   la verificación de F-016 (V2) antes del despliegue», y retirar «medidas así» hasta que V2 lo confirme.
2. **`specs/F-016-proforma-a-origen/verificacion_manual.md`, §G.** La llave solo se cierra al final de G3 (camino
   feliz). Si G1 no da `escritura_proformas_origen_deshabilitada` con `count` 0, si G2 no da `creado`/`idempotente`
   o si G3 se tuerce, el texto no dice qué hacer y las llaves (`SIGRID_PROFORMA_WRITE_ENABLED` desde G1, la de origen
   desde G2) quedarían abiertas en producción. Pedido: crear `f016_cerrar.json` **antes** de G1 y añadir una regla
   explícita «ante cualquier resultado distinto del esperado en G1-G3, lo primero es cerrar las dos llaves
   (`f016_cerrar.json`) y parar; se anota en `progress/verificacion_F-016.md`». Es lo que pide R24/T18 («la llave
   abierta solo para ello … y cerrar la llave»).

## Observaciones (no bloquean)

- **Comentario con `;` en la consulta 2** del contrato (`-- parameters: … (max_rows ≥ nº de líneas; ver truncated)`):
  si `proformas` copia el bloque tal cual, `SqlQueryGuard._contains_multiple_statements` lo rechaza («una única
  sentencia») porque solo se quitan los comentarios del principio. Mejor sacar la nota de parámetros fuera del bloque
  `sql`, o quitar el `;`.
- **`<ctride>` «que devuelve la previa»** (§2.3): para obtenerlo, la previa tiene que ser válida, así que a origen
  necesita ya `proforma_anterior` o `primera_de_cadena`. Precisar «`contrato.ide` de una previa (de mes o con
  `primera_de_cadena`)» o «el del `cod_contrato`», que ya se menciona.
- **Aviso a `proformas`**: «cada `linea_anterior` es de ella y del mismo `ctrpro`» podría añadir «(o sin vincular,
  si la línea es nueva sin vincular)», como dice §2.3.
- **T15 marcada `[x]`** con su verificación («las dos consultas probadas en lectura sobre una cadena real») pendiente.
  El informe lo dice con claridad y la traslada a V2; que el líder lo deje explícito en `tasks.md` o en
  `current.md` (verificación de T15 = V2 de T17) para que no se cierre la feature sin ella.
- **G1 abre `SIGRID_PROFORMA_WRITE_ENABLED` en producción**: durante G1-G3 cualquier llamante con clave puede grabar
  proformas de mes. Igual que en F-007 T22 y aceptado entonces; conviene que el humano lo tenga presente al elegir la
  hora.

## Cobertura del bloque (requisito → evidencia)

| Requisito | Evidencia |
|---|---|
| R25 contrato v1.2 | `contrato_proformas.md` §1, §2.1-§2.3, §3.1, §4, §6, §7, §8 (cambio 1 pendiente) |
| R25 `azure-apps` | `3744877`, `7afe9e9` en `azure-apps/sigrid_api.md` |
| R25 ARCHITECTURE, CLAUDE.md, sample | diff de `dev...HEAD` de los tres ficheros |
| R25 avisos (D13) | `progress/impl_F-016.md` §T15, «Aviso a `proformas`» y «Aviso a `facturas`» |
| R24 (MANUAL) | `verificacion_manual.md` D1-D3, V0-V6, G1-G3, V9 (cambio 2 pendiente); sin ejecutar, como corresponde a T17-T18 |

## Propuesta de automejora (para el humano; no aplicada)

- `CHECKPOINTS.md`/`reviewer.md`: en las verificaciones manuales con escritura, exigir una línea de **«cierre ante
  fallo»** (qué llaves cerrar y cómo) además del cierre del camino feliz. F-007 y F-016 solo traen el segundo.
- Al documentar una consulta para otro equipo, prohibir anotaciones dentro del bloque `sql` que el guardia de
  `sql/read` rechazaría si se copian (`;`, comentarios a mitad).
