<!-- progress/spec_F-011.md -->
# F-011 · Informe del spec-author

Spec en `specs/F-011-documents-read-valida-database/` (requirements 105/150, design 211/250,
tasks 15 tareas; `python -m harness.tamano --feature F-011` dentro de los topes). Rama
`feature/F-011-documents-read-valida-database`. No se ha tocado código, ni la API ni el SQL Server.

## Qué propone

- **Validación en el caso de uso** (`ReadDocumentUseCase`, que pasa a recibir `Settings`):
  `database` debe estar en `ALLOWED_DATABASES` (igualdad exacta, como `sql/read`), antes de
  validar identificadores y de abrir conexión. Rechazo **400 `BaseNoPermitidaError`**, clase nueva
  en `domain/models/document_models.py` que hereda de `ValueError` pero cuyo `details.type` nunca
  es `"ValueError"` (mcp-bbdd lo leería como «sin binario»; con el tipo nuevo lo trata como «origen
  no disponible»). Texto paralelo al de `sql/read`, con `(ninguna)` si la lista está vacía.
- **Sin tocar `infrastructure/security/`, `config/settings.py` ni el modelo.** Los demás errores de
  `documents/read` (F-010) no cambian. Los tests de F-010 solo cambian la construcción del caso de
  uso (dos líneas), sin tocar aserciones.
- **Opcional (D2 = A1)**: `IdentifierGuard` sobre `database` dentro de `_connect`, para todos los
  endpoints. Las tareas que dependen de esto van marcadas `[A1]`.
- Documentación: `docs/ARCHITECTURE.md` y `azure-apps/sigrid_api.md` §8.3, §5.1, §4 y §10 (T10-T11).
- Verificación manual en solo lectura (T12-T14): App Settings antes de desplegar; después
  `ruesma_rep`/365617 → 200 con 17865 bytes, base inexistente, `;APP=` y `RUESMA_REP` → 400.

## Hallazgo nuevo (pesa en D2)

El hueco de D6 **no es solo de `documents/read`**. `sigrid/contrato-lineas` conecta en dry-run
con `request.database` sin lista blanca: la comprobación de `ALLOWED_WRITE_DATABASES` está en el
paso 6 de `application/use_cases/add_contract_lines_use_case.py` (l. 171), solo con `commit`, y
`locate_contract` (l. 39) ya conecta antes. El albarán clásico (l. 506) y `albaran-directo`
(l. 299) siguen el mismo patrón (lo confirma el implementer). Solo lo cierra A1.

## Decisiones que necesitan al humano

- **D1 · Qué lista valida `documents/read`.** Recomiendo **`ALLOWED_DATABASES` tal cual**: es la
  misma frontera y la misma credencial que `sql/read`, que ya lee esas bases enteras (también
  `ruesma_rep.dbo.gra` por tres partes), así que una lista más estrecha no protege nada; además no
  exige ningún paso de despliegue. La alternativa es una App Setting nueva
  `ALLOWED_DOCUMENT_READ_DATABASES=["ruesma_rep"]`, con defecto cerrado: toca `config/settings.py`
  y obliga a fijarla **antes** de publicar (comando en design §D1), o los tres consumidores
  reciben 400. Descartado reutilizar `SIGRID_DOCUMENT_WRITE_DATABASE`, porque es la llave de
  escritura. Quitar `master` de `ALLOWED_DATABASES` queda **fuera** de F-011, porque afecta a
  `sql/read`.
- **D2 · ¿Se blinda `_connect` para todos los endpoints?** Recomiendo **A1**
  (`IdentifierGuard.validate_identifier(database, field_name="database")` en `_connect`). **Es un
  cambio de seguridad en el adaptador compartido**: no modifica `infrastructure/security/`, pero
  lo atraviesan las ocho conexiones de toda la API. Cierra el hueco de dominio de arriba y el de
  una lista blanca mal configurada. Riesgo: una base fuera del patrón `^[A-Za-z_][A-Za-z0-9_]*$`
  dejaría de conectar (T12 lo comprueba en las App Settings). Alternativas: A0 (no tocar: cumple
  el acceptance para `documents/read`, pero deja el hueco de dominio), A2 (escapar con llaves:
  descartada porque no es verificable sin BBDD), A3 (validar en los seis modelos de dominio) y
  A4 (validar las listas al arrancar).
- **D3 · Código y tipo**: 400 `BaseNoPermitidaError` y texto que lista las bases permitidas, como
  `sql/read`. La alternativa es no listarlas.
- **D4 · Comparación sensible a mayúsculas** (`RUESMA_REP` → 400), igual que `sql/read`.
- El paso 5 de la verificación manual (dry-run de `sigrid/contrato-lineas` con una base
  inyectada, solo con A1) necesita la autorización del humano para esa llamada concreta.
