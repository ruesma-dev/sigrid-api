<!-- progress/explore_F-018.md -->
# F-018 · Medición en producción del descuento por línea (solo lecturas)

Medido el 2026-10-28 por `POST /api/sql/read` de la API desplegada (base `ruesma`), SQL parametrizado con `?`,
`truncated` comprobado en cada respuesta (ninguna truncada) y consultas acotadas por fecha (la más lenta, 11,4 s).
Script y salidas en el scratchpad del spec-author, fuera del repositorio. Sin nombres de personas ni de proveedores.
Numeración a continuación de [`explore_F-016.md`](explore_F-016.md) (M41-M44, en la rama de F-016).

Universo salvo que se diga otra cosa: albaranes de compra `con.tip 14`, `emp 1`, `con.fec >= 20250101` (67.586
albaranes, 298.031 líneas). «Con dto» = `LTRIM(RTRIM(ISNULL(dcapro.dto, ''))) <> ''`. `d` = el número de `dto`
(`REPLACE` de `%` y de la coma decimal, `TRY_CONVERT(decimal(18,6))`).

## M45 · Formato de `dcapro.dto` (texto de 24)

- **Con dto: 24.616 líneas (8,3 %) en 7.541 albaranes (11,2 %).** Valores: `40%` 15.593 (63 %), `7%` 1.255, `25%`
  1.128, `1%` 1.080, `15%` 559, `20%` 494, `2%` 484, `42%` 471… y con decimales `1,5%` 143, `3,5%` 99, `2,5%` 69,
  `0,01%` 51, `32,5%` 9, `21,45%` 5, `0,001%` 8, `0,0001%` 5.
- **Forma única**: número con **coma decimal** seguido de `%`, sin espacios ni signo. 24.616 de 24.616 llevan `%` y
  ninguno más de uno; 0 con punto, 0 con `+`, 0 con `-`; 0 que no se lean como número. Sin ceros a la derecha
  (`1,5%`, nunca `1,50%`): 415 con un decimal, 107 con dos, 20 con más de dos. Mínimo 0,00001; máximo 99,99.
- **Sin cascada nunca**: 0 en las 48.588 líneas con dto de 2020-2024 (M45g) y 0 en los 1.783 `ctrpro` con dto desde
  2024 (M49f), que tienen el mismo formato.

## M46 · Cómo calcula Sigrid la línea: `tar` es el bruto, `pre` el neto

El diccionario lo dice (`tar` «P.Bruto», `pre` «Precio», `dto` «Descuentos», `tot` «Importe Línea») y los datos lo
confirman. En las 23.993 líneas con dto y `can` ≠ 0:

| Regla | Líneas | % |
|---|---|---|
| `tot` = ROUND(`can`·`tar`·(1 − `d`/100), 2) en `decimal` (redondeo **mitad lejos del cero**) | 23.990 | 99,99 |
| `pre` = `tot` / `can` (sin redondear) | 23.991 | 99,99 |
| las dos | 23.990 | 99,99 |
| `tot` = ROUND(`can`·`pre`, 2) (consecuencia: `pre` ya es neto) | 24.614 de 24.616 | 99,99 |
| `tot` = ROUND(`can`·`pre`·(1 − `d`/100), 2) (`pre` bruto) | 664 de 24.616 | 2,7 |
| `tar` = `pre` | 62 de 24.616 | 0,3 |

- El redondeo es sobre el producto **exacto**: 1 × 18,625 × 0,60 = 11,175 → **11,18** (`ROUND` sobre `float` da
  11,17); 1 × 265 × 0,965 = 255,725 → **255,73**; −0,4 × 1.275,68 × 0,975 = −497,5152 → **−497,52**. Es `Decimal`
  con `ROUND_HALF_UP`, el `redondear_euros` de F-009 (H33).
- `pre` = `tot`/`can`: 36 × 4,278 × 0,60 = 92,4048 → `tot` 92,40 y `pre` 2,566666…; 0,3 × 12.825 × 0,99 = 3.809,025
  → 3.809,03 y `pre` 12.696,766…. Por eso `pre` no es `ROUND(tar·(1 − d), k)` para ningún `k` (de 2 a 6 decimales
  casan entre 11.657 y 7.849).
- Excepciones (3): una con el dto escrito y sin aplicar (`tot` = `can`·`tar`) y dos a un céntimo.
- `can` 0 con dto (623): `tot` 0 y `pre` = `tar`·(1 − `d`/100) en las 623.
- **Sin dto** (273.415 líneas): `tar` = `pre` en el **100 %**; `tot` = ROUND(`can`·`pre`, 2) en 228.320 de 228.352 con
  `can` ≠ 0. Es lo que hace hoy F-009 (`pre` = `tar` = `precio`, `dto` `''`).

## M47 · Cabecera `dca` de los 7.541 albaranes con dto

| Columna | Regla | Albaranes |
|---|---|---|
| `impbru` | Σ ROUND(`can`·`tar`, 2) de sus líneas (bruto) | **7.541** (= Σ `tot`: 32) |
| `impnet` | = `totbas` | 7.541 |
| `totbas` | Σ `tot` (neto) | 7.540 |
| `impdes`, `imprec` | 0 (el dto de línea no va al descuento de cabecera) | 7.541 |
| `totdoc` | `totbas` + `totiva` | 7.541 |
| `totiva` | Σ `ivacuo` | 7.441 (100 no; no se atribuye al dto, fuera de alcance) |

- `ivacuo` = ROUND(`tot`·`iva`, 2) sobre el **neto**: 24.615 de 24.616 (M47d).
- En todos los `AC` desde 2025 (67.682), `impdes` ≠ 0 en 2 y `impnet` ≠ `totbas` en 2: el descuento de cabecera no se
  usa; `impbru` ≠ `totbas` en 7.513, que son los albaranes con dto.

## M48 · El `mov` y el PMP van con el neto

22.368 `mov` de líneas con dto (`mov.linide` = `dcapro.ide`, `doctip` 14): `mov.pre` = `mov.prc` = `dcapro.pre`
(neto) en **22.366**; = `tar` en 32 (las que no tienen dto efectivo). `canent` = `can` en todas y `dcapro.prepma` =
`mov.prepma` en todas. El `almpma` se calcula con el neto. De las 24.614 líneas, 22.393 son de productos con
`pro.tipmov` 1.

## M49 · Vinculadas: el dto de la línea frente al del `ctrpro`

| Vinculadas desde 2025 (`docoritip` 44) | 101.097 |
|---|---|
| Línea con dto | 2.267 (2,2 %) |
| `ctrpro` con dto | 2.256 |
| Los dos, **mismo** texto | **2.243** |
| Los dos, distinto | 1 (40 % frente a 50 %, y otro `tar`) |
| Solo la línea (el `ctrpro` sin dto) | 23 |
| Solo el `ctrpro` (la línea sin dto, con `pre` = `tar`) | 12 |

- Con los dos con dto (2.244): `tar` igual al del `ctrpro` en 2.238; `pre` igual en 1.451 (el neto depende de `can`).
- El `ctrpro` sigue la misma regla que `dcapro` (M49h, 1.783 con dto desde 2024): `tot` = ROUND(`can`·`tar`·(1 − `d`),
  2) en 1.783, `tot` = ROUND(`can`·`pre`, 2) en 1.783 y `pre` = `tot`/`can` en 1.758. **`ctrpro.pre` es neto.**
- `ctrprodes.can` = `dcapro.can` en las 2.267 (M49g): `canser` cuenta cantidad; el dto no lo toca.
- Consecuencia para F-009 (opción C, R17): hoy una vinculada sin dto en la petición compara `precio` con
  `ctrpro.pre`, que es **neto**; si casa, copia `pre`, `tar` y `dto` del `ctrpro`, que es la forma de Sigrid.

## M50 · Proformas con dto

Proformas desde 2025 (`cod LIKE 'PROF%'`, `cla 141` o `entref LIKE 'PROF%'`): 8.989 con 110.910 líneas. **Con dto:
211 (2,3 %)** en 44 contratos, 2.309 líneas, 1.024 de ellas en 52 proformas a origen. Vinculadas en su mayoría
(`1%` 1.080 líneas, 1.040 vinculadas; `2%` 360, todas): el dto es el del contrato. Las de `40%` (70) y `7%` (18), sin
vincular. Ejemplo: `PROF26/01377`, 1 %, con `tot` y `pre` por la regla de M46.

## M51 · Obra 0692 (la del caso de albaranes)

2.519 líneas de `AC` desde 2025; 271 con dto; 102 dadas de alta por la API (`synckey` `ALB-%`), de ellas 16 con un
`pre` de más de 2 decimales (el neto `importe/cantidad` de sv9, sin dto).

## Hallazgo documental

`docs/ARCHITECTURE.md` §Semántica 9 y `azure-apps/sigrid_api.md` §9.4/§12 dicen que `canfac * pre` «ignora el
descuento de línea». En albaranes y contratos desde 2024-2025 **no** es así: `pre` es el neto (M46, M49h) y
`can`·`pre` = `tot` salvo el redondeo. Prorratear sobre `tot` sigue siendo lo correcto (exacto al céntimo); lo que
falla es el motivo. No se mide aquí `dcf`/`dcfpro`.
