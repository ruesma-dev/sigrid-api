<!-- progress/current.md -->
# Trabajo en curso

## F-006 cerrada el 2026-09-25 (APROBADO): queda lo del humano

Resumen en `history.md`. Por orden:

1. Merge de `feature/F-006-alta-parte-reclamacion` en `dev` y push (y `main`
   cuando toque). `azure-apps` `7df52e9` va sin push (no tiene remoto).
2. **T15-T18 MANUALES**, comandos exactos en
   `specs/F-006-alta-parte-reclamacion/tasks.md`: desplegar y fijar las cuatro
   App Settings con la escritura de reclamaciones cerrada; dry-run del lote
   literal en la obra 0626 / UPV `0626.03PORTAL 1.1.A`; un `commit:true`
   autorizado de `PVI-PRUEBA-0001` abriendo **solo**
   `SIGRID_RECLAMACION_WRITE_ENABLED` (`SIGRID_DOMAIN_WRITE_ENABLED` no se
   toca); repetirlo (idempotente), anular el parte en la UI (NO PROCEDE sin
   correo) y cerrar la llave. Resultados a un `verificacion_F-006_*.md`.
   Avisos: en la respuesta `indice` empieza en 0; los paréntesis del `--query`
   de T15 pueden romper `az.cmd` en Windows (`sigrid_api.md` §11).
3. Dar la function key a `postventa-incidencias` para F-040.

**Sin trackear en la raíz:** el fichero vacío `` `0`].{t `` (2026-09-24 12:31),
ajeno; parece un comando de consola mal escapado. Lo borra el humano si quiere.

**Menores abiertos de la revisión (no bloquean):** M2, `[0-9]` acepta
superíndices con la colación CI (0 filas hoy; si aparece, feature propia); O2 y
O4 van a `postventa-incidencias` F-040; dos precisiones de `azure-apps/sigrid_api.md`
(§8.9 «o sin ficha `rcp`», §7.2 `base_de_datos_no_permitida` también en dry-run)
para la próxima vez que se toque.

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

Las MANUALES de F-006 (humano). Después: F-007 (proformas) y F-008 (facturas de compra), `pending`
con `sdd` y rigor `critico`; y F-001 (calentamiento). Candidato del arnés: el
diagnóstico de la mutación paralela.

## Prompt para retomar

> Lee `CLAUDE.md` y `progress/current.md`. F-006 está cerrada (APROBADO) y
> espera al humano: merge y las MANUALES T15-T18. Si trae sus resultados,
> anótalos en `progress/verificacion_F-006_*.md`. No ejecutes escrituras contra
> Sigrid. No arranques F-007 ni F-008 sin preguntar.
