<!-- progress/review_F-015_cabecera.md -->
Revisión completa (pasada 1) · bloque CABECERA · HEAD `e42e0ad` · desde `dev`

# F-015 · Revisión troceada: conformidad funcional de la cabecera (R1-R11, D1-D7, D12)

**Veredicto: CAMBIOS** (tres hallazgos pequeños, ninguno de comportamiento; el código de la cabecera cumple la spec).

Rigor `critico` (declarado en `features.json`). Este bloque **no** recorre `init.sh`, la suite completa, cobertura ni
mutación (encargo del líder: lo hacen otros reviewers en paralelo). Ejecutado aquí:
`python -m pytest tests/test_f015_statements.py tests/test_f015_use_case.py -q` → **167 passed**;
`tests/test_f009_{statements,use_case,equivalencia,models}.py` → **494 passed**. Nada contra Sigrid; el árbol sigue limpio
(solo aparece `review_F-015_C1C2C5.md`, de otro reviewer).

## Lo comprobado (con evidencia)

| Punto | Resultado | Cómo |
|---|---|---|
| `DCA_COLUMNAS` (145, orden) y `_DCA_TEXTO` (48) = design §Lista blanca | [x] | Extraje con un script las dos listas del texto del design y las comparé con las constantes: iguales, sin diferencias |
| `ORIGEN_DCA`: 6 identidad, 15 cascada, 18 calculadas, 106 fijas; sin huecos ni repetidas | [x] | `Counter(ORIGEN_DCA.values())`; los grupos no se solapan; `DCA_FIJAS` solo vale distinto de 0/`''` en `tipgar` −1 y `emptex` None |
| `con` = las 19 `CON_COLUMNAS` de F-006 con el valor de design §`con` (`tiemod` OLE UTC) | [x] | `albaran_compra_statements.py:635-663`; `insertar_con`/`insertar_dca` con columnas fijas (`:1403-1409`); `_TABLAS_CLONADAS = {"dcapro"}` |
| No se copia nada fuera de la lista | [x] | `construir_dca` arma la fila desde cero y la recorta a `DCA_COLUMNAS` (`:851`); en el caso de uso nadie vuelve a tocar `filas.dca`/`filas.con` (`grep`); ya no se lee la `con` del respaldo |
| `resolver_cascada`: orden contrato → respaldo → `prv`; sin contrato, respaldo → `prv` | [x] | `_origenes` (`:690-697`). Lo comprobé además con contrato **sin** respaldo (script en el scratchpad): la cascada pasa al `prv` y `dircon1` se queda sin fuente |
| Qué es «con valor» | [x] | `_tiene_valor` (`:666-672`): NULL, 0, 0.0, `Decimal(0)`, `False`, `''` y los textos solo de espacios no cuentan; −1 y `'0'` sí. Coincide con R3 («≠ 0, no vacío») |
| Pago en bloque, según el primer `pagide` ≠ 0; del `prv`, los textos de su `auxpag` | [x] | `:774` y `_de_la_cascada` (`:854-864`); `efeide` del propio `prv` (R3). `pago_del_proveedor` decide cuándo se lee el `auxpag` |
| Banco en bloque, del primero con `banban` ≠ 0 o `ban` no vacío | [x] | `:775-778`; tests `r3_banco_*` |
| `ivadif`: del `ctr` aunque sea 0; si no, del respaldo; si no hay ninguno, 0 | [x] | `:786-791` (D5) |
| Identidad (R4): del `ctr` aunque venga vacía; sin él, del respaldo y, sin respaldo, del `prv` + `con.cod` de L17 | [x] | `:752-758`; caso de uso `:408-419` |
| Respaldo L5 (R6): `AC__/%`, `cla 0`, `ISNULL(entref,'') NOT LIKE 'PROF%'`, por `entide` o por CIF; opcional | [x] | `:192-201`, `:1256-1268`; `_leer_cabecera` sin respaldo sigue con `template_ide` 0 |
| L17 (R7) y sus errores, solo sin contrato ni respaldo por CIF | [x] | `:202-205`; `_proveedor_por_cif` (`use_case:430-450`): 0 filas → `proveedor_no_encontrado`, más de una → `proveedor_ambiguo`, los dos en `CODIGOS_CABECERA` |
| Fijas a 0 (R9, D7): facturación, cadena, divisa, `fecent`/`feclim`/`cocide`, `dtumID` `''`, `tipgar` −1, `cla` 0 | [x] | `test_f015_r9_*` y el centinela; coincide con M18 (99 columnas a 0 + las 7 que la spec deja a 0) |
| R10: si falta una columna, `ValueError` antes de escribir | [x] | `_exigir` sobre todas las filas leídas, se usen o no; test del caso de uso con `commit` true/false sin `peek` ni transacción |
| Aviso `cabecera_sin_dato` (R5, D12): pago sin fuente, o banco sin fuente con efecto `CC`/`CT`/`TR` | [x] | `_completar_cabecera` (`use_case:452-480`), informativo; en la previa y en `creado` |
| `proveedor_sin_albaran_previo` ya no se emite | [x] | Ningún `.py` de producción lo cita; en `CODIGOS_CABECERA` ya no está; `test_f009_models.py:440` lo trata como código fuera de la lista |
| Test centinela (R25) | parcial | Ver **H1** |
| Contrato con albaranes v8.3 | parcial | Ver **H2** |

## Hallazgos

**H1 · R25: al centinela le falta el caso «con contrato y sin respaldo».** R25 pide el centinela «con y sin contrato, con
y sin respaldo» y que, al vaciar un origen, la columna pase al siguiente. En `tests/test_f015_statements.py` hay tres
combinaciones: C+R+P (`:299`), R+P (`:313`) y P (`:323`). Ningún test llama a `_dca(contrato, None, …)`, y todas las
pruebas de vaciado (`:345-453`) llevan respaldo. El caso de uso sí ejerce esa combinación
(`test_f015_r6_sin_respaldo_el_alta_sigue…`), pero solo para pago, `cueide` y `dirdir1`, no con la propiedad del
centinela. **Escenario sin test:** con contrato y sin respaldo, si alguien tomara `dircon1` o `ivadif` del `prv`, o
copiara una columna `prv` que no está en la lista, los tests no lo detectarían. El comportamiento actual es correcto
(lo medí: 0 discrepancias). **Cambio:** añadir en `test_f015_statements.py`:
(a) un centinela `_dca(_contrato(), None, _proveedor(), _auxpag())` en el que toda columna de identidad o cascada salga
del contrato;
(b) un caso con el contrato vaciado en `DCA_CASCADA` y sin respaldo, en el que la cascada sale del `prv` (`pagtex`/`pagfor`
del `auxpag`), `dircon1` queda `''` y aparece en `sin_fuente`, e `ivadif` sale del contrato (0) y **no** aparece en
`sin_fuente`.

**H2 · `contrato_albaranes.md` v8.3, §4.1 paso 2 (línea 401): el orden sin contrato contradice R7 y la propia §3.3.**
El texto dice «contrato … o, sin contrato, el proveedor por CIF (v8.3) → albarán anterior opcional (… del mismo
proveedor …)». El código (`use_case:393-413`), R7 y las filas 359-360 de §3.3 hacen lo contrario: sin contrato se
busca primero el albarán anterior **por CIF**, y L17 solo corre si no lo hay. **Escenario:** sin contrato, con un CIF
repetido en la empresa (M27: 4 CIF) y con albarán anterior, albaranes esperaría por §4.1 un `proveedor_ambiguo`, y lo que
recibe es un alta normal. **Cambio:** reescribir el paso 2 así: «… → contrato (localizador + esa obra) → albarán anterior
opcional (con contrato, por su `entide`; sin él, por CIF) → sin contrato ni albarán anterior, el proveedor por CIF
(`proveedor_no_encontrado`/`proveedor_ambiguo`) → idempotencia …». Además, en §4.2 (línea 417), sacar «identidad» de la
cadena «→»: según R4 no es cascada, va con el contrato aunque venga vacía. No hace falta un nuevo acuse: solo se alinea
el texto con §3.3, que ya está bien.

**H3 · Docstring del módulo desactualizado: `application/use_cases/albaran_compra_statements.py:13-17`.** Dice que
«`con`, `dca` y `dcapro` se CLONAN de su plantilla (`SELECT *`…)» y cita la v8.1. Eso contradice R1/D6 y el propio
código (`_TABLAS_CLONADAS = {"dcapro"}`, `:186`). **Cambio:** decir que solo se clona `dcapro`, que `con` y `dca` van
por lista blanca con columnas fijas (F-015) y citar la v8.3.

## Observaciones (no bloquean; para el humano)

- **O1 · Lectura de `auxefp` que el design no declara** (`use_case:500-507`). Es la decisión 2 del implementer, sin SQL
  nuevo (`read_full_row`). Si el `efeide` apunta a una fila de `auxefp` que no existe, el alta da 500 en vez de solo
  dejar de avisar. Es coherente con R10, aunque D12 dice «no para nada». Propuesta: que la próxima versión del design lo
  recoja en §Flujo.
- **O2 · Un NULL del origen elegido se escribe tal cual.** Solo una cascada **sin fuente** recibe el vacío del alta a
  mano. Si el contrato trae `pagide` ≠ 0 y `pagtex` NULL, o `ivadif` NULL, se escribe NULL. Es lo que dice la spec
  (pago en bloque; `ivadif` del `ctr`), y M21 da `pagtex` lleno en el 100 % de los contratos. Que lo vigilen los dry-runs
  de R29.
- **O3 · `entcod` va recortado cuando sale de L17** (`.strip()`, `use_case:450`) y sin recortar cuando sale del `ctr`
  o del respaldo. No tiene efecto en la práctica.

## Trazabilidad del bloque (requisito → test)

| R | Tests |
|---|---|
| R1 | `test_f015_r1_*` (lista, texto, origen, `INSERT` fijos de `con`/`dca`), `test_f015_r24_solo_dcapro_se_clona` |
| R2 | centinelas `test_f015_r25_*` (`_COLUMNAS_PRV` trae a propósito columnas con nombre de `dca`) |
| R3 | `test_f015_r3_*` (statements y caso de uso) |
| R4 | `test_f015_r4_*`, `test_f015_r6_sin_contrato_el_respaldo_por_cif_da_la_identidad`, `test_f015_r7_sin_contrato_ni_respaldo…` |
| R5 | `test_f015_r5_*` (statements y caso de uso: CC/CT/TR/` cc `, P/R/'', sin efecto, pago, en `creado`) |
| R6 | `test_f015_r6_*`, `test_f009_r11_proveedor_sin_albaran_previo_en_la_empresa` (ahora sigue) |
| R7 | `test_f015_r7_*` (SQL, único, ninguno, varios, no se busca con contrato) |
| R8 | `test_f015_r8_*` |
| R9 | `test_f015_r9_*`, `test_f015_r3_la_respuesta_lleva_lo_escrito_sin_las_bancarias` |
| R10 | `test_f015_r10_*` (statements y caso de uso, con `commit` true/false) |
| R11 | fuera de este bloque (lo mide C1C2C5) |
| R25 | `test_f015_r25_*` y `r3_*`: **falta con contrato y sin respaldo (H1)** |

## Cambios requeridos

1. **H1**: añadir a `tests/test_f015_statements.py` el centinela con contrato y sin respaldo, más el caso de vaciado sin
   respaldo, con las aserciones (a) y (b).
2. **H2**: corregir `specs/F-009-alta-albaran-compra/contrato_albaranes.md:401` (orden sin contrato) y `:417` (identidad
   fuera de la cascada).
3. **H3**: actualizar el docstring de `application/use_cases/albaran_compra_statements.py:13-17`.

## Automejora (propuesta, no aplicada)

Que `CHECKPOINTS.md` (C3) pida, en toda spec con «con y sin X, con y sin Y», que el test recorra la tabla completa de
combinaciones (producto cartesiano) con `pytest.mark.parametrize`, en vez de casos sueltos. El hueco de H1 es justo el
caso que falta en una matriz 2×2.
