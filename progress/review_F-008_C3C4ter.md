# progress/review_F-008_C3C4ter.md

Revisión completa (pasada 1) · trozo `C3C4ter` · rama `feature/F-008-registrar-factura`, HEAD `2879ddb9c6ba2b05a6974fd5c13216450065228e`,
diff `git diff ccfb334...HEAD` (28 ficheros, +8.904 / -11).

## Veredicto: CHANGES_REQUESTED

Un solo hallazgo bloqueante, de la lista de trampas de Sigrid que C3 obliga a vigilar SIEMPRE: el `con.est` de los
pagos (`tip 25`) va **escrito a mano como `1`** y no se resuelve ni se comprueba contra `dbo.conest` (hallazgo H1).
El resto de C3, C3 bis y las verificaciones extra pedidas por el líder están en verde.

## Nivel de rigor

`critico` (declarado en `harness/features.json`). Este trozo no evalúa sus puertas (RED, cobertura, mutación: C4 bis,
otro revisor). Alcance: C3, C3 bis y C4 ter + verificaciones extra del encargo. Sin `bash harness/init.sh` ni suite
completa (regla de convivencia): solo `pytest` de ficheros concretos y `ruff` sobre ficheros.

## C3 — Arquitectura y convenciones

- [x] **Hexagonal.** `domain/models/factura_models.py` solo importa stdlib y pydantic. `application/` no importa
      repositorios: el caso de uso recibe el repositorio por inyección (`function_app.py`, `CreateFacturaUseCase(repository,
      settings)`). `factura_statements.py:38` importa `infrastructure.security.database_reference_guard`: es el patrón
      vigente y documentado (`albaran_compra_statements.py:39`, `proforma_statements.py:40`,
      `parte_reclamacion_statements.py:30`; `docs/ARCHITECTURE.md:252` ya lo describe para F-008). No es regresión.
- [x] **Primera línea con la ruta** en los 15 `.py` del diff (comprobado uno a uno con `head -1`).
- [x] **Sin `print`/`breakpoint`/TODO sin contexto** en código ni tests de F-008 (grep). **Sin secretos**: ver C4 ter.
      **Sin dependencias nuevas**: `requirements*.txt` y `pyproject.toml` no están en el diff.
- [ ] **Reglas de dominio de Sigrid** (`docs/ARCHITECTURE.md`):
  - [x] **Base correcta.** Escritura solo si `request.database ∈ ALLOWED_WRITE_DATABASES`
        (`create_factura_use_case.py:341`; lista vacía no abre). Cero referencias a `ruesma_rep` en el código nuevo; toda
        sentencia pasa por `DatabaseReferenceGuard.validate(..., allowed=[self.database])` (`factura_statements.py:528`).
  - [x] **`cod/res/fec/tip/est` en `con`.** Medido sobre `INSERTS`: `dcf` (145 columnas), `dcfrec`, `pag`, `dcaprodes`
        no llevan ninguna; `con` sí (correcto). `dcfpro.fec/res`, `consii.est` y `log.*` son columnas propias de línea,
        de SII y de bitácora (listas de T0 medidas), igual que en el precedente `LOG_COLUMNAS` de F-009.
  - [x] **Nada se recalcula solo.** El alta escribe totales de `dcf`, `pag`, `consii`, `dcaprodes`, marca los orígenes
        (`EM3_ESTADO`, `dca.estfac/fecfac/horfac/antestfac`, `ctrpro.canfac`, `ctr.estfac`) y los relee antes del COMMIT
        (R45). La corrección fina de cada cifra es de los revisores de lógica.
  - [ ] **Estados nunca hardcodeados.** Factura (REC/RECGG/RECH) y origen (CON/FAC) se resuelven contra `conest`
        (`create_factura_use_case.py:368-379`). **El pago no**: ver H1.
  - [x] **SQL parametrizado con `?`.** Todas las sentencias son constantes con `?`; los únicos `f"..."`/`.format` que
        tocan SQL interpolan listas de columnas constantes, marcadores `?` generados por `_marcadores(n)` y el nombre de
        tabla de la constante `TABLAS_CON_IDE` (`factura_statements.py:374-462, 534, 550, 635`). Ningún valor de la
        petición se concatena.

## C3 bis — Documentos que entran de fuera

N/A, justificado: el diff no añade ni modifica nada en `docs/referencia/`
(`git diff --name-only ccfb334...HEAD | grep docs/referencia` vacío). Comprobado además que ninguna rama del historial
añade originales: `git log --diff-filter=A --name-only ccfb334..HEAD | grep -iE '\.(pdf|docx?|xlsx?|pptx?)$'` vacío.

## C4 ter — Rutas sensibles

Formalmente **N/A, justificado**: el repositorio no declara `harness/rutas_sensibles.json` (solo existen
`rutas_sensibles.ejemplo.json` y `rutas_sensibles.py`); sin declaración el bloque no aplica (`CHECKPOINTS.md:264`).
Las verificaciones extra que pide el encargo, hechas una a una:

| Verificación | Resultado | Evidencia |
|---|---|---|
| Escritura en producción | [x] | `commit` por defecto `False` y estricto (`factura_models.py:152`). El commit exige `SIGRID_FACTURA_WRITE_ENABLED` en la ruta (`_exigir_escritura_de_facturas`, después del cuerpo y antes del caso de uso) y además `SIGRID_DOMAIN_WRITE_ENABLED` + credenciales + base permitida en el caso de uso (`create_factura_use_case.py:330-345`). Ningún `DELETE/TRUNCATE/DROP` en el código nuevo. Ninguna escritura real hecha por agentes en esta rama: T22-T24 (grabaciones) siguen como MANUAL del humano (`progress/current.md`). |
| SQL siempre con `?` | [x] | Ver C3. |
| Nada en `infrastructure/security/` | [x] | Ningún fichero de esa carpeta en el diff; solo se usa `DatabaseReferenceGuard` tal cual. |
| Llave propia apagada por defecto | [x] | `config/settings.py`: `sigrid_factura_write_enabled = False`, listas y mapa vacíos; `local.settings.sample.json` con `"false"`, `[]`, `{}`. Tests: `test_f008_r47_los_siete_ajustes_arrancan_ausentes_y_cerrados`, `test_f008_r47_la_muestra_lleva_las_siete_cerradas`, `test_f008_r4_ninguna_otra_llave_la_abre`, `test_f008_r4_llave_cerrada_antes_del_caso_de_uso`. |
| 400 sin eco | [x] | `_respuesta_factura_invalida` devuelve solo `loc`, `type` y `msg`, nunca `input` ni `ctx`; el log, solo `(loc, type)`. Los `msg` de los validadores de `factura_models.py` no citan valores de la petición (solo `serie`, que es el literal FR/FRGG, e índices). Test `test_f008_r1_cuerpo_invalido_sin_eco_ni_codigo`. |
| Sin secretos ni datos reales | [x] | Barrido propio sobre las 8.904 líneas añadidas (abajo). |

`pytest -q tests/test_f008_route.py tests/test_f008_settings.py tests/test_f008_models.py` → **83 passed**.

### Barrido de datos sensibles (ejecutado por el reviewer)

Sobre `git diff ccfb334...HEAD -U0` (líneas `+`), patrones:

- CIF/NIF/NIE `\b[ABCDEFGHJNPQRSUVW][0-9]{7}[0-9A-J]\b|\b[0-9]{8}[A-Z]\b|\b[XYZ][0-9]{7}[A-Z]\b` → solo `B00000000`,
  `B00000001`, `B00000002`, `B99999999` (ficticios).
- Correo `[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}` → solo decoradores (`@app.route`, `@pytest.mark…`).
- IPv4 y GUID de suscripción/tenant → 0 coincidencias.
- Claves `password|pwd|secret|token|apikey|x-functions-key|AccountKey|SharedAccess|Bearer` → solo nombres de
  ajustes, `"clave-de-prueba"`, `"no-es-una-credencial"` y `$env:SIGRID_API_FUNCTION_KEY` (variable de entorno).
- IBAN `ES[0-9]{2}…` → `ES000…0`, `ES111…1` (ficticios).
- Razones sociales y nombres (`S.L.`, `SLU`, `S.A.`, dos/tres palabras capitalizadas, mayúsculas entre comillas) →
  solo `PROVEEDOR UNO SL`, `PROVEEDOR DOS SL`, `PROVEEDOR SL` del doble (`tests/f008_dobles.py:13` se declara
  sintético). Ningún nombre de persona.
- `verificacion_manual.md` ordena anotar las facturas reales solo como `con.ide` en `progress/verificacion_F-008.md`,
  que aún no existe.

## Hallazgos

**H1 (bloqueante, C3 «Estados nunca hardcodeados»).** `application/use_cases/factura_statements.py:136-145`,
`construir_con_pago` fija `est=1` para el `con` de cada vencimiento (`tip 25`). El caso de uso ya lee `conest` de los
tres tipos (`leer_estados`, `factura_statements.py:560-562`, con `TIP_PAGO`), pero `_estados`
(`create_factura_use_case.py:370-373`) no incluye `(TIP_PAGO, "PDT")` en `necesarios` y el valor leído no se usa en
`create_factura_use_case.py:825`. El diseño dice «`est` PDT» (`design.md:135-136`), no «1». Hoy PDT vale 1 (medido en
`impl_F-008.md:24`), así que no hay error en datos, pero es exactamente la trampa que la regla vigila, y el precedente
de F-009 (`albaran_compra_statements.py:62`) al menos exige que el estado esté en `conest`.

## Cambios requeridos

1. `create_factura_use_case.py:370-373`: añadir `(TIP_PAGO, "PDT")` a `necesarios` (solo cuando la factura lleve
   vencimientos o retención de garantía, o siempre: decisión del implementer, explicada en el informe), de modo que un
   `conest` sin PDT dé `estado_inicial_no_encontrado` sin escribir nada.
2. `factura_statements.py:136-145` y `create_factura_use_case.py:825`: `construir_con_pago` recibe `est` como
   parámetro (igual que `construir_con_factura`) y el caso de uso le pasa `estados[(TIP_PAGO, "PDT")]`.
3. Test nuevo `test_f008_r9_…`/`r41_…` (el que corresponda en requirements) que: (a) con `conest` sin `25 PDT` dé el
   400 sin escribir, y (b) con PDT en un valor distinto de 1 en el doble, el `con` del pago salga con ese valor. Ajustar
   la aserción de `tests/test_f008_statements.py` que hoy fija `est` del pago.
4. Al tocar código del alcance de la campaña, actualizar `progress/mutacion_F-008.md` (RM1: el SHA medido dejaría de ser
   HEAD) según decida el revisor de C4 bis.

## Observaciones no bloqueantes

- **ruff:** F-008 añade 26 avisos nuevos (comparado con `git show ccfb334:<f> | ruff --stdin-filename`): 3 `ISC004` en
  `factura_lineas.py:337, 409, 418` (concatenación implícita intencionada dentro de tuplas, no es una coma olvidada),
  1 `RUF059` en `tests/test_f008_route.py:113`, y 22 en `tests/test_f008_statements.py` (`ISC004`, `RUF100` en
  595-599, `I001` en 646). Los de `function_app.py` y `config/settings.py` son previos. El lint no bloquea en este
  repo (`init.sh` §6b, deuda total 104), pero ya que hay que volver a tocar código, conviene dejarlos a cero.
- `function_app.py`, rama `except Exception`: el 500 devuelve `str(exc)` en `details.exception`. Es el patrón de todas
  las rutas (previo a F-008); fuera del alcance de esta feature.

## Automejora (propuesta, no aplicada)

C3 dice «Estados nunca hardcodeados» pero no cuenta los estados de los documentos **auxiliares** (pagos, efectos). H1
pasó por eso. Propuesta para `CHECKPOINTS.md` C3 (y `arnes-base` no, es de Sigrid): «…se resuelven contra
`dbo.conest`, **también los de los `con` auxiliares que nazcan con el documento (pagos `tip 25`, efectos)**».
