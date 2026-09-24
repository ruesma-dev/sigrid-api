<!-- progress/current.md -->
# Trabajo en curso

## F-006 · Alta de partes de reclamación en lote (`in_progress`, en revisión)

Rama `feature/F-006-alta-parte-reclamacion` (desde `dev` `210fac1`), sin push.
Endpoint `POST /api/sigrid/partes-reclamacion`: lote de hasta 50 partes de una
obra, una transacción por parte, dry-run por defecto, idempotencia por
`conext RCPCLI` con prefijo `PVI-`. Spec aprobada por el humano el 2026-09-24
(`specs/F-006-alta-parte-reclamacion/`, decisiones Q1-Q4 al principio de
`requirements.md`); modelo medido en
[`explore_F-006_modelo_parte.md`](explore_F-006_modelo_parte.md).

**Implementación hecha** ([`impl_F-006.md`](impl_F-006.md), HEAD `22ba2a5`):
T3-T14 y T19, un commit por tarea; 229 tests de F-006, cobertura 100 % de 560
líneas, mutación 217/217 sobre `22e23f7`, `init.sh` en verde. `azure-apps`
`7df52e9` (solo `sigrid_api.md`, sin push). Nada escrito contra Sigrid.

**Revisión troceada en curso (2026-09-25)**, un informe por bloque:
[`review_F-006_estado.md`](review_F-006_estado.md) (C1/C2/C5: CAMBIOS, este
fichero), [`review_F-006_docs.md`](review_F-006_docs.md) (C3 bis y
documentación: APROBADO), [`review_F-006_verificacion.md`](review_F-006_verificacion.md)
(C4/C4 ter: CAMBIOS en el guion manual T16/T17), `review_F-006_codigo.md`
(C3 y corrección) y `review_F-006_rigor.md` (C4 bis). Después, veredicto
consolidado en `review_F-006.md`.

**Ronda de cambios aplicada (2026-09-25)**, [`impl_F-006.md`](impl_F-006.md) §7, §9 y §10: T17 (`2edba47`, solo la llave de reclamaciones, cerrada tras T18), T16 (`657a9bf`, lote literal, oficio `0006` leído por `sql/read`) y M1 (`52ba4be`, log sin valores, RED y 8/8 mutantes manuales muertos: el arnés genera 0 en esas líneas); `init.sh` en verde, 1.733 tests.

**Después del APROBADO**, del humano: merge a `dev` y push, y las MANUALES
T15-T18 de `tasks.md` (desplegar con la escritura de reclamaciones cerrada,
dry-run en la obra 0626 / UPV `0626.03PORTAL 1.1.A`, un `commit:true` autorizado
de `PVI-PRUEBA-0001`, repetirlo para la idempotencia y anular el parte en la UI
como NO PROCEDE sin correo).

**Sin trackear en la raíz:** el fichero vacío `` `0`].{t `` (2026-09-24 12:31),
ajeno a F-006; parece un comando de consola mal escapado. Lo borra el humano si
quiere.

## Lo que espera al humano además de F-006

- Decidir si el adjunto de prueba de F-004 (`cod` `202609060933388219.prueba`,
  reclamación `RS26.08/0123`) se borra desde la UI de Sigrid.
- Dar a Posventa su function key (contrato en `azure-apps/sigrid_api.md` §8.8).
- `azure-apps` no tiene remoto y acumula commits locales; hay un `.env` sin
  trackear allí que no debe commitearse.

## Pendiente de decisión del humano

### Del arnés — valen para cualquier proyecto, así que van a `arnes-base`

- **Diagnosticar `harness/mutacion_paralela.py`.** Dos evidencias ya: en F-003,
  un mutante que muere en 1,9 s salió superviviente; en F-004, 5 supervivientes
  no reproducibles sobre el mismo commit. **Pista concreta** del reviewer
  final: `ResultadoSuite.verde` (`harness/mutacion.py` l. 491) da verde para
  `exit 5` de pytest (ningún test recogido) y `ejecutar` (l. 612) lo traduce a
  SUPERVIVIENTE. Propuesta: `SUPERVIVIENTE` con `sin_tests` → `INDETERMINADO`.
  Sesgo pesimista en las dos features, así que los ceros son sólidos. **Tercera
  evidencia en F-006:** 6 de 42 supervivientes de la ronda 1 murieron al
  reevaluarlos en serie (`mutacion_F-006.md`).
- **Un test que construye `Settings` real debe aislar el entorno** (la campaña
  exporta el `.env`): lección de F-004 T14c; merece regla en `CONVENTIONS.md`.
- Pendientes de antes: `pytest-timeout` para los cuelgues; «Evidencias» con
  SHA y workers como regla; `init.sh` sin aviso de `mutacion_F-XXX.md` en
  `critico`; RM5 pide reproducir uno; `harness/rutas_sensibles.json` no
  existe en un repo con `infrastructure/security/`; cada trozo de revisión
  debe declarar qué checkpoints deja fuera.

### De configuración y de la base

- **`local.settings.json` está versionado con dos contraseñas reales** desde
  el primer commit (`e903394`, 2026-04-16), en `origin/main` y `origin/dev`.
  Lo que cierra el hueco es **rotarlas** en Sigrid y en el Key Vault; después
  `git rm --cached local.settings.json` y `.gitignore`.
- **`ALLOWED_DATABASES` incluye `master`** y ningún consumidor lo necesita.
- **`user_rw` tiene `UPDATE`** sobre `ruesma_rep.dbo.gra`; no se probó `DELETE`.
- El guard de `ALLOWED_WRITE_DATABASES` vacía **falla abierto** en los cuatro
  casos de uso de dominio (patrón calcado de albaranes); feature propia.
- `scripts/verificar_sql_ecosistema.py` copia a mano las listas blancas.
- 19.196 filas documentales sin dueño ni en `gra` ni en `dog` (~2.000/año):
  Sigrid parece borrar en negocio sin borrar en el repositorio.
- En albaranes, `sigrid_api_contrato_client.py` resuelve por `cod` sin `emp`
  (8 `cod` repetidos entre empresas, hoy inocuo).

## Lo siguiente en el backlog

Cerrar F-006. Después: F-007 (proformas) y F-008 (facturas de compra), `pending`
con `sdd` y rigor `critico`; y F-001 (calentamiento). Candidato del arnés: el
diagnóstico de la mutación paralela.

## Prompt para retomar

> Lee `CLAUDE.md` y `progress/current.md`. F-006 está implementada en
> `feature/F-006-alta-parte-reclamacion` y en revisión troceada
> (`progress/review_F-006_*.md`). Si falta algún informe parcial, relánzalo; con
> todos, aplica los CAMBIOS con el implementer y pide el veredicto consolidado en
> `review_F-006.md`. No ejecutes T15-T18: son del humano. No arranques nada nuevo
> sin preguntar.
