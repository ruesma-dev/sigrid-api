<!-- progress/review_F-008_enmienda1.md -->
Revisión incremental desde `4f6bddd` (pasada 2): delta `4f6bddd..fa0bfcf` + azure-apps `8fca6a3`

# Review F-008 · enmienda 1 (spec v3.2): naturaleza de la ficha o forzada por empresa, FR con cuenta

**Veredicto: APPROVED.** B1, M1, M2 y M3 de la pasada 1 están corregidos. El delta no toca código de producción. T34
(manual, humano) es lo único pendiente de la enmienda.

**Nivel de rigor:** `critico` (`harness/features.json:166`). La pasada 1 ya validó fase RED, cobertura y mutación, y
ninguna de las tres cambia: el delta no toca el alcance medido.

**Base:** lo aprobado en la pasada 1 hasta `4f6bddd` (código, tests, mutación, contrato v8.5 y `azure-apps` `612d84b`)
queda dado por bueno. Su texto completo está en `git show 84ee690:progress/review_F-008_enmienda1.md`.

## Delta revisado

| Commit | Ficheros | Qué |
|---|---|---|
| `84ee690` | `progress/review_F-008_enmienda1.md` | el informe de la pasada 1 |
| `f3ce85c` | `specs/F-008-registrar-factura/verificacion_manual.md`, `progress/current.md` | B1: §D.1 superada, §T34 nueva y enlazada |
| `214418c` | `tests/test_f008_models.py` | M3: dos tests renombrados, sin tocar el cuerpo |
| `fa0bfcf` | `progress/impl_F-008.md` | M2, la tabla de commits y las evidencias |
| azure-apps `8fca6a3` | `sigrid_api.md:362` | M1: `CUENTAS_GASTO_PREFIJOS` rige también la FR con cuenta |

**Sin código de producción:** `git diff --stat 4f6bddd..HEAD` solo trae `progress/`, `specs/` y un test. No hay nada en
`application/`, `domain/`, `config/`, `infrastructure/`, `function_app.py`, `infra/` ni `.env`. El cambio del test es
solo de nombre (`git diff 214418c^..214418c`: dos líneas `def`). Por tanto **RM1** sigue valiendo: la campaña se midió en
`66c7570` y ninguno de los 6 ficheros del alcance ha cambiado desde entonces.

## Verificación ejecutada

- `bash harness/init.sh` → exit 0, `4364 passed, 1 skipped` (111,85 s), `PUERTA COBERTURA` [OK] 100 % (136/136), `PUERTA TAMAÑO` [OK] (impl 217/220), `ENTORNO LISTO`.
- La rama sigue siendo `feature/F-008-registrar-factura`, el árbol está limpio y no hay worktrees de más.

## B1 · La sección T34 de `verificacion_manual.md:183-330`, comprobada punto por punto

- **Comandos exactos y ejecutables.**
  - Todas las órdenes `az` van con `export MSYS_NO_PATHCONV=1;` y el prefijo `!` (Git Bash), con `<grupo>` y `<app>`
    tecleados por el humano. Así no queda ningún nombre de recurso en el repositorio.
  - La escritura de App Settings va por `@json`: `appsettings set --settings @<ruta de $f>`, con un fichero ASCII sin BOM
    `[{"name","value","slotSetting"}]`, igual que en D1 de F-007.
  - Antes de subir, el JSON se valida con `Settings` real: tiene que imprimir los dos mapas, y si falla no se sube. Las
    variables SQL que el script pone a mano son ficticias (`"x"`); el script no incluye secretos.
  - `appsettings delete --setting-names` lleva las dos viejas y deja expresamente la de proformas (P23).
  - Las lecturas (`appsettings list` con el filtro `NATURALEZA`, y los `Fila`/`Leer` de `sql/read`) usan los helpers de
    §S (`verificacion_manual.md:24-40`).
- **La previa de albaranes va solo con `commit:false`.** PC lleva `commit = $false` en el cuerpo y el texto dice
  «**nunca** se manda `commit:true`» porque la llave de albaranes está abierta. PA y PB son previas de factura, también
  con `$false`. Se toma C0 antes y después, también el de albaranes (`tip 14`).
- **Cada escritura pide autorización.** Publicar (T34.2), `appsettings set` (T34.4) y `appsettings delete` (T34.5) los
  lanza el humano, cada uno marcado «con autorización expresa». Las lecturas y las previas las lanza el líder con la
  autorización de esa sesión, como manda `CLAUDE.md`. El aviso a `albaranes` y su acuse van **antes** de publicar
  (T34.0).
- **Qué cambia por empresa.** Coincide con el dato medido que me pasaron:
  - en la empresa 1, las fichas de `SM9999`, `SB9999`, `SM370001`, `QA9999` y `XA9999` coinciden con el mapa viejo y
    **solo cambia `MA9999`** (`MA99`/`CDSB37` → `MA1501`/`CDMA15`);
  - en la empresa 34, la ficha de `SM370001` es **`SM08`**, y hoy no entra porque no está en `EMPRESAS_OBRA`;
  - el guion indica `34:SM370001` como el forzado si algún día entra.

  Esto resuelve la duda de la pasada 1 sobre `SM9999`, `SB9999` y `SM370001`. No he releído `dbo.pro`: el dato es la
  medición del líder del 2026-11-06, y el propio guion lo vuelve a comprobar en T34.3 con `$nat` (si la ficha cambió, se
  para).
- **Lo que se anota** en `verificacion_F-008.md` («T34 · Enmienda 1») está bien acotado: solo `con.ide` y códigos, nunca
  CIF ni nombres.
- **§D.1:** la carga de `SIGRID_FACTURA_NATURALEZA_POR_PRODUCTO` queda marcada como «Superada por la enmienda 1… no se
  vuelve a cargar», con remisión a §T34. `current.md:28-29` enlaza §T34.

## M1-M3

- **M1** · `azure-apps` `8fca6a3`: la fila de `SIGRID_FACTURA_CUENTAS_GASTO_PREFIJOS` dice ahora «líneas FRGG sin origen
  y, desde la enmienda 1, de las FR con cuenta». Coincide con `resolver_linea_gg` y con el test
  `r26_fr_con_cuenta_y_prefijos_vacios_no_vale`. El commit solo toca `sigrid_api.md`.
- **M2** · `impl_F-008.md:166` explica por qué `ProformaStatements` lista L15D y que las proformas nunca la lanzan.
- **M3** · `test_f008_models.py:135` se llama ahora `..._exige_producto_o_cuenta_y_analitica`, y `:142`,
  `..._con_producto_y_campo_de_cuenta_es_ambigua`. Las aserciones no cambian.

## Checkpoints (delta; el resto, en la pasada 1)

- **C1** [x] `init.sh` en verde · [x] los ficheros del arnés existen.
- **C2** [x] una sola `in_progress` · [x] la rama es la de la feature · [x] `current.md` enlaza T34 y dice la verdad.
- **C3** [x] no hay código nuevo · [x] el guion tiene su primera línea con la ruta · [x] sin secretos: `<grupo>`, `<app>`
  y las claves vienen del entorno (`$env:SIGRID_API_*`).
- **C3 bis** N/A: no entra ningún documento de fuera.
- **C4** [x] la trazabilidad sigue igual (los renombres conservan el prefijo `test_f008_r23_`) · [x] los tests no tocan
  red ni base · [x] **MANUAL con comando exacto: T34 en §T34, enlazada desde `current.md`** (antes `[ ]`, B1).
- **C4 bis** [x] sin cambios desde la pasada 1. El delta no toca el alcance (RM1) y la cobertura sale [OK] 100 %.
  N/A RM5 y RM6: no hay mutantes nuevos.
- **C4 ter** N/A: no existe `harness/rutas_sensibles.json`.
- **C5** [x] T26-T33 y T36 en `[x]` con commit; T34 es manual y T35 es esta revisión · [x] no hay temporales ·
  [x] `features.json` dice `in_progress`, que es lo real.

## Pendiente para cerrar la enmienda

- **T34** (humano, con el guion de §T34): aviso a `albaranes`, publicar, previas PA/PB/PC, decidir los `_FORZADA` y
  borrar las dos viejas, cada escritura con su autorización.
- Marcar **T35** `[x]` con este APROBADO. Le toca al líder: el reviewer no edita `tasks.md`.

## Menores (no bloquean)

- `impl_F-008.md`, fila «Tamaños» de Evidencias: dice `review 133/140`, que es la cifra de `review_F-008.md` antes de
  esta pasada. Cifra vieja, inofensiva.
