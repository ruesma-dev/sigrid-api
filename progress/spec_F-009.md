<!-- progress/spec_F-009.md -->
# Spec F-009 · Alta de albaranes de compra para el pipeline (PRE-1 de albaranes F-053)

Spec-author, 2026-10-01. Rama `feature/F-009-alta-albaran-compra` desde `dev` (2a5ac24).
Estado `spec_ready`, `sdd`, rigor `critico`. Spec en `specs/F-009-alta-albaran-compra/`.
**No se ha llamado a la API, ni a Azure, ni al SQL Server**: todo lo que depende de cómo
trabaja el escritorio de Sigrid queda como medición de solo lectura (T0, abajo).

`bash harness/init.sh` en verde (1733 tests) **con el venv del proyecto**. Lanzado desde una
sesión con `VIRTUAL_ENV` heredado de otro repositorio (albaranes), salía en rojo por
`azure.functions` ausente: el portero respeta un venv ya activado y no antepone el suyo.
No es un fallo del repo; quien lo ejecute desde otra sesión debe hacerlo sin ese `VIRTUAL_ENV`.

## Qué pide F-053 y cómo queda

Fuente: `albaranes-F-053/specs/F-053-alta-sigrid/design.md` §2 y `progress/spec_F-053.md`.

| Necesidad (humano, 2026-10-01) | En la spec |
|---|---|
| Mezclar vinculadas (`ctrpro`, consumen medición) y sin vincular; contrato opcional | R2, R9-R11; `cod_contrato` opcional |
| Partida por línea (código → `paride`), nunca heredada, o almacén | R12, R13 |
| Partida de una vinculada distinta de la del `ctrpro` | R14: se permite, `ctrpro` intacto, aviso (pregunta 5) |
| Producto: vinculadas, el del `ctrpro`; sin vincular, por código (MA9999…) | R10, R11 + lista blanca (pregunta 4) |
| Precio aprobado por nosotros; convivencia con el del contrato | R15: manda el nuestro; si difiere, `tar` = precio, `dto` `''` y aviso (pregunta 6) |
| Negativas ya: stock, PMP, `canser` como el escritorio | R16 + M5/M6 (preguntas 7 y 8) |
| Idempotencia `referencia_externa` → `dca.synckey` | R27, R28 + M1 (pregunta 3) |
| Errores con código y respuesta por línea | R3, R4, design §Códigos |
| Clave de siempre; ¿segunda llave? | R5, R22 y R7 (pregunta 2) |
| Retrocompatibilidad de los dos endpoints | Ruta nueva: R6 (pregunta 1) |
| Evaluar `dcapropar` y `almide`/`cenide` por línea | Fuera salvo M7; derivados, no en la petición (pregunta 12) |

## Hallazgos del código actual (no se corrigen en los endpoints viejos)

1. **No hay ni un test** de `sigrid/albaran` ni de `albaran-directo`: el núcleo solo está
   validado a mano (junio, `AC26/15950-15952`). De ahí el test de equivalencia (R31).
2. El `cod` se calcula **fuera** de la transacción (`_next_cod`): carrera con el escritorio.
3. `con.est = 1` y `mov.emp = 1` están **escritos a mano**; la serie `AC` medida en junio
   (`serie_stock.txt`, sin versionar) tenía `sercon.estini = 0`. Choca con ARCHITECTURE §7.
4. Fecha y hora con `datetime.now()`: en Azure es **UTC**, no Madrid.
5. La `dcapro` se clona de la **última línea del mismo producto en cualquier obra**: si el
   `ctrpro` trae `paride`/`cenide`/`caaide` `NULL`, se quedan los de esa otra línea, y
   siempre arrastra medición, analítica, desglose y `prepma` ajenos. `albaran-directo` hereda
   además el almacén y la partida.
6. `su_referencia` admite 200 caracteres y `dca.entref` es de 128.
7. `lineas_recibidas` repetidas sobre el mismo `ctrpro` se **suman** en una sola `dcapro`.
8. Tasa de IVA = `ivacuo/tot` del `ctrpro`: con `tot` 0 sale 0.

## Mediciones (T0) — solo lectura, por `sql/read`

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

## Manuales (T19-T21)

Plantilla del cuerpo del dry-run (los `<...>` se leen antes, del contrato `CTSU16/0206` y de las partidas de la obra):

```json
{ "database": "ruesma", "cod_obra": "0404", "cif_proveedor": "<CIF de GARSAN>", "cod_contrato": "CTSU16/0206",
  "referencia_externa": "ALB-prueba-F009-1", "su_referencia": "prueba-F009", "commit": false,
  "lineas": [
    { "referencia_linea": "1", "ctrpro_ide": <ctrpro_ide>, "cantidad": 1, "precio": 100.0, "almacen": true },
    { "referencia_linea": "2", "producto": "MA9999", "descripcion": "Prueba F-009", "unidad": "UD", "cantidad": 1, "precio": 1.0, "partida": "<cod>" },
    { "referencia_linea": "3", "ctrpro_ide": <ctrpro_ide>, "cantidad": -1, "precio": 100.0, "partida": "<cod>" } ] }
```

## Preguntas al humano (PARADA 1)

1. **Ruta nueva `sigrid/albaran-compra`** (propuesta; design «La decisión de fondo») o ampliar
   `sigrid/albaran` con un modo según los campos.
2. **Segunda llave `SIGRID_ALBARAN_WRITE_ENABLED`**, defecto `false`, para la ruta nueva.
   ¿Gobierna también el `commit` de `sigrid/albaran` y `albaran-directo` (R7, T13)?
   Propuesta: **sí**; hoy los dos escriben con solo `SIGRID_DOMAIN_WRITE_ENABLED` y nadie los
   usa en vivo. Con `false` en el despliegue, su `commit` queda cerrado hasta que lo abras.
3. **Prefijo de la referencia**: propuesta `["ALB-"]` y F-053 envía `ALB-<document_id>`.
4. **Productos sin contrato**: propuesta `["MA9999"]` al desplegar; añadir SM9999, SB9999 o
   QA9999 es cambiar la App Setting.
5. **Partida distinta en una vinculada** (R14): se permite con aviso (propuesta) o se rechaza.
6. **Precio distinto en una vinculada** (R15): manda el nuestro, `tar` = precio y `dto` `''`
   (se pierde el desglose bruto/descuento del contrato), con aviso.
7. **Devolución que deja `canser` < 0** (R16): se rechaza la línea (propuesta) o se admite.
8. **Si M5 no encuentra devoluciones reales**: ¿hipótesis A (design §Devoluciones), o las
   negativas se quedan fuera hasta tener una que medir?
9. **`dcapropar`**: fuera, salvo que M7 diga que el escritorio lo escribe siempre.
10. **Fila de `log`** al crear: fuera, salvo M13.
11. **Fecha atrasada**: no se recalculan los `mov` posteriores (como hoy). Si M10 dice que el
    escritorio sí, ¿se acepta el desfase o se para?
12. **Almacén y centro por línea**: derivados (R13), no en la petición. ¿De acuerdo?
13. **`con.est`**: el valor que dé M2 (hoy se escribe 1 a mano; la serie dice `estini` 0).
14. **Lista de reseteo** (R19): solo en la ruta nueva; los endpoints viejos siguen clonando
    como hoy (ver hallazgo 5). ¿Ficha aparte para ellos?
15. **Hora de Madrid e IVA por `dbo.iva`**: solo en la ruta nueva (diferencias de R31).
16. **Endpoints viejos**: ¿se marcan obsoletos en `sigrid_api.md` cuando F-053 esté en real?
17. **Prioridad**: F-009 queda con prioridad 9; ¿va antes que F-007 y F-008? (propuesta: sí,
    es precondición de F-053).
18. **F-053 debe alinearse** (lo hace el líder de albaranes): una lista `lineas` con
    `ctrpro_ide` **o** `producto` por línea, `precio` obligatorio, `referencia_externa` con
    prefijo, códigos de design §Códigos, y la ruta `sigrid/albaran-compra`.

## Riesgo residual

Ninguna escritura hasta T20, con autorización expresa. Varios puntos de la spec, marcados [Mn],
dependen de T0: es deliberado, porque decidirlos sin medir era inventar cómo trabaja el
escritorio de Sigrid. Si T0 contradice algo, la spec se corrige antes de `in_progress`.
