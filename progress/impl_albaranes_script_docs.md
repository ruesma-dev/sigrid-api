# progress/impl_albaranes_script_docs.md

# `albaranes-persistencia` · cruce documental de `diagnose_sigrid_contrato_docs.py`

| | |
|---|---|
| **Rama · commit** | `proveedor` · `47ca3730a07e805c36395b31c4e3f2decd6d740d` (`47ca373`), 1 fichero, +85/−35 |
| **Fecha** | 2026-09-05 · solo `sql/read` y `documents/read` contra la API desplegada |

## Qué cambió (solo `scripts/diagnose_sigrid_contrato_docs.py`)

- **Las cuatro vías** (`rcg`, `PFfir`, `acugra`, `k_acd`) dejan de cruzar a la documental por `ide`. Ahora `rcg.gra`/`graide` → `ruesma.gra` (`g_neg`) → `LEFT JOIN {database_rep}.dbo.gra AS g_rep ON g_rep.cod = g_neg.cod AND g_rep.emp = g_neg.emp`. El `emp` va en el join: hay 8 `cod` repetidos entre empresas (§B de `explore_F-004_relacion_gra.md`).
- **Alias explícitos** `gra_neg_ide` / `gra_rep_ide`. `gra_cod`, `gra_fec`, `gra_usu` y `gra_nom`/`gra_nomori` salen de negocio; se añaden `gra_rep_nom`/`gra_rep_nomori` como respaldo del nombre (en importaciones masivas la fila documental trae `nom` vacío) y `gra_emp`. `ima_bytes` pasa a medirse sobre `g_rep.ima`: el binario vive ahí.
- **`_gra_ide` lleva ahora el ide DOCUMENTAL**, que es el que consumen la comparación A vs B (el conjunto B ya salía de `ruesma_rep`) y la descarga (`download_gra` → `documents/read` sobre `database_rep`). Se añade `_gra_neg_ide`. Vale `0` si el gráfico de negocio no tiene pareja documental (`vin<>3`), caso que el join por `ide` ocultaba porque siempre casaba.
- **`LEFT JOIN` a la documental en las cuatro**, también en la VÍA 1 que tenía `JOIN`: el inner join se conserva contra `ruesma.gra` (donde siempre casa), así que la VÍA 1 no cambia de nº de filas y nada desaparece en silencio.
- Docstring de cabecera con la nota **CORRECCIÓN 2026-09-05** y el porqué; docstring de `buscar_docs_desde_concepto` con el significado de las claves. Extra: la primera línea decía `# scripts/diagnose_sigrid_contrato_gra.py` (copia del script hermano) y los ejemplos de uso invocaban ese otro fichero; corregidos al nombre real.

## Verificación

`python scripts/diagnose_sigrid_contrato_docs.py B86359866 0695` → contrato 2441136 `CTSU24/0476`, VÍA 1 = 2 filas, vías 2-4 = 0 filas (mismas cifras que antes; las cuatro consultas ejecutan sin error en el servidor). El script no imprime los `ide`, así que se repitió con `--download`, que sí los muestra:

```
antes    [1/2] 213710 '3E_Sol.Integrales.IND1.pdf' 469.580 B · [2/2] 217644 'RS23.080002.pdf' 151.735 B
después  [1/2] 270162 'SUMINISTROS DE OBRAS MOSTOLES.PED1.r.docx' 379.250 B
         [2/2] 274282 'SUMINISTROS_DE_OBRAS_MOSTOLES.PED1.r__1_.pdf' 1.139.587 B
```

Coincide con §C/§G de la exploración, tamaños incluidos. `py_compile` en verde; ese repositorio no tiene tests para los scripts de diagnóstico.

## Propagación al monorepo `albaranes` (2026-09-05, segundo encargo)

| | |
|---|---|
| **Rama · commit** | `feature/F-043-clasificacion-por-ia1` · `ec5b5b0ecd3da990b104adaa7997a533244f8201` (`ec5b5b0`), 1 fichero, +85/−35 |
| **Fichero** | `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs.py` |

La copia viva era **idéntica** a la versión anterior a la corrección (`47ca373^`) salvo el fin de línea (árbol en CRLF, blob en LF): nada que fusionar, se trasladó tal cual. Aviso para futuras copias entre estos dos repositorios: `core.autocrlf=true` está definido pero **no normaliza en `git add`** en esta máquina, así que copiar con CRLF produce un commit que reescribe el fichero entero; escrito con LF, el diff quedó en +85/−35, igual que el de origen.

Verificación desde el monorepo (su `.env` y `.venv`), `... B86359866 0695 --download`: `[1/2] gra.ide=270162 ... 379.250 B` y `[2/2] gra.ide=274282 ... 1.139.587 B` — mismos ides, nombres y tamaños que en origen. `py_compile` en verde. No se arrancó el flujo de features del monorepo (`harness/init.sh` no se ejecutó): es una corrección puntual pedida por el humano, y su árbol quedó limpio.

## Dirección B y `_v2.py` (2026-09-05, tercer encargo)

| | |
|---|---|
| **Monorepo** | `feature/F-043-clasificacion-por-ia1` · `48e3d179972a551edae9fe3d4851f9d4e4b233c4` (`48e3d17`), 2 ficheros, +225/−60 |
| **Archivado** | `proveedor` · `9b4fccfda6f3597a4a64f3a520ac3eb3227dd906` (`9b4fccf`), copia byte a byte del anterior |

**DIRECCIÓN B** (`--find`): la búsqueda por nombre corre sobre `ruesma_rep` y
devuelve ides documentales, pero `rcg.gra` y los `graide` son de negocio.
Nueva `traducir_documentales_a_negocio()` (consulta **parametrizada** con
`cod IN (?,?,…)`, cruce en Python por `(emp, cod)`);
`buscar_conceptos_desde_gra()` pasa a recibir ides de negocio más el mapa
negocio → documental y emite `_gra_neg_ide` y `_gra_ide` (documental), con lo
que la comparación A vs B compara el mismo tipo de ide y la descarga sigue
usando el documental. Las documentales sin pareja se listan como «sin fila de
negocio». Se añadió `emp` al `SELECT` de B1 (es media clave).

**`_v2.py`**: mismas cuatro vías hacia `gra` corregidas por `(emp, cod)` con
`LEFT JOIN` y alias explícitos; `_target_ide` (el que descarga de
`database_rep`) pasa a ser el documental y se añade `_neg_ide`. La clave de
deduplicación incluye ahora el ide de negocio, porque `_target_ide` vale 0 en
los `gra` sin pareja y dos documentos distintos colapsarían. FASE 4 traduce
antes de buscar vínculos. **Las vías hacia `dog` no se tocan**: `dog` vive en
`ruesma` con su propio binario (`graima`), no hay cruce entre bases.

Verificación desde el monorepo, `... B86359866 0695 --find SUMINISTROS_DE_OBRAS_MOSTOLES`:

```
docs.py  ↔️ 8/10 con fila de negocio por (emp, cod); 2 sin fila de negocio
           gra_rep_ide=274312  cod='202412170933526075.vmartin'  — sin fila de negocio
           gra_rep_ide=60446   cod='201808031400096287.vnueda'   — sin fila de negocio
         gra_rep_ide=270162  gra_neg_ide=213710  [rcg] → con.ide=2441136 'CTSU24/0476'
         gra_rep_ide=274282  gra_neg_ide=217644  [rcg] → con.ide=2441136 'CTSU24/0476'
         COMPARACIÓN: en AMBAS 2 (270162, 274282) · SOLO en A 0 · SOLO en B 8
v2.py    VÍA rcg: gra_rep_ide=270162 gra_neg_ide=213710 · 274282 / 217644
         FASE 4: 270162 (negocio 213710) y 274282 (negocio 217644) → 2441136 CTSU24/0476
```

`py_compile` en verde en los dos repositorios; el archivado se ejecutó también
y dio la misma salida. Solo lecturas.

## Fuera de alcance (decisión del humano)

- El repositorio `albaranes-persistencia` está marcado archivado (`cab78e2` «ARCHIVADO: migrado al monorepo albaranes; no trabajar aqui»). La copia viva del monorepo ya está corregida (ver «Propagación al monorepo»).
- Sin tocar: `t8_antes.txt` y `t8_despues.txt` (sin seguimiento, ajenos) e `infrastructure/sigrid/sigrid_api_contrato_client.py` (ya resuelve por `cod`; su único matiz es que no filtra por `emp`).
