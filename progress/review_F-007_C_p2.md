<!-- progress/review_F-007_C_p2.md -->
Revisión incremental desde `fe85523` (pasada 2) · commits `32ad8b4..765f273` · bloque CHECKPOINTS, tests y documentación

# Review F-007 · pasada 2 · C1, C2, C4 (MANUAL y RED), C5, documentación y `azure-apps`

**Veredicto del bloque: CHANGES_REQUESTED.** Los cinco hallazgos de la pasada 1 de este bloque están resueltos,
pero `verificacion_manual.md` (H1 de C4red) trae dos defectos nuevos que lo hacen no ejecutable tal cual: N1 (D2 con
`!` y sintaxis de PowerShell) y N2 (V1 espera un mensaje que la ruta no da). Arreglo de dos líneas, sin código.

**Rigor:** `critico`. Nada contra Sigrid ni la API; sin `harness.mutacion`. Mi worktree, creado y **borrado**.

## `bash harness/init.sh` sobre `765f273` (tal cual, exit 0)

```
[OK] Arnés v1.7.8 · features.json válido · BACKLOG.md al día · rigor.json válido
    15 features, 6 abiertas, en curso: ['F-007'], bloqueadas: ['F-015']
[AVISO] features blocked (F-015, esperado) · [AVISO] ruff: 79 avisos (deuda previa)
3393 passed, 1 skipped, 1 warning in 239.49s
[OK] PUERTA COBERTURA: 100.0% de 736 líneas cambiadas cubiertas (736/736, umbral 80%, nivel critico)
[OK] PUERTA TAMAÑO: requirements 150/150, design 248/250, impl 173/220
[OK] Rama actual: feature/F-007-registrar-proforma · ENTORNO LISTO
```

Casa con «Evidencias» de `impl_F-007.md` (3393/1, 736/736, topes); solo cambia el tiempo (carga de la máquina).

## Hallazgos de la pasada 1 y su estado

| Hallazgo | Estado | Comprobación |
|---|---|---|
| H1 C1C2C5 · `current.md` falso | **Resuelto** | `:4-50` F-007 `in_progress` con «Lo siguiente» T23 → avisos → merge → T20-T22 → T24; `:52-59` F-015 `blocked` por `AC26/30670`; «Lo siguiente en el backlog» y «Prompt para retomar» (`:203-220`) al estado real. Sin `spec_ready`, sin «F-015 `in_progress`», D4 aprobada, preguntas abiertas aclaradas (`:42-46`). |
| H2 C1C2C5 · descripción de F-007 | **Resuelto** | `features.json`: spec v3 + enmienda 1, `proformas` (F-005), proforma de mes, llave propia; `BACKLOG.md:49` igual (`init.sh`: «al día»; commit `357e070`). |
| H1 C4red · MANUAL sin comando | **Resuelto en parte** | Existe `verificacion_manual.md` con D1-D3 y V0-V5; ver N1 y N2. |
| O1 C4red · cifras de T17; worktree `rev007-mut` | Resuelto | Ya no están en `current.md`; el worktree ya no existe. |
| Obs. 3 C3C4ter · autorización hojas | **Resuelto** | `impl_F-007.md:27-28` («lo autorizó el humano el 2026-10-25»), además de la cabecera de cada hoja. |

## `verificacion_manual.md` (punto 4) frente al de F-015

- [x] **Sin secretos**: URL, clave, app y grupo por `$env:` (F-015 los escribe literales); JSON en `$env:TEMP`.
- [x] **D1 reproducido** en local: imprime `False ['PRF-'] ['SM9999', 'SB9999', 'SM370001'] {...} 500` (cerrada); la
  `--query` con `||` pasa de PowerShell 5.1 a `az` (probado). D3: dry-run de `sigrid/albaran` primero.
- [x] **Cuerpos de V1-V4**: `Cuerpo` (con `Ctr`/`Vinc` simulados), tres hojas, con y sin `ctrpro_ide` y con
  `otra_del_mes`: los 7 JSON pasan `ProformaRequest.model_validate` y cuadran con su `importe_mes` a ±0,05.
- [x] **V5**: un único `commit:true` tras `previsto`, llave abierta solo para él y cerrada tras la repetición
  `idempotente`; anulación por la UI, nunca `DELETE`, con lecturas de comprobación.
- [ ] **Ejecutable tal cual**: N1 y N2.

## Defectos nuevos
- **N1 (bloquea) · `verificacion_manual.md:9` y `:58-59`.** D2 manda lanzar `func azure functionapp publish
  $env:SIGRID_API_APP --python` «con el prefijo `!`», pero el `!` de la sesión corre en **bash** (comprobado el
  2026-10-18: «Set-Location: command not found»): ahí `$env:SIGRID_API_APP` se expande a `:SIGRID_API_APP` y las
  variables de la consola de PowerShell no existen. Falla sin desplegar. Requerido: decir que D1-D3 se teclean en
  la consola PowerShell del humano (donde vive `$env:SIGRID_API_APP`), o dar la forma para `!` en bash con el
  nombre de la app que teclea él (`! func azure functionapp publish <app> --python`), y quitar la contradicción con
  «Todo desde PowerShell 5.1» (`:10`).
- **N2 (bloquea) · `verificacion_manual.md:145`.** V1 espera «Escritura de proformas desactivada: hacen falta …»,
  pero con la llave cerrada responde la **ruta** (`function_app.py:353-358`): «Escritura de proformas desactivada
  (SIGRID_PROFORMA_WRITE_ENABLED=false): no se ha escrito nada.». El «hacen falta …» de T35 es el del núcleo, que
  solo sale si la ruta deja pasar. Requerido: el texto real de la ruta (el `codigo` sí es el correcto).
- **N3 (no bloquea) · `:135`/`:159`.** V2 dice mirar `dcapro_ide` y `linoriide`, pero `Lineas` no los selecciona:
  `Select-Object dcapro_ide, ctrpro_ide, linoriide, producto, cantidad, precio, importe`.
- **N4 (no bloquea) · `:221-225`.** Tras anular falta `COUNT(*) FROM dbo.dcarec WHERE docide = ?` (F-015 lo tiene).

## Fase ROJA de las correcciones (punto 5)

- [x] Documentada con salida real en `impl_F-007.md:99-122` para T25, T27, T29, T33, T35 y T32; T31 y T34 son de
  fijación y su ROJO es el mutante (declarado). Los cinco commits ROJOS (`dc8fb9a`, `a22beb5`, `f419ec4`, `3435b63`,
  `a0b89b8`) solo tocan `tests/`.
- [x] **Reproducidas dos** en worktree aparte, sobre el commit ROJO (el anterior a la implementación):
  - T29 `f419ec4`: `10 failed, 50 passed`, `assert ['referencia'...] == [...]` en `test_f007_transaccion.py:146` y
    `DID NOT RAISE ProformaError`: **idéntico al informe**. Verde `10644b5`: `60 passed`.
  - T33 `3435b63`: `7 failed, 154 passed`, `'locate_contract' not in [...]` y `No hay un contrato 'CTSB26/0472'
    de la obra '0719' y ese proveedor.`: **idéntico**. Verde `6df00fe`: `162 passed`; el verde **añade** un test
    (`test_f007_o4_el_contrato_que_desaparece_antes_de_grabar_no_se_encuentra`), no toca asertos de los ROJOS.

## `azure-apps` `0072629` (punto 6)

- [x] Solo `sigrid_api.md` (+17/−4); `datamart_seg_anual.md` intacto (va aparte en `995e369`, de otro proyecto).
- [x] §8.10 recoge: riesgo O3 (JSON mal formado tumba todas las rutas, `@fichero.json`, llave cerrada, dry-run de
  `sigrid/albaran` primero, enlace a `verificacion_manual.md`); R14/R8 v1.1 (partida y precio ±0,0001, ambigua con
  `candidatos`); `otra_del_mes` con el mismo importe; idempotente repetida bajo el applock con `origen` nulo;
  `proveedor_no_encontrado` por `ctr.entcif` vacío; IVA del `ctrpro` por `pos`. La llave (§4.1, §8 punto 9) ya daba
  el código correcto. Sin URL, claves ni personas.

## Puntos 7, 8 y C5

- [x] Autorización de las hojas con precios: `impl_F-007.md:27-28` y la cabecera de cada hoja.
- [x] Barrido de 17 ficheros de `specs/` y `progress/` (diff, `specs/F-007-*`, `progress/*F-007*`, `current.md`):
  0 correos, GUID, CIF/NIF/NIE, claves, IPv4 ni nombres de persona (~60 nombres y apellidos). Solo razones sociales
  ya aceptadas (`GARSAN`, «NUN S.A.») y el nombre de la Function App heredado de F-009 (`current.md:85`, no secreto).
- [x] C5: 21 commits en `32ad8b4^..765f273`, todos con el pie; ROJO y verde separados. T25-T40 `[x]`; T20-T24
  abiertas, como deben. Obs.: la `acceptance` 2 de F-007 nombra `SIGRID_DOMAIN_WRITE_ENABLED`, no la llave propia.

## Cambios requeridos

1. N1: `specs/F-007-registrar-proforma/verificacion_manual.md:9-10` y `:58-59`, D2 ejecutable donde se dice.
2. N2: `specs/F-007-registrar-proforma/verificacion_manual.md:145`, el mensaje real de la ruta.
3. (Opcionales, mismo commit) N3 y N4.

**Automejora (no aplicada, `arnes-base`):** cada bloque MANUAL dice su shell y su «Se mira» copia el texto del código.
