<!-- progress/review_F-007_mutacion.md -->
Revisión completa (pasada 1) · encargo acotado: **solo la parte de mutación de C4 bis**, HEAD `fe85523`

# F-007 · Revisión de la mutación (C4 bis)

**Veredicto de este bloque: CHANGES_REQUESTED** (dos cambios, abajo). El resto de C4 bis y C1-C5 lo cubren
los otros reviewers.

**Nivel de rigor:** `critico`, declarado en `harness/features.json`. Exige fase RED, cobertura, mutación y
**cero supervivientes salvo justificación escrita aceptada por el humano**, además de RM5 (reproducir un
equivalente).

**Cómo se midió.** Todo en un worktree propio y desechable (`git worktree add ../sigrid-api-rev007-mut fe85523`,
HEAD separado), ya borrado (`git worktree list` solo muestra el árbol compartido). Cada mutante es una sustitución
exacta de texto aplicada por un script del scratchpad (`mutar_rev007.py`) que comprueba que el original aparece
**una sola vez**, ejecuta pytest y restaura con `git checkout`. Al final el árbol del worktree quedó limpio. No se
ha tocado el árbol compartido, ni se ha ejecutado `init.sh` ni la campaña, ni se ha hecho ningún commit.
Línea base del worktree: `tests/test_f007_*.py tests/test_f009_*.py tests/test_f015_*.py` → **1282 passed**, 9 s.

Comando de cada fila: `python -m pytest <tests> -q --tb=no -p no:cacheprovider -rf`, donde `<tests>` es
**T** = `tests` (suite entera), **7** = `tests/test_f007_*.py` y **N** = `tests/test_f009_*.py tests/test_f015_*.py
tests/test_f007_perfil.py`. «Fallos» es el número de tests en rojo con el mutante aplicado.

## 1-2 · Supervivientes de la ronda 2 y el falso superviviente de la ronda 1

| Mutante | Original → mutado | Tests | Resultado medido | s |
|---|---|---|---|---|
| R2-1 `albaran_compra_statements.py:331` | `*, cifras: int = 0) -> str:` → `cifras: int = 1` | T | **SOBREVIVE**: `3347 passed, 1 skipped`, exit 0 | 121 |
| R2-2 `proforma_models.py:170` | `<= 2999` → `<= 3000` | 7 | **MUERE**: 1 fallo (`test_f007_t18_fecha_proforma_fuera_de_los_anios[30000101]`) | 10 |
| R1 `albaran_compra_statements.py:328` | `% 100:02d}/` → `% 101:02d}/` | 7+N | **MUERE**: 29 fallos (7 F-009 statements, 10 F-009 use_case, 3 equivalencia, 4 perfil…) | 15 |

- **R2-1 es equivalente: lo reproduzco (RM5, muestra de uno).** La suite entera sigue en verde con el mutante. Además,
  `str(n)` nunca es vacío (tampoco con signo), así que `zfill(0)` y `zfill(1)` coinciden para cualquier entero.
  El defecto no es código muerto: lo usa la llamada sin `cifras` de `test_f009_r26_siguiente_cod`. **Falta la
  aceptación del humano por escrito** que exige el nivel `critico`. El informe dice «justificado para el humano»,
  pero no consta que la haya dado: tiene que quedar registrada antes de cerrar.
- **R2-2**: el test corregido en `8c92d52` lo mata. Encaja con la fase ROJA que trae el informe.
- **R1**: muere, y no solo en `test_f007_perfil` sino también en F-009. Confirmo que el «superviviente» de la ronda 1
  era falso. La causa sigue sin diagnosticar. Ver la propuesta para `arnes-base`, abajo.
- **RM1**: el informe midió `7cbff6b`. Entre `7cbff6b` y `fe85523` solo cambian `tests/test_f007_models.py` (el test
  de `8c92d52`), `progress/` y `tasks.md`. Ningún fichero del alcance cambió, así que la campaña sigue valiendo. [x]
- **RM2**: línea base 67,8 s; media 10,0 s con 1 worker. 374 × 10,0 = 3740 s frente a 3755 s declarados: cuadra.
  La media es 1/6,8 de la base, que no es un salto de orden de magnitud, y con `-x` y 372 de 374 muertos es lo
  esperable. El coste por mutante es de 10 s, muy por encima de 1 s. [x]
- **60 s**: el «Tiempo total» es de 3755 s, así que **la campaña no se ha reejecutado** (además, el encargo lo
  prohíbe). Sustituyen a la reejecución estas mediciones a mano y RM4.
- **RM6**: se quitaron el `break` de `identificar_linea` (código muerto, no defensivo) y el `or 0` de `es_proforma`.
  Ahora es `cla == CLA_PROFORMA`: un `cla` NULL da `False` sin romper, y hay un test con NULL. No se perdió
  ninguna defensa. [x]

## 3 · Núcleo de F-009: mis mutantes sobre las costuras (`create_albaran_compra_use_case.py` salvo indicación)

| Mutante | Original → mutado | Tests | Resultado medido | s |
|---|---|---|---|---|
| N1 perfil: ancho de serie | `PERFIL_ALBARAN … cifras_serie=0,` → `cifras_serie=5,` | N | MUERE: 3 (2 `test_f009_use_case`, 1 perfil) | 13 |
| N2 perfil: prefijo | `prefijo_serie="AC",` → `prefijo_serie="ACX",` | N | MUERE: 15 (10 F-009 use_case, 3 equivalencia, 2 perfil) | 12 |
| N3 prefijo del perfil al sello | `request.fecha_albaran, self.perfil.prefijo_serie` → `request.fecha_albaran` | N+7 | MUERE: 6 (1 perfil, 2 transacción, 3 use_case) | 14 |
| N4 sin gancho R28 | borrar la línea `self._comprobar_dentro(cursor, request, cabecera)` | N+7 | MUERE: 7 (1 perfil, 6 transacción) | 16 |
| N5 albarán con productos del contrato | `productos_del_contrato=False,\n)` → `=True` | N | MUERE: 3 (1 `test_f009_r13_la_lista_blanca_es_exacta…`, 2 perfil) | 10 |
| N6 código de la llave | `codigo=perfil.codigo_llave,` → `codigo="escritura_albaranes_deshabilitada",` | N+7 | MUERE: 4 (1 perfil, 3 use_case) | 14 |
| **N7 `_Catalogo`: primera línea por `proide`** | `por_proide.setdefault(_entero(ctrpro.get("proide")), ctrpro)` → `por_proide[_entero(ctrpro.get("proide"))] = ctrpro` | N+7 | **SOBREVIVE**: `1282 passed`, exit 0 | 15 |
| N8 sin vincular ignora el contrato | `if ctrpro is None and producto not in self._lista_blanca:` → `if producto not in self._lista_blanca:` | N+7 | MUERE: 29 (4 perfil, 14 transacción, 11 use_case) | 17 |
| N9 conjunto `permitidos` | `if p in self._lista_blanca and p not in self._del_contrato]` → `if p in self._lista_blanca]` | N+7 | MUERE: 1 (`test_f007_r17_un_producto_de_la_lista_que_es_del_contrato…`) | 16 |
| N10 aviso de IVA | `and not linea.vinculada and not linea.del_contrato:` → `and not linea.vinculada:` | N+7 | MUERE: 1 (`test_f007_r17_…_sin_aviso_de_iva`) | 13 |

Los que cambian la conducta del albarán (N1, N2 y N5) mueren en `tests/test_f009_*.py`. Todos los demás, salvo N7,
mueren al menos en `tests/test_f007_perfil.py`, que es lo que pedía el encargo.

**N7 no es equivalente: lo he medido.** Escribí un test desechable en el worktree, sin versionar y ya borrado, con el
contrato del doble más una línea `9004` (`proide` 55, `pos` 256, `ivaide` 7) y una sin vincular `HA25` en
`CasoConProductosDelContrato`. Con el código original pasa (`1 passed`, `ivaide` 3, el de la primera línea por
`pos`). Con N7 aplicado falla (`1 failed`). Si un producto aparece en dos líneas del contrato con distinto IVA,
nadie comprueba de cuál sale el IVA. La regla «la PRIMERA por `pos`» solo está en el docstring de
`_productos_del_contrato` (línea ~1305): no aparece en `requirements.md` ni en `design.md`. La herramienta no
podía verlo porque no muta llamadas a métodos. Es un hueco real en código del núcleo que se desplegará.

## 4 · `create_proforma_use_case.py` (R14, R24, R28)

| Mutante | Original → mutado | Tests | Resultado medido | s |
|---|---|---|---|---|
| P1 R14 un fallo no corta | `if fallos:` → `if len(fallos) > 1:` | 7 | MUERE: 1 (`test_f007_r33_traza_de_un_error`) | 7 |
| P2 R14 sin líneas del contrato | `request.lineas, lineas_contrato, sin_contrato=…` → `request.lineas, [], sin_contrato=…` | 7 | MUERE: 43 | 6 |
| P3 R24 `existente` invertido | `if existente is not None:\n return self._existente(` → `if existente is None:` | 7 | MUERE: 39 | 7 |
| P4 R24 `otra_del_mes` fuera | `otra_del_mes=request.otra_del_mes,` (paso 5) → `otra_del_mes=True,` | 7 | MUERE: 13 | 6 |
| P5 R28 contexto sin contrato | `ctride=ctride, periodo=request.periodo,` → `ctride=0, …` | 7 | MUERE: 6 (transacción) | 8 |
| P6 R28 `otra_del_mes` dentro | `otra_del_mes=contexto.otra_del_mes,` → `otra_del_mes=True,` | 7 | MUERE: 2 (`test_f007_r28_dentro_aparece…`) | 8 |
| P7 R28 no lanza | `if existente is not None:\n raise _ExistenteDentro` → `if existente is None:` | 7 | MUERE: 11 | 8 |

P1 solo lo mata un test de traza. Con una única línea mala, el núcleo acaba rechazando la petición por su cuenta
(`lineas_no_validas`) y la respuesta es la misma: muere, pero por poco. Lo dejo anotado, no es un cambio requerido.

## 5 · ¿Se pueden repetir los manuales A1-A5 y S1-S5 del implementer?

**No: [ ].** `impl_F-007.md` (T18) y `mutacion_F-007.md` los describen solo en prosa («un código de proforma en el
conjunto base», «tope 100»…), sin línea ni **texto exacto original → mutado** y sin número de fallos por
mutante. `albaran_compra_models.py` dio **0** mutantes automáticos y A1-A5 lo sustituyen, así que aplica el checkbox
de campaña MANUAL de C4 bis: «describir la mutación con palabras no la hace reproducible». Reconstruí los diez a
partir de la prosa (mi lectura, que puede no ser la suya) y **mueren los diez**:

| Mutante (reconstruido) | Original → mutado | Tests | Fallos | s |
|---|---|---|---|---|
| A1 | `CODIGOS_LINEA`: añadir `"linea_ambigua",` tras `"linea_no_es_del_contrato",` | 7+N | 2 (f007_models, f009_models) | 17 |
| A2 | `CODIGOS_CABECERA`: añadir `"proforma_del_mes_existente",` tras `"peticion_mixta",` | 7+N | 1 (`test_f009_r9_codigos_cerrados_de_design`) | 16 |
| A3 | `FalloLinea`: `if value not in cls.codigos:` → `CODIGOS_LINEA` | 7+N | 8 | 17 |
| A4 | `AlbaranCompraError`: `if codigo not in type(self).codigos:` → `CODIGOS_CABECERA` | 7+N | 35 | 17 |
| A5 | `AvisoAlbaran`: `if value not in cls.codigos:` → `CODIGOS_AVISO` | 7+N | 38 | 18 |
| S1 | `sigrid_proforma_write_enabled: bool = Field(False,` → `Field(True,` | 7 | 1 | 5 |
| S2 | quitar `"sigrid_proforma_prefijos_referencia",` de `parse_string_list` | 7 | 4 | 5 |
| S3 | quitar `"sigrid_proforma_naturaleza_por_producto",` de `parse_string_dict` | 7 | 8 | 4 |
| S4 | `Field(500, alias="SIGRID_PROFORMA_MAX_LINEAS")` → `Field(100, …)` | 7 | 1 | 5 |
| S5 | `alias="SIGRID_PROFORMA_PRODUCTOS_SIN_CONTRATO"` → `"SIGRID_ALBARAN_PRODUCTOS_SIN_CONTRATO"` | 7 | 6 | 7 |

Es decir, la conclusión del implementer se sostiene, pero su evidencia no se puede repetir tal como está escrita.

## Cambios requeridos

1. **N7 · hueco de test en el núcleo** (`application/use_cases/create_albaran_compra_use_case.py`,
   `_Catalogo._productos_del_contrato`, el `setdefault`): un test en `tests/test_f007_perfil.py` con dos líneas del
   contrato del mismo `proide` y distinto `ivaide` que fije que el IVA sale de la primera por `pos`. Mi test desechable
   del §3 sirve de plantilla. Si la regla «la primera» es una decisión de negocio, que conste también en
   `design.md` (R17), porque hoy solo vive en el docstring. Con el test, la fase ROJA se demuestra aplicando N7.
2. **Manuales irreproducibles**: en `progress/mutacion_F-007.md`, o en T18 de `impl_F-007.md`, una tabla de A1-A5 y
   S1-S5 con una fila por mutante: fichero:línea, **texto exacto original → mutado** y número de fallos. Basta con la
   suya. Si coincide con mi reconstrucción, puede copiar las filas de arriba.
3. *(No bloqueante en este bloque, pero necesario para cerrar en `critico`)*: que conste la aceptación del humano
   para el equivalente R2-1 (`cifras: int = 0`).

## Propuesta de automejora (no aplicada)

- El generador no muta llamadas a métodos (`setdefault`, `get`, `append`…) ni elige entre la primera y la última
  aparición, y por eso N7 se le escapó. En `.claude/agents/reviewer.md` (núcleo y rigor `critico`): exigir al
  menos un mutante manual del tipo «primera ↔ última» cuando el diff construye un diccionario con `setdefault` o con
  `next(...)`. Para `arnes-base`: el falso superviviente `% 101` de la ronda 1 sigue sin diagnosticar.
