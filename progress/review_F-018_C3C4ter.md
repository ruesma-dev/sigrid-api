Revisión completa (pasada 1) · `git diff dev` (merge-base `6aca027`) hasta HEAD `7ce2240`

# Review F-018 · bloque C3, C3 bis y C4 ter (revisión troceada)

- **Veredicto del bloque: APROBADO.** Sin cambios requeridos.
- **Nivel de rigor:** `critico`, declarado en `harness/features.json`. Este bloque no lleva puertas propias de rigor
  (RED, cobertura y mutación son de C4/C4 bis, en otro trozo); sí exige revisar las rutas de escritura en producción.
- **Lo que no he hecho, por las reglas de convivencia:** no ejecuté `bash harness/init.sh` ni la suite completa (lo
  hace otro revisor), no apliqué mutantes y no edité el árbol. Las medidas sobre `dev` se hicieron en copias
  `git archive` dentro de mi scratchpad, borradas al acabar.

## Verificaciones ejecutadas (con resultado real)

| Qué | Cómo | Resultado |
|---|---|---|
| Huella SQL (R23) | sha256 de `todas_las_sentencias()` de `AlbaranCompraStatements`, `ProformaStatements` y `ProformaOrigenStatements`, más sha256 de **todas** las constantes de módulo con `SELECT/INSERT/UPDATE/DELETE/MERGE/EXEC` de cada `application/use_cases/*.py`, en una copia de `dev` y otra de HEAD | **Idénticas**: 47/6/3 sentencias (`d494a01d…`, `eda6c100…`, `61e9021f…`, las mismas que fija `_SQL_DE_DEV` en `test_f018_use_case.py:346`); 40/6/3 constantes, mismos hashes |
| INSERT dinámico | `construir_dcapro_*` ya escribían `pre`, `tar`, `dto` y `tot` en `dev`; `construir_dca` ya escribía `impbru` | Mismo conjunto de columnas: el `dto` viaja en la fila clonada. Lo fija también `test_f018_r23_el_commit_con_dto_usa_las_mismas_sentencias_que_sin_el` |
| Tests de R23, R24 y protegidos | `pytest tests/test_f009_models.py tests/test_f016_models.py tests/test_f018_*.py` | **427 passed** |
| `ruff` en lo cambiado | `ruff check` (0.16.5) sobre los 4 ficheros de código y los 7 de test | Los 4 de producción y los tests: limpios salvo **3 avisos de `function_app.py` (I001, BLE001, RUF010) idénticos en `dev`** (deuda previa; F-018 solo tocó su docstring) |
| Rutas protegidas | `git diff dev --name-only` y `git log dev..HEAD --name-only` (cada commit, no solo el neto) | Ni `infrastructure/`, ni `infra/`, ni `config/`, ni `.env`, ni `local.settings.sample.json`, ni `tests/fixtures/`, ni `f007/f009/f016_dobles.py`, ni `requirements*.txt` |
| Tests existentes protegidos | `git diff dev -- tests/test_f009_models.py tests/test_f016_models.py` | Exactamente las **tres líneas autorizadas**: `"dto_distinto_del_contrato",` en `test_f009_models.py:426` (P9), `"dto", "precio_bruto",` en `:549` dentro de `test_f009_r7_la_respuesta_es_superconjunto_de_la_clasica` (P11) y `"dto_distinto_del_contrato",` en `_AVISO_F007` de `test_f016_models.py:210` (P10). Ningún otro test existente modificado en ningún commit de la rama |
| Barrido de datos sensibles | Sobre las 2.745 líneas añadidas de `git diff dev` (código, specs, tests y `progress/`). Patrones: correo `[\w.%+-]+@[\w.-]+\.\w{2,}`; IPv4; GUID; CIF/NIF `[A-HJNP-SUVW]-?\d{7}[0-9A-J]`, `\d{8}[A-Z]`, `[XYZ]\d{7}[A-Z]`; IBAN `ES\d{2}`; `password\|secret\|token\|api_key\|function_key\|code=\|sig=\|AccountKey\|SharedAccess\|Bearer\|connection string`; cadenas `[A-Za-z0-9+/=_-]{40,}`; razones sociales (`S.L.`, `S.A.`, `SLU`, `Construcciones`, `Hnos`); pares de palabras en mayúscula inicial (nombres) y palabras en mayúsculas de 5+ letras (proveedores) | **Limpio.** Correos: solo `@pytest.mark.parametrize`. Claves: solo `verificacion_manual.md`, que las toma de variables de entorno (`$env:SIGRID_API_FUNCTION_KEY` vía `az functionapp keys list`), sin literal. Cadenas largas: separadores y rutas. Sin CIF, IBAN, IP, GUID, personas ni proveedores; sí códigos internos de documento/obra/producto (`PROF26/01377`, `0692`, `MA9999`), como en features anteriores |

## C3 — El código respeta arquitectura y convenciones

- [x] **Hexagonal.** `domain/models/albaran_compra_models.py` solo añade `decimal` y símbolos de `pydantic`
      (`SerializerFunctionWrapHandler`, `model_serializer`). La lógica nueva (funciones puras y filas) está en
      `application/use_cases/albaran_compra_statements.py`, sin E/S; el caso de uso no importa nada nuevo de
      `infrastructure/`. `function_app.py`: solo docstring. Ficheros cambiados = tabla «Ficheros a modificar» del
      design; los de «NO se tocan» siguen intactos (incluidos `create_proforma_use_case.py` y `proforma_*`).
- [x] **Primera línea con la ruta** en los 11 `.py` cambiados o nuevos (comprobado uno a uno).
- [x] **Sin `print()`, sin TODO/FIXME, sin `breakpoint`/`pdb`** en líneas añadidas. **Sin secretos** (barrido
      arriba). **Sin dependencias nuevas**: solo `re` y `decimal` (stdlib) y API de `pydantic` ya instalada;
      `requirements*.txt` sin tocar. Pydantic: `dto: float | None = Field(default=None, ...)` sigue el patrón ya
      existente en la misma clase (`partida`, `paride`).
- [x] **Reglas de dominio de Sigrid:**
  - [x] **Base correcta**: todo contra `ruesma` por el endpoint de dominio `sigrid/albaran` (y la proforma por el
        núcleo); `ruesma_rep` no aparece en el diff de código.
  - [x] **`cod`/`res`/`fec`/`tip`/`est` en `con`**: `construir_con` no cambia; F-018 solo toca `dcapro` y `dca.impbru`.
  - [x] **Nada se recalcula solo**: con descuento efectivo, los importes de cabecera salen de la **fila**
        (`create_albaran_compra_use_case.py:1023-1031`), `impbru` = Σ brutos (R8), el `mov` y el PMP toman
        `dcapro[i]["pre"]` (neto; l. 1042 y 1059, sin cambio de código) y `canser` sigue por cantidad
        (`construir_ctrprodes(cantidad=...)`; lo fija `test_f018_r24_commit_vinculada_r15`). `_con_dto_efectivo`
        aplica la misma regla que `construir_dcapro_vinculada` (`vinculada` ⇔ `ctrpro is not None`, l. 253).
  - [x] **Estados nunca hardcodeados**: el diff no introduce ningún estado.
  - [x] **SQL parametrizado**: no hay SQL nuevo ni cambiado (huella idéntica arriba).
- Observación, no bloqueante: `assert datos.dto is not None` (`create_albaran_compra_use_case.py:1704`) es un
  estrechamiento de tipos; el llamador lo garantiza (`if datos.con_dto`) y sigue un patrón que ya existe en el mismo
  fichero (l. 216, 921, 1485).

## C3 bis — Los documentos que entran de fuera son seguros

- N/A **justificado**: la feature no añade ni modifica nada en `docs/referencia/` (`git diff dev --name-only` y
  `git log dev..HEAD --name-only`). Además, ningún commit de la rama añadió jamás un PDF u ofimático
  (`git log dev..HEAD --diff-filter=A --name-only`: solo `.md` y `.py`). El barrido de datos sensibles se hizo igual
  sobre todo lo añadido (tabla de arriba) porque el encargo lo pedía.

## C4 ter — Las verificaciones extra por rutas sensibles están hechas

- N/A **justificado**: el repositorio no declara `harness/rutas_sensibles.json` (no existe en HEAD ni en ningún commit
  de ninguna rama: `git log --all -- harness/rutas_sensibles.json` vacío). Sin declaración, CHECKPOINTS dice que el
  bloque es N/A y la puerta de `init.sh` (§7 ter, l. 513) no se activa.
- **Verificaciones extra pedidas por el líder (escritura en Sigrid de producción)**, hechas a mano:
  - [x] Sin endpoint ni ruta nueva, sin App Setting nuevo; las llaves `SIGRID_ALBARAN_WRITE_ENABLED` y
        `SIGRID_PROFORMA_WRITE_ENABLED` y el dry-run por defecto (`commit` falso) no cambian (`function_app.py`: solo
        docstring; `config/` sin tocar).
  - [x] R24: la escritura con descuento va por la misma transacción, applocks (`APPLOCKS`), reintento con nuevos
        `ide` y relecturas: `test_f018_r24_commit_sin_vincular_con_dto`, `_commit_vinculada_r15` y
        `_reintento_con_los_mismos_importes` (pasan).
  - [x] Ningún `DELETE`: las 7 apariciones en lo añadido son «nunca `DELETE`» / anulación desde la UI.
  - [x] `verificacion_manual.md`: todo por la API desplegada (`sql/read` y endpoints de dominio), lecturas con parada
        si `truncated`, `commit:false` en V2, V3 y V5, y el único `commit = $true` (V4, l. 135) está bajo el epígrafe
        «el humano, con autorización expresa para esta escritura», con usuario `prueba` y anulación desde la UI.
  - [x] Trazas (R18): solo el contador `n_lineas_con_dto`; ni porcentajes, ni precios, ni importes.

## Cobertura de lo que toca a este bloque

| Requisito | Test que lo cubre |
|---|---|
| R23 (sin SQL nuevo) | `test_f018_use_case.py::test_f018_r23_las_sentencias_son_las_de_dev`, `::test_f018_r23_el_commit_con_dto_usa_las_mismas_sentencias_que_sin_el` + mi huella independiente |
| R24 (transacción) | `test_f018_use_case.py::test_f018_r24_*` (3) |
| R7/R17 (tres líneas) | `git diff dev` de los dos ficheros protegidos (arriba) y `test_f018_compatibilidad.py` (T13) |

## Cambios requeridos

Ninguno.

## Propuesta de automejora (no aplicada)

1. `CHECKPOINTS.md` C3 podría pedir que el reviewer **compare `ruff` contra `dev`** en los ficheros tocados y no solo
   «sin avisos»: aquí `function_app.py` arrastra 3 avisos previos que, leídos sin comparar, parecerían de la feature.
2. `verificacion_manual.md` V1a imprime el CIF del proveedor (`d.entcif`) en consola. Es correcto (no se escribe en el
   repo), pero conviene que la plantilla de verificación manual del arnés recuerde **no pegar esas salidas en
   `progress/`** sin redactar el CIF.
