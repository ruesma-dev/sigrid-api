# progress/explore_F-004_relacion_gra.md

# F-004 · ¿Cómo enlaza Sigrid `ruesma.gra` con `ruesma_rep.gra`? Y qué es `vin`

| | |
|---|---|
| **Fecha** | 2026-09-05 · solo `sql/read` por la API desplegada; ni una escritura. Todo [MEDIDO] salvo marca |
| **Volúmenes** | `ruesma.gra` 284.096 · `ruesma_rep.gra` 359.572 · `ruesma.dog` 58.248 · `rcg` 284.511 |
| **Respuesta corta** | **Por `(emp, cod)`**, nunca por `ide`. `vin` es el modo de almacenamiento (3 = binario en el repositorio). El `JOIN ... ON rcg.gra = g.ide` del script de T8 es **incorrecto**: devuelve documentos ajenos |

## A · Qué hicieron los que vinieron antes

| Quién | Relación que usa | Deja escrito por qué |
|---|---|---|
| `albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs.py` (el de T8) y `_v2.py` | `JOIN ruesma_rep.dbo.gra g ON rcg.gra = g.ide` (**por `ide`**) | No |
| `albaranes-persistencia/scripts/diagnose_sigrid_contrato_gra.py` | `rcg.gra = ruesma.gra.ide` → `ruesma.gra.cod = ruesma_rep.gra.cod` (**por `cod`**); su ejemplo `--download-ide 274282` es justo el `ide` documental que sale por `cod` en §C | Docstring: «Cadena de relaciones confirmada» |
| `sigrid-api/scripts/contratos.py` | Por `cod` («resuelve cada gra.cod en ruesma_rep, donde vive el binario») | Sí, en el docstring |
| `postventa-incidencias/docs/referencia/03_modelo_posventa_sigrid.md` §4.1 | Por `cod`; 13.399/13.450 con pareja; «`ide` 296221 es el parte firmado en negocio y un PDF ajeno de junio 2025 en la documental» | Sí. Y `vin=3` = «[INCRUSTADO EXTERNO]» que enseña la pantalla |
| `docs/propuestas/2026-09-03_...` §4 y §8.3 | Por `cod`; dice que `cod` «no tiene índice único» | Corrección: **sí lo tiene** en las dos bases (§B) |
| `azure-apps/sigrid_api.md` §2.2 | «descargas el PDF usando ese identificador»: ambiguo, deja creer que el `ide` de negocio sirve en `documents/read` | No |
| `azure-apps/sigrid_tablas.md` | `gra.vin` «Vinculado»; `dog.codrep` «**Código repositorio externo**»; `DB.gramodo/grapath/gracopy`; `cat/ppo.gra_modo/gra_cnxext` («Gráficos conexión repositorio») | El diccionario nombra el repositorio y lo referencia **por código**, no por `ide` |

## B · `ide` frente a `(emp, cod)` (`ruesma`, `JOIN ruesma_rep.dbo.gra d ON d.cod = g.cod AND d.emp = g.emp`)

| Medida | Resultado |
|---|---|
| Parejas por `(emp,cod)` | **283.385** de 284.096 filas de negocio (99,75 %) |
| Con `g.ide = d.ide` | **426**, todas con `ide` ≤ 575 (año 2009). `MAX(g.ide)` coincidente = 575 |
| Con `g.ide <> d.ide` | **282.959**, desde `g.ide` = **576** (`576→577`, `577→579`…). La diferencia `d.ide − g.ide` va de −7.532 a +111.784 y crece por tramos |
| `JOIN ruesma_rep.dbo.gra d2 ON d2.ide = g.ide` | 284.096 filas casan (los espacios se solapan), pero solo **426** tienen el mismo `cod`: el join por `ide` «funciona» sintácticamente y devuelve **otro documento** el 99,85 % de las veces |
| Negocio sin pareja | **711**: `0/3` 414, `0/2` 152, `34/3` 50, `9/0` 31, resto <10 por clase. **Todo `vin<>3` (194 filas) carece de pareja**; los `vin=3` huérfanos son 517, casi todos de 2021 (`ide` 207.797-208.805) y uno de clase 35 (`ide` **236774**, el huérfano de T1) |
| Documental sin pareja en `ruesma.gra` | **76.187** (`gratipide` 0/3 76.185, 34/3 2; `graant=0` en todas). **56.991 son `dog.codrep`** (§E); quedan 19.196 repartidos 2009-2026 (~2.000/año), 16.530 con `cod` sello: [INFERIDO] restos de altas borradas en negocio o de otros módulos; no son versiones |
| Índices | `ruesma.gra`: `gra_indide` único (`ide`), **`gra_empcod` único (`emp`,`cod`)**, más `gra_emp`, `gra_graant`, `gra_gratipide`. La documental tiene los mismos dos únicos (F-002) |
| `cod` repetido en una base | Negocio **1** (`CTSB20_0022.doc`, `emp` 1 y 31); documental 0 |
| Mismo `cod` entre bases, distinto `emp` | **8** (todos `.doc` de 2017-2020, `emp` 25/31 frente a 1, y sin pareja en su propia `emp`). El `emp` en el join **no es adorno** |

## C · El contrato 2441136 (`CTSU24/0476`, obra 0695) con el join del script de T8

| `rcg.gra` | negocio `WHERE ide = rcg.gra` | documental **por `ide`** (lo que hace el script) | documental **por `(emp,cod)`** |
|---|---|---|---|
| 213710 | `202411251154319354.vmartin` · `SUMINISTROS DE OBRAS MOSTOLES.PED1.r.docx` · 20241125 · `ima` NULL | `ide` 213710 · `202308220856060559.bplaza` · **`3E_Sol.Integrales.IND1.pdf`** · 20230822 · 469.580 B | `ide` **270162** · mismo `cod` · mismo `nom` · 20241125 · 379.250 B |
| 217644 | `202412170843089860.vmartin` · `SUMINISTROS_DE_OBRAS_MOSTOLES.PED1.r__1_.pdf` · 20241217 · `ima` NULL | `ide` 217644 · `202309271102201630.fgallego` · **`RS23.080002.pdf`** · 20230927 · 151.735 B | `ide` **274282** · mismo `cod` · mismo `nom` · 20241217 · 1.139.587 B |

El join por `ide` devuelve **dos documentos ajenos** (de otros usuarios, 14 meses anteriores). T8 verificó que la salida era «byte a byte idéntica» antes y después del despliegue: cierto, pero **idénticamente equivocada**. El script `_gra.py` del mismo repositorio ya lo hacía bien.

## D · Qué es `vin` (`GROUP BY vin`)

| Base | `vin` | n | `ima` NULL | `ima` con datos | `tex` con datos | pareja documental | Ejemplos |
|---|---|---|---|---|---|---|---|
| ruesma | **0** | 38 | 0 | **38** | 0 | 0/38 | `23_NO1701_0001.pdf` (clase 9, 48 KB dentro de negocio) |
| ruesma | 1 | 1 | 1 | 0 | 0 | 0/1 | `nom` = `X:\Declaraciones\...\is_200RUESMA.xml` (2011) |
| ruesma | 2 | 154 | 154 | 0 | 0 | 0/154 | `THAYR.IND1.doc`, `2930_001.pdf`: sin binario en ningún sitio |
| ruesma | **3** | 283.902 | 283.869 | 33 | 362 | 283.385 | el caso general; los 33 con `ima` son clase 9 de 2019-2020 y **también** tienen pareja (doble copia) |
| ruesma | 4 | 1 | 1 | 0 | 0 | 0/1 | `nom` = ruta `X:\...\DEPOSITO.xml` (2011) |
| ruesma_rep | **3** | 359.572 | 0 | 359.572 | 0 | — | única modalidad |

[MEDIDO] `vin` codifica **dónde está el binario**: `0` = incrustado en la propia fila de negocio (`ima` relleno), `1`/`4` = vínculo a ruta de fichero (`nom` es la ruta; `tex` «Camino» vacío en todos), `2` = sin binario (vínculo perdido / solo referencia), **`3` = en el repositorio externo (`ruesma_rep`), localizado por `(emp,cod)`**. La pantalla lo llama «[INCRUSTADO EXTERNO]». `tex` en `vin=3` (362 filas, altas de 2026) es una descripción larga, no un camino. [INFERIDO] el nombre exacto de cada valor 1/2/4; no hay tabla de códigos. Configuración: `DB.gramodo=0`, `grapath`/`gracopy` NULL; `cat`/`ppo` (`gra_modo`, `gra_cnxext`) y `tip.gracambus/gracamcop` **vacíos**: la conexión al repositorio no está en datos, [INFERIDO] va en el cliente Sigrid.

## E · Tablas intermedias y columnas de enlace

| Objeto | Filas | ¿Contiene 296221 / 357208? |
|---|---|---|
| `rcg.gra` | 284.511 | 296221 **sí** (1) · 357208 no |
| `PFfir.graide`, `acugra.graide`, `k_acd.graide`, `catprogra.graide`, `ppoprogra.graide`, `conauxgra`, `catgra`, `ppogra` | **0** todas | — |
| `gra.graant`, `gra.mntide` | 0 filas con valor ≠ 0 | no |
| `ruesma_rep` | **una tabla**, `gra` | no hay puente |
| **`dog`** (`con` tipo Documento, «DocMultimedia») | 58.248 · `gravin=3` 57.082 con `graima` NULL y **`codrep` relleno** · `gravin=0` 1.155 · 2 · 11 | **`dog.codrep` = `ruesma_rep.gra.cod`**: 56.991 casan. Ej. `dog` 2828577 `codrep=202609021110476684.agavilan` → documental 359082, 600.319 B |

No existe tabla intermedia ni columna de `ide` cruzado. Sigrid tiene un **segundo consumidor del repositorio** (`dog`) que lo referencia con una columna llamada literalmente «Código repositorio externo»: la clave del repositorio es el `cod`. Todos los `graide` de negocio apuntan a `ruesma.gra`, nunca a la documental.

## F · Segunda clase: `cod` = nombre de fichero (clases 9 y 39)

| clase | `g.ide` | `d.ide` | `cod` | `emp` | `d.gratipide` | `g.ima` | `d.ima` |
|---|---|---|---|---|---|---|---|
| 9 | 8484 | 21075 | `01_NO1701_0085.pdf` | 1 | 0 | NULL | 290.767 |
| 9 | 283404 | 343559 | `29_NO2604_0021.pdf` | **28** | 0 | NULL | 239.837 |
| 39 | 102236 | 153322 | `1_707_POSTV2_031_02_1_B.pdf` | 1 | 0 | NULL | 123.974 |
| 39 | 295450 | 356376 | `1_707_0677_03VILLA 7_.pdf` | 1 | 0 | NULL | 211.350 |

Por clase (`con_pareja` / `ide_igual`): 0 → 223.436/224.004 / 426 · 9 → 28.454/28.485 / **0** · 34 → 6.394/6.444 / 0 · 35 → 3.679/3.680 / 0 · 39 → **818/818** / 0. Vale igual con `cod` no-sello; en la documental `gratipide` es 0 y `res` `''` también aquí. Contraejemplo del join por `ide`: `g.ide` 295450 (`1_707_0677_03VILLA 7_.pdf`) → documental 295450 = `S.SOCIALES-C57019101622997052025..pdf` de `mmcuesta`.

## Respuesta

1. **Relación [MEDIDO]: `ruesma.gra (emp, cod)` = `ruesma_rep.gra (emp, cod)`.** Índice único `gra_empcod` en las dos bases; 283.385 parejas; ningún `ide`, columna ni tabla intermedia las une. Los `ide` solo coinciden en las 426 filas de 2009 (`ide` ≤ 575) por arranque paralelo de los dos contadores; desde 576 divergen y desde ~50.000 la diferencia supera 47.000. El segundo cliente del repositorio (`dog.codrep`) confirma que la clave del repositorio es el código.
2. **`vin` [MEDIDO] = modo de almacenamiento del binario.** `3` («incrustado externo»: 99,9 % en negocio, 100 % en la documental) = el fichero vive en `ruesma_rep` y se localiza por `(emp,cod)`; `0` = dentro de `ruesma.gra.ima`; `1`/`4` = ruta de fichero en `nom`; `2` = sin binario. El endpoint debe escribir **`vin=3` en las dos filas**, `ima` NULL en negocio, y no rellenar `tex`.
3. **El join por `ide` de `diagnose_sigrid_contrato_docs.py` (T8) es incorrecto [MEDIDO]:** en el contrato 2441136 devuelve `3E_Sol.Integrales.IND1.pdf` y `RS23.080002.pdf` en vez de los dos PDF de Suministros de Obras Móstoles (`ide` documentales 270162 y 274282). Hay que corregirlo (`_gra.py` y `contratos.py` ya lo hacen bien) y aclarar `sigrid_api.md` §2.2: el `ide` que acepta `documents/read` es el **documental**, que se obtiene por `cod`. T8 sigue valiendo como prueba de no-regresión, no como prueba de corrección.
4. **Implicación para el endpoint:** la fila de negocio (`ide` propio de `ruesma.gra`, `vin=3`, `ima` NULL, `emp` de la reclamación, `cod` generado una vez) es a la que apunta `rcg.gra`; la fila documental lleva **el mismo `cod` y el mismo `emp`**, `ide` propio de `ruesma_rep.gra`, `vin=3`, `gratipide=0`, `res=''`, `ima`=binario. Si `cod` o `emp` difieren en un carácter, el motor no avisa y el gráfico queda «sin fichero» (como los 517 huérfanos `vin=3` de 2021). No hace falta que los `ide` coincidan ni conviene intentarlo. `emp` va en el join: hay 8 `cod` repetidos entre empresas.
5. [ABIERTO] Los 19.196 documentales sin dueño ni en `gra` ni en `dog` (~2.000/año): no afectan al endpoint, pero conviene saber si Sigrid borra en negocio sin borrar en la documental (sería el patrón inverso al huérfano de negocio). No se pudo medir el nombre que Sigrid da a `vin` 1/2/4 (no hay tabla de códigos).
