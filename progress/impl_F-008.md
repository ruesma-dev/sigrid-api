<!-- progress/impl_F-008.md -->
# F-008 · Informe del implementer (T0-T20)

Spec v3.1 (`specs/F-008-registrar-factura/`), rigor `critico`. Rama `feature/F-008-registrar-factura`.

## T0 · Esquema medido (solo `sys.columns` y agregados por `sql/read`, 2026-10-30)

Ninguna columna es `IDENTITY`: todos los `ide` se reservan con `MAX + 1` bajo applock. Nulables: todas salvo `ide` (y
`docide`/`docproide` en las hijas). Tipos de texto `text` (`tex`, `pagtex`, `pagfor`, `dir*`, `detinm`...) aceptan `NULL`.

| Tabla | Cols | Lista blanca y vacíos fijados (lo no citado: 0 en numéricas, `''` en `varchar`) |
|---|---|---|
| `con` | 19 | `CON_COLUMNAS` de F-006; `tip` 15 o 25, `tex` NULL (`con` 25: NULL en 11 de 11) |
| `dcf` | 145 | **Idénticas a `dca`** (mismo orden): `DCA_COLUMNAS` de F-009. `tipgar` -1 (10.857 de 11.408), `emptex` NULL, `cla` 1001 |
| `dcfpro` | 73 | lista propia `DCFPRO_COLUMNAS`; `texcom`, `desesp`, `serdesdat`, `med` NULL (35 de 35 en REC/COM); `tex`, `pac`, `ico`, `refent` `''` |
| `dcfrec` | 21 | **Idénticas a `dcarec`**: `DCAREC_COLUMNAS`; `pos` 64, `tex` `''` |
| `pag` | 46 | lista propia; `remide`, `fecrea`, `blo*`, `natide`, `pun`, divisa 0; `cypref`, `retref`, `blores`, `cpa*` `''` |
| `consii` | 50 | lista propia; `pos` 64, A0/F1/01, `emiter`/`facsimcua`/`facsinide`/`difplaenv` N, resto `''`/0, `detinm` NULL |
| `dcaprodes` | 7 | `ide`, `docproide`, `can`, `docdestip` 15, `docdescod`, `docdeside`, `lindeside` |
| `log` | 14 | `LOG_COLUMNAS` de F-006; alta de factura: `ope 1`, `tab con`, `tip 15`, `est 1`, `ori 0` (medido) |

Identificación medida para las lecturas: IVA = `con.tip 23` por (`emp`, `cod`) con `iva.iva` (tasa) e `iva.sopded` (0 en
los NDED); cuenta = `con.tip 17` + `cua.niv`; analítica = `con.tip 19` + `caa`, hoja = sin `caa.padide` que la apunte (0
analíticas con hijas en 8.634 líneas FRGG26); obra `tip 42`; `conest` 14: CON 3, FAC 10; 15: REC 1, RECGG 20; 25: PDT 1.
