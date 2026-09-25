<!-- progress/current.md -->
# Trabajo en curso

## F-006 cerrada, desplegada y verificada (2026-09-25)

Resumen en `history.md`; verificación en
[`verificacion_F-006_obra0626.md`](verificacion_F-006_obra0626.md).
`sigrid/partes-reclamacion` queda **abierto** por decisión del humano
(`SIGRID_RECLAMACION_WRITE_ENABLED=true`). Lo que queda:

1. **Anular el parte de prueba `RS26.09/0439`** (obra 0626, UPV
   `0626.03PORTAL 1.1.A`) desde la UI de Sigrid: NO PROCEDE **sin** correo.
   Tras T18 seguía en SAT.
2. Push de `dev` y `main` (el humano). `azure-apps` `7df52e9` y `b3a43c2`,
   locales (no tiene remoto).
3. Dar la function key a `postventa-incidencias` para F-040.

**Menores abiertos (no bloquean):** M2, `[0-9]` acepta superíndices con la
colación CI (0 filas hoy); O2 y O4 van a `postventa-incidencias` F-040; el test
`test_f006_r4_los_prefijos_aceptan_json_y_csv` dice «CSV» pero solo prueba el
constructor: como App Setting, una lista en CSV no arranca la Function (medido;
afecta a todas las listas, ya documentado en `azure-apps/sigrid_api.md` §4).

**Sin trackear en la raíz:** el fichero vacío `` `0`].{t `` (2026-09-24 12:31),
ajeno; lo borra el humano si quiere.

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

F-007 (proformas) y F-008 (facturas de compra), `pending`
con `sdd` y rigor `critico`; y F-001 (calentamiento). Candidato del arnés: el
diagnóstico de la mutación paralela.

## Prompt para retomar

> Lee `CLAUDE.md` y `progress/current.md`. F-006 está cerrada, desplegada y
> verificada; queda que el humano anule en Sigrid el parte de prueba
> `RS26.09/0439`. Lo siguiente del backlog es F-007 (proformas) o F-008 (facturas
> de compra), ambas `pending` con `sdd`: no arranques ninguna sin preguntar.
