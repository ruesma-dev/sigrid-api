<!-- progress/current.md -->
# Trabajo en curso

Limpiado el 2026-11-23: las secciones de features cerradas están en `history.md`. Por decisión del humano
(2026-11-23), **los documentos de prueba que siguen en Sigrid ya no se persiguen**: `AC26/30670` (F-015),
`PROF26/01360` (F-007), `PROF26/01386` y `PROF26/01387` (F-016), `FR26/11425` y `FRGG26/2772` (F-008, con el aviso de
abajo), el parte `RS26.09/0439` (F-006) y el adjunto `202609060933388219.prueba` (F-004). Nadie los anula ni los borra
desde aquí.

## Sin feature activa

F-008 cerrada el 2026-11-24 (en `history.md`). **Aviso abierto:** las dos facturas de prueba de F-008,
`FR26/11425` y `FRGG26/2772`, tienen pagos en PDT a **2026-12-02** (82,84 y 12,1). Financiero las anula en el escritorio
o bloquea los pagos; desde la API no se puede (anular borra filas).

## Llaves y avisos que esperan al humano

- **F-009** (`sigrid/albaran`): llave `SIGRID_ALBARAN_WRITE_ENABLED=true` desde el 2026-10-07. Queda **T24**, en solo
  lectura cuando F-053 de albaranes esté en real: `prepma` de la primera alta y stock/PMP/`canser` de la primera
  devolución (consultas en `progress/spec_F-009.md` §Manuales). Sin respuesta aún del director de Administración y
  Control de Costes (correo del 2026-10-07) sobre la contabilización de `AC26/28916` (MA9999 → `0404.CDSB37`); la ficha
  de MA9999 tiene naturaleza `MA1501`. Contrato con albaranes §2-§4 congelado: avisar a su sesión antes de tocarlo.
- **F-007 y F-016** (`sigrid/proforma`): `SIGRID_PROFORMA_WRITE_ENABLED` y `SIGRID_PROFORMA_ORIGEN_ENABLED` cerradas.
  Abrirlas es decisión del humano, avisando a `proformas`.
- **F-018**: `albaranes` enciende `ALTA_SIGRID_ENVIAR_DTO` cuando decida.
- **F-006**: `sigrid/partes-reclamacion` abierto (`SIGRID_RECLAMACION_WRITE_ENABLED=true`). Falta dar la function key a
  Posventa (`postventa-incidencias` F-040; contrato en `azure-apps/sigrid_api.md` §8.8).

## Pendiente de decisión del humano

### Del arnés (van a `arnes-base`)

- **El instalador pisa tests propios homónimos** (`tests/**` como `arnes_puro`; F-019 perdió los 8 tests de F-004).
  Encargado en `arnes-base` el 2026-11-23 (`ENCARGO_pendiente_instalador_pisa_tests_propios_homonimos.md`,
  `48a0e7f`).
- **`harness/mutacion_paralela.py`**: supervivientes no reproducibles en F-003, F-004 y F-006 (`exit 5` de pytest
  contado como verde). La 1.10.1 trae `INDETERMINADO` (F-023 de `arnes-base`): comprobar en la próxima campaña si
  queda resuelto.
- **`harness/mutacion.py` no genera mutantes** para `not in`, literales de texto ni argumentos con nombre (F-011).
- **C4 y C5 de `CHECKPOINTS.md` chocan** con las tareas MANUAL posteriores al merge (F-010): propuesta «toda tarea `[x]`
  salvo las MANUAL de despliegue y verificación, que bloquean el `done` pero no el APROBADO».
- **Un test que construye `Settings` real debe aislar el entorno** (lección de F-004 T14c): regla en `CONVENTIONS.md`.
- Menores: `pytest-timeout` para los cuelgues; «Evidencias» con SHA y workers como regla; RM5 pide reproducir uno;
  cada trozo de revisión declara qué checkpoints deja fuera.
- Resuelto en la 1.10.1 (F-019): el hook `PostToolUse` que contaminaba la mutación ya no está.

### De configuración y de la base

- **`sql/read` no aplica `timeout_seconds` como tope de la consulta** (solo el del login): una lectura que el balanceador
  corta a 230 s sigue corriendo en producción. Es **F-013**. Mientras tanto, no relanzar una lectura justo después de un
  corte.
- **El dry-run de dominio lee cualquier base que case con el patrón** y a la que llegue `ro_user`: **F-014**.
- **`ALLOWED_DATABASES` incluye `master`** y ningún consumidor lo necesita.
- **`user_rw` tiene `UPDATE`** sobre `ruesma_rep.dbo.gra`; no se probó `DELETE`.
- El guardia de `ALLOWED_WRITE_DATABASES` vacía **falla abierto** en los casos de uso de dominio; feature propia.
- Las trazas `str(exc)` de las rutas distintas de las de F-012 vuelcan `input` de la petición; sin alta.
- `scripts/verificar_sql_ecosistema.py` copia a mano las listas blancas.
- 19.196 filas documentales sin dueño ni en `gra` ni en `dog` (~2.000/año): Sigrid parece borrar en negocio sin borrar
  en el repositorio.
- **`sigrid-api-v2`** tiene el fallo de cabecera que arregló F-010 (`interface_adapters/http/responses.py:62`): aviso
  para ese repositorio.
- En albaranes, `sigrid_api_contrato_client.py` resuelve por `cod` sin `emp` (8 `cod` repetidos entre empresas, hoy
  inocuo).

## Lo siguiente en el backlog

Ninguna feature activa ni en `todo`. En `pending`, por prioridad: F-001 (calentamiento), F-013 (tope real de
`sql/read`), F-014 (dry-run de dominio) y F-017 (partidas con código repetido en `sigrid/proforma`). Comprometer
cualquiera es decisión del humano.

## Prompt para retomar

> Lee `CLAUDE.md` y `progress/current.md`. No hay feature activa. Aviso abierto: los pagos de `FR26/11425` y
> `FRGG26/2772` vencen el 2026-12-02 y los tiene que anular o bloquear Financiero. En `pending`: F-001, F-013, F-014 y
> F-017.
