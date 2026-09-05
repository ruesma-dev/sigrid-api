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
antes    [1/2] gra.ide=213710  '3E_Sol.Integrales.IND1.pdf'                      469.580 B
         [2/2] gra.ide=217644  'RS23.080002.pdf'                                 151.735 B
después  [1/2] gra.ide=270162  'SUMINISTROS DE OBRAS MOSTOLES.PED1.r.docx'       379.250 B
         [2/2] gra.ide=274282  'SUMINISTROS_DE_OBRAS_MOSTOLES.PED1.r__1_.pdf'  1.139.587 B
```

Coincide con lo esperado y con §C/§G de la exploración, tamaños incluidos. `py_compile` en verde; ese repositorio no tiene tests para los scripts de diagnóstico.

## Propagación al monorepo `albaranes` (2026-09-05, segundo encargo)

| | |
|---|---|
| **Rama · commit** | `feature/F-043-clasificacion-por-ia1` · `ec5b5b0ecd3da990b104adaa7997a533244f8201` (`ec5b5b0`), 1 fichero, +85/−35 |
| **Fichero** | `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs.py` |

La copia viva era **idéntica** a la versión anterior a la corrección
(`47ca373^`) salvo el fin de línea (el árbol la tenía en CRLF; el blob, en
LF). No hubo nada que fusionar: se trasladó la versión corregida tal cual.
Aviso para futuras copias entre estos dos repositorios: `core.autocrlf=true`
está definido pero **no normaliza en `git add`** en esta máquina, así que
copiar con CRLF produce un commit que reescribe el fichero entero; se escribió
con LF y el diff quedó en +85/−35, igual que el del repositorio de origen.

Verificación desde el monorepo (solo lecturas, su propio `.env` y `.venv`):
`python services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs.py B86359866 0695 --download`

```
  📎 DIRECCIÓN A encontró 2 vínculos → 2 gra únicos    rcg  2
  [1/2] gra.ide=270162  'SUMINISTROS DE OBRAS MOSTOLES.PED1.r.docx'        379.250 B
  [2/2] gra.ide=274282  'SUMINISTROS_DE_OBRAS_MOSTOLES.PED1.r__1_.pdf'   1.139.587 B
```

Mismos ides, nombres y tamaños que en el repositorio de origen. `py_compile`
en verde. No se arrancó el flujo de features del monorepo (`harness/init.sh`
no se ejecutó): es una corrección puntual pedida por el humano, y su árbol
quedó limpio.

## Fuera de alcance (decisión del humano)

- **DIRECCIÓN B tiene el defecto invertido**: `buscar_conceptos_desde_gra` mete los `ide` **documentales** de la búsqueda por nombre en `rcg.gra IN (...)` y en los `graide`, que son de negocio. Solo afecta a `--find`; corregirlo exige traducir documental → negocio por `(emp, cod)`.
- `scripts/diagnose_sigrid_contrato_docs_v2.py` conserva el mismo join por `ide`.
- El repositorio `albaranes-persistencia` está marcado archivado (`cab78e2` «ARCHIVADO: migrado al monorepo albaranes; no trabajar aqui»). La copia viva del monorepo ya está corregida (ver «Propagación al monorepo»).
- Sin tocar: `t8_antes.txt` y `t8_despues.txt` (sin seguimiento, ajenos) e `infrastructure/sigrid/sigrid_api_contrato_client.py` (ya resuelve por `cod`; su único matiz es que no filtra por `emp`).
