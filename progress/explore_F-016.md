<!-- progress/explore_F-016.md -->
# F-016 · Medición en producción de la proforma a origen (solo lecturas)

Medido el 2026-10-28 por `POST /api/sql/read` de la API desplegada (base `ruesma`), SQL parametrizado con `?`,
`truncated` comprobado en cada respuesta y consultas acotadas por fecha, contrato o documento (la más lenta, 5,3 s).
Script y salidas en el scratchpad del spec-author, fuera del repositorio. Sin nombres de personas ni de proveedores.
Lo ya medido no se repite: **M11** y **M16-M26** de [`explore_F-007.md`](explore_F-007.md) (cadena `docoriide`,
arrastre, M25 elegir la anterior, M26 detectar la ya registrada) y **M37** (contratos que van a origen) siguen valiendo.

«A origen» = `con.tip 14`, `emp 1`, `dca.docoritip 1`, `dca.ctride > 0`, `con.fec >= 20250101`, **cualquier serie**
(`PROF` y `AC`: la cadena mezcla series, M19). «Primera» = `docoriide 0`; «encadenada» = `docoriide > 0`.

## M41 · Columnas a origen de las líneas, primeras y encadenadas

| Clase | Tipo | Líneas | `can` 0 | Con `canorilin` | Sin `canorilin`: `canoriori` = `can` | ≠ `can` | `canoriant` ≠ 0 | `imporiant` ≠ 0 | Docs |
|---|---|---|---|---|---|---|---|---|---|
| primera | vinculada | 3.738 | 2.465 | 0 | **3.736** | 2 | 0 | 0 | 293 |
| primera | sin vincular | 462 | 104 | 0 | 444 | 18 | 9 | 15 | 121 |
| encadenada | vinculada | 41.716 | 30.330 | 39.822 | **1.887** | 7 | 0 | 0 | 1.883 |
| encadenada | sin vincular | 16.500 | 12.433 | 13.999 | 2.452 | 49 | 33 | 25 | 1.464 |

- **Sigrid no siembra el origen**: en la primera de una cadena `canoriori` = `can` (99,9 % de las vinculadas), también
  cuando el contrato ya tenía proformas de mes (M43). Las líneas **nuevas** de una encadenada (sin `canorilin`),
  igual: `canoriori` = `can` en 1.887 de 1.894.
- `canoriant` e `imporiant` van a 0 (≥ 99,8 % en las cuatro filas).

## M42 · Qué líneas lleva la primera de una cadena

Primeras con contrato desde 2025 (342), por sus vinculadas frente a las líneas del contrato:

| Forma | Docs | Vinculadas | Con MES | Líneas del contrato |
|---|---|---|---|---|
| Solo las del mes | **151** | 587 | 583 | 5.865 |
| Todas las del contrato | 96 | 1.960 | 451 | 1.960 |
| Parte, con algunas a 0 | 46 | 1.191 | 235 | 1.719 |
| Sin vinculadas | 49 | 0 | 0 | 1.352 |

La forma más común es **solo las partidas del mes**: es la de la proforma de mes de F-007, con `docoritip 1`.

## M43 · Contratos que cambian de modo

Contratos con proformas de mes (`docoritip 0`, `entref` o serie `PROF`, sin `PREV`) y a origen desde 2025: **64**.
Secuencia por fecha (O = a origen, M = de mes): `OM` 43, `OMO` 10, `OMOMO` 4, `MO` 4, `MOMO` 1, `MOM` 1,
`OMOMOMOMOM` 1. En los **29 pasos de mes a origen**:

- **22 retoman la cadena vieja**: su `docoriide` es la última a origen, saltándose los meses registrados de mes. La
  cadena acumula sin esos meses (lo que ya advertía M37). Ejemplo: contrato con cinco PROF a origen de febrero a junio
  de 2025, julio como `AC` de mes y agosto a origen colgando de junio.
- 5 empiezan cadena nueva (`docoriide 0`); en un caso la de mes se anuló (`AC` negativa) y se rehízo a origen.
- 2 cuelgan de un documento de fuera de la lista (otro contrato o fuera de fecha).

## M44 · La consulta de la cadena (LP7 de la spec) sobre tres contratos

Por contrato: `tip 14`, su `ctride`, `docoritip 1`, con Σ `ROUND(canoriori · pre, 2)` de las líneas de cada documento
en subconsulta por `docide`. Tiempos: 3,8 s (24 documentos), 4,1 s (10) y ~4 s (5); sin `truncated`.

- Cuadre de la cadena, Σ(n) = Σ(anterior) + `totbas`(n) ± 0,05: 23 de 23, 8 de 8 y 3 de 4 encadenadas. La que no
  cuadra (21.796,62 frente a 1.607,86 + 34.124,43) es de las que no arrastran todas las líneas (M23: 29 de 775).
- Puntas: 1, **2** (una cadena nueva de mayo de 2026 junto a la vieja) y 1. Una primera de 2024 tiene Σ 2.095,50 con
  `totbas` 4.389: su `canoriori` no es `can` en alguna línea (los 2 + 18 casos de M41).

## Lo que solo se ve en la UI (verificación del humano)

- **V9**: una proforma a origen dada de alta por la API (arrastradas solo como `dcapro`, sin `ctrprodes` ni `mov` a 0;
  design D6) se ve, se imprime con unidades ORIGEN/ANTERIOR, se factura con sus «hojitas» y se anula desde la UI como
  las de hoy.
- ~~V10~~: cerrada por el cambio de alcance del 2026-10-28: retomar la cadena vieja o empezar otra al pasar de mes a
  origen lo decide el llamante (`proforma_anterior` o `primera_de_cadena`); la API no siembra el origen (M41).
