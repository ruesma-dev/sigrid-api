Revisión completa (pasada 1) · bloque acotado «núcleo de F-009» (R31, D12) · rama `feature/F-007-registrar-proforma`, HEAD `fe85523`, base `dev` = merge-base `60db955`

# Review F-007 · costuras en el núcleo de F-009

**Veredicto del bloque: APPROVED.** `sigrid/albaran` (clásico y extendido) y `sigrid/albaran-directo` producen lo
mismo que en `dev`. Sin cambios de conducta escondidos. Tres observaciones no bloqueantes (O1-O3).

**Nivel de rigor:** `critico` (declarado). Este encargo solo cubre R31/D12. No ejecuté `init.sh`, la suite completa ni
la campaña de mutación: el coordinador lo prohibió en este encargo, porque otros reviewers cubren esos bloques.

## Qué se ejecutó

| Comprobación | Resultado |
|---|---|
| `git diff dev -- tests/test_f009_* tests/test_f015_* tests/fixtures/f009_caracterizacion.json tests/f009_dobles.py` | **vacío** |
| `pytest tests/test_f009_*.py tests/test_f015_*.py tests/test_f007_perfil.py -q` | **853 passed** |
| Diferencial `dev` ↔ HEAD (ver abajo) | **279/279 ejecuciones idénticas** |
| `git status` después | limpio (solo los informes sin seguimiento de los otros reviewers) |

**Diferencial (más allá de lo que afirman los tests).** Exporté `dev` y HEAD con `git archive` a mi scratchpad y corrí
los 816 tests de F-009 y F-015 en cada árbol. Un plugin de pytest envolvía `CreateAlbaranCompraUseCase.run` (solo la
clase base) y grababa, por cada llamada:
- la respuesta completa (`model_dump`) o la excepción (clase, texto, `codigo` y `lineas` con sus mensajes);
- todas las lecturas del doble, con su SQL y sus parámetros;
- las sentencias dentro de la transacción y sus parámetros;
- la configuración de cada transacción (`applock_resources`, timeout, reintentos);
- todos los registros de log, incluida la traza.

Son 279 ejecuciones: 114 acaban en excepción y 42 abren transacción. Tras descartar `duracion_ms`, las grabaciones
coinciden por completo. La única diferencia es el test `r22_el_instante_por_defecto_es_utc_con_zona`, que usa el reloj
real, y solo afecta a `hor`, `fechor` y `tiemod`.

## Cambio a cambio

**`create_albaran_compra_use_case.py`**
- `_ENDPOINT` → `perfil.endpoint`: el valor es `"sigrid/albaran"`, el mismo. No quedan más usos en el módulo (la de
  `partes-reclamacion` es otra constante, de otro módulo). La traza no cambia.
- `PerfilAlta` / `PERFIL_ALBARAN` reproducen los literales de antes:
  - serie: `AC` con `cifras_serie=0`;
  - `cla=0`, que el núcleo no lee: la `dca.cla` del albarán sigue saliendo del constructor de filas, sin tocar;
  - llave: `escritura_albaranes_deshabilitada`;
  - campos: los cinco `sigrid_albaran_*`;
  - `productos_del_contrato=False` y `error=AlbaranCompraError`.

  Es atributo de clase de `CreateAlbaranCompraUseCase`. `CreateProformaUseCase` lo sobrescribe en la subclase, sin
  mutar la base ni `PERFIL_ALBARAN`, y no hay efectos al importar `create_proforma_use_case` ni `proforma_models`.
- `_comprobar_guardas`:
  - `getattr(settings, campo)` equivale al acceso directo;
  - el orden de las guardas no cambia: tope de líneas → prefijos → (dry-run sale) → llave → base;
  - `perfil.campo_llave.upper()` da `SIGRID_ALBARAN_WRITE_ENABLED`, así que el mensaje es idéntico (lo afirma
    `test_f007_r31_el_mensaje_de_la_llave_del_albaran_es_el_de_hoy` y el diferencial lo confirma);
  - el código de error y la clase son los mismos.
- `sellos_del_alta(..., self.perfil.prefijo_serie)` → `AC`. `siguiente_cod(..., cifras=0)` usa `str(n).zfill(0)`, que
  da lo mismo que el `f"{n}"` de antes, también con `Decimal` y `float`. Sigue siendo `AC<aa>/N` sin ceros.
- `_comprobar_dentro`:
  - va dentro de `work`, después de E1 y de la salida idempotente, y antes de `reservar_cod`;
  - en la base tiene el cuerpo vacío: no lee ni toca el cursor;
  - se llama en cada intento reentrante y nunca en la previa.

  El orden de las sentencias y de los applocks no cambia: `_SECUENCIA_COMPLETA` y `applock_resources` de
  `test_f009_use_case` pasan, y las cuatro pruebas de `test_f007_perfil` sobre el gancho también. `infrastructure/`
  no se toca.
- `_Catalogo.__init__` con el interruptor apagado:
  - `leidos` contiene la misma lista, en el mismo orden y con los mismos duplicados, que el `permitidos` de antes;
  - `_del_contrato` queda en `{}` y no se lee nada de más;
  - `permitidos` coincide con `leidos`;
  - el orden de lectura sigue siendo partidas → productos → naturalezas, los mismos parámetros (diferencial).
- `_sin_vincular`:
  - `ctrpro` es `None`, así que la condición se queda en `producto not in lista_blanca`;
  - los mensajes nombran `SIGRID_ALBARAN_PRODUCTOS_SIN_CONTRATO` y `SIGRID_ALBARAN_NATURALEZA_POR_PRODUCTO`, como antes.

  **El `assert` sube** por delante de las guardas de naturaleza. Comprobé el invariante en quien construye el dato
  (en el espíritu de RM6):
  - `_resolver_lineas` fija `almacen_sin_vincular` siempre que haya alguna `tipo == "sin_vincular"`;
  - `tipo` es `sin_vincular` si y solo si `ctrpro_ide is None` (`albaran_compra_models.py:259-260`), que es
    justo la condición con la que `resolver_origen` llama a `_sin_vincular`;
  - `_almacen_sin_vincular` devuelve una tupla o lanza `almacen_de_obra_no_resuelto`.

  Así que el `assert` nunca dispara, y adelantarlo no puede convertir un `_FalloDeLinea` en un 500.
- `completar` / plantilla: `not linea.del_contrato` vale siempre `True` en el albarán, y la rama `elif not
  linea.vinculada` es la de antes. El aviso `iva_de_otro_proveedor` y el IVA de plantilla no cambian.

**`albaran_compra_statements.py`:** solo se añaden parámetros con el defecto de hoy (`PREFIJO_SERIE = "AC"`,
`cifras=0`). Ninguna constante SQL cambia. Los únicos que llaman son el núcleo y la subclase; `partes-reclamacion` tiene
sus propios `prefijo_de_serie` y `siguiente_cod`.

**`albaran_compra_models.py`:**
- `codigos: ClassVar` en `FalloLinea`, `AlbaranCompraError` y `AvisoAlbaran` apunta a los mismos `frozenset`, y
  `CODIGOS_*` no cambia.
- Un `ClassVar` no es campo de pydantic, así que `model_dump` y el esquema siguen iguales (diferencial y dorado).
- La base sigue rechazando los códigos nuevos (`test_f007_r31_la_base_sigue_rechazando_un_codigo_nuevo`).
- `proforma_models` amplía los conjuntos por unión en subclases, sin mutarlos.

**`config/settings.py`:** cinco campos nuevos con defectos cerrados. A los validadores existentes solo se les añaden
nombres de campo, y los `sigrid_albaran_*` no cambian (`test_f009_settings` pasa).

**`function_app.py`:**
- `_respuesta_albaran_compra_error` añade `details.reparto` solo si `getattr(exc, "reparto", None)` es verdadero.
  `AlbaranCompraError` no define `reparto` (solo `ProformaError`), así que en `sigrid/albaran` y `albaran-directo`
  los `details` no cambian.
- `build_dependencies`, `_exigir_escritura_de_albaranes`, `sigrid_albaran`, `_sigrid_albaran_extendido` y
  `sigrid_albaran_directo` no se tocan.
- La ruta nueva construye su propio caso de uso en cada petición y no comparte la instancia cacheada del albarán.

**`interface_adapters/`:** solo cambia un docstring (9 → 10 rutas).

**Clásico y `albaran-directo`:** sus casos de uso y modelos (`create_purchase_albaran_use_case`,
`create_direct_albaran_use_case`, `albaran_domain_models`, `albaran_directo_models`) no aparecen en el diff. Solo les
alcanzan `function_app` y `AlbaranCompraError` (la llave R8), ya revisados arriba. Su dorado está intacto y pasa.

## Lo que los tests de F-009 no cubrirían (y cómo queda)

1. **El dorado `f009_caracterizacion.json` solo cubre el clásico y `albaran-directo`.** Sus 12 claves son `clasico_*`
   y `directo_*`; el **modo extendido**, que es el que tocan las costuras, **no tiene dorado**. Para él, la red de R31
   son los tests unitarios de F-009 y F-015 sobre `f009_dobles`. Por eso añadí el diferencial: cierra ese hueco para
   todo lo que esos tests ejercitan, comparando el resultado entero y no solo lo que cada test afirma.
2. Los mensajes completos de `producto_no_permitido` y `naturaleza_no_valida` no los afirma ningún test de F-009. Los
   fijan `test_f007_perfil` (el de producto, por subcadena) y el diferencial (el texto exacto de los dos).
3. La configuración es compartida (O3, abajo). Ningún test puede cubrirla, porque es una cuestión de despliegue.

## Observaciones (no bloquean este bloque)

- **O1 · `design.md` se queda corto frente a lo implementado.** §Costuras 1-2 y la tabla «Ficheros a modificar» no
  mencionan:
  - `PerfilAlta.cifras_serie` ni el parámetro `siguiente_cod(..., cifras=)`, que es un tercer cambio en
    `albaran_compra_statements.py`;
  - `campo_max_lineas`;
  - `error`.

  Los tres son neutros con sus defectos y están probados (`test_f007_perfil`: 242-259 y 147-171), pero el diseño
  debería recogerlos para que la próxima revisión del núcleo los encuentre.
- **O2 · `PERFIL_ALBARAN.cla = 0` es dato muerto para el albarán.** Solo lo lee `CreateProformaUseCase._construir`.
  No hace daño, pero que nadie crea que cambiarlo mueve la `cla` del albarán.
- **O3 · Riesgo de despliegue: `Settings` es único para toda la Function App.** Una App Setting `SIGRID_PROFORMA_*`
  mal formada, por ejemplo una clave repetida en `..._NATURALEZA_POR_PRODUCTO` o una lista sin JSON válido, hace
  fallar `Settings()` y deja caídas **todas** las rutas, también `sigrid/albaran` en producción con la llave abierta.
  El mecanismo ya existía con las `SIGRID_ALBARAN_*`; lo nuevo es el acoplamiento.

  Recomiendo al líder dos cosas:
  - dar de alta las `SIGRID_PROFORMA_*` solo en JSON (D11) y con la llave cerrada;
  - tras el cambio de configuración, verificar un dry-run de `sigrid/albaran`.

  Conviene anotarlo en `azure-apps/sigrid_api.md` y avisar a albaranes antes de fusionar (§Riesgos del diseño).
- Aparte: `tests/test_f012_rutas.py` cambia el recuento de 9 a 10 rutas. Está fuera de la lista de R31 y el cambio es
  legítimo por la ruta nueva.

## Cambios requeridos

Ninguno para este bloque. O1 es una actualización de documentación que queda a decisión del líder.
