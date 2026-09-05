<!-- progress/verificacion_F-004_t18_t19.md -->
# F-004 · T18 y T19 contra producción (2026-09-06)

Todo [MEDIDO]. Ninguna escritura: `SIGRID_DOCUMENT_WRITE_ENABLED=false` en la
Function App y ningún `commit:true` aceptado. Script: `t19_dry_run.py` del
scratchpad de la sesión (no se versiona: solo llama a la API con el `.env`).

## T18 — despliegue y App Settings

- `func azure functionapp publish func-sigridapi-dev-huyke --python` desde
  `dev` = `main` = `70ac430`: la lista final incluye `sigrid_concepto_grafico`
  junto a las siete rutas anteriores.
- App Settings fijadas por fichero JSON y releídas con `az … appsettings list`:

| Clave | Valor |
|---|---|
| `ALLOWED_WRITE_DATABASES` | `["ruesma"]` (sin cambios) |
| `SIGRID_DOMAIN_WRITE_ENABLED` | `true` (ya estaba) |
| `SIGRID_DOCUMENT_WRITE_ENABLED` | **`false`** |
| `SIGRID_DOCUMENT_WRITE_DATABASE` | `ruesma_rep` |
| `SIGRID_DOCUMENT_ALLOWED_CONTIP` | `[708]` |
| `SIGRID_DOCUMENT_ALLOWED_GRATIPIDE` | `[35]` |

- Control tras publicar y **antes** de las App Settings: el guardia de F-003
  sigue activo (`msdb` dentro del SQL → 400), la lectura cruzada legítima → 200,
  y `concepto-grafico` → 400 `escritura_documental_deshabilitada` tanto en
  dry-run como con `commit:true` (R4/R6: cerrado por defecto).

## T19 — dry-run (100 % lectura)

`MAX(ide)` antes y después, idénticos: `ruesma.gra` 298417, `ruesma_rep.gra`
359572, `rcg` 298857.

**Huérfana real de clase 35:** `gra.ide` 236774, `cod`
`202505231205227262.aechevarria`, `fec` 20250523, concepto **2530061**
(`RS25.05/0662`, tip 708, «Lámina del salón mal puesta…»).

**Reclamación normal 2811179 (`RS26.08/0123`, la pareja de T1)** → 200,
`ok:true committed:false dry_run:true idempotente:false filas_afectadas:0`,
`grafico.bytes` 303, `cod` `202609060129488219.aechevarria` (sello en hora de
Madrid: 01:29 del 06), `enlace.pos` 128 (ya tenía un gráfico en 64). Las dos
filas que escribiría, columna a columna iguales a lo medido en
`explore_F-004_mediciones.md` §2.1-2.3:

| Columna | documental (ide prov. 359573) | negocio (ide prov. 298418) |
|---|---|---|
| `cod` / `emp` / `usu` / `fec` | `202609060129488219.aechevarria` / 1 / aechevarria / 20260906 | **iguales** |
| `nom` = `nomori` | `prueba_f004.pdf` | igual |
| `res` | `''` | `PRUEBA API - BORRAR` |
| `gratipide` | 0 | 35 |
| `vin` | 3 | 3 |
| `ima` | 303 bytes | NULL |
| `tex`, `cam`, `pul` | NULL | NULL |
| `cla`, `guid`, `texrev`, `salusu`, `saltex` | `''` | `''` |
| `estcon`, `tipocu`, `numrev`, `salfec`, `salhor`, `mntide`, `graant`, `anx`, `ori`, `tip` | 0 | 0 |

Enlace: `{ide 298858, con 2811179, gra 298418 (el de negocio), pos 128, cla 0,
feclee 0, fecalt 0}`. Aviso del dry-run: los tres `ide` son provisionales.

**Concepto de la huérfana 2530061** → 200, `idempotente:false`, `pos` 192, y el
aviso esperado: «El concepto tiene 1 grafico(s) sin binario en la base
documental (ide 236774). No se reparan: se adjunta uno nuevo.»

**Negativos:**

| Caso | Respuesta |
|---|---|
| `conide` de un contrato (2441136) | 400 `tipo_de_concepto_no_coincide` — «El concepto es de tipo 44 y la peticion dice 708» |
| Un PNG | 400 `tipo_de_fichero_no_permitido` — firmas permitidas `%PDF-` |
| `usu` inventado | 400 `usuario_no_valido` |
| `commit:true` con la escritura documental cerrada | 400 `escritura_documental_deshabilitada` |

**Criterio de T19: cumplido.** Para la obra 404, el tipo de concepto de un
contrato es **44** (medido en el negativo); un albarán tendrá el suyo.

## Queda: T20 y T21

Primer `commit:true` con autorización expresa del humano, sobre la reclamación
que elija (candidata: 2811179, que ya tiene un gráfico real y no es huérfana),
con `SIGRID_DOCUMENT_WRITE_ENABLED=true` solo durante esa ventana; después
`documents/read` por `cod`, las cuatro consultas de comprobación y la
repetición idempotente (T21).
