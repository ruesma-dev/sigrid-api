<!-- progress/impl_F-009_loteE_docs.md -->
# F-009 · Informe del implementer · Lote E, parte documental (T17, T18)

Rama `feature/F-009-alta-albaran-compra`, 2026-10-06. Spec v8.2. Nivel `critico`. Sin red, sin Azure, sin SQL Server.
**Sin tocar código ni tests** (la campaña de mutación T16 va después, sobre el código tal cual).

| Commit | Repositorio | Qué |
|---|---|---|
| `1da0c5e` | sigrid-api | T17: `docs/ARCHITECTURE.md` + `tasks.md` (T17 `[x]`) |
| `51b29a6` | **azure-apps** | T18: `sigrid_api.md` (solo ese fichero; el `.env` de `azure-apps` está ignorado y no entra). Sin push: no tiene remoto |
| (este) | sigrid-api | `tasks.md` (T18 `[x]`), `progress/current.md` y este informe |

Fuentes leídas: `requirements.md` (R36), `design.md`, `tasks.md`, `contrato_albaranes.md` (§1-§4, H32, §7), los informes y
revisiones de los lotes C y D (lo marcado «para T17/T18»), `function_app.py`, `config/settings.py` y los casos de uso
(solo para comprobar lo que se escribe; nada se documentó sin mirarlo en el código).

## T17 · `docs/ARCHITECTURE.md` (+53/−3)

- **§Capas y estructura**: `build_dependencies()` con tupla de **ocho** posiciones (6 clásico, 7 extendido; O7 del lote
  D: el docstring «tupla de siete» de `tests/test_f004_route.py` sigue ahí, es un test de otra feature y no se toca);
  `albaran_compra_models` en `domain/models`; `create_albaran_compra_use_case` y `albaran_compra_statements` en
  `application/use_cases`.
- **Subsección nueva «Los dos modos de `sigrid/albaran` (F-009)»**: selector por claves (`elegir_modo_albaran`,
  `peticion_mixta`); clásico intocable y fijado por el dorado de caracterización, obsoleto con F-053 en real; extendido
  por capa (domain: modelos y `AlbaranCompraError`; application: SQL constante L1-L15/E1-E12 autovalidado con
  `DatabaseReferenceGuard` + funciones puras + caso de uso con `work` reentrante en una transacción bajo los applocks en
  su orden; infrastructure: nada nuevo); la colisión sale del caso de uso como `AlbaranCompraError(colision_de_clave)`
  y la ruta no captura `IntegrityError` (O4 del lote D); guarda R8 en las dos rutas entre el modelo y el caso de uso;
  traza R32 emitida por el caso de uso, y lo que la ruta corta antes solo deja su `warning` (O6 del lote D).
- **§Acceso a datos**: la segunda llave propia de albaranes, partes y documentos.

## T18 · `azure-apps/sigrid_api.md` (+214/−35), sección a sección

| Sección | Cambio |
|---|---|
| Intro, §1.1, §1.2 | Mención del modo extendido; los tres ficheros nuevos en el árbol; tupla de ocho |
| **§4** | Seis filas nuevas `SIGRID_ALBARAN_*` con defecto y efecto (vacías cierran, también en dry-run donde aplica); el mapeo **solo objeto JSON** y estricto también en código (CSV, lista, valores no texto o vacíos, claves repetidas ⇒ no arranca); listas solo JSON |
| **§4.1** | Las seis claves «aún sin fijar» con los valores previstos de T19: `WRITE_ENABLED=false` hasta la grabación autorizada, `["ALB-"]`, `["MA9999", "QA9999", "XA9999"]`, `[1]`, `{"MA9999": "MA99", "QA9999": "QA99", "XA9999": "XA99"}`, `MAX_LINEAS` por defecto; aviso: **`dev` escribe en la base real `ruesma`; la previa (`commit:false`) es el entorno de prueba** |
| **§7.2** | Punto 8: `SIGRID_ALBARAN_WRITE_ENABLED` en los dos modos y en `albaran-directo`, 400 `escritura_albaranes_deshabilitada` con `type` `AlbaranCompraError` **también en clásico y directo** (decisión 1 del lote D), tras validar y antes del caso de uso; en el extendido, `ALLOWED_WRITE_DATABASES` vacía no abre (solo en commit); el clásico conserva lo de siempre |
| **§7.5** | **Corregido H32**: el `cod` va fuera de la transacción solo en el clásico y el directo; párrafo nuevo del extendido (todo dentro, applocks en orden, `UPDLOCK, HOLDLOCK`, reintento de la transacción entera); nota «`colision_de_clave` no siempre es una colisión»: el repositorio reintenta **toda** `IntegrityError` (no solo 2627/2601), una fila mal construida acaba en `colision_de_clave` con un «reenvíalo» engañoso, ERP intacto; compartido con F-006 y el clásico (este, agotados los reintentos, da 500; comprobado en `function_app.py`) |
| **§7.6** | Fila del clásico corregida (solo `lineas_recibidas`, suma por `ctrpro`; **no** replica el contrato); fila nueva del extendido (qué escribe, `UPDATE` solo con vinculadas, nada de `dcapropar`/`dcaproana`/`pro`) |
| §8 (tabla) | La fila de `sigrid/albaran` nombra los dos modos |
| **§8.6** | Reescrita. Selector; clásico corregido (H32) y **obsoleto cuando F-053 esté en real**; extendido con **enlace al contrato** de la spec (no se copia) y lo esencial: petición, resolución (almacén: contrato si `ctr.almide` ≠ 0, ficha de obra, único `alm`; centro de la misma fuente: decisión 3 del lote C), respuesta 200, **`lineas[].producto` `null` en vinculadas** (albaranes no lo lee), `idempotente` con `fec` en `cabecera = {"fec": …}` y `totales` (decisión 9 del lote C), **`details.lineas` con varias entradas por línea** (origen, partida, precio; sv9 se queda con el peor código), orden R8 frente a `demasiadas_lineas` (O3 del lote D, con su efecto en F-053), **400 de texto libre** también para maestro incoherente (IVA fuera de `dbo.iva`, plantilla ilegible; F-053 ⇒ `error`), 500 con `str(exc)` (O2 lote D), **ante un 500 en grabación reenviar la misma `referencia_externa`** (O6 del lote C, trozo 2), `ValidationError` interno (O1 lote D), trazas R32 y límites (O7 del lote C, `prepma` por verificar) |
| **§8.7** | Sin cambios salvo R8; **obsoleto cuando F-053 esté en real**; el directo hereda `paride` de la plantilla y el extendido nunca (comprobado en `create_direct_albaran_use_case.py`) |
| **§10** | El pipeline sv1-sv6 queda en `sql/read`; fila nueva **albaranes sv9 (F-053)**: modo extendido (previa siempre, grabación única), `sql/read` y `concepto-grafico`; nunca clásico, directo ni `sql/write`; F-009 sin desplegar; enlace a `albaranes.md` y al contrato |
| §12 | La fila de «400 de permisos» ya no dice «5 condiciones» y nombra la llave de albaranes |
| **§13** | «Replica todas las líneas» corregido; clásico y directo obsoletos con F-053; estado de F-009 (implementado, sin desplegar, lo que falta: T19-T24); roadmap 1, 2 y 4 cerrados o reorientados; punto nuevo: filtrar el reintento por número de error |

**Secretos**: ninguno. El diff solo nombra App Settings, tablas y ficheros; se escaneó en busca de IP, GUID y
contraseñas (nada; la única coincidencia es la palabra «secretos»). Los nombres de la Function App y del grupo de
recursos ya estaban en el documento.

**No hecho a propósito**: §9.7 (numeración y PMP del clásico) no se tocó: no la pide R36 y describe el clásico, que no
cambia. El docstring de `tests/test_f004_route.py` (O7 del lote D) es un test: fuera del encargo.

## `bash harness/init.sh` (tal cual)

Al empezar (precondición), en verde: `2339 passed, 1 skipped`, cobertura 100,0 % (1102/1102). Al terminar, con T17,
T18 y este informe:

```
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 80 avisos (deuda previa, no bloquea)
2339 passed, 1 skipped, 1 warning in 78.27s (0:01:18)
[OK] pytest en verde (con medición de cobertura)
[OK] PUERTA COBERTURA: 100.0% de 1102 líneas cambiadas cubiertas (1102/1102, umbral 80%, nivel critico)
[OK] PUERTA TAMAÑO: F-009 dentro de los topes (requirements 150/150, design 250/250, impl 196/220, review 117/140)
[OK] Rama actual: feature/F-009-alta-albaran-compra
ENTORNO LISTO. Puedes trabajar.
```

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados | 2339 passed, 1 skipped (`bash harness/init.sh`); este lote no añade tests (solo documentación) |
| Cobertura de las líneas cambiadas | 100,0 % (1102/1102) (línea `PUERTA COBERTURA`); sin líneas de código nuevas en este lote |
| Mutantes | No aplica a este trozo (solo documentación). La campaña `critico` de la feature es **T16**, que se lanza ahora sobre el código sin cambios |
| Tiempo de la suite | 78,27 s la suite completa con cobertura |

## Fase RED

No aplica: T17 y T18 son documentación (verificación «revisión del reviewer»), sin requisitos de comportamiento nuevos.

## Lo que queda

- **T16** campaña de mutación de la feature; después, revisión del lote E (T16-T18).
- Manuales T19-T24 (despliegue con los valores de §4.1, previas, grabación autorizada, anulación, primera alta real).
  Tras T19, actualizar §4.1 de `azure-apps/sigrid_api.md` de «previsto» a «fijado el <fecha>».
- Al hacer merge de la rama, el enlace al contrato de §8.6/§10 deja de depender de la rama (ya lo dice el texto).
