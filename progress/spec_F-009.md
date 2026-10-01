<!-- progress/spec_F-009.md -->
# Spec F-009 · Alta de albaranes de compra para el pipeline (PRE-1 de albaranes F-053) — v2

Spec-author. v1 y **v2 del 2026-10-01** (respuestas del humano a la PARADA 1). Rama
`feature/F-009-alta-albaran-compra` desde `dev` (2a5ac24). Estado `spec_ready`, `sdd`, rigor
`critico`, prioridad 7 (antes que F-007 y F-008). Spec en `specs/F-009-alta-albaran-compra/`.
**No se ha llamado a la API, ni a Azure, ni al SQL Server**: lo que depende de cómo trabaja el
escritorio de Sigrid queda como medición de solo lectura (T0) o como verificación manual.

`bash harness/init.sh` en verde **con el venv del proyecto**. Desde una sesión con `VIRTUAL_ENV`
heredado de otro repositorio sale en rojo (`azure.functions` ausente): el portero respeta un
venv ya activado. No es un fallo del repo; se lanza sin esa variable.

## Qué cambia en la v2

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
  distintos del contrato con aviso; `dcapropar` y `log` fuera salvo M7/M13; sin recálculo de
  `mov` posteriores; almacén y centro derivados; `con.est` según M2; lista de reseteo, hora de
  Madrid e IVA por `dbo.iva` solo en el modo extendido; los viejos, obsoletos cuando F-053 esté
  en real (T18); prioridad 7.

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

## Forma final para alinear F-053 (pregunta 18, la hace el líder de albaranes)

Ruta `POST /api/sigrid/albaran` (la de siempre), modo extendido. Petición:

```json
{ "database": "ruesma", "cod_obra": "0404", "cif_proveedor": "<CIF>", "cod_contrato": "CTSU16/0206 o null",
  "referencia_externa": "ALB-<document_id>", "su_referencia": "<nº de albarán del proveedor, ≤128>",
  "fecha_albaran": 20261001, "empide": null, "commit": false,
  "lineas": [ { "referencia_linea": "<id de línea, ≤64>", "ctrpro_ide": 123, "producto": null,
                "descripcion": "<≤128, obligatoria sin vincular>", "unidad": "<≤8>", "cantidad": -2.5,
                "precio": 10.0, "partida": "<cod de obrparpar>", "almacen": false } ] }
```

Exactamente uno de `ctrpro_ide`/`producto` y uno de `partida`/`almacen:true`; `cantidad` ≠ 0
(negativa = devolución, en los dos tipos); `precio` ≥ 0 obligatorio; `ctrpro_ide` exige
`cod_contrato`; **no** enviar `lineas_recibidas` (→ `peticion_mixta`).

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
`contrato_ambiguo`, `proveedor_sin_albaran_previo`, `estado_inicial_no_encontrado`,
`almacen_de_obra_no_resuelto`, `colision_de_clave`, `filas_afectadas_inesperadas`,
`lineas_no_validas`; por línea: `linea_no_es_del_contrato`, `producto_no_permitido`,
`producto_no_encontrado`, `partida_no_encontrada`, `partida_ambigua`, `partida_no_imputable`.
Avisos: `plantilla_de_otro_proveedor`, `producto_sin_historico`, `supera_pendiente`,
`partida_distinta_del_contrato`, `precio_distinto_del_contrato`, `servido_negativo`,
`stock_negativo`, `cod_provisional`. Para F-053: los «avisos bloqueantes» pasan a compararse por
`codigo`, no por texto; `colision_de_clave` y los 500 se pueden reintentar con la misma
referencia (la idempotencia lo hace seguro).

## Preguntas abiertas

Ninguna de diseño: las 1-17 están respondidas y la 18 es del líder de albaranes. Queda **T0**:
si alguna medición contradice un punto [Mn] (sobre todo M2 `est`/`emp`, M5 devoluciones, M8
almacén de obra, M14 lista de reseteo), la spec se corrige y vuelve a la PARADA 1.

## Riesgo residual

Ninguna escritura hasta T22, con autorización expresa. Al desplegar con la llave en `false`, el
`commit` del modo clásico y de `albaran-directo` queda cerrado (decidido; nadie los usa en
vivo). Las devoluciones van con la hipótesis A si M5 no da muestra: riesgo aceptado, T24 lo
vigila.
