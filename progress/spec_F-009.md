<!-- progress/spec_F-009.md -->
# Spec F-009 · Alta de albaranes de compra para el pipeline (PRE-1 de albaranes F-053) — v5

Spec-author. v1 y v2 del 2026-10-01 (respuestas del humano a la PARADA 1); v3 del 2026-10-02 (T0); v4 del 2026-10-02 (respuestas a N1-N3); **v5 del 2026-10-05** (huecos de `contrato_albaranes.md` §5 y decisiones del humano; §v5). Rama
`feature/F-009-alta-albaran-compra` desde `dev` (2a5ac24). Estado `spec_ready`, `sdd`, rigor
`critico`, prioridad 7 (antes que F-007 y F-008). Spec en `specs/F-009-alta-albaran-compra/`.
**No se ha llamado a la API, ni a Azure, ni al SQL Server**: lo que depende de cómo trabaja el
escritorio de Sigrid queda como medición de solo lectura (T0) o como verificación manual.

`bash harness/init.sh` en verde **con el venv del proyecto**. Desde una sesión con `VIRTUAL_ENV`
heredado de otro repositorio sale en rojo (`azure.functions` ausente): el portero respeta un
venv ya activado. No es un fallo del repo; se lanza sin esa variable.

## v5 (2026-10-05): huecos del contrato con albaranes y decisiones del humano

Fuente: `specs/F-009-alta-albaran-compra/contrato_albaranes.md` §5 (H1-H33, escrito el mismo día
por el agente de albaranes contra la v4) y las decisiones del humano del 2026-10-05 sobre H4, H8,
H9, H17, H20, H28 y H31. Estado de cada hueco: tabla al principio de §5 de ese documento. Topes:
`requirements.md` 150/150 y `design.md` 249/250; para caber, el detalle campo a campo y los
ejemplos se enlazan a `contrato_albaranes.md` y el razonamiento de N1 y de la regla A a este informe.

### Qué cambió en la spec

| Hueco | Cambio | Dónde |
|---|---|---|
| H2 | Obra solo en las empresas de `SIGRID_ALBARAN_EMPRESAS_OBRA` (quinta App Setting, defecto `[]`, despliegue `[1]`); código nuevo `obra_de_empresa_no_permitida`. Con `[1]`, `obra_ambigua` ya no puede darse (índice único `(emp, tip, cod)`, M2) | R10, R11, design L1 |
| H3 | Plantilla de cabecera del mismo proveedor **en la empresa de la obra** (`AND c.emp = ?`) y `con.emp` = la de la obra | R11, design L5 |
| H4 | Decidido: se conserva «imputable» y **no** se exige hoja | R14 |
| H8 | Segunda barrera: `precio` < 0 ⇒ fallo de línea `precio_negativo`. **Ya existía algo equivalente**: `precio` con `ge=0` en Pydantic (400 sin código, toda la petición). Se sustituye por el fallo de línea con código para que F-053 lo pueda mapear; el efecto (rechazo) es el mismo | R17, design §Modelo y §Riesgos |
| H9 | Regla condicional a M17 (R30b) | R30b, design §Condicionales |
| H10 | Almacén y centro para **toda** sin vincular (con o sin partida); `caaide` por hipótesis condicionada a M16 | R15, design §Analítica |
| H11 | Lista de reseteo cerrada para las sin vincular, confirmada con M14 ampliada | R13, design §Reseteo |
| H12 | Aviso `almacen_en_linea_con_partida` | R16 |
| H13 | `obr.almide`/`obr.cenide` antes que el único `alm` de la obra (orden: `ctrpro` o contrato → ficha de obra → único `alm`) | R15, design L10 |
| H14 | Tolerancia 0,0001 (la de M4); si casa, `pre`, `tar` y `dto` del `ctrpro` | R17 |
| H15 | Plantilla de la sin vincular = última `dcapro` del producto **del mismo proveedor** (L8b); si no hay, la del producto con aviso `iva_de_otro_proveedor` | R13, design L8b |
| H16 | `COLUMNAS_BANCARIAS` (15 columnas de `dca` según el diccionario) fuera de `cabecera`, `filas.dca` y trazas; se escriben igual | R7, R32, design §Respuesta |
| H17 | `paride` opcional solo si M3 da repetidos entre imputables (R14b, código `paride_no_valido`) | R14b |
| H18 | `idempotente`: `committed` `false`, `dry_run` = `not commit`, líneas por `pos` con `indice` desde 0; `referencia_linea` en `dcapro.refent` condicionada a M18 (y entonces ≤24) | R30, R30b |
| H19 | `fecha_no_valida` si `fecha_albaran` > hoy (Madrid), también en dry-run | R11 |
| H20 | Puerta dura: sin M9 cerrada no hay modo real; si MA9999 mueve stock, PARADA | R35, tasks T22 |
| H21 | `cif_proveedor` a mayúsculas sin espacios | R5 |
| H26, H27 | `indice` desde 0; avisos `{codigo, mensaje}` y `warnings` = sus mensajes | R7 |
| H28 | Una sola repetición de T0 con el script ampliado | R35, tasks T0a-T0c |
| H31 | **Comprobado: F-009 ya admite** `cod_contrato` sin ninguna vinculada (ninguna regla lo prohíbe: se resuelve el contrato, `dca.ctride` queda enlazado y plantilla y almacén salen del contrato). Lo único que faltaba: sin vinculadas no hay `UPDATE` de `ctrpro` ni de `ctr` (E9-E11) | R6, R20, R25 |
| H32 | Docstring de `sigrid_albaran` (T13) y `sigrid_api.md` §4, §7.5, §7.6, §8.6 (T18) | R36 |
| H33 | `Decimal` + `ROUND_HALF_UP` en `tot` e `ivacuo`; diferencia declarada en R33 (el clásico usa `round`) | R17, R33 |

Otros: `cantidad` y `precio` finitos (`NaN`/`inf` fuera); R34 añade fase RED en R11 y R17. Ningún
hueco contradice el código ni las mediciones de la primera pasada. Matiz en H13: la propuesta decía
«`obr.almide` primero»; se mantiene antes el almacén del `ctrpro`/contrato (M8: el del contrato es
de su obra en el 99,4 %) y la ficha de obra pasa a ser el segundo recurso, antes que `alm`.

### T0 v5: mediciones nuevas y ampliadas (solo lectura, `sql/read`)

Una sola repetición (H28): `& .\.venv\Scripts\python.exe -m scripts.medir_f009_t0 --solo M3 M7 M9
M11 M13 M14 M16 M17 M18`, después de que el implementer amplíe el script (tasks T0a). Las sentencias
siguen la regla del error 130: nada de agregados sobre subconsultas o `APPLY` escalares; recuentos
en tablas derivadas. M3, M7, M9 y M13 quedan como están en el script.

- **M16 analítica, almacén y centro (H10, H13)** → decide design §Analítica y el orden de R15.
  - `M16_caa_con_partida`: `SELECT CASE WHEN ISNULL(d.docoritip, 0) = 44 THEN 'vinculada' ELSE 'sin_vincular' END AS tipo, CASE WHEN ISNULL(d.docoritip, 0) = 44 AND ISNULL(d.paride, 0) <> ISNULL(t.paride, 0) THEN 1 ELSE 0 END AS partida_distinta, COUNT(*) AS n, SUM(CASE WHEN ISNULL(d.caaide, 0) = ISNULL(p.caaide, 0) THEN 1 ELSE 0 END) AS caa_de_la_partida, SUM(CASE WHEN ISNULL(p.caaide, 0) = 0 THEN 1 ELSE 0 END) AS partida_sin_caa, SUM(CASE WHEN t.ide IS NOT NULL AND ISNULL(d.caaide, 0) = ISNULL(t.caaide, 0) THEN 1 ELSE 0 END) AS caa_del_ctrpro FROM dbo.dcapro d JOIN dbo.con c ON c.ide = d.docide JOIN dbo.obrparpar p ON p.ide = d.paride LEFT JOIN dbo.ctrpro t ON t.ide = d.linoriide AND d.docoritip = 44 WHERE c.tip = 14 AND c.fec >= 20250101 AND d.paride > 0 GROUP BY` (las dos expresiones `CASE`).
  - `M16_caa_almacen`: `SELECT CASE WHEN ISNULL(d.docoritip, 0) = 44 THEN 'vinculada' ELSE 'sin_vincular' END AS tipo, COUNT(*) AS n, SUM(CASE WHEN ISNULL(d.caaide, 0) = ISNULL(a.caaproide, 0) THEN 1 ELSE 0 END) AS caa_pro_del_alm, SUM(CASE WHEN ISNULL(d.caaide, 0) = ISNULL(a.caaseride, 0) THEN 1 ELSE 0 END) AS caa_ser_del_alm, SUM(CASE WHEN ISNULL(a.caaproide, 0) = 0 THEN 1 ELSE 0 END) AS alm_sin_caa FROM dbo.dcapro d JOIN dbo.con c ON c.ide = d.docide LEFT JOIN dbo.alm a ON a.ide = d.almide WHERE c.tip = 14 AND c.fec >= 20250101 AND ISNULL(d.paride, 0) = 0 GROUP BY` (el `CASE`).
  - `M16_almacen_sin_vincular`: `SELECT CASE WHEN ISNULL(d.paride, 0) > 0 THEN 'con_partida' ELSE 'almacen' END AS tipo, CASE WHEN ISNULL(a.ctride, 0) > 0 THEN 'con_contrato' ELSE 'sin_contrato' END AS cabecera, COUNT(*) AS n, SUM(CASE WHEN d.almide = t.almide THEN 1 ELSE 0 END) AS alm_del_contrato, SUM(CASE WHEN d.almide = o.almide THEN 1 ELSE 0 END) AS alm_de_la_ficha, SUM(CASE WHEN d.cenide = t.cenide THEN 1 ELSE 0 END) AS cen_del_contrato, SUM(CASE WHEN d.cenide = o.cenide THEN 1 ELSE 0 END) AS cen_de_la_ficha FROM dbo.dcapro d JOIN dbo.con c ON c.ide = d.docide JOIN dbo.dca a ON a.ide = d.docide LEFT JOIN dbo.obr o ON o.ide = d.obride LEFT JOIN dbo.ctr t ON t.ide = a.ctride WHERE c.tip = 14 AND c.fec >= 20250101 AND ISNULL(d.docoritip, 0) <> 44 GROUP BY` (los dos `CASE`).
  - `M16_ficha_obra`: `SELECT COUNT(*) AS obras, SUM(CASE WHEN ISNULL(o.almide, 0) > 0 THEN 1 ELSE 0 END) AS con_almide, SUM(CASE WHEN a.obride = o.ide THEN 1 ELSE 0 END) AS almide_de_su_obra, SUM(CASE WHEN ISNULL(o.cenide, 0) > 0 THEN 1 ELSE 0 END) AS con_cenide FROM dbo.obr o LEFT JOIN dbo.alm a ON a.ide = o.almide WHERE o.ide IN (SELECT d.obride FROM dbo.dca d JOIN dbo.con c ON c.ide = d.ide WHERE c.tip = 14 AND c.fec >= 20250101)`.
  - **Debe salir / decide**: `caa_de_la_partida` ≥ 95 % de `n` en las sin vincular y en las vinculadas con `partida_distinta` 1, y `caa_pro_del_alm` ≥ 95 % en almacén ⇒ hipótesis de design §Analítica confirmada. `alm_del_contrato` dominante en `con_contrato` y `alm_de_la_ficha` en `sin_contrato`, con `con_almide` ≈ `obras` y `almide_de_su_obra` ≈ `con_almide` ⇒ orden de R15 confirmado. Cualquier otro reparto ⇒ PARADA y v6.
- **M17 anulación de albaranes (H9)** → decide R30b (ignorar anulados o no).
  - `M17_ope`: `SELECT ope, COUNT(*) AS n, MIN(fec) AS desde, MAX(fec) AS hasta FROM dbo.log WHERE ide > (SELECT MAX(ide) - 1000000 FROM dbo.log) AND tab = 'con' AND tip = 14 GROUP BY ope ORDER BY ope` (qué operaciones registra el escritorio sobre albaranes; el diccionario no documenta los valores de `log.ope`).
  - `M17_existe`: `SELECT l.ope, COUNT(*) AS n, SUM(CASE WHEN c.ide IS NULL THEN 0 ELSE 1 END) AS con_existe, SUM(CASE WHEN ISNULL(c.fecbaj, 0) > 0 THEN 1 ELSE 0 END) AS con_fecbaj FROM dbo.log l LEFT JOIN dbo.con c ON c.emp = l.emp AND c.tip = l.tip AND c.cod = l.cod WHERE l.ide > (SELECT MAX(ide) - 1000000 FROM dbo.log) AND l.tab = 'con' AND l.tip = 14 AND l.ope <> 1 GROUP BY l.ope ORDER BY l.ope` (si `log.emp` sale 0 o nulo, repetir el `JOIN` solo por `tip` y `cod`).
  - `M17_marcas`: `SELECT est, CASE WHEN ISNULL(fecbaj, 0) > 0 THEN 1 ELSE 0 END AS con_fecbaj, COUNT(*) AS n FROM dbo.con WHERE tip = 14 AND fec >= 20250101 GROUP BY est, CASE WHEN ISNULL(fecbaj, 0) > 0 THEN 1 ELSE 0 END ORDER BY n DESC`.
  - **Debe salir / decide**: si hay una `ope` distinta de alta y modificación cuyo `con_existe` ≈ 0 ⇒ anular **borra**: R30 sin cambios. Si `con_existe` ≈ `n` y aparece una marca (`fecbaj` > 0 o un `est` fuera de `conest`) ⇒ **marca**: L11 añade `AND <no marcado>` y F-053 usa `ALB-{id}-{n}`. Sin `ope` de baja clara ⇒ se decide con T23 (anulación del albarán de prueba, leída después).
- **M18 uso de `dcapro.refent` (H18)** → decide R30b (escribir `referencia_linea` o no).
  - `M18_refent`: `SELECT CASE WHEN ISNULL(d.docoritip, 0) = 44 THEN 'vinculada' ELSE 'sin_vincular' END AS tipo, COUNT(*) AS n, SUM(CASE WHEN ISNULL(d.refent, '') <> '' THEN 1 ELSE 0 END) AS con_refent FROM dbo.dcapro d JOIN dbo.con c ON c.ide = d.docide WHERE c.tip = 14 AND c.fec >= 20250101 GROUP BY CASE WHEN ISNULL(d.docoritip, 0) = 44 THEN 'vinculada' ELSE 'sin_vincular' END`.
  - `M18_valores`: `SELECT TOP 20 LEFT(d.refent, 8) AS prefijo, COUNT(*) AS n FROM dbo.dcapro d JOIN dbo.con c ON c.ide = d.docide WHERE c.tip = 14 AND c.fec >= 20250101 AND ISNULL(d.refent, '') <> '' GROUP BY LEFT(d.refent, 8) ORDER BY n DESC`.
  - `M18_propagacion` (¿pasa `refent` del albarán a la factura?): `SELECT COUNT(*) AS n, SUM(CASE WHEN ISNULL(f.refent, '') <> '' THEN 1 ELSE 0 END) AS con_refent, SUM(CASE WHEN ISNULL(d.refent, '') <> '' AND f.refent = d.refent THEN 1 ELSE 0 END) AS copiada FROM dbo.dcfpro f JOIN dbo.dcapro d ON d.ide = f.linoriide WHERE f.docoritip = 14 AND f.docide IN (SELECT ide FROM dbo.con WHERE fec >= 20250101)`.
  - **Debe salir / decide**: `con_refent` ≤ 0,1 % de `n` ⇒ `refent` libre: se escribe `referencia_linea` (que baja a 1-24) y se devuelve en `idempotente`. Más ⇒ no se escribe. Si `copiada` > 0, la referencia llegaría a la factura (pregunta N9).
- **M11 ampliada: IVA de MA9999 por proveedor (H15)** → confirma L8b. Por cada `ide` de MA9999 (uno por empresa):
  - `M11_iva_por_proveedor`: `SELECT COUNT(*) AS proveedores, SUM(CASE WHEN x.n_iva > 1 THEN 1 ELSE 0 END) AS con_varios_iva FROM (SELECT a.entide, COUNT(DISTINCT d.ivaide) AS n_iva FROM dbo.dcapro d JOIN dbo.dca a ON a.ide = d.docide JOIN dbo.con c ON c.ide = d.docide WHERE c.tip = 14 AND c.fec >= 20250101 AND d.proide = ? GROUP BY a.entide) x`.
  - `M11_iva_y_isp`: `SELECT a.tipisp, d.ivaide, COUNT(DISTINCT a.entide) AS proveedores, COUNT(*) AS lineas FROM dbo.dcapro d JOIN dbo.dca a ON a.ide = d.docide JOIN dbo.con c ON c.ide = d.docide WHERE c.tip = 14 AND c.fec >= 20250101 AND d.proide = ? GROUP BY a.tipisp, d.ivaide ORDER BY lineas DESC`.
  - `M11_acierto`: `SELECT COUNT(*) AS lineas, SUM(CASE WHEN x.iva_prev_prv IS NULL THEN 1 ELSE 0 END) AS sin_previa_del_prv, SUM(CASE WHEN x.ivaide = x.iva_prev_prv THEN 1 ELSE 0 END) AS acierta_mismo_prv, SUM(CASE WHEN x.ivaide = x.iva_prev THEN 1 ELSE 0 END) AS acierta_cualquiera FROM (SELECT d.ivaide, LAG(d.ivaide) OVER (PARTITION BY a.entide ORDER BY d.ide) AS iva_prev_prv, LAG(d.ivaide) OVER (ORDER BY d.ide) AS iva_prev FROM dbo.dcapro d JOIN dbo.dca a ON a.ide = d.docide JOIN dbo.con c ON c.ide = d.docide WHERE c.tip = 14 AND c.fec >= 20250101 AND d.proide = ?) x` (si `SqlQueryGuard` rechaza `OVER`, se queda con las dos primeras).
  - **Debe salir / decide**: `acierta_mismo_prv` > `acierta_cualquiera` o IVA distinto con `tipisp` 1 ⇒ L8b justificada. Si aciertan igual, L8b es inocua y se queda. Sigue la comprobación de `ivacuo = round(tot·iva, 2)` de `M11_iva_usado`.
- **M14 ampliada: columnas de la `dcapro` sin vincular (H11)** → confirma o corrige design §Reseteo.
  - `M14_sv_valores`: `SELECT COUNT(*) AS n, SUM(CASE WHEN DATALENGTH(d.med) > 0 THEN 1 ELSE 0 END) AS med, SUM(CASE WHEN ISNULL(d.canmed, 0) <> 0 THEN 1 ELSE 0 END) AS canmed` y el mismo patrón para `parcandes`, `anades`, `serdes`, `fecimp`, `item`, `anexo`, `taride`, `fec`, `pla` (numéricas, `<> 0`), `tex`, `texcom` (`DATALENGTH > 0`), `cod2`, `pac`, `refent` (`<> ''`) y `SUM(CASE WHEN d.fec = c.fec THEN 1 ELSE 0 END) AS fec_igual_albaran`, `FROM dbo.dcapro d JOIN dbo.con c ON c.ide = d.docide WHERE c.tip = 14 AND c.fec >= 20260101 AND ISNULL(d.docoritip, 0) <> 44`.
  - `M14_sv_arrastre`: las 3 últimas sin vincular de MA9999 de la empresa 1 (`SELECT TOP 3 d.ide, d.proide FROM dbo.dcapro d JOIN dbo.con c ON c.ide = d.docide WHERE c.tip = 14 AND c.fec >= 20260901 AND ISNULL(d.docoritip, 0) <> 44 AND d.proide = ? ORDER BY d.ide DESC`), cada una con `SELECT * FROM dbo.dcapro WHERE ide = ?` y su plantilla `SELECT TOP 1 * FROM dbo.dcapro WHERE proide = ? AND ide < ? ORDER BY ide DESC`; `columnas_distintas` entre cada línea y su plantilla.
  - **Debe salir / decide**: columnas de la lista con ≈ 0 valores no vacíos ⇒ reseteo confirmado. Una que el escritorio rellene siempre (p. ej. `fec` = fecha del albarán, `fec_igual_albaran` ≈ `n`) ⇒ se corrige §Reseteo con ese valor (v6). Columnas fuera de la lista que el escritorio no arrastra de la plantilla ⇒ se añaden.

### Preguntas abiertas para el humano (v5)

- **N4 (H31).** F-009 admite `cod_contrato` sin ninguna línea vinculada: enlaza `dca.ctride`, toma
  plantilla y almacén del contrato y no toca la medición. ¿Debe F-053 mandar `cod_contrato` siempre
  que la valoración tenga contrato, aunque no case ninguna línea? Recomendación: **sí** (el albarán
  queda colgado del contrato, como lo haría el escritorio). Es cambio de F-053 R12, no de F-009.
- **N5 (H2).** `SIGRID_ALBARAN_EMPRESAS_OBRA` con defecto **cerrado** `[]` (sin ella el modo
  extendido no encuentra ninguna obra: `obra_de_empresa_no_permitida`) y despliegue `[1]`, como las
  otras listas de R10. Alternativa: defecto `[1]`. Recomendación: cerrado.
- **N6 (H2, opcional).** ¿Rechazar obras de baja (`con.fecbaj` > 0)? Propuesta: **no** (un albarán
  tardío de una obra cerrada debe poder entrar; con `[1]` ya no hay ambigüedad que resolver).
- **N7 (H8).** El `precio ≥ 0` de Pydantic (400 sin código, toda la petición) pasa a fallo de línea
  `precio_negativo` (400 `lineas_no_validas`, junto con los demás fallos). ¿Conforme?
- **N8 (H15).** «Con aviso si difieren» se ha escrito como: aviso `iva_de_otro_proveedor` cuando el
  proveedor no tiene ninguna línea previa del producto y se usa la de otro. ¿Conforme, y bloqueante o
  informativo en F-053? Propuesta: informativo.
- **N9 (H18, si M18 sale libre).** Escribir `referencia_linea` en `dcapro.refent` hace visible en la
  UI de Sigrid el `id` de la línea de albaranes y obliga a `referencia_linea` ≤ 24 (sv9 manda un
  entero). Si M18 muestra que `refent` se copia a la factura, también aparecería allí. ¿Conforme?
- **N10 (H19).** F-009 solo rechaza fechas **futuras**; la ventana de plausibilidad (hoy − 365 días)
  queda en F-053. ¿Conforme?
- **N11 (H21).** F-009 normaliza mayúsculas y espacios del CIF, pero **no** quita el prefijo `ES` ni
  guiones (lo garantiza albaranes con F-052). ¿Conforme?
- **N12 (códigos nuevos).** Mapeo propuesto en `contrato_albaranes.md` §3.3 para F-053:
  `fecha_no_valida` → `revisar`, `obra_de_empresa_no_permitida` → `error`, `precio_negativo` →
  `revisar`, `paride_no_valido` → `no_admitido`; avisos nuevos, informativos. Es de albaranes (H25).

## Qué cambió en la v2 (lo que la v3 revisa va marcado)

- **Se amplía `sigrid/albaran`** (no hay ruta nueva). Dos modos, decididos por las **claves**
  del JSON: `lineas` o `referencia_externa` → extendido; ninguna → clásico; `lineas_recibidas`
  junto a cualquiera de ellas → 400 `peticion_mixta` (design §La decisión de fondo).
- **Modo clásico idéntico a hoy** (incluida la suma de `lineas_recibidas` al mismo `ctrpro`):
  sus casos de uso y modelos no se tocan y lo fija un **test de caracterización** con fichero
  dorado escrito sobre `dev` antes de cualquier cambio (T1, design §Caracterización).
- **Segunda llave `SIGRID_ALBARAN_WRITE_ENABLED`** (defecto `false`) cierra el `commit` de los
  dos modos de `sigrid/albaran` **y** de `albaran-directo` (R8); el dry-run no cambia.
- **Devolución que deja `canser` < 0: se admite** con aviso `servido_negativo`; `estser` se
  recalcula con la regla de hoy y puede volver a 0 (R18, R20).
- **Negativas en vinculadas y sin vincular** (R6, R18). Si M5 no encuentra devoluciones reales,
  **hipótesis A** (simétrica al alta), verificada con la primera devolución real del pipeline
  (T24, consulta abajo). Pregunta 8 cerrada (opción a).
- Aceptadas las propuestas 3-6 y 9-17: prefijo `ALB-`; productos `["MA9999"]`; partida y precio
  distintos del contrato con aviso; `dcapropar` y `log` fuera salvo M7/M13 (*v3: el `log` se
  escribe*); sin recálculo de `mov` posteriores (*v3: reabierto, pregunta N1*); almacén y centro derivados; `con.est` según M2; lista de reseteo, hora de
  Madrid e IVA por `dbo.iva` solo en el modo extendido; los viejos, obsoletos cuando F-053 esté
  en real (T18); prioridad 7.

## Resultados de T0 (primera pasada, 2026-10-02) y decisiones de la v3

Fuente: el fichero de resultados del humano (en `%TEMP%`, **no** se versiona: lleva datos de
negocio). Aquí solo cifras agregadas y conclusiones. M7 y M9 fallaron (error 130 de SQL
Server, corregido en `28afc96`) y M11 tenía un fallo del script (abajo).

| M | Resultado | Decisión en la spec v3 |
|---|---|---|
| M1 | `dca.synckey` vacío en los 312.644 albaranes; ningún `ALB-`; búsqueda sin índice, 0,1 s | **Cerrado**: idempotencia por `synckey` sin índice (R30) |
| M2 | Albaranes desde 2025: 99,97 % en `emp` 1. Estados de `conest` tip 14: 1 `PDT` Pendiente, 2 `COM` Comprobado, 3 `CON` Contabilizado, 10 `FAC` Facturado. `sercon.estini` = 0 en las tres series tip 14 (`AC`, `NTC`, `PROF`), y 0 no es un estado (solo 6 albaranes lo tienen). `mov.emp` = 1 en todos. Índice único `con_emptipcod (emp, tip, cod)` | `cod` por `emp` bajo el índice único (R26); `mov.emp` = `con.emp`; **`con.est` = 1 `PDT`** (R22): el «3» de los no facturados está sesgado por los ya contabilizados, el ciclo es Pendiente → Comprobado → Contabilizado → Facturado y el alta de junio con 1 se vio bien en la UI. Lo confirma la repetición de M13, que lee el `est` de la fila de alta en `log` |
| M3 | Partidas usadas en albaranes desde 2025: 100 % `tip 1`, `tipdes 0`; `tipvis` 0 (99,6 %) o 1. En `obrparpar`: `tip` 0 = 45.783, 1 = 349.408, 99 = 5. 5.207 pares (obra, código) repetidos | Imputable = `tip 1`, `tipdes 0`, `tipvis` 0/1 (R14). **Abierto**: cuántos repetidos quedan entre imputables (repetición) → pregunta N2 si hay |
| M4 | Escritorio, vinculadas desde 2025: partida distinta del `ctrpro` 5,3 % (5.178 de 98.145), precio distinto 1,5 %. `ctrpro` sin `paride`/`cenide`/`caaide` nulos | **Cerrado**: confirma R16/R17 (permitido con aviso); la herencia de partida por `NULL` no ocurre |
| M5 | 119.554 líneas negativas desde 2008 (112.379 sin vincular, 6.411 vinculadas). Muestra de 20: regla A en 13 (todas las que tienen `mov`), sin `mov` en 6, «?» en 1 | **Cerrado: regla A** (R18). La «?» es un albarán con fecha atrasada comparado con el `mov` anterior por `ide` (ver M10). Las 6 sin `mov` son **todas del mismo producto** (ide 571020): depende del producto, no de la devolución → repetición de M9 (`pro.tipmov` «Hace movimientos») |
| M6 | `ctrprodes.can` = cantidad negativa en 20 de 20; `canser` ≠ Σ `ctrprodes.can` en 13 de 5.348; `canser` < 0 en 750 `ctrpro` | **Cerrado**: coherente con admitir `canser` < 0 (R18, R20) |
| M7 | Falló (error 130) | Repetición |
| M8 | 649 obras con un almacén, 5 con dos; `ctr.almide` es de su obra en el 99,4 %; líneas sin partida: almacén de la obra 98,9 %, con el centro del almacén 90,8 % | **Cerrado** (R15); dos almacenes → `almacen_de_obra_no_resuelto` |
| M9 | Falló (error 130) | Repetición: ¿cuándo no hay `mov`? |
| M10 | En las 3 series medidas, la cadena de `almcan` cuadra en orden de `fechor` (0 roturas) y no en orden de `ide` (1 rotura en 2): **el escritorio recalcula los `mov` posteriores** cuando entra uno con fecha anterior | **Pregunta N1** (design §Fecha atrasada) |
| M11 | Hay **un producto genérico por empresa** (1, 31, 34; `tip 3`), todos con `comide` e `ivacomide` a 0 y `natide` propio. «0 líneas de MA9999» era **un fallo del script**: cogía el primer MA9999 de la lista (el de la empresa 31). `dbo.iva` se repite por empresa; `iva` es una fracción (0,16…) | Producto por `(emp, cod)`; cuenta e IVA de su última `dcapro`, naturaleza del maestro (R13). Repetición: líneas de cada MA9999 y comprobación `ivacuo = round(tot·iva, 2)` |
| M12 | El 77,4 % de los albaranes con contrato desde 2025 llevan alguna línea sin vincular | **Cerrado**: confirma el diseño |
| M13 | 13.934 filas de alta de albarán (`tab 'con'`, `tip 14`, `ope 1`) en los últimos 300.000 `ide` de `log` (la comparación con albaranes salió mal: ventana desde fecha 0) | **Se escribe** la fila de alta, con `usu` nuevo y obligatorio en la petición (R5, R25). Repetición: cobertura, `est` inicial y `ori` |
| M14 | La cabecera de la API difería en forma de pago, efecto y dirección, pero **la muestra era de otros proveedores**: la API copió la de su propio proveedor. `dcapro.prepma` de la API = el de la plantilla; el del escritorio coincide con el PMP vigente del almacén. Resto de columnas de línea, sin diferencias | Plantilla de cabecera **solo del mismo proveedor**, sin *fallback* (R11); `prepma` = PMP resultante (R21). Repetición con el mismo proveedor, frente al maestro `prv` y `prepma` contra su `mov` |
| M15 | 748 `mov` con stock negativo desde 2025, en 20 almacenes | **Cerrado**: solo aviso |

**Para F-007 (proformas):** la serie `PROF<aa>/` es `tip 14`, como los albaranes: las proformas
son albaranes de compra con otra serie.

## Repetición de T0 (v4; **sustituida por la de §T0 v5**)

> v5 (H28): **una sola** repetición, con el script ampliado (tasks T0a): `--solo M3 M7 M9 M11 M13
> M14 M16 M17 M18`. Lo de abajo describe lo que ya traía el script para M3, M7, M9, M11, M13 y M14.

M7 y M9 son las que fallaron. Las otras cuatro traen consultas nuevas para cerrar sus [Mn]:
partidas repetidas entre imputables (M3), banderas `pro.tipmov`/`tipinv` y productos de las
líneas sin `mov` (M9), cada MA9999 por empresa e IVA usado (M11), `est` y `ori` de la fila de
alta en `log` y su cobertura (M13), y M14 con el mismo proveedor, frente al maestro `prv` y con
`prepma` contra su `mov`. Se pega de vuelta el fichero de `%TEMP%` entero. La prueba de humo
ahora detecta el patrón del error 130 (agregado sobre subconsulta o sobre un `APPLY` escalar).

## T0: comando para PowerShell

El script `scripts/medir_f009_t0.py` lanza M1-M15 como SELECT por `POST /api/sql/read` (nada de
escrituras ni de endpoints de dominio; el propio cliente rechaza en local cualquier SQL que no
sea `SELECT`/`WITH` de una sentencia). Lee `SIGRID_API_BASE_URL` y `SIGRID_API_FUNCTION_KEY` del
entorno o, si no están, del `.env` de la raíz de sigrid-api (las dos claves están allí), y no
las imprime nunca. Las 42 sentencias pasan el mismo `SqlQueryGuard` de `sql/read` en la prueba
de humo (`tests/test_f009_t0_script.py`, 97 tests sin red). **No se ha ejecutado contra la API.**

```powershell
cd C:\Users\pgris\PycharmProjects\sigrid-api
git switch feature/F-009-alta-albaran-compra
& .\.venv\Scripts\python.exe -m scripts.medir_f009_t0
# una o varias:  & .\.venv\Scripts\python.exe -m scripts.medir_f009_t0 --solo M5 M6
```

- Tarda varios minutos: las consultas pesadas (M1, M3, M4, M6-M10, M12, M13, M15) piden
  hasta 200 s cada una, por debajo del corte de 230 s; la instancia `dev` admite
  `MAX_QUERY_TIMEOUT_SECONDS` 230 (§4.1). Si una falla, el script lo anota en su bloque y
  sigue con las demás.
- **Qué pegar de vuelta**: el fichero que indica al final (`%TEMP%\f009_t0_<fecha>.txt`),
  **entero**. Cada medición trae sus filas y un bloque «CONCLUSIÓN» con lo que necesita la
  spec (p. ej. `con.est` inicial probable, regla A/B de las devoluciones, columnas de la lista
  de reseteo con diferencia). Una medición que falle se repite con `--solo`.
- El fichero lleva datos de negocio (códigos, CIF, precios): no se versiona, y el script se
  niega a escribirlo dentro del repositorio.
- Añadidos frente a las consultas de §Mediciones: M2 mide también el `est` de los albaranes
  aún sin facturar (el inicial más probable); M4 cuenta los `caaide` nulos; M5 contrasta la
  regla A/B con el `mov` anterior de cada devolución de la muestra; M9 cuenta `mov` según la
  línea tenga partida o no; M10 compara las roturas de la cadena de `almcan` en orden de fecha
  y de `ide`; M13 acota por fechas la ventana de `log`.

## Hallazgos del código actual (el modo clásico los conserva)

1. **No hay ni un test** de `sigrid/albaran` ni de `albaran-directo`: de ahí T1.
2. El `cod` se calcula **fuera** de la transacción (`_next_cod`): carrera con el escritorio.
3. `con.est = 1` y `mov.emp = 1` **escritos a mano**; la serie `AC` medida en junio
   (`serie_stock.txt`, sin versionar) tenía `sercon.estini = 0`.
4. Fecha y hora con `datetime.now()`: en Azure es **UTC**, no Madrid.
5. La `dcapro` se clona de la **última línea del mismo producto en cualquier obra**: si el
   `ctrpro` trae `paride`/`cenide`/`caaide` `NULL`, se quedan los de esa otra línea, y siempre
   arrastra medición, analítica, desglose y `prepma` ajenos. `albaran-directo` hereda además el
   almacén y la partida.
6. `su_referencia` admite 200 caracteres y `dca.entref` es de 128.
7. Tasa de IVA = `ivacuo/tot` del `ctrpro`: con `tot` 0 sale 0.
8. El modelo clásico **ignora** las claves que no conoce: por eso `peticion_mixta` se decide
   antes de validar.

## Mediciones (T0) — solo lectura, por `sql/read`

Texto de la v1. La versión vigente de cada consulta es la de `scripts/medir_f009_t0.py` (M7 y
M9 reescritas; M3, M11, M13 y M14 ampliadas).

Setup de `azure-apps/sigrid_api.md` §8 (`$base`, `$headers`). Cada consulta:

```powershell
function Q($sql, $p = @()) { $b = @{ database = "ruesma"; sql = $sql; parameters = $p; max_rows = 200 } | ConvertTo-Json -Depth 5
  (Invoke-RestMethod -Uri "$base/api/sql/read" -Method Post -Headers $headers -ContentType "application/json" -Body $b) | ConvertTo-Json -Depth 8 }
```

- **M1 `synckey`** (¿libre?, ¿coste sin índice?):
  `SELECT COUNT(*) AS total, SUM(CASE WHEN ISNULL(synckey, '') <> '' THEN 1 ELSE 0 END) AS con_synckey FROM dbo.dca`;
  `SELECT TOP 20 LEFT(synckey, 6) AS prefijo, COUNT(*) AS n FROM dbo.dca WHERE ISNULL(synckey, '') <> '' GROUP BY LEFT(synckey, 6) ORDER BY n DESC`;
  coste: `Measure-Command { Q "SELECT c.ide, c.cod FROM dbo.dca d JOIN dbo.con c ON c.ide = d.ide WHERE c.tip = ? AND d.synckey = ?" @(14, "ALB-no-existe") }`.
- **M2 `emp`, estado, serie e índice**:
  `SELECT c.emp, c.est, COUNT(*) AS n FROM dbo.con c WHERE c.tip = 14 AND c.fec >= 20250101 GROUP BY c.emp, c.est`;
  `SELECT tip, est, cod, res FROM dbo.conest WHERE tip = 14`; `SELECT ide, tip, cod, emp, estini, act FROM dbo.sercon WHERE tip = 14`;
  `SELECT emp, COUNT(*) AS n FROM dbo.mov WHERE doctip = 14 AND fec >= 20250101 GROUP BY emp`;
  `SELECT i.name, i.is_unique, c.name AS col, ic.key_ordinal FROM sys.indexes i JOIN sys.index_columns ic ON ic.object_id = i.object_id AND ic.index_id = i.index_id JOIN sys.columns c ON c.object_id = ic.object_id AND c.column_id = ic.column_id WHERE i.object_id = OBJECT_ID('dbo.con') ORDER BY i.name, ic.key_ordinal`.
- **M3 partidas**:
  `SELECT p.tip, p.tipdes, p.tipvis, COUNT(*) AS n FROM dbo.dcapro d JOIN dbo.obrparpar p ON p.ide = d.paride JOIN dbo.con c ON c.ide = d.docide WHERE c.tip = 14 AND c.fec >= 20250101 GROUP BY p.tip, p.tipdes, p.tipvis`;
  `SELECT tip, COUNT(*) AS n FROM dbo.obrparpar GROUP BY tip`;
  `SELECT COUNT(*) AS repetidos FROM (SELECT obride, cod FROM dbo.obrparpar GROUP BY obride, cod HAVING COUNT(*) > 1) x`.
- **M4 vinculadas del escritorio con partida o precio distintos del contrato**:
  `SELECT COUNT(*) AS n, SUM(CASE WHEN ISNULL(d.paride, 0) <> ISNULL(p.paride, 0) THEN 1 ELSE 0 END) AS partida_distinta, SUM(CASE WHEN ABS(d.pre - p.pre) > 0.0001 THEN 1 ELSE 0 END) AS precio_distinto FROM dbo.dcapro d JOIN dbo.ctrpro p ON p.ide = d.linoriide JOIN dbo.con c ON c.ide = d.docide WHERE d.docoritip = 44 AND c.tip = 14 AND c.fec >= 20250101`;
  `SELECT SUM(CASE WHEN paride IS NULL THEN 1 ELSE 0 END) AS paride_null, SUM(CASE WHEN cenide IS NULL THEN 1 ELSE 0 END) AS cenide_null, COUNT(*) AS n FROM dbo.ctrpro`.
- **M5 devoluciones reales y su `mov`**:
  `SELECT ISNULL(d.docoritip, 0) AS docoritip, COUNT(*) AS n, MIN(c.fec) AS desde, MAX(c.fec) AS hasta FROM dbo.dcapro d JOIN dbo.con c ON c.ide = d.docide WHERE c.tip = 14 AND d.can < 0 GROUP BY ISNULL(d.docoritip, 0)`;
  `SELECT TOP 20 c.cod, c.fec, d.ide AS linea, d.proide, d.almide, d.can, d.pre, d.paride, m.ide AS mov, m.tip, m.oritip, m.destip, m.canent, m.cansal, m.pre AS mpre, m.prepma, m.almcan, m.almpma, m.fechor FROM dbo.dcapro d JOIN dbo.con c ON c.ide = d.docide LEFT JOIN dbo.mov m ON m.docide = d.docide AND m.linide = d.ide WHERE c.tip = 14 AND d.can < 0 ORDER BY d.ide DESC`;
  por cada `mov`, el anterior: `SELECT TOP 1 ide, almcan, almpma, fechor FROM dbo.mov WHERE proide = ? AND almide = ? AND ide < ? ORDER BY ide DESC`.
  Regla A si `canent` = can y `almpma` = (stock·pma + can·pre)/(stock + can); B si `cansal` = |can| y el PMP no cambia.
- **M6 vinculadas negativas**:
  `SELECT TOP 20 d.ide, d.can, d.linoriide, s.can AS ctrprodes_can, p.can AS ctr_can, p.canser FROM dbo.dcapro d JOIN dbo.con c ON c.ide = d.docide LEFT JOIN dbo.ctrprodes s ON s.lindeside = d.ide AND s.docdestip = 14 JOIN dbo.ctrpro p ON p.ide = d.linoriide WHERE c.tip = 14 AND d.docoritip = 44 AND d.can < 0 ORDER BY d.ide DESC`;
  `SELECT COUNT(*) AS descuadres FROM dbo.ctrpro p WHERE p.ide IN (SELECT linoriide FROM dbo.dcapro WHERE docoritip = 44 AND can < 0) AND ABS(p.canser - (SELECT ISNULL(SUM(s.can), 0) FROM dbo.ctrprodes s WHERE s.docproide = p.ide AND s.docdestip = 14)) > 0.001`.
- **M7 `dcapropar`**: `SELECT COUNT(*) AS lineas, SUM(CASE WHEN EXISTS (SELECT 1 FROM dbo.dcapropar x WHERE x.docproide = d.ide) THEN 1 ELSE 0 END) AS con_desglose, SUM(CASE WHEN ISNULL(d.parcandes, 0) <> 0 THEN 1 ELSE 0 END) AS parcandes FROM dbo.dcapro d JOIN dbo.con c ON c.ide = d.docide WHERE c.tip = 14 AND c.fec >= 20250101 AND d.paride > 0`.
- **M8 almacén de obra**:
  `SELECT n_almacenes, COUNT(*) AS obras FROM (SELECT obride, COUNT(*) AS n_almacenes FROM dbo.alm WHERE obride > 0 GROUP BY obride) x GROUP BY n_almacenes`;
  `SELECT SUM(CASE WHEN a.obride = t.obride THEN 1 ELSE 0 END) AS alm_de_su_obra, COUNT(*) AS n FROM dbo.ctr t LEFT JOIN dbo.alm a ON a.ide = t.almide`;
  `SELECT CASE WHEN a.obride = d.obride THEN 'alm_de_la_obra' ELSE 'otro' END AS tipo, ISNULL(a.paride, 0) AS alm_paride, CASE WHEN d.cenide = a.cenide THEN 1 ELSE 0 END AS cen_del_alm, COUNT(*) AS n FROM dbo.dcapro d JOIN dbo.con c ON c.ide = d.docide LEFT JOIN dbo.alm a ON a.ide = d.almide WHERE c.tip = 14 AND c.fec >= 20250101 AND ISNULL(d.paride, 0) = 0 GROUP BY CASE WHEN a.obride = d.obride THEN 'alm_de_la_obra' ELSE 'otro' END, ISNULL(a.paride, 0), CASE WHEN d.cenide = a.cenide THEN 1 ELSE 0 END`.
- **M9 ¿un `mov` por línea?**: `SELECT d.tipsininv, COUNT(*) AS albaranes, SUM(x.lineas) AS lineas, SUM(x.movs) AS movs FROM dbo.dca d JOIN dbo.con c ON c.ide = d.ide CROSS APPLY (SELECT (SELECT COUNT(*) FROM dbo.dcapro p WHERE p.docide = d.ide) AS lineas, (SELECT COUNT(*) FROM dbo.mov m WHERE m.docide = d.ide) AS movs) x WHERE c.tip = 14 AND c.fec >= 20260701 GROUP BY d.tipsininv`.
- **M10 fecha atrasada**: `SELECT TOP 20 m.ide, m.proide, m.almide, m.fechor, m.canent, m.almcan FROM dbo.mov m WHERE m.doctip = 14 AND m.fec >= 20260101 AND EXISTS (SELECT 1 FROM dbo.mov n WHERE n.proide = m.proide AND n.almide = m.almide AND n.ide < m.ide AND n.fechor > m.fechor) ORDER BY m.ide DESC`;
  para uno: `SELECT ide, fechor, canent, cansal, almcan, almpma FROM dbo.mov WHERE proide = ? AND almide = ? ORDER BY fechor, ide` → ¿el `almcan` de los posteriores incluye la entrada atrasada?
- **M11 productos genéricos e IVA**:
  `SELECT c.ide, c.cod, c.res, c.tip, c.emp, c.fecbaj, p.ivacomide, p.comide, p.natide, p.medide, p.gaside FROM dbo.con c JOIN dbo.pro p ON p.ide = c.ide WHERE c.cod IN (?, ?, ?, ?)` con `@("MA9999","SM9999","SB9999","QA9999")`;
  `SELECT TOP 30 d.cueide, d.ivaide, d.natide, d.unimed, d.caaide, COUNT(*) AS n FROM dbo.dcapro d JOIN dbo.con c ON c.ide = d.docide WHERE c.tip = 14 AND c.fec >= 20250101 AND d.proide = ? GROUP BY d.cueide, d.ivaide, d.natide, d.unimed, d.caaide ORDER BY n DESC` (el `ide` de MA9999);
  `SELECT i.ide, c.cod, i.iva FROM dbo.iva i JOIN dbo.con c ON c.ide = i.ide`.
- **M12 ¿mezcla el escritorio?**: `SELECT COUNT(DISTINCT d.ide) AS con_lineas_sin_vincular, (SELECT COUNT(*) FROM dbo.dca d2 JOIN dbo.con c2 ON c2.ide = d2.ide WHERE c2.tip = 14 AND c2.fec >= 20250101 AND d2.ctride > 0) AS con_contrato FROM dbo.dca d JOIN dbo.con c ON c.ide = d.ide JOIN dbo.dcapro p ON p.docide = d.ide WHERE c.tip = 14 AND c.fec >= 20250101 AND d.ctride > 0 AND ISNULL(p.docoritip, 0) <> 44`.
- **M13 ¿fila de `log` al crear un albarán?**: `SELECT COUNT(*) AS n FROM dbo.log WHERE ide > (SELECT MAX(ide) - 300000 FROM dbo.log) AND tab = 'con' AND tip = 14 AND ope = 1`, frente a los albaranes del mismo periodo.
- **M14 diff de columnas** (la lista de reseteo): `SELECT TOP 3 c.ide FROM dbo.con c JOIN dbo.dca d ON d.ide = c.ide WHERE c.tip = 14 AND d.ctride > 0 AND c.fec >= 20260901 ORDER BY c.ide DESC`; después `SELECT * FROM dbo.<con|dca> WHERE ide IN (?, ?, ?, ?)` y `SELECT * FROM dbo.dcapro WHERE docide IN (?, ?, ?, ?)` con esos tres y el de `AC26/15951`; anotar cada columna en que difieran.
- **M15 stock negativo**: `SELECT COUNT(*) AS n FROM dbo.mov WHERE almcan < 0 AND fec >= 20250101`.

## Manuales (T20-T24)

Setup y función `Q` de §Mediciones. Dry-run **clásico** (T20), el mismo cuerpo de junio:
`{ "database": "ruesma", "cod_contrato": "CTSU16/0206", "cod_obra": "0404", "cif_proveedor": "<CIF>",
"su_referencia": "prueba-F009", "lineas_recibidas": [ { "ctrpro_ide": <ide>, "cantidad": 1 } ] }`.

Dry-run **extendido** (T21; los `<...>` se leen antes del contrato y de las partidas de la obra):

```json
{ "database": "ruesma", "cod_obra": "0404", "cif_proveedor": "<CIF>", "cod_contrato": "CTSU16/0206",
  "referencia_externa": "ALB-prueba-F009-1", "su_referencia": "prueba-F009", "commit": false,
  "lineas": [
    { "referencia_linea": "1", "ctrpro_ide": <ide>, "cantidad": 1, "precio": 100.0, "almacen": true },
    { "referencia_linea": "2", "producto": "MA9999", "descripcion": "Prueba F-009", "unidad": "UD", "cantidad": 1, "precio": 1.0, "partida": "<cod>" },
    { "referencia_linea": "3", "ctrpro_ide": <ide>, "cantidad": -1, "precio": 100.0, "partida": "<cod>" } ] }
```

**Primera devolución real (T24)**, solo lectura, con la `referencia_externa` de ese albarán:

- líneas y su `mov`: `SELECT d.ide AS linea, d.proide, d.almide, d.can, d.pre, d.linoriide, m.ide AS mov, m.canent, m.cansal, m.almcan, m.almpma FROM dbo.dcapro d JOIN dbo.dca a ON a.ide = d.docide LEFT JOIN dbo.mov m ON m.docide = d.docide AND m.linide = d.ide WHERE a.synckey = ? AND d.can < 0`;
- `mov` anterior: `SELECT TOP 1 ide, almcan, almpma FROM dbo.mov WHERE proide = ? AND almide = ? AND ide < ? ORDER BY ide DESC`
  → cuadra si `almcan` = anterior + `can` y `almpma` = (anterior·pma + `can`·`pre`)/(anterior + `can`);
- medición: `SELECT p.ide, p.can, p.canser, (SELECT SUM(s.can) FROM dbo.ctrprodes s WHERE s.docproide = p.ide AND s.docdestip = 14) AS suma_destinos FROM dbo.ctrpro p WHERE p.ide = ?`
  → `canser` = `suma_destinos`; y `SELECT estser, estfac FROM dbo.ctr WHERE ide = ?` frente a `Σcanser ≥ Σcan`;
- en la UI, la ficha de stock del producto en ese almacén debe dar el mismo stock y PMP.

## Forma final para alinear F-053 (pregunta 18, la hace el líder de albaranes) — v3

> **Contrato completo con albaranes (2026-10-05):**
> `specs/F-009-alta-albaran-compra/contrato_albaranes.md` — petición y respuesta campo a campo, casos
> de línea (almacén, devoluciones, compuestas repartidas), códigos → estados de F-053 y **33 huecos**
> entre F-009 v4, F-053 v5, F-051 v3 y F-049 v4 (9 bloqueantes). Lo de abajo es el resumen de la v3.

Ruta `POST /api/sigrid/albaran` (la de siempre), modo extendido. Petición:

```json
{ "database": "ruesma", "cod_obra": "0404", "cif_proveedor": "<CIF>", "cod_contrato": "CTSU16/0206 o null",
  "referencia_externa": "ALB-<document_id>", "su_referencia": "<nº de albarán del proveedor, ≤128>",
  "usu": "<usuario de Sigrid, ≤24>", "fecha_albaran": 20261001, "empide": null, "commit": false,
  "lineas": [ { "referencia_linea": "<id de línea, ≤64>", "ctrpro_ide": 123, "producto": null,
                "descripcion": "<≤128, obligatoria sin vincular>", "unidad": "<≤8>", "cantidad": -2.5,
                "precio": 10.0, "partida": "<cod de obrparpar>", "almacen": false } ] }
```

Exactamente uno de `ctrpro_ide`/`producto` y uno de `partida`/`almacen:true`; `cantidad` ≠ 0
(negativa = devolución, en los dos tipos); `precio` ≥ 0 obligatorio; `ctrpro_ide` exige
`cod_contrato`; **no** enviar `lineas_recibidas` (→ `peticion_mixta`). **Nuevo en v3:** `usu`
obligatorio (va a la fila de alta de `log`; F-053 ya tiene `ALTA_SIGRID_USUARIO`), y el
proveedor tiene que tener algún albarán previo (si no, `proveedor_sin_albaran_previo`: ya no se
copia la cabecera de otro proveedor, así que el antiguo aviso «plantilla de otro proveedor»
desaparece y pasa a ser este error).

Respuesta 200 (dry-run, commit o idempotente): todos los campos de la respuesta clásica (`ok`,
`database`, `committed`, `dry_run`, `con_ide`, `cod`, `contrato`, `cabecera`, `lineas`,
`movimientos`, `estados_contrato`, `totales`, `warnings`) más `estado`
(`previsto`|`creado`|`idempotente`), `referencia_externa`, `avisos[{codigo, mensaje}]` y
`filas`; cada línea suma `indice`, `referencia_linea`, `tipo` (`vinculada`|`sin_vincular`),
`producto`, `paride`, `partida`, `almacen`, `cenide` y `avisos`. Error 400: `{ok:false, error,
details:{type, codigo, lineas?:[{indice, referencia_linea, codigo, mensaje}]}}`; 400 sin
`codigo` = validación Pydantic (`details.validation`); 500 = inesperado.

Códigos de error: `peticion_mixta`, `escritura_albaranes_deshabilitada`,
`base_de_datos_no_permitida`, `demasiadas_lineas`, `referencia_no_permitida`,
`referencia_en_conflicto`, `obra_no_encontrada`, `obra_ambigua`, `contrato_no_encontrado`,
`contrato_ambiguo`, `usuario_no_valido`, `proveedor_sin_albaran_previo`, `estado_inicial_no_encontrado`,
`almacen_de_obra_no_resuelto`, `colision_de_clave`, `filas_afectadas_inesperadas`,
`lineas_no_validas`; por línea: `linea_no_es_del_contrato`, `producto_no_permitido`,
`producto_no_encontrado`, `partida_no_encontrada`, `partida_ambigua`, `partida_no_imputable`.
Avisos: `producto_sin_historico`, `supera_pendiente`,
`partida_distinta_del_contrato`, `precio_distinto_del_contrato`, `servido_negativo`,
`stock_negativo`, `cod_provisional`. Para F-053: los «avisos bloqueantes» pasan a compararse por
`codigo`, no por texto; `colision_de_clave` y los 500 se pueden reintentar con la misma
referencia (la idempotencia lo hace seguro).

## Preguntas de la v3: respondidas por el humano (2026-10-02)

- **N1 → (b).** El movimiento de stock se fecha en el momento del alta (`mov.fec`, `hor` y
  `fechor` de ahora, hora de Madrid); el albarán conserva su fecha. No se recalculan los `mov`
  posteriores. El balance vigente se lee por `fechor DESC, ide DESC` (R19, design §Fecha
  atrasada, L12/E7).
- **N2 → rechazo.** Código de partida repetido entre las imputables de la obra: la línea falla
  con `partida_ambigua` y el revisor lo corrige en sv4 (R14). Sin `paride` en la petición.
- **N3 → retirar el script.** En cuanto T0 quede cerrada, y antes de T1, un commit propio con
  `git rm scripts/medir_f009_t0.py tests/test_f009_t0_script.py`: sale del alcance de cobertura
  y mutación y queda en el historial (tasks T0). **Todavía no se retira**: el humano va a
  repetir `--solo M3 M7 M9 M11 M13 M14`.

No quedan preguntas de diseño abiertas. Las 1-17 de la v1 están respondidas y la 18 (alinear
F-053) es del líder de albaranes; para F-053, N1 no cambia el contrato.

## Riesgo residual

Ninguna escritura hasta T22, con autorización expresa, y T22 no se hace sin M9 cerrada (puerta
H20). Al desplegar con la llave en `false`, el `commit` del modo clásico y de `albaran-directo`
queda cerrado (decidido; nadie los usa en vivo). Devoluciones con la regla A medida en el
escritorio; T24 vigila la primera real del pipeline. Hasta la repetición única de T0 (`--solo M3
M7 M9 M11 M13 M14 M16 M17 M18`), su volcado en la spec (v6 si alguna regla condicional cambia), la
retirada del script (N3) y las respuestas a N4-N12, F-009 no pasa a `in_progress`.
